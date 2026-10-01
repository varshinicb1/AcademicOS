"""Teaching that spans sections (SCH-2/SCH-8, v3 audit N-3-20): an elective
group whose students split into parallel lanes, a combined class, and a
section split or merged mid-year -- each through the solver and checked by
an independent clock-time checker, then through the HTTP routes.

Before N-3-20 the model had one allocation per (section, subject) and no
group across sections: an elective block or two sections taught together
could not be expressed, and a section could be neither split nor merged.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from types import SimpleNamespace

import pytest

from academicos.curriculum.school_model import TimetableClash
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


def _school(store):
    """Class 9 in three sections and 10-A. Hindi's teacher also teaches 10-A."""
    year = store.create_academic_year(school_id="s1", label="2026-27", start_date="2026-04-01",
                                      end_date="2027-03-31")
    store.create_bell_schedule(academic_year_id=year.id, name="Main", slots=EIGHT)
    hall = store.create_room(school_id="s1", name="Hall", kind="hall")
    lab = store.create_room(school_id="s1", name="Language Lab", kind="lab")
    nine = store.create_grade(academic_year_id=year.id, number=9)
    secs = store.sections_for_grade(nine.id) + [store.create_section(grade_id=nine.id, name=n) for n in "BC"]
    subj = {n: store.create_subject(grade_id=nine.id, name=n)
            for n in ("Maths", "Science", "English", "Social", "Hindi", "Sanskrit", "French", "PE")}
    for i, sec in enumerate(secs):
        for name, ppw in (("Maths", 7), ("Science", 7), ("English", 6), ("Social", 6)):
            store.set_allocation(section_id=sec.id, subject_id=subj[name].id, teacher_id=f"t_{name}_{i // 2}",
                                 periods_per_week=ppw)
    ten = store.create_grade(academic_year_id=year.id, number=10)
    [ten_a] = store.sections_for_grade(ten.id)
    hindi10 = store.create_subject(grade_id=ten.id, name="Hindi")
    store.set_allocation(section_id=ten_a.id, subject_id=hindi10.id, teacher_id="t_hindi", periods_per_week=6)
    for n, sec in enumerate(secs):
        for k in range(4):
            store.enroll_student(school_id="s1", student_id=f"stu_{sec.name}{k}", section_id=sec.id)
    return SimpleNamespace(year=year.id, a=secs[0], b=secs[1], c=secs[2], subj=subj, ten_a=ten_a,
                           hindi10=hindi10, hall=hall, lab=lab)


def _elective(store, s, sections=None, **kw):
    return store.save_teaching_group(
        academic_year_id=s.year, kind="elective", name=kw.get("name", "Third language"), periods_per_week=4,
        section_ids=[x.id for x in (sections or (s.a, s.b, s.c))],
        lanes=kw.get("lanes") or [
            {"subject_id": s.subj["Hindi"].id, "teacher_id": "t_hindi", "student_ids": ["stu_A0", "stu_B0"]},
            {"subject_id": s.subj["Sanskrit"].id, "teacher_id": "t_sanskrit"},
            {"subject_id": s.subj["French"].id, "teacher_id": "t_french", "room_id": s.lab.id}])[1]


def _combined(store, s):
    return store.save_teaching_group(
        academic_year_id=s.year, kind="combined", name="PE 9-B and 9-C", periods_per_week=2,
        section_ids=[s.b.id, s.c.id],
        lanes=[{"subject_id": s.subj["PE"].id, "teacher_id": "t_pe", "room_id": s.hall.id}])[1]


def _solve_and_apply(store, year, sections=None):
    result = solve(store, year, SolveOptions(section_ids=sections, time_limit_seconds=30))
    assert result.status == "solved", result.problems
    store.apply_solved_timetable(year, result.entries, sections or {x.id for x in store.sections_for_year(year)},
                                 result.group_sessions, result.group_ids)
    return result


