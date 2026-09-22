"""Read-only paper-template presets: class 6-10, five main subjects, four exam types.

A teacher should never start from a blank builder. Every (class, subject,
exam type) here is a complete, exactly-summing template; "use as starting
point" copies one into the teacher's own templates (see
paper_template_routes.duplicate), and the copy is what they edit.

Where each pattern comes from -- said in each preset's `source` so a teacher
(or a principal checking the paper) can verify it:

* **Class 10, annual, Mathematics, Science, Social Science** -- `cbse_board`,
  read (Task 904, PyMuPDF) from the General Instructions on page 3 of the
  CBSE 2025 class X board papers in `cbse-dataset/question-papers/
  question-paper/2025/X/` (set 1 of each: `041_Mathematics_Standard.zip` ->
  `30-1-1_Mathematics Standard.pdf`, `086_Science.zip` -> `31-1-1_Science.pdf`,
  `087_Social_Science.zip` -> `32-1-1_Social Science.pdf`). Every section
  count and mark value below matches those pages. The 2024-25 SQP PDFs the
  earlier version cited are not on this machine (the corpus holds only
  their extracted text and download manifest), so the board papers are the
  evidence now; the Mathematics design is also in the SQP text
  (`academicos-data/corpus/cbse-sqp/questions.json`).
  The 2026 board papers regroup Science by discipline (Biology 30 /
  Chemistry 25 / Physics 25, `2026/X/Science.zip` -> `31-2-1.pdf` p. 3) and
  Social Science into four 20-mark discipline sections with the map item
  split in two (`2026/X/Social_Science.zip` -> `1165-1_32-4-1_Social Sc..pdf`
  p. 3); the question kinds and mark values are unchanged, so the 2025 A-E/F
  design is kept.
  What a template cannot hold: the board's internal choice is an OR
  alternative inside a question (Mathematics: 2 questions in B, 2 in C, 2 in
  D, 3 in E), not "attempt any N of M". The presets print one question per
  slot and say so in their source line.
* **Class 9, every subject** -- `suggested`. CBSE sets no class IX paper; the
  annual preset applies the class X board design, which is what most schools
  do, and is labelled as such.
* **English and Hindi, every class** -- `suggested`. The board papers are
  passage-based (a 10-mark reading passage is one "question" with sub-parts),
  which the bank does not hold as such. English keeps the 2025 board paper's
  section weights at question level, read from `2025/X/
  184_English_Language_and_Literature.zip` -> `2-1-1_English Language and
  Literature.pdf`: Reading 20 (p. 2), Grammar "any ten of twelve" + two
  5-mark writing tasks = 20 (pp. 8-12), Literature 40 = two extracts,
  "any four of five" and "any two of three" 3-mark answers, two 6-mark long
  answers (pp. 13-19). Hindi uses the same rows but is NOT checked against a
  Hindi paper: the 2025 Hindi board PDFs' text does not extract (their
  Devanagari is in an unmapped font), and the source line says so.
* **Class 6-8, every subject, and every unit test / periodic test** --
  `suggested`: CBSE prescribes no paper design for these. They are common
  school patterns, labelled as a suggestion, not a CBSE rule.
* **Half-yearly, class 9-10** -- `suggested`: the board design applied to the
  half-yearly, which is what most CBSE schools do but not a CBSE rule.

Difficulty mixes are suggestions in every case: CBSE does not publish a
per-section difficulty split.

Long-answer, case-based and map sections carry the question kind they
promise (`_types_for`), so a source item cannot fill a long-answer heading
and a map section is a gap, not any 5-mark question, when the bank has no map
question at that mark value.
"""
from __future__ import annotations

from functools import lru_cache

from .schemas import DifficultyDistribution, PaperTemplate, TemplateHeader, TemplateSection

MAIN_SUBJECTS: tuple[str, ...] = ("Mathematics", "Science", "Social Science", "English", "Hindi")
PRESET_EXAM_TYPES: tuple[str, ...] = ("unit_test", "periodic", "half_yearly", "annual")

_EXAM_NAMES = {
    "unit_test": "Unit Test",
    "periodic": "Periodic Test",
    "half_yearly": "Half-Yearly Examination",
    "annual": "Annual Examination",
}
_DURATION = {"unit_test": 40, "periodic": 90, "half_yearly": 180, "annual": 180}
# The total each exam type is meant to carry. Passed to the model as the
# template's total (not summed from the rows), so a row table that drifts
# from it fails `PaperTemplateDraft`'s exact-totals check at import.
_TOTAL = {"unit_test": 20, "periodic": 40, "half_yearly": 80, "annual": 80}

