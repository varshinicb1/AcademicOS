"""Tag every question in the bank to a chapter, and report what could not be tagged.

PRD rule Q2: *"Every question is mapped to a curriculum topic."* Tagging is what
makes this a database rather than a pile of PDFs, and it is what lets a consumer
ask for "5-mark case-based questions on Chemical Reactions and get a real
answer".

Three corpora enter, and they are in very different states:

  * CBE item banks -- already carry CBSE's own learning-ladder content code
    (`6A1a`, `9.1.13`), so their topic is authoritative rather than inferred.
  * SQP+MS -- no code at all; the sample paper does not publish one.
  * Board papers -- no code, and 3,382 of them were measured untagged.

So this does two different things: it KEEPS the authoritative CBE codes, and it
INFERS a chapter for everything else. The two must stay distinguishable in the
output, or an inferred tag will later be read as a CBSE-authored one -- which is
the same failure the topic mapper already guards against by writing to a
separate file.

What it will not do
-------------------
It does not invent a chapter. `tag_questions` returns `(None, 0.0)` when every
candidate scores below its similarity floor, and those stay untagged and are
counted. A confident wrong chapter is worse than a blank, because the blank is
visible in the coverage report and the wrong one is not.

Run:  python scripts/tag_question_bank.py [--check] [--grade 10]

Topics and subtopics (classes 6-10)
-----------------------------------
``--topics BANK.json [BANK.json ...]`` instead tags each bank's questions to
the taxonomy trees (``academicos-data/syllabus/taxonomy``) with
`academicos.syllabus.tagger`, and writes the result INTO each bank file: the
fields ``taxonomyChapterId``, ``topicIds``, ``subtopicIds``, ``tagConfidence``
and ``tagMethod`` are added to each class 6-10 Mathematics / Science / Social
Science record, and nothing else on any record changes. A level whose
confidence is below the gold-set threshold is left empty on the record and
the question goes to ``taxonomy/review_queue.json`` with the tagger's proposal
(a rerun replaces that bank's entries in the queue). ``--check`` prints the
coverage per class and subject and writes nothing.

    python scripts/tag_question_bank.py --topics academicos-data/corpus/ncert-exemplar/questions.json
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

CORPORA = {
    "cbe": REPO / "academicos-data" / "corpus" / "cbse-cbe" / "questions.json",
    "sqp": REPO / "academicos-data" / "corpus" / "cbse-sqp" / "questions.json",
    "board": REPO / "academicos-data" / "syllabus" / "questions.json",
}
OUT = REPO / "academicos-data" / "syllabus" / "chapter_tags.json"

# Grades are stored as ints in some corpora and Roman in others.
_ROMAN = {"vi": 6, "vii": 7, "viii": 8, "ix": 9, "x": 10, "xi": 11, "xii": 12}


def _grade_int(value) -> int:
    if isinstance(value, int):
        return value
    s = str(value or "").strip().lower()
    if s.isdigit():
        return int(s)
    return _ROMAN.get(s, 0)


def _text(rec: dict) -> str:
    return (rec.get("stem") or rec.get("question") or rec.get("text") or "").strip()


def _hash(text: str) -> str:
    return hashlib.sha256(" ".join(text.lower().split()).encode("utf-8")).hexdigest()


# The name Task 703 gives it. The tree tests pick tree files by a case-sensitive
# first capital, so a lower-case name here is not read as a tree on Windows.
REVIEW_QUEUE = REPO / "academicos-data" / "syllabus" / "taxonomy" / "review_queue.json"


def _bank_label(path: Path) -> str:
    """The bank's key in the review queue: repo-relative inside the repo, else the
    full resolved path. Every bank is named questions.json, so a bare file name
    let a second outside bank replace the first one's queue entries.

    Inside-the-repo is read on the absolute path, links unresolved: a checkout
    whose academicos-data is a junction to another drive (D:/AcademicOS-
    academicos-data) resolved every bank to a D: path and keyed the served
    bank's queue entries by it."""
    absolute = Path(os.path.abspath(path))
    for candidate in (absolute, path.resolve()):
        try:
            return candidate.relative_to(REPO).as_posix()
        except ValueError:
            continue
    return path.resolve().as_posix()


