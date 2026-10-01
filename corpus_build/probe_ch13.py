import json, subprocess, sys
# Devanagari on stdout: the console defaults to cp1252 and raises rather than
# substituting, so the probe dies before it can print what it found.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
WR=r"C:\nvm4w\nodejs\npx.cmd"; CWD=r"D:\wt\tagfix\workers\corpus-rag"
def q(sql):
    p=subprocess.run([WR,"wrangler","d1","execute","academicos-corpus","--remote","--json","--command",sql],
        cwd=CWD,capture_output=True,text=True,encoding="utf-8",errors="replace")
    s=p.stdout.find("[")
    return json.loads(p.stdout[s:])[0]["results"]
rows=q("SELECT id, heading_path, substr(text,1,220) AS snippet FROM chunks WHERE chapter_id='aejm1-ch13' ORDER BY id LIMIT 3")
for r in rows:
    print(r["id"])
    print("  heading:", r["heading_path"][:90])
    print("  text   :", " ".join(r["snippet"].split())[:200])
    print()
