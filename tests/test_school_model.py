"""The school model (M1.2-M1.3): teaching allocations, rooms, bell schedules
and each section's timetable, through the real HTTP routes as signed-in users.

The case that motivated it is audit D115 (docs/audits/2026-09-28-09649eb.md):
periods per week and weekday slots were stored once per subject NAME per year,
so every class's Science shared one timetable. Here a subject is a grade's own
row, so class 6's Science and class 10's Science are separate cells with
separate weeks -- `test_class_6_science_and_class_10_science_are_separate`.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from _auth_helpers import register_invited
from test_assessment_routes_auth import _boot_client, _register

BASE = "/api/v1/curriculum"
KEY = "test-bootstrap-key"
YEAR = {"academicYearLabel": "2026-27", "startDate": "2026-04-01", "endDate": "2027-03-31"}
# Assembly, four periods, a break, four periods.
BELL = {"name": "Main", "slots": [
    {"start": "07:50", "end": "08:05", "kind": "assembly"},
    {"start": "08:05", "end": "08:45"}, {"start": "08:45", "end": "09:25"},
    {"start": "09:25", "end": "10:05"}, {"start": "10:05", "end": "10:45"},
    {"start": "10:45", "end": "11:05", "kind": "break"},
    {"start": "11:05", "end": "11:45"}, {"start": "11:45", "end": "12:25"},
    {"start": "12:25", "end": "13:05"}, {"start": "13:05", "end": "13:45"},
]}


def _h(user):
    return {"Authorization": f"Bearer {user['token']}"}


@pytest.fixture
def w(tmp_path, monkeypatch):
    with _boot_client(tmp_path, monkeypatch) as c:
        p1 = _register(c, "school_1", "p1@example.com", "Priya", principal_key=KEY)
        p2 = _register(c, "school_2", "p2@example.com", "Ravi", principal_key=KEY)
        t1 = _register(c, "school_1", "t1@example.com", "Ana")
        t2 = _register(c, "school_1", "t2@example.com", "Bala")
        t_other = _register(c, "school_2", "t9@example.com", "Omar")
        stu = register_invited(c, "school_1", "s1@example.com", name="Asha", role="student")
        g10 = c.post(f"{BASE}/seed/cbse", json={**YEAR, "grade": 10}, headers=_h(p1)).json()
        g6 = c.post(f"{BASE}/seed/cbse", json={**YEAR, "grade": 6}, headers=_h(p1)).json()
        assert g10["academicYearId"] == g6["academicYearId"]
        year = g10["academicYearId"]
        sections = {f"{s['gradeNumber']}-{s['name']}": s["id"]
                    for s in c.get(f"{BASE}/academic-years/{year}/sections", headers=_h(p1)).json()}
        b = c.post(f"{BASE}/grades/{g10['gradeId']}/sections", json={"name": "B"}, headers=_h(p1)).json()
        sections["10-B"] = b["id"]

        def subjects(grade_id):
            return {s["name"]: s["id"] for s in
                    c.get(f"{BASE}/grades/{grade_id}/subjects", headers=_h(p1)).json()}
        yield SimpleNamespace(
            c=c, p1=_h(p1), p2=_h(p2), t1=_h(t1), stu=_h(stu), year=year, sec=sections,
            t1_id=t1["user"]["id"], t2_id=t2["user"]["id"], t_other=t_other["user"]["id"],
            stu_id=stu["user"]["id"], sub10=subjects(g10["gradeId"]), sub6=subjects(g6["gradeId"]),
            grade10=g10["gradeId"])


def _alloc(w, section, subject, teacher=None, n=6, auth=None):
    return w.c.put(f"{BASE}/sections/{w.sec[section]}/allocations/{subject}",
                   json={"teacherId": teacher, "periodsPerWeek": n}, headers=auth or w.p1)


def _bell(w):
    r = w.c.post(f"{BASE}/academic-years/{w.year}/bell-schedules", json=BELL, headers=w.p1)
    assert r.status_code == 200, r.text
    return r.json()


def _week(w, section, entries, auth=None):
    return w.c.put(f"{BASE}/sections/{w.sec[section]}/timetable", json={"entries": entries},
                   headers=auth or w.p1)


def _e(day, period, subject, **kw):
    return {"dayOfWeek": day, "period": period, "subjectId": subject, **kw}


def _audit(action):
    from academicos.assessment.audit_log import get_audit_log
    from academicos.curriculum import routes as cr
    return list(reversed(get_audit_log(cr._cfg.data_root).for_action(action)))


# ---------------- allocations ----------------

def test_an_allocation_cell_is_set_listed_and_audited(w):
    sci = w.sub10["Science"]
    r = _alloc(w, "10-A", sci, w.t1_id, 6)
    assert r.status_code == 200, r.text
    assert r.json()["periodsPerWeek"] == 6 and r.json()["teacherId"] == w.t1_id
    again = _alloc(w, "10-A", sci, w.t2_id, 7)          # the same cell, changed
    assert again.status_code == 200 and again.json()["id"] == r.json()["id"]
    [cell] = w.c.get(f"{BASE}/academic-years/{w.year}/allocations", headers=w.t1).json()
    assert (cell["teacherId"], cell["periodsPerWeek"]) == (w.t2_id, 7)
    first, second = _audit("allocation_set")
    assert first["details"]["before"] is None
    assert second["details"]["before"] == {"teacherId": w.t1_id, "periodsPerWeek": 6}
    assert second["details"]["after"] == {"teacherId": w.t2_id, "periodsPerWeek": 7}


def test_an_allocation_is_checked(w):
    sci = w.sub10["Science"]
    assert _alloc(w, "10-A", sci, w.t_other).status_code == 403        # another school's teacher
    assert _alloc(w, "10-A", sci, w.stu_id).status_code == 422         # a student cannot teach
    assert _alloc(w, "10-A", w.sub6["Science"]).status_code == 422     # class 6's subject on 10-A
    assert _alloc(w, "10-A", sci, n=0).status_code == 422
    assert _alloc(w, "10-A", sci, auth=w.t1).status_code == 403        # teachers read, never write
    assert _alloc(w, "10-A", sci, auth=w.p2).status_code == 403        # another school's principal


def test_class_6_science_and_class_10_science_are_separate(w):
    """Audit D115: one Science timetable per year name, shared by every class."""
    _bell(w)
    assert _alloc(w, "6-A", w.sub6["Science"], w.t1_id, 5).status_code == 200
    assert _alloc(w, "10-A", w.sub10["Science"], w.t2_id, 6).status_code == 200
    six = _week(w, "6-A", [_e(d, 1, w.sub6["Science"]) for d in range(5)])
    ten = _week(w, "10-A", [_e(d, 2, w.sub10["Science"]) for d in range(6)])
    assert six.status_code == 200 and ten.status_code == 200, (six.text, ten.text)
    assert len(six.json()["entries"]) == 5 and len(ten.json()["entries"]) == 6
    assert six.json()["gaps"] == [{"subjectId": w.sub6["Science"], "allocated": 5, "timetabled": 5}]
    assert ten.json()["gaps"] == [{"subjectId": w.sub10["Science"], "allocated": 6, "timetabled": 6}]
    load = {r["teacherId"]: r for r in
            w.c.get(f"{BASE}/academic-years/{w.year}/teacher-load", headers=w.p1).json()}
    assert load[w.t1_id]["allocatedPerWeek"] == 5 and load[w.t2_id]["allocatedPerWeek"] == 6


# ---------------- bell schedules ----------------

def test_a_bell_numbers_its_teaching_periods_and_the_first_is_the_default(w):
    b = _bell(w)
    assert b["teachingPeriods"] == 8 and b["isDefault"] is True
    assert [s["period"] for s in b["slots"]] == [None, 1, 2, 3, 4, None, 5, 6, 7, 8]
    assert b["days"] == [0, 1, 2, 3, 4, 5]
    junior = w.c.post(f"{BASE}/academic-years/{w.year}/bell-schedules",
                      json={"name": "Junior", "slots": BELL["slots"][:5]}, headers=w.p1).json()
    assert junior["isDefault"] is False and junior["teachingPeriods"] == 4
    # Students read the bells: their day view needs the period times.
    assert w.c.get(f"{BASE}/academic-years/{w.year}/bell-schedules", headers=w.stu).status_code == 200


def test_a_bell_is_checked(w):
    overlap = {"name": "Bad", "slots": [{"start": "08:00", "end": "08:40"},
                                        {"start": "08:30", "end": "09:10"}]}
    r = w.c.post(f"{BASE}/academic-years/{w.year}/bell-schedules", json=overlap, headers=w.p1)
    assert r.status_code == 422 and "before the previous slot ends" in r.json()["detail"]
    backwards = {"name": "Bad", "slots": [{"start": "09:00", "end": "08:00"}]}
    assert w.c.post(f"{BASE}/academic-years/{w.year}/bell-schedules", json=backwards,
                    headers=w.p1).status_code == 422
    no_teaching = {"name": "Bad", "slots": [{"start": "09:00", "end": "09:30", "kind": "break"}]}
    assert w.c.post(f"{BASE}/academic-years/{w.year}/bell-schedules", json=no_teaching,
                    headers=w.p1).status_code == 422
    assert w.c.post(f"{BASE}/academic-years/{w.year}/bell-schedules", json=BELL,
                    headers=w.t1).status_code == 403


def test_a_bell_cannot_drop_periods_the_timetable_uses(w):
    b = _bell(w)
    _alloc(w, "10-A", w.sub10["Science"], w.t1_id, 6)
    assert _week(w, "10-A", [_e(0, 8, w.sub10["Science"])]).status_code == 200
    shorter = w.c.put(f"{BASE}/bell-schedules/{b['id']}", json={"slots": BELL["slots"][:5]},
                      headers=w.p1)
    assert shorter.status_code == 422 and "period 8" in shorter.json()["detail"]


# ---------------- the timetable ----------------

def test_a_week_with_a_teacher_in_two_places_is_refused_whole(w):
    _bell(w)
    sci = w.sub10["Science"]
    _alloc(w, "10-A", sci, w.t1_id, 6)
    _alloc(w, "10-B", sci, w.t1_id, 6)
    assert _week(w, "10-A", [_e(0, 1, sci), _e(1, 1, sci)]).status_code == 200
    r = _week(w, "10-B", [_e(0, 1, sci), _e(0, 2, sci)])       # Monday 1: Ana is in 10-A
    assert r.status_code == 409
    assert r.json()["detail"]["clashes"] == ["Monday period 1: the teacher already teaches 10-A then"]
    week_b = w.c.get(f"{BASE}/sections/{w.sec['10-B']}/timetable", headers=w.p1).json()
    assert week_b["entries"] == [], "a refused week writes nothing"


def test_a_room_in_two_places_is_refused(w):
    _bell(w)
    lab = w.c.post(f"{BASE}/rooms", json={"name": "Science Lab", "kind": "lab"}, headers=w.p1).json()
    sci = w.sub10["Science"]
    _alloc(w, "10-A", sci, w.t1_id, 6)
    _alloc(w, "10-B", sci, w.t2_id, 6)
    assert _week(w, "10-A", [_e(2, 3, sci, roomId=lab["id"])]).status_code == 200
    r = _week(w, "10-B", [_e(2, 3, sci, roomId=lab["id"])])
    assert r.status_code == 409
    assert r.json()["detail"]["clashes"] == ["Wednesday period 3: the room is already used by 10-A then"]


def test_every_other_kind_of_bad_week_is_named(w):
    _bell(w)
    sci, maths = w.sub10["Science"], w.sub10["Mathematics"]
    _alloc(w, "10-A", sci, w.t1_id, 2)
    r = _week(w, "10-A", [_e(0, 1, sci), _e(0, 1, sci), _e(1, 9, sci), _e(6, 1, sci),
                          _e(2, 1, maths), _e(3, 1, sci), _e(4, 1, sci)])
    assert r.status_code == 409
    clashes = r.json()["detail"]["clashes"]
    assert "Monday period 1: given twice for 10-A" in clashes
    assert "Tuesday period 9: Main has periods 1 to 8" in clashes
    assert any(c.startswith("Sunday period 1: the school does not teach on Sunday") for c in clashes)
    assert any(c.startswith("Wednesday period 1: 10-A has no allocation for that subject") for c in clashes)
    assert any("gets 3 periods a week here but is allocated 2" in c for c in clashes)


def test_a_week_needs_a_bell(w):
    _alloc(w, "10-A", w.sub10["Science"], w.t1_id, 6)
    r = _week(w, "10-A", [_e(0, 1, w.sub10["Science"])])
    assert r.status_code == 422 and "bell schedule" in r.json()["detail"]


def test_an_allocation_cannot_shrink_below_or_vanish_under_its_timetable(w):
    _bell(w)
    sci = w.sub10["Science"]
    _alloc(w, "10-A", sci, w.t1_id, 6)
    assert _week(w, "10-A", [_e(d, 1, sci) for d in range(4)]).status_code == 200
    assert _alloc(w, "10-A", sci, w.t1_id, 3).status_code == 422
    r = w.c.delete(f"{BASE}/sections/{w.sec['10-A']}/allocations/{sci}", headers=w.p1)
    assert r.status_code == 409
    # A new teacher for the cell takes over its periods.
    assert _alloc(w, "10-A", sci, w.t2_id, 6).status_code == 200
    week = w.c.get(f"{BASE}/sections/{w.sec['10-A']}/timetable", headers=w.p1).json()
    assert {e["teacherId"] for e in week["entries"]} == {w.t2_id}


def test_my_timetable_is_the_teachers_and_the_students_own_week(w):
    _bell(w)
    sci, maths = w.sub10["Science"], w.sub10["Mathematics"]
    _alloc(w, "10-A", sci, w.t1_id, 6)
    _alloc(w, "10-B", maths, w.t1_id, 6)
    _alloc(w, "10-B", sci, w.t2_id, 6)
    _week(w, "10-A", [_e(0, 1, sci)])
    _week(w, "10-B", [_e(0, 2, maths), _e(1, 1, sci)])
    mine = w.c.get(f"{BASE}/my-timetable", headers=w.t1).json()
    assert sorted((e["sectionId"], e["period"]) for e in mine["entries"]) == \
        sorted([(w.sec["10-A"], 1), (w.sec["10-B"], 2)])
    assert mine["bellSchedule"]["teachingPeriods"] == 8
    w.c.post(f"{BASE}/student-enrollments", json={"studentId": w.stu_id, "sectionId": w.sec["10-B"]},
             headers=w.p1)
    theirs = w.c.get(f"{BASE}/my-timetable", headers=w.stu).json()
    assert theirs["sectionId"] == w.sec["10-B"] and len(theirs["entries"]) == 2


def _timetable_notices(user_id):
    from academicos.operations.routes import store
    return sum(1 for n in store().inbox(user_id) if n.kind == "timetable_published")


def test_a_hand_made_week_tells_its_students_and_the_teachers_it_changes(w):
    """N-8-5: a manual PUT of a section's week used to notify nobody, and the
    solver's publish told teachers only."""
    w.c.post(f"{BASE}/student-enrollments", json={"studentId": w.stu_id, "sectionId": w.sec["10-A"]},
             headers=w.p1)
    _bell(w)
    sci, maths = w.sub10["Science"], w.sub10["Mathematics"]
    _alloc(w, "10-A", sci, w.t1_id, 6)
    _alloc(w, "10-A", maths, w.t2_id, 6)
    assert _week(w, "10-A", [_e(0, 1, sci), _e(0, 2, maths)]).status_code == 200
    assert [_timetable_notices(u) for u in (w.stu_id, w.t1_id, w.t2_id)] == [1, 1, 1]
    # Bala's period moves and Ana's does not: the class and Bala hear, Ana does not.
    assert _week(w, "10-A", [_e(0, 1, sci), _e(0, 3, maths)]).status_code == 200
    assert [_timetable_notices(u) for u in (w.stu_id, w.t1_id, w.t2_id)] == [2, 1, 2]
    # The same week saved again changes nothing and tells no one; a refused one neither.
    assert _week(w, "10-A", [_e(0, 1, sci), _e(0, 3, maths)]).status_code == 200
    assert _week(w, "10-A", [_e(0, 1, sci), _e(0, 1, maths)]).status_code == 409
    assert [_timetable_notices(u) for u in (w.stu_id, w.t1_id, w.t2_id)] == [2, 1, 2]
    items = w.c.get("/api/v1/notifications", headers=w.stu).json()["items"]
    assert items[0]["title"] == "Timetable updated" and items[0]["link"] == "/my-timetable"