def _clashes(store, year):
    """Every double booking by the clock, from section rows AND group
    periods: a teacher, a room or a section in two places at once."""
    times = {sec.id: {sl.period: (_minutes(sl.start), _minutes(sl.end)) for sl in store.bell_for_section(sec).slots
                      if sl.period} for sec in store.sections_for_year(year)}
    busy: dict[tuple, list] = defaultdict(list)
    for e in store.timetable_for_year(year):
        span = times[e.section_id][e.period]
        for t in {e.teacher_id, e.co_teacher_id} - {None}:
            busy[("teacher", t, e.day_of_week)].append(span)
        if e.room_id:
            busy[("room", e.room_id, e.day_of_week)].append(span)
        busy[("section", e.section_id, e.day_of_week)].append(span)
    for g, d, p in store.group_periods_for_year(year):
        span = times[g.section_ids[0]][p]
        for t in g.teacher_ids:
            busy[("teacher", t, d)].append(span)
        for r in g.room_ids:
            busy[("room", r, d)].append(span)
        for sid in g.section_ids:
            busy[("section", sid, d)].append(times[sid][p])
    out = []
    for key, spans in busy.items():
        spans.sort()
        out += [(key, a, b) for a, b in zip(spans, spans[1:]) if b[0] < a[1]]
    return out


def _allocations_met(store, year):
    count = Counter((e.section_id, e.subject_id) for e in store.timetable_for_year(year))
    return [a for a in store.allocations_for_year(year) if count[(a.section_id, a.subject_id)] != a.periods_per_week]


def test_an_elective_across_sections_is_one_simultaneous_block(store):
    """SCH-8: 9-A, 9-B and 9-C split into Hindi, Sanskrit and French at the
    same time, three teachers at once; Hindi's teacher also teaches 10-A."""
    s = _school(store)
    group = _elective(store, s)
    result = _solve_and_apply(store, s.year)
    placed = [(d, p) for g, d, p in store.group_periods_for_year(s.year) if g.id == group.id]
    assert len(placed) == group.periods_per_week == 4
    assert len(result.group_sessions) == 4 and result.group_ids == {group.id}
    for d, p in placed:
        # No member section has a period of its own then: the whole class is in its lanes.
        assert not [e for e in store.timetable_for_year(s.year)
                    if e.section_id in group.section_ids and (e.day_of_week, e.period) == (d, p)]
    assert _clashes(store, s.year) == [], "no teacher, lab or section is in two places"
    assert _allocations_met(store, s.year) == []
    # The lane teachers' week and load count the group's periods.
    lanes = store.group_periods_for_teacher("t_hindi", s.year)
    assert len(lanes) == 4 and {lane.subject_id for _, lane, _, _ in lanes} == {s.subj["Hindi"].id}
    load = {r["teacherId"]: r for r in store.teacher_load(s.year)}
    assert load["t_hindi"]["allocatedPerWeek"] == 10 and load["t_hindi"]["timetabledPerWeek"] == 10
    assert load["t_french"]["sectionSubjects"] == 1


def test_a_combined_class_is_one_teacher_in_one_room_for_both_sections(store):
    """SCH-8: 9-B and 9-C taught PE together, by one teacher, in the hall."""
    s = _school(store)
    _elective(store, s)
    group = _combined(store, s)
    _solve_and_apply(store, s.year)
    placed = [(d, p) for g, d, p in store.group_periods_for_year(s.year) if g.id == group.id]
    assert len(placed) == 2
    assert _clashes(store, s.year) == []
    # One teacher for both sections at once is one period of theirs, not two.
    assert store.teacher_load(s.year)[[r["teacherId"] for r in store.teacher_load(s.year)].index("t_pe")][
        "timetabledPerWeek"] == 2
    # A re-solve keeps every period where it is.
    again = solve(store, s.year, SolveOptions(time_limit_seconds=30))
    assert (again.moved_or_added, again.removed) == (0, 0)


def test_a_section_split_mid_year_takes_its_students_allocations_and_groups(store):
    """SCH-8: 9-A splits; two students go to a new 9-D, which gets 9-A's
    allocations and groups, and then a week of its own that clashes with
    nothing -- 9-A's teachers now teach both halves."""
    s = _school(store)
    group = _elective(store, s)
    _solve_and_apply(store, s.year)
    week_a = {(e.day_of_week, e.period, e.subject_id) for e in store.timetable_for_section(s.a.id)}
    out = store.split_section(s.a.id, name="D", student_ids=["stu_A2", "stu_A3"])
    d = out["section"]
    assert (out["moved"], out["allocations"], out["groups"]) == (2, 4, [group.id])
    assert sorted(e.student_id for e in store.enrollments_for_section(d.id)) == ["stu_A2", "stu_A3"]
    assert sorted(e.student_id for e in store.enrollments_for_section(s.a.id)) == ["stu_A0", "stu_A1"]
    assert d.id in store.get_teaching_group(group.id).section_ids
    assert {(e.day_of_week, e.period, e.subject_id) for e in store.timetable_for_section(s.a.id)} == week_a
    with pytest.raises(ValueError):
        store.split_section(s.a.id, name="E", student_ids=["stu_A0", "stu_A1"])      # would empty 9-A
    with pytest.raises(ValueError):
        store.split_section(s.a.id, name="B", student_ids=["stu_A0"])               # 9-B exists
    # The new section's week: only it is solved; the group's periods stay
    # and take 9-D's periods too.
    placed = {(dd, p) for g, dd, p in store.group_periods_for_year(s.year)}
    _solve_and_apply(store, s.year, {d.id})
    assert len(store.timetable_for_section(d.id)) == 26
    assert not {(e.day_of_week, e.period) for e in store.timetable_for_section(d.id)} & placed
    assert {(dd, p) for g, dd, p in store.group_periods_for_year(s.year)} == placed
    assert _clashes(store, s.year) == [] and _allocations_met(store, s.year) == []


