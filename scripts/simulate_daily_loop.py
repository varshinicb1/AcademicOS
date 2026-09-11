"""P5.3 — offline evaluation: a 90-day simulation of the daily learning loop.

Five synthetic learner *policies* run the exact same 90-day window against the
same fixed mastery curve (probability of correct is a function of the
concept's recall probability). Memory is the repo's `ForgettingModel` (FSRS-6
default): a review is `answer` interaction replayed through the DSR engine,
so retention rises on recall and collapses on lapse exactly as the production
model would predict it.

Every learner starts empty and plays the same daily loop:

    pick the highest-retention **failing** concept (closest to the forgetting
    threshold first), else introduce a brand-new concept; review it; repeat
    until today's minute-budget runs out.

What differs is *attendance and preference*, nothing about the engine:

  * consistent    — studies every day, 20 min/day (the "keep the streak" floor)
  * erratic       — one spurt a month (day 0/30/60), 60 min when it shows up
  * fatigue-prone — studies daily but stops as soon as `AttentionModel`
                    reports "tired"; it can never exceed its daily budget
  * perfectionist — studies most days but *procrastinates hard new content*:
                    it refuses brand-new concepts rated difficult and skips
                    ~1 in 5 days entirely (never "sub-optimal" study)
  * new           — the "knows nothing new" control: every slot consumes a
                    fresh concept and Völkan repetition is refused, so it
                    piles up maximum exposure but never consolidates

Metrics per learner: days_studied, reviews_done, new_concepts_learned,
avg_retention_at_end, forgotten_events (times a concept was reviewed only
after it had already fallen below the forgetting threshold), total_minutes,
the projected retention-at-t1/t5/t14/t30 curve, and max_daily_minutes (the
capacity-cap check that must hold for every learner).

The headline claim the numbers have to support:

  * consistent retention > erratic retention at day 90 (regular practice wins)
  * consistent reviews >= erratic (she wrote more because she showed up more)
  * no policy ever exceeds its daily budget,
  * the "knows nothing new" aggregate — maximal exposure, minimal retention.

Deterministic: fixed timestamps (day 0 = 2026-01-01), one seeded PRNG
(`--seed 42`), pure-`python` standard library only. Exits 0 when run.

Usage:
    python scripts/simulate_daily_loop.py [--days 90] [--seed 42]
"""
from __future__ import annotations

import argparse
import random
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.algorithms.attention_model import AttentionModel, FatigueParams
from academicos.algorithms.forgetting import ForgettingModel
from academicos.algorithms.learner_model import Interaction, LearnerModel

DEFAULT_DAYS = 90
MINUTES_PER_ITEM = 5
CAPACITY_MINUTES = 20          # the 20-minute daily study budget
SPURT_MINUTES = 60             # erratic's once-a-month binge
FATIGUE_MAX_ATTENTION = 14.0   # fatigue-prone session budget (max_attention_minutes)

PREDICTION_WINDOW = (1, 5, 14, 30)

DEFAULT_POLICIES = ("consistent", "erratic", "fatigue-prone",
                    "perfectionist", "new")

# Deterministic per-concept curriculum difficulty (1..5, curriculum-style).
_DIFFICULTY_CYCLE = (1.0, 2.0, 3.0, 4.0, 5.0)
_DIFFICULTY_COUNT = len(_DIFFICULTY_CYCLE)
HARD_DIFFICULTY_FLOOR = 4.0    # a new concept at this difficulty is "hard"

DAY_START = datetime(2026, 1, 1, tzinfo=timezone.utc)
DAY = timedelta(days=1)


# --------------------------------------------------------------------------- #
# Pure helpers (kept deterministic and importable for tests)                   #
# --------------------------------------------------------------------------- #

def mastery_curve(recall_prob: float, floor: float = 0.05, ceiling: float = 0.95) -> float:
    """Probability of answering correctly, from the concept's recall estimate.

    The *same fixed curve* every synthetic learner draws from: an item you are
    most-likely-to-recall (R near 1) is answered correctly; an item you have
    largely forgotten (R near 0) is not. Floor/ceiling model irreducible noise
    at the extremes so nothing is ever a certainty.
    """
    return max(floor, min(ceiling, recall_prob))


