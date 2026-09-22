"""PARAKH & CBSE assessment standards test suite:
- Student level tiers (Foundation, Standard, Advanced)
- CBSE Competency-Based Question (CBQ) >= 50% quota
- PARAKH intra-chapter internal choice ("OR") pairing
- Parallel equivalent sets (Set A, Set B, Set C) invariance and cheating-resistant permutations
- Quick Examzo-style generation and ID-based curated compilation
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.api.main import app
from academicos.assessment.paper import generate_paper, generate_paper_sets
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
from academicos.assessment.selection import is_competency_question, optimize


def _scheme(marks: int, ans: str = "model answer") -> AnswerSchemeSchema:
    return AnswerSchemeSchema(
        total_marks=marks,
        marking_points=[
            MarkingPointSchema(id="mp1", description="Step 1", marks=marks // 2 or 1, keyword="k1"),
        ],
        model_answer=ans,
        metadata={},
    )


def _q(
    qid: str,
    marks: int,
    chapters: list[str],
    difficulty: str = "medium",
    bloom: str = "understand",
    qtype: str = "short_answer",
    stem: str | None = None,
    quality: float = 0.7,
    **overrides,
) -> QuestionSchema:
    now = datetime.now(timezone.utc)
    return QuestionSchema(
        id=qid,
        question_bank_id="bank1",
        subject="Science",
        grade=10,
        chapter_ids=chapters,
        competency_ids=[],
        bloom_level=bloom,
        difficulty=difficulty,
        type=qtype,
        stem=stem or f"Question stem for {qid}",
        parts=[],
        answer_scheme=_scheme(marks, f"Answer for {qid}"),
        estimated_time_minutes=2,
        marks=marks,
        language="en",
        source="ncert_textbook",
        quality_score=quality,
        tags=[],
        created_at=now,
        updated_at=now,
        **overrides,
    )


def _section(
    label: str,
    marks_per_question: int,
    question_count: int,
    has_choice: bool = False,
) -> SectionBlueprint:
    return SectionBlueprint(
        id=f"sec_{label.lower()}",
        label=label,
        name=f"Section {label}",
        marks_per_question=marks_per_question,
        question_count=question_count,
        total_marks=marks_per_question * question_count,
        has_internal_choice=has_choice,
        internal_choice_count=1 if has_choice else 0,
    )


def _blueprint(
    total_marks: int,
    sections: list[SectionBlueprint],
    tier: str = "standard",
    competency_pct: float = 0.50,
) -> Blueprint:
    return Blueprint(
        total_marks=total_marks,
        duration_minutes=180,
        difficulty=DifficultyDistribution(easy=0.3, medium=0.4, hard=0.3),
        bloom=BloomDistribution(
            remember=0.2, understand=0.2, apply=0.2,
            analyze=0.2, evaluate=0.1, create=0.1
        ),
        chapter_weights=ChapterWeights(),
        competency_weights=CompetencyWeights(),
        sections=sections,
        tier=tier,
        competency_percentage=competency_pct,
    )


def test_tier_foundation_prioritizes_easy():
    """Foundation/Remedial tier prioritizes easy questions over hard."""
    sec = _section("A", marks_per_question=1, question_count=1)
    bp = _blueprint(total_marks=1, sections=[sec], tier="foundation")
    candidates = [
        _q("hard_q", 1, ["ch1"], difficulty="hard", quality=0.7),
        _q("easy_q", 1, ["ch1"], difficulty="easy", quality=0.7),
    ]
    res = optimize(candidates, bp)
    assert res.selected_questions[0].id == "easy_q"


def test_tier_advanced_prioritizes_hard():
    """Advanced/HOTS tier prioritizes hard questions and higher-order thinking."""
    sec = _section("A", marks_per_question=1, question_count=1)
    bp = _blueprint(total_marks=1, sections=[sec], tier="advanced")
    candidates = [
        _q("easy_q", 1, ["ch1"], difficulty="easy", quality=0.7),
        _q("hard_q", 1, ["ch1"], difficulty="hard", bloom="evaluate", quality=0.7),
    ]
    res = optimize(candidates, bp)
    assert res.selected_questions[0].id == "hard_q"


def test_cbse_competency_quota_boost():
    """Competency-based questions receive priority to satisfy the 50% CBSE mandate."""
    sec = _section("C", marks_per_question=3, question_count=1)
    bp = _blueprint(total_marks=3, sections=[sec], tier="standard", competency_pct=0.50)
    candidates = [
        _q("rote_q", 3, ["ch1"], bloom="remember", qtype="short_answer", quality=0.75),
        _q("cbq", 3, ["ch1"], bloom="apply", qtype="competency_based", quality=0.70),
    ]
    res = optimize(candidates, bp)
    assert res.selected_questions[0].id == "cbq"
    assert is_competency_question(res.selected_questions[0])
    assert res.optimization_metrics["competencyPercentage"] == 1.0


def test_parakh_intra_chapter_internal_choice_pairing():
    """PARAKH standard: Section with internal choice pairs an alternative question from the same chapter."""
    sec = _section("D", marks_per_question=5, question_count=1, has_choice=True)
    bp = _blueprint(total_marks=5, sections=[sec])
    candidates = [
        _q("primary_q", 5, ["ch_electricity"], quality=0.9),
        _q("diff_chap_q", 5, ["ch_acids_bases"], quality=0.7),
        _q("same_chap_alt", 5, ["ch_electricity"], quality=0.6),
    ]
    res = optimize(candidates, bp)
    assert len(res.selected_questions) == 1
    selected = res.selected_questions[0]
    assert selected.id == "primary_q"
    assert selected.metadata.get("internal_choice_id") == "same_chap_alt"
    assert selected.metadata.get("internal_choice_stem") == "Question stem for same_chap_alt"


def test_parallel_sets_invariance_and_swapping():
    """Multi-set generation produces Set A, Set B, Set C with invariant marks and duration,

    rotated MCQs, and swapped primary/OR choices on alternate sets.
    """
    sec_a = _section("A", marks_per_question=1, question_count=3)
    sec_d = _section("D", marks_per_question=5, question_count=1, has_choice=True)
    bp = _blueprint(total_marks=8, sections=[sec_a, sec_d])

    q_mcqs = [_q(f"mcq_{i}", 1, ["ch1"]) for i in range(1, 4)]
    q_long = _q("long_primary", 5, ["ch2"])
    q_long.metadata["internal_choice_id"] = "long_choice"
    q_long.metadata["internal_choice_stem"] = "Choice stem"
    q_long.metadata["internal_choice_scheme"] = "Choice answer"

    questions = q_mcqs + [q_long]

    paper = generate_paper_sets(
        paper_id="paper_multi_test",
        assessment_id="asm_multi_test",
        assessment_title="Class X Science",
        subject="Science",
        grade=10,
        blueprint=bp,
        selected_questions=questions,
        set_count=2,
    )

    assert paper.set_label == "A"
    assert len(paper.sets) == 2

    set_a = paper.sets[0]
    set_b = paper.sets[1]

    # Invariance check
    assert set_a.metadata.total_marks == set_b.metadata.total_marks == 8
    assert set_a.metadata.duration_minutes == set_b.metadata.duration_minutes == 180

    # MCQs rotated
    set_a_mcqs = [q.question_id for q in set_a.sections[0].questions]
    set_b_mcqs = [q.question_id for q in set_b.sections[0].questions]
    assert set_a_mcqs != set_b_mcqs

    # Long answer: Set A has long_primary with OR Choice, Set B swaps them
    set_a_sec_d = set_a.sections[1].questions[0]
    set_b_sec_d = set_b.sections[1].questions[0]
    assert set_a_sec_d.question_id == "long_primary"
    assert set_a_sec_d.internal_choice_question_id == "long_choice"
    assert set_b_sec_d.question_id == "long_choice"
    assert set_b_sec_d.internal_choice_question_id == "long_primary"


def _make_pool():
    from academicos.assessment.pool import PoolQuestion, QuestionPool
    from academicos.models.academic import Question

    questions = []
    # 20 1-mark MCQs
    for i in range(1, 21):
        q = Question(
            canonical_id=f"syn_q_{i}",
            title=f"Sample question {i}?",
            source_text=f"Sample question {i}?\n(a) Opt A\n(b) Opt B\n(c) Opt C\n(d) Opt D",
            marks=1.0,
        )
        questions.append(PoolQuestion(
            question=q, subject="Science", grade="X", academic_year="2024",
            chapter_id="ch_chemical_reactions", chapter_name="Chemical Reactions", chapter_confidence=0.9,
            text_hash=f"hash_{i}",
        ))
    # 10 2-mark questions
    for i in range(21, 31):
        q = Question(
            canonical_id=f"syn_q_{i}",
            title=f"Two mark question {i}?",
            source_text=f"Two mark question {i}?",
            marks=2.0,
        )
        questions.append(PoolQuestion(
            question=q, subject="Science", grade="X", academic_year="2024",
            chapter_id="ch_chemical_reactions", chapter_name="Chemical Reactions", chapter_confidence=0.9,
            text_hash=f"hash_{i}",
        ))
    # 10 3-mark questions
    for i in range(31, 41):
        q = Question(
            canonical_id=f"syn_q_{i}",
            title=f"Three mark question {i}?",
            source_text=f"Three mark question {i}?",
            marks=3.0,
        )
        questions.append(PoolQuestion(
            question=q, subject="Science", grade="X", academic_year="2024",
            chapter_id="ch_chemical_reactions", chapter_name="Chemical Reactions", chapter_confidence=0.9,
            text_hash=f"hash_{i}",
        ))
    # 5 5-mark questions
    for i in range(41, 46):
        q = Question(
            canonical_id=f"syn_q_{i}",
            title=f"Five mark question {i}?",
            source_text=f"Five mark question {i}?",
            marks=5.0,
        )
        questions.append(PoolQuestion(
            question=q, subject="Science", grade="X", academic_year="2024",
            chapter_id="ch_chemical_reactions", chapter_name="Chemical Reactions", chapter_confidence=0.9,
            text_hash=f"hash_{i}",
        ))
    # 4 4-mark case studies
    for i in range(46, 50):
        q = Question(
            canonical_id=f"syn_q_{i}",
            title=f"Case study question {i}?",
            source_text=f"Case study question {i}?",
            marks=4.0,
        )
        questions.append(PoolQuestion(
            question=q, subject="Science", grade="X", academic_year="2024",
            chapter_id="ch_chemical_reactions", chapter_name="Chemical Reactions", chapter_confidence=0.9,
            text_hash=f"hash_{i}",
        ))
    return QuestionPool(questions=questions)


def test_quick_generate_api_endpoint(tmp_path, monkeypatch):
    """POST /api/v1/papers/quick-generate generates a valid paper in 1 click."""
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr("academicos.assessment.routes.get_pool", lambda cfg, subject, grade, llm=None: _make_pool())
    with TestClient(app) as client:
        # Register user
        reg_resp = client.post(
            "/api/v1/auth/register",
            json={
                "id": "u1",
                "email": "t1@school.org",
                "name": "Teacher",
                "schoolId": "school_1",
                "role": "teacher",
                "password": "correct horse battery",
            },
        )
        assert reg_resp.status_code == 200, reg_resp.text
        token = reg_resp.json()["token"]
        auth = {"Authorization": f"Bearer {token}"}

        resp = client.post(
            "/api/v1/papers/quick-generate",
            json={
                "subject": "Science",
                "grade": 10,
                "totalMarks": 25,
                "tier": "standard",
                "examType": "class_test",
                "setCount": 2,
            },
            headers=auth,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["setLabel"] == "A"
        assert len(data["sets"]) == 2
        assert data["metadata"]["totalMarks"] == 25


def test_generate_from_ids_api_endpoint(tmp_path, monkeypatch):
    """POST /api/v1/papers/generate-from-ids compiles specific question IDs."""
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr("academicos.assessment.routes.get_pool", lambda cfg, subject, grade, llm=None: _make_pool())
    with TestClient(app) as client:
        reg_resp = client.post(
            "/api/v1/auth/register",
            json={
                "id": "u2",
                "email": "t2@school.org",
                "name": "Teacher 2",
                "schoolId": "school_1",
                "role": "teacher",
                "password": "correct horse battery",
            },
        )
        assert reg_resp.status_code == 200, reg_resp.text
        token = reg_resp.json()["token"]
        auth = {"Authorization": f"Bearer {token}"}

        # Search for 2 questions from the pool
        search_res = client.post(
            "/api/v1/questions/search",
            json={"subject": "Science", "grade": 10, "limit": 2},
            headers=auth,
        )
        assert search_res.status_code == 200
        items = search_res.json()
        assert len(items) >= 2
        qids = [q["id"] for q in items[:2]]

        resp = client.post(
            "/api/v1/papers/generate-from-ids",
            json={
                "title": "Custom Test",
                "subject": "Science",
                "grade": 10,
                "questionIds": qids,
            },
            headers=auth,
        )
        assert resp.status_code == 200, resp.text
        paper = resp.json()
        all_qids = [q["questionId"] for sec in paper["sections"] for q in sec["questions"]]
        for qid in qids:
            assert qid in all_qids

        # Test answer-key export
        exp_resp = client.post(
            f"/api/v1/papers/{paper['id']}/export/answer-key",
            headers=auth,
        )
        assert exp_resp.status_code == 200, exp_resp.text
        assert "url" in exp_resp.json()

        file_resp = client.get(
            f"/api/v1/papers/{paper['id']}/file?format=answer-key",
            headers=auth,
        )
        assert file_resp.status_code == 200
        assert file_resp.headers["content-type"] == "application/pdf"
        assert len(file_resp.content) > 100


def test_baked_in_question_bank_loads_when_parse_dir_empty(tmp_path):
    """build_pool loads questions from baked-in questions.json when no parse dump exists.

    Asked for Science X: since the merge serves only board records with a
    verified key, Physics XII has 17 served questions (16 through the web
    gates), below this test's floor of 50; Science X, which also carries CBE
    and NCERT Exemplar records, has 506 (500 through the gates).
    """
    from academicos.config import Config
    from academicos.assessment.pool import build_pool

    cfg = Config(data_root=tmp_path)
    cfg._load_baked_questions = True
    pool = build_pool(cfg, subject="Science", grade="X")
    assert len(pool.questions) >= 50
    assert any(q.subject == "Science" for q in pool.questions)


def test_generate_paper_copies_each_questions_type():
    """The PDF grids options only for an objective type; an empty type is read
    as a legacy paper and grids any (a)-(d). If generate_paper stopped copying
    q.type, a descriptive question's sub-parts would print as options again."""
    sec_a = _section("A", marks_per_question=1, question_count=2)
    sec_b = _section("B", marks_per_question=4, question_count=1)
    questions = [
        _q("mcq_q", 1, ["ch1"], qtype="mcq"),
        _q("ar_q", 1, ["ch1"], qtype="assertion_reason"),
        _q("long_q", 4, ["ch2"], qtype="long_answer",
           stem="Two brothers share money. (a) Find each share. (b) Explain."),
    ]
    paper = generate_paper(
        paper_id="paper_types", assessment_id="asm_types",
        assessment_title="Class X Science", subject="Science", grade=10,
        blueprint=_blueprint(total_marks=6, sections=[sec_a, sec_b]),
        selected_questions=questions,
    )
    types = {gq.question_id: gq.type for s in paper.sections for gq in s.questions}
    assert types == {"mcq_q": "mcq", "ar_q": "assertion_reason", "long_q": "long_answer"}
