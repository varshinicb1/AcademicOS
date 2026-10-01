"""Validate the 38 OCR'd chapters against the source PDFs, independently.

The OCR text came from Sarvam Vision reading page images, so checking it against
that same OCR would be circular. The PDFs also carry a text layer, which gives an
independent witness: for the six English chapters it is plain text, and for the
32 Hindi chapters it is legacy KrutiDev/Walkman-Chanakya905 8-bit code that
`ncert_extract.decode_legacy` maps back to Devanagari.

Three things this first got wrong, and why they are fixed the way they are:

1. Decoding the whole document at once. `detect_legacy` asks whether a legacy
   font is embedded AND the text has no real Devanagari. Three English chapters
   (`aejm1-ch13`, `gecu1-ch12`, `gepr1-ch02`) embed a legacy-named font
   somewhere -- a stray glyph, a symbol -- which is true of plenty of clean
   documents, and applying the table to their whole text turned English into
   `gपससन`. Decoding is now per page, and a page is only decoded when that
   page's own text looks legacy. Mixed documents then come out right on both
   sides instead of being mangled wholesale.

2. Comparing words with matras attached. `decode_legacy` is context-free and
   character-level, so it puts the pre-base i-matra on the wrong side of its
   consonant: the PDF layer yields `अितिथ` and `अधययन` where the OCR
   correctly reads `अतिथि` and `अध्ययन`. Judging the OCR against a decoder that
   is known to be wrong in exactly that way scores a correct chapter as a
   mismatch -- which is what happened to 30 chapters on the first run.
   Comparison therefore runs on a canonical form with vowel signs, matras and
   nukta removed, so the two sides are compared on consonants and structure.

3. Counting blank underscores and page furniture. The PDF layer carries
   `______________` fill-in rules and the OCR carries slide labels like
   `0124ch13`; neither is a content word.

The result is advisory input for `quote_exact`, not an automatic flip. A high
score says the OCR is faithful enough to quote; it cannot prove the absence of
every single-character error, because a text layer is not a pixel-level ground
truth and Vision OCR is not the only thing that could be wrong.
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "pdf_ingest"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import fitz  # noqa: E402

from ncert_extract import decode_legacy, detect_legacy  # noqa: E402

MANIFEST = Path(r"D:\wt\tagfix\corpus_build\legacy_ocr_manifest.json")
OUT_JSON = Path(r"D:\wt\tagfix\corpus_build\pdf_validation.json")
OUT_MD = Path(r"D:\wt\tagfix\corpus_build\pdf_validation.md")

# Coverage = share of OCR content words present in the PDF text layer.
# Reciprocal = the reverse, which catches a dropped or hallucinated page.
MIN_COVERAGE = 0.90
MIN_RECIPROCAL = 0.75
REVIEW_MARGIN = 0.08

WORD = re.compile(r"[\wऀ-ॿ]+", re.UNICODE)

# Independent vowel signs, matras, anusvara/visarga-ish marks, nukta, and
# ZWJ/ZWNJ. Stripping these makes the comparison blind to the i-matra placement
# error the legacy decoder is known to make, while keeping every consonant.
_MARKS = re.compile(r"[\u0900-\u0903\u093A-\u094F\u0951-\u0957\u0962\u0963"
                    r"\u200C\u200D]")

STOP = {
    "the", "a", "an", "and", "or", "of", "to", "in", "is", "are", "was",
    "were", "for", "on", "with", "as", "at", "by", "be", "it", "its", "this",
    "that", "from", "we", "you", "they", "he", "she", "not", "but", "have",
    "has", "had", "will", "can", "all", "one", "two", "our", "your", "their",
}


def canonical(text: str) -> list[str]:
    """Content words, matra-stripped, furniture and short noise removed."""
    text = unicodedata.normalize("NFC", text)
    out: list[str] = []
    for w in WORD.findall(text):
        w = w.casefold()
        if "_" in w or set(w) <= {"_", "-", "."}:
            continue
        w = _MARKS.sub("", w)
        if not w or w in STOP:
            continue
        # Slide labels the OCR pipeline injects, e.g. "0124ch13".
        if re.fullmatch(r"\d+ch\d+", w):
            continue
        if len(w) < 2:
            continue
        out.append(w)
    return out


def pdf_layer(pdf: Path) -> tuple[str, str | None]:
    """Document text with legacy decoding applied per page, not globally.

    A page is decoded only when that page's own text fails the legacy test. A
    document that embeds a legacy font for one stray glyph therefore keeps its
    real text, while a page that is genuinely 8-bit encoded gets decoded.
    """
    doc = fitz.open(pdf)
    parts: list[str] = []
    saw_legacy: str | None = None
    for page in doc:
        d = page.get_text("dict")
        lines: list[tuple] = []
        fonts: list[str] = []
        for block in d.get("blocks", []):
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                text = "".join(s.get("text", "") for s in spans)
                if not text.strip():
                    continue
                font = spans[0].get("font", "") if spans else ""
                lines.append((text, font))
                fonts.append(font)
        found = detect_legacy(lines, fonts)
        raw = page.get_text()
        if found:
            saw_legacy = saw_legacy or found
            raw = decode_legacy(raw)
        parts.append(raw)
    doc.close()
    return "\n".join(parts), saw_legacy


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
    print(f"{'chapter':<13} {'lg':<3} {'font':<10} {'ocr_w':>6} {'pdf_w':>6} "
          f"{'cover':>7} {'recip':>7}  verdict")
    print("-" * 80)

    for m in sorted(manifest, key=lambda x: x["label"]):
        ch = m["label"]
        pdf = Path(m["pdf"])
        ocr_body = body_of(Path(m["corpus_out"]))

        if not pdf.exists():
            results.append({"chapter": ch, "verdict": "pdf-missing",
                            "pdf": str(pdf)})
            print(f"{ch:<13} {m['language'][:2]:<3} {'MISSING':<10}")
            continue

        try:
            layer, legacy = pdf_layer(pdf)
        except Exception as exc:  # noqa: BLE001 - report, do not abort the sweep
            results.append({"chapter": ch, "verdict": f"pdf-error: {exc}"})
            print(f"{ch:<13} {m['language'][:2]:<3} {'ERROR':<10} {exc}")
            continue

        ocr_set = set(canonical(ocr_body))
        pdf_set = set(canonical(layer))
        # Vocabulary membership, not occurrence counts. A text layer repeats
        # every running head on every page while the OCR pipeline collapses them,
        # so a multiset intersection reports "missing" words that are present:
        # on the first multiset run "astrophysics" looked absent from
        # gecu1-ch12 when it occurs in the OCR. Repetition-count differences
        # measure extraction style, not fidelity; membership measures whether
        # the OCR says what the PDF says.
        ocr_c, pdf_c = Counter(ocr_set), Counter(pdf_set)
        ocr_n, pdf_n = len(ocr_set), len(pdf_set)

        if not ocr_n or not pdf_n:
            results.append({"chapter": ch, "verdict": "empty-side",
                            "ocr_words": ocr_n, "pdf_words": pdf_n})
            print(f"{ch:<13} {m['language'][:2]:<3} "
                  f"{(legacy or 'native')[:10]:<10} {ocr_n:>6} {pdf_n:>6}  EMPTY")
            continue

        matched = len(ocr_set & pdf_set)
        coverage = matched / ocr_n
        reciprocal = matched / pdf_n

        if coverage >= MIN_COVERAGE and reciprocal >= MIN_RECIPROCAL:
            verdict = "verified"
        elif coverage >= MIN_COVERAGE - REVIEW_MARGIN:
            verdict = "review"
        else:
            verdict = "mismatch"

        results.append({
            "chapter": ch, "language": m["language"], "pdf": str(pdf),
            "legacy_font": legacy, "ocr_words": ocr_n, "pdf_words": pdf_n,
            "coverage": round(coverage, 4), "reciprocal": round(reciprocal, 4),
            "verdict": verdict,
            "only_in_ocr_sample": sorted(w for w in (ocr_c - pdf_c) if len(w) > 2)[:20],
            "only_in_pdf_sample": sorted(w for w in (pdf_c - ocr_c) if len(w) > 2)[:20],
        })
        print(f"{ch:<13} {m['language'][:2]:<3} {(legacy or 'native')[:10]:<10} "
              f"{ocr_n:>6} {pdf_n:>6} {coverage:>7.3f} {reciprocal:>7.3f}  "
              f"{verdict}")

    OUT_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=1),
                        encoding="utf-8")

    tally = Counter(r["verdict"] for r in results)
    lines = [
        "# OCR vs source-PDF validation", "",
        "Coverage = share of OCR content words present in the PDF text layer. "
        "Reciprocal = the reverse. Both are fuzzy: the legacy 8-bit font decoder "
        "is context-free, and OCR and a text layer differ on line breaks, "
        "hyphenation and running heads. Comparison runs on matra-stripped words "
        "so that the decoder's known i-matra misplacement is not charged to the "
        "OCR.", "",
        f"Thresholds: coverage >= {MIN_COVERAGE} and reciprocal >= "
        f"{MIN_RECIPROCAL} marks `verified`; within {REVIEW_MARGIN} of the "
        f"coverage floor marks `review`.", "",
        "| chapter | lang | font | ocr words | pdf words | coverage | "
        "reciprocal | verdict |", "|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {r['chapter']} | {r.get('language','')} | "
            f"{r.get('legacy_font') or 'native'} | {r.get('ocr_words','-')} | "
            f"{r.get('pdf_words','-')} | {r.get('coverage','-')} | "
            f"{r.get('reciprocal','-')} | {r['verdict']} |")
    lines += ["", f"Tally: {dict(tally)}", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("-" * 80)
    print(f"tally: {dict(tally)}")
    print(f"wrote {OUT_JSON.name} and {OUT_MD.name}")


if __name__ == "__main__":
    main()
