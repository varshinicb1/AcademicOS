"""The calendar and the teaching load inside the apps (TA-2; v3 audit area 4).

Before: holidays, exams and duties reached a teacher only through the ICS
link (calendar-feed), and the teacher-load route was the principal's alone,
so no page showed a teacher their own load. Both now come from the same
events the ICS feed is built from.

2026-06-01 is a Monday and today in test_cover_routes' world.
"""
from __future__ import annotations

from test_cover_routes import BASE, MON, _apply, w  # noqa: F401 - `w` is a fixture


def _exam_with_bala_invigilating(w):
    exam = w.c.post("/api/v1/exams", json={"name": "Unit test 1", "startDate": "2026-06-08",
                                            "endDate": "2026-06-10", "grades": [10],
                                            "academicYearId": w.year}, headers=w.p)
    assert exam.status_code == 200, exam.text
    eid = exam.json()["id"]
    sheet = w.c.put(f"/api/v1/exams/{eid}/datesheet", json={"papers": [
        {"grade": 10, "subjectId": w.sci10, "date": "2026-06-08", "startTime": "09:30", "endTime": "11:00"}]},
        headers=w.p)
    assert sheet.status_code == 200, sheet.text
    roster = w.c.put(f"/api/v1/exams/{eid}/invigilation", json={"duties": [
        {"examPaperId": sheet.json()["papers"][0]["id"], "sectionId": w.a10, "teacherId": w.uid["bala"]}]},
        headers=w.p)
    assert roster.status_code == 200, roster.text
    assert w.c.post(f"/api/v1/exams/{eid}/publish", headers=w.p).status_code == 200


def test_the_apps_calendar_lists_what_is_coming(w):
    closed = w.c.post(f"{BASE}/academic-years/{w.year}/closures", json={"date": "2026-06-05", "reason": "Sports day"},
                      headers=w.p)
    assert closed.status_code == 200, closed.text
    _exam_with_bala_invigilating(w)

    bala = w.c.get("/api/v1/my-calendar", headers=w.t["bala"])
    assert bala.status_code == 200, bala.text
    seen = [(i["kind"], i["date"]) for i in bala.json()]
    assert ("holiday", "2026-06-05") in seen and ("invigilation", "2026-06-08") in seen
    assert seen == sorted(seen, key=lambda k: k[1]), "in date order"
    assert not any(k == "period" for k, _ in seen), "the weekly periods are the timetable's, not the list's"
    duty = next(i for i in bala.json() if i["kind"] == "invigilation")
    assert (duty["startTime"], duty["endTime"]) == ("09:30", "11:00") and "10-A" in duty["title"]

    student = [(i["kind"], i["date"]) for i in w.c.get("/api/v1/my-calendar", headers=w.stu).json()]
    assert ("exam", "2026-06-08") in student and ("holiday", "2026-06-05") in student
    assert not any(k == "invigilation" for k, _ in student), "a student sees their papers, not staff duties"

    soon = w.c.get("/api/v1/my-calendar", params={"days": 3}, headers=w.t["bala"]).json()
    assert all(i["date"] <= "2026-06-04" for i in soon), "days bounds the window"
    assert w.c.get("/api/v1/my-calendar", params={"days": 61}, headers=w.t["bala"]).status_code == 422


def test_a_cover_duty_is_on_the_substitutes_calendar(w):
    leave = _apply(w, "ana").json()
    subs = w.c.post(f"{BASE}/leave-requests/{leave['id']}/decision", json={"approve": True},
                    headers=w.p).json()["substitutions"]
    who = {s["substituteId"] for s in subs if s.get("substituteId")}
    assert who, "the leave proposed cover"
    name = next(n for n, u in w.uid.items() if u in who)
    covers = [i for i in w.c.get("/api/v1/my-calendar", headers=w.t[name]).json() if i["kind"] == "cover"]
    assert covers and covers[0]["date"] == MON and covers[0]["title"].startswith("Cover:")


