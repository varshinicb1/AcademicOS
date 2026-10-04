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
