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
from academicos.curriculum.timetable_solver import SolveOptions, _minutes, break_minutes, solve

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


def _longest_run(spans, gap):
    """The most periods back to back on the clock: each starts less than
    `gap` minutes after the one before ends."""
    longest = run = 0
    last_end = None
    for s, e in sorted(spans):
        run = run + 1 if last_end is not None and 0 <= s - last_end < gap else 1
        longest, last_end = max(longest, run), e
    return longest


def _violations(store, year_id, *, max_per_day=7, max_consecutive=4):
    """Every hard rule, checked from the stored timetable."""
    out = []
    gap = break_minutes(store.bell_schedules_for_year(year_id))
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
        if _longest_run(spans, gap) > max_consecutive:
            out.append(f"{t} day {d}: {_longest_run(spans, gap)} in a row > {max_consecutive}")
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


# Two bells 15-20 minutes apart, each with a 20-minute break (audit N-3-3's
# school): Junior's P4 ends 11:00 and Main's P5 starts 11:05, so a teacher
# going from one to the other gets no break.
MAIN = [{"start": a, "end": b} for a, b in (("08:05", "08:45"), ("08:45", "09:25"), ("09:25", "10:05"),
                                            ("10:05", "10:45"))] + \
    [{"start": "10:45", "end": "11:05", "kind": "break"}] + \
    [{"start": a, "end": b} for a, b in (("11:05", "11:45"), ("11:45", "12:25"), ("12:25", "13:05"),
                                         ("13:05", "13:45"))]
JUNIOR = [{"start": a, "end": b} for a, b in (("08:20", "09:00"), ("09:00", "09:40"), ("09:40", "10:20"),
                                              ("10:20", "11:00"))] + \
    [{"start": "11:00", "end": "11:20", "kind": "break"}] + \
    [{"start": a, "end": b} for a, b in (("11:20", "12:00"), ("12:00", "12:40"), ("12:40", "13:20"),
                                         ("13:20", "14:00"))]


def _two_bells(store):
    year = store.create_academic_year(school_id="s1", label="2026-27", start_date="2026-04-01",
                                      end_date="2027-03-31")
    store.create_bell_schedule(academic_year_id=year.id, name="Main", slots=MAIN)
    junior = store.create_bell_schedule(academic_year_id=year.id, name="Junior", slots=JUNIOR)
    return year.id, junior


def test_most_in_a_row_is_counted_by_the_clock_across_two_bells(store):
    """N-3-3: the solver's windows were five consecutive START TIMES over
    both bells -- about two and a half periods of clock time -- so a teacher
    could teach 6-A's P1-P4 on the Junior bell and walk into 7-A's P5 on
    Main five minutes later: five in a row with maxConsecutive 4."""
    year, junior = _two_bells(store)
    six = store.create_grade(academic_year_id=year, number=6)
    seven = store.create_grade(academic_year_id=year, number=7)
    [six_a] = store.sections_for_grade(six.id)
    [seven_a] = store.sections_for_grade(seven.id)
    store.set_section_bell(six_a.id, junior.id)
    t = "t_shared"
    junior_subjects = [store.create_subject(grade_id=six.id, name=n) for n in ("Maths", "Science", "English", "Hindi")]
    for subj in junior_subjects:
        store.set_allocation(section_id=six_a.id, subject_id=subj.id, teacher_id=t, periods_per_week=1)
    social = store.create_subject(grade_id=seven.id, name="Social")
    store.set_allocation(section_id=seven_a.id, subject_id=social.id, teacher_id=t, periods_per_week=1)
    # Monday: Junior P1-P4 (08:20-11:00), then Main P5 (11:05), all locked.
    store.replace_section_timetable(six_a.id, [{"day_of_week": 0, "period": p, "subject_id": s.id, "locked": True}
                                               for p, s in enumerate(junior_subjects, start=1)])
    store.replace_section_timetable(seven_a.id, [{"day_of_week": 0, "period": 5, "subject_id": social.id,
                                                  "locked": True}])
    assert solve(store, year, SolveOptions(max_consecutive=4)).status == "infeasible"
    assert solve(store, year, SolveOptions(max_consecutive=5)).status == "solved"


def test_a_teacher_on_two_bells_keeps_every_rule_by_the_clock(store):
    """N-3-3 at school scale: one teacher for three Junior sections and two
    Main ones, checked independently for runs by the clock."""
    year, junior = _two_bells(store)
    t = "t_shared"
    for number, on_junior in ((6, True), (7, False)):
        grade = store.create_grade(academic_year_id=year, number=number)
        secs = store.sections_for_grade(grade.id)
        secs += [store.create_section(grade_id=grade.id, name=n) for n in ("B", "C")[:2 if on_junior else 1]]
        maths = store.create_subject(grade_id=grade.id, name="Maths")
        for sec in secs:
            if on_junior:
                store.set_section_bell(sec.id, junior.id)
            store.set_allocation(section_id=sec.id, subject_id=maths.id, teacher_id=t, periods_per_week=6)
    result = solve(store, year, SolveOptions(max_per_day=6, max_consecutive=3))
    assert result.status == "solved", result.problems
    store.apply_solved_timetable(year, result.entries, {s.id for s in store.sections_for_year(year)})
    assert _violations(store, year, max_per_day=6, max_consecutive=3) == []


