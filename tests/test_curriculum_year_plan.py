"""The year plan fits the year, keeps double periods, and reordering works.

The product audit (2026-09-21, reproduced twice on school_1's real data):

- calendar.py sized the teaching-time budget as periods_per_week x calendar
  weeks, ignoring holidays and alternate Saturdays, then round()-ed each
  subtopic on its own: Social Science's stored estimates summed to 323
  periods against a 288 budget, while the scheduler had 258 real slots. 49
  of 404 real subtopics ended the year with no date, and the route said 200.
- scheduling.py reduced a timetable to a set of weekdays, so a Monday double
  period was lost: Mathematics' 6 periods a week became at most 5 lessons.
- A force regenerate deleted every completion mark.
- set_sequence updated one row and never shifted its siblings: moving
  'Carbon and its Compounds' to seq 0 left two chapters of that unit at 0.

And from Task 102's review of the same code:

- a lesson PUSH could not place stayed 'scheduled' on its old date while the
  previous lesson was moved onto that same date (a double-booked day);
- the cadence a book was scheduled with was never saved, so PUSH fell back
  to the subject allocation and could silently reschedule at another cadence.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from types import SimpleNamespace

import pytest

from academicos.assessment.audit_log import AuditLog
from academicos.curriculum import calendar as calendar_mod
from academicos.curriculum import scheduling as scheduling_mod
from academicos.curriculum.store import CurriculumStore

from _auth_helpers import register_invited

BASE = "/api/v1/curriculum"
PRINCIPAL_KEY = "test-bootstrap-key"

# Monday double period, one period Tuesday-Friday: 6 a week, 5 weekdays.
MON_DOUBLE = [(0, 1), (0, 2), (1, 1), (2, 1), (3, 1), (4, 1)]


@pytest.fixture
def store(tmp_path):
    s = CurriculumStore(tmp_path / "curriculum.sqlite")
    yield s
    s.close()


@pytest.fixture
def audit_log(tmp_path):
    return AuditLog(tmp_path / "audit.sqlite")


def _seed(store, *, units=((30, 7), (20, 5), (30, 9)), start="2026-06-01", end="2027-03-31",
          weekly_off=("sunday",), saturday_rule="second_fourth", holidays=(), timetable=(),
          subject="Mathematics", school_id="school_1"):
    """A book whose units carry (marks, n_subtopics), each unit one chapter
    per 3 subtopics, on a real calendar with real holidays."""
    board = store.create_board(name="CBSE", code="CBSE")
    year = store.create_academic_year(school_id=school_id, label="2026-27",
                                      start_date=start, end_date=end)
    grade = store.create_grade(academic_year_id=year.id, number=10)
    subj = store.create_subject(grade_id=grade.id, name=subject)
    book = store.create_book(subject_id=subj.id, board_id=board.id, title=subject)
    chapters = []
    for u_idx, (marks, n) in enumerate(units):
        unit = store.create_unit(canonical_id=f"u:{u_idx}", book_id=book.id, unit_no=str(u_idx),
                                 name=f"Unit {u_idx}", marks=marks, seq=u_idx)
        for c_idx in range(0, n, 3):
            chapter = store.create_chapter(canonical_id=f"c:{u_idx}:{c_idx}", unit_id=unit.id,
                                           name=f"Chapter {u_idx}.{c_idx // 3}", seq=c_idx // 3)
            chapters.append(chapter)
            topic = store.create_topic(canonical_id=f"t:{u_idx}:{c_idx}", chapter_id=chapter.id,
                                       name=f"Topic {u_idx}.{c_idx // 3}", seq=0)
            for s_idx in range(c_idx, min(c_idx + 3, n)):
                store.create_subtopic(canonical_id=f"st:{u_idx}:{s_idx}", topic_id=topic.id,
                                      name=f"Subtopic {u_idx}.{s_idx}", seq=s_idx - c_idx)
    cal = store.create_calendar(academic_year_id=year.id, weekly_off_days=list(weekly_off),
                                alternate_saturday_rule=saturday_rule)
    for h_date, h_end in holidays:
        store.add_holiday(calendar_id=cal.id, date=h_date, end_date=h_end, label="Break",
                          kind="school")
    store.create_period_configuration(school_id=school_id, academic_year_id=year.id,
                                      period_minutes=40)
    for day_of_week, period_number in timetable:
        store.add_timetable_slot(school_id=school_id, academic_year_id=year.id, subject=subject,
                                 day_of_week=day_of_week, period_number=period_number)
    return SimpleNamespace(year=year.id, book=book.id, calendar=cal.id, chapters=chapters)


def _all_subtopic_ids(store, book_id):
    return [st.id for u in store.units_for_book(book_id) for c in store.chapters_for_unit(u.id)
            for t in store.topics_for_chapter(c.id) for st in store.subtopics_for_topic(t.id)]


def _first_n_days_per_week(working_dates, n):
    by_week = defaultdict(list)
    for d in working_dates:
        by_week[date.fromisoformat(d).isocalendar()[:2]].append(d)
    return [d for key in sorted(by_week) for d in sorted(by_week[key])[:n]]


HOLIDAYS = (("2026-08-15", None), ("2026-10-12", "2026-10-24"), ("2026-12-24", "2027-01-02"),
            ("2027-01-26", None))


# --------------------------------------------------------------------- #
# 1-2. The budget is the real number of teaching periods, distributed exactly
# --------------------------------------------------------------------- #

def test_estimates_are_budgeted_against_real_working_days(store):
    b = _seed(store, holidays=HOLIDAYS)
    working = calendar_mod.working_days_for_year(store, b.year).dates
    real_periods = len(_first_n_days_per_week(working, 6))

    result = calendar_mod.compute_teaching_time_estimates(
        store, academic_year_id=b.year, book_id=b.book, periods_per_week=6)

    # 6 x 44 calendar weeks = 264 was the old budget; alternate Saturdays and
    # the breaks take real periods away.
    assert real_periods < 6 * result.calendar_weeks
    assert result.total_subject_periods == real_periods
    stored = [store.teaching_time_estimate_for_subtopic(s, b.year) for s in _all_subtopic_ids(store, b.book)]
    assert all(e is not None and e.estimated_periods >= 1 for e in stored)
    assert sum(e.estimated_periods for e in stored) == real_periods
    assert result.fits_in_year and result.periods_short == 0


def test_rounding_never_overflows_the_budget(store):
    """21 subtopics over a budget that divides unevenly: per-subtopic
    round() rounded most of them up (the 323-over-288 overflow); the
    largest-remainder split lands on the budget exactly."""
    b = _seed(store, units=((13, 7), (11, 5), (17, 9)), start="2026-06-01", end="2026-08-31",
              saturday_rule="none")
    result = calendar_mod.compute_teaching_time_estimates(
        store, academic_year_id=b.year, book_id=b.book, periods_per_week=5)
    periods = [store.teaching_time_estimate_for_subtopic(s, b.year).estimated_periods
               for s in _all_subtopic_ids(store, b.book)]
    assert sum(periods) == result.total_subject_periods
    minutes = [store.teaching_time_estimate_for_subtopic(s, b.year).estimated_minutes
               for s in _all_subtopic_ids(store, b.book)]
    assert sum(minutes) == result.total_instructional_minutes


def test_estimate_budget_follows_the_timetable_double_period(store):
    b = _seed(store, timetable=MON_DOUBLE, holidays=HOLIDAYS)
    working = calendar_mod.working_days_for_year(store, b.year).dates
    weekday_periods = Counter(dow for dow, _ in MON_DOUBLE)
    real_periods = sum(weekday_periods[date.fromisoformat(d).weekday()] for d in working)

    result = calendar_mod.compute_teaching_time_estimates(
        store, academic_year_id=b.year, book_id=b.book, periods_per_week=6)
    assert result.total_subject_periods == real_periods


def test_recompute_brings_earlier_estimates_back_inside_a_smaller_year(store):
    """Estimates are kept on a re-run, so ones computed before a break was
    entered (or by the old periods x weeks formula, as school_1's are)
    stay over the budget. recompute=True replaces the computation's own
    estimates and still leaves an admin's hand-set number alone."""
    b = _seed(store)
    ids = _all_subtopic_ids(store, b.book)
    store.create_teaching_time_estimate(subtopic_id=ids[0], academic_year_id=b.year,
                                        estimated_minutes=200, estimated_periods=5)
    calendar_mod.compute_teaching_time_estimates(
        store, academic_year_id=b.year, book_id=b.book, periods_per_week=6)
    for h_date, h_end in HOLIDAYS:
        store.add_holiday(calendar_id=b.calendar, date=h_date, end_date=h_end, label="Break",
                          kind="school")

    def stored_sum():
        return sum(store.teaching_time_estimate_for_subtopic(s, b.year).estimated_periods for s in ids)

    kept = calendar_mod.compute_teaching_time_estimates(
        store, academic_year_id=b.year, book_id=b.book, periods_per_week=6)
    assert stored_sum() > kept.total_subject_periods     # the breaks took periods away

    redone = calendar_mod.compute_teaching_time_estimates(
        store, academic_year_id=b.year, book_id=b.book, periods_per_week=6, recompute=True)
    assert stored_sum() == redone.total_subject_periods and redone.fits_in_year
    assert store.teaching_time_estimate_for_subtopic(ids[0], b.year).estimated_periods == 5


# --------------------------------------------------------------------- #
# 3. Double periods are honoured
# --------------------------------------------------------------------- #

def test_a_monday_double_gets_two_lessons_and_a_week_yields_six(store):
    b = _seed(store, timetable=MON_DOUBLE, saturday_rule="none")
    calendar_mod.compute_teaching_time_estimates(
        store, academic_year_id=b.year, book_id=b.book, periods_per_week=6)
    result = scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=b.year,
                                          book_id=b.book, periods_per_week=6)
    lessons = store.scheduled_lessons_for_book(b.year, b.book)
    per_day = Counter(l.date for l in lessons)
    mondays = [d for d in per_day if date.fromisoformat(d).weekday() == 0]
    assert mondays and all(per_day[d] == 2 for d in mondays)
    assert all(n == 1 for d, n in per_day.items() if date.fromisoformat(d).weekday() != 0)
    # A full Mon-Fri week (no holiday in this calendar) holds 6 lessons.
    per_week = Counter(date.fromisoformat(l.date).isocalendar()[:2] for l in lessons)
    assert per_week[date(2026, 6, 8).isocalendar()[:2]] == 6
    assert result.periods_per_week == 6
    assert result.lessons_created == result.teaching_periods_available


