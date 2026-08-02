"""Learning-outcome ontology tests: LO statement derivation, layer build
(MAPS_TO + inherited prereqs), and LO-level planning."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.graph.learning_outcomes import (
    build_lo_layer,
    lo_node,
    lo_node_id,
    lo_statement,
)
from academicos.graph.query import prereq_plan
from academicos.graph.schema import new_node
from academicos.graph.store import GraphStore
from academicos.models.enums import EdgeType, NodeType


def test_lo_statement_templates():
    assert lo_statement("fractions", "apply") == \
        "apply the concept of fractions to solve problems"
    assert lo_statement("photosynthesis", "understand") == \
        "explain and compare the concept of photosynthesis"
    assert lo_statement("x", "unknown-level") == \
        "explain and compare the concept of x"


def test_lo_node_canonical_id_and_attrs():
    n = lo_node("fractions", "apply", difficulty=3, learning_hours=2.0)
    assert n.type == NodeType.LEARNING_OUTCOME
    assert n.id == lo_node_id("fractions", "apply")
    assert n.attributes["concept"] == "fractions"
    assert n.attributes["bloom"] == "apply"
    assert n.attributes["difficulty"] == 3
    assert n.attributes["learning_hours"] == 2.0


def test_build_lo_layer(tmp_path):
    store = GraphStore(tmp_path / "lo.db")
    for label in ("fractions", "algebra"):
        store.upsert_node(new_node(NodeType.CONCEPT, label,
                                   id_=f"cbse:concept:{label}"))
    profiles = {
        "fractions": {"bloom": "apply", "difficulty": 2, "learning_hours": 1.5},
        "algebra": {"bloom": "analyze", "difficulty": 3, "learning_hours": 2.0},
    }
    prereqs = {"algebra": [("fractions", 0.7, 5)]}
    n_lo, n_maps, n_prereq = build_lo_layer(store, profiles, prereqs)
    assert (n_lo, n_maps, n_prereq) == (2, 2, 1)

    lo_frac = store.get_node(lo_node_id("fractions", "apply"))
    assert lo_frac is not None
    assert lo_frac.label == "apply the concept of fractions to solve problems"
    lo_alg = store.get_node(lo_node_id("algebra", "analyze"))
    assert lo_alg is not None

    # MAPS_TO edges concept -> LO
    maps = store.conn.execute(
        "SELECT source, target FROM edges WHERE type='MAPS_TO'").fetchall()
    assert len(maps) == 2
    # PREREQUISITE_OF LO -> LO inherited with derived flag
    pre = store.conn.execute(
        "SELECT source, target, attributes FROM edges WHERE type='PREREQUISITE_OF'").fetchone()
    assert pre["source"] == lo_node_id("fractions", "apply")
    assert pre["target"] == lo_node_id("algebra", "analyze")
    import json
    assert json.loads(pre["attributes"]) == {"derived": True, "score": 0.7}
    store.close()


def test_build_lo_layer_skips_missing_profiles(tmp_path):
    store = GraphStore(tmp_path / "lo2.db")
    for label in ("a",):
        store.upsert_node(new_node(NodeType.CONCEPT, label,
                                   id_=f"cbse:concept:{label}"))
    profiles = {"a": {"bloom": "understand"}}
    prereqs = {"b": [("a", 0.5, 3)], "c": [("a", 0.6, 4)]}
    n_lo, n_maps, n_prereq = build_lo_layer(store, profiles, prereqs)
    assert (n_lo, n_maps, n_prereq) == (1, 1, 0)
    store.close()


def test_lo_prereq_plan(tmp_path):
    from academicos.graph.learning_outcomes import lo_node_id
    store = GraphStore(tmp_path / "lop.db")
    for label in ("fractions", "algebra", "calculus"):
        store.upsert_node(new_node(NodeType.CONCEPT, label,
                                   id_=f"cbse:concept:{label}"))
    profiles = {
        "fractions": {"bloom": "apply", "difficulty": 2, "learning_hours": 1.5},
        "algebra": {"bloom": "analyze", "difficulty": 3, "learning_hours": 2.0},
        "calculus": {"bloom": "create", "difficulty": 5, "learning_hours": 3.0},
    }
    prereqs = {"algebra": [("fractions", 0.7, 5)],
               "calculus": [("algebra", 0.8, 6)]}
    build_lo_layer(store, profiles, prereqs)

    plan = prereq_plan(store, "create solutions involving calculus"
                       if False else lo_node_id("calculus", "create")[:0] or
                       "design and create solutions involving calculus",
                       ntype=NodeType.LEARNING_OUTCOME)
    assert plan["concept"] == "design and create solutions involving calculus"
    labels = [s["label"] for s in plan["steps"]]
    assert labels[-1] == "design and create solutions involving calculus"
    frac = next(s for s in plan["steps"]
                if s["label"] == "apply the concept of fractions to solve problems")
    assert frac["score"] == pytest.approx(0.7)
    assert frac["difficulty"] == 2
    assert labels.index("apply the concept of fractions to solve problems") < \
        labels.index("analyze problems and situations involving algebra")
    store.close()
