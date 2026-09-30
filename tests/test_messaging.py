"""SMS and WhatsApp as notification channels (REQUIREMENTS INT-2, NTF-1).

A person gives their own number, confirms it with a one-time code, and
consents per channel; only kinds about someone's next action go out,
respecting quiet hours, the push choice and a daily digest; a student's
kinds go to their actively linked parents; each message goes once, even
with two senders at once; nothing leaves the server until the owner
configures the provider; students are refused; the consent is audited
without the number. The providers are faked at the HTTP call, and the
payloads checked against the WhatsApp Cloud API and MSG91 v5 flow shapes.
"""
from __future__ import annotations

import os
import threading
import time
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from academicos.operations.messaging import normalize_mobile

from _auth_helpers import register_invited
from test_assessment_routes_auth import _boot_client, _register

NOON_IST = datetime(2026, 6, 1, 6, 30, tzinfo=timezone.utc)      # 12:00 IST
NIGHT_IST = datetime(2026, 6, 1, 17, 30, tzinfo=timezone.utc)    # 23:00 IST
SUB = {"section": "10-A", "period": 3, "date": "2026-06-02", "subject": "Science"}


def test_indian_mobiles_are_read_the_ways_people_type_them():
    for typed in ("98765 43210", "+91-98765-43210", "098765 43210", "919876543210", "(987) 654-3210"):
        assert normalize_mobile(typed) == "+919876543210"
    for bad in ("12345", "5876543210", "+1 415 555 0100", "98765432100", "९८७६५४३२१०"):
        with pytest.raises(ValueError, match="Indian mobile"):
            normalize_mobile(bad)


class _Post:
    """Records requests.post calls and answers them."""

    def __init__(self, status=200, body=None, delay=0.0):
        self.calls, self.status, self.body, self.delay = [], status, body, delay

    def __call__(self, url, json=None, headers=None, timeout=None):
        if self.delay:
            time.sleep(self.delay)
        self.calls.append(SimpleNamespace(url=url, json=json, headers=headers))
        body = self.body if self.body is not None else {"messages": [{"id": "wamid.1"}], "type": "success",
                                                         "message": "req-1"}
        return SimpleNamespace(status_code=self.status, text=str(body), content=b"x", json=lambda: body)

    def whatsapp(self):
        return [c for c in self.calls if "graph.facebook.com" in c.url]

    def sms(self):
        return [c for c in self.calls if "msg91" in c.url]


def _whatsapp_on(monkeypatch):
    monkeypatch.setenv("ACOS_WHATSAPP_TOKEN", "wa-token")
    monkeypatch.setenv("ACOS_WHATSAPP_PHONE_NUMBER_ID", "12345")


def _sms_on(monkeypatch):
    monkeypatch.setenv("ACOS_SMS_AUTHKEY", "sms-key")
    monkeypatch.setenv("ACOS_SMS_FLOW_SUBSTITUTION_PROPOSED", "flow-sub")
    monkeypatch.setenv("ACOS_SMS_FLOW_HOMEWORK_DUE", "flow-hw")
    monkeypatch.setenv("ACOS_SMS_FLOW_HOMEWORK_DUE_HI", "flow-hw-hi")
    monkeypatch.setenv("ACOS_SMS_FLOW_CODE", "flow-code")


@pytest.fixture
def w(tmp_path, monkeypatch):
    from academicos.operations.store import OperationsStore
    # Delivery only when a test calls deliver_due with its own clock: no
    # background thread on the real one.
    monkeypatch.setattr(OperationsStore, "deliver_inline", False)
    monkeypatch.setattr(OperationsStore, "_deliver_quietly", lambda self: None)
    for var in [v for v in os.environ if v.startswith(("ACOS_WHATSAPP_", "ACOS_SMS_"))]:
        monkeypatch.delenv(var, raising=False)
    with _boot_client(tmp_path, monkeypatch) as c:
        _register(c, "school_1", "p1@example.com", "Priya", principal_key="test-bootstrap-key")
        t = _register(c, "school_1", "ana@example.com", "Ana Rao")
        s = register_invited(c, "school_1", "s1@example.com", name="Asha Verma", role="student")
        from academicos.operations.routes import store
        yield SimpleNamespace(c=c, store=store(), t={"Authorization": f"Bearer {t['token']}"}, tid=t["user"]["id"],
                              s={"Authorization": f"Bearer {s['token']}"}, sid=s["user"]["id"])


