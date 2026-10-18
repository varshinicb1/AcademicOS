"""curriculum/calendar.py -- Academic Year -> Working Days -> Holidays ->
Period Duration -> Teaching-Time Estimate (§10, §27-29).

Two halves: pure-function tests for compute_working_days() (no store
dependency, exact date arithmetic), and store-backed tests for
working_days_for_year() / compute_teaching_time_estimates() covering the
real error paths (no calendar yet, no period configuration yet, no
marks-weightage to distribute by) and the real distribution + idempotency
guarantees.
"""
from __future__ import annotations

from store_backend import sqlite_only
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.curriculum import calendar as calendar_mod
from academicos.curriculum.store import CurriculumStore


@pytest.fixture
def store(tmp_path):
    s = CurriculumStore(tmp_path / "curriculum.sqlite")
    yield s
    s.close()


# --------------------------------------------------------------------- #
# compute_working_days -- pure function, no store
# --------------------------------------------------------------------- #

def test_single_day_range_is_inclusive_and_working():
    # 2026-09-14 is a Monday.
    r = calendar_mod.compute_working_days(
        start_date="2026-09-14", end_date="2026-09-14", weekly_off_days=["sunday"],
        alternate_saturday_rule="none", holiday_dates=set())
    assert r.total_days == 1
    assert r.working_days == 1
    assert r.dates == ("2026-09-14",)


def test_end_before_start_raises():
    with pytest.raises(ValueError):
        calendar_mod.compute_working_days(
            start_date="2026-09-14", end_date="2026-09-01", weekly_off_days=["sunday"],
            alternate_saturday_rule="none", holiday_dates=set())


def test_one_week_sunday_off_only():
    # 2026-09-14 (Mon) .. 2026-09-20 (Sun): 6 working days, 1 Sunday off.
    r = calendar_mod.compute_working_days(
        start_date="2026-09-14", end_date="2026-09-20", weekly_off_days=["sunday"],
        alternate_saturday_rule="none", holiday_dates=set())
    assert r.total_days == 7
    assert r.working_days == 6
    assert r.weekly_off_count == 1
    assert r.alternate_saturday_off_count == 0
    assert "2026-09-20" not in r.dates  # the Sunday


def test_alternate_saturday_rule_2nd_4th():
    # September 2026 Saturdays: 5th, 12th, 19th, 26th -> 2nd=12th, 4th=26th.
    r = calendar_mod.compute_working_days(
        start_date="2026-09-01", end_date="2026-09-30", weekly_off_days=["sunday"],
        alternate_saturday_rule="2nd,4th", holiday_dates=set())
    assert "2026-09-12" not in r.dates
    assert "2026-09-26" not in r.dates
    assert "2026-09-05" in r.dates   # 1st Saturday -- a working day under this rule
    assert "2026-09-19" in r.dates   # 3rd Saturday -- a working day under this rule
    assert r.alternate_saturday_off_count == 2


def test_alternate_saturday_rule_all():
    r = calendar_mod.compute_working_days(
        start_date="2026-09-01", end_date="2026-09-30", weekly_off_days=["sunday"],
        alternate_saturday_rule="all", holiday_dates=set())
    assert r.alternate_saturday_off_count == 4  # every Saturday in September 2026
    assert "2026-09-05" not in r.dates
    assert "2026-09-12" not in r.dates
    assert "2026-09-19" not in r.dates
    assert "2026-09-26" not in r.dates


def test_holiday_on_a_weekday_is_excluded_and_counted_once():
    # 2026-10-02 (Gandhi Jayanti) is a Friday in 2026 -- a real national holiday.
    r = calendar_mod.compute_working_days(
        start_date="2026-09-28", end_date="2026-10-04", weekly_off_days=["sunday"],
        alternate_saturday_rule="none", holiday_dates={"2026-10-02"})
    assert r.holiday_count == 1
    assert "2026-10-02" not in r.dates
    # total_days(7) = working(5) + weekly_off(1, the Sunday) + holiday(1)
    assert r.total_days == r.working_days + r.weekly_off_count + r.alternate_saturday_off_count + r.holiday_count


def test_holiday_that_falls_on_a_weekly_off_day_does_not_double_subtract():
    # A "holiday" declared on a date that's already a weekly off (e.g. a
    # Sunday) must not be double-counted -- precedence rule: weekly-off wins,
    # holiday_count stays 0 for that date.
    r = calendar_mod.compute_working_days(
        start_date="2026-09-14", end_date="2026-09-20", weekly_off_days=["sunday"],
        alternate_saturday_rule="none", holiday_dates={"2026-09-20"})  # the Sunday
    assert r.weekly_off_count == 1
    assert r.holiday_count == 0
    assert r.working_days == 6


