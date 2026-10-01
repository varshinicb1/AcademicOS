"""API-6: webhooks for partners -- `questions.added`, signed, retried, and
never sent anywhere but a public HTTPS address, never for a revoked key, and
never about a question the key may not read.

The service is driven with an injected sender, DNS resolver and clock, so
nothing here touches the network. The last group goes through the routes a
principal uses on the web (register, list, revoke, the delivery log).
"""
from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from academicos.assessment import webhooks
from academicos.assessment.api_keys import ApiKeyStore
from academicos.assessment.qbank_engine import QuestionBank
from academicos.assessment.webhooks import (
    BACKOFF_SECONDS, MAX_ATTEMPTS, SIGNATURE_HEADER, UnsafeWebhookUrl, WebhookError, WebhookService,
    WebhookStore, check_url, is_public_address, sign, signature_header, verify_signature,
)

PUBLIC_IP = "93.184.216.34"
KEYED = {"totalMarks": 1, "provenance": "cbse_marking_scheme",
         "markingPoints": [{"id": "mp1", "description": "the answer", "marks": 1}]}


def _rec(i: int, *, subject: str = "Science", grade: int = 10, chapter: str = "life-processes",
         keyed: bool = True) -> dict[str, Any]:
    return {"id": f"q{i:04d}", "subject": subject, "grade": grade, "marks": 1, "type": "very_short_answer",
            "stem": f"Stem text {i} that must never be pushed", "chapterIds": [chapter],
            "answerScheme": dict(KEYED) if keyed else {"totalMarks": 1, "markingPoints": []}}


class Wire:
    """The fake network: a resolver from a dict, and a sender that records
    every request and answers with the next scripted status (or raises)."""

    def __init__(self) -> None:
        self.dns: dict[str, list[str]] = {"partner.example": [PUBLIC_IP]}
        self.sent: list[dict[str, Any]] = []
        self.answers: list[Any] = []

    def resolve(self, host: str, port: int) -> list[str]:
        if host not in self.dns:
            raise OSError("no such host")
        return list(self.dns[host])

    def send(self, url: str, address: str, body: bytes, headers: dict[str, str],
             timeout: tuple[float, float]) -> int:
        self.sent.append({"url": url, "address": address, "body": body, "headers": headers, "timeout": timeout})
        answer = self.answers.pop(0) if self.answers else 200
        if isinstance(answer, Exception):
            raise answer
        return answer


class Clock:
    def __init__(self) -> None:
        self.now = datetime.now(timezone.utc).replace(microsecond=0)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


@pytest.fixture
def svc(tmp_path: Path, monkeypatch):
    # No school has rejected anything unless a test says so.
    rejected: dict[str, frozenset[str]] = {}
    monkeypatch.setattr(webhooks, "_rejected_for", lambda school: rejected.get(school, frozenset()))
    wire, clock = Wire(), Clock()
    keys = ApiKeyStore(tmp_path / "keys.sqlite")
    service = WebhookService(WebhookStore(tmp_path / "webhooks.sqlite"), keys, sender=wire.send,
                             resolver=wire.resolve, clock=clock, background=False)
    service.wire, service.clock_, service.rejected = wire, clock, rejected
    return service


def _key(svc, *, school: str = "school_1", scopes=("questions:read",), grades=(), subjects=()):
    _, key = svc.keys.create(school_id=school, scopes=list(scopes), grades=grades, subjects=subjects)
    return key


def _hook(svc, key, url: str = "https://partner.example/hooks/acos"):
    return svc.register(key, url=url, events=["questions.added"], created_by="user_p")


def _payloads(svc) -> list[dict[str, Any]]:
    return [json.loads(s["body"]) for s in svc.wire.sent]


# --------------------------------------------------------------------------- signing

