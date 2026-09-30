"""The chapters a class studies now: its syllabus file's, and its current
NCERT book's (academicos-data/syllabus/ncert_books.json, written by
scripts/build_textbook_bank.py).

Without the book's chapters, every question taken from a class 9 book of the
2026-27 edition, and from a language book whose syllabus file lists CBSE
assessment units rather than chapters, was filed "unmapped". Classes 1-5
had no chapter list at all. The rule that keeps an older edition's slugs
unfiled is unchanged.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from academicos.api.main import app  # noqa: E402
from academicos.assessment import chapter_filing, pillar_routes, pool as pool_module  # noqa: E402
from academicos.corpus import textbook as tb  # noqa: E402
from academicos.syllabus import cbse_syllabus  # noqa: E402

EVS_3 = [
    {"id": "evs-3/family-and-friends", "name": "Family and Friends", "book": "ceev1",
     "bookTitle": "Our Wondrous World", "number": 1, "topics": [{"id": "T1", "title": "My family"}]},
    {"id": "evs-3/going-to-the-mela", "name": "Going to the Mela", "book": "ceev1",
     "bookTitle": "Our Wondrous World", "number": 2, "topics": []},
]
ENGLISH_9 = [
    {"id": "english-9/how-i-taught-my-grandmother-to-read", "name": "How I Taught My Grandmother to Read",
     "book": "iebe1", "bookTitle": "Kaveri", "number": 1, "topics": []},
]


@pytest.fixture
def books(monkeypatch):
    """The book chapters as the textbook build writes them, for EVS 3 (no
    syllabus file) and English 9 (a file listing CBSE units)."""
    data = {"EVS|3": {"chapters": EVS_3}, "English|9": {"chapters": ENGLISH_9}}
    monkeypatch.setattr(cbse_syllabus, "_ncert_books", lambda: data)
    cbse_syllabus.load_syllabus.cache_clear()
    yield data
    cbse_syllabus.load_syllabus.cache_clear()


def test_a_primary_class_takes_its_books_chapters_as_its_syllabus(books):
    doc = cbse_syllabus.load_syllabus("EVS", 3)
    assert doc is not None and doc.units == () and doc.total_marks == 0
    assert [c.id for _u, c in doc.all_chapters()] == ["evs-3/family-and-friends", "evs-3/going-to-the-mela"]
    assert doc.source == "NCERT Class 3 EVS: the book's own chapters (no CBSE marks table)"
    assert "EVS" in cbse_syllabus.get_available_subjects_for_grade(3)
    # Only EVS has a book here: the other three are reported missing, not hidden.
    assert cbse_syllabus.get_missing_subjects_for_grade(3) == ["English", "Hindi", "Mathematics"]


def test_primary_classes_expect_their_ncert_subjects():
    assert cbse_syllabus.EXPECTED_SUBJECTS_BY_GRADE[1] == ("English", "Hindi", "Mathematics")
    assert cbse_syllabus.EXPECTED_SUBJECTS_BY_GRADE[3] == ("English", "Hindi", "Mathematics", "EVS")


def test_a_current_book_chapter_is_filed_but_an_old_slug_is_not(books):
    filing = chapter_filing.ChapterFiling.for_class("English", 9)
    book_id = ENGLISH_9[0]["id"]
    assert filing.chapter_of(book_id, [book_id]) == book_id
    assert filing.chapter_of(None, ["beehive-the-fun-they-had"]) == chapter_filing.UNMAPPED
    # Where the syllabus names a chapter too, its own id still wins by name.
    assert filing.by_name[chapter_filing.name_key("How I Taught My Grandmother to Read")] == book_id


def test_the_picker_lists_a_primary_class_in_book_order(books, tmp_path, monkeypatch):
    from academicos.assessment import audit_log, users as users_mod
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr(audit_log, "_INSTANCE", None)
    monkeypatch.setattr(users_mod, "_INSTANCE", None)
    pool_module._CACHE.clear()
    try:
        with TestClient(app) as client:
            r = client.get("/api/v1/catalog/EVS/3/chapters")
            assert r.status_code == 200, r.text
            rows = [(e["chapterId"], e["chapterName"]) for e in r.json()]
            assert rows[:2] == [("evs-3/family-and-friends", "Family and Friends"),
                                ("evs-3/going-to-the-mela", "Going to the Mela")]
            # English 9: the file's units first, then the current book's chapter by its printed name.
            names = [e["chapterName"] for e in client.get("/api/v1/catalog/English/9/chapters").json()]
            assert "How I Taught My Grandmother to Read" in names
    finally:
        pool_module._CACHE.clear()


def test_textbook_records_carry_their_chapter_and_the_bank_subject():
    t = {"book": {"code": "ceev1", "class": 3, "subject": "The World Around Us", "title": "Our Wondrous World",
                  "language": "en"},
         "chapter": {"number": 2, "title": "Going to the Mela"},
         "topics": [{"id": "T1", "title": "At the mela"}],
         "questions": [{"ref": "G1", "origin": "generated", "topic": "T1", "type": "short_answer",
                        "stem": "Where did the children go?",
                        "answer": {"source": "grounded", "points": [
                            {"text": "To the mela.", "evidence": "The children went to the mela."}]}}]}
    b = tb.build(t, "Going to the Mela\nThe children went to the mela. It was a big fair.")
    assert len(b.records) == 1, b.refused
    r = b.records[0]
    assert r["subject"] == "EVS" and r["metadata"]["bookSubject"] == "The World Around Us"
    assert r["chapterIds"] == ["evs-3/going-to-the-mela"]
    assert (r["taxonomyChapterId"], r["tagMethod"]) == ("evs-3/going-to-the-mela", "source_chapter")


def test_a_hindi_chapter_id_keeps_its_script():
    assert tb.chapter_id("Hindi", 6, "मातृभूमि") == "hindi-6/मातृभूमि"
    assert tb.chapter_id("Hindi", 8, "स्वदेश") != tb.chapter_id("Hindi", 8, "मातृभूमि")


def test_the_build_files_a_chapter_under_the_syllabus_id_that_names_it():
    import build_textbook_bank as build
    # Social Science 6's file lists "Locating Places on the Earth" in a unit, under an id of its own.
    assert build.chapter_ref("Social Science", 6, "Locating Places on the Earth") == "locating-places-on-the-earth"
    assert build.chapter_ref("Social Science", 6, "A Chapter No File Names") == \
        "social-science-6/a-chapter-no-file-names"


def test_hindi_chapters_stay_distinct_and_never_become_a_catch_all(monkeypatch):
    """Both name keys dropped every non-ASCII letter, so every Devanagari
    chapter name was "": all Hindi chapters were one, and an unknown tag found
    a "twin" among them (review of #54)."""
    chapters = [{"id": "hindi-6/मातृभूमि", "name": "मातृभूमि", "bookTitle": "Malhar"},
                {"id": "hindi-6/गोल", "name": "गोल", "bookTitle": "Malhar"}]
    monkeypatch.setattr(cbse_syllabus, "_ncert_books", lambda: {"Hindi|6": {"chapters": chapters}})
    cbse_syllabus.load_syllabus.cache_clear()
    try:
        assert chapter_filing.name_key("मातृभूमि") != chapter_filing.name_key("गोल")
        assert chapter_filing.name_key("मातृभूमि") == pillar_routes._name_key("मातृभूमि")
        filing = chapter_filing.ChapterFiling.for_class("Hindi", 6)
        assert "" not in filing.by_name
        assert filing.chapter_of("hindi-6/गोल", []) == "hindi-6/गोल"
        # A tag the class does not know is not filed under a Hindi chapter.
        assert filing.chapter_of("some-old-tag", []) == chapter_filing.UNMAPPED
    finally:
        cbse_syllabus.load_syllabus.cache_clear()
