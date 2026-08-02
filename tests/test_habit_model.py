"""A5 — Habit formation model: streaks, consistency, phases, relapse risk."""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.algorithms.habit_model import HabitModel, HabitParams
from academicos.algorithms.learner_model import Interaction

NOW = "2026-03-10T12:00:00+00:00"


def _inter(day: str) -> Interaction:
    return Interaction(concept_id="x", kind="answer", outcome=1.0,
                       ts=f"{day}T10:00:00+00:00")


def _run(start: str, end: str):
    """Consecutive study days [start, end] (inclusive ISO dates)."""
    d0, dN = date.fromisoformat(start), date.fromisoformat(end)
    out, d = [], d0
    while d <= dN:
        out.append(_inter(d.isoformat()))
        d += timedelta(days=1)
    return out


def _hm(pairs, params=None, now=NOW):
    return HabitModel(params).estimate(pairs, now)


def test_empty_history():
    r = _hm([])
    assert r.current_streak == 0
    assert r.longest_streak == 0
    assert r.study_days == []
    assert r.last_day is None
    assert r.phase == "forming"


def test_three_consecutive_days():
    r = _hm([_inter(d) for d in ("2026-03-08", "2026-03-09", "2026-03-10")])
    assert r.current_streak == 3
    assert r.longest_streak == 3


def test_gap_breaks_streak():
    r = _hm([_inter("2026-03-08"), _inter("2026-03-10")])
    assert r.current_streak == 1
    assert r.longest_streak == 1


def test_consistency_7():
    # 4 of the last 7 calendar days: 03-04, 03-06, 03-08, 03-10
    r = _hm([_inter(d) for d in ("2026-03-04", "2026-03-06",
                                 "2026-03-08", "2026-03-10")])
    assert r.consistency_7 == 0.5714  # round(4/7, 4)


def test_beyond_66_becomes_automated():
    r = _hm(_run("2026-01-03", "2026-03-10"))  # 67 study days, gap-free
    assert len(r.study_days) == 67
    assert r.current_streak == 67
    assert r.phase == "automated"


def test_resume_recomputes_streak():
    # 7-day run, then 2 idle days, then a single resumed day
    r = _hm(_run("2026-02-25", "2026-03-03") + [_inter("2026-03-06")],
            now="2026-03-06T12:00:00+00:00")
    assert r.longest_streak == 7
    assert r.current_streak == 1
    assert r.last_day == "2026-03-06"


def test_relapse_when_consistency_7_low():
    # 31 daily days, then one flag in the week, then queried after a gap
    r = _hm(_run("2026-02-01", "2026-03-03") + [_inter("2026-03-04")], now=NOW)
    assert r.consistency_7 == 0.1429  # round(1/7, 4)
    assert r.phase == "relapse"
    assert r.current_streak == 0
    assert r.risk == 1.0  # 6 idle days >= breakday_limit (3)


def test_consistency_30():
    days = ("2026-02-09", "2026-02-15", "2026-02-20", "2026-02-25",
            "2026-03-01", "2026-03-05", "2026-03-07", "2026-03-10")
    r = _hm([_inter(d) for d in days])
    assert r.consistency_30 == 0.2667  # round(8/30, 4)


def test_duplicates_same_day_not_double_counted():
    inter = [_inter("2026-03-09"), _inter("2026-03-09"), _inter("2026-03-09"),
             _inter("2026-03-10"), _inter("2026-03-10")]
    r = _hm(inter)
    assert r.study_days == ["2026-03-09", "2026-03-10"]
    assert r.current_streak == 2
    assert r.longest_streak == 2


def test_params_roundtrip():
    hm = HabitModel(HabitParams(formation_days=100, breakday_limit=5))
    r = hm.estimate([_inter("2026-03-09"), _inter("2026-03-10")], NOW)
    assert r.params == hm._params()
    assert r.params["formation_days"] == 100
    assert r.params["breakday_limit"] == 5
    assert r.params["streak_grace_days"] == 1
    assert HabitModel.version == "1.0"