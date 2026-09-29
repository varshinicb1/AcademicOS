"""Labs, double periods, co-teaching and a room out of use (REQUIREMENTS
SCH-2 "labs and double periods", SCH-8 "a lab unavailable" and "a subject
with multiple teachers or co-teaching").

The solver's output is checked by an independent checker (`_lab_and_pair_
violations`), not taken from the solver: no room holds two classes at one
clock time, a subject that needs a lab is in a lab every period, a double
period is two periods in a row with no break between them in one room, and
a co-teacher is never in two places. Cover: a co-taught period needs a
substitute only when both of its teachers are away.

2026-06-01 is a Monday.
"""
from __future__ import annotations

from collections import defaultdict
from types import SimpleNamespace

import pytest

from academicos.curriculum.school_model import InUse, TimetableClash, adjacent_pairs
from academicos.curriculum.store import CurriculumStore
from academicos.curriculum.timetable_solver import SolveOptions, _minutes, solve

pytest.importorskip("ortools")

MON = "2026-06-01"
# Eight 45-minute periods, a break after period 4 (so 4 and 5 are not a pair).
BELL = [{"start": "08:00", "end": "08:45"}, {"start": "08:45", "end": "09:30"},
        {"start": "09:30", "end": "10:15"}, {"start": "10:15", "end": "11:00"},
        {"start": "11:00", "end": "11:20", "kind": "break"},
        {"start": "11:20", "end": "12:05"}, {"start": "12:05", "end": "12:50"},
        {"start": "12:50", "end": "13:35"}, {"start": "13:35", "end": "14:20"}]
# A break after every period: no double period fits anywhere.
BROKEN = []
for i in range(6):
    BROKEN.append({"start": f"{8 + i}:00".zfill(5), "end": f"{8 + i}:40".zfill(5)})
    BROKEN.append({"start": f"{8 + i}:40".zfill(5), "end": f"{8 + i}:50".zfill(5), "kind": "break"})


@pytest.fixture
def store(tmp_path):
    s = CurriculumStore(tmp_path / "curriculum.sqlite")
    yield s
    s.close()


def _school(store, *, sections=("A", "B"), bell=BELL, labs=1, science=6, lab_kind="lab", doubles=0,
            co_teacher=None):
    """Class 10 with `sections`; Science needs a `lab_kind` and is taught by
    ana (with `co_teacher`), Maths by bala, English by chitra."""
    year = store.create_academic_year(school_id="s1", label="2026-27", start_date="2026-04-01",
                                      end_date="2027-03-31")
    store.create_calendar(academic_year_id=year.id, weekly_off_days=["sunday"], alternate_saturday_rule="none")
    store.create_bell_schedule(academic_year_id=year.id, name="Main", slots=bell)
    grade = store.create_grade(academic_year_id=year.id, number=10)
    secs = store.sections_for_grade(grade.id)
    for name in sections[1:]:
        secs.append(store.create_section(grade_id=grade.id, name=name))
    sci = store.create_subject(grade_id=grade.id, name="Science")
    mat = store.create_subject(grade_id=grade.id, name="Maths")
    eng = store.create_subject(grade_id=grade.id, name="English")
    lab_rooms = [store.create_room(school_id="s1", name=f"Lab {i + 1}", kind="lab") for i in range(labs)]
    store.create_room(school_id="s1", name="Room 1", kind="classroom")
    for i, sec in enumerate(secs):
        store.set_allocation(section_id=sec.id, subject_id=sci.id, teacher_id=f"ana{i // 2}",
                             periods_per_week=science, room_kind=lab_kind, double_periods=doubles,
                             co_teacher_id=co_teacher)
        store.set_allocation(section_id=sec.id, subject_id=mat.id, teacher_id=f"bala{i // 2}", periods_per_week=6)
        store.set_allocation(section_id=sec.id, subject_id=eng.id, teacher_id=f"chitra{i // 2}", periods_per_week=5)
    return SimpleNamespace(year=year.id, sections=[s.id for s in secs], sci=sci.id, mat=mat.id, eng=eng.id,
                           labs=[r.id for r in lab_rooms])


def _apply(store, w, **opts):
    result = solve(store, w.year, SolveOptions(time_limit_seconds=30, **opts))
    assert result.status == "solved", result.problems
    store.apply_solved_timetable(w.year, result.entries, set(w.sections))
    return result


