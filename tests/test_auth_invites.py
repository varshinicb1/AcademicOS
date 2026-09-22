"""Registration is by invite: nobody joins a school by typing its id.

The 2026-09-21 audit (scorecard item 8.4, reproduced by two auditors with
TestClient probes) found school membership was self-asserted. RegisterRequest
took `schoolId` from the client and the store saved it unchecked, so
`attacker@evil.example` registered into school_A as a teacher and then got 200
on /assessments/{id}, /knowledge/{studentId}, /insights/class/{aid}, every
student's answers under /evaluations/.../question/q_1, and /consent/students/{sid}.
Every `school_id` check in the product rested on that claim. Separately, the one
global ACOS_PRINCIPAL_BOOTSTRAP_KEY made its holder principal of any school,
including a school that already had one.

What these tests pin:
  * the school and role of a new account come from a principal-issued,
    single-use invite, never from the request;
  * an invite is consumed atomically with the account (a race on one code has
    exactly one winner);
  * the bootstrap key only creates a school's FIRST principal;
  * the demo accounts (`principal@school.com` / `password123`) are seeded only
    when ACOS_SEED_DEMO_USERS is set. Until now they were re-created on every
    Render cold start.
"""
from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone

import pytest

from academicos.assessment import auth_routes
from academicos.assessment.users import RegistrationRefused, UserStore

from test_route_inventory import _boot_client, blueprint_body

KEY = "test-bootstrap-key"
PASSWORD = "correct horse battery"
REGISTER = "/api/v1/auth/register"
INVITES = "/api/v1/auth/invites"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("ACOS_PRINCIPAL_BOOTSTRAP_KEY", KEY)
    with _boot_client(tmp_path, monkeypatch) as c:
        yield c