def _notify(w, kind="substitution_proposed", now=NOON_IST, uid=None, params=None):
    [n] = w.store.notify(school_id="school_1", user_ids=[uid or w.tid], kind=kind, now=now,
                         params=SUB if params is None else params)
    return n


def _consent(w, **body):
    r = w.c.put("/api/v1/me/contact", json=body, headers=w.t)
    assert r.status_code == 200, r.text
    return r.json()


def _confirmed(w, user_id, *, phone="9876543210", sms=False, whatsapp=True):
    """A number given and confirmed, straight in the store: the code flow
    itself is tested through the routes below."""
    w.store.set_contact(user_id, phone=phone, sms_ok=sms, whatsapp_ok=whatsapp)
    w.store._exec("INSERT OR REPLACE INTO contact_verifications (user_id, phone, verified_at) VALUES (?,?,?)",
                  (user_id, normalize_mobile(phone), "2026-05-01T00:00:00+00:00"))
    w.store._commit()


def _row(w, n, user_id=None):
    return w.store._fetchone("SELECT * FROM message_outbox WHERE notification_id=? AND user_id=?",
                             (n.id, user_id or n.user_id))


# --------------------------------------------------------------------- #
# Who may give a number, and how it is kept
# --------------------------------------------------------------------- #

def test_a_student_does_not_add_a_number(w):
    assert w.c.get("/api/v1/me/contact", headers=w.s).status_code == 403
    assert w.c.put("/api/v1/me/contact", json={"phone": "9876543210", "smsOk": True},
                   headers=w.s).status_code == 403
    assert w.c.post("/api/v1/me/contact/verify", json={"code": "123456"}, headers=w.s).status_code == 403


def test_consent_is_given_per_channel_and_audited_without_the_number(w):
    from academicos.assessment.audit_log import get_audit_log
    from academicos.curriculum import routes as cr
    assert w.c.put("/api/v1/me/contact", json={"phone": "12345", "smsOk": True}, headers=w.t).status_code == 422
    assert w.c.put("/api/v1/me/contact", json={"smsOk": True}, headers=w.t).status_code == 422
    got = _consent(w, phone="98765 43210", whatsappOk=True)
    assert (got["phone"], got["smsOk"], got["whatsappOk"], got["verified"]) == ("+919876543210", False, True, False)
    assert got["whatsappAvailable"] is False, "the owner has not switched WhatsApp on"
    assert got["codeSentVia"] is None and "not switched on" in got["codeError"]
    assert "substitution_proposed" in got["kinds"]
    # A different number with the same last two digits is still a change.
    _consent(w, phone="91234 56710", whatsappOk=True)
    entries = get_audit_log(cr._cfg.data_root).for_action("message_consent_set")
    assert [e["details"]["numberChanged"] for e in reversed(entries)] == [True, True]
    assert entries[0]["details"]["before"] == entries[0]["details"]["after"] == \
        {"phoneEnding": "10", "sms": False, "whatsapp": True}
    assert "9876543210" not in str(entries) and "9123456710" not in str(entries)


def test_a_number_with_neither_box_ticked_is_not_kept(w):
    _consent(w, phone="9876543210", smsOk=True)
    gone = _consent(w, phone="9876543210", smsOk=False, whatsappOk=False)
    assert gone["phone"] is None and w.store.contact_for(w.tid) is None
    assert w.store._fetchone("SELECT phone FROM contact_verifications WHERE user_id=?", (w.tid,)) in \
        (None, {"phone": ""}), "no copy of the number is left behind"


# --------------------------------------------------------------------- #
# Confirming the number
# --------------------------------------------------------------------- #

def _code_from(post):
    return post.whatsapp()[-1].json["template"]["components"][0]["parameters"][0]["text"]


