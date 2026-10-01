"""Every question held, as a matrix.

The question bank has been assembled from six corpora plus a generated one, and
the number that matters is not the total but where the questions are. A bank of
nine thousand questions that is entirely grade 10 is worth less to a school than
one thousand questions spread over grades 1-10, so this prints subject against
grade rather than a headline count.
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

CORPUS = ROOT / "academicos-data" / "corpus"
SERVED = ROOT / "academicos-data" / "syllabus" / "questions.json"

GRADES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

# What each corpus is, and whether its questions are official -- lifted from a
# board paper or a book -- or generated. Mixing the two in a single total is how a
# bank ends up claiming coverage it has not earned.
CORPORA = [
    ("cbse-board", "CBSE board papers", "official"),
    ("cbse-sqp", "CBSE SQP papers", "official"),
    ("cbse-sqpt", "CBSE SQP sample papers", "official"),
    ("cbse-cbe", "CBSE competency banks", "official"),
    ("ncert-exemplar", "NCERT exemplar", "official"),
    ("ncert-textbook", "NCERT textbook exercises", "mixed"),
    ("ai-cbse", "AI generated, CBSE format", "generated"),
]


def load(path: Path) -> list[dict]:
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("questions") or []
    except (OSError, ValueError):
        return []


def subject_of(question: dict) -> str:
    """The subject, as the taxonomy names it.

    A paper variant -- "Mathematics (Standard, VIC)" -- has no syllabus file of
    its own and uses its base subject's chapters, so it is reported under the base
    rather than as a subject in its own right.
    """
    raw = str(question.get("subject") or "?").strip()
    base = raw.split("(")[0].strip()
    return base or raw


def main() -> int:
    print("=" * 118)
    print("QUESTIONS BY CORPUS".center(118))
    print("=" * 118)
    print("%-16s %-28s %-10s %8s %7s" % ("corpus", "what it is", "kind", "total", "grades"))
    print("-" * 118)

    by_corpus: dict[str, list[dict]] = {}
    for name, description, kind in CORPORA:
        path = CORPUS / name / "questions.json"
        if not path.is_file():
            print("%-16s %-28s %-10s %8s" % (name, description, kind, "-"))
            continue
        questions = load(path)
        by_corpus[name] = questions
        grades = sorted({q.get("grade") for q in questions if q.get("grade")})
        span = (f"{grades[0]}-{grades[-1]}" if len(grades) > 2
                else ",".join(str(g) for g in grades))
        print("%-16s %-28s %-10s %8d %7s" % (name, description, kind,
                                             len(questions), span))

    everything = [q for questions in by_corpus.values() for q in questions]
    print("-" * 118)
    print("%-16s %-28s %-10s %8d" % ("TOTAL", "", "", len(everything)))
    print()
    generated = sum(len(v) for k, v in by_corpus.items() if k == "ai-cbse")
    print(f"  generated {generated:,}   official/collected {len(everything) - generated:,}")

    # -- the matrix --------------------------------------------------------- #
    print()
    print("=" * 118)
    print("SUBJECT x GRADE   (all corpora)".center(118))
    print("=" * 118)
    grid: dict[tuple[str, int], int] = defaultdict(int)
    for question in everything:
        grid[(subject_of(question), int(question.get("grade") or 0))] += 1
    subjects = sorted({s for s, _ in grid})
    header = " " * 30 + "".join(f"{g:>7}" for g in GRADES) + f"{'total':>9}"
    print(header)
    print("-" * len(header))
    for subject in subjects:
        cells = "".join(f"{grid.get((subject, g), 0) or '.':>7}" for g in GRADES)
        total = sum(grid.get((subject, g), 0) for g in GRADES)
        print(f"{subject[:29]:<30}{cells}{total:>9}")
    print("-" * len(header))
    cells = "".join(f"{sum(grid.get((s, g), 0) for s in subjects) or '.':>7}"
                    for g in GRADES)
    print(f"{'TOTAL':<30}{cells}{len(everything):>9}")

    # -- what the school can actually print --------------------------------- #
    print()
    print("=" * 118)
    print("BY CBSE SECTION TYPE   (what a paper is made of)".center(118))
    print("=" * 118)
    types = Counter(str(q.get("type") or "?") for q in everything)
    width = max(len(t) for t in types) + 2
    for qtype, count in types.most_common():
        print(f"  {qtype:<{width}} {count:>7}  {'#' * min(60, count // max(1, len(everything) // 60))}")

    # -- the generated bank, which is the part still filling ---------------- #
    if "ai-cbse" in by_corpus:
        ai = by_corpus["ai-cbse"]
        print()
        print("=" * 118)
        print("GENERATED (ai-cbse) IN DETAIL".center(118))
        print("=" * 118)
        print("  total          :", len(ai))
        print("  by grade       :", dict(sorted(
            (g, c) for g, c in Counter(q.get("grade") for q in ai).items() if g)))
        print("  by subject     :", dict(Counter(subject_of(q) for q in ai).most_common()))
        print("  by section     :", dict(Counter(
            (q.get("provenance") or {}).get("section") for q in ai).most_common()))
        print("  by type        :", dict(Counter(q.get("type") for q in ai).most_common()))
        print("  by source      :", dict(Counter(q.get("source") for q in ai).most_common()))
        print("  chapters       :", len({q.get("taxonomyChapterId") for q in ai
                                           if q.get("taxonomyChapterId")}), "distinct")

    # -- the served bank --------------------------------------------------- #
    print()
    print("=" * 118)
    print("SERVED BANK (what a student can be served today)".center(118))
    print("=" * 118)
    if SERVED.is_file():
        served = load(SERVED)
        print(f"  {SERVED}")
        print(f"  questions      : {len(served):,}")
        print("  by grade       :", dict(sorted(
            (g, c) for g, c in Counter(q.get("grade") for q in served).items() if g)))
        official = sum(1 for q in served if str(q.get("source") or "").startswith("cbse"))
        print(f"  official board : {official:,}")
    else:
        print("  not present in this worktree")

    # -- the gap ------------------------------------------------------------ #
    print()
    print("=" * 118)
    print("WHERE THE BANK IS EMPTY".center(118))
    print("=" * 118)
    empty = [(s, g) for s in subjects for g in GRADES if not grid.get((s, g))]
    by_grade = Counter(g for _, g in empty)
    print(f"  subject x grade cells with no questions at all: {len(empty)} of "
          f"{len(subjects) * len(GRADES)}")
    for grade, count in sorted(by_grade.items()):
        print(f"     grade {grade:>2}: {count} subjects empty")
    ai_grades = {q.get("grade") for q in by_corpus.get("ai-cbse", [])}
    missing_gen = [g for g in GRADES if g not in ai_grades]
    if missing_gen:
        print(f"  grades with no generated question yet: {missing_gen}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
