"""PUSH / ADJUST (curriculum/scheduling.py, §14) never falsify the teaching
record and never produce a schedule the school's own data contradicts.

The product audit (2026-09-21, reproduced twice with real data) found four
integrity defects in the reschedule endpoints:

- PUSH moved lessons already marked completed or skipped: a lesson marked
  completed on 2026-09-21 was moved to 2026-09-22 with its status still
  'completed' -- the record now claims it was taught on a day it wasn't.
- PUSH ignored the subject's SubjectTimetableSlot rows (initial scheduling
  honours them), so Mathematics lessons were pushed onto Saturdays, a day
  the timetable does not include.
- PUSH made the caller re-supply periodsPerWeek and ignored the persisted
  SubjectPeriodAllocation, so a push without it was a 422.
- ADJUST did no clash check: a lesson moved onto 2026-09-24, which already
  held one, double-booked the day.

These run through the real HTTP routes as an authenticated principal (Task
101 made curriculum reads auth-required; the reschedule writes always were).
"""
from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest

from test_assessment_routes_auth import _boot_client, _register

BASE = "/api/v1/curriculum"
PRINCIPAL_KEY = "test-bootstrap-key"


def _bearer(user: dict) -> dict:
    return {"Authorization": f"Bearer {user['token']}"}


def _seed_book(store, *, school_id: str, periods_per_week: int, timetable=None,
               allocation=None) -> SimpleNamespace:
    """One Mathematics book (two units, 4 + 3 subtopics) with a real
    calendar (Sunday off, so Saturday IS a working day -- the case the audit
    caught), real teaching-time estimates and a real initial schedule.
    `timetable` is a list of (day_of_week, period_number) SubjectTimetableSlot
    rows; `allocation` a stored SubjectPeriodAllocation.periods_per_week."""
    from academicos.curriculum import calendar as calendar_mod
    from academicos.curriculum import scheduling as scheduling_mod

    board = store.create_board(name="CBSE", code="CBSE")
    year = store.create_academic_year(school_id=school_id, label="2026-27",
                                      start_date="2026-06-01", end_date="2027-03-31")
    grade = store.create_grade(academic_year_id=year.id, number=10)
    subject = store.create_subject(grade_id=grade.id, name="Mathematics")
    book = store.create_book(subject_id=subject.id, board_id=board.id, title="Maths")
    for u_seq, (prefix, n) in enumerate((("A", 4), ("B", 3))):
        unit = store.create_unit(canonical_id=f"u:{prefix}", book_id=book.id, unit_no=prefix,
                                 name=f"Unit {prefix}", marks=20, seq=u_seq)
        chapter = store.create_chapter(canonical_id=f"c:{prefix}", unit_id=unit.id,
                                       name=f"Chapter {prefix}", seq=u_seq)
        topic = store.create_topic(canonical_id=f"t:{prefix}", chapter_id=chapter.id,
                                   name=f"Topic {prefix}", seq=0)
        for i in range(n):
            store.create_subtopic(canonical_id=f"st:{prefix}:{i}", topic_id=topic.id,
                                  name=f"Subtopic {prefix}{i}", seq=i)
    store.create_calendar(academic_year_id=year.id, weekly_off_days=["sunday"],
                          alternate_saturday_rule="none")
    store.create_period_configuration(school_id=school_id, academic_year_id=year.id,
                                      period_minutes=40)
    for day_of_week, period_number in timetable or []:
        store.add_timetable_slot(school_id=school_id, academic_year_id=year.id, subject="Mathematics",
                                 day_of_week=day_of_week, period_number=period_number)
    if allocation is not None:
        store.set_subject_period_allocation(school_id=school_id, academic_year_id=year.id,
                                            subject="Mathematics", periods_per_week=allocation)
    calendar_mod.compute_teaching_time_estimates(
        store, academic_year_id=year.id, book_id=book.id, periods_per_week=periods_per_week)
    scheduling_mod.schedule_book(store, school_id=school_id, academic_year_id=year.id,
                                 book_id=book.id, periods_per_week=periods_per_week)
    lessons = store.scheduled_lessons_for_book(year.id, book.id)
    assert len(lessons) >= 10, "fixture needs a real multi-week schedule to push"
    return SimpleNamespace(year=year.id, book=book.id, lessons=lessons)


@pytest.fixture
def principal_world(tmp_path, monkeypatch):
    with _boot_client(tmp_path, monkeypatch) as client:
        principal = _register(client, "school_1", "p1@example.com", "Priya Principal",
                              principal_key=PRINCIPAL_KEY)
        assert principal["user"]["role"] == "principal"
        from academicos.curriculum import routes as curriculum_routes
        yield SimpleNamespace(client=client, auth=_bearer(principal),
                              store=curriculum_routes._require())


