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
  4. Adds every scheme the relink removed to scheme_quarantine.json, next to
     the served bank. It merges, never overwrites: a rerun finds almost
     nothing left to remove, so an overwrite would lose the review list.

Idempotent: re-running does not double-bump versions or overwrite a rights
decision someone has since recorded. `--check` verifies without writing, for CI.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
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
# Next to the served bank: every scheme the relink removed, and why.
QUARANTINE = REPO / "academicos-data" / "syllabus" / "scheme_quarantine.json"


def print_subject_grade_table(records: list[dict], report, had_official: set) -> None:
    """Per subject and grade: records, official before, verified after, quarantined."""
    quarantined = {e["id"] for e in report.quarantine}
    rows: dict[tuple[str, str], list[int]] = {}
    for r in records:
        key = (str(r.get("subject") or "?"), str(r.get("grade") or "?"))
        row = rows.setdefault(key, [0, 0, 0, 0])
        row[0] += 1
        row[1] += r.get("id") in had_official
        row[2] += (r.get("answerScheme") or {}).get("provenance") == "cbse_marking_scheme"
        row[3] += r.get("id") in quarantined
    print("{:<26} {:>5} {:>8} {:>9} {:>9} {:>12}".format(
        "subject", "grade", "records", "labelled", "verified", "quarantined"))
    print("  (labelled = cbse_marking_scheme before the relink; verified = after)")
    for (subject, grade), (n, before, after, quar) in sorted(rows.items()):
        print("{:<26} {:>5} {:>8,} {:>9,} {:>9,} {:>12,}".format(
            subject[:26], grade, n, before, after, quar))
    tot = [sum(v[i] for v in rows.values()) for i in range(4)]
    print("{:<26} {:>5} {:>8,} {:>9,} {:>9,} {:>12,}".format("total", "", *tot))


QUARANTINE_ABOUT = (
    "Schemes removed from served records because the relink rejected them for "
    "their question. For a person to review; see "
    "src/academicos/corpus/scheme_verify.py and "
    "src/academicos/assessment/question_bank.py (conflicting-keys, unbacked-key) "
    "for each reason. Every run ADDS to this file and never drops an entry: "
    "after one run the served bank no longer holds what was removed, so a "
    "rerun finds almost nothing, and overwriting would lose the review list.")


def _entry_key(e: dict) -> tuple:
    return (e.get("id"), e.get("reason"), e.get("text"))


def write_quarantine(path: Path, entries: list[dict]) -> dict:
    """Merge `entries` into the quarantine file at `path`; returns what was written.

    Keyed by (id, reason, text): the same removal seen twice is one entry, a
    different scheme removed from the same record later is a second one.
    Existing entries keep their order and are never dropped.
    """
    existing: list[dict] = []
    if path.exists():
        existing = list(json.loads(path.read_text(encoding="utf-8")).get("entries") or [])
    seen = {_entry_key(e) for e in existing}
    merged = list(existing)
    for e in entries:
        if _entry_key(e) not in seen:
            seen.add(_entry_key(e))
            merged.append(e)
    counts = Counter(str(e.get("reason")) for e in merged)
    out = {"about": QUARANTINE_ABOUT, "counts": dict(sorted(counts.items())),
           "entries": merged}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="report only; do not write")
    args = ap.parse_args()
    return run(targets=TARGETS, quarantine=QUARANTINE,
               data_root=REPO / "academicos-data", check=args.check)


def run(*, targets: list[Path], quarantine: Path, data_root: Path, check: bool) -> int:
    primary = targets[0]
    if not primary.exists():
        print(f"missing corpus: {primary}", file=sys.stderr)
        return 1

    payload = json.loads(primary.read_text(encoding="utf-8"))
    records = payload.get("questions") or []
    print(f"loaded {len(records):,} questions from {_rel(primary)}")

    index = AnswerKeyIndex(data_root / "answer_keys.db")
    stats = index.stats()
    print("answer key index: {rows_keyed:,} of {rows_total:,} rows indexed "
          "across {distinct_codes:,} paper codes".format(**stats))
    print()

    had_official = {r.get("id") for r in records
                    if (r.get("answerScheme") or {}).get("provenance") == "cbse_marking_scheme"}
    report = relink_answer_schemes(records, index, parse_dir=data_root / "parse")
    print("relink")
    for line in report.lines():
        print("  " + line)
    print()
    print_subject_grade_table(records, report, had_official)
    print()

    census = enrich_all(records)
    print("enrichment")
    for k, v in census.items():
        print(f"  {k:<24} {v:,}")
    print()

    payload["questions"] = records
    payload["exportedCount"] = len(records)
    # Surfaced in the payload so a consumer can see the bank's own honesty
    # about how much of it carries an official scheme. Since Task 15 the relink
    # labels cbse_marking_scheme only on schemes `scheme_verify` accepted, so
    # this counts VERIFIED official schemes, not links to an answer key.
    payload["schemeCoverage"] = round(
        census["with_official_scheme"] / len(records), 4) if records else 0.0

    if check:
        print(f"--check: nothing written (would add up to "
              f"{len(report.quarantine):,} schemes to {_rel(quarantine)})")
        return 0

    saved = write_quarantine(quarantine, report.quarantine)
    print(f"wrote {_rel(quarantine)}  ({len(report.quarantine):,} this run, "
          f"{len(saved['entries']):,} entries in all)")

    text = json.dumps(payload, ensure_ascii=False)
    for target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        before = target.stat().st_size if target.exists() else 0
        target.write_text(text, encoding="utf-8")
        delta = target.stat().st_size - before
        print(f"wrote {_rel(target)}  "
              f"({target.stat().st_size / 1_000_000:.1f} MB, {delta:+,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
