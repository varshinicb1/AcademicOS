"""The chapter a teacher is shown is the chapter a paper draws from.

Audit D24 (2026-09-26): the builder's chapter picker lists chapters and counts
from GET /catalog/{subject}/{grade}/chapters, which files each question by its
taxonomy tag first. Every filter that takes a
teacher's chosen chapters -- the template scope, quick-generate, the question
search, the parallel sets -- matched the record's own `chapterIds`. Across
classes 6-10 Mathematics and Science, 2,297 questions were filed under named
chapters and choosing those chapters reached 1,266. Mathematics 6 "Lines and
Angles" showed 16 questions and generating a paper from it returned 400 "no
question in the bank fits this template".

These run on the committed served bank, like tests/test_catalog_chapters.py.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.api.main import app  # noqa: E402
from academicos.assessment import chapter_filing, pillar_routes, pool as pool_module  # noqa: E402
from academicos.assessment.mapping import to_question_schema  # noqa: E402
from academicos.assessment.paper_templates import build_scope_filter  # noqa: E402
from academicos.assessment.pool import get_pool  # noqa: E402
from academicos.assessment.schemas import QuestionSchema, TemplateScope  # noqa: E402

SERVED_BANK = ROOT / "academicos-data" / "syllabus" / "questions.json"
CORE = [(subject, grade) for grade in range(6, 11) for subject in ("Mathematics", "Science")]
# Served classes whose school is seeded with the current book in place of the
# syllabus file's chapters (#136): the view and the filter must follow it too.
CURRENT_BOOK = [("English", 9), ("Social Science", 9)]
ROMAN = {6: "VI", 7: "VII", 8: "VIII", 9: "IX", 10: "X"}


@pytest.fixture
def served(tmp_path, monkeypatch):
    """A client and the pools, both reading the committed bank."""
    from academicos.assessment import audit_log, users as users_mod
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("ACOS_PRINCIPAL_BOOTSTRAP_KEY", "test-bootstrap-key")
    monkeypatch.setattr(audit_log, "_INSTANCE", None)
    monkeypatch.setattr(users_mod, "_INSTANCE", None)
    pool_module._CACHE.clear()
    try:
        with TestClient(app) as client:
            pillar_routes._cfg._load_baked_questions = True
            yield client, pillar_routes._cfg
    finally:
        pool_module._CACHE.clear()


def _view(client, subject, grade) -> dict[str, int]:
    r = client.get(f"/api/v1/catalog/{subject}/{grade}/chapters")
    assert r.status_code == 200, r.text
    return {e["chapterId"]: e["questionCount"] for e in r.json()}


def _schemas(cfg, subject, grade) -> list[QuestionSchema]:
    return [to_question_schema(q) for q in get_pool(cfg, subject=subject, grade=ROMAN[grade]).questions]


@pytest.mark.skipif(not SERVED_BANK.exists(), reason="served bank not built")
def test_the_chapter_view_counts_every_question_where_the_shared_rule_files_it(served):
    """The view kept its own copy of the rule until 2026-10-13, and a test held
    the two equal. It now files through the shared rule; this holds what the
    route shows to what the rule says, chapter for chapter, on every served
    question of these classes, so the picker cannot lie again."""
    client, cfg = served
    checked = 0
    for subject, grade in CORE + CURRENT_BOOK:
        filing = chapter_filing.ChapterFiling.for_class(subject, grade)
        filed = Counter(filing.chapter_of(q.taxonomy_chapter_id, q.chapter_ids)
                        for q in _schemas(cfg, subject, grade))
        shown = {cid: n for cid, n in _view(client, subject, grade).items() if n}
        assert shown == dict(filed), (subject, grade)
        checked += sum(filed.values())
    assert checked > 4000, checked


@pytest.mark.skipif(not SERVED_BANK.exists(), reason="served bank not built")
def test_choosing_a_chapter_reaches_every_question_the_picker_counts(served):
    """The builder's path: a template scoped to one chapter admits exactly the
    questions the picker said that chapter holds -- for every chapter of every
    class 6-10 Mathematics and Science pair, the unmatched bucket included."""
    client, cfg = served
    shown = reached = 0
    wrong = []
    for subject, grade in CORE + CURRENT_BOOK:
        candidates = _schemas(cfg, subject, grade)
        for cid, count in _view(client, subject, grade).items():
            scope = build_scope_filter(TemplateScope(chapter_ids=[cid]), candidates)
            n = sum(1 for q in candidates if scope.in_scope(q))
            shown += count
            reached += n
            if n != count:
                wrong.append((subject, grade, cid, count, n))
    assert wrong == [], wrong[:10]
    assert shown == reached and shown > 4000, (shown, reached)


@pytest.mark.skipif(not SERVED_BANK.exists(), reason="served bank not built")
def test_quick_generate_and_search_draw_from_the_same_chapter(served):
    """quick-generate, the question search and the parallel sets filter
    through QuestionPool.filter; it must reach what the picker counts too."""
    client, cfg = served
    wrong = []
    for subject, grade in CORE:
        pool = get_pool(cfg, subject=subject, grade=ROMAN[grade])
        for cid, count in _view(client, subject, grade).items():
            n = len(pool.filter(subject=subject, grade=ROMAN[grade], chapter_ids=[cid]))
            if n != count:
                wrong.append((subject, grade, cid, count, n))
    assert wrong == [], wrong[:10]


@pytest.mark.skipif(not SERVED_BANK.exists(), reason="served bank not built")
def test_the_audits_reproduction_now_prints_a_paper(served):
    """D24's own case: Mathematics 6 "Lines and Angles", shown with 16, was
    available 0 in every section of the unit-test preset."""
    client, _cfg = served
    view = _view(client, "Mathematics", 6)
    assert view.get("mathematics-6/lines-and-angles", 0) > 0, sorted(view)
    principal = _principal(client)
    r = client.post(
        "/api/v1/schools/school_1/teacher-templates/preset:cbse:6:mathematics:unit_test/availability",
        headers=principal, json={"scope": {"chapterIds": ["mathematics-6/lines-and-angles"]}})
    assert r.status_code == 200, r.text
    assert sum(s["available"] for s in r.json()["sections"]) > 0, r.json()


def _principal(client):
    r = client.post("/api/v1/auth/register", json={
        "name": "head", "email": "head@example.com", "password": "correct horse battery",
        "schoolId": "school_1", "principalKey": "test-bootstrap-key"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_a_chapter_id_the_view_cannot_show_still_matches_its_own_records():
    """A template saved before the chapter view changed may hold an id the
    view no longer lists (a pre-2024 chapter slug). It keeps matching the
    records that carry it, as it always did, rather than emptying the paper."""
    filing = chapter_filing.ChapterFiling(
        known=frozenset({"maths-6/new"}), by_name={}, book_names={})
    test = filing.selects({"old-slug"}, filed_in_class={"maths-6/new"})
    assert test(None, ["old-slug"]) is True
    assert test(None, ["another"]) is False
    # An id the view does show is matched by where the view files the question.
    shown = filing.selects({"maths-6/new"}, filed_in_class={"maths-6/new"})
    assert shown("maths-6/new", ["old-slug"]) is True
    assert shown(None, ["maths-6/new"]) is True
    assert shown("tax-unknown", []) is False


def test_the_unmatched_bucket_can_be_chosen():
    filing = chapter_filing.ChapterFiling(
        known=frozenset({"c1"}), by_name={}, book_names={})
    test = filing.selects({chapter_filing.UNMAPPED}, filed_in_class={"c1", "unmapped"})
    assert test(None, []) is True
    assert test(None, ["c1"]) is False


@pytest.mark.skipif(not SERVED_BANK.exists(), reason="served bank not built")
def test_homework_from_a_class_9_lesson_reaches_its_chapters_questions(served, tmp_path):
    """The homework suggestion matches a lesson's chapter, by the slug the seed
    gave it, against the bank's chapters (`homework_routes._bank_chapters`, the
    picker's list). For English and Social Science 9 no planned slug was a bank
    chapter until 2026-10-13, so a suggestion after any of their lessons
    offered no question."""
    from academicos.curriculum.decomposition_templates import chapter_slug
    from academicos.curriculum.seed_cbse10 import seed_cbse_grade
    from academicos.curriculum.store import CurriculumStore
    from academicos.operations import homework_routes

    _client, cfg = served
    store = CurriculumStore(tmp_path / "plan.sqlite")
    try:
        result = seed_cbse_grade(store, school_id="school_1", academic_year_label="2026-27",
                                 start_date="2026-06-01", end_date="2027-03-31", grade_number=9,
                                 apply_templates=False)
        for subject_name in ("English", "Social Science"):
            subject = store.get_subject_by_name(result.grade_id, subject_name)
            planned = {chapter_slug(c) for book in store.books_for_subject(subject.id)
                       for c in store.chapters_for_book(book.id)}
            offered = {c["chapter_id"]: c["question_count"]
                       for c in homework_routes._bank_chapters(subject_name, 9)}
            assert planned <= set(offered), (subject_name, sorted(planned - set(offered))[:3])
            reached = sum(n for cid, n in offered.items() if cid in planned)
            assert reached > 0, subject_name
            if subject_name == "Social Science":
                # Every Social Science 9 question is tagged with a chapter of the current book.
                assert reached == len(_schemas(cfg, subject_name, 9))
    finally:
        store.close()
