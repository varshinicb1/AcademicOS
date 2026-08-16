"""Hermetic tests for the agent registry (name -> factory).

``_FACTORIES`` is a module-global that persists across tests, so an autouse
fixture snapshots and restores it around every test to avoid cross-test
pollution (and unique names are used anyway).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import academicos.agents.registry as registry
from academicos.agents.base import Tool


class _DummyTool(Tool):
    name = "dummy"
    description = "dummy tool"

    def run(self, **kwargs):
        return {"ran": True}


@pytest.fixture(autouse=True)
def _isolate_registry():
    saved = dict(registry._FACTORIES)
    registry._FACTORIES.clear()
    yield
    registry._FACTORIES.clear()
    registry._FACTORIES.update(saved)


def test_register_agent_decorator_registers_factory():
    @registry.register_agent("test_agent_dummy")
    def factory():
        return _DummyTool()

    tool = registry.get_agent("test_agent_dummy")
    assert isinstance(tool, _DummyTool)
    assert tool.run() == {"ran": True}


def test_register_agent_returns_factory_unchanged():
    def factory():
        return _DummyTool()

    wrapped = registry.register_agent("test_agent_identity")(factory)
    assert wrapped is factory


def test_get_agent_missing_returns_none():
    assert registry.get_agent("does_not_exist_anywhere") is None


def test_get_agent_invokes_factory_on_every_call():
    calls: list[int] = []

    def factory():
        calls.append(1)
        return _DummyTool()

    registry.register_agent("test_agent_calls")(factory)
    registry.get_agent("test_agent_calls")
    registry.get_agent("test_agent_calls")
    assert len(calls) == 2


def test_list_agents_is_sorted():
    registry.register_agent("test_agent_zebra")(lambda: _DummyTool())
    registry.register_agent("test_agent_alpha")(lambda: _DummyTool())
    registry.register_agent("test_agent_mango")(lambda: _DummyTool())
    assert registry.list_agents() == ["test_agent_alpha", "test_agent_mango", "test_agent_zebra"]


def test_registry_repeated_register_latest_wins():
    first_marker = object()
    second_marker = object()

    def first():
        return ("first", first_marker)

    def second():
        return ("second", second_marker)

    registry.register_agent("test_agent_latest")(first)
    assert registry.get_agent("test_agent_latest") == ("first", first_marker)

    registry.register_agent("test_agent_latest")(second)
    assert registry.get_agent("test_agent_latest") == ("second", second_marker)