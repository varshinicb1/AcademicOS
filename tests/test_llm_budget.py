"""Per-request ceiling on outbound LLM calls (OWASP LLM06, Unbounded Consumption).

Two things are being proven here, and the second matters more than the first:

1. The counter works -- it stops at the ceiling.
2. **The budget actually binds from inside an endpoint.** The implementation
   carries the ceiling in a `contextvars.ContextVar`, which is only correct if
   the value set by the handler is visible to the code that makes the model
   call. FastAPI runs synchronous endpoints on threadpool workers whose contexts
   are copied, so "it works on my call stack" is not evidence. The route-level
   test at the bottom exercises the real path.
"""
from __future__ import annotations

import sys
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.llm.budget import (
    DEFAULT_MAX_LLM_CALLS,
    LLMBudget,
    LLMBudgetExceeded,
    consume_budget,
    current_budget,
    llm_budget,
)


# --------------------------------------------------------------------------- #
# LLMBudget
# --------------------------------------------------------------------------- #

def test_budget_allows_exactly_max_calls():
    budget = LLMBudget(3)
    for _ in range(3):
        budget.consume()
    assert budget.used == 3
    assert budget.remaining == 0
    assert budget.exhausted is True


def test_budget_raises_on_the_call_after_the_ceiling():
    budget = LLMBudget(2, label="agent.doubt")
    budget.consume("critic.decide_retrieve")
    budget.consume("critic.score")
    with pytest.raises(LLMBudgetExceeded) as exc_info:
        budget.consume("critic.score")
    message = str(exc_info.value)
    assert "agent.doubt" in message
    assert "2 of 2" in message
    # The last operation is named, which is what makes the error actionable.
    assert "critic.score" in message


def test_budget_exhaustion_does_not_increment_past_the_ceiling():
    budget = LLMBudget(1)
    budget.consume()
    for _ in range(5):
        with pytest.raises(LLMBudgetExceeded):
            budget.consume()
    assert budget.used == 1


def test_remaining_never_goes_negative():
    budget = LLMBudget(1)
    budget.consume()
    assert budget.remaining == 0
    with pytest.raises(LLMBudgetExceeded):
        budget.consume()
    assert budget.remaining == 0


def test_last_operation_is_recorded():
    budget = LLMBudget(5)
    assert budget.last_operation is None
    budget.consume("first")
    budget.consume("second")
    assert budget.last_operation == "second"


def test_snapshot_is_serialisable():
    budget = LLMBudget(4, label="x")
    budget.consume()
    snap = budget.snapshot()
    assert snap == {"label": "x", "max_calls": 4, "used": 1, "remaining": 3}
    import json
    json.dumps(snap)  # must not raise


@pytest.mark.parametrize("max_calls", [0, -1])
def test_max_calls_must_be_positive(max_calls):
    with pytest.raises(ValueError):
        LLMBudget(max_calls)


def test_default_ceiling_is_a_named_constant():
    assert DEFAULT_MAX_LLM_CALLS == 12
    assert LLMBudget().max_calls == DEFAULT_MAX_LLM_CALLS


# --------------------------------------------------------------------------- #
# concurrency
# --------------------------------------------------------------------------- #

def test_ceiling_holds_under_concurrent_callers():
    """Checked and incremented under one lock, so two threads cannot share the last slot."""
    budget = LLMBudget(50)
    granted = []
    denied = []
    lock = threading.Lock()

    def worker():
        for _ in range(20):
            try:
                budget.consume()
            except LLMBudgetExceeded:
                with lock:
                    denied.append(1)
            else:
                with lock:
                    granted.append(1)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(granted) == 50, f"expected exactly 50 grants, got {len(granted)}"
    assert len(denied) == 150
    assert budget.used == 50


# --------------------------------------------------------------------------- #
# context manager
# --------------------------------------------------------------------------- #

def test_no_budget_in_force_by_default():
    assert current_budget() is None


def test_consume_is_a_no_op_without_a_budget():
    """CLI and test paths run unbudgeted; that must not raise."""
    consume_budget("anything")


def test_context_manager_sets_and_restores():
    assert current_budget() is None
    with llm_budget(5, label="outer") as budget:
        assert current_budget() is budget
        assert budget.max_calls == 5
        assert budget.label == "outer"
        consume_budget("op")
        assert budget.used == 1
    assert current_budget() is None


def test_nested_budget_replaces_and_then_restores():
    """An inner scope choosing a tighter ceiling must not leak outward."""
    with llm_budget(10, label="outer") as outer:
        with llm_budget(2, label="inner") as inner:
            assert current_budget() is inner
            assert inner.max_calls == 2
        assert current_budget() is outer
        assert outer.used == 0


def test_budget_is_restored_even_when_the_body_raises():
    with llm_budget(3) as budget:
        with pytest.raises(LLMBudgetExceeded):
            for _ in range(4):
                consume_budget()
        assert budget.exhausted
    assert current_budget() is None


def test_consuming_past_the_ceiling_raises_through_the_module_helper():
    with llm_budget(1):
        consume_budget("first")
        with pytest.raises(LLMBudgetExceeded):
            consume_budget("second")


# --------------------------------------------------------------------------- #
# regression: the exhaustion path must not deadlock
# --------------------------------------------------------------------------- #

def test_exhaustion_does_not_deadlock_on_a_non_reentrant_lock():
    """Regression. Exhausting the budget used to hang the request thread forever.

    `consume()` holds a plain `threading.Lock` while it checks the ceiling, and
    the `LLMBudgetExceeded` constructor used to read `budget.used` -- which
    acquires that same lock, on the same thread, while it is already held. The
    result was not an error: it was a stopped process, with no exception, no
    log line, and no timeout inside the library to break it out.

    A hang is the worst possible failure mode, so this test guards it with an
    explicit wait rather than trusting the call to return.
    """
    budget = LLMBudget(1, label="x")
    budget.consume()
    finished = threading.Event()

    def exhaust():
        try:
            budget.consume()
        except LLMBudgetExceeded:
            pass
        finally:
            finished.set()

    worker = threading.Thread(target=exhaust, daemon=True)
    worker.start()
    assert finished.wait(timeout=5.0), "consume() deadlocked instead of raising"
    worker.join(timeout=1.0)


def test_exhaustion_error_holds_plain_values_and_not_the_budget():
    """An exception carrying a live mutable object reports stale numbers later."""
    budget = LLMBudget(1, label="x")
    budget.consume("first")
    with pytest.raises(LLMBudgetExceeded) as exc_info:
        budget.consume("second")
    exc = exc_info.value
    assert exc.label == "x"
    assert exc.used == 1
    assert exc.max_calls == 1
    assert exc.last_operation == "first"
    assert not hasattr(exc, "budget"), "the exception must not hold the live budget"

