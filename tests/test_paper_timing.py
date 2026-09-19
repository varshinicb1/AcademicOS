"""Time saved per paper — the renewal criterion, and what the number means.

Decision 11: *"Renewal is measured as time saved per paper."* The tests that
matter most here are not the arithmetic ones; they are the ones asserting that a
DECLARED baseline is never presented as a measured result. This figure will be
quoted at a principal deciding whether to renew, and the failure mode is a
number that reads as evidence when it is an assumption.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from academicos.assessment import paper_timing as pt  # noqa: E402


@pytest.fixture()
def data_root(tmp_path):
    return tmp_path / "data"


# --- the baseline is declared, and says so --------------------------------

def test_the_default_baseline_is_declared_not_measured(monkeypatch):
    monkeypatch.delenv(pt._ENV_KEY, raising=False)
    value, provenance = pt.baseline_minutes()
    assert value == pt._DEFAULT_BASELINE_MINUTES
    assert "declared" in provenance.lower()
    assert "not measured" in provenance.lower(), (
        "the provenance must say the baseline is not measured, or the saving "
        "reads as evidence"
    )


def test_a_school_can_supply_its_own_baseline(monkeypatch):
    """A school's own figure is worth more in a renewal conversation."""
    monkeypatch.setenv(pt._ENV_KEY, "25")
    value, provenance = pt.baseline_minutes()
    assert value == 25.0
    assert pt._ENV_KEY in provenance


@pytest.mark.parametrize("bad", ["not-a-number", "", "0", "-10"])
def test_an_unusable_baseline_falls_back_and_says_why(monkeypatch, bad):
    """Never silently substitute a number without recording the substitution."""
    monkeypatch.setenv(pt._ENV_KEY, bad)
    value, provenance = pt.baseline_minutes()
    assert value == pt._DEFAULT_BASELINE_MINUTES
    if bad != "":
        assert "fell back" in provenance or "not positive" in provenance or \
               "not a number" in provenance


# --- recording ------------------------------------------------------------

def test_a_negative_duration_is_refused(data_root):
    """A duration cannot be negative; this is a caller bug, not a slow paper."""
    with pytest.raises(ValueError, match="negative"):
        pt.record_generation(data_root=data_root, school_id="s1", user_id="u1",
                             paper_id="p1", elapsed_seconds=-1.0)


def test_recording_then_reporting_round_trips(data_root):
    pt.record_generation(data_root=data_root, school_id="s1", user_id="u1",
                         paper_id="p1", elapsed_seconds=8.0, question_count=20)
    pt.record_generation(data_root=data_root, school_id="s1", user_id="u1",
                         paper_id="p2", elapsed_seconds=12.0, question_count=22)
    rep = pt.report(data_root, school_id="s1")
    assert rep.papers == 2
    assert rep.median_generation_seconds == 10.0
    assert rep.total_generation_seconds == 20.0


def test_the_report_is_scoped_to_one_school(data_root):
    """Cross-school leakage in a management figure is a tenancy bug."""
    pt.record_generation(data_root=data_root, school_id="s1", user_id="u1",
                         paper_id="p1", elapsed_seconds=8.0)
    pt.record_generation(data_root=data_root, school_id="s2", user_id="u2",
                         paper_id="p2", elapsed_seconds=8.0)
    assert pt.report(data_root, school_id="s1").papers == 1
    assert pt.report(data_root, school_id="s2").papers == 1
    assert pt.report(data_root).papers == 2          # unscoped is explicit


def test_an_empty_report_is_zero_rather_than_an_error(data_root):
    rep = pt.report(data_root, school_id="s1")
    assert rep.papers == 0
    assert rep.estimated_minutes_saved_total == 0.0
    assert rep.baseline_minutes_per_paper > 0        # the baseline is still told


def test_the_saving_is_clamped_at_zero(monkeypatch, data_root):
    """A machine slower than a teacher by hand is not a saving.

    Reporting a negative one invites the reader to distrust the figure that IS
    real, so it is clamped -- and the clamp is asserted rather than assumed.
    """
    monkeypatch.setenv(pt._ENV_KEY, "1")             # 1 minute baseline
    pt.record_generation(data_root=data_root, school_id="s1", user_id="u1",
                         paper_id="p1", elapsed_seconds=600.0)   # 10 minutes
    rep = pt.report(data_root, school_id="s1")
    assert rep.estimated_minutes_saved_per_paper == 0.0
    assert rep.estimated_minutes_saved_total == 0.0
    # But the MEASURED number is still reported honestly, unclamped.
    assert rep.median_generation_seconds == 600.0


# --- the payload separates measured from declared -------------------------

def test_the_payload_names_which_fields_are_measured(monkeypatch, data_root):
    """The word "estimated" has to travel with the number.

    This is the whole design: a saving built on a declared baseline is a
    perfectly good management figure and an unacceptable engineering claim, and
    the difference is only visible if it is written down next to the value.
    """
    pt.record_generation(data_root=data_root, school_id="s1", user_id="u1",
                         paper_id="p1", elapsed_seconds=5.0)
    payload = pt.report(data_root, school_id="s1").as_dict()

    assert payload["measured"] == ["generationSeconds"]
    assert payload["declared"] == ["baselineMinutesPerPaper"]
    assert "DECLARED, not measured" in payload["caveat"]
    assert "baselineProvenance" in payload
    assert payload["baselineProvenance"]


def test_the_timer_measures_something_real():
    """A monotonic clock, so an adjustment mid-generation cannot alter it."""
    import time as _time

    with pt.generation_timer() as timer:
        _time.sleep(0.02)
    assert timer.elapsed_seconds >= 0.02
    assert timer.elapsed_seconds < 5.0        # sanity: not minutes


def test_the_action_constant_matches_what_the_route_writes():
    """The writer and the reader must not drift apart.

    `routes.py` appends this action with `generationSeconds` in the details; if
    either changes alone, the report silently reports zero papers.
    """
    source = (REPO / "src" / "academicos" / "assessment"
              / "routes.py").read_text(encoding="utf-8")
    assert '"quick_paper_generated"' in source
    assert pt.ACTION == "quick_paper_generated"
    assert "generationSeconds" in source
