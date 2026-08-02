"""P2.4 — per-learner FSRS fitting (scalar v1 surrogate) tests.

Covers the contract: empty/short histories, monotone improvement, strict
determinism, finite weights (no NaN on zero gaps), 0 vs 1 outcomes, long
chains, learner_id / params bookkeeping, weight bounds, and a synthesized
self-consistent learner whose true stability the surrogate should recover
with ``gain > 0``.
"""
from __future__ import annotations

import math
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.algorithms.fsrs_fit import (  # noqa: E402
    BOUNDS, DEFAULT_WEIGHTS, FSRSFit, FitParams, FitResult,
)
from academicos.algorithms.learner_model import Interaction  # noqa: E402

START = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
DEFAULT_WEIGHTS_LIST = list(DEFAULT_WEIGHTS)


def it(concept: str, days: int, outcome: float,
       difficulty: float | None = None) -> Interaction:
    """Answer interaction at ``days`` days after the reference epoch."""
    return Interaction(concept_id=concept, kind="answer", outcome=outcome,
                       difficulty=difficulty,
                       ts=(START + timedelta(days=days)).isoformat())


def history(concept: str, gap_days: list[float],
            outcomes: list[float]) -> list[Interaction]:
    """``gap_days[0]`` events after the first; 0 gaps = single review."""
    reviews = [0.0] + list(gap_days)
    ts = START
    events = []
    for d, o in zip(reviews, outcomes):
        ts = START + timedelta(days=d)
        events.append(Interaction(concept_id=concept, kind="answer",
                                  outcome=o, ts=ts.isoformat()))
    return events


# ------------------------------------------------------------ history edges

def test_empty_history_returns_defaults():
    res = FSRSFit().fit([])
    assert res.n_reviews == 0 and res.n_observed == 0
    assert res.converged is False
    assert res.loss_before == res.loss_after == 0.0
    assert res.gain == 0.0
    assert res.fitted_weights == DEFAULT_WEIGHTS_LIST
    assert res.default_lr == DEFAULT_WEIGHTS_LIST


def test_single_review_has_no_interval():
    # one answer, one concept -> no gap to calibrate against
    res = FSRSFit().fit([it("c", 0, 1.0)], learner_id="solo")
    assert res.n_reviews == 1 and res.n_observed == 0
    assert res.converged is False
    assert res.fitted_weights == DEFAULT_WEIGHTS_LIST
    assert res.loss_after == 0.0


def test_non_answer_events_ignored():
    events = [
        Interaction(concept_id="a", kind="watch", outcome=None,
                    ts=START.isoformat()),
        Interaction(concept_id="a", kind="answer", outcome=1.0,
                    ts=(START + timedelta(days=2)).isoformat()),
        Interaction(concept_id="a", kind="session_end", outcome=None,
                    ts=(START + timedelta(days=4)).isoformat()),
    ]
    res = FSRSFit().fit(events)
    assert res.n_reviews == 1 and res.n_observed == 0


# -------------------------------------------------------- boundary + fitting

def test_two_reviews_converges_quickly():
    res = FSRSFit().fit(history("frac", [3.0], [1.0, 1.0]))
    assert res.n_observed == 1
    assert res.converged is True
    assert res.loss_after <= res.loss_before + 1e-9
    assert all(math.isfinite(v) for v in res.fitted_weights)


def test_loss_improves_on_consistent_learner():
    # a steady, mostly-correct learner: defaults underestimate stability a lot
    good = FSRSFit().fit(
        history("c", [1.0, 2.0, 4.0, 8.0, 16.0, 1.0, 2.5, 6.0, 12.0],
                [1.0] * 10))
    assert good.n_observed == 9
    assert 0.0 <= good.gain <= 1.0
    assert good.loss_after < good.loss_before


def test_loss_improves_on_erratic_learner():
    # mixed success/failure: the surrogate still fits better than defaults
    erratic = FSRSFit().fit(history(
        "c", [1.0, 0.5, 0.0, 2.0, 3.0, 1.0, 4.0, 2.0, 1.5, 6.0, 3.0],
        [1.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0, 1.0, 0.5, 1.0]))
    assert erratic.n_observed >= 5
    assert erratic.loss_after < erratic.loss_before
    assert erratic.gain > 0.0


