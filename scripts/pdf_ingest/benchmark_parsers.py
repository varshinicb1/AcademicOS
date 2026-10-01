"""Benchmark PDF parsers on real NCERT chapters against curated ground truth.

Ground truth = bank-pipeline/transcriptions/textbook/*.json, which carries per-chapter
topic titles and `startsWith` anchor strings. Those anchors are literal text from the
printed book, so "was this anchor recovered" is an objective, checkable question.
No LLM judge is involved.

Engines: pdfplumber, docling, opendataloader-pdf.

Usage:
    python scripts/pdf_ingest/benchmark_parsers.py --per-stratum 2
    python scripts/pdf_ingest/benchmark_parsers.py --engines pdfplumber,docling
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
from collections import defaultdict
from pathlib import Path

CHAPTER_DIR = Path(
    r"C:\Users\varsh\OneDrive\Documents\Sarvam\ncert-dataset\textbooks\chapters"
)
TRUTH_DIR = Path(
    r"C:\Users\varsh\OneDrive\Documents\Sarvam\bank-pipeline\transcriptions\textbook"
)
OUT_DIR = Path(__file__).resolve().parent

DEVANAGARI = re.compile(r"[\u0900-\u097F]")
REPLACEMENT = re.compile(r"[\ufffd\u0000-\u0008\u000b\u000c\u000e-\u001f]")


def norm(text: str) -> str:
    """Normalise for substring matching. Never deletes non-ASCII.

    Devanagari must survive: NCERT Hindi is the reason this function exists.
    """
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\u00a0", " ")
    text = REPLACEMENT.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip().casefold()


# --------------------------------------------------------------------------- truth


def build_truth_index() -> dict[tuple[str, int], dict]:
    """Map (book_code, chapter_number) -> {title, language, class, subject, topics}."""
    index: dict[tuple[str, int], dict] = {}
    for path in sorted(TRUTH_DIR.glob("*.json")):
        if path.name.endswith(".solve2.json"):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        book = data.get("book") or {}
        chapter = data.get("chapter") or {}
        code = book.get("code")
        num = chapter.get("number")
        if not code or not isinstance(num, int):
            continue
        topics = [
            {"title": t.get("title", ""), "anchor": t.get("startsWith", "")}
            for t in data.get("topics", [])
            if isinstance(t, dict)
        ]
        if not topics:
            continue
        index[(code, num)] = {
            "code": code,
            "chapter": num,
            "title": chapter.get("title", ""),
            "class": book.get("class"),
            "subject": book.get("subject"),
            "language": book.get("language"),
            "topics": topics,
        }
    return index


def build_pdf_index() -> dict[tuple[str, int], Path]:
    """Map (book_code, chapter_number) -> pdf path, parsed from `<code><NN>.pdf`."""
    index: dict[tuple[str, int], Path] = {}
    for pdf in sorted(CHAPTER_DIR.rglob("*.pdf")):
        stem = pdf.stem
        m = re.match(r"^([a-z]+?[a-z0-9]*?)(\d{2})$", stem, re.IGNORECASE)
        if not m:
            continue
        code, num = m.group(1).lower(), int(m.group(2))
        index.setdefault((code, num), pdf)
    return index


def select_sample(truth, pdfs, per_stratum: int) -> list[dict]:
    strata: dict[tuple, list[dict]] = defaultdict(list)
    for key, t in truth.items():
        if key not in pdfs:
            continue
        if not any(t["topics"]):
            continue
        # Stratum: class + subject + language, so every script and every content
        # shape (tables, figures, prose) is represented.
        strata[(t["class"], t["subject"], t["language"])].append(t)

    sample: list[dict] = []
    for key in sorted(strata, key=lambda k: (str(k[0]), str(k[1]), str(k[2]))):
        bucket = strata[key]
        # Spread chapters within a stratum instead of taking the first N.
        step = max(1, len(bucket) // per_stratum)
        picked = bucket[::step][:per_stratum]
        for t in picked:
            sample.append({**t, "pdf": pdfs[(t["code"], t["chapter"])]})
    return sample


# -------------------------------------------------------------------------- engines


def page_count(pdf: Path) -> int:
    """Best-effort page count. Never raise: a missing reader must not discard a
    completed conversion, which is the expensive part."""
    for mod, fn in (("fitz", None), ("pypdf", None)):
        try:
            if mod == "fitz":
                import fitz

                doc = fitz.open(pdf)
                n = doc.page_count
                doc.close()
            else:
                from pypdf import PdfReader

                n = len(PdfReader(str(pdf)).pages)
            return max(n, 1)
        except Exception:  # noqa: BLE001, S112
            continue
    return 1


def engine_pdfplumber(pdf: Path) -> tuple[str, dict]:
    import pdfplumber

    t0 = time.time()
    pages: list[str] = []
    tables = 0
    with pdfplumber.open(pdf) as doc:
        n = len(doc.pages)
        for page in doc.pages:
            pages.append(page.extract_text() or "")
            try:
                tables += len(page.find_tables())
            except Exception:  # noqa: BLE001, S110
                pass
    dt = time.time() - t0
    return "\n".join(pages), {"s_per_page": round(dt / max(n, 1), 4), "tables": tables}


def engine_docling(pdf: Path) -> tuple[str, dict]:
    from docling.document_converter import DocumentConverter

    t0 = time.time()
    result = DocumentConverter().convert(str(pdf))
    dt = time.time() - t0
    md = result.document.export_to_markdown()
    n = getattr(result, "page_count", None) or page_count(pdf)
    return md, {"s_per_page": round(dt / max(n, 1), 4), "tables": None}


def engine_opendataloader(pdf: Path, workdir: Path) -> tuple[str, dict]:
    import opendataloader_pdf

    out = workdir / pdf.stem
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    opendataloader_pdf.convert(
        input_path=str(pdf), output_dir=str(out), format="markdown,json"
    )
    dt = time.time() - t0
    mds = sorted(out.rglob("*.md"))
    text = mds[0].read_text(encoding="utf-8", errors="replace") if mds else ""

    return text, {"s_per_page": round(dt / max(page_count(pdf), 1), 4), "tables": None}


def engine_pymupdf(pdf: Path) -> tuple[str, dict]:
    """Fast structural extraction from the PDF text layer via the shared module.

    See ncert_extract.py for the full rationale and the failure modes it fixes.
    """
    import fitz

    import ncert_extract as nx

    t0 = time.time()
    doc = fitz.open(pdf)
    n = max(doc.page_count, 1)
    lines: list[tuple] = []
    fonts: set[str] = set()
    for i, page in enumerate(doc):
        lines.extend(nx.read_page_lines(page, i))
        try:
            for f in page.get_fonts(full=True):
                fonts.add(f[3] or "")
        except Exception:  # noqa: BLE001, S110
            pass
    res = nx.structure(lines, fonts=sorted(fonts))
    doc.close()
    dt = time.time() - t0
    return res["markdown"], {
        "s_per_page": round(dt / n, 4),
        "tables": None,
        "headings_found": res["n_headings"],
        "body_size": res["body_size"],
    }


ENGINES = {
    "pdfplumber": lambda p, w: engine_pdfplumber(p),
    "pymupdf": lambda p, w: engine_pymupdf(p),
    "docling": lambda p, w: engine_docling(p),
    "opendataloader": lambda p, w: engine_opendataloader(p, w),
}

RUN_T0 = time.time()


# -------------------------------------------------------------------------- scoring


def ngrams(text: str, n: int = 5) -> set[str]:
    t = norm(text)
    if len(t) < n:
        return {t} if t else set()
    return {t[i : i + n] for i in range(len(t) - n + 1)}


def ngram_containment(anchor: str, doc_ngrams: set[str], n: int = 5) -> float | None:
    """Graded containment of an anchor's character n-grams in the document.

    The transcription anchors are themselves OCR-derived and carry typos
    (e.g. Hindi "मेें" for "में", "क््ययाया"), so strict substring equality
    measures ground-truth noise rather than extraction fidelity. Containment
    stays 1.0 for an exact hit and decays smoothly for 1-2 character errors.
    """
    a = ngrams(anchor, n)
    if not a:
        return None
    return len(a & doc_ngrams) / len(a)


def score(text: str, truth: dict) -> dict:
    flat = norm(text)

    titles = [t["title"] for t in truth["topics"] if len(t["title"].strip()) >= 3]
    title_hits = sum(1 for t in titles if norm(t) in flat)

    # Probe anchors on their first 40 normalised chars: long enough to be specific,
    # short enough to survive line-wrap differences between engines.
    probes = []
    for t in truth["topics"]:
        a = norm(t["anchor"])
        if len(a) >= 8:
            probes.append(a[:40])
    anchor_hits = sum(1 for p in probes if p in flat)

    doc_ngrams = ngrams(text)
    ng_scores = [s for s in (ngram_containment(p, doc_ngrams) for p in probes) if s is not None]
    anchor_ng = round(sum(ng_scores) / len(ng_scores), 4) if ng_scores else None

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    dup_rate = 0.0
    if lines:
        dup_rate = round(1 - (len(set(lines)) / len(lines)), 4)

    dev_out = len(DEVANAGARI.findall(text))
    dev_truth = len(DEVANAGARI.findall(json.dumps(truth, ensure_ascii=False)))

    return {
        "chars": len(text),
        "heading_recall": round(title_hits / len(titles), 4) if titles else None,
        "n_titles": len(titles),
        "anchor_recall": round(anchor_hits / len(probes), 4) if probes else None,
        "anchor_ng5": anchor_ng,
        "n_anchors": len(probes),
        "dup_line_rate": dup_rate,
        "devanagari_out": dev_out,
        "devanagari_in_truth": dev_truth,
        "replacement_chars": text.count("\ufffd"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-stratum", type=int, default=2)
    ap.add_argument("--engines", default="pdfplumber,docling,opendataloader")
    ap.add_argument("--out", default="parser_benchmark.json")
    ap.add_argument("--limit", type=int, default=0, help="cap sample size (smoke test)")
    args = ap.parse_args()

    sys.path.insert(0, str(Path(__file__).resolve().parent))

    engines = [e.strip() for e in args.engines.split(",") if e.strip()]
    truth = build_truth_index()
    pdfs = build_pdf_index()
    sample = select_sample(truth, pdfs, args.per_stratum)
    if args.limit:
        sample = sample[: args.limit]
    print(
        f"truth={len(truth)} pdfs={len(pdfs)} matched_strata={len(sample)} engines={engines}\n"
    )
    if not sample:
        print("no (code, chapter) pairs matched — check filename conventions")
        return 1

    work = OUT_DIR / "_odl_tmp"
    out_path = OUT_DIR / args.out
    rows = []
    for i, item in enumerate(sample, 1):
        pdf: Path = item.pop("pdf")
        label = f"{item['code']}-{item['chapter']:02d} {item['language']}/{item['subject']}"
        print(f"[{i}/{len(sample)}] {label}", flush=True)
        row = {
            "code": item["code"],
            "chapter": item["chapter"],
            "class": item["class"],
            "subject": item["subject"],
            "language": item["language"],
            "pdf": str(pdf),
        }
        for name in engines:
            t_start = time.time()
            print(f"    -> {name} start", flush=True)
            try:
                text, meta = ENGINES[name](pdf, work)
                row[name] = {**score(text, item), **meta}
                print(
                    f"    {name:15s} head={row[name]['heading_recall']} "
                    f"anchor={row[name]['anchor_recall']} "
                    f"ng5={row[name]['anchor_ng5']} "
                    f"dup={row[name]['dup_line_rate']} "
                    f"s/pg={meta['s_per_page']} "
                    f"[{time.time() - t_start:.1f}s]",
                    flush=True,
                )
            except Exception as exc:  # noqa: BLE001
                row[name] = {"error": f"{type(exc).__name__}: {exc}"}
                print(
                    f"    {name:15s} FAILED {type(exc).__name__}: {exc} "
                    f"[{time.time() - t_start:.1f}s]",
                    flush=True,
                )
        rows.append(row)
        # Persist after every row so a crash or hang never loses completed work.
        out_path.write_text(
            json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8"
        )
        done_pct = round(100 * i / len(sample), 1)
        print(
            f"    == {done_pct}% complete ({i}/{len(sample)}) "
            f"elapsed={time.time() - RUN_T0:.0f}s",
            flush=True,
        )

    (OUT_DIR / args.out).write_text(
        json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8"
    )

    # Aggregate
    print("\n" + "=" * 86)
    print(
        f"{'engine':16s}{'head_rec':>10s}{'anch_exact':>11s}{'anch_ng5':>10s}"
        f"{'dup_rate':>10s}{'s/page':>9s}{'fails':>7s}"
    )
    print("-" * 86)
    for name in engines:
        ok = [r[name] for r in rows if "error" not in r.get(name, {"error": 1})]
        fails = len(rows) - len(ok)
        if not ok:
            print(f"{name:16s}{'n/a':>10s}")
            continue

        def avg(key):
            vals = [o[key] for o in ok if o.get(key) is not None]
            return sum(vals) / len(vals) if vals else float("nan")

        print(
            f"{name:16s}{avg('heading_recall'):>10.3f}{avg('anchor_recall'):>11.3f}"
            f"{avg('anchor_ng5'):>10.3f}{avg('dup_line_rate'):>10.3f}"
            f"{avg('s_per_page'):>9.3f}{fails:>7d}"
        )

    # Per-language split: the Hindi anchors are noisier than the English ones, so
    # strict and graded scores diverge there. Both are reported deliberately.
    print("\nBy language (anchor_exact / anchor_ng5 / head_rec):")
    for name in engines:
        for lang in ("en", "hi"):
            sel = [
                r[name]
                for r in rows
                if r["language"] == lang and "error" not in r.get(name, {"error": 1})
            ]
            if not sel:
                continue

            def a2(key):
                vals = [o[key] for o in sel if o.get(key) is not None]
                return sum(vals) / len(vals) if vals else float("nan")

            print(
                f"  {name:16s} {lang}  n={len(sel):<3d} "
                f"{a2('anchor_recall'):.3f} / {a2('anchor_ng5'):.3f} / {a2('heading_recall'):.3f}"
            )

    # Per-language Devanagari check: guards the "strip non-ASCII" anti-pattern.
    print("\nDevanagari retention (Hindi rows only):")
    for name in engines:
        hin = [
            r[name]
            for r in rows
            if r["language"] == "hi" and "error" not in r.get(name, {"error": 1})
        ]
        if hin:
            kept = sum(1 for o in hin if o.get("devanagari_out", 0) > 0)
            total = sum(o.get("devanagari_out", 0) for o in hin)
            print(f"  {name:16s} {kept}/{len(hin)} files retain Devanagari, {total} chars")
    print(f"\nwrote {OUT_DIR / args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
