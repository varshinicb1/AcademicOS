"""Auth boundary for the assessment-designer routes (routes.py, plus the
paper/answer-key/mail handlers that wrap the same stores).

Every route here depends on Depends(get_current_user), so it must 401 with no
token; because the objects they touch are school-scoped, a token from a
different school must be rejected (403 when the object exists, 404 when it
doesn't -- never a 2xx), and the owning school's token must pass auth.

The full-boot group in test_route_inventory.py already proves the happy paths
and the proper-4xx routes in detail; this file pins the authorization
boundary itself (no token / wrong school / right role).
"""
from __future__ import annotations

import pytest

from academicos.api.main import app

from test_route_inventory import blueprint_body, question_body


def _boot_client(tmp_path, monkeypatch):
    """Fresh boot with an empty corpus; resets the store singletons so an
    earlier boot's data root can't leak into this test."""
    from academicos.assessment import audit_log, users as users_mod
    from academicos.curriculum import store as curriculum_store_mod

    monkeypatch.setenv("ACOS_PRINCIPAL_BOOTSTRAP_KEY", "test-bootstrap-key")
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr(audit_log, "_INSTANCE", None)
    monkeypatch.setattr(users_mod, "_INSTANCE", None)
    monkeypatch.setattr(curriculum_store_mod, "_INSTANCE", None)
    from fastapi.testclient import TestClient

    return TestClient(app)


def _register(client, school_id, email, name="Teacher", principal_key=None):
    body = {
        "schoolId": school_id, "name": name, "email": email,
        "password": "correct horse battery",
    }
    if principal_key:
        body["principalKey"] = principal_key
    r = client.post("/api/v1/auth/register", json=body)
    assert r.status_code == 200, r.text
    return r.json()


def _assessment_body(aid: str) -> dict:
    return {
        "id": aid, "teacherId": "t", "schoolId": "school_1",
        "title": "Auth Test Assessment", "subject": "Mathematics", "grade": 10,
        "chapterIds": [], "blueprint": blueprint_body(), "status": "draft",
        "createdAt": "2026-01-01T00:00:00Z", "updatedAt": "2026-01-01T00:00:00Z",
    }


def _paper_gen_body(aid: str) -> dict:
    return {
        "assessmentId": aid, "blueprint": blueprint_body(),
        "selectedQuestions": [question_body()],
        "template": {"id": "t1", "schoolId": "school_1", "name": "Default"},
    }


def _answer_key_body(aid: str) -> dict:
    return {
        "assessmentId": aid, "questions": [question_body()],
        "correctOptions": {},
    }


def test_assessment_designer_auth_boundary(tmp_path, monkeypatch):
    with _boot_client(tmp_path, monkeypatch) as client:
        teacher = _register(client, "school_1", "auth-t1@example.com", "Ana Teacher")
        other = _register(client, "school_2", "auth-t2@example.com", "Bob Teacher")
        principal = _register(client, "school_1", "auth-p1@example.com",
                              "Priya Principal", principal_key="test-bootstrap-key")
        assert principal["user"]["role"] == "principal"

        created = client.post("/api/v1/assessments", json={
            "teacherId": teacher["user"]["id"], "schoolId": "school_1",
            "title": "Auth Boundary", "subject": "Mathematics", "grade": 10,
            "chapterIds": [], "blueprint": blueprint_body(),
        }, headers={"Authorization": f"Bearer {teacher['token']}"})
        assert created.status_code == 200, created.text
        a1 = created.json()["id"]

        auth_ok = {"Authorization": f"Bearer {teacher['token']}"}
        auth_other = {"Authorization": f"Bearer {other['token']}"}

        routes = [
            # (method, path, body, wrong-school expected; 404 when the route
            # leads with an object lookup on a missing id, 403 otherwise)
            ("GET", "/api/v1/schools/school_1/templates", None, 403),
            ("GET", "/api/v1/schools/school_1/paper-templates", None, 403),
            ("POST", "/api/v1/papers/generate", _paper_gen_body(a1), 403),
            ("GET", "/api/v1/papers/paper_missing", None, 404),
            ("POST", "/api/v1/papers/paper_missing/export/pdf", None, 404),
            ("GET", "/api/v1/papers/paper_missing/file", None, 404),
            ("GET", f"/api/v1/assessments/{a1}", None, 403),
            ("PUT", f"/api/v1/assessments/{a1}", _assessment_body(a1), 403),
            ("PATCH", f"/api/v1/assessments/{a1}/status", {"status": "draft"}, 403),
            ("POST", f"/api/v1/assessments/{a1}/answer-key", _answer_key_body(a1), 403),
            ("POST", "/api/v1/mail/send-paper",
             {"paperId": "paper_missing", "recipients": ["a@b.c"]}, 404),
            ("DELETE", f"/api/v1/assessments/{a1}", None, 403),
        ]
        for method, path, body, wrong_expected in routes:
            r = client.request(method, path, json=body)
            assert r.status_code == 401, f"{method} {path} no-token -> {r.status_code}"
            r = client.request(method, path, json=body, headers=auth_other)
            assert r.status_code == wrong_expected, (
                f"{method} {path} other-school -> {r.status_code}"
            )
            r = client.request(method, path, json=body, headers=auth_ok)
            assert r.status_code not in (401, 403), (
                f"{method} {path} owning-school -> {r.status_code}"
            )


