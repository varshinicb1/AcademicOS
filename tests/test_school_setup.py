"""POST /curriculum/school-setup: a new school's year, classes, calendar,
terms and bell in one call (curriculum/school_setup.py).

A real school signed up on 2026-10-01 and every screen answered with a server
refusal: the term report "no academic year covers today", the new-exam dialog
"no academic year contains the exam's start date". These tests hold the one
call that sets a school up to what the screens need:

  * an empty body makes everything, and the term report and today's term
    then answer;
  * a second call makes nothing new, and a call after the principal set
    parts up by hand keeps those parts as they are;
  * only the principal may call it, and only for their own school;
  * classes 1-5 (and 11-12) are refused with the reason, and a refused
    request writes nothing.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from academicos.curriculum import school_setup as setup_mod  # noqa: E402
from test_assessment_routes_auth import _boot_client, _register  # noqa: E402

BASE = "/api/v1/curriculum"
SETUP = f"{BASE}/school-setup"
PRINCIPAL_KEY = "test-bootstrap-key"
TODAY = date(2026, 10, 1)


@pytest.fixture
def client(tmp_path, monkeypatch):
    from academicos.curriculum import routes as curriculum_routes
    monkeypatch.setattr(curriculum_routes, "_school_today", lambda: TODAY)
    with _boot_client(tmp_path, monkeypatch) as c:
        yield c


def _principal(client, school_id="school_1", email="head@school1.test") -> dict:
    p = _register(client, school_id, email, "Head", principal_key=PRINCIPAL_KEY)
    return {"Authorization": f"Bearer {p['token']}"}


def _years(client, auth, school_id="school_1") -> list[dict]:
    r = client.get(f"{BASE}/academic-years", params={"school_id": school_id}, headers=auth)
    assert r.status_code == 200, r.text
    return r.json()


def _sections(client, auth, year_id) -> list[str]:
    return [f"{s['gradeNumber']}-{s['name']}"
            for s in client.get(f"{BASE}/academic-years/{year_id}/sections", headers=auth).json()]


# ---------------------------------------------------------------- the defaults


def test_an_empty_body_sets_up_the_whole_school(client):
    auth = _principal(client)
    # Before: what the school saw on every screen.
    before = client.get("/api/v1/dashboard/term", headers=auth)
    assert before.status_code == 404 and "no academic year covers today" in before.json()["detail"]
    assert client.get(f"{BASE}/terms/current", headers=auth).status_code == 404

    r = client.post(SETUP, json={}, headers=auth)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["academicYear"]["label"] == "2026-27"
    assert (body["academicYear"]["startDate"], body["academicYear"]["endDate"]) == ("2026-04-01", "2027-03-31")
    assert body["alreadyExisted"] == [] and body["skipped"] == []
    assert body["created"][0] == "Academic year 2026-27 (2026-04-01 to 2027-03-31)"

    year = body["academicYear"]["id"]
    assert [y["id"] for y in _years(client, auth)] == [year]
    grades = client.get(f"{BASE}/academic-years/{year}/grades", headers=auth).json()
    assert sorted(g["number"] for g in grades) == [6, 7, 8, 9, 10]
    assert _sections(client, auth, year) == ["6-A", "7-A", "8-A", "9-A", "10-A"]
    for c in body["classes"]:
        assert c["created"] is True and c["sections"] == ["A"]
        assert c["subjects"] == 5 and c["chaptersAdded"] > 0, c
        subjects = client.get(f"{BASE}/grades/{c['gradeId']}/subjects", headers=auth).json()
        assert {s["name"] for s in subjects} == {"Mathematics", "Science", "English", "Hindi", "Social Science"}

    cal = client.get(f"{BASE}/academic-years/{year}/calendar", headers=auth).json()
    assert (cal["weeklyOffDays"], cal["alternateSaturdayRule"]) == (["sunday"], "none")
    terms = client.get(f"{BASE}/academic-years/{year}/terms", headers=auth).json()
    assert [(t["name"], t["startDate"], t["endDate"]) for t in terms] == [
        ("Term 1", "2026-04-01", "2026-09-30"), ("Term 2", "2026-10-01", "2027-03-31")]
    assert sorted(body["termIds"]) == sorted(t["id"] for t in terms)

    bells = client.get(f"{BASE}/academic-years/{year}/bell-schedules", headers=auth).json()
    assert len(bells) == 1 and bells[0]["id"] == body["bellScheduleId"]
    bell = bells[0]
    assert bell["isDefault"] and bell["teachingPeriods"] == 8 and bell["days"] == [0, 1, 2, 3, 4, 5]
    assert [(s["start"], s["end"], s["kind"]) for s in bell["slots"]][:6] == [
        ("08:00", "08:40", "teaching"), ("08:40", "09:20", "teaching"), ("09:20", "10:00", "teaching"),
        ("10:00", "10:40", "teaching"), ("10:40", "11:00", "break"), ("11:00", "11:40", "teaching")]
    assert bell["slots"][-1]["end"] == "13:40"

    # After: the screens that refused now answer.
    assert client.get(f"{BASE}/terms/current", headers=auth).json()["name"] == "Term 2"
    report = client.get("/api/v1/dashboard/term", headers=auth)
    assert report.status_code == 200, report.text
    exam = client.post("/api/v1/exams", headers=auth, json={
        "name": "Half-yearly", "startDate": "2026-10-12", "endDate": "2026-10-20", "grades": [9, 10]})
    assert exam.status_code == 200, exam.text


def test_the_call_is_written_to_the_audit_log(client):
    from academicos.assessment.audit_log import get_audit_log
    from academicos.curriculum import routes as cr
    auth = _principal(client)
    client.post(SETUP, json={"classes": [{"grade": 10}]}, headers=auth)
    client.post(SETUP, json={"classes": [{"grade": 10}]}, headers=auth)   # nothing new: no entry
    entries = get_audit_log(cr._cfg.data_root).for_action("school_set_up")
    assert len(entries) == 1
    assert entries[0]["details"]["schoolId"] == "school_1"
    assert "Academic year 2026-27 (2026-04-01 to 2027-03-31)" in entries[0]["details"]["created"]


# ---------------------------------------------------------------- idempotent


def test_a_second_call_makes_nothing_new(client):
    auth = _principal(client)
    first = client.post(SETUP, json={}, headers=auth).json()
    second = client.post(SETUP, json={}, headers=auth)
    assert second.status_code == 200, second.text
    again = second.json()
    assert again["created"] == [] and again["skipped"] == []
    assert again["academicYear"]["id"] == first["academicYear"]["id"]
    assert again["alreadyExisted"] == [
        "Academic year 2026-27", "Class 6", "Class 7", "Class 8", "Class 9", "Class 10",
        "Calendar: Sunday off", "Terms: Term 1, Term 2", "Bell schedule Main"]
    assert all(c["created"] is False and c["chaptersAdded"] == 0 for c in again["classes"])

    year = first["academicYear"]["id"]
    assert len(_years(client, auth)) == 1
    assert _sections(client, auth, year) == ["6-A", "7-A", "8-A", "9-A", "10-A"]
    assert len(client.get(f"{BASE}/academic-years/{year}/terms", headers=auth).json()) == 2
    assert len(client.get(f"{BASE}/academic-years/{year}/bell-schedules", headers=auth).json()) == 1


def test_a_later_call_adds_only_the_missing_classes_and_sections(client):
    auth = _principal(client)
    first = client.post(SETUP, json={"classes": [{"grade": 10}]}, headers=auth).json()
    year = first["academicYear"]["id"]
    r = client.post(SETUP, headers=auth, json={"classes": [
        {"grade": 9, "sections": ["A", "B"]}, {"grade": 10, "sections": ["A", "B", "C"]}]})
    assert r.status_code == 200, r.text
    body = r.json()
    assert "Class 10: sections 10-B, 10-C" in body["created"]
    assert any(line.startswith("Class 9: 5 subjects") and "sections 9-A, 9-B" in line for line in body["created"])
    assert "Class 10" in body["alreadyExisted"]
    assert _sections(client, auth, year) == ["9-A", "9-B", "10-A", "10-B", "10-C"]


def test_sections_named_otherwise_replace_the_default_a(client):
    auth = _principal(client)
    r = client.post(SETUP, headers=auth, json={"classes": [{"grade": 6, "sections": ["Rose", "Lily", "rose"]}]})
    assert r.status_code == 200, r.text
    assert r.json()["classes"][0]["sections"] == ["Lily", "Rose"]
    assert _sections(client, auth, r.json()["academicYear"]["id"]) == ["6-Lily", "6-Rose"]


def test_what_the_principal_set_up_by_hand_is_kept(client):
    auth = _principal(client)
    # A year and class seeded by hand, its own calendar, one term and a short bell.
    seeded = client.post(f"{BASE}/seed/cbse", headers=auth, json={
        "grade": 10, "academicYearLabel": "2026-2027", "startDate": "2026-04-01", "endDate": "2027-03-31"}).json()
    year = seeded["academicYearId"]
    assert client.post(f"{BASE}/academic-years/{year}/calendar", headers=auth, json={
        "weeklyOffDays": ["sunday", "saturday"], "alternateSaturdayRule": "none"}).status_code == 200
    assert client.post(f"{BASE}/academic-years/{year}/terms", headers=auth, json={
        "name": "Whole year", "startDate": "2026-04-01", "endDate": "2027-03-31"}).status_code == 200
    assert client.post(f"{BASE}/academic-years/{year}/bell-schedules", headers=auth, json={
        "name": "Short day", "slots": [{"start": "09:00", "end": "09:45"}]}).status_code == 200

    r = client.post(SETUP, json={"classes": [{"grade": 10}]}, headers=auth)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["academicYear"]["id"] == year, "the year covering today is reused, whatever its name"
    assert body["created"] == [] and body["skipped"] == []
    assert body["alreadyExisted"] == [
        "Academic year 2026-2027", "Class 10", "Calendar: Sunday, Saturday off", "Terms: Whole year",
        "Bell schedule Short day"]
    assert len(_years(client, auth)) == 1
    assert client.get(f"{BASE}/academic-years/{year}/calendar", headers=auth).json()["weeklyOffDays"] == [
        "sunday", "saturday"]
    assert [t["name"] for t in client.get(f"{BASE}/academic-years/{year}/terms", headers=auth).json()] == [
        "Whole year"]


def test_named_terms_add_the_missing_one_and_say_why_one_was_not(client):
    auth = _principal(client)
    year = client.post(SETUP, headers=auth, json={"classes": [{"grade": 10}], "terms": [
        {"name": "Term 1", "startDate": "2026-04-01", "endDate": "2026-09-30"}]}).json()["academicYear"]["id"]
    r = client.post(SETUP, headers=auth, json={"classes": [{"grade": 10}], "terms": [
        {"name": "Term 1", "startDate": "2026-04-01", "endDate": "2026-09-30"},
        {"name": "Term 2", "startDate": "2026-10-01", "endDate": "2027-03-31"},
        {"name": "Overlap", "startDate": "2026-09-01", "endDate": "2026-10-15"}]})
    assert r.status_code == 200, r.text
    body = r.json()
    assert "Term Term 2 (2026-10-01 to 2027-03-31)" in body["created"]
    assert "Term Term 1" in body["alreadyExisted"]
    assert len(body["skipped"]) == 1 and body["skipped"][0].startswith("Term Overlap: ") and "overlaps" in body["skipped"][0]
    assert [t["name"] for t in client.get(f"{BASE}/academic-years/{year}/terms", headers=auth).json()] == [
        "Term 1", "Term 2"]


# ---------------------------------------------------------------- overrides


def test_the_principal_may_give_other_dates_saturdays_and_a_bell(client):
    auth = _principal(client)
    r = client.post(SETUP, headers=auth, json={
        "startDate": "2026-06-01", "endDate": "2027-04-30", "classes": [{"grade": 8}],
        "weeklyOffDays": ["sunday"], "secondAndFourthSaturdaysOff": True,
        "bell": {"periods": 6, "periodMinutes": 45, "startsAt": "07:30", "breakAfterPeriod": 3, "breakMinutes": 30}})
    assert r.status_code == 200, r.text
    body = r.json()
    assert (body["academicYear"]["label"], body["academicYear"]["startDate"], body["academicYear"]["endDate"]) == (
        "2026-27", "2026-06-01", "2027-04-30")
    year = body["academicYear"]["id"]
    assert client.get(f"{BASE}/academic-years/{year}/calendar", headers=auth).json()[
        "alternateSaturdayRule"] == "second_fourth"
    assert "Calendar: Sunday off; second and fourth Saturdays off" in body["created"]
    terms = client.get(f"{BASE}/academic-years/{year}/terms", headers=auth).json()
    assert [(t["startDate"], t["endDate"]) for t in terms] == [
        ("2026-06-01", "2026-11-30"), ("2026-12-01", "2027-04-30")]
    bell = client.get(f"{BASE}/academic-years/{year}/bell-schedules", headers=auth).json()[0]
    assert bell["teachingPeriods"] == 6
    assert [(s["start"], s["kind"]) for s in bell["slots"]][2:5] == [
        ("09:00", "teaching"), ("09:45", "break"), ("10:15", "teaching")]


def test_saturday_as_a_weekly_off_leaves_it_out_of_the_bell(client):
    auth = _principal(client)
    body = client.post(SETUP, headers=auth, json={
        "classes": [{"grade": 7}], "weeklyOffDays": ["saturday", "sunday"]}).json()
    bell = client.get(f"{BASE}/academic-years/{body['academicYear']['id']}/bell-schedules", headers=auth).json()[0]
    assert bell["days"] == [0, 1, 2, 3, 4]


@pytest.mark.parametrize("body,reason", [
    ({"classes": [{"grade": 3}]}, "class 3 cannot be set up here: choose classes 6 to 10"),
    ({"classes": [{"grade": 11}]}, "class 11 cannot be set up here"),
    ({"classes": [{"grade": 6}, {"grade": 6}]}, "class 6 is listed twice"),
    ({"classes": [{"grade": 6, "sections": ["  "]}]}, "a section needs a name"),
    ({"startDate": "2026-04-01", "endDate": "2026-03-01"}, "before it starts"),
    ({"endDate": "2027-03-31"}, "give the year's first day as well as its last"),
    ({"startDate": "1 April"}, "is not a date like 2026-04-01"),
    ({"weeklyOffDays": ["Sun"]}, "unknown weekly off day"),
    ({"terms": [{"name": "Term 1", "startDate": "2026-03-01", "endDate": "2026-09-30"}]}, "is outside the year"),
    ({"bell": {"periods": 12, "periodMinutes": 90, "startsAt": "11:00"}}, "past midnight"),
    ({"bell": {"startsAt": "8 am!"}}, "the day starts at a time like 08:00"),
])
def test_a_refused_request_says_why_and_writes_nothing(client, body, reason):
    auth = _principal(client)
    r = client.post(SETUP, json=body, headers=auth)
    assert r.status_code == 422, r.text
    assert reason in str(r.json()["detail"]), r.json()
    assert _years(client, auth) == [], "nothing is written for a refused request"


# ---------------------------------------------------------------- who may call it


def test_only_the_principal_may_set_up_the_school(client):
    auth = _principal(client)
    teacher = _register(client, "school_1", "teacher@school1.test")
    assert client.post(SETUP, json={}).status_code == 401
    r = client.post(SETUP, json={}, headers={"Authorization": f"Bearer {teacher['token']}"})
    assert r.status_code == 403, r.text
    assert _years(client, auth) == []


def test_it_sets_up_only_the_callers_own_school(client):
    one = _principal(client)
    two = _principal(client, "school_2", "head@school2.test")
    # The school comes from the session; the body cannot name another.
    assert client.post(SETUP, json={"schoolId": "school_2"}, headers=one).status_code == 422
    first = client.post(SETUP, json={"classes": [{"grade": 10}]}, headers=one).json()
    assert _years(client, two, "school_2") == []
    assert client.get(f"{BASE}/academic-years", params={"school_id": "school_1"},
                      headers=two).status_code == 403

    second = client.post(SETUP, json={"classes": [{"grade": 10}]}, headers=two)
    assert second.status_code == 200, second.text
    assert second.json()["created"][0].startswith("Academic year 2026-27")
    assert second.json()["academicYear"]["id"] != first["academicYear"]["id"]
    assert [y["id"] for y in _years(client, one)] == [first["academicYear"]["id"]]


# ---------------------------------------------------------------- the defaults, unit


@pytest.mark.parametrize("today,expected", [
    (date(2026, 10, 1), ("2026-27", "2026-04-01", "2027-03-31")),
    (date(2026, 4, 1), ("2026-27", "2026-04-01", "2027-03-31")),
    (date(2027, 3, 31), ("2026-27", "2026-04-01", "2027-03-31")),
    (date(2027, 1, 15), ("2026-27", "2026-04-01", "2027-03-31")),
    (date(2099, 5, 2), ("2099-00", "2099-04-01", "2100-03-31")),
])
def test_the_school_year_holding_today(today, expected):
    assert setup_mod.school_year_for(today) == expected


def test_default_terms_split_the_year_in_two_halves():
    assert [(t.name, t.start_date, t.end_date) for t in setup_mod.default_terms("2026-04-01", "2027-03-31")] == [
        ("Term 1", "2026-04-01", "2026-09-30"), ("Term 2", "2026-10-01", "2027-03-31")]
    assert [(t.start_date, t.end_date) for t in setup_mod.default_terms("2026-08-31", "2027-06-30")] == [
        ("2026-08-31", "2027-02-27"), ("2027-02-28", "2027-06-30")]
    assert [(t.name, t.start_date, t.end_date) for t in setup_mod.default_terms("2026-04-01", "2026-08-31")] == [
        ("Term 1", "2026-04-01", "2026-08-31")]


def test_the_default_bell_is_eight_forty_minute_periods_from_eight_with_a_break():
    slots = setup_mod.bell_slots(setup_mod.BellSpec())
    assert sum(1 for s in slots if s["kind"] == "teaching") == 8
    assert [s for s in slots if s["kind"] == "break"] == [{"start": "10:40", "end": "11:00", "kind": "break"}]
    assert (slots[0]["start"], slots[-1]["end"]) == ("08:00", "13:40")
    no_break = setup_mod.bell_slots(setup_mod.BellSpec(periods=4, break_after_period=0))
    assert [s["kind"] for s in no_break] == ["teaching"] * 4
