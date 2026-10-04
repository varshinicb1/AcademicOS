"""Half days, exam windows and compensatory working days (v3 audit N-3-19;
SCH-1, and the SCH-8 cases "half-days", "an exam day that cancels teaching"
and "a day that becomes a working day (compensatory Saturday)").

The calendar knew only weekly offs, alternate Saturdays and closures, and an
`event` never removed a day: a half day could not shorten a day, an exam
window could not stop teaching without a published datesheet, and a Saturday
made working could not be added. Each is now a calendar row that the day
view, cover, the lesson plans and the calendar feed all read the same way.

test_cover_routes' world: 2026-06-01 (MON) is a Monday and "today"; period n
runs (7+n):00-(7+n):45. On Mondays 10-A has Science (Ana) in P1 and Maths
(Bala) in P2; 10-B has Maths (Bala) in P1 and Science (Ana) in P2; 9-A has
Science (Chitra) in P1 and Maths (Dev) in P3. Nothing is taught on other
weekdays. A Science plan of one lesson a week is laid on each Monday.
"""
from __future__ import annotations

from academicos.curriculum import calendar as calendar_mod
from academicos.curriculum import scheduling

from test_cover_exams import _dates, _science_book
from test_cover_routes import BASE, MON, _apply, w  # noqa: F401 - `w` is a fixture

MONDAYS = ["2026-06-01", "2026-06-08", "2026-06-15", "2026-06-22", "2026-06-29", "2026-07-06"]
SECOND_SATURDAY = "2026-06-13"


def _plan(w, *sections) -> str:
    book = _science_book(w)
    for section in sections:
        scheduling.schedule_book(w.store, school_id="school_1", academic_year_id=w.year, book_id=book,
                                 periods_per_week=1, from_date=MON, section_id=section)
        assert _dates(w, book, section) == MONDAYS
    return book


def _add(w, **body):
    return w.c.post(f"{BASE}/academic-years/{w.year}/holidays", json=body, headers=w.p)


def _day(w, on, section, headers=None):
    r = w.c.get(f"{BASE}/day", params={"date": on, "sectionId": section}, headers=headers or w.p)
    assert r.status_code == 200, r.text
    return r.json()


def _decide(w, who, on):
    leave = _apply(w, who, startDate=on, endDate=on).json()
    r = w.c.post(f"{BASE}/leave-requests/{leave['id']}/decision", json={"approve": True}, headers=w.p)
    assert r.status_code == 200, r.text
    return {(s["sectionId"], s["period"]): s for s in r.json()["substitutions"]}


def _ics(w, who) -> str:
    url = w.c.get("/api/v1/calendar-feed", headers=w.t[who]).json()["url"]
    return w.c.get(url[url.index("/api/v1"):]).text


def _calendar(w, who):
    r = w.c.get("/api/v1/my-calendar", headers=who if isinstance(who, dict) else w.t[who])
    assert r.status_code == 200, r.text
    return r.json()


# ---------------------------------------------------------------- the arithmetic


def test_a_compensatory_day_is_a_working_day_and_a_closure_still_closes_it():
    sat = "2026-06-13"
    base = dict(start_date="2026-06-01", end_date="2026-06-30", weekly_off_days=["sunday"],
                alternate_saturday_rule="second_fourth", holiday_dates=set())
    before = calendar_mod.compute_working_days(**base)
    after = calendar_mod.compute_working_days(**base, extra_working_dates=frozenset({sat}))
    assert sat not in before.dates and sat in after.dates
    assert after.working_days == before.working_days + 1 and after.compensatory_count == 1
    assert after.alternate_saturday_off_count == before.alternate_saturday_off_count - 1
    closed = calendar_mod.compute_working_days(**{**base, "holiday_dates": {sat}},
                                               extra_working_dates=frozenset({sat}))
    assert sat not in closed.dates and closed.compensatory_count == 0


# ---------------------------------------------------------------- half days


