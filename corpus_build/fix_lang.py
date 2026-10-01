import json, re, os, glob
outdir = r"D:\wt\tagfix\corpus_build\sarvam_ocr"
rows = json.load(open(r"D:\AcademicOS-academicos-data\corpus\ncert_chapters\extract_report.json", encoding="utf-8"))
legacy = {f"{r['code']}-ch{r['chapter']:02d}": r
          for r in rows if "decod" in str(r.get("text_quality","")).lower()}
print(f"{'label':13}{'decl':5}{'dev%':>7}{'latin%':>8}{'chars':>8}  verdict")
bad = []
for lab, r in sorted(legacy.items()):
    p = os.path.join(outdir, lab + ".md")
    if not os.path.exists(p):
        print(f"{lab:13}{r['language']:5}{'--':>7}{'--':>8}{'--':>8}  MISSING"); bad.append((lab,r)); continue
    t = open(p, encoding="utf-8").read()
    dev = sum(1 for c in t if "\u0900" <= c <= "\u097f")
    let = sum(1 for c in t if c.isascii() and c.isalpha())
    ds, ls = dev/max(1,dev+let), let/max(1,dev+let)
    if ds < 0.05:
        bad.append((lab, r))
        v = "RE-OCR as hi-IN (not English!)"
    elif r["language"] == "en" and ds > 0.30:
        v = "declared en but IS Devanagari -> re-OCR as hi-IN"
        bad.append((lab, r))
    else:
        v = "ok"
    print(f"{lab:13}{r['language']:5}{ds*100:6.1f}%{ls*100:7.1f}%{len(t):8}  {v}")
print()
print("to redo:", [b[0] for b in bad])
if bad:
    json.dump([{"pdf": b[1]["pdf"], "label": b[0], "language": "hi-IN",
                "subject": b[1]["subject"], "class": b[1]["class"], "pages": b[1]["n_pages"],
                "current_quality": b[1]["text_quality"], "corpus_out": b[1]["out"]} for b in bad],
              open(r"D:\wt\tagfix\corpus_build\legacy_ocr_manifest_fix.json","w",encoding="utf-8"),
              indent=2, ensure_ascii=False)
    pg = sum(b[1]["n_pages"] for b in bad)
    print(f"pages={pg} cost=Rs{pg*0.5}")
