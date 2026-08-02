"""Prerequisite edge enrichment tests: edge materialization, confidence and
spacing math, and store round-trip (pure, no API calls)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.graph.curriculum import CRITERION_WEIGHTS
from academicos.graph.prereq_edges import (
    build_prerequisite_edges,
    confidence_from_votes,
    recommended_spacing_days,
    write_prerequisite_edges,
)
from academicos.graph.schema import edge_id, new_node
from academicos.graph.store import GraphStore
from academicos.models.enums import EdgeType, NodeType

ACTIVE = tuple(CRITERION_WEIGHTS.keys())
ACTIVE_W = float(sum(CRITERION_WEIGHTS.values()))


def test_confidence_range_and_monotonicity():
    low = confidence_from_votes(4.0, 2.0, ACTIVE_W)
    high = confidence_from_votes(6.0, 0.0, ACTIVE_W)
    assert 0.0 <= low <= high <= 1.0
    same_margin_more_participation = confidence_from_votes(8.0, 4.0, ACTIVE_W)
    assert same_margin_more_participation > confidence_from_votes(4.0, 2.0, ACTIVE_W)
    assert confidence_from_votes(0.0, 0.0, 0.0) == 0.0


def test_spacing_scales_with_gap_and_drops_with_confidence():
    assert recommended_spacing_days(1.0, 0) == 3
    assert recommended_spacing_days(1.0, 2) > recommended_spacing_days(1.0, 0)
    assert recommended_spacing_days(0.0, 0) > recommended_spacing_days(1.0, 0)
    assert recommended_spacing_days(0.0, 0) >= 1


def test_build_edges_direction_and_attributes():
    prereqs = {"later1": [("prereq1", 0.5, 6.0)]}
    label_to_id = {"later1": "cbse:concept:later1", "prereq1": "cbse:concept:prereq1"}
    detail = [{"prereq": "prereq1", "later": "later1", "score": 0.5,
               "va": 6.0, "vb": 2.0, "votes": {"CMH": 1, "IOLR": 1, "Text": 1}}]
    edges = build_prerequisite_edges(prereqs, label_to_id, pair_detail=detail,
                                     difficulty={"later1": 4, "prereq1": 2})
    assert len(edges) == 1
    e = edges[0]
    assert e.type == EdgeType.PREREQUISITE_OF
    assert e.source == "cbse:concept:prereq1"
    assert e.target == "cbse:concept:later1"
    assert e.weight == pytest.approx(0.5)
    a = e.attributes
    assert a["score"] == pytest.approx(0.5)
    assert a["confidence"] == pytest.approx(confidence_from_votes(6.0, 2.0, ACTIVE_W))
    assert a["criteria"] == {"CMH": 1, "IOLR": 1, "Text": 1}
    assert a["n_criteria"] == 3
    assert a["difficulty_jump"] == 2
    assert a["recommended_spacing_days"] >= 1
    assert "transitive" not in a


def test_build_edges_marks_transitive_when_no_detail():
    prereqs = {"later1": [("prereq1", 0.5, 6.0)]}
    label_to_id = {"later1": "cbse:concept:later1", "prereq1": "cbse:concept:prereq1"}
    edges = build_prerequisite_edges(prereqs, label_to_id)
    assert edges[0].attributes["transitive"] is True
    assert edges[0].attributes["criteria"] == {}
    assert "difficulty_jump" not in edges[0].attributes


def test_build_edges_skips_unknown_labels():
    prereqs = {"ghost": [("prereq1", 0.5, 6.0)], "later1": [("ghost2", 0.4, 4.0)]}
    label_to_id = {"later1": "cbse:concept:later1"}
    assert build_prerequisite_edges(prereqs, label_to_id) == []


def test_store_roundtrip(tmp_path):
    store = GraphStore(tmp_path / "g.db")
    for nid, label in (("cbse:concept:a", "a"), ("cbse:concept:b", "b")):
        store.upsert_node(new_node(NodeType.CONCEPT, label, id_=nid))
    edges = build_prerequisite_edges(
        {"b": [("a", 0.6, 8.0)]},
        {"a": "cbse:concept:a", "b": "cbse:concept:b"},
        pair_detail=[{"prereq": "a", "later": "b", "score": 0.6,
                      "va": 8.0, "vb": 0.0, "votes": {"HL-A": 1, "Text": 1}}],
    )
    assert write_prerequisite_edges(store, edges) == 1
    e = store.get_edge(edge_id(EdgeType.PREREQUISITE_OF, "cbse:concept:a", "cbse:concept:b"))
    assert e is not None
    assert e.type == EdgeType.PREREQUISITE_OF
    assert e.weight == pytest.approx(0.6)
    assert e.attributes["confidence"] > 0.5
    assert e.provenance is not None
    assert e.provenance.method.value == "rule_based"
    store.close()


def _concept(store, label, difficulty=3, hours=2.0):
    nid = f"cbse:concept:{label}"
    store.upsert_node(new_node(NodeType.CONCEPT, label, id_=nid,
                               attributes={"difficulty": difficulty,
                                           "learning_hours": hours, "bloom": "understand"}))
    return nid


def test_prereq_plan_topological_order(tmp_path):
    from academicos.graph.prereq_edges import (build_prerequisite_edges,
                                               write_prerequisite_edges)
    from academicos.graph.query import prereq_plan

    store = GraphStore(tmp_path / "p.db")
    # a <- b <- c  (a foundational, c target) plus c <- a direct
    ids = {lb: _concept(store, lb) for lb in ("a", "b", "c")}
    edges = build_prerequisite_edges(
        {"b": [("a", 0.8, 6.0)], "c": [("b", 0.6, 4.0), ("a", 0.7, 5.0)]},
        {lb: ids[lb] for lb in ("a", "b", "c")},
        pair_detail=[{"prereq": "a", "later": "b", "score": 0.8, "va": 6.0, "vb": 0.0,
                      "votes": {"HL-A": 1, "Text": 1}},
                     {"prereq": "b", "later": "c", "score": 0.6, "va": 4.0, "vb": 0.0,
                      "votes": {"HL-A": 1, "IOLR": 1}},
                     {"prereq": "a", "later": "c", "score": 0.7, "va": 5.0, "vb": 0.0,
                      "votes": {"CMH": 1, "Text": 1}}],
    )
    write_prerequisite_edges(store, edges)

    plan = prereq_plan(store, "c")
    assert plan["concept"] == "c"
    labels = [s["label"] for s in plan["steps"]]
    assert labels[-1] == "c"
    assert labels.index("a") < labels.index("b") < labels.index("c")
    a = next(s for s in plan["steps"] if s["label"] == "a")
    assert a["score"] == pytest.approx(0.8)
    assert a["confidence"] is not None
    assert a["spacing_days"] is not None
    assert a["difficulty"] == 3
    store.close()


def test_prereq_plan_confidence_gate(tmp_path):
    from academicos.graph.prereq_edges import (build_prerequisite_edges,
                                               write_prerequisite_edges)
    from academicos.graph.query import prereq_plan

    store = GraphStore(tmp_path / "pg.db")
    ids = {lb: _concept(store, lb) for lb in ("a", "b")}
    # high-confidence edge a->b and a low-confidence a2->b
    ids["a2"] = _concept(store, "a2")
    edges = build_prerequisite_edges(
        {"b": [("a", 0.9, 9.0), ("a2", 0.3, 2.0)]},
        ids,
        pair_detail=[{"prereq": "a", "later": "b", "score": 0.9, "va": 9.0, "vb": 0.0,
                      "votes": {"CMH": 1, "Text": 1, "HL-A": 1}},
                     {"prereq": "a2", "later": "b", "score": 0.3, "va": 2.0, "vb": 0.0,
                      "votes": {"Text": 1}}],
    )
    write_prerequisite_edges(store, edges)
    full = prereq_plan(store, "b")
    assert {s["label"] for s in full["steps"] if s["label"] != "b"} == {"a", "a2"}
    gated = prereq_plan(store, "b", min_confidence=0.5)
    labels = {s["label"] for s in gated["steps"] if s["label"] != "b"}
    assert "a" in labels and "a2" not in labels
    store.close()


def test_prereq_plan_missing_concept(tmp_path):
    from academicos.graph.query import prereq_plan

    store = GraphStore(tmp_path / "pm.db")
    assert prereq_plan(store, "nope")["steps"] == []
    store.close()

def test_prereq_plan_skips_mastered_prereq(tmp_path):
    from academicos.algorithms.learner_model import ConceptState, LearnerModel
    from academicos.graph.prereq_edges import (build_prerequisite_edges,
                                               write_prerequisite_edges)
    from academicos.graph.query import prereq_plan

    store = GraphStore(tmp_path / "pm2.db")
    ids = {lb: _concept(store, lb) for lb in ("a", "b", "c")}
    edges = build_prerequisite_edges(
        {"b": [("a", 0.8, 6.0)], "c": [("b", 0.6, 4.0)]},
        ids,
        pair_detail=[{"prereq": "a", "later": "b", "score": 0.8, "va": 6.0, "vb": 0.0,
                      "votes": {"HL-A": 1, "Text": 1}},
                     {"prereq": "b", "later": "c", "score": 0.6, "va": 4.0, "vb": 0.0,
                      "votes": {"HL-A": 1, "IOLR": 1}}],
    )
    write_prerequisite_edges(store, edges)

    learner = LearnerModel(learner_id="alice")
    learner.concepts["cbse:concept:a"] = ConceptState(
        concept_id="cbse:concept:a", mastery=0.9)

    plan = prereq_plan(store, "c", learner=learner)
    labels = [s["label"] for s in plan["steps"]]
    assert "a" not in labels
    assert "b" in labels and labels[-1] == "c"
    b = next(s for s in plan["steps"] if s["label"] == "b")
    assert b["mastered"] is False and b["mastery"] is None
    store.close()


def test_prereq_plan_label_fallback_and_target_mastered(tmp_path):
    from academicos.algorithms.learner_model import ConceptState, LearnerModel
    from academicos.graph.prereq_edges import (build_prerequisite_edges,
                                               write_prerequisite_edges)
    from academicos.graph.query import prereq_plan

    store = GraphStore(tmp_path / "pm3.db")
    ids = {lb: _concept(store, lb) for lb in ("a", "b")}
    edges = build_prerequisite_edges(
        {"b": [("a", 0.8, 6.0)]}, ids,
        pair_detail=[{"prereq": "a", "later": "b", "score": 0.8, "va": 6.0, "vb": 0.0,
                      "votes": {"HL-A": 1, "Text": 1}}],
    )
    write_prerequisite_edges(store, edges)

    learner = LearnerModel(learner_id="alice")
    learner.concepts["a"] = ConceptState(concept_id="a", mastery=0.9)
    plan = prereq_plan(store, "b", learner=learner)
    assert "a" not in [s["label"] for s in plan["steps"]]

    learner2 = LearnerModel(learner_id="bob")
    learner2.concepts["cbse:concept:b"] = ConceptState(
        concept_id="cbse:concept:b", mastery=0.95)
    plan2 = prereq_plan(store, "b", learner=learner2)
    assert plan2["steps"][-1]["mastered"] is True
    assert "a" in [s["label"] for s in plan2["steps"]]
    store.close()


def test_prereq_plan_mastery_gate(tmp_path):
    from academicos.algorithms.learner_model import ConceptState, LearnerModel
    from academicos.graph.prereq_edges import (build_prerequisite_edges,
                                               write_prerequisite_edges)
    from academicos.graph.query import prereq_plan

    store = GraphStore(tmp_path / "pm4.db")
    ids = {lb: _concept(store, lb) for lb in ("a", "b")}
    edges = build_prerequisite_edges(
        {"b": [("a", 0.8, 6.0)]}, ids,
        pair_detail=[{"prereq": "a", "later": "b", "score": 0.8, "va": 6.0, "vb": 0.0,
                      "votes": {"HL-A": 1, "Text": 1}}],
    )
    write_prerequisite_edges(store, edges)

    learner = LearnerModel(learner_id="alice")
    learner.concepts["a"] = ConceptState(concept_id="a", mastery=0.4)
    kept = prereq_plan(store, "b", learner=learner, mastery_gate=0.5)
    assert "a" in [s["label"] for s in kept["steps"]]
    dropped = prereq_plan(store, "b", learner=learner, mastery_gate=0.3)
    assert "a" not in [s["label"] for s in dropped["steps"]]
    store.close()


def test_prereq_plan_lo_resolves_mastery_via_maps_to(tmp_path):
    from academicos.algorithms.learner_model import ConceptState, LearnerModel
    from academicos.graph.learning_outcomes import (build_lo_layer, lo_node_id,
                                                    lo_statement)
    from academicos.graph.prereq_edges import (build_prerequisite_edges,
                                               write_prerequisite_edges)
    from academicos.graph.query import prereq_plan
    from academicos.models.enums import EdgeType

    store = GraphStore(tmp_path / "pmlo.db")
    ids = {lb: _concept(store, lb) for lb in ("a", "b")}
    edges = build_prerequisite_edges(
        {"b": [("a", 0.8, 6.0)]}, ids,
        pair_detail=[{"prereq": "a", "later": "b", "score": 0.8, "va": 6.0, "vb": 0.0,
                      "votes": {"HL-A": 1, "Text": 1}}],
    )
    write_prerequisite_edges(store, edges)
    profiles = {lb: {"bloom": "understand", "difficulty": 3.0,
                     "learning_hours": 2.0} for lb in ("a", "b")}
    build_lo_layer(store, profiles)

    learner = LearnerModel(learner_id="alice")
    learner.concepts["a"] = ConceptState(concept_id="a", mastery=0.9)
    plan = prereq_plan(store, "b", ntype=NodeType.LEARNING_OUTCOME,
                       learner=learner)
    labels = [s["label"] for s in plan["steps"]]
    assert lo_statement("a", "understand") not in labels
    assert lo_statement("b", "understand") in labels
    assert labels[-1] == lo_statement("b", "understand")
    store.close()
