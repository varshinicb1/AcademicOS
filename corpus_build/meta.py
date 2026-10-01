import os, re
outdir = r"D:\wt\tagfix\corpus_build\sarvam_ocr"
for lab in ["fepr1-ch05","gecu1-ch12"]:
    t = open(os.path.join(outdir, lab+".md"), encoding="utf-8").read()
    print(f"--- {lab}: {len(t)} chars")
    print(repr(t[300:700])); print()
# vision meta-sentences: the model narrating about images instead of transcribing
PAT = re.compile(r"\*?\*?(This image|The image|This (?:page|figure|diagram|photo|photograph|illustration)|"
                 r"The (?:figure|diagram|photo|photograph|illustration|text)|"
                 r"अक्षरों में|इस चित्र|चित्र में)\b[^*]{0,180}", re.I)
print("=== chapters containing vision meta-commentary ===")
tot = 0
for f in sorted(os.listdir(outdir)):
    if not f.endswith(".md"): continue
    t = open(os.path.join(outdir, f), encoding="utf-8").read()
    hits = PAT.findall(t)
    if hits:
        chars = sum(len(h) for h in PAT.finditer(t).__iter__().__class__ and [m.group(0) for m in PAT.finditer(t)])
        tot += chars
        print(f"  {f[:-3]:13} {len(hits):4} meta blocks  ~{chars:6} chars  ({chars*100//max(1,len(t))}% of file)")
print(f"total meta-commentary chars across corpus: {tot}")
