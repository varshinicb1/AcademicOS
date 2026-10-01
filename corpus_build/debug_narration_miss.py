"""Why did the Hindi narration survive the stripper?

Two candidate causes, and they need opposite fixes:

  1. The opener regex does not match Devanagari, because Python treats
     combining vowel signs (category Mn) as non-word characters, so a `\b`
     placed after a Devanagari word can fail.
  2. The narration opened an italic block that never closed, so the
     block-consumption state machine swallowed real body text to end of file.
     That is data loss, not a missed match, and it is the worse of the two.

This prints the verdict for the exact lines that survived, plus how many body
lines each file lost, so the cause is identified rather than patched by guesswork.
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\wt\tagfix\corpus_build")

from strip_narration import NARRATION_OPENER, NO_TEXT_TAIL  # noqa: E402

SRC = Path(r"D:\wt\tagfix\corpus_build\sarvam_ocr")
CLEAN = Path(r"D:\wt\tagfix\corpus_build\sarvam_ocr_clean")

TESTS = [
    "छवि में एक ऊर्ध्वाधर आयताकार बैनर है जो टील रंग का है।",
    "यह छवि एक वैज्ञानिक विषयवस्तु का श्वेत-श्याम (black and white) चित्रण है",
    "यह चित्र एक कार्टून शैली का चित्रण है जिसमें एक हल्के पीले रंग की पृष्ठभूमि है",
    "This image contains a QR code, not text.",
]

print("=== direct regex probe ===")
for t in TESTS:
    print(f"opener={bool(NARRATION_OPENER.match(t))!s:<5} "
          f"note={bool(NO_TEXT_TAIL.search(t))!s:<5} {t[:60]!r}")

print("\n=== word-boundary probe ===")
for w in ["छवि\\b", "(?:छवि|चित्र)\\b", "में\\b", "यह\\b"]:
    pat = w.replace("\\b", "\x00")
    pat = re.sub(r"\\x00", r"\b", pat)
    probe = re.compile(pat)
    for s in ["छवि में", "में एक", "यह छवि"]:
        print(f"  {w:<22} vs {s!r:<12} -> {bool(probe.search(s))}")
    break  # one representative is enough

print("\n=== \\w behaviour on Devanagari combining marks ===")
for ch, name in [("छ", "U+091B LO"), ("व", "U+0935 LO"), ("ि", "U+093F Mn"),
                 ("ा", "U+093E Mn"), ("ँ", "U+0901 Mn")]:
    print(f"  {ch} {name} is_word={bool(re.match(r'\w', ch))} "
          f"alnum={ch.isalnum()}")

print("\n=== unclosed italic block check (data-loss risk) ===")
for label in ["fegp1-ch10", "gecu1-ch12", "gepr1-ch02", "gegp1-ch04",
              "fepr1-ch05", "aejm1-ch13"]:
    orig = (SRC / f"{label}.md").read_text(encoding="utf-8", errors="replace")
    lines = orig.splitlines()
    # Count asterisks: an odd total per file means an italic block never closed.
    stars = orig.count("*")
    unclosed = None
    for i, l in enumerate(lines, 1):
        if l.strip().startswith("*") and not l.strip().endswith("*") and len(l.strip()) > 2:
            unclosed = (i, l.strip()[:80])
    clean_lines = len((CLEAN / f"{label}.md").read_text(
        encoding="utf-8", errors="replace").splitlines())
    print(f"  {label:<14} orig_lines={len(lines):>5} clean_lines={clean_lines:>5} "
          f"stars={stars:>5} {'odd -> UNCLOSED' if stars % 2 else ''}")
    if unclosed:
        print(f"      first_opener L{unclosed[0]}: {unclosed[1]!r}")
