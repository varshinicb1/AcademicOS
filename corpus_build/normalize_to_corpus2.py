"""Actually write the files with the cleaned body while keeping front matter.

But first: inspect the exact front-matter format of an existing corpus file and
decide whether to rewrite it or preserve it. The chunker/corpus builder expects
YAML front matter. Let us copy the front matter verbatim from the existing
corpus files and replace everything after the closing --- with the cleaned
OCR body (which also has no front matter of its own).
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLEAN_DIR = Path(r"D:\wt\tagfix\corpus_build\sarvam_ocr_clean")
MANIFEST = Path(r"D:\wt\tagfix\corpus_build\legacy_ocr_manifest.json")
manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
ok = 0
for m in manifest:
    target = Path(m["corpus_out"])
    src = CLEAN_DIR / f"{m['label']}.md"
    if not target.exists():
        print(f"NO TARGET: {target}")
        continue
    target_text = target.read_text(encoding="utf-8", errors="replace")
    clean_text = src.read_text(encoding="utf-8", errors="replace")
    new_body = clean_text.strip() + "\n"
    # Split on ---: front matter is lines 1..k with --- at boundaries
    # Most files: line 1 is ---; find the second ---
    if target_text.startswith("---"):
        parts = target_text.split("---", 2)
        if len(parts) >= 3:
            front = "---" + parts[1] + "---"
        else:
            front = target_text
    else:
        front = ""
    # The stored n_chars still describes the old mojibake body, and
    # text_quality still claims decoded-legacy-font for text that has now been
    # replaced by real OCR. Leaving both would make the corpus self-contradict:
    # a consumer filtering on text_quality would keep treating this as decoded
    # mojibake, and any char-count check would fail against the new body.
    front = re.sub(r"^text_quality:.*$", "text_quality: ocr-vision-cleaned", front,
                   flags=re.M)
    front = re.sub(r"^n_chars:.*$", f"n_chars: {len(new_body)}", front, flags=re.M)
    new_text = front + "\n" + new_body if front else new_body
    target.write_text(new_text, encoding="utf-8", newline="\n")
    ok += 1

print(f"normalized {ok} files")
