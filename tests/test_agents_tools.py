"""Hermetic tests for the agent tool protocol and the built-in tools."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from academicos.agents.base import (
    ConceptLookupTool,
    EvidencePack,
    SearchTool,
    ToolResult,
)
from academicos.graph.schema import new_edge, new_node
from academicos.models.common import Confidence, Evidence, Provenance, SourceSpan
from academicos.models.enums import EdgeType, ExtractionMethod, NodeType


class _RaisingRetriever:
    def search(self, query, limit=12, **kw):
        raise RuntimeError("boom")


# --------------------------------------------------------------------------- #
# SearchTool
# --------------------------------------------------------------------------- #

def test_search_tool_ok_payload_shape(retriever):
    tool = SearchTool(retriever)
    res = tool.run(query="photosynthesis light reaction", limit=2)
    assert res.ok is True
    assert res.tool == "search"
    assert res.error is None
    assert len(res.payload) == 2
    for p in res.payload:
        assert set(p) == {"document_id", "page", "heading", "score", "text"}
        assert isinstance(p["page"], int)
        assert isinstance(p["score"], float)
        assert p["score"] == round(p["score"], 3)  # rounded to 3 dp
        assert len(p["text"]) <= 600


def test_search_tool_ok_empty_payload(empty_retriever):
    tool = SearchTool(empty_retriever)
    res = tool.run(query="photosynthesis", limit=5)
    assert res.ok is True
    assert res.payload == []


def test_search_tool_ok_false_with_error_when_retriever_raises():
    tool = SearchTool(_RaisingRetriever())
    res = tool.run(query="photosynthesis", limit=5)
    assert res.ok is False
    assert res.tool == "search"
    assert res.payload is None
    assert res.error == "boom"


# --------------------------------------------------------------------------- #
# ConceptLookupTool
# --------------------------------------------------------------------------- #

@pytest.fixture
def concept_graph(graph):
    photo = new_node(NodeType.CONCEPT, "Photosynthesis", id_="cbse:concept:photosynthesis")
    sun = new_node(NodeType.CONCEPT, "Sunlight", id_="cbse:concept:sunlight")
    chloro = new_node(NodeType.CONCEPT, "Chlorophyll", id_="cbse:concept:chlorophyll")
    graph.upsert_node(photo)
    graph.upsert_node(sun)
    graph.upsert_node(chloro)
    graph.upsert_edge(new_edge(EdgeType.PREREQUISITE_OF, sun.id, photo.id))
    graph.upsert_edge(new_edge(EdgeType.RELATED_TO, photo.id, chloro.id))
    return graph


def test_concept_lookup_ok_payload_shape(concept_graph):
    tool = ConceptLookupTool(concept_graph)
    res = tool.run(concept="Photosynthesis")
    assert res.ok is True
    assert res.error is None
    assert set(res.payload) == {"concept", "prereqs", "related"}
    assert res.payload["concept"].label == "Photosynthesis"
    assert len(res.payload["prereqs"]) == 1
    assert res.payload["prereqs"][0]["edge"].type is EdgeType.PREREQUISITE_OF
    assert len(res.payload["related"]) == 1
    assert res.payload["related"][0]["edge"].type is EdgeType.RELATED_TO


def test_concept_lookup_not_found_returns_ok_false(graph):
    tool = ConceptLookupTool(graph)
    res = tool.run(concept="nonexistentconceptxyz")
    assert res.ok is False
    assert res.payload is None
    assert res.error == "concept not found: nonexistentconceptxyz"


def test_concept_lookup_exception_captured(graph):
    graph.close()
    tool = ConceptLookupTool(graph)
    res = tool.run(concept="Photosynthesis")
    assert res.ok is False
    assert res.payload is None
    assert "closed" in res.error


# --------------------------------------------------------------------------- #
# EvidencePack
# --------------------------------------------------------------------------- #

def test_evidence_pack_defaults():
    pack = EvidencePack()
    assert isinstance(pack.evidence, Evidence)
    assert pack.tool_calls == []
    assert pack.messages == []


def test_evidence_pack_collects_state():
    pack = EvidencePack()
    pack.tool_calls.append({"tool": "search", "query": "q", "ok": True})
    pack.messages.append({"role": "user", "content": "hello"})
    pack.evidence.add(Provenance(
        source=SourceSpan(document_id="d1", page=1),
        method=ExtractionMethod.PDF_NATIVE,
        confidence=Confidence(method=ExtractionMethod.PDF_NATIVE, score=0.9),
    ))
    assert pack.tool_calls == [{"tool": "search", "query": "q", "ok": True}]
    assert pack.messages == [{"role": "user", "content": "hello"}]
    assert len(pack.evidence.items) == 1
    assert pack.evidence.items[0].source.document_id == "d1"


# --------------------------------------------------------------------------- #
# ToolResult
# --------------------------------------------------------------------------- #

def test_tool_result_defaults():
    tr = ToolResult(tool="t", ok=True)
    assert tr.tool == "t"
    assert tr.ok is True
    assert tr.payload is None
    assert tr.error is None


def test_tool_result_fields():
    tr = ToolResult(tool="t", ok=False, payload={"x": 1}, error="nope")
    assert (tr.tool, tr.ok, tr.payload, tr.error) == ("t", False, {"x": 1}, "nope")