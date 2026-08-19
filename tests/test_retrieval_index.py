"""Hermetic tests for retrieval/index.py (ChunkIndex: FTS5 BM25 + pure-python TF-IDF).

Fully offline: FTS5 ships with stdlib sqlite3 and TF-IDF is pure python. All
SQLite lives in pytest tmp_path; connections are closed in fixture teardown.
"""
from __future__ import annotations

import math
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.extract.chunking import Chunk
from academicos.retrieval.index import ChunkIndex


def _chunk(cid, doc_id, page, text, heading="h"):
    return Chunk(id=cid, document_id=doc_id, page=page,
                 heading_path=[heading] if heading else [], text=text)


@pytest.fixture
def index(tmp_path):
    ix = ChunkIndex(tmp_path / "idx.sqlite")
    yield ix
    ix.close()


# --------------------------------------------------------------------------- #
# add / count / replace_doc
# --------------------------------------------------------------------------- #

def test_add_and_count(index):
    assert index.count() == 0
    index.add([_chunk("c1", "d1", 1, "Photosynthesis converts light to chemical energy.")])
    assert index.count() == 1
    index.add([_chunk("c2", "d1", 2, "Respiration releases energy from glucose.")])
    assert index.count() == 2


def test_add_without_replace_keeps_existing_chunks(index):
    index.add([_chunk("c1", "d1", 1, "Photosynthesis uses chlorophyll.")])
    index.add([_chunk("c2", "d1", 2, "Photosynthesis splits water.")])
    assert index.count() == 2
    ids = {c.id for c, _ in index.bm25("photosynthesis", limit=10)}
    assert ids == {"c1", "c2"}


def test_add_with_replace_doc_removes_old_chunks(index):
    index.add([_chunk("c1", "d1", 1, "Old photosynthesis paragraph.")])
    index.add([
        _chunk("c2", "d1", 2, "New photosynthesis paragraph."),
        _chunk("c3", "d1", 3, "Chlorophyll absorbs light in chloroplasts."),
    ], replace_doc=True)
    assert index.count() == 2
    assert {c.id for c, _ in index.bm25("photosynthesis", limit=10)} == {"c2"}
    assert {c.id for c, _ in index.bm25("chlorophyll", limit=10)} == {"c3"}


def test_replace_doc_replaces_all_documents_in_batch(index):
    index.add([_chunk("c1", "d1", 1, "old d1 stuff"),
               _chunk("c2", "d2", 1, "old d2 stuff")])
    index.add([_chunk("c3", "d1", 2, "new d1 stuff"),
               _chunk("c4", "d2", 2, "new d2 stuff")], replace_doc=True)
    # every document in the replaced batch is dropped, not just the first one
    assert index.count() == 2
    ids = {c.id for c, _ in index.bm25("stuff", limit=10)}
    assert ids == {"c3", "c4"}


# --------------------------------------------------------------------------- #
# bm25
# --------------------------------------------------------------------------- #

def test_bm25_ranks_better_matching_chunks_higher(index):
    index.add([
        _chunk("cA", "d1", 1, "Photosynthesis uses chlorophyll found in the chloroplast of plant cells."),
        _chunk("cB", "d2", 1, "Photosynthesis is the conversion of light energy to chemical energy."),
        _chunk("cC", "d3", 1, "Newton's second law relates force mass and acceleration."),
    ])
    hits = index.bm25("photosynthesis chlorophyll chloroplast", limit=10)
    assert [c.id for c, _ in hits] == ["cA", "cB"]
    assert hits[0][1] > hits[1][1]


def test_bm25_empty_query_returns_empty(index):
    index.add([_chunk("c1", "d1", 1, "photosynthesis text")])
    assert index.bm25("") == []
    assert index.bm25("   ") == []
    assert index.bm25("!!! ???") == []


def test_bm25_respects_limit(index):
    for i in range(5):
        index.add([_chunk(f"c{i}", f"d{i}", 1, f"photosynthesis in plants {i}")])
    hits = index.bm25("photosynthesis", limit=3)
    assert len(hits) == 3


def test_bm25_round_trips_chunk_fields(index):
    index.add([_chunk("c1", "d1", 7, "Photosynthesis occurs in chloroplasts.", heading="Photosynthesis")])
    hits = index.bm25("photosynthesis", limit=10)
    assert len(hits) == 1
    c, score = hits[0]
    assert c.id == "c1"
    assert c.document_id == "d1"
    assert c.page == 7
    assert c.heading == "Photosynthesis"
    assert c.text == "Photosynthesis occurs in chloroplasts."
    assert score > 0


# --------------------------------------------------------------------------- #
# tfidf
# --------------------------------------------------------------------------- #

def test_tfidf_scores_and_absent_terms_zero(index):
    index.add([
        _chunk("c1", "d1", 1, "photosynthesis photosynthesis photosynthesis"),
        _chunk("c2", "d2", 1, "respiration releases energy from glucose"),
    ])
    hits = index.tfidf("photosynthesis", limit=20)
    assert hits and hits[0][0].document_id == "d1"
    by_doc = {c.document_id: s for c, s in hits}
    assert by_doc["d2"] == 0.0
    # idf = log((doc_count+1)/(df+1)) + 1 = log(3/2) + 1 with 2 docs, 1 containing the term
    assert hits[0][1] == pytest.approx(math.log(1.5) + 1.0)