# --------------------------------------------------------------------- #
# 4. Every subtopic gets a date, or the shortfall is loud
# --------------------------------------------------------------------- #

def test_a_syllabus_that_fits_dates_every_subtopic(store):
    b = _seed(store, holidays=HOLIDAYS, timetable=MON_DOUBLE)
    calendar_mod.compute_teaching_time_estimates(
        store, academic_year_id=b.year, book_id=b.book, periods_per_week=6)
    result = scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=b.year,
                                          book_id=b.book, periods_per_week=6)
    assert result.subtopics_unscheduled == ()
    assert result.subtopics_partially_scheduled == ()
    assert result.all_subtopics_scheduled is True
    assert result.warning is None
    dated = {l.subtopic_id for l in store.scheduled_lessons_for_book(b.year, b.book)}
    assert dated == set(_all_subtopic_ids(store, b.book))


def test_a_syllabus_bigger_than_the_year_is_reported(store):
    """Two weeks, 21 subtopics, one period a day: 12 periods cannot hold 21
    subtopics. Each subtopic still needs at least one period, so the
    estimate says how many periods short the year is, and the schedule says
    how many subtopics have no date."""
    b = _seed(store, start="2026-06-01", end="2026-06-14", saturday_rule="none")
    est = calendar_mod.compute_teaching_time_estimates(
        store, academic_year_id=b.year, book_id=b.book, periods_per_week=6)
    assert est.total_subject_periods == 12
    assert est.fits_in_year is False and est.periods_short == 21 - 12

    result = scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=b.year,
                                          book_id=b.book, periods_per_week=6)
    assert len(result.subtopics_unscheduled) == 21 - 12
    assert result.all_subtopics_scheduled is False
    assert "9 of 21 subtopics" in result.warning


