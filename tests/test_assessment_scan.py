"""REGRESSION suite for assessment/scan.py question-number segmentation.

Locks in fixes shipped today against real handwritten CBSE booklets:
  1. _HTML_TAG stripping — Sarvam Vision renders some tabular MCQ answer
     blocks as HTML tables; every answer was silently dropped as "blank".
  2. Leading-period tolerance — ".13)" must match as "13)".
  3. _split_nested_marker — a bogus "9." from a misread "Q.", and a spurious
     leading digit ("8.14)" for "14)"), must not swallow the real answer.
Plus the ordinary happy paths so the above fixes can't regress them.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.assessment.scan import segment_answers
from academicos.assessment.vision import PageOCR


def _page(page_no: int, text: str, warnings: list[str] | None = None) -> PageOCR:
    return PageOCR(page_no=page_no, text=text, warnings=warnings or [])


def _by_number(segments) -> dict[int, str]:
    return {s.question_no: s.text for s in segments}


# 1) HTML-table MCQ answer blocks ----------------------------------------

def test_html_table_answers_recovered_not_blank():
    # Real production shape: Sarvam rendered a tabular MCQ answer block as
    # HTML. Every table row lands on its own line, so after tag-stripping
    # "Ans1." naturally starts a line and _Q_MARKER can see it. Before the
    # fix all 20 real answers were discarded as blank.
    text = (
        "<table>\n"
        "<tbody>\n"
        "<tr><td>Ans1.</td><td>(A) No Solution</td></tr>\n"
        "<tr><td>Ans2.</td><td>(B) 4</td></tr>\n"
        "<tr><td>Ans3.</td><td>(D) 100</td></tr>\n"
        "</tbody>\n"
        "</table>"
    )
    segments = segment_answers([_page(1, text)])
    by_no = _by_number(segments)
    assert by_no.get(1) == "(A) No Solution"
    assert by_no.get(2) == "(B) 4"
    assert by_no.get(3) == "(D) 100"
    assert len(segments) == 3
    assert all(not s.is_blank for s in segments)


def test_html_table_single_row_recovers_answer():
    text = "<table><tr><td>Ans1.</td><td>(A) No Solution</td></tr></table>"
    segments = segment_answers([_page(1, text)])
    assert _by_number(segments).get(1) == "(A) No Solution"


# 2) Leading-period tolerance ---------------------------------------------

def test_leading_period_before_marker():
    # OCR emitted a stray "." before the real marker: ".13)" for "13)".
    # Before the fix the regex only tolerated whitespace or an ans/q word,
    # so the whole answer vanished. Now it must recover question 13.
    segments = segment_answers([_page(1, ".13) (D) 99%")])
    assert len(segments) == 1
    assert segments[0].question_no == 13
    assert segments[0].text == "(D) 99%"


def test_leading_period_with_whitespace():
    segments = segment_answers([_page(1, " . 5) (C) Both")])
    assert _by_number(segments).get(5) == "(C) Both"


# 3) _split_nested_marker ------------------------------------------------

def test_misread_q_as_9_does_not_merge_two_answers():
    # Sarvam misread handwritten "Q." as "9.", so both "Q.5)" and "Q.7)"
    # matched as bogus "9" markers, concatenating two real answers into
    # question 9's slot and leaving 5 and 7 blank. The inner "5)" and "7)"
    # markers are the real ones and must split out.
    text = "9.5) (B) 5\n9.7) (D) 1:8."
    segments = segment_answers([_page(1, text)])
    by_no = _by_number(segments)
    assert by_no.get(5) == "(B) 5"
    assert by_no.get(7) == "(D) 1:8."
    assert 9 not in by_no


def test_spurious_leading_digit_does_not_pollute_previous_question():
    # OCR prefixed a spurious digit before a real two-digit number:
    # "8.14)" for what should be "14)", which used to dump question 14's
    # answer into question 8's segment after a real "Q.8) ..." answer.
    text = "Q.8) (D) Cytoplasm and Nucleus\n8.14) (D)(ii) and (iv)"
    segments = segment_answers([_page(1, text)])
    by_no = _by_number(segments)
    assert by_no.get(8) == "(D) Cytoplasm and Nucleus"
    assert by_no.get(14) == "(D)(ii) and (iv)"


def test_spurious_leading_digit_standalone():
    # Same "8.14)" noise when no preceding Q.8 exists: the segment must
    # land on 14, not a bogus question 8.
    segments = segment_answers([_page(1, "8.14) (D)(ii) and (iv)")])
    assert _by_number(segments).get(14) == "(D)(ii) and (iv)"
    assert 8 not in _by_number(segments)


def test_genuine_marker_not_split_when_body_is_option():
    # A real "9. (B) 5" (question 9 answered "(B) 5") must NOT be split:
    # the body starts with "(", not a fresh "<digit><separator>".
    segments = segment_answers([_page(1, "9) (B) 5")])
    assert _by_number(segments).get(9) == "(B) 5"


# 4) Happy paths ----------------------------------------------------------

def test_q_word_marker():
    segments = segment_answers([_page(1, "Q.1) (B) Calcium and Magnesium")])
    assert _by_number(segments).get(1) == "(B) Calcium and Magnesium"


def test_bare_number_marker():
    segments = segment_answers([_page(1, "1) answer text")])
    assert _by_number(segments).get(1) == "answer text"


def test_ans_word_marker():
    segments = segment_answers([_page(1, "Ans 12. answer text")])
    assert _by_number(segments).get(12) == "answer text"


def test_multiple_markers_on_one_page():
    segments = segment_answers([_page(1, "1) aaa\n2) bbb\n3) ccc")])
    assert _by_number(segments) == {1: "aaa", 2: "bbb", 3: "ccc"}


def test_answers_accumulate_across_pages():
    segments = segment_answers([
        _page(1, "1) first part"),
        _page(2, "second part"),
    ])
    assert len(segments) == 1
    assert segments[0].question_no == 1
    assert segments[0].text == "first part\nsecond part"
    assert segments[0].page_numbers == [1, 2]


def test_head_text_appends_to_previous_question():
    segments = segment_answers([
        _page(1, "1) first"),
        _page(2, "continuation\n2) second"),
    ])
    assert _by_number(segments).get(1) == "first\ncontinuation"
    assert _by_number(segments).get(2) == "second"


def test_no_markers_yields_no_segments():
    segments = segment_answers([_page(1, "just some prose without markers")])
    assert segments == []


def test_orphan_text_before_any_marker_is_flagged():
    segments = segment_answers([
        _page(1, "answer text with no question number yet"),
        _page(2, "1) real answer"),
    ])
    assert segments
    assert any("discarded" in w for w in segments[0].warnings)


def test_page_warnings_copied_onto_matching_segment():
    segments = segment_answers([
        _page(1, "1) answer", warnings=["vision passes disagreed on this page"]),
    ])
    assert "vision passes disagreed on this page" in segments[0].warnings


def test_question_10_15_parsed_as_two_digits():
    segments = segment_answers([_page(1, "10) first\n15) second")])
    assert _by_number(segments).get(10) == "first"
    assert _by_number(segments).get(15) == "second"