def test_tfidf_caps_three_chunks_per_document(index):
    index.add([_chunk(f"c{i}", "d1", i, f"photosynthesis occurs in plants part {i}")
               for i in range(1, 5)])
    hits = index.tfidf("photosynthesis", limit=20)
    d1_chunks = [c for c, _ in hits if c.document_id == "d1"]
    assert len(d1_chunks) == 3


def test_tfidf_idf_reset_after_delete(index):
    # _df must reflect the *current* corpus: a deleted document's document
    # frequency must not linger and pull idf down on later queries.
    index.add([_chunk("c1", "d1", 1, "photosynthesis photosynthesis"),
               _chunk("c2", "d2", 1, "photosynthesis"),
               _chunk("c3", "d3", 1, "respiration releases energy")])
    index.delete_document("d1")
    # after the delete: 2 docs, 1 still containing the term
    # idf = log((doc_count+1)/(df+1)) + 1 = log(3/2) + 1
    hits = index.tfidf("photosynthesis", limit=20)
    by_doc = {c.document_id: s for c, s in hits}
    assert by_doc["d2"] == pytest.approx(math.log(1.5) + 1.0)
    assert "d1" not in by_doc


def test_tfidf_multi_chunk_document_accumulates_all_chunks(index):
    # a document split across chunks must be scored over ALL its chunks, not
    # just the last one added to the index.
    index.add([
        _chunk("c1", "d1", 1, "photosynthesis converts light energy"),
        _chunk("c2", "d1", 2, "photosynthesis splits water and releases oxygen"),
        _chunk("c3", "d2", 1, "respiration releases energy from glucose"),
    ])
    # "converts" appears only in d1's FIRST chunk; d1 must still be scored > 0
    hits = index.tfidf("converts", limit=20)
    by_doc = {c.document_id: s for c, s in hits}
    assert by_doc["d1"] > 0.0
    # and the combined token stats rank d1 ahead of d2 for "photosynthesis"
    hits2 = index.tfidf("photosynthesis", limit=20)
    assert hits2 and hits2[0][0].document_id == "d1"


def test_tfidf_empty_index(tmp_path):
    ix = ChunkIndex(tmp_path / "empty.sqlite")
    assert ix.tfidf("anything") == []
    ix.close()


# --------------------------------------------------------------------------- #
# delete / persistence / close
# --------------------------------------------------------------------------- #

def test_delete_document(index):
    index.add([
        _chunk("c1", "d1", 1, "photosynthesis in plants"),
        _chunk("c2", "d1", 2, "photosynthesis light reaction"),
        _chunk("c3", "d2", 1, "photosynthesis basics"),
    ])
    index.delete_document("d1")
    assert index.count() == 1
    ids = {c.id for c, _ in index.bm25("photosynthesis", limit=10)}
    assert ids == {"c3"}
    t = index.tfidf("photosynthesis", limit=20)
    assert [c.document_id for c, _ in t] == ["d2"]


def test_delete_document_unknown_id_is_noop(index):
    index.add([_chunk("c1", "d1", 1, "photosynthesis x")])
    index.delete_document("missing")
    assert index.count() == 1


def test_persistence_after_close_and_reopen(tmp_path):
    db = tmp_path / "idx.sqlite"
    ix = ChunkIndex(db)
    ix.add([_chunk("c1", "d1", 1, "Photosynthesis occurs in plants.", heading="Photosynthesis")])
    ix.close()

    ix2 = ChunkIndex(db)
    assert ix2.count() == 1
    hits = ix2.bm25("photosynthesis", limit=10)
    assert len(hits) == 1 and hits[0][0].id == "c1"
    t = ix2.tfidf("photosynthesis", limit=10)
    assert [c.id for c, _ in t] == ["c1"]
    ix2.close()


def test_close_closes_connection(index):
    index.close()
    with pytest.raises(sqlite3.ProgrammingError):
        index.count()


def test_close_idempotent(index):
    index.close()
    index.close()


# --------------------------------------------------------------------------- #
# package re-exports
# --------------------------------------------------------------------------- #

def test_retrieval_package_reexports():
    import academicos.retrieval as ret
    from academicos.retrieval.hybrid import HybridRetriever, RetrievalHit, rrf
    from academicos.retrieval.index import ChunkIndex
    from academicos.retrieval.rerank import get_reranker, heading_prior

    assert ret.ChunkIndex is ChunkIndex
    assert ret.HybridRetriever is HybridRetriever
    assert ret.RetrievalHit is RetrievalHit
    assert ret.rrf is rrf
    assert ret.get_reranker is get_reranker
    assert ret.heading_prior is heading_prior
    assert set(ret.__all__) == {
        "HybridRetriever", "RetrievalHit", "rrf", "ChunkIndex",
        "get_reranker", "heading_prior",
    }