def _lab_and_pair_violations(store, year_id):
    """Room, lab, double-period and co-teacher rules, checked from storage."""
    out = []
    entries = store.timetable_for_year(year_id)
    sections = {s.id: s for s in store.sections_for_year(year_id)}
    bells = {sid: store.bell_for_section(s) for sid, s in sections.items()}
    times = {sid: {sl.period: (_minutes(sl.start), _minutes(sl.end)) for sl in b.slots if sl.period}
             for sid, b in bells.items()}
    rooms = {r.id: r for r in store.rooms_for_school("s1")}
    closed = store.room_unavailability_for_year(year_id)
    allocs = {(a.section_id, a.subject_id): a for a in store.allocations_for_year(year_id)}
    by_room = defaultdict(list)
    by_person = defaultdict(list)
    for e in entries:
        a = allocs[(e.section_id, e.subject_id)]
        span = times[e.section_id][e.period]
        if a.room_kind:
            if e.room_id is None or rooms[e.room_id].kind != a.room_kind:
                out.append(f"{e.section_id} {e.day_of_week}/{e.period}: needs a {a.room_kind}, has {e.room_id}")
        if e.room_id:
            by_room[(e.room_id, e.day_of_week)].append(span)
            if (e.day_of_week, e.period) in closed.get(e.room_id, set()):
                out.append(f"{e.room_id} used while closed on {e.day_of_week}/{e.period}")
        if e.co_teacher_id != a.co_teacher_id:
            out.append(f"{e.section_id} {e.day_of_week}/{e.period}: co-teacher {e.co_teacher_id} != {a.co_teacher_id}")
        for t in {e.teacher_id, e.co_teacher_id} - {None}:
            by_person[(t, e.day_of_week)].append(span)
    for key, spans in list(by_room.items()) + list(by_person.items()):
        spans.sort()
        for (s1, e1), (s2, _) in zip(spans, spans[1:]):
            if s2 < e1:
                out.append(f"{key}: two classes at once")
    for (sid, subj), a in allocs.items():
        if not a.double_periods:
            continue
        pairs = set(adjacent_pairs(bells[sid]))
        mine = [e for e in entries if e.section_id == sid and e.subject_id == subj]
        found = 0
        by_day = defaultdict(dict)
        for e in mine:
            by_day[e.day_of_week][e.period] = e.room_id
        for day, periods in by_day.items():
            used = set()
            for p, q in sorted(pairs):
                if p in periods and q in periods and p not in used and q not in used \
                        and periods[p] == periods[q]:
                    found += 1
                    used |= {p, q}
        if found < a.double_periods:
            out.append(f"{sid}/{subj}: {found} double period(s), wants {a.double_periods}")
    return out


# --------------------------------------------------------------------- #
# The solver
# --------------------------------------------------------------------- #

def test_every_lab_period_is_in_a_lab_and_no_lab_holds_two_classes(store):
    w = _school(store, sections=("A", "B", "C"), labs=2)
    _apply(store, w)
    assert _lab_and_pair_violations(store, w.year) == []
    science = [e for e in store.timetable_for_year(w.year) if e.subject_id == w.sci]
    assert len(science) == 18 and {e.room_id for e in science} <= set(w.labs)
    others = [e for e in store.timetable_for_year(w.year) if e.subject_id != w.sci]
    assert not {e.room_id for e in others} & set(w.labs), "a lab went to a subject that did not ask for one"


def test_one_lab_is_shared_by_clock_time(store):
    w = _school(store, sections=("A", "B", "C", "D"), labs=1)
    _apply(store, w)
    assert _lab_and_pair_violations(store, w.year) == []
    assert {e.room_id for e in store.timetable_for_year(w.year) if e.subject_id == w.sci} == {w.labs[0]}


def test_a_lab_out_of_use_is_never_booked(store):
    w = _school(store, labs=1)
    closed = [(0, p) for p in range(1, 7)] + [(2, 1), (2, 2)]
    store.set_room_unavailability(w.year, w.labs[0], closed)
    _apply(store, w)
    assert _lab_and_pair_violations(store, w.year) == []
    used = {(e.day_of_week, e.period) for e in store.timetable_for_year(w.year) if e.room_id == w.labs[0]}
    assert not used & set(closed)


def test_double_periods_are_two_in_a_row_without_a_break_in_one_lab(store):
    w = _school(store, labs=2, doubles=2)
    _apply(store, w)
    assert _lab_and_pair_violations(store, w.year) == []
    bell = store.bell_for_section(store.get_section(w.sections[0]))
    assert (4, 5) not in adjacent_pairs(bell), "the break after period 4 splits 4 and 5"