def test_a_half_day_keeps_only_its_early_periods_everywhere(w):
    book = _plan(w, w.a10, w.b10)
    half = "2026-06-08"
    r = _add(w, date=half, label="PTM", kind="half_day", lastPeriod=1)
    assert r.status_code == 200, r.text
    assert (r.json()["kind"], r.json()["lastPeriod"]) == ("half_day", 1)
    assert r.json()["lessonsMoved"] >= 1

    # The day view: 10-B's period 2 is not held; 9-A keeps its P1, loses its P3.
    assert [(x["period"], x["kind"]) for x in _day(w, half, w.b10)] == [(1, "regular")]
    assert [x["period"] for x in _day(w, half, w.a9)] == [1]
    assert {x["period"] for x in w.c.get(f"{BASE}/my-day", params={"date": half}, headers=w.stu).json()} == {1}
    # Still a full working day for the count.
    assert half in w.c.get(f"{BASE}/academic-years/{w.year}/working-days", headers=w.p).json()["dates"]

    # The plan: 10-B's Science (period 2) moves off the half day; 10-A's (period 1) stays.
    assert _dates(w, book, w.b10) == [MON] + MONDAYS[2:] + ["2026-07-13"]
    assert _dates(w, book, w.a10) == MONDAYS
    # A regenerate keeps the cut period off too.
    scheduling.schedule_book(w.store, school_id="school_1", academic_year_id=w.year, book_id=book,
                             periods_per_week=1, from_date=MON, section_id=w.b10, force=True)
    assert "2026-06-08" not in _dates(w, book, w.b10)

    # Cover: Ana's 10-B period 2 is cut, so only her 10-A period 1 needs anyone.
    assert set(_decide(w, "ana", half)) == {(w.a10, 1)}

    # The calendar feed leaves the cut period out, and the apps list the day.
    ics = _ics(w, "ana")
    assert "EXDATE;TZID=Asia/Kolkata:20260608T090000" in ics
    assert "Half day: PTM (periods 1-1)" in ics
    assert ("half_day", half, "Half day: PTM (periods 1-1)") in {
        (i["kind"], i["date"], i["title"]) for i in _calendar(w, w.stu)}


def test_removing_a_half_day_gives_the_plan_its_period_back(w):
    book = _plan(w, w.b10)
    h = _add(w, date="2026-06-08", label="PTM", kind="half_day", lastPeriod=1).json()
    assert _dates(w, book, w.b10)[1] == "2026-06-15"
    r = w.c.delete(f"{BASE}/academic-years/{w.year}/holidays/{h['id']}", headers=w.p)
    assert r.status_code == 200, r.text
    assert _dates(w, book, w.b10) == MONDAYS
    assert [x["period"] for x in _day(w, "2026-06-08", w.b10)] == [1, 2]


def test_a_half_day_is_refused_without_its_last_period_and_fields_stay_with_their_kind(w):
    assert _add(w, date="2026-06-08", label="PTM", kind="half_day").status_code == 422
    assert _add(w, date="2026-06-08", label="PTM", kind="half_day", lastPeriod=0).status_code == 422
    bad = _add(w, date="2026-06-08", label="Diwali", kind="public", lastPeriod=4)
    assert bad.status_code == 422 and "only a half day" in bad.json()["detail"]
    assert _add(w, date="2026-06-08", label="Diwali", kind="public", grades=[10]).status_code == 422
    assert _add(w, date="2026-06-08", label="Diwali", kind="public", timetableWeekday=0).status_code == 422


# ---------------------------------------------------------------- exam windows


