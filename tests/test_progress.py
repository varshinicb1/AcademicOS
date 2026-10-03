"""Saved progress (operations/progress.py) and the setup level (progress_routes.py).

Nothing the Guide or the setup wizard knew survived a new browser, a new phone or a cleared
cache, and nobody could say how far a school had got. These hold:

  * a person's progress is theirs: saved, read back after a restart's worth of reads, last
    write wins, and invisible to everyone else, including the principal of their school;
  * a bad key, an oversize value and a flood of keys are refused with a sentence;
  * the setup level is the school's own data read on demand: it starts at 0, moves as the
    school sets itself up, names the next step, and only the principal may read it;
  * erasing a student erases their progress (forget.py).
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from test_assessment_routes_auth import _boot_client, _register  # noqa: E402

PRINCIPAL_KEY = "test-bootstrap-key"
STATUS = "/api/v1/setup-status"
MINE = "/api/v1/me/progress"


@pytest.fixture
def client(tmp_path, monkeypatch):
    from academicos.curriculum import routes as curriculum_routes
    monkeypatch.setattr(curriculum_routes, "_school_today", lambda: date(2026, 10, 1))
    with _boot_client(tmp_path, monkeypatch) as c:
        yield c


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _principal(client, school_id="school_1", email="head@school1.test") -> dict:
    return _auth(_register(client, school_id, email, "Head", principal_key=PRINCIPAL_KEY)["token"])


def _invite_and_join(client, principal, role: str, email: str, name: str) -> dict:
    """The person joins through the invite the school's principal issued, as they would."""
    code = client.post("/api/v1/auth/invites", headers=principal, json={"role": role, "email": email})
    assert code.status_code == 200, code.text
    joined = client.post("/api/v1/auth/register", json={
        "name": name, "email": email, "password": "correct horse battery", "inviteCode": code.json()["code"]})
    assert joined.status_code == 200, joined.text
    return _auth(joined.json()["token"])


def test_a_saved_entry_is_read_back_and_the_last_write_wins(client):
    me = _principal(client)
    assert client.get(MINE, headers=me).json() == {"items": {}}
    first = client.put(f"{MINE}/guide.done.setup", headers=me, json={"value": True})
    assert first.status_code == 200, first.text
    client.put(f"{MINE}/guide.done.setup", headers=me, json={"value": {"at": "2026-10-03", "steps": 4}})
    items = client.get(MINE, headers=me).json()["items"]
    assert items["guide.done.setup"]["value"] == {"at": "2026-10-03", "steps": 4}
    assert items["guide.done.setup"]["updatedAt"]
    assert len(items) == 1


def test_progress_is_the_persons_own_and_no_one_elses(client):
    head = _principal(client)
    teacher = _invite_and_join(client, head, "teacher", "ana@school1.test", "Ana")
    client.put(f"{MINE}/welcome", headers=teacher, json={"value": "seen"})
    assert client.get(MINE, headers=teacher).json()["items"]["welcome"]["value"] == "seen"
    assert "welcome" not in client.get(MINE, headers=head).json()["items"], "not even the principal's"


def test_it_needs_an_account(client):
    assert client.get(MINE).status_code == 401
    assert client.put(f"{MINE}/welcome", json={"value": 1}).status_code == 401


@pytest.mark.parametrize("key", ["Welcome", "has space", "a" * 61, "9starts.with.digit", "x/y"])
def test_a_key_that_is_not_one_of_ours_is_refused(client, key):
    me = _principal(client)
    r = client.put(f"{MINE}/{key.replace('/', '%2F')}", headers=me, json={"value": 1})
    assert r.status_code in (404, 405, 422), (key, r.status_code)  # a slash never reaches the handler
    if r.status_code == 422:
        assert "progress key" in r.json()["detail"]


