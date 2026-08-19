"""A7 — Curiosity Engine: Berlyne + Bjork cue weighting, skipping, determinism."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.algorithms.curiosity_engine import (  # noqa: E402
    CandidateScore,
    CuriosityEngine,
    CuriosityParams,
    CuriosityResult,
)
from academicos.algorithms.learner_model import ConceptState, Interaction, LearnerModel  # noqa: E402


def _known(cid, attempts=0, correct=0, mastery=0.0, outcomes=None):
    state = ConceptState(concept_id=cid, attempts=attempts, correct=correct, mastery=mastery)
    for o in (outcomes or []):
        state.record(Interaction(
            concept_id=cid, kind="answer", outcome=o,
            ts=datetime.now(timezone.utc).isoformat()))
    return state


def test_empty_candidates_returns_empty_result():
    eng = CuriosityEngine()
    r = eng.rank(LearnerModel("t"), [], current_concept="c0")
    assert isinstance(r, CuriosityResult)
    assert r.ranked == []
    assert r.source_concept == "c0"
    assert r.version == "1.0"


def test_novelty_wins_on_empty_model_and_in_band():
    eng = CuriosityEngine()
    r = eng.rank(LearnerModel("t"), [{"concept_id": "xx", "difficulty": 0.75}])
    assert len(r.ranked) == 1
    # novelty 1.0 * .35 + desired(0.75)=e^(-.1^2/(2*.15^2))*.35 + momentum .5*.15 + .2 bonus
    top = r.ranked[0]
    assert top.novelty == 1.0
    expected = round(0.9053, 4)
    assert top.score == pytest.approx(expected, abs=5e-4)


def test_desired_peak_beats_band_edge():
    eng = CuriosityEngine()
    r = eng.rank(LearnerModel("t"), [
        {"concept_id": "mid", "difficulty": 0.65},   # exact Gaussian peak (cue = 1.0)
        {"concept_id": "edge", "difficulty": 0.85},  # inside band but lower cue
    ])
    assert r.ranked[0].concept_id == "mid"
    assert r.ranked[1].concept_id == "edge"
    assert r.ranked[0].score > r.ranked[1].score


def test_mastered_candidate_is_skipped():
    m = LearnerModel("t")
    # mastery computed at use from real evidence: 6 correct answers -> 0.80,
    # exactly the mastery_threshold, so the concept must be skipped
    m.concepts["known"] = _known("known", outcomes=[1.0] * 6)
    r = CuriosityEngine().rank(m, [{"concept_id": "known", "difficulty": 0.65},
                                   {"concept_id": "novel", "difficulty": 0.65}])
    assert [c.concept_id for c in r.ranked] == ["novel"]


def test_difficulty_band_prefers_dot75_over_dot2_when_novelty_ties():
    m = LearnerModel("t")
    m.concepts["a"] = _known("a", attempts=2, correct=0, outcomes=[0.0, 0.0])
    m.concepts["b"] = _known("b", attempts=2, correct=0, outcomes=[0.0, 0.0])
    r = CuriosityEngine().rank(m, [{"concept_id": "a", "difficulty": 0.75},
                                   {"concept_id": "b", "difficulty": 0.2}])
    by = {c.concept_id: c.score for c in r.ranked}
    # a: .35*desired(.75)=.2803 + 0 momentum - .2 penalty = .0803 ; b: out-of-band -> 0
    assert by["a"] == pytest.approx(0.0803, abs=5e-4)
    assert by["b"] == 0.0
    assert by["a"] > by["b"]


def test_novelty_breaks_tie_novel_above_known():
    m = LearnerModel("t")
    m.concepts["known"] = _known("known")
    r = CuriosityEngine().rank(m, [{"concept_id": "known", "difficulty": 0.65},
                                   {"concept_id": "new", "difficulty": 0.65}])
    by = {c.concept_id: c for c in r.ranked}
    assert r.ranked[0].concept_id == "new"
    assert by["new"].novelty == 1.0 and by["known"].novelty == 0.0
    # new: .35+.35+.075+.2=.975 ; known: .35+.075-.2(penalty_seen) = .225
    assert by["new"].score == pytest.approx(0.975, abs=5e-4)
    assert by["known"].score == pytest.approx(0.225, abs=5e-4)


def test_interleaving_bonus_for_cross_domain():
    r = CuriosityEngine().rank(LearnerModel("t"), [
        {"concept_id": "c1", "difficulty": 0.65, "domain": "math"},
        {"concept_id": "c2", "difficulty": 0.65, "domain": "chem"},
    ], current_concept="c1")
    assert r.ranked[0].concept_id == "c2"  # cross-domain gets the interleave bonus
    assert r.ranked[0].interleave is True
    assert r.ranked[1].interleave is False
    assert r.ranked[0].score == pytest.approx(1.0, abs=5e-4)   # .975 + .15, clamped
    assert r.ranked[1].score == pytest.approx(0.975, abs=5e-4)


def test_no_source_gives_no_interleave_bonus():
    r = CuriosityEngine().rank(LearnerModel("m"), [
        {"concept_id": "c2", "difficulty": 0.65, "domain": "chem"},
        {"concept_id": "c1", "difficulty": 0.65, "domain": "math"},
    ])
    assert all(c.interleave is False for c in r.ranked)
    # identical scores (no bonus) -> the alphabetic tie-break decides
    assert [c.concept_id for c in r.ranked] == ["c1", "c2"]


def test_stable_tie_break_alphabetical():
    r = CuriosityEngine().rank(LearnerModel("t"), [
        {"concept_id": "zebra", "difficulty": 0.65},
        {"concept_id": "apple", "difficulty": 0.65},
        {"concept_id": "mango", "difficulty": 0.65},
    ])
    assert [c.concept_id for c in r.ranked] == ["apple", "mango", "zebra"]


def test_params_roundtrip():
    eng = CuriosityEngine(CuriosityParams(w_novelty=0.4, novelty_bonus=0.3,
                                          penalty_seen=0.1))
    r = eng.rank(LearnerModel("t"), [{"concept_id": "x", "difficulty": 0.65}])
    assert r.params["w_novelty"] == 0.4
    assert r.params["novelty_bonus"] == 0.3
    assert r.params["penalty_seen"] == 0.1
    assert r.params["model"] == "berlyne-bjork"
    assert r.params["desired_difficulty_band"] == [0.5, 0.85]


def test_scores_clamped_to_unit_interval():
    up = CuriosityParams(w_novelty=0.5, w_desired_difficulty=0.5,
                         w_interest_momentum=0.5, novelty_bonus=0.2)
    r_hi = CuriosityEngine(up).rank(LearnerModel("t"), [{"concept_id": "x", "difficulty": 0.65}])
    assert r_hi.ranked[0].score == 1.0

    down = CuriosityParams(penalty_seen=0.8)
    m = LearnerModel("t")
    m.concepts["y"] = _known("y")
    r_lo = CuriosityEngine(down).rank(m, [{"concept_id": "y", "difficulty": 0.65}])
    assert r_lo.ranked[0].score == 0.0


def test_result_field_names():
    r = CuriosityEngine().rank(LearnerModel("t"), [{"concept_id": "x", "difficulty": 0.65}])
    for f in ("source_concept", "ranked", "params", "version"):
        assert hasattr(r, f)
    c = r.ranked[0]
    assert isinstance(c, CandidateScore)
    for f in ("concept_id", "score", "novelty", "interleave", "momentum", "reasons", "overall"):
        assert hasattr(c, f)
    assert c.overall == c.score
    assert c.reasons