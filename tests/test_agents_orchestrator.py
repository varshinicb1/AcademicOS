"""Hermetic tests for the agent orchestrators (DoubtSolver, ExaminerScorer,
PaperAnalyst) plus the private answer/citation helpers.

Retrieval fixtures are real offline ChunkIndex/HybridRetriever over tmp SQLite;
any LLM interaction is faked via FakeLLM at the client boundary.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _agent_helpers import FakeLLM, build_index, make_chunk, scoring_handler
from academicos.agents.critic import SarvamCritic
from academicos.agents.orchestrator import (
    Agent,
    DoubtSolver,
    ExaminerScorer,
    PaperAnalyst,
    _answer_from_hits,
    _cite,
)
from academicos.retrieval.hybrid import HybridRetriever

NO_EVIDENCE_MSG = "No evidence found in the corpus for this doubt. Try rephrasing or check the syllabus documents."


def _doubt_seed_chunks():
    return [
        make_chunk("d1", "docA", 3, "Sec A",
                   "Photosynthesis light reaction converts light energy into chemical energy in the thylakoid."),
        make_chunk("d2", "docB", 5, "Sec B",
                   "The Calvin cycle consumes the ATP and NADPH made during the light reaction."),
        make_chunk("d3", "docC", 7, "Sec C",
                   "During the light reaction of photosynthesis, water is split and oxygen is released."),
    ]


def _doubt_scores():
    return {
        "docA": {"relevant": False, "support": "none", "utility": 1},
        "docB": {"relevant": True, "support": "partial", "utility": 3},
        "docC": {"relevant": True, "support": "full", "utility": 5},
    }


# --------------------------------------------------------------------------- #
# DoubtSolver.solve WITHOUT a critic
# --------------------------------------------------------------------------- #

def test_solve_without_critic_is_deterministic(tmp_path):
    idx = build_index(tmp_path, [
        make_chunk("s1", "doc1", 7, "Chapter 1", "Photosynthesis uses light energy."),
    ])
    try:
        solver = DoubtSolver(HybridRetriever(idx))
        result = solver.solve("photosynthesis light energy")
        expected = (
            "Based on the corpus, the following passages are most relevant to your doubt:\n\n"
            "[1] (doc1 p.7) Photosynthesis uses light energy."
        )
        assert result["answer"] == expected
        assert result["citations"] == [{"document_id": "doc1", "page": 7, "heading": "Chapter 1"}]
        assert result["evidence"] == [{"document_id": "doc1", "page": 7}]
        assert result["reflection"] == {"used_critic": False}
    finally:
        idx.close()


def test_solve_without_critic_cites_and_limits_evidence(tmp_path):
    chunks = [make_chunk(f"e{i}", f"doc{i}", i + 1, "Sec",
                         f"Question paper 2025 marks item {i} evidence text") for i in range(8)]
    idx = build_index(tmp_path, chunks)
    try:
        solver = DoubtSolver(HybridRetriever(idx))
        result = solver.solve("question paper 2025 marks item")
        assert result["agent"] == "doubt-solver"
        assert result["doubt"] == "question paper 2025 marks item"
        assert result["answer"].startswith("Based on the corpus")
        assert len(result["citations"]) == 8
        assert len(result["evidence"]) == 5  # evidence capped at 5, citations not
        for c in result["citations"]:
            assert set(c) == {"document_id", "page", "heading"}
        for e in result["evidence"]:
            assert set(e) == {"document_id", "page"}
        assert result["reflection"] == {"used_critic": False}
    finally:
        idx.close()


def test_solve_without_critic_no_evidence_on_empty_index(empty_retriever):
    solver = DoubtSolver(empty_retriever)
    result = solver.solve("what is the capital of france")
    assert result["answer"] == NO_EVIDENCE_MSG
    assert result["citations"] == []
    assert result["evidence"] == []
    assert result["reflection"] == {"used_critic": False}


# --------------------------------------------------------------------------- #
# DoubtSolver.solve WITH a critic
# --------------------------------------------------------------------------- #

def test_solve_with_critic_retrieve_false_skips_retrieval(retriever):
    llm = FakeLLM(responses=[{"retrieve": False}])
    solver = DoubtSolver(retriever, critic=SarvamCritic(llm))
    result = solver.solve("photosynthesis")
    assert "No retrieval needed" in result["answer"]
    assert result["citations"] == []
    assert result["evidence"] == []
    assert result["reflection"] == {"used_critic": True, "retrieved": False}


def test_solve_with_critic_retrieve_true_zero_hits(empty_retriever):
    llm = FakeLLM(responses=[{"retrieve": True}])
    solver = DoubtSolver(empty_retriever, critic=SarvamCritic(llm))
    result = solver.solve("photosynthesis")
    assert result["answer"] == "No evidence found in the corpus for this doubt."
    assert result["citations"] == []
    assert result["evidence"] == []
    assert result["reflection"] == {"used_critic": True, "retrieved": True, "paths": []}


def test_solve_with_critic_selects_best_path(tmp_path):
    idx = build_index(tmp_path, _doubt_seed_chunks())
    try:
        llm = FakeLLM(handler=scoring_handler(_doubt_scores()))
        critic = SarvamCritic(llm)
        solver = DoubtSolver(HybridRetriever(idx), critic=critic)
        result = solver.solve("explain the light reaction of photosynthesis")

        reflection = result["reflection"]
        assert reflection["used_critic"] is True
        assert reflection["retrieved"] is True
        assert reflection["best_score"] == 2.5  # docC: 1.0 + 1.0 + 0.5*1.0
        assert reflection["weights"] == {"relevance": 1.0, "support": 1.0, "utility": 0.5}

        paths = reflection["paths"]
        assert [p["document_id"] for p in paths] == ["docC", "docB", "docA"]
        assert [p["score"] for p in paths] == [2.5, 1.5, -0.5]
        assert (paths[0]["relevance"], paths[0]["support"], paths[0]["utility"]) == (1.0, 1.0, 1.0)

        assert result["answer"].startswith("Based on the corpus, the most relevant passage is:")
        assert "[docC p.7]" in result["answer"]
        assert result["citations"][0]["document_id"] == "docC"
        assert len(result["citations"]) == 3
        assert result["evidence"][0] == {"document_id": "docC", "page": 7}
        assert len(result["evidence"]) == 3
        # 1 retrieve-decision call + 3 per-path score calls
        assert llm.call_count == 4
    finally:
        idx.close()


def test_solve_with_critic_respects_custom_weights(tmp_path):
    idx = build_index(tmp_path, _doubt_seed_chunks())
    try:
        llm = FakeLLM(handler=scoring_handler(_doubt_scores()))
        critic = SarvamCritic(llm, w_rel=2.0, w_sup=3.0, w_use=4.0)
        solver = DoubtSolver(HybridRetriever(idx), critic=critic)
        result = solver.solve("explain the light reaction of photosynthesis")

        reflection = result["reflection"]
        assert reflection["weights"] == {"relevance": 2.0, "support": 3.0, "utility": 4.0}
        # docC: 2*1 + 3*1 + 4*1 = 9.0; docB: 2*1 + 3*0.5 = 3.5; docA: 4*(-1) = -4.0
        assert reflection["best_score"] == 9.0
        paths = reflection["paths"]
        assert [p["document_id"] for p in paths] == ["docC", "docB", "docA"]
        assert [p["score"] for p in paths] == [9.0, 3.5, -4.0]
    finally:
        idx.close()


def test_solve_with_critic_unavailable_falls_through_to_deterministic(retriever):
    llm = FakeLLM(available=False)
    solver = DoubtSolver(retriever, critic=SarvamCritic(llm))
    result = solver.solve("photosynthesis light reaction")
    assert result["reflection"] == {"used_critic": False}
    assert result["answer"].startswith("Based on the corpus")
    assert llm.call_count == 0


def test_solve_with_critic_retrieve_true_paths_empty_when_no_hits(empty_retriever):
    llm = FakeLLM(handler=scoring_handler({}, retrieve=True))
    solver = DoubtSolver(empty_retriever, critic=SarvamCritic(llm))
    result = solver.solve("photosynthesis")
    assert result["reflection"]["paths"] == []
    assert result["answer"] == "No evidence found in the corpus for this doubt."


# --------------------------------------------------------------------------- #
# ExaminerScorer
# --------------------------------------------------------------------------- #

def test_examiner_scorer_finds_marking_scheme(retriever):
    scorer = ExaminerScorer(retriever)
    result = scorer.score("State Newton's second law", "F = ma", marks_available=2.0)
    assert result["agent"] == "examiner-scorer"
    assert result["score"] == {"earned": None, "available": 2.0, "scheme_found": True}
    assert result["scheme_citations"]
    assert "marking" in result["scheme_citations"][0]["document_id"].lower()
    assert result["note"] == "v0.1 heuristic scorer; LLM rubric application lands in Phase 4."


def test_examiner_scorer_falls_back_to_all_hits(tmp_path):
    idx = build_index(tmp_path, [
        make_chunk("n1", "XII_Physics_QP_2025", 3, "Section B",
                   "State Newton's second law of motion. (2 marks)"),
        make_chunk("n2", "XII_Physics_Textbook_2025", 10, "Laws of Motion",
                   "Newton's second law states that F equals m times a."),
    ])
    try:
        scorer = ExaminerScorer(HybridRetriever(idx))
        result = scorer.score("State Newton's second law", "F = ma")
        assert result["score"]["scheme_found"] is True
        # no chunk mentions "marking" -> scheme falls back to the full hit list
        assert len(result["scheme_citations"]) == 2
        docs = {c["document_id"] for c in result["scheme_citations"]}
        assert docs == {"XII_Physics_QP_2025", "XII_Physics_Textbook_2025"}
    finally:
        idx.close()


def test_examiner_scorer_no_hits_scheme_not_found(empty_retriever):
    scorer = ExaminerScorer(empty_retriever)
    result = scorer.score("Some weird question", "answer", marks_available=5.0)
    assert result["score"] == {"earned": None, "available": 5.0, "scheme_found": False}
    assert result["scheme_citations"] == []


# --------------------------------------------------------------------------- #
# PaperAnalyst
# --------------------------------------------------------------------------- #

def _paper_chunks():
    return [
        make_chunk("p1", "QP_2025", 1, "Section A",
                   "Question paper 2025 Section A. What is photosynthesis? (2 marks)"),
        make_chunk("p2", "QP_2025", 2, "Section A",
                   "Question paper 2025 Section A. State Newton's second law. (2 marks)"),
        make_chunk("p3", "QP_2025", 3, "Section B",
                   "Question paper 2025 Section B. Explain solar cell. (3 marks)"),
        make_chunk("p4", "QP_2025", 4, "",
                   "Question paper 2025. General instructions: answer all questions."),
        make_chunk("p5", "QP_2025", 5, "Section C",
                   "Question paper 2025 Section C. Long answer example. (5 marks)"),
    ]


def test_paper_analyst_groups_sections_by_heading(tmp_path):
    idx = build_index(tmp_path, _paper_chunks())
    try:
        analyst = PaperAnalyst(HybridRetriever(idx))
        result = analyst.analyze("2025")
        assert result["agent"] == "paper-analyst"
        assert result["paper_id"] == "2025"
        assert result["sections_found"] == ["Section A", "Section B", "Section C"]
        assert len(result["top_chunks"]) == 5
        assert len(result["top_chunks"]) <= 8
        for c in result["top_chunks"]:
            assert set(c) == {"document_id", "page", "heading"}
    finally:
        idx.close()


def test_paper_analyst_top_chunks_capped_at_eight(tmp_path):
    chunks = [make_chunk(f"q{i}", "QP_2025", i + 1, f"Section {chr(65 + i)}" if i < 8 else "",
                         f"Question paper 2025 {i} marks example text number {i}")
              for i in range(10)]
    idx = build_index(tmp_path, chunks)
    try:
        analyst = PaperAnalyst(HybridRetriever(idx))
        result = analyst.analyze("2025")
        assert len(result["top_chunks"]) == 8
    finally:
        idx.close()


# --------------------------------------------------------------------------- #
# private helpers
# --------------------------------------------------------------------------- #

def test_make_evidence_builds_valid_provenance():
    agent = Agent(retriever=None)  # _make_evidence never touches the retriever
    ev = agent._make_evidence([
        {"document_id": "doc1", "page": 3, "heading": "h", "text": "x"},
        {"document_id": "doc2", "page": 5, "heading": "h", "text": "y"},
        {"document_id": "doc3", "heading": "h", "text": "z"},
    ])
    assert len(ev.items) == 3
    for p in ev.items:
        # provenance requires a real Confidence (was passing None -> pydantic violation)
        assert p.confidence is not None
        assert p.confidence.method == p.method
        assert 0.0 <= p.confidence.score <= 1.0
    assert ev.items[0].source.document_id == "doc1"
    assert ev.items[0].source.page == 3
    assert ev.items[2].source.document_id == "doc3"


def test_make_evidence_caps_at_five():
    agent = Agent(retriever=None)
    hits = [{"document_id": f"doc{i}", "page": i + 1, "heading": "h", "text": "x"}
            for i in range(8)]
    ev = agent._make_evidence(hits)
    assert len(ev.items) == 5


def test_answer_from_hits_empty_message():
    assert _answer_from_hits([]) == NO_EVIDENCE_MSG


def test_answer_from_hits_formats_first_three_only():
    hits = [{"document_id": f"doc{i}", "page": i, "heading": "h", "score": 1.0,
             "text": f"text {i}"} for i in range(4)]
    ans = _answer_from_hits(hits)
    assert ans.startswith("Based on the corpus, the following passages are most relevant to your doubt:")
    for i in range(3):
        assert f"[{i + 1}] (doc{i} p.{i}) text {i}" in ans
    assert "doc3" not in ans  # 4th hit is never referenced


def test_answer_from_hits_page_fallback_question_mark():
    ans = _answer_from_hits([{"document_id": "doc1", "text": "no page here"}])
    assert "(doc1 p.?)" in ans


def test_cite_full_shape():
    assert _cite({"document_id": "d1", "page": 3, "heading": "Sec"}) == {
        "document_id": "d1", "page": 3, "heading": "Sec",
    }


def test_cite_defaults_missing_page_and_heading():
    assert _cite({"document_id": "d1"}) == {"document_id": "d1", "page": 1, "heading": ""}