# Suggested difficulty mix by mark value: short items lean easy, long ones hard.
_MIX = {
    1: DifficultyDistribution(easy=0.5, medium=0.4, hard=0.1),
    2: DifficultyDistribution(easy=0.4, medium=0.5, hard=0.1),
    3: DifficultyDistribution(easy=0.3, medium=0.5, hard=0.2),
    4: DifficultyDistribution(easy=0.2, medium=0.5, hard=0.3),
    5: DifficultyDistribution(easy=0.2, medium=0.4, hard=0.4),
    6: DifficultyDistribution(easy=0.2, medium=0.4, hard=0.4),
}

# (title, questions, marks each, attempt or None, competency share or None)
_Row = tuple[str, int, int, "int | None", "float | None"]

_BOARD: dict[str, list[_Row]] = {
    "Mathematics": [
        ("Section A - Objective (MCQ / assertion-reason)", 20, 1, None, None),
        ("Section B - Very short answer", 5, 2, None, None),
        ("Section C - Short answer", 6, 3, None, None),
        ("Section D - Long answer", 4, 5, None, None),
        ("Section E - Case-study based", 3, 4, None, 1.0),
    ],
    "Science": [
        ("Section A - Objective (MCQ / assertion-reason)", 20, 1, None, None),
        ("Section B - Very short answer", 6, 2, None, None),
        ("Section C - Short answer", 7, 3, None, None),
        ("Section D - Long answer", 3, 5, None, None),
        ("Section E - Source / case based", 3, 4, None, 1.0),
    ],
    "Social Science": [
        ("Section A - Objective (MCQ)", 20, 1, None, None),
        ("Section B - Very short answer", 4, 2, None, None),
        ("Section C - Short answer", 5, 3, None, None),
        ("Section D - Long answer", 4, 5, None, None),
        ("Section E - Case / source based", 3, 4, None, 1.0),
        ("Section F - Map skill", 1, 5, None, None),
    ],
}

_QP = "cbse-dataset/question-papers/question-paper/2025/X/"
_NO_OR = (" Internal choice on the board paper is an OR alternative inside a "
          "question{which}; this preset prints one question per slot.")

_BOARD_SOURCE = {
    "Mathematics": (
        "CBSE Class X board paper 2025, Mathematics (Standard), General Instructions, "
        f"{_QP}041_Mathematics_Standard.zip -> 30-1-1_Mathematics Standard.pdf, p. 3: "
        "A 18 MCQ + 2 assertion-reason x1, B 5x2, C 6x3, D 4x5, E 3 case studies x4 = 80. "
        "The same design is in the 2024-25 and 2025-26 SQP text "
        "(academicos-data/corpus/cbse-sqp)."
        + _NO_OR.format(which=" (2 in B, 2 in C, 2 in D, 3 in E)")),
    "Science": (
        "CBSE Class X board paper 2025, Science, General Instructions, "
        f"{_QP}086_Science.zip -> 31-1-1_Science.pdf, p. 3: A 20 MCQ x1 (assertion-"
        "reason items among them), B 6x2, C 7x3, D 3x5, E 3 source/case-based units "
        "x4 = 80. The 2026 paper regroups these as Biology 30 / Chemistry 25 / "
        "Physics 25 (2026/X/Science.zip -> 31-2-1.pdf, p. 3)."
        + _NO_OR.format(which=" (in some sections)")),
    "Social Science": (
        "CBSE Class X board paper 2025, Social Science, General Instructions, "
        f"{_QP}087_Social_Science.zip -> 32-1-1_Social Science.pdf, p. 3: A 20 MCQ x1, "
        "B 4x2, C 5x3, D 4x5, E 3 case/source-based x4, F one map question of 5 "
        "(History 2 + Geography 3) = 80. The 2026 paper regroups these into four "
        "20-mark discipline sections (2026/X/Social_Science.zip -> "
        "1165-1_32-4-1_Social Sc..pdf, p. 3)."
        + _NO_OR.format(which="")),
}