def test_a_section_merged_mid_year_moves_its_students_and_frees_its_teachers(store):
    """SCH-8: 9-C merges into 9-B: its students follow 9-B's week, and its
    own periods and allocations go, so its teachers are free."""
    s = _school(store)
    group = _elective(store, s)
    _combined(store, s)
    _solve_and_apply(store, s.year)
    assert {r["teacherId"]: r for r in store.teacher_load(s.year)}["t_Maths_1"]["timetabledPerWeek"] == 7
    out = store.merge_section(s.c.id, s.b.id)
    assert (out["moved"], out["periods"], out["allocations"]) == (4, 26, 4)
    assert store.get_section(s.c.id) is None
    assert len(store.enrollments_for_section(s.b.id)) == 8
    assert not [e for e in store.timetable_for_year(s.year) if e.section_id == s.c.id]
    assert "t_Maths_1" not in {r["teacherId"] for r in store.teacher_load(s.year)}
    assert store.get_teaching_group(group.id).section_ids == [s.a.id, s.b.id]
    assert _clashes(store, s.year) == []


def test_a_merge_is_refused_while_the_section_is_in_a_group_the_other_is_not(store):
    s = _school(store)
    _elective(store, s, sections=(s.a, s.c), lanes=[{"subject_id": s.subj["Hindi"].id, "teacher_id": "t_hindi"},
                                                    {"subject_id": s.subj["French"].id, "teacher_id": "t_french"}])
    with pytest.raises(ValueError, match="9-C is in Third language and 9-B is not"):
        store.merge_section(s.c.id, s.b.id)
    with pytest.raises(ValueError, match="one class"):
        store.merge_section(s.c.id, s.ten_a.id)
    assert len(store.enrollments_for_section(s.c.id)) == 4, "a refused merge moves no one"


def test_a_deleted_section_leaves_its_groups(store):
    """A section removed while in a group: the group goes on with its other
    sections and is still placed (it was dropped from the solve)."""
    s = _school(store)
    group = _combined(store, s)
    extra = store.create_section(grade_id=s.b.grade_id, name="D")
    store.save_teaching_group(academic_year_id=s.year, kind="combined", name=group.name, periods_per_week=2,
                              section_ids=[s.b.id, s.c.id, extra.id], lanes=[{
                                  "subject_id": s.subj["PE"].id, "teacher_id": "t_pe", "room_id": s.hall.id}],
                              group_id=group.id)
    store.delete_section(extra.id)
    assert store.get_teaching_group(group.id).section_ids == [s.b.id, s.c.id]
    _solve_and_apply(store, s.year)
    assert len([1 for g, _, _ in store.group_periods_for_year(s.year) if g.id == group.id]) == 2


def test_a_hand_made_week_cannot_take_a_group_period_or_its_teachers(store):
    """The clash check of a hand-made week knows the groups: a member's
    period in the group is the group's, and a lane's teacher is busy."""
    s = _school(store)
    group = _elective(store, s)
    _solve_and_apply(store, s.year)
    d, p = next((dd, pp) for g, dd, pp in store.group_periods_for_year(s.year) if g.id == group.id)
    week_a = [{"day_of_week": e.day_of_week, "period": e.period, "subject_id": e.subject_id}
              for e in store.timetable_for_section(s.a.id)]
    with pytest.raises(TimetableClash) as refused:
        store.replace_section_timetable(s.a.id, week_a[1:] + [{"day_of_week": d, "period": p,
                                                               "subject_id": week_a[0]["subject_id"]}])
    assert any("9-A is in Third language then" in c for c in refused.value.clashes)
    week_10 = [{"day_of_week": e.day_of_week, "period": e.period, "subject_id": e.subject_id}
               for e in store.timetable_for_section(s.ten_a.id)]
    with pytest.raises(TimetableClash) as refused:
        store.replace_section_timetable(s.ten_a.id, week_10[1:] + [{"day_of_week": d, "period": p,
                                                                    "subject_id": s.hindi10.id}])
    assert any("the teacher already teaches the group Third language then" in c for c in refused.value.clashes)


