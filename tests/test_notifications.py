"""The notification service (NTF-1): inbox, per-kind channels, quiet hours,
language, dedupe, delivery status and retries -- and the substitution flow
landing in the substitute's inbox."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from academicos.operations import notifications as notif_mod
from academicos.operations.store import OperationsStore

IST = timezone(timedelta(hours=5, minutes=30))


def _at(hh, mm=0):
    return datetime(2026, 6, 1, hh, mm, tzinfo=IST).astimezone(timezone.utc)


@pytest.fixture
def ops(tmp_path, monkeypatch):
    monkeypatch.setattr(OperationsStore, "deliver_inline", True)
    s = OperationsStore(tmp_path / "ops.sqlite")
    yield s
    s.close()


def _sub(ops, user="t1", **kw):
    return ops.notify(school_id="s1", user_ids=[user], kind="substitution_proposed",
                      params={"section": "10-B", "period": 2, "date": "2026-06-01", "subject": "Science"}, **kw)


def test_a_notification_is_in_the_inbox_and_push_is_tried(ops, monkeypatch):
    calls = []
    monkeypatch.setattr(notif_mod, "send_push", lambda tokens, t, b, d: (calls.append(t) or ("sent", None)))
    ops.register_device("t1", "tok_" + "x" * 20, "android")
    [n] = _sub(ops, now=_at(10))
    assert n.title == "Substitution: 10-B period 2"
    assert "Accept or decline" in n.body
    after = ops.get_notification(n.id)
    assert after.push_status == "sent" and after.email_status == "none"
    assert calls == ["Substitution: 10-B period 2"]
    assert ops.unread_count("t1") == 1
    assert ops.mark_read("t1", n.id) == 1 and ops.unread_count("t1") == 0


def test_quiet_hours_hold_push_until_morning_but_not_the_inbox(ops, monkeypatch):
    monkeypatch.setattr(notif_mod, "send_push", lambda *a: ("sent", None))
    [n] = _sub(ops, now=_at(22))
    assert ops.get_notification(n.id).push_status == "deferred"
    assert ops.unread_count("t1") == 1, "the inbox has it at once"
    ops.deliver_due(now=_at(23, 30))
    assert ops.get_notification(n.id).push_status == "deferred"
    ops.deliver_due(now=_at(7, 5) + timedelta(days=1))
    assert ops.get_notification(n.id).push_status == "sent"


def test_a_repeated_dedupe_key_notifies_once(ops, monkeypatch):
    monkeypatch.setattr(notif_mod, "send_push", lambda *a: ("skipped", "no device registered"))
    assert len(_sub(ops, dedupe_key="sub:1:t1", now=_at(10))) == 1
    assert _sub(ops, dedupe_key="sub:1:t1", now=_at(10)) == []
    assert len(ops.inbox("t1")) == 1


def test_hindi_and_per_kind_switches(ops, monkeypatch):
    monkeypatch.setattr(notif_mod, "send_push", lambda *a: ("sent", None))
    ops.set_settings("t1", language="hi")
    ops.set_channel("t1", "substitution_proposed", "push", False)
    [n] = _sub(ops, now=_at(10))
    assert n.title.startswith("स्थानापन्न") and n.push_status == "none"
    with pytest.raises(ValueError):
        ops.set_channel("t1", "streak_reminder", "push", True)       # there is no such kind
    with pytest.raises(ValueError):
        ops.set_settings("t1", language="fr")


def test_a_failing_channel_is_retried_three_times_then_left(ops, monkeypatch):
    monkeypatch.setattr(notif_mod, "send_push", lambda *a: ("failed", "403 permission denied"))
    [n] = _sub(ops, now=_at(10))
    for _ in range(5):
        ops.deliver_due(now=_at(10))
    after = ops.get_notification(n.id)
    assert after.push_status == "failed" and after.attempts == notif_mod.MAX_ATTEMPTS
    assert "403" in after.last_error


_UNREGISTERED = '404 {"error": {"code": 404, "status": "NOT_FOUND", "details": [{"errorCode": "UNREGISTERED"}]}}'


def test_a_token_fcm_calls_dead_is_removed_after_max_attempts(ops, monkeypatch):
    """N-8-10: a device whose token FCM calls UNREGISTERED used to be kept for
    good, so every later notification to that person failed the same way."""
    seen = []

    def push(tokens, t, b, d):
        seen.append(list(tokens))
        dead = [x for x in tokens if x == "tok_dead"]
        return ("failed", _UNREGISTERED, dead) if tokens else ("skipped", "no device registered", [])
    monkeypatch.setattr(notif_mod, "send_push", push)
    ops.register_device("t1", "tok_dead", "android")
    [n] = _sub(ops, now=_at(10))
    for _ in range(notif_mod.MAX_ATTEMPTS - 2):
        ops.deliver_due(now=_at(10))
    assert ops.devices_for("t1") == ["tok_dead"], "kept while it has failed fewer than MAX_ATTEMPTS times"
    ops.deliver_due(now=_at(10))
    assert ops.devices_for("t1") == [], "removed at the MAX_ATTEMPTS-th dead answer"
    assert ops.get_notification(n.id).attempts == notif_mod.MAX_ATTEMPTS
    [later] = _sub(ops, now=_at(11))
    assert seen[-1] == [] and ops.get_notification(later.id).push_status == "skipped"


def test_a_transient_push_failure_keeps_the_token(ops, monkeypatch):
    monkeypatch.setattr(notif_mod, "send_push", lambda *a: ("failed", "503 service unavailable", []))
    ops.register_device("t1", "tok_ok", "android")
    _sub(ops, now=_at(10))
    for _ in range(5):
        ops.deliver_due(now=_at(10))
    assert ops.devices_for("t1") == ["tok_ok"]


def test_a_send_that_goes_through_clears_the_count(ops, monkeypatch):
    answers = iter([("failed", _UNREGISTERED, ["tok_x"]), ("failed", _UNREGISTERED, ["tok_x"]),
                    ("sent", None, []), ("failed", _UNREGISTERED, ["tok_x"])])
    monkeypatch.setattr(notif_mod, "send_push", lambda *a: next(answers))
    ops.register_device("t1", "tok_x", "android")
    [n] = _sub(ops, now=_at(10))                  # dead answer 1
    ops.deliver_due(now=_at(10))                  # dead answer 2
    ops.deliver_due(now=_at(10))                  # it went through
    assert ops.get_notification(n.id).push_status == "sent"
    _sub(ops, now=_at(10), dedupe_key="second")   # a third dead answer, but not in a row
    assert ops.devices_for("t1") == ["tok_x"]


def test_only_a_dead_token_answer_counts():
    assert notif_mod.token_is_dead(404, _UNREGISTERED)
    assert notif_mod.token_is_dead(400, '{"error": {"status": "INVALID_ARGUMENT", "message": '
                                         '"The registration token is not a valid FCM registration token"}}')
    assert not notif_mod.token_is_dead(503, "Service Unavailable")
    assert not notif_mod.token_is_dead(404, "Requested entity was not found.  (wrong project)")
    assert not notif_mod.token_is_dead(403, '{"error": {"status": "PERMISSION_DENIED", "details": '
                                            '[{"errorCode": "SENDER_ID_MISMATCH"}]}}')


def test_email_is_skipped_with_a_reason_when_no_mailer_is_set_up(ops, monkeypatch):
    monkeypatch.setattr(OperationsStore, "email_for", staticmethod(lambda uid: "p1@example.com"))
    monkeypatch.setattr(notif_mod, "send_push", lambda *a: ("skipped", "no device registered"))
    for k in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "COMPOSIO_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    [n] = ops.notify(school_id="s1", user_ids=["p1"], kind="principal_alert",
                     params={"title": "Unfilled substitution", "body": "10-B period 2 has no teacher"}, now=_at(10))
    after = ops.get_notification(n.id)
    assert after.email_status == "skipped" and "not configured" in (after.last_error or "")


# ---------------- through the routes ----------------

from test_cover_routes import BASE, MON, _apply, w  # noqa: E402,F401 - `w` is a fixture


def test_the_substitute_is_told_and_only_they_can_read_it(w, monkeypatch):
    monkeypatch.setattr(OperationsStore, "deliver_inline", True)
    monkeypatch.setattr(notif_mod, "send_push", lambda *a: ("skipped", "no device registered"))
    leave = _apply(w, "ana").json()
    w.c.post(f"{BASE}/leave-requests/{leave['id']}/decision", json={"approve": True}, headers=w.p)
    inbox = w.c.get("/api/v1/notifications", headers=w.t["chitra"]).json()
    assert inbox["unreadCount"] >= 1
    item = next(i for i in inbox["items"] if i["kind"] == "substitution_proposed")
    assert item["title"] == "Substitution: 10-B period 2" and item["link"] == f"/my-day?date={MON}"
    ana = w.c.get("/api/v1/notifications", headers=w.t["ana"]).json()
    assert any(i["kind"] == "leave_decided" and "approved" in i["body"] for i in ana["items"])
    assert w.c.post(f"/api/v1/notifications/{item['id']}/read", headers=w.t["dev"]).status_code == 403
    assert w.c.post(f"/api/v1/notifications/{item['id']}/read", headers=w.t["chitra"]).status_code == 200
    assert w.c.get("/api/v1/notifications", params={"unreadOnly": "true"},
                   headers=w.t["chitra"]).json()["items"] == []


def test_preferences_and_devices_through_the_routes(w):
    h = w.t["ana"]
    prefs = w.c.get("/api/v1/notification-preferences", headers=h).json()
    assert prefs["quietStart"] == "21:00" and any(k["kind"] == "homework_due" for k in prefs["kinds"])
    r = w.c.put("/api/v1/notification-preferences", json={"quietStart": "20:00", "language": "hi",
                                                          "kinds": [{"kind": "timetable_published", "push": False}]},
                headers=h)
    assert r.status_code == 200 and r.json()["language"] == "hi"
    assert next(k for k in r.json()["kinds"] if k["kind"] == "timetable_published")["push"] is False
    assert w.c.put("/api/v1/notification-preferences", json={"quietStart": "25:00"}, headers=h).status_code == 422
    assert w.c.put("/api/v1/notification-preferences", json={"kinds": [{"kind": "nope", "push": True}]},
                   headers=h).status_code == 422
    token = "fcm_" + "y" * 40
    assert w.c.post("/api/v1/devices", json={"token": token, "platform": "android"}, headers=h).status_code == 200
    assert w.c.delete(f"/api/v1/devices/{token}", headers=w.t["bala"]).status_code == 404
    assert w.c.delete(f"/api/v1/devices/{token}", headers=h).status_code == 200
