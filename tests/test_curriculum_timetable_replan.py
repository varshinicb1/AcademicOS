"""A mid-term timetable change re-lays the section's plan on its new week
(v3 audit N-3-14, SCH-4 / SCH-8).

Before: `PUT /sections/{id}/timetable` and a published solve rewrote
timetable_entries and never touched scheduled_lessons. Moving 10-A's Monday
Science period to Wednesday left 25 of 198 future Science lessons on
Mondays, when 10-A has no Science -- the teacher saw lessons on days she
does not teach the class.
"""
from __future__ import annotations

from collections import Counter
from datetime import date

import pytest

from test_section_plans import A_DAYS, BASE, _route_plan, world  # noqa: F401  (fixture)

NEW_A_WEEK = [(d, 1) for d in A_DAYS if d != 0] + [(2, 3)]   # Monday's period moves to Wednesday


def _a_lessons(w):
    return w.store.scheduled_lessons_for_book(w.year, w.book, w.a)


def test_a_section_week_change_moves_its_future_lessons_onto_the_new_week(world):
    w = world
    assert _route_plan(w, w.a).status_code == 200
    assert _route_plan(w, w.b).status_code == 200
    first = _a_lessons(w)[0]
    assert first.date == "2026-06-01" and date.fromisoformat(first.date).weekday() == 0
    assert w.c.patch(f"{BASE}/scheduled-lessons/{first.id}", json={"status": "completed"},
                     headers=w.ana).status_code == 200
    b_before = [(l.id, l.date) for l in w.store.scheduled_lessons_for_book(w.year, w.book, w.b)]
    n_before = len(_a_lessons(w))
    on_mondays = [l.id for l in _a_lessons(w)
                  if l.date > "2026-06-01" and date.fromisoformat(l.date).weekday() == 0]
    assert on_mondays

    r = w.c.put(f"{BASE}/sections/{w.a}/timetable", headers=w.p, json={"entries": [
        {"dayOfWeek": d, "period": p, "subjectId": w.subject} for d, p in NEW_A_WEEK]})
    assert r.status_code == 200, r.text

    lessons = _a_lessons(w)
    assert len(lessons) == n_before, "nothing is added or lost, only moved"
    still_to_teach = [l for l in lessons if l.status == "scheduled"]
    stranded = [l.date for l in still_to_teach if date.fromisoformat(l.date).weekday() == 0]
    assert stranded == [], f"{len(stranded)} lessons left on Mondays, when 10-A has no Science"
    per_day = Counter(l.date for l in still_to_teach)
    assert all(n <= (2 if date.fromisoformat(d).weekday() == 2 else 1) for d, n in per_day.items())
    assert any(n == 2 for d, n in per_day.items()), "the new Wednesday period is used"

    # The taught lesson keeps its day; the other section's plan is not touched.
    assert next(l for l in lessons if l.id == first.id).date == "2026-06-01"
    assert [(l.id, l.date) for l in w.store.scheduled_lessons_for_book(w.year, w.book, w.b)] == b_before

    # Each move is on the lesson's history, with the reason.
    history = w.c.get(f"{BASE}/scheduled-lessons/{on_mondays[0]}/history", headers=w.p).json()
    assert history and "timetable changed" in history[0]["reason"]


def test_an_unchanged_week_moves_nothing(world):
    w = world
    assert _route_plan(w, w.a).status_code == 200
    before = [(l.id, l.date) for l in _a_lessons(w)]
    r = w.c.put(f"{BASE}/sections/{w.a}/timetable", headers=w.p, json={"entries": [
        {"dayOfWeek": d, "period": 1, "subjectId": w.subject} for d in A_DAYS]})
    assert r.status_code == 200, r.text
    assert [(l.id, l.date) for l in _a_lessons(w)] == before


def test_a_published_solve_that_changes_the_week_moves_the_plan_too(world):
    """The solver's publish is the other way a section's periods change."""
    pytest.importorskip("ortools")
    w = world
    assert _route_plan(w, w.a).status_code == 200
    ana = w.store.allocation_for(w.a, w.subject).teacher_id
    # 10-A's teacher is away every Monday from now on; one double period
    # keeps the six a week inside five days.
    w.store.set_allocation(section_id=w.a, subject_id=w.subject, teacher_id=ana, periods_per_week=6,
                           double_periods=1)
    r = w.c.put(f"{BASE}/academic-years/{w.year}/teacher-unavailability/{ana}", headers=w.p,
                json={"slots": [{"dayOfWeek": 0, "period": p} for p in range(1, 7)]})
    assert r.status_code == 200, r.text
    solved = w.c.post(f"{BASE}/academic-years/{w.year}/timetable/solve", headers=w.p,
                      json={"apply": True, "sectionIds": [w.a]})
    assert solved.status_code == 200 and solved.json()["applied"] is True, solved.text
    week = Counter(e.day_of_week for e in w.store.timetable_for_section(w.a) if e.subject_id == w.subject)
    assert 0 not in week
    future = [l for l in _a_lessons(w) if l.status == "scheduled" and l.date >= "2026-06-01"]
    assert future and all(date.fromisoformat(l.date).weekday() in week for l in future)
    per_day = Counter(l.date for l in future)
    assert all(n <= week[date.fromisoformat(d).weekday()] for d, n in per_day.items())
