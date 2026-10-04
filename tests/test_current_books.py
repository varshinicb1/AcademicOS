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

from academicos.curriculum.seed_cbse10 import _name_key  # noqa: E402
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
