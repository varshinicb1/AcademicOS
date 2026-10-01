"""The teacher's and student's day as the apps show it (v3 audit, areas 4
and 5). These defects were found:

  * N-4-2: My day and Today had no period time, no room and nothing saying a
    period differs from the usual week.
  * N-4-3 / N-3-13: the handover note never reached the substitute.
  * TA-7: no notice that a period was about to start.
  * N-4-8: a teacher's calendar feed left out invigilation duties.

2026-06-01 is a Monday (test_cover_routes' world: bell 08:00, 09:00, ...).
"""
from __future__ import annotations

from datetime import datetime, timezone

from test_cover_routes import BASE, MON, _apply, w  # noqa: F401 - `w` is a fixture


def test_the_day_says_when_each_period_starts_and_what_changed(w):
    day = w.c.get(f"{BASE}/my-day", params={"date": MON}, headers=w.t["ana"]).json()
    assert [(r["period"], r["startTime"], r["endTime"]) for r in day] == [(1, "08:00", "08:45"), (2, "09:00", "09:45")]
    assert all(r["changed"] is False for r in day), "an ordinary day changes nothing"
    student = w.c.get(f"{BASE}/my-day", params={"date": MON}, headers=w.stu).json()
    assert student[0]["startTime"] == "08:00" and student[0]["teacherName"]

    # A room booked for the period is named.
    room = w.store.create_room(school_id="school_1", name="Physics Lab", kind="lab")
    week = [{"day_of_week": e.day_of_week, "period": e.period, "subject_id": e.subject_id,
             **({"room_id": room.id} if e.subject_id == w.sci10 else {})}
            for e in w.store._entries_where("section_id=?", (w.b10,))]
    w.store.replace_section_timetable(w.b10, week)
    day = w.c.get(f"{BASE}/my-day", params={"date": MON}, headers=w.stu).json()
    assert [r["roomName"] for r in day] == [None, "Physics Lab"]

    # Ana on leave: the class's period says it changed, and the cover
    # teacher reads her handover note.
    leave = _apply(w, "ana", handoverNote="Worksheet 3 is on my desk").json()
    subs = w.c.post(f"{BASE}/leave-requests/{leave['id']}/decision", json={"approve": True},
                    headers=w.p).json()["substitutions"]
    duty = next(s for s in subs if s["sectionId"] == w.b10)
    assert duty["handoverNote"] == "Worksheet 3 is on my desk"
    cover = w.c.get(f"{BASE}/substitutions", params={"from": MON, "to": MON},
                    headers=w.t["chitra"]).json()
    assert cover[0]["handoverNote"] == "Worksheet 3 is on my desk"
    w.c.post(f"{BASE}/substitutions/{duty['id']}/respond", json={"accept": True}, headers=w.t["chitra"])
    mine = w.c.get(f"{BASE}/my-day", params={"date": MON}, headers=w.t["chitra"]).json()
    covering = next(r for r in mine if r["kind"] == "substitute")
    assert covering["note"] == "Worksheet 3 is on my desk" and covering["changed"] is True
    student = w.c.get(f"{BASE}/my-day", params={"date": MON}, headers=w.stu).json()
    assert [r["changed"] for r in student] == [False, True]
    assert "Worksheet" not in (student[1]["note"] or ""), "the note is for the cover teacher, not the class"


def test_a_teacher_is_told_a_period_is_about_to_start(w):
    from academicos.operations import automations, routes as ops_routes
    from academicos.curriculum import routes as cr
    sent: list[dict] = []

    def notify(**kw):
        sent.append(kw)
        return [kw]

    # 07:52 IST on Monday: period 1 starts at 08:00, inside the ten minutes.
    at = datetime(2026, 6, 1, 2, 22, tzinfo=timezone.utc)
    n = automations.period_starting(ops_routes.store(), cr._require(), cr._require_users(), notify, at)
    told = {(s["user_ids"][0], s["params"]["period"]) for s in sent}
    assert n == len(sent) and (w.uid["ana"], 1) in told and (w.uid["bala"], 1) in told
    assert all(s["kind"] == "period_starting" and s["params"]["start"] == "08:00" for s in sent)
    assert not any(s["params"]["period"] == 2 for s in sent), "period 2 is an hour away"


def test_a_teachers_calendar_feed_has_their_invigilation(w):
    from academicos.curriculum import routes as cr
    exam = w.c.post("/api/v1/exams", json={"name": "Unit test 1", "startDate": "2026-06-08",
                                            "endDate": "2026-06-10", "grades": [10],
                                            "academicYearId": w.year}, headers=w.p)
    assert exam.status_code == 200, exam.text
    eid = exam.json()["id"]
    sheet = w.c.put(f"/api/v1/exams/{eid}/datesheet", json={"papers": [
        {"grade": 10, "subjectId": w.sci10, "date": "2026-06-08", "startTime": "09:30", "endTime": "11:00"}]},
        headers=w.p)
    assert sheet.status_code == 200, sheet.text
    paper_id = sheet.json()["papers"][0]["id"]
    roster = w.c.put(f"/api/v1/exams/{eid}/invigilation", json={"duties": [
        {"examPaperId": paper_id, "sectionId": w.a10, "teacherId": w.uid["bala"]}]}, headers=w.p)
    assert roster.status_code == 200, roster.text
    assert w.c.post(f"/api/v1/exams/{eid}/publish", headers=w.p).status_code == 200
    url = w.c.get("/api/v1/calendar-feed", headers=w.t["bala"]).json()["url"]
    ics = w.c.get(url[url.index("/api/v1"):]).text
    assert "Invigilation:" in ics and "20260608" in ics
    assert cr._require() is not None