def test_an_exam_window_stops_its_classes_teaching_without_a_datesheet(w):
    book = _plan(w, w.a10, w.b10)
    r = _add(w, date="2026-06-08", endDate="2026-06-12", label="Unit test 1", kind="exam_window", grades=[10])
    assert r.status_code == 200, r.text
    assert r.json()["grades"] == [10]
    on = "2026-06-08"

    # Grade 10 sits exams all day; grade 9 is taught as usual.
    day = _day(w, on, w.b10)
    assert [(x["period"], x["kind"]) for x in day] == [(1, "exam"), (2, "exam")]
    assert all(x["teacherId"] is None and x["note"] == "Exam window: Unit test 1" for x in day)
    assert {x["kind"] for x in _day(w, on, w.a9)} == {"regular"}
    student = w.c.get(f"{BASE}/my-day", params={"date": on}, headers=w.stu).json()
    assert {x["kind"] for x in student} == {"exam"}
    # It is still a working day: the school is open.
    assert on in w.c.get(f"{BASE}/academic-years/{w.year}/working-days", headers=w.p).json()["dates"]

    # The plans of grade 10 move past the window.
    assert _dates(w, book, w.a10) == _dates(w, book, w.b10) == [MON] + MONDAYS[2:] + ["2026-07-13"]

    # Cover: with Chitra away, Ana is free during 9-A's Science (her classes
    # are in the window) and teaches Science; Ana's own leave needs nobody.
    subs = _decide(w, "chitra", on)
    assert subs[(w.a9, 1)]["substituteId"] == w.uid["ana"] and subs[(w.a9, 1)]["mode"] == "substitute"
    leave = _apply(w, "bala", startDate=on, endDate=on).json()
    assert w.store.affected_periods(w.store.get_leave(leave["id"])) == []

    # The apps list it for the classes it stops, not for the others.
    assert any(i["kind"] == "exam_window" and i["title"] == "Exam window: Unit test 1 (class 10)"
               and i["endDate"] == "2026-06-12" for i in _calendar(w, w.stu))
    assert any(i["kind"] == "exam_window" for i in _calendar(w, "ana"))
    assert not any(i["kind"] == "exam_window" for i in _calendar(w, "dev")), "Dev teaches grade 9 only"
    assert any(i["kind"] == "exam_window" for i in _calendar(w, w.p))
    assert "EXDATE;TZID=Asia/Kolkata:20260608T080000" in _ics(w, "ana")


def test_an_exam_window_and_a_published_paper_agree(w):
    """The paper inside the window is named by the paper; taking the window
    away leaves the paper's period off the plan, and only that."""
    book = _plan(w, w.a10, w.b10)
    window = _add(w, date="2026-06-08", label="Unit test 1", kind="exam_window", grades=[10]).json()
    exam = w.c.post("/api/v1/exams", json={"name": "Unit test 1", "startDate": "2026-06-08", "endDate": "2026-06-08",
                                            "grades": [10], "academicYearId": w.year}, headers=w.p).json()
    sheet = w.c.put(f"/api/v1/exams/{exam['id']}/datesheet", json={"papers": [
        {"grade": 10, "subjectId": w.sci10, "date": "2026-06-08", "startTime": "09:00", "endTime": "09:45"}]},
        headers=w.p)
    assert sheet.status_code == 200, sheet.text
    assert w.c.post(f"/api/v1/exams/{exam['id']}/publish", headers=w.p).status_code == 200
    day = {x["period"]: x["note"] for x in _day(w, "2026-06-08", w.b10)}
    assert day == {1: "Exam window: Unit test 1", 2: "Unit test 1: Science paper, 09:00-09:45"}

    r = w.c.delete(f"{BASE}/academic-years/{w.year}/holidays/{window['id']}", headers=w.p)
    assert r.status_code == 200, r.text
    assert [(x["period"], x["kind"]) for x in _day(w, "2026-06-08", w.b10)] == [(1, "regular"), (2, "exam")]
    assert _dates(w, book, w.a10) == MONDAYS, "10-A's Science is before the paper"
    assert _dates(w, book, w.b10) == [MON] + MONDAYS[2:] + ["2026-07-13"], "10-B's is during it"