def test_date_range_helper_is_inclusive_of_both_ends():
    assert calendar_mod._date_range("2026-05-01", "2026-05-03") == [
        "2026-05-01", "2026-05-02", "2026-05-03"]


def test_date_range_helper_single_day():
    assert calendar_mod._date_range("2026-05-01", "2026-05-01") == ["2026-05-01"]


# --------------------------------------------------------------------- #
# Multi-day (block) holidays -- a real summer break, not one row per date
# --------------------------------------------------------------------- #

def test_add_holiday_rejects_end_date_before_start_date(store):
    year = store.create_academic_year(school_id="s", label="y",
                                      start_date="2026-06-01", end_date="2027-03-31")
    cal = store.create_calendar(academic_year_id=year.id)
    with pytest.raises(ValueError, match="end_date"):
        store.add_holiday(calendar_id=cal.id, date="2026-06-10", label="bad range",
                          end_date="2026-06-01")


def test_single_day_holiday_still_has_no_end_date(store):
    year = store.create_academic_year(school_id="s", label="y",
                                      start_date="2026-06-01", end_date="2027-03-31")
    cal = store.create_calendar(academic_year_id=year.id)
    h = store.add_holiday(calendar_id=cal.id, date="2026-08-15", label="Independence Day")
    assert h.end_date is None
    fetched = store.holidays_for_calendar(cal.id)[0]
    assert fetched.end_date is None


def test_multi_day_summer_break_removes_every_date_in_the_range(store):
    # A real 32-day summer break -- one row, not 32.
    year = store.create_academic_year(school_id="s", label="y",
                                      start_date="2026-05-01", end_date="2027-04-30")
    cal = store.create_calendar(academic_year_id=year.id, weekly_off_days=["sunday"])
    store.add_holiday(calendar_id=cal.id, date="2026-05-15", end_date="2026-06-15",
                      label="Summer break", kind="holiday")

    result = calendar_mod.working_days_for_year(store, year.id)
    # Every date in the block, including both ends and any Sundays inside it
    # (weekly-off still wins precedence, but the date is excluded either way).
    for d in ("2026-05-15", "2026-05-30", "2026-06-15"):
        assert d not in result.dates
    assert "2026-05-14" in result.dates   # the day before the break: unaffected
    assert "2026-06-16" in result.dates   # the day after the break: unaffected


def test_multi_day_event_marker_does_not_remove_any_date(store):
    # An "event" kind spanning a range (e.g. a multi-day sports meet) must not
    # remove teaching days, same rule as a single-day event.
    year = store.create_academic_year(school_id="s", label="y",
                                      start_date="2026-09-01", end_date="2026-09-30")
    cal = store.create_calendar(academic_year_id=year.id, weekly_off_days=["sunday"])
    store.add_holiday(calendar_id=cal.id, date="2026-09-10", end_date="2026-09-12",
                      label="Sports Week", kind="event")
    result = calendar_mod.working_days_for_year(store, year.id)
    for d in ("2026-09-10", "2026-09-11", "2026-09-12"):
        assert d in result.dates


@sqlite_only
def test_migration_adds_end_date_column_to_a_pre_existing_database(tmp_path):
    """Real production concern: school_1 already has real seeded holiday rows
    under the OLD schema (no end_date column) by the time this feature ships.
    Opening that same database file again must not crash, and the new
    end_date-aware add_holiday() must work against it afterward."""
    import sqlite3
    db_path = tmp_path / "curriculum.sqlite"

    # Simulate a pre-existing database created before end_date existed.
    conn = sqlite3.connect(str(db_path))
    conn.execute("""CREATE TABLE holidays (
        id TEXT PRIMARY KEY, calendar_id TEXT NOT NULL, date TEXT NOT NULL,
        label TEXT NOT NULL, kind TEXT NOT NULL DEFAULT 'holiday')""")
    conn.execute("INSERT INTO holidays VALUES ('holiday_old', 'cal_1', '2026-08-15', "
                 "'Independence Day', 'holiday')")
    conn.commit()
    conn.close()

    # Opening it through CurriculumStore must migrate in place, not crash.
    s = CurriculumStore(db_path)
    try:
        cols = {r["name"] for r in s.conn.execute("PRAGMA table_info(holidays)").fetchall()}
        assert "end_date" in cols
        # The pre-existing row survived the migration with end_date=NULL.
        old = s.holidays_for_calendar("cal_1")
        assert len(old) == 1
        assert old[0].end_date is None
        # And the new code path works against the migrated table.
        s.add_holiday(calendar_id="cal_1", date="2026-12-20", end_date="2027-01-02",
                     label="Winter break")
        assert len(s.holidays_for_calendar("cal_1")) == 2
    finally:
        s.close()


