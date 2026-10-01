import gzip, hashlib
local = r"D:\wt\tagfix\corpus_build\chunks.jsonl.gz"
raw = open(local,"rb").read()
print("local gz bytes:", len(raw))
print("local sha256  :", hashlib.sha256(raw).hexdigest().upper())
data = gzip.decompress(raw)
print("decompressed  :", len(data), "bytes")
lines = data.split(b"\n")
print("lines in pack :", len([l for l in lines if l.strip()]))
for i in range(3998, 4004):
    l = lines[i-1] if i-1 < len(lines) else b""
    print(f"  local line #{i}: len={len(l)} head={l[:70]!r}")
