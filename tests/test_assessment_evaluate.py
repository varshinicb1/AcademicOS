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


# ------------------------------------------- objective: ambiguous letters ---
# Regression for a real, high-severity bug: _OPTION_ANSWER took the first
# A-D letter anywhere in the text as "the" selection. Real CBSE transcripts
# routinely contain a SECOND, different letter that is not the student's
# choice -- boilerplate Assertion/Reason phrasing ("...Reason(R)...
# Assertion(A)..."), a "Section-A" heading, or eliminative reasoning text
# ("I first considered (A) but eliminated it, then chose (D)"). Verified
# empirically against today's real 20-question CBSE 31/1/3 harness run
# (docs/compliance.md): the correct letter is always first-mentioned there,
# so first-match stays the pick -- but when a second distinct letter is
# present the pick is genuinely uncertain and must not be trusted silently.

def test_correct_option_still_full_credit_with_trailing_contaminant_letter():
    # Exactly the real Q17 shape: correct answer B, but the boilerplate
    # Assertion/Reason phrasing after it names A too.
    q = _question(marks=1, scheme=_objective_scheme("B"))
    ev = evaluate_answer(
        q, q.answer_scheme,
        "(B) Both Assertion(A) and Reason(R) are true, but Reason (R) "
        "is not the correct explaination of (A).")
    assert ev.verdict == "fullCredit"
    assert ev.awarded_marks == 1
    # still correctly scored, but the ambiguity is real: flag for review
    # rather than claim the same confidence as a clean single-letter answer.
    assert ev.needs_review is True
    assert ev.confidence < REVIEW_THRESHOLD


def test_ambiguous_multiple_letters_forces_review_instead_of_confident_guess():
    # Before the fix: this scored noCredit at 93% confidence with no review
    # flag -- a correct final answer silently and confidently marked wrong.
    q = _question(marks=1, scheme=_objective_scheme("D"))
    ev = evaluate_answer(
        q, q.answer_scheme,
        "I first considered (A) but eliminated it, then chose (D) as final answer.")
    assert ev.needs_review is True
    assert ev.confidence < REVIEW_THRESHOLD
    # First-match is a best-effort guess only, not something to fix by
    # picking a "smarter" letter (a "prefer last" heuristic was tried and
    # measured WORSE against real data) -- the fix is surfacing the
    # uncertainty, not resolving it silently.
    assert ev.verdict == "noCredit"


def test_single_repeated_letter_is_not_ambiguous():
    # The same letter appearing more than once (echoed in the option code
    # and its spelled-out text) is NOT ambiguous -- only multiple DISTINCT
    # letters should trigger the review flag.
    q = _question(marks=1, scheme=_objective_scheme("D"))
    ev = evaluate_answer(q, q.answer_scheme, "(D)(D) both are correct, definitely (D)")
    assert ev.verdict == "fullCredit"
    assert ev.confidence == pytest.approx(0.93)
    assert ev.needs_review is False


def test_ambiguous_reasoning_shows_in_reasoning_text():
    # First-match picks B here (real answer stated last, after eliminating
    # B and C) -- a genuinely unresolvable case for a first-letter heuristic,
    # which is exactly why it must be surfaced for review rather than
    # trusted at full confidence either way.
    q = _question(marks=1, scheme=_objective_scheme("D"))
    ev = evaluate_answer(q, q.answer_scheme, "Ruled out (B) and (C); the correct one is (D).")
    assert ev.verdict == "noCredit"
    assert ev.needs_review is True
    assert ev.confidence < REVIEW_THRESHOLD
    assert "uncertain" in ev.reasoning.lower() or "human check" in ev.reasoning.lower()


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


# ------------------------------------------------------ any N of the above ---
# Task 124 splits "Any two of the following" into every listed point at
# marks/N, records `anyOf` on the scheme and marks each listed point
# isRequired=False (corpus/marking_split.py value_points), because the board
# awards only N of them. The scorer has to read that flag: the alternatives a
# full-credit answer did not take are not gaps.

