"""assessment/users.py -- password hashing, sessions, invites, and the
principal-role bootstrap gate.

Two fixes are pinned here:

* 2026-09-11: role used to be `"principal"` for whichever request won the
  race to register first for a given `school_id`. Now only a `principal_key`
  matching the server-side `Config.principal_bootstrap_key` grants it.
* 2026-09-21: the school and role of every other account used to be whatever
  the caller sent, and the key could mint a principal for a school that
  already had one. Now an account comes from a principal-issued invite, and
  the key only creates a school's FIRST principal.

These tests exercise the store directly (`UserStore`). The HTTP layer is in
tests/test_auth_invites.py and test_route_inventory.py's
`test_full_boot_auth_and_principal_approval`.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.assessment.users import (
    EmailAlreadyRegistered, InvalidCredentials, RegistrationConflict, RegistrationRefused,
    UserStore,
)


@pytest.fixture
def store_no_key(tmp_path):
    s = UserStore(tmp_path / "users.sqlite", principal_bootstrap_key="")
    yield s
    s.conn.close()


@pytest.fixture
def store_with_key(tmp_path):
    s = UserStore(tmp_path / "users.sqlite", principal_bootstrap_key="the-real-secret")
    yield s
    s.conn.close()


def _register(store, *, school="s1", name="A", email="a@example.com",
              password="password123", role="teacher"):
    """An ordinary member: invited by the school's principal, then registered."""
    code = store.create_invite(school_id=school, role=role, created_by="principal_1").code
    return store.register(invite_code=code, name=name, email=email, password=password)


def _bootstrap(store, *, school="s1", email="p@example.com", key="the-real-secret"):
    return store.register(school_id=school, name="P", email=email, password="password123",
                          principal_key=key)


# --------------------------------------------------------------------- #
# the security fixes themselves
# --------------------------------------------------------------------- #

def test_no_bootstrap_key_configured_nobody_ever_becomes_principal(store_no_key):
    """The secure default: an unconfigured deployment can't have its
    principal role taken, because nothing can ever satisfy
    `_valid_principal_key` when no key exists to match against."""
    with pytest.raises(RegistrationRefused):
        _bootstrap(store_no_key, key="anything")
    assert store_no_key.users_for_school("s1") == []


def test_registering_first_grants_nothing_without_the_key(store_with_key):
    """The 2026-09-11 vulnerability: winning the race to register first for
    a schoolId must not matter. Without an invite it no longer even creates
    an account."""
    with pytest.raises(RegistrationRefused):
        store_with_key.register(school_id="school_1", name="Eve", email="attacker@example.com",
                                password="password123")
    real_principal = _bootstrap(store_with_key, school="school_1", email="real@example.com")
    assert real_principal.role == "principal"


def test_wrong_key_grants_nothing(store_with_key):
    with pytest.raises(RegistrationRefused):
        _bootstrap(store_with_key, email="wrong@example.com", key="not-the-secret")
    assert store_with_key.get_by_email("wrong@example.com") is None


def test_the_key_cannot_mint_a_second_principal_for_a_school(store_with_key):
    """Reversed on 2026-09-21. The key used to grant principal any number of
    times for the same school, so its holder could take over a school that
    already had one. It now creates only the first."""
    assert _bootstrap(store_with_key, email="p1@example.com").role == "principal"
    with pytest.raises(RegistrationRefused, match="already has a principal"):
        _bootstrap(store_with_key, email="p2@example.com")
    assert store_with_key.get_by_email("p2@example.com") is None


def test_key_bootstraps_each_new_school_once(store_with_key):
    """Still one global key, not a per-school one: the operator provisions
    any NEW school's first principal with it."""
    a = _bootstrap(store_with_key, school="school_a", email="a@example.com")
    b = _bootstrap(store_with_key, school="school_b", email="b@example.com")
    assert (a.role, a.school_id) == ("principal", "school_a")
    assert (b.role, b.school_id) == ("principal", "school_b")


def test_no_invite_and_no_key_is_refused(store_no_key):
    with pytest.raises(RegistrationRefused):
        store_no_key.register(name="A", email="a@example.com", password="password123")


def test_invite_decides_school_and_role(store_no_key):
    code = store_no_key.create_invite(school_id="s9", role="student", created_by="p").code
    user = store_no_key.register(invite_code=code, name="Stu", email="stu@example.com",
                                 password="password123")
    assert (user.school_id, user.role) == ("s9", "student")


def test_invite_plus_disagreeing_school_or_role_is_a_conflict(store_no_key):
    code = store_no_key.create_invite(school_id="s1", role="teacher", created_by="p").code
    for extra in ({"school_id": "s2"}, {"role": "student"}, {"role": "principal"}):
        with pytest.raises(RegistrationConflict):
            store_no_key.register(invite_code=code, name="X", email="x@example.com",
                                  password="password123", **extra)
    assert store_no_key.get_by_email("x@example.com") is None
    # The refused attempts never consumed the invite.
    assert store_no_key.register(invite_code=code, name="X", email="x@example.com",
                                 password="password123").school_id == "s1"