def _auth(body: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {body['token']}"}


def _bootstrap_principal(client, school_id: str, email: str) -> dict:
    r = client.post(REGISTER, json={
        "schoolId": school_id, "principalKey": KEY, "name": "Principal",
        "email": email, "password": PASSWORD,
    })
    assert r.status_code == 200, r.text
    assert r.json()["user"]["role"] == "principal"
    return r.json()


def _create_invite(client, principal: dict, **body) -> dict:
    r = client.post(INVITES, json={"role": "teacher", **body}, headers=_auth(principal))
    assert r.status_code == 200, r.text
    return r.json()


def _register(client, code: str, email: str, **extra):
    return client.post(REGISTER, json={
        "inviteCode": code, "name": "New Member", "email": email,
        "password": PASSWORD, **extra,
    })


def _roster_emails(client, principal: dict) -> set[str]:
    r = client.get("/api/v1/auth/users", headers=_auth(principal))
    assert r.status_code == 200, r.text
    return {u["email"] for u in r.json()}


def _invite_row(client, principal: dict, code: str) -> dict:
    rows = client.get(INVITES, headers=_auth(principal))
    assert rows.status_code == 200, rows.text
    matches = [i for i in rows.json() if i["code"] == code]
    assert len(matches) == 1, rows.json()
    return matches[0]


def _cannot_log_in(client, email: str) -> bool:
    return client.post("/api/v1/auth/login", json={
        "email": email, "password": PASSWORD,
    }).status_code == 401


# --------------------------------------------------------------------- #
# no invite, no key -> no account
# --------------------------------------------------------------------- #

def test_register_with_no_invite_and_no_key_is_403(client):
    r = client.post(REGISTER, json={
        "name": "Nobody", "email": "nobody@example.com", "password": PASSWORD,
    })
    assert r.status_code == 403, r.text
    assert "invite" in r.json()["detail"].lower()
    assert _cannot_log_in(client, "nobody@example.com")


def test_the_audit_attack_replayed_gets_no_account_and_no_data(client):
    """The exact request from the audit: a stranger names school_A and a role,
    with no invite. It used to return a teacher token for school_A."""
    principal = _bootstrap_principal(client, "school_A", "principal-a@example.com")
    created = client.post("/api/v1/assessments", json={
        "teacherId": principal["user"]["id"], "schoolId": "school_A", "title": "Unit Test 1",
        "subject": "Science", "grade": 10, "chapterIds": [], "blueprint": blueprint_body(),
    }, headers=_auth(principal))
    assert created.status_code == 200, created.text
    assessment_id = created.json()["id"]

    attack = client.post(REGISTER, json={
        "schoolId": "school_A", "role": "teacher", "name": "Mallory",
        "email": "attacker@evil.example", "password": PASSWORD,
    })
    assert attack.status_code == 403, attack.text
    assert "token" not in attack.json()

    # Guessing the bootstrap key is the other door; it is shut the same way.
    guessed = client.post(REGISTER, json={
        "schoolId": "school_A", "principalKey": "guessed-key", "name": "Mallory",
        "email": "attacker@evil.example", "password": PASSWORD,
    })
    assert guessed.status_code == 403, guessed.text

    assert _cannot_log_in(client, "attacker@evil.example")
    assert "attacker@evil.example" not in _roster_emails(client, principal)
    assert client.get(f"/api/v1/assessments/{assessment_id}").status_code == 401
    assert client.get(f"/api/v1/assessments/{assessment_id}",
                      headers={"Authorization": "Bearer forged"}).status_code == 401


# --------------------------------------------------------------------- #
# the invite decides the school and the role
# --------------------------------------------------------------------- #

def test_invite_code_alone_registers_into_the_invites_school_and_role(client):
    principal = _bootstrap_principal(client, "school_A", "principal-a@example.com")
    invite = _create_invite(client, principal, role="student")
    assert invite["role"] == "student"
    assert invite.get("email") is None
    assert invite["status"] == "open"
    lifetime = (datetime.fromisoformat(invite["expiresAt"])
                - datetime.now(timezone.utc))
    assert timedelta(days=13, hours=23) < lifetime <= timedelta(days=14)

    r = _register(client, invite["code"], "student@example.com")
    assert r.status_code == 200, r.text
    user = r.json()["user"]
    assert user["schoolId"] == "school_A"
    assert user["role"] == "student"

    me = client.get("/api/v1/auth/me", headers=_auth(r.json()))
    assert (me.json()["schoolId"], me.json()["role"]) == ("school_A", "student")

    used = _invite_row(client, principal, invite["code"])
    assert used["status"] == "used"
    assert used["usedBy"] == user["id"]
    assert used["usedAt"]
    assert used["createdBy"] == principal["user"]["id"]


def test_school_and_role_that_agree_with_the_invite_are_accepted(client):
    """An older client still sends schoolId/role. When they match the invite
    there is nothing to reject."""
    principal = _bootstrap_principal(client, "school_A", "principal-a@example.com")
    invite = _create_invite(client, principal, role="teacher")
    r = _register(client, invite["code"], "teacher@example.com",
                  schoolId="school_A", role="teacher")
    assert r.status_code == 200, r.text
    assert (r.json()["user"]["schoolId"], r.json()["user"]["role"]) == ("school_A", "teacher")


@pytest.mark.parametrize("extra", [
    {"schoolId": "school_B"},
    {"role": "student"},
    {"role": "principal"},
])
def test_school_or_role_that_disagree_with_the_invite_is_400_and_burns_nothing(client, extra):
    """So an old client cannot believe it joined one school while landing in
    another. Nothing is created and the invite stays usable."""
    principal = _bootstrap_principal(client, "school_A", "principal-a@example.com")
    invite = _create_invite(client, principal, role="teacher")

    r = _register(client, invite["code"], "confused@example.com", **extra)
    assert r.status_code == 400, r.text
    assert _cannot_log_in(client, "confused@example.com")
    assert "confused@example.com" not in _roster_emails(client, principal)
    assert _invite_row(client, principal, invite["code"])["status"] == "open"

    retry = _register(client, invite["code"], "confused@example.com")
    assert retry.status_code == 200, retry.text


# --------------------------------------------------------------------- #
# unusable invites
# --------------------------------------------------------------------- #

def test_unknown_invite_is_403(client):
    r = _register(client, "not-a-real-code", "someone@example.com")
    assert r.status_code == 403, r.text
    assert r.json()["detail"]


def test_used_invite_is_403(client):
    principal = _bootstrap_principal(client, "school_A", "principal-a@example.com")
    invite = _create_invite(client, principal)
    assert _register(client, invite["code"], "first@example.com").status_code == 200
    second = _register(client, invite["code"], "second@example.com")
    assert second.status_code == 403, second.text
    assert "used" in second.json()["detail"]
    assert _cannot_log_in(client, "second@example.com")


def test_revoked_invite_is_403(client):
    principal = _bootstrap_principal(client, "school_A", "principal-a@example.com")
    invite = _create_invite(client, principal)
    revoked = client.delete(f"{INVITES}/{invite['code']}", headers=_auth(principal))
    assert revoked.status_code == 200, revoked.text
    assert revoked.json()["status"] == "revoked"
    assert revoked.json()["revokedAt"]

    r = _register(client, invite["code"], "late@example.com")
    assert r.status_code == 403, r.text
    assert _cannot_log_in(client, "late@example.com")


def test_expired_invite_is_403(client):
    principal = _bootstrap_principal(client, "school_A", "principal-a@example.com")
    invite = _create_invite(client, principal)
    store = auth_routes._require()
    past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    with store._conn_lock:
        store.conn.execute("UPDATE invites SET expires_at=? WHERE code=?", (past, invite["code"]))
        store.conn.commit()

    r = _register(client, invite["code"], "late@example.com")
    assert r.status_code == 403, r.text
    assert "expired" in r.json()["detail"]
    assert _invite_row(client, principal, invite["code"])["status"] == "expired"


def test_email_bound_invite_only_registers_that_email(client):
    principal = _bootstrap_principal(client, "school_A", "principal-a@example.com")
    invite = _create_invite(client, principal, email="  Asha@Example.com ")
    assert invite["email"] == "asha@example.com"

    wrong = _register(client, invite["code"], "someone-else@example.com")
    assert wrong.status_code == 403, wrong.text
    assert _invite_row(client, principal, invite["code"])["status"] == "open"

    right = _register(client, invite["code"], "ASHA@example.com")
    assert right.status_code == 200, right.text
    assert right.json()["user"]["email"] == "asha@example.com"


# --------------------------------------------------------------------- #
# single use under concurrency
# --------------------------------------------------------------------- #

def test_two_concurrent_registrations_with_one_invite_exactly_one_succeeds(client):
    principal = _bootstrap_principal(client, "school_A", "principal-a@example.com")
    invite = _create_invite(client, principal)
    barrier = threading.Barrier(2)
    statuses: dict[str, int] = {}

    def attempt(email: str) -> None:
        barrier.wait()
        statuses[email] = _register(client, invite["code"], email).status_code

    threads = [threading.Thread(target=attempt, args=(e,))
               for e in ("racer-1@example.com", "racer-2@example.com")]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)

    assert sorted(statuses.values()) == [200, 403], statuses
    roster = _roster_emails(client, principal)
    assert len(roster & {"racer-1@example.com", "racer-2@example.com"}) == 1