def test_a_delivery_is_signed_with_hmac_sha256_over_the_timestamp_and_the_raw_body(svc):
    key = _key(svc)
    secret, hook = _hook(svc, key)
    assert secret.startswith("whsec_") and hook["secret"] == secret
    svc.on_bank_loaded(QuestionBank([_rec(1)]))
    svc.on_bank_loaded(QuestionBank([_rec(1), _rec(2)]))
    assert svc.deliver_due()["delivered"] == 1
    sent = svc.wire.sent[0]
    header = sent["headers"][SIGNATURE_HEADER]
    t, v1 = (part.split("=", 1)[1] for part in header.split(","))
    assert header == f"t={t},v1={v1}"
    expected = hmac.new(secret.encode(), f"{t}.".encode() + sent["body"], hashlib.sha256).hexdigest()
    assert v1 == expected == sign(secret, int(t), sent["body"])
    assert int(t) == int(svc.clock_.now.timestamp())
    assert verify_signature(secret, header, sent["body"], now=int(t))
    assert sent["headers"]["X-AcademicOS-Event"] == "questions.added"
    assert sent["headers"]["Content-Type"] == "application/json"


def test_a_receiver_refuses_a_forged_tampered_or_replayed_request():
    body = b'{"type":"questions.added"}'
    header = signature_header("whsec_right", body, 1_000_000)
    assert verify_signature("whsec_right", header, body, now=1_000_000)
    assert not verify_signature("whsec_wrong", header, body, now=1_000_000)
    assert not verify_signature("whsec_right", header, body + b" ", now=1_000_000)
    assert not verify_signature("whsec_right", header, body, now=1_000_000 + 301)   # replayed later
    assert not verify_signature("whsec_right", "v1=abc", body, now=1_000_000)       # no timestamp
    assert not verify_signature("whsec_right", "", body, now=1_000_000)


# --------------------------------------------------------------------------- SSRF

@pytest.mark.parametrize("address", [
    "127.0.0.1", "10.1.2.3", "172.16.0.1", "192.168.1.1", "169.254.169.254", "169.254.1.1", "100.64.0.1",
    "0.0.0.0", "224.0.0.1", "255.255.255.255", "240.0.0.1", "::1", "fe80::1", "fc00::1", "fd00:ec2::254",
    "::ffff:127.0.0.1", "::ffff:10.0.0.1", "64:ff9b::a00:1", "2002:a00:1::", "::", "2001:db8::1",
])
def test_private_loopback_link_local_and_metadata_addresses_are_not_public(address):
    assert not is_public_address(address)


def test_a_public_address_is(svc):
    assert is_public_address(PUBLIC_IP) and is_public_address("2606:4700:4700::1111")


@pytest.mark.parametrize("url,why", [
    ("http://partner.example/hook", "https"),
    ("ftp://partner.example/hook", "https"),
    ("https://user:pw@partner.example/hook", "user name"),
    ("https://localhost/hook", "internal"),
    ("https://api.localhost/hook", "internal"),
    ("https://metadata.google.internal/computeMetadata/v1/", "internal"),
    ("https://127.0.0.1/hook", "127.0.0.1"),
    ("https://169.254.169.254/latest/meta-data/", "169.254.169.254"),
    ("https://[::1]/hook", "::1"),
    ("https://10.0.0.8:8443/hook", "10.0.0.8"),
    ("https://unknown.example/hook", "does not resolve"),
    ("https://rebind.example/hook", "192.168.0.10"),
    ("https://split.example/hook", "10.9.9.9"),
])
def test_unsafe_urls_are_refused_at_registration(svc, url, why):
    svc.wire.dns["rebind.example"] = ["192.168.0.10"]
    svc.wire.dns["split.example"] = [PUBLIC_IP, "10.9.9.9"]     # one public, one private: refused
    with pytest.raises(UnsafeWebhookUrl) as e:
        _hook(svc, _key(svc), url)
    assert why in str(e.value)


def test_check_url_answers_the_checked_addresses(svc):
    assert check_url("https://partner.example:8443/x?y=1", svc.wire.resolve) == ("partner.example", 8443, [PUBLIC_IP])


