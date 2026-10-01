"""Regression tests for the validation normalisations established in
VALIDATION_FINDINGS.md.

These exist because each of the behaviours below was the product of a
measurement, and each is easy to undo by accident:

  * the danda fold closes the last `review` chapter (38/38 verified);
  * the furniture filter must not eat lesson content;
  * the rejected KrutiDev table merge must stay rejected.

Run: python test_validation_normalizations.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "pdf_ingest"))

import validate_word_fidelity as vwf

# The canonical corpus lives in the gitignored data tree, so the checks that
# read it are skipped rather than fatal on a fresh clone. The root is resolved
# the way the rest of the repo resolves it (ACOS_CORPUS_ROOT / ACOS_DATA_ROOT,
# per config/config.toml and src/academicos/config.py).
def _corpus_root() -> Path | None:
    for var in ("ACOS_CORPUS_ROOT", "ACOS_DATA_ROOT"):
        raw = os.environ.get(var)
        if raw:
            root = Path(raw)
            return root if root.name == "corpus" else root / "corpus"
    local = Path(__file__).resolve().parents[1] / "academicos-data" / "corpus"
    return local if local.is_dir() else None


_CORPUS = _corpus_root()
FEPR1_CH05 = (
    _CORPUS / "ncert_chapters" / "English" / "c06" / "fepr1-ch05.md"
    if _CORPUS else None
)

FAILS = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}  {detail}")
        FAILS.append(name)


print("danda folding (closes jhsp1-ch01 p5)")
check("U+0965 folds to the canonical form",
      vwf.norm_word("हइ॥") == vwf.norm_word("हइ।।"),
      f'{vwf.norm_word("हइ॥")!r} vs {vwf.norm_word("हइ।।")!r}')
check("mixed danda runs also fold",
      vwf.norm_word("रव।॥") == vwf.norm_word("रव॥"))
check("folding does not touch the word body",
      vwf.norm_word("कबीर॥").removesuffix("।") == vwf.norm_word("कबीर"),
      f'got {vwf.norm_word("कबीर॥")!r} vs {vwf.norm_word("कबीर")!r}')
check("non-danda punctuation is unaffected",
      vwf.norm_word("कबीर,") == vwf.norm_word("कबीर,"))

print("\nfurniture filter must not remove lesson content")
LESSON = [
    "कस्तूरी वुंफडलि बसै म्ग ढँूढै बन माँहि।",
    "ऐसैं घटि घटि राँम है दुनियाँ देखै नाँहिं।।",
    "Reprint 2026-27",
    "ऋमचतपदज २०२६-२७",
    "संदभ़ ः कबीर ग्रंथावली बाबू श्यामसुंदर दास",
]
kept = vwf.strip_pdf_furniture("\n".join(LESSON)).splitlines()
check("reprint line removed", "Reprint 2026-27" not in kept)
check("garbled imprint removed", "ऋमचतपदज २०२६-२७" not in kept)
check("poem line 1 kept", LESSON[0] in kept)
check("poem line 2 kept", LESSON[1] in kept)
check("source note kept", LESSON[4] in kept)

print("\nrejected KrutiDev merge must not be reintroduced")
try:
    from lipi.mappings import FONT_MAPPINGS

    tbl = FONT_MAPPINGS["walkman_chanakya"]
    check("no '.' -> na-halant injected", "." not in tbl,
          f"got {tbl.get('.')!r}; measured worse on 244/272 pages")
    check("no '{' -> ksha-halant injected", "{" not in tbl,
          f"got {tbl.get('{')!r}")
    check("naive 'F'=tha not applied", tbl.get("F") == "थ्", f"got {tbl.get('F')!r}")
    check("corrected 'Fk'=tha retained", tbl.get("Fk") == "थ", f"got {tbl.get('Fk')!r}")
    check("corrected 'D'=ka-halant retained", tbl.get("D") == "क्", f"got {tbl.get('D')!r}")
    check("naive 'Dk' absent", "Dk" not in tbl, f"got {tbl.get('Dk')!r}")
except ImportError:
    print("  SKIP  lipi not installed")

print("\nfepr1-ch05 figure labels present")
if FEPR1_CH05 is not None and FEPR1_CH05.is_file():
    fepr = FEPR1_CH05.read_text(encoding="utf-8")
    for label in ("Delta", "Diamond", "Parafoil", "Rokkaku"):
        check(f"{label} in body", label in fepr)
else:
    print(f"  SKIP  canonical corpus not present (looked for {FEPR1_CH05})")

print()
if FAILS:
    print(f"{len(FAILS)} FAILED: {FAILS}")
    sys.exit(1)
print("all checks passed")