def _connected_school(store, subjects):
    """Forty sections (6-A..10-H) whose teachers each take four sections in
    a row, a different four per subject, so teachers cross grades and every
    section is tied to every other: no part of the school can be solved
    alone, as in a real staff room."""
    year = store.create_academic_year(school_id="s1", label="2026-27", start_date="2026-04-01",
                                      end_date="2027-03-31")
    store.create_bell_schedule(academic_year_id=year.id, name="Main", slots=EIGHT)
    secs = []
    for g in (6, 7, 8, 9, 10):
        grade = store.create_grade(academic_year_id=year.id, number=g)
        own = store.sections_for_grade(grade.id) + [store.create_section(grade_id=grade.id, name=n)
                                                    for n in "BCDEFGH"]
        subj = {n: store.create_subject(grade_id=grade.id, name=n) for n, _ in subjects}
        secs += [(sec, subj) for sec in own]
    for k, (name, ppw) in enumerate(subjects):
        for i, (sec, subj) in enumerate(secs):
            store.set_allocation(section_id=sec.id, subject_id=subj[name].id,
                                 teacher_id=f"t_{name}_{(i + 2 * k) % 40 // 4}", periods_per_week=ppw)
    return year.id


def test_forty_sections_are_solved_inside_a_minute_on_one_worker(store):
    """N-3-18: Cloud Run gives the API one CPU (--cpu=1). With one worker,
    CP-SAT's default search found no week for 40 sections in 20 s, and took
    61-64 s at a 60 s limit; for a school whose teachers cross grades it
    found none in 60 s. Now the search interleaves CP-SAT's portfolio on the
    one thread, the limit covers the whole solve, and the search stops once
    no better week has come for `stall_seconds`. Measured pinned to one core
    on the dev machine: about 20 s, the first week after about 3 s."""
    year = _connected_school(store, (("Maths", 8), ("Science", 7), ("English", 6), ("Hindi", 6),
                                     ("Social", 6), ("Sanskrit", 3), ("Computer", 2), ("Art", 2)))
    assert len(store.sections_for_year(year)) == 40
    started = time.monotonic()
    result = solve(store, year, SolveOptions(time_limit_seconds=60, num_workers=1))
    elapsed = time.monotonic() - started
    print(f"40 sections, one worker: {result.status} in {elapsed:.1f} s")
    assert result.status == "solved", result.problems
    assert elapsed < 60
    store.apply_solved_timetable(year, result.entries, {s.id for s in store.sections_for_year(year)})
    assert _violations(store, year) == []
    # A re-solve after one change starts from the published week.
    a = store.allocations_for_year(year)[0]
    store.set_allocation(section_id=a.section_id, subject_id=a.subject_id, teacher_id=a.teacher_id,
                         periods_per_week=a.periods_per_week + 1)
    started = time.monotonic()
    again = solve(store, year, SolveOptions(time_limit_seconds=60, num_workers=1))
    assert again.status == "solved" and time.monotonic() - started < 15
    assert (again.moved_or_added, again.removed) == (1, 0)


def test_the_limit_covers_the_whole_solve(store, monkeypatch):
    """N-3-18: the search was given the full limit after the model was
    built, so a 60 s request answered in 61-64 s."""
    from academicos.curriculum import timetable_solver as ts
    year, _, _ = _school(store, grades=(10,), sections=("A",), subjects=(("Science", 6),))
    seen = {}
    real = ts._search

    def slow_build_then_search(solver, model, stall):
        seen["limit"] = solver.parameters.max_time_in_seconds
        return real(solver, model, stall)
    monkeypatch.setattr(ts, "_search", slow_build_then_search)
    real_check = ts.check_feasibility
    monkeypatch.setattr(ts, "check_feasibility", lambda *a: (time.sleep(2), real_check(*a))[1])
    assert solve(store, year, SolveOptions(time_limit_seconds=10, num_workers=1)).status == "solved"
    assert seen["limit"] <= 8.5


def test_solver_workers_follow_the_cpu_quota(monkeypatch):
    """N-3-18: workers came from os.cpu_count(), which sees the host's
    cores, not the container's one-CPU quota."""
    from academicos.curriculum import timetable_solver as ts
    monkeypatch.setenv("ACOS_SOLVER_WORKERS", "1")
    assert ts.solver_workers() == 1
    monkeypatch.setenv("ACOS_SOLVER_WORKERS", "32")
    assert ts.solver_workers() == 8
    monkeypatch.delenv("ACOS_SOLVER_WORKERS")
    quota = {"/sys/fs/cgroup/cpu.max": "100000 100000\n"}       # one CPU, as --cpu=1 sets

    def cgroup(path):
        if path not in quota:
            raise OSError(path)
        return quota[path]
    monkeypatch.setattr(ts, "_read_text", cgroup)
    monkeypatch.setattr(ts.os, "cpu_count", lambda: 16)
    assert ts.solver_workers() == 1
    quota["/sys/fs/cgroup/cpu.max"] = "max 100000\n"            # no quota: the CPUs it may run on
    monkeypatch.setattr(ts.os, "sched_getaffinity", lambda pid: {0, 1}, raising=False)
    assert ts.solver_workers() == 2


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