def test_a_name_repointed_at_a_private_address_after_registration_is_not_called(svc):
    """DNS rebinding: the name was public when registered; at send time it
    resolves to the metadata server. Nothing is sent, and the attempt says why."""
    key = _key(svc)
    _hook(svc, key)
    svc.on_bank_loaded(QuestionBank([_rec(1)]))
    svc.on_bank_loaded(QuestionBank([_rec(1), _rec(2)]))
    svc.wire.dns["partner.example"] = ["169.254.169.254"]
    assert svc.deliver_due() == {"delivered": 0, "retrying": 1, "failed": 0, "cancelled": 0}
    assert svc.wire.sent == []
    [d] = svc.store.deliveries(svc.store.for_key(key.id)[0]["id"])
    assert d["status"] == "pending" and d["attempts"] == 1 and "169.254.169.254" in d["last_error"]
    # ...and the send goes to the address that was just checked
    svc.wire.dns["partner.example"] = [PUBLIC_IP]
    svc.clock_.advance(BACKOFF_SECONDS[0] + 1)
    assert svc.deliver_due()["delivered"] == 1
    assert svc.wire.sent[0]["address"] == PUBLIC_IP
    assert svc.wire.sent[0]["timeout"] == (webhooks.CONNECT_TIMEOUT, webhooks.READ_TIMEOUT)


# --------------------------------------------------------------------------- registration

def test_registration_needs_a_live_key_that_can_read_questions_and_a_known_event(svc):
    with pytest.raises(WebhookError, match="questions:read"):
        _hook(svc, _key(svc, scopes=("facets:read",)))
    key = _key(svc)
    with pytest.raises(WebhookError, match="unknown event"):
        svc.register(key, url="https://partner.example/h", events=["students.updated"], created_by="p")
    svc.keys.revoke(key.id)
    with pytest.raises(WebhookError, match="revoked"):
        _hook(svc, svc.keys.get(key.id))


# --------------------------------------------------------------------------- the trigger and scope

def test_the_first_load_announces_nothing_and_later_loads_announce_new_ids_per_chapter(svc):
    key = _key(svc)
    _hook(svc, key)
    first = [_rec(1), _rec(2, chapter="cell-structure")]
    assert svc.on_bank_loaded(QuestionBank(first)) == 0
    bank = QuestionBank(first + [_rec(3), _rec(4), _rec(5, chapter="cell-structure"),
                                 _rec(6, keyed=False)])           # no answer key: not served, not announced
    assert svc.on_bank_loaded(bank) == 2
    assert svc.on_bank_loaded(bank) == 0                           # nothing new the second time
    svc.deliver_due()
    events = {p["data"]["chapterId"]: p["data"] for p in _payloads(svc)}
    by_chapter: dict[str, list[str]] = {}
    for r in bank.records:
        if r["id"] in ("q0003", "q0004", "q0005"):
            by_chapter.setdefault(bank.chapter_of(r), []).append(r["id"])
    assert {c: sorted(d["questionIds"]) for c, d in events.items()} == by_chapter
    assert all(d["reason"] == "bank_updated" and d["count"] == len(d["questionIds"]) for d in events.values())


def test_an_event_carries_ids_and_taxonomy_only_never_text_or_people(svc):
    _hook(svc, _key(svc))
    svc.on_bank_loaded(QuestionBank([_rec(1)]))
    svc.on_bank_loaded(QuestionBank([_rec(1), _rec(2)]))
    svc.deliver_due()
    [payload] = _payloads(svc)
    assert set(payload) == {"id", "type", "createdAt", "data"}
    assert set(payload["data"]) == {"subject", "grade", "chapterId", "questionIds", "count", "reason"}
    assert "Stem text" not in svc.wire.sent[0]["body"].decode()
    assert payload["data"]["questionIds"] == ["q0002"] and payload["type"] == "questions.added"


