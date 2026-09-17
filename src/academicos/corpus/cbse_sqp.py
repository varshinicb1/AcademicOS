"""Parse a CBSE Sample Question Paper and its Marking Scheme, and join them.

SQP and MS are separate documents numbered the same way, so the link between a
question and its answer is authority-provided. That is what the board-paper
corpus could not give us: there, 1,658 questions had a matching paper code and
no answer for their question number, and the offset that would have joined them
proved unmeasurable.

Three traps, all characterised against the real Class X Social Science pair
before this module was written:

1. MARKS ARE A LONE DIGIT ON THEIR OWN LINE, after the question text. There is
   no "N marks" string anywhere in the document -- measured at zero occurrences
   -- so marks cannot be read from prose and must be read positionally.

2. `OR` MEANS AN INTERNAL CHOICE. `17A` and `17B` are not two questions; they
   are one question with two options. Counting rows naively inflates the paper,
   so B is recorded as an alternative of A rather than as a sibling.

3. PAGE NUMBERS BLEED INTO THE TEXT, and they are shaped exactly like question
   headers. The marking scheme for 17A reads "...in 2016-" then
   "17. Panchpatmali deposits..." -- where that `17.` is the PAGE NUMBER, sitting
   inside a 1-2-3-4-5 list. A text-based strip cannot tell it from a question
   header, and a naive split creates a phantom question 17 nested inside 17A,
   which would then pair question 17's answer with a fragment of 17A's.

   So page furniture is removed BY POSITION: text in the top and bottom band of
   the page is dropped before lines are rebuilt. The page number lives in the
   margin, so the band catches it and the body text survives.

The rule this module holds: it never pairs a question with an answer it cannot
key on exactly. Anything unmatched is reported as unmatched.
"""

from __future__ import annotations

import dataclasses
import re
from pathlib import Path
from typing import Iterator

try:
    import pymupdf as _fitz
except ImportError:                                # pragma: no cover
    import fitz as _fitz

# A page number is a bare number equal to the page index, sitting in a
# furniture position: vertically in the header/footer band, or horizontally in
# an outer margin. The value test alone would delete a real mark that happens to
# equal the page index (a 3-mark question on page 3); the position test alone
# would delete a question number that happens to be indented.
#
# MEASURED, and this was a real defect rather than a hypothetical one: the first
# version required only the HORIZONTAL margin, and the page numbers in this
# paper are centred, so they were never caught. They then fell through to the
# marks rule and were assigned to questions as mark values -- page 10's number
# became a 10-mark question, page 11's an 11-mark question. Twelve of the
# fourteen lone digits in the document were page numbers, and the marks
# distribution showed values (6,7,8,9,10,11) that no Social Science question
# could carry. Verified line by line against the page index before being fixed.
_MARGIN_FRACTION = 0.16
_TOP_BAND = 0.08
_BOTTOM_BAND = 0.92

# A mark value is right-aligned in a column of its own, so it is separated from
# the last word of the question text by a gap much wider than the normal space
# between words. Measured on the real paper: ordinary inter-word spacing is a
# few points, and the gap before the marks column is an order of magnitude more.
#
# The marks digit is NOT on its own line. Rows are grouped by y-position and the
# marks sit on the same visual row as the last line of the question text:
#
#     "...vibrant pre-modern trade and cultural links 2"
#     "...was not the result of a sudden upheaval 5"
#
# 21 lines have this shape and a lone-digit rule misses every one. Rather than
# teach the marks rule about gaps, the gap is used here to SPLIT the row, so the
# value arrives as a lone digit line and one rule handles both shapes.
#
# The gap is what stops a question that legitimately ends in a number from being
# misread as carrying that many marks.
_MARK_GAP = 18.0


def _is_page_number(text: str, page_number: int, *, x0: float, x1: float,
                    y0: float, y1: float, width: float, height: float) -> bool:
    """Is this word the page number rather than content?

    Both conditions are required. See the note above for why the horizontal
    margin alone was insufficient and what it cost.
    """
    # The trailing period is deliberately NOT stripped. A page number in this
    # corpus is a bare digit; a question header is `12.` with the period. So the
    # period separates them, and stripping it made `12.` at the top of page 12
    # indistinguishable from the page number -- which destroyed the header, the
    # exact failure the band was originally blamed for.
    stripped = (text or "").strip()
    if not stripped.isdigit():
        return False
    if int(stripped) != page_number:
        return False
    if width <= 0 or height <= 0:
        return False
    in_margin = (x0 < width * _MARGIN_FRACTION
                 or x1 > width * (1.0 - _MARGIN_FRACTION))
    in_band = y0 < height * _TOP_BAND or y1 > height * _BOTTOM_BAND
    return in_margin or in_band


