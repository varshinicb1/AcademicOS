"""Compose the served question bank from board papers, CBE and SQP.

Run AFTER the builders and the chapter tagger:

    build_cbe_bank.py   build_sqp_bank.py
    tag_question_bank.py
    apply_chapter_tags.py
    merge_question_banks.py        <- this
    enrich_question_bank.py

It writes academicos-data/syllabus/questions.json and its APK copy,
frontend/assets/corpus/questions.json, byte-identical, plus every record it left
out and why in academicos-data/syllabus/_merge_excluded.json. The rules live in
src/academicos/corpus/bank_merge.py; this file only does the I/O.

It refuses a source with no chapter tags. Re-running a builder discards the tags
apply_chapter_tags.py wrote, and merging such a source ships class 6-9 with no
chapter a paper blueprint can select on.

Run:  python scripts/merge_question_banks.py [--check]
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from academicos.corpus import bank_merge  # noqa: E402


@dataclass
class Paths:
    served: Path
    apk: Path
    cbe: Path
    sqp: Path
    excluded: Path


DEFAULT = Paths(
    served=REPO / "academicos-data" / "syllabus" / "questions.json",
    apk=REPO / "frontend" / "assets" / "corpus" / "questions.json",
    cbe=REPO / "academicos-data" / "corpus" / "cbse-cbe" / "questions.json",
    sqp=REPO / "academicos-data" / "corpus" / "cbse-sqp" / "questions.json",
    excluded=REPO / "academicos-data" / "syllabus" / "_merge_excluded.json",
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _has_official_scheme(rec: dict) -> bool:
    scheme = rec.get("answerScheme") or {}
    return scheme.get("provenance") == "cbse_marking_scheme" and bool(
        scheme.get("markingPoints") or (scheme.get("modelAnswer") or "").strip())


def _chapter_names(questions: list[dict]) -> dict[tuple[str, int, str], str]:
    """(subject, grade, chapter id) -> chapter name, from the syllabus files."""
    from academicos.syllabus.cbse_syllabus import load_syllabus

    names: dict[tuple[str, int, str], str] = {}
    for subject, grade in {(q.get("subject"), q.get("grade")) for q in questions}:
        syllabus = load_syllabus(subject, grade) if subject and grade else None
        if syllabus is None:
            continue
        for _unit, chapter in syllabus.all_chapters():
            names[(subject, grade, chapter.id)] = chapter.name
    return names


def run(paths: Paths, *, check: bool) -> int:
    served, cbe, sqp = _load(paths.served), _load(paths.cbe), _load(paths.sqp)
    for name, payload in (("CBE", cbe), ("SQP", sqp)):
        if payload.get("questions") and not payload.get("chapterTaggedAt"):
            print(f"refusing: the {name} bank carries no chapter tags -- "
                  f"run scripts/apply_chapter_tags.py first")
            return 2

    result = bank_merge.compose(served["questions"], cbe["questions"], sqp["questions"])
    questions = bank_merge.apply_chapter_names(result.questions, _chapter_names(result.questions))
    covered = sum(1 for q in questions if _has_official_scheme(q))

    # Deterministic, so re-running on unchanged sources gives identical bytes:
    # the timestamp comes from the sources, not the clock, and every key this
    # script writes is rebuilt in a fixed order. (Carrying a previous run's
    # composedFrom/composedAt forward would move them ahead of "questions" on
    # the second run and change the bytes although nothing else had.)
    composed_at = max(str(p.get("builtAt") or "") for p in (cbe, sqp)) or None
    written_here = ("questions", "exportedCount", "schemeCoverage", "composedFrom", "composedAt")
    payload = {k: v for k, v in served.items() if k not in written_here}
    payload.update({
        "questions": questions,
        "exportedCount": len(questions),
        "schemeCoverage": round(covered / len(questions), 4) if questions else 0.0,
        "composedFrom": result.counts,
        "composedAt": composed_at,
    })

    reasons = collections.Counter((e["source"], e["reason"]) for e in result.excluded)
    print(f"composed {len(questions):,} questions  {result.counts}")
    print(f"excluded {len(result.excluded):,}")
    for (source, reason), n in reasons.most_common():
        print(f"  {n:5,}  {str(source):20s} {reason}")
    print("by grade:", dict(sorted(collections.Counter(q.get("grade") for q in questions).items())))
    print(f"official scheme coverage: {covered:,}/{len(questions):,}")
    if check:
        print("\n--check: nothing written")
        return 0

    body = json.dumps(payload, ensure_ascii=False)
    for target in (paths.served, paths.apk):
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(target.suffix + ".tmp")
        tmp.write_text(body, encoding="utf-8")
        os.replace(tmp, target)
    paths.excluded.write_text(json.dumps(
        {"excluded": result.excluded, "counts": dict(collections.Counter(
            e["reason"] for e in result.excluded))}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(f"\nwrote {paths.served}\nwrote {paths.apk}\nwrote {paths.excluded}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="report only; write nothing")
    return run(DEFAULT, check=ap.parse_args().check)


if __name__ == "__main__":
    raise SystemExit(main())
