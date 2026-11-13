"""A school declares its own terms, and "this term" can be computed.

PRD section 12.6 measures exam coverage and time saved "this term", and
section 0 decision 11 times the same task before and after "per term". The
product audit found no term anywhere: CurriculumStore had academic_years
only, so none of those three measures could be computed. A term is a named
date range inside one academic year; terms of a year never overlap, never
leave the year, and never share a name, so a date maps to at most one term
and term_for_date never has to guess.

Nothing is seeded: CBSE schools split the year differently (two terms,
three, or semesters), so a default split would be wrong for most of them.

These run through the real HTTP routes as authenticated users.
"""
from __future__ import annotations

from store_backend import sqlite_only
import sqlite3
from types import SimpleNamespace

import pytest

from test_assessment_routes_auth import _boot_client, _register

BASE = "/api/v1/curriculum"
PRINCIPAL_KEY = "test-bootstrap-key"
YEAR_START, YEAR_END = "2026-04-01", "2027-03-31"


def _bearer(user: dict) -> dict:
    return {"Authorization": f"Bearer {user['token']}"}


@pytest.fixture
def world(tmp_path, monkeypatch):
    with _boot_client(tmp_path, monkeypatch) as client:
        p1 = _register(client, "school_1", "p1@example.com", "Priya Principal",
                       principal_key=PRINCIPAL_KEY)
        p2 = _register(client, "school_2", "p2@example.com", "Ravi Principal",
                       principal_key=PRINCIPAL_KEY)
        teacher = _register(client, "school_1", "t1@example.com", "Ana Teacher")
        assert p1["user"]["role"] == p2["user"]["role"] == "principal"
        assert teacher["user"]["role"] == "teacher"
        from academicos.curriculum import routes as curriculum_routes
        store = curriculum_routes._require()
        year = store.create_academic_year(school_id="school_1", label="2026-27",
                                          start_date=YEAR_START, end_date=YEAR_END)
        yield SimpleNamespace(client=client, store=store, year=year.id,
                              p1=_bearer(p1), p2=_bearer(p2), teacher=_bearer(teacher))


def _create(w, body: dict, auth=None):
    return w.client.post(f"{BASE}/academic-years/{w.year}/terms", json=body,
                         headers=auth or w.p1)


def _two_terms(w) -> tuple[dict, dict]:
    t1 = _create(w, {"name": "Term 1", "startDate": "2026-04-01", "endDate": "2026-09-30"})
    assert t1.status_code == 200, t1.text
    t2 = _create(w, {"name": "Term 2", "startDate": "2026-10-15", "endDate": "2027-03-31"})
    assert t2.status_code == 200, t2.text
    return t1.json(), t2.json()


# --------------------------------------------------------------------- #
# Declaring terms
# --------------------------------------------------------------------- #

def test_a_principal_creates_two_terms_and_lists_them_in_date_order(world):
    t1, t2 = _two_terms(world)
    assert t1["name"] == "Term 1" and t1["startDate"] == "2026-04-01"
    assert t1["endDate"] == "2026-09-30" and t1["academicYearId"] == world.year
    r = world.client.get(f"{BASE}/academic-years/{world.year}/terms", headers=world.p1)
    assert r.status_code == 200, r.text
    assert [t["id"] for t in r.json()] == [t1["id"], t2["id"]]


def test_a_teacher_of_the_school_can_read_the_terms(world):
    _two_terms(world)
    r = world.client.get(f"{BASE}/academic-years/{world.year}/terms", headers=world.teacher)
    assert r.status_code == 200 and len(r.json()) == 2


def test_nothing_is_seeded_by_default(world):
    r = world.client.get(f"{BASE}/academic-years/{world.year}/terms", headers=world.p1)
    assert r.status_code == 200 and r.json() == []
    assert world.store.term_for_date("school_1", "2026-06-15") is None


@pytest.mark.parametrize("start,end", [
    ("2026-09-01", "2026-12-31"),   # starts inside Term 1
    ("2026-03-15", "2026-04-10"),   # ends inside Term 1 (and starts before the year)
    ("2026-05-01", "2026-06-01"),   # wholly inside Term 1
    ("2026-10-01", "2027-03-31"),   # swallows the gap and all of Term 2
    ("2026-09-30", "2026-10-05"),   # shares Term 1's last day only
])
def test_an_overlapping_term_is_refused(world, start, end):
    _two_terms(world)
    r = _create(world, {"name": "Term 3", "startDate": start, "endDate": end})
    assert r.status_code == 422, r.text
    assert len(world.store.terms_for_year(world.year)) == 2