def test_co_teacher_is_never_in_two_places(store):
    # dev co-teaches Science to 10-A and 10-B and teaches nothing else: the
    # two sections' Science can never meet at the same time.
    w = _school(store, labs=2, co_teacher="dev")
    _apply(store, w)
    assert _lab_and_pair_violations(store, w.year) == []
    devs = [e for e in store.timetable_for_year(w.year) if e.co_teacher_id == "dev"]
    assert len(devs) == 12
    assert len({(e.day_of_week, e.period) for e in devs}) == 12


@pytest.mark.parametrize("setup, sentence", [
    (dict(labs=0), "needs a lab and the school has none"),
    (dict(sections=tuple("ABCDEFGH"), labs=1, science=7), "periods a week need a lab"),
    (dict(bell=BROKEN, doubles=1), "has no two periods in a row without a break"),
    (dict(closed_all_monday=True), "a lab is open on only 5 of the section's 6 days"),
])
def test_what_no_timetable_can_meet_is_said_before_solving(store, setup, sentence):
    closed_all_monday = setup.pop("closed_all_monday", False)
    w = _school(store, **setup)
    if closed_all_monday:
        store.set_room_unavailability(w.year, w.labs[0], [(0, p) for p in range(1, 9)])
    result = solve(store, w.year, SolveOptions(time_limit_seconds=5))
    assert result.status == "infeasible"
    assert any(sentence in p for p in result.problems), result.problems


# --------------------------------------------------------------------- #
# Allocations and the hand-made week
# --------------------------------------------------------------------- #

def test_allocation_rules(store):
    w = _school(store, labs=1)
    sec, sci = w.sections[0], w.sci
    with pytest.raises(ValueError, match="co-teacher is the subject's teacher"):
        store.set_allocation(section_id=sec, subject_id=sci, teacher_id="ana0", periods_per_week=6,
                             co_teacher_id="ana0")
    with pytest.raises(ValueError, match="double period"):
        store.set_allocation(section_id=sec, subject_id=sci, teacher_id="ana0", periods_per_week=6,
                             double_periods=4)
    with pytest.raises(ValueError, match="room kind is one of"):
        store.set_allocation(section_id=sec, subject_id=sci, teacher_id="ana0", periods_per_week=6,
                             room_kind="garden")
    with pytest.raises(ValueError, match="teacher before a co-teacher"):
        store.set_allocation(section_id=sec, subject_id=sci, teacher_id=None, periods_per_week=6,
                             co_teacher_id="dev")
    # Left out, the three stay as they were.
    _, a = store.set_allocation(section_id=sec, subject_id=sci, teacher_id="ana0", periods_per_week=5)
    assert (a.room_kind, a.double_periods, a.co_teacher_id) == ("lab", 0, None)


def test_the_hand_made_week_checks_labs_closures_and_co_teachers(store):
    w = _school(store, labs=1, co_teacher="dev")
    a10, b10 = w.sections[:2]
    lab = w.labs[0]
    classroom = next(r.id for r in store.rooms_for_school("s1") if r.kind == "classroom")
    with pytest.raises(TimetableClash) as no_room:
        store.replace_section_timetable(a10, [{"day_of_week": 0, "period": 1, "subject_id": w.sci}])
    assert "needs a lab; choose one" in str(no_room.value)
    with pytest.raises(TimetableClash) as wrong_room:
        store.replace_section_timetable(a10, [{"day_of_week": 0, "period": 1, "subject_id": w.sci,
                                               "room_id": classroom}])
    assert "Room 1 is a classroom" in str(wrong_room.value)
    store.set_room_unavailability(w.year, lab, [(1, 1)])
    with pytest.raises(TimetableClash) as closed:
        store.replace_section_timetable(a10, [{"day_of_week": 1, "period": 1, "subject_id": w.sci,
                                               "room_id": lab}])
    assert "Lab 1 is not available then" in str(closed.value)

    [e] = store.replace_section_timetable(a10, [{"day_of_week": 0, "period": 1, "subject_id": w.sci,
                                                 "room_id": lab}])
    assert e.co_teacher_id == "dev"
    # dev is in 10-A then, so 10-B's Science cannot be at that time either.
    with pytest.raises(TimetableClash) as busy:
        store.replace_section_timetable(b10, [{"day_of_week": 0, "period": 1, "subject_id": w.sci,
                                               "room_id": lab}])
    assert "the co-teacher already teaches 10-A then" in str(busy.value)
    # A room the week uses cannot be closed under it.
    with pytest.raises(InUse, match="Monday period 1"):
        store.set_room_unavailability(w.year, lab, [(0, 1)])


