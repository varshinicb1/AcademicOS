"""Algorithm tests: forgetting prediction + revision scheduler (pure, no API calls)."""
from __future__ import annotations

import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.algorithms.forgetting import (
    ForgettingModel,
    ForgettingParams,
    PREDICTION_WINDOW_DAYS,
    RevisionScheduler,
)
from academicos.algorithms.learner_model import Interaction, LearnerModel

NOW = datetime.now(timezone.utc)

EXP = ForgettingParams(model="exponential")  # legacy v1 model (opt-in)


def _model(*events) -> LearnerModel:
    model = LearnerModel(learner_id="t")
    for cid, days_ago, outcome in events:
        model.observe(Interaction(
            concept_id=cid, kind="answer", outcome=outcome,
            ts=(NOW - timedelta(days=days_ago)).isoformat(),
        ))
    return model


def test_retention_decay_math():
    fm = ForgettingModel(EXP)
    model = _model(("c", 1, 1.0))
    assert fm.strength(model, "c") == pytest.approx(2.2, abs=1e-4)
    assert fm.retention_at(model, "c", NOW.isoformat()) == pytest.approx(
        math.exp(-1.0 / 2.2), abs=1e-4)


def test_strength_growth_on_correct_answers():
    fm = ForgettingModel(EXP)
    model = _model(("c", 1, 1.0), ("c", 2, 1.0), ("c", 3, 1.0))
    assert fm.strength(model, "c") == pytest.approx(2.2 ** 3, abs=1e-4)


def test_strength_decay_on_wrong_answers():
    fm = ForgettingModel(EXP)
    model = _model(("c", 1, 1.0), ("c", 2, 0.0))
    assert fm.strength(model, "c") == pytest.approx(2.2 * math.exp(-0.8), abs=1e-4)


def test_days_until_forgotten_math():
    fm = ForgettingModel(EXP)
    model = _model(("c", 0, 1.0))
    r = fm.predict_forgetting(model, "c", now=NOW.isoformat())
    assert r.retention_now == pytest.approx(1.0, abs=1e-4)
    assert r.days_until_forgotten == pytest.approx(-2.2 * math.log(0.6), abs=1e-3)


def test_days_until_forgotten_zero_when_already_forgotten():
    fm = ForgettingModel(EXP)
    model = _model(("c", 30, 1.0))
    r = fm.predict_forgetting(model, "c", now=NOW.isoformat())
    assert r.retention_now < 0.6
    assert r.days_until_forgotten == 0.0


def test_prediction_window_and_confident_flag():
    fm = ForgettingModel(EXP)
    model = _model(("c", 0, 1.0), ("c", 1, 1.0))
    r = fm.predict_forgetting(model, "c", now=NOW.isoformat())
    assert [d for d, _ in r.predicted_retention_at] == list(PREDICTION_WINDOW_DAYS)
    values = [v for _, v in r.predicted_retention_at]
    assert all(a >= b for a, b in zip(values, values[1:]))
    assert r.evidence_count == 2
    assert not r.confident


def test_no_evidence_graceful():
    fm = ForgettingModel()
    model = LearnerModel(learner_id="t")
    r = fm.predict_forgetting(model, "missing", now=NOW.isoformat())
    assert r.retention_now == pytest.approx(fm.p.noise_floor, abs=1e-4)
    assert r.days_until_forgotten == 0.0
    assert r.evidence_count == 0
    assert not r.confident
    assert all(v == fm.p.noise_floor for _, v in r.predicted_retention_at)


def test_scheduler_marks_due_concepts_below_threshold():
    sched = RevisionScheduler(ForgettingModel(EXP))
    model = _model(("old", 10, 1.0), ("fresh", 1, 1.0))
    plan = sched.plan(model, now=NOW.isoformat())
    due_ids = {c for c, _, _ in plan.due_today}
    assert "old" in due_ids
    assert "fresh" not in due_ids
    assert all(p > 0.0 for _, _, p in plan.due_today)
    assert plan.totals["due_today"] == 1
    assert plan.totals["next_reviews"] == 1
    assert plan.next_reviews[0][0] == "fresh"
    assert datetime.fromisoformat(plan.next_reviews[0][1]).date() > NOW.date()


