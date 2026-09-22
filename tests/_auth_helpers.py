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


def grant_consent(school_id: str, *student_ids: str) -> None:
    """Record parental consent for each student at `school_id`, as a staff
    member would from a signed admission form (`recorded_by="test-fixture"`).

    Since 2026-09-22 every route that processes a named student's work refuses
    with 409 until that student has active consent (authz.require_consent,
    DPDP Act 2023 s.9). Tests that grade, scan or practise record it here,
    through the store the running app reads -- never by switching the rule
    off. Needs a booted app, like the helpers above."""
    from academicos.assessment import consent_routes

    store = consent_routes._require_store()
    for sid in student_ids:
        store.record_consent(school_id=school_id, student_id=sid,
                             guardian_name=f"Guardian of {sid}",
                             method="Signed admission form", recorded_by="test-fixture")
