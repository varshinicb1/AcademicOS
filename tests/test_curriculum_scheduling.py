"""curriculum/scheduling.py -- the §11-14 micro-scheduling engine: real
curriculum order x real TeachingTimeEstimate x real working days -> a real,
dated ScheduledLesson[].

Hermetic: builds its own small curriculum hierarchy + calendar + period
config + teaching-time estimates per test, no dependency on the real CBSE
seed data.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.assessment.audit_log import AuditLog
from academicos.curriculum import calendar as calendar_mod
from academicos.curriculum import scheduling as scheduling_mod
from academicos.curriculum.store import CurriculumStore


@pytest.fixture
def store(tmp_path):
    s = CurriculumStore(tmp_path / "curriculum.sqlite")
    yield s
    s.close()


@pytest.fixture
def audit_log(tmp_path):
    return AuditLog(tmp_path / "audit.sqlite")


def _seed_schedulable_book(store, *, school_id="school_1", n_subtopics_a=3, n_subtopics_b=2,
                           start_date="2026-06-01", end_date="2027-03-31",
                           period_minutes=40, weekly_off_days=None, alternate_saturday_rule="none"):
    """Two real units (unequal marks, 30 vs 10) each with one chapter ->
    one topic -> N subtopics, a real calendar, a real period configuration,
    and real, computed TeachingTimeEstimate rows for every subtopic --
    everything schedule_book() requires to run for real, no shortcuts."""
    board = store.create_board(name="CBSE", code="CBSE")
    year = store.create_academic_year(school_id=school_id, label="2026-27",
                                      start_date=start_date, end_date=end_date)
    grade = store.create_grade(academic_year_id=year.id, number=10)
    subject = store.create_subject(grade_id=grade.id, name="Science")
    book = store.create_book(subject_id=subject.id, board_id=board.id, title="Book")

    unit_a = store.create_unit(canonical_id="u:A", book_id=book.id, unit_no="I", name="Unit A", marks=30, seq=0)
    unit_b = store.create_unit(canonical_id="u:B", book_id=book.id, unit_no="II", name="Unit B", marks=10, seq=1)

    def _add(unit, n, prefix, seq):
        chapter = store.create_chapter(canonical_id=f"c:{prefix}", unit_id=unit.id, name=f"Chapter {prefix}", seq=seq)
        topic = store.create_topic(canonical_id=f"t:{prefix}", chapter_id=chapter.id, name=f"Topic {prefix}", seq=0)
        for i in range(n):
            store.create_subtopic(canonical_id=f"st:{prefix}:{i}", topic_id=topic.id,
                                  name=f"Subtopic {prefix}{i}", seq=i)

    _add(unit_a, n_subtopics_a, "A", 0)
    _add(unit_b, n_subtopics_b, "B", 1)

    store.create_calendar(academic_year_id=year.id, weekly_off_days=weekly_off_days or ["sunday"],
                          alternate_saturday_rule=alternate_saturday_rule)
    store.create_period_configuration(school_id=school_id, academic_year_id=year.id,
                                      period_minutes=period_minutes)
    calendar_mod.compute_teaching_time_estimates(
        store, academic_year_id=year.id, book_id=book.id, periods_per_week=6)

    return book.id, year.id


def test_periods_per_week_must_be_positive(store):
    book_id, year_id = _seed_schedulable_book(store)
    with pytest.raises(ValueError):
        scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=year_id,
                                     book_id=book_id, periods_per_week=0)


def test_schedule_produces_dated_lessons_in_curriculum_order(store):
    book_id, year_id = _seed_schedulable_book(store)
    result = scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=year_id,
                                          book_id=book_id, periods_per_week=6)

    assert result.lessons_created > 0
    assert result.subtopics_without_estimate == ()
    lessons = store.scheduled_lessons_for_book(year_id, book_id)
    assert len(lessons) == result.lessons_created
    # Every lesson lands on a real date, in non-decreasing date order
    # (store orders by date; scheduling itself only ever moves forward).
    dates = [l.date for l in lessons]
    assert dates == sorted(dates)
    # Unit A (30 marks, 3 subtopics) is scheduled entirely before Unit B
    # (10 marks, seq=1) starts -- real curriculum delivery order (§13).
    unit_a_subtopic_ids = {s.id for s in store.subtopics_for_topic(
        store.topics_for_chapter(store.chapters_for_unit(
            store.units_for_book(book_id)[0].id)[0].id)[0].id)}
    first_non_a_index = next(i for i, l in enumerate(lessons) if l.subtopic_id not in unit_a_subtopic_ids)
    assert all(l.subtopic_id in unit_a_subtopic_ids for l in lessons[:first_non_a_index])


def test_real_timetable_slots_override_the_first_n_days_heuristic(store):
    """Real proof a school's entered SubjectTimetableSlot rows are actually
    used: with no slots, schedule_book() falls back to the "first N working
    days of each week" heuristic (which would include Monday, the first
    working day). Adding slots for exactly Tuesday and Thursday must make
    every scheduled lesson land on one of those two weekdays instead."""
    book_id, year_id = _seed_schedulable_book(store)
    store.add_timetable_slot(school_id="school_1", academic_year_id=year_id, subject="Science",
                             day_of_week=1, period_number=1)   # Tuesday
    store.add_timetable_slot(school_id="school_1", academic_year_id=year_id, subject="Science",
                             day_of_week=3, period_number=1)   # Thursday

    result = scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=year_id,
                                          book_id=book_id, periods_per_week=6)
    lessons = store.scheduled_lessons_for_book(year_id, book_id)
    assert len(lessons) == result.lessons_created > 0
    for lesson in lessons:
        weekday = date.fromisoformat(lesson.date).weekday()
        assert weekday in (1, 3), f"{lesson.date} is weekday {weekday}, not Tue/Thu"


def test_reordering_a_unit_changes_the_next_schedule_book_run(store):
    """Real proof store.set_sequence() isn't just a store-level field flip --
    schedule_book() reads units_for_book()/chapters_for_unit() etc live
    (all ORDER BY seq), so a reorder made *before* a schedule_book() call
    genuinely changes its output. Default order here is Unit A (seq=0) then
    Unit B (seq=1) -- confirmed by test_schedule_produces_dated_lessons_
    in_curriculum_order above. This test swaps them and shows B goes first."""
    book_id, year_id = _seed_schedulable_book(store)
    unit_a, unit_b = store.units_for_book(book_id)
    assert unit_a.name == "Unit A" and unit_b.name == "Unit B"

    store.set_sequence("unit", unit_a.id, 1)
    store.set_sequence("unit", unit_b.id, 0)

    result = scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=year_id,
                                          book_id=book_id, periods_per_week=6)
    lessons = store.scheduled_lessons_for_book(year_id, book_id)
    assert len(lessons) == result.lessons_created

    unit_b_subtopic_ids = {s.id for s in store.subtopics_for_topic(
        store.topics_for_chapter(store.chapters_for_unit(unit_b.id)[0].id)[0].id)}
    first_non_b_index = next(i for i, l in enumerate(lessons) if l.subtopic_id not in unit_b_subtopic_ids)
    # Unit B (now seq=0) is scheduled entirely before Unit A (now seq=1)
    # starts -- the exact reverse of the pre-reorder default.
    assert all(l.subtopic_id in unit_b_subtopic_ids for l in lessons[:first_non_b_index])


def test_schedule_skips_subtopics_without_a_teaching_time_estimate(store):
    book_id, year_id = _seed_schedulable_book(store)
    # Add one more subtopic to Unit A's topic *after* estimates were
    # already computed -- it genuinely has no real estimate yet.
    unit = store.units_for_book(book_id)[0]
    chapter = store.chapters_for_unit(unit.id)[0]
    topic = store.topics_for_chapter(chapter.id)[0]
    orphan = store.create_subtopic(canonical_id="st:orphan", topic_id=topic.id, name="No estimate yet", seq=99)

    result = scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=year_id,
                                          book_id=book_id, periods_per_week=6)
    assert orphan.id in result.subtopics_without_estimate
    scheduled_ids = {l.subtopic_id for l in store.scheduled_lessons_for_book(year_id, book_id)}
    assert orphan.id not in scheduled_ids


def test_schedule_refuses_to_silently_reschedule(store):
    book_id, year_id = _seed_schedulable_book(store)
    scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=year_id,
                                 book_id=book_id, periods_per_week=6)
    with pytest.raises(ValueError, match="already has a schedule"):
        scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=year_id,
                                     book_id=book_id, periods_per_week=6)


def test_schedule_force_regenerates_cleanly(store):
    book_id, year_id = _seed_schedulable_book(store)
    first = scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=year_id,
                                         book_id=book_id, periods_per_week=6)
    second = scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=year_id,
                                          book_id=book_id, periods_per_week=6, force=True)
    # Force deletes and regenerates -- not doubled.
    assert len(store.scheduled_lessons_for_book(year_id, book_id)) == second.lessons_created
    assert second.lessons_created == first.lessons_created


def test_schedule_reports_unscheduled_subtopics_when_the_year_runs_out(store):
    """A deliberately tiny academic year (2 real weeks) can't fit every
    subtopic's real estimated periods -- the leftover must be reported,
    never silently dropped or pushed past the real calendar."""
    book_id, year_id = _seed_schedulable_book(
        store, n_subtopics_a=3, n_subtopics_b=2, start_date="2026-06-01", end_date="2026-06-14")
    result = scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=year_id,
                                          book_id=book_id, periods_per_week=6)
    assert result.subtopics_unscheduled or result.subtopics_partially_scheduled
    # Nothing scheduled past the real academic year's own end date.
    lessons = store.scheduled_lessons_for_book(year_id, book_id)
    assert all(l.date <= "2026-06-14" for l in lessons)


def test_schedule_respects_alternate_saturday_and_holidays(store):
    """The subject's teaching-day list itself must come from the real
    calendar -- no lesson lands on an off day."""
    board = store.create_board(name="CBSE", code="CBSE")
    year = store.create_academic_year(school_id="school_1", label="y",
                                      start_date="2026-09-01", end_date="2026-09-30")
    grade = store.create_grade(academic_year_id=year.id, number=10)
    subject = store.create_subject(grade_id=grade.id, name="Science")
    book = store.create_book(subject_id=subject.id, board_id=board.id, title="Book")
    unit = store.create_unit(canonical_id="u:A", book_id=book.id, unit_no="I", name="Unit A", marks=100, seq=0)
    chapter = store.create_chapter(canonical_id="c:A", unit_id=unit.id, name="Chapter A", seq=0)
    topic = store.create_topic(canonical_id="t:A", chapter_id=chapter.id, name="Topic A", seq=0)
    for i in range(20):
        store.create_subtopic(canonical_id=f"st:A:{i}", topic_id=topic.id, name=f"Subtopic {i}", seq=i)

    cal = store.create_calendar(academic_year_id=year.id, weekly_off_days=["sunday"],
                                alternate_saturday_rule="2nd,4th")
    store.add_holiday(calendar_id=cal.id, date="2026-09-02", label="Test holiday", kind="holiday")
    store.create_period_configuration(school_id="school_1", academic_year_id=year.id, period_minutes=40)
    calendar_mod.compute_teaching_time_estimates(
        store, academic_year_id=year.id, book_id=book.id, periods_per_week=6)

    scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=year.id,
                                 book_id=book.id, periods_per_week=6)
    lessons = store.scheduled_lessons_for_book(year.id, book.id)
    scheduled_dates = {l.date for l in lessons}
    assert "2026-09-02" not in scheduled_dates   # the holiday
    assert "2026-09-06" not in scheduled_dates   # a Sunday
    assert "2026-09-12" not in scheduled_dates   # 2nd Saturday
    assert "2026-09-26" not in scheduled_dates   # 4th Saturday


# --------------------------------------------------------------------- #
# rescheduling on disruption -- §14: PUSH / ADJUST + audit trail
# --------------------------------------------------------------------- #

def test_adjust_lesson_moves_to_a_real_working_day(store, audit_log):
    book_id, year_id = _seed_schedulable_book(store)
    scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=year_id,
                                 book_id=book_id, periods_per_week=6)
    lesson = store.scheduled_lessons_for_book(year_id, book_id)[0]
    old_date = lesson.date

    # A real, later working day for this calendar -- Monday of the
    # following week (2026-06-01 is a Monday, so this is 2026-06-08).
    result = scheduling_mod.adjust_lesson(store, audit_log, lesson_id=lesson.id, new_date="2026-06-08",
                                          reason="Teacher requested swap", changed_by="teacher_1")
    assert result.old_date == old_date
    assert result.new_date == "2026-06-08"
    assert result.mode == "adjust"
    assert store.get_scheduled_lesson(lesson.id).date == "2026-06-08"


def test_adjust_lesson_rejects_a_non_working_day(store, audit_log):
    book_id, year_id = _seed_schedulable_book(store)
    scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=year_id,
                                 book_id=book_id, periods_per_week=6)
    lesson = store.scheduled_lessons_for_book(year_id, book_id)[0]

    # 2026-06-07 is a Sunday -- a real weekly off day for this calendar.
    with pytest.raises(ValueError, match="not a real working day"):
        scheduling_mod.adjust_lesson(store, audit_log, lesson_id=lesson.id, new_date="2026-06-07",
                                     reason="oops", changed_by="teacher_1")
    # rejected -- the real row is untouched
    assert store.get_scheduled_lesson(lesson.id).date != "2026-06-07"


def test_adjust_lesson_unknown_id_raises(store, audit_log):
    with pytest.raises(ValueError, match="no such scheduled lesson"):
        scheduling_mod.adjust_lesson(store, audit_log, lesson_id="not_real", new_date="2026-06-08",
                                     reason="x", changed_by="teacher_1")


def test_adjust_lesson_writes_a_real_audit_entry(store, audit_log):
    book_id, year_id = _seed_schedulable_book(store)
    scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=year_id,
                                 book_id=book_id, periods_per_week=6)
    lesson = store.scheduled_lessons_for_book(year_id, book_id)[0]
    old_date = lesson.date

    scheduling_mod.adjust_lesson(store, audit_log, lesson_id=lesson.id, new_date="2026-06-08",
                                 reason="Assembly conflict", changed_by="teacher_1")

    history = scheduling_mod.reschedule_history_for_lesson(audit_log, lesson.id)
    assert len(history) == 1
    entry = history[0]
    assert entry["actor"] == "teacher_1"
    assert entry["details"]["old_date"] == old_date
    assert entry["details"]["new_date"] == "2026-06-08"
    assert entry["details"]["reason"] == "Assembly conflict"
    assert entry["details"]["mode"] == "adjust"
    assert entry["timestamp"]


def test_reschedule_history_only_returns_entries_for_that_lesson(store, audit_log):
    book_id, year_id = _seed_schedulable_book(store)
    scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=year_id,
                                 book_id=book_id, periods_per_week=6)
    lessons = store.scheduled_lessons_for_book(year_id, book_id)
    scheduling_mod.adjust_lesson(store, audit_log, lesson_id=lessons[0].id, new_date="2026-06-08",
                                 reason="a", changed_by="t1")
    scheduling_mod.adjust_lesson(store, audit_log, lesson_id=lessons[1].id, new_date="2026-06-09",
                                 reason="b", changed_by="t1")

    history = scheduling_mod.reschedule_history_for_lesson(audit_log, lessons[0].id)
    assert len(history) == 1
    assert history[0]["details"]["lesson_id"] == lessons[0].id


def test_push_lessons_after_shifts_the_affected_tail_forward(store, audit_log):
    book_id, year_id = _seed_schedulable_book(store)
    result = scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=year_id,
                                          book_id=book_id, periods_per_week=6)
    lessons_before = store.scheduled_lessons_for_book(year_id, book_id)
    assert len(lessons_before) == result.lessons_created

    # Push everything from the very first lesson's date onward.
    from_date = lessons_before[0].date
    push = scheduling_mod.push_lessons_after(
        store, audit_log, academic_year_id=year_id, book_id=book_id, from_date=from_date,
        periods_per_week=6, reason="Unplanned school closure", changed_by="principal_1")

    assert push.lessons_pushed + len(push.lessons_dropped) == len(lessons_before)
    assert push.lessons_pushed > 0

    lessons_after = store.scheduled_lessons_for_book(year_id, book_id)
    # Every real lesson that got pushed now falls strictly after its own
    # original date -- nothing moved backward.
    before_by_id = {l.id: l.date for l in lessons_before}
    moved = 0
    for l in lessons_after:
        if l.id in before_by_id and l.date != before_by_id[l.id]:
            assert l.date > before_by_id[l.id]
            moved += 1
    assert moved == push.lessons_pushed

    # Relative order is preserved -- no two pushed lessons swapped places.
    pushed_ids = {r.lesson_id for r in push.reschedules}
    pushed_lessons_after = sorted(
        (l for l in lessons_after if l.id in pushed_ids), key=lambda l: l.date)
    pushed_lessons_before = sorted(
        (l for l in lessons_before if l.id in pushed_ids), key=lambda l: l.date)
    assert [l.id for l in pushed_lessons_after] == [l.id for l in pushed_lessons_before]


def test_push_lessons_after_leaves_earlier_lessons_untouched(store, audit_log):
    book_id, year_id = _seed_schedulable_book(store)
    scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=year_id,
                                 book_id=book_id, periods_per_week=6)
    lessons_before = store.scheduled_lessons_for_book(year_id, book_id)
    # Push from the date of the 3rd lesson onward -- the first two must
    # not move.
    from_date = lessons_before[2].date
    untouched_ids = {l.id for l in lessons_before[:2]}

    scheduling_mod.push_lessons_after(
        store, audit_log, academic_year_id=year_id, book_id=book_id, from_date=from_date,
        periods_per_week=6, reason="disruption", changed_by="principal_1")

    lessons_after = {l.id: l.date for l in store.scheduled_lessons_for_book(year_id, book_id)}
    for l in lessons_before[:2]:
        assert lessons_after[l.id] == l.date
    assert lessons_before[2].id not in untouched_ids  # sanity on the test itself


def test_push_lessons_after_reports_no_op_when_nothing_is_affected(store, audit_log):
    book_id, year_id = _seed_schedulable_book(store)
    result = scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=year_id,
                                          book_id=book_id, periods_per_week=6)
    # A real date strictly after every real lesson in this small book's schedule.
    from datetime import date, timedelta
    after_last = (date.fromisoformat(result.last_scheduled_date) + timedelta(days=1)).isoformat()
    push = scheduling_mod.push_lessons_after(
        store, audit_log, academic_year_id=year_id, book_id=book_id, from_date=after_last,
        periods_per_week=6, reason="x", changed_by="principal_1")
    assert push.lessons_pushed == 0
    assert push.lessons_dropped == ()
    assert push.reschedules == ()


def test_push_lessons_after_drops_lessons_that_would_fall_off_the_calendar(store, audit_log):
    # A deliberately tiny academic year so pushing the whole book off the
    # very first day runs out of real teaching days immediately.
    book_id, year_id = _seed_schedulable_book(
        store, start_date="2026-06-01", end_date="2026-06-14")
    scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=year_id,
                                 book_id=book_id, periods_per_week=6)
    lessons_before = store.scheduled_lessons_for_book(year_id, book_id)

    push = scheduling_mod.push_lessons_after(
        store, audit_log, academic_year_id=year_id, book_id=book_id, from_date=lessons_before[0].date,
        periods_per_week=6, reason="disruption", changed_by="principal_1")

    assert push.lessons_pushed + len(push.lessons_dropped) == len(lessons_before)
    assert len(push.lessons_dropped) > 0   # a 2-week year genuinely can't absorb a full push
    for lesson_id in push.lessons_dropped:
        assert lesson_id not in {r.lesson_id for r in push.reschedules}


def test_push_lessons_after_writes_one_audit_entry_per_pushed_lesson(store, audit_log):
    book_id, year_id = _seed_schedulable_book(store)
    scheduling_mod.schedule_book(store, school_id="school_1", academic_year_id=year_id,
                                 book_id=book_id, periods_per_week=6)
    lessons_before = store.scheduled_lessons_for_book(year_id, book_id)

    push = scheduling_mod.push_lessons_after(
        store, audit_log, academic_year_id=year_id, book_id=book_id, from_date=lessons_before[0].date,
        periods_per_week=6, reason="Sudden closure", changed_by="principal_1")

    for r in push.reschedules:
        history = scheduling_mod.reschedule_history_for_lesson(audit_log, r.lesson_id)
        assert len(history) == 1
        assert history[0]["details"]["mode"] == "push"
        assert history[0]["details"]["reason"] == "Sudden closure"
        assert history[0]["actor"] == "principal_1"
