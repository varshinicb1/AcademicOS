"""assessment/users.py — password hashing, sessions, and the principal-role
bootstrap gate.

Fixed 2026-09-11: role used to be `"principal"` for whichever request won
the race to register first for a given `school_id` -- an unauthenticated
attacker who beat the real school administrator to `/auth/register` got
admin rights for that school. Now a caller only becomes principal by
supplying a `principal_key` that matches the server-side
`Config.principal_bootstrap_key` secret. These tests exercise the store
directly (`UserStore`), independent of the HTTP layer covered in
test_route_inventory.py's `test_full_boot_auth_and_principal_approval`.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.assessment.users import EmailAlreadyRegistered, InvalidCredentials, UserStore


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
             password="password123", key=None):
    return store.register(school_id=school, name=name, email=email, password=password,
                          principal_key=key)


# --------------------------------------------------------------------- #
# the security fix itself
# --------------------------------------------------------------------- #

def test_no_bootstrap_key_configured_nobody_ever_becomes_principal(store_no_key):
    """The secure default: an unconfigured deployment can't have its
    principal role stolen by a registration race, because nothing can ever
    satisfy `_valid_principal_key` when no key exists to match against."""
    first = _register(store_no_key, email="first@example.com")
    second = _register(store_no_key, email="second@example.com")
    with_bogus_key = _register(store_no_key, email="third@example.com", key="anything")
    assert first.role == "teacher"
    assert second.role == "teacher"
    assert with_bogus_key.role == "teacher"


def test_registering_first_grants_nothing_without_the_key(store_with_key):
    """The exact vulnerability: winning the race to register first for a
    schoolId must not matter anymore."""
    attacker = _register(store_with_key, school="school_1", email="attacker@example.com")
    assert attacker.role == "teacher"

    real_principal = _register(store_with_key, school="school_1",
                               email="real@example.com", key="the-real-secret")
    assert real_principal.role == "principal"


def test_wrong_key_grants_nothing(store_with_key):
    wrong = _register(store_with_key, email="wrong@example.com", key="not-the-secret")
    assert wrong.role == "teacher"


def test_correct_key_can_mint_more_than_one_principal(store_with_key):
    """No "only the first" constraint is enforced -- whoever holds the
    secret can register as principal, any number of times. That's a
    deliberate minimal design (see users.py's module docstring), not an
    oversight."""
    p1 = _register(store_with_key, email="p1@example.com", key="the-real-secret")
    p2 = _register(store_with_key, email="p2@example.com", key="the-real-secret")
    assert p1.role == "principal"
    assert p2.role == "principal"


def test_key_is_school_agnostic_by_design(store_with_key):
    """One global bootstrap key, not a per-school one -- documented
    trade-off, not a bug: whoever holds the key can bootstrap any school."""
    a = _register(store_with_key, school="school_a", email="a@example.com", key="the-real-secret")
    b = _register(store_with_key, school="school_b", email="b@example.com", key="the-real-secret")
    assert a.role == "principal"
    assert b.role == "principal"


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
