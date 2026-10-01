import json
import subprocess
import sys

SQL = (
    "SELECT chapter_id, COUNT(*) AS chunks, SUM(quote_exact) AS qe "
    "FROM chunks WHERE text_quality='decoded-legacy-font' GROUP BY chapter_id ORDER BY chapter_id"
)

proc = subprocess.run(
    [
        # npx is a .cmd shim; CreateProcess cannot launch it bare, so point at
        # the shim explicitly rather than relying on PATHEXT resolution.
        r"C:\nvm4w\nodejs\npx.cmd",
        "wrangler", "d1", "execute", "academicos-corpus",
        "--remote", "--json", "--command", SQL,
    ],
    cwd=r"D:\wt\tagfix\workers\corpus-rag",
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
)

out = proc.stdout
start = out.find("[")
if start == -1:
    print("no JSON in wrangler output", file=sys.stderr)
    print(out[:800], file=sys.stderr)
    print(proc.stderr[:800], file=sys.stderr)
    raise SystemExit(1)

rows = json.loads(out[start:])[0]["results"]
print(f"legacy chapters = {len(rows)}")
print(f"total legacy chunks = {sum(r['chunks'] for r in rows)}")
print(f"chapters with any quote_exact=1 = {sum(1 for r in rows if r['qe'] > 0)}")
print()
for r in rows[:6]:
    print(f"  {r['chapter_id']}  chunks={r['chunks']}  quote_exact={r['qe']}")
print("  ...")
for r in rows[-2:]:
    print(f"  {r['chapter_id']}  chunks={r['chunks']}  quote_exact={r['qe']}")

with open(r"D:\wt\tagfix\corpus_build\legacy_chapters.json", "w", encoding="utf-8") as fh:
    json.dump([r["chapter_id"] for r in rows], fh, indent=1)

with open(r"D:\wt\tagfix\corpus_build\reset_test.json", "w", encoding="utf-8") as fh:
    json.dump({"chapters": [rows[0]["chapter_id"]]}, fh)

print(f"\nprobe chapter = {rows[0]['chapter_id']}")

