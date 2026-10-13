"""N-67-6: the term report's syllabus section is the chosen term's lessons,
not the year's so far. It used to pass only `as_of_date`, so Term 2 viewed
before it started showed Term 1's lessons as planned to date and behind."""
from __future__ import annotations

from datetime import date, timedelta

from test_curriculum_reschedule_integrity import _seed_book, principal_world  # noqa: F401 - fixture


def _syllabus(w, term_id):
    r = w.client.get("/api/v1/dashboard/term", params={"termId": term_id}, headers=w.auth)
    assert r.status_code == 200, r.text
    return r.json()["syllabus"]


def test_each_terms_syllabus_counts_only_its_own_lessons(principal_world, monkeypatch):
    from academicos.curriculum import routes as cr
    w = principal_world
    book = _seed_book(w.store, school_id="school_1", periods_per_week=6)
    dates = sorted(l.date for l in book.lessons if l.status == "scheduled")
    split = dates[len(dates) // 2]
    after_split = (date.fromisoformat(split) + timedelta(days=1)).isoformat()
    t1 = w.store.create_term(academic_year_id=book.year, name="Term 1", start_date="2026-06-01", end_date=split)
    t2 = w.store.create_term(academic_year_id=book.year, name="Term 2", start_date=after_split,
                             end_date="2027-03-31")
    in_t1 = sum(1 for d in dates if d <= split)
    in_t2 = len(dates) - in_t1
    assert in_t1 and in_t2

    # Before Term 2 starts: it has nothing planned to date and nobody is behind.
    monkeypatch.setattr(cr, "_school_today", lambda: date.fromisoformat(split))
    early = _syllabus(w, t2.id)
    assert early["plannedToDate"] == 0 and early["behind"] == 0
    assert sum(r["totalLessons"] for r in early["rows"]) == in_t2

    # After both (the day after the last lesson: on its own day an unmarked
    # lesson is not behind yet): each term counts its own lessons, and
    # together the year's.
    monkeypatch.setattr(cr, "_school_today", lambda: date.fromisoformat(dates[-1]) + timedelta(days=1))
    one, two = _syllabus(w, t1.id), _syllabus(w, t2.id)
    assert one["plannedToDate"] == in_t1 and sum(r["totalLessons"] for r in one["rows"]) == in_t1
    assert two["plannedToDate"] == in_t2 and sum(r["totalLessons"] for r in two["rows"]) == in_t2
