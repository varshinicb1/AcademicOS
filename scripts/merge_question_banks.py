"""Compose the served question bank from board papers, CBE, SQP and NCERT Exemplar.

Run AFTER the builders, the chapter tagger and the relink:

    build_cbe_bank.py   build_sqp_bank.py
    tag_question_bank.py
    apply_chapter_tags.py
    enrich_question_bank.py        relinks and verifies the board schemes
    merge_question_banks.py        <- this
    enrich_question_bank.py        again: fills the added records' asset fields

It refuses a served bank enrich_question_bank.py has not stamped with the
current scheme verifier (`schemeVerifier`, question_bank.SCHEME_VERIFIER).
The merge serves the board records the relink verified; run before the
relink, or after a relink under older rules, it would serve labels no current
verifier has seen. --allow-no-board does not override this.

It writes academicos-data/syllabus/questions.json and its APK copy,
frontend/assets/corpus/questions.json, byte-identical, plus every record it left
out and why in academicos-data/syllabus/_merge_excluded.json. The rules live in
src/academicos/corpus/bank_merge.py; this file only does the I/O.

A board record the no-verified-key gate withholds is kept whole in
academicos-data/syllabus/board_withheld.json, which this script and
enrich_question_bank.py both read back and neither overwrites: the board
records come from the served file this script replaces, and
_merge_excluded.json keeps 200 characters of a stem and is rewritten every
run, so without it a withheld question would leave the pipeline for good.

It refuses, unless --allow-no-board is given, a board input none of whose
records carries a verified key: that is a bank enrich_question_bank.py has not
relinked yet, and writing it would serve no board question at all.

It refuses a source with no chapter tags. Re-running a builder discards the tags
apply_chapter_tags.py wrote, and merging such a source ships class 6-9 with no
chapter a paper blueprint can select on.

The NCERT Exemplar bank (academicos-data/corpus/ncert-exemplar/questions.json,
build_exemplar_bank.py) is read when it exists and gated like CBE and SQP
(bank_merge.compose), after them, so a CBSE copy of a question wins. It is not
held to the chapter-tag rule: its builder tags a chapter from the book's own
chapter title, and apply_chapter_tags.py never writes it.

Every record's symbol-font characters are restored before the gates read it
(bank_merge.repair_symbol_font), and one still holding a private-use character
is excluded; every chapter id the (subject, grade) syllabus does not know --
a raw CBE content code such as "10A2b" -- is resolved to the chapter the
record names or dropped (bank_merge.resolve_chapter_ids), so no teacher is
offered "10A2B" as a chapter and no chapter is listed twice.

Board records are gated like CBE and SQP ones (bank_merge.exclusion_reason),
after the repairs that are certain (bank_merge.repair_board); --check prints
what each reason removes, the repairs, and the served count by subject and
grade before and after. `--check --relink-in-memory` measures that on a
relinked copy of the served and withheld board records -- the relink
enrich_question_bank.py runs, done in memory and stamped in memory -- so the
gate can be measured before the tracked bank is relinked. It writes nothing,
and without --check it is refused.

Run:  python scripts/merge_question_banks.py [--check [--relink-in-memory]]
"""
from __future__ import annotations

import argparse
import collections
import copy
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from academicos.assessment.question_bank import SCHEME_VERIFIER  # noqa: E402
from academicos.corpus import bank_merge  # noqa: E402


@dataclass
class Paths:
    served: Path
    apk: Path
    cbe: Path
    sqp: Path
    excluded: Path
    # The NCERT Exemplar bank; no file (or None) serves none.
    exemplar: Path | None = None
    # The NCERT taxonomy trees, which name a record's taxonomyChapterId.
    taxonomy: Path | None = None
    # Withheld board records, whole. Next to `excluded` unless named.
    held: Path | None = None
    # What --relink-in-memory reads: the answer-key index and the parse trees.
    answer_keys: Path | None = None
    parse_dir: Path | None = None
    # Papers transcribed with their official schemes (corpus/transcribed.py),
    # and NCERT textbook exercises (corpus/textbook.py); no file serves none.
    transcribed: Path | None = None
    textbook: Path | None = None
    # Questions a model wrote from a chapter, collected by collect_ai_910.py; served only
    # where grounded (bank_merge.ai_not_grounded). No file serves none.
    ai: Path | None = None

    @property
    def withheld(self) -> Path:
        return self.held or self.excluded.with_name(bank_merge.WITHHELD_NAME)


DEFAULT = Paths(
    served=REPO / "academicos-data" / "syllabus" / "questions.json",
    apk=REPO / "frontend" / "assets" / "corpus" / "questions.json",
    cbe=REPO / "academicos-data" / "corpus" / "cbse-cbe" / "questions.json",
    sqp=REPO / "academicos-data" / "corpus" / "cbse-sqp" / "questions.json",
    excluded=REPO / "academicos-data" / "syllabus" / "_merge_excluded.json",
    exemplar=REPO / "academicos-data" / "corpus" / "ncert-exemplar" / "questions.json",
    taxonomy=REPO / "academicos-data" / "syllabus" / "taxonomy",
    answer_keys=REPO / "academicos-data" / "answer_keys.db",
    parse_dir=REPO / "academicos-data" / "parse",
    transcribed=REPO / "academicos-data" / "corpus" / "cbse-board" / "questions.json",
    textbook=REPO / "academicos-data" / "corpus" / "ncert-textbook" / "questions.json",
    ai=REPO / "academicos-data" / "corpus" / "ai-cbse-9-10" / "questions.json",
)


