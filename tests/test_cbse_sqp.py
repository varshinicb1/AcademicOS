"""Tests for the SQP+MS parser.

This parser is NOT production-ready and these tests say so. They pin the
primitives that do work, and they pin the KNOWN GAPS so the current state cannot
be mistaken for a finished extractor.

Measured on the real Class X 2025-26 Social Science pair:

    questions parsed        32   (the paper states 38)
    with marks               0   of 32
    join against the scheme 30   of 32
    options                 16

A question bank built from that would still be missing six questions and carry
no mark values at all. It is committed as documented work-in-progress, not
wired into any build.

The specific unfixed defects, recorded so the next attempt starts where this one
stopped:

  1. MARKS ARE NOT DETECTED, and the reason is now known exactly. The mark value
     is NOT on its own line: rows are grouped by y-position, and the marks digit
     sits on the same visual row as the last line of the question text, so it
     merges into it. Measured, 21 lines end with a small number after text:

         "...vibrant pre-modern trade and cultural links 2"
         "...was not the result of a sudden upheaval 5"
         "...using per capita income (average 1"

     `_MARKS` matches only a LONE digit, so every one of these is missed. The
     fix is to read a trailing 1-6 as the mark value when it is separated from
     the preceding word by an x-gap, which is how CBSE right-aligns the marks
     column -- the gap is the discriminator that stops a question legitimately
     ending in a number from being misread.

  2. SIX QUESTIONS ARE STILL MISSED (32 of the paper's stated 38), a cause
     separate from the margin band that used to explain it.

  3. HYPHENATED LINE-BREAKS ARE NOT JOINED. The scheme for 17A holds
     "...in 2016- 5 17. Panchpatmali..." -- a year range split across a line,
     where an earlier revision of this file misread the `17.` as a page number.
     The marking scheme is 11 pages long, so there is no page 17.

A DEFECT THAT WAS FIXED HERE, and was worse than the gaps above
---------------------------------------------------------------
The parser was assigning PAGE NUMBERS as MARK VALUES. Page 10's number became a
10-mark question, page 11's an 11-mark question. The marks distribution showed
values (6,7,8,9,10,11) that no Social Science question can carry, which is what
gave it away.

Twelve of the fourteen lone digits in the document were page numbers. The
page-number test required the HORIZONTAL margin, and these numbers are centred,
so none were caught. They then fell through to the marks rule.

The count of questions with marks therefore went 8 -> 0, and that is an
improvement: eight WRONG mark values were replaced by none. A wrong mark
silently corrupts any marks-wise report built on it; an absent one is visible.
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


# --- page numbers: value AND furniture position --------------------------

def _pn(text, page, *, x0=250, x1=270, y0=400, y1=415, w=600, h=800):
    return cbse_sqp._is_page_number(text, page, x0=x0, x1=x1, y0=y0, y1=y1,
                                    width=w, height=h)


def test_a_matching_number_in_the_header_band_is_a_page_number():
    """The case that actually occurred, and the reason the margin alone failed.

    Page numbers in this paper are centred, so they are never in the horizontal
    margin. Requiring the margin let all twelve through, where they fell to the
    marks rule and were assigned to questions -- page 10's number became a
    10-mark question.
    """
    assert _pn("10", 10, x0=290, x1=310, y0=20, y1=35)      # top band


def test_a_matching_number_in_the_footer_band_is_a_page_number():
    assert _pn("4", 4, x0=290, x1=300, y0=780, y1=795)      # bottom band


def test_a_matching_number_in_the_side_margin_is_a_page_number():
    assert _pn("17", 17, x0=20, x1=40, y0=400, y1=415)


def test_a_number_that_is_not_the_page_index_is_content():
    """The paper's own question numbers must survive."""
    assert not _pn("17", 6, y0=400, y1=415)
    assert not _pn("12", 13, y0=400, y1=415)


def test_a_matching_number_in_the_body_is_content():
    """A 3-mark question on page 3 keeps its marks.

    This is why the value test alone is not enough and the position test is
    also required.
    """
    assert not _pn("3", 3, y0=400, y1=415)


def test_prose_and_ranges_are_never_page_numbers():
    assert not _pn("Odisha", 4, y0=20, y1=35)
    assert not _pn("2016-17", 4, y0=20, y1=35)
    assert not _pn("", 4, y0=20, y1=35)


def test_the_band_removes_page_numbers_without_destroying_body_text():
    """The band is an IDENTIFIER, not a filter -- that distinction was the bug.

    An earlier version dropped everything inside the band, which destroyed any
    question header landing at the top of a page and took the parsed count from
    38 to 29. Now a band word is dropped only if it is also the page number, so
    body text at the top of a page survives.
    """
    # A header at the very top of the page is text, so it is not a page number.
    assert not _pn("12.", 12, x0=60, x1=90, y0=20, y1=35)
    # The page number in the same band is.
    assert _pn("12", 12, x0=290, x1=310, y0=20, y1=35)



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
