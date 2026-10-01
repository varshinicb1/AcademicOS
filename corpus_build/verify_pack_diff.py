import gzip, json, hashlib, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
def load(p):
    d={}
    with gzip.open(p,"rt",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if not line: continue
            r=json.loads(line)
            d[r["id"]]=r
    return d
def sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest().upper()
old=load("chunks.new.jsonl.gz"); new=load("chunks.final.jsonl.gz")
print(f"old live pack : {len(old)} chunks  sha={sha('chunks.new.jsonl.gz')[:24]}")
print(f"rebuilt pack  : {len(new)} chunks  sha={sha('chunks.final.jsonl.gz')[:24]}")
print(f"\nids only in old: {len(set(old)-set(new))}")
print(f"ids only in new: {len(set(new)-set(old))}")
diff=[i for i in set(old)&set(new) if json.dumps(old[i],sort_keys=True,ensure_ascii=False)!=json.dumps(new[i],sort_keys=True,ensure_ascii=False)]
print(f"ids with changed content: {len(diff)}")
for i in sorted(diff):
    o,n=old[i],new[i]
    print(f"\n  {i}")
    print(f"    chapter: {o.get('chapter')}  quote_exact old={o.get('quote_exact')} new={n.get('quote_exact')}")
    for k in set(o)|set(n):
        if k in ("id","embedding"): continue
        ov,nv=o.get(k),n.get(k)
        if json.dumps(ov,sort_keys=True,ensure_ascii=False)!=json.dumps(nv,sort_keys=True,ensure_ascii=False):
            so,sn=str(ov),str(nv)
            print(f"    field '{k}' changed: len {len(so)} -> {len(sn)}")
            if len(so)<400 and len(sn)<400:
                print(f"      old: {so[:300]}")
                print(f"      new: {sn[:300]}")
