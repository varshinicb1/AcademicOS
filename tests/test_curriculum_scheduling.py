"""curriculum/scheduling.py -- the §11-14 micro-scheduling engine: real
curriculum order x real TeachingTimeEstimate x real working days -> a real,
dated ScheduledLesson[].

Hermetic: builds its own small curriculum hierarchy + calendar + period
config + teaching-time estimates per test, no dependency on the real CBSE
seed data.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.curriculum import calendar as calendar_mod
from academicos.curriculum import scheduling as scheduling_mod
from academicos.curriculum.store import CurriculumStore


@pytest.fixture
def store(tmp_path):
    s = CurriculumStore(tmp_path / "curriculum.sqlite")
    yield s
    s.close()


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
