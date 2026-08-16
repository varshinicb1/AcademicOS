"""Hermetic tests for the deterministic curriculum layer (graph/curriculum.py).

Pure functions (Bloom/difficulty/hours/shannon/transitivity) plus the FTS5
index-backed CurriculumEstimator (mine/grade/text/vote prerequisites). Real
SQLite FTS in a tmp dir; no spacy, no LLM, no network.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.extract.chunking import Chunk
from academicos.graph.builder import GraphBuilder
from academicos.graph.curriculum import (
    VOTE_THETA,
    CurriculumEstimator,
    _phrase,
    _plain_label,
    _shannon,
    classify_bloom,
    estimate_difficulty,
    estimate_learning_hours,
    transitive_prereqs,
)
from academicos.graph.store import GraphStore
from academicos.retrieval.index import ChunkIndex


def _chunk(cid, doc_id, page, text, heading="h"):
    return Chunk(id=cid, document_id=doc_id, page=page, heading_path=[heading], text=text)


@pytest.fixture
def index(tmp_path):
    ix = ChunkIndex(tmp_path / "index.sqlite")
    yield ix
    ix.close()


@pytest.fixture
def estimator(tmp_path, index):
    est = CurriculumEstimator(tmp_path / "index.sqlite")
    yield est
    est.close()


# --------------------------------------------------------------------------- #
# pure functions
# --------------------------------------------------------------------------- #

def test_classify_bloom():
    assert classify_bloom(["define", "list", "name"]) == "remember"
    assert classify_bloom(["explain", "describe", "discuss"]) == "understand"
    assert classify_bloom(["design", "create", "construct"]) == "create"
    assert classify_bloom([]) == "understand"
    assert classify_bloom(["gibberish", "zzz"]) == "understand"
    # tie broken toward the higher cognitive demand
    assert classify_bloom(["define", "design"]) == "create"


def test_estimate_difficulty():
    assert estimate_difficulty("remember", 100, 2) == 1
    assert estimate_difficulty("create", 100, 1) == 4
    assert estimate_difficulty("create", 1, 1) == 5            # rare -> +1
    assert estimate_difficulty("create", 100, 3) == 4          # familiar -> -0.5
    assert estimate_difficulty("create", 1, 3, prereq_count=8) == 5  # clamped at 5
    assert estimate_difficulty("remember", 5, 1, prereq_count=4) == 2  # 1+0.5+0.5 -> 2


def test_estimate_learning_hours():
    assert estimate_learning_hours(1) == 1.0
    assert estimate_learning_hours(2) == 1.5
    assert estimate_learning_hours(5) == 3.0


def test_shannon_entropy():
    assert _shannon({}) == 0.0
    assert _shannon({"a": 10}) == 0.0
    uniform = _shannon({"a": 1, "b": 1, "c": 1})
    assert uniform == pytest.approx(1.0986, abs=1e-3)
    assert uniform > _shannon({"a": 9, "b": 1})


def test_transitive_prereqs_two_hop():
    prereqs = {
        "C": [("B", 0.8, 2)],
        "B": [("A", 0.8, 2)],
    }
    out = transitive_prereqs(prereqs)
    assert ("B", 0.8, 2) in out["C"]
    assert ("A", 0.8, 2) in out["B"]
    assert ("A", pytest.approx(0.64), 4) in out["C"]


def test_transitive_prereqs_drops_below_theta():
    prereqs = {"C": [("B", 0.3, 2)], "B": [("A", 0.9, 2)]}
    out = transitive_prereqs(prereqs)
    # 0.3*0.9=0.27 < VOTE_THETA -> no composed edge
    assert all(p != "A" for p, _, _ in out["C"])


def test_phrase_and_plain_label():
    assert _phrase("water cycle") == '"water cycle"'
    assert _phrase('rate "of"') == '"rate  of"'
    assert _plain_label("cbse:concept:water") == "water"
    assert _plain_label("cbse:concept:photosynthesis") == "photosynthesis"


# --------------------------------------------------------------------------- #
# index-backed estimators
# --------------------------------------------------------------------------- #

def test_occurs_in(index, estimator):
    index.add([_chunk("c1", "d1", 9, "Algebra is the study of equations and variables.")])
    assert estimator.occurs_in("algebra") is True
    assert estimator.occurs_in("trigonometry") is False


def test_mine_prerequisites_from_page_order(index, estimator):
    index.add([
        # d1: algebra appears before trigonometry
        _chunk("c1", "d1", 5, "Algebra is the study of equations and variables."),
        _chunk("c2", "d1", 7, "Algebra and trigonometry are both math topics."),
        _chunk("c3", "d1", 9, "Trigonometry is about triangles and angles."),
        # d2: same relative order
        _chunk("c4", "d2", 5, "Algebra fundamentals are revisited here."),
        _chunk("c5", "d2", 9, "Trigonometry and algebra connect in triangles."),
    ])
    prereqs = estimator.mine_prerequisites(["algebra", "trigonometry"], min_support=2)
    assert "algebra" in {p for p, _, _ in prereqs["trigonometry"]}
    entry = next(p for p in prereqs["trigonometry"] if p[0] == "algebra")
    assert entry[1] == pytest.approx(1.0)  # share
    assert entry[2] == 2                   # support


def test_grade_prerequisites_cross_grade(index, estimator):
    index.add([
        _chunk("c1", "g7", 9, "Algebra is introduced in grade seven."),
        _chunk("c2", "g8", 9, "Trigonometry is studied in grade eight."),
    ])
    prereqs = estimator.grade_prerequisites(
        ["algebra", "trigonometry"], {"g7": 7, "g8": 8})
    assert prereqs["trigonometry"] == [("algebra", 1.0, 1)]
    assert "trigonometry" not in prereqs.get("algebra", [])


def test_graph_link_stats_and_text_prerequisites(tmp_path):
    store = GraphStore(tmp_path / "g.sqlite")
    GraphBuilder(store).build_triples("g1", [("trigonometry", "requires", "algebra"),
                                             ("trigonometry", "needs", "angles")])
    est = CurriculumEstimator(tmp_path / "index.sqlite")  # empty index is fine
    stats = est.graph_link_stats(store)
    assert stats["cbse:concept:trigonometry"] == (0, 2)
    assert stats["cbse:concept:algebra"] == (1, 0)
    tp = est.text_prerequisites(store)
    assert tp["cbse:concept:trigonometry"] == [
        ("cbse:concept:algebra", 1.0, 1),
        ("cbse:concept:angles", 1.0, 1),
    ]
    est.close()
    store.close()


def test_vote_prerequisites_temporal_order(tmp_path, index, estimator):
    index.add([
        _chunk("c1", "d1", 9, "Algebra is the base concept of quantitative reasoning."),
        _chunk("c2", "d1", 12, "Trigonometry builds on algebra."),
        _chunk("c3", "d2", 9, "Algebra revisited for advanced learners."),
        _chunk("c4", "d2", 12, "Trigonometry depends on algebra foundations."),
    ])
    prereqs = estimator.vote_prerequisites(
        ["algebra", "trigonometry"],
        min_criteria=1,
        min_cooccur=2,
        criteria=("TemO",),
        strong_criteria=("TemO",),
    )
    assert prereqs["trigonometry"] == [("algebra", pytest.approx(1.0), 1)]


def test_vote_prerequisites_text_triples(tmp_path, index, estimator):
    index.add([
        _chunk("c1", "d1", 9, "Algebra and trigonometry overview for the board."),
    ])
    store = GraphStore(tmp_path / "g.sqlite")
    GraphBuilder(store).build_triples("g1", [("trigonometry", "requires", "algebra")])
    prereqs = estimator.vote_prerequisites(
        ["algebra", "trigonometry"],
        graph=store,
        min_criteria=1,
        min_cooccur=1,
        criteria=("Text",),
        strong_criteria=("Text",),
    )
    assert prereqs["trigonometry"] == [("algebra", pytest.approx(1.0), 2)]
    store.close()


def test_vote_prerequisites_theta_gate(tmp_path, index, estimator):
    # single criterion, weight 1 -> score 1.0; theta above it -> no edge
    index.add([
        _chunk("c1", "d1", 9, "Algebra base."),
        _chunk("c2", "d1", 12, "Trigonometry later."),
        _chunk("c3", "d2", 9, "Algebra base again."),
        _chunk("c4", "d2", 12, "Trigonometry later again."),
    ])
    prereqs = estimator.vote_prerequisites(
        ["algebra", "trigonometry"],
        min_criteria=1,
        min_cooccur=2,
        criteria=("TemO",),
        strong_criteria=("TemO",),
        theta=1.5,
    )
    assert prereqs == {}