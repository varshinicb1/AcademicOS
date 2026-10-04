"""Classes 1-5 can be set up in production (N-3-2): academicos-data/syllabus/
ncert_books.json is committed, with each class 1-5 book's chapters as its
contents page prints them (Reprint 2026-27).

The file had lived only on one machine, and as the textbook build wrote it:
1 to 7 chapters of books with 9 to 26, the chapters someone had transcribed.
A seeded class 1-5 school got every subject skipped (no file) or would have got
a fraction of each book (that file).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

from academicos.syllabus import cbse_syllabus  # noqa: E402
from test_curriculum_seed_grades import _bearer, _seed, client, principal  # noqa: E402,F401

BOOKS = ROOT / "academicos-data" / "syllabus" / "ncert_books.json"

# Numbered lessons on each book's contents page (a starred read-only piece is not one).
PRINTED = {
    "English|1": 9, "English|2": 13, "English|3": 12, "English|4": 12, "English|5": 10,
    "Hindi|1": 19, "Hindi|2": 26, "Hindi|3": 18, "Hindi|4": 13, "Hindi|5": 12,
    "Mathematics|1": 13, "Mathematics|2": 11, "Mathematics|3": 14, "Mathematics|4": 14, "Mathematics|5": 15,
    "EVS|3": 12, "EVS|4": 10, "EVS|5": 10,
}


@pytest.fixture
def listed():
    cbse_syllabus._ncert_books.cache_clear()
    cbse_syllabus.load_syllabus.cache_clear()
    yield json.loads(BOOKS.read_text(encoding="utf-8"))["classes"]
    cbse_syllabus._ncert_books.cache_clear()
    cbse_syllabus.load_syllabus.cache_clear()


def test_every_class_1_to_5_book_is_listed_whole(listed):
    assert {k: len(v["chapters"]) for k, v in listed.items() if int(k.split("|")[1]) <= 5} == PRINTED
    for key, book in listed.items():
        chapters = book["chapters"]
        assert [c["number"] for c in chapters] == list(range(1, len(chapters) + 1)), key
        assert len({c["id"] for c in chapters}) == len(chapters), key
        assert all(c["name"].strip() and c["bookTitle"] for c in chapters), key
    assert [c["name"] for c in listed["Mathematics|1"]["chapters"]][:3] == [
        "Finding the Furry Cat!", "What is Long? What is Round?", "Mango Treat"]
    assert listed["Hindi|2"]["chapters"][-1]["name"] == "बादल"


def test_classes_6_to_9_are_not_listed_from_a_partial_build(listed):
    """A class whose syllabus file has units and no chapters seeds the book's
    chapters (D118): a partial list there would seed a fraction of the book."""
    assert all(int(k.split("|")[1]) <= 5 for k in listed)


def test_no_class_1_to_5_subject_is_missing(listed):
    for grade in range(1, 6):
        assert cbse_syllabus.get_missing_subjects_for_grade(grade) == [], grade
        doc = cbse_syllabus.load_syllabus("Mathematics", grade)
        assert doc is not None and len(doc.chapters) == PRINTED[f"Mathematics|{grade}"]


@pytest.mark.parametrize("grade", [1, 3, 5])
def test_a_primary_class_seeds_every_subject_and_chapter(client, principal, listed, grade):  # noqa: F811
    r = _seed(client, _bearer(principal), grade)
    assert r.status_code == 200, r.text
    body = r.json()
    subjects = [k for k in PRINTED if k.endswith(f"|{grade}")]
    assert body["subjectsSkipped"] == []
    assert body["subjectsSeeded"] == len(subjects)
    assert body["chaptersSeeded"] == sum(PRINTED[k] for k in subjects)


def test_a_rebuild_adds_topics_and_never_drops_a_listed_chapter():
    import build_textbook_bank as build
    listed = {"EVS|3": {"chapters": [
        {"id": "evs-3/family-and-friends", "name": "Family and Friends", "book": "ceev1", "number": 1, "topics": []},
        {"id": "evs-3/going-to-the-mela", "name": "Going to the Mela", "book": "ceev1", "number": 2, "topics": []},
    ]}}
    built = {"EVS|3": [{"id": "evs-3/family-friends", "name": "Family & Friends", "book": "ceev1", "number": 1,
                        "topics": [{"id": "t1", "title": "Playing Together"}]}],
             "Science|6": [{"id": "science-6/x", "name": "X", "book": "fecu1", "number": 1, "topics": []}]}
    merged = build.merge_books(listed, built)
    evs = merged["EVS|3"]["chapters"]
    assert [c["number"] for c in evs] == [1, 2]
    # The listed name and id stay (a school may have seeded it); the build's topics are taken.
    assert (evs[0]["id"], evs[0]["name"]) == ("evs-3/family-and-friends", "Family and Friends")
    assert evs[0]["topics"] == [{"id": "t1", "title": "Playing Together"}]
    assert merged["Science|6"]["chapters"][0]["id"] == "science-6/x"


def test_a_class_3_school_gets_a_dated_plan_for_every_evs_chapter(tmp_path, monkeypatch, listed):
    """Classes 1-5 seeded chapters and nothing below them: no topic was
    proposed ("a separate decision") and timing refused a book with no marks
    ("seed real Unit.marks first"), so no plan could be made. Each chapter is
    now proposed whole and the year's periods are shared evenly."""
    from _auth_helpers import register_invited
    from test_assessment_routes_auth import _boot_client, _register
    from test_web_school_setup import BASE, PRINCIPAL_KEY, _session

    with _boot_client(tmp_path, monkeypatch) as client:
        principal = _register(client, "school_1", "head@school1.test", "Head", principal_key=PRINCIPAL_KEY)
        auth = {"Authorization": f"Bearer {principal['token']}"}
        from academicos.curriculum.routes import _school_today
        label, start, end = _session(_school_today())
        seeded = client.post(f"{BASE}/seed/cbse", headers=auth, json={
            "grade": 3, "academicYearLabel": label, "startDate": start, "endDate": end}).json()
        evs = next(t for t in seeded["topicTemplates"] if t["subject"] == "EVS")
        assert (evs["chaptersWithTopics"], evs["topicsProposed"], evs["subtopicsProposed"]) == (12, 12, 12)
        assert evs["provenance"] == ["template:ncert-book-chapter"]

        year = client.get(f"{BASE}/academic-years", params={"school_id": "school_1"}, headers=auth).json()[0]["id"]
        client.post(f"{BASE}/academic-years/{year}/calendar", headers=auth,
                    json={"weeklyOffDays": ["sunday"], "alternateSaturdayRule": "none"})
        slots = [{"start": f"{8 + i:02d}:00", "end": f"{8 + i:02d}:40"} for i in range(6)]
        client.post(f"{BASE}/academic-years/{year}/bell-schedules", headers=auth, json={"name": "Main", "slots": slots})
        grade = client.get(f"{BASE}/academic-years/{year}/grades", headers=auth).json()[0]["id"]
        section = client.get(f"{BASE}/academic-years/{year}/sections", headers=auth).json()[0]["id"]
        subject = next(s["id"] for s in client.get(f"{BASE}/grades/{grade}/subjects", headers=auth).json()
                       if s["name"] == "EVS")
        teacher = register_invited(client, "school_1", "asha@school1.test", name="Asha", role="teacher")["user"]["id"]
        r = client.put(f"{BASE}/sections/{section}/allocations/{subject}", headers=auth,
                       json={"teacherId": teacher, "periodsPerWeek": 5})
        assert r.status_code == 200, r.text

        # The year began in April; a school joining mid-year fits the book into the periods left (D35).
        built = client.post(f"{BASE}/academic-years/{year}/lesson-plans", headers=auth,
                            json={"approveProposedTopics": True, "fitToPeriodsLeft": True}).json()
        assert built["notPlanned"] == [], built
        plan = built["plans"][0]
        assert plan["subjectName"] == "EVS" and plan["chaptersWithoutSubtopics"] == []
        assert plan["lessonsCreated"] > 100 and plan["subtopicsWithoutEstimate"] == 0, plan

        book = client.get(f"{BASE}/subjects/{subject}/selected-book", headers=auth).json()["id"]
        lessons = client.get(f"{BASE}/books/{book}/schedule", headers=auth,
                             params={"academic_year_id": year, "sectionId": section}).json()
        dated = {l["subtopicId"] for l in lessons}
        assert len(dated) == 12, "every chapter has days"
        per = {}
        for l in lessons:
            per[l["subtopicId"]] = per.get(l["subtopicId"], 0) + 1
        assert max(per.values()) - min(per.values()) <= 1, "the periods are shared evenly"
