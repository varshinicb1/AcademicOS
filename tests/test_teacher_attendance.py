"""Teacher attendance (SCH-9): marking a teacher absent opens same-day cover
for every period they miss; marking them present again withdraws it; a
teacher checks in but never over an absence the principal marked."""
from __future__ import annotations

from test_cover_routes import BASE, MON, _apply, w  # noqa: F401 - `w` is a fixture

URL = f"{BASE}/teacher-attendance"


def _mark(w, **marks):
    body = {"marks": [{"teacherId": w.uid[n], "status": s} for n, s in marks.items()]}
    r = w.c.put(URL, params={"date": MON}, json=body, headers=w.p)
    assert r.status_code == 200, r.text
    return r.json()


def _status(out, w, name):
    return next(r["status"] for r in out["rows"] if r["teacherId"] == w.uid[name])


def test_an_absence_opens_cover_and_a_correction_withdraws_it(w):
    before = w.c.get(URL, params={"date": MON}, headers=w.p).json()
    assert {r["status"] for r in before["rows"]} == {"unmarked"}
    out = _mark(w, ana="absent", bala="present")
    assert _status(out, w, "ana") == "absent" and _status(out, w, "bala") == "present"
    assert {(s["sectionId"], s["period"]) for s in out["substitutions"]} == {(w.a10, 1), (w.b10, 2)}
    assert all(s["substituteId"] for s in out["substitutions"]), "each has a proposed substitute"
    subs = w.store.substitutions_between(w.year, MON, MON)
    assert len([s for s in subs if s.status != "cancelled"]) == 2

    out = _mark(w, ana="present")
    assert out["substitutions"] == []
    assert all(s.status == "cancelled" for s in w.store.substitutions_between(w.year, MON, MON))


def test_half_days_and_existing_leave(w):
    out = _mark(w, ana="second_half_absent")
    assert out["substitutions"] == [], "Ana teaches periods 1 and 2, in the first half"
    out = _mark(w, ana="first_half_absent")
    assert len(out["substitutions"]) == 2

    leave = _apply(w, "bala").json()
    w.c.post(f"{BASE}/leave-requests/{leave['id']}/decision", json={"approve": True}, headers=w.p)
    listed = w.c.get(URL, params={"date": MON}, headers=w.p).json()
    assert _status(listed, w, "bala") == "on_leave"
    assert _mark(w, bala="absent")["substitutions"] == [], "already covered by the approved leave"


def test_a_pending_leave_is_approved_by_marking_absent(w):
    leave = _apply(w, "ana").json()
    out = _mark(w, ana="absent")
    assert len(out["substitutions"]) == 2
    assert w.store.get_leave(leave["id"]).status == "approved"


def test_check_in_and_who_may(w):
    r = w.c.post(f"{BASE}/my-attendance", headers=w.t["dev"])
    assert r.status_code == 200 and r.json()["status"] == "present"
    _mark(w, chitra="absent")
    r = w.c.post(f"{BASE}/my-attendance", headers=w.t["chitra"])
    assert r.json()["status"] == "absent", "a check-in never overrides the principal's absence"
    assert w.c.get(URL, headers=w.t["ana"]).status_code == 403
    assert w.c.post(f"{BASE}/my-attendance", headers=w.stu).status_code == 403
    bad = w.c.put(URL, params={"date": MON}, json={"marks": [{"teacherId": w.uid["ana"], "status": "asleep"}]},
                  headers=w.p)
    assert bad.status_code == 422
    other = w.c.put(URL, params={"date": MON}, json={"marks": [{"teacherId": w.uid["ana"], "status": "absent"}]},
                    headers=w.p2)
    assert other.status_code in (403, 404)
