import json,sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
d=json.loads(Path("pdf_validation.json").read_text(encoding="utf-8"))
for ch in ["aejm1-ch13","jhks1-ch05","fegp1-ch10"]:
    r=next(x for x in d if x["chapter"]==ch)
    print("="*60)
    print(ch,"lang",r["language"],"font",r.get("legacy_font"),"cov",r.get("coverage"))
    print("  only_in_ocr:",r.get("only_in_ocr_sample")[:10])
    print("  only_in_pdf:",r.get("only_in_pdf_sample")[:10])