# Language papers at question level, keeping the SQP's weights (see module doc).
_LANGUAGE_80: list[_Row] = [
    ("Section A - Reading comprehension", 20, 1, None, 1.0),
    ("Section B - Grammar (attempt any 10)", 12, 1, 10, None),
    ("Section B - Writing", 2, 5, None, None),
    ("Section C - Literature: extract based", 10, 1, None, None),
    ("Section C - Literature: short answer (attempt any 4)", 5, 3, 4, None),
    # Q9 of the 2025 board paper: "any two of the following three" at 3 marks
    # (p. 17). The earlier 3 x 2-mark row matched no paper.
    ("Section C - Literature: short answer II (attempt any 2)", 3, 3, 2, None),
    ("Section C - Literature: long answer (attempt any 2)", 3, 6, 2, None),
]

# Class 6-8 school pattern for the term exams, maths / science / social science.
_JUNIOR_80: list[_Row] = [
    ("Section A - Objective", 16, 1, None, None),
    ("Section B - Very short answer", 8, 2, None, None),
    ("Section C - Short answer", 8, 3, None, None),
    ("Section D - Long answer", 4, 5, None, None),
    ("Section E - Case based", 1, 4, None, 1.0),
]
_JUNIOR_LANGUAGE_80: list[_Row] = [
    ("Section A - Reading comprehension", 15, 1, None, 1.0),
    ("Section B - Grammar", 15, 1, None, None),
    ("Section C - Writing", 2, 5, None, None),
    ("Section D - Literature: extract based", 10, 1, None, None),
    ("Section D - Literature: short answer", 6, 3, None, None),
    ("Section D - Literature: long answer", 2, 6, None, None),
]

_PERIODIC_40: list[_Row] = [
    ("Section A - Objective", 10, 1, None, None),
    ("Section B - Very short answer", 4, 2, None, None),
    ("Section C - Short answer", 4, 3, None, None),
    ("Section D - Long answer", 2, 5, None, None),
]
_PERIODIC_LANGUAGE_40: list[_Row] = [
    ("Section A - Reading comprehension", 10, 1, None, 1.0),
    ("Section B - Grammar", 10, 1, None, None),
    ("Section C - Writing", 1, 5, None, None),
    ("Section D - Literature: extract based", 5, 1, None, None),
    ("Section D - Literature: long answer", 2, 5, None, None),
]

_UNIT_20: list[_Row] = [
    ("Section A - Objective", 6, 1, None, None),
    ("Section B - Very short answer", 4, 2, None, None),
    ("Section C - Short answer", 2, 3, None, None),
]
_UNIT_LANGUAGE_20: list[_Row] = [
    ("Section A - Reading comprehension", 5, 1, None, 1.0),
    ("Section B - Grammar", 5, 1, None, None),
    ("Section C - Writing", 1, 5, None, None),
    ("Section D - Literature", 5, 1, None, None),
]

_SUGGESTED_SOURCE = (
    "Suggested school pattern, not a CBSE rule: CBSE prescribes no paper design "
    "for {what}. Edit it to match your school.")


def _pattern(grade: int, subject: str, exam_type: str) -> tuple[list[_Row], str, str]:
    """(rows, pattern_status, source) for one preset."""
    language = subject in ("English", "Hindi")
    if exam_type == "unit_test":
        return (_UNIT_LANGUAGE_20 if language else _UNIT_20, "suggested",
                _SUGGESTED_SOURCE.format(what="unit tests"))
    if exam_type == "periodic":
        return (_PERIODIC_LANGUAGE_40 if language else _PERIODIC_40, "suggested",
                _SUGGESTED_SOURCE.format(what="periodic tests"))
    if grade >= 9 and not language:
        rows = _BOARD[subject]
        if exam_type == "annual" and grade == 10:
            return rows, "cbse_board", _BOARD_SOURCE[subject]
        if exam_type == "annual":
            # No CBSE paper exists for class IX to check a preset against.
            return rows, "suggested", (
                "Suggested: CBSE sets no class IX paper; this is the class X board "
                "design, which most schools use for class IX. Class X design: "
                + _BOARD_SOURCE[subject])
        return rows, "suggested", (
            "Suggested: the CBSE board design applied to the half-yearly, as most "
            "CBSE schools do; not a CBSE rule. Board design: " + _BOARD_SOURCE[subject])
    if language and grade >= 9:
        if subject == "English":
            return _LANGUAGE_80, "suggested", (
                "Suggested: keeps the CBSE Class X English board paper 2025's section "
                "weights at question level (Reading 20, Grammar + Writing 20, "
                f"Literature 40), read from {_QP}184_English_Language_and_Literature.zip "
                "-> 2-1-1_English Language and Literature.pdf, pp. 2-19. The paper "
                "itself is passage-based and not reproduced exactly.")
        return _LANGUAGE_80, "suggested", (
            "Suggested: a question-level language pattern (Reading 20, Grammar + "
            f"Writing 20, Literature 40). Not checked against a CBSE {subject} paper: "
            "the Hindi board papers' text does not extract from the PDFs on this "
            "server. Edit it to match your school.")
    return (_JUNIOR_LANGUAGE_80 if language else _JUNIOR_80), "suggested", \
        _SUGGESTED_SOURCE.format(what=f"class {grade} term examinations")


