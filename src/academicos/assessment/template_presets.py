"""Read-only paper-template presets: class 6-10, five main subjects, four exam types.

A teacher should never start from a blank builder. Every (class, subject,
exam type) here is a complete, exactly-summing template; "use as starting
point" copies one into the teacher's own templates (see
paper_template_routes.duplicate), and the copy is what they edit.

Where each pattern comes from -- said in each preset's `source` so a teacher
(or a principal checking the paper) can verify it:

* **Class 10 and 9, annual, Mathematics** -- `cbse_board`. The section design
  is read from the SQP text in the corpus
  (`academicos-data/corpus/cbse-sqp/questions.json`, question banks
  `cbse-sqp:ClassX_2024_25:Mathematics (Standard)` and `..._2025_26:...`):
  "Section A consists of 20 questions of 1 mark each", B 5 x 2, C 6 x 3,
  D 4 x 5, E "3 case study based questions of 4 marks each" = 80.
* **Class 10 and 9, annual, Science and Social Science** -- `cbse_board`, read
  from the General Instructions of the SQP PDFs themselves
  (`cbse-sqp/ClassX_2024_25/Science-SQP.pdf` and `SocialScience-SQP.pdf` in
  the academicos-data corpus; the extracted `questions.json` text does not
  carry those instructions). Science: A 16 MCQ + 4 assertion-reason x 1,
  B 6 x 2, C 7 x 3, D 3 x 5, E 3 case units x 4 = 80. Social Science: A 20 x 1,
  B 4 x 2, C 5 x 3, D 4 x 5, E 3 x 4, F one map question of 5 (2 History +
  3 Geography) = 80. The 2025-26 SQPs regroup the same papers by discipline
  (Science: Biology / Chemistry / Physics; Social Science: four 20-mark
  sections) and the Science one states that the 2024-25 assessment scheme
  continues, so the 2024-25 section design is the one used.
* **Class 9** uses the class 10 design: CBSE publishes an SQP for class X (and
  XII) only, and the class IX paper follows the same design.
* **English and Hindi, every class** -- `suggested`. Their SQPs are
  passage-based (a 10-mark reading passage is one "question" with sub-parts),
  which the bank does not hold as such; the preset keeps the SQP's section
  weights (Reading 20 / Grammar + Writing 20 / Literature 40 of 80) at
  question level.
* **Class 6-8, every subject, and every unit test / periodic test** --
  `suggested`: CBSE prescribes no paper design for these. They are common
  school patterns, labelled as a suggestion, not a CBSE rule.
* **Half-yearly, class 9-10** -- `suggested`: the board design applied to the
  half-yearly, which is what most CBSE schools do but not a CBSE rule.

Difficulty mixes are suggestions in every case: CBSE does not publish a
per-section difficulty split.
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
        ("Section E - Case based", 3, 4, None, 1.0),
        ("Section F - Map skill", 1, 5, None, None),
    ],
}

_BOARD_SOURCE = {
    "Mathematics": (
        "CBSE SQP Class X Mathematics (Standard) 2024-25 and 2025-26 General "
        "Instructions, read from the SQP text in academicos-data/corpus/cbse-sqp: "
        "A 20x1, B 5x2, C 6x3, D 4x5, E 3x4 = 80."),
    "Science": (
        "CBSE SQP Class X Science 2024-25 General Instructions, read from "
        "cbse-sqp/ClassX_2024_25/Science-SQP.pdf in academicos-data: A 16 MCQ + "
        "4 assertion-reason x1, B 6x2, C 7x3, D 3x5, E 3x4 = 80. The 2025-26 SQP "
        "keeps this scheme, regrouped as Biology / Chemistry / Physics."),
    "Social Science": (
        "CBSE SQP Class X Social Science 2024-25 General Instructions, read from "
        "cbse-sqp/ClassX_2024_25/SocialScience-SQP.pdf in academicos-data: A 20x1, "
        "B 4x2, C 5x3, D 4x5, E 3x4, F map 5 (History 2 + Geography 3) = 80. The "
        "2025-26 SQP keeps these question types, regrouped into four 20-mark "
        "discipline sections."),
}

# Language papers at question level, keeping the SQP's weights (see module doc).
_LANGUAGE_80: list[_Row] = [
    ("Section A - Reading comprehension", 20, 1, None, 1.0),
    ("Section B - Grammar (attempt any 10)", 12, 1, 10, None),
    ("Section B - Writing", 2, 5, None, None),
    ("Section C - Literature: extract based", 10, 1, None, None),
    ("Section C - Literature: short answer (attempt any 4)", 5, 3, 4, None),
    ("Section C - Literature: long answer (attempt any 2)", 3, 6, 2, None),
    ("Section C - Literature: very short answer", 3, 2, None, None),
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
        if exam_type == "annual":
            src = _BOARD_SOURCE[subject]
            if grade == 9:
                src = ("Class IX follows the class X paper design; CBSE publishes "
                       "the SQP for class X. " + src)
            return rows, "cbse_board", src
        return rows, "suggested", (
            "Suggested: the CBSE board design applied to the half-yearly, as most "
            "CBSE schools do; not a CBSE rule. Board design: " + _BOARD_SOURCE[subject])
    if language and grade >= 9:
        return _LANGUAGE_80, "suggested", (
            f"Suggested: keeps the CBSE Class X {subject} SQP's section weights "
            "(Reading 20, Grammar + Writing 20, Literature 40) at question level. "
            "The SQP itself is passage-based and not reproduced exactly.")
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


def _build(grade: int, subject: str, exam_type: str) -> PaperTemplate:
    rows, status, source = _pattern(grade, subject, exam_type)
    sections = [
        TemplateSection(
            id=f"s{i + 1}", title=title, question_count=count, marks_each=marks,
            attempt_count=attempt, difficulty_mix=_MIX.get(marks),
            competency_share=competency,
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
