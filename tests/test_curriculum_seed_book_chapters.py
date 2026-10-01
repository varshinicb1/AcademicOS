"""Mathematics 6-10 and Science 7-9 are seeded with the book's own chapters
(audit D118), against the REAL syllabus and taxonomy files.

Before: those syllabus files list their CBSE units (with marks) and the
book's chapters separately, and the seed made each unit its own only
chapter. A class got chapters no textbook prints, no topic source keyed
onto them, and only 6 of 25 class-subject pairs reached subtopics -- so
approving the proposed topics and "Plan every section" dated nothing for
those classes.
"""
from __future__ import annotations

import dataclasses
from datetime import date

import pytest

from academicos.curriculum import extraction, seed_cbse10
from academicos.curriculum.seed_cbse10 import seed_cbse_grade
from academicos.curriculum.store import CurriculumStore
from academicos.syllabus.cbse_syllabus import load_syllabus, taxonomy_chapters

PAIRS = [("Mathematics", g) for g in (6, 7, 8, 9, 10)] + [("Science", g) for g in (7, 8, 9)]
YEAR = dict(school_id="school_1", academic_year_label="2026-27", start_date="2026-06-01",
            end_date="2027-03-31")


@pytest.fixture
def store(tmp_path):
    s = CurriculumStore(tmp_path / "curriculum.sqlite")
    yield s
    s.close()


def _book(store, result, subject):
    s = store.get_subject_by_name(result.grade_id, subject)
    return store.books_for_subject(s.id)[0]


def _approve_all(store, book):
    for chapter in store.chapters_for_book(book.id):
        for run in store.extraction_runs_for_chapter(chapter.id):
            if run.status in ("pending", "reviewed"):
                extraction.approve_run(store, run.id, approved_by="p1")


def _subtopics(store, chapter):
    return [st for t in store.topics_for_chapter(chapter.id) for st in store.subtopics_for_topic(t.id)]


@pytest.mark.parametrize("subject,grade", PAIRS)
def test_a_fresh_seed_has_the_books_chapters_and_they_reach_subtopics(store, subject, grade):
    result = seed_cbse_grade(store, grade_number=grade, **YEAR)
    book = _book(store, result, subject)
    doc = load_syllabus(subject, grade)
    book_order = list(taxonomy_chapters(subject, grade).values())
    chapters = store.chapters_for_book(book.id)
    names = [c.name for c in chapters]

    assert sorted(names) == sorted(book_order), "the book's chapters, not its units"
    if subject == "Mathematics" and grade == 10:
        assert len(store.units_for_book(book.id)) == len(doc.units), "placed in the CBSE units"
    else:
        assert names == book_order, "one unit holding the book, in book order"
    assert sum(u.marks or 0 for u in store.units_for_book(book.id)) == sum(u.marks for u in doc.units)

    _approve_all(store, book)
    empty = [c.name for c in chapters if not _subtopics(store, c)]
    # The only chapters left without subtopics are the ones whose contents
    # print no sections (the "introduction to science" first chapters).
    report = next(t for t in result.topic_templates if t.subject == subject)
    assert len(empty) == report.chapters_without_topics <= 1, empty
    assert all(name in (report.note or "") for name in empty)