def test_a_key_hears_only_of_the_classes_and_subjects_it_may_read(svc):
    narrow = _key(svc, grades=[10], subjects=["Science"])
    wide = _key(svc, school="school_2")
    _hook(svc, narrow, "https://partner.example/narrow")
    _hook(svc, wide, "https://partner.example/wide")
    svc.on_bank_loaded(QuestionBank([_rec(1)]))
    svc.on_bank_loaded(QuestionBank([_rec(1), _rec(2), _rec(3, subject="Mathematics", chapter="real-numbers"),
                                     _rec(4, grade=9, chapter="tissues")]))
    svc.deliver_due()
    got: dict[str, set[str]] = {}
    for s in svc.wire.sent:
        got.setdefault(s["url"].rsplit("/", 1)[1], set()).update(json.loads(s["body"])["data"]["questionIds"])
    assert got == {"narrow": {"q0002"}, "wide": {"q0002", "q0003", "q0004"}}


def test_a_question_the_schools_reviewer_rejected_is_not_announced_to_its_partners(svc):
    _hook(svc, _key(svc, school="school_1"), "https://partner.example/one")
    _hook(svc, _key(svc, school="school_2"), "https://partner.example/two")
    svc.rejected["school_1"] = frozenset({"q0002"})
    svc.on_bank_loaded(QuestionBank([_rec(1)]))
    svc.on_bank_loaded(QuestionBank([_rec(1), _rec(2)]))
    svc.deliver_due()
    assert [s["url"] for s in svc.wire.sent] == ["https://partner.example/two"]


def test_a_review_that_takes_back_a_rejection_announces_the_question_to_that_school_only(svc):
    _hook(svc, _key(svc, school="school_1"), "https://partner.example/one")
    _hook(svc, _key(svc, school="school_2"), "https://partner.example/two")
    bank = QuestionBank([_rec(1), _rec(2)])
    svc.on_bank_loaded(bank)
    # a first approval adds nothing: /v1 serves a checked answer already
    assert svc.on_review_decision(bank, school_id="school_1", question_id="q0001", before=None,
                                  after="approved") == 0
    assert svc.on_review_decision(bank, school_id="school_1", question_id="q0001", before="approved",
                                  after="rejected") == 0
    assert svc.on_review_decision(bank, school_id="school_1", question_id="q0001", before="rejected",
                                  after="approved") == 1
    svc.deliver_due()
    [sent] = svc.wire.sent
    assert sent["url"] == "https://partner.example/one"
    data = json.loads(sent["body"])["data"]
    assert data["questionIds"] == ["q0001"] and data["reason"] == "review_approved"


# --------------------------------------------------------------------------- retries

def test_a_failed_send_is_retried_with_backoff_and_logged(svc):
    key = _key(svc)
    _hook(svc, key)
    svc.wire.answers = [500, ConnectionError("connection reset"), 200]
    svc.on_bank_loaded(QuestionBank([_rec(1)]))
    svc.on_bank_loaded(QuestionBank([_rec(1), _rec(2)]))
    hook_id = svc.store.for_key(key.id)[0]["id"]

    assert svc.deliver_due()["retrying"] == 1
    [d] = svc.store.deliveries(hook_id)
    assert (d["status"], d["attempts"], d["last_status_code"]) == ("pending", 1, 500)
    assert d["next_attempt_at"] == (svc.clock_.now + timedelta(seconds=BACKOFF_SECONDS[0])).isoformat()
    assert svc.deliver_due()["retrying"] == 0, "not due again before its backoff"

    svc.clock_.advance(BACKOFF_SECONDS[0])
    assert svc.deliver_due()["retrying"] == 1
    [d] = svc.store.deliveries(hook_id)
    assert d["attempts"] == 2 and "connection reset" in d["last_error"]
    assert d["next_attempt_at"] == (svc.clock_.now + timedelta(seconds=BACKOFF_SECONDS[1])).isoformat()

    svc.clock_.advance(BACKOFF_SECONDS[1])
    assert svc.deliver_due()["delivered"] == 1
    [d] = svc.store.deliveries(hook_id)
    assert (d["status"], d["attempts"], d["last_status_code"], d["last_error"]) == ("delivered", 3, 200, "")
    # the same signed body every time, so a receiver can de-duplicate on the delivery header
    assert len({s["body"] for s in svc.wire.sent}) == 1
    assert len({s["headers"]["X-AcademicOS-Delivery"] for s in svc.wire.sent}) == 1