def test_a_term_in_the_gap_between_two_terms_is_accepted(world):
    _two_terms(world)
    r = _create(world, {"name": "Mid-term break", "startDate": "2026-10-01",
                        "endDate": "2026-10-14"})
    assert r.status_code == 200, r.text


@pytest.mark.parametrize("start,end", [
    ("2026-03-01", "2026-06-30"),   # starts before the year
    ("2027-01-01", "2027-04-30"),   # ends after the year
    ("2027-05-01", "2027-06-30"),   # entirely after
])
def test_a_term_outside_the_year_is_refused(world, start, end):
    r = _create(world, {"name": "Term 1", "startDate": start, "endDate": end})
    assert r.status_code == 422, r.text
    assert YEAR_START in r.json()["detail"] and YEAR_END in r.json()["detail"]
    assert world.store.terms_for_year(world.year) == []


@pytest.mark.parametrize("start,end", [
    ("2026-09-30", "2026-04-01"),   # ends before it starts
    ("next monday", "2026-09-30"),
    ("20260401", "2026-09-30"),     # fromisoformat takes it; the string compare would not
])
def test_a_malformed_range_is_refused(world, start, end):
    r = _create(world, {"name": "Term 1", "startDate": start, "endDate": end})
    assert r.status_code == 422, r.text
    assert world.store.terms_for_year(world.year) == []


@pytest.mark.parametrize("name", ["Term 1", "term 1", "  Term 1 "])
def test_a_duplicate_name_in_the_same_year_is_refused(world, name):
    _two_terms(world)
    r = _create(world, {"name": name, "startDate": "2026-10-01", "endDate": "2026-10-14"})
    assert r.status_code == 422, r.text


def test_the_same_name_in_another_year_is_fine(world):
    _two_terms(world)
    other = world.store.create_academic_year(school_id="school_1", label="2027-28",
                                             start_date="2027-04-01", end_date="2028-03-31")
    r = world.client.post(f"{BASE}/academic-years/{other.id}/terms", headers=world.p1,
                          json={"name": "Term 1", "startDate": "2027-04-01",
                                "endDate": "2027-09-30"})
    assert r.status_code == 200, r.text


# --------------------------------------------------------------------- #
# Update and delete
# --------------------------------------------------------------------- #

def test_a_principal_updates_a_term_and_the_same_rules_apply(world):
    t1, t2 = _two_terms(world)
    url = f"{BASE}/terms/{t1['id']}"
    # Moving Term 1's own end is not an overlap with itself.
    r = world.client.put(url, json={"name": "First Term", "startDate": "2026-04-01",
                                    "endDate": "2026-10-10"}, headers=world.p1)
    assert r.status_code == 200, r.text
    assert r.json()["name"] == "First Term" and r.json()["endDate"] == "2026-10-10"
    # Into Term 2, outside the year, or onto Term 2's name: refused, unchanged.
    for body in ({"name": "First Term", "startDate": "2026-04-01", "endDate": "2026-10-20"},
                 {"name": "First Term", "startDate": "2026-03-01", "endDate": "2026-09-30"},
                 {"name": "Term 2", "startDate": "2026-04-01", "endDate": "2026-09-30"}):
        bad = world.client.put(url, json=body, headers=world.p1)
        assert bad.status_code == 422, (body, bad.text)
    stored = world.store.get_term(t1["id"])
    assert (stored.name, stored.end_date) == ("First Term", "2026-10-10")


def test_a_principal_deletes_a_term(world):
    t1, t2 = _two_terms(world)
    r = world.client.delete(f"{BASE}/terms/{t1['id']}", headers=world.p1)
    assert r.status_code == 200, r.text
    assert [t.id for t in world.store.terms_for_year(world.year)] == [t2["id"]]
    assert world.store.term_for_date("school_1", "2026-06-15") is None
    assert world.client.delete(f"{BASE}/terms/{t1['id']}", headers=world.p1).status_code == 404


# --------------------------------------------------------------------- #
# Which term is a date in?
# --------------------------------------------------------------------- #

def test_term_for_date_finds_the_right_term_and_never_guesses(world):
    t1, t2 = _two_terms(world)
    store = world.store
    assert store.term_for_date("school_1", "2026-04-01").id == t1["id"]   # first day
    assert store.term_for_date("school_1", "2026-06-15").id == t1["id"]
    assert store.term_for_date("school_1", "2026-09-30").id == t1["id"]   # last day
    assert store.term_for_date("school_1", "2026-10-15").id == t2["id"]
    assert store.term_for_date("school_1", "2027-03-31").id == t2["id"]
    assert store.term_for_date("school_1", "2026-10-05") is None          # the gap
    assert store.term_for_date("school_1", "2027-04-01") is None          # after the year
    assert store.term_for_date("school_1", "2026-03-31") is None          # before it
    assert store.term_for_date("school_2", "2026-06-15") is None          # another school


