"""Tests for graph models (academicos.models.graph)."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from academicos.models import (
    Confidence,
    Edge,
    EdgeType,
    ExtractionMethod,
    GraphSnapshot,
    GraphStatus,
    Node,
    NodeType,
    Provenance,
    SourceSpan,
)


def _prov():
    return Provenance(
        source=SourceSpan(document_id="d1", page=1),
        method=ExtractionMethod.ENSEMBLE,
        confidence=Confidence(method=ExtractionMethod.ENSEMBLE, score=0.9),
    )


def test_node_requires_id_type_label():
    with pytest.raises(ValidationError):
        Node(type=NodeType.CHAPTER, label="Ch 1")
    with pytest.raises(ValidationError):
        Node(id="n1", label="Ch 1")
    with pytest.raises(ValidationError):
        Node(id="n1", type=NodeType.CHAPTER)


def test_node_defaults():
    node = Node(id="n1", type=NodeType.CHAPTER, label="Ch 1")
    assert node.status == GraphStatus.DRAFT
    assert node.version == 1
    assert node.attributes == {}
    assert node.valid_from is None
    assert node.valid_until is None
    assert node.provenance is None
    assert node.created_at == ""
    assert node.updated_at == ""


def test_node_full_payload():
    node = Node(
        id="n1",
        type=NodeType.CHAPTER,
        label="Ch 1",
        status=GraphStatus.VERIFIED,
        version=3,
        provenance=_prov(),
        attributes={"grade": "XII"},
    )
    assert node.status == GraphStatus.VERIFIED
    assert node.version == 3
    assert node.provenance.confidence.score == 0.9
    assert node.attributes == {"grade": "XII"}


def test_edge_requires_id_source_target_type():
    with pytest.raises(ValidationError):
        Edge(source="n1", target="n2", type=EdgeType.CONTAINS)
    with pytest.raises(ValidationError):
        Edge(id="e1", target="n2", type=EdgeType.CONTAINS)
    with pytest.raises(ValidationError):
        Edge(id="e1", source="n1", type=EdgeType.CONTAINS)
    with pytest.raises(ValidationError):
        Edge(id="e1", source="n1", target="n2")


def test_edge_defaults():
    edge = Edge(id="e1", source="n1", target="n2", type=EdgeType.CONTAINS)
    assert edge.weight == 1.0
    assert edge.version == 1
    assert edge.status == GraphStatus.DRAFT
    assert edge.attributes == {}
    assert edge.provenance is None


def test_edge_weight_within_unit_interval():
    with pytest.raises(ValidationError):
        Edge(id="e1", source="n1", target="n2", type=EdgeType.CONTAINS, weight=1.5)
    with pytest.raises(ValidationError):
        Edge(id="e1", source="n1", target="n2", type=EdgeType.CONTAINS, weight=-0.1)
    assert Edge(id="e1", source="n1", target="n2", type=EdgeType.CONTAINS, weight=0.0).weight == 0.0


def test_graph_snapshot_requires_snapshot_id_and_created_at():
    with pytest.raises(ValidationError):
        GraphSnapshot(created_at="2026-01-01T00:00:00Z")
    with pytest.raises(ValidationError):
        GraphSnapshot(snapshot_id="s1")


def test_graph_snapshot_defaults():
    snap = GraphSnapshot(snapshot_id="s1", created_at="2026-01-01T00:00:00Z")
    assert snap.node_count == 0
    assert snap.edge_count == 0
    assert snap.notes == ""
    assert snap.parent_snapshot_id is None


def test_graph_snapshot_full_payload():
    snap = GraphSnapshot(
        snapshot_id="s2",
        created_at="2026-01-01T00:00:00Z",
        parent_snapshot_id="s1",
        node_count=10,
        edge_count=25,
        notes="second snapshot",
    )
    assert snap.parent_snapshot_id == "s1"
    assert snap.node_count == 10
    assert snap.edge_count == 25
    assert snap.notes == "second snapshot"


def test_node_round_trip_with_provenance():
    node = Node(id="n1", type=NodeType.CHAPTER, label="Ch 1", provenance=_prov())
    assert Node.model_validate_json(node.model_dump_json()) == node