# --------------------------------------------------------------------- #
# 5. Force regenerate preserves completion marks
# --------------------------------------------------------------------- #

def test_force_regenerate_keeps_completed_and_skipped_lessons(store):
    b = _seed(store, holidays=HOLIDAYS)
    calendar_mod.compute_teaching_time_estimates(
        store, academic_year_id=b.year, book_id=b.book, periods_per_week=6)
    scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=b.year,
                                 book_id=b.book, periods_per_week=6)
    lessons = store.scheduled_lessons_for_book(b.year, b.book)
    store.mark_lesson(lessons[0].id, status="completed", note="done well", completed_by="t1")
    store.mark_lesson(lessons[1].id, status="skipped", note="assembly", completed_by="t1")
    store.mark_lesson(lessons[2].id, status="completed", note=None, completed_by="t1")
    kept = {l.id: store.get_scheduled_lesson(l.id) for l in lessons[:3]}

    result = scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=b.year,
                                          book_id=b.book, periods_per_week=6, force=True)

    after = store.scheduled_lessons_for_book(b.year, b.book)
    by_id = {l.id: l for l in after}
    for lesson_id, before in kept.items():
        assert by_id[lesson_id] == before     # every field, including the note and who marked it
    assert result.lessons_kept == 3
    # Only what is still to be taught was replanned, around the recorded ones:
    # the three kept lessons hold the first three periods, nothing shares them.
    replanned = [l for l in after if l.id not in kept]
    assert replanned and all(l.status == "scheduled" for l in replanned)
    assert not {l.date for l in replanned} & {l.date for l in kept.values()}
    # Each subtopic still gets exactly its estimated periods of teaching,
    # counting the completed ones; a skipped lesson taught nothing, so its
    # period is planned again.
    per_subtopic = Counter(l.subtopic_id for l in after if l.status != "skipped")
    # The estimates fill the year exactly, so the one skipped period leaves the
    # plan one period short -- and the result says so rather than hiding it.
    short = sum(store.teaching_time_estimate_for_subtopic(st, b.year).estimated_periods
                - per_subtopic[st] for st in _all_subtopic_ids(store, b.book))
    assert short == 1
    assert not result.all_subtopics_scheduled and result.warning
    for st in _all_subtopic_ids(store, b.book):
        assert per_subtopic[st] <= store.teaching_time_estimate_for_subtopic(st, b.year).estimated_periods


