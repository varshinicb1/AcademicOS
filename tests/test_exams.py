"""Exam planning (EX-7): a datesheet that refuses clashes, a roster that
never puts a teacher on their own subject's paper, on leave, or in two
rooms at once, and publishing that tells students and invigilators. Uses
the cover fixture: classes 10 (A, B) and 9 (A); Ana teaches Science 10,
Bala Maths 10, Chitra Science 9, Dev Maths 9. 2026-06-01 is a Monday."""
from __future__ import annotations

from test_cover_routes import BASE, _apply, w  # noqa: F401 - `w` is a fixture


def _exam(w):
    r = w.c.post("/api/v1/exams", json={"name": "Unit test 1", "startDate": "2026-06-01", "endDate": "2026-06-05",
                                        "grades": [9, 10]}, headers=w.p)
    assert r.status_code == 200, r.text
    return r.json()["id"]


def _subjects(w):
    subs = {}
    for g in w.store.grades_for_year(w.year):
        for s in w.store.subjects_for_grade(g.id):
            subs[(g.number, s.name)] = s.id
    return subs


def _sheet(w, eid, rows):
    subs = _subjects(w)
    return w.c.put(f"/api/v1/exams/{eid}/datesheet", headers=w.p, json={"papers": [
        {"grade": g, "subjectId": subs[(g, name)], "date": d} for g, name, d in rows]})


def test_the_datesheet_refuses_clashes(w):
    eid = _exam(w)
    bad = _sheet(w, eid, [(10, "Science", "2026-06-01"), (10, "Maths", "2026-06-01"), (9, "Science", "2026-06-08")])
    assert bad.status_code == 409
    assert "class 10 has two papers on 2026-06-01" in bad.json()["detail"] and "outside the exam" in bad.json()["detail"]
    ok = _sheet(w, eid, [(10, "Science", "2026-06-01"), (10, "Maths", "2026-06-02"), (9, "Science", "2026-06-01"),
                         (9, "Maths", "2026-06-03")])
    assert ok.status_code == 200 and len(ok.json()["papers"]) == 4


def test_the_roster_respects_subjects_leave_and_overlaps(w):
    eid = _exam(w)
    _sheet(w, eid, [(10, "Science", "2026-06-01"), (10, "Maths", "2026-06-02"), (9, "Science", "2026-06-01"),
                    (9, "Maths", "2026-06-02")])
    leave = _apply(w, "dev", startDate="2026-06-02", endDate="2026-06-02").json()
    w.c.post(f"{BASE}/leave-requests/{leave['id']}/decision", json={"approve": True}, headers=w.p)
    out = w.c.post(f"/api/v1/exams/{eid}/invigilation/auto", headers=w.p).json()
    duties = out["duties"]
    assert len(duties) == 6 and all(d["teacherId"] for d in duties) and out["unfilled"] == []
    teaches = {(w.uid["ana"], "Science", 10), (w.uid["bala"], "Maths", 10), (w.uid["chitra"], "Science", 9),
               (w.uid["dev"], "Maths", 9)}
    assert not any((d["teacherId"], d["subjectName"], d["grade"]) in teaches for d in duties)
    assert not any(d["teacherId"] == w.uid["dev"] and d["date"] == "2026-06-02" for d in duties)
    slots = [(d["teacherId"], d["date"], d["startTime"]) for d in duties]
    assert len(slots) == len(set(slots)), "nobody is in two rooms at once"
    # a manual change is kept by the next auto-fill
    first = duties[0]
    w.c.put(f"/api/v1/exams/{eid}/invigilation", headers=w.p, json={"duties": [
        {"examPaperId": first["examPaperId"], "sectionId": first["sectionId"], "teacherId": w.uid["dev"]}]})
    again = w.c.post(f"/api/v1/exams/{eid}/invigilation/auto", headers=w.p).json()["duties"]
    kept = next(d for d in again if d["examPaperId"] == first["examPaperId"] and d["sectionId"] == first["sectionId"])
    assert kept["teacherId"] == w.uid["dev"]


def test_publishing_tells_students_and_invigilators(w):
    eid = _exam(w)
    _sheet(w, eid, [(10, "Science", "2026-06-01"), (9, "Maths", "2026-06-02")])
    assert w.c.get("/api/v1/my-exams", headers=w.stu).json()["exams"] == [], "not before publishing"
    w.c.post(f"/api/v1/exams/{eid}/invigilation/auto", headers=w.p)
    assert w.c.post(f"/api/v1/exams/{eid}/publish", headers=w.p).json()["status"] == "published"
    [mine] = w.c.get("/api/v1/my-exams", headers=w.stu).json()["exams"]
    assert [p["subjectName"] for p in mine["papers"]] == ["Science"] and mine["duties"] == []
    inbox = w.c.get("/api/v1/notifications", headers=w.stu).json()["items"]
    assert any(i["kind"] == "exam_scheduled" and "Unit test 1" in i["title"] for i in inbox)
    told = [n for n in ("ana", "bala", "chitra", "dev")
            if any(i["kind"] == "invigilation_duty" for i in w.c.get("/api/v1/notifications",
                                                                     headers=w.t[n]).json()["items"])]
    assert len(told) >= 2
    for n in told:
        exams = w.c.get("/api/v1/my-exams", headers=w.t[n]).json()["exams"]
        assert exams and all(d["teacherId"] == w.uid[n] for d in exams[0]["duties"])


def test_who_may(w):
    assert w.c.post("/api/v1/exams", json={"name": "x", "startDate": "2026-06-01", "endDate": "2026-06-02",
                                           "grades": [10]}, headers=w.t["ana"]).status_code == 403
    eid = _exam(w)
    assert w.c.get(f"/api/v1/exams/{eid}", headers=w.p2).status_code == 403
    assert w.c.post("/api/v1/exams", json={"name": "x", "startDate": "2026-06-01", "endDate": "2026-06-02",
                                           "grades": [4]}, headers=w.p).status_code == 422
    assert w.c.post(f"/api/v1/exams/{eid}/publish", headers=w.p).status_code == 409      # no datesheet yet