def test_a_send_that_never_succeeds_fails_after_the_last_attempt(svc):
    key = _key(svc)
    _hook(svc, key)
    svc.wire.answers = [503] * MAX_ATTEMPTS
    svc.on_bank_loaded(QuestionBank([_rec(1)]))
    svc.on_bank_loaded(QuestionBank([_rec(1), _rec(2)]))
    for wait in (0, *BACKOFF_SECONDS):
        svc.clock_.advance(wait)
        svc.deliver_due()
    [d] = svc.store.deliveries(svc.store.for_key(key.id)[0]["id"])
    assert (d["status"], d["attempts"]) == ("failed", MAX_ATTEMPTS)
    assert len(svc.wire.sent) == MAX_ATTEMPTS
    svc.clock_.advance(10 ** 6)
    svc.deliver_due()
    assert len(svc.wire.sent) == MAX_ATTEMPTS


# --------------------------------------------------------------------------- revoked

def test_nothing_is_delivered_for_a_revoked_key(svc):
    key = _key(svc)
    _hook(svc, key)
    svc.on_bank_loaded(QuestionBank([_rec(1)]))
    svc.on_bank_loaded(QuestionBank([_rec(1), _rec(2)]))       # an event waits
    svc.keys.revoke(key.id)
    assert svc.deliver_due() == {"delivered": 0, "retrying": 0, "failed": 0, "cancelled": 1}
    assert svc.wire.sent == []
    [d] = svc.store.deliveries(svc.store.for_key(key.id)[0]["id"])
    assert d["status"] == "cancelled" and "revoked" in d["last_error"]
    # and no new event is made for it
    assert svc.on_bank_loaded(QuestionBank([_rec(1), _rec(2), _rec(3)])) == 0


def test_a_revoked_webhook_cancels_what_it_had_not_delivered(svc):
    key = _key(svc)
    _, hook = _hook(svc, key)
    svc.on_bank_loaded(QuestionBank([_rec(1)]))
    svc.on_bank_loaded(QuestionBank([_rec(1), _rec(2)]))
    svc.store.revoke(hook["id"], revoked_by="user_p")
    assert svc.deliver_due()["delivered"] == 0
    assert svc.wire.sent == []
    assert svc.store.deliveries(hook["id"])[0]["status"] == "cancelled"


# --------------------------------------------------------------------------- the routes

@pytest.fixture
def web(tmp_path_factory, monkeypatch):
    """A booted app with two schools' principals, each with a key; the live
    webhook service gets the fake wire."""
    import uuid

    from fastapi.testclient import TestClient

    from academicos.api.main import app
    from academicos.assessment import audit_log
    from academicos.assessment import users as users_mod
    from academicos.curriculum import store as curriculum_store_mod

    from _auth_helpers import PASSWORD

    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path_factory.mktemp("webhooks_web")))
    monkeypatch.setenv("ACOS_PRINCIPAL_BOOTSTRAP_KEY", "webhooks-bootstrap")
    monkeypatch.setattr(audit_log, "_INSTANCE", None)
    monkeypatch.setattr(users_mod, "_INSTANCE", None)
    monkeypatch.setattr(curriculum_store_mod, "_INSTANCE", None)
    with TestClient(app) as client:
        wire = Wire()
        live = webhooks.service()
        monkeypatch.setattr(live, "resolver", wire.resolve)
        monkeypatch.setattr(live, "sender", wire.send)
        monkeypatch.setattr(live, "background", False)
        tag = uuid.uuid4().hex[:6]
        heads = []
        for school in ("w1", "w2"):
            r = client.post("/api/v1/auth/register", json={
                "schoolId": f"{school}_{tag}", "name": "P", "email": f"{school}-{tag}@example.com",
                "password": PASSWORD, "principalKey": "webhooks-bootstrap"})
            assert r.status_code == 200, r.text
            heads.append({"Authorization": f"Bearer {r.json()['token']}"})
        key = client.post("/api/v1/api-keys", json={"label": "Partner LMS", "scopes": ["questions:read"]},
                          headers=heads[0])
        assert key.status_code == 200, key.text
        yield client, heads, key.json()["id"], wire, live


