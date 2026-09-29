"""Delegated admin (M1.4): the principal grants a teacher a capability,
optionally scoped; the teacher then passes that capability's routes and no
others; revoking shuts them again. Uses the cover fixture (Ana, Bala,
Chitra, Dev; 10-A, 10-B, 9-A). 2026-06-01 is a Monday."""
from __future__ import annotations

from test_cover_routes import BASE, MON, _apply, w  # noqa: F401 - `w` is a fixture


def _grant(w, who, cap, scope=None, by=None):
    body = {"userId": w.uid[who], "capability": cap}
    if scope:
        body["scope"] = scope
    return w.c.post("/api/v1/admin/grants", json=body, headers=by or w.p)


def test_a_granted_teacher_runs_leave_and_attendance(w):
    leave = _apply(w, "ana").json()
    decide = f"{BASE}/leave-requests/{leave['id']}/decision"
    assert w.c.post(decide, json={"approve": True}, headers=w.t["bala"]).status_code == 403
    g = _grant(w, "bala", "leave")
    assert g.status_code == 200, g.text
    assert g.json()["label"].startswith("Leave")
    mine = w.c.get("/api/v1/my-grants", headers=w.t["bala"]).json()
    assert mine["capabilities"] == ["leave"]
    assert w.c.post(decide, json={"approve": True}, headers=w.t["bala"]).status_code == 200
    assert w.c.get(f"{BASE}/teacher-attendance", params={"date": MON}, headers=w.t["bala"]).status_code == 200
    # a leave admin sees everyone's leave and every substitution, like the principal
    assert len(w.c.get(f"{BASE}/leave-requests", headers=w.t["bala"]).json()) == 1
    assert len(w.c.get(f"{BASE}/substitutions", params={"from": MON, "to": MON}, headers=w.t["bala"]).json()) == 2
    # and nothing else
    assert w.c.post("/api/v1/exams", json={"name": "x", "startDate": MON, "endDate": MON, "grades": [10]},
                    headers=w.t["bala"]).status_code == 403
    assert w.c.get("/api/v1/admin/grants", headers=w.t["bala"]).status_code == 403


def test_revoking_shuts_the_door(w):
    gid = _grant(w, "chitra", "exams").json()["id"]
    body = {"name": "UT", "startDate": MON, "endDate": "2026-06-05", "grades": [10]}
    assert w.c.post("/api/v1/exams", json=body, headers=w.t["chitra"]).status_code == 200
    assert w.c.delete(f"/api/v1/admin/grants/{gid}", headers=w.p).json()["active"] is False
    assert w.c.post("/api/v1/exams", json=body, headers=w.t["chitra"]).status_code == 403
    assert w.c.delete(f"/api/v1/admin/grants/{gid}", headers=w.p).status_code == 409
    assert w.c.get("/api/v1/my-grants", headers=w.t["chitra"]).json()["capabilities"] == []


def test_only_the_principal_grants_and_only_to_teachers(w):
    assert _grant(w, "ana", "leave", by=w.t["bala"]).status_code == 403
    assert _grant(w, "ana", "leave", by=w.p2).status_code == 403
    assert w.c.post("/api/v1/admin/grants", json={"userId": w.uid["ana"], "capability": "everything"},
                    headers=w.p).status_code == 422
    stu = w.c.get("/api/v1/auth/me", headers=w.stu).json()["id"]
    assert w.c.post("/api/v1/admin/grants", json={"userId": stu, "capability": "leave"},
                    headers=w.p).status_code == 422
    assert w.c.get("/api/v1/my-grants", headers=w.p).json()["capabilities"][0] == "users"
    assert w.c.get("/api/v1/my-grants", headers=w.stu).json()["capabilities"] == []


def test_granting_again_replaces_the_scope(w):
    first = _grant(w, "dev", "timetable", {"sectionIds": [w.a9]}).json()
    assert first["scope"] == {"sectionIds": [w.a9]}
    again = _grant(w, "dev", "timetable", {"grades": [9, 10]}).json()
    grants = w.c.get("/api/v1/admin/grants", headers=w.p).json()
    assert [g["id"] for g in grants] == [again["id"]] and again["scope"] == {"grades": [9, 10]}