# --------------------------------------------------------------------- #
# working_days_for_year -- store-backed
# --------------------------------------------------------------------- #

def test_working_days_for_year_raises_without_calendar(store):
    year = store.create_academic_year(school_id="s", label="y",
                                      start_date="2026-06-01", end_date="2027-03-31")
    with pytest.raises(ValueError, match="no calendar"):
        calendar_mod.working_days_for_year(store, year.id)


def test_working_days_for_year_raises_for_unknown_year(store):
    with pytest.raises(ValueError, match="no such academic year"):
        calendar_mod.working_days_for_year(store, "not_a_real_year")


def test_working_days_for_year_real_computation(store):
    year = store.create_academic_year(school_id="s", label="y",
                                      start_date="2026-09-01", end_date="2026-09-30")
    cal = store.create_calendar(academic_year_id=year.id, weekly_off_days=["sunday"],
                                alternate_saturday_rule="2nd,4th")
    store.add_holiday(calendar_id=cal.id, date="2026-10-02", label="outside range", kind="holiday")
    store.add_holiday(calendar_id=cal.id, date="2026-09-15", label="Local closure", kind="unexpected_closure")
    store.add_holiday(calendar_id=cal.id, date="2026-09-18", label="Annual Day", kind="event")  # not a closure

    result = calendar_mod.working_days_for_year(store, year.id)
    assert result.total_days == 30
    assert "2026-09-15" not in result.dates          # unexpected_closure removes a day
    assert "2026-09-18" in result.dates              # a plain "event" marker does NOT remove a day


# --------------------------------------------------------------------- #
# compute_teaching_time_estimates -- store-backed
# --------------------------------------------------------------------- #

def _seed_hierarchy(store, *, school_id="school_1"):
    """Two real units under one book, each with one chapter -> one topic ->
    three subtopics, mirroring a real approved chapter's shape. Unit marks
    are deliberately unequal (30 vs 10) to exercise proportional
    distribution, not just an even split."""
    board = store.create_board(name="CBSE", code="CBSE")
    year = store.create_academic_year(school_id=school_id, label="2026-27",
                                      start_date="2026-06-01", end_date="2027-03-31")
    grade = store.create_grade(academic_year_id=year.id, number=10)
    subject = store.create_subject(grade_id=grade.id, name="Science")
    book = store.create_book(subject_id=subject.id, board_id=board.id, title="Book")

    unit_a = store.create_unit(canonical_id="u:A", book_id=book.id, unit_no="I", name="Unit A", marks=30, seq=0)
    unit_b = store.create_unit(canonical_id="u:B", book_id=book.id, unit_no="II", name="Unit B", marks=10, seq=1)

    def _add_subtopics(unit, n, prefix):
        chapter = store.create_chapter(canonical_id=f"c:{prefix}", unit_id=unit.id, name=f"Chapter {prefix}", seq=0)
        topic = store.create_topic(canonical_id=f"t:{prefix}", chapter_id=chapter.id, name=f"Topic {prefix}", seq=0)
        ids = []
        for i in range(n):
            st = store.create_subtopic(canonical_id=f"st:{prefix}:{i}", topic_id=topic.id,
                                       name=f"Subtopic {prefix}{i}", seq=i)
            ids.append(st.id)
        return ids

    unit_a_subtopic_ids = _add_subtopics(unit_a, 3, "A")
    unit_b_subtopic_ids = _add_subtopics(unit_b, 2, "B")
    # The estimate is budgeted against the year's real teaching periods
    # (since 2026-09-22), so it needs the real calendar.
    store.create_calendar(academic_year_id=year.id, weekly_off_days=["sunday"],
                          alternate_saturday_rule="none")

    return book.id, year.id, unit_a_subtopic_ids, unit_b_subtopic_ids


def test_compute_teaching_time_raises_without_period_configuration(store):
    book_id, year_id, _, _ = _seed_hierarchy(store)
    with pytest.raises(ValueError, match="no period configuration"):
        calendar_mod.compute_teaching_time_estimates(
            store, academic_year_id=year_id, book_id=book_id, periods_per_week=6)


def test_compute_teaching_time_raises_for_non_positive_periods_per_week(store):
    book_id, year_id, _, _ = _seed_hierarchy(store)
    store.create_period_configuration(school_id="school_1", academic_year_id=year_id, period_minutes=40)
    with pytest.raises(ValueError):
        calendar_mod.compute_teaching_time_estimates(
            store, academic_year_id=year_id, book_id=book_id, periods_per_week=0)


