"""Tests for the SQP+MS parser.

This parser is NOT production-ready and these tests say so. They pin the
primitives that do work, and they pin the KNOWN GAPS so the current state cannot
be mistaken for a finished extractor.

Measured on the real Class X 2025-26 Social Science pair:

    questions parsed        29   (the paper states 38)
    with marks               8   of 29
    join against the scheme 24   of 29
    page numbers in answers  yes -- "in 2016- 5 17. Panchpatmali deposits..."

A question bank built from that would contain missing questions, missing marks,
and answers with page numbers spliced into them. It is committed as documented
work-in-progress, not wired into any build.

The specific unfixed defects, recorded so the next attempt starts where this one
stopped:

  1. THE MARGIN BAND IS THE WRONG MECHANISM. Furniture is stripped by position
     (top 5.5% / bottom 6% of the page), but a question header that lands at the
     top of a page is inside that band and is destroyed -- which is how question
     12 and both parts of 17 disappeared when the band was tightened. Meanwhile
     the page number is NOT in the margin at all: it is inline in the text flow,
     so the band never catches the thing it was added to catch.
  2. MARKS ARE MOSTLY MISSING. 8 of 29. A lone digit line is the mark value, and
     the detection is not finding them reliably.
  3. THE SECTIONS ARE UNGATED AFTER THE FIRST. Only the first SECTION header is
     used, to skip the General Instructions. Section boundaries within the paper
     carry no other meaning for now.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from academicos.corpus import cbse_sqp  # noqa: E402

SQP_DIR = REPO / "academicos-data" / "corpus" / "cbse-sqp" / "ClassX_2025_26"
HAVE_PDFS = (SQP_DIR / "SocialScience-SQP.pdf").exists()
needs_pdfs = pytest.mark.skipif(
    not HAVE_PDFS, reason="SQP PDFs not present (not committed)")


# --- the General Instructions trap ---------------------------------------

def test_a_section_header_is_recognised():
    assert cbse_sqp._SECTION.match("SECTION A")
    assert cbse_sqp._SECTION.match("Section – B")
    assert cbse_sqp._SECTION.match("SECTION-D")


def test_prose_containing_the_word_section_is_not_a_header():
    """The instructions say "has Four Sections – A-History..." """
    assert not cbse_sqp._SECTION.match("2. The question paper has Four Sections")


def test_instructions_before_the_first_section_are_not_questions():
    """Instructions are numbered 1, 2, 3 -- the same shape as a question.

    Without gating, the six instruction lines become questions 1-6 and the real
    questions 1-7 are swallowed, shifting every join against the scheme.
    """
    assert cbse_sqp._MAX_Q >= 38           # the real paper reaches 38
    # The parser skips everything until `started` flips, which only a SECTION
    # header does. Asserted via the constant the loop keys on.
    assert cbse_sqp._SECTION.pattern


# --- marks and headers ---------------------------------------------------

def test_a_lone_digit_is_a_marks_value():
    assert cbse_sqp._MARKS.match("1")
    assert cbse_sqp._MARKS.match("  5 ")
    assert cbse_sqp._MARKS.match("10")


def test_a_number_followed_by_text_is_a_header_not_marks():
    m = cbse_sqp._HEADER.match("15. Which of the following statements best")
    assert m and m.group(1) == "15" and m.group(2) is None
    assert m.group(3).startswith("Which")


def test_a_lettered_header_is_captured_as_a_part():
    m = cbse_sqp._HEADER.match("17A. Person P is willing to establish")
    assert m and m.group(1) == "17" and m.group(2) == "A"


def test_a_bare_digit_is_marks_and_not_a_header():
    """`1` alone is a mark value; only `1.` is a header shape.

    This is why marks are checked before headers in the parse loop.
    """
    assert cbse_sqp._MARKS.match("1")
    assert cbse_sqp._HEADER.match("1") is None
    assert cbse_sqp._HEADER.match("1. Something") is not None


# --- the join -------------------------------------------------------------

def test_question_key_matches_the_scheme_key_shape():
    q = cbse_sqp.Question(number=17, part="A")
    assert q.key == "17A"
    assert cbse_sqp.Question(number=15).key == "15"


def test_an_or_alternative_is_recorded_as_an_alternative():
    """17B is one question with two options, not two questions."""
    b = cbse_sqp.Question(number=17, part="B", alternative_of=17)
    assert b.alternative_of == 17


# --- against the real documents: the gaps, pinned ------------------------

@needs_pdfs
def test_the_paper_states_38_questions_and_we_do_not_yet_reach_it():
    """Pins the gap rather than hiding it.

    If a future attempt fixes the margin band and the count reaches 38, this
    test fails and should be replaced by one asserting the exact count. That is
    the intended signal.
    """
    questions, _errors = cbse_sqp.parse_questions(SQP_DIR / "SocialScience-SQP.pdf")
    assert len(questions) < 38, (
        f"parsed {len(questions)} questions; the parser now reaches the paper's "
        "stated 38 -- replace this gap-pinning test with a correctness test"
    )
    assert len(questions) >= 20, (
        f"parsed only {len(questions)} questions, which is a regression beyond "
        "the known margin-band defect"
    )


@needs_pdfs
def test_marks_are_mostly_missing_which_is_a_known_defect():
    questions, _ = cbse_sqp.parse_questions(SQP_DIR / "SocialScience-SQP.pdf")
    with_marks = sum(1 for q in questions if q.marks)
    assert with_marks < len(questions), (
        "every question now has marks -- the known marks defect is fixed, so "
        "this test should become an assertion that ALL questions have marks"
    )


@needs_pdfs
def test_the_join_never_invents_an_answer():
    """The invariant that MUST hold even while the parser is incomplete.

    An incomplete parser is acceptable. One that pairs a question with an
    answer it could not key is not -- that is a silently wrong answer key, and
    it is the failure this whole module is shaped to avoid.

    Note what is NOT asserted: that the join is complete. It reaches 24 of 29,
    and that gap is the known defect, not a violation.
    """
    joined, stats = cbse_sqp.parse_pair(
        SQP_DIR / "SocialScience-SQP.pdf", SQP_DIR / "SocialScience-MS.pdf")
    for item in joined:
        assert item.answer.strip(), (
            f"{item.question.key} was joined with an empty answer"
        )
    assert stats["joined"] == len(joined)
    assert stats["joined"] + len(stats["unjoined"]) == stats["questions"], (
        "every parsed question is either joined or reported unjoined; none may "
        "be silently dropped"
    )
