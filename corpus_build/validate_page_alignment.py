"""Per-page alignment of OCR text against the source PDFs, with a correct witness.

The earlier failure was not in the OCR. It was in how this script built its
reference text.

`detect_legacy` classifies a page as legacy-encoded if any font on it looks
like a KrutiDev/Chanakya face. On English chapters a single decorative or
symbol font is enough to trip it: `aejm1-ch13` p4 carries `KrutiDev010`
alongside `Arial`, and `gecu1-ch12` p7 carries `Chanakya` alongside `Arial`.
Running `decode_legacy` over those pages transliterated perfectly good English
into Devanagari gibberish -- "Ancient Indian astronomers" became
"दबपमदज प्दकपंद ंेजतवदवउमतेए" -- and then scored the OCR against the garbage.
Three pages came out at exactly 0.000 because of it.

So the fix is to stop trusting detection on its own. The manifest records each
chapter's language authoritatively, and that governs: a Hindi page is decoded,
an English page never is. Within a Hindi page, the raw and decoded variants are
compared on Devanagari density and the more plausible one wins, which handles
pages that are mixed.

A second problem is that some pages are not extractable at all. Where a
multi-column layout defeats PyMuPDF's line grouping, the text arrives
interleaved one character per line -- `aejm1-ch13` p4 yields
`e i g h t t s f i v e h n t e`, which is "eight" and "fifteen" shredded. No
alignment method can match that, and its absence says nothing about the OCR,
so such pages are recorded as `unreadable-layer` and excluded from scoring
rather than counted as failures.

Scoring is otherwise unchanged: each readable page's character 4-gram content
is matched against the whole OCR text, and the chapter is judged by its WORST
page, so one garbled page cannot hide inside an average and a dropped page
cannot be diluted. Numbers are reported, not scored, because a 4-gram
neighbourhood already covers the digits around a number and arithmetic still
needs the page itself.
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "pdf_ingest"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import fitz  # noqa: E402

from ncert_extract import decode_legacy, detect_legacy, font_type_for  # noqa: E402

MANIFEST = Path(r"D:\wt\tagfix\corpus_build\legacy_ocr_manifest.json")
OUT_JSON = Path(r"D:\wt\tagfix\corpus_build\pdf_page_alignment.json")
OUT_MD = Path(r"D:\wt\tagfix\corpus_build\pdf_page_alignment.md")

N = 4
PAGE_MIN = 0.60
WARN = 0.75
MIN_PAGE_CHARS = 120

_DEVANAGARI = re.compile(r"[\u0900-\u097F]")
_ALPHA = re.compile(r"[\w\u0900-\u097F]+", re.UNICODE)
_MARKS = re.compile(r"[\u0900-\u0903\u093A-\u094F\u0951-\u0957\u0962\u0963"
                    r"\u200C\u200D]")


def devanagari_ratio(text: str) -> float:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if _DEVANAGARI.match(c)) / len(letters)


def is_scrambled(text: str) -> bool:
    """True when multi-column layout shredded the text into single characters."""
    tokens = _ALPHA.findall(text)
    if len(tokens) < 40:
        return False
    singles = sum(1 for t in tokens if len(t) == 1)
    return singles / len(tokens) > 0.25


def page_text(page, language: str) -> tuple[str, str]:
    """Readable text for one page, plus how it was obtained.

    The legacy layout is chosen from the fonts actually embedded on the page,
    not assumed. `krutidev` and `walkman_chanakya` share an ASCII layout while
    `chanakya` is a different one, and decoding one with the other produces
    garbage.
    """
    raw = page.get_text()
    if not language.startswith("hi"):
        return raw, "raw"

    spans: list[tuple[str, str]] = []
    for block in page.get_text("dict").get("blocks", []):
        for line in block.get("lines", []):
            ls = line.get("spans", [])
            text = "".join(s.get("text", "") for s in ls)
            if text.strip():
                spans.append((text, ls[0].get("font", "") if ls else ""))
    fonts = [f for _, f in spans]
    if not spans or not detect_legacy(spans, fonts):
        return raw, "raw"

    layout = None
    for f in fonts:
        layout = font_type_for(f) or layout
    decoded = decode_legacy(raw, font_type=layout)
    # Only accept the decode if it actually looks more Devanagari than the raw
    # text, so a stray legacy font on an otherwise clean page cannot corrupt it.
    if devanagari_ratio(decoded) > devanagari_ratio(raw) + 0.10:
        return decoded, f"decoded:{layout}"
    return raw, "raw"


def skeleton(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = _MARKS.sub("", text)
    return re.sub(r"\s+", "", text.casefold())


def grams(text: str, n: int = N) -> set[str]:
    if len(text) < n:
        return {text} if text else set()
    return {text[i:i + n] for i in range(len(text) - n + 1)}


def body_of(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4:]
    return text


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    results = []
    print(f"{'chapter':<13} {'pg':>3} {'scored':>7} {'worst':>7} {'mean':>7} "
          f"{'low':>4}  verdict   worst pages")
    print("-" * 96)

    for m in sorted(manifest, key=lambda x: x["label"]):
        ch, lang = m["label"], m["language"]
        ocr_g = grams(skeleton(body_of(Path(m["corpus_out"]))))
        ocr_raw = body_of(Path(m["corpus_out"]))
        ocr_nums = set(re.findall(r"\d+", ocr_raw))

        doc = fitz.open(m["pdf"])
        rows = []
        for i, page in enumerate(doc, start=1):
            text, how = page_text(page, lang)
            sk = skeleton(text)
            if len(sk) < MIN_PAGE_CHARS:
                rows.append({"page": i, "score": None, "chars": len(sk),
                             "note": "skipped-short", "source": how})
                continue
            if is_scrambled(text):
                rows.append({"page": i, "score": None, "chars": len(sk),
                             "note": "unreadable-layer", "source": how})
                continue
            pg = grams(sk)
            row = {
                "page": i, "chars": len(sk), "source": how,
                "score": round(len(pg & ocr_g) / len(pg), 4) if pg else 0.0,
                "missing_numbers": sorted(
                    n for n in set(re.findall(r"\d+", text))
                    if len(n) >= 2 and n not in ocr_nums),
            }
            rows.append(row)
        doc.close()

        scored = [r for r in rows if r["score"] is not None]
        skipped = [r for r in rows if r["score"] is None]
        if not scored:
            results.append({"chapter": ch, "verdict": "no-readable-pages",
                            "page_count": len(rows), "pages": rows})
            print(f"{ch:<13} {len(rows):>3} {0:>7} {'-':>7} {'-':>7} "
                  f"{0:>4}  no-readable-pages")
            continue

        scores = [r["score"] for r in scored]
        worst, mean = min(scores), sum(scores) / len(scores)
        below = [r for r in scored if r["score"] < PAGE_MIN]
        warn = [r for r in scored if PAGE_MIN <= r["score"] < WARN]
        verdict = ("page-failure" if below else
                   "review" if warn else "verified")

        results.append({
            "chapter": ch, "language": lang, "page_count": len(rows),
            "pages_scored": len(scored), "pages_skipped": len(skipped),
            "worst_page_score": round(worst, 4),
            "mean_page_score": round(mean, 4),
            "below_threshold": len(below), "warn_pages": len(warn),
            "verdict": verdict, "pages": rows,
        })
        worst_list = ", ".join(
            f"p{r['page']}={r['score']}" for r in
            sorted(scored, key=lambda r: r["score"])[:4])
        print(f"{ch:<13} {len(rows):>3} {len(scored):>7} {worst:>7.3f} "
              f"{mean:>7.3f} {len(below):>4}  {verdict:<11} {worst_list}")

    OUT_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=1),
                        encoding="utf-8")

    tally = Counter(r["verdict"] for r in results)
    lines = ["# Per-page alignment of OCR text against source PDFs", "",
             "Each readable page's character 4-gram content is matched against "
             "the whole OCR text. A chapter is judged by its WORST page, so one "
             "garbled page cannot hide in an average.", "",
             "The manifest language governs decoding. A Hindi page is decoded "
             "only when decoding raises its Devanagari density; an English page "
             "is never decoded, because a single stray `KrutiDev010` or "
             "`Chanakya` font otherwise gets transliterated into gibberish and "
             "scored against the OCR. Pages shredded into one character per line "
             "by column detection are recorded as `unreadable-layer` and "
             "excluded.", "",
             f"Thresholds: worst page >= {WARN} is `verified`, {PAGE_MIN}-{WARN} "
             f"is `review`, below {PAGE_MIN} is `page-failure`.", "",
             "| chapter | pages | scored | skipped | worst page | mean | below | "
             "warn | verdict |", "|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        if r["verdict"] == "no-readable-pages":
            lines.append(f"| {r['chapter']} | {len(r['pages'])} | 0 | "
                         f"{len(r['pages'])} | - | - | - | - | no-readable-pages |")
            continue
        lines.append(
            f"| {r['chapter']} | {r['page_count']} | {r['pages_scored']} | "
            f"{r['pages_skipped']} | {r['worst_page_score']} | "
            f"{r['mean_page_score']} | {r['below_threshold']} | "
            f"{r['warn_pages']} | {r['verdict']} |")
    lines += ["", f"Tally: {dict(tally)}", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("-" * 96)
    print(f"tally: {dict(tally)}")
    for r in results:
        if r["verdict"] in ("page-failure", "review"):
            print(f"  {r['chapter']:<13} {r['verdict']:<12} "
                  f"worst={r['worst_page_score']} below={r['below_threshold']} "
                  f"pages=" + ",".join(
                      f"p{x['page']}:{x['score']}" for x in r["pages"]
                      if x["score"] is not None and x["score"] < WARN))
    print(f"\nwrote {OUT_JSON.name} and {OUT_MD.name}")


if __name__ == "__main__":
    main()
