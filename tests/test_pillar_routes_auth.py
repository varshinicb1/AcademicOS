"""Auth boundary for the pillar routes (school templates, evaluations,
knowledge, practice, insights). Same contract as the other *_routes_auth
files: 401 with no token, never a 2xx for a cross-school caller, and the
owning school's caller passes auth. /insights/school is additionally
role-gated to principals.
"""
from __future__ import annotations

import pytest

from academicos.api.main import app

from test_route_inventory import blueprint_body, question_body
from _auth_helpers import grant_consent, invite_code


def _boot_client(tmp_path, monkeypatch):
    from academicos.assessment import audit_log, users as users_mod
    from academicos.curriculum import store as curriculum_store_mod

    monkeypatch.setenv("ACOS_PRINCIPAL_BOOTSTRAP_KEY", "test-bootstrap-key")
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr(audit_log, "_INSTANCE", None)
    monkeypatch.setattr(users_mod, "_INSTANCE", None)
    monkeypatch.setattr(curriculum_store_mod, "_INSTANCE", None)
    from fastapi.testclient import TestClient

    return TestClient(app)


def _register(client, school_id, email, name="Teacher", role="teacher",
              principal_key=None):
    body = {"name": name, "email": email, "password": "correct horse battery"}
    if principal_key:
        body.update(schoolId=school_id, principalKey=principal_key)
    else:
        body["inviteCode"] = invite_code(school_id, role)
    r = client.post("/api/v1/auth/register", json=body)
    assert r.status_code == 200, r.text
    return r.json()


def _template_body() -> dict:
    return {"id": "t1", "schoolId": "school_1", "name": "Default"}


def _eval_answer_body(aid: str) -> dict:
    return {
        "assessmentId": aid, "studentId": "s_unreg", "question": question_body(),
        "studentAnswer": "x = 2",
    }


def test_pillar_routes_auth_boundary(tmp_path, monkeypatch):
    with _boot_client(tmp_path, monkeypatch) as client:
        teacher = _register(client, "school_1", "pillar-t1@example.com", "Ana Teacher")
        other = _register(client, "school_2", "pillar-t2@example.com", "Bob Teacher")
        principal = _register(client, "school_1", "pillar-p1@example.com",
                              "Priya Principal", principal_key="test-bootstrap-key")
        assert principal["user"]["role"] == "principal"
        sid = _register(client, "school_1", "pillar-s1@example.com",
                        "Sheeta Student", role="student")["user"]["id"]

        created = client.post("/api/v1/assessments", json={
            "teacherId": teacher["user"]["id"], "schoolId": "school_1",
            "title": "Pillar Boundary", "subject": "Mathematics", "grade": 10,
            "chapterIds": [], "blueprint": blueprint_body(),
        }, headers={"Authorization": f"Bearer {teacher['token']}"})
        assert created.status_code == 200, created.text
        a1 = created.json()["id"]
        # Grading and practice need recorded parental consent
        # (authz.require_consent); with it, the owning school reaches each
        # handler's real path instead of a consent 409.
        grant_consent("school_1", "s_unreg", sid)

        auth_ok = {"Authorization": f"Bearer {teacher['token']}"}
        auth_other = {"Authorization": f"Bearer {other['token']}"}
        auth_principal = {"Authorization": f"Bearer {principal['token']}"}

        routes = [
            ("GET", "/api/v1/schools/school_1/school-templates", None, 403),
            ("POST", "/api/v1/schools/school_1/school-templates",
             {"template": _template_body(), "sections": []}, 403),
            ("GET", "/api/v1/schools/school_1/school-templates/tpl_missing/sections",
             None, 403),
            ("DELETE", "/api/v1/schools/school_1/school-templates/tpl_missing", None, 403),
            ("POST", "/api/v1/evaluations/answer", _eval_answer_body(a1), 403),
            ("POST", "/api/v1/evaluations/sheet", {
                "assessmentId": a1, "studentId": "s_unreg", "studentName": "S",
                "questions": [question_body()], "answers": {"q_1": "x"},
                "correctOptions": {},
            }, 403),
            ("POST", f"/api/v1/evaluations/sheet/{a1}/s_unreg/review/q_1",
             {"action": "approve"}, 403),
            ("POST", f"/api/v1/evaluations/sheet/{a1}/s_unreg/finalize", {}, 403),
            ("GET", f"/api/v1/knowledge/{sid}", None, 403),
            ("GET", f"/api/v1/knowledge/{sid}/report", None, 403),
            ("POST", "/api/v1/practice/generate",
             {"studentId": sid, "subject": "Science", "grade": "X"}, 403),
            ("POST", "/api/v1/practice/submit", {"setId": "nope", "answers": {}}, 404),
            ("GET", f"/api/v1/insights/class/{a1}", None, 403),
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

        # -- /insights/school is principal-gated on top of the school check.
        assert client.get("/api/v1/insights/school/school_1").status_code == 401
        for headers, label in ((auth_other, "other-school"), (auth_ok, "teacher")):
            r = client.get("/api/v1/insights/school/school_1", headers=headers)
            assert r.status_code == 403, f"insights/school {label} -> {r.status_code}"
        r = client.get("/api/v1/insights/school/school_1", headers=auth_principal)
        assert r.status_code not in (401, 403), (
            f"insights/school principal -> {r.status_code}"
        )