def test_many_threads_racing_on_one_invite_at_the_store_have_one_winner(tmp_path):
    """The HTTP test above may serialise by accident; this one releases eight
    callers at once straight at the store, so the single-use guarantee has to
    come from the conditional UPDATE, not from request timing."""
    store = UserStore(tmp_path / "users.sqlite")
    try:
        code = store.create_invite(school_id="school_A", role="teacher",
                                   created_by="p1").code
        barrier = threading.Barrier(8)
        winners, refused, errors = [], [], []

        def attempt(i: int) -> None:
            barrier.wait()
            try:
                winners.append(store.register(
                    invite_code=code, name=f"Racer {i}",
                    email=f"racer-{i}@example.com", password=PASSWORD))
            except RegistrationRefused:
                refused.append(i)
            except Exception as exc:  # noqa: BLE001 - reported below
                errors.append(exc)

        threads = [threading.Thread(target=attempt, args=(i,)) for i in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=120)

        assert errors == []
        assert len(winners) == 1 and len(refused) == 7
        assert [u.email for u in store.users_for_school("school_A")] == [winners[0].email]
        [invite] = store.invites_for_school("school_A")
        assert invite.used_by == winners[0].id
    finally:
        store.conn.close()


# --------------------------------------------------------------------- #
# who may manage invites
# --------------------------------------------------------------------- #

