"""Tests for GET /api/v1/curriculum/export -- the "easy transfer of school
data" feature. No such bulk export existed anywhere in the backend before
this pass (confirmed: the only prior "export" was a single generated
paper's PDF, and the Flutter app's "Backup & Restore" button is an
unscoped single-device Hive dump with no restore implementation at all).
"""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from academicos.api.main import app
from academicos.assessment import auth_routes
from academicos.assessment import routes as assessment_routes
from academicos.assessment import pillar_routes
from academicos.assessment.schemas import (
    Assessment, BloomDistribution, Blueprint, ChapterWeights, CompetencyWeights,
    DifficultyDistribution,
)
from academicos.assessment.store import AssessmentStore
from academicos.assessment.school_templates import TemplateStore
from academicos.assessment.users import UserStore
from academicos.curriculum.store import CurriculumStore
from academicos.curriculum import routes as curriculum_routes


def _blueprint() -> Blueprint:
    return Blueprint(
        total_marks=30, duration_minutes=60,
        difficulty=DifficultyDistribution(easy=0.3, medium=0.5, hard=0.2),
        bloom=BloomDistribution(remember=0.2, understand=0.25, apply=0.3, analyze=0.15,
                                evaluate=0.05, create=0.05),
        chapter_weights=ChapterWeights(),
        competency_weights=CompetencyWeights(),
    )


@pytest.fixture
def test_setup(tmp_path: Path):
    store = CurriculumStore(tmp_path / "curriculum.db")
    user_store = UserStore(tmp_path / "users.db", principal_bootstrap_key="test_bootstrap_key")
    assessment_store = AssessmentStore(tmp_path / "assessments.db")
    template_store = TemplateStore(tmp_path / "templates.db")

    curriculum_routes._store = store
    curriculum_routes._cfg = None
    auth_routes._users = user_store
    assessment_routes._store = assessment_store
    pillar_routes._templates = template_store

    school_id = "school_export_test"
    other_school_id = "school_other"
    principal = user_store.register(
        school_id=school_id, name="Export Principal", email="export.principal@test.com",
        password="pass", principal_key="test_bootstrap_key",
    )
    teacher = user_store.register(
        school_id=school_id, name="Export Teacher", email="export.teacher@test.com",
        password="pass", requested_role="teacher",
    )
    # A different school's data must never appear in this school's export.
    other_principal = user_store.register(
        school_id=other_school_id, name="Other Principal", email="other.principal@test.com",
        password="pass", principal_key="test_bootstrap_key",
    )
    p_token = user_store.create_session(principal.id)

    ay = store.create_academic_year(
        school_id=school_id, label="2026-27", start_date="2026-06-01", end_date="2027-04-30",
    )
    grade = store.create_grade(academic_year_id=ay.id, number=10)
    subject = store.create_subject(grade_id=grade.id, name="Science", code="SCI10")
    board = store.create_board(name="CBSE", code="CBSE")
    book = store.create_book(subject_id=subject.id, board_id=board.id, title="Science 10")
    unit = store.create_unit(book_id=book.id, canonical_id="u1", unit_no="1", name="Chemical Substances")
    chapter = store.create_chapter(canonical_id="ch1", unit_id=unit.id, name="Chemical Reactions")
    topic = store.create_topic(chapter_id=chapter.id, canonical_id="tp1", name="Types of Reactions")
    store.create_subtopic(topic_id=topic.id, canonical_id="st1", name="Combination Reactions")
    store.set_subject_period_allocation(
        school_id=school_id, academic_year_id=ay.id, subject="Science", periods_per_week=6,
    )

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    assessment_store.save(Assessment(
        id="a_export_1", school_id=school_id, teacher_id=teacher.id, title="Unit Test",
        subject="Science", grade=10, blueprint=_blueprint(), status="draft",
        created_at=now, updated_at=now,
    ))
    # Another school's assessment -- must be excluded from this export.
    assessment_store.save(Assessment(
        id="a_other_1", school_id=other_school_id, teacher_id=other_principal.id,
        title="Other School Paper", subject="Science", grade=10, blueprint=_blueprint(),
        status="draft", created_at=now, updated_at=now,
    ))

    return {
        "school_id": school_id, "other_school_id": other_school_id,
        "p_token": p_token, "teacher": teacher,
    }


def test_export_requires_authentication(test_setup):
    client = TestClient(app)
    r = client.get("/api/v1/curriculum/export")
    assert r.status_code == 401


def test_export_returns_full_school_bundle(test_setup):
    client = TestClient(app)
    r = client.get(
        "/api/v1/curriculum/export",
        headers={"Authorization": f"Bearer {test_setup['p_token']}"},
    )
    assert r.status_code == 200
    body = r.json()

    assert body["schema_version"] == 1
    assert body["school_id"] == test_setup["school_id"]

    curriculum = body["curriculum"]
    assert len(curriculum) == 1
    year = curriculum[0]
    assert year["label"] == "2026-27"
    assert len(year["subject_period_allocations"]) == 1
    grades = year["grades"]
    assert len(grades) == 1
    subjects = grades[0]["subjects"]
    assert subjects[0]["name"] == "Science"
    books = subjects[0]["books"]
    assert books[0]["title"] == "Science 10"
    units = books[0]["units"]
    assert units[0]["name"] == "Chemical Substances"
    chapters = units[0]["chapters"]
    assert chapters[0]["name"] == "Chemical Reactions"
    topics = chapters[0]["topics"]
    assert topics[0]["name"] == "Types of Reactions"
    subtopics = topics[0]["subtopics"]
    assert subtopics[0]["name"] == "Combination Reactions"

    assessments = body["assessments"]
    assert len(assessments) == 1
    assert assessments[0]["id"] == "a_export_1"

    assert "notes" in body and len(body["notes"]) >= 1


def test_export_never_leaks_another_schools_data(test_setup):
    client = TestClient(app)
    r = client.get(
        "/api/v1/curriculum/export",
        headers={"Authorization": f"Bearer {test_setup['p_token']}"},
    )
    body = r.json()
    assessment_ids = {a["id"] for a in body["assessments"]}
    assert "a_other_1" not in assessment_ids
    for u in body["users"]:
        assert u["school_id"] == test_setup["school_id"]


def test_export_users_exclude_password_fields(test_setup):
    client = TestClient(app)
    r = client.get(
        "/api/v1/curriculum/export",
        headers={"Authorization": f"Bearer {test_setup['p_token']}"},
    )
    body = r.json()
    assert len(body["users"]) == 2  # principal + teacher, both this school
    for u in body["users"]:
        assert "password_hash" not in u
        assert "password_salt" not in u
