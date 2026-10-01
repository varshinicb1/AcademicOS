"""A lesson marked not taught, or partly taught, is taught again (v3 audit
N-4-1, TA-1). "Not taught" only set the status: the subtopic silently lost
its period while My day told the teacher the plan would catch up. There was
no "partly" at all (422)."""
from __future__ import annotations

from collections import Counter

from test_curriculum_reschedule_integrity import BASE, _seed_book, principal_world  # noqa: F401


def _mark(w, lesson_id, status, note=None):
    return w.client.patch(f"{BASE}/scheduled-lessons/{lesson_id}", json={"status": status, "note": note},
                          headers=w.auth)


def _plan(w, book):
    return w.store.scheduled_lessons_for_book(book.year, book.book)


def test_not_taught_puts_the_subtopic_back_and_moves_the_rest_on(principal_world):  # noqa: F811
    w = principal_world
    book = _seed_book(w.store, school_id="school_1", periods_per_week=6)
    before = _plan(w, book)
    missed = before[2]
    later = [l for l in before if l.date > missed.date]
    r = _mark(w, missed.id, "skipped", "assembly ran over")
    assert r.status_code == 200 and r.json()["status"] == "skipped"

    after = _plan(w, book)
    assert len(after) == len(before) + 1, "one lesson added for the missed subtopic"
    again = [l for l in after if l.subtopic_id == missed.subtopic_id and l.status == "scheduled"
             and l.date > missed.date]
    assert again, "the missed subtopic is taught again after the missed day"
    moved = {l.id: l.date for l in after}
    assert all(moved[l.id] >= l.date for l in later) and any(moved[l.id] > l.date for l in later), \
        "later lessons move on, never back"
    by_day = Counter(l.date for l in after if l.status != "unscheduled")
    assert max(by_day.values()) <= max(Counter(l.date for l in before).values()), "no day double-booked"

    # Marking it again does not add a second lesson.
    _mark(w, missed.id, "skipped", "still not")
    assert len(_plan(w, book)) == len(after)


def test_partly_taught_counts_as_taught_and_plans_the_rest(principal_world):  # noqa: F811
    w = principal_world
    book = _seed_book(w.store, school_id="school_1", periods_per_week=6)
    before = _plan(w, book)
    lesson = before[1]
    r = _mark(w, lesson.id, "partly", "finished the examples only")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "completed" and r.json()["note"] == "Partly taught: finished the examples only"
    after = _plan(w, book)
    assert len(after) == len(before) + 1
    assert any(l.subtopic_id == lesson.subtopic_id and l.status == "scheduled" and l.date > lesson.date
               for l in after)
    # A plain "completed" adds nothing.
    _mark(w, before[3].id, "completed")
    assert len(_plan(w, book)) == len(after)