def test_a_teacher_sees_their_own_load(w):
    ana = w.c.get("/api/v1/my-load", headers=w.t["ana"])
    assert ana.status_code == 200, ana.text
    load = ana.json()
    assert load["periodsPerWeek"] == 2 and load["maxInOneDay"] == 2 and load["daysTaught"] == {"0": 2}
    assert sorted((c["sectionName"], c["subjectName"], c["periodsPerWeek"]) for c in load["classes"]) == [
        ("10-A", "Science", 1), ("10-B", "Science", 1)]
    assert load["coversThisWeek"] == 0 and load["invigilationsAhead"] == 0

    _exam_with_bala_invigilating(w)
    assert w.c.get("/api/v1/my-load", headers=w.t["bala"]).json()["invigilationsAhead"] == 1

    leave = _apply(w, "ana").json()
    subs = w.c.post(f"{BASE}/leave-requests/{leave['id']}/decision", json={"approve": True},
                    headers=w.p).json()["substitutions"]
    name = next(n for n, u in w.uid.items() if u == subs[0]["substituteId"])
    assert w.c.get("/api/v1/my-load", headers=w.t[name]).json()["coversThisWeek"] >= 1

    assert w.c.get("/api/v1/my-load", headers=w.stu).status_code == 403, "a load is for staff"
    assert w.c.get("/api/v1/my-load", headers=w.p).status_code == 200


def test_the_feeds_weekly_periods_skip_the_days_the_school_is_closed(w):
    """QA S-13: the calendar a teacher added to Google Calendar showed their
    classes on holidays: weekly periods recurred with no exception dates."""
    closed = w.c.post(f"{BASE}/academic-years/{w.year}/closures", json={"date": "2026-06-15", "reason": "Rain"},
                      headers=w.p)
    assert closed.status_code == 200, closed.text
    url = w.c.get("/api/v1/calendar-feed", headers=w.t["ana"]).json()["url"]
    ics = w.c.get(url[url.index("/api/v1"):]).text.replace("\r\n ", "")
    periods = [ev for ev in ics.split("BEGIN:VEVENT")[1:] if "RRULE:FREQ=WEEKLY" in ev]
    assert periods, "Ana's Monday periods are in the feed"
    for ev in periods:
        exdates = next(line for line in ev.splitlines() if line.startswith("EXDATE"))
        assert "20260615T" in exdates
        assert "20260608T" not in exdates and "20260622T" not in exdates


def test_a_parent_sees_their_childs_calendar_and_no_one_elses(w):
    """SA-6 (2026-10-04): /my-calendar refused a parent and the family day page only said "a holiday,
    a weekly off, or no timetable", so a parent could not see a holiday or an exam coming."""
    closed = w.c.post(f"{BASE}/academic-years/{w.year}/closures", json={"date": "2026-06-05", "reason": "Sports day"},
                      headers=w.p)
    assert closed.status_code == 200, closed.text
    _exam_with_bala_invigilating(w)
    child = w.c.get("/api/v1/auth/me", headers=w.stu).json()["id"]
    invite = w.c.post(f"/api/v1/students/{child}/guardian-invites", json={"relation": "mother"}, headers=w.p)
    assert invite.status_code == 200, invite.text
    reg = w.c.post("/api/v1/auth/register", json={"inviteCode": invite.json()["code"], "name": "Meena",
                                                  "email": "meena@example.com", "password": "correct horse battery"})
    assert reg.status_code == 200, reg.text
    mum = {"Authorization": f"Bearer {reg.json()['token']}"}

    r = w.c.get(f"/api/v1/children/{child}/calendar", headers=mum)
    assert r.status_code == 200, r.text
    seen = [(i["kind"], i["date"]) for i in r.json()]
    assert ("holiday", "2026-06-05") in seen and ("exam", "2026-06-08") in seen
    assert seen == [(i["kind"], i["date"]) for i in w.c.get("/api/v1/my-calendar", headers=w.stu).json()], \
        "the parent sees what the child sees"
    assert w.c.get("/api/v1/children/someone-else/calendar", headers=mum).status_code == 404
    assert w.c.get(f"/api/v1/children/{child}/calendar", headers=w.t["bala"]).status_code == 403
    assert w.c.get("/api/v1/my-calendar", headers=mum).status_code == 403
