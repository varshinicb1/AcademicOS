import gzip, json
with gzip.open(r"D:\wt\tagfix\corpus_build\chunks.jsonl.gz", "rt", encoding="utf-8") as fh:
    for n, line in enumerate(fh, 1):
        if n != 4001:
            continue
        print("line bytes:", len(line))
        try:
            json.loads(line)
            print("parses OK")
        except Exception as e:
            print("PARSE FAIL:", e)
            try:
                row = json.loads(line[:line.rfind('}') + 1])
                print("truncated-tail parse OK; chapter_id=", row.get("chapter_id"))
            except Exception as e2:
                print("truncated parse also failed:", e2)
        break
