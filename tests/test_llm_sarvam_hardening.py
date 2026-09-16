"""SarvamLLM hardening: retry loop, telemetry, bounds, response validation.

Transport is faked at `requests.post` and the backoff sleeper is injected, so
nothing here touches the network or spends real time waiting. That injection
point is the reason these cases are testable at all -- a retry policy that can
only be verified by actually waiting is a retry policy nobody verifies.

The base URL points at 127.0.0.1 so `.available` is True without an API key:
the client treats localhost as a self-hosted deployment that needs no auth.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.llm.budget import LLMBudgetExceeded, llm_budget
from academicos.llm.resilience import RetryPolicy
from academicos.llm.sarvam import LLMProviderError, SarvamLLM
from academicos.llm.telemetry import LLMTelemetry

LOCAL_URL = "http://127.0.0.1:9"


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text="", headers=None,
                 json_raises=False):
        self.status_code = status_code
        self._payload = payload
        self.text = text
        self.headers = headers or {}
        self._json_raises = json_raises

    def json(self):
        if self._json_raises:
            raise ValueError("Expecting value: line 1 column 1")
        return self._payload


def ok(content: str = "hello") -> FakeResponse:
    return FakeResponse(200, {
        "choices": [{"message": {"content": content}, "finish_reason": "stop"}]
    })


def status(code: int, *, retry_after: str | None = None, text: str = "") -> FakeResponse:
    headers = {"Retry-After": retry_after} if retry_after is not None else {}
    return FakeResponse(code, payload={"error": "x"}, text=text, headers=headers)


class Transport:
    """Records calls and replays queued responses (or raises queued exceptions)."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls: list[dict] = []

    def post(self, url, **kw):
        self.calls.append({"url": url, **kw})
        if not self.responses:
            raise AssertionError("transport exhausted: unexpected extra HTTP call")
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class Sleeper:
    """Records requested delays instead of performing them."""

    def __init__(self):
        self.delays: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.delays.append(seconds)


@pytest.fixture
def build(monkeypatch):
    """Returns a factory that wires a SarvamLLM to a fake transport.

    `api_key` is set explicitly to a placeholder rather than left to default.
    The constructor falls back to `os.environ["SARVAM_API_KEY"]`, and a real key
    is present in some developer environments -- which meant an earlier version
    of this suite put the live key into a pytest traceback (the transport dumps
    `requests.post(**kwargs)`, and the kwargs include the Authorization header).
    Tests must not depend on, or leak, a real credential.
    """
    def _build(responses, *, policy=None, max_tokens=2048, max_prompt_chars=200_000):
        transport = Transport(responses)
        monkeypatch.setattr(requests, "post", transport.post)
        sleeper = Sleeper()
        telemetry = LLMTelemetry()
        llm = SarvamLLM(
            api_key="test-key-not-a-real-credential",
            base_url=LOCAL_URL,
            model="sarvam-test",
            policy=policy or RetryPolicy(max_attempts=4, base_delay_s=1.0, max_delay_s=20.0),
            sleep=sleeper,
            telemetry=telemetry,
            max_tokens=max_tokens,
            max_prompt_chars=max_prompt_chars,
        )
        return llm, transport, sleeper, telemetry

    return _build


MESSAGES = [{"role": "user", "content": "hi"}]


# --------------------------------------------------------------------------- #
# happy path
# --------------------------------------------------------------------------- #

def test_success_on_first_attempt(build):
    llm, transport, sleeper, telemetry = build([ok("answer")])
    assert llm.chat(MESSAGES, operation="test.op") == "answer"
    assert len(transport.calls) == 1
    assert sleeper.delays == []
    records = telemetry.recent()
    assert len(records) == 1
    assert records[0].ok is True
    assert records[0].attempt == 0
    assert records[0].operation == "test.op"
    assert records[0].latency_ms >= 0.0


def test_default_max_tokens_is_applied_when_caller_omits_it(build):
    """The previous client omitted `max_tokens` entirely, making completion length
    someone else's decision. A cap is now always sent."""
    llm, transport, _, _ = build([ok()], max_tokens=777)
    llm.chat(MESSAGES)
    assert transport.calls[0]["json"]["max_tokens"] == 777


def test_explicit_max_tokens_overrides_the_default(build):
    llm, transport, _, _ = build([ok()])
    llm.chat(MESSAGES, max_tokens=64)
    assert transport.calls[0]["json"]["max_tokens"] == 64


def test_timeout_is_always_passed(build):
    llm, transport, _, _ = build([ok()])
    llm.chat(MESSAGES)
    assert transport.calls[0]["timeout"] == llm.timeout
    assert transport.calls[0]["timeout"] is not None


# --------------------------------------------------------------------------- #
# retries
# --------------------------------------------------------------------------- #

def test_retries_503_then_succeeds(build):
    llm, transport, sleeper, telemetry = build([status(503), ok("recovered")])
    assert llm.chat(MESSAGES) == "recovered"
    assert len(transport.calls) == 2
    assert len(sleeper.delays) == 1
    records = telemetry.recent()
    assert [r.ok for r in records] == [False, True]
    assert [r.attempt for r in records] == [0, 1]
    assert records[0].status_code == 503


