import re
for lab in ["fegp1-ch10","gepr1-ch02","aejm1-ch13"]:
    t = open(rf"D:\wt\tagfix\corpus_build\sarvam_ocr\{lab}.md", encoding="utf-8").read()
    # what fraction of "words" are real English vs junk?
    words = re.findall(r"[A-Za-z']{2,}", t)
    vocab = {}
    for w in words:
        vocab[w.lower()] = vocab.get(w.lower(), 0) + 1
    top = sorted(vocab.items(), key=lambda kv: -kv[1])[:12]
    print(f"--- {lab}: {len(t)} chars, {len(words)} tokens, {len(vocab)} distinct")
    print("   top:", ", ".join(f"{w}x{n}" for w, n in top))
    print("   sample:", repr(t[2000:2400]))
    print()
