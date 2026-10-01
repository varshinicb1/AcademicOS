"""Insert the four missing kite labels into fepr1-ch05.

The Vision OCR pass dropped the figure labels `Delta`, `Diamond`, `Parafoil` and
`Rokkaku` on PDF page 20. The four Hindi answers immediately below the figure
still describe them (upper kite triangular = Delta, two diamond-shaped = Diamond,
lower kite = Parafoil/Rokkaku), so the omission is purely the figure's own text
layer and not a content loss. Patch the labels back in at the figure position
with a short caption.

Idempotent: re-running is a no-op once the caption is present.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LABELS = ["Delta", "Diamond", "Parafoil", "Rokkaku"]
CAPTION = (
    "*Figure: the four kites are labelled "
    + ", ".join(LABELS[:-1])
    + " and "
    + LABELS[-1]
    + ".*"
)

# The figure's own caption line, immediately after the "look at the picture"
# instruction. Everything after this marker is the numbered question block.
# The cleaned OCR keeps it on one line while the canonical body wraps it across
# two, so match it whitespace-flexibly.
ANCHOR_RE = re.compile(
    r"windy kite flying birds sky\s+looking has ribbons"
)

CLEAN = Path("sarvam_ocr_clean/fepr1-ch05.md")
CANON = Path(
    r"D:\AcademicOS-academicos-data\corpus\ncert_chapters\English\c06\fepr1-ch05.md"
)


def patch(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if CAPTION in text:
        print(f"{path.name}: already patched, skipping")
        return False

    match = ANCHOR_RE.search(text)
    if match is None:
        raise SystemExit(f"{path}: anchor not found; refusing to guess a position")

    new = text[: match.end()] + f"\n\n{CAPTION}\n" + text[match.end() :].lstrip("\n")

    if path == CANON:
        # Convention across every canonical chapter: n_chars is the exact
        # length of everything after the closing front-matter delimiter.
        close = new.find("\n---\n", 4)
        if close == -1:
            raise SystemExit(f"{path}: no closing front-matter delimiter")
        declared = len(new[close + len("\n---\n") :])
        new = re.sub(
            r"(?m)^n_chars: \d+$",
            f"n_chars: {declared}",
            new,
            count=1,
        )

    path.write_text(new, encoding="utf-8")
    print(f"{path.name}: inserted {len(LABELS)} labels -> {CAPTION}")
    return True


if __name__ == "__main__":
    touched = sum(patch(p) for p in (CLEAN, CANON))
    print(f"\npatched {touched}/2 files")
    canon = CANON.read_text(encoding="utf-8")
    declared = re.search(r"(?m)^n_chars: (\d+)$", canon).group(1)
    print(f"n_chars declared: {declared}")
    for lab in LABELS:
        print(f"  {lab:<8} occurrences: {canon.count(lab)}")
