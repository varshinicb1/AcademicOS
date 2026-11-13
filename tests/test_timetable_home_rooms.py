"""Ordinary periods keep the section's classroom after a re-solve (TA-1,
SA-1: the teacher's and the student's day say where to go; handover §9,
"Rooms are empty for ordinary classes").

The solver books rooms only for a subject that needs a kind of room (a lab).
Every other period kept its room only when it stayed in the same slot, so a
period the solver moved or added came back with no room, although the
section's other periods all named its classroom. A section's classroom is
taken from its own week -- the classroom most of its ordinary periods are in
-- never invented: a school that has set no rooms still gets no room.
"""
from __future__ import annotations

from collections import defaultdict

import pytest

from academicos.curriculum.store import CurriculumStore
from academicos.curriculum.timetable_solver import SolveOptions, _minutes, solve

pytest.importorskip("ortools")

EIGHT = [{"start": f"{h:02d}:{m:02d}", "end": f"{h2:02d}:{m2:02d}"}
         for (h, m), (h2, m2) in zip([(8, 0), (8, 45), (9, 30), (10, 15), (11, 15), (12, 0), (12, 45), (13, 30)],
                                     [(8, 45), (9, 30), (10, 15), (11, 0), (12, 0), (12, 45), (13, 30), (14, 15)])]
SUBJECTS = (("Maths", 7), ("Science", 7), ("English", 6), ("Hindi", 5), ("Social", 6))


@pytest.fixture
def store(tmp_path):
    s = CurriculumStore(tmp_path / "curriculum.sqlite")
    yield s
    s.close()


def _school(store):
    year = store.create_academic_year(school_id="s1", label="2026-27", start_date="2026-04-01",
                                      end_date="2027-03-31")
    store.create_bell_schedule(academic_year_id=year.id, name="Main", slots=EIGHT)
    grade = store.create_grade(academic_year_id=year.id, number=9)
    secs = store.sections_for_grade(grade.id)
    secs.append(store.create_section(grade_id=grade.id, name="B"))
    allocs = []
    for name, ppw in SUBJECTS:
        subj = store.create_subject(grade_id=grade.id, name=name)
        for i, sec in enumerate(secs):
            allocs.append(store.set_allocation(section_id=sec.id, subject_id=subj.id,
                                               teacher_id=f"t_{name}_{i}", periods_per_week=ppw)[1])
    return year.id, secs, allocs


def _all(store, year):
    return {s.id for s in store.sections_for_year(year)}


def _set_rooms(store, section_id, room_of):
    """The school's week as imported: each period names a room."""
    store.replace_section_timetable(section_id, [
        {"day_of_week": e.day_of_week, "period": e.period, "subject_id": e.subject_id,
         "teacher_id": e.teacher_id, "room_id": room_of(e)}
        for e in store.timetable_for_section(section_id)])


def _room_clashes(store, year):
    times = {}
    for s in store.sections_for_year(year):
        bell = store.bell_for_section(s)
        times[s.id] = {sl.period: (_minutes(sl.start), _minutes(sl.end)) for sl in bell.slots if sl.period}
    by_room = defaultdict(list)
    for e in store.timetable_for_year(year):
        if e.room_id:
            by_room[(e.room_id, e.day_of_week)].append(times[e.section_id][e.period])
    out = []
    for key, spans in by_room.items():
        spans.sort()
        out += [f"{key}: {a} overlaps {b}" for a, b in zip(spans, spans[1:]) if b[0] < a[1]]
    return out


def test_a_moved_or_added_period_keeps_the_sections_classroom(store):
    year, secs, allocs = _school(store)
    first = solve(store, year)
    assert first.status == "solved", first.problems
    store.apply_solved_timetable(year, first.entries, _all(store, year))
    home = {s.id: store.create_room(school_id="s1", name=f"Room 9-{s.name}", kind="classroom").id
            for s in secs}
    for s in secs:
        _set_rooms(store, s.id, lambda e, s=s: home[s.id])

    # One more Maths period for 9-A: the solver adds it, and may move others.
    a = allocs[0]
    store.set_allocation(section_id=a.section_id, subject_id=a.subject_id, teacher_id=a.teacher_id,
                         periods_per_week=a.periods_per_week + 1)
    second = solve(store, year, SolveOptions(keep_existing=True))
    assert second.status == "solved", second.problems
    assert second.moved_or_added >= 1
    missing = [(e.section_id, e.day_of_week, e.period) for e in second.entries if e.room_id != home[e.section_id]]
    assert missing == [], f"ordinary periods with no classroom: {missing}"
    store.apply_solved_timetable(year, second.entries, _all(store, year))
    assert _room_clashes(store, year) == []


