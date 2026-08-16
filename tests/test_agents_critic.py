"""Hermetic tests for the Self-RAG-style reflection critic.

Every LLM call is faked at the client boundary (FakeLLM); no SarvamLLM instance
with a real key is ever constructed and no network is touched.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _agent_helpers import FakeLLM
from academicos.agents.critic import (
    CRITIC_SYSTEM,
    RETRIEVE_SYSTEM,
    ReflectionScores,
    SarvamCritic,
)

QUERY = "explain the photosynthesis light reaction"
ANSWER = "Light energy is converted to chemical energy in the thylakoid membrane."
EVIDENCE = "The light reaction of photosynthesis converts light energy into chemical energy."


# --------------------------------------------------------------------------- #
# decide_retrieve
# --------------------------------------------------------------------------- #

def test_decide_retrieve_true_when_llm_says_retrieve():
    llm = FakeLLM(responses=[{"retrieve": True, "reason": "needs docs"}])
    critic = SarvamCritic(llm)
    assert critic.decide_retrieve(QUERY) is True
    assert llm.call_count == 1


def test_decide_retrieve_false_when_llm_says_no_retrieval():
    llm = FakeLLM(responses=[{"retrieve": False}])
    critic = SarvamCritic(llm)
    assert critic.decide_retrieve(QUERY) is False


@pytest.mark.parametrize("payload", [[], "nope", None, 42])
def test_decide_retrieve_non_dict_defaults_to_retrieve(payload):
    llm = FakeLLM(responses=[payload])
    assert SarvamCritic(llm).decide_retrieve(QUERY) is True


def test_decide_retrieve_string_value_is_truthy():
    # bool("false") is True -> a stringy non-empty value still means retrieve
    llm = FakeLLM(responses=[{"retrieve": "false"}])
    assert SarvamCritic(llm).decide_retrieve(QUERY) is True


def test_decide_retrieve_empty_dict_key_defaults_to_retrieve():
    # out.get("retrieve", True) when the key is absent -> True
    llm = FakeLLM(responses=[{"reason": "no opinion"}])
    assert SarvamCritic(llm).decide_retrieve(QUERY) is True


def test_decide_retrieve_raising_chat_json_defaults_to_retrieve():
    llm = FakeLLM(responses=[RuntimeError("llm down")])
    assert SarvamCritic(llm).decide_retrieve(QUERY) is True


def test_decide_retrieve_unavailable_returns_true_without_calling_llm():
    llm = FakeLLM(available=False)
    critic = SarvamCritic(llm)
    assert critic.decide_retrieve(QUERY) is True
    assert llm.call_count == 0


def test_decide_retrieve_prompt_contains_system_and_query():
    llm = FakeLLM(responses=[{"retrieve": True}])
    SarvamCritic(llm).decide_retrieve(QUERY)
    messages, kw = llm.calls[0]
    assert messages[0]["role"] == "system"
    assert RETRIEVE_SYSTEM in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == QUERY
    assert kw.get("temperature") == 0.0
    assert kw.get("max_tokens") == 128


# --------------------------------------------------------------------------- #
# score
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("relevant,expected", [(True, 1.0), (False, 0.0), (None, 0.0)])
def test_score_relevance_mapping(relevant, expected):
    llm = FakeLLM(responses=[{"relevant": relevant, "support": "full", "utility": 3}])
    rs = SarvamCritic(llm).score(QUERY, ANSWER, EVIDENCE)
    assert rs.relevance == expected


@pytest.mark.parametrize("support,expected", [
    ("full", 1.0),
    ("partial", 0.5),
    ("none", 0.0),
    ("FULL", 1.0),
    ("garbage", 0.0),
])
def test_score_support_mapping(support, expected):
    llm = FakeLLM(responses=[{"relevant": True, "support": support, "utility": 3}])
    rs = SarvamCritic(llm).score(QUERY, ANSWER, EVIDENCE)
    assert rs.support == expected


@pytest.mark.parametrize("utility,expected", [
    (1, -1.0), (2, -0.5), (3, 0.0), (4, 0.5), (5, 1.0),
])
def test_score_utility_mapping(utility, expected):
    llm = FakeLLM(responses=[{"relevant": True, "support": "full", "utility": utility}])
    rs = SarvamCritic(llm).score(QUERY, ANSWER, EVIDENCE)
    assert rs.utility == expected


def test_score_garbage_utility_falls_back_to_neutral():
    # int("not-an-int") raises inside score(); the exception path returns neutral
    # scores with the error surfaced in detail.
    llm = FakeLLM(responses=[{"relevant": True, "support": "full", "utility": "not-an-int"}])
    rs = SarvamCritic(llm).score(QUERY, ANSWER, EVIDENCE)
    assert rs.relevance == 0.5
    assert rs.support == 0.5
    assert rs.utility == 0.0
    assert rs.retrieved is True
    assert "error" in rs.detail


def test_score_raising_chat_json_returns_neutral_and_does_not_propagate():
    llm = FakeLLM(responses=[RuntimeError("llm down")])
    rs = SarvamCritic(llm).score(QUERY, ANSWER, EVIDENCE)
    assert (rs.relevance, rs.support, rs.utility) == (0.5, 0.5, 0.0)
    assert rs.retrieved is True
    assert "error" in rs.detail


def test_score_unavailable_returns_fixed_scores_without_calling_llm():
    llm = FakeLLM(available=False)
    rs = SarvamCritic(llm).score(QUERY, ANSWER, EVIDENCE)
    assert (rs.relevance, rs.support, rs.utility) == (1.0, 0.5, 0.0)
    assert rs.retrieved is True
    assert llm.call_count == 0


def test_score_detail_carries_raw_output():
    raw = {"relevant": True, "support": "full", "utility": 4}
    llm = FakeLLM(responses=[raw])
    rs = SarvamCritic(llm).score(QUERY, ANSWER, EVIDENCE)
    assert rs.detail["raw"] == raw


def test_score_prompt_contains_system_and_all_texts():
    llm = FakeLLM(responses=[{"relevant": True, "support": "full", "utility": 5}])
    SarvamCritic(llm).score(QUERY, ANSWER, EVIDENCE)
    messages, kw = llm.calls[0]
    assert messages[0]["role"] == "system"
    assert CRITIC_SYSTEM in messages[0]["content"]
    user = messages[1]["content"]
    assert QUERY in user
    assert ANSWER in user
    assert EVIDENCE in user
    assert kw.get("temperature") == 0.0
    assert kw.get("max_tokens") == 128


# --------------------------------------------------------------------------- #
# ReflectionScores.final
# --------------------------------------------------------------------------- #

def test_reflection_final_weighted_sum_default_weights():
    rs = ReflectionScores(retrieved=True, relevance=1.0, support=0.5, utility=0.5)
    assert rs.final() == pytest.approx(1.0 + 0.5 + 0.5 * 0.5)  # = 1.75


def test_reflection_final_custom_weights():
    rs = ReflectionScores(retrieved=True, relevance=1.0, support=0.5, utility=-0.5)
    assert rs.final(w_rel=2.0, w_sup=3.0, w_use=4.0) == pytest.approx(2.0 + 1.5 - 2.0)  # = 1.5


def test_reflection_final_zero_utility_weight():
    rs = ReflectionScores(retrieved=True, relevance=1.0, support=0.0, utility=-1.0)
    assert rs.final(w_rel=1.0, w_sup=1.0, w_use=0.0) == pytest.approx(1.0)


def test_critic_stores_weights_and_threshold():
    critic = SarvamCritic(FakeLLM(), w_rel=0.5, w_sup=1.5, w_use=2.0, retrieve_threshold=0.8)
    assert critic.w_rel == 0.5
    assert critic.w_sup == 1.5
    assert critic.w_use == 2.0
    assert critic.retrieve_threshold == 0.8