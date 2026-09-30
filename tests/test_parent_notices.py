"""N-8-7: parents heard only of marked homework. A linked parent now hears
the school notices about their child -- a holiday, a published or changed
exam, a timetable change -- under their own notification settings, and only
through an active link at the child's school. Uses the cover fixture:
classes 10 (A, B) and 9 (A); the student Asha is in 10-B; 2026-06-01 is a
Monday and the school's today."""
from __future__ import annotations

from test_cover_routes import BASE, w  # noqa: F401 - `w` is a fixture
from test_exams import _exam, _sheet

PASSWORD = "correct horse battery"


def _h(body):
    return {"Authorization": f"Bearer {body['token']}"}


def _parent(w):
    sid = w.c.get("/api/v1/auth/me", headers=w.stu).json()["id"]
    r = w.c.post(f"/api/v1/students/{sid}/guardian-invites", json={"relation": "mother"}, headers=w.p)
    assert r.status_code == 200, r.text
    reg = w.c.post("/api/v1/auth/register", json={"inviteCode": r.json()["code"], "name": "Meena",
                                                  "email": "mum@example.com", "password": PASSWORD})
    assert reg.status_code == 200, reg.text
    return sid, reg.json()


def _items(w, headers, kind):
    return [i for i in w.c.get("/api/v1/notifications", headers=headers).json()["items"] if i["kind"] == kind]


def test_a_parent_hears_the_exam_and_its_changes_and_an_unlinked_one_does_not(w):
    sid, mum = _parent(w)
    other_school = w.c.get("/api/v1/auth/me", headers=w.p2).json()["id"]
    from academicos.operations.routes import store
    # a link recorded under another school must not carry this school's notices
    store().link_guardian(parent_id=other_school, student_id=sid, school_id="school_2", relation="guardian",
                          created_by="test")
    eid = _exam(w)
    sheet = [(10, "Science", "2026-06-01"), (9, "Maths", "2026-06-02")]
    _sheet(w, eid, sheet)
    w.c.post(f"/api/v1/exams/{eid}/publish", headers=w.p)
    [item] = _items(w, _h(mum), "exam_scheduled")
    assert item["title"] == "Datesheet: Unit test 1" and item["link"] == "/my-children"
    assert "The datesheet is in the app." in item["body"]
    w.c.post(f"/api/v1/exams/{eid}/publish", headers=w.p)
    assert len(_items(w, _h(mum), "exam_scheduled")) == 1, "once"

    _sheet(w, eid, [(10, "Science", "2026-06-03"), (9, "Maths", "2026-06-02")])
    [changed] = _items(w, _h(mum), "exam_changed")
    assert changed["body"].startswith("Science moves to 2026-06-03")
    assert _items(w, w.p2, "exam_scheduled") == [] and _items(w, w.p2, "exam_changed") == []

    # a link the principal ends carries nothing more
    assert w.c.delete(f"/api/v1/guardianships/{mum['user']['id']}/{sid}", headers=w.p).status_code == 200
    _sheet(w, eid, [(10, "Science", "2026-06-04"), (9, "Maths", "2026-06-02")])
    assert len(_items(w, _h(mum), "exam_changed")) == 1
    assert len(_items(w, w.stu, "exam_changed")) == 2, "the student still hears"


def test_a_parent_hears_a_holiday_and_a_timetable_change_in_their_own_language(w):
    _, mum = _parent(w)
    r = w.c.put("/api/v1/notification-preferences", json={"language": "hi"}, headers=_h(mum))
    assert r.status_code == 200, r.text
    r = w.c.post(f"{BASE}/academic-years/{w.year}/holidays", json={"date": "2026-06-03", "label": "Rain closure"},
                 headers=w.p)
    assert r.status_code == 200, r.text
    [holiday] = _items(w, _h(mum), "holiday_declared")
    assert holiday["title"] == "अवकाश: Rain closure" and holiday["link"] == "/my-children"

    subs = {s.name: s.id for g in w.store.grades_for_year(w.year) if g.number == 10
            for s in w.store.subjects_for_grade(g.id)}
    # 10-B's Maths moves from period 1 to period 3 (Bala is free then)
    r = w.c.put(f"{BASE}/sections/{w.b10}/timetable", headers=w.p, json={"entries": [
        {"dayOfWeek": 0, "period": 3, "subjectId": subs["Maths"]},
        {"dayOfWeek": 0, "period": 2, "subjectId": subs["Science"]}]})
    assert r.status_code == 200, r.text
    [week] = _items(w, _h(mum), "timetable_published")
    assert week["title"] == "समय-सारिणी बदली" and week["link"] == "/my-children"
    assert len(_items(w, w.stu, "timetable_published")) == 1
