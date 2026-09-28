"""Lesson plans per section (SCH-4), which closes audit D115 on the live path.

Until now a book had one plan for the whole school, laid out on the weekday
slots stored per subject NAME for the year, so every class of the year shared
one Science timetable. Now a plan is per (book, section): it reads the
section's own week (TimetableEntry, M1.2-M1.3) and its allocation, its lessons
carry the section, and PUSH, ADJUST, regenerate, the teacher's day, marking,
the student's class view and coverage all stay inside it. The school-wide
plan (section NULL) keeps working as it did.
"""
from __future__ import annotations

from collections import Counter
from datetime import date
from types import SimpleNamespace

import pytest

from academicos.assessment.audit_log import AuditLog
from academicos.curriculum import calendar as calendar_mod
from academicos.curriculum import scheduling
from academicos.curriculum.store import CurriculumStore

BASE = "/api/v1/curriculum"
BELL = [{"start": f"{8 + i}:00".zfill(5), "end": f"{8 + i}:40".zfill(5)} for i in range(6)]
A_DAYS = [0, 1, 2, 3, 4, 5]          # 10-A: Science every day, Monday to Saturday
B_DAYS = [0, 2, 4]                   # 10-B: Monday, Wednesday, Friday


def _seed(store, school_id="school_1"):
    board = store.create_board(name="CBSE", code="CBSE")
    year = store.create_academic_year(school_id=school_id, label="2026-27",
                                      start_date="2026-06-01", end_date="2027-03-31")
    grade = store.create_grade(academic_year_id=year.id, number=10)      # gets section A
    subject = store.create_subject(grade_id=grade.id, name="Science")
    book = store.create_book(subject_id=subject.id, board_id=board.id, title="Science")
    for u in range(3):
        unit = store.create_unit(canonical_id=f"u:{u}", book_id=book.id, unit_no=str(u),
                                 name=f"Unit {u}", marks=20 + u * 5, seq=u)
        chapter = store.create_chapter(canonical_id=f"c:{u}", unit_id=unit.id, name=f"Chapter {u}", seq=0)
        topic = store.create_topic(canonical_id=f"t:{u}", chapter_id=chapter.id, name=f"Topic {u}", seq=0)
        for s in range(4):
            store.create_subtopic(canonical_id=f"st:{u}:{s}", topic_id=topic.id,
                                  name=f"Subtopic {u}.{s}", seq=s)
    store.create_calendar(academic_year_id=year.id, weekly_off_days=["sunday"],
                          alternate_saturday_rule="none")
    store.create_period_configuration(school_id=school_id, academic_year_id=year.id, period_minutes=40)
    [a] = store.sections_for_grade(grade.id)
    b = store.create_section(grade_id=grade.id, name="B")
    store.create_bell_schedule(academic_year_id=year.id, name="Main", slots=BELL)
    store.set_allocation(section_id=a.id, subject_id=subject.id, teacher_id="t_ana", periods_per_week=6)
    store.set_allocation(section_id=b.id, subject_id=subject.id, teacher_id="t_bala", periods_per_week=3)
    store.replace_section_timetable(a.id, [{"day_of_week": d, "period": 1, "subject_id": subject.id}
                                           for d in A_DAYS])
    store.replace_section_timetable(b.id, [{"day_of_week": d, "period": 2, "subject_id": subject.id}
                                           for d in B_DAYS])
    calendar_mod.compute_teaching_time_estimates(store, academic_year_id=year.id, book_id=book.id,
                                                 periods_per_week=6)
    return SimpleNamespace(year=year.id, book=book.id, subject=subject.id, grade=grade.id,
                           a=a.id, b=b.id, school=school_id)


@pytest.fixture
def store(tmp_path):
    s = CurriculumStore(tmp_path / "curriculum.sqlite")
    yield s
    s.close()


def _plan(store, w, section):
    return scheduling.schedule_book(store, school_id=w.school, academic_year_id=w.year, book_id=w.book,
                                    periods_per_week=6 if section == w.a else 3,
                                    from_date="2026-06-01", section_id=section)


def _weekdays(lessons):
    return Counter(date.fromisoformat(l.date).weekday() for l in lessons)


