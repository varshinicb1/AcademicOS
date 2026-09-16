"""Route-level guardrails: the budget, the request bounds, and the telemetry probe.

Why these go through a real `TestClient` rather than calling the handler directly
-------------------------------------------------------------------------------
The LLM budget is carried in a `contextvars.ContextVar`. That choice is only
correct if a value set inside a synchronous FastAPI endpoint is visible to the
code the endpoint calls -- and FastAPI runs those endpoints on threadpool
workers whose contexts are *copied*, so "it works when I call the function
myself" is not evidence about the deployed behaviour. `TestClient` drives the
real ASGI stack and the real threadpool, so these tests are the ones that
actually establish the property.

The second thing being proven is the failure mode: a spent budget must surface
as 429 with an actionable `Retry-After`, not as a 500. A 500 reads as our bug
and invites an immediate retry, which is exactly backwards when the point is to
stop spending.
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.agents.orchestrator import DoubtSolver
from academicos.api.main import MAX_QUERY_CHARS, app
from academicos.llm.budget import current_budget


def register_and_login(client: TestClient) -> dict[str, str]:
    """Mint a real identity. Email is unique because UserStore is a process singleton."""
    email = f"guardrail-{uuid.uuid4().hex[:10]}@example.com"
    r = client.post("/api/v1/auth/register", json={
        "schoolId": "school_1", "name": "Guardrail Tester", "email": email,
        "password": "correct horse battery",
    })
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


# --------------------------------------------------------------------------- #
# the budget binds inside the request thread
# --------------------------------------------------------------------------- #

def test_budget_reaches_the_code_that_would_call_the_model(tmp_path, monkeypatch):
    """The load-bearing assumption: an endpoint-set budget is visible to its callees."""
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("ACOS_MAX_LLM_CALLS_PER_REQUEST", "3")

    seen: dict = {}

    def fake_solve(self, doubt):  # noqa: ANN001 - stand-in for the real agent
        budget = current_budget()
        seen["budget"] = budget
        seen["is_none"] = budget is None
        return {"agent": "doubt-solver", "doubt": doubt, "answer": "stub",
                "citations": [], "evidence": [], "reflection": {"used_critic": False}}

    monkeypatch.setattr(DoubtSolver, "solve", fake_solve)

    with TestClient(app) as client:
        headers = register_and_login(client)
        r = client.post("/v1/agent/doubt", json={"doubt": "what is photosynthesis"},
                        headers=headers)

    assert r.status_code == 200, r.text
    assert seen["is_none"] is False, (
        "the budget did not reach the endpoint's callee -- the contextvar does "
        "not survive FastAPI's threadpool hop, and the ceiling is therefore not "
        "enforced at all"
    )
    assert seen["budget"].max_calls == 3
    assert seen["budget"].label == "agent.doubt"


def test_budget_ceiling_is_read_from_the_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("ACOS_MAX_LLM_CALLS_PER_REQUEST", "7")
    seen: dict = {}

    def fake_solve(self, doubt):  # noqa: ANN001
        seen["budget"] = current_budget()
        return {"agent": "doubt-solver", "doubt": doubt, "answer": "stub",
                "citations": [], "evidence": []}

    monkeypatch.setattr(DoubtSolver, "solve", fake_solve)
    with TestClient(app) as client:
        headers = register_and_login(client)
        client.post("/v1/agent/doubt", json={"doubt": "hello there"}, headers=headers)
    assert seen["budget"].max_calls == 7


def test_invalid_budget_env_falls_back_to_the_default(tmp_path, monkeypatch):
    """A bad env var is a warning, not a crash on the request path."""
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("ACOS_MAX_LLM_CALLS_PER_REQUEST", "lots")
    seen: dict = {}

    def fake_solve(self, doubt):  # noqa: ANN001
        seen["budget"] = current_budget()
        return {"agent": "doubt-solver", "doubt": doubt, "answer": "stub",
                "citations": [], "evidence": []}

    monkeypatch.setattr(DoubtSolver, "solve", fake_solve)
    with TestClient(app) as client:
        headers = register_and_login(client)
        client.post("/v1/agent/doubt", json={"doubt": "hello there"}, headers=headers)
    assert seen["budget"].max_calls == 12


def test_exhausting_the_budget_returns_429_with_retry_after(tmp_path, monkeypatch):
    """A spent budget is 429, not 500 -- and it must carry Retry-After."""
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("ACOS_MAX_LLM_CALLS_PER_REQUEST", "2")
    from academicos.llm.budget import consume_budget

    def greedy_solve(self, doubt):  # noqa: ANN001
        for _ in range(5):
            consume_budget("greedy")
        return {}  # pragma: no cover - unreachable

    monkeypatch.setattr(DoubtSolver, "solve", greedy_solve)
    with TestClient(app) as client:
        headers = register_and_login(client)
        r = client.post("/v1/agent/doubt", json={"doubt": "hello there"}, headers=headers)

    assert r.status_code == 429, r.text
    assert r.headers.get("Retry-After") == "5"
    assert "budget" in r.json()["detail"].lower()


def test_budget_is_not_leaked_between_requests(tmp_path, monkeypatch):
    """Each request gets its own allowance; a spent one must not poison the next."""
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("ACOS_MAX_LLM_CALLS_PER_REQUEST", "1")
    from academicos.llm.budget import consume_budget

    mode = {"greedy": True}

    def solve(self, doubt):  # noqa: ANN001
        if mode["greedy"]:
            for _ in range(3):
                consume_budget("greedy")
        return {"agent": "doubt-solver", "doubt": doubt, "answer": "ok",
                "citations": [], "evidence": []}

    monkeypatch.setattr(DoubtSolver, "solve", solve)
    with TestClient(app) as client:
        headers = register_and_login(client)
        first = client.post("/v1/agent/doubt", json={"doubt": "hello there"}, headers=headers)
        assert first.status_code == 429

        mode["greedy"] = False
        second = client.post("/v1/agent/doubt", json={"doubt": "hello there"}, headers=headers)
        assert second.status_code == 200, "a fresh request must get a fresh budget"
        assert current_budget() is None, "the budget leaked out of the request"


# --------------------------------------------------------------------------- #
# request bounds (LLM06)
# --------------------------------------------------------------------------- #

def test_oversized_doubt_is_rejected_before_the_agent_runs(tmp_path, monkeypatch):
    """Validation happens before any work, so a hostile body costs nothing."""
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    calls = {"n": 0}

    def counting_solve(self, doubt):  # noqa: ANN001
        calls["n"] += 1
        return {}

    monkeypatch.setattr(DoubtSolver, "solve", counting_solve)
    with TestClient(app) as client:
        headers = register_and_login(client)
        r = client.post("/v1/agent/doubt",
                        json={"doubt": "x" * (MAX_QUERY_CHARS + 1)}, headers=headers)

    assert r.status_code == 422
    assert calls["n"] == 0, "the agent must not run for a rejected request"


def test_doubt_at_the_limit_is_accepted(tmp_path, monkeypatch):
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))

    def solve(self, doubt):  # noqa: ANN001
        return {"agent": "doubt-solver", "doubt": doubt, "answer": "ok",
                "citations": [], "evidence": []}

    monkeypatch.setattr(DoubtSolver, "solve", solve)
    with TestClient(app) as client:
        headers = register_and_login(client)
        r = client.post("/v1/agent/doubt", json={"doubt": "x" * MAX_QUERY_CHARS}, headers=headers)
    assert r.status_code == 200


def test_oversized_student_answer_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    with TestClient(app) as client:
        headers = register_and_login(client)
        r = client.post("/api/v1/evaluations/answer", headers=headers, json={
            "question": "q", "studentAnswer": "y" * 50_000,
        })
    assert r.status_code == 422


def test_capacity_minutes_has_an_upper_bound(tmp_path, monkeypatch):
    """An unbounded value here asks the planner to compute for an arbitrary time."""
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    with TestClient(app) as client:
        headers = register_and_login(client)
        r = client.post("/v1/plan", headers=headers,
                        json={"target": "Photosynthesis", "capacity_minutes": 100_000})
    assert r.status_code == 422


# --------------------------------------------------------------------------- #
# observability probe
# --------------------------------------------------------------------------- #

def test_health_llm_exposes_component_telemetry(tmp_path, monkeypatch):
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    with TestClient(app) as client:
        r = client.get("/health/llm")
    assert r.status_code == 200
    body = r.json()
    for key in ("calls", "failures", "retries", "window", "p50_ms", "p95_ms", "failure_rate"):
        assert key in body, f"/health/llm missing {key}"


def test_health_llm_never_exposes_prompt_content(tmp_path, monkeypatch):
    """It is unauthenticated, so it must be safe to expose to an uptime check."""
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    import json

    def solve(self, doubt):  # noqa: ANN001
        return {"agent": "doubt-solver", "doubt": doubt, "answer": "ok",
                "citations": [], "evidence": []}

    monkeypatch.setattr(DoubtSolver, "solve", solve)
    secret = "Aarav Menon scored 41 in the term test"
    with TestClient(app) as client:
        headers = register_and_login(client)
        client.post("/v1/agent/doubt", json={"doubt": secret}, headers=headers)
        body = json.dumps(client.get("/health/llm").json())
    assert secret not in body
    assert "Aarav" not in body
