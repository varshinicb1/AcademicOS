"""ATT-1 daily student attendance: the section's teachers take the register,
a student without parental consent is left out and named, a parent hears the
same day that their child was marked absent (once), and the student, the
parent and the section's teachers read the record -- nobody else. Uses the
cover fixture: Asha is in 10-B, taught by Ana (Science) and Bala (Maths);
Chitra and Dev teach 9-A only; 2026-06-01 is the school's today."""
from __future__ import annotations

from _auth_helpers import grant_consent, register_invited
from test_cover_routes import w  # noqa: F401 - `w` is a fixture
from test_parent_notices import _h, _items, _parent

TODAY = "2026-06-01"


def _url(w):
    return f"/api/v1/sections/{w.b10}/attendance"


def _asha(w):
    return w.c.get("/api/v1/auth/me", headers=w.stu).json()["id"]


def test_a_teacher_of_the_section_takes_the_register_and_the_parent_hears_once(w):
    sid, mum = _parent(w)
    grant_consent("school_1", sid)
    empty = w.c.get(_url(w), headers=w.t["ana"])
    assert empty.status_code == 200, empty.text
    assert empty.json()["taken"] is False and [r["status"] for r in empty.json()["rows"]] == [None]

    r = w.c.put(_url(w), json={"entries": [{"studentId": sid, "status": "absent"}]}, headers=w.t["ana"])
    assert r.status_code == 200, r.text
    assert r.json()["taken"] is True and r.json()["counts"]["absent"] == 1 and r.json()["withoutConsent"] == []
    [notice] = _items(w, _h(mum), "child_absent")
    assert notice["title"] == "Absent today: Asha" and "10-B" in notice["body"] and notice["link"] == "/my-children"
    assert _items(w, w.stu, "child_absent") == [], "the student is not told"

    # saving again, or by another teacher of the section, is one row and one notice
    assert w.c.put(_url(w), json={"entries": [{"studentId": sid, "status": "absent"}]},
                   headers=w.t["bala"]).status_code == 200
    assert len(_items(w, _h(mum), "child_absent")) == 1
    # a correction to present is kept, and a day earlier is fine; tomorrow is not
    r = w.c.put(_url(w), json={"entries": [{"studentId": sid, "status": "late", "note": "bus"}]}, headers=w.t["ana"])
    assert r.json()["rows"][0]["status"] == "late" and r.json()["rows"][0]["note"] == "bus"
    assert w.c.put(_url(w) + "?date=2026-05-29", json={"entries": [{"studentId": sid, "status": "absent"}]},
                   headers=w.t["ana"]).status_code == 200
    assert len(_items(w, _h(mum), "child_absent")) == 1, "a past day's register sends no notice"
    future = w.c.put(_url(w) + "?date=2026-06-02", json={"entries": [{"studentId": sid, "status": "present"}]},
                     headers=w.t["ana"])
    assert future.status_code == 422 and "future" in future.json()["detail"]


def test_only_the_sections_teachers_and_the_principal_take_or_read_it(w):
    sid = _asha(w)
    grant_consent("school_1", sid)
    body = {"entries": [{"studentId": sid, "status": "present"}]}
    assert w.c.put(_url(w), json=body, headers=w.t["chitra"]).status_code == 403
    assert w.c.get(_url(w), headers=w.t["dev"]).status_code == 403
    assert w.c.put(_url(w), json=body, headers=w.stu).status_code == 403
    assert w.c.get(_url(w), headers=w.p2).status_code == 403, "another school's principal"
    assert w.c.put(_url(w), json=body, headers=w.p).status_code == 200
    # a student of another section cannot be slipped in
    other = register_invited(w.c, "school_1", "s2@example.com", name="Bina", role="student")
    w.store.enroll_student(school_id="school_1", student_id=other["user"]["id"], section_id=w.a10)
    r = w.c.put(_url(w), json={"entries": [{"studentId": other["user"]["id"], "status": "absent"}]}, headers=w.p)
    assert r.status_code == 422 and "not in 10-B" in r.json()["detail"]
    # unknown fields and statuses are refused
    assert w.c.put(_url(w), json={"entries": [{"studentId": sid, "status": "sick"}]}, headers=w.p).status_code == 422
    assert w.c.put(_url(w), json={"entries": [], "extra": 1}, headers=w.p).status_code == 422


def test_a_student_without_consent_is_left_out_and_named(w):
    sid = _asha(w)             # no consent recorded
    r = w.c.put(_url(w), json={"entries": [{"studentId": sid, "status": "absent"}]}, headers=w.t["ana"])
    assert r.status_code == 200, r.text
    assert r.json()["withoutConsent"] == ["Asha"] and r.json()["taken"] is False


def test_the_student_the_parent_and_the_teacher_read_the_record_and_nobody_else(w):
    sid, mum = _parent(w)
    grant_consent("school_1", sid)
    for day, status in (("2026-05-26", "present"), ("2026-05-27", "late"), ("2026-05-28", "absent"),
                        ("2026-05-29", "excused"), (TODAY, "present")):
        assert w.c.put(_url(w) + f"?date={day}", json={"entries": [{"studentId": sid, "status": status}]},
                       headers=w.t["ana"]).status_code == 200
    own = w.c.get("/api/v1/my-attendance-record", headers=w.stu)
    assert own.status_code == 200, own.text
    rec = own.json()
    assert rec["daysTaken"] == 5 and rec["counts"] == {"present": 2, "late": 1, "absent": 1, "excused": 1}
    assert rec["percent"] == 75.0, "3 of the 4 counted days; the excused day is left out"
    assert [d["date"] for d in rec["recent"]] == ["2026-05-29", "2026-05-28", "2026-05-27"]

    assert w.c.get(f"/api/v1/children/{sid}/attendance", headers=_h(mum)).json() == rec
    assert w.c.get(f"/api/v1/students/{sid}/attendance", headers=w.t["bala"]).json() == rec
    assert w.c.get(f"/api/v1/students/{sid}/attendance", headers=w.t["chitra"]).status_code == 403
    assert w.c.get(f"/api/v1/students/{sid}/attendance", headers=w.p2).status_code == 403
    assert w.c.get(f"/api/v1/children/{sid}/attendance", headers=w.stu).status_code == 403
    assert w.c.get("/api/v1/my-attendance-record", headers=_h(mum)).status_code == 403


def test_erasing_a_student_removes_their_register_rows(w):
    from academicos.operations.routes import store
    sid = _asha(w)
    grant_consent("school_1", sid)
    w.c.put(_url(w), json={"entries": [{"studentId": sid, "status": "present"}]}, headers=w.t["ana"])
    counts = store().forget_student(sid, school_id="school_1", email="s1@example.com", name="Asha")
    assert counts["student_attendance"] == 1
    assert store().attendance_of_student("school_1", sid, start="2026-01-01", end="2026-12-31") == []
