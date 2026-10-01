import json, re, os
rows = json.load(open(r"D:\AcademicOS-academicos-data\corpus\ncert_chapters\extract_report.json", encoding="utf-8"))
r = next(x for x in rows if x["code"]=="jhks1" and x["chapter"]==1)
print("out:", r["out"], "exists:", os.path.exists(r["out"]), "n_chars:", r["n_chars"])

ocr = open(r"D:\wt\tagfix\corpus_build\sarvam_ocr\jhks1-ch01.md", encoding="utf-8").read()
clean = re.sub(r"!\[[^\]]*\]\(data:[^)]*\)", "", ocr)
clean = re.sub(r"\n{3,}", "\n\n", clean).strip()

base = open(r["out"], encoding="utf-8").read()
btext = re.sub(r"^---.*?---", "", base, flags=re.S)
btext = re.sub(r"^#+\s*", "", btext, flags=re.M)
btext = re.sub(r"\s+", " ", btext).strip()
ctext = re.sub(r"\s+", " ", clean).strip()

def toks(s): return re.findall(r"[\u0900-\u097F]+", s)
ow, nw = toks(btext), toks(ctext)
os_, ns_ = set(ow), set(nw)
inter = os_ & ns_
print()
print(f"our decoded : {len(btext)} chars, {len(ow)} devanagari tokens, {len(os_)} distinct")
print(f"sarvam ocr  : {len(ctext)} chars, {len(nw)} devanagari tokens, {len(ns_)} distinct")
print(f"shared distinct: {len(inter)}  ({len(inter)/max(1,len(os_))*100:.1f}% of our tokens)")
print()
print("=== OUR decoded sample ===")
print(btext[:420])
print()
print("=== SARVAM OCR sample ===")
print(ctext[:420])