def _push(w, book: SimpleNamespace, from_date: str, periods_per_week=None):
    body = {"fromDate": from_date, "reason": "Unplanned closure"}
    if periods_per_week is not None:
        body["periodsPerWeek"] = periods_per_week
    return w.client.post(f"{BASE}/books/{book.book}/schedule/push",
                         params={"academic_year_id": book.year}, json=body, headers=w.auth)


def test_push_never_moves_a_completed_or_skipped_lesson(principal_world):
    w = principal_world
    book = _seed_book(w.store, school_id="school_1", periods_per_week=6)
    from_date = book.lessons[3].date
    completed, skipped = book.lessons[4], book.lessons[6]
    w.store.mark_lesson(completed.id, status="completed", note=None, completed_by="t1")
    w.store.mark_lesson(skipped.id, status="skipped", note="assembly", completed_by="t1")

    r = _push(w, book, from_date, periods_per_week=6)
    assert r.status_code == 200, r.text
    moved_ids = {m["lessonId"] for m in r.json()["reschedules"]}
    assert completed.id not in moved_ids and skipped.id not in moved_ids

    after = {l.id: l for l in w.store.scheduled_lessons_for_book(book.year, book.book)}
    assert (after[completed.id].date, after[completed.id].status) == (completed.date, "completed")
    assert (after[skipped.id].date, after[skipped.id].status) == (skipped.date, "skipped")
    # The still-to-teach lessons really moved, and none of them was pushed
    # onto a day a taught lesson already occupies.
    assert r.json()["lessonsPushed"] > 0
    kept_dates = {completed.date, skipped.date}
    assert not any(after[i].date in kept_dates for i in moved_ids)


def test_push_honours_a_mon_to_fri_timetable(principal_world):
    """Six Mathematics periods a week, all Monday-Friday (two on Monday).
    Saturday is a working day in this calendar, so the old "first N working
    days of the week" fallback put the 6th period on Saturday -- exactly
    the audit's finding. The timetable says Mathematics never meets then."""
    w = principal_world
    mon_to_fri = [(0, 1), (0, 2), (1, 1), (2, 1), (3, 1), (4, 1)]
    book = _seed_book(w.store, school_id="school_1", periods_per_week=6, timetable=mon_to_fri)
    assert all(date.fromisoformat(l.date).weekday() < 5 for l in book.lessons)

    r = _push(w, book, book.lessons[2].date, periods_per_week=6)
    assert r.status_code == 200, r.text
    assert r.json()["lessonsPushed"] > 0
    for m in r.json()["reschedules"]:
        weekday = date.fromisoformat(m["newDate"]).weekday()
        assert weekday < 5, f"lesson pushed onto {m['newDate']} (weekday {weekday})"


def test_push_without_periods_per_week_uses_the_stored_allocation(principal_world):
    """Stored allocation = 3 periods/week, no timetable. A push that omits
    periodsPerWeek must keep that cadence: at most 3 lessons in any ISO week,
    on the first 3 working days (Mon/Tue/Wed), the same rule schedule_book
    used for the original schedule."""
    w = principal_world
    book = _seed_book(w.store, school_id="school_1", periods_per_week=3, allocation=3)

    r = _push(w, book, book.lessons[2].date)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["periodsPerWeek"] == 3
    assert body["lessonsPushed"] > 0

    per_week: dict[tuple[int, int], int] = {}
    for l in w.store.scheduled_lessons_for_book(book.year, book.book):
        d = date.fromisoformat(l.date)
        assert d.weekday() in (0, 1, 2), f"{l.date} breaks the stored 3-periods/week cadence"
        key = d.isocalendar()[:2]
        per_week[key] = per_week.get(key, 0) + 1
    assert max(per_week.values()) <= 3


def test_push_with_no_periods_per_week_and_no_allocation_is_refused(principal_world):
    w = principal_world
    book = _seed_book(w.store, school_id="school_1", periods_per_week=6)
    r = _push(w, book, book.lessons[2].date)
    assert r.status_code == 422
    assert "allocation" in r.text.lower()


def test_adjust_onto_an_occupied_date_is_a_409(principal_world):
    w = principal_world
    book = _seed_book(w.store, school_id="school_1", periods_per_week=6)
    lesson, occupant = book.lessons[0], book.lessons[3]

    r = w.client.post(f"{BASE}/scheduled-lessons/{lesson.id}/reschedule",
                      json={"newDate": occupant.date, "reason": "swap"}, headers=w.auth)
    assert r.status_code == 409, r.text
    assert occupant.date in r.json()["detail"]
    assert w.store.get_scheduled_lesson(lesson.id).date == lesson.date