def test_compute_teaching_time_raises_without_unit_marks(store):
    board = store.create_board(name="CBSE", code="CBSE")
    year = store.create_academic_year(school_id="s", label="y", start_date="2026-06-01", end_date="2027-03-31")
    grade = store.create_grade(academic_year_id=year.id, number=10)
    subject = store.create_subject(grade_id=grade.id, name="Science")
    book = store.create_book(subject_id=subject.id, board_id=board.id, title="Book")
    store.create_unit(canonical_id="u:none", book_id=book.id, unit_no="I", name="No marks", marks=None, seq=0)
    store.create_period_configuration(school_id="s", academic_year_id=year.id, period_minutes=40)

    with pytest.raises(ValueError, match="marks-weightage"):
        calendar_mod.compute_teaching_time_estimates(
            store, academic_year_id=year.id, book_id=book.id, periods_per_week=6)


def test_compute_teaching_time_distributes_proportionally_and_sums_exactly(store):
    book_id, year_id, unit_a_ids, unit_b_ids = _seed_hierarchy(store)
    store.create_period_configuration(school_id="school_1", academic_year_id=year_id, period_minutes=40)

    result = calendar_mod.compute_teaching_time_estimates(
        store, academic_year_id=year_id, book_id=book_id, periods_per_week=6, approved_by="principal_1")

    assert result.units_skipped_no_subtopics == ()
    assert len(result.estimates) == 5  # 3 subtopics in unit A + 2 in unit B
    # Largest-remainder rounding: per-subtopic minutes sum exactly to the
    # total, no drift from naive independent rounding.
    assert sum(e.estimated_minutes for e in result.estimates) == result.total_instructional_minutes

    # Unit A carries 3x Unit B's marks (30 vs 10) -> its 3 subtopics should
    # collectively get ~3x Unit B's 2 subtopics' total minutes.
    unit_a_ids_set, unit_b_ids_set = set(unit_a_ids), set(unit_b_ids)
    unit_a_minutes = sum(e.estimated_minutes for e in result.estimates if e.subtopic_id in unit_a_ids_set)
    unit_b_minutes = sum(e.estimated_minutes for e in result.estimates if e.subtopic_id in unit_b_ids_set)
    assert unit_a_minutes > unit_b_minutes
    ratio = unit_a_minutes / unit_b_minutes
    assert 2.5 < ratio < 3.5  # allows for integer-minute rounding slack

    for e in result.estimates:
        assert e.method == "marks_weightage_proportional"
        assert e.approved_by == "principal_1"


def test_compute_teaching_time_skips_units_with_no_subtopics_yet(store):
    board = store.create_board(name="CBSE", code="CBSE")
    year = store.create_academic_year(school_id="s", label="y", start_date="2026-06-01", end_date="2027-03-31")
    grade = store.create_grade(academic_year_id=year.id, number=10)
    subject = store.create_subject(grade_id=grade.id, name="Science")
    book = store.create_book(subject_id=subject.id, board_id=board.id, title="Book")
    store.create_unit(canonical_id="u:empty", book_id=book.id, unit_no="I", name="Not decomposed yet", marks=25, seq=0)
    store.create_period_configuration(school_id="s", academic_year_id=year.id, period_minutes=40)
    store.create_calendar(academic_year_id=year.id, weekly_off_days=["sunday"])

    result = calendar_mod.compute_teaching_time_estimates(
        store, academic_year_id=year.id, book_id=book.id, periods_per_week=6)
    assert result.units_skipped_no_subtopics == ("Not decomposed yet",)
    assert result.estimates == ()


def test_compute_teaching_time_is_idempotent_per_subtopic(store):
    """§29: an admin's prior hand-adjusted estimate must not be silently
    clobbered by a re-run -- create_teaching_time_estimate is called only
    for subtopics that don't already have one for this academic year."""
    book_id, year_id, _, _ = _seed_hierarchy(store)
    store.create_period_configuration(school_id="school_1", academic_year_id=year_id, period_minutes=40)

    first = calendar_mod.compute_teaching_time_estimates(
        store, academic_year_id=year_id, book_id=book_id, periods_per_week=6)
    assert len(first.estimates) == 5

    second = calendar_mod.compute_teaching_time_estimates(
        store, academic_year_id=year_id, book_id=book_id, periods_per_week=6)
    assert second.estimates == ()  # nothing new created -- every subtopic already has one
