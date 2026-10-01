import json
rows = json.load(open(r"D:\AcademicOS-academicos-data\corpus\ncert_chapters\extract_report.json", encoding="utf-8"))
print("rows:", len(rows))
dec = [r for r in rows if "decod" in str(r.get("text_quality","")).lower()]
print("decoded chapters:", len(dec), "of", len(rows))
tot = 0
for r in sorted(dec, key=lambda r: (r["subject"], r["class"], r["chapter"])):
    pg = r.get("n_pages", 0)
    tot += pg
    print(f"  {r['code']}-ch{r['chapter']:02d} p{pg:3} {r['language']:3} {r['subject'][:14]:14} {r['title'][:28]}")
print()
print("TOTAL legacy pages:", tot)
print("OCR jobs (10pg):", -(-tot//10))
print("OCR cost Rs:", tot*0.5)
print("submit minutes at 10 req/min:", round(-(-tot//10)/10, 1))
tot_all = sum(r.get("n_pages",0) for r in rows)
print()
print("ALL corpus pages:", tot_all, "-> full OCR cost Rs:", tot_all*0.5)
