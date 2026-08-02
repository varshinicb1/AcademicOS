"""A6 — emotion/affect summary: valence-arousal aggregation, dominance, ratio."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.algorithms.emotion_model import (  # noqa: E402
    EmotionModel,
    EmotionParams,
    demo,
)
from academicos.algorithms.learner_model import Interaction  # noqa: E402

T0 = "2026-01-15T10:00:00+00:00"


def _i(concept, affect, idx=0, outcome=None, kind="answer"):
    return Interaction(
        concept_id=concept, kind=kind, outcome=outcome, affect=affect,
        ts=f"2026-01-15T10:{idx:02d}:00+00:00",
    )


def _r(interactions, params=None, now=None):
    return EmotionModel(params).estimate(interactions, now=now)


def _bucket(v, high=0.55, low=0.45):
    return "positive" if v >= high else "negative" if v <= low else "neutral"


def test_empty_history_returns_neutral_defaults():
    r = _r([])
    assert r.valence == pytest.approx(0.6)
    assert r.arousal == pytest.approx(0.5)
    assert r.dominant_primary == "neutral"
    assert r.dominant_affect is None
    assert r.positive_ratio == pytest.approx(0.0)
    assert r.n_snapshots == 0
    assert r.per_concept == {}


def test_single_happy_snapshot():
    r = _r([_i("c1", "happy", idx=0)])
    assert r.valence == pytest.approx(0.85)
    assert r.arousal == pytest.approx(0.7)
    assert r.dominant_primary == "positive"
    assert r.dominant_affect == "happy"
    assert r.n_snapshots == 1


def test_affect_to_map_for_representative_tags():
    cases = {
        "happy": (0.85, 0.7, "positive"),
        "frustrated": (0.25, 0.5, "negative"),
        "anxious": (0.2, 0.85, "negative"),
        "tired": (0.3, 0.25, "negative"),
        "neutral": (0.6, 0.5, "positive"),
    }
    for tag, (exp_v, exp_a, _exp_b) in cases.items():
        r = _r([_i("c1", tag, idx=0)])
        assert r.valence == pytest.approx(exp_v), tag
        assert r.arousal == pytest.approx(exp_a), tag
        assert r.dominant_primary == _bucket(exp_v), tag
        assert r.dominant_affect == tag, tag


def test_dominant_primary_majority_positive_beats_negative():
    # 3 happy (0.85) + 2 frustrated (0.25) -> mean 0.61 -> positive
    r = _r([_i("c1", "happy", idx=i) for i in range(3)]
           + [_i("c1", "frustrated", idx=3 + i) for i in range(2)])
    assert r.valence == pytest.approx(0.61)
    assert r.dominant_primary == "positive"
    assert r.dominant_affect == "happy"       # share 0.6 == w_primary


def test_dominant_primary_majority_negative():
    # 1 happy (0.85) + 3 anxious (0.2) -> mean 0.3625 -> negative
    r = _r([_i("c1", "happy", idx=0)]
           + [_i("c1", "anxious", idx=1 + i) for i in range(3)])
    assert r.dominant_primary == "negative"
    assert r.positive_ratio == pytest.approx(0.25)


def test_mixed_history_mixed_dominant_affect():
    # two tags split 3/3 -> share 0.5 < w_primary -> not a single dominant tag
    r = _r([_i("c1", "happy", idx=i) for i in range(3)]
           + [_i("c1", "anxious", idx=3 + i) for i in range(3)])
    assert r.dominant_affect is None
    assert r.dominant_primary == _bucket((3 * 0.85 + 3 * 0.2) / 6)


def test_per_concept_accumulation():
    r = _r([_i("c1", "happy", idx=0), _i("c1", "happy", idx=1),
            _i("c2", "frustrated", idx=2), _i("c2", "tired", idx=3)])
    assert r.per_concept["c1"].valence == pytest.approx(0.85)
    assert r.per_concept["c1"].dominant_primary == "positive"
    assert r.per_concept["c2"].valence == pytest.approx(0.275)
    assert r.per_concept["c2"].dominant_primary == "negative"
    assert r.per_concept["c1"].n_snapshots == 2


def test_positive_ratio():
    # happy(0.85), happy(0.85), neutral(0.6), angry(0.15)
    r = _r([_i("c1", "happy", idx=0), _i("c1", "happy", idx=1),
            _i("c1", "neutral", idx=2), _i("c1", "angry", idx=3)])
    assert r.positive_ratio == pytest.approx(0.75)   # 3 of 4 >= 0.55


def test_untagged_snapshots_use_neutral_default():
    r = _r([_i("c1", None, idx=0), _i("c1", None, idx=1)])
    assert r.valence == pytest.approx(0.6)
    assert r.arousal == pytest.approx(0.5)
    assert r.dominant_affect is None
    assert r.n_snapshots == 2


def test_time_order_independence():
    a = [_i("c1", "happy", 0), _i("c2", "frustrated", 1), _i("c1", "anxious", 2)]
    rev = a[::-1]
    assert _r(a).valence == _r(rev).valence
    assert _r(a).arousal == _r(rev).arousal
    assert _r(a).positive_ratio == _r(rev).positive_ratio
    assert _r(a).per_concept == _r(rev).per_concept


def test_timestamps_and_now_do_not_change_aggregate():
    early = [_i("c1", "happy", idx=0), _i("c1", "frustrated", idx=1)]
    late = [_i("c1", "happy", idx=99), _i("c1", "frustrated", idx=100)]
    r1 = _r(early, now="2025-01-01T00:00:00+00:00")
    r2 = _r(late, now="2027-06-30T23:59:59+00:00")
    assert r1.valence == r2.valence
    assert r1.arousal == r2.arousal
    assert r1.dominant_primary == r2.dominant_primary


def test_demo_is_deterministic():
    r1 = _r(demo())
    r2 = _r(demo())
    assert r1 == r2
    assert r1.n_snapshots == 4


def test_deterministic_params_roundtrip_via_results():
    p = EmotionParams(w_primary=0.7, positive_threshold=0.5)
    r1 = EmotionModel(p).estimate([_i("c1", "happy", idx=0)])
    restored = EmotionParams(**r1.params)
    assert restored == p
    r2 = EmotionModel(restored).estimate([_i("c1", "happy", idx=0)])
    assert r1.params == r2.params
    assert r1.valence == r2.valence