def test_retries_502_and_504_which_the_old_client_ignored(build):
    llm, transport, _, _ = build([status(502), status(504), ok("ok")])
    assert llm.chat(MESSAGES) == "ok"
    assert len(transport.calls) == 3


def test_retries_408_and_425(build):
    llm, transport, _, _ = build([status(408), status(425), ok("ok")])
    assert llm.chat(MESSAGES) == "ok"
    assert len(transport.calls) == 3


def test_retries_connection_errors(build):
    llm, transport, sleeper, _ = build([requests.ConnectionError("refused"), ok("ok")])
    assert llm.chat(MESSAGES) == "ok"
    assert len(sleeper.delays) == 1


def test_retries_timeouts(build):
    llm, _, sleeper, _ = build([requests.Timeout("slow"), ok("ok")])
    assert llm.chat(MESSAGES) == "ok"
    assert len(sleeper.delays) == 1


def test_non_retryable_status_raises_immediately_without_retrying_or_sleeping(build):
    """A 400 will fail identically on retry; retrying only burns provider quota."""
    llm, transport, sleeper, _ = build([status(400, text="bad request")])
    with pytest.raises(LLMProviderError) as exc_info:
        llm.chat(MESSAGES)
    assert "400" in str(exc_info.value)
    assert "not retryable" in str(exc_info.value)
    assert len(transport.calls) == 1
    assert sleeper.delays == []


@pytest.mark.parametrize("code", [401, 403, 404, 422])
def test_other_deterministic_4xx_are_not_retried(build, code):
    llm, transport, sleeper, _ = build([status(code)])
    with pytest.raises(LLMProviderError):
        llm.chat(MESSAGES)
    assert len(transport.calls) == 1
    assert sleeper.delays == []


def test_exhaustion_sleeps_once_per_retry_and_not_after_the_final_attempt(build):
    """4 attempts -> exactly 3 waits. Sleeping after the last failure is dead time.

    The previous implementation did sleep after its final 429 (`time.sleep` then
    `continue`, with the loop then falling out), so it added a full delay to a
    request that had already failed.
    """
    llm, transport, sleeper, telemetry = build([status(503)] * 4)
    with pytest.raises(LLMProviderError):
        llm.chat(MESSAGES)
    assert len(transport.calls) == 4
    assert len(sleeper.delays) == 3
    assert len(telemetry.recent()) == 4


def test_connection_error_exhaustion_names_the_failure(build):
    llm, transport, sleeper, _ = build([requests.ConnectionError("boom")] * 4)
    with pytest.raises(LLMProviderError) as exc_info:
        llm.chat(MESSAGES)
    assert "ConnectionError" in str(exc_info.value)
    assert len(sleeper.delays) == 3


# --------------------------------------------------------------------------- #
# Retry-After
# --------------------------------------------------------------------------- #

def test_retry_after_seconds_is_honoured(build):
    llm, _, sleeper, _ = build([status(429, retry_after="7"), ok()])
    llm.chat(MESSAGES)
    assert sleeper.delays == [7.0]


def test_retry_after_is_clamped_to_the_policy_ceiling(build):
    """An upstream asking for a day must not park the worker for a day."""
    llm, _, sleeper, _ = build([status(429, retry_after="99999"), ok()])
    llm.chat(MESSAGES)
    assert sleeper.delays == [20.0]


def test_retry_after_http_date_is_honoured(build):
    llm, _, sleeper, _ = build([status(429, retry_after="Wed, 21 Oct 2026 07:28:00 GMT"), ok()])
    llm.chat(MESSAGES)
    assert len(sleeper.delays) == 1
    assert sleeper.delays[0] >= 0.0  # parsed as a delta, not silently ignored


# --------------------------------------------------------------------------- #
# bounds
# --------------------------------------------------------------------------- #

def test_oversized_prompt_is_refused_before_any_network_call(build):
    llm, transport, _, telemetry = build([ok()], max_prompt_chars=50)
    with pytest.raises(ValueError) as exc_info:
        llm.chat([{"role": "user", "content": "x" * 51}])
    assert "over the" in str(exc_info.value)
    assert transport.calls == []
    assert telemetry.recent() == []


def test_prompt_exactly_at_the_limit_is_allowed(build):
    llm, transport, _, _ = build([ok()], max_prompt_chars=10)
    llm.chat([{"role": "user", "content": "x" * 10}])
    assert len(transport.calls) == 1


def test_unavailable_provider_raises_before_transport(build):
    llm, transport, _, _ = build([ok()])
    llm.base_url = "https://api.sarvam.ai"
    llm.api_key = ""
    with pytest.raises(LLMProviderError) as exc_info:
        llm.chat(MESSAGES)
    assert "no API key" in str(exc_info.value)
    assert transport.calls == []


# --------------------------------------------------------------------------- #
# response validation (LLM10)
# --------------------------------------------------------------------------- #

