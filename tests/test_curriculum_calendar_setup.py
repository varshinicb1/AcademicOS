"""A principal can set up the school calendar from the web admin, and every
holiday the UI offers really removes a teaching day.

The product audit (2026-09-21, reproduced twice with real data) found the
web admin's "Calendar & Setup" tab broken on its main path, silently:

- the client sent weeklyOffDays as [7] (ints); CreateCalendarRequest wants
  weekday-name strings, so every create was a 422;
- the UI's Saturday rule 'second_fourth' matched no digit token in the
  parser, so no Saturday ever came off;
- every holiday kind the UI offers (public / school / emergency) was
  stored and listed with a 200 but never removed a teaching day -- only
  'holiday' and 'unexpected_closure' were counted;
- weeklyOffDays ['Sun'] was accepted, then working-days answered 404
  'tuple.index(x): x not in tuple', and with no update route the year's
  calendar was stuck (re-create is a 409);
- a holiday whose end_date precedes its date was a 500; garbage dates
  ('next monday') and dates outside the year (2030-01-01) were accepted.

These run through the real HTTP routes as an authenticated principal.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from test_assessment_routes_auth import _boot_client, _register

BASE = "/api/v1/curriculum"
PRINCIPAL_KEY = "test-bootstrap-key"

# The academic year every test uses. September 2026's Saturdays are the
# 5th, 12th, 19th and 26th; 2026-10-05 is a Monday.
YEAR_START, YEAR_END = "2026-06-01", "2027-03-31"


def _bearer(user: dict) -> dict:
    return {"Authorization": f"Bearer {user['token']}"}


@pytest.fixture
def world(tmp_path, monkeypatch):
    with _boot_client(tmp_path, monkeypatch) as client:
        principal = _register(client, "school_1", "p1@example.com", "Priya Principal",
                              principal_key=PRINCIPAL_KEY)
        assert principal["user"]["role"] == "principal"
        from academicos.curriculum import routes as curriculum_routes
        store = curriculum_routes._require()
        year = store.create_academic_year(school_id="school_1", label="2026-27",
                                          start_date=YEAR_START, end_date=YEAR_END)
        yield SimpleNamespace(client=client, auth=_bearer(principal), store=store, year=year.id)


def _create(w, body: dict):
    return w.client.post(f"{BASE}/academic-years/{w.year}/calendar", json=body, headers=w.auth)


def _holiday(w, body: dict):
    return w.client.post(f"{BASE}/academic-years/{w.year}/holidays", json=body, headers=w.auth)


def _working_days(w) -> dict:
    r = w.client.get(f"{BASE}/academic-years/{w.year}/working-days", headers=w.auth)
    assert r.status_code == 200, r.text
    return r.json()


# --------------------------------------------------------------------- #
# Creating the calendar with what the web client actually sends
# --------------------------------------------------------------------- #

def test_the_web_clients_exact_payload_creates_a_calendar(world):
    # curriculum_api.dart createCalendar(): weekday names, the UI's rule value.
    r = _create(world, {"weeklyOffDays": ["sunday"], "alternateSaturdayRule": "second_fourth"})
    assert r.status_code == 200, r.text
    assert r.json()["weeklyOffDays"] == ["sunday"]
    assert r.json()["alternateSaturdayRule"] == "second_fourth"
    got = world.client.get(f"{BASE}/academic-years/{world.year}/calendar", headers=world.auth)
    assert got.status_code == 200 and got.json()["weeklyOffDays"] == ["sunday"]


def test_weekday_names_are_case_insensitive_and_stored_lowercase(world):
    r = _create(world, {"weeklyOffDays": ["Sunday"], "alternateSaturdayRule": "none"})
    assert r.status_code == 200, r.text
    assert r.json()["weeklyOffDays"] == ["sunday"]
    _working_days(world)  # and working-days computes, rather than 404ing


@pytest.mark.parametrize("rule", ["second_fourth", "2nd,4th"])
def test_second_and_fourth_saturdays_come_off(world, rule):
    assert _create(world, {"weeklyOffDays": ["sunday"], "alternateSaturdayRule": rule}).status_code == 200
    dates = set(_working_days(world)["dates"])
    assert "2026-09-12" not in dates and "2026-09-26" not in dates   # 2nd and 4th
    assert "2026-09-05" in dates and "2026-09-19" in dates           # 1st and 3rd teach
    # Ten months, two Saturdays each -- not zero, which is what 'second_fourth' gave.
    assert _working_days(world)["alternateSaturdayOffCount"] == 20


@pytest.mark.parametrize("rule", ["second_and_fourth", "alternate", "6th", "2nd,banana"])
def test_an_unrecognised_saturday_rule_is_refused(world, rule):
    r = _create(world, {"weeklyOffDays": ["sunday"], "alternateSaturdayRule": rule})
    assert r.status_code == 422, r.text
    assert "second_fourth" in r.json()["detail"]   # tells the caller what IS accepted
    assert world.store.get_calendar_for_year(world.year) is None


@pytest.mark.parametrize("day", ["Sun", "7", "funday"])
def test_an_unknown_weekday_is_refused_with_the_accepted_names(world, day):
    r = _create(world, {"weeklyOffDays": [day], "alternateSaturdayRule": "none"})
    assert r.status_code == 422, r.text
    assert "sunday" in r.json()["detail"] and "monday" in r.json()["detail"]
    assert world.store.get_calendar_for_year(world.year) is None


# --------------------------------------------------------------------- #
# Holidays: every kind the UI offers removes a teaching day
# --------------------------------------------------------------------- #

@pytest.mark.parametrize("kind", ["public", "school", "emergency", "holiday", "unexpected_closure"])
def test_a_six_day_block_of_every_closure_kind_removes_six_days(world, kind):
    assert _create(world, {"weeklyOffDays": ["sunday"], "alternateSaturdayRule": "none"}).status_code == 200
    before = _working_days(world)
    # Mon 2026-10-05 .. Sat 2026-10-10: six working days under a Sunday-off week.
    r = _holiday(world, {"date": "2026-10-05", "endDate": "2026-10-10", "label": "Dussehra break",
                         "kind": kind})
    assert r.status_code == 200, r.text
    after = _working_days(world)
    assert before["workingDays"] - after["workingDays"] == 6
    assert after["holidayCount"] == 6
    assert not {"2026-10-05", "2026-10-10"} & set(after["dates"])


def test_an_event_stays_a_working_day(world):
    """'event' (Annual Day, a PTM) is the one kind that marks a day without
    closing the school -- the distinction is deliberate, not an omission."""
    assert _create(world, {"weeklyOffDays": ["sunday"], "alternateSaturdayRule": "none"}).status_code == 200
    before = _working_days(world)
    assert _holiday(world, {"date": "2026-10-07", "label": "Annual Day", "kind": "event"}).status_code == 200
    after = _working_days(world)
    assert after["workingDays"] == before["workingDays"]
    assert "2026-10-07" in after["dates"]


def _holiday_refused(w, body: dict) -> str:
    assert _create(w, {"weeklyOffDays": ["sunday"], "alternateSaturdayRule": "none"}).status_code == 200
    r = _holiday(w, body)
    assert r.status_code == 422, r.text
    assert w.client.get(f"{BASE}/academic-years/{w.year}/holidays", headers=w.auth).json() == []
    return r.json()["detail"]


def test_an_unknown_holiday_kind_is_refused(world):
    detail = _holiday_refused(world, {"date": "2026-10-05", "label": "x", "kind": "festival"})
    assert "public" in detail and "event" in detail


def test_end_date_before_date_is_a_422_not_a_500(world):
    _holiday_refused(world, {"date": "2026-10-10", "endDate": "2026-10-05", "label": "backwards",
                             "kind": "public"})


@pytest.mark.parametrize("field", ["date", "endDate"])
def test_an_unparseable_date_is_refused(world, field):
    body = {"date": "2026-10-05", "label": "x", "kind": "public"}
    body[field] = "next monday"
    _holiday_refused(world, body)


@pytest.mark.parametrize("date, end_date", [("2030-01-01", None), ("2026-05-31", None),
                                            ("2027-03-25", "2027-04-10")])
def test_a_holiday_outside_the_academic_year_is_refused(world, date, end_date):
    body = {"date": date, "label": "x", "kind": "public"}
    if end_date:
        body["endDate"] = end_date
    detail = _holiday_refused(world, body)
    assert YEAR_START in detail and YEAR_END in detail


# --------------------------------------------------------------------- #
# Correcting a calendar after it was created
# --------------------------------------------------------------------- #

def test_a_calendar_can_be_updated_and_the_working_day_count_follows(world):
    assert _create(world, {"weeklyOffDays": ["sunday"], "alternateSaturdayRule": "none"}).status_code == 200
    before = _working_days(world)
    # Re-creating is still a 409 -- the correction path is the update.
    assert _create(world, {"weeklyOffDays": ["saturday", "sunday"]}).status_code == 409

    r = world.client.put(f"{BASE}/academic-years/{world.year}/calendar", headers=world.auth,
                         json={"weeklyOffDays": ["saturday", "sunday"], "alternateSaturdayRule": "none"})
    assert r.status_code == 200, r.text
    assert r.json()["weeklyOffDays"] == ["saturday", "sunday"]
    after = _working_days(world)
    # 2026-06-01 .. 2027-03-31 holds 43 Saturdays; each is now a weekly off.
    assert before["workingDays"] - after["workingDays"] == 43
    assert after["weeklyOffCount"] == before["weeklyOffCount"] + 43


def test_an_update_is_validated_like_a_create(world):
    assert _create(world, {"weeklyOffDays": ["sunday"], "alternateSaturdayRule": "none"}).status_code == 200
    url = f"{BASE}/academic-years/{world.year}/calendar"
    assert world.client.put(url, headers=world.auth,
                            json={"weeklyOffDays": ["Sun"]}).status_code == 422
    assert world.client.put(url, headers=world.auth,
                            json={"weeklyOffDays": ["sunday"],
                                  "alternateSaturdayRule": "bogus"}).status_code == 422
    assert world.store.get_calendar_for_year(world.year).weekly_off_days == ["sunday"]


def test_updating_a_calendar_that_does_not_exist_is_a_404(world):
    r = world.client.put(f"{BASE}/academic-years/{world.year}/calendar", headers=world.auth,
                         json={"weeklyOffDays": ["sunday"], "alternateSaturdayRule": "none"})
    assert r.status_code == 404, r.text


def test_only_the_schools_own_principal_can_update_its_calendar(world):
    assert _create(world, {"weeklyOffDays": ["sunday"], "alternateSaturdayRule": "none"}).status_code == 200
    url = f"{BASE}/academic-years/{world.year}/calendar"
    body = {"weeklyOffDays": ["friday"], "alternateSaturdayRule": "none"}
    teacher = _register(world.client, "school_1", "t1@example.com", "Tara Teacher")
    assert world.client.put(url, json=body, headers=_bearer(teacher)).status_code == 403
    other = _register(world.client, "school_2", "p2@example.com", "Other Principal",
                      principal_key=PRINCIPAL_KEY)
    assert world.client.put(url, json=body, headers=_bearer(other)).status_code == 403
    assert world.client.put(url, json=body).status_code == 401
    assert world.store.get_calendar_for_year(world.year).weekly_off_days == ["sunday"]


def test_a_wrong_holiday_can_be_removed_and_the_day_teaches_again(world):
    assert _create(world, {"weeklyOffDays": ["sunday"], "alternateSaturdayRule": "none"}).status_code == 200
    before = _working_days(world)
    h = _holiday(world, {"date": "2026-10-07", "label": "Typo", "kind": "public"}).json()
    assert _working_days(world)["workingDays"] == before["workingDays"] - 1

    url = f"{BASE}/academic-years/{world.year}/holidays/{h['id']}"
    teacher = _register(world.client, "school_1", "t1@example.com", "Tara Teacher")
    assert world.client.delete(url, headers=_bearer(teacher)).status_code == 403
    other = _register(world.client, "school_2", "p2@example.com", "Other Principal",
                      principal_key=PRINCIPAL_KEY)
    assert world.client.delete(url, headers=_bearer(other)).status_code == 403

    r = world.client.delete(url, headers=world.auth)
    assert r.status_code == 200, r.text
    assert _working_days(world)["workingDays"] == before["workingDays"]
    assert world.client.delete(url, headers=world.auth).status_code == 404
