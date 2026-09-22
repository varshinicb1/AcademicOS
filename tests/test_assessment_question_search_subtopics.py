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
from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.assessment import routes as assessment_routes
from academicos.assessment.pool import PoolQuestion, QuestionPool
from academicos.assessment.schemas import QuestionSearchParams
from academicos.assessment.users import User
from academicos.config import Config
from academicos.curriculum.store import CurriculumStore
from academicos.models.academic import Question

from test_curriculum_store import _seed_subtopic


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


def _user(school_id: str) -> User:
    return User(id=f"user_{school_id}", school_id=school_id, name="Teacher",
                email=f"t@{school_id}.example", role="teacher", created_at="2026-09-21T00:00:00Z")


def test_another_schools_subtopic_is_refused_not_resolved(monkeypatch, cfg, curriculum_store):
    """This route, not curriculum/routes.py's questions/by-subtopics, is the
    subtopic filter the web client actually sends (assessment_create_page.dart
    -> QuestionSearchParams.subtopicIds). Until 2026-09-21 it resolved any
    school's subtopic id: school_2 holding school_1's id got back the question
    ids school_1 had tagged to it. It now refuses a foreign id with the same
    403 by-subtopics gives, even mixed in with the caller's own ids, and
    before the pool is loaded."""
    board = curriculum_store.create_board(name="CBSE", code="CBSE")
    theirs = _seed_subtopic(curriculum_store, board.id, "school_1")
    mine = _seed_subtopic(curriculum_store, board.id, "school_2")
    curriculum_store.link_question_to_subtopic(question_id="q1", subtopic_id=theirs)
    curriculum_store.link_question_to_subtopic(question_id="q2", subtopic_id=mine)
    pool = QuestionPool(questions=[_pool_question("q1", "One."), _pool_question("q2", "Two.")])
    monkeypatch.setattr(assessment_routes, "_require", lambda: (cfg, None))
    monkeypatch.setattr(assessment_routes, "get_pool", lambda cfg, subject, grade, llm=None: pool)
    monkeypatch.setattr(
        "academicos.curriculum.store.get_curriculum_store", lambda data_root: curriculum_store)

    for ids in ([theirs], [mine, theirs]):
        with pytest.raises(HTTPException) as refused:
            assessment_routes.search_questions(
                QuestionSearchParams(subject="Science", grade=10, subtopic_ids=ids),
                current=_user("school_2"))
        assert refused.value.status_code == 403

    own = assessment_routes.search_questions(
        QuestionSearchParams(subject="Science", grade=10, subtopic_ids=[mine]),
        current=_user("school_2"))
    assert [q.id for q in own] == ["q2"]
    owner = assessment_routes.search_questions(
        QuestionSearchParams(subject="Science", grade=10, subtopic_ids=[theirs]),
        current=_user("school_1"))
    assert [q.id for q in owner] == ["q1"]


def test_unknown_subtopic_id_is_ignored_not_refused(monkeypatch, cfg, curriculum_store):
    """A subtopic force-deleted after the picker loaded resolves to no school.
    It is not another school's row, so it is not a 403: its question links
    went with it and it simply matches nothing, next to the caller's own ids."""
    board = curriculum_store.create_board(name="CBSE", code="CBSE")
    mine = _seed_subtopic(curriculum_store, board.id, "school_2")
    curriculum_store.link_question_to_subtopic(question_id="q2", subtopic_id=mine)
    pool = QuestionPool(questions=[_pool_question("q1", "One."), _pool_question("q2", "Two.")])
    monkeypatch.setattr(assessment_routes, "_require", lambda: (cfg, None))
    monkeypatch.setattr(assessment_routes, "get_pool", lambda cfg, subject, grade, llm=None: pool)
    monkeypatch.setattr(
        "academicos.curriculum.store.get_curriculum_store", lambda data_root: curriculum_store)

    result = assessment_routes.search_questions(
        QuestionSearchParams(subject="Science", grade=10, subtopic_ids=[mine, "st_deleted"]),
        current=_user("school_2"))
    assert [q.id for q in result] == ["q2"]