def test_a_skip_late_in_the_year_does_not_throw_away_the_periods_before_it(store):
    """A skip may be marked on a future lesson; a regenerate after one must
    still use every free period before it. Until the review of 2026-09-22
    the replan started after the latest recorded lesson, so one skip in
    March pushed the whole remaining syllabus past March and left subtopics
    undated in a year with room for them."""
    b = _seed(store, holidays=HOLIDAYS)
    calendar_mod.compute_teaching_time_estimates(
        store, academic_year_id=b.year, book_id=b.book, periods_per_week=6)
    scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=b.year,
                                 book_id=b.book, periods_per_week=6)
    lessons = store.scheduled_lessons_for_book(b.year, b.book)
    late = next(l for l in lessons if l.date >= "2027-03-01")
    store.mark_lesson(late.id, status="skipped", note="exam prep", completed_by="t1")

    result = scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=b.year,
                                          book_id=b.book, periods_per_week=6, force=True)

    # The skipped period taught nothing and the year has no spare period, so
    # exactly one subtopic is one period short, and the warning says so.
    assert not result.all_subtopics_scheduled and result.warning
    assert result.subtopics_unscheduled == () and len(result.subtopics_partially_scheduled) == 1
    after = store.scheduled_lessons_for_book(b.year, b.book)
    assert store.get_scheduled_lesson(late.id).status == "skipped"
    replanned = [l for l in after if l.id != late.id]
    assert min(l.date for l in replanned) == lessons[0].date   # the year's first period is used
    # The skipped lesson keeps its own period: no replanned lesson shares its day
    # (no timetable here, so each working day is one period).
    assert late.date not in {l.date for l in replanned}
    assert len({l.date for l in after}) == len(after)
    per_subtopic = Counter(l.subtopic_id for l in after if l.status != "skipped")
    assert sum(store.teaching_time_estimate_for_subtopic(st, b.year).estimated_periods
               - per_subtopic[st] for st in _all_subtopic_ids(store, b.book)) == 1


# --------------------------------------------------------------------- #
# 6. Reordering shifts siblings atomically
# --------------------------------------------------------------------- #

def test_moving_a_chapter_to_seq_0_renumbers_its_siblings(store):
    b = _seed(store, units=((80, 9),), holidays=HOLIDAYS)   # one unit, three chapters
    unit_id = b.chapters[0].unit_id
    first, second, third = store.chapters_for_unit(unit_id)

    store.set_sequence("chapter", third.id, 0)

    ordered = store.chapters_for_unit(unit_id)
    assert [c.id for c in ordered] == [third.id, first.id, second.id]
    assert [c.seq for c in ordered] == [0, 1, 2]

    calendar_mod.compute_teaching_time_estimates(
        store, academic_year_id=b.year, book_id=b.book, periods_per_week=6)
    scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=b.year,
                                 book_id=b.book, periods_per_week=6)
    first_lesson = store.scheduled_lessons_for_book(b.year, b.book)[0]
    third_subtopics = {s.id for t in store.topics_for_chapter(third.id)
                       for s in store.subtopics_for_topic(t.id)}
    assert first_lesson.subtopic_id in third_subtopics


def test_reorder_repairs_duplicate_seqs_and_clamps_past_the_end(store):
    """The live unit already had two chapters at seq 0; a move must leave
    the whole sibling list unique and contiguous, whatever it started as."""
    b = _seed(store, units=((80, 9),))
    unit_id = b.chapters[0].unit_id
    a, c2, c3 = store.chapters_for_unit(unit_id)
    store.conn.execute("UPDATE chapters SET seq=0 WHERE unit_id=?", (unit_id,))
    store.conn.commit()

    store.set_sequence("chapter", a.id, 99)

    ordered = store.chapters_for_unit(unit_id)
    assert [c.seq for c in ordered] == [0, 1, 2]
    assert ordered[-1].id == a.id


def test_reorder_route_returns_renumbered_siblings(principal_world):
    w = principal_world
    b = _seed(w.store, units=((80, 9),))
    unit_id = b.chapters[0].unit_id
    third = w.store.chapters_for_unit(unit_id)[2]
    r = w.client.patch(f"{BASE}/chapters/{third.id}/sequence", json={"seq": 0}, headers=w.auth)
    assert r.status_code == 200, r.text
    assert r.json()["seq"] == 0
    seqs = [c.seq for c in w.store.chapters_for_unit(unit_id)]
    assert seqs == [0, 1, 2]


# --------------------------------------------------------------------- #
# Task 102 review, finding 1: a dropped lesson never double-books a day
# --------------------------------------------------------------------- #

