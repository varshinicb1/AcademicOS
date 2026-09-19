"""Domain exceptions must reach the client as a status it can act on.

Four classes were raised but never caught anywhere, so every one of them arrived
as a bare 500. A 500 says "we broke"; three of these say something the caller
can fix, and one says the provider did.

Two things are asserted, and they are different:
  * each handler maps its exception to the right status
  * each handler is REGISTERED on the real app

The second matters because a correct handler that nothing calls changes nothing.
The failure mode is a future edit dropping the decorator, which the first test
would not notice.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from academicos.api import main as api_main  # noqa: E402
from academicos.assessment.api_keys import ScopeError  # noqa: E402
from academicos.assessment.llm_evaluate import LLMEvaluationError  # noqa: E402
from academicos.assessment.qbank_store import ReviewStateError  # noqa: E402
from academicos.llm.sarvam import LLMProviderError  # noqa: E402

# (exception class, handler, expected status)
CASES = [
    (ScopeError, api_main._on_scope_error, 400),
    (ReviewStateError, api_main._on_review_state_error, 409),
    (LLMProviderError, api_main._on_llm_provider_error, 503),
    (LLMEvaluationError, api_main._on_llm_evaluation_error, 502),
]


def _body(response):
    return json.loads(bytes(response.body).decode("utf-8"))


@pytest.mark.parametrize("exc_cls,handler,expected", CASES,
                         ids=[c[0].__name__ for c in CASES])
def test_each_handler_is_registered_on_the_real_app(exc_cls, handler, expected):
    """A handler nothing calls changes nothing."""
    assert exc_cls in api_main.app.exception_handlers, (
        f"{exc_cls.__name__} has no handler on the app, so it still surfaces "
        "as a 500"
    )
    assert api_main.app.exception_handlers[exc_cls] is handler


@pytest.mark.parametrize("exc_cls,handler,expected", CASES,
                         ids=[c[0].__name__ for c in CASES])
def test_each_handler_returns_its_status(exc_cls, handler, expected):
    response = handler(None, exc_cls("a message the caller may need"))
    assert response.status_code == expected


def test_a_scope_error_tells_the_caller_which_scopes_were_wrong():
    """400 is only useful if it says what to fix.

    `validate_scopes` produces a message naming the offending scopes and listing
    the vocabulary, so returning it lets a caller fix the request without
    reading our source.
    """
    response = api_main._on_scope_error(
        None, ScopeError("unknown scope(s) ['nope']; the vocabulary is ['qbank:read']"))
    body = _body(response)
    assert "nope" in body["detail"]
    assert "qbank:read" in body["detail"]


def test_llm_errors_do_not_echo_the_message_back():
    """`LLMEvaluationError` carries raw model output.

    One of its raises is `f"no JSON object in model response: {raw[:200]!r}"`.
    Echoing that to a client is how prompt content leaks, so both LLM handlers
    return a fixed string -- and this pins it, because "just add str(exc)" is
    exactly the sort of helpful-looking change that would reintroduce the leak.
    """
    secret = "MODEL SAID: the passage is about a private student's family"
    for handler, exc_cls in ((api_main._on_llm_evaluation_error, LLMEvaluationError),
                             (api_main._on_llm_provider_error, LLMProviderError)):
        body = _body(handler(None, exc_cls(secret)))
        assert secret not in json.dumps(body), (
            f"{exc_cls.__name__}'s handler echoed the exception message"
        )
        assert body["detail"]


def test_a_review_state_error_names_the_states_involved():
    """409 is more useful when it says what the current state was."""
    response = api_main._on_review_state_error(
        None, ReviewStateError("'published' -> 'draft' is not a legal transition"))
    assert "'published' -> 'draft'" in _body(response)["detail"]


def test_the_four_are_distinguishable_by_status():
    """Four classes, four statuses -- collapsing any two loses information.

    502 and 503 are the pair most tempting to merge: both are "the LLM did not
    give us an answer". But retrying is sensible for an unreachable provider and
    pointless for one that answered unusably, so the caller needs them apart.
    """
    statuses = [handler(None, cls("x")).status_code for cls, handler, _ in CASES]
    assert len(set(statuses)) == len(statuses), (
        f"two domain exceptions share a status, so a caller cannot tell them "
        f"apart: {statuses}"
    )


def test_no_domain_exception_is_left_unmapped():
    """The general form of the bug: a raised domain class with no handler.

    Scanning for the four known classes was how this was found; asserting it
    over the modules that define them means the next one added is caught too.
    """
    import importlib
    import inspect

    modules = {
        "ScopeError": "academicos.assessment.api_keys",
        "ReviewStateError": "academicos.assessment.qbank_store",
        "LLMProviderError": "academicos.llm.sarvam",
        "LLMEvaluationError": "academicos.assessment.llm_evaluate",
        "LLMBudgetExceeded": "academicos.llm.budget",
        "SupabaseUnavailable": "academicos.assessment.supabase_kv",
    }
    registered = set(api_main.app.exception_handlers)
    for name, module_path in modules.items():
        cls = getattr(importlib.import_module(module_path), name)
        assert inspect.isclass(cls)
        assert cls in registered, (
            f"{name} is defined in {module_path} and is not registered on the "
            "app, so it will surface as a 500"
        )
