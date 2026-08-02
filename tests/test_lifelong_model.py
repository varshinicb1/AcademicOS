"""A14 — Lifelong/longitudinal learner model: academic year, continuity,
cross-subject growth (all deterministic from the event log)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.algorithms.learner_model import Interaction
from academicos.algorithms.lifelong_model import LifelongLearner, academic_year


def analyze_events(events, learner="x"):
    return LifelongLearner(learner).analyze(events)


def ev(concept, outcome, ts):
    return Interaction(concept_id=concept, kind="answer", outcome=outcome, ts=ts)


def test_cbse_academic_year_boundaries():
    assert academic_year("2025-04-01T00:00:00+00:00") == "2025-26"
    assert academic_year("2026-03-31T23:59:59+00:00") == "2025-26"
    assert academic_year("2026-02-15T10:00:00+00:00") == "2025-26"
    assert academic_year("2025-03-31T23:59:59+00:00") == "2024-25"


def test_years_are_ascending_and_bucketed():
    events = [
        ev("fractions", 1.0, "2024-09-15T00:00:00+00:00"),
        ev("fractions", 1.0, "2026-01-15T00:00:00+00:00"),
    ]
    r = LifelongLearner("a").analyze(events)
    assert r.years == ["2024-25", "2025-26"]
    assert r.portraits["2024-25"].accuracy == 1.0


def test_recurring_concept_detected_with_per_year_accuracy():
    events = [
        ev("fractions", 0.0, "2024-09-15T00:00:00+00:00"),
        ev("fractions", 1.0, "2025-09-15T00:00:00+00:00"),
        ev("fractions", 1.0, "2025-09-16T00:00:00+00:00"),
    ]
    r = LifelongLearner("b").analyze(events)
    assert "fractions" in r.recurring
    cont = [c for c in r.continuity if c.concept == "fractions"][0]
    assert cont.chain[0][0] == "2024-25" and cont.chain[0][1] == 0.0
    assert cont.chain[-1][0] == "2025-26" and cont.chain[-1][1] == 1.0
    assert cont.improves == pytest.approx(1.0)


def test_growth_is_last_minus_first_year_accuracy():
    events = [
        ev("a", 0.0, "2023-09-15T00:00:00+00:00"),   # year 2023-24, acc 0.0
        ev("b", 1.0, "2025-09-15T00:00:00+00:00"),   # year 2025-26, acc 1.0
    ]
    r = LifelongLearner("c").analyze(events)
    assert r.growth == pytest.approx(1.0)


def test_subject_breakdown_and_accuracy():
    events = [
        ev("c-fractions", 1.0, "2026-01-15T00:00:00+00:00"),
        ev("e-poetry", 0.0, "2026-01-15T00:00:00+00:00"),
        ev("e-poetry", 1.0, "2026-01-16T00:00:00+00:00"),
    ]
    subj = lambda c: ("math" if c.startswith("c-") else "eng")
    r = LifelongLearner("d", subject_of=subj).analyze(events)
    assert r.subjects["math"] == pytest.approx(1.0)
    assert r.subjects["eng"] == pytest.approx(0.5)
    # portrait subject breakdown reflects event counts
    yp = r.portraits[r.years[-1]]
    assert yp.subject_breakdown["math"] == 1
    assert yp.subject_breakdown["eng"] == 2


def test_confident_requires_two_years_and_events():
    one_year = [ev("a", 1.0, "2026-01-15T00:00:00+00:00")] * 6
    assert LifelongLearner("e").analyze(one_year).confident is False  # one year
    across_two_years = [
        ev("a", 1.0, "2025-01-15T00:00:00+00:00"),
        ev("b", 1.0, "2025-02-15T00:00:00+00:00"),
        ev("c", 1.0, "2026-01-15T00:00:00+00:00"),
        ev("c", 1.0, "2026-01-16T00:00:00+00:00"),
        ev("c", 1.0, "2026-01-17T00:00:00+00:00"),
    ]
    assert LifelongLearner("f").analyze(across_two_years).confident is True  # ≥5 events & 2 years


def test_as_dict_serializes():
    events = [ev("a", 1.0, "2025-03-15T00:00:00+00:00"),   # 2024-25
              ev("a", 1.0, "2026-01-15T00:00:00+00:00")]   # 2025-26
    d = LifelongLearner("g").analyze(events).as_dict()
    assert d["years"] == ["2024-25", "2025-26"]
    assert d["growth"] == round(0.0, 3)
    assert "annual" in d and "continuity" in d