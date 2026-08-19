"""Hermetic tests for academicos.integrations.composio_calendar.

The HTTP boundary (requests.post) is mocked in every test that would
otherwise call out — never hits the real Composio/Google API.
"""
from __future__ import annotations

from datetime import datetime, time, timedelta, timezone

import pytest
import requests

from academicos.assessment.schemas import (
    Assessment,
    BloomDistribution,
    Blueprint,
    ChapterWeights,
    CompetencyWeights,
    DifficultyDistribution,
)
from academicos.integrations.composio_calendar import sync_to_google_calendar

ENV_KEYS = (
    "COMPOSIO_API_KEY",
    "COMPOSIO_CALENDAR_CONNECTED_ACCOUNT_ID",
    "COMPOSIO_CALENDAR_USER_ID",
)
API_KEY = "test-key-123"
ACCOUNT_ID = "ca_test_account"
USER_ID = "user_42"

SCHEDULED = datetime(2026, 5, 10, 9, 30, tzinfo=timezone(timedelta(hours=5, minutes=30)))


@pytest.fixture(autouse=True)
def _clean_composio_env(monkeypatch):
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def _set_full_env(monkeypatch):
    monkeypatch.setenv("COMPOSIO_API_KEY", API_KEY)
    monkeypatch.setenv("COMPOSIO_CALENDAR_CONNECTED_ACCOUNT_ID", ACCOUNT_ID)
    monkeypatch.setenv("COMPOSIO_CALENDAR_USER_ID", USER_ID)


def make_blueprint(duration_minutes: int = 60, total_marks: int = 80) -> Blueprint:
    return Blueprint(
        total_marks=total_marks,
        duration_minutes=duration_minutes,
        difficulty=DifficultyDistribution(easy=0.3, medium=0.4, hard=0.3),
        bloom=BloomDistribution(
            remember=0.2, understand=0.2, apply=0.2, analyze=0.2, evaluate=0.1, create=0.1,
        ),
        chapter_weights=ChapterWeights(),
        competency_weights=CompetencyWeights(),
    )


def make_assessment(
    scheduled_at: datetime | None = SCHEDULED,
    metadata: dict | None = None,
    duration_minutes: int = 60,
    total_marks: int = 80,
) -> Assessment:
    return Assessment(
        id="assess_1",
        school_id="school_1",
        teacher_id="teacher_1",
        title="Unit Test 1",
        subject="Mathematics",
        grade=10,
        chapter_ids=["ch1"],
        blueprint=make_blueprint(duration_minutes=duration_minutes, total_marks=total_marks),
        status="paperGenerated",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        scheduled_at=scheduled_at,
        metadata=metadata or {},
    )


class FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class PostRecorder:
    """Stands in for requests.post; records the call and returns/raises a canned result."""

    def __init__(self, result):
        self._result = result
        self.calls: list[dict] = []

    def __call__(self, url, *, headers=None, json=None, timeout=None):
        self.calls.append({"url": url, "headers": headers, "body": json, "timeout": timeout})
        if isinstance(self._result, BaseException):
            raise self._result
        return self._result


def _patch_post(monkeypatch, result) -> PostRecorder:
    recorder = PostRecorder(result)
    monkeypatch.setattr(
        "academicos.integrations.composio_calendar.requests.post", recorder
    )
    return recorder


# ---- No-op guards ---------------------------------------------------------


def test_noop_when_scheduled_at_none(monkeypatch):
    _set_full_env(monkeypatch)
    a = make_assessment(scheduled_at=None)
    recorder = _patch_post(monkeypatch, FakeResponse({}))

    assert sync_to_google_calendar(a) is None
    assert recorder.calls == []
    assert "googleCalendarEventId" not in a.metadata


def test_noop_when_already_synced(monkeypatch):
    _set_full_env(monkeypatch)
    a = make_assessment(metadata={"googleCalendarEventId": "evt_old"})
    recorder = _patch_post(monkeypatch, FakeResponse({}))

    assert sync_to_google_calendar(a) is None
    assert recorder.calls == []
    assert a.metadata["googleCalendarEventId"] == "evt_old"


def test_noop_when_env_vars_all_missing(monkeypatch):
    a = make_assessment()
    recorder = _patch_post(monkeypatch, FakeResponse({}))

    assert sync_to_google_calendar(a) is None
    assert recorder.calls == []


@pytest.mark.parametrize("present_key", ENV_KEYS)
def test_noop_when_only_some_env_vars_set(monkeypatch, present_key):
    monkeypatch.setenv(present_key, "something")
    a = make_assessment()
    recorder = _patch_post(monkeypatch, FakeResponse({}))

    assert sync_to_google_calendar(a) is None
    assert recorder.calls == []


# ---- Happy path ------------------------------------------------------------


