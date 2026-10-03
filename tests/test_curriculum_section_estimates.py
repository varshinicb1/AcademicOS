"""Teaching-time estimates are sized from a section's own week (v3 audit
N-3-8, SCH-4).

Before: `compute_teaching_time_estimates` budgeted the book from the
school-wide per-subject-NAME slots, which a school that builds section
timetables never fills, so the fallback took one period per working day.
`POST /books/{id}/teaching-time-estimates {periodsPerWeek: 9}` gave every
book a budget of 235 -- the year's working days -- for a subject its
sections teach 8-9 periods a week.
"""
from __future__ import annotations

from datetime import date

from test_section_plans import A_DAYS, B_DAYS, BASE, _seed, store, world  # noqa: F401  (fixtures)

from academicos.curriculum import calendar as calendar_mod

DOUBLES = (0, 2, 4)      # 10-A gets a second Science period on Monday, Wednesday and Friday


def _nine_a_week(store, w):
    store.set_allocation(section_id=w.a, subject_id=w.subject, teacher_id="t_ana", periods_per_week=9)
    store.replace_section_timetable(w.a, [{"day_of_week": d, "period": 1, "subject_id": w.subject}
                                          for d in A_DAYS]
                                    + [{"day_of_week": d, "period": 3, "subject_id": w.subject}
                                       for d in DOUBLES])
    days = [date.fromisoformat(d) for d in calendar_mod.working_days_for_year(store, w.year).dates]
    a_periods = sum(1 + (d.weekday() in DOUBLES) for d in days if d.weekday() in A_DAYS)
    b_periods = sum(1 for d in days if d.weekday() in B_DAYS)
    return len(days), a_periods, b_periods


def test_the_budget_is_the_sections_periods_not_the_working_days(store):
    w = _seed(store)
    working_days, a_periods, b_periods = _nine_a_week(store, w)
    assert a_periods > working_days, "fixture: 10-A has more Science periods than the year has days"

    r = calendar_mod.compute_teaching_time_estimates(store, academic_year_id=w.year, book_id=w.book,
                                                     periods_per_week=9, recompute=True)
    assert r.total_subject_periods == a_periods, (r.total_subject_periods, working_days)
    assert r.section_id == w.a, "sized by the class's largest section week"

    rb = calendar_mod.compute_teaching_time_estimates(store, academic_year_id=w.year, book_id=w.book,
                                                      periods_per_week=3, recompute=True, section_id=w.b)
    assert rb.total_subject_periods == b_periods and rb.section_id == w.b


def test_the_route_sizes_estimates_from_the_section_week(world):
    w = world
    working_days, a_periods, b_periods = _nine_a_week(w.store, w)
    # The section allocations name real teachers in this fixture; keep 10-A's
    # teacher on its 9-period cell.
    r = w.c.post(f"{BASE}/books/{w.book}/teaching-time-estimates", params={"academic_year_id": w.year},
                 json={"periodsPerWeek": 9, "recompute": True}, headers=w.p)
    assert r.status_code == 200, r.text
    assert r.json()["totalSubjectPeriods"] == a_periods != working_days
    assert r.json()["sectionId"] == w.a

    # A named section, with periodsPerWeek left to its allocation.
    rb = w.c.post(f"{BASE}/books/{w.book}/teaching-time-estimates", params={"academic_year_id": w.year},
                  json={"sectionId": w.b, "recompute": True}, headers=w.p)
    assert rb.status_code == 200, rb.text
    assert (rb.json()["totalSubjectPeriods"], rb.json()["periodsPerWeek"]) == (b_periods, 3)

    # No legacy per-name allocation and no periodsPerWeek: the section allocation still sizes it.
    bare = w.c.post(f"{BASE}/books/{w.book}/teaching-time-estimates", params={"academic_year_id": w.year},
                    json={}, headers=w.p)
    assert bare.status_code == 200, bare.text
    assert bare.json()["periodsPerWeek"] == 9
