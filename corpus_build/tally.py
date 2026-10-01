import os, json, re
outdir = r"D:\wt\tagfix\corpus_build\sarvam_ocr"
rows = json.load(open(r"D:\AcademicOS-academicos-data\corpus\ncert_chapters\extract_report.json", encoding="utf-8"))
legacy = {f"{r['code']}-ch{r['chapter']:02d}": r for r in rows
          if "decod" in str(r.get("text_quality","")).lower()}
tot_ocr = tot_old = 0
worse = []
for lab, r in sorted(legacy.items()):
    p = os.path.join(outdir, lab + ".md")
    new = open(p, encoding="utf-8").read() if os.path.exists(p) else ""
    old = open(r["out"], encoding="utf-8").read() if os.path.exists(r["out"]) else ""
    tot_ocr += len(new); tot_old += len(old)
    if len(new) < len(old) * 0.6:
        worse.append((lab, len(old), len(new)))
print(f"38 legacy chapters: old decoded total {tot_old:,} chars -> OCR total {tot_ocr:,} chars")
print(f"chapters where OCR is much SHORTER than the old decode: {worse}")
print()
print("sample devanagari shaping check (jhkr1-ch01 first verse):")
t = open(os.path.join(outdir,"jhkr1-ch01.md"), encoding="utf-8").read()
i = t.find("\n\n")
print(" ", t[:260].replace("\n"," | "))
