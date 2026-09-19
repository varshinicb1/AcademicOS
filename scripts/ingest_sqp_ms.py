"""Download CBSE SQP+MS pairs and report their structure.

SQP and MS are separate documents: the question paper holds the questions, the
marking scheme holds the answers. They are linked by question number, and CBSE
numbers them the same way -- which is the whole reason this source is worth
ingesting when the board-paper corpus could not be relinked.

Targets are chosen by value, not availability: Class X Social Science is the
largest unmapped block in the coverage matrix (375 questions, no labeled
reference at all), so it is first.

Run:  python scripts/ingest_sqp_ms.py [--inspect SUBJECT]
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "academicos-data" / "corpus" / "cbse-sqp"
UA = {"User-Agent": "Mozilla/5.0 (compatible; AcademicOS corpus research)"}

# (year-label, index page) pairs that the discovery script confirmed live.
INDEXES = [
    ("ClassX_2025_26", "https://cbseacademic.nic.in/SQP_CLASSX_2025-26.html"),
    ("ClassXII_2025_26", "https://cbseacademic.nic.in/SQP_CLASSXII_2025-26.html"),
]

# Subjects to ingest, by the stem CBSE uses in the filename.
#
# Originally a 3-subject list that delivered Social Science only. The PRD's
# decision 4 is "all grades 6-12, all subjects", so the filter is now None --
# take everything the index publishes. The list is kept as a mechanism because
# a targeted run is genuinely useful when adding one subject at a time.
TARGETS = None


def discover() -> dict[tuple[str, str], dict[str, str]]:
    """`(year, subject) -> {"SQP": url, "MS": url}` for paired documents only.

    A question paper with no marking scheme is not ingested: the answer-key rule
    is that a question without an answer is not a question, and half a pair
    cannot produce one.
    """
    pairs: dict[tuple[str, str], dict[str, str]] = {}
    for label, page in INDEXES:
        try:
            with urllib.request.urlopen(
                    urllib.request.Request(page, headers=UA), timeout=30) as r:
                html = r.read().decode("utf-8", errors="replace")
        except Exception as exc:
            print(f"  {label}: {type(exc).__name__}: {exc}")
            continue
        for href in sorted(set(re.findall(r'href\s*=\s*["\']([^"\']+\.pdf)["\']',
                                          html, re.I))):
            name = href.split("/")[-1]
            # Hindi-medium duplicates live alongside; keep them distinguishable.
            medium = "hi" if name.endswith("_hi.pdf") else "en"
            stem = re.sub(r"(_hi)?\.pdf$", "", name, flags=re.I)
            m = re.match(r"(.+?)-(SQP|MS)$", stem, re.I)
            if not m:
                continue
            subject, kind = m.group(1), m.group(2).upper()
            pairs.setdefault((label, subject), {})[medium + ":" + kind] = href
    return pairs


def url_for(href: str, page: str) -> str:
    base = page.rsplit("/", 1)[0]
    return href if href.startswith("http") else f"{base}/{href.lstrip('/')}"


def download(url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 2000:
        return True
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=90) as r:
            data = r.read()
        if len(data) < 2000:
            return False
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return True
    except Exception as exc:
        print(f"    FAILED {type(exc).__name__}: {exc}")
        return False


def inspect(pdf: Path) -> None:
    """Print enough structure to design a parser against."""
    try:
        import pymupdf
    except ImportError:
        import fitz as pymupdf
    doc = pymupdf.open(pdf)
    print(f"    pages: {doc.page_count}")
    text = "\n".join(doc[i].get_text() for i in range(min(3, doc.page_count)))
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    print(f"    first lines: {lines[:12]}")
    # How are questions numbered? This decides whether SQP and MS agree.
    nums = re.findall(r"^\s*(\d{1,2})[.)]\s", text, re.M)
    print(f"    question numbers seen on first pages: {nums[:20]}")
    secs = re.findall(r"^\s*(SECTION\s*[-–]?\s*[A-E])\b", text, re.I | re.M)
    print(f"    sections: {sorted(set(s.upper() for s in secs))}")
    doc.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inspect", action="store_true")
    args = ap.parse_args()

    print("== discovering pairs ==")
    pairs = discover()
    print(f"  {len(pairs)} (year, subject) entries")

    if TARGETS is None:
        wanted = dict(pairs)
        print(f"  taking all {len(wanted)} (no subject filter)")
    else:
        wanted = {k: v for k, v in pairs.items() if k[1] in TARGETS}
        print(f"  {len(wanted)} match the targets {TARGETS}")

    manifest = []
    for (label, subject), kinds in sorted(wanted.items()):
        sqp = kinds.get("en:SQP")
        ms = kinds.get("en:MS")
        if not sqp or not ms:
            print(f"  SKIP {label} {subject}: incomplete pair "
                  f"(have {sorted(kinds)})")
            continue
        page = dict(INDEXES)[label]
        print(f"\n  {label} {subject}")
        ok_a = download(url_for(sqp, page), OUT / label / f"{subject}-SQP.pdf")
        ok_b = download(url_for(ms, page), OUT / label / f"{subject}-MS.pdf")
        print(f"    SQP {'ok' if ok_a else 'FAILED'}   MS {'ok' if ok_b else 'FAILED'}")
        if ok_a and ok_b:
            manifest.append({
                "year": label, "subject": subject,
                "sqp": f"{subject}-SQP.pdf", "ms": f"{subject}-MS.pdf",
                "sqpUrl": url_for(sqp, page), "msUrl": url_for(ms, page),
            })
            if args.inspect:
                print("    -- SQP --")
                inspect(OUT / label / f"{subject}-SQP.pdf")
                print("    -- MS --")
                inspect(OUT / label / f"{subject}-MS.pdf")

    if manifest:
        (OUT / "_manifest.json").write_text(json.dumps({
            "source_pages": dict(INDEXES),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "count": len(manifest),
            "rights": {
                "origin": "CBSE",
                "redistribution": "unknown",
                "note": "No redistribution position obtained. Same status as the "
                        "CBE corpus; see docs/question-bank-api.md section 2.",
            },
            "pairs": manifest,
        }, indent=1), encoding="utf-8")
        print(f"\nwrote {(OUT / '_manifest.json').relative_to(REPO)} ({len(manifest)} pairs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
