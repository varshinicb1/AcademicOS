import json, re, os
rep = json.load(open(r"D:\wt\tagfix\corpus_build\sarvam_ocr\ocr_report.json", encoding="utf-8"))
bad = [r for r in rep if r["status"] not in ("ok","cached")]
print("not-ok:", [(r["label"], r["status"], r.get("failures")) for r in bad])
print()
rows = []
for r in rep:
    if r["status"] not in ("ok","cached"): continue
    p = r["out"]
    t = open(p, encoding="utf-8").read()
    dev = sum(1 for c in t if "\u0900" <= c <= "\u097f")
    latin = sum(1 for c in t if c.isascii() and c.isalpha())
    rows.append((r["label"], len(t), dev, latin, r["status"]))
print(f"{'label':14} {'chars':>7} {'devan':>7} {'latin':>7}  status")
for lab, n, d, l, s in rows:
    print(f"{lab:14} {n:7} {d:7} {l:7}  {s}")
print()
print("total chars:", sum(r[1] for r in rows))
print("chapters with ZERO devanagari but should be hindi:",
      [r[0] for r in rows if r[2] < 50 and r[0].startswith('jh')])
