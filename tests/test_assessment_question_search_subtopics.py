"""assessment/routes.py::search_questions's subtopic_ids filter -- the
gap-2 bridge: "generate a paper using selected subtopics" (curriculum/
routes.py's questions/by-subtopics) now reaches the real, existing
question-search -> paper-generation pipeline, not just a standalone query.

Calls search_questions() directly (not through HTTP) with a monkeypatched
get_pool returning a small synthetic pool -- pool.py's real corpus-reading
machinery is exercised elsewhere; this isolates the new filter itself.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.assessment import routes as assessment_routes
from academicos.assessment.pool import PoolQuestion, QuestionPool
from academicos.assessment.schemas import QuestionSearchParams
from academicos.config import Config
from academicos.curriculum.store import CurriculumStore
from academicos.models.academic import Question


def _pool_question(qid: str, stem: str) -> PoolQuestion:
    q = Question(canonical_id=qid, title=stem, source_text=stem, marks=2.0)
    return PoolQuestion(question=q, subject="Science", grade="X", academic_year=None,
                        chapter_id=None, chapter_name=None, chapter_confidence=0.0,
                        text_hash=qid)


@pytest.fixture
def curriculum_store(tmp_path):
    s = CurriculumStore(tmp_path / "curriculum.sqlite")
    yield s
    s.close()


@pytest.fixture
def cfg(tmp_path):
    return Config(data_root=tmp_path)


def test_subtopic_filter_returns_only_tagged_questions(monkeypatch, cfg, curriculum_store):
    pool = QuestionPool(questions=[
        _pool_question("q1", "Balance the equation."),
        _pool_question("q2", "Explain photosynthesis."),
        _pool_question("q3", "Untagged question."),
    ])
    monkeypatch.setattr(assessment_routes, "_require", lambda: (cfg, None))
    monkeypatch.setattr(assessment_routes, "get_pool", lambda cfg, subject, grade, llm=None: pool)
    monkeypatch.setattr(
        "academicos.curriculum.store.get_curriculum_store", lambda data_root: curriculum_store)

    curriculum_store.link_question_to_subtopic(question_id="q1", subtopic_id="st_balance")
    curriculum_store.link_question_to_subtopic(question_id="q2", subtopic_id="st_photosynthesis")

    result = assessment_routes.search_questions(
        QuestionSearchParams(subject="Science", grade=10, subtopic_ids=["st_balance"]))
    assert [q.id for q in result] == ["q1"]


def test_subtopic_filter_with_no_tags_excludes_everything(monkeypatch, cfg, curriculum_store):
    """A subtopic nothing is tagged to must return zero questions, not
    silently fall back to the unfiltered pool -- matches the same
    "no silent guess" property curriculum/routes.py's own
    questions/by-subtopics already has."""
    pool = QuestionPool(questions=[_pool_question("q1", "Any question.")])
    monkeypatch.setattr(assessment_routes, "_require", lambda: (cfg, None))
    monkeypatch.setattr(assessment_routes, "get_pool", lambda cfg, subject, grade, llm=None: pool)
    monkeypatch.setattr(
        "academicos.curriculum.store.get_curriculum_store", lambda data_root: curriculum_store)

    result = assessment_routes.search_questions(
        QuestionSearchParams(subject="Science", grade=10, subtopic_ids=["st_nothing_tagged"]))
    assert result == []


def test_no_subtopic_filter_is_a_no_op(monkeypatch, cfg, curriculum_store):
    """Omitting subtopic_ids entirely must not change existing behavior --
    the real regression this test guards against."""
    pool = QuestionPool(questions=[
        _pool_question("q1", "One."), _pool_question("q2", "Two."),
    ])
    monkeypatch.setattr(assessment_routes, "_require", lambda: (cfg, None))
    monkeypatch.setattr(assessment_routes, "get_pool", lambda cfg, subject, grade, llm=None: pool)

    result = assessment_routes.search_questions(QuestionSearchParams(subject="Science", grade=10))
    assert {q.id for q in result} == {"q1", "q2"}


def test_subtopic_filter_combines_with_other_filters(monkeypatch, cfg, curriculum_store):
    """subtopic_ids narrows the same candidate list bloom/difficulty/marks
    filters already narrow -- an AND, not a replacement."""
    high_marks = Question(canonical_id="q_hi", title="Hard one", marks=5.0)
    low_marks = Question(canonical_id="q_lo", title="Easy one", marks=1.0)
    pool = QuestionPool(questions=[
        PoolQuestion(question=high_marks, subject="Science", grade="X", academic_year=None,
                    chapter_id=None, chapter_name=None, chapter_confidence=0.0, text_hash="q_hi"),
        PoolQuestion(question=low_marks, subject="Science", grade="X", academic_year=None,
                    chapter_id=None, chapter_name=None, chapter_confidence=0.0, text_hash="q_lo"),
    ])
    monkeypatch.setattr(assessment_routes, "_require", lambda: (cfg, None))
    monkeypatch.setattr(assessment_routes, "get_pool", lambda cfg, subject, grade, llm=None: pool)
    monkeypatch.setattr(
        "academicos.curriculum.store.get_curriculum_store", lambda data_root: curriculum_store)

    curriculum_store.link_question_to_subtopic(question_id="q_hi", subtopic_id="st1")
    curriculum_store.link_question_to_subtopic(question_id="q_lo", subtopic_id="st1")

    result = assessment_routes.search_questions(
        QuestionSearchParams(subject="Science", grade=10, subtopic_ids=["st1"], min_marks=3))
    assert [q.id for q in result] == ["q_hi"]
