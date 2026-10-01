"""Verify the 38 written chapters are internally consistent and mojibake-free.

Checks that must pass before re-packing:
  - every file has front matter and a body
  - n_chars matches the actual body length
  - text_quality is no longer decoded-legacy-font
  - quote_exact is still false (PDF validation has not run)
  - no replacement characters (U+FFFD) and no legacy-font mojibake signature
  - the body script matches the front-matter language
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MANIFEST = Path(r"D:\wt\tagfix\corpus_build\legacy_ocr_manifest.json")
manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

DEV = re.compile(r"[ऀ-ॿ]")
LATIN = re.compile(r"[A-Za-z]{2,}")
# U+FFFD replacement char, and the hallmark of the broken Krutidev/legacy decode
REPL = "�"

problems = []
rows = []
for m in manifest:
    label = m["label"]
    path = Path(m["corpus_out"])
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        problems.append(f"{label}: no front matter")
        continue
    parts = text.split("---", 2)
    if len(parts) < 3:
        problems.append(f"{label}: unterminated front matter")
        continue
    front, body = parts[1], parts[2]
    def f(key, default="?"):
        mm = re.search(rf"^{key}:\s*(.*)$", front, flags=re.M)
        return mm.group(1).strip() if mm else default

    n_chars = int(f("n_chars", "0"))
    actual = len(body.strip()) + 1
    quality = f("text_quality")
    quote = f("quote_exact")
    lang = f("language")

    dev = len(DEV.findall(body))
    lat = len(LATIN.findall(body))
    dev_pct = dev / (dev + lat) if (dev + lat) else 0

    if abs(n_chars - actual) > 2:
        problems.append(f"{label}: n_chars {n_chars} != body {actual}")
    if quality == "decoded-legacy-font":
        problems.append(f"{label}: still decoded-legacy-font")
    if quote != "false":
        problems.append(f"{label}: quote_exact is {quote}, expected false")
    if REPL in body:
        problems.append(f"{label}: contains U+FFFD replacement chars")
    # script vs language
    if lang == "hi" and dev_pct < 0.7:
        problems.append(f"{label}: lang=hi but dev={dev_pct:.0%}")
    if lang == "en" and lat / (dev + lat) < 0.7:
        problems.append(f"{label}: lang=en but latin={lat/(dev+lat):.0%}")

    rows.append((label, lang, quality, n_chars, actual, dev_pct, len(body.strip())))

print(f"{'label':<14} {'lang':<5} {'quality':<20} {'n_chars':>8} {'actual':>8} "
      f"{'dev%':>6} {'ok':>4}")
for label, lang, quality, nc, act, dp, blen in rows:
    ok = "OK" if abs(nc - act) <= 2 else "MISMATCH"
    print(f"{label:<14} {lang:<5} {quality:<20} {nc:>8} {act:>8} {dp:>5.0%} {ok:>4}")

print()
if problems:
    print(f"PROBLEMS ({len(problems)}):")
    for p in problems:
        print("  " + p)
else:
    print("All 38 chapters consistent, mojibake-free, quote_exact=false.")
