"""TA-1: a lesson nobody marks never reflows the plan, so a forgotten mark
leaves the plan and the coverage figures wrong in silence. On a teaching
day's afternoon each teacher hears how many of their lessons from the last
week are still unmarked."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from test_homework import w  # noqa: F401 - `w` is a fixture

IST = timezone(timedelta(hours=5, minutes=30))


def _plan(w):
    """A Science 10 book with one subtopic, and lessons for 10-A (Ana) and
    10-B (Bala) on 2026-06-01 (today, a Monday) and the Saturday before."""
    s = w.store
    board = s.create_board(name="CBSE", code="CBSE")
    book = s.create_book(subject_id=w.sci10, board_id=board.id, title="Science 10")
    unit = s.create_unit(canonical_id="u:1", book_id=book.id, unit_no="1", name="Unit 1", marks=20, seq=0)
    chapter = s.create_chapter(canonical_id="c:light", unit_id=unit.id, name="Light", seq=0)
    topic = s.create_topic(canonical_id="t:1", chapter_id=chapter.id, name="Reflection", seq=0)
    sub = s.create_subtopic(canonical_id="st:1", topic_id=topic.id, name="Mirrors", seq=0)

    def lesson(section, day, status="scheduled"):
        return s.create_scheduled_lesson(school_id="school_1", academic_year_id=w.year, book_id=book.id,
                                         subtopic_id=sub.id, date=day, status=status, section_id=section)
    return lesson


def _inbox(w, who):
    return [i for i in w.c.get("/api/v1/notifications", headers=who).json()["items"]
            if i["kind"] == "lessons_unmarked"]


def _at(day: int, hour: int, month: int = 6) -> datetime:
    return datetime(2026, month, day, hour, 30, tzinfo=IST).astimezone(timezone.utc)


def _clear_runs():
    from academicos.operations.routes import store
    with store()._conn_lock:
        store().conn.execute("DELETE FROM automation_runs")
        store()._commit()


def test_a_teacher_hears_of_lessons_still_to_mark_that_afternoon(w):
    from academicos.operations.routes import run_automations
    lesson = _plan(w)
    lesson(w.a10, "2026-05-30")                 # Saturday, forgotten
    lesson(w.a10, "2026-06-01")                 # today, not marked yet
    lesson(w.a10, "2026-05-29", "completed")    # marked: not counted
    lesson(w.a10, "2026-05-20")                 # older than a week: not counted
    lesson(w.a10, "2026-06-02")                 # tomorrow: not due yet
    lesson(w.b10, "2026-06-01", "skipped")      # Bala marked his

    assert run_automations(_at(1, 15))["lessons_unmarked"] == "not yet", "after the school day, not during it"
    assert run_automations(_at(1, 16))["lessons_unmarked"] == 1
    [told] = _inbox(w, w.ana)
    assert told["title"] == "Lessons to mark: 2"
    assert "10-A on 2026-05-30" in told["body"] and told["link"] == "/school/my-day"
    assert _inbox(w, w.bala) == [], "a teacher whose lessons are all marked hears nothing"
    assert run_automations(_at(1, 17))["lessons_unmarked"] == "done", "once a day"


def test_nothing_is_sent_on_a_day_the_plan_does_not_teach(w):
    from academicos.operations.routes import run_automations
    lesson = _plan(w)
    lesson(w.a10, "2026-05-30")                 # Saturday's lesson, still unmarked
    # Sunday 2026-05-31: no lesson is dated today, so it is no teaching day.
    assert run_automations(_at(31, 16, month=5))["lessons_unmarked"] == 0
    assert _inbox(w, w.ana) == []


def test_a_long_leave_replacement_is_told_not_the_teacher_away(w):
    from academicos.operations.routes import run_automations
    lesson = _plan(w)
    lesson(w.a10, "2026-06-01")
    ana_id = w.c.get("/api/v1/auth/me", headers=w.ana).json()["id"]
    bala_id = w.c.get("/api/v1/auth/me", headers=w.bala).json()["id"]
    leave = w.store.apply_for_leave(school_id="school_1", academic_year_id=w.year, teacher_id=ana_id,
                                    start_date="2026-06-01", end_date="2026-06-20", kind="full_day",
                                    reason="Medical", created_by=ana_id)
    w.store.decide_leave(leave.id, approve=True, decided_by="principal")
    w.store.set_leave_replacement(leave.id, bala_id, today="2026-06-01")

    assert run_automations(_at(1, 16))["lessons_unmarked"] == 1
    assert _inbox(w, w.ana) == [], "the teacher on leave did not teach it"
    [told] = _inbox(w, w.bala)
    assert told["title"] == "Lessons to mark: 1"

    _clear_runs()
    w.store.set_leave_replacement(leave.id, None, today="2026-06-01")
    assert run_automations(_at(1, 16))["lessons_unmarked"] == 0, "leave with no replacement: nobody taught it"
