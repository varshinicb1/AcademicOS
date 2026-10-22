"""Sign in with an emailed code (ROLE-2): for principals, students and
parents (not teachers), the same answer whether or not an email has an
account, one use, ten minutes, five tries, thirty a day, and nothing without
the school's email set up."""
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
    sign_in_codes._daily_verify_limiter.reset()
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


def test_no_account_and_teachers_look_the_same_and_get_nothing(w, mail):
    a = w.c.post("/api/v1/auth/code/request", json={"email": "nobody@example.com"})
    b = w.c.post("/api/v1/auth/code/request", json={"email": "ana@example.com"})
    c = w.c.post("/api/v1/auth/code/request", json={"email": "p1@example.com"})
    assert a.status_code == b.status_code == c.status_code == 200 and a.json() == b.json() == c.json()
    assert [to for to, _ in mail] == ["p1@example.com"], "teachers use their password; unknown emails get nothing"


def test_a_principal_signs_in_with_a_code(w, mail):
    assert w.c.post("/api/v1/auth/code/request", json={"email": "p1@example.com"}).status_code == 200
    ok = w.c.post("/api/v1/auth/code/verify", json={"email": "p1@example.com", "code": _code(mail)})
    assert ok.status_code == 200, ok.text
    assert ok.json()["user"]["role"] == "principal"
    assert w.c.get("/api/v1/setup-status", headers={"Authorization": f"Bearer {ok.json()['token']}"}).status_code == 200


def test_tries_per_email_are_capped_per_day(w, mail, monkeypatch):
    from academicos.api.rate_limit import RateLimiter
    from academicos.operations import sign_in_codes
    monkeypatch.setenv("ACOS_TEST_RATE_LIMIT", "1")
    monkeypatch.setattr(sign_in_codes, "_daily_verify_limiter", RateLimiter(max_requests=3, window_seconds=86400))
    w.c.post("/api/v1/auth/code/request", json={"email": "p1@example.com"})
    code = _code(mail)
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(3):
        assert w.c.post("/api/v1/auth/code/verify", json={"email": "p1@example.com", "code": wrong}).status_code == 401
    assert w.c.post("/api/v1/auth/code/verify", json={"email": "p1@example.com", "code": code}).status_code == 429


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


def test_the_right_code_sent_twice_at_once_signs_in_once(tmp_path):
    """Security review 2026-10 (ASVS V2.7.3): the check read the row and deleted it later, so two
    submissions of the right code at the same moment (two tabs, or two instances) both passed."""
    import threading

    from academicos.operations.store import OperationsStore
    ops = OperationsStore(tmp_path / "operations.sqlite")
    code = ops.issue_code("kid@example.com")
    start = threading.Barrier(8)
    results = []

    def submit():
        start.wait()
        results.append(ops.check_code("kid@example.com", code))

    threads = [threading.Thread(target=submit) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert results.count(True) == 1, results


def test_wrong_codes_at_once_still_burn_the_code_at_five(tmp_path):
    import threading

    from academicos.operations.store import OperationsStore
    ops = OperationsStore(tmp_path / "operations.sqlite")
    code = ops.issue_code("kid@example.com")
    wrong = "000000" if code != "000000" else "111111"
    start = threading.Barrier(8)

    def guess():
        start.wait()
        ops.check_code("kid@example.com", wrong)

    threads = [threading.Thread(target=guess) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert ops.check_code("kid@example.com", code) is False, "eight wrong tries burnt it"