def test_a_number_is_confirmed_by_the_code_sent_to_it_and_nothing_goes_before(w, monkeypatch):
    from academicos.assessment.audit_log import get_audit_log
    from academicos.curriculum import routes as cr
    _whatsapp_on(monkeypatch)
    post = _Post()
    monkeypatch.setattr("requests.post", post)
    got = _consent(w, phone="9876543210", whatsappOk=True)
    assert (got["verified"], got["codeSentVia"]) == (False, "whatsapp")
    [sent] = post.whatsapp()
    template = sent.json["template"]
    assert template["name"] == "academicos_code" and sent.json["to"] == "919876543210"
    code = _code_from(post)
    assert len(code) == 6 and code.isdigit()
    assert template["components"][1] == {"type": "button", "sub_type": "url", "index": "0",
                                         "parameters": [{"type": "text", "text": code}]}, "the copy-code button"

    # Until it comes back, nothing is queued for the number.
    assert w.store.message_status(_notify(w).id) == {}

    wrong = "000000" if code != "000000" else "111111"
    r = w.c.post("/api/v1/me/contact/verify", json={"code": wrong}, headers=w.t)
    assert r.status_code == 422 and "4 tries left" in r.json()["detail"]
    r = w.c.post("/api/v1/me/contact/verify", json={"code": code}, headers=w.t)
    assert r.status_code == 200 and r.json()["verified"] is True
    [entry] = get_audit_log(cr._cfg.data_root).for_action("message_number_verified")
    assert entry["details"]["phoneEnding"] == "10" and "9876543210" not in str(entry)
    assert w.store.message_status(_notify(w).id) == {"whatsapp": "pending"}

    # Consent changes keep it confirmed; a new number is unconfirmed again.
    assert _consent(w, phone="9876543210", whatsappOk=True)["verified"] is True
    assert len(post.whatsapp()) == 1, "no second code for a confirmed number"
    assert _consent(w, phone="9123456789", whatsappOk=True)["verified"] is False


def test_codes_expire_tries_are_limited_and_sends_are_rate_limited(w, monkeypatch):
    _whatsapp_on(monkeypatch)
    post = _Post()
    monkeypatch.setattr("requests.post", post)
    start = NOON_IST
    w.store.set_contact(w.tid, phone="9876543210", sms_ok=False, whatsapp_ok=True)
    assert w.store.send_contact_code(w.tid, start) == ("whatsapp", None)
    code = _code_from(post)
    via, why = w.store.send_contact_code(w.tid, start + timedelta(seconds=10))
    assert via is None and "less than a minute" in why
    with pytest.raises(ValueError, match="expired"):
        w.store.verify_contact_code(w.tid, code, start + timedelta(minutes=11))
    # A new code, then five wrong tries end it -- even the right one after.
    assert w.store.send_contact_code(w.tid, start + timedelta(minutes=2))[0] == "whatsapp"
    code = _code_from(post)
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(5):
        with pytest.raises(ValueError, match="not right"):
            w.store.verify_contact_code(w.tid, wrong, start + timedelta(minutes=3))
    with pytest.raises(ValueError, match="too many"):
        w.store.verify_contact_code(w.tid, code, start + timedelta(minutes=3))
    # Five codes a day, however the number is changed in between.
    for i in range(3):
        w.store.set_contact(w.tid, phone=f"98765432{i}0", sms_ok=False, whatsapp_ok=True)
        assert w.store.send_contact_code(w.tid, start + timedelta(minutes=5 + 2 * i))[0] == "whatsapp"
    w.store.set_contact(w.tid, phone=None, sms_ok=False, whatsapp_ok=False)
    w.store.set_contact(w.tid, phone="9000000001", sms_ok=False, whatsapp_ok=True)
    via, why = w.store.send_contact_code(w.tid, start + timedelta(minutes=20))
    assert via is None and "five codes" in why
    assert len(post.whatsapp()) == 5


def test_the_code_goes_by_sms_when_only_sms_is_ticked(w, monkeypatch):
    _sms_on(monkeypatch)
    post = _Post()
    monkeypatch.setattr("requests.post", post)
    assert _consent(w, phone="9876543210", smsOk=True)["codeSentVia"] == "sms"
    [sms] = post.sms()
    assert sms.json["template_id"] == "flow-code"
    code = sms.json["recipients"][0]["code"]
    assert w.c.post("/api/v1/me/contact/verify", json={"code": code}, headers=w.t).json()["verified"] is True


# --------------------------------------------------------------------- #
# What is sent, to whom, and when
# --------------------------------------------------------------------- #

def test_nothing_leaves_the_server_until_the_provider_is_configured(w, monkeypatch):
    post = _Post()
    monkeypatch.setattr("requests.post", post)
    _confirmed(w, w.tid, sms=True, whatsapp=True)
    n = _notify(w)
    assert w.store.message_status(n.id) == {"sms": "pending", "whatsapp": "pending"}
    w.store.deliver_due(now=NOON_IST)
    assert w.store.message_status(n.id) == {"sms": "skipped", "whatsapp": "skipped"}
    assert post.calls == []


