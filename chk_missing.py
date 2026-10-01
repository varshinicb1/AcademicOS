import sys, json
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
mani=json.loads(Path(r"D:\wt\tagfix\corpus_build\legacy_ocr_manifest.json").read_text(encoding="utf-8"))
by={m["label"]:m for m in mani}
def body(label):
    t=Path(by[label]["corpus_out"]).read_text(encoding="utf-8",errors="replace")
    return t[t.find("\n---",3)+4:] if t.startswith("---") else t
g=body("gecu1-ch12").casefold()
print("gecu1-ch12 len",len(g))
for w in ["astrophys","astrophoto","activity","amount","angle","telescope","galaxy","nebula","spectr"]:
    print(f"  {w:<12} {'FOUND' if w in g else 'MISSING'}")
print()
a=body("aejm1-ch13").casefold()
print("aejm1-ch13 len",len(a))
for w in ["elephant","bigcirc","circle","75th","colourful"]:
    print(f"  {w:<12} {'FOUND' if w in a else 'MISSING'}")
print()
print("--- aejm1-ch13 body first 700 chars ---")
print(body("aejm1-ch13")[:700])
