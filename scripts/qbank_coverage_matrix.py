"""The coverage matrix: topic x marks, per subject per grade.

"What should I add?" is a question about gaps, and a gap is only visible
against a grid. This prints that grid, flags the thin cells, and ranks the
holes, so effort goes where the bank is actually weak rather than where it is
already strong.

Two kinds of gap are reported separately, because they need different work:

  * a topic with too few questions in a marks band -- needs MORE QUESTIONS
  * a topic whose questions are all one mark -- needs a SPREAD, which is often
    a different fix (the topic may only ever be assessed in one format)

An empty band is not the same as an unassessable one. A 1-mark topic that has
no 5-mark questions may simply never be asked for 5 marks; the matrix reports
the absence and does not invent a requirement for it.

Run:  python scripts/qbank_coverage_matrix.py [--json OUT] [--min-2|--min-3]
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

CORPORA = [
    REPO / "academicos-data" / "corpus" / "cbse-cbe" / "questions.json",
    REPO / "academicos-data" / "syllabus" / "questions.json",
]

# The marks bands CBSE actually uses. Grouping into these rather than raw marks
# keeps the matrix readable; the raw distribution is printed separately.
BANDS = [(1, 1), (2, 2), (3, 3), (4, 5), (6, 10), (11, 100)]


def band_of(marks) -> str:
    try:
        m = int(marks)
    except (TypeError, ValueError):
        return "?"
    for lo, hi in BANDS:
        if lo <= m <= hi:
            return f"{lo}" if lo == hi else f"{lo}-{hi}"
    return "?"


def load() -> tuple[list[dict], list[str]]:
    out: list[dict] = []
    used: list[str] = []
    seen: set[str] = set()
    for path in CORPORA:
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        records = payload.get("questions", payload) if isinstance(payload, dict) else payload
        n = 0
        for rec in records:
            rid = rec.get("id")
            if rid in seen:                     # the two corpora can overlap
                continue
            seen.add(rid)
            rec["_corpus"] = path.parent.name
            out.append(rec)
            n += 1
        used.append(f"{path.relative_to(REPO)} ({n:,} new)")
    return out, used


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, help="also write the matrix as JSON")
    ap.add_argument("--min", type=int, default=3,
                    help="a topic x band cell is 'thin' below this (default 3)")
    ap.add_argument("--top", type=int, default=40, help="rows to print per subject")
    args = ap.parse_args()

    records, used = load()
    print(f"questions: {len(records):,}")
    for u in used:
        print(f"  from {u}")
    print()

    # grid[(subject, grade)][topic][band] = count
    grid: dict[tuple, dict[str, dict[str, int]]] = collections.defaultdict(
        lambda: collections.defaultdict(lambda: collections.defaultdict(int)))
    untopiced = collections.Counter()
    for rec in records:
        key = (rec.get("subject") or "?", rec.get("grade") or "?")
        topic = (rec.get("contentCode") or "").strip()
        if not topic:
            untopiced[key] += 1
            continue
        grid[key][topic][band_of(rec.get("marks"))] += 1

    bands = [f"{lo}" if lo == hi else f"{lo}-{hi}" for lo, hi in BANDS]
    header = "  ".join(f"{b:>5}" for b in bands)

    thin: list[tuple] = []
    overview: list[dict] = []

    for key in sorted(grid, key=lambda k: (str(k[0]), str(k[1]))):
        subject, grade = key
        topics = grid[key]
        total = sum(sum(c.values()) for c in topics.values())
        per_band = collections.Counter()
        for bands_ in topics.values():
            for b, n in bands_.items():
                per_band[b] += n

        print("=" * 92)
        print(f"{subject}  class {grade}   {len(topics)} topics   {total} questions"
              + (f"   ({untopiced[key]} untopiced)" if untopiced[key] else ""))
        print("=" * 92)
        print(f"  {'topic':<14} {header}    total")
        print(f"  {'-' * 14} {'-' * (len(header))}")

        ranked = sorted(topics.items(), key=lambda kv: -sum(kv[1].values()))
        for code, band_counts in ranked[:args.top]:
            cells = "  ".join(f"{band_counts.get(b, 0):>5}" for b in bands)
            print(f"  {code:<14} {cells}    {sum(band_counts.values()):>4}")
            for b in bands:
                n = band_counts.get(b, 0)
                if 0 < n < args.min:
                    thin.append((subject, grade, code, b, n))
        if len(ranked) > args.top:
            print(f"  ... {len(ranked) - args.top} more topics")

        # Band-level coverage: how many topics have ANY question in this band.
        #
        # A band above the highest mark this pair is ever assessed at is NOT a
        # gap. Every class 6-10 pair showed "no questions at 11-100 marks",
        # which reads as eight holes and is really one banding artefact: those
        # grades top out at 6 marks. An inapplicable band is reported as such,
        # so a real absence is never buried under a fake one.
        observed_max = max((int(r.get("marks") or 0) for r in records
                            if (r.get("subject"), r.get("grade")) == key), default=0)
        band_topics = {b: sum(1 for c in topics.values() if c.get(b)) for b in bands}
        floor = {f"{lo}" if lo == hi else f"{lo}-{hi}": lo for lo, hi in BANDS}
        inapplicable = [b for b in bands
                        if band_topics[b] == 0 and floor[b] > observed_max]
        real_empty = [b for b in bands
                      if band_topics[b] == 0 and b not in inapplicable]

        print()
        print(f"  topics with any question per band: "
              + ", ".join(f"{b}:{band_topics[b]}/{len(topics)}" for b in bands))
        print(f"  highest mark assessed here: {observed_max}")
        if inapplicable:
            print(f"  NOT APPLICABLE (band starts above {observed_max} marks): "
                  f"{', '.join(inapplicable)}")
        if real_empty:
            print(f"  BANDS WITH NOTHING AT ALL: {', '.join(real_empty)}")
        overview.append({
            "subject": subject, "grade": grade, "topics": len(topics),
            "questions": total, "untopiced": untopiced[key],
            "bandTopics": band_topics, "emptyBands": real_empty,
            "inapplicableBands": inapplicable, "observedMaxMarks": observed_max,
        })
        print()

    print("=" * 92)
    print(f"SUMMARY")
    print("=" * 92)
    print(f"  subject x grade pairs : {len(overview)}")
    print(f"  topics (distinct)     : {sum(o['topics'] for o in overview)}")
    print(f"  untopiced questions   : {sum(o['untopiced'] for o in overview)}")
    pairs_no_band = [o for o in overview if o["emptyBands"]]
    print(f"  pairs missing a whole marks band : {len(pairs_no_band)}")
    for o in pairs_no_band:
        print(f"      {o['subject']:<12} class {str(o['grade']):<5} "
              f"no questions at: {', '.join(o['emptyBands'])} marks")
    print()
    print(f"  thin topic x band cells (< {args.min} questions): {len(thin):,}")
    worst = collections.Counter((s, g) for s, g, _c, _b, _n in thin)
    print("  concentrated in:")
    for (s, g), n in worst.most_common(10):
        print(f"      {s:<12} class {str(g):<5} {n:>4} thin cells")

    if args.json:
        args.json.write_text(json.dumps(
            {"overview": overview,
             "thin": [{"subject": s, "grade": g, "topic": c, "band": b, "n": n}
                      for s, g, c, b, n in thin]},
            indent=1), encoding="utf-8")
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