class ConceptPool:
    """Deterministic, unbounded stream of brand-new concepts (id + difficulty)."""

    def __init__(self) -> None:
        self._counter = 0

    def next(self) -> tuple[str, float]:
        self._counter += 1
        cid = f"c{self._counter}"
        difficulty = _DIFFICULTY_CYCLE[(self._counter - 1) % _DIFFICULTY_COUNT]
        return cid, difficulty


def pick_next_concept(model: LearnerModel, fm: ForgettingModel, pool: ConceptPool,
                      t_iso: str, *, force_new: bool = False,
                      avoid_hard: bool = False) -> tuple[str, bool]:
    """Decision policy: ('review', preferred) or (new concept id, False).

    Among concepts that have fallen **below the forgetting threshold**, pick
    the one with the highest retention (failing to remember the least); if
    none is failing (or `force_new`), draw a brand-new concept. `avoid_hard`
    models the perfectionist: it declines brand-new material at or above the
    hard-difficulty floor, so it must consume the easier frontier first.
    """
    threshold = fm.p.threshold
    best: tuple[float, str] | None = None
    for cid, st in model.concepts.items():
        if st.attempts == 0:
            continue
        r = fm.retention_at(model, cid, t_iso)
        if r < threshold and (best is None or r > best[0]):
            best = (r, cid)
    if best is not None and not force_new:
        return best[1], True  # review the highest-retention-failing concept
    cid, difficulty = pool.next()
    while avoid_hard and difficulty >= HARD_DIFFICULTY_FLOOR:
        cid, difficulty = pool.next()
    return cid, False  # new exposure


def learner_review(model: LearnerModel, fm: ForgettingModel, concept_id: str,
                   t_iso: str, rng: random.Random) -> bool:
    """One review: draw the real outcome from the mastery curve and log it.

    A brand-new concept is learned on first contact (outcome 1.0); every
    later review is a *retrieval attempt* whose success probability comes from
    `mastery_curve` applied to the concept's FSRS-estimated recall probability.
    Returns the observed success.
    """
    st = model.concepts.get(concept_id)
    if st is None or st.attempts == 0:
        outcome = 1.0
    else:
        r = fm.retention_at(model, concept_id, t_iso)
        outcome = 1.0 if rng.random() < mastery_curve(r) else 0.0
    model.observe(Interaction(concept_id=concept_id, kind="answer",
                              outcome=outcome, ts=t_iso))
    return outcome >= 0.5


def minutes_allocated(policy: str, day: int, rng: random.Random) -> int:
    """Attendance policy: how many minutes this learner shows up with on `day`."""
    if policy == "erratic":
        return SPURT_MINUTES if day % 30 == 0 else 0
    if policy == "perfectionist":
        return CAPACITY_MINUTES if rng.random() >= 0.2 else 0  # procrastination
    if policy in ("consistent", "fatigue-prone", "new"):
        return CAPACITY_MINUTES
    raise ValueError(f"unknown policy: {policy}")


# ------------------------------------------------------------------------- #
# Result + the per-learner loop                                              #
# ------------------------------------------------------------------------- #

@dataclass
class SimResult:
    """Offline metrics for one (policy, seed) run of the 90-day loop."""
    policy: str
    days_studied: int = 0
    reviews_done: int = 0
    new_concepts_learned: int = 0
    avg_retention_at_end: float = 0.0
    forgotten_events: int = 0      # reviews on already-below-threshold items
    total_minutes: int = 0
    max_daily_minutes: int = 0
    retention_curve: dict = field(default_factory=dict)   # day → mean retention


