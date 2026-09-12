"""Micro scheduling -- §11-14, §38-41: the module the transcript calls the
actual point of the project. Turns curriculum (real, approved Subtopics, in
their real delivery order) x teaching-time-estimate (real, calendar-grounded
periods per subtopic) x calendar (real working days) into a real, dated
`ScheduledLesson[]` -- never a week-numbered or subtopic-less approximation.

Deliberately consumes calendar.py's working_days_for_year() and
store.py's TeachingTimeEstimate rows rather than recomputing either --
scheduling is the last stage of a pipeline (calendar -> teaching-time
-> schedule), not a parallel path that could drift from the other two.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from typing import Optional

from .calendar import working_days_for_year
from .store import CurriculumStore


def _subject_teaching_days(working_days: list[date], periods_per_week: int) -> list[date]:
    """Groups the real working days into real calendar weeks (ISO
    Mon-Sun) and takes the first `periods_per_week` of each week, in date
    order, as the days this subject meets.

    This data model has no school-wide, period-by-period timetable (no
    `SubjectPeriodAllocation`/weekday-slot concept exists -- confirmed
    missing, see docs/TRANSCRIPT_REQUIREMENTS_MATRIX.md), so there is no
    real signal for exactly *which* weekdays a school actually assigns this
    subject. This is a deterministic, explainable, honestly-documented
    simplification -- the same "no finer real signal exists, don't
    fabricate one" stance seed_cbse10.py and calendar.py already take --
    not a claim to reproduce a real school's actual timetable."""
    by_week: dict[tuple[int, int], list[date]] = defaultdict(list)
    for d in working_days:
        iso_year, iso_week, _ = d.isocalendar()
        by_week[(iso_year, iso_week)].append(d)
    selected: list[date] = []
    for key in sorted(by_week):
        days = sorted(by_week[key])
        selected.extend(days[:periods_per_week])
    return selected


@dataclass(frozen=True)
class ScheduleResult:
    academic_year_id: str
    book_id: str
    periods_per_week: int
    teaching_days_available: int
    lessons_created: int
    subtopics_scheduled: int
    subtopics_partially_scheduled: tuple[str, ...]   # got some but not all periods before days ran out
    subtopics_unscheduled: tuple[str, ...]            # got zero periods -- days ran out entirely
    subtopics_without_estimate: tuple[str, ...]       # skipped -- no real TeachingTimeEstimate yet
    first_scheduled_date: Optional[str]
    last_scheduled_date: Optional[str]


def schedule_book(
    store: CurriculumStore, *, school_id: str, academic_year_id: str, book_id: str,
    periods_per_week: int, force: bool = False,
) -> ScheduleResult:
    """Schedules every real, approved Subtopic in a book's real delivery
    order (Unit.seq -> Chapter.seq -> Topic.seq -> Subtopic.seq -- §13's
    independently-reorderable sequence, already respected by store.py's own
    ORDER BY) across the real teaching days this subject gets this year.

    A Subtopic without a real TeachingTimeEstimate for this academic year
    is skipped and reported, never given a guessed period count -- run
    calendar.py's compute_teaching_time_estimates() first.

    Not idempotent by default: re-scheduling an already-scheduled book
    raises unless `force=True`, which deletes the existing schedule first.
    A real schedule may already be visible to teachers/students (the next
    two milestones); silently regenerating it out from under them would be
    wrong. Deliberate rescheduling of individual lessons (§14, PUSH/ADJUST
    with an audit trail) is a separate, smaller, later operation -- this
    function only ever produces the initial full-book schedule.
    """
    if periods_per_week <= 0:
        raise ValueError("periods_per_week must be positive")

    existing = store.scheduled_lessons_for_book(academic_year_id, book_id)
    if existing:
        if not force:
            raise ValueError(
                f"book {book_id} already has a schedule for {academic_year_id} "
                f"({len(existing)} lessons) -- pass force=True to regenerate "
                "(this deletes the existing schedule first)")
        store.delete_scheduled_lessons_for_book(academic_year_id, book_id)

    wd = working_days_for_year(store, academic_year_id)
    teaching_days = _subject_teaching_days([date.fromisoformat(s) for s in wd.dates], periods_per_week)

    ordered: list[tuple[str, int]] = []   # (subtopic_id, periods_needed)
    without_estimate: list[str] = []
    for unit in store.units_for_book(book_id):
        for chapter in store.chapters_for_unit(unit.id):
            for topic in store.topics_for_chapter(chapter.id):
                for subtopic in store.subtopics_for_topic(topic.id):
                    est = store.teaching_time_estimate_for_subtopic(subtopic.id, academic_year_id)
                    if est is None or not est.estimated_periods:
                        without_estimate.append(subtopic.id)
                        continue
                    ordered.append((subtopic.id, max(1, est.estimated_periods)))

    lessons_created = 0
    fully_scheduled = 0
    partially_scheduled: list[str] = []
    unscheduled: list[str] = []
    first_date: Optional[str] = None
    last_date: Optional[str] = None
    day_idx = 0

    for subtopic_id, periods_needed in ordered:
        placed = 0
        for _ in range(periods_needed):
            if day_idx >= len(teaching_days):
                break
            d = teaching_days[day_idx]
            store.create_scheduled_lesson(school_id=school_id, academic_year_id=academic_year_id,
                                          book_id=book_id, subtopic_id=subtopic_id, date=d.isoformat())
            lessons_created += 1
            first_date = first_date or d.isoformat()
            last_date = d.isoformat()
            day_idx += 1
            placed += 1
        if placed == 0:
            unscheduled.append(subtopic_id)
        elif placed < periods_needed:
            partially_scheduled.append(subtopic_id)
        else:
            fully_scheduled += 1

    return ScheduleResult(
        academic_year_id=academic_year_id, book_id=book_id, periods_per_week=periods_per_week,
        teaching_days_available=len(teaching_days), lessons_created=lessons_created,
        subtopics_scheduled=fully_scheduled,
        subtopics_partially_scheduled=tuple(partially_scheduled),
        subtopics_unscheduled=tuple(unscheduled),
        subtopics_without_estimate=tuple(without_estimate),
        first_scheduled_date=first_date, last_scheduled_date=last_date,
    )
