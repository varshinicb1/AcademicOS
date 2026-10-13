"""Coverage reads the school's today, as delayed topics do (audit D66), and
today's lessons are not behind before they have been taught or missed
(handover §9, ADM-2 and ADM-3).

Before D66: `store.get_coverage_report` defaulted its as-of date to the
server's UTC date, while `/reporting/delayed-topics` used the school's IST
today. The web sends no asOfDate, so between 00:00 and 05:30 IST Coverage &
Pace showed yesterday's figures beside today's overdue list.

Before 2026-10-13: every lesson dated today counted as planned to date the
moment the day began, so each morning every class read as behind by its day's
lessons, on Coverage & Pace and on the term report, until a teacher marked
them. Delayed topics and the 08:00 "behind plan" alert already waited for the
day to pass.
"""
from __future__ import annotations

from test_section_plans import BASE, _route_plan, world  # noqa: F401  (fixture)

TODAY = "2026-06-01"     # the fixture pins the school's today here


def _lesson_on(w, day):
    return next(l for l in w.store.scheduled_lessons_for_book(w.year, w.book, w.a) if l.date == day)


def _coverage(w, **params):
    r = w.c.get(f"{BASE}/reporting/coverage", params={"academic_year_id": w.year, **params}, headers=w.p)
    assert r.status_code == 200, r.text
    return r.json()


def test_coverage_and_delayed_topics_share_the_schools_today(world):
    w = world
    assert _route_plan(w, w.a).status_code == 200
    coverage = _coverage(w)
    delayed = w.c.get(f"{BASE}/reporting/delayed-topics", params={"academic_year_id": w.year}, headers=w.p)
    assert delayed.status_code == 200
    assert coverage["asOfDate"] == delayed.json()["asOfDate"] == TODAY

    # An explicit date still wins, and reads to the end of that day: 1 to 6 June.
    explicit = _coverage(w, as_of_date="2026-06-06")
    assert explicit["asOfDate"] == "2026-06-06" and explicit["plannedToDate"] == 6


def test_todays_lesson_is_not_behind_until_it_is_marked(world):
    w = world
    assert _route_plan(w, w.a).status_code == 200
    lesson = _lesson_on(w, TODAY)

    # The morning of day one: 10-A's lesson of today is planned, not yet behind.
    morning = _coverage(w)
    assert morning["plannedToDate"] == 0 and morning["overallVariance"] == 0
    assert [s["variance"] for s in morning["subjects"]] == [0]
    term = w.c.get("/api/v1/dashboard/term", headers=w.p)
    assert term.status_code == 200, term.text
    assert term.json()["syllabus"]["behind"] == 0

    # Taught today: due and done.
    assert w.c.patch(f"{BASE}/scheduled-lessons/{lesson.id}", json={"status": "completed"},
                     headers=w.ana).status_code == 200
    taught = _coverage(w)
    assert (taught["plannedToDate"], taught["completedToDate"], taught["overallVariance"]) == (1, 1, 0)

    # Marked not taught today: due, not done, so behind by one.
    assert w.c.patch(f"{BASE}/scheduled-lessons/{lesson.id}", json={"status": "scheduled"},
                     headers=w.ana).status_code == 200
    assert w.c.patch(f"{BASE}/scheduled-lessons/{lesson.id}", json={"status": "skipped"},
                     headers=w.ana).status_code == 200
    missed = _coverage(w)
    assert (missed["plannedToDate"], missed["completedToDate"], missed["overallVariance"]) == (1, 0, -1)
    assert w.c.get("/api/v1/dashboard/term", headers=w.p).json()["syllabus"]["behind"] == 1


def test_a_past_day_counts_its_unmarked_lessons(world, monkeypatch):
    """Only today waits for its marks. Read as of a day that is over, that
    day's unmarked lessons are due -- a term that ended, or a date asked for."""
    from datetime import date

    from academicos.curriculum import routes as cr
    w = world
    assert _route_plan(w, w.a).status_code == 200
    # The school's today moves on to 3 June; 1 and 2 June were never marked.
    monkeypatch.setattr(cr, "_school_today", lambda: date(2026, 6, 3))
    assert _coverage(w, as_of_date="2026-06-02")["plannedToDate"] == 2
    later = _coverage(w)
    assert later["asOfDate"] == "2026-06-03"
    assert (later["plannedToDate"], later["overallVariance"]) == (2, -2), "3 June's lesson is not behind yet"
