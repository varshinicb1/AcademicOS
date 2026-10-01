import json,sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
d=json.loads(Path("pdf_validation.json").read_text(encoding="utf-8"))
for ch in ["fegp1-ch10","jhkr1-ch03","gecu1-ch12","jhsp1-ch09"]:
    r=next(x for x in d if x["chapter"]==ch)
    print("="*66)
    print(ch,"font",r.get("legacy_font"),"cov",r.get("coverage"),"recip",r.get("reciprocal"))
    print("  only_in_ocr:",r.get("only_in_ocr_sample")[:18])
    print("  only_in_pdf:",r.get("only_in_pdf_sample")[:18])
