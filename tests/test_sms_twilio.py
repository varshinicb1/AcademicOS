"""INT-2: SMS goes out through Twilio (the owner's choice, 2026-11-14), with MSG91 kept as the other
provider. The credentials come from the environment, which config/secrets.env fills locally and
Secret Manager fills on Cloud Run; none is in the repository.

- With Twilio's account SID, auth token and a sender (a Messaging Service SID, or a From number or
  sender ID), SMS is "available" and a delivery is one POST to Twilio's Messages API: form fields
  To / Body / MessagingServiceSid (or From), basic auth with the SID and token.
- Without them, nothing leaves the server and the delivery is "skipped" with what is missing.
- Twilio refusing (4xx/5xx) is "failed" with its code, and retried like every channel.
- ACOS_SMS_PROVIDER picks one when both are set; with neither set, the missing names are Twilio's.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from academicos.operations import messaging

TWILIO = ("ACOS_TWILIO_ACCOUNT_SID", "ACOS_TWILIO_AUTH_TOKEN", "ACOS_TWILIO_MESSAGING_SERVICE_SID",
          "ACOS_TWILIO_FROM", "ACOS_SMS_PROVIDER", "ACOS_SMS_AUTHKEY", "ACOS_SMS_TEMPLATE_ID")


class _Post:
    def __init__(self, status=201, body=None):
        self.calls, self.status = [], status
        self.body = body if body is not None else {"sid": "SM123", "status": "queued"}

    def __call__(self, url, data=None, json=None, headers=None, auth=None, timeout=None):
        self.calls.append(SimpleNamespace(url=url, data=data, json=json, headers=headers, auth=auth))
        return SimpleNamespace(status_code=self.status, text=str(self.body), content=b"x", json=lambda: self.body)


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    for v in TWILIO:
        monkeypatch.delenv(v, raising=False)


def _twilio(monkeypatch, **extra):
    monkeypatch.setenv("ACOS_TWILIO_ACCOUNT_SID", "AC_test_sid")
    monkeypatch.setenv("ACOS_TWILIO_AUTH_TOKEN", "test-token")
    for k, v in extra.items():
        monkeypatch.setenv(k, v)


def test_nothing_is_sent_and_the_twilio_names_are_given_until_it_is_set_up(monkeypatch):
    post = _Post()
    monkeypatch.setattr("requests.post", post)
    missing = messaging._configured("sms")
    assert missing and "ACOS_TWILIO_ACCOUNT_SID" in missing and "ACOS_TWILIO_AUTH_TOKEN" in missing
    status, err, pid = messaging.send_sms("+919876543210", "Homework due", "Light worksheet is due tomorrow.")
    assert (status, pid) == ("skipped", None) and "ACOS_TWILIO" in err
    assert post.calls == []


def test_a_sid_and_token_without_a_sender_is_not_set_up(monkeypatch):
    _twilio(monkeypatch)
    assert "ACOS_TWILIO_MESSAGING_SERVICE_SID or ACOS_TWILIO_FROM" in messaging._configured("sms")


def test_an_sms_is_one_post_to_twilios_messages_api(monkeypatch):
    _twilio(monkeypatch, ACOS_TWILIO_MESSAGING_SERVICE_SID="MG_service")
    post = _Post()
    monkeypatch.setattr("requests.post", post)
    assert messaging._configured("sms") is None
    status, err, pid = messaging.send_sms("+919876543210", "Homework due", "Light worksheet is due tomorrow.")
    assert (status, err, pid) == ("sent", None, "SM123")
    [call] = post.calls
    assert call.url == "https://api.twilio.com/2010-04-01/Accounts/AC_test_sid/Messages.json"
    assert call.auth == ("AC_test_sid", "test-token")
    assert call.data == {"To": "+919876543210", "MessagingServiceSid": "MG_service",
                         "Body": "Homework due: Light worksheet is due tomorrow."}


def test_a_from_number_or_sender_id_is_used_when_there_is_no_messaging_service(monkeypatch):
    _twilio(monkeypatch, ACOS_TWILIO_FROM="ACADOS")
    post = _Post()
    monkeypatch.setattr("requests.post", post)
    messaging.send_sms("+919876543210", "Exam tomorrow", "Science, 09:00-12:00.")
    assert post.calls[0].data["From"] == "ACADOS" and "MessagingServiceSid" not in post.calls[0].data


def test_a_long_message_is_cut_to_two_sms_parts(monkeypatch):
    _twilio(monkeypatch, ACOS_TWILIO_FROM="ACADOS")
    post = _Post()
    monkeypatch.setattr("requests.post", post)
    messaging.send_sms("+919876543210", "Notice", "x" * 1000)
    assert len(post.calls[0].data["Body"]) == messaging.SMS_LIMIT


def test_twilio_refusing_is_a_failure_with_its_code(monkeypatch):
    _twilio(monkeypatch, ACOS_TWILIO_FROM="ACADOS")
    monkeypatch.setattr("requests.post", _Post(status=400, body={"code": 21211, "message": "Invalid 'To' Phone Number"}))
    status, err, pid = messaging.send_sms("+919876543210", "t", "b")
    assert status == "failed" and pid is None and "400" in err and "21211" in err
    assert "test-token" not in err


def test_the_provider_can_be_chosen_and_msg91_still_works(monkeypatch):
    _twilio(monkeypatch, ACOS_TWILIO_FROM="ACADOS", ACOS_SMS_AUTHKEY="k", ACOS_SMS_TEMPLATE_ID="flow-1")
    assert messaging.sms_provider() == "twilio", "Twilio when its credentials are there"
    monkeypatch.setenv("ACOS_SMS_PROVIDER", "msg91")
    post = _Post(status=200, body={"type": "success", "message": "req-1"})
    monkeypatch.setattr("requests.post", post)
    assert messaging.send_sms("+919876543210", "t", "b") == ("sent", None, "req-1")
    assert post.calls[0].url == "https://control.msg91.com/api/v5/flow"


def test_msg91_alone_is_still_picked_without_a_setting(monkeypatch):
    monkeypatch.setenv("ACOS_SMS_AUTHKEY", "k")
    monkeypatch.setenv("ACOS_SMS_TEMPLATE_ID", "flow-1")
    assert messaging.sms_provider() == "msg91" and messaging._configured("sms") is None


def test_an_unknown_provider_is_refused_by_name(monkeypatch):
    monkeypatch.setenv("ACOS_SMS_PROVIDER", "carrier-pigeon")
    assert "ACOS_SMS_PROVIDER" in messaging._configured("sms")


def test_the_deployment_placeholder_is_not_a_credential(monkeypatch):
    _twilio(monkeypatch, ACOS_TWILIO_FROM="ACADOS")
    monkeypatch.setenv("ACOS_TWILIO_AUTH_TOKEN", "REPLACE_ME")
    assert "ACOS_TWILIO_AUTH_TOKEN" in messaging._configured("sms")
