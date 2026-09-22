"""The invite rules on the REMOTE branch, which is the one production runs.

tests/test_auth_invites.py builds every UserStore with no remote configured,
so it only proves the SQLite branch: single use there comes from an UPDATE's
rowcount. On Render the durable store is Supabase (PostgREST), which returns no
rowcount, so `_claim_invite` does a conditional PATCH (`used_at=eq.` and
`revoked_at=eq.`) and then reads the row back to see whose `used_by` stuck. The
2026-09-22 review of Task 301 found none of that, nor the remote release, the
remote revoke or the fail-closed bootstrap check, was executed by any test.

`FakeDurableTable` stands in for `postgres_kv.durable_table(name)`. It keeps
rows in memory and applies each call under one lock, which is what Postgres
gives a single PATCH statement: the filter and the write happen together, so
two conditional PATCHes on one row cannot both match. Equality filters treat
'' as a value, as `eq.` does in PostgREST (and NULL matches nothing). Setting
`down` makes every call raise SupabaseUnavailable, like a Supabase outage or a
missing table (PostgREST 404).
"""
from __future__ import annotations

import copy
import threading

import pytest

from academicos.assessment import users as users_mod
from academicos.assessment.supabase_kv import SupabaseUnavailable
from academicos.assessment.users import (
    InviteAlreadyUsed, RegistrationRefused, UserStore,
)

from test_route_inventory import _boot_client

KEY = "test-bootstrap-key"
PASSWORD = "correct horse battery"
REGISTER = "/api/v1/auth/register"
INVITES = "/api/v1/auth/invites"


class FakeDurableTable:
    """In-memory PostgREST table: enabled/select/update/upsert/delete with
    equality filters. Not a model of every PostgREST feature, only of the
    calls UserStore makes."""

    def __init__(self, table: str):
        self.table = table
        self.rows: list[dict] = []
        self.down = False
        # Per-operation failure injection, e.g. {"upsert": RuntimeError("x")}.
        self.fail: dict[str, BaseException] = {}
        self._lock = threading.Lock()

    @property
    def enabled(self) -> bool:
        return True

    def _check(self, op: str) -> None:
        if self.down:
            raise SupabaseUnavailable(table=self.table, op=op, status=503,
                                      body="fake outage")
        if op in self.fail:
            raise self.fail[op]

    @staticmethod
    def _matches(row: dict, filters: dict) -> bool:
        # `eq.` compares as text; a stored None (SQL NULL) matches nothing.
        return all(row.get(k) is not None and str(row.get(k)) == str(v)
                   for k, v in filters.items())

    def select(self, order=None, limit=None, gt=None, **eq):
        with self._lock:
            self._check("select")
            return [copy.deepcopy(r) for r in self.rows if self._matches(r, eq)]

    def update(self, values: dict, **eq) -> None:
        with self._lock:
            self._check("update")
            for r in self.rows:
                if self._matches(r, eq):
                    r.update(values)

    def upsert(self, row: dict, on_conflict: str) -> None:
        with self._lock:
            self._check("upsert")
            for r in self.rows:
                if r.get(on_conflict) == row[on_conflict]:
                    r.update(copy.deepcopy(row))
                    return
            self.rows.append(copy.deepcopy(row))

    def delete(self, **eq) -> None:
        with self._lock:
            self._check("delete")
            self.rows = [r for r in self.rows if not self._matches(r, eq)]


@pytest.fixture
def remote(monkeypatch):
    """Every table UserStore opens is a fake; returns them by name."""
    tables: dict[str, FakeDurableTable] = {}

    def factory(name: str) -> FakeDurableTable:
        return tables.setdefault(name, FakeDurableTable(name))

    monkeypatch.setattr(users_mod, "durable_table", factory)
    return tables


@pytest.fixture
def store(tmp_path, remote):
    s = UserStore(tmp_path / "users.sqlite", principal_bootstrap_key=KEY)
    yield s
    s.conn.close()


@pytest.fixture
def client(tmp_path, monkeypatch, remote):
    monkeypatch.setenv("ACOS_PRINCIPAL_BOOTSTRAP_KEY", KEY)
    with _boot_client(tmp_path, monkeypatch) as c:
        yield c


