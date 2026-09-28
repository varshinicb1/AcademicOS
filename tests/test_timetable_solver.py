"""Timetable generation (SCH-3): every hard rule is checked on the solver's
output by an independent checker (`_violations`), not taken from the solver.

Includes the requirement's scale target (NFR-3: a 40-section school in under
60 seconds) and the clock-time rule: two bells whose period numbers line up
differently must not hide a teacher in two rooms at once.
"""
from __future__ import annotations

import math
import time
from collections import Counter, defaultdict

import pytest

from academicos.curriculum.store import CurriculumStore
from academicos.curriculum.timetable_solver import SolveOptions, _minutes, solve

pytest.importorskip("ortools")

EIGHT = [{"start": f"{h:02d}:{m:02d}", "end": f"{h2:02d}:{m2:02d}"}
         for (h, m), (h2, m2) in zip([(8, 0), (8, 45), (9, 30), (10, 15), (11, 15), (12, 0), (12, 45), (13, 30)],
                                     [(8, 45), (9, 30), (10, 15), (11, 0), (12, 0), (12, 45), (13, 30), (14, 15)])]


@pytest.fixture
def store(tmp_path):
    s = CurriculumStore(tmp_path / "curriculum.sqlite")
    yield s
    s.close()


def _school(store, *, grades=(9, 10), sections=("A", "B"), subjects=(("Maths", 7), ("Science", 7),
            ("English", 6), ("Hindi", 5), ("Social", 6), ("Computer", 3)), share=2):
    """Each grade's subject is taught by one teacher per `share` sections."""
    year = store.create_academic_year(school_id="s1", label="2026-27", start_date="2026-04-01",
                                      end_date="2027-03-31")
    bell = store.create_bell_schedule(academic_year_id=year.id, name="Main", slots=EIGHT)
    alloc = []
    for g in grades:
        grade = store.create_grade(academic_year_id=year.id, number=g)
        secs = store.sections_for_grade(grade.id)
        for name in sections[1:]:
            secs.append(store.create_section(grade_id=grade.id, name=name))
        for subj_name, ppw in subjects:
            subj = store.create_subject(grade_id=grade.id, name=subj_name)
            for i, sec in enumerate(secs):
                teacher = f"t_{g}_{subj_name}_{i // share}"
                a = store.set_allocation(section_id=sec.id, subject_id=subj.id, teacher_id=teacher,
                                         periods_per_week=ppw)[1]
                alloc.append(a)
    return year.id, bell, alloc


def _violations(store, year_id, *, max_per_day=7, max_consecutive=4):
    """Every hard rule, checked from the stored timetable."""
    out = []
    entries = store.timetable_for_year(year_id)
    sections = {s.id: s for s in store.sections_for_year(year_id)}
    times = {}
    for sid, s in sections.items():
        bell = store.bell_for_section(s)
        times[sid] = {sl.period: (_minutes(sl.start), _minutes(sl.end)) for sl in bell.slots if sl.period}
    count = Counter((e.section_id, e.subject_id) for e in entries)
    for a in store.allocations_for_year(year_id):
        if count[(a.section_id, a.subject_id)] != a.periods_per_week:
            out.append(f"allocation {a.id}: {count[(a.section_id, a.subject_id)]} != {a.periods_per_week}")
        days = store.bell_for_section(sections[a.section_id]).days
        cap = max(1, math.ceil(a.periods_per_week / len(days)))
        per_day = Counter(e.day_of_week for e in entries
                          if e.section_id == a.section_id and e.subject_id == a.subject_id)
        if per_day and max(per_day.values()) > cap:
            out.append(f"allocation {a.id}: {max(per_day.values())} in a day > {cap}")
    by_teacher_day = defaultdict(list)
    for e in entries:
        if e.teacher_id:
            by_teacher_day[(e.teacher_id, e.day_of_week)].append(times[e.section_id][e.period])
    for (t, d), spans in by_teacher_day.items():
        spans.sort()
        for (s1, e1), (s2, e2) in zip(spans, spans[1:]):
            if s2 < e1:
                out.append(f"{t} day {d}: {s1}-{e1} overlaps {s2}-{e2}")
        if len(spans) > max_per_day:
            out.append(f"{t} day {d}: {len(spans)} periods > {max_per_day}")
    return out


def test_a_small_school_is_solved_without_breaking_a_rule(store):
    year, _, allocs = _school(store)
    result = solve(store, year, SolveOptions(time_limit_seconds=30))
    assert result.status == "solved", result.problems
    store.apply_solved_timetable(year, result.entries, {s.id for s in store.sections_for_year(year)})
    assert _violations(store, year) == []
    assert len(store.timetable_for_year(year)) == sum(a.periods_per_week for a in allocs)