def test_each_kind_goes_as_its_own_registered_template(w, monkeypatch):
    _whatsapp_on(monkeypatch)
    _sms_on(monkeypatch)
    post = _Post()
    monkeypatch.setattr("requests.post", post)
    _confirmed(w, w.tid, sms=True, whatsapp=True)
    n = _notify(w, params={**SUB, "subject": "Social Science and Political\nLife (long name)"})
    w.store.deliver_due(now=NOON_IST)
    assert w.store.message_status(n.id) == {"sms": "sent", "whatsapp": "sent"}
    [wa] = post.whatsapp()
    assert wa.url.endswith("/12345/messages") and wa.headers["Authorization"] == "Bearer wa-token"
    assert wa.json["to"] == "919876543210" and wa.json["type"] == "template"
    assert wa.json["template"]["name"] == "academicos_substitution_proposed"
    assert wa.json["template"]["language"] == {"code": "en"}
    assert [p["text"] for p in wa.json["template"]["components"][0]["parameters"]] == \
        ["Ana", "2026-06-02", "Social Science and Political Life (long name)", "10-A", "3"], \
        "no newline in a WhatsApp variable (error 132018)"
    [sms] = post.sms()
    assert sms.url == "https://control.msg91.com/api/v5/flow" and sms.headers["authkey"] == "sms-key"
    assert sms.json["template_id"] == "flow-sub"
    [to] = sms.json["recipients"]
    assert to == {"mobiles": "919876543210", "name": "Ana", "date": "2026-06-02",
                  "subject": "Social Science and Political L", "section": "10-A", "period": "3"}
    assert all(len(v) <= 30 for v in to.values()), "DLT caps each variable at 30 characters"
    # A kind with no SMS template registered is skipped, not sent as text.
    n2 = _notify(w, kind="leave_decided", params={"decision": "approved", "start": "2026-06-03", "end": "2026-06-04"})
    w.store.deliver_due(now=NOON_IST)
    assert w.store.message_status(n2.id) == {"sms": "skipped", "whatsapp": "sent"}
    skipped = w.store._fetchone("SELECT last_error FROM message_outbox WHERE notification_id=? AND channel='sms'",
                                (n2.id,))
    assert "no SMS template" in skipped["last_error"]


def test_a_student_s_notice_goes_to_their_linked_parents_only(w, monkeypatch):
    _whatsapp_on(monkeypatch)
    _sms_on(monkeypatch)
    post = _Post()
    monkeypatch.setattr("requests.post", post)
    for parent, relation in (("mum", "mother"), ("dad", "father"), ("aunt", "guardian"), ("other", "mother")):
        _confirmed(w, parent, phone={"mum": "9876543210", "dad": "9876543211", "aunt": "9876543212",
                                     "other": "9876543213"}[parent], sms=parent == "dad", whatsapp=parent != "dad")
    w.store.link_guardian(parent_id="mum", student_id=w.sid, school_id="school_1", relation="mother", created_by="p")
    w.store.link_guardian(parent_id="dad", student_id=w.sid, school_id="school_1", relation="father", created_by="p")
    w.store.link_guardian(parent_id="aunt", student_id=w.sid, school_id="school_1", relation="guardian",
                          created_by="p")
    w.store.end_guardianship("aunt", w.sid, revoked_by="p")   # an ended link
    w.store.set_settings("dad", language="hi")
    n = _notify(w, kind="homework_due", uid=w.sid, params={"title": "Fractions worksheet", "due": "tomorrow"})
    assert w.store.message_status(n.id) == {}, "the student has no number"
    assert w.store.message_status(n.id, "mum") == {"whatsapp": "pending"}
    assert w.store.message_status(n.id, "dad") == {"sms": "pending"}
    assert w.store.message_status(n.id, "aunt") == {} and w.store.message_status(n.id, "other") == {}
    w.store.deliver_due(now=NOON_IST)
    [wa] = post.whatsapp()
    assert wa.json["to"] == "919876543210" and wa.json["template"]["name"] == "academicos_homework_due"
    assert [p["text"] for p in wa.json["template"]["components"][0]["parameters"]] == \
        ["Asha", "Fractions worksheet", "tomorrow"], "the child's first name, so a parent of two knows which"
    [sms] = post.sms()
    assert sms.json["template_id"] == "flow-hw-hi", "the parent's own language"
    assert sms.json["recipients"][0]["mobiles"] == "919876543211"
    assert _row(w, n, "mum")["about_id"] == w.sid
    # Only a student's kinds go to their parents.
    assert w.store._fetchone("SELECT COUNT(*) AS k FROM message_outbox WHERE notification_id=?",
                             (_notify(w, uid=w.sid).id,))["k"] == 0