def _local_count(store: UserStore, table: str) -> int:
    with store._conn_lock:
        return store.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def _auth(body: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {body['token']}"}


def _bootstrap_principal(client, school_id: str, email: str) -> dict:
    r = client.post(REGISTER, json={
        "schoolId": school_id, "principalKey": KEY, "name": "Principal",
        "email": email, "password": PASSWORD,
    })
    assert r.status_code == 200, r.text
    return r.json()


# --------------------------------------------------------------------- #
# (a) single use, on the remote branch
# --------------------------------------------------------------------- #

def test_invite_is_written_to_the_remote_store_not_local(store, remote):
    invite = store.create_invite(school_id="school_A", role="teacher", created_by="p1")
    assert [r["code"] for r in remote["invites"].rows] == [invite.code]
    assert _local_count(store, "invites") == 0


def test_many_threads_racing_on_one_remote_invite_have_one_winner(store, remote):
    """Eight callers released at once against the remote branch. The status
    check passes for all of them; single use has to come from the
    conditional PATCH plus the read-back of `used_by`."""
    code = store.create_invite(school_id="school_A", role="teacher", created_by="p1").code
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
    assert [r["email"] for r in remote["users"].rows] == [winners[0].email]
    [row] = remote["invites"].rows
    assert row["used_by"] == winners[0].id and row["used_at"]
    assert _local_count(store, "users") == 0


def test_a_used_remote_invite_is_refused_the_second_time(store):
    code = store.create_invite(school_id="school_A", role="student", created_by="p1").code
    first = store.register(invite_code=code, name="A", email="a@example.com", password=PASSWORD)
    assert (first.school_id, first.role) == ("school_A", "student")
    with pytest.raises(RegistrationRefused):
        store.register(invite_code=code, name="B", email="b@example.com", password=PASSWORD)


# --------------------------------------------------------------------- #
# (b) a failed account insert after a remote claim releases the invite
# --------------------------------------------------------------------- #

def test_failed_user_insert_after_remote_claim_releases_the_invite(store, remote):
    code = store.create_invite(school_id="school_A", role="teacher", created_by="p1").code
    # Not a RequestException, so _insert_user does not fall back to local
    # SQLite: the insert genuinely fails after the claim has been made.
    remote["users"].fail["upsert"] = RuntimeError("disk full")
    with pytest.raises(RuntimeError):
        store.register(invite_code=code, name="A", email="a@example.com", password=PASSWORD)

    [row] = remote["invites"].rows
    assert (row["used_by"], row["used_at"]) == ("", "")
    assert remote["users"].rows == []

    del remote["users"].fail["upsert"]
    user = store.register(invite_code=code, name="A", email="a@example.com", password=PASSWORD)
    assert remote["invites"].rows[0]["used_by"] == user.id


def test_release_only_undoes_our_own_claim(store, remote):
    """The release is conditional on `used_by` being us, so a late release
    from a loser cannot free an invite someone else now holds."""
    code = store.create_invite(school_id="school_A", role="teacher", created_by="p1").code
    winner = store.register(invite_code=code, name="A", email="a@example.com", password=PASSWORD)
    store._release_invite(code, "user_someone_else", "remote")
    assert remote["invites"].rows[0]["used_by"] == winner.id


# --------------------------------------------------------------------- #
# (c) the bootstrap check fails closed when the remote read fails
# --------------------------------------------------------------------- #

def test_bootstrap_check_remote_outage_is_503_and_creates_no_principal(client, remote):
    remote["users"].down = True
    r = client.post(REGISTER, json={
        "schoolId": "school_A", "principalKey": KEY, "name": "Second",
        "email": "second@example.com", "password": PASSWORD,
    })
    assert r.status_code == 503, r.text
    remote["users"].down = False
    assert remote["users"].rows == []
    store = users_mod._INSTANCE
    stores = store.values() if isinstance(store, dict) else [store]
    assert all(_local_count(s, "users") == 0 for s in stores)


def test_bootstrap_sees_a_principal_that_only_the_remote_store_knows(client, remote):
    """After a cold start the local file is empty; the remote row alone must
    stop a second principal."""
    remote["users"].rows.append({
        "id": "user_p1", "school_id": "school_A", "name": "P", "email": "p@example.com",
        "password_hash": "x", "password_salt": "00", "role": "principal",
        "created_at": "2026-09-01T00:00:00+00:00",
    })
    r = client.post(REGISTER, json={
        "schoolId": "school_A", "principalKey": KEY, "name": "Second",
        "email": "second@example.com", "password": PASSWORD,
    })
    assert r.status_code == 403, r.text


# --------------------------------------------------------------------- #
# (d) revoke racing a claim on the remote branch
# --------------------------------------------------------------------- #

@pytest.mark.parametrize("round_", range(10))
def test_revoke_racing_a_remote_claim_has_one_outcome(store, remote, round_):
    code = store.create_invite(school_id="school_A", role="teacher", created_by="p1").code
    barrier = threading.Barrier(2)
    outcome: dict[str, object] = {}

    def claim() -> None:
        barrier.wait()
        try:
            outcome["user"] = store.register(invite_code=code, name="A",
                                             email="a@example.com", password=PASSWORD)
        except RegistrationRefused as exc:
            outcome["claim_refused"] = exc

    def revoke() -> None:
        barrier.wait()
        try:
            outcome["revoked"] = store.revoke_invite(code=code, school_id="school_A")
        except InviteAlreadyUsed as exc:
            outcome["revoke_refused"] = exc

    threads = [threading.Thread(target=claim), threading.Thread(target=revoke)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)

    [row] = remote["invites"].rows
    assert not (row["used_at"] and row["revoked_at"]), row
    if "user" in outcome:
        assert set(outcome) == {"user", "revoke_refused"}, outcome
        assert row["used_by"] == outcome["user"].id
        assert [r["email"] for r in remote["users"].rows] == ["a@example.com"]
    else:
        assert set(outcome) == {"revoked", "claim_refused"}, outcome
        assert row["revoked_at"] and row["used_by"] == ""
        assert remote["users"].rows == []


# --------------------------------------------------------------------- #
# an outage is reported as an outage, not as a wrong answer
# --------------------------------------------------------------------- #

def test_invite_lookup_during_outage_raises_instead_of_saying_unknown(store, remote):
    code = store.create_invite(school_id="school_A", role="teacher", created_by="p1").code
    remote["invites"].down = True
    with pytest.raises(SupabaseUnavailable):
        store.register(invite_code=code, name="A", email="a@example.com", password=PASSWORD)
    with pytest.raises(SupabaseUnavailable):
        store.revoke_invite(code=code, school_id="school_A")
    with pytest.raises(SupabaseUnavailable):
        store.invites_for_school("school_A")


def test_create_invite_during_outage_raises_and_writes_nothing_local(store, remote):
    """On Render the local disk is wiped at every cold start: an invite saved
    only there would be handed to the principal as a working code and then
    vanish. Refuse instead."""
    remote["invites"].down = True
    with pytest.raises(SupabaseUnavailable):
        store.create_invite(school_id="school_A", role="teacher", created_by="p1")
    assert _local_count(store, "invites") == 0


def test_invite_routes_answer_503_during_an_outage(client, remote):
    principal = _bootstrap_principal(client, "school_A", "principal-a@example.com")
    r = client.post(INVITES, json={"role": "teacher"}, headers=_auth(principal))
    assert r.status_code == 200, r.text
    code = r.json()["code"]

    remote["invites"].down = True
    registered = client.post(REGISTER, json={
        "inviteCode": code, "name": "T", "email": "t@example.com", "password": PASSWORD,
    })
    assert registered.status_code == 503, registered.text
    assert client.get(INVITES, headers=_auth(principal)).status_code == 503
    assert client.delete(f"{INVITES}/{code}", headers=_auth(principal)).status_code == 503
    assert client.post(INVITES, json={"role": "teacher"},
                       headers=_auth(principal)).status_code == 503

    remote["invites"].down = False
    # The code was never consumed or lost: it still works once storage is back.
    ok = client.post(REGISTER, json={
        "inviteCode": code, "name": "T", "email": "t@example.com", "password": PASSWORD,
    })
    assert ok.status_code == 200, ok.text