def test_a_resolve_after_one_change_moves_few_periods(store):
    year, _, allocs = _school(store)
    first = solve(store, year)
    store.apply_solved_timetable(year, first.entries, {s.id for s in store.sections_for_year(year)})
    a = allocs[0]
    store.set_allocation(section_id=a.section_id, subject_id=a.subject_id, teacher_id=a.teacher_id,
                         periods_per_week=a.periods_per_week + 1)
    second = solve(store, year, SolveOptions(keep_existing=True))
    assert second.status == "solved"
    total = sum(x.periods_per_week for x in store.allocations_for_year(year))
    assert second.kept >= total - 10, (second.kept, second.moved_or_added, second.removed)
    store.apply_solved_timetable(year, second.entries, {s.id for s in store.sections_for_year(year)})
    assert _violations(store, year) == []


def test_unavailable_periods_stay_free_and_locked_periods_stay_put(store):
    year, _, allocs = _school(store)
    a = allocs[0]
    store.set_teacher_unavailability(year, a.teacher_id, [(0, p) for p in range(1, 9)])   # all Monday
    result = solve(store, year)
    assert result.status == "solved"
    assert not [e for e in result.entries if e.teacher_id == a.teacher_id and e.day_of_week == 0]
    sections = {s.id for s in store.sections_for_year(year)}
    store.apply_solved_timetable(year, result.entries, sections)
    # Lock one of this section's periods, then re-solve from scratch.
    week = store.timetable_for_section(a.section_id)
    pinned = week[0]
    store.replace_section_timetable(a.section_id, [
        {"day_of_week": e.day_of_week, "period": e.period, "subject_id": e.subject_id,
         "locked": e.id == pinned.id} for e in week])
    again = solve(store, year, SolveOptions(keep_existing=False))
    assert again.status == "solved"
    assert any(e.section_id == pinned.section_id and e.day_of_week == pinned.day_of_week
               and e.period == pinned.period and e.subject_id == pinned.subject_id for e in again.entries)


def test_impossible_requests_are_named_before_solving(store):
    year, _, allocs = _school(store, subjects=(("Maths", 30), ("Science", 20)))
    result = solve(store, year)
    assert result.status == "infeasible"
    assert any("needs 50 periods a week; its bell gives 48" in p for p in result.problems)


def test_a_teacher_cannot_be_in_two_rooms_across_two_bells(store):
    """Senior bell: 45-minute periods. Junior bell: 30-minute periods. A
    teacher shared by both must not overlap by clock time, whatever the
    period numbers say."""
    year, _, _ = _school(store, grades=(10,), sections=("A",), subjects=(("Science", 6),))
    grade6 = store.create_grade(academic_year_id=year, number=6)
    [junior_sec] = store.sections_for_grade(grade6.id)
    junior = store.create_bell_schedule(academic_year_id=year, name="Junior", slots=[
        {"start": f"{8 + (i * 30) // 60:02d}:{(i * 30) % 60:02d}",
         "end": f"{8 + ((i + 1) * 30) // 60:02d}:{((i + 1) * 30) % 60:02d}"} for i in range(8)])
    store.set_section_bell(junior_sec.id, junior.id)
    evs = store.create_subject(grade_id=grade6.id, name="EVS")
    shared = "t_10_Science_0"
    store.set_allocation(section_id=junior_sec.id, subject_id=evs.id, teacher_id=shared, periods_per_week=6)
    result = solve(store, year)
    assert result.status == "solved", result.problems
    store.apply_solved_timetable(year, result.entries, {s.id for s in store.sections_for_year(year)})
    assert _violations(store, year) == []


def test_forty_sections_are_solved_inside_a_minute(store):
    """NFR-3: timetable generation for a 40-section school < 60 s."""
    year, _, allocs = _school(store, grades=(6, 7, 8, 9, 10),
                              sections=("A", "B", "C", "D", "E", "F", "G", "H"),
                              subjects=(("Maths", 8), ("Science", 7), ("English", 6), ("Hindi", 6),
                                        ("Social", 6), ("Sanskrit", 3), ("Computer", 2), ("Art", 2)),
                              share=4)
    assert len(store.sections_for_year(year)) == 40
    started = time.monotonic()
    result = solve(store, year, SolveOptions(time_limit_seconds=60))
    elapsed = time.monotonic() - started
    assert result.status == "solved", result.problems
    assert elapsed < 60
    store.apply_solved_timetable(year, result.entries, {s.id for s in store.sections_for_year(year)})
    assert _violations(store, year) == []
