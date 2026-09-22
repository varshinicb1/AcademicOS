"""No student's work is processed without recorded parental consent.

Audit item 8.5 (2026-09-21): "Parental consent is recorded but never checked.
A grep found no has_consent or consent reference outside consent.py and
consent_routes.py, so grading and scanning proceed without consent (a DPDP
gap)." Every CBSE student is a minor, and DPDP Act 2023 s.9 requires verifiable
parental consent before their data is processed (docs/compliance.md).

These tests hold the fixed contract, through the real routes of a booted app:

* grading a student with no consent on file is 409 with a message that says
  what to do; after consent is recorded it is 200; after it is withdrawn it is
  409 again (withdrawn consent is no consent);
* a refused request writes nothing: no graded sheet, no audit entry;
* starting a scan session for a student without consent is 409, and so is
  every later write on a session whose consent was withdrawn;
* a bulk award refuses the whole request, before any write, if any target
  student has no consent;
* reading already-stored work still works for staff after withdrawal --
  reading is not processing new data;
* a school can ask which of a list of students have no active consent.

Every store is under pytest's tmp_path; nothing touches a live service.
"""
from __future__ import annotations

import pytest

from academicos.api.main import app
from academicos.assessment import audit_log as audit_mod

from _auth_helpers import register_invited
from test_route_inventory import blueprint_body, question_body

GOOD_ANSWER = ("The solution is x = 2, obtained by subtracting 3 from both sides "
               "then dividing by 2.")


class World:
    def __init__(self, client, headers, aid, data_root):
        self.client = client
        self.headers = headers
        self.aid = aid
        self.data_root = data_root

    def grant(self, student_id: str):
        r = self.client.post("/api/v1/consent", json={
            "studentId": student_id, "guardianName": "Parent of " + student_id,
            "guardianRelationship": "parent", "method": "Signed admission form",
        }, headers=self.headers)
        assert r.status_code == 200, r.text

    def withdraw(self, student_id: str):
        r = self.client.delete(f"/api/v1/consent/students/{student_id}", headers=self.headers)
        assert r.status_code == 200, r.text

    def evaluate_sheet(self, student_id: str, **extra):
        return self.client.post("/api/v1/evaluations/sheet", json={
            "assessmentId": self.aid, "studentId": student_id, "studentName": "S",
            "questions": [question_body()], "answers": {"q_1": GOOD_ANSWER},
            "correctOptions": {}, **extra,
        }, headers=self.headers)

    def evaluate_answer(self, student_id: str):
        return self.client.post("/api/v1/evaluations/answer", json={
            "assessmentId": self.aid, "studentId": student_id,
            "question": question_body(), "studentAnswer": GOOD_ANSWER,
        }, headers=self.headers)

    def create_scan(self, student_id: str):
        return self.client.post("/api/v1/scan/sessions", json={
            "assessmentId": self.aid, "studentId": student_id, "studentName": "S",
        }, headers=self.headers)

    def audit(self) -> list[dict]:
        return audit_mod.get_audit_log(self.data_root).for_assessment(self.aid)


@pytest.fixture
def world(tmp_path, monkeypatch):
    from academicos.assessment import consent as consent_mod
    from academicos.assessment import consent_routes as consent_routes_mod
    from academicos.assessment import users as users_mod
    from academicos.curriculum import store as curriculum_store_mod
    from fastapi.testclient import TestClient

    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr(audit_mod, "_INSTANCE", None)
    monkeypatch.setattr(users_mod, "_INSTANCE", None)
    monkeypatch.setattr(curriculum_store_mod, "_INSTANCE", None)
    monkeypatch.setattr(consent_mod, "_INSTANCE", None)
    monkeypatch.setattr(consent_routes_mod, "_store", None)
    monkeypatch.setattr(consent_routes_mod, "_audit", None)
    with TestClient(app) as client:
        teacher = register_invited(client, "school_1", "consent-t@example.com")
        headers = {"Authorization": f"Bearer {teacher['token']}"}
        created = client.post("/api/v1/assessments", json={
            "teacherId": teacher["user"]["id"], "schoolId": "school_1",
            "title": "Consent", "subject": "Mathematics", "grade": 10,
            "chapterIds": [], "blueprint": blueprint_body(),
        }, headers=headers)
        assert created.status_code == 200, created.text
        yield World(client, headers, created.json()["id"], tmp_path)


def _assert_consent_refusal(r, student_id: str):
    assert r.status_code == 409, r.text
    detail = r.json()["detail"]
    assert f"no recorded parental consent for student {student_id}" in detail
    assert "Classes" in detail


# --------------------------------------------------------------------------- #
# grading
# --------------------------------------------------------------------------- #

