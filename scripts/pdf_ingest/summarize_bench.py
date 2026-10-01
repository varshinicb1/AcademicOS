import json
import statistics as st
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "parser_benchmark.json"
data = json.load(open(path, encoding="utf-8"))
rows = data if isinstance(data, list) else data.get("rows", [])

META = {"code", "chapter", "class", "subject", "language", "pdf"}
engines = []
for r in rows:
    for k, v in r.items():
        if k not in META and isinstance(v, dict) and k not in engines:
            engines.append(k)

NUM = (
    "heading_recall",
    "anchor_recall",
    "anchor_ng5",
    "dup_line_rate",
    "replacement_chars",
    "s_per_page",
    "tables",
    "chars",
)


def mean(vals):
    vals = [v for v in vals if isinstance(v, (int, float))]
    return st.mean(vals) if vals else float("nan")


print("file: %s   rows: %d   engines: %s" % (path, len(rows), ", ".join(engines)))
for eng in engines:
    pairs = [(r, r[eng]) for r in rows if isinstance(r.get(eng), dict)]
    print("\n== %s  n=%d" % (eng, len(pairs)))
    for k in NUM:
        v = [m.get(k) for _, m in pairs]
        n = len([x for x in v if isinstance(x, (int, float))])
        if n:
            print(
                "   %-17s n=%-3d mean=%-9.4f median=%-9.4f min=%-8.3f max=%.3f"
                % (k, n, mean(v), st.median([x for x in v if isinstance(x, (int, float))]),
                   min(x for x in v if isinstance(x, (int, float))),
                   max(x for x in v if isinstance(x, (int, float))))
            )
    for lang in sorted({r.get("language") for r, _ in pairs if r.get("language")}):
        L = [m for r, m in pairs if r.get("language") == lang]
        print(
            "   -- %s n=%-3d head=%.3f anchor=%.3f ng5=%.3f dup=%.3f s/pg=%.3f"
            % (lang, len(L), mean([m.get("heading_recall") for m in L]),
               mean([m.get("anchor_recall") for m in L]),
               mean([m.get("anchor_ng5") for m in L]),
               mean([m.get("dup_line_rate") for m in L]),
               mean([m.get("s_per_page") for m in L]))
        )
    worst = sorted(
        [(mean([m.get("anchor_ng5")]), r.get("code"), r.get("language")) for r, m in pairs]
    )[:5]
    print("   worst ng5: " + ", ".join("%s/%s=%.2f" % (c, l, s) for s, c, l in worst if s == s))
