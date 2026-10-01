"""Write cleaned OCR chapters into the canonical corpus location.

The existing corpus in D:\\AcademicOS-academicos-data\\corpus\\ncert_chapters
still has the old decoded-legacy-font (mojibake) text. After stripping narration,
the cleaned OCR text needs to replace the body while keeping the front matter
fields that the chunker/ingest expect. Some fields may be updated (quote_exact
remains false until PDF validation; text_quality can be marked ocr-cleaned),
and the body is plain markdown with no embedded font-remap artifacts.
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLEAN_DIR = Path(r"D:\wt\tagfix\corpus_build\sarvam_ocr_clean")
MANIFEST = Path(r"D:\wt\tagfix\corpus_build\legacy_ocr_manifest.json")
OUT_DIR = Path(r"D:\AcademicOS-academicos-data\corpus\ncert_chapters")

# Which files to overwrite? All 38 from manifest
manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
out_list = []
for m in manifest:
    target = Path(m["corpus_out"])
    src = CLEAN_DIR / f"{m['label']}.md"
    if not src.exists():
        print(f"MISSING: {src}")
        continue
    out_list.append((m, src, target))
    target.parent.mkdir(parents=True, exist_ok=True)

print(f"Will write {len(out_list)} chapters")