# `15.` or `17A.` at the start of a line, optionally followed by text.
_HEADER = re.compile(r"^\s*(\d{1,2})([A-Z])?\.\s*(.*)$")

# A lone digit is the mark value for the preceding question.
_MARKS = re.compile(r"^\s*(\d{1,2})\s*$")

# The word that marks an internal choice.
_OR = re.compile(r"^\s*OR\s*$", re.I)

# `SECTION A`, `SECTION B`, ... Every paper opens with a General Instructions
# list that is numbered 1, 2, 3 -- the SAME shape as a question header. Without
# gating on the first section header those instructions are read as questions
# 1-6, which both invents six questions and swallows the real questions 1-7.
# Measured: 38 questions were still parsed correctly by count, but the numbering
# was shifted, so the join against the marking scheme was wrong for the first
# seven questions -- the exact silent error this module exists to avoid.
_SECTION = re.compile(r"^\s*SECTION\s*[-\u2013\u2014]?\s*([A-Z])\b", re.I)

# The largest question number a paper could plausibly reach. Guards against a
# stray large number being read as a header.
_MAX_Q = 60


@dataclasses.dataclass
class Question:
    number: int
    part: str = ""                     # "" for 15, "A"/"B" for 17A/17B
    text: str = ""
    marks: int = 0
    options: list[str] = dataclasses.field(default_factory=list)
    alternative_of: int | None = None   # set on a B that follows an A
    page: int = 0

    @property
    def key(self) -> str:
        return f"{self.number}{self.part}"


def _body_lines(pdf_path: Path) -> list[tuple[int, str]]:
    """`(page, line)` for the body text of every page, page numbers removed.

    Lines are rebuilt from positioned words rather than taken from
    `get_text()`, because a pageless `get_text()` splice puts the page number in
    the middle of a sentence -- "...in 2016- 17. Panchpatmali deposits..." --
    where no line-based rule can find it. Working from positioned words lets the
    page number be identified and dropped on its own merits.
    """
    out: list[tuple[int, str]] = []
    doc = _fitz.open(pdf_path)
    try:
        for index in range(doc.page_count):
            page = doc[index]
            width = page.rect.width or 1.0
            height = page.rect.height or 1.0
            try:
                words = page.get_text("words")
            except Exception:                      # pragma: no cover
                continue
            rows: dict[float, list] = {}
            for w in words:
                x0, y0, x1, y1, text = w[0], w[1], w[2], w[3], w[4]
                if _is_page_number(text, index + 1, x0=x0, x1=x1, y0=y0, y1=y1,
                                   width=width, height=height):
                    continue
                rows.setdefault(round(y0 / 3.0), []).append((x0, x1, text))
            for key in sorted(rows):
                items = sorted(rows[key])
                # A trailing 1-6 set off by a wide gap is the marks column.
                if len(items) >= 2:
                    last_x0, _last_x1, last_text = items[-1]
                    if (last_text.isdigit() and 1 <= int(last_text) <= 6
                            and (last_x0 - items[-2][1]) >= _MARK_GAP):
                        body = " ".join(t for _a, _b, t in items[:-1]).strip()
                        if body:
                            out.append((index + 1, body))
                        out.append((index + 1, last_text))
                        continue
                line = " ".join(t for _a, _b, t in items).strip()
                if line:
                    out.append((index + 1, line))
    finally:
        doc.close()
    return out


