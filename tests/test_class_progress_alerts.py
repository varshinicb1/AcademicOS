"""Class progress (TA-6) for the section's teachers and the principal only,
and the principal's morning alerts (ADM-3)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from test_homework import _create, w  # noqa: F401 - `w` is a fixture

IST = timezone(timedelta(hours=5, minutes=30))


def _mark_all(w):
    hw = _create(w, "ana", questionIds=["q1", "q2"]).json()
    w.c.post(f"/api/v1/my-homework/{hw['id']}/submit", json={"answers": {"q1": "A", "q2": "B"}}, headers=w.s1)
    w.c.post(f"/api/v1/my-homework/{hw['id']}/submit", json={"answers": {"q1": "C", "q2": "C"}}, headers=w.s2)
    return hw


def test_class_progress_for_the_sections_teacher(w):
    _mark_all(w)
    r = w.c.get(f"/api/v1/sections/{w.a10}/progress", headers=w.ana)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["sectionName"] == "10-A" and d["students"] == 2
    [light] = d["chapters"]
    assert light["studentsWithEvidence"] == 2 and sum(light["counts"].values()) == 2
    assert w.c.get(f"/api/v1/sections/{w.a10}/progress", headers=w.p).status_code == 200
    assert w.c.get(f"/api/v1/sections/{w.a10}/progress", headers=w.bala).status_code == 403    # teaches 10-B only
    assert w.c.get(f"/api/v1/sections/{w.a10}/progress", headers=w.s1).status_code == 403
    assert w.c.get(f"/api/v1/sections/{w.a10}/progress", headers=w.p2).status_code == 403
    assert w.c.get(f"/api/v1/sections/{w.a10}/progress", params={"subject": "Maths"},
                   headers=w.ana).json()["chapters"] == []


def test_morning_alerts_name_what_needs_the_principal(w, monkeypatch):
    from academicos.curriculum import routes as cr
    from academicos.operations.routes import run_automations
    from datetime import date
    _create(w, "ana", questionIds=["q1"], dueDate="2026-06-02")
    monkeypatch.setattr(cr, "_school_today", lambda: date(2026, 6, 5))
    now = datetime(2026, 6, 5, 8, 30, tzinfo=IST).astimezone(timezone.utc)
    out = run_automations(now)
    assert out["principal_alerts"] == 1
    inbox = w.c.get("/api/v1/notifications", headers=w.p).json()["items"]
    alert = next(i for i in inbox if i["kind"] == "principal_alert" and i["title"].startswith("Needs attention"))
    assert "homework past due with fewer than half handed in" in alert["body"]
    assert run_automations(now + timedelta(hours=1))["principal_alerts"] == "done"


def test_teachers_hear_about_work_waiting_for_their_marks(w):
    from academicos.operations.routes import run_automations, store
    hw = _create(w, "ana").json()        # q3 is written: the submission waits for the teacher
    w.c.post(f"/api/v1/my-homework/{hw['id']}/submit", json={"answers": {"q1": "A", "q2": "B", "q3": "angle"}},
             headers=w.s1)
    s = store()
    with s._conn_lock:
        s.conn.execute("UPDATE homework_submissions SET submitted_at=?", ("2026-01-01T00:00:00+00:00",))
        s._commit()
    now = datetime.now(timezone.utc).replace(hour=11)       # 16:30 IST
    assert run_automations(now)["marking_due"] == 1
    inbox = w.c.get("/api/v1/notifications", headers=w.ana).json()["items"]
    assert any(i["kind"] == "marking_due" and i["title"] == "1 waiting for your marks" for i in inbox)
