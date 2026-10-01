"""Show the one narration hit in jess3-ch05 so it can be judged by eye.

A single hit is not automatically a defect: jess3-ch05 is a native-text-layer
chapter that was never re-OCR'd, so if the sentence is real textbook prose that
happens to begin "This image shows ...", the corpus is correct and the detector
is over-eager. Deciding by reading beats deleting on a regex.
"""
import gzip
import json
import re

NAR = re.compile(
    r"(this\s+(?:image|picture|diagram)\s+(?:contains|shows|depicts))", re.I)

with gzip.open(r"D:\wt\tagfix\corpus_build\chunks.new.jsonl.gz", "rt",
               encoding="utf-8") as fh:
    for line in fh:
        r = json.loads(line)
        if r["chapter_id"] != "jess3-ch05":
            continue
        text = r.get("text") or ""
        m = NAR.search(text)
        if not m:
            continue
        print("chunk id      :", r.get("id"))
        print("quality       :", r.get("text_quality"))
        print("heading_path  :", r.get("heading_path"))
        print("quote_exact   :", r.get("quote_exact"))
        print("--- context ---")
        print(text[max(0, m.start() - 400):m.start() + 400])
        print("--- end ---")