def test_assessment_approve_is_principal_only(tmp_path, monkeypatch):
    """Approval is role-gated, not just school-gated: teachers 403 even on
    their own school's assessment; the principal passes."""
    with _boot_client(tmp_path, monkeypatch) as client:
        teacher = _register(client, "school_1", "approve-t1@example.com")
        other = _register(client, "school_2", "approve-t2@example.com")
        principal = _register(client, "school_1", "approve-p1@example.com",
                              principal_key="test-bootstrap-key")

        created = client.post("/api/v1/assessments", json={
            "teacherId": teacher["user"]["id"], "schoolId": "school_1",
            "title": "Approve Gate", "subject": "Mathematics", "grade": 10,
            "chapterIds": [], "blueprint": blueprint_body(),
        }, headers={"Authorization": f"Bearer {teacher['token']}"})
        assert created.status_code == 200, created.text
        a1 = created.json()["id"]

        auth_teacher = {"Authorization": f"Bearer {teacher['token']}"}
        auth_other = {"Authorization": f"Bearer {other['token']}"}
        auth_principal = {"Authorization": f"Bearer {principal['token']}"}

        for headers in (None, auth_other, auth_teacher):
            kw = {} if headers is None else {"headers": headers}
            r = client.patch(f"/api/v1/assessments/{a1}/approve", **kw)
            assert r.status_code == 401 if headers is None else r.status_code == 403, (
                f"approve headers={headers is not None} role -> {r.status_code}"
            )
        r = client.patch(f"/api/v1/assessments/{a1}/approve", headers=auth_principal)
        assert r.status_code not in (401, 403), f"approve principal -> {r.status_code}"


def test_assessment_create_claims_callers_school(tmp_path, monkeypatch):
    """POST /assessments ignores any schoolId in the body and scopes the new
    assessment to the authenticated caller -- a token is mandatory (401
    without), and either school's teacher can create, in their own school."""
    with _boot_client(tmp_path, monkeypatch) as client:
        teacher = _register(client, "school_1", "create-t1@example.com")
        other = _register(client, "school_2", "create-t2@example.com")

        assert client.post("/api/v1/assessments", json={
            "teacherId": "x", "schoolId": "school_1", "title": "T",
            "subject": "Science", "grade": 10, "chapterIds": [], "blueprint": blueprint_body(),
        }).status_code == 401

        body = {
            "teacherId": "x", "schoolId": "school_1", "title": "T",
            "subject": "Science", "grade": 10, "chapterIds": [], "blueprint": blueprint_body(),
        }
        mine = client.post("/api/v1/assessments", json=body,
                           headers={"Authorization": f"Bearer {teacher['token']}"})
        assert mine.status_code == 200, mine.text
        assert mine.json()["schoolId"] == "school_1"
        assert mine.json()["teacherId"] == teacher["user"]["id"]

        theirs = client.post("/api/v1/assessments", json=body,
                             headers={"Authorization": f"Bearer {other['token']}"})
        assert theirs.status_code == 200, theirs.text
        assert theirs.json()["schoolId"] == "school_2"


def test_assessments_list_requires_auth(tmp_path, monkeypatch):
    with _boot_client(tmp_path, monkeypatch) as client:
        teacher = _register(client, "school_1", "list-t1@example.com")
        assert client.get("/api/v1/assessments").status_code == 401
        r = client.get("/api/v1/assessments",
                       headers={"Authorization": f"Bearer {teacher['token']}"})
        assert r.status_code == 200
        assert r.json() == []