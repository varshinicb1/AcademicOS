"""Shared pytest fixtures for the agents test suite (hermetic, SQLite-in-tmp)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _agent_helpers import build_index, make_chunk
from academicos.retrieval.hybrid import HybridRetriever


@pytest.fixture
def default_chunks():
    return [
        make_chunk("c1", "XII_Physics_QP_2025", 3, "Section A",
                   "What is photosynthesis? Explain the light reaction and its products. (2 marks)"),
        make_chunk("c2", "XII_Physics_QP_2025", 4, "Section B",
                   "State Newton's second law of motion. (2 marks)"),
        make_chunk("c3", "XII_Physics_MarkingScheme_2025", 2, "Marking Scheme",
                   "Photosynthesis: conversion of light energy to chemical energy. Water splitting releases oxygen."),
        make_chunk("c4", "XII_Physics_Textbook_2025", 10, "Chapter 4 Photosynthesis",
                   "The light reaction of photosynthesis occurs in the thylakoid membrane and splits water."),
    ]


@pytest.fixture
def empty_index(tmp_path):
    idx = build_index(tmp_path, [])
    yield idx
    idx.close()


@pytest.fixture
def seeded_index(tmp_path, default_chunks):
    idx = build_index(tmp_path, default_chunks)
    yield idx
    idx.close()


@pytest.fixture
def retriever(seeded_index):
    return HybridRetriever(seeded_index)


@pytest.fixture
def empty_retriever(empty_index):
    return HybridRetriever(empty_index)


@pytest.fixture
def graph(tmp_path):
    from academicos.graph.store import GraphStore
    g = GraphStore(tmp_path / "graph.sqlite")
    yield g
    g.close()