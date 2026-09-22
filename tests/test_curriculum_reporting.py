"""Tests for curriculum management reporting & variance (§17, §32)."""
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from academicos.api.main import app
from academicos.assessment import auth_routes
from academicos.assessment.users import UserStore
from academicos.curriculum.store import CurriculumStore
from academicos.curriculum import routes as curriculum_routes


@pytest.fixture
def test_setup(tmp_path: Path):
    db_path = tmp_path / "curriculum.db"
    store = CurriculumStore(db_path)
    user_db = tmp_path / "users.db"
    user_store = UserStore(user_db, principal_bootstrap_key="test_bootstrap_key")

    curriculum_routes._store = store
    auth_routes._users = user_store

    # Create school, academic year, grade, subject, book, unit, chapter, topic, subtopic
    school_id = "school_test"
    principal = user_store.register(
        school_id=school_id, name="Test Principal", email="principal@test.com",
        password="pass", principal_key="test_bootstrap_key"
    )
    # Teachers join by invite since 2026-09-21 (users.py); the principal
    # above issues it.
    teacher = user_store.register(
        invite_code=user_store.create_invite(
            school_id=school_id, role="teacher", created_by=principal.id).code,
        name="Test Teacher", email="teacher@test.com", password="pass",
    )
    p_token = user_store.create_session(principal.id)
    t_token = user_store.create_session(teacher.id)

    ay = store.create_academic_year(
        school_id=school_id, label="2026-27", start_date="2026-06-01", end_date="2027-04-30"
    )
    grade = store.create_grade(academic_year_id=ay.id, number=10)
    subject = store.create_subject(grade_id=grade.id, name="Science", code="SCI10")
    board = store.create_board(name="CBSE", code="CBSE")
    book = store.create_book(subject_id=subject.id, board_id=board.id, title="Science 10")
    unit = store.create_unit(book_id=book.id, canonical_id="u1", unit_no="1", name="Chemical Substances")
    chapter = store.create_chapter(canonical_id="ch1", unit_id=unit.id, name="Chemical Reactions")
    topic = store.create_topic(chapter_id=chapter.id, canonical_id="tp1", name="Types of Reactions")
    sub1 = store.create_subtopic(topic_id=topic.id, canonical_id="st1", name="Combination Reactions")
    sub2 = store.create_subtopic(topic_id=topic.id, canonical_id="st2", name="Decomposition Reactions")
    sub3 = store.create_subtopic(topic_id=topic.id, canonical_id="st3", name="Displacement Reactions")

    # Assign teacher to book
    store.assign_teacher(school_id=school_id, teacher_id=teacher.id, book_id=book.id)

    return {
        "store": store,
        "user_store": user_store,
        "school_id": school_id,
        "principal": principal,
        "teacher": teacher,
        "ay": ay,
        "book": book,
        "sub1": sub1,
        "sub2": sub2,
        "sub3": sub3,
        "p_token": p_token,
        "t_token": t_token,
    }


def test_coverage_and_delayed_reporting(test_setup):
    store: CurriculumStore = test_setup["store"]
    school_id = test_setup["school_id"]
    ay_id = test_setup["ay"].id
    book_id = test_setup["book"].id
    sub1 = test_setup["sub1"].id
    sub2 = test_setup["sub2"].id
    sub3 = test_setup["sub3"].id

    as_of = "2026-09-14"

    # 1. Empty report test
    rep = store.get_coverage_report(school_id=school_id, academic_year_id=ay_id, as_of_date=as_of)
    assert rep["total_lessons"] == 0
    assert rep["overall_coverage_pct"] == 0.0

    # 2. Add 4 lessons:
    # Lesson 1: in past (2026-09-10), completed
    l1 = store.create_scheduled_lesson(school_id=school_id, academic_year_id=ay_id, book_id=book_id,
                                       subtopic_id=sub1, date="2026-09-10", status="scheduled")
    store.mark_lesson(l1.id, status="completed", note="All done", completed_by=test_setup["teacher"].id)

    # Lesson 2: in past (2026-09-12), still scheduled (delayed!)
    l2 = store.create_scheduled_lesson(school_id=school_id, academic_year_id=ay_id, book_id=book_id,
                                       subtopic_id=sub2, date="2026-09-12", status="scheduled")

    # Lesson 3: today (2026-09-14), skipped
    l3 = store.create_scheduled_lesson(school_id=school_id, academic_year_id=ay_id, book_id=book_id,
                                       subtopic_id=sub3, date="2026-09-14", status="scheduled")
    store.mark_lesson(l3.id, status="skipped", note="School assembly", completed_by=test_setup["teacher"].id)

    # Lesson 4: in future (2026-09-20), scheduled
    l4 = store.create_scheduled_lesson(school_id=school_id, academic_year_id=ay_id, book_id=book_id,
                                       subtopic_id=sub1, date="2026-09-20", status="scheduled")

    rep = store.get_coverage_report(school_id=school_id, academic_year_id=ay_id, as_of_date=as_of)
    assert rep["total_lessons"] == 4
    assert rep["completed_lessons"] == 1
    assert rep["skipped_lessons"] == 1
    assert rep["planned_to_date"] == 3  # Sept 10, Sept 12, Sept 14
    assert rep["completed_to_date"] == 1
    assert rep["overall_coverage_pct"] == 25.0
    assert rep["overall_pace_pct"] == round(1 / 3 * 100, 2)
    assert rep["overall_variance"] == 1 - 3  # -2 (behind schedule by 2 lessons)

    assert len(rep["subjects"]) == 1
    subj = rep["subjects"][0]
    assert subj["subject_name"] == "Science"
    assert subj["variance"] == -2
    assert len(subj["chapters"]) == 1
    assert subj["chapters"][0]["total_lessons"] == 4
    assert subj["chapters"][0]["completed_lessons"] == 1

    # Check delayed topics
    delayed = store.get_delayed_topics(school_id=school_id, academic_year_id=ay_id, as_of_date=as_of)
    assert delayed["delayed_count"] == 1
    d_entry = delayed["delayed_lessons"][0]
    assert d_entry["lesson_id"] == l2.id
    assert d_entry["subtopic_name"] == "Decomposition Reactions"
    assert d_entry["days_overdue"] == 2  # Sept 14 - Sept 12


def test_reporting_api_endpoints(test_setup):
    client = TestClient(app)
    p_token = test_setup["p_token"]
    t_token = test_setup["t_token"]
    ay_id = test_setup["ay"].id
    headers_principal = {"Authorization": f"Bearer {p_token}"}
    headers_teacher = {"Authorization": f"Bearer {t_token}"}

    # Principal can view coverage
    res = client.get(f"/api/v1/curriculum/reporting/coverage?academic_year_id={ay_id}",
                     headers=headers_principal)
    assert res.status_code == 200
    data = res.json()
    assert data["academicYearId"] == ay_id

    # Teacher gets 403
    res_t = client.get(f"/api/v1/curriculum/reporting/coverage?academic_year_id={ay_id}",
                       headers=headers_teacher)
    assert res_t.status_code == 403

    # Delayed topics endpoint
    res_del = client.get(f"/api/v1/curriculum/reporting/delayed-topics?academic_year_id={ay_id}",
                         headers=headers_principal)
    assert res_del.status_code == 200
    data_del = res_del.json()
    assert "delayedLessons" in data_del
