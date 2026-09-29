"""SMS and WhatsApp as notification channels (REQUIREMENTS INT-2, NTF-1).

A person gives their own number and consents per channel; only kinds about
their next action go out, respecting quiet hours, their push choice and a
daily digest; nothing leaves the server until the owner configures the
provider; students are refused (their parent is messaged); the consent is
audited without the number. The providers are faked at the HTTP call, and
the payloads checked against the WhatsApp Cloud API and MSG91 v5 flow shapes.
"""
from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from academicos.operations.messaging import normalize_mobile

from _auth_helpers import register_invited
from test_assessment_routes_auth import _boot_client, _register

NOON_IST = datetime(2026, 6, 1, 6, 30, tzinfo=timezone.utc)      # 12:00 IST
NIGHT_IST = datetime(2026, 6, 1, 17, 30, tzinfo=timezone.utc)    # 23:00 IST


def test_indian_mobiles_are_read_the_ways_people_type_them():
    for typed in ("98765 43210", "+91-98765-43210", "098765 43210", "919876543210", "(987) 654-3210"):
        assert normalize_mobile(typed) == "+919876543210"
    for bad in ("12345", "5876543210", "+1 415 555 0100", "98765432100"):
        with pytest.raises(ValueError, match="Indian mobile"):
            normalize_mobile(bad)


class _Post:
    """Records requests.post calls and answers them."""

    def __init__(self, status=200, body=None):
        self.calls, self.status, self.body = [], status, body

    def __call__(self, url, json=None, headers=None, timeout=None):
        self.calls.append(SimpleNamespace(url=url, json=json, headers=headers))
        body = self.body if self.body is not None else {"messages": [{"id": "wamid.1"}], "type": "success",
                                                         "message": "req-1"}
        return SimpleNamespace(status_code=self.status, text=str(body), content=b"x", json=lambda: body)


@pytest.fixture
def w(tmp_path, monkeypatch):
    from academicos.operations.store import OperationsStore
    # Delivery only when a test calls deliver_due with its own clock: no
    # background thread on the real one.
    monkeypatch.setattr(OperationsStore, "deliver_inline", False)
    monkeypatch.setattr(OperationsStore, "_deliver_quietly", lambda self: None)
    for var in ("ACOS_WHATSAPP_TOKEN", "ACOS_WHATSAPP_PHONE_NUMBER_ID", "ACOS_SMS_AUTHKEY", "ACOS_SMS_TEMPLATE_ID"):
        monkeypatch.delenv(var, raising=False)
    with _boot_client(tmp_path, monkeypatch) as c:
        _register(c, "school_1", "p1@example.com", "Priya", principal_key="test-bootstrap-key")
        t = _register(c, "school_1", "ana@example.com", "Ana")
        s = register_invited(c, "school_1", "s1@example.com", name="Asha", role="student")
        from academicos.operations.routes import store
        yield SimpleNamespace(c=c, store=store(), t={"Authorization": f"Bearer {t['token']}"}, tid=t["user"]["id"],
                              s={"Authorization": f"Bearer {s['token']}"})


def _notify(w, kind="substitution_proposed", now=NOON_IST):
    [n] = w.store.notify(school_id="school_1", user_ids=[w.tid], kind=kind, now=now,
                         params={"section": "10-A", "period": 3, "date": "2026-06-02", "subject": "Science"})
    return n


def _consent(w, **body):
    r = w.c.put("/api/v1/me/contact", json=body, headers=w.t)
    assert r.status_code == 200, r.text
    return r.json()


def test_a_student_does_not_add_a_number(w):
    assert w.c.get("/api/v1/me/contact", headers=w.s).status_code == 403
    assert w.c.put("/api/v1/me/contact", json={"phone": "9876543210", "smsOk": True},
                   headers=w.s).status_code == 403


def test_consent_is_given_per_channel_and_audited_without_the_number(w):
    from academicos.assessment.audit_log import get_audit_log
    from academicos.curriculum import routes as cr
    assert w.c.put("/api/v1/me/contact", json={"phone": "12345", "smsOk": True}, headers=w.t).status_code == 422
    assert w.c.put("/api/v1/me/contact", json={"smsOk": True}, headers=w.t).status_code == 422
    got = _consent(w, phone="98765 43210", whatsappOk=True)
    assert (got["phone"], got["smsOk"], got["whatsappOk"]) == ("+919876543210", False, True)
    assert got["whatsappAvailable"] is False, "the owner has not switched WhatsApp on"
    assert "substitution_proposed" in got["kinds"]
    [entry] = get_audit_log(cr._cfg.data_root).for_action("message_consent_set")
    assert entry["details"]["after"] == {"phoneEnding": "10", "sms": False, "whatsapp": True}
    assert "9876543210" not in str(entry)


