"""A4 — Attention/fatigue model: time-on-task decay, affect hazard, breaks."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.algorithms.attention_model import (
    AttentionModel,
    CurvePoint,
    FatigueParams,
    SessionAttentionParams,
    _fatigue_state,
    _verdict,
)
from academicos.algorithms.learner_model import Interaction

BASE = "2026-03-01T09:00:00+00:00"


def _at(minutes: float, affect: str | None = "neutral") -> Interaction:
    ts = datetime.fromisoformat(BASE) + timedelta(minutes=minutes)
    return Interaction(concept_id="c", kind="watch", affect=affect, ts=ts.isoformat())


def _run(offsets, affects=None, params=None, start=None, now=None):
    affects = affects or ["neutral"] * len(offsets)
    m = AttentionModel(params)
    return m.estimate(start or BASE, [_at(o, a) for o, a in zip(offsets, affects)],
                      now=now)


def test_empty_session_defaults_to_focused():
    r = AttentionModel().estimate(None, [])
    assert r.fatigue_state == "focused"
    assert r.attention_curve[0].attention == pytest.approx(1.0)
    assert r.attention_curve[0].verdict == "focused"
    assert r.computed_uptime_minutes == 0.0


def test_first_minute_focused():
    r = _run([1.0])
    assert r.attention_curve[-1].verdict == "focused"
    assert r.attention_curve[-1].attention > 0.9


def test_last_point_waning_far_boundary():
    r = _run([18.0])          # attentive budget ~25min -> residual in [0.2,0.5)
    assert r.attention_curve[-1].verdict == "waning"
    assert r.attention_curve[-1].attention < 0.5  # by construction
    assert FatigueParams().attention_exponent == pytest.approx(1.7)
    assert FatigueParams().max_attention_minutes == pytest.approx(25.0)


def test_way_beyond_max_is_fatigued():
    r = _run([90.0])
    assert r.attention_curve[-1].attention == pytest.approx(0.0)
    assert r.attention_curve[-1].verdict == "fatigued"
    assert r.fatigue_state == "fatigued"
    assert r.params["rest_needed_minutes"] > 0


def test_engaged_decays_slower_than_tired():
    r_engaged = _run([10.0, 20.0, 30.0], affects=["engaged"] * 3)
    r_tired = _run([10.0, 20.0, 30.0], affects=["tired"] * 3)
    for ea, ta in zip(r_engaged.attention_curve, r_tired.attention_curve):
        assert ea.attention > ta.attention


def test_strictly_monotonic_non_increasing_curve():
    r = _run([0.0, 5.0, 10.0, 20.0, 40.0])
    atts = [pt.attention for pt in r.attention_curve]
    assert all(b <= a for a, b in zip(atts, atts[1:]))


def test_break_between_sessions_resets_no_carryover():
    r1 = _run([60.0])                      # long first session, floor exhausted
    starts2 = (datetime.fromisoformat(BASE) + timedelta(hours=3)).isoformat()
    second = (datetime.fromisoformat(starts2) + timedelta(minutes=1)).isoformat()
    r2 = AttentionModel().estimate(starts2,
                                   [Interaction(concept_id="c", kind="watch",
                                                affect="neutral",
                                                ts=second)])
    minute1_b1 = r1.attention_curve[-1].attention    # saturated ~0
    minute1_b2 = r2.attention_curve[-1].attention    # fresh ~1-(1/25)^1.7
    assert minute1_b2 == pytest.approx(1 - (1 / 25) ** 1.7, abs=5e-4)
    assert minute1_b2 > minute1_b1 * 0.99          # new session ≈ full attention


def test_now_param_only_source_of_wallclock():
    now = (datetime.fromisoformat(BASE) + timedelta(hours=2)).isoformat()
    r_up = _run([5.0], now=now)
    assert r_up.computed_uptime_minutes == pytest.approx(120.0, abs=0.02)
    assert r_up.params  # parametrisation dict present


def test_zero_duration_no_division_by_zero():
    r = _run([0.0, 0.0])
    assert all(pt.attention == pytest.approx(1.0) for pt in r.attention_curve)


def test_param_driven_budget_and_exponent():
    p = FatigueParams(max_attention_minutes=50.0, attention_exponent=2.0)
    r = _run([25.0], params=p)
    assert r.attention_curve[-1].attention == pytest.approx(1 - (25 / 50) ** 2)


def test_single_observation_round():
    r = _run([12.0])
    assert len(r.attention_curve) >= 1
    assert all(isinstance(pt.verdict, str) and pt.verdict in
               ("focused", "distracted", "waning", "fatigued")
               for pt in r.attention_curve)


def test_params_roundtrip_contract():
    r = _run([3.0])
    assert r.params["model"] == "time_on_air"
    assert r.params["hazard_rate_others"]["frustrated"] == pytest.approx(1.8)
    assert r.params["hazard_rate_others"]["engaged"] == pytest.approx(0.8)