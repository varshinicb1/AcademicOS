"""Sign in with an emailed code (ROLE-2): for students and parents only, the
same answer whether or not an email has an account, one use, ten minutes,
five tries, and nothing without the school's email set up."""
from __future__ import annotations

import pytest

from test_homework import w  # noqa: F401 - `w` is a fixture


@pytest.fixture
def mail(monkeypatch):
    """Email set up, and every sent message kept."""
    from academicos.assessment import mailer
    from academicos.operations import notifications, sign_in_codes
    sign_in_codes._request_limiter.reset()
    sign_in_codes._verify_limiter.reset()
    sent: list[tuple[str, str]] = []
    monkeypatch.setattr(mailer, "available_backends", lambda: {"smtp": {"configured": True, "reason": ""}})
    monkeypatch.setattr(notifications, "send_email", lambda to, title, body: (sent.append((to, body)) or ("sent", None)))
    return sent


def _code(sent):
    import re
    return re.search(r"\b(\d{6})\b", sent[-1][1]).group(1)


def test_a_student_signs_in_with_a_code(w, mail):
    r = w.c.post("/api/v1/auth/code/request", json={"email": "s1@example.com"})
    assert r.status_code == 200 and len(mail) == 1
    code = _code(mail)
    ok = w.c.post("/api/v1/auth/code/verify", json={"email": "S1@example.com", "code": code})
    assert ok.status_code == 200, ok.text
    body = ok.json()
    assert body["user"]["role"] == "student" and body["token"]
    assert w.c.get("/api/v1/my-homework", headers={"Authorization": f"Bearer {body['token']}"}).status_code == 200
    again = w.c.post("/api/v1/auth/code/verify", json={"email": "s1@example.com", "code": code})
    assert again.status_code == 401, "a code works once"


def test_no_account_and_staff_look_the_same_and_get_nothing(w, mail):
    a = w.c.post("/api/v1/auth/code/request", json={"email": "nobody@example.com"})
    b = w.c.post("/api/v1/auth/code/request", json={"email": "ana@example.com"})
    assert a.status_code == b.status_code == 200 and a.json() == b.json()
    assert mail == [], "staff sign in with their password; unknown emails get nothing"


def test_five_wrong_tries_burn_the_code(w, mail):
    w.c.post("/api/v1/auth/code/request", json={"email": "s2@example.com"})
    code = _code(mail)
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(5):
        assert w.c.post("/api/v1/auth/code/verify", json={"email": "s2@example.com", "code": wrong}).status_code == 401
    assert w.c.post("/api/v1/auth/code/verify", json={"email": "s2@example.com", "code": code}).status_code == 401


def test_without_email_set_up_the_route_says_so(w, monkeypatch):
    from academicos.assessment import mailer
    from academicos.operations import sign_in_codes
    sign_in_codes._request_limiter.reset()
    monkeypatch.setattr(mailer, "available_backends", lambda: {"smtp": {"configured": False, "reason": "no host"}})
    r = w.c.post("/api/v1/auth/code/request", json={"email": "s1@example.com"})
    assert r.status_code == 503 and "password" in r.json()["detail"]
