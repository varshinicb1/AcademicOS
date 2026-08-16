"""Hermetic tests for the graph layer: schema id/factories, SQLite GraphStore,
GraphBuilder canonical-object wiring, and the query helpers.

Uses real SQLite in a tmp dir and hand-built academic objects with provenance.
No network, no LLM.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.graph.builder import GraphBuilder, _entity_part
from academicos.graph.query import (
    candidate_concepts,
    evidence_chain,
    exam_pattern_for,
    find_concept_chain,
    prereq_plan,
    subgraph_for_query,
)
from academicos.graph.schema import edge_id, new_edge, new_node, node_id, retract
from academicos.graph.store import GraphStore
from academicos.models.academic import (
    AnswerScheme,
    Concept,
    MarkingPoint,
    Question,
    QuestionPart,
    QuestionPaper,
)
from academicos.models.common import Confidence, Evidence, Provenance, SourceSpan
from academicos.models.enums import EdgeType, ExtractionMethod, GraphStatus, NodeType


def _prov(doc_id="d1", page=1):
    return Provenance(
        source=SourceSpan(document_id=doc_id, page=page),
        method=ExtractionMethod.PDF_NATIVE,
        confidence=Confidence(method=ExtractionMethod.PDF_NATIVE, score=0.9),
    )


def _evidence(doc_id="d1", page=1):
    return Evidence(items=[_prov(doc_id, page)])


@pytest.fixture
def store(tmp_path):
    s = GraphStore(tmp_path / "graph.sqlite")
    yield s
    s.close()


def _question(qid, q_no="1", marks=2.0):
    return Question(
        canonical_id=f"cbse:q:{qid}:{q_no}",
        question_paper_id=f"cbse:qp:{qid}",
        q_no=q_no,
        marks=marks,
        title=f"Question {q_no}",
        evidence=_evidence(qid),
    )


# --------------------------------------------------------------------------- #
# schema factories
# --------------------------------------------------------------------------- #

def test_node_id_and_edge_id_deterministic():
    nid = node_id(NodeType.CONCEPT, "Photosynthesis")
    assert nid == "cbse:concept:Photosynthesis"
    nid2 = node_id(NodeType.CONCEPT, "Photosynthesis")
    assert nid2 == nid
    assert node_id(NodeType.QUESTION, "qp1", "3") == "cbse:question:qp1:3"
    e1 = edge_id(EdgeType.RELATED_TO, "a", "b")
    e2 = edge_id(EdgeType.RELATED_TO, "a", "b")
    e3 = edge_id(EdgeType.RELATED_TO, "b", "a")
    assert e1 == e2
    assert e1 != e3
    assert e1.startswith("edge:")


def test_new_node_defaults_and_status():
    n = new_node(NodeType.TOPIC, "Electricity", id_="cbse:topic:elec")
    assert n.id == "cbse:topic:elec"
    assert n.type is NodeType.TOPIC
    assert n.label == "Electricity"
    assert n.status is GraphStatus.DRAFT
    assert n.attributes == {}
    assert n.created_at and n.updated_at


def test_new_node_auto_id_from_label():
    n = new_node(NodeType.CONCEPT, "Fractions")
    assert n.id == "cbse:concept:Fractions"


def test_retract_sets_status_and_valid_until():
    n = new_node(NodeType.CONCEPT, "X", id_="cbse:concept:x")
    retract(n)
    assert n.status is GraphStatus.RETRACTED
    assert n.valid_until is not None


def test_new_edge_provenance():
    e = new_edge(EdgeType.CONTAINS, "a", "b", weight=0.5, attributes={"k": 1},
                 provenance=_prov())
    assert e.id == edge_id(EdgeType.CONTAINS, "a", "b")
    assert e.weight == 0.5
    assert e.attributes == {"k": 1}
    assert e.provenance is not None


# --------------------------------------------------------------------------- #
# GraphStore
# --------------------------------------------------------------------------- #

def test_store_upsert_and_get_node(store):
    n = new_node(NodeType.CONCEPT, "Photosynthesis", id_="cbse:concept:photo")
    store.upsert_node(n)
    got = store.get_node("cbse:concept:photo")
    assert got is not None
    assert got.label == "Photosynthesis"
    assert got.type is NodeType.CONCEPT
    # upsert bumps version and updates label
    n2 = new_node(NodeType.CONCEPT, "Photosynthesis updated", id_="cbse:concept:photo")
    store.upsert_node(n2)
    got2 = store.get_node("cbse:concept:photo")
    assert got2.version == 2
    assert got2.label == "Photosynthesis updated"


def test_store_query_nodes(store):
    for i, lab in enumerate(["Algebra", "Geometry", "Trigo"]):
        store.upsert_node(new_node(NodeType.TOPIC, lab, id_=f"cbse:topic:t{i}"))
    store.upsert_node(new_node(NodeType.CONCEPT, "Algebraic identity", id_="cbse:concept:ai"))
    assert len(store.query_nodes(NodeType.TOPIC)) == 3
    assert len(store.query_nodes(NodeType.CONCEPT)) == 1
    assert len(store.query_nodes(label_contains="trig")) == 1
    assert store.query_nodes(NodeType.TOPIC, label_contains="geo")[0].label == "Geometry"


def test_store_upsert_edge_and_get_edge(store):
    a = new_node(NodeType.CONCEPT, "A", id_="cbse:concept:a")
    b = new_node(NodeType.CONCEPT, "B", id_="cbse:concept:b")
    store.upsert_node(a)
    store.upsert_node(b)
    e = new_edge(EdgeType.PREREQUISITE_OF, "cbse:concept:a", "cbse:concept:b")
    store.upsert_edge(e)
    got = store.get_edge(e.id)
    assert got is not None
    assert got.source == "cbse:concept:a"
    assert got.target == "cbse:concept:b"
    assert got.type is EdgeType.PREREQUISITE_OF


def test_store_neighbors_bfs(store):
    a, b, c = "cbse:concept:a", "cbse:concept:b", "cbse:concept:c"
    for nid in (a, b, c):
        store.upsert_node(new_node(NodeType.CONCEPT, nid, id_=nid))
    store.upsert_edge(new_edge(EdgeType.RELATED_TO, a, b))
    store.upsert_edge(new_edge(EdgeType.RELATED_TO, b, c))
    nb = store.neighbors(a, max_depth=2)
    labels = {h["node"].id for h in nb}
    assert labels == {b, c}
    depths = {h["node"].id: h["depth"] for h in nb}
    assert depths[b] == 1
    assert depths[c] == 2


def test_store_paths(store):
    a, b, c = "cbse:concept:a", "cbse:concept:b", "cbse:concept:c"
    for nid in (a, b, c):
        store.upsert_node(new_node(NodeType.CONCEPT, nid, id_=nid))
    store.upsert_edge(new_edge(EdgeType.PREREQUISITE_OF, a, b))
    store.upsert_edge(new_edge(EdgeType.PREREQUISITE_OF, b, c))
    paths = store.paths(a, c)
    assert len(paths) == 1
    assert len(paths[0]) == 2
    assert paths[0][0].type is EdgeType.PREREQUISITE_OF


def test_store_count_and_snapshot(store):
    store.upsert_node(new_node(NodeType.CONCEPT, "X", id_="cbse:concept:x"))
    store.upsert_node(new_node(NodeType.CONCEPT, "Y", id_="cbse:concept:y"))
    store.upsert_edge(new_edge(EdgeType.RELATED_TO, "cbse:concept:x", "cbse:concept:y"))
    assert store.count() == (2, 1)
    snap = store.snapshot(notes="first")
    assert snap.node_count == 2
    assert snap.edge_count == 1
    assert snap.snapshot_id == "snap:1"


# --------------------------------------------------------------------------- #
# GraphBuilder
# --------------------------------------------------------------------------- #

def test_builder_upsert_object_and_build_question(store):
    gb = GraphBuilder(store)
    q = _question("qp1", q_no="1")
    q.parts = [QuestionPart(
        canonical_id="cbse:q:qp1:1a", question_id=q.canonical_id, part="a",
        title="Q1(a)", text="Part a", evidence=q.evidence)]
    qid = gb.build_question(q)
    assert qid == "cbse:q:qp1:1"
    node = store.get_node(qid)
    assert node.type is NodeType.QUESTION
    assert node.attributes.get("marks") == 2.0
    # CONTAINS edge to the part
    rows = store.conn.execute("SELECT * FROM edges WHERE source=? AND type=?",
                              (qid, EdgeType.CONTAINS.value)).fetchall()
    assert len(rows) == 1
    assert rows[0]["target"] == "cbse:q:qp1:1a"


def test_builder_build_answer_scheme(store):
    gb = GraphBuilder(store)
    scheme = AnswerScheme(
        canonical_id="cbse:as:qp1",
        question_id="cbse:q:qp1:1",
        document_id="d1",
        title="Scheme",
        evidence=_evidence("d1"),
        marking_points=[
            MarkingPoint(canonical_id="cbse:mp:qp1:1", answer_scheme_id="cbse:as:qp1",
                         point_no=1, marks=2.0, detail="Stated the law.",
                         title="MP1", evidence=_evidence("d1")),
        ],
    )
    sid = gb.build_answer_scheme(scheme)
    assert store.get_node(sid).type is NodeType.ANSWER_SCHEME
    rows = store.conn.execute("SELECT target FROM edges WHERE source=? AND type=?",
                              (sid, EdgeType.HAS_MARKING_POINT.value)).fetchall()
    assert [r["target"] for r in rows] == ["cbse:mp:qp1:1"]


def test_builder_build_paper(store):
    gb = GraphBuilder(store)
    q1 = _question("qp1", q_no="1")
    q2 = _question("qp1", q_no="2")
    gb.build_question(q1)
    gb.build_question(q2)
    paper = QuestionPaper(
        canonical_id="cbse:qp:qp1", title="Sample Paper 2025",
        questions=["cbse:q:qp1:1", "cbse:q:qp1:2"],
        evidence=_evidence("qp1"), total_marks=80, duration_min=180)
    pid = gb.build_paper(paper)
    assert store.get_node(pid).type is NodeType.QUESTION_PAPER
    rows = store.conn.execute("SELECT target FROM edges WHERE source=? AND type=?",
                              (pid, EdgeType.CONTAINS.value)).fetchall()
    assert {r["target"] for r in rows} == {"cbse:q:qp1:1", "cbse:q:qp1:2"}


def test_builder_build_triples_dedupes_and_counts_occurrences(store):
    gb = GraphBuilder(store)
    triples = [
        ("Photosynthesis", "requires", "sunlight"),
        ("Photosynthesis", "requires", "chlorophyll"),
        ("Photosynthesis", "requires", "sunlight"),  # repeat
    ]
    nodes, edges = gb.build_triples("d1", triples, page=3)
    assert nodes == 3  # 3 distinct entities
    assert edges == 3  # 3 upserts (repeat bumps occurrences, still counted)
    ent = store.get_node(node_id(NodeType.CONCEPT, "photosynthesis"))
    assert ent is not None
    assert ent.type is NodeType.CONCEPT
    # repeated predicate aggregated on one edge
    sun = node_id(NodeType.CONCEPT, "sunlight")
    e = store.get_edge(edge_id(EdgeType.RELATED_TO, node_id(NodeType.CONCEPT, "photosynthesis"), sun))
    assert e is not None
    assert e.attributes["occurrences"] == 2
    assert e.attributes["predicates"] == ["requires"]


def test_builder_build_triples_self_loop_skipped(store):
    gb = GraphBuilder(store)
    nodes, edges = gb.build_triples("d1", [("A", "equals", "A")])
    assert nodes == 1
    assert edges == 0


def test_builder_unknown_object_type_maps_to_document(store):
    gb = GraphBuilder(store)
    nid = gb.upsert_object(Concept(
        canonical_id="cbse:concept:uni", title="Unit Tests",
        evidence=_evidence("d1"), definition="def"))
    assert store.get_node(nid).type is NodeType.CONCEPT


def test_entity_part_normalization():
    assert _entity_part("Fractions") == "fractions"
    assert _entity_part("  spaced   name  ") == "spaced name"
    assert _entity_part("a:b:c") == "a-b-c"


# --------------------------------------------------------------------------- #
# query helpers
# --------------------------------------------------------------------------- #

def test_candidate_concepts_heuristic():
    cands = candidate_concepts("What is photosynthesis in plants?")
    assert "photosynthesis" in cands
    assert "what" not in cands
    assert "the" not in cands
    assert len(cands) <= 5


def test_find_concept_chain(store):
    gb = GraphBuilder(store)
    gb.build_triples("d1", [("Photosynthesis", "requires", "sunlight"),
                            ("Photosynthesis", "requires", "chlorophyll")])
    res = find_concept_chain(store, "photosynthesis")
    assert res["concept"] is not None
    assert res["concept"].label == "Photosynthesis"
    assert len(res["related"]) == 2
    assert all(x["edge"].type == EdgeType.RELATED_TO for x in res["related"])
    missing = find_concept_chain(store, "nonexistentxyz")
    assert missing["concept"] is None


def test_subgraph_for_query(store):
    gb = GraphBuilder(store)
    gb.build_triples("d1", [("Photosynthesis", "requires", "sunlight"),
                            ("Photosynthesis", "requires", "chlorophyll")])
    res = subgraph_for_query(store, "explain photosynthesis")
    assert "Photosynthesis" in res["concepts"]
    assert len(res["nodes"]) >= 1
    assert len(res["edges"]) >= 1


def test_evidence_chain_walks_neighbors(store):
    gb = GraphBuilder(store)
    gb.build_triples("d1", [("Magnetism", "related_to", "Electromagnetism")])
    nid = node_id(NodeType.CONCEPT, "magnetism")
    chain = evidence_chain(store, nid)
    assert len(chain) == 1
    assert chain[0]["edge"].type is EdgeType.RELATED_TO


def test_exam_pattern_for(store):
    gb = GraphBuilder(store)
    paper = QuestionPaper(
        canonical_id="cbse:qp:phy", title="Physics Sample Paper 2025",
        questions=[], evidence=_evidence("qp1"), academic_year="2025",
        subject="Physics")
    gb.upsert_object(paper)
    out = exam_pattern_for(store, "Physics", "2025")
    assert len(out) == 1
    assert out[0]["attrs"]["academic_year"] == "2025"
    # wrong year filtered out
    assert exam_pattern_for(store, "Physics", "2024") == []


def test_prereq_plan_orders_foundations_first(store):
    gb = GraphBuilder(store)
    basic = new_node(NodeType.CONCEPT, "basic_math", id_="cbse:concept:basic")
    trig = new_node(NodeType.CONCEPT, "trigonometry", id_="cbse:concept:trig")
    store.upsert_node(basic)
    store.upsert_node(trig)
    store.upsert_edge(new_edge(
        EdgeType.PREREQUISITE_OF, "cbse:concept:basic", "cbse:concept:trig",
        attributes={"score": 0.8, "confidence": 0.7, "recommended_spacing_days": 3},
        provenance=_prov()))
    plan = prereq_plan(store, "trigonometry")
    assert plan["concept"] == "trigonometry"
    steps = [s["label"] for s in plan["steps"]]
    assert steps == ["basic_math", "trigonometry"]
    assert plan["steps"][0]["confidence"] == 0.7
    assert plan["steps"][0]["spacing_days"] == 3


def test_prereq_plan_min_confidence_gate(store):
    gb = GraphBuilder(store)
    basic = new_node(NodeType.CONCEPT, "basic_math", id_="cbse:concept:basic")
    trig = new_node(NodeType.CONCEPT, "trigonometry", id_="cbse:concept:trig")
    store.upsert_node(basic)
    store.upsert_node(trig)
    store.upsert_edge(new_edge(
        EdgeType.PREREQUISITE_OF, "cbse:concept:basic", "cbse:concept:trig",
        attributes={"score": 0.8, "confidence": 0.2}, provenance=_prov()))
    plan = prereq_plan(store, "trigonometry", min_confidence=0.5)
    assert plan["concept"] == "trigonometry"
    assert [s["label"] for s in plan["steps"]] == ["trigonometry"]
    missing = prereq_plan(store, "nope")
    assert missing["concept"] is None
    assert missing["steps"] == []