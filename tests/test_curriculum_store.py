"""curriculum/store.py -- CRUD + idempotency for the operational curriculum
hierarchy (docs/ACADEMIC_DATA_MODEL.md). Hermetic: every test builds its
own tmp_path-backed store, no dependency on real CBSE data (that's
test_curriculum_seed_cbse10.py's job).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.curriculum.store import CurriculumStore, get_curriculum_store


@pytest.fixture
def store(tmp_path):
    s = CurriculumStore(tmp_path / "curriculum.sqlite")
    yield s
    s.close()


# --------------------------------------------------------------------- #
# boards
# --------------------------------------------------------------------- #

def test_create_and_get_board(store):
    b = store.create_board(name="CBSE", code="CBSE")
    assert store.get_board(b.id) == b
    assert store.get_board_by_code("CBSE") == b


def test_list_boards(store):
    store.create_board(name="CBSE", code="CBSE")
    store.create_board(name="ICSE", code="ICSE")
    assert {b.code for b in store.list_boards()} == {"CBSE", "ICSE"}


# --------------------------------------------------------------------- #
# academic years / grades / subjects -- full parent chain
# --------------------------------------------------------------------- #

def test_academic_year_grade_subject_chain(store):
    year = store.create_academic_year(
        school_id="school_1", label="2026-27", start_date="2026-06-01", end_date="2027-04-30")
    assert store.get_academic_year(year.id) == year
    assert store.academic_years_for_school("school_1") == [year]

    grade = store.create_grade(academic_year_id=year.id, number=10)
    assert store.get_grade(grade.id) == grade
    assert store.grades_for_year(year.id) == [grade]

    subject = store.create_subject(grade_id=grade.id, name="Science")
    assert store.get_subject(subject.id) == subject
    assert store.subjects_for_grade(grade.id) == [subject]


def test_get_academic_year_by_label_scoped_per_school(store):
    a = store.create_academic_year(school_id="school_1", label="2026-27",
                                   start_date="2026-06-01", end_date="2027-04-30")
    store.create_academic_year(school_id="school_2", label="2026-27",
                               start_date="2026-06-01", end_date="2027-04-30")
    found = store.get_academic_year_by_label("school_1", "2026-27")
    assert found.id == a.id
    assert store.get_academic_year_by_label("school_1", "no-such-label") is None


def test_get_grade_by_number_distinguishes_sections(store):
    year = store.create_academic_year(school_id="s", label="y", start_date="2026-01-01", end_date="2026-12-31")
    g_none = store.create_grade(academic_year_id=year.id, number=10)
    g_a = store.create_grade(academic_year_id=year.id, number=10, section="A")

    assert store.get_grade_by_number(year.id, 10).id == g_none.id
    assert store.get_grade_by_number(year.id, 10, section="A").id == g_a.id
    assert store.get_grade_by_number(year.id, 10, section="B") is None


def test_get_subject_by_name(store):
    year = store.create_academic_year(school_id="s", label="y", start_date="2026-01-01", end_date="2026-12-31")
    grade = store.create_grade(academic_year_id=year.id, number=10)
    subj = store.create_subject(grade_id=grade.id, name="Science")
    assert store.get_subject_by_name(grade.id, "Science").id == subj.id
    assert store.get_subject_by_name(grade.id, "Physics") is None


# --------------------------------------------------------------------- #
# books
# --------------------------------------------------------------------- #

def test_book_roundtrip_with_source_doc_ids(store):
    board = store.create_board(name="CBSE", code="CBSE")
    year = store.create_academic_year(school_id="s", label="y", start_date="2026-01-01", end_date="2026-12-31")
    grade = store.create_grade(academic_year_id=year.id, number=10)
    subject = store.create_subject(grade_id=grade.id, name="Science")

    book = store.create_book(subject_id=subject.id, board_id=board.id, title="NCERT Science X",
                             publisher="NCERT", source_doc_ids=["doc_1", "doc_2"])
    fetched = store.get_book(book.id)
    assert fetched.title == "NCERT Science X"
    assert fetched.source_doc_ids == ["doc_1", "doc_2"]
    assert fetched.status == "selected"

    assert store.get_book_by_title(subject.id, "NCERT Science X").id == book.id
    assert store.books_for_subject(subject.id) == [fetched]


# --------------------------------------------------------------------- #
# units / chapters -- the real curriculum hierarchy + reordering (§13)
# --------------------------------------------------------------------- #

def _seed_book(store) -> str:
    board = store.create_board(name="CBSE", code="CBSE")
    year = store.create_academic_year(school_id="s", label="y", start_date="2026-01-01", end_date="2026-12-31")
    grade = store.create_grade(academic_year_id=year.id, number=10)
    subject = store.create_subject(grade_id=grade.id, name="Science")
    return store.create_book(subject_id=subject.id, board_id=board.id, title="Book").id


def test_unit_chapter_hierarchy_and_book_join(store):
    book_id = _seed_book(store)
    unit1 = store.create_unit(canonical_id="cbse:10:science:unit:I", book_id=book_id,
                              unit_no="I", name="Chemical Substances", marks=25, seq=0)
    unit2 = store.create_unit(canonical_id="cbse:10:science:unit:II", book_id=book_id,
                              unit_no="II", name="World of Living", marks=25, seq=1)
    store.create_chapter(canonical_id="cbse:10:science:chapter:c1", unit_id=unit1.id, name="Chapter 1", seq=0)
    store.create_chapter(canonical_id="cbse:10:science:chapter:c2", unit_id=unit1.id, name="Chapter 2", seq=1)
    store.create_chapter(canonical_id="cbse:10:science:chapter:c3", unit_id=unit2.id, name="Chapter 3", seq=0)

    assert len(store.chapters_for_unit(unit1.id)) == 2
    # chapters_for_book: unit-then-chapter seq order across the whole book
    names = [c.name for c in store.chapters_for_book(book_id)]
    assert names == ["Chapter 1", "Chapter 2", "Chapter 3"]

    assert store.get_unit_by_canonical_id("cbse:10:science:unit:I").id == unit1.id
    assert store.get_chapter_by_canonical_id("cbse:10:science:chapter:c2").name == "Chapter 2"


def test_reorder_chapter_changes_delivery_sequence(store):
    """§13: 'teach last chapter first' -- delivery order (seq) must be
    independently changeable from the unit/textbook order chapters were
    created in."""
    book_id = _seed_book(store)
    unit = store.create_unit(canonical_id="cbse:10:science:unit:I", book_id=book_id,
                             unit_no="I", name="Unit", marks=25, seq=0)
    first = store.create_chapter(canonical_id="c:first", unit_id=unit.id, name="First", seq=0)
    last = store.create_chapter(canonical_id="c:last", unit_id=unit.id, name="Last", seq=1)

    store.reorder_chapter(last.id, 0)
    store.reorder_chapter(first.id, 1)

    ordered = store.chapters_for_unit(unit.id)
    assert [c.name for c in ordered] == ["Last", "First"]


# --------------------------------------------------------------------- #
# topics / subtopics -- canonical_id is what qmap.py will resolve against
# --------------------------------------------------------------------- #

def test_topic_subtopic_hierarchy(store):
    book_id = _seed_book(store)
    unit = store.create_unit(canonical_id="u", book_id=book_id, unit_no="I", name="Unit", seq=0)
    chapter = store.create_chapter(canonical_id="c", unit_id=unit.id, name="Chapter", seq=0)
    topic = store.create_topic(canonical_id="cbse:10:science:topic:optics", chapter_id=chapter.id,
                               name="Optics", seq=0)
    subtopic = store.create_subtopic(canonical_id="cbse:10:science:subtopic:diffraction",
                                     topic_id=topic.id, name="Diffraction", seq=0)

    assert store.topics_for_chapter(chapter.id) == [topic]
    assert store.subtopics_for_topic(topic.id) == [subtopic]
    assert store.get_subtopic_by_canonical_id("cbse:10:science:subtopic:diffraction").id == subtopic.id


def test_canonical_id_uniqueness_enforced(store):
    book_id = _seed_book(store)
    store.create_unit(canonical_id="dup", book_id=book_id, unit_no="I", name="A", seq=0)
    with pytest.raises(Exception):  # sqlite3.IntegrityError -- UNIQUE constraint
        store.create_unit(canonical_id="dup", book_id=book_id, unit_no="II", name="B", seq=1)


# --------------------------------------------------------------------- #
# period configuration / calendar / holidays (§8, §10)
# --------------------------------------------------------------------- #

def test_period_configuration_never_hardcoded(store):
    """§8: 30/40/45/50 min periods, admin-set -- not a fixed global."""
    year = store.create_academic_year(school_id="s", label="y", start_date="2026-01-01", end_date="2026-12-31")
    cfg = store.create_period_configuration(school_id="s", academic_year_id=year.id, period_minutes=40)
    assert store.period_configuration_for_year(year.id).period_minutes == 40
    assert cfg.period_minutes == 40  # not the 45 CLAUDE.md-adjacent docs might assume


def test_calendar_and_holidays(store):
    year = store.create_academic_year(school_id="s", label="y", start_date="2026-01-01", end_date="2026-12-31")
    cal = store.create_calendar(academic_year_id=year.id, weekly_off_days=["sunday"],
                                alternate_saturday_rule="2nd,4th")
    fetched = store.get_calendar_for_year(year.id)
    assert fetched.weekly_off_days == ["sunday"]
    assert fetched.alternate_saturday_rule == "2nd,4th"

    store.add_holiday(calendar_id=cal.id, date="2026-10-20", label="Diwali", kind="holiday")
    store.add_holiday(calendar_id=cal.id, date="2026-08-15", label="Independence Day", kind="holiday")
    holidays = store.holidays_for_calendar(cal.id)
    assert [h.label for h in holidays] == ["Independence Day", "Diwali"]  # date-ordered


# --------------------------------------------------------------------- #
# teaching time estimates (§9, §27)
# --------------------------------------------------------------------- #

def test_teaching_time_estimate_unapproved_by_default(store):
    """§29: admin must 'assign / approve' teaching times -- approved_by
    stays null until that real review step happens."""
    book_id = _seed_book(store)
    unit = store.create_unit(canonical_id="u", book_id=book_id, unit_no="I", name="Unit", seq=0)
    chapter = store.create_chapter(canonical_id="c", unit_id=unit.id, name="Chapter", seq=0)
    topic = store.create_topic(canonical_id="t", chapter_id=chapter.id, name="Topic", seq=0)
    subtopic = store.create_subtopic(canonical_id="st", topic_id=topic.id, name="Subtopic", seq=0)
    year = store.create_academic_year(school_id="s", label="y", start_date="2026-01-01", end_date="2026-12-31")

    tte = store.create_teaching_time_estimate(
        subtopic_id=subtopic.id, academic_year_id=year.id, estimated_minutes=45,
        method="marks_weightage_proportional")
    assert tte.approved_by is None
    assert store.teaching_time_estimate_for_subtopic(subtopic.id, year.id).estimated_minutes == 45


# --------------------------------------------------------------------- #
# teacher assignments (§15 -- "what do I teach today")
# --------------------------------------------------------------------- #

def test_assign_teacher_and_read_back(store):
    book_id = _seed_book(store)
    a = store.assign_teacher(school_id="s", teacher_id="user_1", book_id=book_id)
    assert a.teacher_id == "user_1"
    assignments = store.assignments_for_teacher("user_1")
    assert len(assignments) == 1
    assert assignments[0].book_id == book_id


def test_assign_teacher_is_idempotent(store):
    """Same (teacher, book) pair assigned twice -- one real row, not two."""
    book_id = _seed_book(store)
    first = store.assign_teacher(school_id="s", teacher_id="user_1", book_id=book_id)
    second = store.assign_teacher(school_id="s", teacher_id="user_1", book_id=book_id)
    assert first.id == second.id
    assert len(store.assignments_for_teacher("user_1")) == 1


def test_unassign_teacher_removes_the_assignment(store):
    book_id = _seed_book(store)
    store.assign_teacher(school_id="s", teacher_id="user_1", book_id=book_id)
    store.unassign_teacher(teacher_id="user_1", book_id=book_id)
    assert store.assignments_for_teacher("user_1") == []


def test_teacher_with_no_assignments_gets_an_empty_list(store):
    assert store.assignments_for_teacher("nobody") == []


# --------------------------------------------------------------------- #
# completion tracking (§15 -- YES/NO + optional note)
# --------------------------------------------------------------------- #

def _seed_lesson(store):
    book_id = _seed_book(store)
    year = store.create_academic_year(school_id="s2", label="y2",
                                      start_date="2026-01-01", end_date="2026-12-31")
    return store.create_scheduled_lesson(school_id="s", academic_year_id=year.id, book_id=book_id,
                                         subtopic_id="st_1", date="2026-06-15")


def test_new_lesson_is_unmarked_by_default(store):
    lesson = _seed_lesson(store)
    assert lesson.status == "scheduled"
    assert lesson.note is None
    assert lesson.completed_by is None
    assert lesson.completed_at is None


def test_mark_lesson_completed_with_a_note(store):
    lesson = _seed_lesson(store)
    updated = store.mark_lesson(lesson.id, status="completed", note="Covered fully, good engagement",
                                completed_by="teacher_1")
    assert updated.status == "completed"
    assert updated.note == "Covered fully, good engagement"
    assert updated.completed_by == "teacher_1"
    assert updated.completed_at is not None
    # persisted, not just the return value
    assert store.get_scheduled_lesson(lesson.id).status == "completed"


def test_mark_lesson_skipped_without_a_note(store):
    lesson = _seed_lesson(store)
    updated = store.mark_lesson(lesson.id, status="skipped", note=None, completed_by="teacher_1")
    assert updated.status == "skipped"
    assert updated.note is None


def test_mark_lesson_rejects_an_invalid_status(store):
    lesson = _seed_lesson(store)
    with pytest.raises(ValueError):
        store.mark_lesson(lesson.id, status="done", note=None, completed_by="teacher_1")
    # rejected -- the real row is untouched
    assert store.get_scheduled_lesson(lesson.id).status == "scheduled"


def test_mark_lesson_can_be_undone_back_to_scheduled(store):
    lesson = _seed_lesson(store)
    store.mark_lesson(lesson.id, status="completed", note="oops wrong day", completed_by="teacher_1")
    undone = store.mark_lesson(lesson.id, status="scheduled", note=None, completed_by="teacher_1")
    assert undone.status == "scheduled"
    assert undone.note is None


# --------------------------------------------------------------------- #
# student enrollment (§18 -- student visibility)
# --------------------------------------------------------------------- #

def test_enroll_student_and_read_back(store):
    board = store.create_board(name="CBSE", code="CBSE")
    year = store.create_academic_year(school_id="s", label="y", start_date="2026-01-01", end_date="2026-12-31")
    grade = store.create_grade(academic_year_id=year.id, number=10, section="A")

    e = store.enroll_student(school_id="s", student_id="user_stu1", grade_id=grade.id)
    assert e.grade_id == grade.id
    assert store.enrollment_for_student("user_stu1").grade_id == grade.id


def test_enroll_student_is_one_enrollment_per_student(store):
    """Re-enrolling (e.g. promotion to a new grade) replaces the row,
    never leaves two."""
    board = store.create_board(name="CBSE", code="CBSE")
    year = store.create_academic_year(school_id="s", label="y", start_date="2026-01-01", end_date="2026-12-31")
    grade9 = store.create_grade(academic_year_id=year.id, number=9)
    grade10 = store.create_grade(academic_year_id=year.id, number=10)

    first = store.enroll_student(school_id="s", student_id="user_stu1", grade_id=grade9.id)
    second = store.enroll_student(school_id="s", student_id="user_stu1", grade_id=grade10.id)
    assert first.id == second.id
    assert store.enrollment_for_student("user_stu1").grade_id == grade10.id


def test_unenrolled_student_has_no_enrollment(store):
    assert store.enrollment_for_student("nobody") is None


def test_grade_id_for_book_and_book_ids_for_grade(store):
    book_id = _seed_book(store)
    book = store.get_book(book_id)
    subject = store.get_subject(book.subject_id)
    assert store.grade_id_for_book(book_id) == subject.grade_id
    assert book_id in store.book_ids_for_grade(subject.grade_id)


def test_school_id_for_grade(store):
    board = store.create_board(name="CBSE", code="CBSE")
    year = store.create_academic_year(school_id="school_x", label="y",
                                      start_date="2026-01-01", end_date="2026-12-31")
    grade = store.create_grade(academic_year_id=year.id, number=10)
    assert store.school_id_for_grade(grade.id) == "school_x"


# --------------------------------------------------------------------- #
# get_curriculum_store singleton
# --------------------------------------------------------------------- #

def test_get_curriculum_store_is_a_singleton(tmp_path, monkeypatch):
    import academicos.curriculum.store as store_mod
    monkeypatch.setattr(store_mod, "_INSTANCE", None)
    a = store_mod.get_curriculum_store(tmp_path)
    b = store_mod.get_curriculum_store(tmp_path)
    assert a is b
    a.close()
