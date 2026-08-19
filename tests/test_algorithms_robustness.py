"""Audit regression tests for D6 — learner-algorithm robustness against
out-of-range inputs that previously crashed or silently escaped their domain.

* A single out-of-range outcome (1.5, e.g. from a malformed evaluator) used
  to push confidence/competence above 1.0.
* Future-dated interactions (clock skew / bad sync) used to overflow
  math.exp in mastery/confidence/motivation.
* The exponential forgetting model schedules a next review at a date that can
  exceed the maximum representable date; plan() used to raise OverflowError.

A/B: every test here fails on the pre-audit code and passes on the clamped
code.
"""
from __future__ import annotations

import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.algorithms.confidence_model import ConfidenceModel  # noqa: E402
from academicos.algorithms.forgetting import (  # noqa: E402
    ForgettingModel,
    ForgettingParams,
    RevisionScheduler,
)
from academicos.algorithms.learner_model import Interaction, LearnerModel  # noqa: E402
from academicos.algorithms.mastery import KnowledgeMastery  # noqa: E402
from academicos.algorithms.motivation_model import MotivationModel  # noqa: E402

NOW = datetime.now(timezone.utc)


def _observe(model, cid, outcome, days_ago=0):
    model.observe(Interaction(
        concept_id=cid, kind="answer", outcome=outcome,
        ts=(NOW - timedelta(days=days_ago)).isoformat()))
    return model


# ---------------------------------------------------------------- clamps


def test_mastery_clamps_out_of_range_outcome():
    m = _observe(LearnerModel("t"), "c", 1.5)
    r = KnowledgeMastery().score(m, "c")
    assert 0.0 <= r.confidence <= 1.0
    assert 0.0 <= r.mastery <= 1.0


def test_confidence_clamps_out_of_range_outcome():
    m = _observe(LearnerModel("t"), "c", 1.5)
    r = ConfidenceModel().estimate(m, "c")
    assert 0.0 <= r.efficacy <= 1.0
    assert 0.0 <= r.accuracy <= 1.0


def test_motivation_clamps_out_of_range_outcome():
    m = _observe(LearnerModel("t"), "c", 1.5)
    r = MotivationModel().estimate(m)
    assert 0.0 <= r.competence_signal <= 1.0
    assert 0.0 <= r.engagement_signal <= 1.0


def test_mastery_negative_outcome_clamps_to_floor():
    m = _observe(LearnerModel("t"), "c", -0.5)
    r = KnowledgeMastery().score(m, "c")
    assert 0.0 <= r.confidence <= 1.0
    assert 0.0 <= r.mastery <= 1.0


# -------------------------------------------------- future-dated events


def test_mastery_future_dated_event_does_not_overflow():
    m = _observe(LearnerModel("t"), "c", 1.0, days_ago=-4000)
    r = KnowledgeMastery().score(m, "c")
    assert math.isfinite(r.mastery)
    assert math.isfinite(r.confidence)
    assert math.isfinite(r.retention)


def test_confidence_future_dated_event_does_not_overflow():
    m = _observe(LearnerModel("t"), "c", 1.0, days_ago=-4000)
    r = ConfidenceModel().estimate(m, "c")
    assert math.isfinite(r.efficacy)
    assert math.isfinite(r.accuracy)


def test_motivation_future_dated_event_does_not_overflow():
    m = _observe(LearnerModel("t"), "c", 1.0, days_ago=-4000)
    r = MotivationModel().estimate(m)
    assert math.isfinite(r.competence_signal)
    assert math.isfinite(r.engagement_signal)
    assert math.isfinite(r.motivation_score)


# --------------------------------------------------- forgetting plan cap


def test_forgetting_exponential_plan_caps_huge_intervals():
    fm = ForgettingModel(ForgettingParams(model="exponential"))
    sched = RevisionScheduler(fm)
    m = _observe(LearnerModel("t"), "c", 1.0)
    for _ in range(29):
        _observe(m, "c", 1.0)
    plan = sched.plan(m, now=NOW.isoformat())
    for cid, due_iso in plan.next_reviews:
        due = datetime.fromisoformat(due_iso)
        assert due.date() <= datetime.max.date()


def test_forgetting_exponential_still_returns_reasonable_due_date():
    fm = ForgettingModel(ForgettingParams(model="exponential"))
    sched = RevisionScheduler(fm)
    m = _observe(LearnerModel("t"), "c", 1.0)
    for _ in range(4):
        _observe(m, "c", 1.0)
    plan = sched.plan(m, now=NOW.isoformat())
    assert plan.next_reviews  # 5 corrects keep the concept recalled, scheduled ahead
    due = datetime.fromisoformat(plan.next_reviews[0][1])
    assert due.date() >= NOW.date()