def test_an_oversize_value_and_a_flood_of_keys_are_refused(client):
    me = _principal(client)
    big = client.put(f"{MINE}/note", headers=me, json={"value": "x" * 3000})
    assert big.status_code == 422 and "at most" in big.json()["detail"]
    for i in range(300):
        assert client.put(f"{MINE}/k{i}", headers=me, json={"value": i}).status_code == 200
    over = client.put(f"{MINE}/one.too.many", headers=me, json={"value": 1})
    assert over.status_code == 422 and "at most 300" in over.json()["detail"]
    assert client.put(f"{MINE}/k0", headers=me, json={"value": "rewrite"}).status_code == 200, \
        "an existing entry can still change at the limit"


def test_an_unknown_field_is_refused_not_ignored(client):
    me = _principal(client)
    assert client.put(f"{MINE}/welcome", headers=me, json={"value": 1, "extra": 2}).status_code == 422


# ----------------------------------------------------------------- the setup level


def test_a_new_school_is_at_zero_and_the_first_step_is_next(client):
    head = _principal(client)
    body = client.get(STATUS, headers=head).json()
    assert body["done"] == 0 and body["percent"] == 0 and body["total"] == len(body["steps"]) == 8
    assert body["nextKey"] == "profile"
    assert [s["key"] for s in body["steps"]] == ["profile", "classes", "calendar", "teachers", "subjects",
                                                  "timetable", "students", "paper"]
    assert all(not s["done"] and s["detail"] and s["path"].startswith("/") for s in body["steps"])


def test_the_level_moves_as_the_school_sets_itself_up(client):
    head = _principal(client)
    assert client.put("/api/v1/curriculum/school-profile", headers=head,
                      json={"name": "Green Valley School"}).status_code == 200
    mid = client.get(STATUS, headers=head).json()
    assert [s["key"] for s in mid["steps"] if s["done"]] == ["profile"]
    assert mid["nextKey"] == "classes" and mid["percent"] == 12

    assert client.post("/api/v1/curriculum/school-setup", headers=head, json={}).status_code == 200
    after = client.get(STATUS, headers=head).json()
    done = {s["key"] for s in after["steps"] if s["done"]}
    assert {"profile", "classes", "calendar"} <= done
    assert after["nextKey"] == "teachers" and after["percent"] > mid["percent"]
    classes = next(s for s in after["steps"] if s["key"] == "classes")
    assert classes["detail"] == "5 classes"

    _invite_and_join(client, head, "teacher", "ana@school1.test", "Ana")
    teachers = next(s for s in client.get(STATUS, headers=head).json()["steps"] if s["key"] == "teachers")
    assert teachers["done"] and teachers["detail"] == "1 joined"


def test_an_invite_waiting_is_said_but_is_not_a_teacher(client):
    head = _principal(client)
    client.post("/api/v1/auth/invites", headers=head, json={"role": "teacher", "email": "later@school1.test"})
    step = next(s for s in client.get(STATUS, headers=head).json()["steps"] if s["key"] == "teachers")
    assert not step["done"] and step["detail"] == "1 invite waiting to be used"


def test_only_the_principal_reads_the_setup_level_and_only_their_own_school(client):
    head = _principal(client)
    teacher = _invite_and_join(client, head, "teacher", "ana@school1.test", "Ana")
    assert client.get(STATUS, headers=teacher).status_code == 403
    assert client.get(STATUS).status_code == 401
    other = _principal(client, school_id="school_2", email="head@school2.test")
    client.put("/api/v1/curriculum/school-profile", headers=other, json={"name": "Elsewhere"})
    mine = client.get(STATUS, headers=head).json()
    assert next(s for s in mine["steps"] if s["key"] == "profile")["done"] is False, "another school's name"


def test_erasing_a_students_data_erases_their_progress(client, tmp_path):
    from academicos.operations.routes import store
    head = _principal(client)
    student = _invite_and_join(client, head, "student", "kid@school1.test", "Kid")
    me = client.get("/api/v1/auth/me", headers=student).json()
    client.put(f"{MINE}/welcome", headers=student, json={"value": "seen"})
    assert store().progress_of(me["id"])
    store().forget_student(me["id"], school_id="school_1", email="kid@school1.test", name="Kid")
    assert store().progress_of(me["id"]) == {}
