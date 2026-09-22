"""Enrich the question bank: relink official marking schemes, and fill the
standalone-asset fields.

Run:  python scripts/enrich_question_bank.py [--check]

What it does, in order:

  1. Relink. Walks `question -> parse tree -> paper code -> answer_keys.db` and
     attaches the official CBSE marking scheme the content join finds for it
     across every set of its paper series, where the verifier accepts one.
     Never invents an answer; a question with no verified scheme is left with
     none (the merge then excludes it as no-verified-key) and counted.
  2. Enrich. Sets `rights`, `calibration`, `version`, `reviewState`, `language`,
     and page-level `provenance`.
  3. Writes both copies of the corpus (the server-side one and the Flutter
     asset) so they cannot drift, stamped `schemeVerifier` with the verifier
     it ran: merge_question_banks.py refuses a bank without that stamp, so
     it cannot serve labels this relink has not seen.
  4. Adds every scheme the relink removed to scheme_quarantine.json, next to
     the served bank, whole (marking points, model answer, option letter,
     scheme file). It merges, never overwrites: a rerun finds almost nothing
     left to remove, so an overwrite would lose the review list.

  5. Relinks the board records the merge withheld as no-verified-key too,
     read from board_withheld.json next to the served bank and written back
     there whole (never into the served files), so a later, better join can
     re-attach a key.

A record whose own verified scheme and the join's accepted pick name
different answers keeps neither: both go to the quarantine as
conflicting-keys, and each is printed by id with both answers.

Run this BEFORE merge_question_banks.py, and again after it: the merge's
no-verified-key gate reads the labels and stamps this relink writes, and
serves a withheld record this relink verified.

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
    SCHEME_VERIFIER,
    AnswerKeyIndex,
    enrich_all,
    relink_answer_schemes,
)
from academicos.corpus import bank_merge                     # noqa: E402

TARGETS = [
    REPO / "academicos-data" / "syllabus" / "questions.json",
    REPO / "frontend" / "assets" / "corpus" / "questions.json",
]
# Next to the served bank: every scheme the relink removed, and why.
QUARANTINE = REPO / "academicos-data" / "syllabus" / "scheme_quarantine.json"


def print_subject_grade_table(records: list[dict], report, had_official: set) -> None:
    """Per subject and grade: records, official before, verified after, and the
    quarantined records split so no column overlaps another's meaning:
    `replaced` had a scheme quarantined and a verified official attached in
    its place (it is counted in `verified` too); `quarantined` had a scheme
    quarantined and ends with none verified; `conflicts`, among those, had
    two official keys naming different answers."""
    quarantined = {e["id"] for e in report.quarantine}
    conflicted = {c["id"] for c in report.conflicts}
    rows: dict[tuple[str, str], list[int]] = {}
    for r in records:
        key = (str(r.get("subject") or "?"), str(r.get("grade") or "?"))
        row = rows.setdefault(key, [0, 0, 0, 0, 0, 0])
        verified = (r.get("answerScheme") or {}).get("provenance") == "cbse_marking_scheme"
        removed = r.get("id") in quarantined
        row[0] += 1
        row[1] += r.get("id") in had_official
        row[2] += verified
        row[3] += removed and verified
        row[4] += removed and not verified
        row[5] += r.get("id") in conflicted
    fmt = "{:<26} {:>5} {:>8} {:>9} {:>9} {:>9} {:>12} {:>10}"
    print(fmt.format("subject", "grade", "records", "labelled", "verified", "replaced",
                     "quarantined", "conflicts"))
    print("  (labelled = cbse_marking_scheme before the relink; verified = after;")
    print("   replaced = scheme quarantined, a verified official attached instead,")
    print("   and counted in verified; quarantined = scheme removed, none verified;")
    print("   conflicts = of those, two official keys named different answers)")
    num = "{:<26} {:>5} {:>8,} {:>9,} {:>9,} {:>9,} {:>12,} {:>10,}"
    for (subject, grade), vals in sorted(rows.items()):
        print(num.format(subject[:26], grade, *vals))
    tot = [sum(v[i] for v in rows.values()) for i in range(6)]
    print(num.format("total", "", *tot))


QUARANTINE_ABOUT = (
    "Schemes removed from served records because the relink rejected them for "
    "their question. For a person to review and, if right, restore: each entry "
    "keeps the whole removed scheme ('scheme'), its option letter and its scheme "
    "file. See src/academicos/corpus/scheme_verify.py and "
    "src/academicos/assessment/question_bank.py (unbacked-key) for each "
    "reason. Every run ADDS to this file and never drops an entry: "
    "after one run the served bank no longer holds what was removed, so a "
    "rerun finds almost nothing, and overwriting would lose the review list.")


def _answer(a: dict) -> str:
    words = " ".join(str(a.get("text") or "").split())
    words = words if len(words) <= 60 else words[:57] + "..."
    return f"{a.get('option') or '-'} {words}".strip()


def print_conflicts(report) -> None:
    """Every record whose two official keys disagree, with both answers, so a
    person can settle it; neither is served until then."""
    if not report.conflicts:
        return
    print(f"conflicting official keys, neither served ({len(report.conflicts):,}):")
    print("  (id  code Qn: the record's own scheme  |  the join's pick  [pick's row])")
    for c in report.conflicts:
        join = c["join"]
        print(f"  {c['id']}  {c['code']} Q{c['q_no']}: {_answer(c['existing'])}  |  "
              f"{_answer(join)}  [{join.get('code')} Q{join.get('qNo')}, {join.get('source')}]")
    print()


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

    # Board records the merge withheld as no-verified-key live only in
    # board_withheld.json. They are relinked with the served ones (in one
    # pass, so each finds its siblings in the other), so that a better join
    # can re-attach a key the next merge then serves, and written back there.
    held_path = primary.with_name(bank_merge.WITHHELD_NAME)
    held_all = bank_merge.load_withheld(held_path)
    served_ids = {r.get("id") for r in records}
    held = [r for r in held_all if r.get("id") not in served_ids]
    if held_all:
        print(f"plus {len(held):,} withheld board records from {_rel(held_path)} "
              f"(relinked, written back there, never served from here)")
        print()

    had_official = {r.get("id") for r in records + held
                    if (r.get("answerScheme") or {}).get("provenance") == "cbse_marking_scheme"}
    report = relink_answer_schemes(records + held, index, parse_dir=data_root / "parse")
    print("relink")
    for line in report.lines():
        print("  " + line)
    print()
    print_conflicts(report)
    print_subject_grade_table(records + held, report, had_official)
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
    payload["schemeVerifier"] = SCHEME_VERIFIER

    if check:
        print(f"--check: nothing written (would add up to "
              f"{len(report.quarantine):,} schemes to {_rel(quarantine)})")
        return 0

    saved = write_quarantine(quarantine, report.quarantine)
    print(f"wrote {_rel(quarantine)}  ({len(report.quarantine):,} this run, "
          f"{len(saved['entries']):,} entries in all)")
    if held:
        bank_merge.write_withheld(held_path, bank_merge.hold(held_all, held))
        print(f"wrote {_rel(held_path)}  ({len(held):,} relinked)")

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