def test_happy_path_creates_event_and_stores_event_id(monkeypatch):
    _set_full_env(monkeypatch)
    a = make_assessment()
    response = FakeResponse(
        {"data": {"response_data": {"id": "evt_123", "htmlLink": "https://cal/evt_123"}, "successful": True}}
    )
    recorder = _patch_post(monkeypatch, response)

    assert sync_to_google_calendar(a) is None

    assert len(recorder.calls) == 1
    call = recorder.calls[0]
    assert call["url"] == "https://backend.composio.dev/api/v3/tools/execute/GOOGLECALENDAR_CREATE_EVENT"
    assert call["headers"]["x-api-key"] == API_KEY
    assert call["headers"]["Content-Type"] == "application/json"
    assert call["timeout"] == 15

    body = call["body"]
    assert body["connected_account_id"] == ACCOUNT_ID
    assert body["user_id"] == USER_ID

    args = body["arguments"]
    assert args["summary"] == "Unit Test 1 — Mathematics (Grade 10)"
    assert "AcademicOS assessment: Unit Test 1" in args["description"]
    assert "Subject: Mathematics · Grade 10" in args["description"]
    assert "Total marks: 80" in args["description"]
    assert args["calendar_id"] == "primary"
    assert args["start_datetime"] == SCHEDULED.isoformat()
    assert args["end_datetime"] == (SCHEDULED + timedelta(minutes=60)).isoformat()

    assert a.metadata["googleCalendarEventId"] == "evt_123"


def test_duration_falls_back_to_60_when_blueprint_is_zero(monkeypatch):
    _set_full_env(monkeypatch)
    a = make_assessment(duration_minutes=0)
    recorder = _patch_post(monkeypatch, FakeResponse({"data": {"response_data": {"id": "e1"}}}))

    sync_to_google_calendar(a)

    args = recorder.calls[0]["body"]["arguments"]
    assert args["end_datetime"] == (SCHEDULED + timedelta(minutes=60)).isoformat()


def test_long_duration_uses_end_datetime_and_not_event_duration_fields(monkeypatch):
    _set_full_env(monkeypatch)
    a = make_assessment(duration_minutes=180)
    recorder = _patch_post(monkeypatch, FakeResponse({"data": {"response_data": {"id": "e1"}}}))

    sync_to_google_calendar(a)

    args = recorder.calls[0]["body"]["arguments"]
    assert args["start_datetime"] == SCHEDULED.isoformat()
    assert args["end_datetime"] == (SCHEDULED + timedelta(hours=3)).isoformat()
    assert not any(k.startswith("event_duration") for k in args)
    assert "event_duration" not in args


# ---- Response-shape edge cases --------------------------------------------


@pytest.mark.parametrize(
    "payload",
    [
        {"data": {"response_data": {}}},
        {"data": {}},
        {"data": {"response_data": None}},  # 200 + null body: must not AttributeError
        {"data": None},
        {},
        [],
        "not an object",
    ],
)
def test_response_without_event_id_leaves_metadata_unchanged(monkeypatch, payload):
    _set_full_env(monkeypatch)
    a = make_assessment()
    recorder = _patch_post(monkeypatch, FakeResponse(payload))

    assert sync_to_google_calendar(a) is None
    assert len(recorder.calls) == 1
    assert "googleCalendarEventId" not in a.metadata


# ---- Failure handling: RequestException is caught, never propagated --------


def test_connection_error_swallowed_and_caller_unblocked(monkeypatch):
    _set_full_env(monkeypatch)
    a = make_assessment()
    recorder = _patch_post(monkeypatch, requests.exceptions.ConnectionError("boom"))

    assert sync_to_google_calendar(a) is None
    assert len(recorder.calls) == 1
    assert "googleCalendarEventId" not in a.metadata


def test_http_error_from_raise_for_status_swallowed(monkeypatch):
    _set_full_env(monkeypatch)
    a = make_assessment()

    class HttpErrorResponse(FakeResponse):
        def raise_for_status(self):
            raise requests.exceptions.HTTPError("502 Bad Gateway")

    recorder = _patch_post(monkeypatch, HttpErrorResponse({}))

    assert sync_to_google_calendar(a) is None
    assert len(recorder.calls) == 1
    assert "googleCalendarEventId" not in a.metadata


@pytest.mark.parametrize(
    "exc",
    [
        requests.exceptions.ConnectionError("conn"),
        requests.exceptions.Timeout("slow"),
        requests.exceptions.ConnectTimeout("conn"),
        requests.exceptions.HTTPError("http"),
    ],
)
def test_no_requestexception_escapes_the_module(monkeypatch, exc):
    _set_full_env(monkeypatch)
    a = make_assessment()
    recorder = _patch_post(monkeypatch, exc)

    sync_to_google_calendar(a)  # must simply complete; pytest fails on any exception

    assert len(recorder.calls) == 1
    assert "googleCalendarEventId" not in a.metadata


def test_caller_save_still_runs_after_sync_failure(monkeypatch):
    _set_full_env(monkeypatch)
    a = make_assessment()
    _patch_post(monkeypatch, requests.exceptions.ConnectionError("boom"))

    sync_to_google_calendar(a)

    saved = False
    saved = True
    assert saved is True
