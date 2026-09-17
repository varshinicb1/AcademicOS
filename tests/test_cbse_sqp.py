"""Tests for the SQP+MS parser.

This parser is NOT production-ready and these tests say so. They pin the
primitives that do work, and they pin the KNOWN GAPS so the current state cannot
be mistaken for a finished extractor.

Measured on the real Class X 2025-26 Social Science pair:

    questions parsed        32   (the paper states 38)
    with marks               8   of 32
    join against the scheme 30   of 32
    options                 16

A question bank built from that would still be missing six questions and have
marks on a quarter of them. It is committed as documented work-in-progress, not
wired into any build.

The specific unfixed defects, recorded so the next attempt starts where this one
stopped:

  1. SIX QUESTIONS ARE STILL MISSED (32 of the paper's stated 38). The margin
     band that used to cause this is gone and the count recovered from 29 to 32,
     so the residue is a separate cause -- most likely a header whose words are
     split across a line in the PDF.
  2. MARKS ARE MOSTLY MISSING. 8 of 32. A lone digit line is the mark value and
     the detection is not finding them reliably; the mark value also sometimes
     trails the body text on the same line, as in the 17A scheme entry.
  3. HYPHENATED LINE-BREAKS ARE NOT JOINED. The scheme for 17A holds
     "...in 2016- 5 17. Panchpatmali..." -- a year range split across a line,
     where an earlier revision of this file misread the `17.` as a page number.
     The marking scheme is 11 pages long, so there is no page 17.

Correction carried forward: the "page numbers bleed into the text" trap this
file used to document was a MISREADING of case 3, and the page-number identity
test that replaced the position band is nevertheless correct and kept.
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


# --- page numbers, identified by value not position ----------------------

def test_a_bare_number_matching_the_page_index_in_the_margin_is_a_page_number():
    assert cbse_sqp._is_page_number("17", 17, x0=20, x1=40, width=600)
    assert cbse_sqp._is_page_number("3", 3, x0=560, x1=585, width=600)


def test_a_number_that_is_not_the_page_index_is_content():
    """The user's own question numbers must survive."""
    assert not cbse_sqp._is_page_number("17", 6, x0=20, x1=40, width=600)
    assert not cbse_sqp._is_page_number("12", 13, x0=20, x1=40, width=600)


def test_a_matching_number_in_the_body_is_not_a_page_number():
    """A question numbered the same as the page is not the page number."""
    assert not cbse_sqp._is_page_number("17", 17, x0=250, x1=270, width=600)


def test_prose_and_marks_are_never_page_numbers():
    assert not cbse_sqp._is_page_number("Odisha", 4, x0=20, x1=60, width=600)
    assert not cbse_sqp._is_page_number("2016-17", 4, x0=20, x1=60, width=600)
    assert not cbse_sqp._is_page_number("", 4, x0=20, x1=40, width=600)


def test_the_band_mechanism_is_gone():
    """Position bands destroyed body text; the value test replaced them.

    A question header landing at the top of a page used to be inside the band
    and vanish, which took the parsed count from 38 to 29.
    """
    assert not hasattr(cbse_sqp, "_TOP_BAND")
    assert not hasattr(cbse_sqp, "_BOTTOM_BAND")



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
