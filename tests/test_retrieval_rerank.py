"""Hermetic tests for retrieval/rerank.py (heading_prior + cross_encoder fallback).

The cross-encoder path downloads a model, which is forbidden here: we only test
the ImportError fallback (sentence-transformers masked out of sys.modules).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.extract.chunking import Chunk
from academicos.retrieval.hybrid import RetrievalHit
from academicos.retrieval.rerank import cross_encoder, get_reranker, heading_prior


def _hit(cid, heading, text="body text", score=0.0):
    return RetrievalHit(chunk=Chunk(id=cid, document_id="d1", page=1,
                                    heading_path=[heading], text=text),
                        score=score)


# --------------------------------------------------------------------------- #
# heading_prior
# --------------------------------------------------------------------------- #

def test_heading_prior_adds_tenth_per_matching_long_word():
    hits = [_hit("c1", "Photosynthesis", score=1.0),
            _hit("c2", "Respiration", score=1.0)]
    out = heading_prior("explain photosynthesis", hits)
    by_id = {h.chunk.id: h.score for h in out}
    assert by_id["c1"] == pytest.approx(1.1)
    assert by_id["c2"] == pytest.approx(1.0)
    assert out[0].chunk.id == "c1"


def test_heading_prior_counts_multiple_matches():
    hits = [_hit("c1", "Photosynthesis plants", score=0.0)]
    out = heading_prior("define photosynthesis plants", hits)
    assert out[0].score == pytest.approx(0.2)


def test_heading_prior_ignores_short_query_words():
    hits = [_hit("c1", "at", score=0.0), _hit("c2", "the", score=0.0)]
    out = heading_prior("at the", hits)
    assert all(h.score == 0.0 for h in out)


def test_heading_prior_returns_sorted_desc():
    hits = [_hit("c1", "Other", score=1.0), _hit("c2", "Photosynthesis", score=1.0)]
    out = heading_prior("explain photosynthesis", hits)
    assert [h.chunk.id for h in out] == ["c2", "c1"]
    scores = [h.score for h in out]
    assert scores == sorted(scores, reverse=True)


# --------------------------------------------------------------------------- #
# get_reranker / cross_encoder
# --------------------------------------------------------------------------- #

def test_get_reranker_default_returns_heading_prior():
    assert get_reranker(False) is heading_prior
    assert get_reranker() is heading_prior


def test_cross_encoder_falls_back_to_heading_prior_on_import_error(monkeypatch):
    monkeypatch.setitem(sys.modules, "sentence_transformers", None)
    rerank = cross_encoder()
    hits = [_hit("c1", "Photosynthesis", score=0.5),
            _hit("c2", "Other", score=0.5)]
    out = rerank("define photosynthesis", hits)
    by_id = {h.chunk.id: h.score for h in out}
    assert by_id["c1"] == pytest.approx(0.6)
    assert by_id["c2"] == pytest.approx(0.5)
    assert out[0].chunk.id == "c1"


def test_cross_encoder_fallback_with_empty_hits(monkeypatch):
    monkeypatch.setitem(sys.modules, "sentence_transformers", None)
    rerank = cross_encoder()
    assert rerank("anything", []) == []