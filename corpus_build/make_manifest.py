import json, os
rows = json.load(open(r"D:\AcademicOS-academicos-data\corpus\ncert_chapters\extract_report.json", encoding="utf-8"))
LANG = {"hi": "hi-IN", "en": "en-IN", "te": "te-IN", "mr": "mr-IN", "bn": "bn-IN",
        "ta": "ta-IN", "kn": "kn-IN", "gu": "gu-IN", "pa": "pa-IN", "ml": "ml-IN",
        "or": "od-IN", "ur": "ur-IN", "as": "as-IN", "sa": "sa-IN", "mai": "mai-IN",
        "doi": "doi-IN", "kok": "kok-IN", "sat": "sat-IN", "sind": "sd-IN",
        "kas": "ks-IN", "mni": "mni-IN", "brx": "brx-IN", "nep": "ne-IN"}
items, missing = [], []
for r in rows:
    if "decod" not in str(r.get("text_quality", "")).lower():
        continue
    pdf = r["pdf"]
    if not os.path.exists(pdf):
        missing.append(pdf); continue
    label = f"{r['code']}-ch{r['chapter']:02d}"
    items.append({"pdf": pdf, "label": label, "language": LANG.get(r["language"], "en-IN"),
                  "subject": r["subject"], "class": r["class"], "pages": r["n_pages"],
                  "current_quality": r["text_quality"], "corpus_out": r["out"]})
out = r"D:\wt\tagfix\corpus_build\legacy_ocr_manifest.json"
json.dump(items, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
pages = sum(i["pages"] for i in items)
print(f"manifest: {len(items)} chapters, {pages} pages, cost Rs {pages*0.5}")
print("by language:", {k: sum(1 for i in items if i['language']==k) for k in sorted({i['language'] for i in items})})
print("missing PDFs:", len(missing))
print("written:", out)
