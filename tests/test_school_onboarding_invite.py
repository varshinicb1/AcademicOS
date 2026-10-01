"""A new school's first principal joins by a single-use invite link the
operator generates (2026-10-01). The school had been sent a School ID and the
platform-wide principal key, and could not get in: the key path asked them for
an ID nobody had given them, and the key itself must never leave the operator.
"""
from __future__ import annotations

import pytest

from academicos.assessment.users import RegistrationRefused, UserStore
from test_route_inventory import _boot_client

KEY = "test-operator-key-0123456789abcdef"
PASSWORD = "correct horse battery"
INVITE = "/api/v1/auth/operator/school-invites"
REGISTER = "/api/v1/auth/register"


@pytest.fixture
def store(tmp_path):
    s = UserStore(tmp_path / "users.sqlite", principal_bootstrap_key=KEY)
    yield s
    s.conn.close()


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Stored with the trailing newline the live secret has.
    monkeypatch.setenv("ACOS_PRINCIPAL_BOOTSTRAP_KEY", KEY + "\n")
    with _boot_client(tmp_path, monkeypatch) as c:
        yield c


def test_a_principal_invite_makes_the_schools_first_principal_once(store):
    invite = store.create_principal_invite(school_id="St-Marys-Hyd")
    assert invite.school_id == "st-marys-hyd" and invite.role == "principal"
    user = store.register(invite_code=invite.code, name="P", email="p@example.com", password=PASSWORD)
    assert user.role == "principal" and user.school_id == "st-marys-hyd"
    # The school now has a principal: no further principal invite, by either path.
    with pytest.raises(RegistrationRefused):
        store.create_principal_invite(school_id="st-marys-hyd")


def test_a_principal_invite_is_refused_if_the_school_got_a_principal_meanwhile(store):
    first = store.create_principal_invite(school_id="greenwood")
    second = store.create_principal_invite(school_id="greenwood")
    store.register(invite_code=first.code, name="P", email="p@example.com", password=PASSWORD)
    with pytest.raises(RegistrationRefused):
        store.register(invite_code=second.code, name="Q", email="q@example.com", password=PASSWORD)


@pytest.mark.parametrize("bad", ["", "ab", "has space", "UPPER_case!", "-lead", "x" * 61])
def test_a_school_id_must_be_a_slug(store, bad):
    with pytest.raises(ValueError):
        store.create_principal_invite(school_id=bad)


def test_the_route_needs_the_operator_key(client):
    for headers in ({}, {"X-Operator-Key": "wrong"}, {"X-Operator-Key": ""}):
        r = client.post(INVITE, json={"schoolId": "oakridge"}, headers=headers)
        assert r.status_code == 403, (headers, r.text)


def test_the_link_signs_up_the_principal_with_nothing_but_their_details(client):
    r = client.post(INVITE, json={"schoolId": "oakridge"}, headers={"X-Operator-Key": f"  {KEY} "})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["schoolId"] == "oakridge"
    assert body["link"].endswith(f"/#/login?invite={body['code']}")
    # The Create account form sends only the code and the person's details.
    r = client.post(REGISTER, json={"inviteCode": body["code"], "name": "Principal",
                                    "email": "head@oakridge.example", "password": PASSWORD})
    assert r.status_code == 200, r.text
    assert r.json()["user"]["role"] == "principal"
    assert r.json()["user"]["schoolId"] == "oakridge"
    # Single use, and the school now has its principal.
    again = client.post(REGISTER, json={"inviteCode": body["code"], "name": "X",
                                        "email": "x@oakridge.example", "password": PASSWORD})
    assert again.status_code == 403
    r = client.post(INVITE, json={"schoolId": "oakridge"}, headers={"X-Operator-Key": KEY})
    assert r.status_code == 409