def test_a_parent_s_own_quiet_hours_digest_and_choices_hold(w, monkeypatch):
    _confirmed(w, "mum")
    w.store.link_guardian(parent_id="mum", student_id=w.sid, school_id="school_1", relation="mother", created_by="p")
    exam = {"exam": "Half-yearly", "subject": "Maths", "start": "09:00", "end": "12:00"}
    w.store.set_settings("mum", quiet_start="11:00", quiet_end="13:00")
    assert w.store.message_status(_notify(w, kind="exam_reminder", uid=w.sid, params=exam).id, "mum") == \
        {"whatsapp": "deferred"}, "noon is inside the parent's quiet hours, whatever the child's are"
    w.store.set_channel("mum", "holiday_declared", "push", False)
    holiday = {"label": "Diwali", "dates": "2026-11-08"}
    assert w.store.message_status(_notify(w, kind="holiday_declared", uid=w.sid, params=holiday).id, "mum") == {}
    w.store.set_digest("mum", "18:00")
    homework = {"title": "Map work", "due": "tomorrow"}
    assert w.store.message_status(_notify(w, kind="homework_due", uid=w.sid, params=homework).id, "mum") == {}


def test_only_next_action_kinds_go_and_the_persons_choices_hold(w):
    _confirmed(w, w.tid)
    assert w.store.message_status(_notify(w, kind="timetable_published").id) == {}, "not a messaging kind"
    assert w.store.message_status(_notify(w, now=NIGHT_IST, params={**SUB, "period": 5}).id) == \
        {"whatsapp": "deferred"}, "quiet hours"
    w.store.set_channel(w.tid, "exam_reminder", "push", False)
    assert w.store.message_status(_notify(w, kind="exam_reminder").id) == {}, "push for it is off"
    w.store.set_digest(w.tid, "18:00")
    assert w.store.message_status(_notify(w, kind="homework_due").id) == {}, "held for the digest"
    assert w.store.message_status(_notify(w, params={**SUB, "period": 6}).id) == {"whatsapp": "pending"}, \
        "a cover request never waits"


def test_the_same_notice_to_the_same_person_goes_once_a_day(w):
    _confirmed(w, w.tid)
    holiday = {"label": "Diwali", "dates": "2026-11-08", "moved": "3 Science lessons move"}
    first = _notify(w, kind="holiday_declared", params=holiday)
    again = _notify(w, kind="holiday_declared", params={**holiday, "moved": "2 Maths lessons move"})
    assert w.store.message_status(first.id) == {"whatsapp": "pending"}
    assert w.store.message_status(again.id) == {}, "a holiday is notified once per lesson plan it moves"
    later = _notify(w, kind="holiday_declared", params=holiday, now=NOON_IST + timedelta(days=1))
    assert w.store.message_status(later.id) == {"whatsapp": "pending"}


def test_withdrawing_consent_stops_what_is_waiting(w):
    _confirmed(w, w.tid, sms=True, whatsapp=True)
    n = _notify(w, now=NIGHT_IST)
    _consent(w, phone="9876543210", smsOk=True, whatsappOk=False)
    assert w.store.message_status(n.id) == {"sms": "deferred", "whatsapp": "skipped"}
    gone = w.c.put("/api/v1/me/contact", json={"phone": None}, headers=w.t).json()
    assert gone["phone"] is None
    assert w.store.message_status(n.id) == {"sms": "skipped", "whatsapp": "skipped"}


# --------------------------------------------------------------------- #
# Once, and retried with a wait
# --------------------------------------------------------------------- #

def test_a_failed_send_waits_before_each_retry_and_stops_after_the_third(w, monkeypatch):
    _whatsapp_on(monkeypatch)
    down = _Post(status=500, body={"error": "down"})
    monkeypatch.setattr("requests.post", down)
    _confirmed(w, w.tid)
    n = _notify(w)
    w.store.deliver_due(now=NOON_IST)
    row = _row(w, n)
    assert (row["status"], row["attempts"]) == ("failed", 1) and "500" in row["last_error"]
    w.store.deliver_due(now=NOON_IST + timedelta(minutes=1))
    assert len(down.calls) == 1, "not before its wait"
    w.store.deliver_due(now=NOON_IST + timedelta(minutes=3))
    assert len(down.calls) == 2 and _row(w, n)["attempts"] == 2
    w.store.deliver_due(now=NOON_IST + timedelta(minutes=10))
    assert len(down.calls) == 2, "the second wait is longer"
    w.store.deliver_due(now=NOON_IST + timedelta(minutes=20))
    row = _row(w, n)
    assert (row["status"], row["attempts"], row["next_at"]) == ("failed", 3, None)
    monkeypatch.setattr("requests.post", up := _Post())
    w.store.deliver_due(now=NOON_IST + timedelta(hours=2))
    assert up.calls == [] and _row(w, n)["status"] == "failed", "three tries in all"


