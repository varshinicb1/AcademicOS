"""A11 — Reward engine: deterministic celebration policy (SDT + schedules)."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.algorithms.reward_engine import (
    ACTION_ACKNOWLEDGE,
    ACTION_CELEBRATE,
    ACTION_COOLDOWN,
    ACTION_ENCOURAGE,
    ACTION_NONE,
    RewardEngine,
    RewardParams,
    RewardSnapshot,
)

NOW = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc).isoformat()


def _engine(params=None) -> RewardEngine:
    return RewardEngine(params or RewardParams())


def _snap(**kw) -> RewardSnapshot:
    base = dict(learner_id="l", achievement=0.9, mastery=0.8, attempts=6,
                streak=4, relatedness=0.5)
    base.update(kw)
    return RewardSnapshot(**base)


def _iso(days_ago: float) -> str:
    return (datetime.fromisoformat(NOW) - timedelta(days=days_ago)).isoformat()


# --- 1. perfect achievement + high streak -> celebrate (competence) --------

def test_perfect_achievement_celebrates_competence():
    r = _engine().estimate(_snap(achievement=1.0, mastery=1.0, streak=10,
                                 attempts=12), now=NOW)
    act = r.actions[0]
    assert act.rm == ACTION_CELEBRATE
    assert act.intent == "competence"


# --- 2. celebration is throttled by cooldown on repeat ----------------------

def test_cooldown_respects_repeat_celebration():
    engine = _engine()
    snap = _snap(achievement=1.0, mastery=1.0, streak=10, attempts=12)
    first = engine.estimate(snap, now=NOW)
    assert first.actions[0].rm == ACTION_CELEBRATE and not first.actions[0].cooldown
    # same learner celebrated 3 hours ago -> cool down (they've been celebrated)
    repeat = engine.estimate(snap, last_reward_iso=_iso(0.125), now=NOW)
    act = repeat.actions[0]
    assert act.rm == ACTION_COOLDOWN and act.cooldown is True


# --- 3. cooldown window resets after the gap --------------------------------

def test_cooldown_resets_after_gap():
    snap = _snap(achievement=1.0, mastery=1.0, streak=10, attempts=12)
    # last celebration was 9 days ago (well past the 2-day cooldown)
    r = _engine().estimate(snap, last_reward_iso=_iso(9.0), now=NOW)
    assert r.actions[0].rm == ACTION_CELEBRATE and r.actions[0].cooldown is False


# --- 4. frustration / near-miss -> encourage, and it BYPASSES cooldown ------

def test_frustration_encourages_even_in_cooldown():
    snap = _snap(achievement=0.1, mastery=0.1, streak=1, attempts=12,
                 frustrated=True)
    # last celebration was minutes ago -> still reassure (no extrinsic gift)
    r = _engine().estimate(snap, last_reward_iso=_iso(0.01), now=NOW)
    assert r.actions[0].rm == ACTION_ENCOURAGE
    assert r.actions[0].intent == "effort"
    assert r.actions[0].cooldown is False


def test_near_miss_encourages_even_in_cooldown():
    snap = _snap(achievement=0.82, mastery=0.82, streak=3, attempts=9,
                near_miss=True)
    r = _engine().estimate(snap, last_reward_iso=_iso(0.01), now=NOW)
    act = r.actions[0]
    assert act.rm == ACTION_ENCOURAGE and act.message_key == "encourage_near_miss"


# --- 5. no observations -> no reward ---------------------------------------

def test_no_observations_returns_none():
    snap = RewardSnapshot(learner_id="l", mastery=1.0)  # attempts defaults to 0
    assert snap.attempts == 0
    r = _engine().estimate(snap, now=NOW)
    assert r.actions[0].rm == ACTION_NONE


# --- 6. threshold boundaries (0.85) ----------------------------------------

def test_mastery_boundary_crossing():
    ceiling = RewardParams().breakthrough_threshold  # 0.85
    above = _snap(achievement=0.5, mastery=ceiling + 0.001, streak=2, attempts=3)
    r_above = _engine().estimate(above, now=NOW)
    assert r_above.actions[0].rm == ACTION_CELEBRATE
    assert r_above.actions[0].intent == "competence"

    below = _snap(achievement=0.5, mastery=ceiling - 0.01, streak=1, attempts=3)
    r_below = _engine().estimate(below, now=NOW)
    assert r_below.actions[0].rm != ACTION_CELEBRATE  # not rounded up


# --- 7. attests-1 breakthrough fires celebrate (competence) ------------------

def test_breakthrough_on_first_attempt():
    snap = _snap(achievement=0.0, mastery=0.0, attempts=1, streak=0,
                breakthrough=True)
    r = _engine().estimate(snap, now=NOW)
    assert r.actions[0].rm == ACTION_CELEBRATE
    assert r.actions[0].message_key == "celebrate_mastery"


# --- 8. autonomy_flag self-selection -> autonomy celebration -------------------

def test_autonomy_self_selection_celebrates_autonomy():
    snap = _snap(achievement=1.0, mastery=0.9, attempts=12, streak=9,
                autonomy_flag=True)
    r = _engine().estimate(snap, now=NOW)
    assert r.actions[0].rm == ACTION_CELEBRATE
    assert r.actions[0].intent == "autonomy"


# --- 9. max rewards cap per call = 1 -----------------------------------------

def test_max_one_reward_per_call():
    # every rule could fire; still only ONE action (cap per call == 1).
    snap = _snap(achievement=1.0, mastery=1.0, attempts=100, streak=50,
                relatedness=0.95, autonomy_flag=True)
    r = _engine().estimate(snap, now=NOW)
    assert len(r.actions) == 1


# --- 10. as_dict exposes params + actions -------------------------------------

def test_as_dict_has_actions_and_params():
    snap = _snap(achievement=1.0, mastery=1.0, attempts=12, streak=9)
    r = _engine().estimate(snap, now=NOW)
    d = r.as_dict()
    assert d["learner_id"] == snap.learner_id
    assert d["actions"][0]["rm"] == ACTION_CELEBRATE
    assert d["params"]["model"] == "sdt-reward"
    assert d["params"]["breakthrough_threshold"] == 0.85


# --- 11. effort/relatedness acknowledgments bypass the cooldown ----------------

def test_effort_acknowledgment_bypasses_cooldown():
    # many attempts, moderate (not-celebrate-worthy) achievement — but in
    # cooldown: effort praise is process praise and must still be shown.
    # visible effort but a ceiling-composition below celebrate: process praise
    snap = _snap(achievement=0.4, mastery=0.4, attempts=4, streak=2)
    r = _engine().estimate(snap, last_reward_iso=_iso(0.1), now=NOW)
    assert r.actions[0].rm == ACTION_ACKNOWLEDGE
    assert r.actions[0].intent == "effort"
    assert r.actions[0].cooldown is False


def test_relatedness_celebration_not_gated_by_cooldown():
    # below celebrate-ceiling (score 0.68) so only relatedness can fire; still
    # in cooldown -> relational praise must come through unaffected.
    snap = _snap(achievement=0.5, mastery=0.4, attempts=4, streak=2,
                relatedness=0.9)
    r = _engine().estimate(snap, last_reward_iso=_iso(0.1), now=NOW)
    act = r.actions[0]
    assert act.rm == ACTION_CELEBRATE and act.intent == "relatedness"
    assert act.cooldown is False