def test_outcome_zero_and_one_both_handled():
    # y=0 reviews (lapses) push stability down; y=1 handle the growth path
    mixed = FSRSFit().fit(history(
        "c", [1.0, 1.0, 1.0, 1.0, 1.0], [1.0, 0.0, 1.0, 0.0, 1.0]))
    assert all(math.isfinite(v) for v in mixed.fitted_weights)
    assert math.isfinite(mixed.loss_before) and math.isfinite(mixed.loss_after)
    assert mixed.gain >= 0.0


def test_zero_elapsed_never_nan():
    # two reviews at the same timestamp produce elapsed == 0 -> pred = 1.0
    events = [
        Interaction(concept_id="same", kind="answer", outcome=1.0,
                    ts=START.isoformat()),
        Interaction(concept_id="same", kind="answer", outcome=1.0,
                    ts=START.isoformat()),
    ]
    res = FSRSFit().fit(events)
    assert all(math.isfinite(v) for v in res.fitted_weights)
    assert math.isfinite(res.loss_after)


def test_long_review_chain():
    n = 40
    days = [float(1 + i % 5) for i in range(n - 1)]
    outcomes = [1.0 if i % 4 else 0.0 for i in range(n)]
    res = FSRSFit().fit(history("c", days, outcomes))
    assert res.n_reviews == n
    assert res.n_observed == n - 1
    assert res.loss_after <= res.loss_before + 1e-9


# ------------------------------------------------------------- determinism

def test_deterministic_same_input_identical_results():
    hist = history("c", [1.0, 2.0, 3.0, 5.0, 8.0],
                   [1.0, 1.0, 0.0, 1.0, 1.0])
    a = FSRSFit().fit(hist)
    b = FSRSFit().fit(hist)
    assert a.fitted_weights == b.fitted_weights
    assert a.loss_before == b.loss_before
    assert a.loss_after == b.loss_after
    assert a.converged == b.converged


def test_seed_change_may_perturb_path_but_result_valid():
    hist = history("c", [1.0, 2.0, 4.0, 8.0, 16.0], [1.0] * 5)
    r0 = FSRSFit(FitParams(seed=0)).fit(hist)
    r1 = FSRSFit(FitParams(seed=7)).fit(hist)
    assert r1.loss_after <= r1.loss_before + 1e-9
    assert all(math.isfinite(w) for w in r1.fitted_weights)


# ---------------------------------------------------------------- bookkeeping

def test_learner_id_field():
    res = FSRSFit().fit(history("c", [2.0, 2.0], [1.0, 1.0]), learner_id="alice")
    assert res.learner_id == "alice"


def test_params_roundtrip():
    p = FitParams(model="fsrs-optimized", learning_rate=0.05, max_iter=40,
                  prediction_horizon=False, loss="rmse", reg=1e-3, seed=3)
    res = FSRSFit(p).fit(history("c", [1.0, 1.0, 1.0], [1.0, 1.0, 1.0]))
    assert res.params == p
    assert res.params.model == p.model
    assert res.params.learning_rate == p.learning_rate


def test_weights_stay_in_sane_bounds():
    # stability can't be negative; sens >= 0; gain >= 1 by construction
    res = FSRSFit().fit(history("c", [1.0, 2.0, 4.0, 8.0, 16.0],
                                [1.0, 1.0, 0.0, 1.0, 1.0]))
    w = res.fitted_weights
    for value, (lo, hi) in zip(w, BOUNDS):
        assert lo <= value <= hi
        assert math.isfinite(value)
    assert w[2] >= 1.0


# ----------------------------------------------------- synthesized validation

def test_synthetic_self_consistent_learner_is_fit_with_gain():
    """Grow a learner whose true stability follows exp(-t/S); recover it."""
    rng = random.Random(42)
    s = 6.0                      # true stability (days) of this learner
    events, ts = [], START
    for k in range(30):
        ts = ts + timedelta(days=1.0 + rng.uniform(0.0, 4.0))
        # outcome follows the true exponential forgetting curve
        if events:
            prev_ts = datetime.fromisoformat(events[-1].ts)
            elapsed = (ts - prev_ts).total_seconds() / 86400.0
            recall = math.exp(-elapsed / s)
        else:
            recall = 1.0
        outcome = 1.0 if rng.random() < max(0.05, recall) else 0.0
        events.append(Interaction(concept_id="syn", kind="answer",
                                  outcome=outcome, ts=ts.isoformat()))
        s = s * 2.0 if outcome >= 0.5 else s * 0.6
    res = FSRSFit().fit(events)
    assert res.n_observed == len(events) - 1
    assert res.loss_after < res.loss_before
    assert res.gain > 0.0
    assert all(math.isfinite(w) for w in res.fitted_weights)