def test_a_lesson_push_cannot_place_is_unscheduled_not_left_on_its_date(store, audit_log):
    b = _seed(store, units=((30, 5),), start="2026-06-01", end="2026-06-14", saturday_rule="none")
    calendar_mod.compute_teaching_time_estimates(
        store, academic_year_id=b.year, book_id=b.book, periods_per_week=6)
    scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=b.year,
                                 book_id=b.book, periods_per_week=6)
    before = store.scheduled_lessons_for_book(b.year, b.book)
    assert len(before) == 12      # the year is full: every working day holds one lesson

    push = scheduling_mod.push_lessons_after(
        store, audit_log, academic_year_id=b.year, book_id=b.book, from_date=before[0].date,
        reason="closure", changed_by="p1")

    assert len(push.lessons_dropped) == 1
    after = store.scheduled_lessons_for_book(b.year, b.book)
    dropped = next(l for l in after if l.id == push.lessons_dropped[0])
    assert dropped.status == "unscheduled"
    on_the_plan = [l for l in after if l.status == "scheduled"]
    assert len({l.date for l in on_the_plan}) == len(on_the_plan), "a day holds two lessons"
    # The calendar views (date-range reads) show only lessons that hold a day.
    ranged = store.scheduled_lessons_for_date_range("school_1", "2026-06-01", "2026-06-14")
    assert dropped.id not in {l.id for l in ranged}
    # Losing its day is on the lesson's history, like every move.
    history = scheduling_mod.reschedule_history_for_lesson(audit_log, dropped.id)
    assert len(history) == 1
    details = history[0]["details"]
    assert details["mode"] == "unscheduled"
    assert details["old_date"] == dropped.date and details["new_date"] is None
    assert details["reason"] == "closure"


# --------------------------------------------------------------------- #
# Task 102 review, finding 2: PUSH uses the cadence the schedule was made with
# --------------------------------------------------------------------- #

def test_push_uses_the_cadence_the_book_was_scheduled_with(store, audit_log):
    b = _seed(store, saturday_rule="none")
    store.set_subject_period_allocation(school_id="school_1", academic_year_id=b.year,
                                        subject="Mathematics", periods_per_week=3)
    calendar_mod.compute_teaching_time_estimates(
        store, academic_year_id=b.year, book_id=b.book, periods_per_week=6)
    scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=b.year,
                                 book_id=b.book, periods_per_week=6)
    lessons = store.scheduled_lessons_for_book(b.year, b.book)

    push = scheduling_mod.push_lessons_after(
        store, audit_log, academic_year_id=b.year, book_id=b.book, from_date=lessons[10].date,
        reason="closure", changed_by="p1")
    assert push.periods_per_week == 6
    per_week = Counter(date.fromisoformat(l.date).isocalendar()[:2]
                       for l in store.scheduled_lessons_for_book(b.year, b.book)
                       if l.status == "scheduled")
    assert max(per_week.values()) == 6

    with pytest.raises(ValueError, match="scheduled at 6"):
        scheduling_mod.push_lessons_after(
            store, audit_log, academic_year_id=b.year, book_id=b.book, from_date=lessons[20].date,
            periods_per_week=3, reason="closure", changed_by="p1")


# --------------------------------------------------------------------- #
# Route level: the shortfall flag
# --------------------------------------------------------------------- #

@pytest.fixture
def principal_world(tmp_path, monkeypatch):
    from test_assessment_routes_auth import _boot_client, _register

    with _boot_client(tmp_path, monkeypatch) as client:
        principal = _register(client, "school_1", "p1@example.com", "Priya Principal",
                              principal_key=PRINCIPAL_KEY)
        from academicos.curriculum import routes as curriculum_routes
        # The schedule route plans from the school's today; pinned to the
        # first day of these test years so the tests do not change with the
        # real date. A test that needs a mid-year today sets w.today.
        w = SimpleNamespace(today=date(2026, 6, 1))
        monkeypatch.setattr(curriculum_routes, "_school_today", lambda: w.today)
        w.__dict__.update(
            client=client, auth={"Authorization": f"Bearer {principal['token']}"},
            store=curriculum_routes._require(), routes=curriculum_routes,
            principal=principal)
        yield w


def _schedule_via_route(w, b, periods_per_week=6):
    r = w.client.post(f"{BASE}/books/{b.book}/teaching-time-estimates",
                      params={"academic_year_id": b.year}, json={"periodsPerWeek": periods_per_week},
                      headers=w.auth)
    assert r.status_code == 200, r.text
    r = w.client.post(f"{BASE}/books/{b.book}/schedule", params={"academic_year_id": b.year},
                      json={"periodsPerWeek": periods_per_week}, headers=w.auth)
    assert r.status_code == 200, r.text
    return r


def test_schedule_route_flags_a_shortfall(principal_world):
    w = principal_world
    b = _seed(w.store, start="2026-06-01", end="2026-06-14", saturday_rule="none")
    body = _schedule_via_route(w, b).json()
    assert body["allSubtopicsScheduled"] is False
    assert len(body["subtopicsUnscheduled"]) == 9
    assert "9 of 21 subtopics" in body["warning"]