def test_teachers_and_students_cannot_manage_invites(client):
    principal = _bootstrap_principal(client, "school_A", "principal-a@example.com")
    code = _create_invite(client, principal)["code"]
    teacher = _register(client, _create_invite(client, principal, role="teacher")["code"],
                        "teacher@example.com").json()
    student = _register(client, _create_invite(client, principal, role="student")["code"],
                        "student@example.com").json()

    for member in (teacher, student):
        headers = _auth(member)
        assert client.post(INVITES, json={"role": "teacher"},
                           headers=headers).status_code == 403
        assert client.get(INVITES, headers=headers).status_code == 403
        assert client.delete(f"{INVITES}/{code}", headers=headers).status_code == 403

    assert client.post(INVITES, json={"role": "teacher"}).status_code == 401
    assert client.get(INVITES).status_code == 401
    assert client.delete(f"{INVITES}/{code}").status_code == 401
    assert _invite_row(client, principal, code)["status"] == "open"


def test_a_principal_cannot_see_or_revoke_another_schools_invites(client):
    principal_a = _bootstrap_principal(client, "school_A", "principal-a@example.com")
    principal_b = _bootstrap_principal(client, "school_B", "principal-b@example.com")
    code = _create_invite(client, principal_a)["code"]

    listed = client.get(INVITES, headers=_auth(principal_b))
    assert listed.status_code == 200
    assert code not in {i["code"] for i in listed.json()}

    assert client.delete(f"{INVITES}/{code}", headers=_auth(principal_b)).status_code == 404
    r = _register(client, code, "still-valid@example.com")
    assert r.status_code == 200, r.text
    assert r.json()["user"]["schoolId"] == "school_A"


def test_invites_are_created_for_the_callers_school_only(client):
    """A schoolId in the create body is not how the school is chosen."""
    principal = _bootstrap_principal(client, "school_A", "principal-a@example.com")
    code = _create_invite(client, principal, schoolId="school_B")["code"]
    r = _register(client, code, "new@example.com")
    assert r.json()["user"]["schoolId"] == "school_A"


def test_invite_list_shows_used_and_unused(client):
    principal = _bootstrap_principal(client, "school_A", "principal-a@example.com")
    used = _create_invite(client, principal)["code"]
    unused = _create_invite(client, principal, role="student")["code"]
    assert _register(client, used, "member@example.com").status_code == 200

    rows = {i["code"]: i for i in client.get(INVITES, headers=_auth(principal)).json()}
    assert rows[used]["status"] == "used"
    assert rows[unused]["status"] == "open"
    assert rows[unused]["usedBy"] is None


def test_invite_creation_rejects_bad_input(client):
    principal = _bootstrap_principal(client, "school_A", "principal-a@example.com")
    headers = _auth(principal)
    for body in ({"role": "principal"}, {"role": "admin"},
                 {"role": "teacher", "expiresInDays": 0},
                 {"role": "teacher", "expiresInDays": 91},
                 {"role": "teacher", "email": "not-an-email"}):
        r = client.post(INVITES, json=body, headers=headers)
        assert r.status_code == 400, (body, r.text)

    month = _create_invite(client, principal, expiresInDays=30)
    lifetime = datetime.fromisoformat(month["expiresAt"]) - datetime.now(timezone.utc)
    assert timedelta(days=29, hours=23) < lifetime <= timedelta(days=30)