def test_a_failure_then_success_is_sent_once(w, monkeypatch):
    _whatsapp_on(monkeypatch)
    monkeypatch.setattr("requests.post", _Post(status=500, body={"error": "down"}))
    _confirmed(w, w.tid)
    n = _notify(w)
    w.store.deliver_due(now=NOON_IST)
    monkeypatch.setattr("requests.post", up := _Post())
    w.store.deliver_due(now=NOON_IST + timedelta(minutes=3))
    w.store.deliver_due(now=NOON_IST + timedelta(minutes=30))
    assert w.store.message_status(n.id) == {"whatsapp": "sent"} and len(up.calls) == 1


def test_two_senders_at_once_send_a_message_once(w, monkeypatch):
    """notify()'s thread and a request can both find the same pending row;
    only the one that claims it first calls the provider."""
    _whatsapp_on(monkeypatch)
    post = _Post(delay=0.2)
    monkeypatch.setattr("requests.post", post)
    _confirmed(w, w.tid)
    n = _notify(w)
    both_read = threading.Barrier(2, timeout=5)
    real_claim = type(w.store)._claim

    def claim_together(self, row, now):
        both_read.wait()          # both senders have read the row as due
        return real_claim(self, row, now)
    monkeypatch.setattr(type(w.store), "_claim", claim_together)
    errors = []

    def send():
        try:
            w.store._deliver_messages(NOON_IST)
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)
    threads = [threading.Thread(target=send) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(10)
    assert errors == []
    assert len(post.whatsapp()) == 1
    assert w.store.message_status(n.id) == {"whatsapp": "sent"}


def test_a_send_interrupted_mid_call_is_not_sent_again(w, monkeypatch):
    _whatsapp_on(monkeypatch)
    post = _Post()
    monkeypatch.setattr("requests.post", post)
    _confirmed(w, w.tid)
    n = _notify(w)
    assert w.store._claim(_row(w, n), NOON_IST) is True     # a process claims it, then dies
    w.store.deliver_due(now=NOON_IST + timedelta(minutes=5))
    assert _row(w, n)["status"] == "sending", "a claim is left alone while it may still be running"
    w.store.deliver_due(now=NOON_IST + timedelta(minutes=16))
    row = _row(w, n)
    assert (row["status"], row["attempts"]) == ("failed", 3) and "may have gone" in row["last_error"]
    assert post.calls == []


def test_opening_the_inbox_does_not_wait_on_a_provider(w, monkeypatch):
    _whatsapp_on(monkeypatch)
    post = _Post()
    monkeypatch.setattr("requests.post", post)
    _confirmed(w, w.tid)
    later = []
    monkeypatch.setattr(type(w.store), "deliver_messages_soon", lambda self: later.append(True))
    n = _notify(w, now=datetime.now(timezone.utc) - timedelta(minutes=1))
    assert w.c.get("/api/v1/notifications", headers=w.t).status_code == 200
    assert post.calls == [] and later == [True], "handed to a background thread"
    assert w.store.message_status(n.id) != {"whatsapp": "sent"}


def test_a_parent_gives_their_number_the_route_is_open_to_parents(tmp_path, monkeypatch):
    """Parents may call only route_policy.PARENT_PATHS; the consent and
    confirmation routes are on it (a parent is who SMS and WhatsApp are
    mostly for)."""
    from test_guardians import _h, _parent
    from test_homework import w as homework_world

    gen = homework_world.__wrapped__(tmp_path, monkeypatch)
    hw = next(gen)
    try:
        mum = _h(_parent(hw))
        r = hw.c.put("/api/v1/me/contact", json={"phone": "9876543210", "whatsappOk": True}, headers=mum)
        assert r.status_code == 200, r.text
        assert hw.c.get("/api/v1/me/contact", headers=mum).json()["whatsappOk"] is True
        r = hw.c.post("/api/v1/me/contact/verify", json={"code": "123456"}, headers=mum)
        assert r.status_code == 422 and "ask for a code first" in r.json()["detail"], r.text
    finally:
        gen.close()
