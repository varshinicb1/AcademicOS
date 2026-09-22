"""Registration helpers for tests: every account now needs an invite.

Since 2026-09-21 nobody joins a school by typing its id. POST /auth/register
takes an invite code that a principal issued, and the account's school and role
come from the invite (assessment/users.py, UserStore.register). Tests that only
need "a teacher at school_1" mint that invite through the store the running app
is using, not through a weaker registration rule kept around for tests.

Both helpers need a booted app (`with TestClient(app)`), because they reach the
store through `auth_routes._require()`, the same instance the route uses.
"""
from __future__ import annotations

from typing import Optional

PASSWORD = "correct horse battery"


def invite_code(school_id: str, role: str = "teacher", *,
                email: Optional[str] = None) -> str:
    """A fresh single-use invite for `school_id`/`role`, created as if by a
    principal (`created_by="test-fixture"`)."""
    from academicos.assessment import auth_routes

    return auth_routes._require().create_invite(
        school_id=school_id, role=role, created_by="test-fixture", email=email,
    ).code


def register_invited(client, school_id: str, email: str, *, name: str = "Teacher",
                     role: str = "teacher", password: str = PASSWORD) -> dict:
    """Register through the real route with a fixture invite. Returns the
    AuthResponse body (`{"user": ..., "token": ...}`)."""
    r = client.post("/api/v1/auth/register", json={
        "inviteCode": invite_code(school_id, role),
        "name": name, "email": email, "password": password,
    })
    assert r.status_code == 200, r.text
    return r.json()
