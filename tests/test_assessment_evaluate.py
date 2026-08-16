"""Keyword answer-evaluation engine (assessment/evaluate.py) — deterministic
marking-point/keyword scoring, blank-vs-skipped phrase detection, objective
MCQ key matching, and OCR-risk confidence damping. Pure, no LLM / no network.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.assessment.evaluate import (
    DESCRIPTIVE_MIN_CHARS,
    REVIEW_THRESHOLD,
    evaluate_answer,
    ocr_risk_flags,
)
from academicos.assessment.schemas import (
    AnswerSchemeSchema,
    MarkingPointSchema,
    QuestionSchema,
)


def _point(pid: str, marks: int, keyword: str, *synonyms: str,
           description: str = "") -> MarkingPointSchema:
    return MarkingPointSchema(
        id=pid, description=description or f"point {pid}", marks=marks,
        keyword=keyword, synonyms=list(synonyms),
    )


def _question(marks: int = 3, scheme: AnswerSchemeSchema | None = None) -> QuestionSchema:
    now = datetime.now(timezone.utc)
    return QuestionSchema(
        id="q1", question_bank_id="bank1", subject="science", grade=10,
        chapter_ids=["c1"], competency_ids=[], bloom_level="understand",
        difficulty="medium", type="short_answer", stem="stem", parts=[],
        answer_scheme=scheme or AnswerSchemeSchema(total_marks=marks, metadata={}),
        estimated_time_minutes=2, marks=marks, language="en", source="teacher_created",
        quality_score=0.7, tags=[], created_at=now, updated_at=now,
    )


def _objective_scheme(correct_option: str | None = "B") -> AnswerSchemeSchema:
    return AnswerSchemeSchema(
        total_marks=1,
        marking_points=[_point("mp1", 1, "correct option selected",
                               description="correct option selected")],
        metadata={"objective": True, "correctOption": correct_option,
                  "options": {"A": "xylem", "B": "phloem"}},
    )


# ---------------------------------------------------------------- blanks ----

def test_blank_answer_is_blank_verdict():
    q = _question()
    ev = evaluate_answer(q, q.answer_scheme, "")
    assert ev.verdict == "blank"
    assert ev.awarded_marks == 0
    assert ev.confidence == pytest.approx(0.95)
    assert ev.needs_review is False


def test_whitespace_and_punctuation_only_is_blank():
    q = _question()
    ev = evaluate_answer(q, q.answer_scheme, "   . . .   ")
    assert ev.verdict == "blank"


def test_not_attempted_phrase_is_blank_not_no_credit():
    # Regression: "Not attempted." contains alnum chars so the old
    # "any alnum char" blank check missed it, and it fell through to
    # option-matching / a confusing verdict. _BLANK_PHRASES must catch it.
    q = _question()
    for phrase in ("Not attempted.", "no answer", "BLANK", "skipped", "N/A", "none"):
        ev = evaluate_answer(q, q.answer_scheme, phrase)
        assert ev.verdict == "blank", phrase
        assert ev.needs_review is False


# -------------------------------------------------------------- objective ---

def test_objective_correct_option_full_credit():
    q = _question(marks=1, scheme=_objective_scheme("B"))
    ev = evaluate_answer(q, q.answer_scheme, "(B)")
    assert ev.verdict == "fullCredit"
    assert ev.awarded_marks == 1
    assert ev.confidence == pytest.approx(0.93)
    assert ev.needs_review is False
    assert ev.marking_points[0].awarded is True


def test_objective_wrong_option_no_credit():
    q = _question(marks=1, scheme=_objective_scheme("B"))
    ev = evaluate_answer(q, q.answer_scheme, "(A)")
    assert ev.verdict == "noCredit"
    assert ev.awarded_marks == 0
    assert ev.gaps == ["Correct option was B"]


def test_objective_unidentifiable_option_needs_review():
    q = _question(marks=1, scheme=_objective_scheme("B"))
    ev = evaluate_answer(q, q.answer_scheme, "xylem transports water")
    assert ev.verdict == "noCredit"
    assert ev.confidence == pytest.approx(0.45)
    assert ev.needs_review is True


def test_objective_missing_key_needs_teacher():
    q = _question(marks=1, scheme=_objective_scheme(correct_option=None))
    ev = evaluate_answer(q, q.answer_scheme, "(B)")
    assert ev.verdict == "partialCredit"
    assert ev.confidence == 0.0
    assert ev.needs_review is True
    assert "teacher must set the key" in ev.reasoning


def test_option_alone_is_not_blank():
    # A single "(B)" is a complete MCQ answer, not a blank — the
    # descriptive-min-chars rule must never apply to objective questions.
    q = _question(marks=1, scheme=_objective_scheme("B"))
    ev = evaluate_answer(q, q.answer_scheme, "(B)")
    assert ev.verdict == "fullCredit"
    assert ev.awarded_marks == 1


def test_objective_ocr_flag_drops_confidence_into_review():
    # Struck-through working merged into "44220" flags the transcription.
    q = _question(marks=1, scheme=_objective_scheme("B"))
    ev = evaluate_answer(q, q.answer_scheme, "(B) 44220")
    assert ev.verdict == "fullCredit"
    assert ev.confidence == pytest.approx(0.6)
    assert ev.needs_review is True
    assert ev.ocr_warnings


# ------------------------------------------------------------- descriptive ---

def test_descriptive_full_credit_when_all_points_present():
    scheme = AnswerSchemeSchema(
        total_marks=3,
        marking_points=[_point("mp1", 3, "photosynthesis", description="process")],
    )
    q = _question(marks=3, scheme=scheme)
    ev = evaluate_answer(q, q.answer_scheme,
                         "Photosynthesis converts light energy into chemical energy")
    assert ev.verdict == "fullCredit"
    assert ev.awarded_marks == 3
    assert ev.confidence == pytest.approx(0.9)
    assert ev.needs_review is False


def test_descriptive_partial_credit():
    scheme = AnswerSchemeSchema(
        total_marks=3,
        marking_points=[_point("mp1", 2, "calcium", description="calcium"),
                        _point("mp2", 1, "potassium", description="potassium")],
    )
    q = _question(marks=3, scheme=scheme)
    ev = evaluate_answer(q, q.answer_scheme, "Calcium is needed for strong bones")
    assert ev.verdict == "partialCredit"
    assert ev.awarded_marks == 2
    assert [o.marking_point_id for o in ev.marking_points if o.awarded] == ["mp1"]
    assert ev.needs_review is True  # middling keyword hit-rate is untrustworthy


def test_descriptive_no_credit():
    scheme = AnswerSchemeSchema(
        total_marks=2,
        marking_points=[_point("mp1", 2, "photosynthesis", description="process")],
    )
    q = _question(marks=2, scheme=scheme)
    ev = evaluate_answer(q, q.answer_scheme, "Magnesium and iron are both metals")
    assert ev.verdict == "noCredit"
    assert ev.awarded_marks == 0


def test_descriptive_too_short_needs_review():
    q = _question(marks=3)
    ev = evaluate_answer(q, q.answer_scheme, "yes")
    assert len("yes") < DESCRIPTIVE_MIN_CHARS
    assert ev.verdict == "noCredit"
    assert ev.confidence == pytest.approx(0.4)
    assert ev.needs_review is True
    assert "too short" in ev.reasoning


def test_synonym_matches_keyword():
    scheme = AnswerSchemeSchema(
        total_marks=2,
        marking_points=[_point("mp1", 2, "respiration", "breathing",
                               description="gas exchange")],
    )
    q = _question(marks=2, scheme=scheme)
    ev = evaluate_answer(q, q.answer_scheme, "Breathing supplies oxygen to the cells")
    assert ev.verdict == "fullCredit"
    assert ev.awarded_marks == 2


def test_multiword_keyword_phrase_matches():
    scheme = AnswerSchemeSchema(
        total_marks=2,
        marking_points=[_point("mp1", 2, "light energy", description="energy source")],
    )
    q = _question(marks=2, scheme=scheme)
    ev = evaluate_answer(q, q.answer_scheme, "It uses light energy from the sun")
    assert ev.verdict == "fullCredit"
    assert ev.awarded_marks == 2


def test_multiword_keyword_phrase_not_split_across_words():
    scheme = AnswerSchemeSchema(
        total_marks=2,
        marking_points=[_point("mp1", 2, "light energy", description="energy source")],
    )
    q = _question(marks=2, scheme=scheme)
    ev = evaluate_answer(q, q.answer_scheme, "Light travels fast; energy is conserved")
    assert ev.verdict == "noCredit"  # "light energy" as an adjacent phrase is absent


def test_awarded_marks_clamped_to_max():
    scheme = AnswerSchemeSchema(
        total_marks=2,
        marking_points=[_point("mp1", 2, "oxygen", description="a"),
                        _point("mp2", 2, "glucose", description="b")],
    )
    q = _question(marks=2, scheme=scheme)
    ev = evaluate_answer(q, q.answer_scheme, "Oxygen and glucose are both produced")
    assert ev.awarded_marks == 2  # not 4
    assert ev.verdict == "fullCredit"


def test_full_credit_needs_no_review_but_partial_does():
    scheme = AnswerSchemeSchema(
        total_marks=2,
        marking_points=[_point("mp1", 2, "oxygen", description="a")],
    )
    q = _question(marks=2, scheme=scheme)
    ev = evaluate_answer(q, q.answer_scheme, "Oxygen is released")
    assert ev.needs_review is False


# ------------------------------------------------------------ ocr risk ----

def test_ocr_risk_flags_fused_number():
    flags = ocr_risk_flags("The mass was 44220 kg")
    assert any("struck-through" in f for f in flags)


def test_ocr_risk_flags_multiple_unresolved_chars():
    flags = ocr_risk_flags("a?? b? c?")
    assert any("unresolved" in f for f in flags)


def test_ocr_risk_flags_mixed_script():
    # Hindi "photosynthesis" — mostly non-Latin letters, flagged as possibly
    # mis-segmented transcription.
    flags = ocr_risk_flags("प्रकाश संश्लेषण")
    assert any("mixed-script" in f for f in flags)


def test_ocr_risk_flags_clean_text_no_flags():
    assert ocr_risk_flags("Photosynthesis converts light to chemical energy.") == []


def test_ocr_flags_force_review_on_descriptive():
    scheme = AnswerSchemeSchema(
        total_marks=2,
        marking_points=[_point("mp1", 2, "oxygen", description="a")],
    )
    q = _question(marks=2, scheme=scheme)
    ev = evaluate_answer(q, q.answer_scheme, "Oxygen is released, mass 44220")
    assert ev.verdict == "fullCredit"
    assert ev.needs_review is True  # ocr flag overrides clean-keyword confidence


def test_max_marks_falls_back_to_question_marks():
    scheme = AnswerSchemeSchema(total_marks=0, metadata={})
    q = _question(marks=5, scheme=scheme)
    ev = evaluate_answer(q, q.answer_scheme, "")
    assert ev.max_marks == 5
    assert ev.percentage == 0.0


def test_blank_evaluation_has_percentage_zero():
    q = _question(marks=4)
    ev = evaluate_answer(q, q.answer_scheme, "")
    assert ev.percentage == 0.0