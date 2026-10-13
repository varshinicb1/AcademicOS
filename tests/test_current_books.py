"""Classes 6-9 seed the books a school teaches from now (2026-27).

Measured 2026-10-04 on a seeded school:
- Social Science 7, 8 and 9 got 0 chapters of the current book: the syllabus
  files list Our Pasts, Our Environment and India and the Contemporary World,
  which Exploring Society and Understanding Society replaced. Social Science 6
  missed 4 of its 14.
- English and Hindi 6-9 got only skill headings ("Reading Comprehension",
  "Vasant Bhag 2 (Kavita evam Kahani)"): no lesson of Poorvi, Kaveri, Malhar or
  Ganga, so nothing to plan or mark taught.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from academicos.syllabus.current_book import _name_key  # noqa: E402
from academicos.syllabus.cbse_syllabus import taxonomy_chapters  # noqa: E402
from test_curriculum_seed_grades import _bearer, _seed, client, principal  # noqa: E402,F401


def _book_of(store, grade_id: str, subject: str):
    sub = next(s for s in store.subjects_for_grade(grade_id) if s.name == subject)
    return store.books_for_subject(sub.id)[0]


def test_class_7_seeds_the_current_books(client, principal):  # noqa: F811
    from academicos.curriculum import routes as curriculum_routes
    r = _seed(client, _bearer(principal), 7)
    assert r.status_code == 200, r.text
    body = r.json()
    store = curriculum_routes._require()

    # Social Science: Exploring Society Parts I and II, not Our Pasts.
    ss = [c.name for c in store.chapters_for_book(_book_of(store, body["gradeId"], "Social Science").id)]
    assert ss == list(taxonomy_chapters("Social Science", 7).values()) and len(ss) == 20
    assert "Kings and Kingdoms" not in ss

    # English: the skills stay, and the textbook unit holds Poorvi's 15 lessons.
    book = _book_of(store, body["gradeId"], "English")
    units = {u.name: [c.name for c in store.chapters_for_unit(u.id)] for u in store.units_for_book(book.id)}
    assert set(units) == {"Reading Comprehension", "Writing and Grammar", "Textbook: Poorvi"}
    assert units["Textbook: Poorvi"][:2] == ["The Day the River Spoke", "Try Again"]
    assert len(units["Textbook: Poorvi"]) == 15

    # Hindi: Malhar, not Vasant.
    book = _book_of(store, body["gradeId"], "Hindi")
    malhar = next(u for u in store.units_for_book(book.id) if u.name == "Textbook: Malhar")
    assert [c.name for c in store.chapters_for_unit(malhar.id)][:3] == ["माँ, कह एक कहानी", "तीन बुद्धिमान",
                                                                          "फूल और काँटा"]

    # Every lesson and skill row can be planned: each has a topic proposed.
    reports = {t["subject"]: t for t in body["topicTemplates"]}
    for subject in ("English", "Hindi"):
        assert reports[subject]["chaptersWithoutTopics"] == 0, reports[subject]
    assert "template:ncert-book-chapter" in reports["Hindi"]["provenance"]
    # Social Science is divided by its book's own sections.
    assert reports["Social Science"]["provenance"] == ["template:ncert-textbook-contents"]


def test_maths_and_science_are_unchanged(client, principal):  # noqa: F811
    """Their files already name the current books' chapters."""
    from academicos.curriculum import routes as curriculum_routes
    body = _seed(client, _bearer(principal), 6).json()
    store = curriculum_routes._require()
    for subject in ("Mathematics", "Science"):
        seeded = [c.name for c in store.chapters_for_book(_book_of(store, body["gradeId"], subject).id)]
        # The file and the book differ only in punctuation ("Nature's" and "Nature’s").
        assert [_name_key(n) for n in seeded] == [_name_key(n) for n in taxonomy_chapters(subject, 6).values()]


def test_every_chapter_a_school_is_seeded_with_is_one_the_question_bank_lists(tmp_path):
    """The seed took the current book for English and Social Science 6-9 (#136),
    but the bank's chapter view and the filter every paper and homework draws
    through kept reading the syllabus file. Measured 2026-10-13: 120 of the 132
    chapters those eight classes plan were chapters the bank did not know, so
    homework from a class 9 lesson found no question, and 281 class 9 questions
    sat in "Not yet matched to a chapter". One decision now
    (syllabus/current_book.py); this holds it on every class 1-10."""
    from academicos.assessment.chapter_filing import ChapterFiling
    from academicos.curriculum.decomposition_templates import chapter_slug
    from academicos.curriculum.seed_cbse10 import seed_cbse_grade
    from academicos.curriculum.store import CurriculumStore

    store = CurriculumStore(tmp_path / "curriculum.sqlite")
    unlisted: dict[str, list[str]] = {}
    planned = 0
    try:
        for grade in range(1, 11):
            result = seed_cbse_grade(store, school_id="school_1", academic_year_label="2026-27",
                                     start_date="2026-06-01", end_date="2027-03-31", grade_number=grade,
                                     apply_templates=False)
            for subject in store.subjects_for_grade(result.grade_id):
                known = ChapterFiling.for_class(subject.name, grade).known
                for book in store.books_for_subject(subject.id):
                    for chapter in store.chapters_for_book(book.id):
                        planned += 1
                        if chapter_slug(chapter) not in known:
                            unlisted.setdefault(f"{subject.name} {grade}", []).append(chapter.name)
    finally:
        store.close()
    assert planned > 500, f"only {planned} chapters seeded across classes 1-10: the check is vacuous"
    assert unlisted == {}, {k: (len(v), v[:2]) for k, v in unlisted.items()}


def test_class_10_english_and_hindi_seed_their_literature_books(client, principal):  # noqa: F811
    """Class 10 English and Hindi seeded only skill headings ("Language through Literature"), so a
    teacher had no lesson of First Flight, Footprints without Feet, Kshitij or Kritika to plan or mark
    taught. The books' contents pages are listed now (ncert_books.json, 2026-10-14)."""
    from academicos.curriculum import routes as curriculum_routes
    r = _seed(client, _bearer(principal), 10)
    assert r.status_code == 200, r.text
    body = r.json()
    store = curriculum_routes._require()

    book = _book_of(store, body["gradeId"], "English")
    units = {u.name: [c.name for c in store.chapters_for_unit(u.id)] for u in store.units_for_book(book.id)}
    lessons = units["Textbook: First Flight and Footprints without Feet"]
    assert len(lessons) == 18
    assert (lessons[0], lessons[9]) == ("A Letter to God", "A Triumph of Surgery")

    book = _book_of(store, body["gradeId"], "Hindi")
    units = {u.name: [c.name for c in store.chapters_for_unit(u.id)] for u in store.units_for_book(book.id)}
    lessons = units["Textbook: Kshitij Part 2 and Kritika Part 2"]
    assert len(lessons) == 15 and lessons[-1] == "मैं क्यों लिखता हूँ?"