def test_adjust_onto_a_free_working_day_is_a_200(principal_world):
    from academicos.curriculum.calendar import working_days_for_year

    w = principal_world
    # 5 periods/week fills Mon-Fri; teaching-time estimates spread the book
    # over the whole year, so Saturdays are the working days left free.
    book = _seed_book(w.store, school_id="school_1", periods_per_week=5)
    occupied = {l.date for l in book.lessons}
    free = next(d for d in working_days_for_year(w.store, book.year).dates if d not in occupied)
    lesson = book.lessons[0]

    r = w.client.post(f"{BASE}/scheduled-lessons/{lesson.id}/reschedule",
                      json={"newDate": free, "reason": "moved"}, headers=w.auth)
    assert r.status_code == 200, r.text
    assert r.json()["date"] == free


def test_adjust_allows_as_many_lessons_as_the_timetable_has_periods_that_day(principal_world):
    """Two Mathematics periods on Monday means a Monday can hold two lessons;
    a third is the clash."""
    w = principal_world
    book = _seed_book(w.store, school_id="school_1", periods_per_week=6,
                      timetable=[(0, 1), (0, 2), (1, 1), (2, 1), (3, 1), (4, 1)])
    monday = next(l for l in book.lessons if date.fromisoformat(l.date).weekday() == 0)
    movers = [l for l in book.lessons if l.date != monday.date][:2]

    first = w.client.post(f"{BASE}/scheduled-lessons/{movers[0].id}/reschedule",
                          json={"newDate": monday.date, "reason": "double period"}, headers=w.auth)
    assert first.status_code == 200, first.text
    second = w.client.post(f"{BASE}/scheduled-lessons/{movers[1].id}/reschedule",
                           json={"newDate": monday.date, "reason": "triple?"}, headers=w.auth)
    assert second.status_code == 409, second.text


def test_push_with_a_timetable_needs_no_allocation(principal_world):
    """With SubjectTimetableSlot rows the timetable alone decides the days
    (_subject_teaching_days ignores periods_per_week when weekday_slots is
    set), so demanding an allocation or periodsPerWeek made the admin type a
    number that changed nothing -- and the response echoed it back as the
    cadence. The review reproduced the 422 with a Mon-Fri timetable and no
    allocation. The reported periodsPerWeek is the timetable's slot count."""
    w = principal_world
    mon_to_fri = [(0, 1), (0, 2), (1, 1), (2, 1), (3, 1), (4, 1)]
    book = _seed_book(w.store, school_id="school_1", periods_per_week=6, timetable=mon_to_fri)

    r = _push(w, book, book.lessons[2].date)
    assert r.status_code == 200, r.text
    assert r.json()["lessonsPushed"] > 0
    assert r.json()["periodsPerWeek"] == len(mon_to_fri)
    assert all(date.fromisoformat(m["newDate"]).weekday() < 5 for m in r.json()["reschedules"])

    # An override the timetable makes irrelevant is not echoed as the cadence.
    r = _push(w, book, book.lessons[2].date, periods_per_week=2)
    assert r.status_code == 200, r.text
    assert r.json()["periodsPerWeek"] == len(mon_to_fri)


@pytest.mark.parametrize("status", ["completed", "skipped"])
def test_adjust_never_moves_a_completed_or_skipped_lesson(principal_world, status):
    """ADJUST is the other way to re-date a lesson; the review moved a
    completed lesson to a free working day through this route and got a 200
    with the new date and status still 'completed' -- the same falsified
    record the PUSH fix closed. It is a 409: it conflicts with the lesson's
    existing state, and nothing about the request itself is malformed."""
    from academicos.curriculum.calendar import working_days_for_year

    w = principal_world
    book = _seed_book(w.store, school_id="school_1", periods_per_week=5)
    occupied = {l.date for l in book.lessons}
    free = next(d for d in working_days_for_year(w.store, book.year).dates if d not in occupied)
    lesson = book.lessons[0]
    w.store.mark_lesson(lesson.id, status=status, note=None, completed_by="t1")

    r = w.client.post(f"{BASE}/scheduled-lessons/{lesson.id}/reschedule",
                      json={"newDate": free, "reason": "moved"}, headers=w.auth)
    assert r.status_code == 409, r.text
    assert status in r.json()["detail"]
    after = w.store.get_scheduled_lesson(lesson.id)
    assert (after.date, after.status) == (lesson.date, status)
