import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = Path(r"D:\wt\tagfix\corpus_build\sarvam_ocr\jhsp1-ch01.md")
raw = p.read_bytes()
text = raw.decode("utf-8", errors="replace")

print(f"file = {p.name}")
print(f"bytes = {len(raw)}  chars = {len(text)}")
print(f"starts with BOM = {raw[:3] == b'\\xef\\xbb\\xbf'}")
print()

# Codepoint census over the whole file.
dev = repl = latin_q = 0
for ch in text:
    o = ord(ch)
    if 0x0900 <= o <= 0x097F:
        dev += 1
    elif o == 0xFFFD:
        repl += 1
    elif ch == "?":
        latin_q += 1

total = len(text)
print(f"Devanagari U+0900-097F : {dev:>8}  ({dev / total:.2%})")
print(f"U+FFFD replacement     : {repl:>8}  ({repl / total:.2%})")
print(f"literal '?'            : {latin_q:>8}  ({latin_q / total:.2%})")
print()

print("--- first 3 non-empty lines, escaped so nothing depends on the console ---")
shown = 0
for line in text.splitlines():
    if not line.strip():
        continue
    print(repr(line[:100]))
    shown += 1
    if shown == 3:
        break