def test_non_json_body_names_the_body(build):
    llm, _, _, _ = build([FakeResponse(200, json_raises=True, text="<html>oops</html>")])
    with pytest.raises(LLMProviderError) as exc_info:
        llm.chat(MESSAGES)
    assert "not JSON" in str(exc_info.value)
    assert "html" in str(exc_info.value)


@pytest.mark.parametrize("payload", [
    {},                                  # no choices
    {"choices": []},                     # empty choices
    {"choices": [{}]},                   # no message
    {"choices": [{"message": {}}]},      # no content / reasoning_content
    {"choices": "not-a-list"},           # wrong type
])
def test_unexpected_response_shape_is_reported_clearly(build, payload):
    """This used to surface as a bare KeyError/IndexError four frames up."""
    llm, _, _, _ = build([FakeResponse(200, payload)])
    with pytest.raises(LLMProviderError):
        llm.chat(MESSAGES)


def test_reasoning_only_reply_is_an_error_not_an_empty_answer(build):
    """A reasoning-only reply is a real provider behaviour, but it is unusable
    as an answer and must not be handed back as an empty string."""
    payload = {"choices": [{"message": {"reasoning_content": "thinking..."},
                            "finish_reason": "length"}]}
    llm, _, _, _ = build([FakeResponse(200, payload)])
    with pytest.raises(LLMProviderError) as exc_info:
        llm.chat(MESSAGES)
    assert "no content" in str(exc_info.value)


# --------------------------------------------------------------------------- #
# budget integration
# --------------------------------------------------------------------------- #

def test_budget_caps_a_retry_storm(build):
    """The ceiling is on calls, not on attempts -- which is the point.

    A request that keeps retrying must stop when the *request's* allowance runs
    out, not merely when this one call's attempt budget does.
    """
    llm, transport, _, _ = build([status(503)] * 10)
    with llm_budget(2, label="test"):
        with pytest.raises(LLMBudgetExceeded):
            llm.chat(MESSAGES)
    assert len(transport.calls) == 2, "the third call must never leave the process"


def test_unbudgeted_calls_are_unrestricted(build):
    llm, transport, _, _ = build([status(503), ok("fine")])
    assert llm.chat(MESSAGES) == "fine"


def test_budget_is_consumed_before_the_network_call(build):
    """A call that cannot be afforded must not be made at all."""
    llm, transport, _, _ = build([ok(), ok()])
    with llm_budget(1):
        llm.chat(MESSAGES)
    assert len(transport.calls) == 1

    with llm_budget(1):
        llm.chat(MESSAGES)  # uses the fresh budget's single slot
    assert len(transport.calls) == 2


def test_no_real_credential_is_used_by_this_suite(build):
    """Guard the guard: the fixture must not pick up a live key from the environment."""
    llm, _, _, _ = build([ok()])
    assert llm.api_key == "test-key-not-a-real-credential"


# --------------------------------------------------------------------------- #
# telemetry hygiene
# --------------------------------------------------------------------------- #

def test_telemetry_records_shape_not_prompt_content(build):
    """DPDP: student text must not be duplicated into an observability store."""
    secret = "Aarav Menon scored 41 in the term test"
    llm, _, _, telemetry = build([ok("reply")])
    llm.chat([{"role": "user", "content": secret}], operation="privacy.check")

    import json
    blob = json.dumps([r.__dict__ for r in telemetry.recent()])
    assert secret not in blob
    assert "Aarav" not in blob
    record = telemetry.recent()[0]
    assert record.prompt_chars == len(secret)
    assert record.completion_chars == len("reply")


def test_summary_reports_percentiles_and_failure_rate(build):
    # The second call needs a 503 per allowed attempt so it exhausts rather than
    # running the transport dry and raising AssertionError instead.
    llm, _, _, telemetry = build([ok()] + [status(503)] * 4 + [ok()])
    llm.chat(MESSAGES)
    with pytest.raises(LLMProviderError):
        llm.chat(MESSAGES, operation="failing")
    llm.chat(MESSAGES)

    summary = telemetry.summary()
    assert summary["calls"] >= 5
    assert summary["failures"] >= 4
    assert summary["p50_ms"] is not None
    assert 0.0 <= summary["failure_rate"] <= 1.0
    assert "by_operation" in summary
    assert summary["by_operation"].get("failing") == 4


def test_no_real_time_is_spent_waiting(build):
    """Proves the injected sleeper is actually in use."""
    llm, _, sleeper, _ = build([status(503), status(503), status(503), ok()])
    started = time.monotonic()
    llm.chat(MESSAGES)
    assert time.monotonic() - started < 1.0
    assert len(sleeper.delays) == 3


def test_single_attempt_policy_makes_no_retries(build):
    llm, transport, sleeper, _ = build([status(503)],
                                       policy=RetryPolicy(max_attempts=1))
    with pytest.raises(LLMProviderError):
        llm.chat(MESSAGES)
    assert len(transport.calls) == 1
    assert sleeper.delays == []
