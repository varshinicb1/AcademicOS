"""A9 — Teacher Assistance tests: class-level mastery aggregation."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.algorithms.learner_model import Interaction, LearnerModel
from academicos.algorithms.teacher_assistance import (
    ClassParams,
    ClassReport,
    ConceptSnapshot,
    LearnerSnapshot,
    TeacherAssistance,
)


def snap(learner_id: str, *concepts: tuple[str, float, int]) -> LearnerSnapshot:
    return LearnerSnapshot(learner_id, {cid: ConceptSnapshot(acc, att)
                                        for cid, acc, att in concepts})


def test_empty_class_focus_empty():
    report = TeacherAssistance().report([])
    assert report.suggested_focus == []
    assert report.concepts == []
    assert report.n_learners == 0
    assert report.n_rated == 0


def test_single_learner_single_concept_mastered():
    s = snap("l1", ("algebra", 1.0, 3))
    report = TeacherAssistance().report([s])
    assert report.n_learners == 1
    assert report.n_rated == 1
    assert len(report.concepts) == 1
    row = report.concepts[0]
    assert row.concept_id == "algebra"
    assert row.class_accuracy == 1.0
    assert row.n_students_rated == 1
    assert row.at_risk == []
    assert row.focus_priority == 0.0
    assert report.suggested_focus == []


def test_two_learners_averaging_same_concept():
    a = snap("a", (3, 1.0, 3))
    b = snap("b", (3, 0.5, 3))
    report = TeacherAssistance().report([a, b])
    row = report.concepts[0]
    assert row.class_accuracy == 0.75
    assert row.n_students_rated == 2
    assert row.at_risk == ["b"]
    assert row.focus_priority == pytest.approx(0.125, abs=1e-4)


def test_one_knows_two_not_is_high_priority():
    strong = snap("s", ("gap", 0.9, 5), ("ok", 1.0, 5))
    weak1 = snap("w1", ("gap", 0.4, 5), ("ok", 0.9, 5))
    weak2 = snap("w2", ("gap", 0.45, 5), ("ok", 0.8, 5))
    report = TeacherAssistance().report([strong, weak1, weak2])
    row = report.concepts[0]
    assert row.concept_id == "gap"
    gap = report.concepts[0].focus_priority
    assert not any(r.focus_priority > gap for r in report.concepts[1:])
    assert report.suggested_focus[0] == "gap"
    assert set(row.at_risk) == {"w1", "w2"}


def test_attempts_filter_excludes_thin_evidence():
    a = snap("a", ("thick", 0.2, 4), ("thin", 0.9, 1))
    b = snap("b", ("thick", 0.3, 4), ("thin", 0.8, 2))
    report = TeacherAssistance().report([a, b])
    cids = {r.concept_id for r in report.concepts}
    assert "thick" in cids
    assert "thin" not in cids


def test_weak_threshold_boundary_uses_strict_inequality():
    p = ClassParams(weak_threshold=0.5, min_attempts=3)
    a = snap("a", (3, 0.5, 3))
    b = snap("b", (3, 0.49, 3))
    row = TeacherAssistance(p).report([a, b]).concepts[0]
    assert "a" not in row.at_risk
    assert row.at_risk == ["b"]


def test_rank_order_multiple_concepts():
    a = snap("a", ("soft", 1.0, 3), ("mid", 0.7, 3), ("weak", 0.3, 3))
    b = snap("b", ("soft", 1.0, 3), ("mid", 0.6, 3), ("weak", 0.2, 3))
    report = TeacherAssistance().report([a, b])
    order = [r.concept_id for r in report.concepts]
    assert order == ["weak", "mid", "soft"]
    assert report.suggested_focus == ["weak"]


def test_at_risk_lists_only_strictly_below_threshold():
    a = snap("a", (3, 0.4, 4))
    b = snap("b", (3, 0.56, 4))
    c = snap("c", (3, 0.54, 4))
    report = TeacherAssistance().report([a, b, c])
    row = report.concepts[0]
    assert sorted(row.at_risk) == ["a", "c"]
    assert "b" not in row.at_risk


def test_focus_limited_to_max():
    learners = [
        snap(f"l{i}", *[(f"t{j}", 0.1, 3) for j in range(7)])
        for i in range(2)
    ]
    report = TeacherAssistance().report(learners)
    assert len(report.suggested_focus) == ClassParams().max_focus == 5
    assert all(r.focus_priority > 0 for r in report.concepts)
    assert report.suggested_focus == ["t0", "t1", "t2", "t3", "t4"]


def test_stable_tie_break_alphabetical():
    a = snap("a", ("zeta", 0.5, 3), ("alpha", 0.5, 3))
    b = snap("b", ("zeta", 0.4, 3), ("alpha", 0.4, 3))
    r1 = TeacherAssistance().report([a, b])
    r2 = TeacherAssistance().report([a, b])
    assert [c.concept_id for c in r1.concepts] == ["alpha", "zeta"]
    assert [c.concept_id for c in r2.concepts] == [c.concept_id for c in r1.concepts]


def test_learner_with_no_rated_concepts_excluded():
    empty = LearnerModel("noless")
    active = snap("l1", (3, 0.3, 3))
    report = TeacherAssistance().report([empty, active])
    assert report.n_learners == 2
    assert report.n_rated == 1
    assert all("noless" not in (r.at_risk or []) for r in report.concepts)
    assert [r.n_students_rated for r in report.concepts] == [1]


def test_accepts_learner_model_objects_duck_typed():
    model = LearnerModel("model-1")
    model.observe(Interaction(concept_id="geom", kind="answer", outcome=1.0))
    model.observe(Interaction(concept_id="geom", kind="answer", outcome=1.0))
    model.observe(Interaction(concept_id="geom", kind="answer", outcome=0.0))
    report = TeacherAssistance().report([model])
    row = report.concepts[0]
    assert row.concept_id == "geom"
    assert row.class_accuracy == pytest.approx(2 / 3, abs=1e-2)
    assert row.n_students_rated == 1


def test_class_report_as_dict_serialization():
    a = snap("a", ("3", 0.3, 4), ("9", 1.0, 4))
    b = snap("b", ("3", 0.4, 4), ("9", 1.0, 4))
    report = TeacherAssistance().report([a, b])
    exported = report.as_dict()
    assert set(exported) == {"concepts", "suggested_focus",
                             "n_learners", "n_rated", "params"}
    assert exported["n_learners"] == 2
    assert exported["n_rated"] == 2
    assert exported["params"]["model"] == "class_aggregate"
    assert {"concept_id", "class_accuracy", "n_students_rated",
            "at_risk", "focus_priority"} <= set(exported["concepts"][0])
    assert set(exported["suggested_focus"]) == {"3"}