def tag_topics(banks: list[Path], check: bool, queue_path: Path) -> int:
    """Tag each bank to chapter/topic/subtopic; see the module docstring."""
    from academicos.syllabus.tagger import LEVELS, TopicTagger, apply_tags

    tagger = TopicTagger()
    review_all: dict[str, list[dict]] = {}
    for path in banks:
        payload = json.loads(path.read_text(encoding="utf-8"))
        label = _bank_label(path)
        records, review = apply_tags(payload["questions"], tagger, bank=label)
        review_all[label] = review
        queued = collections.Counter(r["id"] for r in review)
        cells: dict[tuple, collections.Counter] = collections.defaultdict(collections.Counter)
        for rec in records:
            if "tagMethod" not in rec:
                continue
            c = cells[(rec.get("subject"), int(rec.get("grade")))]
            c["questions"] += 1
            c["chapter"] += bool(rec["taxonomyChapterId"])
            c["topic"] += bool(rec["topicIds"])
            c["subtopic"] += bool(rec["subtopicIds"])
            c["review"] += queued[rec.get("id")] > 0
        print(f"\n{label}  ({len(records):,} records, "
              f"{sum(c['questions'] for c in cells.values()):,} in the trees' scope)")
        print(f"{'subject':<16}{'class':>6}{'questions':>11}{'chapter':>9}{'topic':>7}"
              f"{'subtopic':>10}{'review':>8}")
        total = collections.Counter()
        for (subject, grade), c in sorted(cells.items()):
            total.update(c)
            print(f"{subject:<16}{grade:>6}{c['questions']:>11}{c['chapter']:>9}{c['topic']:>7}"
                  f"{c['subtopic']:>10}{c['review']:>8}")
        print(f"{'all':<22}{total['questions']:>11}{total['chapter']:>9}{total['topic']:>7}"
              f"{total['subtopic']:>10}{total['review']:>8}")
        by_level = collections.Counter(r["level"] for r in review)
        print("review queue by first unaccepted level: "
              + ", ".join(f"{lv} {by_level[lv]}" for lv in LEVELS))
        if not check:
            payload["questions"] = records
            # the banks are written as their builders write them: one line
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            print(f"wrote {label}")
    if check:
        print("\n--check: nothing written")
        return 0
    items: list[dict] = []
    if queue_path.exists():
        old = json.loads(queue_path.read_text(encoding="utf-8"))
        items = [e for e in old.get("items", []) if e.get("bank") not in review_all]
    for label in review_all:
        items.extend(review_all[label])
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    queue_path.write_text(json.dumps({
        "notice": ("Questions whose chapter, topic or subtopic tag fell below the confidence "
                   "threshold that keeps accepted tags >= 90% right on the gold set. Each "
                   "entry names the first level not accepted and the tagger's proposal; the "
                   "proposal is NOT on the question. Each entry also names the method its "
                   "PROPOSED CHAPTER came from -- an Exemplar record queued at the topic "
                   "level has a chapter the book itself printed it under, not one this "
                   "tagger matched -- and `methods` below counts them. It was one method "
                   "for the whole file, which called every entry tfidf_textbook_v2."),
        "methods": dict(collections.Counter(e.get("method") or "unrecorded" for e in items)),
        "builtAt": datetime.now(timezone.utc).isoformat(),
        "counts": dict(collections.Counter(e["bank"] for e in items)),
        "items": items,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {_bank_label(queue_path)}  ({len(items):,} entries)")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report only, write nothing")
    ap.add_argument("--grade", type=int, default=None, help="limit to one grade")
    ap.add_argument("--topics", nargs="+", type=Path, default=None, metavar="BANK",
                    help="tag these bank files to taxonomy topics/subtopics (see docstring)")
    ap.add_argument("--review-queue", type=Path, default=REVIEW_QUEUE)
    args = ap.parse_args(argv)
    if args.topics and args.grade is not None:
        # --topics tags every class 6-10 record in the bank; a --grade that is
        # silently ignored would look like a one-class run that was not one.
        ap.error("--grade cannot be combined with --topics")
    if args.topics:
        return tag_topics(args.topics, args.check, args.review_queue)

    from academicos.assessment.embedding_chapter_tagger import (
        ChapterTagCache, tag_questions,
    )

    records: list[tuple[str, dict]] = []
    for label, path in CORPORA.items():
        if not path.exists():
            print(f"  {label}: missing {path.name}")
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for rec in payload["questions"]:
            records.append((label, rec))
    print(f"questions loaded: {len(records):,}")

    # Group by the subject FAMILY, not the display name.
    #
    # `load_syllabus` is keyed on the CBSE subject ("Mathematics"), while the
    # bank's display name preserves the paper variant ("Mathematics
    # (Standard)"). Looking the syllabus up by display name returned None for
    # every variant, which showed up as a silent 0% tag rate for 133 Mathematics
    # questions rather than as an error. `subjectFamily` exists for exactly this
    # -- reporting AND lookup -- while the display name stays distinct.
    def _lookup_subject(rec: dict) -> str:
        meta = rec.get("metadata") or {}
        return meta.get("subjectFamily") or rec.get("subject") or ""

    by_sg: dict[tuple[str, int], list[tuple[str, dict]]] = collections.defaultdict(list)
    for label, rec in records:
        grade = _grade_int(rec.get("grade"))
        if args.grade and grade != args.grade:
            continue
        by_sg[(_lookup_subject(rec), grade)].append((label, rec))

    cache = ChapterTagCache(REPO / "academicos-data" / "assessment" / "chapter_tags.sqlite")
    tagged: dict[str, dict] = {}
    per_pair: list[tuple[str, int, int, int, float]] = []
    no_syllabus: list[tuple[str, int, int]] = []

    try:
        for (subject, grade), group in sorted(by_sg.items()):
            if not subject or not grade:
                continue
            items = [(_hash(_text(r)), _text(r)) for _label, r in group]
            items = [(h, t) for h, t in items if t]
            if not items:
                continue
            from academicos.syllabus.cbse_syllabus import load_syllabus
            if load_syllabus(subject, grade) is None:
                # No CBSE chapters for this subject/grade. That is a coverage
                # fact, not a tagging failure, and conflating the two would make
                # the report read as though the tagger was broken.
                no_syllabus.append((subject, grade, len(items)))
                continue
            try:
                result = tag_questions(cache, subject=subject,
                                       grade_label=str(grade), grade_int=grade,
                                       items=items)
            except Exception as exc:                      # pragma: no cover
                print(f"  {subject} {grade}: tagging failed ({type(exc).__name__}: {exc})")
                continue
            hits = 0
            scores = []
            for (label, rec), (h, _t) in zip(group, [(_hash(_text(r)), 0) for _l, r in group]):
                chapter, score = result.get(h, (None, 0.0))
                if chapter:
                    tagged[rec["id"]] = {
                        "chapterId": chapter,
                        "score": round(score, 4),
                        "subject": subject,
                        "grade": grade,
                        "method": "embedding_chapter_v1",
                        "source": label,
                    }
                    hits += 1
                    scores.append(score)
            per_pair.append((subject, grade, len(items), hits,
                             sum(scores) / len(scores) if scores else 0.0))
    finally:
        cache.close()

    print()
    print(f"{'subject':<20} {'gr':>3} {'asked':>6} {'tagged':>7} {'cov':>5} {'mean sim':>9}")
    print("-" * 58)
    for subject, grade, n, hits, mean in per_pair:
        print(f"{subject:<20} {grade:>3} {n:>6} {hits:>7} "
              f"{hits / max(1, n):>5.0%} {mean:>9.2f}")

    if no_syllabus:
        n = sum(x[2] for x in no_syllabus)
        print(f"\nno CBSE syllabus for this subject/grade: {len(no_syllabus)} pairs, "
              f"{n} questions")
        for subject, grade, count in sorted(no_syllabus, key=lambda x: -x[2])[:14]:
            print(f"    {subject:<24} {grade:<3} {count:>4}")
        if len(no_syllabus) > 14:
            print(f"    ... and {len(no_syllabus) - 14} more")

    total_asked = sum(p[2] for p in per_pair)
    total_tagged = sum(p[3] for p in per_pair)
    print()
    print(f"tagged {total_tagged:,} of {total_asked:,} "
          f"({total_tagged / max(1, total_asked):.0%})")

    # Coverage against the curriculum itself: which chapters got NOTHING.
    from academicos.syllabus.cbse_syllabus import load_syllabus
    gaps = []
    for (subject, grade), group in sorted(by_sg.items()):
        syl = load_syllabus(subject, grade)
        if syl is None:
            continue
        by_chapter = collections.Counter(
            t["chapterId"] for t in tagged.values()
            if t["subject"] == subject and t["grade"] == grade)
        for _unit, ch in syl.all_chapters():
            if not by_chapter.get(ch.id):
                gaps.append((subject, grade, ch.name))
    print(f"chapters with no tagged question: {len(gaps)}")
    for subject, grade, name in gaps[:25]:
        print(f"    {subject:<18} {grade:<3} {name[:56]}")
    if len(gaps) > 25:
        print(f"    ... and {len(gaps) - 25} more")

    if args.check:
        print("\n--check: nothing written")
        return 0

    OUT.write_text(json.dumps({
        "notice": ("Chapter tags INFERRED by embedding similarity to CBSE "
                   "chapter anchors. NOT authored by CBSE. The CBE corpus's own "
                   "learning-ladder codes remain authoritative where present."),
        "method": "embedding_chapter_v1",
        "builtAt": datetime.now(timezone.utc).isoformat(),
        "count": len(tagged),
        "asked": total_asked,
        "tags": tagged,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nwrote {OUT.relative_to(REPO)}  ({len(tagged):,} tags)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
