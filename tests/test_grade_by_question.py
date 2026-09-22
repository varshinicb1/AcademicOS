"""Grade by question, not by student (C3).

The claim being tested is a workflow claim, so the tests assert the workflow:
one question yields every student's answer with the scheme attached once, and one
decision applies to many students -- without ever becoming able to produce a
state the per-student path could not.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.assessment import grade_by_question as gbq
from academicos.assessment.audit_log import AuditLog
from academicos.assessment.auth_routes import get_current_user
from academicos.assessment.consent import ConsentStore
from academicos.assessment.grade_lock import FINALIZED_ACTION


# --------------------------------------------------------------------------- #
# a store small enough to reason about, shaped like GradedStore
# --------------------------------------------------------------------------- #

@dataclass
class FakeQuestion:
    id: str
    stem: str = "Explain the light reaction."
    marks: int = 3


@dataclass
class FakeEvaluation:
    question_id: str
    awarded_marks: int = 0
    max_marks: int = 3
    verdict: str = "partialCredit"
    confidence: float = 0.5
    reasoning: str = "model reasoning"
    needs_review: bool = True
    student_answer: str = "some answer"


class FakeGradedStore:
    """Mirrors `GradedStore`: `for_assessment -> {student_id: [(question, eval)]}`."""

    def __init__(self, sheets):
        self._sheets = sheets
        self.saves = 0

    def for_assessment(self, assessment_id):
        return self._sheets.get(assessment_id, {})

    def save(self, assessment_id, student_id, graded):
        self._sheets[assessment_id][student_id] = graded
        self.saves += 1


def sheet(awarded=0, max_marks=3, qid="q1", needs_review=True):
    return [(FakeQuestion(qid), FakeEvaluation(
        question_id=qid, awarded_marks=awarded, max_marks=max_marks,
        needs_review=needs_review))]


@pytest.fixture
def ctx(tmp_path):
    sheets = {
        "a1": {
            "s1": sheet(0), "s2": sheet(3, needs_review=False),
            "s3": sheet(1), "s4": sheet(2),
        },
    }
    store = FakeGradedStore(sheets)
    # A real AuditLog on tmp_path: every award is audited, and the route
    # refuses to write without one (grade_lock.py).
    store.audit = AuditLog(tmp_path / "audit.sqlite")
    # A real ConsentStore too: every student here has a parent's consent on
    # file, because the route refuses to grade anyone without it
    # (authz.require_consent).
    store.consent = ConsentStore(tmp_path / "consents.db")
    for sid in ("s1", "s2", "s3", "s4"):
        store.consent.record_consent(school_id="school_1", student_id=sid,
                                     guardian_name="Guardian", method="Signed admission form",
                                     recorded_by="test-fixture")
    gbq.init(
        audit=lambda: store.audit,
        consent=lambda: store.consent,
        graded=store,
        require=lambda: None,
        require_school_owns_assessment=lambda aid, user: None,
        questions_by_id=lambda qid: {
            "answerScheme": {"provenance": "cbse_marking_scheme",
                             "markingPoints": [{"id": "mp1", "description": "light energy", "marks": 1}]}
        } if qid == "q1" else None,
    )
    app = FastAPI()
    app.include_router(gbq.router)
    app.dependency_overrides[get_current_user] = lambda: _User()
    return TestClient(app), store


class _User:
    id = "u1"
    school_id = "school_1"
    # Both routes are require_staff (api/route_policy.py); a student is
    # refused before any of this runs -- see tests/test_role_gates.py.
    role = "teacher"


# --------------------------------------------------------------------------- #
# read side
# --------------------------------------------------------------------------- #

def test_one_question_returns_every_students_answer(ctx):
    c, _ = ctx
    body = c.get("/api/v1/evaluations/assessment/a1/question/q1").json()
    assert body["total"] == 4
    assert [a["studentId"] for a in body["answers"]] == ["s1", "s2", "s3", "s4"]


def test_the_scheme_is_attached_once_for_the_whole_batch(ctx):
    """The whole point of the transposed view: read the value points once."""
    c, _ = ctx
    body = c.get("/api/v1/evaluations/assessment/a1/question/q1").json()
    assert body["schemeProvenance"] == "cbse_marking_scheme"
    assert len(body["markingPoints"]) == 1
    assert body["marks"] == 3


def test_the_read_counts_what_still_needs_review(ctx):
    c, _ = ctx
    body = c.get("/api/v1/evaluations/assessment/a1/question/q1").json()
    assert body["needsReview"] == 3
    assert body["alreadyGraded"] == 1


def test_a_question_not_in_any_sheet_is_404(ctx):
    c, _ = ctx
    assert c.get("/api/v1/evaluations/assessment/a1/question/nope").status_code == 404


def test_an_assessment_with_no_sheets_is_404(ctx):
    c, _ = ctx
    assert c.get("/api/v1/evaluations/assessment/missing/question/q1").status_code == 404


def test_a_missing_scheme_does_not_break_the_batch(ctx):
    """A teacher must be able to mark a question the bank has never seen."""
    c, _ = ctx
    sheets = {"a2": {"s1": sheet(qid="school-made-q")}}
    gbq._deps["graded"]._sheets.update(sheets)
    body = c.get("/api/v1/evaluations/assessment/a2/question/school-made-q").json()
    assert body["total"] == 1
    assert body["markingPoints"] == []
    assert body["schemeProvenance"] == "none"


# --------------------------------------------------------------------------- #
# write side
# --------------------------------------------------------------------------- #

def test_award_applies_one_decision_to_selected_students(ctx):
    c, store = ctx
    body = c.post("/api/v1/evaluations/assessment/a1/question/q1/award",
                  json={"marks": 3, "studentIds": ["s1", "s3"]}).json()
    assert body["updated"] == 2
    assert body["unchanged"] == 0
    assert [e.awarded_marks for _q, e in store._sheets["a1"]["s1"]] == [3]
    assert [e.awarded_marks for _q, e in store._sheets["a1"]["s3"]] == [3]


def test_award_clears_the_review_flag(ctx):
    c, store = ctx
    c.post("/api/v1/evaluations/assessment/a1/question/q1/award",
           json={"marks": 2, "studentIds": ["s1"]})
    assert [e.needs_review for _q, e in store._sheets["a1"]["s1"]] == [False]


def test_award_can_target_the_whole_class_explicitly(ctx):
    c, store = ctx
    body = c.post("/api/v1/evaluations/assessment/a1/question/q1/award",
                  json={"marks": 3, "allStudents": True}).json()
    # s2 already had 3, so it counts as unchanged rather than updated.
    assert body["updated"] == 3
    assert body["unchanged"] == 1


def test_an_empty_student_list_never_means_the_whole_class(ctx):
    """The safety case. A caller that forgot the list must not award to everyone."""
    c, store = ctx
    r = c.post("/api/v1/evaluations/assessment/a1/question/q1/award",
               json={"marks": 3, "studentIds": []})
    assert r.status_code == 400
    assert store.saves == 0
    assert [e.awarded_marks for _q, e in store._sheets["a1"]["s1"]] == [0]


def test_sending_both_target_forms_is_refused(ctx):
    c, _ = ctx
    r = c.post("/api/v1/evaluations/assessment/a1/question/q1/award",
               json={"marks": 3, "studentIds": ["s1"], "allStudents": True})
    assert r.status_code == 400


def test_award_is_clamped_to_each_students_own_maximum(ctx):
    """A caller cannot award 10 on a 3-mark question, and the clamp uses the
    student's max rather than the request's idea of it."""
    c, store = ctx
    c.post("/api/v1/evaluations/assessment/a1/question/q1/award",
           json={"marks": 99, "studentIds": ["s1"]})
    assert [e.awarded_marks for _q, e in store._sheets["a1"]["s1"]] == [3]


def test_unknown_students_are_reported_not_silently_dropped(ctx):
    c, _ = ctx
    body = c.post("/api/v1/evaluations/assessment/a1/question/q1/award",
                  json={"marks": 1, "studentIds": ["s1", "ghost"]}).json()
    assert body["updated"] == 1
    assert body["skipped"] == ["ghost"]


def test_an_already_correct_mark_counts_as_unchanged(ctx):
    c, _ = ctx
    body = c.post("/api/v1/evaluations/assessment/a1/question/q1/award",
                  json={"marks": 3, "studentIds": ["s2"]}).json()
    assert body["unchanged"] == 1
    assert body["updated"] == 0


def test_award_carries_the_teachers_note_into_the_reasoning(ctx):
    c, store = ctx
    c.post("/api/v1/evaluations/assessment/a1/question/q1/award",
           json={"marks": 2, "studentIds": ["s1"], "note": "value point 2 missing"})
    assert [e.reasoning for _q, e in store._sheets["a1"]["s1"]] == ["value point 2 missing"]


def test_award_does_not_touch_other_questions_on_the_sheet(ctx):
    """A sheet carries several questions; a bulk award for one must leave the
    rest alone."""
    c, store = ctx
    store._sheets["a1"]["s1"] = sheet(0, qid="q1") + sheet(1, qid="q2")
    c.post("/api/v1/evaluations/assessment/a1/question/q1/award",
           json={"marks": 3, "studentIds": ["s1"]})
    marks = {q.id: e.awarded_marks for q, e in store._sheets["a1"]["s1"]}
    assert marks == {"q1": 3, "q2": 1}


def test_award_on_an_unknown_assessment_is_404(ctx):
    c, _ = ctx
    r = c.post("/api/v1/evaluations/assessment/missing/question/q1/award",
               json={"marks": 1, "allStudents": True})
    assert r.status_code == 404


def test_negative_marks_are_refused(ctx):
    c, _ = ctx
    r = c.post("/api/v1/evaluations/assessment/a1/question/q1/award",
               json={"marks": -1, "studentIds": ["s1"]})
    assert r.status_code == 422


# --------------------------------------------------------------------------- #
# the audit trail and the finalized lock (grade_lock.py, audit item 8.5)
# --------------------------------------------------------------------------- #

def test_every_changed_student_gets_one_audit_entry(ctx):
    c, store = ctx
    body = c.post("/api/v1/evaluations/assessment/a1/question/q1/award",
                  json={"marks": 3, "allStudents": True}).json()
    assert body["updated"] == 3
    entries = store.audit.for_action("grade_awarded")
    # s2 already had 3: unchanged, so no entry for it.
    assert sorted(e["student_id"] for e in entries) == ["s1", "s3", "s4"]
    assert all(e["actor"] == "u1" for e in entries)
    by_student = {e["student_id"]: e["details"] for e in entries}
    assert by_student["s3"]["before"] == 1 and by_student["s3"]["after"] == 3


def test_one_finalized_sheet_refuses_the_whole_award_without_a_reason(ctx):
    """No half-applied bulk award: the lock on s3 stops s1's change too."""
    c, store = ctx
    store.audit.append(FINALIZED_ACTION, assessment_id="a1", student_id="s3", actor="u1")
    r = c.post("/api/v1/evaluations/assessment/a1/question/q1/award",
               json={"marks": 3, "studentIds": ["s1", "s3"]})
    assert r.status_code == 409, r.text
    assert store.saves == 0
    assert store.audit.for_action("grade_awarded") == []

    r = c.post("/api/v1/evaluations/assessment/a1/question/q1/award",
               json={"marks": 3, "studentIds": ["s1", "s3"], "reason": "moderation"})
    assert r.status_code == 200, r.text
    finalized = {e["student_id"]: e["details"]["finalized"]
                 for e in store.audit.for_action("grade_awarded")}
    assert finalized == {"s1": False, "s3": True}


def test_one_student_without_consent_refuses_the_whole_award(ctx):
    """Withdrawn consent on s3 stops s1's change too, and names s3."""
    c, store = ctx
    store.consent.revoke_consent("school_1", "s3", revoked_by="u1")
    r = c.post("/api/v1/evaluations/assessment/a1/question/q1/award",
               json={"marks": 3, "studentIds": ["s1", "s3"]})
    assert r.status_code == 409, r.text
    assert "no recorded parental consent for student s3" in r.json()["detail"]
    assert store.saves == 0
    assert store.audit.for_action("grade_awarded") == []


def test_without_a_consent_store_the_award_writes_nothing(ctx):
    c, store = ctx
    gbq._deps["consent"] = None
    r = c.post("/api/v1/evaluations/assessment/a1/question/q1/award",
               json={"marks": 3, "studentIds": ["s1"]})
    assert r.status_code == 503
    assert store.saves == 0


def test_without_an_audit_log_the_award_writes_nothing(ctx):
    c, store = ctx
    gbq._deps["audit"] = None
    r = c.post("/api/v1/evaluations/assessment/a1/question/q1/award",
               json={"marks": 3, "studentIds": ["s1"]})
    assert r.status_code == 503
    assert store.saves == 0
