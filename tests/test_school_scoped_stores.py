"""Coverage for the school_id column added to PaperStore, PracticeStore, and
ScanSessionStore on 2026-09-17 -- the "largest outstanding correctness gap"
per docs/system-review.html (these three stores had no school scoping at
all, so the school-data export route couldn't cover them and cross-school
authorization had to be inferred entirely through a join on assessment_id).

All three tests run against local SQLite (no Supabase/Cloud SQL configured
in the test environment), matching every other store's test convention in
this suite.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from academicos.assessment.paper_store import PaperStore
from academicos.assessment.practice_store import PracticeStore
from academicos.assessment.remediation import PracticeItem, PracticeSet
from academicos.assessment.scan_session_store import ScanSessionStore
from academicos.assessment.schemas import (
    GeneratedPaper, GeneratedQuestionSchema, GeneratedSectionSchema,
    PaperMetadataSchema, QuestionSchema,
)


def _question(qid: str = "q1") -> QuestionSchema:
    return QuestionSchema(
        id=qid, question_bank_id="bank_1", subject="Mathematics", grade=10,
        chapter_ids=["ch1"], competency_ids=[], bloom_level="apply", difficulty="medium",
        type="short_answer", stem="2x=4, find x", stem_latex="", parts=[],
        answer_scheme={
            "total_marks": 2, "marking_points": [], "rubric_levels": [],
            "common_errors": [], "alternative_answers": [], "model_answer": "x=2",
            "model_answer_latex": "", "has_partial_credit": False, "metadata": {},
        },
        estimated_time_minutes=2, marks=2, language="en", source="teacher_created",
        quality_score=0.9, tags=[], created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z", metadata={},
    )


def _paper(paper_id: str = "paper_1", assessment_id: str = "a1") -> GeneratedPaper:
    gq = GeneratedQuestionSchema(
        question_id="q1", display_number=1, stem="2x=4, find x",
        marks=2, bloom_level="apply", difficulty="medium",
    )
    section = GeneratedSectionSchema(
        section_id="A", label="A", name="Sec A", total_marks=2, questions=[gq],
    )
    metadata = PaperMetadataSchema(
        assessment_title="T", subject="Mathematics", grade=10,
        total_marks=2, duration_minutes=30, generated_at=datetime.now(timezone.utc),
        generated_by="test", version="1.0",
    )
    return GeneratedPaper(
        id=paper_id, assessment_id=assessment_id, sections=[section],
        formatted_content="", formatted_content_latex="", answer_key={},
        metadata=metadata,
    )


# ---------------- PaperStore ----------------

def test_paper_store_school_id_roundtrip_and_list_by_school(tmp_path: Path) -> None:
    store = PaperStore(tmp_path / "papers.sqlite")
    store.save(_paper("p1"), school_id="school_1")
    store.save(_paper("p2"), school_id="school_2")
    store.save(_paper("p3"), school_id="school_1")

    school_1_papers = store.list_by_school("school_1")
    assert {p.id for p in school_1_papers} == {"p1", "p3"}
    assert store.list_by_school("school_2")[0].id == "p2"
    assert store.list_by_school("school_3") == []


def test_paper_store_school_id_defaults_to_none_when_omitted(tmp_path: Path) -> None:
    store = PaperStore(tmp_path / "papers.sqlite")
    store.save(_paper("p1"))  # no school_id -- must not raise
    assert store.get("p1") is not None
    assert store.list_by_school("school_1") == []


def test_paper_store_migrates_a_pre_existing_db_missing_school_id(tmp_path: Path) -> None:
    """A real pre-2026-09-17 papers.sqlite has rows with no school_id column
    at all -- _migrate() must ALTER TABLE rather than silently no-op like a
    bare CREATE TABLE IF NOT EXISTS would."""
    db_path = tmp_path / "papers.sqlite"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE papers (id TEXT PRIMARY KEY, paper_json TEXT NOT NULL, template_json TEXT)")
    conn.execute("INSERT INTO papers (id, paper_json) VALUES ('old_p', '{}')")
    conn.commit()
    conn.close()

    store = PaperStore(db_path)  # must not raise
    cols = {r["name"] for r in store.conn.execute("PRAGMA table_info(papers)").fetchall()}
    assert "school_id" in cols
    store.save(_paper("new_p"), school_id="school_1")
    assert store.list_by_school("school_1")[0].id == "new_p"


# ---------------- PracticeStore ----------------

def _practice_set(set_id: str = "ps1", student_id: str = "student_1") -> PracticeSet:
    return PracticeSet(
        id=set_id, student_id=student_id, concept_ids=["fractions"],
        items=[PracticeItem(question=_question(), concept_id="fractions")],
        answer_key={}, warnings=[],
    )


def test_practice_store_school_id_roundtrip_and_list_by_school(tmp_path: Path) -> None:
    store = PracticeStore(tmp_path / "practice.sqlite")
    store.save(_practice_set("ps1"), school_id="school_1")
    store.save(_practice_set("ps2"), school_id="school_2")

    school_1_sets = store.list_by_school("school_1")
    assert len(school_1_sets) == 1
    assert school_1_sets[0].id == "ps1"
    assert store.list_by_school("school_2")[0].id == "ps2"


def test_practice_store_migrates_a_pre_existing_db(tmp_path: Path) -> None:
    db_path = tmp_path / "practice.sqlite"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE practice_sets (id TEXT PRIMARY KEY, practice_json TEXT NOT NULL)")
    conn.commit()
    conn.close()

    store = PracticeStore(db_path)  # must not raise
    cols = {r["name"] for r in store.conn.execute("PRAGMA table_info(practice_sets)").fetchall()}
    assert "school_id" in cols


# ---------------- ScanSessionStore ----------------

def _make_session(session_id: str, assessment_id: str = "a1"):
    from academicos.assessment.mobile_scan import ScanSession
    return ScanSession(
        id=session_id, assessment_id=assessment_id, student_id="s1",
        student_name="Student", subject="Science", grade=10,
    )


def test_scan_session_store_school_id_roundtrip_and_list_by_school(tmp_path: Path) -> None:
    store = ScanSessionStore(tmp_path / "sessions.sqlite")
    store.save(_make_session("sc1"), school_id="school_1")
    store.save(_make_session("sc2"), school_id="school_2")

    school_1 = store.list_by_school("school_1")
    assert len(school_1) == 1
    assert school_1[0].id == "sc1"


def test_scan_session_store_resave_without_school_id_does_not_clobber(tmp_path: Path) -> None:
    """The real bug this guards against: mobile_scan.py's save_session() is
    called many times across one session's lifecycle, but only knows
    school_id from an in-process cache that a restart wipes mid-session.
    Without the COALESCE fix, resuming a session after exactly that restart
    would silently overwrite a real school_id with NULL on the next save."""
    store = ScanSessionStore(tmp_path / "sessions.sqlite")
    session = _make_session("sc1")
    store.save(session, school_id="school_1")

    # Simulate a later save (e.g. after a page upload) that doesn't know the
    # school_id anymore -- must NOT clobber the one already on record.
    store.save(session, school_id=None)

    assert store.list_by_school("school_1")[0].id == "sc1"


def test_scan_session_store_migrates_a_pre_existing_db(tmp_path: Path) -> None:
    db_path = tmp_path / "sessions.sqlite"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE scan_sessions (id TEXT PRIMARY KEY, session_json TEXT NOT NULL)")
    conn.commit()
    conn.close()

    store = ScanSessionStore(db_path)  # must not raise
    cols = {r["name"] for r in store.conn.execute("PRAGMA table_info(scan_sessions)").fetchall()}
    assert "school_id" in cols
    assert "assessment_id" in cols
