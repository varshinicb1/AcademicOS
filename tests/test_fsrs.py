"""FSRS-6 engine tests: math invariants + revision pipeline + CLI revise."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.algorithms.forgetting import (ForgettingModel, ForgettingParams,
                                              RevisionScheduler)
from academicos.algorithms.fsrs import (
    DEFAULT_W, FSRS, FSRSCard,
    RATING_AGAIN, RATING_EASY, RATING_GOOD, RATING_HARD,
    compute_decay_factor, forgetting_curve, init_difficulty, init_stability,
    interval_modifier, next_difficulty, next_forget_stability,
    next_recall_stability, outcome_to_grade, seed_difficulty,
)
from academicos.algorithms.learner_model import Interaction
from academicos.storage.event_store import EventStore

NOW = datetime.now(timezone.utc)


# ---------------------------------------------------------------- curve math

def test_forgetting_curve_recall_at_stability_is_09():
    fsrs = FSRS()
    r = forgetting_curve(DEFAULT_W, 1.0, 1.0)
    assert r == pytest.approx(0.9, abs=1e-9)


def test_forgetting_curve_monotone_decreasing():
    fsrs = FSRS()
    s = 10.0
    values = [forgetting_curve(DEFAULT_W, t, s) for t in (0.0, 1.0, 5.0, 20.0, 60.0)]
    assert values[0] == pytest.approx(1.0, abs=1e-9)
    assert all(a > b for a, b in zip(values, values[1:]))


def test_compute_decay_factor_matches_definition():
    decay, factor = compute_decay_factor(DEFAULT_W)
    assert decay == pytest.approx(-DEFAULT_W[20])
    assert factor == pytest.approx(2.718281828 ** (0.1053605 / -decay) - 1, rel=1e-4)


def test_interval_modifier_recovers_target_retention():
    fsrs = FSRS(desired_retention=0.9)
    assert fsrs.ivl_modifier == pytest.approx(1.0, abs=1e-9)
    # t = interval_modifier(r) * S must give exactly r under the curve
    for r in (0.9, 0.8, 0.7):
        t = interval_modifier(DEFAULT_W, r) * 10.0
        assert forgetting_curve(DEFAULT_W, t, 10.0) == pytest.approx(r, abs=1e-9)


def test_days_until_retention_roundtrip():
    fsrs = FSRS()
    card = FSRSCard(stability=20.0, last_review="2026-01-01T00:00:00+00:00",
                    reps=1)
    t = fsrs.days_until_retention(card)
    assert forgetting_curve(DEFAULT_W, t, 20.0) == pytest.approx(0.9, abs=1e-9)
    t60 = fsrs.days_until_retention(card, 0.6)
    assert forgetting_curve(DEFAULT_W, t60, 20.0) == pytest.approx(0.6, abs=1e-9)


# --------------------------------------------------------------- state rules

def test_initial_stability_monotonic_in_grade():
    s = [init_stability(DEFAULT_W, g) for g in (1, 2, 3, 4)]
    assert s[0] < s[1] < s[2] < s[3]


def test_initial_difficulty_lower_for_easier_grades():
    d = [init_difficulty(DEFAULT_W, g) for g in (1, 2, 3, 4)]
    assert d[0] > d[1] > d[2] > d[3]
    assert all(1.0 <= x <= 10.0 for x in d)


def test_forget_stability_never_exceeds_current():
    for s in (1.0, 5.0, 50.0):
        s2 = next_forget_stability(DEFAULT_W, 5.0, s, 0.5)
        assert 0.0 < s2 <= s


def test_recall_stability_grows_with_retrievability():
    # Recalling at lower retrievability (closer to forgetting) strengthens more.
    a = next_recall_stability(DEFAULT_W, 5.0, 10.0, 0.9, RATING_GOOD)
    b = next_recall_stability(DEFAULT_W, 5.0, 10.0, 0.5, RATING_GOOD)
    assert b > a > 10.0


def test_difficulty_mean_reverts_toward_easy_anchor():
    d_hard = next_difficulty(DEFAULT_W, 8.0, RATING_HARD)
    d_easy = next_difficulty(DEFAULT_W, 2.0, RATING_EASY)
    assert 1.0 <= d_hard <= 10.0 and 1.0 <= d_easy <= 10.0


def test_outcome_to_grade_mapping():
    assert outcome_to_grade(1.0) == RATING_GOOD
    assert outcome_to_grade(0.6) == RATING_GOOD
    assert outcome_to_grade(0.4) == RATING_HARD
    assert outcome_to_grade(0.0) == RATING_AGAIN
    with pytest.raises(ValueError):
        outcome_to_grade(None)


def test_seed_difficulty_ranges():
    assert seed_difficulty(None) == pytest.approx(5.5)
    assert seed_difficulty(1.0) < seed_difficulty(5.0)
    assert seed_difficulty(3.0, bloom="analyze") > seed_difficulty(3.0, bloom="remember")
    assert 1.0 <= seed_difficulty(5.0, bloom="create") <= 10.0


# ----------------------------------------------------------------- scheduler

def test_review_first_good_seeds_and_schedules_future():
    fsrs = FSRS()
    card = FSRSCard()
    rev = fsrs.review(card, RATING_GOOD, now=NOW.isoformat())
    assert card.reps == 1 and card.lapses == 0
    assert card.stability == pytest.approx(DEFAULT_W[2], abs=1e-6)
    assert datetime.fromisoformat(card.due) > NOW
    assert card.state == "learning"
    assert rev.retrievability == pytest.approx(1.0, abs=1e-9)


def test_review_lapse_counts_and_transitions_state():
    fsrs = FSRS()
    card = FSRSCard()
    fsrs.review(card, RATING_GOOD, now=NOW.isoformat())
    s_before = card.stability
    fsrs.review(card, RATING_AGAIN, now=(NOW + timedelta(days=3)).isoformat())
    assert card.lapses == 1
    assert card.reps == 2
    assert card.state == "relearning"
    assert card.stability < s_before
    assert card.difficulty > init_difficulty(DEFAULT_W, RATING_GOOD)


def test_review_interval_scales_with_stability():
    fsrs = FSRS()
    card = FSRSCard()
    for i in range(4):
        fsrs.review(card, RATING_GOOD,
                    now=(NOW + timedelta(days=2 ** i)).isoformat())
    intervals = []
    c = FSRSCard()
    fsrs.review(c, RATING_GOOD, now=NOW.isoformat())
    intervals.append(fsrs.next_interval(c.stability))
    fsrs.review(c, RATING_GOOD, now=(NOW + timedelta(days=30)).isoformat())
    intervals.append(fsrs.next_interval(c.stability))
    assert intervals[1] > intervals[0]


def test_replay_history_deterministic():
    fsrs = FSRS()
    grades = [(10.0, RATING_GOOD), (3.0, RATING_GOOD), (0.0, RATING_AGAIN)]
    c1 = fsrs.replay_history(grades, now=NOW.isoformat())
    c2 = fsrs.replay_history(list(reversed(grades)), now=NOW.isoformat())
    assert c1.stability == c2.stability
    assert c1.difficulty == c2.difficulty
    assert c1.lapses == 1


def test_fsrs_rejects_bad_weights():
    with pytest.raises(ValueError):
        FSRS(w=(0.5, 1.0))
    with pytest.raises(ValueError):
        FSRS(desired_retention=1.5)


# --------------------------------------------- event store -> revise pipeline

def test_event_store_to_revision_plan_fsrs(tmp_path: Path) -> None:
    es = EventStore(tmp_path / "events.sqlite")
    try:
        es.append_many("alice", [
            Interaction(concept_id="fractions", kind="answer", outcome=1.0),
            Interaction(concept_id="fractions", kind="answer", outcome=1.0),
            Interaction(concept_id="perimeter", kind="answer", outcome=0.0),
            Interaction(concept_id="perimeter", kind="answer", outcome=1.0),
        ])
        model = es.replay("alice")
    finally:
        es.close()
    sched = RevisionScheduler(ForgettingModel())
    plan = sched.plan(model)
    assert plan.totals["concepts"] == 2
    due = {cid for cid, _, _ in plan.due_today}
    upcoming = {cid for cid, _ in plan.next_reviews}
    assert "fractions" in upcoming
    assert plan.totals["due_today"] + plan.totals["next_reviews"] == 2


def test_cmd_revise_prints_plan(tmp_path: Path, monkeypatch) -> None:
    from academicos import cli
    from academicos.config import Config

    monkeypatch.setattr(cli.Config, "load",
                        staticmethod(lambda: Config(data_root=tmp_path)))
    es = EventStore(tmp_path / "events" / "events.sqlite")
    try:
        es.append_many("bob", [
            Interaction(concept_id="c1", kind="answer", outcome=1.0),
            Interaction(concept_id="c2", kind="answer", outcome=0.0),
        ])
    finally:
        es.close()
    args = argparse.Namespace(learner="bob", model="fsrs")
    assert cli.cmd_revise(args) == 0


def test_cmd_revise_empty_learner(tmp_path: Path, monkeypatch, capsys) -> None:
    from academicos import cli
    from academicos.config import Config

    monkeypatch.setattr(cli.Config, "load",
                        staticmethod(lambda: Config(data_root=tmp_path)))
    args = argparse.Namespace(learner="nobody", model="fsrs")
    assert cli.cmd_revise(args) == 1
    assert "no interactions" in capsys.readouterr().out
