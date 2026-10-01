"""SCH-8 edge cases the v3 audit found absent or partial, each with a test:

- long leave with a temporary replacement teacher (absent): the replacement
  takes over the absent teacher's periods for the leave's dates and appears
  in cover and in the plans;
- a teacher who joins or leaves mid-year (partial: the timetable followed the
  new teacher, the plans and the cover did not, and there was no test);
- an event day, which marks the day but still teaches.

Half days, exam days and a compensatory working Saturday are in
test_calendar_days.py (N-3-19).

test_cover_routes' world: 2026-06-01 (MON) is a Monday and "today"; period n
runs (7+n):00-(7+n):45. On Mondays 10-A has Science (Ana) in P1 and Maths
(Bala) in P2; 10-B has Maths (Bala) in P1 and Science (Ana) in P2; 9-A has
Science (Chitra) in P1 and Maths (Dev) in P3. A Science plan of one lesson a
week is laid on each Monday.
"""
from __future__ import annotations

from test_assessment_routes_auth import _register
from test_calendar_days import MONDAYS, _plan
from test_cover_exams import _dates
from test_cover_routes import BASE, MON, _apply, _h, w  # noqa: F401 - `w` is a fixture


def _approve(w, leave_id):
    r = w.c.post(f"{BASE}/leave-requests/{leave_id}/decision", json={"approve": True}, headers=w.p)
    assert r.status_code == 200, r.text
    return r.json()


def _schedule(w, who, start="2026-06-01", end="2026-07-31"):
    r = w.c.get(f"{BASE}/my-schedule", params={"start_date": start, "end_date": end}, headers=who)
    assert r.status_code == 200, r.text
    return r.json()


# ---------------------------------------------------------------- long leave, a temporary replacement


def test_a_temporary_replacement_takes_over_a_long_leave(w):
    book = _plan(w, w.a10, w.b10)
    eve = _register(w.c, "school_1", "eve@example.com", "Eve")
    eve_id, eve_h = eve["user"]["id"], _h(eve)
    leave = _apply(w, "ana", startDate=MON, endDate="2026-06-30", reason="maternity leave").json()
    _approve(w, leave["id"])

    # Only the leave admin names the replacement.
    assert w.c.put(f"{BASE}/leave-requests/{leave['id']}/replacement", json={"teacherId": eve_id},
                   headers=w.t["bala"]).status_code == 403
    assert w.c.put(f"{BASE}/leave-requests/{leave['id']}/replacement", json={"teacherId": eve_id},
                   headers=w.p2).status_code == 403
    r = w.c.put(f"{BASE}/leave-requests/{leave['id']}/replacement", json={"teacherId": eve_id}, headers=w.p)
    assert r.status_code == 200, r.text
    assert r.json()["leave"]["replacementId"] == eve_id
    subs = r.json()["substitutions"]
    # Ana's two Monday periods on each of the five Mondays of June.
    assert len(subs) == 10
    assert all((s["substituteId"], s["status"], s["mode"]) == (eve_id, "accepted", "substitute") for s in subs)

    # Cover: nothing is lost, and the register and the day say it is Eve.
    assert w.c.get(f"{BASE}/academic-years/{w.year}/lost-periods", headers=w.p).json() == []
    assert len(w.c.get(f"{BASE}/substitutions", params={"from": MON, "to": "2026-06-30"}, headers=eve_h).json()) == 10
    day = w.c.get(f"{BASE}/my-day", params={"date": "2026-06-08"}, headers=eve_h).json()
    assert {(x["sectionId"], x["period"], x["kind"]) for x in day} == {(w.a10, 1, "substitute"),
                                                                       (w.b10, 2, "substitute")}
    student = w.c.get(f"{BASE}/my-day", params={"date": "2026-06-08"}, headers=w.stu).json()
    assert next(x for x in student if x["period"] == 2)["teacherName"] == "Eve"

    # Plans: Eve has the lessons of the leave's dates, not the ones after it,
    # and nothing is moved (the subject is still taught).
    assert _dates(w, book, w.a10) == MONDAYS
    mine = _schedule(w, eve_h)
    assert sorted({l["date"] for l in mine}) == MONDAYS[:5]
    assert {l["sectionId"] for l in mine} == {w.a10, w.b10}
    in_leave = next(l for l in mine if l["date"] == "2026-06-08")
    assert w.c.patch(f"{BASE}/scheduled-lessons/{in_leave['lessonId']}", json={"status": "completed"},
                     headers=eve_h).status_code == 200
    after = next(l for l in w.store.scheduled_lessons_for_book(w.year, book, w.a10) if l.date == "2026-07-06")
    assert w.c.patch(f"{BASE}/scheduled-lessons/{after.id}", json={"status": "completed"},
                     headers=eve_h).status_code == 403, "Ana is back by then"
    assert w.c.get(f"{BASE}/scheduled-lessons/{in_leave['lessonId']}/history", headers=eve_h).status_code == 200


