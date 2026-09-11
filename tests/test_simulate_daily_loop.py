"""P5.3 — offline eval: `scripts/simulate_daily_loop.py`.

This script had never actually run: `DEFAULT_DAYS` was referenced but never
defined (NameError at import time, before `main()` could even start),
`_DIFFIFFY_COUNT` / `FATIGUE_AXS_MINUTES` were typos for real constants, a
local `attention` variable was referenced as `fatigue` inside the loop, and
the retention-curve formatter called an undefined `fri()`. Fixed all five;
these tests lock in that it actually runs and that the four headline claims
in its own docstring are real, not aspirational.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import simulate_daily_loop as sim

CAPACITY_MINUTES = sim.CAPACITY_MINUTES
SPURT_MINUTES = sim.SPURT_MINUTES


def _policy_daily_cap(policy: str) -> int:
    """Each policy's own ceiling for a single day's session, matching
    `minutes_allocated`: erratic's spurt days get SPURT_MINUTES, everyone
    else including erratic's non-spurt days is capped at CAPACITY_MINUTES."""
    return SPURT_MINUTES if policy == "erratic" else CAPACITY_MINUTES


def test_all_policies_run_without_error():
    results = sim.simulate_each(days=90, seed=42)
    assert set(results) == set(sim.DEFAULT_POLICIES)
    for res in results.values():
        assert res.reviews_done >= 0
        assert res.days_studied >= 0


def test_same_seed_is_deterministic():
    a = sim.simulate_each(days=90, seed=42)
    b = sim.simulate_each(days=90, seed=42)
    for policy in sim.DEFAULT_POLICIES:
        assert a[policy].reviews_done == b[policy].reviews_done
        assert a[policy].avg_retention_at_end == b[policy].avg_retention_at_end
        assert a[policy].retention_curve == b[policy].retention_curve


def test_no_policy_exceeds_its_own_daily_budget():
    results = sim.simulate_each(days=90, seed=42)
    for policy, res in results.items():
        cap = _policy_daily_cap(policy)
        assert res.max_daily_minutes <= cap, (
            f"{policy} exceeded its {cap}-minute daily budget: {res.max_daily_minutes}")


def test_consistent_beats_erratic_on_retention_and_reviews():
    """Headline claim 1+2 from the module docstring."""
    results = sim.simulate_each(days=90, seed=42)
    c, e = results["consistent"], results["erratic"]
    assert c.avg_retention_at_end > e.avg_retention_at_end
    assert c.reviews_done >= e.reviews_done


def test_fatigue_prone_never_exceeds_capacity():
    """Headline claim 3: the fatigue-aware policy is the interesting budget
    check -- it can stop *early* (attention model says "tired") but must
    never run past the 20-minute cap."""
    results = sim.simulate_each(days=90, seed=42)
    f = results["fatigue-prone"]
    assert f.max_daily_minutes <= CAPACITY_MINUTES


def test_new_control_has_max_exposure_and_lower_retention_than_consistent():
    """Headline claim 4: 'new' (knows-nothing-new) piles up maximum
    exposure but never consolidates, so its retention should trail
    consistent's despite equal or greater review volume."""
    results = sim.simulate_each(days=90, seed=42)
    n, c = results["new"], results["consistent"]
    assert n.new_concepts_learned >= c.new_concepts_learned
    assert n.avg_retention_at_end < c.avg_retention_at_end


def test_run_and_print_returns_same_shape_and_does_not_crash(capsys):
    results = sim.run_and_print(days=30, seed=7)
    out = capsys.readouterr().out
    assert "P5.3" in out
    assert set(results) == set(sim.DEFAULT_POLICIES)
