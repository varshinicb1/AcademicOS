"""Show only the narration candidates that are NOT italic-wrapped.

Those 48 are the ones where the opener phrase could belong to real textbook
text. Everything else is unambiguous: Vision wrapped its own description in
italics, the books do not wrap their body paragraphs. This decides the rule set,
so the ambiguous lines are printed in full rather than counted.
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\wt\tagfix\corpus_build")

from find_narration import ITALIC_WRAP, classify  # noqa: E402

OCR_DIR = Path(r"D:\wt\tagfix\corpus_build\sarvam_ocr")
OUT = Path(r"D:\wt\tagfix\corpus_build\ocr_narration_review.md")

out = ["# Narration candidates without italic markup\n",
       "These matched an image-reference opener but are not wrapped in `*...*`.",
       "If a line here is real textbook prose, the loose rule must not be used.\n"]

total = 0
for path in sorted(OCR_DIR.glob("*.md")):
    hits = []
    for i, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        loose, strict = classify(line)
        if loose and not strict:
            hits.append((i, line))
    if not hits:
        continue
    total += len(hits)
    out.append(f"\n## {path.stem}  ({len(hits)})\n")
    for i, line in hits:
        flag = "ITALIC" if ITALIC_WRAP.match(line) else "PLAIN "
        out.append(f"- L{i} [{flag}] {line.strip()}")

OUT.write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"loose-but-not-strict lines: {total}")
print(f"review file: {OUT}")