def test_the_current_term_route(world):
    t1, _ = _two_terms(world)
    r = world.client.get(f"{BASE}/terms/current", params={"date": "2026-06-15"},
                         headers=world.teacher)
    assert r.status_code == 200, r.text
    assert r.json()["id"] == t1["id"]
    gap = world.client.get(f"{BASE}/terms/current", params={"date": "2026-10-05"},
                           headers=world.p1)
    assert gap.status_code == 404, gap.text
    # school_2 has no terms: its principal gets a 404, never school_1's term.
    other = world.client.get(f"{BASE}/terms/current", params={"date": "2026-06-15"},
                             headers=world.p2)
    assert other.status_code == 404, other.text
    bad = world.client.get(f"{BASE}/terms/current", params={"date": "15/06/2026"},
                           headers=world.p1)
    assert bad.status_code == 422, bad.text


def test_the_current_term_defaults_to_the_schools_today(world, monkeypatch):
    t1, _ = _two_terms(world)
    from datetime import date
    from academicos.curriculum import routes as curriculum_routes
    monkeypatch.setattr(curriculum_routes, "_school_today", lambda: date(2026, 7, 1))
    r = world.client.get(f"{BASE}/terms/current", headers=world.p1)
    assert r.status_code == 200 and r.json()["id"] == t1["id"]


# --------------------------------------------------------------------- #
# Who may do what
# --------------------------------------------------------------------- #

def test_a_teacher_cannot_create_update_or_delete_a_term(world):
    t1, _ = _two_terms(world)
    r = _create(world, {"name": "Term 3", "startDate": "2026-10-01", "endDate": "2026-10-14"},
                auth=world.teacher)
    assert r.status_code == 403, r.text
    body = {"name": "Mine", "startDate": "2026-04-01", "endDate": "2026-09-30"}
    assert world.client.put(f"{BASE}/terms/{t1['id']}", json=body,
                            headers=world.teacher).status_code == 403
    assert world.client.delete(f"{BASE}/terms/{t1['id']}",
                               headers=world.teacher).status_code == 403
    assert len(world.store.terms_for_year(world.year)) == 2


def test_another_schools_principal_cannot_read_or_write_the_terms(world):
    t1, _ = _two_terms(world)
    r = world.client.get(f"{BASE}/academic-years/{world.year}/terms", headers=world.p2)
    assert r.status_code == 403, r.text
    r = _create(world, {"name": "Term 3", "startDate": "2026-10-01", "endDate": "2026-10-14"},
                auth=world.p2)
    assert r.status_code == 403, r.text
    body = {"name": "Hijacked", "startDate": "2026-04-01", "endDate": "2026-09-30"}
    assert world.client.put(f"{BASE}/terms/{t1['id']}", json=body,
                            headers=world.p2).status_code == 403
    assert world.client.delete(f"{BASE}/terms/{t1['id']}", headers=world.p2).status_code == 403
    assert world.store.get_term(t1["id"]).name == "Term 1"


def test_reads_need_a_token(world):
    assert world.client.get(f"{BASE}/academic-years/{world.year}/terms").status_code == 401
    assert world.client.get(f"{BASE}/terms/current",
                            params={"date": "2026-06-15"}).status_code == 401


# --------------------------------------------------------------------- #
# An existing school's database gains the table
# --------------------------------------------------------------------- #

@sqlite_only
def test_an_existing_database_without_the_terms_table_gains_it_on_startup(tmp_path):
    """school_1's real curriculum.sqlite was created before terms existed.
    CurriculumStore runs executescript(SCHEMA) on every open, so the table
    must arrive through CREATE TABLE IF NOT EXISTS -- without touching the
    rows already there."""
    from academicos.curriculum.store import CurriculumStore

    db = tmp_path / "curriculum.sqlite"
    store = CurriculumStore(db)
    year = store.create_academic_year(school_id="school_1", label="2026-27",
                                      start_date=YEAR_START, end_date=YEAR_END)
    store.close()
    conn = sqlite3.connect(str(db))
    conn.execute("DROP TABLE terms")
    conn.commit()
    assert conn.execute("SELECT name FROM sqlite_master WHERE name='terms'").fetchone() is None
    conn.close()

    reopened = CurriculumStore(db)
    try:
        assert reopened.get_academic_year(year.id).label == "2026-27"
        term = reopened.create_term(academic_year_id=year.id, name="Term 1",
                                    start_date="2026-04-01", end_date="2026-09-30")
        assert reopened.term_for_date("school_1", "2026-05-01").id == term.id
    finally:
        reopened.close()
