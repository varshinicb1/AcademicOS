"""Detect the actual script of each OCR output rather than trusting the manifest.

The manifest disagrees with itself: the main file marks six books `en-IN` while
`legacy_ocr_manifest_fix.json` re-marks two of those same six as `hi-IN`. A
language field that cannot be trusted cannot drive the stripper's rules, so the
script mix is measured from the text itself and the two are compared.
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OCR_DIR = Path(r"D:\wt\tagfix\corpus_build\sarvam_ocr")
REPORT = Path(r"D:\wt\tagfix\corpus_build\ocr_language.md")

# Vision narration is English regardless of the book's language, so it is
# excluded before measuring: otherwise every Hindi book looks partly English.
NARRATION = re.compile(
    r"^\s*\*?\s*(this|the)\s+(image|photo|picture|diagram|figure)\b.*$",
    re.I,
)
FURNITURE = re.compile(r"^\s*(reprint\s+\d{4}\s*-\s*\d{2}|---|\d{3,4}\s*ch\s*\d{1,2})\s*$", re.I)


def scripts(text: str) -> tuple[int, int, int]:
    dev = latin = digit = 0
    for ch in text:
        o = ord(ch)
        if 0x0900 <= o <= 0x097F:
            dev += 1
        elif ch.isalpha() and o < 0x0250:
            latin += 1
        elif ch.isdigit():
            digit += 1
    return dev, latin, digit


def main() -> None:
    manifest = {m["label"]: m for m in
                json.loads(Path(r"D:\wt\tagfix\corpus_build\legacy_ocr_manifest.json")
                          .read_text(encoding="utf-8"))}
    fix_path = Path(r"D:\wt\tagfix\corpus_build\legacy_ocr_manifest_fix.json")
    fix = {m["label"]: m for m in json.loads(fix_path.read_text(encoding="utf-8"))} \
        if fix_path.exists() else {}

    rows = []
    for path in sorted(OCR_DIR.glob("*.md")):
        label = path.stem
        raw_lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        body = [ln for ln in raw_lines
                if not NARRATION.match(ln) and not FURNITURE.match(ln)]
        dev, latin, digit = scripts("\n".join(body))
        letters = dev + latin
        rows.append({
            "label": label,
            "manifest_lang": manifest.get(label, {}).get("language", "?"),
            "fix_lang": fix.get(label, {}).get("language"),
            "dev": dev,
            "latin": latin,
            "digits": digit,
            "dev_share": (dev / letters) if letters else 0.0,
            "sample": next((ln.strip() for ln in body if len(ln.strip()) > 40), ""),
        })

    out = ["# OCR language detection\n",
           "dev_share is Devanagari letters over all letters, after removing",
           "Vision narration and page furniture.\n",
           "| label | manifest | fix | dev_share | verdict |",
           "|---|---|---|---:|---|"]
    for r in rows:
        share = r["dev_share"]
        verdict = "hindi" if share > 0.60 else ("english" if share < 0.15 else "MIXED")
        # A Hindi book should be overwhelmingly Devanagari and vice versa.
        expect = "hindi" if r["manifest_lang"] == "hi-IN" else "english"
        flag = "" if verdict == expect else "  <-- disagrees with manifest"
        out.append(
            f"| {r['label']} | {r['manifest_lang']} | {r['fix_lang'] or '-'} | "
            f"{share:.1%} | {verdict}{flag} |"
        )

    out.append("\n## Longest body line per file (script evidence)\n")
    for r in rows:
        out.append(f"- **{r['label']}** ({r['dev_share']:.0%} dev): {r['sample'][:150]}")

    REPORT.write_text("\n".join(out) + "\n", encoding="utf-8")

    print(f"{'label':<14} {'manifest':<6} {'fix':<6} {'dev%':>6}  verdict")
    disagree = 0
    for r in rows:
        share = r["dev_share"]
        verdict = "hindi" if share > 0.60 else ("english" if share < 0.15 else "MIXED")
        expect = "hindi" if r["manifest_lang"] == "hi-IN" else "english"
        mark = "" if verdict == expect else "  <-- DISAGREES"
        if mark:
            disagree += 1
        print(f"{r['label']:<14} {r['manifest_lang']:<6} "
              f"{(r['fix_lang'] or '-'):<6} {share:>5.0%}  {verdict}{mark}")
    print()
    print(f"files disagreeing with manifest: {disagree}")
    print(f"report: {REPORT}")


if __name__ == "__main__":
    main()