def test_a_reseed_of_an_old_school_adds_the_chapters_without_touching_the_old_ones(store, monkeypatch):
    """A school seeded before D118 has one chapter per unit, maybe with
    approved topics and taught lessons. A re-seed adds the book's chapters
    beside them; nothing is renamed, moved or deleted, and a second re-seed
    adds nothing."""
    real = seed_cbse10.load_syllabus
    monkeypatch.setattr(seed_cbse10, "load_syllabus",
                        lambda s, g: dataclasses.replace(real(s, g), chapters=()) if real(s, g) else None)
    old = seed_cbse_grade(store, grade_number=7, **YEAR)
    book = _book(store, old, "Science")
    before = [(c.id, c.canonical_id, c.unit_id, c.name) for c in store.chapters_for_book(book.id)]
    units_before = [u.id for u in store.units_for_book(book.id)]
    assert [n for *_, n in before] == [u.name for u in load_syllabus("Science", 7).units], "the old shape"

    monkeypatch.setattr(seed_cbse10, "load_syllabus", real)
    again = seed_cbse_grade(store, grade_number=7, **YEAR)
    after = store.chapters_for_book(book.id)
    assert {(c.id, c.canonical_id, c.unit_id, c.name) for c in after} >= set(before), "nothing old changed"
    added = [c.name for c in after if c.id not in {b[0] for b in before}]
    assert added == list(taxonomy_chapters("Science", 7).values())
    units = store.units_for_book(book.id)
    assert [u.id for u in units][:len(units_before)] == units_before, "the book's unit comes after the old ones"
    assert again.topic_templates and next(t for t in again.topic_templates
                                          if t.subject == "Science").topics_proposed > 0

    third = seed_cbse_grade(store, grade_number=7, **YEAR)
    assert third.chapters_seeded == 0 and len(store.chapters_for_book(book.id)) == len(after)


def test_plan_every_section_dates_class_7_mathematics_and_science(tmp_path, monkeypatch):
    """The route a school uses: seed class 7, a calendar, a bell, periods a
    week, then "Plan every section" with the proposed topics approved."""
    from test_assessment_routes_auth import _boot_client, _register
    from test_web_school_setup import BASE, PRINCIPAL_KEY

    from academicos.curriculum import routes as curriculum_routes

    with _boot_client(tmp_path, monkeypatch) as client:
        monkeypatch.setattr(curriculum_routes, "_school_today", lambda: date(2026, 6, 1))
        principal = _register(client, "school_1", "head@school1.test", "Head", principal_key=PRINCIPAL_KEY)
        auth = {"Authorization": f"Bearer {principal['token']}"}
        assert client.post(f"{BASE}/seed/cbse", headers=auth, json={
            "grade": 7, "academicYearLabel": "2026-27", "startDate": "2026-04-01",
            "endDate": "2027-03-31"}).status_code == 200
        year = client.get(f"{BASE}/academic-years", params={"school_id": "school_1"}, headers=auth).json()[0]["id"]
        assert client.post(f"{BASE}/academic-years/{year}/calendar", headers=auth,
                           json={"weeklyOffDays": ["sunday"], "alternateSaturdayRule": "none"}).status_code == 200
        slots = [{"start": f"{8 + i:02d}:00", "end": f"{8 + i:02d}:45"} for i in range(7)]
        assert client.post(f"{BASE}/academic-years/{year}/bell-schedules", headers=auth,
                           json={"name": "Main", "slots": slots}).status_code == 200
        grade = client.get(f"{BASE}/academic-years/{year}/grades", headers=auth).json()[0]["id"]
        section = client.get(f"{BASE}/academic-years/{year}/sections", headers=auth).json()[0]["id"]
        subjects = {s["name"]: s["id"] for s in client.get(f"{BASE}/grades/{grade}/subjects", headers=auth).json()}
        for name in ("Mathematics", "Science"):
            r = client.put(f"{BASE}/sections/{section}/allocations/{subjects[name]}", headers=auth,
                           json={"teacherId": principal["user"]["id"], "periodsPerWeek": 6})
            assert r.status_code == 200, r.text

        built = client.post(f"{BASE}/academic-years/{year}/lesson-plans", headers=auth,
                            json={"approveProposedTopics": True})
        assert built.status_code == 200, built.text
        plans = {p["subjectName"]: p for p in built.json()["plans"]}
        assert set(plans) == {"Mathematics", "Science"}, built.json()["notPlanned"]
        for name, plan in plans.items():
            assert plan["lessonsCreated"] > 0 and plan["subtopicsWithoutEstimate"] == 0, (name, plan)
