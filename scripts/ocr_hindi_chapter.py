"""Read class 10 Hindi chapters by OCR, one page at a time, into a cache outside the repository.

    python scripts/ocr_hindi_chapter.py --book jhks1 --chapter 1
    python scripts/ocr_hindi_chapter.py --book jhks1 --all --max-pages 130
    python scripts/ocr_hindi_chapter.py --book jhsp1 --all --dry-run     # how many pages, no spend

Why: these books' PDF text layer is a legacy font and not Hindi at all (corpus/hindi_ocr.py).
Each page is sent to Sarvam Vision (the provider production is approved for) with the project's
own key, as its own one-page job, so the page number is exact and a failure costs one page.

Spend: Sarvam bills per page. A page already in the cache is never sent again, `--max-pages`
stops the run before it goes over, and the pages sent are added up in <cache>/_ledger.json so a
total can be reported. The key is read by assessment/vision.py from the environment
(ACOS_LLM_API_KEY / SARVAM_API_KEY, or config/secrets.env's value exported by the caller) and is
never printed.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pymupdf  # noqa: E402

from academicos.corpus import hindi_ocr  # noqa: E402

BOOKS = Path(r"C:\Users\varsh\OneDrive\Documents\Sarvam\ncert-dataset\textbooks\chapters")


def chapter_files(book: str) -> list[tuple[int, Path]]:
    out = []
    for p in sorted((BOOKS / book).glob(f"{book}*.pdf")):
        tail = p.stem[len(book):]
        if tail.isdigit():
            out.append((int(tail), p))
    return out


def ledger(cache: Path) -> dict:
    path = cache / "_ledger.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {"pages": 0, "chapters": {}}


def save_ledger(cache: Path, data: dict) -> None:
    (cache / "_ledger.json").write_text(json.dumps(data, indent=1, sort_keys=True), encoding="utf-8")


def read_chapter(book: str, number: int, pdf: Path, cache: Path, budget: int | None) -> int:
    """OCR the pages of one chapter not yet cached. Returns the pages sent."""
    from academicos.assessment import vision

    out = hindi_ocr.cache_path(book, number, cache)
    have = json.loads(out.read_text(encoding="utf-8")) if out.is_file() else {"pages": []}
    done = {p["page"] for p in have["pages"]}
    sent = 0
    with pymupdf.open(pdf) as doc:
        for index in range(doc.page_count):
            page_no = index + 1
            if page_no in done:
                continue
            if budget is not None and sent >= budget:
                print(f"{book}-{number:02d}: stopped at the page budget after {sent} pages")
                break
            with tempfile.TemporaryDirectory() as tmp:
                one = Path(tmp) / f"{book}{number:02d}_p{page_no:02d}.pdf"
                single = pymupdf.open()
                single.insert_pdf(doc, from_page=index, to_page=index)
                single.save(one)
                single.close()
                text = vision.extract(one, language="hi-IN", output_format="md")
            sent += 1
            have["pages"].append({"page": page_no, "lines": hindi_ocr.clean(text)})
            have["pages"].sort(key=lambda p: p["page"])
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(have, ensure_ascii=False, indent=1), encoding="utf-8")
    return sent


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--book", required=True)
    ap.add_argument("--chapter", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--max-pages", type=int, default=150, help="stop before sending more than this many pages")
    ap.add_argument("--cache", type=Path, default=hindi_ocr.DEFAULT_CACHE)
    ap.add_argument("--dry-run", action="store_true", help="count the pages that would be sent; send none")
    args = ap.parse_args()
    if not args.chapter and not args.all:
        ap.error("--chapter or --all is required")
    files = chapter_files(args.book)
    if args.chapter:
        files = [(n, p) for n, p in files if n == args.chapter]
    if not files:
        raise SystemExit(f"no chapter PDFs for {args.book}")

    todo = 0
    for number, pdf in files:
        with pymupdf.open(pdf) as doc:
            cached = hindi_ocr.load(args.book, number, args.cache)
            have = len({p for p, _ in cached or []})
            todo += max(0, doc.page_count - have)
    print(f"{args.book}: {len(files)} chapter(s), {todo} page(s) not yet read")
    if args.dry_run:
        return 0

    args.cache.mkdir(parents=True, exist_ok=True)
    state = ledger(args.cache)
    remaining = args.max_pages
    for number, pdf in files:
        if remaining <= 0:
            print(f"page budget ({args.max_pages}) used; stopping before {args.book}-{number:02d}")
            break
        sent = read_chapter(args.book, number, pdf, args.cache, remaining)
        remaining -= sent
        state["pages"] += sent
        state["chapters"][f"{args.book}-{number:02d}"] = state["chapters"].get(f"{args.book}-{number:02d}", 0) + sent
        save_ledger(args.cache, state)
        cached = hindi_ocr.load(args.book, number, args.cache) or []
        share = hindi_ocr.devanagari_share(" ".join(l for _, l in cached))
        print(f"{args.book}-{number:02d}: sent {sent} page(s), {len(cached)} lines, {share:.0%} Devanagari")
    print(f"pages sent to Sarvam in total so far: {state['pages']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
