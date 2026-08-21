"""The provider-adapter seam (docs/provider-architecture.md): ComposioProvider,
ComposioActionTool, and SarvamLLM-as-LLMProvider. Hermetic -- requests.post is
always mocked, never a real network call.
"""
from __future__ import annotations

import requests

from academicos.agents.base import Tool, ToolResult
from academicos.agents.composio_tool import ComposioActionTool
from academicos.integrations.base import ActionProvider
from academicos.integrations.composio_provider import ComposioProvider
from academicos.llm.base import LLMProvider
from academicos.llm.sarvam import SarvamLLM


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


# ---- ComposioProvider -------------------------------------------------


def test_composio_provider_is_an_action_provider():
    assert issubclass(ComposioProvider, ActionProvider)


def test_available_false_without_key(monkeypatch):
    monkeypatch.delenv("COMPOSIO_API_KEY", raising=False)
    assert ComposioProvider(api_key=None).available() is False


def test_available_true_with_key():
    assert ComposioProvider(api_key="k").available() is True


def test_available_reads_env_var_fallback(monkeypatch):
    monkeypatch.setenv("COMPOSIO_API_KEY", "env-key")
    assert ComposioProvider().available() is True


def test_execute_without_key_returns_error_result_never_raises(monkeypatch):
    monkeypatch.delenv("COMPOSIO_API_KEY", raising=False)
    result = ComposioProvider(api_key=None).execute(
        "SOME_TOOL", {}, user_id="u1", connected_account_id="ca1")
    assert result.ok is False
    assert "no API key" in result.error


def test_execute_without_ids_returns_error_result():
    result = ComposioProvider(api_key="k").execute("SOME_TOOL", {})
    assert result.ok is False
    assert "connected_account_id" in result.error


def test_execute_success_returns_response_data_as_payload(monkeypatch):
    recorded = {}

    def fake_post(url, *, headers, json, timeout):
        recorded["url"] = url
        recorded["headers"] = headers
        recorded["body"] = json
        recorded["timeout"] = timeout
        return FakeResponse({"data": {"response_data": {"id": "evt_1"}}, "successful": True})

    monkeypatch.setattr("academicos.integrations.composio_provider.requests.post", fake_post)

    result = ComposioProvider(api_key="k").execute(
        "GOOGLECALENDAR_CREATE_EVENT", {"summary": "test"},
        user_id="u1", connected_account_id="ca1",
    )
    assert result.ok is True
    assert result.payload == {"id": "evt_1"}
    assert recorded["url"] == "https://backend.composio.dev/api/v3/tools/execute/GOOGLECALENDAR_CREATE_EVENT"
    assert recorded["headers"]["x-api-key"] == "k"
    assert recorded["body"] == {"connected_account_id": "ca1", "user_id": "u1",
                                 "arguments": {"summary": "test"}}


def test_execute_missing_response_data_is_a_clean_failure(monkeypatch):
    monkeypatch.setattr(
        "academicos.integrations.composio_provider.requests.post",
        lambda *a, **kw: FakeResponse({"data": {}}),
    )
    result = ComposioProvider(api_key="k").execute("T", {}, user_id="u", connected_account_id="c")
    assert result.ok is False
    assert "response_data" in result.error


def test_execute_transport_error_never_raises(monkeypatch):
    def raiser(*a, **kw):
        raise requests.exceptions.ConnectionError("boom")

    monkeypatch.setattr("academicos.integrations.composio_provider.requests.post", raiser)
    result = ComposioProvider(api_key="k").execute("T", {}, user_id="u", connected_account_id="c")
    assert result.ok is False
    assert "boom" in result.error


# ---- ComposioActionTool -------------------------------------------------


class FakeProvider(ActionProvider):
    def __init__(self, *, is_available: bool, result: ToolResult):
        self._available = is_available
        self._result = result
        self.calls: list[dict] = []

    def available(self) -> bool:
        return self._available

    def execute(self, tool_slug, arguments, *, user_id=None, **kw) -> ToolResult:
        self.calls.append({"tool_slug": tool_slug, "arguments": arguments,
                            "user_id": user_id, **kw})
        return self._result


def test_composio_action_tool_is_a_tool():
    assert issubclass(ComposioActionTool, Tool)


def test_action_tool_delegates_to_available_provider():
    provider = FakeProvider(is_available=True,
                             result=ToolResult(tool="T", ok=True, payload={"id": "e1"}))
    tool = ComposioActionTool(provider, "GOOGLECALENDAR_CREATE_EVENT",
                               name="create_calendar_event", description="d")

    result = tool.run(user_id="u1", connected_account_id="ca1", summary="hi")

    assert result.ok is True
    assert result.payload == {"id": "e1"}
    assert provider.calls == [{"tool_slug": "GOOGLECALENDAR_CREATE_EVENT",
                                "arguments": {"summary": "hi"}, "user_id": "u1",
                                "connected_account_id": "ca1"}]


def test_action_tool_refuses_when_provider_unavailable():
    provider = FakeProvider(is_available=False, result=ToolResult(tool="T", ok=True))
    tool = ComposioActionTool(provider, "T", name="n", description="d")

    result = tool.run(user_id="u1", connected_account_id="ca1")

    assert result.ok is False
    assert "not configured" in result.error
    assert provider.calls == []  # never reaches the provider


# ---- SarvamLLM as LLMProvider -------------------------------------------


def test_sarvam_llm_is_an_llm_provider():
    assert issubclass(SarvamLLM, LLMProvider)


def test_sarvam_llm_available_reflects_api_key(monkeypatch):
    monkeypatch.delenv("SARVAM_API_KEY", raising=False)
    assert SarvamLLM(api_key=None, base_url="https://api.sarvam.ai").available is False
    assert SarvamLLM(api_key="k", base_url="https://api.sarvam.ai").available is True
