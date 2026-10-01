import json, re, os
rows = json.load(open(r"D:\AcademicOS-academicos-data\corpus\ncert_chapters\extract_report.json", encoding="utf-8"))
ENG = ["aejm1-ch13","fegp1-ch10","fepr1-ch05","gecu1-ch12","gegp1-ch04","gepr1-ch02"]
print("existing extraction for the 6 English-legacy chapters:")
for r in rows:
    if f"{r['code']}-ch{r['chapter']:02d}" in ENG:
        p = r["out"]
        t = open(p, encoding="utf-8").read()
        words = re.findall(r"[A-Za-z']{2,}", t)
        top = {}
        for w in words: top[w.lower()] = top.get(w.lower(),0)+1
        common = sorted(top.items(), key=lambda kv:-kv[1])[:8]
        print(f"  {r['code']}-ch{r['chapter']:02d} {r['n_pages']}p quality={r['text_quality']:22} {len(t):6} chars {len(words):5} tokens")
        print(f"      top: {', '.join(f'{w}x{n}' for w,n in common)}")
        print(f"      sample: {t[400:620]!r}")
