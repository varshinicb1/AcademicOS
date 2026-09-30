"""A daily digest instead of each notification as it comes (SA-5): the inbox
still gets everything at once; push and email are held and go as one
message a day at the person's chosen time, once; a cover request still goes
at once; and turning it off returns to "as they come"."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from test_homework import _create, w  # noqa: F401 - `w` is a fixture

IST = timezone(timedelta(hours=5, minutes=30))


def test_a_student_gets_one_message_a_day_at_their_time(w, monkeypatch):
    from academicos.operations import notifications
    from academicos.operations.routes import run_automations, store
    pushes: list[tuple[str, str]] = []           # to Asha's phone only; Bhavna, in the same class, is not on a digest

    def push(tokens, title, body, data):
        if "asha-phone-token" in tokens:
            pushes.append((title, body))
        return "sent", None

    monkeypatch.setattr(notifications, "send_push", push)
    assert w.c.post("/api/v1/devices", json={"token": "asha-phone-token", "platform": "android"},
                    headers=w.s1).status_code == 200
    r = w.c.put("/api/v1/notification-preferences", json={"digestAt": "19:00"}, headers=w.s1)
    assert r.status_code == 200 and r.json()["digestAt"] == "19:00"

    _create(w, "ana", title="Light practice")
    _create(w, "ana", title="Mirrors")
    inbox = w.c.get("/api/v1/notifications", headers=w.s1).json()["items"]
    assigned = [i for i in inbox if i["kind"] == "homework_assigned"]
    assert len(assigned) == 2 and all(i["pushStatus"] == "digest" for i in assigned), "in the inbox now, pushed later"
    assert pushes == []

    s1 = w.c.get("/api/v1/auth/me", headers=w.s1).json()["id"]
    # At a fixed daytime moment: at the real clock, between 21:00 and 07:00
    # IST, the student's default quiet hours deferred the push and this failed
    # every night (the gate for #48-#50, 2026-09-29 22:02).
    store().notify(school_id="school_1", user_ids=[s1], kind="substitution_proposed",
                   params={"section": "10-A", "period": 3, "date": "2026-06-02", "subject": "Science"},
                   now=datetime(2026, 6, 1, 10, 0, tzinfo=IST))
    assert len(pushes) == 1, "a cover request is never held for the digest"

    day = datetime(2026, 6, 1, 18, 30, tzinfo=IST)
    assert run_automations(day.astimezone(timezone.utc))["user_digests"] == 0, "not before 19:00"
    assert run_automations((day + timedelta(hours=1)).astimezone(timezone.utc))["user_digests"] == 1
    title, body = pushes[-1]
    assert title == "Today: 2 updates" and "New homework: Science" in body
    assert run_automations((day + timedelta(hours=2)).astimezone(timezone.utc))["user_digests"] == 0, "once a day"
    statuses = {i["pushStatus"] for i in w.c.get("/api/v1/notifications", headers=w.s1).json()["items"]
                if i["kind"] == "homework_assigned"}
    assert statuses == {"digested"}


def test_turning_the_digest_off_goes_back_to_as_they_come(w):
    assert w.c.put("/api/v1/notification-preferences", json={"digestAt": "07:30"}, headers=w.s2).json()["digestAt"] == "07:30"
    off = w.c.put("/api/v1/notification-preferences", json={"digestAt": ""}, headers=w.s2)
    assert off.status_code == 200 and off.json()["digestAt"] is None
    assert w.c.put("/api/v1/notification-preferences", json={"digestAt": "25:00"}, headers=w.s2).status_code == 422
    _create(w, "ana")
    [item] = [i for i in w.c.get("/api/v1/notifications", headers=w.s2).json()["items"] if i["kind"] == "homework_assigned"]
    assert item["pushStatus"] != "digest"
