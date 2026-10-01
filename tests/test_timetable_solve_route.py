"""The solve route (SCH-3) as the principal: propose without writing, then
publish; teacher unavailability through the API; gates and scoping."""
from __future__ import annotations

import pytest

from test_school_model import BASE, _alloc, _bell, w  # noqa: F401 - `w` is a fixture

pytest.importorskip("ortools")


def _solve(w, auth=None, **body):
    return w.c.post(f"{BASE}/academic-years/{w.year}/timetable/solve", json=body, headers=auth or w.p1)


def test_a_proposal_writes_nothing_and_apply_publishes_it(w):
    _bell(w)
    for sec, teacher in (("10-A", w.t1_id), ("10-B", w.t2_id)):
        _alloc(w, sec, w.sub10["Science"], teacher, 6)
        _alloc(w, sec, w.sub10["Mathematics"], teacher, 6)
    proposal = _solve(w)
    assert proposal.status_code == 200, proposal.text
    body = proposal.json()
    assert body["status"] == "solved" and body["applied"] is False and len(body["entries"]) == 24
    assert w.c.get(f"{BASE}/academic-years/{w.year}/timetable", headers=w.p1).json() == []
    applied = _solve(w, apply=True).json()
    assert applied["applied"] is True
    stored = w.c.get(f"{BASE}/academic-years/{w.year}/timetable", headers=w.p1).json()
    assert len(stored) == 24
    # One teacher per slot: Ana teaches 10-A only, Bala 10-B only, but check anyway.
    slots = [(e["teacherId"], e["dayOfWeek"], e["period"]) for e in stored]
    assert len(slots) == len(set(slots))


def test_publishing_a_solved_week_tells_the_students_too(w):
    """N-8-5: the solver's publish told teachers only; the section's students
    never heard their timetable had changed."""
    from test_school_model import _timetable_notices
    w.c.post(f"{BASE}/student-enrollments", json={"studentId": w.stu_id, "sectionId": w.sec["10-A"]},
             headers=w.p1)
    _bell(w)
    for sec, teacher in (("10-A", w.t1_id), ("10-B", w.t2_id)):
        _alloc(w, sec, w.sub10["Science"], teacher, 6)
        _alloc(w, sec, w.sub10["Mathematics"], teacher, 6)
    assert _solve(w).json()["applied"] is False
    assert [_timetable_notices(u) for u in (w.stu_id, w.t1_id, w.t2_id)] == [0, 0, 0], "a proposal tells no one"
    assert _solve(w, apply=True).json()["applied"] is True
    assert [_timetable_notices(u) for u in (w.stu_id, w.t1_id, w.t2_id)] == [1, 1, 1]


def test_an_impossible_allocation_is_explained(w):
    _bell(w)
    _alloc(w, "10-A", w.sub10["Science"], w.t1_id, 30)
    _alloc(w, "10-A", w.sub10["Mathematics"], w.t2_id, 30)
    body = _solve(w).json()
    assert body["status"] == "infeasible" and body["applied"] is False
    assert any("10-A needs 60 periods a week; its bell gives 48" in p for p in body["problems"])


def test_unavailability_is_set_by_the_principal_and_respected(w):
    _bell(w)
    _alloc(w, "10-A", w.sub10["Science"], w.t1_id, 6)
    r = w.c.put(f"{BASE}/academic-years/{w.year}/teacher-unavailability/{w.t1_id}",
                json={"slots": [{"dayOfWeek": 0, "period": p} for p in range(1, 9)]}, headers=w.p1)
    assert r.status_code == 200 and len(r.json()["slots"]) == 8
    listed = w.c.get(f"{BASE}/academic-years/{w.year}/teacher-unavailability", headers=w.p1).json()
    assert listed[0]["teacherId"] == w.t1_id
    # Six periods at most one a day need six free days; Monday is gone.
    body = _solve(w).json()
    assert body["status"] == "infeasible"
    assert body["problems"] == ["Science for 10-A needs 6 periods, at most 1 a day, but its teacher "
                                "is free on only 5 of the section's 6 days"]
    _alloc(w, "10-A", w.sub10["Science"], w.t1_id, 5)
    body = _solve(w).json()
    assert body["status"] == "solved"
    assert len(body["entries"]) == 5 and not [e for e in body["entries"] if e["dayOfWeek"] == 0]


def test_only_this_schools_principal_solves(w):
    _bell(w)
    assert _solve(w, auth=w.t1).status_code == 403
    assert _solve(w, auth=w.p2).status_code == 403
    assert w.c.get(f"{BASE}/academic-years/{w.year}/teacher-unavailability", headers=w.t1).status_code == 403
    r = w.c.put(f"{BASE}/academic-years/{w.year}/teacher-unavailability/{w.t_other}",
                json={"slots": []}, headers=w.p1)
    assert r.status_code == 403, "another school's teacher"
