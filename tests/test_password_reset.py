"""A way back in for someone who forgot their password (QA S-05).

There was none: no reset, no change, and the emailed code is off where email
is not configured. The principal (or a teacher with the "users" grant) sets
a one-time password and the account is signed out everywhere; anyone signed
in changes their own password with the current one.
"""
from __future__ import annotations

from test_homework import w  # noqa: F401 - `w` is a fixture

LOGIN = "/api/v1/auth/login"


def _id(w, h):
    return w.c.get("/api/v1/auth/me", headers=h).json()["id"]


def _signs_in(w, email, password) -> bool:
    return w.c.post(LOGIN, json={"email": email, "password": password}).status_code == 200


def test_the_principal_resets_a_teachers_password(w):
    ana = _id(w, w.ana)
    r = w.c.post(f"/api/v1/auth/users/{ana}/password-reset", headers=w.p)
    assert r.status_code == 200, r.text
    body = r.json()
    temp = body["temporaryPassword"]
    assert body["userId"] == ana and body["name"] == "Ana" and len(temp) >= 12
    # Signed out everywhere; the old password is gone; the new one works.
    assert w.c.get("/api/v1/auth/me", headers=w.ana).status_code == 401
    assert not _signs_in(w, "ana@example.com", "correct horse battery")
    assert _signs_in(w, "ana@example.com", temp)
    # A second reset gives a different password.
    again = w.c.post(f"/api/v1/auth/users/{ana}/password-reset", headers=w.p).json()
    assert again["temporaryPassword"] != temp


def test_who_may_reset_whom(w):
    ana, principal, s1 = _id(w, w.ana), _id(w, w.p), w.ids["s1"]
    assert w.c.post(f"/api/v1/auth/users/{s1}/password-reset", headers=w.ana).status_code == 403
    assert w.c.post(f"/api/v1/auth/users/{principal}/password-reset", headers=w.p).status_code == 403
    assert w.c.post(f"/api/v1/auth/users/{ana}/password-reset", headers=w.p2).status_code == 404
    assert w.c.post("/api/v1/auth/users/user_nobody/password-reset", headers=w.p).status_code == 404
    assert w.c.post(f"/api/v1/auth/users/{s1}/password-reset", headers=w.p).status_code == 200

    grant = w.c.post("/api/v1/admin/grants", json={"userId": ana, "capability": "users"}, headers=w.p)
    assert grant.status_code == 200, grant.text
    assert w.c.post(f"/api/v1/auth/users/{s1}/password-reset", headers=w.ana).status_code == 200
    # Even with the grant, never the principal's account.
    assert w.c.post(f"/api/v1/auth/users/{principal}/password-reset", headers=w.ana).status_code == 403
    # Nor a colleague's: their temporary password would let Ana sign in as them, with their grants
    # (review 2026-10-04). Only the principal resets a staff member.
    bala = _id(w, w.bala)
    r = w.c.post(f"/api/v1/auth/users/{bala}/password-reset", headers=w.ana)
    assert r.status_code == 403 and "principal" in r.json()["detail"]
    assert w.c.post(f"/api/v1/auth/users/{bala}/password-reset", headers=w.p).status_code == 200


def test_the_reset_is_audited_without_the_password(w):
    from academicos.assessment.audit_log import get_audit_log
    from academicos.curriculum import routes as cr

    ana = _id(w, w.ana)
    temp = w.c.post(f"/api/v1/auth/users/{ana}/password-reset", headers=w.p).json()["temporaryPassword"]
    log = get_audit_log(cr._cfg.data_root)
    entries = log.for_action("password_reset")
    assert len(entries) == 1 and entries[0]["details"]["userId"] == ana
    assert temp not in repr(entries[0])
    # Only the id: a name would outlive the person's erasure in the kept audit log.
    assert "name" not in entries[0]["details"]


def test_a_person_changes_their_own_password(w):
    r = w.c.post("/api/v1/auth/password", headers=w.ana,
                 json={"currentPassword": "wrong", "newPassword": "a better password"})
    assert r.status_code == 400 and "current password" in r.json()["detail"]
    r = w.c.post("/api/v1/auth/password", headers=w.ana,
                 json={"currentPassword": "correct horse battery", "newPassword": "short"})
    assert r.status_code == 400 and "8 characters" in r.json()["detail"]

    r = w.c.post("/api/v1/auth/password", headers=w.ana,
                 json={"currentPassword": "correct horse battery", "newPassword": "a better password"})
    assert r.status_code == 200, r.text
    fresh = {"Authorization": f"Bearer {r.json()['token']}"}
    assert w.c.get("/api/v1/auth/me", headers=fresh).status_code == 200
    assert w.c.get("/api/v1/auth/me", headers=w.ana).status_code == 401    # other sessions end
    assert _signs_in(w, "ana@example.com", "a better password")
    assert not _signs_in(w, "ana@example.com", "correct horse battery")


def test_wrong_current_passwords_are_counted(w, monkeypatch):
    """A stolen session cannot guess the current password without limit (review 2026-10-04)."""
    from academicos.api.rate_limit import account_failures
    monkeypatch.setenv("ACOS_TEST_RATE_LIMIT", "1")
    account_failures.reset()
    codes = [w.c.post("/api/v1/auth/password", headers=w.ana,
                      json={"currentPassword": f"guess {i}", "newPassword": "a better password"}).status_code
             for i in range(15)]
    assert codes[0] == 400 and codes[-1] == 429, codes
    # The right password is refused too while locked, so a guesser cannot tell when they hit it.
    r = w.c.post("/api/v1/auth/password", headers=w.ana,
                 json={"currentPassword": "correct horse battery", "newPassword": "a better password"})
    assert r.status_code == 429
    account_failures.reset()
