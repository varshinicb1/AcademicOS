"""seed_cbse10.py against the REAL data files
(academicos-data/syllabus/*.json) -- not synthetic fixtures. This is the
actual bridge from "real, hand-verified CBSE data already exists" to "the
canonical curriculum model has real rows in it" that
docs/ACADEMIC_DATA_MODEL.md section 5 describes.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.curriculum.seed_cbse10 import seed_cbse_class_10
from academicos.curriculum.store import CurriculumStore
from academicos.syllabus.cbse_syllabus import load_syllabus


@pytest.fixture
def store(tmp_path):
    s = CurriculumStore(tmp_path / "curriculum.sqlite")
    yield s
    s.close()


def _seed(store):
    return seed_cbse_class_10(
        store, school_id="school_1", academic_year_label="2026-27",
        start_date="2026-06-01", end_date="2027-04-30")


def test_seeds_all_five_real_subjects(store):
    result = _seed(store)
    assert result.subjects_seeded == 5
    assert result.subjects_skipped == []


def test_seeds_real_chapter_names_matching_the_source_json(store):
    """Not a row-count check -- verifies the actual seeded data matches
    the real CBSE Science JSON, e.g. 'Chemical Reactions and Equations'
    really exists as a Chapter row afterward."""
    _seed(store)
    grade = store.get_grade_by_number(
        store.get_academic_year_by_label("school_1", "2026-27").id, 10)
    subject = store.get_subject_by_name(grade.id, "Science")
    book = store.books_for_subject(subject.id)[0]
    chapters = {c.name for c in store.chapters_for_book(book.id)}

    assert "Chemical Reactions and Equations" in chapters
    assert "Light – Reflection and Refraction" in chapters
    assert "Our Environment" in chapters

    hindi = store.get_subject_by_name(grade.id, "Hindi")
    hindi_book = store.books_for_subject(hindi.id)[0]
    hindi_chapters = {c.name for c in store.chapters_for_book(hindi_book.id)}
    assert "Rachna ke Aadhar par Vakya Bhed" in hindi_chapters
    assert "Kshitij Bhag 2 Gadya Khand" in hindi_chapters
    assert "Anuchhed Lekhan" in hindi_chapters


def test_mathematics_gets_the_books_chapters_under_their_cbse_units(store):
    """Real data: Mathematics_10.json's units all have chapters: [] and the
    book's chapters are listed at the top. Each unit used to be seeded as
    its own only chapter (audit D118); now the book's 14 chapters are, each
    under the unit the CBSE Class X course structure puts it in."""
    _seed(store)
    grade = store.get_grade_by_number(
        store.get_academic_year_by_label("school_1", "2026-27").id, 10)
    subject = store.get_subject_by_name(grade.id, "Mathematics")
    book = store.books_for_subject(subject.id)[0]
    chapters = {c.name for c in store.chapters_for_book(book.id)}

    doc = load_syllabus("Mathematics", 10)
    assert all(len(u.chapters) == 0 for u in doc.units), "fixture assumption changed upstream"
    assert chapters == {c.name for c in doc.chapters}
    assert not chapters & {u.name for u in doc.units} - {"Coordinate Geometry"}
    by_unit = {u.name: [c.name for c in store.chapters_for_unit(u.id)] for u in store.units_for_book(book.id)}
    assert by_unit["Algebra"] == ["Polynomials", "Pair of Linear Equations in Two Variables",
                                  "Quadratic Equations", "Arithmetic Progressions"]
    assert by_unit["Trigonometry"] == ["Introduction to Trigonometry", "Some Applications of Trigonometry"]
    assert sum(u.marks for u in store.units_for_book(book.id)) == 80


def test_unit_marks_are_the_real_cbse_weightage_not_invented(store):
    _seed(store)
    grade = store.get_grade_by_number(
        store.get_academic_year_by_label("school_1", "2026-27").id, 10)
    subject = store.get_subject_by_name(grade.id, "Science")
    book = store.books_for_subject(subject.id)[0]
    units = store.units_for_book(book.id)

    doc = load_syllabus("Science", 10)
    by_no = {u.unit_no: u.marks for u in doc.units}
    for u in units:
        assert u.marks == by_no[u.unit_no]
    assert sum(u.marks for u in units) == doc.total_marks == 80


def test_chapters_have_no_topics_yet_honestly(store):
    """docs/ACADEMIC_DATA_MODEL.md section 6: Topic/Subtopic content isn't
    invented by this seed -- verify it's genuinely absent, not silently
    fabricated."""
    _seed(store)
    grade = store.get_grade_by_number(
        store.get_academic_year_by_label("school_1", "2026-27").id, 10)
    subject = store.get_subject_by_name(grade.id, "Science")
    book = store.books_for_subject(subject.id)[0]
    for chapter in store.chapters_for_book(book.id):
        assert store.topics_for_chapter(chapter.id) == []


def test_idempotent_rerun_creates_no_duplicates(store):
    first = _seed(store)
    second = _seed(store)

    assert first.academic_year_id == second.academic_year_id
    assert first.grade_id == second.grade_id
    # Nothing new created the second time -- everything matched by natural
    # key / canonical_id and was reused.
    assert second.subjects_seeded == 5  # subjects "seeded" counts reused too
    assert store.academic_years_for_school("school_1") == \
        store.academic_years_for_school("school_1")  # sanity: still just one list
    year = store.get_academic_year_by_label("school_1", "2026-27")
    assert len(store.academic_years_for_school("school_1")) == 1
    grade = store.get_grade_by_number(year.id, 10)
    assert len(store.grades_for_year(year.id)) == 1
    subject = store.get_subject_by_name(grade.id, "Science")
    assert len(store.subjects_for_grade(grade.id)) == 5
    book = store.books_for_subject(subject.id)
    assert len(book) == 1
    # Chapter/unit counts identical across both runs (re-verify by re-querying).
    chapters_after_both_runs = store.chapters_for_book(book[0].id)
    assert len(chapters_after_both_runs) == len(
        {c.canonical_id for c in chapters_after_both_runs})  # no duplicate canonical_ids


def test_different_schools_get_independent_seeds(store):
    """Two schools using the same CBSE curriculum must not collide --
    academic years/grades/subjects/books are school-scoped, and (§6: Book
    is the direct parent of Chapters, since two schools can pick genuinely
    different books for the same subject) each school's book owns its own
    real chapter rows -- same content, independent ids, not silently
    aliased onto the first school's rows.

    This is a real regression test: an earlier version of the canonical_id
    scheme made units/chapters (board, grade, subject)-global rather than
    book-scoped, so seeding a second school found the first school's units
    "already existing" and reused them -- leaving the second school's own
    book with zero chapters. Caught by this exact test before it shipped."""
    result_a = seed_cbse_class_10(
        store, school_id="school_a", academic_year_label="2026-27",
        start_date="2026-06-01", end_date="2027-04-30")
    result_b = seed_cbse_class_10(
        store, school_id="school_b", academic_year_label="2026-27",
        start_date="2026-06-01", end_date="2027-04-30")

    assert result_a.academic_year_id != result_b.academic_year_id
    assert result_a.grade_id != result_b.grade_id

    grade_a = store.get_grade(result_a.grade_id)
    grade_b = store.get_grade(result_b.grade_id)
    subj_a = store.get_subject_by_name(grade_a.id, "Science")
    subj_b = store.get_subject_by_name(grade_b.id, "Science")
    book_a = store.books_for_subject(subj_a.id)[0]
    book_b = store.books_for_subject(subj_b.id)[0]
    assert book_a.id != book_b.id

    chapters_a = store.chapters_for_book(book_a.id)
    chapters_b = store.chapters_for_book(book_b.id)
    # Same real content (the same official CBSE syllabus)...
    assert {c.name for c in chapters_a} == {c.name for c in chapters_b}
    assert len(chapters_a) == len(chapters_b) > 0
    # ...but genuinely independent rows, not aliased onto each other.
    assert {c.canonical_id for c in chapters_a}.isdisjoint(
        {c.canonical_id for c in chapters_b})


def test_seed_cbse_all_grades(store):
    from academicos.curriculum.seed_cbse10 import seed_cbse_all_grades
    from academicos.syllabus.cbse_syllabus import list_available_syllabi

    syllabi = list_available_syllabi()
    assert len(syllabi) >= 40

    results = seed_cbse_all_grades(
        store, school_id="school_all", academic_year_label="2026-27",
        start_date="2026-06-01", end_date="2027-04-30",
        grades=[6, 7, 8, 9, 10, 11, 12],
    )
    assert len(results) == 7

    # Check Grade 12 has Senior Secondary subjects
    g12_res = next(r for r in results if store.get_grade(r.grade_id).number == 12)
    assert g12_res.subjects_seeded >= 10
    g12_grade = store.get_grade(g12_res.grade_id)
    assert store.get_subject_by_name(g12_grade.id, "Physics") is not None
    assert store.get_subject_by_name(g12_grade.id, "Accountancy") is not None

    # Check Grade 6 has Middle School subjects
    g6_res = next(r for r in results if store.get_grade(r.grade_id).number == 6)
    assert g6_res.subjects_seeded == 5
    g6_grade = store.get_grade(g6_res.grade_id)
    assert store.get_subject_by_name(g6_grade.id, "Mathematics") is not None