def _slug(text: str) -> str:
    return text.lower().replace(" ", "-")


def _instructions(sections: list[TemplateSection]) -> str:
    lines = [f"This question paper has {len(sections)} sections."]
    for s in sections:
        attempt = (f" Attempt any {s.attempts}." if s.attempts < s.question_count else "")
        lines.append(f"{s.title}: {s.question_count} question(s) of {s.marks_each} "
                     f"mark(s) each.{attempt}")
    lines.append("All questions are compulsory unless a choice is stated.")
    return "\n".join(lines)


def _types_for(title: str) -> list[str]:
    """The question kind a heading promises, where the engine can check it.

    Without this every section was matched by marks alone, and the class 10
    Social Science annual preset reported itself complete while printing
    "Read the given source" items under "Long answer" and outline-map items
    under "Case based". The engine reads map and case / source from the
    question text (paper_templates._content_fits), not from the bank's
    mark-derived type label, so these filters do not empty the real long
    answers (labelled case_study at 5 marks) or case studies (labelled
    long_answer at 4). Other headings (objective, short answer, grammar...)
    stay untyped: nothing in the bank could check them, and the engine says
    so for the ones that name a kind."""
    low = title.lower()
    if "map" in low:
        return ["map_based"]
    if "case" in low:
        return ["case_study"]
    if "long answer" in low:
        return ["long_answer", "very_long_answer"]
    return []


def _build(grade: int, subject: str, exam_type: str) -> PaperTemplate:
    rows, status, source = _pattern(grade, subject, exam_type)
    sections = [
        TemplateSection(
            id=f"s{i + 1}", title=title, question_count=count, marks_each=marks,
            attempt_count=attempt, difficulty_mix=_MIX.get(marks),
            competency_share=competency, question_types=_types_for(title),
        )
        for i, (title, count, marks, attempt, competency) in enumerate(rows)
    ]
    exam_name = _EXAM_NAMES[exam_type]
    return PaperTemplate(
        id=f"preset:cbse:{grade}:{_slug(subject)}:{exam_type}",
        school_id="",
        name=f"Class {grade} {subject} - {exam_name}",
        grade=grade,
        subject=subject,
        exam_type=exam_type,
        total_marks=_TOTAL[exam_type],
        duration_minutes=_DURATION[exam_type],
        instructions=_instructions(sections),
        header=TemplateHeader(exam_name=exam_name),
        sections=sections,
        is_preset=True,
        pattern_status=status,
        source=source,
    )


@lru_cache(maxsize=1)
def _all() -> tuple[PaperTemplate, ...]:
    return tuple(
        _build(grade, subject, exam_type)
        for grade in range(6, 11)
        for subject in MAIN_SUBJECTS
        for exam_type in PRESET_EXAM_TYPES
    )


def presets(*, grade: int | None = None, subject: str | None = None) -> list[PaperTemplate]:
    """Copies, so a caller mutating one can never change the next caller's preset."""
    return [
        p.model_copy(deep=True) for p in _all()
        if (grade is None or p.grade == grade)
        and (subject is None or p.subject.lower() == subject.lower())
    ]


def get_preset(preset_id: str) -> PaperTemplate | None:
    for p in _all():
        if p.id == preset_id:
            return p.model_copy(deep=True)
    return None


def is_preset_id(template_id: str) -> bool:
    return template_id.startswith("preset:")