def test_a_school_with_no_rooms_gets_no_room_not_an_empty_one(store):
    year, _, _ = _school(store)
    result = solve(store, year)
    assert result.status == "solved", result.problems
    assert {e.room_id for e in result.entries} == {None}


def test_a_shared_classroom_is_never_booked_twice_at_once(store):
    """Two sections whose weeks both name the same classroom: a period that
    falls back to it is placed only where the room is free."""
    year, secs, allocs = _school(store)
    first = solve(store, year)
    store.apply_solved_timetable(year, first.entries, _all(store, year))
    shared = store.create_room(school_id="s1", name="Room 9", kind="classroom").id
    # One classroom shared by day: 9-A has it Monday to Wednesday, 9-B
    # Thursday to Saturday, so it is the classroom of both.
    _set_rooms(store, secs[0].id, lambda e: shared if e.day_of_week <= 2 else None)
    _set_rooms(store, secs[1].id, lambda e: shared if e.day_of_week >= 3 else None)
    assert _room_clashes(store, year) == []

    for a in allocs[:2]:
        store.set_allocation(section_id=a.section_id, subject_id=a.subject_id, teacher_id=a.teacher_id,
                             periods_per_week=a.periods_per_week + 1)
    second = solve(store, year, SolveOptions(keep_existing=True))
    assert second.status == "solved", second.problems
    store.apply_solved_timetable(year, second.entries, _all(store, year))
    assert _room_clashes(store, year) == []


def test_a_lab_period_keeps_its_lab_and_is_not_given_the_classroom(store):
    year, secs, allocs = _school(store)
    lab = store.create_room(school_id="s1", name="Lab 1", kind="lab").id
    science = [a for a in allocs if a.section_id == secs[0].id][1]
    store.set_allocation(section_id=science.section_id, subject_id=science.subject_id,
                         teacher_id=science.teacher_id, periods_per_week=science.periods_per_week,
                         room_kind="lab")
    first = solve(store, year)
    assert first.status == "solved", first.problems
    store.apply_solved_timetable(year, first.entries, _all(store, year))
    home = store.create_room(school_id="s1", name="Room 9-A", kind="classroom").id
    _set_rooms(store, secs[0].id, lambda e: e.room_id if e.subject_id == science.subject_id else home)

    second = solve(store, year, SolveOptions(keep_existing=False))
    assert second.status == "solved", second.problems
    for e in second.entries:
        if e.section_id != secs[0].id:
            continue
        assert e.room_id == (lab if e.subject_id == science.subject_id else home), e


def test_a_classroom_already_in_use_at_that_time_is_not_given_again():
    """The guard itself, on hand-made entries: the first period (in a fixed
    order) gets the shared classroom, a second at the same clock time does
    not, and one at another time does."""
    from types import SimpleNamespace as NS

    from academicos.curriculum.timetable_solver import ProposedEntry, _seat_in_classrooms

    rooms = [NS(id="r1", kind="classroom"), NS(id="lab", kind="lab")]
    current = [NS(section_id="A", room_id="r1"), NS(section_id="B", room_id="r1"),
               NS(section_id="B", room_id="lab")]
    grids = {"A": ([0], {1: (480, 525), 2: (525, 570)}), "B": ([0], {1: (480, 525), 2: (525, 570)})}
    a1 = ProposedEntry(section_id="A", day_of_week=0, period=1, subject_id="m", teacher_id="t1")
    b1 = ProposedEntry(section_id="B", day_of_week=0, period=1, subject_id="m", teacher_id="t2")
    b2 = ProposedEntry(section_id="B", day_of_week=0, period=2, subject_id="m", teacher_id="t2")
    entries = [b2, b1, a1]
    _seat_in_classrooms([b2, b1, a1], entries, current, rooms, {"lab"}, grids)
    assert (a1.room_id, b1.room_id, b2.room_id) == ("r1", None, "r1")

    # A room some other period already holds at that time is never given.
    held = ProposedEntry(section_id="A", day_of_week=0, period=2, subject_id="e", teacher_id="t3", room_id="r1")
    late = ProposedEntry(section_id="B", day_of_week=0, period=2, subject_id="m", teacher_id="t2")
    _seat_in_classrooms([late], [held, late], current, rooms, {"lab"}, grids)
    assert late.room_id is None
