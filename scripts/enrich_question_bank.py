"""Enrich the question bank: relink official marking schemes, and fill the
standalone-asset fields.

Run:  python scripts/enrich_question_bank.py [--check]

What it does, in order:

  1. Relink. Walks `question -> parse tree -> paper code -> answer_keys.db` and
     attaches the official CBSE marking scheme where one exists. Never invents
     an answer; a question with no match is left without a scheme and counted.
  2. Enrich. Sets `rights`, `calibration`, `version`, `reviewState`, `language`,
     and page-level `provenance`.
  3. Writes both copies of the corpus (the server-side one and the Flutter
     asset) so they cannot drift.

Idempotent: re-running does not double-bump versions or overwrite a rights
decision someone has since recorded. `--check` verifies without writing, for CI.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from academicos.assessment.question_bank import (          # noqa: E402
    AnswerKeyIndex,
    enrich_all,
    relink_answer_schemes,
)

TARGETS = [
    REPO / "academicos-data" / "syllabus" / "questions.json",
    REPO / "frontend" / "assets" / "corpus" / "questions.json",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="report only; do not write")
    args = ap.parse_args()

    data_root = REPO / "academicos-data"
    primary = TARGETS[0]
    if not primary.exists():
        print(f"missing corpus: {primary}", file=sys.stderr)
        return 1

    payload = json.loads(primary.read_text(encoding="utf-8"))
    records = payload.get("questions") or []
    print(f"loaded {len(records):,} questions from {primary.relative_to(REPO)}")

    index = AnswerKeyIndex(data_root / "answer_keys.db")
    stats = index.stats()
    print("answer key index: {rows_keyed:,} of {rows_total:,} rows indexed "
          "across {distinct_codes:,} paper codes".format(**stats))
    print()

    report = relink_answer_schemes(records, index, parse_dir=data_root / "parse")
    print("relink")
    for line in report.lines():
        print("  " + line)
    print()

    census = enrich_all(records)
    print("enrichment")
    for k, v in census.items():
        print(f"  {k:<24} {v:,}")
    print()

    payload["questions"] = records
    payload["exportedCount"] = len(records)
    # Surfaced in the payload so a consumer can see the bank's own honesty
    # about how much of it carries an official scheme.
    payload["schemeCoverage"] = round(
        census["with_official_scheme"] / len(records), 4) if records else 0.0

    if args.check:
        print("--check: nothing written")
        return 0

    text = json.dumps(payload, ensure_ascii=False)
    for target in TARGETS:
        target.parent.mkdir(parents=True, exist_ok=True)
        before = target.stat().st_size if target.exists() else 0
        target.write_text(text, encoding="utf-8")
        delta = target.stat().st_size - before
        print(f"wrote {target.relative_to(REPO)}  "
              f"({target.stat().st_size / 1_000_000:.1f} MB, {delta:+,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
