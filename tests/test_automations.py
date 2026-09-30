"""Scheduled automations (NTF-2): each job runs once in its window, sends to
the right people, and a second run sends nothing new. 2026-06-01 is a
Monday; the cover fixture's timetable has Monday periods."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from test_cover_routes import BASE, MON, _apply, w  # noqa: F401 - `w` is a fixture

IST = timezone(timedelta(hours=5, minutes=30))


def _at(day, hh, mm=0):
    y, m, d = map(int, day.split("-"))
    return datetime(y, m, d, hh, mm, tzinfo=IST).astimezone(timezone.utc)


def _run(now):
    from academicos.operations.routes import run_automations
    return run_automations(now)


def _kinds(w, headers):
    return [i for i in w.c.get("/api/v1/notifications", headers=headers).json()["items"]]


def _homework(w, due):
    from academicos.operations.routes import store
    return store().create_homework(school_id="school_1", academic_year_id=w.year, teacher_id=w.uid["ana"],
                                   subject_id=w.sci10, subject_name="Science", grade=10, section_ids=[w.b10],
                                   title="Light worksheet", instructions="", chapter_ids=[],
                                   questions=[{"id": "q1", "marks": 1}], due_date=due, created_by=w.uid["ana"],
                                   publish=True)


def test_windows_and_once_only(w):
    _homework(w, MON)
    early = _run(_at("2026-05-31", 8))
    assert early["homework_due_tomorrow"] == "not yet" and early["teacher_daily_digest"] == "not yet"
    out = _run(_at("2026-05-31", 18, 30))
    assert out["homework_due_tomorrow"] == 1 and out["teacher_daily_digest"] >= 1
    again = _run(_at("2026-05-31", 19))
    assert again["homework_due_tomorrow"] == "done" and again["teacher_daily_digest"] == "done"

    due = [i for i in _kinds(w, w.stu) if i["kind"] == "homework_due"]
    assert len(due) == 1 and "tomorrow" in due[0]["title"]
    digest = [i for i in _kinds(w, w.t["ana"]) if i["kind"] == "daily_digest"]
    assert len(digest) == 1 and digest[0]["title"] == "Tomorrow: 2 periods, 0 duties"
    assert "period 1" in digest[0]["body"]


def test_overdue_homework_tells_its_teacher_once(w):
    _homework(w, MON)
    assert _run(_at("2026-06-02", 10))["homework_overdue"] == 1
    _run(_at("2026-06-03", 10))
    over = [i for i in _kinds(w, w.t["ana"]) if i["kind"] == "homework_overdue"]
    assert len(over) == 1 and over[0]["title"] == "1 not submitted: Light worksheet"


def test_unaccepted_cover_is_escalated_to_the_principal(w):
    leave = _apply(w, "ana").json()
    w.c.post(f"{BASE}/leave-requests/{leave['id']}/decision", json={"approve": True}, headers=w.p)
    assert _run(_at(MON, 7, 5))["substitution_escalation"] == 0, "just proposed: not stuck yet"
    w.store._exec("UPDATE substitutions SET updated_at=?", (_at("2026-05-31", 20).isoformat(),))
    w.store._commit()
    assert _run(_at(MON, 7, 10))["substitution_escalation"] == 2
    _run(_at(MON, 7, 20))
    alerts = [i for i in _kinds(w, w.p) if i["kind"] == "principal_alert"]
    assert len(alerts) == 2 and all(a["title"].startswith("Cover needed:") for a in alerts)


def test_the_weekly_digest_goes_to_the_principal_on_monday(w):
    _homework(w, MON)
    assert _run(_at("2026-06-07", 9))["principal_weekly_digest"] == "not yet"     # a Sunday
    assert _run(_at("2026-06-08", 7, 30))["principal_weekly_digest"] == 1
    [digest] = [i for i in _kinds(w, w.p) if i["kind"] == "weekly_digest"]
    assert digest["title"] == "Week of 2026-06-01"


def test_the_cron_route_and_status(w, monkeypatch):
    assert w.c.post("/api/v1/automations/run").status_code == 404
    monkeypatch.setenv("ACOS_CRON_KEY", "k" * 32)
    assert w.c.post("/api/v1/automations/run", headers={"X-Cron-Key": "wrong"}).status_code == 401
    r = w.c.post("/api/v1/automations/run", headers={"X-Cron-Key": "k" * 32})
    assert r.status_code == 200 and "substitution_escalation" in r.json()["jobs"]
    assert w.c.get("/api/v1/automations/status", headers=w.p).status_code == 200
    assert w.c.get("/api/v1/automations/status", headers=w.t["ana"]).status_code == 403


def _hindi(w, headers):
    from academicos.operations.routes import store
    uid = w.c.get("/api/v1/auth/me", headers=headers).json()["id"]
    store().set_settings(uid, language="hi")


def test_hindi_readers_get_no_english_in_their_messages(w):
    """N-8-4: the Hindi templates were filled with English words -- a Hindi
    student read "गृहकार्य tomorrow तक", and a Hindi principal's alerts were
    English sentences in a Hindi frame."""
    _hindi(w, w.stu)
    _hindi(w, w.p)
    _homework(w, MON)
    r = w.c.post("/api/v1/exams", json={"name": "Unit test 1", "startDate": MON, "endDate": "2026-06-05",
                                        "grades": [10]}, headers=w.p)
    assert r.status_code == 200, r.text
    _run(_at("2026-05-31", 18, 30))
    [due] = [i for i in _kinds(w, w.stu) if i["kind"] == "homework_due"]
    assert due["title"] == "गृहकार्य कल तक" and "tomorrow" not in due["body"]
    [alert] = [i for i in _kinds(w, w.p) if i["kind"] == "principal_alert"]
    assert alert["title"] == "आज ध्यान दें (1)"
    assert alert["body"] == "Unit test 1 2026-06-01 से शुरू है, पर डेटशीट नहीं बनी।"
    # An English reader of the same alert still reads English.
    from academicos.operations.notifications import render
    title, body = render("principal_alert", {"title": "Needs attention today (1)", "body": "x.",
                                             "title_hi": "आज ध्यान दें (1)", "body_hi": "y।"}, "en")
    assert (title, body) == ("Needs attention today (1)", "x.")


def test_a_hindi_principal_reads_the_cover_escalation_in_hindi(w):
    _hindi(w, w.p)
    leave = _apply(w, "ana").json()
    w.c.post(f"{BASE}/leave-requests/{leave['id']}/decision", json={"approve": True}, headers=w.p)
    w.store._exec("UPDATE substitutions SET updated_at=?", (_at("2026-05-31", 20).isoformat(),))
    w.store._commit()
    _run(_at(MON, 7, 10))
    alerts = [i for i in _kinds(w, w.p) if i["kind"] == "principal_alert"]
    assert alerts and all(a["title"].startswith("स्थानापन्न चाहिए:") and "पीरियड" in a["title"] for a in alerts)
    assert all("स्वीकार नहीं हुआ" in a["body"] and "accepted" not in a["body"] for a in alerts)