def test_a_co_teachers_week_and_load_include_the_periods(store):
    w = _school(store, labs=1)
    a10 = w.sections[0]
    store.replace_section_timetable(a10, [{"day_of_week": 0, "period": 1, "subject_id": w.sci, "room_id": w.labs[0]}])
    assert store.timetable_for_teacher("dev", w.year) == []
    store.set_allocation(section_id=a10, subject_id=w.sci, teacher_id="ana0", periods_per_week=6,
                         co_teacher_id="dev")
    [e] = store.timetable_for_teacher("dev", w.year)
    assert (e.co_teacher_id, e.teacher_id) == ("dev", "ana0")
    load = {row["teacherId"]: row for row in store.teacher_load(w.year)}
    assert load["dev"]["allocatedPerWeek"] == 6 and load["dev"]["timetabledPerWeek"] == 1


# --------------------------------------------------------------------- #
# Cover: a co-taught period needs a substitute only when both are away
# --------------------------------------------------------------------- #

def _co_taught_week(store):
    w = _school(store, labs=1, co_teacher="dev")
    a10 = w.sections[0]
    store.replace_section_timetable(a10, [{"day_of_week": 0, "period": 1, "subject_id": w.sci,
                                           "room_id": w.labs[0]},
                                          {"day_of_week": 0, "period": 2, "subject_id": w.mat}])
    return w, a10


def _leave(store, w, teacher):
    leave = store.apply_for_leave(school_id="s1", academic_year_id=w.year, teacher_id=teacher, start_date=MON,
                                  end_date=MON, kind="full_day", reason="unwell", created_by=teacher)
    return store.decide_leave(leave.id, approve=True, decided_by="p1")[1]


def test_one_co_teacher_away_is_not_a_substitution(store):
    w, a10 = _co_taught_week(store)
    subs = _leave(store, w, "ana0")
    assert [(s.section_id, s.period) for s in subs] == [], "dev is there: no substitute needed"
    [science] = [r for r in store.day_view(w.year, MON, section_id=a10) if r["period"] == 1]
    assert (science["kind"], science["teacherId"]) == ("co_teacher", "dev")
    [mine] = [r for r in store.day_view(w.year, MON, teacher_id="ana0") if r["period"] == 1]
    assert mine["kind"] == "away"
    [devs] = store.day_view(w.year, MON, teacher_id="dev")
    assert (devs["period"], devs["teacherId"]) == (1, "dev")


def test_both_away_opens_a_substitution_whichever_went_second(store):
    w, a10 = _co_taught_week(store)
    assert _leave(store, w, "dev") == []
    [sub] = _leave(store, w, "ana0")
    assert (sub.section_id, sub.period, sub.subject_id) == (a10, 1, w.sci)
    [row] = [r for r in store.day_view(w.year, MON, section_id=a10) if r["period"] == 1]
    assert row["kind"] in ("substitute", "uncovered") and row["coTeacherId"] is None


def test_a_co_teachers_period_keeps_them_off_the_substitute_list(store):
    w, a10 = _co_taught_week(store)
    # Bala's Maths in 10-A period 2 needs cover; dev co-teaches 10-A period 1
    # only, so dev is free in period 2 and may be proposed, but not for a
    # period-1 clash elsewhere.
    b10 = w.sections[1]
    store.replace_section_timetable(b10, [{"day_of_week": 0, "period": 1, "subject_id": w.mat}])
    subs = {s.section_id: s for s in _leave(store, w, "bala0")}
    candidates = [c.teacher_id for c in store.substitute_candidates(subs[b10].id)]
    assert "dev" not in candidates, "dev co-teaches 10-A in period 1"


# --------------------------------------------------------------------- #
# Through the routes
# --------------------------------------------------------------------- #

