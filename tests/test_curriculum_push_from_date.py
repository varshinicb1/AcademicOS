"""PUSH's fromDate is a real YYYY-MM-DD day, compared as a date (audit D116).

Before: the route took fromDate as text and compared it with each lesson's
date as text. "2026-13-05" returned 200 and pushed every 2027 lesson, and
"2026-10-5" sorts after every October date, so it pushed from November and
moved no October lesson.
"""
from __future__ import annotations

import pytest

from test_section_plans import BASE, _route_plan, world  # noqa: F401  (fixture)

from academicos.assessment.audit_log import AuditLog
from academicos.curriculum import scheduling


def _push(w, from_date):
    return w.c.post(f"{BASE}/books/{w.book}/schedule/push", params={"academic_year_id": w.year},
                    json={"fromDate": from_date, "reason": "school closed", "sectionId": w.a}, headers=w.p)


@pytest.mark.parametrize("bad", ["2026-13-05", "2026-06-8", "2026-6-08", "20260608", "2026-W24-1",
                                 "next monday", ""])
def test_a_from_date_that_is_not_a_day_is_refused_and_moves_nothing(world, bad):
    w = world
    assert _route_plan(w, w.a).status_code == 200
    before = [(l.id, l.date) for l in w.store.scheduled_lessons_for_book(w.year, w.book, w.a)]
    r = _push(w, bad)
    assert r.status_code == 422, r.text
    assert "YYYY-MM-DD" in r.text
    assert [(l.id, l.date) for l in w.store.scheduled_lessons_for_book(w.year, w.book, w.a)] == before


def test_a_real_day_pushes_from_that_day_and_not_before(world):
    w = world
    assert _route_plan(w, w.a).status_code == 200
    before = {l.id: l.date for l in w.store.scheduled_lessons_for_book(w.year, w.book, w.a)}
    r = _push(w, "2026-06-08")
    assert r.status_code == 200, r.text
    moved = r.json()["reschedules"]
    assert moved and min(m["oldDate"] for m in moved) == "2026-06-08"
    after = {l.id: l.date for l in w.store.scheduled_lessons_for_book(w.year, w.book, w.a)}
    assert all(after[i] == d for i, d in before.items() if d < "2026-06-08")


def test_the_scheduler_refuses_a_text_date_too(world, tmp_path):
    w = world
    _route_plan(w, w.a)
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        scheduling.push_lessons_after(w.store, AuditLog(tmp_path / "audit.sqlite"), academic_year_id=w.year,
                                      book_id=w.book, from_date="2026-6-8", reason="x", changed_by="p1",
                                      section_id=w.a)