def test_two_sections_of_one_book_get_two_plans_on_their_own_weeks(store):
    """D115: B's Science never lands on A's days, and neither reads the other."""
    w = _seed(store)
    ra, rb = _plan(store, w, w.a), _plan(store, w, w.b)
    assert ra.section_id == w.a and rb.section_id == w.b
    assert ra.periods_per_week == 6 and rb.periods_per_week == 3
    a_lessons = store.scheduled_lessons_for_book(w.year, w.book, w.a)
    b_lessons = store.scheduled_lessons_for_book(w.year, w.book, w.b)
    assert set(_weekdays(a_lessons)) <= set(A_DAYS)
    assert set(_weekdays(b_lessons)) == set(B_DAYS), "B is taught Monday, Wednesday and Friday only"
    assert all(l.section_id == w.a for l in a_lessons) and all(l.section_id == w.b for l in b_lessons)
    # Estimates are per book (budgeted here at 6 a week), so B's 3 a week
    # cannot fit them all and B's plan says so, rather than inventing time.
    assert {l.subtopic_id for l in b_lessons} <= {l.subtopic_id for l in a_lessons}
    assert ra.warning is None
    assert rb.warning is not None and "teaching periods left" in rb.warning
    assert store.scheduled_lessons_for_book(w.year, w.book) == [], "the school-wide plan is untouched"


def test_regenerating_one_sections_plan_leaves_the_others(store):
    w = _seed(store)
    _plan(store, w, w.a)
    _plan(store, w, w.b)
    before_b = [(l.id, l.date) for l in store.scheduled_lessons_for_book(w.year, w.book, w.b)]
    with pytest.raises(ValueError, match="already has a schedule"):
        _plan(store, w, w.a)
    scheduling.schedule_book(store, school_id=w.school, academic_year_id=w.year, book_id=w.book,
                             periods_per_week=6, force=True, from_date="2026-06-01", section_id=w.a)
    assert [(l.id, l.date) for l in store.scheduled_lessons_for_book(w.year, w.book, w.b)] == before_b


def test_push_moves_only_its_own_sections_lessons(store, tmp_path):
    w = _seed(store)
    _plan(store, w, w.a)
    _plan(store, w, w.b)
    before_b = [(l.id, l.date) for l in store.scheduled_lessons_for_book(w.year, w.book, w.b)]
    result = scheduling.push_lessons_after(store, AuditLog(tmp_path / "audit.sqlite"),
                                           academic_year_id=w.year, book_id=w.book,
                                           from_date="2026-06-03", reason="school closed",
                                           changed_by="p1", section_id=w.a)
    assert result.section_id == w.a and result.lessons_pushed > 0
    assert result.periods_per_week == 6, "A's own week decides the cadence"
    assert [(l.id, l.date) for l in store.scheduled_lessons_for_book(w.year, w.book, w.b)] == before_b
    assert all(date.fromisoformat(l.date).weekday() in A_DAYS
               for l in store.scheduled_lessons_for_book(w.year, w.book, w.a))


def test_adjust_counts_only_its_own_sections_lessons_on_the_day(store, tmp_path):
    w = _seed(store)
    _plan(store, w, w.a)
    _plan(store, w, w.b)
    a_lessons = store.scheduled_lessons_for_book(w.year, w.book, w.a)
    b_monday = next(l for l in store.scheduled_lessons_for_book(w.year, w.book, w.b)
                    if date.fromisoformat(l.date).weekday() == 0)
    # A has one Monday period and its own lesson there; B's lesson that day does not count.
    mover = next(l for l in a_lessons if l.date > b_monday.date
                 and date.fromisoformat(l.date).weekday() == 1)
    free_monday = next(l.date for l in a_lessons if l.date == b_monday.date)
    with pytest.raises(scheduling.RescheduleClash, match="1 lesson"):
        scheduling.adjust_lesson(store, AuditLog(tmp_path / "audit.sqlite"), lesson_id=mover.id,
                                 new_date=free_monday, reason="swap", changed_by="p1")


def test_a_sections_plan_needs_its_allocation_to_resolve_its_cadence(store):
    w = _seed(store)
    c = store.create_section(grade_id=w.grade, name="C")
    with pytest.raises(ValueError, match="no allocation"):
        scheduling._resolve_cadence(store, w.year, w.book, None, c.id)
    assert scheduling._resolve_cadence(store, w.year, w.book, None, w.b) == 3


# --------------------------------------------------------------------- #
# Through the routes, as the section's teachers, a student and the principal
# --------------------------------------------------------------------- #

