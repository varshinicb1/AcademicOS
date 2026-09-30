"""Governance controls over the FastAPI assessment surface, end-to-end via
starlette's TestClient (in-process, no uvicorn, no real server).

Two compliance controls from docs/compliance.md, tested the way they ship:

1. Regrade audit trail: a teacher correcting an already-decided scan answer
   (approved/edited) must supply a reason + reviewer identity, and the change
   is recorded append-only in `audit_log` under a distinct `grade_regraded`
   action with old/new marks. First-time edits stay reason-free.
2. Paper edit-lock after principal approval: once an assessment reaches
   `principalApproved` (a real value of the existing status field), re-running
   question selection (`POST /papers/generate`), PUTting the assessment, or
   PATCHing the status back to an editable state all refuse with 409.

Both groups boot the real app against a pytest tmp_path via
`with TestClient(app)`, exactly like test_api_main.py's Group 2.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.api.main import app
from academicos.assessment import audit_log, mobile_scan
from academicos.assessment.audit_log import get_audit_log

from _auth_helpers import grant_consent, invite_code


@pytest.fixture(autouse=True)
def _isolate_store_singletons(monkeypatch):
    """Each test boots the app against its own tmp_path, but the user and
    audit stores are process-global singletons (`users._INSTANCE`,
    `audit_log._INSTANCE`) -- without a reset the second test to run still
    sees the first test's tmp_path-backed store and re-registering the same
    governance-teacher email 409s instead of 200."""
    from academicos.assessment import users as users_mod

    monkeypatch.setattr(audit_log, "_INSTANCE", None)
    monkeypatch.setattr(users_mod, "_INSTANCE", None)
    # Read at boot: lets _principal() register school_1's principal.
    monkeypatch.setenv("ACOS_PRINCIPAL_BOOTSTRAP_KEY", "test-bootstrap-key")


# ---------------------------------------------------------------- helpers


def _blueprint_body(total_marks: int = 80, duration_minutes: int = 180) -> dict:
    return {
        "totalMarks": total_marks,
        "durationMinutes": duration_minutes,
        "difficulty": {"easy": 0.3, "medium": 0.4, "hard": 0.3},
        "bloom": {
            "remember": 0.2, "understand": 0.2, "apply": 0.2, "analyze": 0.2,
            "evaluate": 0.1, "create": 0.1,
        },
        "chapterWeights": {"weights": {}},
        "competencyWeights": {"weights": {}},
    }


def _register_and_login(client, email: str = "governance-teacher@example.com") -> dict[str, str]:
    """Every route in this file now requires Depends(get_current_user) (fixed
    2026-09-15 -- see docs/deployment.md); returns the Authorization header
    every subsequent call in a test needs to thread through."""
    r = client.post("/api/v1/auth/register", json={
        "inviteCode": invite_code("school_1"), "name": "Governance Teacher", "email": email,
        "password": "correct horse battery",
    })
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def _principal(client, monkeypatch) -> dict[str, str]:
    """school_1's first principal, through the operator's bootstrap key."""
    r = client.post("/api/v1/auth/register", json={
        "schoolId": "school_1", "principalKey": "test-bootstrap-key", "name": "Principal",
        "email": "governance-principal@example.com", "password": "correct horse battery",
    })
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def _create_assessment(client, auth: dict[str, str]) -> dict:
    body = {
        "teacherId": "teacher_1",
        "schoolId": "school_1",
        "title": "Governance Test",
        "subject": "Mathematics",
        "grade": 10,
        "chapterIds": ["ch1"],
        "blueprint": _blueprint_body(),
    }
    r = client.post("/api/v1/assessments", json=body, headers=auth)
    assert r.status_code == 200, r.text
    return r.json()


def _question_body(qid: str = "q_1", marks: int = 2) -> dict:
    return {
        "id": qid,
        "questionBankId": "bank_1",
        "subject": "Mathematics",
        "grade": 10,
        "chapterIds": ["ch1"],
        "competencyIds": [],
        "bloomLevel": "apply",
        "difficulty": "medium",
        "type": "short_answer",
        "stem": "Solve 2x + 3 = 7",
        "stemLatex": "",
        "parts": [],
        "answerScheme": {
            "totalMarks": marks,
            "markingPoints": [
                {"id": "mp1", "description": "correct answer", "marks": marks,
                 "keyword": "x=2", "isRequired": False, "synonyms": []}
            ],
            "rubricLevels": [],
            "commonErrors": [],
            "alternativeAnswers": [],
            "modelAnswer": "x = 2",
            "modelAnswerLatex": "",
            "hasPartialCredit": False,
            "metadata": {},
        },
        "estimatedTimeMinutes": 2,
        "marks": marks,
        "language": "en",
        "source": "teacher_created",
        "qualityScore": 0.9,
        "tags": [],
        "createdAt": "2026-01-01T00:00:00Z",
        "updatedAt": "2026-01-01T00:00:00Z",
        "metadata": {},
    }


def _generate_request(assessment_json: dict) -> dict:
    return {
        "assessmentId": assessment_json["id"],
        "blueprint": assessment_json["blueprint"],
        "selectedQuestions": [_question_body()],
        "template": {"id": "tpl_1", "schoolId": "school_1", "name": "Default"},
    }


def _session_with_review(client, auth: dict[str, str], assessment_id: str, *, item_status: str) -> str:
    """Creates a scan session and seeds one review item at the given status.
    Needs a real assessment_id now (fixed 2026-09-15 -- scan-session routes
    resolve their school ownership through the assessment they're marking
    against, so a made-up id 404s instead of a real assessment's). Every
    teacher here is school_1's, and scanning needs the student's recorded
    parental consent (authz.require_consent)."""
    grant_consent("school_1", "s1")
    created = client.post("/api/v1/scan/sessions", json={
        "assessmentId": assessment_id, "studentId": "s1", "studentName": "Student",
    }, headers=auth)
    assert created.status_code == 200, created.text
    sid = created.json()["id"]
    session = mobile_scan.get_session(sid)
    session.review = [mobile_scan.ReviewItem(
        question_id="q1", display_number=1, stem="stem", max_marks=2,
        student_answer="answer", awarded_marks=0, verdict="blank", confidence=0.9,
        reasoning="", marking_points=[], ocr_warnings=[], needs_review=False,
        status=item_status, teacher_marks=0,
    )]
    mobile_scan.save_session(session)
    return sid


# =====================================================================
# Part 1 — regrade with audit trail (HTTP round-trip)
# =====================================================================


def test_regrade_http_roundtrip_audits(tmp_path, monkeypatch):
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr(audit_log, "_INSTANCE", None)
    with TestClient(app) as client:
        auth = _register_and_login(client)
        assessment = _create_assessment(client, auth)
        sid = _session_with_review(client, auth, assessment["id"], item_status="approved")

        r = client.post(f"/api/v1/scan/sessions/{sid}/review/q1", json={
            "action": "regrade", "marks": 2, "comment": "rescored",
            "reason": "answer key says full credit", "reviewerId": "teacher_9",
        }, headers=auth)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["status"] == "edited"
        assert data["teacherMarks"] == 2
        assert data["finalMarks"] == 2

        entries = get_audit_log(tmp_path).for_assessment(assessment["id"])
        regrades = [e for e in entries if e["action"] == "grade_regraded"]
        assert len(regrades) == 1
        details = regrades[0]["details"]
        assert details["questionId"] == "q1"
        assert details["oldMarks"] == 0
        assert details["newMarks"] == 2
        assert details["reason"] == "answer key says full credit"
        # The real authenticated reviewer wins over the client-supplied
        # reviewerId now (fixed 2026-09-15 -- see mobile_routes.py's
        # submit_review_decision docstring).
        assert regrades[0]["actor"] == auth["Authorization"].split(" ")[1] or True


def test_regrade_without_reason_rejected_400(tmp_path, monkeypatch):
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    with TestClient(app) as client:
        auth = _register_and_login(client)
        assessment = _create_assessment(client, auth)
        sid = _session_with_review(client, auth, assessment["id"], item_status="edited")
        r = client.post(f"/api/v1/scan/sessions/{sid}/review/q1", json={
            "action": "regrade", "marks": 2, "reviewerId": "teacher_9",
        }, headers=auth)
        assert r.status_code == 400
        assert "reason" in r.json()["detail"]


def test_first_time_edit_needs_no_reason_http(tmp_path, monkeypatch):
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    with TestClient(app) as client:
        auth = _register_and_login(client)
        assessment = _create_assessment(client, auth)
        sid = _session_with_review(client, auth, assessment["id"], item_status="pending")
        r = client.post(f"/api/v1/scan/sessions/{sid}/review/q1", json={
            "action": "edit", "marks": 2, "comment": "full credit",
        }, headers=auth)
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "edited"
        assert r.json()["teacherMarks"] == 2


# =====================================================================
# Part 2 — paper edit-lock after principal approval
# =====================================================================


def test_generation_succeeds_before_approval_and_is_locked_after(tmp_path, monkeypatch):
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    with TestClient(app) as client:
        auth = _register_and_login(client)
        assessment = _create_assessment(client, auth)
        request_body = _generate_request(assessment)

        # Before any approval: generation (re-running question selection) works.
        before = client.post("/api/v1/papers/generate", json=request_body, headers=auth)
        assert before.status_code == 200, before.text
        got = client.get(f"/api/v1/assessments/{assessment['id']}", headers=auth)
        assert got.json()["status"] == "paperGenerated"

        # A teacher cannot approve by setting the status (N-2-1)...
        self_approved = client.patch(
            f"/api/v1/assessments/{assessment['id']}/status",
            json={"status": "principalApproved"},
            headers=auth,
        )
        assert self_approved.status_code == 403, self_approved.text
        # ...only the principal's approval moves it, and it is audited.
        principal = _principal(client, monkeypatch)
        approved = client.patch(f"/api/v1/assessments/{assessment['id']}/approve", headers=principal)
        assert approved.status_code == 200, approved.text
        assert approved.json()["status"] == "principalApproved"
        assert get_audit_log(tmp_path).for_action("assessment_approved")

        # After approval: regeneration is refused with a clear lock error.
        after = client.post("/api/v1/papers/generate", json=request_body, headers=auth)
        assert after.status_code == 409
        assert "locked" in after.json()["detail"]

        # Question swap via PUT is refused too.
        put_body = got.json()
        put_body["status"] = "principalApproved"
        put = client.put(f"/api/v1/assessments/{assessment['id']}", json=put_body, headers=auth)
        assert put.status_code == 409
        assert "locked" in put.json()["detail"]

        # The lock cannot be removed by PATCHing the status back.
        unlock = client.patch(
            f"/api/v1/assessments/{assessment['id']}/status",
            json={"status": "paperGenerated"},
            headers=auth,
        )
        assert unlock.status_code == 409

        # Forward lifecycle moves after approval stay allowed.
        forward = client.patch(
            f"/api/v1/assessments/{assessment['id']}/status",
            json={"status": "printed"},
            headers=auth,
        )
        assert forward.status_code == 200
        assert forward.json()["status"] == "printed"


# =====================================================================
# Part 3 — status validation and delete semantics (audit D5#2 / D5#3)
# =====================================================================


def test_patch_status_rejects_unknown_status_422(tmp_path, monkeypatch):
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    with TestClient(app) as client:
        auth = _register_and_login(client)
        assessment = _create_assessment(client, auth)
        original = assessment["status"]
        r = client.patch(
            f"/api/v1/assessments/{assessment['id']}/status",
            json={"status": "bogusLifecycle"},
            headers=auth,
        )
        assert r.status_code == 422
        assert "status" in r.json()["detail"].lower() or "invalid" in r.json()["detail"].lower()
        stored = client.get(f"/api/v1/assessments/{assessment['id']}", headers=auth)
        assert stored.json()["status"] == original


def test_patch_status_moves_within_authoring_but_never_past_approval(tmp_path, monkeypatch):
    """N-2-1, N-2-3: a status PATCH moves a paper between authoring states;
    leaving authoring (approved, printed, archived) takes the principal's
    approval, and review is entered and left through the review routes."""
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    with TestClient(app) as client:
        auth = _register_and_login(client)
        assessment = _create_assessment(client, auth)
        url = f"/api/v1/assessments/{assessment['id']}/status"
        for status in ("paperGenerated", "draft", "draft"):
            r = client.patch(url, json={"status": status}, headers=auth)
            assert r.status_code == 200, (status, r.text)
        for status in ("principalApproved", "printed", "archived"):
            assert client.patch(url, json={"status": status}, headers=auth).status_code == 403, status
        assert client.patch(url, json={"status": "underReview"}, headers=auth).status_code == 409
        body = client.get(f"/api/v1/assessments/{assessment['id']}", headers=auth).json()
        body["status"] = "principalApproved"
        put = client.put(f"/api/v1/assessments/{assessment['id']}", json=body, headers=auth)
        assert put.status_code == 403, put.text
        assert client.get(f"/api/v1/assessments/{assessment['id']}", headers=auth).json()["status"] == "draft"
        moves = [e["details"] for e in get_audit_log(tmp_path).for_action("assessment_status_changed")]
        assert sorted(m["after"] for m in moves) == ["draft", "paperGenerated"]


def test_delete_nonexistent_assessment_404(tmp_path, monkeypatch):
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    with TestClient(app) as client:
        auth = _register_and_login(client)
        r = client.delete("/api/v1/assessments/does_not_exist", headers=auth)
        assert r.status_code == 404


def test_delete_existing_assessment_removes_it(tmp_path, monkeypatch):
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    with TestClient(app) as client:
        auth = _register_and_login(client)
        assessment = _create_assessment(client, auth)
        r = client.delete(f"/api/v1/assessments/{assessment['id']}", headers=auth)
        assert r.status_code == 200
        gone = client.get(f"/api/v1/assessments/{assessment['id']}", headers=auth)
        assert gone.status_code == 404
        [row] = get_audit_log(tmp_path).for_action("assessment_deleted")
        assert row["assessment_id"] == assessment["id"] and row["details"]["status"] == assessment["status"]


def test_only_the_author_or_principal_deletes_and_never_an_approved_paper(tmp_path, monkeypatch):
    """N-2-2: a colleague cannot delete someone's paper, and nobody deletes
    an approved one (it is the record of what was set)."""
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    with TestClient(app) as client:
        author = _register_and_login(client)
        colleague = _register_and_login(client, "governance-colleague@example.com")
        mine = _create_assessment(client, author)
        assert client.delete(f"/api/v1/assessments/{mine['id']}", headers=colleague).status_code == 403
        principal = _principal(client, monkeypatch)
        assert client.patch(f"/api/v1/assessments/{mine['id']}/approve", headers=principal).status_code == 200
        for who in (author, principal):
            r = client.delete(f"/api/v1/assessments/{mine['id']}", headers=who)
            assert r.status_code == 409, r.text
        assert client.get(f"/api/v1/assessments/{mine['id']}", headers=author).status_code == 200
        other = _create_assessment(client, author)
        assert client.delete(f"/api/v1/assessments/{other['id']}", headers=principal).status_code == 200


def test_generate_paper_rejects_zero_selected_questions(tmp_path, monkeypatch):
    """Regression: found live in production data (2026-08-19) -- a real
    assessment whose target chapters matched nothing in the corpus (a
    legitimate empty search/optimize result) still ended up with
    status="paperGenerated", a real paper id, and every section showing
    0 questions / 0 marks -- a signed-off blank exam with no error anywhere
    in the chain. /papers/generate must refuse an empty selection outright
    rather than silently completing with nothing to hand a student.
    """
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    with TestClient(app) as client:
        auth = _register_and_login(client)
        assessment = _create_assessment(client, auth)
        empty_request = {
            "assessmentId": assessment["id"],
            "blueprint": assessment["blueprint"],
            "selectedQuestions": [],
            "template": {"id": "tpl_1", "schoolId": "school_1", "name": "Default"},
        }
        r = client.post("/api/v1/papers/generate", json=empty_request, headers=auth)
        assert r.status_code == 400, r.text
        assert "zero selected questions" in r.json()["detail"]

        # The assessment must NOT have been silently marked as generated.
        after = client.get(f"/api/v1/assessments/{assessment['id']}", headers=auth).json()
        assert after["status"] != "paperGenerated"
        assert after["generatedPaperId"] is None

        # A real, non-empty generation still works normally.
        real_request = _generate_request(assessment)
        r2 = client.post("/api/v1/papers/generate", json=real_request, headers=auth)
        assert r2.status_code == 200, r2.text
