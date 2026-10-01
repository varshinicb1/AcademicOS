"""Find Vision narration in the OCR outputs, in both output languages.

Measured, not assumed. Vision describes each image in the language it thinks the
page is written in, so the narration is English for the English books
("*This image contains a drawing of a plant...*") and Hindi for the Hindi ones
("*यह चित्र एक गुलाबी रंग की तस्वीर है...*"). An English-only detector finds 38
lines across 38 files and misses every Hindi one, which is why the Hindi books
measure 100% Devanagari.

Italic markup cannot be the test on its own: the NCERT Hindi books set real
passages in italics too (jhsp1-ch01 has italic verse). So two rules are measured
side by side and the difference is reported:

  loose  - line begins with an image-reference phrase, either language
  strict - the same, and the line is wholly wrapped in *...*

The audit file lists every candidate so the rule can be checked against real
lines before anything is deleted.
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OCR_DIR = Path(r"D:\wt\tagfix\corpus_build\sarvam_ocr")
AUDIT = Path(r"D:\wt\tagfix\corpus_build\ocr_narration_audit.md")

# Openers that mean "Vision is now describing a picture", in both languages.
# Ordered longest-first so the alternatives do not shadow one another.
NARRATION_OPENER = re.compile(
    r"^\s*\*?\s*(?:"
    # English
    r"this\s+(?:image|photo|picture|diagram|figure|illustration|page|chart|graph|map)\b"
    r"|the\s+(?:image|photo|picture|diagram|figure|illustration)\b"
    r"|an?\s+(?:image|photo|picture|diagram|figure)\s+(?:of|showing|depicting)\b"
    r"|image\s+(?:of|shows|showing|depicts|contains)\b"
    r"|(?:the\s+)?(?:picture|photograph)\s+(?:of|shows|showing)\b"
    # Hindi
    r"|यह\s+(?:चित्र|छवि|तस्वीर|चित्रण|पृष्ठ|रेखाचित्र|मानचित्र)\b"
    r"|इस\s+(?:चित्र|छवि|तस्वीर|चित्रण|पृष्ठ)\b"
    r"|उपरोक्त\s+(?:चित्र|छवि|तस्वीर|चित्रण)\b"
    r"|(?:चित्र|छवि|तस्वीर|चित्रण)\s+में\b"
    r"|(?:ऊपर|नीचे|बाईं|दाईं|दाएँ)\s+(?:दिया|दिए|दिखाया)\s+गया\s+(?:चित्र|चित्रण)\b"
    r")",
    re.I,
)

# Narration often trails an explicit "there is no text" verdict.
NO_TEXT_TAIL = re.compile(
    r"(इसमें\s+कोई\s+पाठ\s+नहीं|इस\s+चित्र\s+में\s+कोई\s+पाठ\s+नहीं"
    r"|इसमें\s+कोई\s+लिखित\s+पाठ\s+नहीं|no\s+text\s+in\s+the\s+image"
    r"|not\s+text|no\s+text\s+to\s+transcribe)",
    re.I,
)

ITALIC_WRAP = re.compile(r"^\s*\*.*\*\s*$")


def classify(line: str) -> tuple[bool, bool]:
    """Return (loose, strict) narration verdicts for one line."""
    if not line.strip():
        return False, False
    loose = bool(NARRATION_OPENER.match(line) or NO_TEXT_TAIL.search(line))
    strict = loose and bool(ITALIC_WRAP.match(line))
    return loose, strict


def main() -> None:
    files = sorted(OCR_DIR.glob("*.md"))
    out = ["# Vision narration audit\n"]
    grand_loose = grand_strict = 0
    summary = []

    for path in files:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        loose_hits, strict_hits = [], []
        for i, line in enumerate(lines, 1):
            loose, strict = classify(line)
            if loose:
                loose_hits.append((i, line, strict))
            if strict:
                strict_hits.append((i, line))

        grand_loose += len(loose_hits)
        grand_strict += len(strict_hits)
        loose_chars = sum(len(l) for _, l, _ in loose_hits)
        strict_chars = sum(len(l) for _, l in strict_hits)
        total_chars = sum(len(l) for l in lines)
        summary.append((path.stem, len(loose_hits), len(strict_hits),
                        loose_chars, strict_chars, total_chars))

        out.append(f"\n## {path.stem}\n")
        out.append(f"loose={len(loose_hits)} strict={len(strict_hits)} "
                   f"loose_chars={loose_chars} strict_chars={strict_chars} "
                   f"of {total_chars} ({loose_chars / total_chars:.1%} / "
                   f"{strict_chars / total_chars:.1%})\n")
        out.append("| line | strict | text |")
        out.append("|---:|---|---|")
        for i, line, strict in loose_hits[:60]:
            text = line.strip().replace("|", "\\|")
            out.append(f"| {i} | {'y' if strict else 'n'} | {text[:180]} |")
        if len(loose_hits) > 60:
            out.append(f"| ... | | {len(loose_hits) - 60} more |")

    out.insert(1, "## Summary\n")
    out.insert(2, "| file | loose | strict | loose_chars | strict_chars | file_chars |")
    out.insert(3, "|---|---:|---:|---:|---:|---:|")
    for name, lo, st, lc, sc, tc in summary:
        out.insert(4, "")
        out.insert(5, f"| {name} | {lo} | {st} | {lc} | {sc} | {tc} |")

    AUDIT.write_text("\n".join(out) + "\n", encoding="utf-8")

    print(f"{'file':<14} {'loose':>5} {'strict':>6} {'loose%':>7} {'strict%':>8}")
    for name, lo, st, lc, sc, tc in summary:
        print(f"{name:<14} {lo:>5} {st:>6} {lc / tc:>6.1%} {sc / tc:>7.1%}")
    print()
    print(f"TOTAL loose hits   : {grand_loose}")
    print(f"TOTAL strict hits  : {grand_strict}")
    print(f"loose but not strict (needs review): {grand_loose - grand_strict}")
    print(f"audit: {AUDIT}")


if __name__ == "__main__":
    main()
