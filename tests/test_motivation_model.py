"""A3 / P2.7 — Deterministic SDT motivation: signals, trend, flags, params."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.algorithms.learner_model import Interaction, LearnerModel
from academicos.algorithms.motivation_model import (
    MotivationModel,
    MotivationParams,
)

NOW = datetime.now(timezone.utc)


def _model(pairs, concept="fractions", learner="t") -> LearnerModel:
    """pairs: list[(days_ago, outcome, affect)]. Returns a LearnerModel."""
    m = LearnerModel(learner)
    for days_ago, outcome, affect in pairs:
        m.observe(Interaction(
            concept_id=concept, kind="answer", outcome=outcome, affect=affect,
            ts=(NOW - timedelta(days=days_ago)).isoformat()))
    return m


def _est(pairs, params=None, concept="fractions"):
    return MotivationModel(params).estimate(_model(pairs, concept=concept))


def test_empty_history_neutral():
    r = MotivationModel().estimate(LearnerModel("empty"))
    assert r.motivation_score == pytest.approx(0.5)
    assert r.competence_signal == pytest.approx(0.5)
    assert r.engagement_signal == pytest.approx(0.5)
    assert r.persistence_signal == pytest.approx(0.5)
    assert r.trend == pytest.approx(0.0)
    assert r.flagged_low is False


def test_all_correct_engaged_daily_intrinsic():
    pairs = [(d, 1.0, "engaged") for d in range(14)]
    r = _est(pairs)
    assert r.motivation_score > 0.8
    assert r.type == "intrinsic"
    assert r.competence_signal > 0.9
    assert r.flagged_intrinsic is True
    assert r.flagged_low is False


def test_success_raises_signal_more_than_failure():
    good = _est([(d, 1.0, "neutral") for d in range(6)])
    bad = _est([(d, 0.0, "neutral") for d in range(6)])
    assert good.competence_signal > bad.competence_signal
    assert good.motivation_score > bad.motivation_score


def test_recent_success_outperforms_old_success():
    # Same effort, same affect pattern — only the pass/fail *position in
    # time* differs: recent passes dominate old passes (7-day half-life).
    recent_passes = ([(d, 0.0, "engaged") for d in (13, 14)]
                     + [(d, 1.0, "engaged") for d in (0, 1, 2)])
    old_passes = ([(d, 1.0, "engaged") for d in (13, 14)]
                  + [(d, 0.0, "engaged") for d in (0, 1, 2)])
    r_new = _est(recent_passes)
    r_old = _est(old_passes)
    assert r_new.competence_signal > r_old.competence_signal
    assert r_new.motivation_score > r_old.motivation_score


def test_sparse_study_days_lower_persistence():
    dense = _est([(d, 0.8, "neutral") for d in range(5)])
    sparse = _est([(0, 0.8, "neutral"), (3, 0.8, "neutral"),
                   (8, 0.8, "neutral"), (13, 0.8, "neutral")])
    assert dense.persistence_signal > sparse.persistence_signal


def test_single_activity_zero_persistence():
    r = _est([(0, 1.0, "engaged")])
    assert r.persistence_signal == 0.0


def test_trend_recent_vs_earlier_window():
    grow = ([(d, 0.0, "frustrated") for d in range(13, 7, -1)]
            + [(d, 1.0, "engaged") for d in range(5, -1, -1)])
    shrink = ([(d, 1.0, "engaged") for d in range(13, 7, -1)]
              + [(d, 0.0, "frustrated") for d in range(5, -1, -1)])
    assert _est(grow).trend > 0.2
    assert _est(shrink).trend < -0.2


def test_type_bands_intrinsic_extrinsic_fragile():
    intrinsic = _est([(d, 1.0, "engaged") for d in range(14)])
    extrinsic = _est([(d, 0.5, "neutral") for d in range(6)])
    fragile = _est([(d, 0.0, "frustrated") for d in range(6)])
    assert intrinsic.type == "intrinsic"
    assert extrinsic.type == "extrinsic"
    assert fragile.type == "fragile"


def test_intrinsic_flag_needs_persistence_and_affect():
    strong = _est([(d, 1.0, "engaged") for d in range(14)])
    neutral_affect = _est([(d, 1.0, "neutral") for d in range(14)])
    sparse = _est([(0, 1.0, "engaged"), (1, 1.0, "engaged")])
    assert strong.flagged_intrinsic is True
    assert neutral_affect.flagged_intrinsic is False   # valence ~0.6, not >0.6
    assert sparse.flagged_intrinsic is False           # persistence low


def test_low_flag_triggers_only_for_fragile():
    low = _est([(d, 0.0, "frustrated") for d in range(6)])
    fine = _est([(d, 1.0, "engaged") for d in range(14)])
    assert low.flagged_low is True
    assert fine.flagged_low is False


def test_params_roundtrip():
    params = MotivationParams(w_competence=0.3, w_persistence=0.3,
                              low_threshold=0.3, min_recent=3,
                              recency_half_life_days=3.5)
    r = MotivationModel(params).estimate(_model([(0, 1.0, "engaged")]))
    assert r.params["model"] == "sdt"
    assert r.params["w_competence"] == 0.3
    assert r.params["w_persistence"] == 0.3
    assert r.params["low_threshold"] == 0.3
    assert r.params["recency_half_life_days"] == 3.5


def test_list_input_ducktype_and_deterministic():
    # plain list of Interactions is accepted (duck-typed, no model required)
    model = _model([(0, 1.0, "engaged"), (1, 1.0, "engaged")])
    events = model.concepts["fractions"].history
    r1 = MotivationModel().estimate(events)
    assert r1.learner_id == "anonymous"
    r2 = MotivationModel().estimate(list(reversed(events)))  # order-safe
    assert r1.motivation_score == r2.motivation_score
    # same input a second time -> identical
    r3 = MotivationModel().estimate(events)
    assert r1.motivation_score == r3.motivation_score
    assert r1.type == r3.type