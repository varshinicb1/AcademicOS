"""Write the question bank's health report: docs/bank-health.md and
academicos-data/syllabus/bank_health.json.

Per class 6-10 x Mathematics, Science, Social Science, English, Hindi: how many
questions, how many keyed and from where, how many tagged to chapter / topic /
subtopic, the marks distribution, every chapter and topic with its question
count -- and the empty ones -- and whether each paper preset can be filled.
See `academicos.syllabus.bank_health` for what counts.

Run:  python scripts/bank_health.py [--served BANK] [--bank BANK ...] [--check]

Defaults: the served bank (academicos-data/syllabus/questions.json) plus the
NCERT Exemplar and CBE source banks. ``--check`` prints the summary and writes
nothing. Both outputs carry the date and each input file's sha256, so a report
can be matched to the banks it was made from.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

DATA = REPO / "academicos-data"
SERVED = DATA / "syllabus" / "questions.json"
EXTRA = [DATA / "corpus" / "ncert-exemplar" / "questions.json",
         DATA / "corpus" / "cbse-cbe" / "questions.json"]
# What the merge refused, written beside the bank it wrote.
EXCLUDED = DATA / "syllabus" / "_merge_excluded.json"
TAXONOMY = DATA / "syllabus" / "taxonomy"
OUT_MD = REPO / "docs" / "bank-health.md"
OUT_JSON = DATA / "syllabus" / "bank_health.json"


def _rel(path: Path) -> str:
    """Repo-relative inside the repo, else the full path. Read on the absolute
    path first, links unresolved: this checkout's academicos-data is a junction
    to D:/AcademicOS-academicos-data, and resolved, every input was named by
    its D: path (as in tag_question_bank._bank_label)."""
    for candidate in (Path(os.path.abspath(path)), path.resolve()):
        try:
            return candidate.relative_to(REPO).as_posix()
        except ValueError:
            continue
    return path.resolve().as_posix()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _label(path: Path, served: bool) -> str:
    # every bank is named questions.json; its folder names it
    return "served" if served else Path(os.path.abspath(path)).parent.name


def load_trees(taxonomy: Path) -> dict:
    trees = {}
    for f in sorted(taxonomy.glob("*.json")):
        if f.name.startswith("_") or f.name == "review_queue.json":
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        trees[(data["subject"], int(data["grade"]))] = data
    return trees


def main(argv: list[str] | None = None) -> int:
    from academicos.syllabus.bank_health import build_report, render_markdown, tagging_accuracy

    ap = argparse.ArgumentParser()
    ap.add_argument("--served", type=Path, default=SERVED, help="the bank served today")
    ap.add_argument("--bank", type=Path, nargs="*", default=EXTRA, help="extra source banks")
    ap.add_argument("--taxonomy", type=Path, default=TAXONOMY)
    ap.add_argument("--excluded", type=Path, default=EXCLUDED,
                    help="what the merge refused (_merge_excluded.json)")
    ap.add_argument("--md", type=Path, default=OUT_MD)
    ap.add_argument("--json", type=Path, default=OUT_JSON)
    ap.add_argument("--check", action="store_true", help="print the summary, write nothing")
    args = ap.parse_args(argv)

    paths = [(args.served, True)] + [(p, False) for p in args.bank]
    labels = [_label(p, s) for p, s in paths]
    if len(set(labels)) != len(labels):
        ap.error(f"two banks would share a label: {labels}")
    banks, inputs = {}, []
    for (path, is_served), label in zip(paths, labels):
        records = json.loads(path.read_text(encoding="utf-8"))["questions"]
        banks[label] = records
        inputs.append({"label": label, "path": _rel(path), "sha256": _sha256(path),
                       "records": len(records)})

    # Absent is reported as absent, not as "nothing was refused": the report
    # prints no exclusion section at all rather than an authoritative zero.
    exclusions = None
    if args.excluded.exists():
        exclusions = json.loads(args.excluded.read_text(encoding="utf-8"))["excluded"]
        inputs.append({"label": "excluded", "path": _rel(args.excluded),
                       "sha256": _sha256(args.excluded), "records": len(exclusions)})
    else:
        print(f"note: {_rel(args.excluded)} is missing; "
              "the report will not say what the merge left out")

    report = build_report(banks, load_trees(args.taxonomy), served="served",
                          exclusions=exclusions)
    report["builtAt"] = datetime.now(timezone.utc).date().isoformat()
    report["inputs"] = inputs
    if exclusions is not None:
        report["excludedPath"] = _rel(args.excluded)
    audit_files = [args.taxonomy / n for n in
                   ("_tagger_model.json", "_tag_audit.json", "_tag_audit_chapter_topic.json")]
    model, audit_sub, audit_ct = (json.loads(f.read_text(encoding="utf-8")) for f in audit_files)
    report["tagging"] = tagging_accuracy(model, audit_sub, audit_ct)
    report["taxonomyInputs"] = [{"path": _rel(f), "sha256": _sha256(f)} for f in audit_files]

    print(f"{'subject':<16}{'class':>6}{'questions':>11}{'keyed':>7}{'chapter%':>10}"
          f"{'topic%':>8}{'cbq%':>7}{'board(all)':>12}{'left out':>10}")
    for c in report["cells"]:
        board = c["papers"]["all"].get("board", {}).get("possible")
        left = c.get("excluded", {}).get("n", "-")
        print(f"{c['subject']:<16}{c['grade']:>6}{c['questions']:>11}{c['keyed']:>7}"
              f"{c['tagged']['chapter']['pct']:>10}{c['tagged']['topic']['pct']:>8}"
              f"{c['competency']['all']['pct']:>7}{str(board):>12}{str(left):>10}")
    if exclusions is not None:
        ex = report["excluded"]
        print(f"\nthe merge refused {ex['records']:,} records, {ex['inScope']:,} in scope; "
              "commonest reasons: "
              + ", ".join(f"{r} {n:,}" for r, n in list(ex["byReason"].items())[:5]))
    if args.check:
        print("\n--check: nothing written")
        return 0
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    args.md.parent.mkdir(parents=True, exist_ok=True)
    args.md.write_text(render_markdown(report), encoding="utf-8")
    print(f"\nwrote {_rel(args.json)} and {_rel(args.md)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