def test_revision_session_fits_budget():
    sched = RevisionScheduler(ForgettingModel(EXP))
    model = _model(("a", 20, 1.0), ("b", 20, 1.0), ("c", 20, 1.0), ("d", 20, 1.0))
    items = sched.suggest_revision_session(model, minutes=10, now=NOW.isoformat())
    assert len(items) == 2
    assert all(i.minutes == 5 for i in items)
    for i in items:
        assert i.expected_gain == pytest.approx(1.0 - i.retention, abs=1e-4)


def test_revision_session_empty_when_nothing_due():
    sched = RevisionScheduler()
    model = _model(("fresh", 0, 1.0))
    assert sched.suggest_revision_session(model, minutes=20, now=NOW.isoformat()) == []


def test_demo_plan_runs():
    from academicos.algorithms.forgetting import demo

    sched = RevisionScheduler(ForgettingModel(EXP))
    plan = sched.plan(demo())
    assert plan.totals["concepts"] == 3
    due_ids = {c for c, _, _ in plan.due_today}
    assert "trigonometry" in due_ids
    assert "algebra" in due_ids
    assert "fractions" not in due_ids
    assert not plan.confident


def test_fsrs_default_engine_seeds_stability_from_weights():
    fm = ForgettingModel()
    assert fm.p.model == "fsrs"
    model = _model(("c", 1, 1.0))
    assert fm.strength(model, "c") == pytest.approx(2.3065, abs=1e-4)


def test_fsrs_retention_follows_curve():
    from academicos.algorithms.fsrs import forgetting_curve

    fm = ForgettingModel()
    model = _model(("c", 1, 1.0))
    r = fm.retention_at(model, "c", NOW.isoformat())
    assert r == pytest.approx(forgetting_curve(fm._fsrs.w, 1.0, 2.3065), abs=1e-4)


def test_fsrs_lapse_collapses_strength_and_raises_difficulty():
    fm = ForgettingModel()
    model = _model(("c", 1, 1.0))
    s_ok = fm.strength(model, "c")
    model.observe(Interaction(concept_id="c", kind="answer", outcome=0.0,
                              ts=(NOW - timedelta(days=0)).isoformat()))
    card = fm._card(model, "c")
    assert card.lapses == 1
    assert fm.strength(model, "c") < s_ok
    assert card.difficulty > 2.5  # failed recall makes the item harder (D' mean-reverts)


def test_fsrs_days_until_forgotten_roundtrip():
    fm = ForgettingModel()
    model = _model(("c", 0, 1.0))
    r = fm.predict_forgetting(model, "c", now=NOW.isoformat())
    assert r.retention_now > fm.p.threshold
    at = fm.retention_at(
        model, "c",
        (NOW + timedelta(days=r.days_until_forgotten)).isoformat())
    assert at == pytest.approx(fm.p.threshold, abs=1e-3)


def test_fsrs_review_history_ordering_independent():
    fm = ForgettingModel()
    m1 = _model(("c", 5, 1.0), ("c", 3, 1.0), ("c", 0, 0.0))
    m2 = _model(("c", 0, 0.0), ("c", 3, 1.0), ("c", 5, 1.0))
    assert fm.strength(m1, "c") == fm.strength(m2, "c")


# ------------------------------------ sleep consolidation (P2.5, Walker) ---

def _sleep(*days_ago, kind="answer") -> LearnerModel:
    model = LearnerModel(learner_id="s")
    for d in days_ago:
        model.observe(Interaction(
            concept_id="c", kind=kind, outcome=1.0,
            ts=(NOW - timedelta(days=d)).isoformat(),
        ))
    return model


