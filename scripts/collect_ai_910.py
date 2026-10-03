"""Collect the per-chapter files oc_bank_batch.py writes into the one corpus file the merge reads.

    python scripts/collect_ai_910.py            # writes corpus/ai-cbse-9-10/questions.json
    python scripts/collect_ai_910.py --check    # only the report

Every record must still be labelled `textbook_grounded` with its quotes (the merge refuses
the rest too); a record that is not is reported and left out. Ids are unique across the
file. Deterministic: sorted by id, no clock in the output, so unchanged chapters give
identical bytes. The served bank is not touched: scripts/merge_question_banks.py reads
this file as its `ai` source.
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.corpus.bank_merge import ai_not_grounded  # noqa: E402

DIR = ROOT / "academicos-data" / "corpus" / "ai-cbse-9-10"


def collect(directory: Path = DIR) -> tuple[list[dict], list[tuple[str, str]], list[str]]:
    """(records, (id, why) left out, chapter files read)."""
    records: dict[str, dict] = {}
    left_out: list[tuple[str, str]] = []
    files = sorted(p for p in directory.glob("*-[0-9][0-9]*.json"))
    for path in files:
        for rec in json.loads(path.read_text(encoding="utf-8")).get("questions", []):
            rid = str(rec.get("id"))
            if ai_not_grounded(rec):
                left_out.append((rid, "not grounded"))
            elif rid in records:
                left_out.append((rid, "duplicate id"))
            else:
                records[rid] = rec
    return [records[k] for k in sorted(records)], left_out, [p.name for p in files]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="report only; write nothing")
    ap.add_argument("--dir", type=Path, default=DIR)
    args = ap.parse_args()
    records, left_out, files = collect(args.dir)
    by = collections.Counter((r["subject"], r["grade"], r["type"]) for r in records)
    print(f"{len(records)} records from {len(files)} chapter files; {len(left_out)} left out")
    for (subject, grade, qtype), n in sorted(by.items()):
        print(f"  {subject:16s} class {grade:<3d} {qtype:20s} {n}")
    for rid, why in left_out[:20]:
        print(f"  left out: {rid} ({why})")
    if args.check:
        return 0
    out = args.dir / "questions.json"
    out.write_text(json.dumps({"questions": records, "source": "ai-cbse-9-10", "chapterFiles": files},
                              ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
