"""A10 — Career Discovery: RIASEC mapping determinism, params, confidence."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.algorithms.career_discovery import (
    RIASEC,
    SUBJECT_RIASEC,
    CareerDiscovery,
    InterestParams,
    _interaction_weight,
    demo,
)
from academicos.algorithms.learner_model import Interaction, LearnerModel


def _watch(concept: str, n: int, duration: float | None = None) -> list[Interaction]:
    now = datetime.now(timezone.utc)
    return [Interaction(concept_id=concept, kind="watch", duration_sec=duration,
                        ts=(now - timedelta(days=i)).isoformat()) for i in range(n)]


def _subject_of(mapping: dict[str, str]):
    def resolve(concept_id: str) -> str | None:
        return mapping.get(concept_id)
    return resolve


def _pruned() -> dict[str, dict[str, float]]:
    """Subject table with 'math' removed (→ anything math resolves uniform)."""
    return {k: dict(v) for k, v in SUBJECT_RIASEC.items() if k != "math"}


def test_empty_list_no_profile():
    r = CareerDiscovery().estimate([])
    assert r.confidence == 0.0
    assert r.holland_code == "---"
    assert r.top3 == []
    assert all(v == 0.0 for v in r.riasec_scores.values())


def test_empty_learner_model_no_profile():
    model = LearnerModel("empty")
    r = CareerDiscovery().estimate(model)
    assert r.confidence == 0.0
    assert "insufficient-data" in r.flags


def test_cs_heavy_top_investigative():
    ev = _watch("circuits", 6)
    r = CareerDiscovery().estimate(ev, _subject_of({"circuits": "cs"}))
    assert r.top3[0][0] == "Investigative"
    assert r.riasec_scores["Investigative"] == pytest.approx(0.6, abs=0.01)
    assert r.holland_code == "IRC"


def test_art_top_artistic():
    ev = _watch("painting", 4)
    r = CareerDiscovery().estimate(ev, _subject_of({"painting": "arts"}))
    assert r.top3[0][0] == "Artistic"
    assert r.holland_code.startswith("A")


def test_mixed_code_ordering():
    ev = _watch("algebra", 3) + _watch("painting", 3)
    r = CareerDiscovery().estimate(ev, _subject_of({"algebra": "math", "painting": "arts"}))
    # 3 math → I1.5 C0.9 R0.6; 3 arts → A2.1 S0.9 ⇒ top3 = Art., Inv., Conv. (tie w/ Social, alpha)
    assert r.holland_code == "AIC"
    assert r.top3[0][0] == "Artistic"
    assert r.top3[1][0] == "Investigative"


def test_low_evidence_low_confidence():
    ev = _watch("algebra", 2, duration=None)
    r = CareerDiscovery().estimate(ev, _subject_of({"algebra": "math"}))
    assert r.confidence == pytest.approx(0.5)
    assert "low-confidence" in r.flags


def test_min_evidence_override():
    ev = _watch("algebra", 6)
    p = InterestParams(min_evidence=10.0)
    r = CareerDiscovery(p).estimate(ev, _subject_of({"algebra": "math"}))
    assert r.confidence == pytest.approx(0.6)


def test_normalization_sums_to_one():
    ev = _watch("algebra", 5) + _watch("sketch", 4)
    r = CareerDiscovery().estimate(ev, _subject_of({"algebra": "math", "sketch": "arts"}))
    assert sum(r.riasec_scores.values()) == pytest.approx(1.0, abs=0.01)


def test_sum_to_override():
    ev = _watch("algebra", 5)
    p = InterestParams(sum_to=2.0)
    r = CareerDiscovery(p).estimate(ev, _subject_of({"algebra": "math"}))
    assert sum(r.riasec_scores.values()) == pytest.approx(2.0, abs=0.02)


def test_top3_length_and_order():
    ev = _watch("algebra", 5)
    r = CareerDiscovery().estimate(ev, _subject_of({"algebra": "math"}))
    assert len(r.top3) == 3
    vals = [s for _, s in r.top3]
    assert vals == sorted(vals, reverse=True)


def test_determinism():
    ev = _watch("algebra", 6) + _watch("essay", 3)
    subj = _subject_of({"algebra": "math", "essay": "language"})
    r1 = CareerDiscovery().estimate(ev, subj)
    r2 = CareerDiscovery().estimate(ev, subj)
    assert r1.riasec_scores == r2.riasec_scores
    assert r1.top3 == r2.top3
    assert r1.holland_code == r2.holland_code


def test_param_override_prune_subject_changes_profile():
    subj = _subject_of({"algebra": "math"})
    base = CareerDiscovery().estimate(_watch("algebra", 4), subj)
    pruned = CareerDiscovery(
        InterestParams(subject_weights=_pruned())).estimate(_watch("algebra", 4), subj)
    assert base.top3[0][0] == "Investigative"   # math row → I dominant
    assert pruned.top3[0][0] != "Investigative"  # math dropped → uniform


def test_missing_subject_neutral():
    ev = _watch("algebra", 5)
    r = CareerDiscovery().estimate(ev, lambda c: None)  # resolver present, subject unknown
    assert len(set(r.riasec_scores.values())) == 1       # uniform → all equal
    assert r.riasec_scores["Investigative"] == pytest.approx(1 / 6, abs=0.01)


def test_duration_counts_as_evidence():
    heavy = CareerDiscovery().estimate(
        _watch("algebra", 3, duration=180), _subject_of({"algebra": "math"}))
    light = CareerDiscovery().estimate(
        _watch("algebra", 3, duration=30), _subject_of({"algebra": "math"}))
    assert heavy.evidence_count == pytest.approx(9.0)  # 3 × (180/60)
    assert light.evidence_count == pytest.approx(3.0)  # sub-minute → 1 each
    assert heavy.confidence > light.confidence


def test_interaction_weight_duration():
    assert _interaction_weight(Interaction("c", "watch")) == 1.0
    assert _interaction_weight(Interaction("c", "watch", duration_sec=0)) == 1.0
    assert _interaction_weight(Interaction("c", "watch", duration_sec=120)) == 2.0


def test_params_roundtrip():
    p = InterestParams(min_evidence=7, sim_coef=0.3, sum_to=1.0)
    r = CareerDiscovery(p).estimate(_watch("algebra", 8), _subject_of({"algebra": "math"}))
    assert r.params["model"] == "riasec"
    assert r.params["min_evidence"] == 7
    assert r.params["sim_coef"] == 0.3
    assert r.params["sum_to"] == 1.0
    assert r.params["subject_weights"]["math"]["Investigative"] == 0.5


def test_subject_table_constant_shape():
    assert set(SUBJECT_RIASEC) >= {"math", "science", "cs", "language", "arts"}
    for subj, row in SUBJECT_RIASEC.items():
        assert all(d in RIASEC for d in row)
        assert sum(row.values()) == pytest.approx(1.0, abs=0.001)


def test_time_window_now_filter():
    ev = _watch("algebra", 4)
    cutoff = ev[2].ts  # keep only interactions not newer than this
    r = CareerDiscovery().estimate(ev, _subject_of({"algebra": "math"}), now=cutoff)
    assert r.evidence_count == 2.0  # the two most recent are excluded


def test_learner_model_input():
    subj = _subject_of({"friction": "science", "circuits": "cs",
                        "algebra": "math", "geometry": "math",
                        "essay-writing": "language"})
    r = CareerDiscovery().estimate(demo(), subj)
    assert r.learner_id == "demo-career"
    assert r.top3[0][0] == "Investigative"