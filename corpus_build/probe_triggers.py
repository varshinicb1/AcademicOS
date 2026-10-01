import json, subprocess
WR=r"C:\nvm4w\nodejs\npx.cmd"; CWD=r"D:\wt\tagfix\workers\corpus-rag"
def q(sql):
    p=subprocess.run([WR,"wrangler","d1","execute","academicos-corpus","--remote","--json","--command",sql],
        cwd=CWD,capture_output=True,text=True,encoding="utf-8",errors="replace")
    s=p.stdout.find("[")
    return json.loads(p.stdout[s:])[0]["results"]
print("--- triggers on chunks ---")
for r in q("SELECT name, sql FROM sqlite_master WHERE type='trigger' AND tbl_name='chunks'"):
    print(f"  {r['name']}")
    for line in (r['sql'] or '').splitlines():
        if line.strip(): print(f"      {line.strip()}")
print("\n--- FTS5 shadow tables ---")
for r in q("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'chunks_fts%'"):
    print(f"  {r['name']}")
