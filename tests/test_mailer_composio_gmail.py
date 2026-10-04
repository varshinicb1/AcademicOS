"""Composio sends mail only through a connected Gmail account (2026-10-04).

The live key had five Google Calendar accounts and no Gmail. composio_status said "configured"
because the key worked, so the sign-in page offered emailed codes (`emailCode: true`) that could
never arrive, and every page load of the public sign-in page called Composio.
"""
from __future__ import annotations

import pytest

from academicos.assessment import mailer


@pytest.fixture
def composio(monkeypatch):
    monkeypatch.setenv("COMPOSIO_API_KEY", "ak_test_key_not_real_0123456789")
    mailer._status_cache.update(at=0.0, key="", value=None)
    calls = []
    state = {"accounts": []}

    def fake(method, path, **kw):
        calls.append((method, path, kw))
        if path.startswith("/connected_accounts"):
            return {"items": state["accounts"]}
        if path.startswith("/tools/execute/"):
            return {"successful": True, "data": {"id": "m1"}}
        raise AssertionError(path)
    monkeypatch.setattr(mailer, "_composio_request", fake)
    yield state, calls
    mailer._status_cache.update(at=0.0, key="", value=None)


def test_calendar_alone_is_not_an_email_sender(composio):
    state, _ = composio
    state["accounts"] = [{"id": "ca_cal", "status": "ACTIVE", "toolkit": {"slug": "googlecalendar"}}]
    status = mailer.composio_status()
    assert status["configured"] is False and "Gmail" in status["reason"]


def test_an_active_gmail_account_is_and_mail_goes_through_it(composio):
    state, calls = composio
    state["accounts"] = [{"id": "ca_gmail", "user_id": "pg-user-1", "status": "ACTIVE", "toolkit": {"slug": "gmail"}}]
    assert mailer.composio_status()["configured"] is True
    result = mailer.send_via_composio(mailer.MailMessage(to=["a@example.com"], subject="s", body="b"))
    assert result.ok
    execute = [kw for m, p, kw in calls if p.startswith("/tools/execute/")]
    assert execute[0]["json"]["connected_account_id"] == "ca_gmail"
    # Composio refuses an account id without its user id ("User ID is required with connected account").
    assert execute[0]["json"]["user_id"] == "pg-user-1"


def test_the_answer_is_cached_so_the_sign_in_page_does_not_call_composio_each_load(composio):
    state, calls = composio
    state["accounts"] = [{"id": "ca_gmail", "status": "ACTIVE", "toolkit": {"slug": "gmail"}}]
    for _ in range(5):
        mailer.composio_status()
    assert sum(1 for m, p, kw in calls if p.startswith("/connected_accounts")) == 1