def test_grading_needs_consent_and_withdrawal_stops_it_again(world):
    refused = world.evaluate_sheet("s_1")
    _assert_consent_refusal(refused, "s_1")
    assert world.audit() == [], "a refused grading must write no audit entry"
    view = world.client.get(f"/api/v1/evaluations/assessment/{world.aid}/question/q_1",
                            headers=world.headers)
    assert view.status_code == 404, "a refused grading must store no sheet"

    world.grant("s_1")
    accepted = world.evaluate_sheet("s_1")
    assert accepted.status_code == 200, accepted.text

    world.withdraw("s_1")
    _assert_consent_refusal(world.evaluate_sheet("s_1"), "s_1")
    _assert_consent_refusal(world.evaluate_answer("s_1"), "s_1")


def test_a_single_answer_needs_consent(world):
    _assert_consent_refusal(world.evaluate_answer("s_2"), "s_2")
    world.grant("s_2")
    assert world.evaluate_answer("s_2").status_code == 200


def test_consent_is_per_school(world):
    """Consent recorded by another school is not this school's consent."""
    other = register_invited(world.client, "school_2", "consent-o@example.com")
    r = world.client.post("/api/v1/consent", json={
        "studentId": "s_3", "guardianName": "Parent", "method": "Signed admission form",
    }, headers={"Authorization": f"Bearer {other['token']}"})
    assert r.status_code == 200, r.text
    _assert_consent_refusal(world.evaluate_sheet("s_3"), "s_3")


def test_review_finalize_and_award_stop_once_consent_is_withdrawn(world):
    world.grant("s_4")
    assert world.evaluate_sheet("s_4").status_code == 200
    world.withdraw("s_4")
    before = len(world.audit())

    review = world.client.post(
        f"/api/v1/evaluations/sheet/{world.aid}/s_4/review/q_1",
        json={"action": "edit", "marks": 0}, headers=world.headers)
    _assert_consent_refusal(review, "s_4")
    finalize = world.client.post(
        f"/api/v1/evaluations/sheet/{world.aid}/s_4/finalize", json={}, headers=world.headers)
    _assert_consent_refusal(finalize, "s_4")
    award = world.client.post(
        f"/api/v1/evaluations/assessment/{world.aid}/question/q_1/award",
        json={"marks": 0, "studentIds": ["s_4"]}, headers=world.headers)
    _assert_consent_refusal(award, "s_4")
    assert len(world.audit()) == before, "a refused change must not be logged as made"


def test_a_bulk_award_is_refused_whole_when_one_student_lacks_consent(world):
    for sid in ("s_5", "s_6"):
        world.grant(sid)
        assert world.evaluate_sheet(sid).status_code == 200
    world.withdraw("s_6")
    view_url = f"/api/v1/evaluations/assessment/{world.aid}/question/q_1"
    before = world.client.get(view_url, headers=world.headers).json()["answers"]

    r = world.client.post(f"{view_url}/award", json={"marks": 0, "allStudents": True},
                          headers=world.headers)
    _assert_consent_refusal(r, "s_6")
    after = world.client.get(view_url, headers=world.headers).json()["answers"]
    assert after == before, "a bulk award must not land half-applied"


# --------------------------------------------------------------------------- #
# scanning
# --------------------------------------------------------------------------- #

def test_a_scan_session_needs_consent(world):
    _assert_consent_refusal(world.create_scan("s_7"), "s_7")

    world.grant("s_7")
    created = world.create_scan("s_7")
    assert created.status_code == 200, created.text
    session_id = created.json()["id"]

    world.withdraw("s_7")
    base = f"/api/v1/scan/sessions/{session_id}"
    upload = world.client.post(f"{base}/pages", files={"file": ("p.jpg", b"x", "image/jpeg")},
                               headers=world.headers)
    _assert_consent_refusal(upload, "s_7")
    _assert_consent_refusal(world.client.post(f"{base}/process", headers=world.headers), "s_7")
    _assert_consent_refusal(world.client.post(f"{base}/review/q_1", json={"action": "approve"},
                                              headers=world.headers), "s_7")
    _assert_consent_refusal(world.client.post(f"{base}/finalize", headers=world.headers), "s_7")
    # Reading the session back is not processing: it still answers.
    assert world.client.get(f"{base}/review", headers=world.headers).status_code == 200


# --------------------------------------------------------------------------- #
# practice (a student's own work, submitted by the student)
# --------------------------------------------------------------------------- #

def test_practice_needs_consent(world):
    student = register_invited(world.client, "school_1", "consent-s@example.com",
                               name="Asha", role="student")
    sid = student["user"]["id"]
    s_auth = {"Authorization": f"Bearer {student['token']}"}
    body = {"studentId": sid, "subject": "Science", "grade": "X"}

    _assert_consent_refusal(
        world.client.post("/api/v1/practice/generate", json=body, headers=s_auth), sid)
    world.grant(sid)
    # With consent the route runs: this student has no weak concepts yet.
    assert world.client.post("/api/v1/practice/generate", json=body,
                             headers=s_auth).status_code == 400


# --------------------------------------------------------------------------- #
# reads keep working
# --------------------------------------------------------------------------- #