def test_a_replacement_busy_in_a_period_leaves_it_to_the_engine_and_can_be_taken_off(w):
    """Chitra teaches 9-A in period 1, so she can take Ana's 10-B period 2
    but not her 10-A period 1, which keeps the engine's proposal."""
    leave = _apply(w, "ana", startDate=MON, endDate="2026-06-08", reason="surgery").json()
    _approve(w, leave["id"])
    r = w.c.put(f"{BASE}/leave-requests/{leave['id']}/replacement", json={"teacherId": w.uid["chitra"]},
                headers=w.p)
    assert r.status_code == 200, r.text
    subs = {(s["date"], s["sectionId"], s["period"]): s for s in r.json()["substitutions"]}
    assert subs[(MON, w.b10, 2)]["substituteId"] == w.uid["chitra"]
    assert subs[(MON, w.b10, 2)]["status"] == "accepted"
    assert subs[(MON, w.a10, 1)]["substituteId"] != w.uid["chitra"]

    off = w.c.put(f"{BASE}/leave-requests/{leave['id']}/replacement", json={"teacherId": None}, headers=w.p)
    assert off.status_code == 200, off.text
    assert off.json()["leave"]["replacementId"] is None
    again = {(s["date"], s["sectionId"], s["period"]): s for s in off.json()["substitutions"]}
    assert again[(MON, w.b10, 2)]["status"] == "proposed", "the engine proposes someone again"


def test_a_replacement_needs_an_approved_leave_and_someone_else(w):
    leave = _apply(w, "ana", startDate=MON, endDate="2026-06-30").json()
    pending = w.c.put(f"{BASE}/leave-requests/{leave['id']}/replacement", json={"teacherId": w.uid["dev"]},
                      headers=w.p)
    assert pending.status_code == 409
    _approve(w, leave["id"])
    assert w.c.put(f"{BASE}/leave-requests/{leave['id']}/replacement", json={"teacherId": w.uid["ana"]},
                   headers=w.p).status_code == 422
    student = w.c.get("/api/v1/auth/me", headers=w.stu).json()["id"]
    assert w.c.put(f"{BASE}/leave-requests/{leave['id']}/replacement", json={"teacherId": student},
                   headers=w.p).status_code == 422


# ---------------------------------------------------------------- a teacher changes mid-year