def _optional(path: Path | None) -> list[dict]:
    """The questions of an optional source bank, or none."""
    return _load(path)["questions"] if path is not None and path.exists() else []


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _has_official_scheme(rec: dict) -> bool:
    scheme = rec.get("answerScheme") or {}
    return scheme.get("provenance") == "cbse_marking_scheme" and bool(
        scheme.get("markingPoints") or (scheme.get("modelAnswer") or "").strip())


def _chapter_names(questions: list[dict]) -> dict[tuple[str, int, str], str]:
    """(subject, grade, chapter id) -> chapter name, from the syllabus files.

    A paper variant ('Mathematics (Standard)', 'Mathematics (Basic, VIC)') has
    no syllabus file of its own but uses its base subject's chapter ids, so it
    falls back to the base syllabus and keeps its own subject in the key.
    """
    from academicos.syllabus.cbse_syllabus import load_syllabus

    names: dict[tuple[str, int, str], str] = {}
    for subject, grade in {(q.get("subject"), q.get("grade")) for q in questions}:
        syllabus = load_syllabus(subject, grade) if subject and grade else None
        if syllabus is None and subject and grade:
            base = re.sub(r"\s*\(.*\)$", "", subject)
            if base != subject:
                syllabus = load_syllabus(base, grade)
        if syllabus is None:
            continue
        for _unit, chapter in syllabus.all_chapters():
            names[(subject, grade, chapter.id)] = chapter.name
    return names


def _chapters_by_grade(names: dict[tuple[str, int, str], str]) -> dict[tuple[str, int], dict]:
    """`_chapter_names` regrouped as resolve_chapter_ids reads it: one chapter
    id -> name map per (subject, grade)."""
    out: dict[tuple[str, int], dict[str, str]] = {}
    for (subject, grade, chapter_id), name in names.items():
        out.setdefault((subject, grade), {})[chapter_id] = name
    return out


def _taxonomy_names(path: Path | None) -> dict[str, str]:
    """Taxonomy chapter id -> name, from the NCERT taxonomy trees (Task 703).

    The tagger writes `taxonomyChapterId` on a record; only the tree names it,
    and that name is what a raw CBE content code is resolved against.
    """
    names: dict[str, str] = {}
    for tree in sorted((path or Path()).glob("*.json")) if path and path.exists() else []:
        if tree.name.startswith("_") or tree.name == "review_queue.json":
            continue
        for chapter in json.loads(tree.read_text(encoding="utf-8")).get("chapters") or []:
            if chapter.get("id") and chapter.get("name"):
                names[chapter["id"]] = chapter["name"]
    return names


def _relink_in_memory(served: dict, held: list[dict], paths: Paths) -> tuple[dict, list[dict]]:
    """Copies of the served bank and the withheld board records, relinked as
    enrich_question_bank.py relinks them -- in one pass, so each finds its
    siblings in the other -- and stamped with the verifier, in memory only."""
    from academicos.assessment import question_bank

    served, held = copy.deepcopy(served), copy.deepcopy(held)
    ids = {r.get("id") for r in served["questions"]}
    index = question_bank.AnswerKeyIndex(paths.answer_keys)
    question_bank.relink_answer_schemes(
        served["questions"] + [r for r in held if r.get("id") not in ids], index,
        parse_dir=paths.parse_dir)
    served["schemeVerifier"] = SCHEME_VERIFIER
    return served, held


def _by_subject_grade(before: list[dict], after: list[dict]) -> None:
    """Served count per subject and grade: in the served file now, and what
    this merge serves (all sources, and board only)."""
    key = lambda q: (str(q.get("subject")), q.get("grade") if isinstance(q.get("grade"), int) else -1)
    was = collections.Counter(key(q) for q in before)
    now = collections.Counter(key(q) for q in after)
    board = collections.Counter(key(q) for q in after if q.get("source") == bank_merge.BOARD_SOURCE)
    print("served by subject x grade (before = the served file now; after = this merge):")
    print(f"  {'subject':32s} {'grade':>5s} {'before':>8s} {'after':>8s} {'board':>8s}")
    for subject, grade in sorted(set(was) | set(now)):
        print(f"  {subject[:32]:32s} {grade:5d} {was[(subject, grade)]:8d} "
              f"{now[(subject, grade)]:8d} {board[(subject, grade)]:8d}")