def test_a_principal_registers_lists_and_revokes_a_webhook_and_reads_its_log(web):
    from academicos.assessment.audit_log import get_audit_log
    from academicos.assessment import auth_routes
    client, (mine, other), key_id, wire, live = web
    base = f"/api/v1/api-keys/{key_id}/webhooks"
    bad = client.post(base, json={"url": "https://169.254.169.254/latest"}, headers=mine)
    assert bad.status_code == 422 and "public address" in bad.json()["detail"]
    made = client.post(base, json={"url": "https://partner.example/acos"}, headers=mine)
    assert made.status_code == 200, made.text
    hook = made.json()
    assert hook["secret"].startswith("whsec_") and hook["events"] == ["questions.added"] and hook["active"]
    listed = client.get(base, headers=mine)
    assert listed.status_code == 200 and "secret" not in listed.json()[0]
    assert hook["secret"] not in listed.text and listed.json()[0]["secretHint"] == hook["secretHint"]
    # another school's principal cannot see or touch it
    assert client.get(base, headers=other).status_code == 404
    assert client.delete(f"{base}/{hook['id']}", headers=other).status_code == 404

    live.on_bank_loaded(QuestionBank([_rec(1)]))
    live.on_bank_loaded(QuestionBank([_rec(1), _rec(2)]))
    wire.answers = [502]
    live.deliver_due()
    log = client.get(f"{base}/{hook['id']}/deliveries", headers=mine)
    assert log.status_code == 200, log.text
    [d] = log.json()
    assert (d["status"], d["attempts"], d["lastStatusCode"], d["questionCount"]) == ("pending", 1, 502, 1)
    assert d["nextAttemptAt"] and "502" in d["lastError"]
    assert verify_signature(hook["secret"], wire.sent[0]["headers"][SIGNATURE_HEADER], wire.sent[0]["body"],
                            now=int(live.clock().timestamp()))

    gone = client.delete(f"{base}/{hook['id']}", headers=mine)
    assert gone.status_code == 200 and gone.json()["active"] is False
    assert client.get(f"{base}/{hook['id']}/deliveries", headers=mine).json()[0]["status"] == "cancelled"
    log_ = get_audit_log(auth_routes._cfg.data_root)
    assert log_.for_action("webhook_created") and log_.for_action("webhook_revoked")


def test_revoking_the_key_stops_its_webhooks(web):
    client, (mine, _), key_id, wire, live = web
    base = f"/api/v1/api-keys/{key_id}/webhooks"
    hook = client.post(base, json={"url": "https://partner.example/acos"}, headers=mine).json()
    assert client.delete(f"/api/v1/api-keys/{key_id}", headers=mine).status_code == 200
    assert client.get(base, headers=mine).json()[0]["active"] is False
    live.on_bank_loaded(QuestionBank([_rec(1)]))
    live.on_bank_loaded(QuestionBank([_rec(1), _rec(2)]))
    live.deliver_due()
    assert wire.sent == [] and live.store.deliveries(hook["id"]) == []


# --------------------------------------------------------------------------- the docs

DOC = Path(__file__).resolve().parents[1] / "docs" / "question-bank-api.md"


def _doc_block(lang: str, needle: str) -> str:
    import re
    for block in re.findall(rf"```{lang}\n(.*?)```", DOC.read_text(encoding="utf-8"), flags=re.S):
        if needle in block:
            return block
    raise AssertionError(f"no {lang} block with {needle!r} in {DOC.name}")