def test_a_group_is_checked(store):
    s = _school(store)
    hindi, sanskrit = s.subj["Hindi"].id, s.subj["Sanskrit"].id

    def make(**kw):
        args = dict(academic_year_id=s.year, kind="elective", name="X", periods_per_week=3,
                    section_ids=[s.a.id, s.b.id],
                    lanes=[{"subject_id": hindi, "teacher_id": "t1"}, {"subject_id": sanskrit, "teacher_id": "t2"}])
        args.update(kw)
        return store.save_teaching_group(**args)
    with pytest.raises(ValueError, match="two lanes taught at the same time"):
        make(lanes=[{"subject_id": hindi, "teacher_id": "t1"}, {"subject_id": sanskrit, "teacher_id": "t1"}])
    with pytest.raises(ValueError, match="one class"):
        make(section_ids=[s.a.id, s.ten_a.id])
    with pytest.raises(ValueError, match="two sections or more"):
        make(kind="combined", section_ids=[s.a.id], lanes=[{"subject_id": hindi}])
    with pytest.raises(ValueError, match="already taught Maths on its own"):
        make(lanes=[{"subject_id": s.subj["Maths"].id, "teacher_id": "t1"}, {"subject_id": sanskrit}])
    with pytest.raises(ValueError, match="not in the group's sections"):
        make(lanes=[{"subject_id": hindi, "student_ids": ["stu_C0"]}, {"subject_id": sanskrit}])
    make()
    with pytest.raises(ValueError, match="in the group X"):
        store.set_allocation(section_id=s.a.id, subject_id=hindi, teacher_id="t1", periods_per_week=3)


# ---------------- through the routes ----------------

from test_school_model import BASE, _alloc, _bell, w  # noqa: E402,F401 - `w` is a fixture