@pytest.fixture
def world(tmp_path, monkeypatch):
    from _auth_helpers import register_invited
    from test_assessment_routes_auth import _boot_client, _register
    from academicos.curriculum import routes as curriculum_routes

    with _boot_client(tmp_path, monkeypatch) as c:
        p = _register(c, "school_1", "p1@example.com", "Priya", principal_key="test-bootstrap-key")
        ana = _register(c, "school_1", "ana@example.com", "Ana")
        bala = _register(c, "school_1", "bala@example.com", "Bala")
        stu = register_invited(c, "school_1", "s1@example.com", name="Asha", role="student")
        monkeypatch.setattr(curriculum_routes, "_school_today", lambda: date(2026, 6, 1))
        store = curriculum_routes._require()
        w = _seed(store)
        # The seeded allocations name placeholder ids; give the cells the real teachers.
        store.set_allocation(section_id=w.a, subject_id=w.subject, teacher_id=ana["user"]["id"],
                             periods_per_week=6)
        store.set_allocation(section_id=w.b, subject_id=w.subject, teacher_id=bala["user"]["id"],
                             periods_per_week=3)
        store.enroll_student(school_id="school_1", student_id=stu["user"]["id"], section_id=w.b)
        h = lambda u: {"Authorization": f"Bearer {u['token']}"}  # noqa: E731
        w.__dict__.update(c=c, p=h(p), ana=h(ana), bala=h(bala), stu=h(stu), store=store)
        yield w


def _route_plan(w, section, **extra):
    return w.c.post(f"{BASE}/books/{w.book}/schedule", params={"academic_year_id": w.year},
                    json={"sectionId": section, **extra}, headers=w.p)


def test_the_route_plans_a_section_from_its_allocation_and_week(world):
    w = world
    r = _route_plan(w, w.b)
    assert r.status_code == 200, r.text
    assert r.json()["sectionId"] == w.b and r.json()["periodsPerWeek"] == 3
    lessons = w.c.get(f"{BASE}/books/{w.book}/schedule", params={"academic_year_id": w.year,
                                                                 "sectionId": w.b}, headers=w.p).json()
    assert lessons and {l["sectionId"] for l in lessons} == {w.b}
    assert w.c.get(f"{BASE}/books/{w.book}/schedule", params={"academic_year_id": w.year},
                   headers=w.p).json() == [], "the school-wide plan is a different plan"
    # The school-wide plan still needs its periods a week.
    bare = w.c.post(f"{BASE}/books/{w.book}/schedule", params={"academic_year_id": w.year},
                    json={}, headers=w.p)
    assert bare.status_code == 422 and "periodsPerWeek" in bare.json()["detail"]


def test_each_teacher_sees_and_marks_only_their_sections_lessons(world):
    w = world
    assert _route_plan(w, w.a).status_code == 200
    assert _route_plan(w, w.b).status_code == 200
    rng = {"start_date": "2026-06-01", "end_date": "2026-06-07"}
    ana = w.c.get(f"{BASE}/my-schedule", params=rng, headers=w.ana).json()
    bala = w.c.get(f"{BASE}/my-schedule", params=rng, headers=w.bala).json()
    assert ana and {e["sectionName"] for e in ana} == {"10-A"}
    assert bala and {e["sectionName"] for e in bala} == {"10-B"}
    assert len(ana) == 6 and len(bala) == 3, "each section's own week: 6 and 3 periods"
    a_lesson = ana[0]["lessonId"]
    assert w.c.patch(f"{BASE}/scheduled-lessons/{a_lesson}", json={"status": "completed"},
                     headers=w.bala).status_code == 403
    assert w.c.patch(f"{BASE}/scheduled-lessons/{a_lesson}", json={"status": "completed"},
                     headers=w.ana).status_code == 200


def test_a_student_follows_their_own_sections_plan(world):
    w = world
    _route_plan(w, w.a)
    _route_plan(w, w.b)
    mine = w.c.get(f"{BASE}/my-class-schedule", params={"start_date": "2026-06-01",
                                                        "end_date": "2026-06-07"}, headers=w.stu)
    assert mine.status_code == 200, mine.text
    assert len(mine.json()) == 3, "10-B's three Science periods, not 10-A's six"
    progress = w.c.get(f"{BASE}/my-progress", params={"academic_year_id": w.year}, headers=w.stu).json()
    [science] = progress["subjects"]
    b_total = len(w.store.scheduled_lessons_for_book(w.year, w.book, w.b))
    assert science["totalCount"] <= b_total


def test_coverage_reports_each_sections_plan_on_its_own_row(world):
    w = world
    _route_plan(w, w.a)
    _route_plan(w, w.b)
    report = w.c.get(f"{BASE}/reporting/coverage", params={"academic_year_id": w.year,
                                                           "as_of_date": "2026-06-30"}, headers=w.p).json()
    rows = {r["sectionName"]: r for r in report["subjects"]}
    assert set(rows) == {"A", "B"}
    a_total = len(w.store.scheduled_lessons_for_book(w.year, w.book, w.a))
    b_total = len(w.store.scheduled_lessons_for_book(w.year, w.book, w.b))
    assert rows["A"]["totalLessons"] == a_total and rows["B"]["totalLessons"] == b_total
    assert rows["A"]["teacherId"] != rows["B"]["teacherId"]
    assert report["totalLessons"] == a_total + b_total
