"""A lesson cannot be marked taught, partly taught or not taught before its
day (audit D67).

Before: on 2026-09-27, PATCH `completed` on lessons dated 2026-09-28 and
09-29 returned 200, and the principal's coverage then read
`completedLessons 4, overallCoveragePct 1.36` with `plannedToDate 0`.
"""
from __future__ import annotations

import pytest

from test_section_plans import BASE, _route_plan, world  # noqa: F401  (fixture)

TODAY = "2026-06-01"     # the fixture pins the school's today here


def _lesson_on(w, day):
    return next(l for l in w.store.scheduled_lessons_for_book(w.year, w.book, w.a) if l.date == day)


@pytest.mark.parametrize("status", ["completed", "partly", "skipped"])
def test_a_future_lesson_cannot_be_marked(world, status):
    w = world
    assert _route_plan(w, w.a).status_code == 200
    tomorrow = _lesson_on(w, "2026-06-02")
    n = len(w.store.scheduled_lessons_for_book(w.year, w.book, w.a))
    r = w.c.patch(f"{BASE}/scheduled-lessons/{tomorrow.id}", json={"status": status}, headers=w.ana)
    assert r.status_code == 409, r.text
    assert "2026-06-02" in r.json()["detail"] and "after today" in r.json()["detail"]
    assert w.store.get_scheduled_lesson(tomorrow.id).status == "scheduled"
    assert len(w.store.scheduled_lessons_for_book(w.year, w.book, w.a)) == n, "nothing was re-planned"
    # Not even the principal: the date has not come for anyone.
    assert w.c.patch(f"{BASE}/scheduled-lessons/{tomorrow.id}", json={"status": status},
                     headers=w.p).status_code == 409


def test_todays_lesson_is_marked_and_coverage_counts_only_it(world):
    w = world
    assert _route_plan(w, w.a).status_code == 200
    today = _lesson_on(w, TODAY)
    assert w.c.patch(f"{BASE}/scheduled-lessons/{today.id}", json={"status": "completed"},
                     headers=w.ana).status_code == 200
    w.c.patch(f"{BASE}/scheduled-lessons/{_lesson_on(w, '2026-06-03').id}", json={"status": "completed"},
              headers=w.ana)
    report = w.c.get(f"{BASE}/reporting/coverage", params={"academic_year_id": w.year, "as_of_date": TODAY},
                     headers=w.p).json()
    assert report["completedLessons"] == 1 and report["completedToDate"] == 1
    # Undoing a mark is always allowed.
    assert w.c.patch(f"{BASE}/scheduled-lessons/{today.id}", json={"status": "scheduled"},
                     headers=w.ana).status_code == 200
