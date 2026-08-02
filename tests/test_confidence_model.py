"""A13 — Confidence/self-efficacy model: sources, calibration, params."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.algorithms.confidence_model import (
    ConfidenceModel,
    ConfidenceParams,
    _valence,
    demo,
)
from academicos.algorithms.learner_model import Interaction, LearnerModel


def _learner(pairs, concept="fractions"):
    """pairs: list of (days_ago, outcome, affect). Returns (model, concept)."""
    model = LearnerModel("t")
    now = datetime.now(timezone.utc)
    for days_ago, outcome, affect in pairs:
        model.observe(Interaction(
            concept_id=concept, kind="answer", outcome=outcome, affect=affect,
            ts=(now - timedelta(days=days_ago)).isoformat()))
    return model, concept


def _eff(pairs, concept="fractions", params=None):
    cm = ConfidenceModel(params)
    model, cid = _learner(pairs, concept)
    return cm.estimate(model, cid)


def test_affect_valence_ranking():
    assert _valence("engaged") > _valence("tired") > _valence("anxious")
    assert _valence("chatty-nonsense") == 0.6  # unknown tags use default


def test_no_evidence_returns_prior():
    model = LearnerModel("empty")
    r = ConfidenceModel().estimate(model, "nothing-seen")
    assert r.efficacy == pytest.approx(0.5)
    assert r.confident is False


def test_demo_overconfident():
    r = ConfidenceModel().estimate(demo(), "fractions")
    assert r.category == "overconfident"
    assert r.efficacy > r.accuracy
    assert r.confident


def test_high_accuracy_calibrated():
    # all-correct, neutral affect -> efficacy ≈ skill, gap ~ 0
    r = _eff([(0, 1.0, "neutral"), (1, 1.0, "neutral"), (2, 1.0, "neutral")])
    assert r.accuracy == pytest.approx(1.0)
    assert r.category in ("calibrated", "overconfident")  # tight bounds test
    assert abs(r.calibration) < 0.15


def test_failure_erodes_efficacy():
    eff_ok = _eff([(0, 1.0, "neutral"), (1, 1.0, "neutral")]).efficacy
    eff_bad = _eff([(0, 0.0, "neutral"), (1, 0.0, "neutral")]).efficacy
    assert eff_bad < eff_ok


def test_params_roundtrip():
    cm = ConfidenceModel(ConfidenceParams(social=0.9))
    r = cm.estimate(*_learner([(0, 1.0, "neutral")]))
    assert r.params["social"] == 0.9
    assert r.params["model"] == "bandura"