def test_invite_plus_principal_key_is_a_conflict(store_with_key):
    code = store_with_key.create_invite(school_id="s1", role="student", created_by="p").code
    with pytest.raises(RegistrationConflict):
        store_with_key.register(invite_code=code, principal_key="the-real-secret",
                                school_id="s1", name="Stu", email="stu@example.com",
                                password="password123")


def test_invites_cannot_grant_principal(store_no_key):
    with pytest.raises(ValueError):
        store_no_key.create_invite(school_id="s1", role="principal", created_by="p")


def test_accounts_from_before_invites_keep_their_stored_school_and_role(store_no_key):
    """Nothing migrates or re-checks old rows. An account that named its own
    school before 2026-09-21 cannot be told apart from a real one by the
    code, which is why the operator reviews each roster instead."""
    from academicos.assessment.users import _hash_password
    salt = b"0123456789abcdef"
    store_no_key.conn.execute(
        "INSERT INTO users (id, school_id, name, email, password_hash, password_salt, role, "
        "created_at) VALUES (?,?,?,?,?,?,?,?)",
        ("user_old", "school_x", "Old Teacher", "old@example.com",
         _hash_password("password123", salt), salt.hex(), "teacher", "2026-09-01T00:00:00+00:00"))
    store_no_key.conn.commit()
    user = store_no_key.authenticate(email="old@example.com", password="password123")
    assert (user.school_id, user.role) == ("school_x", "teacher")


# --------------------------------------------------------------------- #
# pre-existing behavior, unaffected by the fix
# --------------------------------------------------------------------- #

def test_duplicate_email_rejected(store_no_key):
    _register(store_no_key, email="dup@example.com")
    with pytest.raises(EmailAlreadyRegistered):
        _register(store_no_key, email="dup@example.com")


def test_email_is_case_and_whitespace_normalized(store_no_key):
    _register(store_no_key, email="  Person@Example.com ")
    with pytest.raises(EmailAlreadyRegistered):
        _register(store_no_key, email="person@example.com")


def test_authenticate_round_trip(store_no_key):
    _register(store_no_key, email="login@example.com", password="correct horse battery")
    user = store_no_key.authenticate(email="login@example.com", password="correct horse battery")
    assert user.email == "login@example.com"


def test_authenticate_wrong_password_raises(store_no_key):
    _register(store_no_key, email="login2@example.com", password="correct horse battery")
    with pytest.raises(InvalidCredentials):
        store_no_key.authenticate(email="login2@example.com", password="wrong password")


def test_authenticate_unknown_email_raises(store_no_key):
    with pytest.raises(InvalidCredentials):
        store_no_key.authenticate(email="nobody@example.com", password="whatever123")


def test_session_create_lookup_and_delete(store_no_key):
    user = _register(store_no_key, email="session@example.com")
    token = store_no_key.create_session(user.id)
    assert store_no_key.user_for_session(token).id == user.id

    store_no_key.delete_session(token)
    assert store_no_key.user_for_session(token) is None


def test_session_lookup_unknown_token_returns_none(store_no_key):
    assert store_no_key.user_for_session("not-a-real-token") is None


# --------------------------------------------------------------------- #
# users_for_school -- the real roster an admin UI picks from
# --------------------------------------------------------------------- #

def test_users_for_school_returns_only_that_schools_users(store_no_key):
    _register(store_no_key, school="s1", email="a@example.com")
    _register(store_no_key, school="s1", email="b@example.com")
    _register(store_no_key, school="s2", email="c@example.com")
    roster = store_no_key.users_for_school("s1")
    assert {u.email for u in roster} == {"a@example.com", "b@example.com"}


def test_users_for_school_filters_by_role(store_no_key):
    _register(store_no_key, school="s1", name="T", email="t@example.com")
    _register(store_no_key, school="s1", name="S", email="s@example.com", role="student")
    teachers = store_no_key.users_for_school("s1", role="teacher")
    students = store_no_key.users_for_school("s1", role="student")
    assert [u.email for u in teachers] == ["t@example.com"]
    assert [u.email for u in students] == ["s@example.com"]


def test_users_for_school_empty_school_returns_empty_list(store_no_key):
    assert store_no_key.users_for_school("nobody_here") == []


def test_a_key_stored_with_a_trailing_newline_accepts_the_key_as_typed(tmp_path):
    """The live secret was saved as "<key>\n" and the web trims the field, so
    every first-principal registration on live was a 403 (2026-10-01)."""
    s = UserStore(tmp_path / "users.sqlite", principal_bootstrap_key="the-real-secret\n")
    try:
        user = _bootstrap(s, key="  the-real-secret ")
        assert user.role == "principal" and user.school_id == "s1"
        with pytest.raises(RegistrationRefused):
            _bootstrap(s, school="s2", email="q@example.com", key="the-real-secre")
        with pytest.raises(RegistrationRefused):
            _bootstrap(s, school="s3", email="r@example.com", key="   ")
    finally:
        s.conn.close()
