"""A8 — Parent guidance: Dweck praise gates + scaffolding rules."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.algorithms.parent_guidance import (
    CATALOG,
    GuidanceParams,
    ParentGuidance,
    render_text,
    snapshot_from_learner,
)
from academicos.algorithms.learner_model import Interaction, LearnerModel


def keys(result):
    return [(m.template_key, m.target_concept) for m in result.messages]


def test_empty_snapshot_yields_no_guidance():
    r = ParentGuidance().guide({})
    assert r.messages == []
    assert r.scope == "parent:today"


def test_result_defaults_and_messages_alias():
    r = ParentGuidance().guide({"learner_id": "riya"})
    assert r.learner_id == "riya"
    assert r.params["model"] == "guidance"
    assert r.params["max_messages"] == 3
    assert r.messages is r.day_guidance


def test_praise_fires_on_effort_win():
    snap = {
        "accuracy_per_concept": {"fractions": 0.85},
        "attempts": {"fractions": 4},
        "recent_affect": {"fractions": ["frustrated", "engaged"]},
        "difficulty": {"fractions": 0.3},
        "trend": {"fractions": "rising"},
    }
    r = ParentGuidance().guide(snap)
    tags = [m.template_key for m in r.messages]
    assert "praise_effort" in tags
    msg = next(m for m in r.messages if m.template_key == "praise_effort")
    assert msg.component == "praise"
    assert msg.target_concept == "fractions"
    assert "fractions" in msg.text


def test_praise_on_high_difficulty_without_effort():
    snap = {
        "accuracy_per_concept": {"fractions": 0.85},
        "attempts": {"fractions": 4},
        "difficulty": {"fractions": 0.9},
        "recent_affect": {"fractions": []},
    }
    r = ParentGuidance().guide(snap)
    tags = [m.template_key for m in r.messages]
    assert "praise_difficulty" in tags


def test_no_praise_on_easy_win():
    snap = {
        "accuracy_per_concept": {"fractions": 0.85},
        "attempts": {"fractions": 4},
        "difficulty": {"fractions": 0.2},
        "recent_affect": {"fractions": []},
    }
    r = ParentGuidance().guide(snap)
    assert all(m.component != "praise" for m in r.messages)


def test_no_praise_on_low_accuracy():
    snap = {
        "accuracy_per_concept": {"fractions": 0.5},
        "attempts": {"fractions": 4},
        "recent_affect": {"fractions": ["frustrated", "frustrated"]},
        "difficulty": {"fractions": 0.9},
    }
    r = ParentGuidance().guide(snap)
    assert all(m.component != "praise" for m in r.messages)


def test_praise_requires_min_attempts():
    snap = {
        "accuracy_per_concept": {"fractions": 0.85},
        "attempts": {"fractions": 2},
        "difficulty": {"fractions": 0.9},
        "recent_affect": {"fractions": []},
    }
    r = ParentGuidance().guide(snap)
    assert [m.template_key for m in r.messages] == []


def test_encourage_fires_on_rise_after_frustration():
    snap = {
        "accuracy_per_concept": {"fractions": 0.5},
        "attempts": {"fractions": 3},
        "recent_affect": {"fractions": ["frustrated", "frustrated", "engaged"]},
        "trend": {"fractions": "rising"},
    }
    r = ParentGuidance().guide(snap)
    tags = [m.template_key for m in r.messages]
    assert "encourage_rising" in tags
    msg = next(m for m in r.messages if m.template_key == "encourage_rising")
    assert msg.component == "positive"


def test_reassure_fires_on_single_spike_not_burst():
    single = {
        "accuracy_per_concept": {"fractions": 0.6},
        "attempts": {"fractions": 2},
        "recent_affect": {"fractions": ["frustrated"]},
        "trend": {"fractions": "flat"},
    }
    r = ParentGuidance().guide(single)
    assert any(m.template_key == "reassure_single_spike" for m in r.messages)

    burst = {
        "accuracy_per_concept": {"fractions": 0.6},
        "attempts": {"fractions": 2},
        "recent_affect": {"fractions": ["frustrated"] * 4},
    }
    rb = ParentGuidance().guide(burst)
    tags = [m.template_key for m in rb.messages]
    assert "reassure_single_spike" not in tags
    assert "break_frustration" in tags


def test_break_on_fatigue():
    snap = {
        "attempts": {"fractions": 3},
        "accuracy_per_concept": {"fractions": 0.7},
        "recent_affect": {"fractions": ["tired", "tired"]},
    }
    r = ParentGuidance().guide(snap)
    assert any(m.template_key == "break_fatigue" for m in r.messages)


def test_scaffold_for_low_attempts_low_accuracy():
    snap = {
        "accuracy_per_concept": {"fractions": 0.3},
        "attempts": {"fractions": 2},
        "recent_affect": {"fractions": []},
    }
    r = ParentGuidance().guide(snap)
    tags = [m.template_key for m in r.messages]
    assert "scaffold_study_together" in tags
    msg = next(m for m in r.messages if m.template_key == "scaffold_study_together")
    assert msg.component == "scaffold"
    assert msg.hours == pytest.approx(0.5)


def test_scaffold_not_on_many_attempts():
    snap = {
        "accuracy_per_concept": {"fractions": 0.3},
        "attempts": {"fractions": 5},
        "recent_affect": {"fractions": []},
    }
    r = ParentGuidance().guide(snap)
    assert all(m.template_key != "scaffold_study_together" for m in r.messages)


def test_praise_threshold_boundary():
    base = {
        "accuracy_per_concept": {"fractions": 0.0},
        "attempts": {"fractions": 5},
        "difficulty": {"fractions": 0.9},
        "recent_affect": {"fractions": []},
    }
    at01 = dict(base)
    at01["accuracy_per_concept"] = {"fractions": 0.7}
    assert any(m.component == "praise" for m in ParentGuidance().guide(at01).messages)
    at02 = dict(base)
    at02["accuracy_per_concept"] = {"fractions": 0.69}
    assert all(m.component != "praise" for m in ParentGuidance().guide(at02).messages)


def test_focus_on_low_attention():
    snap = {
        "attempts": {"fractions": 1},
        "accuracy_per_concept": {"fractions": 0.6},
        "attention": {"fractions": 0.2},
        "recent_affect": {"fractions": []},
    }
    r = ParentGuidance().guide(snap)
    assert any(m.template_key == "focus_attention" for m in r.messages)


def test_bounded_and_order_safety_health_first():
    snap = {
        "accuracy_per_concept": {
            "algebra": 0.6, "fractions": 0.85, "geometry": 0.3, "binary": 0.8,
        },
        "attempts": {"algebra": 2, "fractions": 5, "geometry": 3, "binary": 5},
        "difficulty": {"fractions": 0.9, "binary": 0.2},
        "recent_affect": {"algebra": ["frustrated"] * 3, "fractions": [],
                          "geometry": ["frustrated"], "binary": []},
        "attention": {"binary": 0.2},
        "trend": {"validated": "flat", "fractions": "flat"},
    }
    r = ParentGuidance(GuidanceParams(max_messages=3)).guide(snap)
    assert len(r.messages) == 3
    assert r.messages[0].template_key == "break_frustration"


def test_deterministic_same_snapshot_same_order():
    snap = {
        "accuracy_per_concept": {"b": 0.85, "a": 0.3, "c": 0.6},
        "attempts": {"b": 5, "a": 1, "c": 2},
        "difficulty": {"b": 0.9},
        "recent_affect": {"c": ["frustrated"], "a": []},
        "trend": {"c": "flat"},
    }
    r1 = ParentGuidance().guide(snap)
    r2 = ParentGuidance().guide(snap)
    assert [(m.template_key, m.target_concept, m.text) for m in r1.messages] == \
           [(m.template_key, m.target_concept, m.text) for m in r2.messages]


def test_render_text_missing_placeholder_is_safe():
    assert render_text("Hello {concept} and {nonexistent}", concept="fractions") == \
        "Hello fractions and "


def test_catalog_keys_cover_components():
    components = {tpl.component for tpl in CATALOG.values()}
    assert components <= set(("positive", "praise", "scaffold", "comfort", "attention"))


def test_learner_model_snapshot_adapter():
    model = LearnerModel("riya")
    now = "2026-08-02T00:00:00+00:00"
    for outcome, affect in [(1.0, "frustrated"), (1.0, "frustrated"), (1.0, "engaged")]:
        model.observe(Interaction(concept_id="fractions", kind="answer",
                                  outcome=outcome, affect=affect, ts=now))
    snap = snapshot_from_learner(model)
    assert snap["attempts"]["fractions"] == 3
    r = ParentGuidance().guide(model)
    assert any(m.template_key == "praise_effort" for m in r.messages)