def simulate_policy(policy: str, days: int = DEFAULT_DAYS, seed: int = 42,
                    fm: ForgettingModel | None = None,
                    pool: ConceptPool | None = None) -> SimResult:
    """Run the full 90-day loop for one learner policy, seeded & deterministic."""
    rng = random.Random(seed)
    fm = fm or ForgettingModel()
    pool = pool if pool is not None else ConceptPool()
    model = LearnerModel(learner_id=f"learner-{policy}")
    res = SimResult(policy=policy)

    attention = None
    if policy == "fatigue-prone":
        attention = AttentionModel(FatigueParams(max_attention_minutes=FATIGUE_MAX_ATTENTION))

    end_iso = (DAY_START + timedelta(days=days)).isoformat()
    for day in range(days):
        t = DAY_START + timedelta(days=day)
        t_iso = t.isoformat()
        alloc = minutes_allocated(policy, day, rng)
        if alloc <= 0:
            continue

        session_minutes = 0
        day_answers: list[Interaction] = []
        while session_minutes < alloc:
            planned = session_minutes + MINUTES_PER_ITEM
            if planned > alloc:
                break
            if attention is not None:                     # stop when "tired"
                now = (t + timedelta(minutes=planned)).isoformat()
                att = attention.estimate(session_start=t_iso,
                                         interactions=day_answers, now=now)
                if att.fatigue_state == "fatigued":
                    break

            cid, is_review = pick_next_concept(
                model, fm, pool, t_iso,
                force_new=(policy == "new"),
                avoid_hard=(policy == "perfectionist"),
            )
            if is_review:
                res.forgotten_events += 1

            review_ts = (t + timedelta(minutes=session_minutes)).isoformat()
            learner_review(model, fm, cid, review_ts, rng)
            day_answers.append(model.concepts[cid].history[-1])
            res.reviews_done += 1
            session_minutes += MINUTES_PER_ITEM

        if day_answers:
            res.days_studied += 1
            res.max_daily_minutes = max(res.max_daily_minutes, session_minutes)

    res.total_minutes = res.reviews_done * MINUTES_PER_ITEM
    seen = [cid for cid, st in model.concepts.items() if st.attempts > 0]
    res.new_concepts_learned = len(seen)
    if seen:
        res.avg_retention_at_end = (
            sum(fm.retention_at(model, cid, end_iso) for cid in seen) / len(seen))
        for d in PREDICTION_WINDOW:
            t_off = (DAY_START + timedelta(days=days + d)).isoformat()
            res.retention_curve[d] = (
                sum(fm.retention_at(model, cid, t_off) for cid in seen) / len(seen))
    return res


def simulate_each(policies: tuple[str, ...] = DEFAULT_POLICIES, days: int = DEFAULT_DAYS,
                  seed: int = 42) -> dict[str, SimResult]:
    """Run every policy against its own learner and fresh concept pool."""
    fm = ForgettingModel()
    out = {}
    for policy in policies:
        out[policy] = simulate_policy(policy, days=days, seed=seed, fm=fm)
    return out


# ------------------------------------------------------------------------- #
# Print + exit                                                               #
# ------------------------------------------------------------------------- #

def _fmt(x: float) -> str:
    return f"{x:.3f}".rstrip("0").rstrip(".")


def _fmt_w(x: float, width: int) -> str:
    return f"{_fmt(x):>{width}}"


def run_and_print(days: int = DEFAULT_DAYS, seed: int = 42) -> dict[str, SimResult]:
    results = simulate_each(days=days, seed=seed)
    print(f"P5.3 — {days}-day simulation of the daily loop (seed={seed})\n")
    hdr = (f"{'policy':<13}{'days':>5}{'reviews':>9}{'new':>7}{'forgot':>8}"
           f"{'min':>6}{'R@end':>8}" + "".join(f"R+{d:<4}" for d in PREDICTION_WINDOW))
    print(hdr)
    for res in results.values():
        curve = "".join(_fmt_w(res.retention_curve[d], 7) for d in PREDICTION_WINDOW)
        print(f"{res.policy:<13}{res.days_studied:>5}{res.reviews_done:>9}"
              f"{res.new_concepts_learned:>7}{res.forgotten_events:>8}"
              f"{res.total_minutes:>6}{_fmt(res.avg_retention_at_end):>8}{curve}")

    print("\n-- compare --")
    c, e, f, p, n = (results[name] for name in DEFAULT_POLICIES)
    delta_ret = c.avg_retention_at_end - e.avg_retention_at_end
    print(f"consistent vs erratic: retention {delta_ret:+.3f} at day 90, "
          f"reviews {c.reviews_done} vs {e.reviews_done} "
          f"({c.reviews_done - e.reviews_done:+d}).")
    if f.max_daily_minutes > CAPACITY_MINUTES:
        print(f"!! fatigue learner exceeded budget: {f.max_daily_minutes} "
              f"min > {CAPACITY_MINUTES}")
    else:
        print(f"fatigue learner never exceeded its {CAPACITY_MINUTES} min/day "
              f"budget (max session {f.max_daily_minutes} min).")
    print(f"'new' control (knows-nothing-new): {n.new_concepts_learned} concepts, "
          f"{n.reviews_done} reviews, avg retention {_fmt(n.avg_retention_at_end)} "
          f"vs consistent {_fmt(c.avg_retention_at_end)}.")
    return results


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=DEFAULT_DAYS)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    run_and_print(args.days, args.seed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())