def test_routes_set_the_new_fields_and_keep_them_when_left_out(tmp_path, monkeypatch):
    from test_assessment_routes_auth import _boot_client, _register

    with _boot_client(tmp_path, monkeypatch) as client:
        p1 = _register(client, "school_1", "p1@example.com", "Priya", principal_key="test-bootstrap-key")
        p2 = _register(client, "school_2", "p2@example.com", "Ravi", principal_key="test-bootstrap-key")
        t1 = _register(client, "school_1", "t1@example.com", "Ana")
        t2 = _register(client, "school_1", "t2@example.com", "Dev")
        other = _register(client, "school_2", "o@example.com", "Omar")
        auth = {"Authorization": f"Bearer {p1['token']}"}
        from academicos.curriculum import routes as curriculum_routes
        store = curriculum_routes._require()
        w = _school(store, sections=("A",), labs=1)
        # _school made the year for "s1"; move it to the real school.
        store._exec("UPDATE academic_years SET school_id='school_1'")
        store._exec("UPDATE sections SET school_id='school_1'")
        store._exec("UPDATE rooms SET school_id='school_1'")
        store._exec("UPDATE teaching_allocations SET school_id='school_1'")
        store._commit()
        url = f"/api/v1/curriculum/sections/{w.sections[0]}/allocations/{w.sci}"
        base = {"teacherId": t1["user"]["id"], "periodsPerWeek": 6}
        r = client.put(url, json={**base, "coTeacherId": t2["user"]["id"], "doublePeriods": 1}, headers=auth)
        assert r.status_code == 200, r.text
        assert (r.json()["coTeacherId"], r.json()["roomKind"], r.json()["doublePeriods"]) == \
            (t2["user"]["id"], "lab", 1)
        kept = client.put(url, json=base, headers=auth).json()
        assert (kept["coTeacherId"], kept["roomKind"], kept["doublePeriods"]) == (t2["user"]["id"], "lab", 1)
        cleared = client.put(url, json={**base, "coTeacherId": None, "roomKind": None}, headers=auth).json()
        assert (cleared["coTeacherId"], cleared["roomKind"]) == (None, None)
        assert client.put(url, json={**base, "coTeacherId": other["user"]["id"]}, headers=auth).status_code == 403

        ru = f"/api/v1/curriculum/academic-years/{w.year}/room-unavailability"
        body = {"slots": [{"dayOfWeek": 0, "period": 1}]}
        assert client.put(f"{ru}/{w.labs[0]}", json=body,
                          headers={"Authorization": f"Bearer {t1['token']}"}).status_code == 403
        assert client.put(f"{ru}/{w.labs[0]}", json=body,
                          headers={"Authorization": f"Bearer {p2['token']}"}).status_code == 403
        assert client.put(f"{ru}/{w.labs[0]}", json=body, headers=auth).status_code == 200
        listed = client.get(ru, headers={"Authorization": f"Bearer {t1['token']}"}).json()
        assert listed == [{"roomId": w.labs[0], "slots": [{"dayOfWeek": 0, "period": 1}]}]


def test_forty_sections_with_labs_and_doubles_are_solved_inside_a_minute(store):
    """NFR-3 (a 40-section school in under 60 s) still holds with labs: classes
    9 and 10 (16 sections) do Science in three shared labs, with one double
    period a week for the practical."""
    import time

    year = store.create_academic_year(school_id="s1", label="2026-27", start_date="2026-04-01",
                                      end_date="2027-03-31")
    store.create_bell_schedule(academic_year_id=year.id, name="Main", slots=BELL)
    for i in range(3):
        store.create_room(school_id="s1", name=f"Lab {i + 1}", kind="lab")
    for g in (6, 7, 8, 9, 10):
        grade = store.create_grade(academic_year_id=year.id, number=g)
        secs = store.sections_for_grade(grade.id)
        for name in "BCDEFGH":
            secs.append(store.create_section(grade_id=grade.id, name=name))
        for subj_name, ppw in (("Maths", 8), ("Science", 7), ("English", 6), ("Hindi", 6), ("Social", 6),
                               ("Sanskrit", 3), ("Computer", 2), ("Art", 2)):
            subj = store.create_subject(grade_id=grade.id, name=subj_name)
            lab = subj_name == "Science" and g >= 9
            for i, sec in enumerate(secs):
                store.set_allocation(section_id=sec.id, subject_id=subj.id, teacher_id=f"t_{g}_{subj_name}_{i // 4}",
                                     periods_per_week=ppw, room_kind="lab" if lab else None,
                                     double_periods=1 if lab else 0)
    assert len(store.sections_for_year(year.id)) == 40
    started = time.monotonic()
    result = solve(store, year.id, SolveOptions(time_limit_seconds=60))
    elapsed = time.monotonic() - started
    assert result.status == "solved", result.problems
    assert elapsed < 60
    store.apply_solved_timetable(year.id, result.entries, {s.id for s in store.sections_for_year(year.id)})
    assert _lab_and_pair_violations(store, year.id) == []
