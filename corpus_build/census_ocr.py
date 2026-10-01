"""Census the 38 Sarvam OCR outputs and characterise the Vision narration.

Two constraints shape this script:

* The console pipe mangles non-ASCII, so anything containing Devanagari is
  written to a UTF-8 report and only ASCII-safe summaries are printed here.
  Reading these files with `Get-Content` and eyeballing the output shows `?????`
  for perfectly good Hindi and is how a clean corpus gets mistaken for a broken
  one.
* The narration is whatever Sarvam Vision decided to say about each image, so it
  is counted by pattern across the whole set before anything is stripped. A
  cleaner that removes text it should not is worse than no cleaner, so the goal
  here is evidence, not deletion.
"""
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OCR_DIR = Path(r"D:\wt\tagfix\corpus_build\sarvam_ocr")
REPORT = Path(r"D:\wt\tagfix\corpus_build\ocr_census.md")

# Line-level patterns that are page furniture or Vision commentary rather than
# textbook content. Each is counted before use; anything not seen in the census
# does not belong in the stripper.
PATTERNS = {
    "qr_code_note": re.compile(r"this image contains a qr code", re.I),
    "reprint_page": re.compile(r"^\s*reprint\s+\d{4}\s*-\s*\d{2}\s*$", re.I),
    "page_rule": re.compile(r"^\s*-{3,}\s*$"),
    "bare_page_code": re.compile(r"^\s*\d{3,4}\s*ch\s*\d{1,2}\s*$", re.I),
    "this_image_shows": re.compile(r"\bthis (image|photo|picture|diagram|figure|page)\b", re.I),
    "the_image": re.compile(r"^\s*the image\b", re.I),
    "image_of": re.compile(r"\bimage (of|shows|depicts|contains)\b", re.I),
    "no_text": re.compile(r"\b(no text|not text|without text|blank)\b", re.I),
    "illustration": re.compile(r"\b(illustration|photograph|icon|logo)\b", re.I),
    "table_tag_open": re.compile(r"^\s*<table>\s*$", re.I),
    "table_tag_close": re.compile(r"^\s*</table>\s*$", re.I),
    "html_tag": re.compile(r"</?[a-zA-Z][^>]*>"),
}


def devanagari_ratio(text: str) -> float:
    if not text:
        return 0.0
    dev = sum(1 for ch in text if 0x0900 <= ord(ch) <= 0x097F)
    return dev / len(text)


def main() -> None:
    files = sorted(OCR_DIR.glob("*.md"))
    lines_out: list[str] = []
    totals = Counter()
    per_file: list[dict] = []

    lines_out.append("# Sarvam OCR census\n")
    lines_out.append(f"files: {len(files)}\n")
    lines_out.append("| file | bytes | chars | devanagari% | U+FFFD | '?' |")
    lines_out.append("|---|---:|---:|---:|---:|---:|")

    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        ffff = text.count("\ufffd")
        qmark = text.count("?")
        ratio = devanagari_ratio(text)

        counts = Counter()
        narration_lines = []
        for line in text.splitlines():
            for name, rx in PATTERNS.items():
                if rx.search(line):
                    counts[name] += 1
                    if name not in ("page_rule",):
                        narration_lines.append(line)
                    break

        totals.update(counts)
        per_file.append({
            "file": path.name,
            "chars": len(text),
            "ratio": ratio,
            "counts": dict(counts),
        })

        lines_out.append(
            f"| {path.name} | {len(text.encode('utf-8'))} | {len(text)} | "
            f"{ratio:.1%} | {ffff} | {qmark} |"
        )

    lines_out.append("\n## Pattern totals across all files\n")
    lines_out.append("| pattern | lines matched |")
    lines_out.append("|---|---:|")
    for name, _ in PATTERNS.items():
        lines_out.append(f"| {name} | {totals.get(name, 0)} |")

    # Everything that looks like furniture or commentary, in context, so the
    # stripper's rules can be checked against real lines.
    sample_block: list[str] = ["\n## Sample lines per pattern (first 4 each)\n"]
    for name, rx in PATTERNS.items():
        found = []
        for path in files:
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                if rx.search(line):
                    found.append(f"{path.name}: {line.strip()[:110]}")
                    if len(found) >= 4:
                        break
            if len(found) >= 4:
                break
        sample_block.append(f"\n### {name}\n")
        sample_block.extend(f"- {line}" for line in found)

    REPORT.write_text("\n".join(lines_out) + "\n" + "\n".join(sample_block) + "\n",
                      encoding="utf-8")

    # ASCII-safe console summary.
    print(f"files analysed      : {len(files)}")
    print(f"report              : {REPORT}")
    print()
    print("pattern line totals (whole set):")
    for name, _ in PATTERNS.items():
        print(f"  {name:<18} {totals.get(name, 0):>7}")
    print()
    total_chars = sum(f["chars"] for f in per_file)
    low = [f for f in per_file if f["ratio"] < 0.30]
    print(f"total characters    : {total_chars}")
    print(f"files < 30% Devanagari: {len(low)}")
    for f in low:
        print(f"  {f['file']:<22} {f['ratio']:.1%}")

    Path(r"D:\wt\tagfix\corpus_build\ocr_census.json").write_text(
        json.dumps({"files": per_file, "totals": dict(totals)}, indent=1),
        encoding="utf-8",
    )
    print()
    print("non-ASCII-safe detail is in the report; console shows counts only")


if __name__ == "__main__":
    main()