def test_nothing_leaves_the_server_until_the_provider_is_configured(w, monkeypatch):
    post = _Post()
    monkeypatch.setattr("requests.post", post)
    _consent(w, phone="9876543210", smsOk=True, whatsappOk=True)
    n = _notify(w)
    assert w.store.message_status(n.id) == {"sms": "pending", "whatsapp": "pending"}
    w.store.deliver_due(now=NOON_IST)
    assert w.store.message_status(n.id) == {"sms": "skipped", "whatsapp": "skipped"}
    assert post.calls == []


def test_whatsapp_and_sms_are_sent_in_the_providers_shapes(w, monkeypatch):
    monkeypatch.setenv("ACOS_WHATSAPP_TOKEN", "wa-token")
    monkeypatch.setenv("ACOS_WHATSAPP_PHONE_NUMBER_ID", "12345")
    monkeypatch.setenv("ACOS_SMS_AUTHKEY", "sms-key")
    monkeypatch.setenv("ACOS_SMS_TEMPLATE_ID", "flow-1")
    post = _Post()
    monkeypatch.setattr("requests.post", post)
    _consent(w, phone="9876543210", smsOk=True, whatsappOk=True)
    n = _notify(w)
    w.store.deliver_due(now=NOON_IST)
    assert w.store.message_status(n.id) == {"sms": "sent", "whatsapp": "sent"}
    wa = next(c for c in post.calls if "graph.facebook.com" in c.url)
    assert wa.url.endswith("/12345/messages") and wa.headers["Authorization"] == "Bearer wa-token"
    assert wa.json["to"] == "919876543210" and wa.json["type"] == "template"
    assert wa.json["template"]["name"] == "academicos_notice"
    assert [p["text"] for p in wa.json["template"]["components"][0]["parameters"]] == [n.title, n.body]
    sms = next(c for c in post.calls if "msg91" in c.url)
    assert sms.url == "https://control.msg91.com/api/v5/flow" and sms.headers["authkey"] == "sms-key"
    assert sms.json["template_id"] == "flow-1"
    assert sms.json["recipients"] == [{"mobiles": "919876543210", "title": n.title, "body": n.body}]


def test_a_failed_send_is_retried_and_counted(w, monkeypatch):
    monkeypatch.setenv("ACOS_WHATSAPP_TOKEN", "t")
    monkeypatch.setenv("ACOS_WHATSAPP_PHONE_NUMBER_ID", "1")
    monkeypatch.setattr("requests.post", _Post(status=500, body={"error": "down"}))
    _consent(w, phone="9876543210", whatsappOk=True)
    n = _notify(w)
    w.store.deliver_due(now=NOON_IST)
    row = w.store._fetchone("SELECT * FROM message_deliveries WHERE notification_id=?", (n.id,))
    assert (row["status"], row["attempts"]) == ("failed", 1) and "500" in row["last_error"]
    monkeypatch.setattr("requests.post", _Post())
    w.store.deliver_due(now=NOON_IST)
    assert w.store.message_status(n.id) == {"whatsapp": "sent"}


def test_only_next_action_kinds_go_and_the_persons_choices_hold(w, monkeypatch):
    _consent(w, phone="9876543210", whatsappOk=True)
    assert w.store.message_status(_notify(w, kind="timetable_published").id) == {}, "not a messaging kind"
    assert w.store.message_status(_notify(w, now=NIGHT_IST).id) == {"whatsapp": "deferred"}, "quiet hours"
    w.store.set_channel(w.tid, "exam_reminder", "push", False)
    assert w.store.message_status(_notify(w, kind="exam_reminder").id) == {}, "push for it is off"
    w.store.set_digest(w.tid, "18:00")
    assert w.store.message_status(_notify(w, kind="homework_due").id) == {}, "held for the digest"
    assert w.store.message_status(_notify(w).id) == {"whatsapp": "pending"}, "a cover request never waits"


def test_withdrawing_consent_stops_what_is_waiting(w):
    _consent(w, phone="9876543210", smsOk=True, whatsappOk=True)
    n = _notify(w, now=NIGHT_IST)
    _consent(w, phone="9876543210", smsOk=True, whatsappOk=False)
    assert w.store.message_status(n.id) == {"sms": "deferred", "whatsapp": "skipped"}
    gone = w.c.put("/api/v1/me/contact", json={"phone": None}, headers=w.t).json()
    assert gone["phone"] is None
    assert w.store.message_status(n.id) == {"sms": "skipped", "whatsapp": "skipped"}


def test_a_parent_gives_their_number_the_route_is_open_to_parents(tmp_path, monkeypatch):
    """Parents may call only route_policy.PARENT_PATHS; the consent route is
    one of them (a parent is who SMS and WhatsApp are mostly for)."""
    from test_guardians import _h, _parent
    from test_homework import w as homework_world

    gen = homework_world.__wrapped__(tmp_path, monkeypatch)
    hw = next(gen)
    try:
        mum = _h(_parent(hw))
        r = hw.c.put("/api/v1/me/contact", json={"phone": "9876543210", "whatsappOk": True}, headers=mum)
        assert r.status_code == 200, r.text
        assert hw.c.get("/api/v1/me/contact", headers=mum).json()["whatsappOk"] is True
    finally:
        gen.close()
