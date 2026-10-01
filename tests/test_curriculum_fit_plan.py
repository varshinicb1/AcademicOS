"""A mid-year plan can be fitted to the periods left (audit D35).

Before: the estimates are sized for the whole year, so a plan made mid-year
dated what fit and left the rest undated -- 60 of 117 Science 10 subtopics
had no date ("160 teaching periods left ... the estimates need 313") -- and
no route could fit it: re-estimating at fewer periods a week was overridden
by the timetable, and no route edits an estimate.
"""
from __future__ import annotations

from collections import Counter
from datetime import date

import pytest

from academicos.curriculum import scheduling

from test_section_plans import BASE, _seed, store, world  # noqa: F401  (fixtures)

LATE = "2027-02-01"       # two months of the year left


def _plan(store, w, **kw):
    return scheduling.schedule_book(store, school_id=w.school, academic_year_id=w.year, book_id=w.book,
                                    periods_per_week=6, from_date=LATE, section_id=w.a, **kw)


def test_fit_periods_scales_in_proportion_with_one_each_at_least():
    assert scheduling.fit_periods([10, 10, 20], 40) == [10, 10, 20], "already fits"
    fitted = scheduling.fit_periods([10, 30, 2, 1], 20)
    assert sum(fitted) == 20 and all(1 <= f <= n for f, n in zip(fitted, [10, 30, 2, 1]))
    assert fitted[1] > fitted[0] > fitted[2] >= fitted[3] == 1
    assert scheduling.fit_periods([5, 5, 5], 2) == [1, 1, 1], "fewer periods than subtopics"


def test_without_fit_a_late_plan_leaves_the_syllabus_undated(store):
    w = _seed(store)
    r = _plan(store, w)
    assert r.subtopics_unscheduled, "the year's estimates do not fit two months"
    assert r.all_subtopics_scheduled is False and r.subtopics_compressed == () and r.fit_note is None


def test_fitted_every_subtopic_gets_a_date_and_the_compression_is_reported(store):
    w = _seed(store)
    r = _plan(store, w, fit_to_periods_left=True)
    assert r.warning is None and r.all_subtopics_scheduled
    assert not r.subtopics_unscheduled and not r.subtopics_partially_scheduled
    assert r.lessons_created == r.teaching_periods_available, "every period left is used"
    per_subtopic = Counter(l.subtopic_id for l in store.scheduled_lessons_for_book(w.year, w.book, w.a))
    assert len(per_subtopic) == 12 and min(per_subtopic.values()) >= 1
    assert r.subtopics_compressed and all(c.periods_planned < c.periods_needed for c in r.subtopics_compressed)
    for c in r.subtopics_compressed:
        assert per_subtopic[c.subtopic_id] == c.periods_planned
    assert f"fitted to the {r.teaching_periods_available} teaching periods left from {LATE}" in r.fit_note
    # The book's estimates (shared by every section) are not changed.
    est = store.teaching_time_estimate_for_subtopic(r.subtopics_compressed[0].subtopic_id, w.year)
    assert est.estimated_periods == r.subtopics_compressed[0].periods_needed


def test_the_routes_fit_on_request(world, monkeypatch):
    from academicos.curriculum import routes as curriculum_routes
    w = world
    monkeypatch.setattr(curriculum_routes, "_school_today", lambda: date.fromisoformat(LATE))
    plain = w.c.post(f"{BASE}/books/{w.book}/schedule", params={"academic_year_id": w.year},
                     json={"sectionId": w.a}, headers=w.p)
    assert plain.status_code == 200 and plain.json()["subtopicsUnscheduled"]
    fitted = w.c.post(f"{BASE}/books/{w.book}/schedule", params={"academic_year_id": w.year},
                      json={"sectionId": w.a, "force": True, "fitToPeriodsLeft": True}, headers=w.p)
    assert fitted.status_code == 200, fitted.text
    body = fitted.json()
    assert body["allSubtopicsScheduled"] is True and body["subtopicsUnscheduled"] == []
    assert body["subtopicsCompressed"] and body["fitNote"].startswith("fitted to the")
    assert {"subtopicId", "periodsNeeded", "periodsPlanned"} <= set(body["subtopicsCompressed"][0])

    built = w.c.post(f"{BASE}/academic-years/{w.year}/lesson-plans", headers=w.p,
                     json={"fitToPeriodsLeft": True})
    assert built.status_code == 200, built.text
    plans = {p["sectionName"]: p for p in built.json()["plans"]}
    assert plans["10-A"]["subtopicsCompressed"] > 0 and plans["10-A"]["fitNote"]
    assert plans["10-A"]["warning"] is None


@pytest.mark.parametrize("fit", [False, True])
def test_a_plan_that_already_fits_is_the_same_either_way(store, fit):
    w = _seed(store)
    r = scheduling.schedule_book(store, school_id=w.school, academic_year_id=w.year, book_id=w.book,
                                 periods_per_week=6, from_date="2026-06-01", section_id=w.a,
                                 fit_to_periods_left=fit)
    assert r.warning is None and r.subtopics_compressed == () and r.fit_note is None
