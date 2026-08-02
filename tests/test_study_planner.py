"""A12 — Study Planner v2 tests: prereq order + FSRS spacing + capacity."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.algorithms.learner_model import Interaction, LearnerModel
from academicos.algorithms.study_planner import StudyPlanner, PlanItem, StudyPlan
from academicos.graph.schema import new_edge, new_node
from academicos.graph.store import GraphStore
from academicos.models.enums import EdgeType, NodeType


def build_graph(tmp_path, edges: list[tuple[str, str]]):
    """Chain edges (prereq, later). Target is the last node in the DAG."""
    store = GraphStore(tmp_path / "graph.sqlite")
    ids: dict[str, str] = {}
    labels = {n for e in edges for n in e}
    for label in labels:
        node = new_node(NodeType.CONCEPT, label,
                        attributes={"difficulty": 3.0, "learning_hours": 1.0,
                                    "bloom": "understand"})
        store.upsert_node(node)
        ids[label] = node.id
    for prereq, later in edges:
        store.upsert_edge(new_edge(
            EdgeType.PREREQUISITE_OF, ids[prereq], ids[later],
            weight=0.9, attributes={"confidence": 0.9, "score": 0.7,
                                    "recommended_spacing_days": 2}))
    return store, ids


def test_plan_orders_prereqs_topologically(tmp_path):
    store, ids = build_graph(tmp_path, [("A", "B"), ("B", "C")])
    planner = StudyPlanner(store, default_capacity_minutes=60)
    plan = planner.plan("C", capacity_minutes=60)
    assert plan.target == "C"
    assert [i.label for i in plan.session] == ["A", "B", "C"]
    assert all(i.action == "learn" for i in plan.session)
    assert plan.totals["in_session"] == 3
    assert plan.totals["deferred"] == 0


def test_capacity_trims_tail_in_order(tmp_path):
    store, ids = build_graph(tmp_path, [("A", "B"), ("B", "C"), ("C", "D")])
    planner = StudyPlanner(store, minutes_per_concept=5,
                           default_capacity_minutes=10)
    plan = planner.plan("D")
    assert [i.label for i in plan.session] == ["A", "B"]
    assert plan.totals["deferred"] == 2
    assert {i.label for i in plan.upcoming} == {"C", "D"}
    assert all(i.scheduled_for for i in plan.upcoming)


def test_mastered_prereqs_are_dropped(tmp_path):
    store, ids = build_graph(tmp_path, [("A", "B"), ("B", "C")])
    learner = LearnerModel("t")
    learner.observe(Interaction(concept_id="A", kind="answer", outcome=1.0))
    planner = StudyPlanner(store, default_capacity_minutes=60)
    plan = planner.plan("C", capacity_minutes=60, learner=learner)
    # A is mastered (>= gate) -> dropped; B and C remain to learn
    assert [i.label for i in plan.session] == ["B", "C"]


def test_learned_but_forgotten_becomes_retrieve(tmp_path):
    store, ids = build_graph(tmp_path, [("A", "B"), ("B", "C")])
    # A and B each near-before-threshold: at least one should flip to retrieve
    learner = LearnerModel("tier")
    for cid in ("A", "B"):
        learner.observe(Interaction(concept_id=cid, kind="answer", outcome=0.0,
                                    ts="2001-01-01T00:00:00+00:00"))
    planner = StudyPlanner(store, default_capacity_minutes=60)
    plan = planner.plan("C", capacity_minutes=60, learner=learner)
    actions = {i.label: i.action for i in plan.session}
    assert actions.get("A") == "retrieve", "forgotten A should be retrieval"


def test_unknown_target_yields_empty(tmp_path):
    store, ids = build_graph(tmp_path, [("A", "B")])
    planner = StudyPlanner(store, default_capacity_minutes=15)
    plan = planner.plan("Nothing")
    assert plan.session == []
    assert plan.totals == {}


def test_params_report_model_and_capacity(tmp_path):
    store, ids = build_graph(tmp_path, [("A", "B")])
    planner = StudyPlanner(store, default_capacity_minutes=15)
    plan = planner.plan("B")
    assert plan.params["forgetting_model"] == "fsrs"
    assert plan.params["default_capacity_minutes"] == 15