def test_a_lesson_cannot_be_moved_into_its_class_exam_window(w):
    book = _plan(w, w.a10)
    _add(w, date="2026-06-09", endDate="2026-06-10", label="Unit test 1", kind="exam_window", grades=[10])
    lesson = next(l for l in w.store.scheduled_lessons_for_book(w.year, book, w.a10) if l.date == "2026-06-15")
    r = w.c.post(f"{BASE}/scheduled-lessons/{lesson.id}/reschedule",
                 json={"newDate": "2026-06-09", "reason": "swap"}, headers=w.p)
    assert r.status_code == 422 and "exam window" in r.json()["detail"], r.text
    ok = w.c.post(f"{BASE}/scheduled-lessons/{lesson.id}/reschedule",
                  json={"newDate": "2026-06-11", "reason": "swap"}, headers=w.p)
    assert ok.status_code == 200, ok.text


def test_an_exam_window_names_classes_of_this_year(w):
    r = _add(w, date="2026-06-08", label="Board", kind="exam_window", grades=[12])
    assert r.status_code == 422 and "no class 12" in r.json()["detail"]
    every = _add(w, date="2026-06-09", label="Half-yearly", kind="exam_window")
    assert every.status_code == 200 and every.json()["grades"] is None


# ---------------------------------------------------------------- compensatory working days


def test_a_compensatory_saturday_runs_a_weekdays_timetable_everywhere(w):
    book = _plan(w, w.a10)
    r = w.c.put(f"{BASE}/academic-years/{w.year}/calendar",
                json={"weeklyOffDays": ["sunday"], "alternateSaturdayRule": "second_fourth"}, headers=w.p)
    assert r.status_code == 200, r.text
    before = w.c.get(f"{BASE}/academic-years/{w.year}/working-days", headers=w.p).json()
    assert SECOND_SATURDAY not in before["dates"] and _day(w, SECOND_SATURDAY, w.b10) == []

    r = _add(w, date=SECOND_SATURDAY, label="Makes up the rain day", kind="working_day", timetableWeekday=0)
    assert r.status_code == 200, r.text
    after = w.c.get(f"{BASE}/academic-years/{w.year}/working-days", headers=w.p).json()
    assert SECOND_SATURDAY in after["dates"]
    assert after["workingDays"] == before["workingDays"] + 1 and after["compensatoryCount"] == 1

    # The day runs Monday's timetable.
    assert [(x["period"], x["subjectName"]) for x in _day(w, SECOND_SATURDAY, w.b10)] == [
        (1, "Maths"), (2, "Science")]
    assert {x["period"] for x in w.c.get(f"{BASE}/my-day", params={"date": SECOND_SATURDAY},
                                         headers=w.stu).json()} == {1, 2}
    # The plan teaches on it: the next lesson comes forward.
    assert _dates(w, book, w.a10) == ["2026-06-01", "2026-06-08", SECOND_SATURDAY, "2026-06-15", "2026-06-22",
                                      "2026-06-29"]
    # Cover follows it.
    leave = _apply(w, "ana", startDate=SECOND_SATURDAY, endDate=SECOND_SATURDAY).json()
    assert {(sec.id, p) for _, sec, p, _ in w.store.affected_periods(w.store.get_leave(leave["id"]))} == {
        (w.a10, 1), (w.b10, 2)}
    # The feed holds that day's periods once, and the apps list the day.
    ics = _ics(w, "ana")
    assert "DTSTART;TZID=Asia/Kolkata:20260613T080000" in ics
    assert "Working day: Makes up the rain day (Monday's timetable)" in ics
    assert any(i["kind"] == "working_day" and i["date"] == SECOND_SATURDAY for i in _calendar(w, w.stu))

    # Taken back off the calendar, the plan returns to Mondays.
    holiday = next(h for h in w.c.get(f"{BASE}/academic-years/{w.year}/holidays", headers=w.p).json()
                   if h["kind"] == "working_day")
    assert holiday["timetableWeekday"] == 0
    assert w.c.delete(f"{BASE}/academic-years/{w.year}/holidays/{holiday['id']}", headers=w.p).status_code == 200
    assert _dates(w, book, w.a10) == MONDAYS
    assert _day(w, SECOND_SATURDAY, w.b10) == []


