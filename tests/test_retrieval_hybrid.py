"""Hermetic tests for retrieval/hybrid.py (rrf fusion, HybridRetriever.search,
subgraph evidence, reasoning paths). Real ChunkIndex + GraphStore on tmp SQLite;
no sentence-transformers, no network, no model downloads.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.extract.chunking import Chunk
from academicos.graph.builder import GraphBuilder
from academicos.graph.schema import new_edge, new_node
from academicos.graph.store import GraphStore
from academicos.models.enums import EdgeType, NodeType
from academicos.retrieval.hybrid import (
    HybridRetriever,
    RetrievalHit,
    _auto_keywords,
    rrf,
)
from academicos.retrieval.index import ChunkIndex


def _chunk(cid, doc_id, page, heading, text):
    return Chunk(id=cid, document_id=doc_id, page=page,
                 heading_path=[heading], text=text)


@pytest.fixture
def chunks():
    return [
        _chunk("c1", "docA", 1, "Photosynthesis",
               "Photosynthesis converts light energy into chemical energy in plants."),
        _chunk("c2", "docA", 2, "Light Reaction",
               "The light reaction of photosynthesis splits water and releases oxygen."),
        _chunk("c3", "docB", 1, "Respiration",
               "Cellular respiration releases energy from glucose in the mitochondria."),
        _chunk("c4", "docB", 2, "Newton",
               "Newton's laws relate force mass and acceleration."),
    ]


@pytest.fixture
def index(tmp_path):
    ix = ChunkIndex(tmp_path / "idx.sqlite")
    yield ix
    ix.close()


@pytest.fixture
def retriever(index, chunks):
    index.add(chunks)
    return HybridRetriever(index)


# --------------------------------------------------------------------------- #
# rrf
# --------------------------------------------------------------------------- #

def test_rrf_math():
    fused = rrf(["a", "b", "c"], ["b", "c", "d"])
    assert fused["a"] == pytest.approx(1 / 61)
    assert fused["b"] == pytest.approx(1 / 62 + 1 / 61)
    assert fused["c"] == pytest.approx(1 / 63 + 1 / 62)
    assert fused["d"] == pytest.approx(1 / 63)


def test_rrf_custom_k():
    fused = rrf(["a", "b"], ["a", "c"], k=10)
    assert fused["a"] == pytest.approx(1 / 11 + 1 / 11)
    assert fused["b"] == pytest.approx(1 / 12)
    assert fused["c"] == pytest.approx(1 / 12)


def test_rrf_empty_rankings():
    assert rrf() == {}
    assert rrf([], []) == {}


# --------------------------------------------------------------------------- #
# search basics
# --------------------------------------------------------------------------- #

def test_search_returns_ranked_hits(retriever):
    hits = retriever.search("photosynthesis light reaction", limit=10)
    assert hits
    assert len(hits) <= 10
    scores = [h.score for h in hits]
    assert scores == sorted(scores, reverse=True)
    assert all(isinstance(h, RetrievalHit) for h in hits)
    assert all(h.chunk.id and h.chunk.text for h in hits)


def test_retrieval_hit_fields_and_document_id(retriever):
    h = retriever.search("photosynthesis light reaction", limit=10)[0]
    assert isinstance(h.chunk, Chunk)
    assert h.chunk.id
    assert h.score > 0
    assert "bm25" in h.sources
    assert "dense" in h.sources
    assert h.graph_nodes == []
    assert h.document_id == h.chunk.document_id


def test_search_limit_and_sorting(retriever):
    hits = retriever.search("photosynthesis", limit=2)
    assert len(hits) == 2
    scores = [h.score for h in hits]
    assert scores == sorted(scores, reverse=True)
    assert len(retriever.search("photosynthesis", limit=1)) == 1


def test_search_empty_index(tmp_path):
    ix = ChunkIndex(tmp_path / "empty.sqlite")
    r = HybridRetriever(ix)
    assert r.search("photosynthesis") == []
    assert r.search("anything", dense=True) == []
    assert r.search("anything", dense=False) == []
    assert r.reasoning_paths("photosynthesis") == []
    ix.close()


# --------------------------------------------------------------------------- #
# boost keywords
# --------------------------------------------------------------------------- #

def test_search_boost_keywords_adds_bonus_only_to_matching_chunks(retriever):
    q = "photosynthesis"
    unboosted = {h.chunk.id: h.score
                 for h in retriever.search(q, limit=10, boost_keywords=["zzzznope"])}
    boosted = {h.chunk.id: h.score
               for h in retriever.search(q, limit=10, boost_keywords=["respiration"])}
    # c3 heading/text contain "respiration" -> +0.15
    assert boosted["c3"] == pytest.approx(unboosted["c3"] + 0.15)
    # chunks without the keyword are untouched (explicit keywords replace auto ones)
    assert boosted["c1"] == pytest.approx(unboosted["c1"])
    assert boosted["c2"] == pytest.approx(unboosted["c2"])
    assert boosted["c4"] == pytest.approx(unboosted["c4"])


def test_auto_keywords_stopword_filtering():
    assert _auto_keywords("what is photosynthesis in plants") == ["photosynthesis", "plants"]
    assert _auto_keywords("explain the process of respiration") == ["process", "respiration"]
    assert _auto_keywords("a an of") == []


def test_auto_keywords_caps_at_five():
    kw = _auto_keywords("photosynthesis light reaction water splitting oxygen")
    assert len(kw) == 5


def test_search_auto_keywords_boost_meaningful_tokens(retriever):
    q = "what is photosynthesis in plants"
    assert _auto_keywords(q) == ["photosynthesis", "plants"]
    unboosted = {h.chunk.id: h.score
                 for h in retriever.search(q, limit=10, boost_keywords=["zzzznope"])}
    auto = {h.chunk.id: h.score for h in retriever.search(q, limit=10)}
    # c1 matches both "photosynthesis" and "plants" (+0.15 each), c2 only "photosynthesis"
    assert auto["c1"] == pytest.approx(unboosted["c1"] + 0.15 * 2)
    assert auto["c2"] == pytest.approx(unboosted["c2"] + 0.15)
    assert auto["c3"] == pytest.approx(unboosted["c3"])
    assert auto["c4"] == pytest.approx(unboosted["c4"])


# --------------------------------------------------------------------------- #
# dense pathway
# --------------------------------------------------------------------------- #

def test_search_dense_flag_changes_fusion(tmp_path):
    ix = ChunkIndex(tmp_path / "idx.sqlite")
    ix.add([
        _chunk("a1", "dA", 1, "h", "photosynthesis photosynthesis"),
        _chunk("a2", "dA", 2, "h", "photosynthesis photosynthesis"),
        _chunk("a3", "dA", 3, "h", "photosynthesis photosynthesis"),
        _chunk("b1", "dB", 1, "h", "photosynthesis photosynthesis"),
        _chunk("c1", "dC", 1, "h", "photosynthesis photosynthesis photosynthesis"),
    ])
    r = HybridRetriever(ix)
    on = r.search("photosynthesis", limit=2, dense=True, boost_keywords=["nope"])
    off = r.search("photosynthesis", limit=2, dense=False, boost_keywords=["nope"])
    # bm25: [c1,a1,a2,a3]; tfidf: [a1,a2,a3,b1] -> fused order differs
    assert [h.chunk.id for h in on] == ["a1", "a2"]
    assert [h.chunk.id for h in off] == ["c1", "a1"]
    assert on[0].score == pytest.approx(1 / 62 + 1 / 61)   # dual-ranked
    assert off[0].score == pytest.approx(1 / 61)           # bm25-only rank 0
    assert "b1" not in {h.chunk.id for h in off}
    ix.close()


def test_search_dense_false_drops_dense_only_hits(retriever):
    on_ids = {h.chunk.id for h in retriever.search("photosynthesis", limit=10, dense=True)}
    off_ids = {h.chunk.id for h in retriever.search("photosynthesis", limit=10, dense=False)}
    # c3/c4 do not contain "photosynthesis" -> only reachable through tfidf
    assert {"c1", "c2", "c3", "c4"} == on_ids
    assert off_ids == {"c1", "c2"}
    bm25_ids = {c.id for c, _ in retriever.index.bm25("photosynthesis", limit=20)}
    assert off_ids <= bm25_ids
    # sources reflect the pathways actually used: dense=False -> bm25 only
    for h in retriever.search("photosynthesis", limit=10, dense=False):
        assert h.sources == ["bm25"]


def test_search_sources_label_actual_pathways(retriever):
    # "dense" is only reported when tfidf actually contributed the hit;
    # "bm25" only when the chunk was returned by FTS5.
    on = retriever.search("photosynthesis", limit=10, dense=True)
    on_by_id = {h.chunk.id: h.sources for h in on}
    assert on_by_id["c1"] == ["bm25", "dense"]  # present in both rankings
    assert on_by_id["c3"] == ["dense"]          # c3/c4 never matched bm25, only tfidf
    off = retriever.search("photosynthesis", limit=10, dense=False)
    for h in off:
        assert h.sources == ["bm25"]


# --------------------------------------------------------------------------- #
# graph: subgraph + graph boost + reasoning paths
# --------------------------------------------------------------------------- #

def test_search_subgraph_true_adds_graph_evidence(tmp_path):
    ix = ChunkIndex(tmp_path / "idx.sqlite")
    ix.add([
        _chunk("c1", "physdoc1", 1, "Photosynthesis", "Photosynthesis converts light to chemical energy."),
        _chunk("c2", "physdoc1", 2, "Chloroplast", "Chlorophyll absorbs light in the chloroplast."),
        _chunk("c3", "newtdoc", 1, "Newton", "Newton's second law relates force and acceleration."),
    ])
    graph = GraphStore(tmp_path / "graph.sqlite")
    GraphBuilder(graph).build_triples("physdoc1", [
        ("photosynthesis", "produces", "glucose"),
        ("chlorophyll", "absorbs", "light"),
    ])
    r = HybridRetriever(ix, graph)
    q = "what is photosynthesis"
    on = r.search(q, limit=10, subgraph=True)
    off = r.search(q, limit=10, subgraph=False)
    assert {h.chunk.id for h in on} == {h.chunk.id for h in off} == {"c1", "c2", "c3"}
    off_by_id = {h.chunk.id: h.score for h in off}
    for h in on:
        assert h.score == pytest.approx(off_by_id[h.chunk.id] + 0.05)
        assert h.graph_nodes == ["photosynthesis"]
        assert "subgraph" in h.sources
    assert all(not h.graph_nodes and "subgraph" not in h.sources for h in off)
    graph.close()
    ix.close()


def test_search_subgraph_no_matching_concepts(tmp_path):
    ix = ChunkIndex(tmp_path / "idx.sqlite")
    ix.add([_chunk("c3", "newtdoc", 1, "Newton", "Newton's second law relates force and acceleration.")])
    graph = GraphStore(tmp_path / "graph.sqlite")
    GraphBuilder(graph).build_triples("physdoc1", [("photosynthesis", "produces", "glucose")])
    r = HybridRetriever(ix, graph)
    on = r.search("newton", limit=10, subgraph=True)
    off = r.search("newton", limit=10, subgraph=False)
    assert on and off
    assert [h.chunk.id for h in on] == [h.chunk.id for h in off]
    assert all("subgraph" not in h.sources and not h.graph_nodes for h in on)
    graph.close()
    ix.close()


def test_graph_boost_and_subgraph_score(tmp_path):
    ix = ChunkIndex(tmp_path / "idx.sqlite")
    doc_id = "physdoc1"
    ix.add([_chunk("c1", doc_id, 1, "h", "Photosynthesis happens in plants.")])
    graph = GraphStore(tmp_path / "graph.sqlite")
    graph.upsert_node(new_node(NodeType.DOCUMENT, "Document " + doc_id, id_="docnode1"))
    graph.upsert_node(new_node(NodeType.CONCEPT, "photosynthesis", id_="concept1"))
    graph.upsert_edge(new_edge(EdgeType.RELATED_TO, "docnode1", "concept1"))

    plain = HybridRetriever(ix)
    with_graph = HybridRetriever(ix, graph)
    base = {h.chunk.id: h.score for h in plain.search("photosynthesis", limit=5)}
    no_sg = {h.chunk.id: h.score for h in with_graph.search("photosynthesis", limit=5, subgraph=False)}
    sg = {h.chunk.id: h.score for h in with_graph.search("photosynthesis", limit=5, subgraph=True)}
    assert no_sg["c1"] == pytest.approx(base["c1"] + 0.1)          # _graph_boost
    assert sg["c1"] == pytest.approx(base["c1"] + 0.1 + 0.05)      # + subgraph concept score
    hit = with_graph.search("photosynthesis", limit=5)[0]
    assert hit.sources == ["bm25", "dense", "subgraph"]
    assert hit.graph_nodes == ["concept1", "photosynthesis"]
    graph.close()
    ix.close()


def test_reasoning_paths_with_graph(tmp_path):
    ix = ChunkIndex(tmp_path / "idx.sqlite")
    ix.add([_chunk("c1", "d1", 1, "h", "photosynthesis text")])
    graph = GraphStore(tmp_path / "graph.sqlite")
    GraphBuilder(graph).build_triples("d1", [("photosynthesis", "produces", "glucose")])
    r = HybridRetriever(ix, graph)
    paths = r.reasoning_paths("photosynthesis")
    assert isinstance(paths, list)
    assert paths
    assert all(isinstance(p, list) for p in paths)
    assert ["photosynthesis", "RELATED_TO"] in paths
    graph.close()
    ix.close()


def test_reasoning_paths_target_node(tmp_path):
    graph = GraphStore(tmp_path / "graph.sqlite")
    GraphBuilder(graph).build_triples("d1", [("photosynthesis", "produces", "glucose")])
    glucose = graph.query_nodes(NodeType.CONCEPT, label_contains="glucose", limit=1)[0]
    ix = ChunkIndex(tmp_path / "idx.sqlite")
    r = HybridRetriever(ix, graph)
    paths = r.reasoning_paths("photosynthesis", target_node=glucose.id)
    assert isinstance(paths, list)
    assert ["RELATED_TO"] in paths
    ix.close()
    graph.close()


def test_reasoning_paths_without_graph(tmp_path):
    r = HybridRetriever(ChunkIndex(tmp_path / "idx.sqlite"))
    assert r.reasoning_paths("photosynthesis") == []
    r.index.close()