def test_invite_codes_are_long_random_and_distinct(client):
    principal = _bootstrap_principal(client, "school_A", "principal-a@example.com")
    codes = {_create_invite(client, principal)["code"] for _ in range(20)}
    assert len(codes) == 20
    assert all(len(c) >= 22 for c in codes)  # secrets.token_urlsafe(16): 128 bits


def test_revoking_a_used_or_unknown_invite(client):
    principal = _bootstrap_principal(client, "school_A", "principal-a@example.com")
    code = _create_invite(client, principal)["code"]
    assert _register(client, code, "member@example.com").status_code == 200
    assert client.delete(f"{INVITES}/{code}", headers=_auth(principal)).status_code == 409
    assert client.delete(f"{INVITES}/no-such-code",
                         headers=_auth(principal)).status_code == 404


# --------------------------------------------------------------------- #
# the principal bootstrap key
# --------------------------------------------------------------------- #

def test_principal_key_only_creates_a_schools_first_principal(client):
    _bootstrap_principal(client, "school_A", "principal-a@example.com")

    takeover = client.post(REGISTER, json={
        "schoolId": "school_A", "principalKey": KEY, "name": "Second Principal",
        "email": "takeover@example.com", "password": PASSWORD,
    })
    assert takeover.status_code == 403, takeover.text
    assert "already has a principal" in takeover.json()["detail"]
    assert _cannot_log_in(client, "takeover@example.com")

    # A new school still gets its first principal from the key.
    _bootstrap_principal(client, "school_B", "principal-b@example.com")


def test_principal_key_request_shapes_that_are_refused(client):
    base = {"name": "P", "email": "p@example.com", "password": PASSWORD}
    wrong_key = client.post(REGISTER, json={**base, "schoolId": "school_C",
                                            "principalKey": "wrong"})
    assert wrong_key.status_code == 403, wrong_key.text

    no_school = client.post(REGISTER, json={**base, "principalKey": KEY})
    assert no_school.status_code == 400, no_school.text

    as_teacher = client.post(REGISTER, json={**base, "schoolId": "school_C",
                                             "principalKey": KEY, "role": "teacher"})
    assert as_teacher.status_code == 400, as_teacher.text

    both = client.post(REGISTER, json={**base, "schoolId": "school_C",
                                       "principalKey": KEY, "inviteCode": "x"})
    assert both.status_code == 400, both.text
    assert _cannot_log_in(client, "p@example.com")


def test_no_key_configured_means_no_principal_bootstrap(tmp_path, monkeypatch):
    monkeypatch.delenv("ACOS_PRINCIPAL_BOOTSTRAP_KEY", raising=False)
    with _boot_client(tmp_path, monkeypatch) as c:
        r = c.post(REGISTER, json={
            "schoolId": "school_A", "principalKey": "anything", "name": "P",
            "email": "p@example.com", "password": PASSWORD,
        })
        assert r.status_code == 403, r.text


# --------------------------------------------------------------------- #
# demo accounts only on request
# --------------------------------------------------------------------- #

def test_demo_seed_creates_no_users_unless_its_env_var_is_set(tmp_path, monkeypatch):
    # The old seed skipped itself only under pytest; take that cover away so
    # this test sees what a production process sees.
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.delenv("ACOS_SEED_DEMO_USERS", raising=False)
    store = UserStore(tmp_path / "users.sqlite")
    try:
        assert store.get_by_email("principal@school.com") is None
        assert store.get_by_email("teacher@school.com") is None
        assert store.users_for_school("demo_school") == []
    finally:
        store.conn.close()


def test_demo_seed_runs_when_explicitly_requested(tmp_path, monkeypatch):
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setenv("ACOS_SEED_DEMO_USERS", "1")
    store = UserStore(tmp_path / "users.sqlite")
    try:
        seeded = {(u.email, u.role) for u in store.users_for_school("demo_school")}
        assert seeded == {("teacher@school.com", "teacher"),
                          ("principal@school.com", "principal")}
    finally:
        store.conn.close()