def test_a_compensatory_day_must_be_an_off_day_with_a_timetable(w):
    w.c.put(f"{BASE}/academic-years/{w.year}/calendar",
            json={"weeklyOffDays": ["sunday"], "alternateSaturdayRule": "second_fourth"}, headers=w.p)
    already = _add(w, date="2026-06-06", label="x", kind="working_day", timetableWeekday=0)
    assert already.status_code == 422 and "already a working day" in already.json()["detail"]
    assert _add(w, date=SECOND_SATURDAY, label="x", kind="working_day").status_code == 422
    sunday = _add(w, date=SECOND_SATURDAY, label="x", kind="working_day", timetableWeekday=6)
    assert sunday.status_code == 422 and "weekly off" in sunday.json()["detail"]
    span = _add(w, date=SECOND_SATURDAY, endDate="2026-06-14", label="x", kind="working_day", timetableWeekday=0)
    assert span.status_code == 422
    assert _add(w, date="2026-06-14", label="Sunday class", kind="working_day", timetableWeekday=0).status_code == 200
    assert _add(w, date="2026-06-14", label="again", kind="working_day", timetableWeekday=1).status_code == 409


YEAR_END_MONDAYS = ["2027-02-22", "2027-03-01", "2027-03-08", "2027-03-15", "2027-03-22", "2027-03-29"]


def _plan_at_year_end(w) -> str:
    """10-B's six Science lessons on the year's last six Mondays (the year ends 2027-03-31)."""
    book = _science_book(w)
    scheduling.schedule_book(w.store, school_id="school_1", academic_year_id=w.year, book_id=book,
                             periods_per_week=1, from_date="2027-02-22", section_id=w.b10)
    assert _dates(w, book, w.b10) == YEAR_END_MONDAYS
    return book


def test_a_half_day_that_pushes_a_lesson_past_the_year_end_says_so_and_gives_it_back(w):
    """Lessons pushed past the year's last period were dropped without a word
    (2e6326a audit) and stayed dayless when the day was removed."""
    book = _plan_at_year_end(w)
    r = _add(w, date="2027-03-01", label="Sports day", kind="half_day", lastPeriod=1)
    assert r.status_code == 200, r.text
    assert r.json()["lessonsDropped"] == 1
    assert _dates(w, book, w.b10) == [d for d in YEAR_END_MONDAYS if d != "2027-03-01"]
    gone = w.c.delete(f"{BASE}/academic-years/{w.year}/holidays/{r.json()['id']}", headers=w.p)
    assert gone.status_code == 200, gone.text
    assert gone.json()["lessonsDropped"] == 0
    assert _dates(w, book, w.b10) == YEAR_END_MONDAYS, "the dropped lesson has its day back"


def test_removing_a_holiday_lays_its_lessons_back_and_restores_the_dropped(w):
    book = _plan_at_year_end(w)
    r = _add(w, date="2027-03-01", label="Holi", kind="public")
    assert r.status_code == 200, r.text
    assert r.json()["lessonsDropped"] == 1
    assert len(_dates(w, book, w.b10)) == 5
    gone = w.c.delete(f"{BASE}/academic-years/{w.year}/holidays/{r.json()['id']}", headers=w.p)
    assert gone.status_code == 200, gone.text
    assert _dates(w, book, w.b10) == YEAR_END_MONDAYS


def test_a_one_day_holiday_moves_a_weekly_plan_one_week(w):
    """The push gave up the next teaching day as well as the holiday, which the
    calendar had already taken off: a Monday holiday moved a weekly plan two
    weeks on (found 2026-10-04)."""
    book = _plan(w, w.b10)
    r = _add(w, date="2026-06-08", label="Holi", kind="public")
    assert r.status_code == 200, r.text
    assert _dates(w, book, w.b10) == [MON] + MONDAYS[2:] + ["2026-07-13"]