def test_a_mid_year_teacher_change_moves_the_timetable_cover_and_plans(w):
    book = _plan(w, w.a10, w.b10)
    w.store.assign_teacher(school_id="school_1", teacher_id=w.uid["ana"], book_id=book)
    # Ana is away next Monday; her 10-B period has cover opened.
    leave = _apply(w, "ana", startDate="2026-06-08", endDate="2026-06-08").json()
    opened = {(s["sectionId"], s["period"]) for s in _approve(w, leave["id"])["substitutions"]}
    assert opened == {(w.a10, 1), (w.b10, 2)}

    # 10-B's Science passes from Ana to Chitra.
    r = w.c.put(f"{BASE}/sections/{w.b10}/allocations/{w.sci10}",
                json={"teacherId": w.uid["chitra"], "periodsPerWeek": 6}, headers=w.p)
    assert r.status_code == 200, r.text

    # The timetable follows (it already did).
    [p2] = [e for e in w.store.timetable_for_section(w.b10) if e.period == 2]
    assert p2.teacher_id == w.uid["chitra"]
    chitra_day = w.c.get(f"{BASE}/my-day", params={"date": "2026-06-15"}, headers=w.t["chitra"]).json()
    assert (w.b10, 2, "regular") in {(x["sectionId"], x["period"], x["kind"]) for x in chitra_day}
    assert w.b10 not in {x["sectionId"] for x in w.c.get(f"{BASE}/my-day", params={"date": "2026-06-15"},
                                                         headers=w.t["ana"]).json()}

    # The cover opened for Ana's absence from 10-B is cancelled: Chitra
    # teaches it. Ana's 10-A period still needs cover.
    subs = w.c.get(f"{BASE}/substitutions", params={"from": "2026-06-08", "to": "2026-06-08"}, headers=w.p).json()
    status = {(s["sectionId"], s["period"]): s["status"] for s in subs}
    assert status[(w.b10, 2)] == "cancelled" and status[(w.a10, 1)] != "cancelled"
    day = w.c.get(f"{BASE}/day", params={"date": "2026-06-08", "sectionId": w.b10}, headers=w.p).json()
    assert next(x for x in day if x["period"] == 2)["teacherId"] == w.uid["chitra"]

    # The plan and its lessons follow the new teacher.
    assert {l["sectionId"] for l in _schedule(w, w.t["chitra"])} == {w.b10}
    assert {l["sectionId"] for l in _schedule(w, w.t["ana"])} == {w.a10}
    lesson = next(l for l in w.store.scheduled_lessons_for_book(w.year, book, w.b10) if l.date == "2026-06-15")
    assert w.c.patch(f"{BASE}/scheduled-lessons/{lesson.id}", json={"status": "completed"},
                     headers=w.t["ana"]).status_code == 403
    assert w.c.patch(f"{BASE}/scheduled-lessons/{lesson.id}", json={"status": "completed"},
                     headers=w.t["chitra"]).status_code == 200
    assert w.c.get(f"{BASE}/scheduled-lessons/{lesson.id}/history", headers=w.t["chitra"]).status_code == 200
    # The book is Chitra's too (the school-wide plan's teacher); Ana keeps it
    # while she still teaches the subject to 10-A.
    assert book in {a.book_id for a in w.store.assignments_for_teacher(w.uid["chitra"])}
    assert book in {a.book_id for a in w.store.assignments_for_teacher(w.uid["ana"])}


def test_a_teacher_who_leaves_hands_over_every_class_of_the_subject(w):
    book = _plan(w, w.a10)
    w.store.assign_teacher(school_id="school_1", teacher_id=w.uid["ana"], book_id=book)
    for section in (w.a10, w.b10):
        r = w.c.put(f"{BASE}/sections/{section}/allocations/{w.sci10}",
                    json={"teacherId": w.uid["chitra"], "periodsPerWeek": 6}, headers=w.p)
        assert r.status_code == 200, r.text
    assert book not in {a.book_id for a in w.store.assignments_for_teacher(w.uid["ana"])}
    assert _schedule(w, w.t["ana"]) == []


# ---------------------------------------------------------------- an event day


def test_an_event_day_marks_the_day_and_still_teaches(w):
    book = _plan(w, w.a10)
    r = w.c.post(f"{BASE}/academic-years/{w.year}/holidays",
                 json={"date": "2026-06-08", "label": "Annual Day rehearsal", "kind": "event"}, headers=w.p)
    assert r.status_code == 200, r.text
    assert "2026-06-08" in w.c.get(f"{BASE}/academic-years/{w.year}/working-days", headers=w.p).json()["dates"]
    assert {x["kind"] for x in w.c.get(f"{BASE}/day", params={"date": "2026-06-08", "sectionId": w.a10},
                                       headers=w.p).json()} == {"regular"}
    assert _dates(w, book, w.a10) == MONDAYS
    # An event that does cancel some classes' teaching is a closure of those
    # sections: their periods are lost and their plans move.
    r = w.c.post(f"{BASE}/academic-years/{w.year}/closures",
                 json={"date": "2026-06-08", "reason": "Annual Day", "sectionIds": [w.a10]}, headers=w.p)
    assert r.status_code == 200 and r.json()["lostPeriods"] == 2, r.text
    assert _dates(w, book, w.a10) == [MON] + MONDAYS[2:] + ["2026-07-13"]
