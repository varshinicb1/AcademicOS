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

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.api.main import app
from academicos.assessment import audit_log, mobile_scan
from academicos.assessment.audit_log import get_audit_log


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


def _create_assessment(client) -> dict:
    body = {
        "teacherId": "teacher_1",
        "schoolId": "school_1",
        "title": "Governance Test",
        "subject": "Mathematics",
        "grade": 10,
        "chapterIds": ["ch1"],
        "blueprint": _blueprint_body(),
    }
    r = client.post("/api/v1/assessments", json=body)
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


def _session_with_review(client, *, item_status: str) -> str:
    """Creates a scan session and seeds one review item at the given status."""
    created = client.post("/api/v1/scan/sessions", json={
        "assessmentId": "a_governance", "studentId": "s1", "studentName": "Student",
    })
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
        sid = _session_with_review(client, item_status="approved")

        r = client.post(f"/api/v1/scan/sessions/{sid}/review/q1", json={
            "action": "regrade", "marks": 2, "comment": "rescored",
            "reason": "answer key says full credit", "reviewerId": "teacher_9",
        })
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["status"] == "edited"
        assert data["teacherMarks"] == 2
        assert data["finalMarks"] == 2

        entries = get_audit_log(tmp_path).for_assessment("a_governance")
        regrades = [e for e in entries if e["action"] == "grade_regraded"]
        assert len(regrades) == 1
        details = regrades[0]["details"]
        assert details["questionId"] == "q1"
        assert details["oldMarks"] == 0
        assert details["newMarks"] == 2
        assert details["reason"] == "answer key says full credit"
        assert details["reviewerId"] == "teacher_9"
        assert regrades[0]["actor"] == "teacher_9"


def test_regrade_without_reason_rejected_400(tmp_path, monkeypatch):
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    with TestClient(app) as client:
        sid = _session_with_review(client, item_status="edited")
        r = client.post(f"/api/v1/scan/sessions/{sid}/review/q1", json={
            "action": "regrade", "marks": 2, "reviewerId": "teacher_9",
        })
        assert r.status_code == 400
        assert "reason" in r.json()["detail"]


def test_first_time_edit_needs_no_reason_http(tmp_path, monkeypatch):
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    with TestClient(app) as client:
        sid = _session_with_review(client, item_status="pending")
        r = client.post(f"/api/v1/scan/sessions/{sid}/review/q1", json={
            "action": "edit", "marks": 2, "comment": "full credit",
        })
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "edited"
        assert r.json()["teacherMarks"] == 2


# =====================================================================
# Part 2 — paper edit-lock after principal approval
# =====================================================================


def test_generation_succeeds_before_approval_and_is_locked_after(tmp_path, monkeypatch):
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    with TestClient(app) as client:
        assessment = _create_assessment(client)
        request_body = _generate_request(assessment)

        # Before any approval: generation (re-running question selection) works.
        before = client.post("/api/v1/papers/generate", json=request_body)
        assert before.status_code == 200, before.text
        got = client.get(f"/api/v1/assessments/{assessment['id']}")
        assert got.json()["status"] == "paperGenerated"

        # A real principal approval exists on the status field.
        approved = client.patch(
            f"/api/v1/assessments/{assessment['id']}/status",
            json={"status": "principalApproved"},
        )
        assert approved.status_code == 200, approved.text
        assert approved.json()["status"] == "principalApproved"

        # After approval: regeneration is refused with a clear lock error.
        after = client.post("/api/v1/papers/generate", json=request_body)
        assert after.status_code == 409
        assert "locked" in after.json()["detail"]

        # Question swap via PUT is refused too.
        put_body = got.json()
        put_body["status"] = "principalApproved"
        put = client.put(f"/api/v1/assessments/{assessment['id']}", json=put_body)
        assert put.status_code == 409
        assert "locked" in put.json()["detail"]

        # The lock cannot be removed by PATCHing the status back.
        unlock = client.patch(
            f"/api/v1/assessments/{assessment['id']}/status",
            json={"status": "paperGenerated"},
        )
        assert unlock.status_code == 409

        # Forward lifecycle moves after approval stay allowed.
        forward = client.patch(
            f"/api/v1/assessments/{assessment['id']}/status",
            json={"status": "printed"},
        )
        assert forward.status_code == 200
        assert forward.json()["status"] == "printed"


# =====================================================================
# Part 3 — status validation and delete semantics (audit D5#2 / D5#3)
# =====================================================================


def test_patch_status_rejects_unknown_status_422(tmp_path, monkeypatch):
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    with TestClient(app) as client:
        assessment = _create_assessment(client)
        original = assessment["status"]
        r = client.patch(
            f"/api/v1/assessments/{assessment['id']}/status",
            json={"status": "bogusLifecycle"},
        )
        assert r.status_code == 422
        assert "status" in r.json()["detail"].lower() or "invalid" in r.json()["detail"].lower()
        stored = client.get(f"/api/v1/assessments/{assessment['id']}")
        assert stored.json()["status"] == original


def test_patch_status_allows_every_valid_status(tmp_path, monkeypatch):
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    valid = ["draft", "paperGenerated", "printed", "principalApproved", "archived"]
    with TestClient(app) as client:
        assessment = _create_assessment(client)
        for status in valid:
            r = client.patch(
                f"/api/v1/assessments/{assessment['id']}/status",
                json={"status": status},
            )
            assert r.status_code == 200, (status, r.text)


def test_delete_nonexistent_assessment_404(tmp_path, monkeypatch):
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    with TestClient(app) as client:
        r = client.delete("/api/v1/assessments/does_not_exist")
        assert r.status_code == 404


def test_delete_existing_assessment_removes_it(tmp_path, monkeypatch):
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    with TestClient(app) as client:
        assessment = _create_assessment(client)
        r = client.delete(f"/api/v1/assessments/{assessment['id']}")
        assert r.status_code == 200
        gone = client.get(f"/api/v1/assessments/{assessment['id']}")
        assert gone.status_code == 404


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
        assessment = _create_assessment(client)
        empty_request = {
            "assessmentId": assessment["id"],
            "blueprint": assessment["blueprint"],
            "selectedQuestions": [],
            "template": {"id": "tpl_1", "schoolId": "school_1", "name": "Default"},
        }
        r = client.post("/api/v1/papers/generate", json=empty_request)
        assert r.status_code == 400, r.text
        assert "zero selected questions" in r.json()["detail"]

        # The assessment must NOT have been silently marked as generated.
        after = client.get(f"/api/v1/assessments/{assessment['id']}").json()
        assert after["status"] != "paperGenerated"
        assert after["generatedPaperId"] is None

        # A real, non-empty generation still works normally.
        real_request = _generate_request(assessment)
        r2 = client.post("/api/v1/papers/generate", json=real_request)
        assert r2.status_code == 200, r2.text