def test_schedule_route_reports_a_full_plan(principal_world):
    w = principal_world
    b = _seed(w.store, holidays=HOLIDAYS)
    body = _schedule_via_route(w, b).json()
    assert body["allSubtopicsScheduled"] is True
    assert body["warning"] is None


# --------------------------------------------------------------------- #
# Review of 75ca9a1, finding 1: a mid-year regenerate plans from today
# --------------------------------------------------------------------- #

def _periods_from(store, year_id, book_id, from_date, periods_per_week=6):
    return [d for d in calendar_mod.teaching_slots_for_book(store, year_id, book_id, periods_per_week)
            if d.isoformat() >= from_date]


def test_a_mid_year_regenerate_plans_only_from_today(store):
    """The review reproduced it: 10 lessons marked in June, regenerated as
    if in November, and 100 of the 210 replanned lessons were dated before
    November (from 2026-06-12) with allSubtopicsScheduled=true. A lesson on
    a day that has passed cannot be taught, so new lessons start at today.
    The June-October lessons nobody marked stay where they are (review of
    9dd889d), so the replan fills exactly the periods left; the shortfall a
    first plan made in November reports is tested below."""
    b = _seed(store, holidays=HOLIDAYS)
    calendar_mod.compute_teaching_time_estimates(
        store, academic_year_id=b.year, book_id=b.book, periods_per_week=6)
    scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=b.year,
                                 book_id=b.book, periods_per_week=6)
    lessons = store.scheduled_lessons_for_book(b.year, b.book)
    for l in lessons[:10]:
        store.mark_lesson(l.id, status="completed", note=None, completed_by="t1")
    today = "2026-11-02"
    past_ids = {l.id for l in lessons if l.date < today}

    result = scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=b.year,
                                          book_id=b.book, periods_per_week=6, force=True,
                                          from_date=today)

    after = store.scheduled_lessons_for_book(b.year, b.book)
    new = [l for l in after if l.id not in past_ids]
    assert new
    assert min(l.date for l in new) >= today
    assert result.first_scheduled_date >= today
    assert result.lessons_kept == 10
    assert result.past_lessons_kept == len(past_ids) - 10
    assert sum(1 for l in after if l.status == "completed") == 10
    left = _periods_from(store, b.year, b.book, today)
    assert result.teaching_periods_available == len(left)
    assert len(new) == len(left)                # every period left is used, none twice
    assert result.all_subtopics_scheduled, result.warning


def test_a_plan_made_before_the_year_starts_uses_the_whole_year(store):
    """Planning from today must not invent a shortfall: before the year's
    first day, the plan starts on that day and fits exactly as before."""
    b = _seed(store, holidays=HOLIDAYS)
    calendar_mod.compute_teaching_time_estimates(
        store, academic_year_id=b.year, book_id=b.book, periods_per_week=6)
    result = scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=b.year,
                                          book_id=b.book, periods_per_week=6,
                                          from_date="2026-05-20")
    assert result.all_subtopics_scheduled, result.warning
    assert result.first_scheduled_date == "2026-06-01"


def test_schedule_route_plans_from_the_school_today(principal_world):
    w = principal_world
    b = _seed(w.store, holidays=HOLIDAYS)
    _schedule_via_route(w, b)
    first = w.store.scheduled_lessons_for_book(b.year, b.book)[0]
    r = w.client.patch(f"{BASE}/scheduled-lessons/{first.id}", json={"status": "completed"},
                       headers=w.auth)
    assert r.status_code == 200, r.text

    w.today = date(2026, 11, 2)
    r = w.client.post(f"{BASE}/books/{b.book}/schedule", params={"academic_year_id": b.year},
                      json={"periodsPerWeek": 6, "force": True}, headers=w.auth)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["firstScheduledDate"] >= "2026-11-02"
    assert body["lessonsKept"] == 1
    # June-October stays as planned (taught or overdue); only November on
    # is replanned, so the plan still fits.
    assert body["pastLessonsKept"] > 0
    assert body["allSubtopicsScheduled"] is True, body["warning"]
    after = w.store.scheduled_lessons_for_book(b.year, b.book)
    assert sum(1 for l in after if l.date < "2026-11-02") == body["pastLessonsKept"] + 1


# --------------------------------------------------------------------- #
# Review of 75ca9a1, finding 2: an 'unscheduled' lesson at the routes
# --------------------------------------------------------------------- #