def run(paths: Paths, *, check: bool, allow_no_board: bool = False,
        relink_in_memory: bool = False) -> int:
    if relink_in_memory and not check:
        print("refusing: --relink-in-memory measures a relinked copy and writes nothing; "
              "pass it with --check (scripts/enrich_question_bank.py relinks for real)")
        return 2
    served, cbe, sqp = _load(paths.served), _load(paths.cbe), _load(paths.sqp)
    exemplar = (_load(paths.exemplar) if paths.exemplar and paths.exemplar.exists()
                else {"questions": []})
    held = bank_merge.load_withheld(paths.withheld)
    if relink_in_memory:
        served, held = _relink_in_memory(served, held, paths)
        print(f"relinked in memory: {len(served['questions']):,} served and "
              f"{len(held):,} withheld records (nothing written)")
    stamp = served.get("schemeVerifier")
    if stamp != SCHEME_VERIFIER:
        seen = f"its stamp is {stamp!r}" if stamp else "it carries no stamp"
        print(f"refusing: the served bank has not been through the scheme verifier "
              f"{SCHEME_VERIFIER!r} ({seen}), so its board labels are not verified -- "
              f"run scripts/enrich_question_bank.py first, then this")
        return 2
    for name, payload in (("CBE", cbe), ("SQP", sqp)):
        if payload.get("questions") and not payload.get("chapterTaggedAt"):
            print(f"refusing: the {name} bank carries no chapter tags -- "
                  f"run scripts/apply_chapter_tags.py first")
            return 2

    result = bank_merge.compose(served["questions"], cbe["questions"], sqp["questions"],
                                held=held, exemplar=exemplar["questions"],
                                transcribed=_optional(paths.transcribed), textbook=_optional(paths.textbook),
                                ai=_optional(paths.ai))
    names = _chapter_names(result.questions)
    questions, chapter_ids = bank_merge.resolve_chapter_ids(
        result.questions, _chapters_by_grade(names), _taxonomy_names(paths.taxonomy))
    questions = bank_merge.apply_chapter_names(questions, names)
    covered = sum(1 for q in questions if _has_official_scheme(q))

    # Deterministic, so re-running on unchanged sources gives identical bytes:
    # the timestamp comes from the sources, not the clock, and every key this
    # script writes is rebuilt in a fixed order. (Carrying a previous run's
    # composedFrom/composedAt forward would move them ahead of "questions" on
    # the second run and change the bytes although nothing else had.)
    composed_at = max(str(p.get("builtAt") or "") for p in (cbe, sqp, exemplar)) or None
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
    # A raw CBE content code is never offered as a chapter: it is resolved to
    # the syllabus chapter the record names, or dropped (Task 121).
    print(f"chapter ids resolved to a syllabus chapter: {chapter_ids['resolved']:,}; "
          f"dropped, no chapter named: {chapter_ids['dropped']:,}")
    print(f"chapter ids the syllabus cannot name (non-board): "
          f"{bank_merge.unresolved_chapters(questions, names):,}")
    print(f"records with no chapter id (non-board): "
          f"{bank_merge.untagged_chapters(questions):,}")
    shared = bank_merge.shared_chapter_labels(questions)
    if shared:
        print("chapter labels shared by several chapter ids:")
        for (subject, grade), labels in sorted(shared.items(), key=lambda kv: (str(kv[0][0]), kv[0][1] or 0)):
            for label, cids in sorted(labels.items()):
                print(f"  {subject} {grade}: {label!r} covers {', '.join(cids)}")
    print(f"board records withheld, kept whole in {paths.withheld.name}: "
          f"{len(result.withheld):,}")
    print("repairs: " + (", ".join(f"{name} {n:,}" for name, n in sorted(result.repairs.items()))
                               or "none"))
    _by_subject_grade(served["questions"], questions)
    # Board records exist but not one carries the relink's stamp: the bank has
    # not been through enrich_question_bank.py since it was built, and a write
    # now would ship a bank with no board question and still exit 0. The
    # records would survive in the withheld file, but a silent collapse of the
    # served bank is the bad ship this pipeline refuses.
    if result.withheld and not result.counts["board"] and not allow_no_board:
        print(f"\nrefusing: none of the {len(result.withheld):,} board records carries "
              f"a verified key, so the served bank would have no board question -- "
              f"run scripts/enrich_question_bank.py first "
              f"(or pass --allow-no-board to write it anyway)")
        return 2
    if check:
        print("\n--check: nothing written")
        return 0

    # The withheld records first: a board record leaving the served file is
    # kept somewhere before that file is replaced.
    bank_merge.write_withheld(paths.withheld, bank_merge.hold(held, result.withheld))
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
    print(f"\nwrote {paths.withheld}\nwrote {paths.served}\nwrote {paths.apk}"
          f"\nwrote {paths.excluded}")
    return 0


def main() -> int:
    # Chapter labels carry the source's own text. On a Windows console the
    # default cp1252 codec cannot encode all of it, and the report died
    # mid-table with UnicodeEncodeError on the first non-Latin label.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="report only; write nothing")
    ap.add_argument("--allow-no-board", action="store_true",
                    help="write even when every board record is withheld")
    ap.add_argument("--relink-in-memory", action="store_true",
                    help="with --check: measure on a copy relinked and stamped in memory")
    args = ap.parse_args()
    return run(DEFAULT, check=args.check, allow_no_board=args.allow_no_board,
               relink_in_memory=args.relink_in_memory)


if __name__ == "__main__":
    raise SystemExit(main())
