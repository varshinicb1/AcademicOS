"""Download the official CBSE CBE item banks.

Why this source, and not a scraped dataset
------------------------------------------
The brief is "work like an examination board". CBSE publishes, under its own
name, exactly the artefact that requires:

    https://cbseacademic.nic.in/cbe/assessment.html

15 documents: Classes 6-10 x {Mathematics, Science, English}. Each one is a
compilation of assessment items where **every item carries**:

  * a Learning Ladder content reference (e.g. `10.3.9 Living world`) -- a
    curriculum-mapped topic id, not a keyword guess;
  * Assessment Objective coverage with a mark split (AO1..AO4);
  * the number of marks;
  * the source material the item depends on;
  * the questions;
  * **and the mark scheme**.

That is the whole requirement in one file format, from the authority, and it is
published for teachers to use. Nothing scraped off a third party comes close,
and two of the third-party datasets surveyed carry no licence at all.

Provenance is recorded per file, not assumed: the discovery step reads the link
CBSE actually publishes rather than guessing a URL, because the filenames are
inconsistent -- `Item-Bank---Maths-Class-6.pdf` against
`Item-Bank--Maths---Class-10.pdf` and `Item-Bank-----English---Class-9.pdf`.

Rights: these are CBSE documents. `scripts/ingest_cbse_item_banks.py` records
`redistribution: "unknown"` for everything it downloads, because no written
position exists. A ruling turns that into a filter, not a migration.

Run:  python scripts/ingest_cbse_item_banks.py [--list] [--force]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

SOURCE_PAGE = "https://cbseacademic.nic.in/cbe/assessment.html"
BASE = "https://cbseacademic.nic.in/cbe/documents/"
DEST = REPO / "academicos-data" / "corpus" / "cbse-cbe"
MANIFEST = DEST / "_manifest.json"

UA = {"User-Agent": "Mozilla/5.0 (compatible; AcademicOS-corpus-builder/1.0)"}
HREF = re.compile(r'href="([^"]*Item-Bank[^"]*\.pdf)"', re.I)
# "Item-Bank---Science-Class-9.pdf" / "Item-Bank-----English---Class-9.pdf"
NAME = re.compile(r"Item-Bank-+(?P<subject>[A-Za-z]+)-+Class-?(?P<class>\d+)", re.I)

SUBJECT_MAP = {"maths": "Mathematics", "mathematics": "Mathematics",
               "science": "Science", "english": "English"}


def discover() -> list[dict]:
    """The authoritative list, read from the page CBSE publishes."""
    req = urllib.request.Request(SOURCE_PAGE, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        html = r.read().decode("utf-8", "replace")

    out: dict[str, dict] = {}
    for href in HREF.findall(html):
        name = href.split("/")[-1]
        m = NAME.search(name)
        if not m:
            continue
        raw = m.group("subject").lower()
        out.setdefault(name, {
            "filename": name,
            "subject": SUBJECT_MAP.get(raw, m.group("subject").title()),
            "grade": int(m.group("class")),
            "url": BASE + name,
            "discovered_from": SOURCE_PAGE,
        })
    return [out[k] for k in sorted(out)]


def fetch(entry: dict, *, force: bool = False) -> dict:
    dest = DEST / entry["filename"]
    if dest.exists() and not force:
        data = dest.read_bytes()
        entry.update(bytes=len(data), sha512=hashlib.sha512(data).hexdigest(),
                     status="cached")
        return entry
    req = urllib.request.Request(entry["url"], headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            data = r.read()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        entry.update(status=f"error: {exc}")
        return entry
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    entry.update(bytes=len(data), sha512=hashlib.sha512(data).hexdigest(),
                 status="downloaded")
    return entry


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="discover only, do not download")
    ap.add_argument("--force", action="store_true", help="re-download everything")
    args = ap.parse_args()

    try:
        entries = discover()
    except Exception as exc:                                   # noqa: BLE001
        print(f"could not read {SOURCE_PAGE}: {exc}", file=sys.stderr)
        return 1

    print(f"discovered {len(entries)} CBSE CBE item bank(s) from the published page")
    for e in entries:
        print(f"  {e['subject']:<12} class {e['grade']:<3} {e['filename']}")

    if args.list:
        return 0

    print()
    total = 0
    failures = 0
    for e in entries:
        e = fetch(e, force=args.force)
        if e["status"].startswith("error"):
            failures += 1
            print(f"  FAIL  {e['filename']}: {e['status']}")
        else:
            total += e.get("bytes", 0)
            print(f"  {e['status']:<10} {e['filename']:<42} {e.get('bytes', 0):>10,} bytes")

    manifest = {
        "source_page": SOURCE_PAGE,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "count": len(entries),
        "total_bytes": total,
        # Recorded, not assumed. Nothing here is redistributable until a written
        # position exists; see docs/question-bank-api.md section 2.
        "rights": {
            "origin": "CBSE",
            "redistribution": "unknown",
            "basis": "",
            "note": "CBSE CBE item banks, published on cbseacademic.nic.in for "
                    "teacher use. No redistribution position obtained.",
        },
        "documents": entries,
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")

    print()
    print(f"{len(entries) - failures}/{len(entries)} documents, {total / 1_000_000:.1f} MB")
    print(f"manifest -> {MANIFEST.relative_to(REPO)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