def test_staff_can_still_read_stored_work_after_withdrawal(world):
    world.grant("s_8")
    assert world.evaluate_sheet("s_8").status_code == 200
    world.withdraw("s_8")

    view = world.client.get(f"/api/v1/evaluations/assessment/{world.aid}/question/q_1",
                            headers=world.headers)
    assert view.status_code == 200, view.text
    assert [a["studentId"] for a in view.json()["answers"]] == ["s_8"]
    insights = world.client.get(f"/api/v1/insights/class/{world.aid}", headers=world.headers)
    assert insights.status_code == 200, insights.text


# --------------------------------------------------------------------------- #
# who is missing consent before a test
# --------------------------------------------------------------------------- #

def test_a_school_can_list_who_is_missing_consent(world):
    world.grant("s_9")
    world.grant("s_10")
    world.withdraw("s_10")
    r = world.client.get("/api/v1/consent/missing",
                         params=[("studentIds", "s_9"), ("studentIds", "s_10"),
                                 ("studentIds", "s_11")],
                         headers=world.headers)
    assert r.status_code == 200, r.text
    assert r.json() == {"checked": 3, "missing": ["s_10", "s_11"]}


def test_practice_submit_needs_consent_and_writes_no_mastery_without_it(world):
    """/practice/submit scores a student's answers and folds them into the
    knowledge model -- processing, so it is gated like grading. The set is
    saved the way /practice/generate saves one (as test_role_gates does):
    generating it through the route would need graded evidence of a weak
    concept first, and the submit gate reads only the stored set's student.

    Each refusal is checked against the knowledge model, not just the status
    code: a 409 that still recorded the answers would be the exact DPDP gap
    this gate closes, and nothing else in the response would show it."""
    from academicos.assessment import pillar_routes
    from academicos.assessment.remediation import PracticeItem, PracticeSet
    from academicos.assessment.schemas import QuestionSchema

    student = register_invited(world.client, "school_1", "consent-ps@example.com",
                               name="Ravi", role="student")
    sid = student["user"]["id"]
    s_auth = {"Authorization": f"Bearer {student['token']}"}
    question = QuestionSchema.model_validate(question_body())
    pset = PracticeSet(id="pset_consent", student_id=sid, concept_ids=["linear_eq"],
                       items=[PracticeItem(question=question, concept_id="linear_eq")])
    pillar_routes._require_practice().save(pset, school_id="school_1")
    _, knowledge, _ = pillar_routes._require()
    body = {"setId": pset.id, "answers": {"q_1": GOOD_ANSWER}}

    def mastery():
        return [(v.concept_id, v.mastery) for v in knowledge.mastery(sid)]

    _assert_consent_refusal(
        world.client.post("/api/v1/practice/submit", json=body, headers=s_auth), sid)
    assert mastery() == [], "a refused submit must not touch the knowledge model"

    world.grant(sid)
    accepted = world.client.post("/api/v1/practice/submit", json=body, headers=s_auth)
    assert accepted.status_code == 200, accepted.text
    after_grant = mastery()
    assert after_grant, "with consent the submit is recorded in the knowledge model"

    world.withdraw(sid)
    _assert_consent_refusal(
        world.client.post("/api/v1/practice/submit", json=body, headers=s_auth), sid)
    assert mastery() == after_grant, "a submit after withdrawal must change nothing"


# --------------------------------------------------------------------------- #
# an unreadable consent status is no consent
# --------------------------------------------------------------------------- #

def test_a_consent_row_with_an_empty_status_refuses_grading(tmp_path, monkeypatch):
    """authz.students_without_consent turns the ValueError consent.from_row
    raises for a blank status into "missing". Without that branch the error
    would escape as a 500 from every grading route; with a reader that
    defaulted instead, it would be a silent 200 -- the pre-2026-09 bug where
    `status or "granted"` read a truncated row as consent. Neither is the
    right answer to "I cannot tell"; a 409 naming the student is.

    The column is NOT NULL, so the reachable bad state is an empty string
    (a partial remote payload or a hand-edited row), written here straight
    through sqlite because the store's own API can never produce it."""
    from fastapi import HTTPException

    from academicos.assessment import authz
    from academicos.assessment.consent import ConsentStore

    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    store = ConsentStore(tmp_path / "assessment" / "consents.db")
    store.conn.execute(
        "INSERT INTO parental_consents (id, school_id, student_id, guardian_name, "
        "guardian_relationship, method, status, recorded_by, recorded_at) "
        "VALUES ('c_blank', 'school_1', 's_blank', 'Parent', 'parent', "
        "'Signed admission form', '', 'u_1', '2026-09-22T00:00:00+00:00')")
    store.conn.commit()

    with pytest.raises(ValueError):
        store.has_consent("school_1", "s_blank")  # the store itself fails closed
    assert authz.students_without_consent(store, "school_1", ["s_blank"]) == ["s_blank"]
    with pytest.raises(HTTPException) as refused:
        authz.require_consent(store, "school_1", "s_blank")
    assert refused.value.status_code == 409
    assert "no recorded parental consent for student s_blank" in refused.value.detail
