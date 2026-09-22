"""Audit regression tests for assessment/knowledge.py.

C2: `record_evaluations` must derive the recorded outcome from the teacher's
awarded/max marks, not from the scanner verdict — a teacher correcting a
"blank" verdict to full marks must see that correction land as outcome 1.0.
A/B: old code used the verdict branch ("blank" -> 0.0).

D4#2: `load()` must restore `updated_at` from the persisted payload; the old
code ignored it and returned a freshly-constructed timestamp, which made any
save-after-load look like a concurrent mutation to external consumers.

D4#3: the local file path sanitizer must be injective so distinct student ids
cannot collide on the same file ("stu.dent" vs "student"). A/B: old code
dropped disallowed characters, collapsing those two ids.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.assessment.evaluate import Evaluation  # noqa: E402
from academicos.assessment.knowledge import KnowledgeStore  # noqa: E402
from academicos.assessment.schemas import (  # noqa: E402
    AnswerSchemeSchema,
    MarkingPointSchema,
    QuestionSchema,
)


def _question(marks: int = 4) -> QuestionSchema:
    now = datetime.now(timezone.utc)
    scheme = AnswerSchemeSchema(
        total_marks=marks,
        marking_points=[MarkingPointSchema(id="mp1", description="correct",
                                           marks=marks, keyword="answer")],
        metadata={},
    )
    return QuestionSchema(
        id="q1", question_bank_id="bank1", subject="math", grade=10,
        chapter_ids=["c1"], competency_ids=[], bloom_level="understand",
        difficulty="medium", type="short_answer", stem="s", parts=[],
        answer_scheme=scheme, estimated_time_minutes=2, marks=marks, language="en",
        source="teacher_created", quality_score=0.7, tags=[], created_at=now,
        updated_at=now,
    )


def test_teacher_correction_of_blank_verdict_keeps_awarded_marks(tmp_path):
    ks = KnowledgeStore(tmp_path)
    ev = Evaluation(question_id="q1", awarded_marks=4, max_marks=4,
                    verdict="blank", confidence=0.9, reasoning="teacher re-checked",
                    ocr_warnings=[], needs_review=False)
    model = ks.record_evaluations("s1", [(_question(), ev)])
    state = model.concepts["c1"]
    assert state.history[-1].outcome == 1.0


def test_genuine_blank_awarded_zero_records_zero(tmp_path):
    ks = KnowledgeStore(tmp_path)
    ev = Evaluation(question_id="q1", awarded_marks=0, max_marks=4,
                    verdict="blank", confidence=0.9, reasoning="",
                    ocr_warnings=[], needs_review=False)
    model = ks.record_evaluations("s1", [(_question(), ev)])
    state = model.concepts["c1"]
    assert state.history[-1].outcome == 0.0


def test_partial_credit_is_fractional(tmp_path):
    ks = KnowledgeStore(tmp_path)
    ev = Evaluation(question_id="q1", awarded_marks=3, max_marks=4,
                    verdict="partial", confidence=0.9, reasoning="",
                    ocr_warnings=[], needs_review=False)
    model = ks.record_evaluations("s1", [(_question(), ev)])
    state = model.concepts["c1"]
    assert state.history[-1].outcome == pytest.approx(0.75)


def test_updated_at_restored_on_load(tmp_path):
    ks = KnowledgeStore(tmp_path)
    model = ks.load("s1")
    model.updated_at = "2026-08-01T00:00:00+00:00"
    ks.save(model)
    loaded = ks.load("s1")
    assert loaded.updated_at == "2026-08-01T00:00:00+00:00"


def test_updated_at_roundtrip_survives_concurrent_save(tmp_path):
    ks = KnowledgeStore(tmp_path)
    a = ks.load("s1")
    a.updated_at = "2026-08-01T00:00:00+00:00"
    ks.save(a)
    b = ks.load("s1")
    b.updated_at = "2026-08-02T00:00:00+00:00"
    ks.save(b)
    assert ks.load("s1").updated_at == "2026-08-02T00:00:00+00:00"


def test_path_sanitization_is_injective(tmp_path):
    ks = KnowledgeStore(tmp_path)
    assert ks._path("stu.dent") != ks._path("student")
    assert ks._path("a.b") != ks._path("a%2eb")
    assert ks._path("stu%2Edent") != ks._path("stu%252Edent")


def test_dotted_id_saves_and_loads_without_colliding(tmp_path):
    ks = KnowledgeStore(tmp_path)
    model_a = ks.load("stu.dent")
    model_b = ks.load("student")
    model_a.updated_at = "2026-08-01T00:00:00+00:00"
    model_b.updated_at = "2026-08-02T00:00:00+00:00"
    ks.save(model_a)
    ks.save(model_b)
    assert ks.load("stu.dent").updated_at == "2026-08-01T00:00:00+00:00"
    assert ks.load("student").updated_at == "2026-08-02T00:00:00+00:00"


# --------------------------------------------------------------------------- #
# a re-finalize keeps the sheet's original timestamp (Task 306 review)
# --------------------------------------------------------------------------- #
#
# KnowledgeMastery weights each answer's confidence by its age and computes
# retention from last_seen. If a re-finalize stamped the replacement answers
# with the time of the re-finalize, correcting one mark on a sheet sat weeks
# ago would make the whole sheet look freshly sat: retention back to ~1.0 and
# the sheet's confidence weight back to full. The evidence count would still
# be right, so nothing else would show it.

def _ev(awarded: int) -> Evaluation:
    return Evaluation(question_id="q1", awarded_marks=awarded, max_marks=4,
                      verdict="partial", confidence=0.9, reasoning="",
                      ocr_warnings=[], needs_review=False)


def _backdate(ks: KnowledgeStore, student_id: str, days: int) -> str:
    """Move every stored timestamp `days` into the past, as if the sheet had
    been finalized then. Returns the new sheet timestamp."""
    model = ks.load(student_id)
    old = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    for state in model.concepts.values():
        for i in state.history:
            i.ts = old
        state.last_seen = old
    ks.save(model)
    return old


def test_re_finalizing_keeps_the_sheets_original_timestamp(tmp_path):
    ks = KnowledgeStore(tmp_path)
    src = "sheet:a1:s1"
    assert ks.record_sheet("s1", [(_question(), _ev(1))], src)
    sat = _backdate(ks, "s1", days=40)
    [before] = ks.mastery("s1")
    assert before.retention < 0.9, "the backdating must be visible to the scorer"

    # A teacher corrects the mark and finalizes again, 40 days later.
    assert ks.record_sheet("s1", [(_question(), _ev(3))], src)

    state = ks.load("s1").concepts["c1"]
    assert [(i.outcome, i.ts) for i in state.history] == [(0.75, sat)]
    assert state.last_seen == sat
    [after] = ks.mastery("s1")
    assert after.retention == pytest.approx(before.retention, abs=1e-6)
    assert after.evidence_count == 1


def test_last_seen_is_the_newest_evidence_not_the_last_written(tmp_path):
    """Practice done after the sheet stays the latest evidence when the older
    sheet is re-finalized (and so re-appended to the history)."""
    ks = KnowledgeStore(tmp_path)
    src = "sheet:a1:s1"
    ks.record_sheet("s1", [(_question(), _ev(1))], src)
    _backdate(ks, "s1", days=40)
    ks.record_evaluations("s1", [(_question(), _ev(4))])   # practice, today
    practice_ts = ks.load("s1").concepts["c1"].last_seen

    ks.record_sheet("s1", [(_question(), _ev(3))], src)

    state = ks.load("s1").concepts["c1"]
    assert state.last_seen == practice_ts
    assert len(state.history) == 2
