"""Coverage reads the school's today, as delayed topics do (audit D66).

Before: `store.get_coverage_report` defaulted its as-of date to the server's
UTC date, while `/reporting/delayed-topics` used the school's IST today. The
web sends no asOfDate, so between 00:00 and 05:30 IST Coverage & Pace showed
yesterday's figures beside today's overdue list.
"""
from __future__ import annotations

from test_section_plans import BASE, _route_plan, world  # noqa: F401  (fixture)


def test_coverage_and_delayed_topics_share_the_schools_today(world):
    w = world                       # the school's today is pinned to 2026-06-01
    assert _route_plan(w, w.a).status_code == 200
    params = {"academic_year_id": w.year}
    coverage = w.c.get(f"{BASE}/reporting/coverage", params=params, headers=w.p)
    delayed = w.c.get(f"{BASE}/reporting/delayed-topics", params=params, headers=w.p)
    assert coverage.status_code == 200 and delayed.status_code == 200
    assert coverage.json()["asOfDate"] == delayed.json()["asOfDate"] == "2026-06-01"
    # Planned to date is counted against that day: 10-A's one lesson of 1 June.
    assert coverage.json()["plannedToDate"] == 1

    # An explicit date still wins.
    explicit = w.c.get(f"{BASE}/reporting/coverage", params={**params, "as_of_date": "2026-06-06"},
                       headers=w.p).json()
    assert explicit["asOfDate"] == "2026-06-06" and explicit["plannedToDate"] == 6