# ---------------- rooms and scoping ----------------

def test_rooms_are_named_once_and_kept_while_used(w):
    r = w.c.post(f"{BASE}/rooms", json={"name": "Lab 1", "kind": "lab", "capacity": 40}, headers=w.p1)
    assert r.status_code == 200 and r.json()["capacity"] == 40
    assert w.c.post(f"{BASE}/rooms", json={"name": "lab 1"}, headers=w.p1).status_code == 422
    assert w.c.post(f"{BASE}/rooms", json={"name": "X", "kind": "garage"}, headers=w.p1).status_code == 422
    renamed = w.c.patch(f"{BASE}/rooms/{r.json()['id']}", json={"name": "Chemistry Lab"}, headers=w.p1)
    assert renamed.status_code == 200 and renamed.json()["capacity"] == 40
    _bell(w)
    _alloc(w, "10-A", w.sub10["Science"], w.t1_id, 6)
    _week(w, "10-A", [_e(0, 1, w.sub10["Science"], roomId=r.json()["id"])])
    assert w.c.delete(f"{BASE}/rooms/{r.json()['id']}", headers=w.p1).status_code == 409
    assert w.c.get(f"{BASE}/rooms", headers=w.t1).status_code == 200
    assert w.c.get(f"{BASE}/rooms", headers=w.stu).status_code == 403


def test_another_school_can_neither_read_nor_change_any_of_it(w):
    b = _bell(w)
    room = w.c.post(f"{BASE}/rooms", json={"name": "Hall"}, headers=w.p1).json()
    sec = w.sec["10-A"]
    assert w.c.get(f"{BASE}/academic-years/{w.year}/allocations", headers=w.p2).status_code == 403
    assert w.c.get(f"{BASE}/academic-years/{w.year}/timetable", headers=w.p2).status_code == 403
    assert w.c.get(f"{BASE}/sections/{sec}/timetable", headers=w.p2).status_code == 403
    assert w.c.put(f"{BASE}/sections/{sec}/timetable", json={"entries": []}, headers=w.p2).status_code == 403
    assert w.c.put(f"{BASE}/bell-schedules/{b['id']}", json={"name": "Mine"}, headers=w.p2).status_code == 403
    assert w.c.delete(f"{BASE}/rooms/{room['id']}", headers=w.p2).status_code == 403
    assert w.c.get(f"{BASE}/academic-years/{w.year}/teacher-load", headers=w.t1).status_code == 403
    assert w.c.get(f"{BASE}/rooms", headers=w.p2).json() == []
