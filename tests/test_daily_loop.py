"""P5.1 — daily loop tests: orchestrator produces a bounded day plan from learner signals."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.algorithms.daily_loop import (  # noqa: E402
    DailyLoop, DailyLoopParams, DailyPlan, SessionBlock,
    _KIND_PRIORITY, _DEFAULT_TRIM_WEIGHTS,
)
from academicos.algorithms.learner_model import (  # noqa: E402
    Interaction, LearnerModel, ConceptState,
)

NOW = datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc).isoformat()


def make_learner(learner_id: str = "dl") -> LearnerModel:
    lm = LearnerModel(learner_id=learner_id)
    lm.concepts.clear()
    return lm


def add_concept(lm: LearnerModel, cid: str, attempts: int = 0, correct: int = 0,
                mastery: float = 0.0, confidence: float = 0.0, retention: float = 1.0,
                last_seen: str | None = None, history: list[Interaction] | None = None):
    st = ConceptState(concept_id=cid, attempts=attempts, correct=correct,
                      mastery=mastery, confidence=confidence, retention=retention,
                      last_seen=last_seen, history=history or [])
    lm.concepts[cid] = st
    return lm


def add_answer(lm: LearnerModel, cid: str, outcome: float, ts: str,
               affect: str | None = None):
    st = lm.state(cid)
    st.record(Interaction(concept_id=cid, kind="answer", outcome=outcome,
                          affect=affect, ts=ts))
    return lm


def test_empty_learner_returns_minimal_plan():
    plan = DailyLoop(make_learner("empty"), now=NOW).plan()
    assert plan.blocks == []
    assert plan.blocked_because == ["insufficient-evidence"]
    assert "Record a few interactions first" in plan.advice[0]


def test_new_concept_learn_block():
    lm = make_learner("newc")
    add_concept(lm, "fractions", attempts=0, retention=1.0)
    plan = DailyLoop(lm, now=NOW).plan()
    kinds = [b.kind for b in plan.blocks]
    assert KIND_LEARN in kinds
    b = next(b for b in plan.blocks if b.kind == KIND_LEARN)
    assert b.source == "fractions"
    assert b.suggested_minutes > 0
    assert plan.total_minutes <= plan.session_capacity_minutes


def test_forgotten_concept_retrieve_block():
    lm = make_learner("forg")
    old = datetime(2026, 7, 1, 12, 0, 0, tzinfo=timezone.utc).isoformat()
    add_concept(lm, "decimals", attempts=5, correct=5, mastery=0.9,
                retention=0.1, last_seen=old)
    plan = DailyLoop(lm, now=NOW).plan()
    kinds = [b.kind for b in plan.blocks]
    assert KIND_RETRIEVE in kinds
    b = next(b for b in plan.blocks if b.kind == KIND_RETRIEVE)
    assert b.source == "decimals"
    assert b.suggested_minutes > 0


def test_fatigued_resets_first():
    lm = make_learner("fat")
    recent = datetime(2026, 8, 1, 11, 30, 0, tzinfo=timezone.utc).isoformat()
    # fill recent events with bored/tired to drive fatigue
    for i in range(5):
        add_answer(lm, "fractions", 1.0,
                   datetime(2026, 8, 1, 11, 30 - i, 0, tzinfo=timezone.utc).isoformat(),
                   affect="tired" if i % 2 == 0 else "bored")
    plan = DailyLoop(lm, capacity_minutes=15, now=NOW).plan()
    assert plan.blocks[0].kind == "reset"
    assert "tired" in plan.blocked_because


def test_capacity_enforced_blocks_trimmed():
    lm = make_learner("cap")
    add_concept(lm, "a", attempts=0)
    add_concept(lm, "b", attempts=0)
    add_concept(lm, "c", attempts=0)
    # capacity 10 min, 3 blocks * 5 = 15 -> only 2 fit
    plan = DailyLoop(lm, capacity_minutes=10, now=NOW).plan()
    assert plan.total_minutes <= 10
    assert len(plan.blocks) <= 2
    assert "Session-capacity enforced" in str(plan.blocked_because)


def test_all_mastered_minimal_plan():
    lm = make_learner("mastered")
    add_concept(lm, "frac", attempts=10, correct=10, mastery=1.0, retention=0.95)
    plan = DailyLoop(lm, now=NOW).plan()
    assert plan.total_minutes == 0
    assert "caught up" in " ".join(plan.advice).lower()


def test_underconfident_advice_added():
    lm = make_learner("under")
    add_concept(lm, "frac", attempts=5, correct=5, mastery=0.8, confidence=0.5, retention=0.9)
    # Underconfident = high mastery but low confidence
    plan = DailyLoop(lm, now=NOW).plan()
    assert any("you know this" in a for a in plan.advice)


def test_overconfident_but_forgotten_advice():
    lm = make_learner("over")
    old = datetime(2026, 7, 1, 12, 0, 0, tzinfo=timezone.utc).isoformat()
    add_concept(lm, "frac", attempts=5, correct=5, mastery=0.8, confidence=0.9,
                retention=0.1, last_seen=old)
    plan = DailyLoop(lm, now=NOW).plan()
    assert any("overconfident but drifting" in a for a in plan.advice)


def test_motivation_low_snippet():
    lm = make_learner("mot")
    # low attempts, sparse history -> low motivation
    add_concept(lm, "frac", attempts=2, correct=2, mastery=0.4,
                retention=0.7, last_seen=NOW)
    plan = DailyLoop(lm, now=NOW).plan()
    assert any("Motivation is low" in s for s in plan.motivational_snippets)


def test_habit_risk_snippet():
    lm = make_learner("hab")
    # very sparse study days -> low consistency_7
    add_concept(lm, "frac", attempts=3, correct=2, mastery=0.5, retention=0.7)
    plan = DailyLoop(lm, now=NOW).plan()
    assert any("consistency is low" in s for s in plan.motivational_snippets)


def test_deterministic_same_inputs_same_output():
    lm1 = make_learner("det1")
    add_concept(lm1, "frac", attempts=5, correct=4, mastery=0.6, retention=0.8)
    p1 = DailyLoop(lm1, capacity_minutes=15, now=NOW).plan()

    lm2 = make_learner("det2")
    add_concept(lm2, "frac", attempts=5, correct=4, mastery=0.6, retention=0.8)
    p2 = DailyLoop(lm2, capacity_minutes=15, now=NOW).plan()

    assert p1.blocks == p2.blocks
    assert p1.advice == p2.advice
    assert p1.motivational_snippets == p2.motivational_snippets


def test_as_dict_roundtrip():
    lm = make_learner("round")
    add_concept(lm, "frac", attempts=2, correct=1, mastery=0.3, retention=0.5)
    p1 = DailyLoop(lm, capacity_minutes=15, now=NOW).plan()
    d = p1.as_dict()
    p2 = DailyPlan.from_dict(d)
    assert p1.as_dict() == p2.as_dict()


def test_no_crash_when_store_none():
    lm = make_learner("nostore")
    add_concept(lm, "frac", attempts=0)
    plan = DailyLoop(lm, store=None, capacity_minutes=15, now=NOW).plan()
    assert isinstance(plan, DailyPlan)


def test_params_intact():
    lm = make_learner("params")
    add_concept(lm, "frac", attempts=0)
    plan = DailyLoop(lm, capacity_minutes=15, now=NOW).plan()
    assert plan.params.get("version") == "1.0"
    assert plan.params.get("min_retention") == 0.35
    assert plan.params.get("capacity_minutes") == 15


def test_reset_block_respects_capacity():
    lm = make_learner("resetcap")
    recent = datetime(2026, 8, 1, 11, 30, 0, tzinfo=timezone.utc).isoformat()
    for i in range(5):
        add_answer(lm, "fractions", 1.0,
                   datetime(2026, 8, 1, 11, 30 - i, 0, tzinfo=timezone.utc).isoformat(),
                   affect="tired")
    # capacity 2 min -> reset block should be at most 2 min
    plan = DailyLoop(lm, capacity_minutes=2, now=NOW).plan()
    assert plan.blocks[0].suggested_minutes <= 2
    assert plan.total_minutes <= 2