def _doc_example() -> tuple[str, bytes]:
    """The worked example's signature header and body, as the doc prints them."""
    block = _doc_block("http", "X-AcademicOS-Signature")
    head, body = block.split("\n\n", 1)
    header = next(line.split(": ", 1)[1] for line in head.splitlines() if line.startswith(SIGNATURE_HEADER))
    return header, body.strip().encode("utf-8")


def test_the_docs_worked_example_is_a_real_signature():
    header, body = _doc_example()
    t = int(header.split(",")[0].split("=")[1])
    assert verify_signature("whsec_test_only", header, body, now=t)
    assert not verify_signature("whsec_other", header, body, now=t)


def test_the_docs_python_verifier_agrees_with_the_server():
    namespace: dict[str, Any] = {}
    exec(_doc_block("python", "def verify("), namespace)     # noqa: S102 - our own documentation
    header, body = _doc_example()
    assert namespace["verify"]("whsec_test_only", header, body, tolerance=10 ** 10)
    assert not namespace["verify"]("whsec_test_only", header, body + b" ", tolerance=10 ** 10)
    fresh = b'{"type":"questions.added"}'
    assert namespace["verify"]("whsec_x", signature_header("whsec_x", fresh, int(__import__("time").time())), fresh)


def test_the_docs_javascript_verifier_agrees_with_the_server():
    import shutil
    import subprocess
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    header, body = _doc_example()
    script = (_doc_block("javascript", "function verify(")
              + f"\nconst ok = verify('whsec_test_only', {json.dumps(header)}, Buffer.from({json.dumps(body.decode())}), 1e12);"
              + f"\nconst bad = verify('whsec_test_only', {json.dumps(header)}, Buffer.from({json.dumps(body.decode() + ' ')}), 1e12);"
              + "\nprocess.stdout.write(JSON.stringify([ok, bad]));")
    out = subprocess.run([node, "-e", script], capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    assert json.loads(out.stdout) == [True, False]


def test_the_bank_reload_and_the_review_queue_trigger_events_through_the_app(web, tmp_path, monkeypatch):
    """The two places the served bank changes, as the running app wires them:
    qbank_routes.load_bank (startup and any reload) and the school's review
    queue (POST /api/v1/qbank/review/{id})."""
    from academicos.assessment import qbank_routes
    monkeypatch.setattr(qbank_routes, "_bank", qbank_routes._bank)    # put back whatever was loaded
    client, (mine, _), key_id, wire, live = web
    hook = client.post(f"/api/v1/api-keys/{key_id}/webhooks", json={"url": "https://partner.example/acos"},
                       headers=mine).json()

    def write(records):
        path = tmp_path / "questions.json"
        path.write_text(json.dumps({"questions": records}), encoding="utf-8")
        return path

    qbank_routes.load_bank(write([_rec(1), _rec(2)]))               # the first load: recorded, not announced
    live.deliver_due()
    assert wire.sent == []
    qbank_routes.load_bank(write([_rec(1), _rec(2), _rec(3)]))       # a reload with one new question
    live.deliver_due()
    assert [json.loads(s["body"])["data"]["questionIds"] for s in wire.sent] == [["q0003"]]

    review = "/api/v1/qbank/review/q0001"
    assert client.post(review, json={"decision": "approved"}, headers=mine).status_code == 200
    live.deliver_due()
    assert len(wire.sent) == 1, "a first approval adds nothing /v1 did not already serve"
    assert client.post(review, json={"decision": "rejected"}, headers=mine).status_code == 200
    assert client.post(review, json={"decision": "approved"}, headers=mine).status_code == 200
    live.deliver_due()
    last = json.loads(wire.sent[-1]["body"])["data"]
    assert (len(wire.sent), last["questionIds"], last["reason"]) == (2, ["q0001"], "review_approved")
    assert [d["status"] for d in client.get(f"/api/v1/api-keys/{key_id}/webhooks/{hook['id']}/deliveries",
                                            headers=mine).json()] == ["delivered", "delivered"]
