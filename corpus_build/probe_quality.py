import json
import subprocess
import sys

WRANGLER = r"C:\nvm4w\nodejs\npx.cmd"
CWD = r"D:\wt\tagfix\workers\corpus-rag"


def query(sql):
    proc = subprocess.run(
        [WRANGLER, "wrangler", "d1", "execute", "academicos-corpus",
         "--remote", "--json", "--command", sql],
        cwd=CWD, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    out = proc.stdout
    start = out.find("[")
    if start == -1:
        print("no JSON in output", file=sys.stderr)
        print(out[:1000], file=sys.stderr)
        print(proc.stderr[:1000], file=sys.stderr)
        raise SystemExit(1)
    return json.loads(out[start:])[0]["results"]


print("--- text_quality distribution ---")
for r in query("SELECT text_quality, COUNT(*) AS n FROM chunks GROUP BY text_quality ORDER BY n DESC"):
    print(f"  {r['text_quality']!r}: {r['n']}")

print("\n--- quote_exact distribution ---")
for r in query("SELECT quote_exact, COUNT(*) AS n FROM chunks GROUP BY quote_exact"):
    print(f"  {r['quote_exact']}: {r['n']}")

print("\n--- columns on chunks ---")
for r in query("PRAGMA table_info(chunks)"):
    print(f"  {r['name']} {r['type']}")
