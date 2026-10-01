import json, subprocess, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
W="https://corpus-rag.cbvarshini1.workers.dev"
def get(p):
    r=subprocess.run(["curl.exe","-sS","-m","120",W+p,
      "-H","User-Agent: AcademicOS-corpus-indexer/1.0"],
      capture_output=True,text=True,encoding="utf-8",errors="replace")
    return json.loads(r.stdout)
h=get("/health")
print("=== health ===")
print(json.dumps(h,indent=1))
ch=get("/chapters")
rows=ch["chapters"]
print(f"\n=== /chapters: {len(rows)} chapters ===")
bad=[r for r in rows if r["chunks"]==0]
print("zero-chunk chapters:",len(bad))
mani=json.loads(Path(r"D:\wt\tagfix\corpus_build\legacy_ocr_manifest.json").read_text(encoding="utf-8"))
d={r["chapter_id"]:r for r in rows}
print(f"\n=== the 38 rewritten chapters in D1 ===")
print(f"{'chapter':<14}{'chunks':>7}{'class':>7}{'subject':<14}{'lang':>7}")
tot=0
for m in sorted(mani,key=lambda x:x["label"]):
    c=m["label"]; r=d.get(c)
    if r: tot+=r["chunks"]
    print(f"{c:<14}{r['chunks'] if r else 'MISSING':>7}{r['class_no'] if r else '-':>7}"
          f"{(r['subject'] if r else '-'):<14}{(r['language'] if r else '-'):>7}")
print("total chunks in 38:",tot)