def _any_of_scheme() -> AnswerSchemeSchema:
    """cbse:sqp:ClassX_2022_23:Home Science:22 in miniature -- five listed
    ways for a 2-mark question, "Any other, Any two"."""
    return AnswerSchemeSchema(
        total_marks=2,
        marking_points=[
            MarkingPointSchema(id=f"mp{i}", description=f"way {i}", marks=1,
                               keyword=kw, is_required=False)
            for i, kw in enumerate(("posture", "crouch", "bucket", "trolley", "stool"), 1)],
        metadata={"anyOf": 2},
    )


def test_any_two_scheme_does_not_report_the_untaken_alternatives_as_gaps():
    scheme = _any_of_scheme()
    q = _question(marks=2, scheme=scheme)
    ev = evaluate_answer(q, scheme, "Change your posture often, and crouch to lift a load.")
    assert ev.awarded_marks == 2
    assert ev.verdict == "fullCredit"
    # The other three ways were never required: two of five is the whole answer.
    assert ev.gaps == []
    assert "Missing" not in ev.reasoning
    assert "3 further" in ev.reasoning


def test_any_two_scheme_still_reports_alternatives_short_of_full_marks():
    """One way of five earns one of two marks, and another alternative would
    earn the second -- so short of the quota they are still what is missing."""
    scheme = _any_of_scheme()
    q = _question(marks=2, scheme=scheme)
    ev = evaluate_answer(q, scheme, "Change your posture often.")
    assert ev.awarded_marks == 1
    assert ev.verdict == "partialCredit"
    assert ev.gaps == ["way 2", "way 3", "way 4", "way 5"]


def test_a_required_point_is_still_a_gap_at_full_marks():
    """Only an alternative is suppressed. A scheme whose points are all
    required cannot reach full marks with one unmatched, but a capped award
    can (`awarded_marks_clamped_to_max`), and that point is genuinely missing."""
    scheme = AnswerSchemeSchema(
        total_marks=2,
        marking_points=[_point("mp1", 2, "oxygen", description="a"),
                        _point("mp2", 2, "glucose", description="b")],
    )
    q = _question(marks=2, scheme=scheme)
    ev = evaluate_answer(q, scheme, "Oxygen is released")
    assert ev.awarded_marks == 2
    assert ev.gaps == ["b"]


# --------------------------------------------------------- keyless scheme ---
# C4: a question whose answer_scheme has zero marking points has no key at all.
# The scorer used to fall through and produce a confident-sounding verdict
# ("none of the expected marking points were found", ~0.9 confidence, no review
# flag) on the strength of an empty rubric. A/B test below: the same answer
# scores confidently noCredit against a real key, but must be low-confidence
# and routed to a human when there is no scheme to score against.

def test_keyless_scheme_routes_to_review_not_confident_zero():
    answer = "Photosynthesis and respiration are opposite metabolic processes"
    assert len(answer) >= DESCRIPTIVE_MIN_CHARS  # must be scoreable length

    # A: a real key exists, the answer genuinely misses every point -> a
    #    confident noCredit with no review flag (legitimate zero, the marker
    #    matched real points and found none).
    keyed = AnswerSchemeSchema(
        total_marks=2,
        marking_points=[_point("mp1", 2, "calcium", description="calcium")],
        metadata={},
    )
    ev_keyed = evaluate_answer(_question(marks=2, scheme=keyed), keyed, answer)
    assert ev_keyed.verdict == "noCredit"
    assert ev_keyed.awarded_marks == 0
    assert ev_keyed.confidence >= REVIEW_THRESHOLD
    assert ev_keyed.needs_review is False

    # B: the same answer against a question with NO marking points at all.
    #    Before the fix this computed the same confident noCredit shape
    #    (0.8-0.9 confidence, needs_review=False) -- an authoritative-looking
    #    score with nothing to score against. It must now fail safe.
    keyless = AnswerSchemeSchema(total_marks=2, metadata={})
    assert keyless.marking_points == []  # genuinely keyless
    ev_keyless = evaluate_answer(_question(marks=2, scheme=keyless), keyless, answer)
    assert ev_keyless.awarded_marks == 0
    assert ev_keyless.verdict == "partialCredit"      # cannot score, not zero-credit
    assert ev_keyless.confidence == 0.0
    assert ev_keyless.confidence < REVIEW_THRESHOLD
    assert ev_keyless.needs_review is True
    assert "no marking" in ev_keyless.reasoning.lower()
    assert "cannot be graded automatically" in ev_keyless.reasoning.lower()


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