def _short_year_with_a_dropped_lesson(w):
    """12 working days, 12 lessons, then PUSH from the first day: the last
    lesson has no period left and becomes 'unscheduled', still carrying its
    last planned date as a stale date."""
    b = _seed(w.store, units=((30, 5),), start="2026-06-01", end="2026-06-14",
              saturday_rule="none")
    _schedule_via_route(w, b)
    lessons = w.store.scheduled_lessons_for_book(b.year, b.book)
    assert len(lessons) == 12
    r = w.client.post(f"{BASE}/books/{b.book}/schedule/push", params={"academic_year_id": b.year},
                      json={"fromDate": lessons[0].date, "reason": "closure"}, headers=w.auth)
    assert r.status_code == 200, r.text
    dropped_ids = r.json()["lessonsDropped"]
    assert len(dropped_ids) == 1
    dropped = w.store.get_scheduled_lesson(dropped_ids[0])
    assert dropped.status == "unscheduled"
    return b, dropped


def test_marking_an_unscheduled_lesson_is_refused(principal_world):
    w = principal_world
    _, dropped = _short_year_with_a_dropped_lesson(w)
    r = w.client.patch(f"{BASE}/scheduled-lessons/{dropped.id}", json={"status": "completed"},
                       headers=w.auth)
    assert r.status_code == 409, r.text
    assert "no day" in r.json()["detail"]
    assert w.store.get_scheduled_lesson(dropped.id).status == "unscheduled"


def test_adjust_ignores_an_unscheduled_lesson_and_gives_it_a_day_back(principal_world):
    w = principal_world
    b, dropped = _short_year_with_a_dropped_lesson(w)
    on_plan = [l for l in w.store.scheduled_lessons_for_book(b.year, b.book)
               if l.status == "scheduled"]
    # The PUSH moved another lesson onto the dropped lesson's stale date.
    # Move that one to the day the closure freed.
    holder = next(l for l in on_plan if l.date == dropped.date)
    r = w.client.post(f"{BASE}/scheduled-lessons/{holder.id}/reschedule",
                      json={"newDate": "2026-06-01", "reason": "reopened"}, headers=w.auth)
    assert r.status_code == 200, r.text

    # Only the unscheduled lesson now carries that date. It holds no period,
    # so another lesson can move there (no timetable: one period a day).
    mover = next(l for l in on_plan if l.id != holder.id)
    r = w.client.post(f"{BASE}/scheduled-lessons/{mover.id}/reschedule",
                      json={"newDate": dropped.date, "reason": "swap"}, headers=w.auth)
    assert r.status_code == 200, r.text

    # ADJUST puts the dropped lesson back on the plan, on the day the mover left.
    r = w.client.post(f"{BASE}/scheduled-lessons/{dropped.id}/reschedule",
                      json={"newDate": mover.date, "reason": "extra class"}, headers=w.auth)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "scheduled" and r.json()["date"] == mover.date
    back = w.store.get_scheduled_lesson(dropped.id)
    assert back.status == "scheduled" and back.date == mover.date

    history = w.client.get(f"{BASE}/scheduled-lessons/{dropped.id}/history", headers=w.auth).json()
    assert [h["mode"] for h in history] == ["adjust", "unscheduled"]   # newest first
    assert history[0]["newDate"] == mover.date and history[0]["reason"] == "extra class"

    after = [l for l in w.store.scheduled_lessons_for_book(b.year, b.book) if l.status == "scheduled"]
    assert len({l.date for l in after}) == len(after) == 12


# --------------------------------------------------------------------- #
# Review of 75ca9a1, finding 3: unscheduled lessons are counted and reported
# --------------------------------------------------------------------- #

def test_progress_and_delayed_topics_count_an_unscheduled_lesson(principal_world):
    w = principal_world
    b, dropped = _short_year_with_a_dropped_lesson(w)
    student = register_invited(w.client, "school_1", "s1@example.com", name="Student",
                               role="student")
    subject = w.store.get_subject(w.store.get_book(b.book).subject_id)
    r = w.client.post(f"{BASE}/student-enrollments",
                      json={"studentId": student["user"]["id"], "gradeId": subject.grade_id},
                      headers=w.auth)
    assert r.status_code == 200, r.text
    first = next(l for l in w.store.scheduled_lessons_for_book(b.year, b.book)
                 if l.status == "scheduled")
    w.today = date.fromisoformat(first.date)     # marked on its own day (D67: never before it)
    r = w.client.patch(f"{BASE}/scheduled-lessons/{first.id}", json={"status": "completed"},
                       headers=w.auth)
    assert r.status_code == 200, r.text

    w.today = date(2026, 6, 20)      # the short year is over
    r = w.client.get(f"{BASE}/my-progress", params={"academic_year_id": b.year},
                     headers={"Authorization": f"Bearer {student['token']}"})
    assert r.status_code == 200, r.text
    assert r.json()["asOfDate"] == "2026-06-20"
    p = r.json()["subjects"][0]
    assert p["unscheduledCount"] == 1
    assert p["completedCount"] == 1
    assert (p["scheduledCount"] + p["completedCount"] + p["skippedCount"] + p["unscheduledCount"]
            == p["totalCount"] == 12)

    r = w.client.get(f"{BASE}/reporting/delayed-topics", params={"academic_year_id": b.year},
                     headers=w.auth)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["asOfDate"] == "2026-06-20"
    assert body["delayedCount"] == 10               # still 'scheduled' on a day that has passed
    assert body["unscheduledCount"] == 1
    entry = body["unscheduledLessons"][0]
    assert entry["lessonId"] == dropped.id
    assert entry["lastPlannedDate"] == dropped.date
    assert entry["subjectName"] == "Mathematics" and entry["subtopicName"]
    assert dropped.id not in {l["lessonId"] for l in body["delayedLessons"]}