def test_groups_split_and_merge_through_the_routes(w):
    """The web's calls: create an elective and a combined class, generate,
    read them in each week, then split and merge a section."""
    _bell(w)
    sub = w.sub10
    hall = w.c.post(f"{BASE}/rooms", json={"name": "Hall", "kind": "hall"}, headers=w.p1).json()["id"]
    for sec in ("10-A", "10-B"):
        _alloc(w, sec, sub["Mathematics"], w.t1_id, 6)
    elective = w.c.post(f"{BASE}/academic-years/{w.year}/teaching-groups", headers=w.p1, json={
        "kind": "elective", "name": "Second language", "periodsPerWeek": 3,
        "sectionIds": [w.sec["10-A"], w.sec["10-B"]],
        "lanes": [{"subjectId": sub["Hindi"], "teacherId": w.t1_id},
                  {"subjectId": sub["English"], "teacherId": w.t2_id}]})
    assert elective.status_code == 200, elective.text
    assert elective.json()["sectionNames"] == ["10-A", "10-B"] and elective.json()["periods"] == []
    combined = w.c.post(f"{BASE}/academic-years/{w.year}/teaching-groups", headers=w.p1, json={
        "kind": "combined", "name": "Social Science together", "periodsPerWeek": 2,
        "sectionIds": [w.sec["10-A"], w.sec["10-B"]],
        "lanes": [{"subjectId": sub["Social Science"], "teacherId": w.t2_id, "roomId": hall}]})
    assert combined.status_code == 200, combined.text
    bad = w.c.post(f"{BASE}/academic-years/{w.year}/teaching-groups", headers=w.p1, json={
        "kind": "combined", "name": "Bad", "periodsPerWeek": 2, "sectionIds": [w.sec["10-A"], w.sec["6-A"]],
        "lanes": [{"subjectId": sub["Science"]}]})
    assert bad.status_code == 422 and "one class" in bad.json()["detail"]
    assert w.c.post(f"{BASE}/academic-years/{w.year}/teaching-groups", headers=w.t1, json={
        "kind": "combined", "name": "No", "periodsPerWeek": 1, "sectionIds": [w.sec["10-A"], w.sec["10-B"]],
        "lanes": [{"subjectId": sub["Science"]}]}).status_code == 403

    preview = w.c.post(f"{BASE}/academic-years/{w.year}/timetable/solve", json={}, headers=w.p1).json()
    assert preview["status"] == "solved", preview["problems"]
    assert len(preview["groupSessions"]) == 5
    assert any(c["after"] and c["after"]["groupName"] == "Second language" for c in preview["changes"])
    assert w.c.post(f"{BASE}/academic-years/{w.year}/timetable/previews/{preview['previewId']}/publish",
                    headers=w.p1).status_code == 200
    listed = {g["name"]: g for g in w.c.get(f"{BASE}/academic-years/{w.year}/teaching-groups",
                                            headers=w.t1).json()}
    assert len(listed["Second language"]["periods"]) == 3 and len(listed["Social Science together"]["periods"]) == 2
    week = w.c.get(f"{BASE}/sections/{w.sec['10-A']}/timetable", headers=w.p1).json()
    assert len(week["entries"]) == 6 and len(week["groupPeriods"]) == 5
    assert {lane["subjectName"] for gp in week["groupPeriods"] if gp["groupName"] == "Second language"
            for lane in gp["lanes"]} == {"Hindi", "English"}
    # Ana's own week: her 12 Maths periods and her 3 Hindi lane periods, once each.
    mine = w.c.get(f"{BASE}/my-timetable", headers=w.t1).json()["entries"]
    assert len(mine) == 15
    lane = [e for e in mine if e["groupId"]]
    assert {(e["subjectName"], e["sectionName"]) for e in lane} == {("Hindi", "10-A, 10-B")}
    assert all(e["startTime"] for e in lane)
    # A student of 10-B sees the group's periods in their week.
    w.c.post(f"{BASE}/student-enrollments", json={"studentId": w.stu_id, "sectionId": w.sec["10-B"]},
             headers=w.p1)
    theirs = w.c.get(f"{BASE}/my-timetable", headers=w.stu).json()["entries"]
    assert {e["subjectName"] for e in theirs if e["groupId"]} == {"Second language", "Social Science"}

    # Split 10-B: the student moves to 10-C, which joins both groups.
    split = w.c.post(f"{BASE}/sections/{w.sec['10-B']}/split", headers=w.p1,
                     json={"name": "C", "studentIds": [w.stu_id]})
    assert split.status_code == 422 and "leave some students" in split.json()["detail"]
    other = _register_student(w, "s2@example.com")
    w.c.post(f"{BASE}/student-enrollments", json={"studentId": other, "sectionId": w.sec["10-B"]}, headers=w.p1)
    split = w.c.post(f"{BASE}/sections/{w.sec['10-B']}/split", headers=w.p1,
                     json={"name": "C", "studentIds": [w.stu_id]})
    assert split.status_code == 200, split.text
    body = split.json()
    assert (body["section"]["name"], body["movedStudents"], body["allocationsCopied"], body["groupsJoined"]) == \
        ("C", 1, 1, 2)
    new = body["section"]["id"]
    assert w.c.post(f"{BASE}/academic-years/{w.year}/timetable/solve", headers=w.p1,
                    json={"apply": True, "sectionIds": [new]}).json()["applied"] is True
    assert len(w.c.get(f"{BASE}/sections/{new}/timetable", headers=w.p1).json()["entries"]) == 6

    # Merge 10-C back into 10-B: the student returns; 10-C's week goes.
    merged = w.c.post(f"{BASE}/sections/{new}/merge", headers=w.p1, json={"intoSectionId": w.sec["10-B"]})
    assert merged.status_code == 200, merged.text
    assert (merged.json()["movedStudents"], merged.json()["periodsRemoved"]) == (1, 6)
    assert w.c.get(f"{BASE}/sections/{new}/timetable", headers=w.p1).status_code == 404
    assert w.c.post(f"{BASE}/sections/{w.sec['10-A']}/merge", headers=w.p2,
                    json={"intoSectionId": w.sec["10-B"]}).status_code == 403
    gid = listed["Social Science together"]["id"]
    assert w.c.delete(f"{BASE}/teaching-groups/{gid}", headers=w.p1).status_code == 200
    assert len(w.c.get(f"{BASE}/sections/{w.sec['10-A']}/timetable", headers=w.p1).json()["groupPeriods"]) == 3


def _register_student(w, email):
    from _auth_helpers import register_invited
    return register_invited(w.c, "school_1", email, name="Bina", role="student")["user"]["id"]