def parse_questions(pdf_path: Path) -> tuple[list[Question], list[str]]:
    """Questions from a Sample Question Paper, with marks and options."""
    lines = _body_lines(pdf_path)
    questions: list[Question] = []
    current: Question | None = None
    last_primary: Question | None = None
    errors: list[str] = []
    started = False

    for page, line in lines:
        # Nothing before the first SECTION header is a question. See _SECTION.
        if not started:
            if _SECTION.match(line):
                started = True
            continue

        marks_hit = _MARKS.match(line)
        header = _HEADER.match(line)

        # A lone digit is the mark value for the question just read. Checked
        # before the header, because a bare `1` is both a marks value and a
        # valid header shape.
        if marks_hit and current is not None and not current.marks:
            value = int(marks_hit.group(1))
            if 1 <= value <= 20:
                current.marks = value
                pending_marks = current
                continue

        if header and int(header.group(1)) <= _MAX_Q and not (marks_hit and header.group(3) == ""):
            number = int(header.group(1))
            part = header.group(2) or ""
            rest = header.group(3).strip()
            # A header must move forward, or be an alternative part of the
            # question just seen. Anything else is body text that happens to
            # start with a number.
            if questions:
                last = questions[-1]
                forward = number > last.number or (number == last.number and part > last.part)
                alternative = (part == "B" and number == last.number and last.part == "A")
                if not (forward or alternative):
                    if current is not None:
                        current.text += " " + line
                    continue
            q = Question(number=number, part=part, page=page)
            if part == "B" and questions and questions[-1].number == number:
                q.alternative_of = number
                last_primary = questions[-1]
            questions.append(q)
            current = q
            if part == "":
                last_primary = q
            if rest:
                current.text = rest
            continue

        if _OR.match(line):
            continue
        if current is not None:
            current.text += " " + line
            # Option lines in an MCQ start "A." "B." "C." "D."
            if re.match(r"^\s*[A-D]\.\s", line):
                current.options.append(line.strip())

    for q in questions:
        q.text = " ".join(q.text.split())
    if not questions:
        errors.append(f"{pdf_path.name}: no questions parsed")
    return questions, errors


def parse_scheme(pdf_path: Path) -> tuple[dict[str, str], dict[str, int], list[str]]:
    """`question key -> answer text` and `question key -> marks`.

    Keyed the same way as the questions (`"15"`, `"17A"`) so the join is exact.
    A key that cannot be matched is simply absent, never guessed.
    """
    lines = _body_lines(pdf_path)
    answers: dict[str, str] = {}
    marks: dict[str, int] = {}
    current_key: str | None = None
    errors: list[str] = []
    last_number = 0

    for _page, line in lines:
        header = _HEADER.match(line)
        marks_hit = _MARKS.match(line)

        if marks_hit and current_key is not None and current_key not in marks:
            value = int(marks_hit.group(1))
            if 1 <= value <= 20:
                marks[current_key] = value
                continue

        if header:
            number = int(header.group(1))
            part = header.group(2) or ""
            rest = header.group(3).strip()
            if number <= _MAX_Q:
                forward = number > last_number or (number == last_number and part)
                if forward:
                    current_key = f"{number}{part}"
                    answers.setdefault(current_key, "")
                    last_number = max(last_number, number)
                    if rest:
                        answers[current_key] += " " + rest
                    continue
        if current_key is not None:
            answers[current_key] += " " + line

    for k in answers:
        answers[k] = " ".join(answers[k].split())
    if not answers:
        errors.append(f"{pdf_path.name}: no marking scheme entries parsed")
    return answers, marks, errors


@dataclasses.dataclass
class SqpQuestion:
    """A question that HAS an answer key. Without one it is not emitted."""

    question: Question
    answer: str
    scheme_marks: int


def parse_pair(sqp_path: Path, ms_path: Path) -> tuple[list[SqpQuestion], dict]:
    """Join a paper to its scheme by question number.

    Reports what it could not join, rather than emitting a question with an
    empty or borrowed answer.
    """
    questions, q_errors = parse_questions(sqp_path)
    answers, marks, ms_errors = parse_scheme(ms_path)

    joined: list[SqpQuestion] = []
    unjoined: list[str] = []
    for q in questions:
        text = answers.get(q.key, "").strip()
        if not text:
            unjoined.append(q.key)
            continue
        joined.append(SqpQuestion(question=q, answer=text,
                                  scheme_marks=marks.get(q.key, 0)))

    stats = {
        "questions": len(questions),
        "schemeEntries": len(answers),
        "joined": len(joined),
        "unjoined": unjoined,
        "errors": q_errors + ms_errors,
    }
    return joined, stats