# --------------------------------------------------------------------- #
# Review of 9dd889d: a mid-year force regenerate kept only marked lessons
# --------------------------------------------------------------------- #

def test_a_mid_year_regenerate_keeps_past_lessons_nobody_marked(store):
    """The review reproduced it on this calendar: 220 estimated periods,
    no lesson marked (teachers taught but did not tick), then force=True
    from 2026-09-22 (the release date). Every June-September lesson was
    deleted, the replan covered only what fit after today, and 9 of 21
    subtopics lost their dates -- the overdue record vanished from
    delayed-topics, planned-to-date and pace, and the second half of the
    syllabus was left undated although that time was spent on the first.
    A day that has passed is history: its planned lessons stay, count
    toward their subtopic's estimate, and only the future is replanned."""
    b = _seed(store, holidays=HOLIDAYS)
    calendar_mod.compute_teaching_time_estimates(
        store, academic_year_id=b.year, book_id=b.book, periods_per_week=6)
    scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=b.year,
                                 book_id=b.book, periods_per_week=6)
    before = store.scheduled_lessons_for_book(b.year, b.book)
    today = "2026-09-22"
    past = {(l.id, l.subtopic_id, l.date, l.status) for l in before if l.date < today}
    assert past

    result = scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=b.year,
                                          book_id=b.book, periods_per_week=6, force=True,
                                          from_date=today)

    after = store.scheduled_lessons_for_book(b.year, b.book)
    assert {(l.id, l.subtopic_id, l.date, l.status) for l in after if l.date < today} == past
    assert result.past_lessons_kept == len(past)
    assert result.lessons_kept == 0                     # nothing was marked
    assert result.all_subtopics_scheduled, result.warning
    assert not result.subtopics_unscheduled and not result.subtopics_partially_scheduled
    assert result.first_scheduled_date >= today
    # The replan is the same plan: every subtopic keeps its periods, and
    # each period of the year still holds exactly one lesson.
    assert Counter(l.subtopic_id for l in after) == Counter(l.subtopic_id for l in before)
    assert sorted(l.date for l in after) == sorted(l.date for l in before)


def test_a_first_plan_made_mid_year_reports_the_periods_left(store):
    """A school that starts using the planner in November has no June plan
    to keep: the plan starts at today, and a syllabus sized for the whole
    year is flagged against the periods really left."""
    b = _seed(store, holidays=HOLIDAYS)
    calendar_mod.compute_teaching_time_estimates(
        store, academic_year_id=b.year, book_id=b.book, periods_per_week=6)
    today = "2026-11-02"
    result = scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=b.year,
                                          book_id=b.book, periods_per_week=6, from_date=today)
    left = _periods_from(store, b.year, b.book, today)
    assert result.first_scheduled_date >= today
    assert result.lessons_created == len(left)
    assert result.all_subtopics_scheduled is False
    assert f"{len(left)} teaching periods left" in result.warning
    assert today in result.warning


def test_a_subtopic_whose_lessons_were_all_skipped_is_planned_again(store):
    """A skip ("assembly", "exam duty") means nothing was taught. Until the
    review of 2026-09-22 a regenerate counted skipped lessons toward their
    subtopic's estimate, so a subtopic with every lesson skipped came back
    with no lesson left to teach and allSubtopicsScheduled=True."""
    b = _seed(store, holidays=HOLIDAYS)
    calendar_mod.compute_teaching_time_estimates(
        store, academic_year_id=b.year, book_id=b.book, periods_per_week=6)
    scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=b.year,
                                 book_id=b.book, periods_per_week=6)
    lessons = store.scheduled_lessons_for_book(b.year, b.book)
    first_st = lessons[0].subtopic_id
    skipped = [l for l in lessons if l.subtopic_id == first_st]
    for l in skipped:
        store.mark_lesson(l.id, status="skipped", note="assembly", completed_by="t1")

    scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=b.year,
                                 book_id=b.book, periods_per_week=6, force=True)

    after = store.scheduled_lessons_for_book(b.year, b.book)
    to_teach = [l for l in after if l.subtopic_id == first_st and l.status == "scheduled"]
    assert len(to_teach) == len(skipped)
    assert all(by.status == "skipped" for by in after if by.id in {l.id for l in skipped})
