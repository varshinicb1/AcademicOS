"""Check whether the stripped English books contain real English body text.

The strip removed a lot of Devanagari from the six `en-IN` books, which is only
consistent with one of two things: Vision narrated English pages in Hindi (fine,
that text is removed), or the pages were sent through the Hindi OCR path and the
body text is Hindi too (not fine, the book needs re-running in English). The
difference decides whether another OCR spend is needed, so it is measured on the
body after stripping rather than assumed from the manifest.
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLEAN = Path(r"D:\wt\tagfix\corpus_build\sarvam_ocr_clean")
REPORT = Path(r"D:\wt\tagfix\corpus_build\ocr_english_quality.md")
ENGLISH = ["aejm1-ch13", "fegp1-ch10", "fepr1-ch05", "gecu1-ch12", "gegp1-ch04",
           "gepr1-ch02"]

# A run of Devanagari long enough to be a sentence rather than a stray glyph.
DEV_SENTENCE = re.compile(r"[\u0900-\u097F](?:[\u0900-\u097F\s।,.:;!?\"'()\-]{12,})")
DEV_WORD = re.compile(r"[\u0900-\u097F]{2,}")


def strip_markup(line: str) -> str:
    line = re.sub(r"^#+\s*", "", line)
    line = re.sub(r"[*_`>]", "", line)
    return line.strip()


def analyse(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    body = [strip_markup(l) for l in lines]
    body = [l for l in body if len(l) > 30]
    text = "\n".join(body)

    latin_words = re.findall(r"[A-Za-z]{2,}", text)
    dev_words = DEV_WORD.findall(text)
    dev_sentences = DEV_SENTENCE.findall(text)
    # A body line that is mostly Devanagari is Hindi prose, not an English book.
    hindi_lines = sum(
        1 for l in body
        if len(DEV_WORD.findall(l)) >= 4
        and len(DEV_WORD.findall(l)) > len(re.findall(r"[A-Za-z]{2,}", l))
    )
    return {
        "file": path.name,
        "body_chars": len(text),
        "body_lines": len(body),
        "latin_words": len(latin_words),
        "dev_words": len(dev_words),
        "dev_sentences": len(dev_sentences),
        "hindi_lines": hindi_lines,
        "latin_share": (len(latin_words)
                        / (len(latin_words) + len(dev_words))
                        if (latin_words or dev_words) else 0.0),
        "samples": body[:6],
    }


def main() -> None:
    out = ["# English-book body quality after narration stripping\n",
           "If these books were OCR'd through the Hindi path, `hindi_lines` is high",
           "and the body is Hindi rather than English.\n"]
    print(f"{'file':<16} {'body_chars':>10} {'lines':>6} {'latin':>7} {'dev':>6} "
          f"{'dev_sent':>8} {'hindi_ln':>8} {'latin%':>7}")
    for name in ENGLISH:
        path = CLEAN / f"{name}.md"
        if not path.exists():
            print(f"{name:<16} MISSING")
            continue
        r = analyse(path)
        out.append(f"\n## {r['file']}\n")
        out.append(
            f"body_chars={r['body_chars']} lines={r['body_lines']} "
            f"latin_words={r['latin_words']} dev_words={r['dev_words']} "
            f"dev_sentences={r['dev_sentences']} hindi_lines={r['hindi_lines']} "
            f"latin_share={r['latin_share']:.1%}\n"
        )
        out.append("body samples:")
        for s in r["samples"]:
            out.append(f"- {s[:200]}")
        print(f"{r['file']:<16} {r['body_chars']:>10} {r['body_lines']:>6} "
              f"{r['latin_words']:>7} {r['dev_words']:>6} {r['dev_sentences']:>8} "
              f"{r['hindi_lines']:>8} {r['latin_share']:>6.0%}")

    REPORT.write_text("\n".join(out) + "\n", encoding="utf-8")
    print()
    print(f"report: {REPORT}")


if __name__ == "__main__":
    main()
