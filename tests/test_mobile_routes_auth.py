"""Auth boundary for the mobile scan-and-grade routes (mobile_routes.py).

Session-scoped routes fetch the session first (404 for a missing id) and then
verify the session's assessment belongs to the caller's school (403 for a
wrong school); session creation verifies the assessment owner directly. No
token on any of them fails fast with 401.
"""
from __future__ import annotations

import pytest

from academicos.api.main import app

from test_route_inventory import blueprint_body
from _auth_helpers import invite_code


def _boot_client(tmp_path, monkeypatch):
    from academicos.assessment import audit_log, users as users_mod
    from academicos.curriculum import store as curriculum_store_mod

    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr(audit_log, "_INSTANCE", None)
    monkeypatch.setattr(users_mod, "_INSTANCE", None)
    monkeypatch.setattr(curriculum_store_mod, "_INSTANCE", None)
    from fastapi.testclient import TestClient

    return TestClient(app)


def _register(client, school_id, email, name="Teacher"):
    r = client.post("/api/v1/auth/register", json={
        "inviteCode": invite_code(school_id), "name": name, "email": email,
        "password": "correct horse battery",
    })
    assert r.status_code == 200, r.text
    return r.json()


def _create_assessment(client, headers):
    r = client.post("/api/v1/assessments", json={
        "teacherId": "t", "schoolId": "school_1",
        "title": "Scan Auth Test", "subject": "Mathematics", "grade": 10,
        "chapterIds": [], "blueprint": blueprint_body(),
    }, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()["id"]


def test_scan_routes_auth_boundary(tmp_path, monkeypatch):
    with _boot_client(tmp_path, monkeypatch) as client:
        teacher = _register(client, "school_1", "scan-auth-t1@example.com", "Ana Teacher")
        other = _register(client, "school_2", "scan-auth-t2@example.com", "Bob Teacher")

        auth_ok = {"Authorization": f"Bearer {teacher['token']}"}
        auth_other = {"Authorization": f"Bearer {other['token']}"}

        a1 = _create_assessment(client, auth_ok)
        created = client.post("/api/v1/scan/sessions", json={
            "assessmentId": a1, "studentId": "s1", "studentName": "Student",
        }, headers=auth_ok)
        assert created.status_code == 200, created.text
        session_id = created.json()["id"]

        # list of (method, path, blank-body-for-json-POST, wrong-school, owning-school)
        checks = [
            # create: verifies assessment ownership directly -> 403 other school
            ("POST", "/api/v1/scan/sessions", {
                "assessmentId": a1, "studentId": "s2", "studentName": "Other",
            }, 403, 200),
            # session-scoped routes: known cross-school session -> 403
            ("POST", f"/api/v1/scan/sessions/{session_id}/process", None, 403, None),
            ("GET", f"/api/v1/scan/sessions/{session_id}/review", None, 403, 200),
            ("POST", f"/api/v1/scan/sessions/{session_id}/review/q_1",
             {"action": "approve"}, 403, 400),
            ("POST", f"/api/v1/scan/sessions/{session_id}/finalize", None, 403, None),
            ("GET", f"/api/v1/scan/sessions/{session_id}/pages/1/image", None, 403, 404),
            ("GET", f"/api/v1/scan/sessions/{session_id}/raw-pdf", None, 403, 404),
            ("GET", f"/api/v1/scan/sessions/{session_id}/corrected-pdf", None, 403, 404),
        ]
        for method, path, body, wrong_expected, own_expected in checks:
            r = client.request(method, path, json=body)
            assert r.status_code == 401, f"{method} {path} no-token -> {r.status_code}"
            r = client.request(method, path, json=body, headers=auth_other)
            assert r.status_code == wrong_expected, (
                f"{method} {path} other-school -> {r.status_code}"
            )
            r = client.request(method, path, json=body, headers=auth_ok)
            if own_expected is None:
                # (process -> 409 no paper, finalize -> 409 nothing to finalize)
                assert r.status_code not in (401, 403), (
                    f"{method} {path} owning-school -> {r.status_code}"
                )
            else:
                assert r.status_code == own_expected, (
                    f"{method} {path} owning-school -> {r.status_code}"
                )

        # -- missing session -> still 404 before any ownership answer, and
        # never a 2xx that would leak the id.
        for method, path in (
            ("GET", "/api/v1/scan/sessions/scan_missing/review"),
            ("POST", "/api/v1/scan/sessions/scan_missing/process"),
        ):
            r = client.request(method, path, headers=auth_other)
            assert r.status_code == 404, f"{method} {path} other-school-missing -> {r.status_code}"

        # -- the page-upload route is multipart, probed separately.
        files = {"file": ("page.jpg", b"x", "image/jpeg")}
        assert client.post(
            f"/api/v1/scan/sessions/{session_id}/pages", files=files,
        ).status_code == 401
        r = client.post(
            f"/api/v1/scan/sessions/{session_id}/pages", files=files, headers=auth_other,
        )
        assert r.status_code == 403, f"pages other-school -> {r.status_code}"
        r = client.post(
            f"/api/v1/scan/sessions/{session_id}/pages", files=files, headers=auth_ok,
        )
        assert r.status_code not in (401, 403), f"pages owning-school -> {r.status_code}"