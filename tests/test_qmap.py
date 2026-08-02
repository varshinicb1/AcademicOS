"""P1.9 — Question → Concept mapping (propose + verify) tests."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.graph.schema import new_node
from academicos.models.enums import NodeType


def concept_graph(tmp_path, concepts: list[tuple[str, dict]]):
    from academicos.graph.store import GraphStore
    store = GraphStore(tmp_path / "graph.sqlite")
    for label, attrs in concepts:
        store.upsert_node(new_node(NodeType.CONCEPT, label, attributes=attrs))
    return store


class _FakeLLM:
    def __init__(self, response: dict, flag: str = "ok"):
        self.available_flag = flag != "unavailable"
        self.response = response

    @property
    def available(self) -> bool:
        return self.available_flag

    def chat_json(self, messages, **kw):
        return self.response


def test_lexical_exact_and_bloom(tmp_path):
    from academicos.qmap import QuestionMapper
    store = concept_graph(tmp_path, [
        ("Photosynthesis", {"bloom": "understand"}),
        ("Newton's second law of motion", {"bloom": "apply"}),
    ])
    m = QuestionMapper(store)
    qmap = m.map("Explain what photosynthesis is.")
    assert qmap.method == "lexical+verify"
    assert len(qmap.concepts) >= 1
    top = qmap.concepts[0]
    assert top.name == "Photosynthesis"
    assert top.verified is True
    assert top.node_id and "cbse:concept:" in top.node_id


def test_lexical_no_llm_skips_llm(tmp_path):
    from academicos.qmap import QuestionMapper
    store = concept_graph(tmp_path, [("Fractions", {}), ("Perimeter", {})])
    m = QuestionMapper(store, llm=_FakeLLM({"concepts": []}, flag="unavailable"))
    assert m._llm_ok() is False
    qmap = m.map("What is the perimeter of a rectangle?")
    assert qmap.method == "lexical+verify"
    assert all(c.verified for c in qmap.concepts)


def test_out_of_graph_flagged(tmp_path):
    from academicos.qmap import QuestionMapper
    store = concept_graph(tmp_path, [("Perimeter", {"bloom": "apply"})])
    llm = _FakeLLM({"concepts": [
        {"name": "Root hair cell", "bloom": "remember", "confidence": 0.6}]})
    m = QuestionMapper(store, llm=llm)
    qmap = m.map("Describe the anatomy of a root hair cell.")
    hits = [c for c in qmap.concepts if not c.verified]
    assert hits, "unknown concepts should surface as out-of-graph, not vanish"
    assert hits[0].out_of_graph is True
    assert qmap.method == "llm+verify"


def test_bloom_conflict_uses_graph_profile(tmp_path):
    from academicos.qmap import QuestionMapper
    store = concept_graph(tmp_path, [("Photosynthesis", {"bloom": "understand"})])
    llm = _FakeLLM({"concepts": [
        {"name": "Photosynthesis", "bloom": "evaluate", "confidence": 0.9}]})
    m = QuestionMapper(store, llm=llm)
    qmap = m.map("Evaluate the role of photosynthesis in the carbon cycle.")
    assert qmap.method == "llm+verify"
    c = qmap.concepts[0]
    assert c.verified is True
    assert c.bloom == "understand"  # graph profile wins
    assert c.bloom_conflict is True


def test_llm_proposal_resolved_casefolded(tmp_path):
    from academicos.qmap import QuestionMapper
    store = concept_graph(tmp_path, [("Newtons Second Law", {"bloom": "apply"})])
    llm = _FakeLLM({"concepts": [{"name": "newtons second law",
                                  "bloom": "apply", "confidence": 0.5}]})
    m = QuestionMapper(store, llm=llm)
    qmap = m.map("State Newton's second law.")
    c = qmap.concepts[0]
    assert c.verified is True
    assert c.node_id and "concept" in c.node_id


def test_dedupe_dupe_proposals(tmp_path):
    from academicos.qmap import QuestionMapper
    store = concept_graph(tmp_path, [("Perimeter", {})])
    llm = _FakeLLM({"concepts": [
        {"name": "Perimeter", "bloom": None, "confidence": 0.7},
        {"name": "PERIMETER", "bloom": None, "confidence": 0.8}]})
    m = QuestionMapper(store, llm=llm)
    qmap = m.map("Perimeter of a square.")
    assert len(qmap.concepts) == 1


def test_question_map_store_roundtrip(tmp_path):
    from academicos.qmap import QuestionMapper, QuestionConcept
    from academicos.storage.question_map import QuestionMapStore, question_key
    store = concept_graph(tmp_path, [("Perimeter", {})])
    mapper = QuestionMapper(store)
    qmap = mapper.map("What is the perimeter?")
    qs = QuestionMapStore(tmp_path / "qm.jsonl")
    key = qs.append(qmap.to_dict())
    assert key == question_key(qmap.question)
    assert qs.count() == 1
    got = qs.for_question("what is   the perimeter?")
    assert got["question"].split() == ["What", "is", "the", "perimeter?"]


def test_store_stable_key_dedupes_whitespace(tmp_path):
    from academicos.storage.question_map import QuestionMapStore, question_key
    assert question_key(" Solve  it ") == question_key("solve it")