def test_sleep_overnight_gaps_boost_stability():
    # Same history; enabling sleep_boost must strictly lift stability ---
    # isolates the consolidation effect from FSRS spacing dynamics.
    spaced = _sleep(5.5, 4.0, 2.5)   # gaps 1.5d, 1.75d -> 2 consolidation nights
    fm_off = ForgettingModel(ForgettingParams(sleep_boost=0.0))
    fm_on = ForgettingModel(ForgettingParams(sleep_boost=0.04))
    base = fm_off.strength(spaced, "c")
    boosted = fm_on.strength(spaced, "c")
    assert boosted > base
    assert boosted / base == pytest.approx((1.04 ** 2), rel=1e-3)


def test_sleep_gain_saturates_at_cap():
    fm = ForgettingModel()
    many = _sleep(10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0)
    gain = fm._sleep_gain(sorted(many.concepts["c"].history,
                                 key=lambda x: x.ts))
    assert gain <= 1.0 + fm.p.sleep_gain_cap


def test_sleep_gain_off_when_params_zeroed():
    fm = ForgettingModel(ForgettingParams(sleep_boost=0.0))
    model = _sleep(5.5, 4.0, 2.5)
    assert fm._sleep_gain(sorted(model.concepts["c"].history,
                                 key=lambda x: x.ts)) == pytest.approx(1.0)


def test_sleep_boost_respects_max_gap():
    fm = ForgettingModel()
    wide = _sleep(8.0, 4.0)     # gap 4d > sleep_gap_max_days(2) -> no boost
    assert fm._sleep_gain(sorted(wide.concepts["c"].history,
                                 key=lambda x: x.ts)) == pytest.approx(1.0)
    tight = _sleep(8.0, 6.5)    # gap 1.5d -> 1 night
    assert fm._sleep_gain(sorted(tight.concepts["c"].history,
                                 key=lambda x: x.ts)) == pytest.approx(1.04)


# -------------------------------------------------- retrieval practice.6 ---

def test_restudy_discounted_relative_to_retrieval():
    # K&R 2008: testing (answer) beats restudy (watch) for long-term.
    fm = ForgettingModel()
    retrieval = _sleep(2.0)  # answer event
    restudy = _sleep(2.0)    # same ts but kind=watch
    restudy.concepts["c"].history = [
        Interaction(concept_id="c", kind="watch", outcome=None,
                    ts=(NOW - timedelta(days=2.0)).isoformat()),
    ]
    assert fm.strength(retrieval, "c") > fm.strength(restudy, "c")


def test_restudy_gain_zeroed_matches_retrieval():
    fm = ForgettingModel(ForgettingParams(restudy_gain=1.0))
    m = _model(("c", 1, 1.0))
    # with gain 1.0 the single answer is unaffected; check params exposed
    assert fm.p.restudy_gain == 1.0
    assert fm.strength(m, "c") == pytest.approx(2.3065, abs=1e-4)


def test_session_items_default_to_retrieval_mode():
    sched = RevisionScheduler(ForgettingModel(EXP))
    model = _model(("a", 20, 1.0), ("b", 20, 1.0))
    items = sched.suggest_revision_session(model, minutes=10, now=NOW.isoformat())
    assert items
    assert all(i.mode == "retrieval" for i in items)
    restudy_items = sched.suggest_revision_session(
        model, minutes=10, now=NOW.isoformat(), mode="restudy")
    assert all(i.mode == "restudy" for i in restudy_items)


def test_components_explains_fsrs_stability():
    fm = ForgettingModel()
    model = _model(("c", 1, 1.0), ("c", 0, 1.0))
    comps = fm.components(model, "c")
    assert comps["model"] == "fsrs"
    assert comps["stability_days"] == fm.strength(model, "c")
    assert comps["reps"] == 2
    assert 0.0 < comps["retrievability_now"] <= 1.0
    assert 1.0 <= comps["sleep_gain"] <= 1.0 + fm.p.sleep_gain_cap
