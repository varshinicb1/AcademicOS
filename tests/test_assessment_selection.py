"""Question Optimizer (assessment/selection.py) — deterministic blueprint
balancing, difficulty/bloom gating, and the chapter-scoped fallback/backfill
rescue path. Pure functions, no API calls.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.assessment.schemas import (
    AnswerSchemeSchema,
    BloomDistribution,
    Blueprint,
    ChapterWeights,
    CompetencyWeights,
    DifficultyDistribution,
    MarkingPointSchema,
    QuestionSchema,
    SectionBlueprint,
)
from academicos.assessment.selection import optimize


def _scheme(marks: int) -> AnswerSchemeSchema:
    return AnswerSchemeSchema(
        total_marks=marks,
        marking_points=[MarkingPointSchema(id="mp1", description="correct", marks=marks,
                                           keyword="answer")],
        metadata={},
    )


def _q(qid: str, marks: int, chapters: list[str], difficulty: str = "easy",
        bloom: str = "remember", quality: float = 0.7, **overrides) -> QuestionSchema:
    now = datetime.now(timezone.utc)
    return QuestionSchema(
        id=qid, question_bank_id="bank1", subject="science", grade=10,
        chapter_ids=chapters, competency_ids=[], bloom_level=bloom, difficulty=difficulty,
        type="short_answer", stem=f"stem {qid}", parts=[], answer_scheme=_scheme(marks),
        estimated_time_minutes=2, marks=marks, language="en", source="teacher_created",
        quality_score=quality, tags=[], created_at=now, updated_at=now, **overrides,
    )


def _section(label: str, marks_per_question: int, question_count: int,
             difficulties: list[str] | None = None,
             bloom_levels: list[str] | None = None) -> SectionBlueprint:
    return SectionBlueprint(
        id=f"section-{label.lower()}", label=label, name=f"Section {label}",
        marks_per_question=marks_per_question, question_count=question_count,
        total_marks=marks_per_question * question_count,
        allowed_bloom_levels=bloom_levels or [],
        allowed_difficulties=difficulties or [],
    )


def _blueprint(total_marks: int, sections: list[SectionBlueprint]) -> Blueprint:
    return Blueprint(
        total_marks=total_marks, duration_minutes=180,
        difficulty=DifficultyDistribution(easy=0.3, medium=0.4, hard=0.3),
        bloom=BloomDistribution(remember=0.2, understand=0.2, apply=0.2,
                                analyze=0.2, evaluate=0.1, create=0.1),
        chapter_weights=ChapterWeights(), competency_weights=CompetencyWeights(),
        sections=sections,
    )


def test_selects_only_exact_marks_match():
    section = _section("B", marks_per_question=2, question_count=2)
    blueprint = _blueprint(total_marks=4, sections=[section])
    candidates = [
        _q("q1", 2, ["c1"]),
        _q("q2", 2, ["c2"]),
        _q("q3", 1, ["c1"]),   # wrong marks -> must not fit
        _q("q4", 3, ["c2"]),   # wrong marks -> must not fit
    ]
    result = optimize(candidates, blueprint)
    assert [q.id for q in result.selected_questions] == ["q1", "q2"]
    assert {q.id for q in result.rejected_questions} == {"q3", "q4"}


def test_difficulty_gate_respected():
    section = _section("B", marks_per_question=2, question_count=2,
                       difficulties=["hard"])
    blueprint = _blueprint(total_marks=4, sections=[section])
    candidates = [
        _q("q1", 2, ["c1"], difficulty="hard"),
        _q("q2", 2, ["c1"], difficulty="hard"),
        _q("q3", 2, ["c1"], difficulty="easy"),   # easy -> blocked
    ]
    result = optimize(candidates, blueprint)
    assert {q.id for q in result.selected_questions} == {"q1", "q2"}


def test_bloom_gate_respected():
    section = _section("A", marks_per_question=1, question_count=1,
                       bloom_levels=["analyze"])
    blueprint = _blueprint(total_marks=1, sections=[section])
    candidates = [
        _q("q1", 1, ["c1"], bloom="analyze"),
        _q("q2", 1, ["c1"], bloom="remember"),
    ]
    result = optimize(candidates, blueprint)
    assert [q.id for q in result.selected_questions] == ["q1"]


def test_quality_score_ranks_selection():
    section = _section("A", marks_per_question=1, question_count=1)
    blueprint = _blueprint(total_marks=1, sections=[section])
    candidates = [
        _q("good", 1, ["c1"], quality=0.9),
        _q("poor", 1, ["c1"], quality=0.4),
    ]
    result = optimize(candidates, blueprint)
    assert [q.id for q in result.selected_questions] == ["good"]


def test_chapter_weight_boosts_score():
    section = _section("A", marks_per_question=1, question_count=1)
    blueprint = _blueprint(
        total_marks=1, sections=[section],
    )
    blueprint = blueprint.model_copy(update={
        "chapter_weights": ChapterWeights(weights={"c2": 2.0}),
    })
    candidates = [
        _q("c1q", 1, ["c1"], quality=0.7),
        _q("c2q", 1, ["c2"], quality=0.7),
    ]
    result = optimize(candidates, blueprint)
    assert [q.id for q in result.selected_questions] == ["c2q"]


def test_repeated_chapter_penalised_for_coverage():
    section = _section("A", marks_per_question=1, question_count=2)
    blueprint = _blueprint(total_marks=2, sections=[section])
    candidates = [
        _q("same1", 1, ["c1"]),
        _q("same2", 1, ["c1"]),
        _q("other", 1, ["c2"], quality=0.9),
    ]
    result = optimize(candidates, blueprint)
    # highest quality picks other first, then c1 questions spread coverage
    assert result.selected_questions[0].id == "other"
    assert len(result.selected_questions) == 2


def test_fallback_backfills_unfillable_section():
    # Narrow chapter pick leaves only 1 of 3 one-mark questions in the primary
    # pool; the rescue path must borrow the shortfall from fallback_candidates
    # (unrestricted by chapter) and record both gaps.
    section = _section("A", marks_per_question=1, question_count=3)
    blueprint = _blueprint(total_marks=3, sections=[section])
    candidates = [
        _q("primary", 1, ["c1"]),
        _q("wrong_marks_2", 2, ["c1"]),
        _q("wrong_marks_3", 3, ["c1"]),
    ]
    fallback = [
        _q("fb1", 1, ["c9"]),
        _q("fb2", 1, ["c10"]),
        _q("fb_unused", 2, ["c10"]),
    ]
    result = optimize(candidates, blueprint, fallback_candidates=fallback)
    ids = {q.id for q in result.selected_questions}
    assert ids == {"primary", "fb1", "fb2"}
    assert all(q.marks == 1 for q in result.selected_questions)
    assert any("needs 3 questions" in g for g in result.gaps)
    assert any("filled 2 of the shortfall" in g for g in result.gaps)
    assert result.gaps  # fallback is a rescue, not silent
    assert result.optimization_metrics["questionCount"] == 3


def test_fallback_not_used_when_candidates_fill_section():
    section = _section("A", marks_per_question=1, question_count=2)
    blueprint = _blueprint(total_marks=2, sections=[section])
    candidates = [_q("a1", 1, ["c1"]), _q("a2", 1, ["c2"])]
    fallback = [_q("fb", 1, ["c9"])]
    result = optimize(candidates, blueprint, fallback_candidates=fallback)
    assert {q.id for q in result.selected_questions} == {"a1", "a2"}
    assert result.gaps == []
    # fallback questions are not candidates, so they never appear as rejected
    assert {q.id for q in result.rejected_questions} == set()


def test_no_fallback_leaves_gap_and_reports_marks_mismatch():
    section = _section("A", marks_per_question=1, question_count=3)
    blueprint = _blueprint(total_marks=3, sections=[section])
    candidates = [
        _q("only1", 1, ["c1"]),
        _q("w2", 2, ["c1"]),
        _q("w3", 3, ["c1"]),
    ]
    result = optimize(candidates, blueprint)  # no fallback pool at all
    assert [q.id for q in result.selected_questions] == ["only1"]
    assert any("needs 3 questions" in g for g in result.gaps)
    assert not any("filled" in g for g in result.gaps)
    assert any("Selected paper totals 1 marks" in w for w in result.warnings)


def test_fallback_pool_dedupes_candidate_ids():
    section = _section("A", marks_per_question=1, question_count=2)
    blueprint = _blueprint(total_marks=2, sections=[section])
    candidates = [_q("shared", 1, ["c1"])]
    fallback = [_q("shared", 1, ["c1"]), _q("extra", 1, ["c2"])]
    result = optimize(candidates, blueprint, fallback_candidates=fallback)
    ids = {q.id for q in result.selected_questions}
    assert ids == {"shared", "extra"}
    assert len(result.selected_questions) == 2
    assert "shared" not in {q.id for q in result.rejected_questions}


def test_single_chapter_concentration_warning():
    section = _section("A", marks_per_question=1, question_count=4)
    blueprint = _blueprint(total_marks=4, sections=[section])
    candidates = [_q(f"q{i}", 1, ["c1"]) for i in range(5)]
    result = optimize(candidates, blueprint)
    assert len(result.selected_questions) == 4
    assert any("single chapter" in w for w in result.warnings)


def test_optimization_metrics_shape():
    section = _section("A", marks_per_question=1, question_count=2)
    blueprint = _blueprint(total_marks=2, sections=[section])
    candidates = [_q("q1", 1, ["c1"], difficulty="easy", bloom="remember"),
                  _q("q2", 1, ["c1"], difficulty="medium", bloom="apply")]
    result = optimize(candidates, blueprint)
    m = result.optimization_metrics
    assert m["totalMarksSelected"] == 2
    assert m["questionCount"] == 2
    assert m["chapterCoverage"] == {"c1": 2}
    assert m["bloomDistribution"] == {"remember": 1, "apply": 1}
    assert m["difficultyDistribution"] == {"easy": 1, "medium": 1}


def test_empty_candidate_pool_graceful():
    section = _section("A", marks_per_question=1, question_count=2)
    blueprint = _blueprint(total_marks=2, sections=[section])
    result = optimize([], blueprint)
    assert result.selected_questions == []
    assert result.rejected_questions == []
    assert result.gaps