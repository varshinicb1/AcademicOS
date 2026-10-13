"""The book a class studies now: which units and chapters a school is seeded
with, and so which chapters the question bank's chapter view lists.

One decision, read by the seed (curriculum/seed_cbse10.py), the chapter view
(GET /catalog/{subject}/{grade}/chapters) and the filter every paper,
homework and search draws through (assessment/chapter_filing.py). Until
2026-10-13 only the seed made it (in seed_cbse10.py) and the other two read
the syllabus file instead, so where #136 seeded the current book (English and Social Science
6-9) the plan's chapters were not the view's: 281 class 9 questions sat in
"Not yet matched to a chapter" and homework from today's lesson found none.
"""
from __future__ import annotations

import json
import re
from typing import Optional

from . import cbse_syllabus
from .cbse_syllabus import (SyllabusChapter, SyllabusDocument, SyllabusUnit, _slug, book_chapters,
                            load_syllabus, taxonomy_chapters)

# Audit D118. Mathematics 6-10 and Science 7-9 list their CBSE units (with
# the marks) and, separately, the book's own chapters -- not which chapter
# is in which unit. Each unit used to be seeded as its own only chapter, so
# those classes had chapters no textbook prints and no topic source could
# key onto. The book's chapters are seeded now, under the unit the CBSE
# course structure puts them in where it says so: an explicit map below, or
# a chapter named exactly as a unit. Where the course structure does not
# place every chapter (the NCF-SE books of classes 6-9, whose units are not
# a CBSE chapter list), the whole book goes under one unit carrying the
# subject's marks.
#
# Class X Mathematics: the CBSE 2025-26 course structure
# (Maths_Sec_2025-26.pdf), Units I-VII.
_CHAPTER_UNITS: dict[tuple[str, int], dict[str, str]] = {
    ("Mathematics", 10): {
        "mathematics-10/real-numbers": "I",
        "mathematics-10/polynomials": "II",
        "mathematics-10/pair-of-linear-equations-in-two-variables": "II",
        "mathematics-10/quadratic-equations": "II",
        "mathematics-10/arithmetic-progressions": "II",
        "mathematics-10/coordinate-geometry": "III",
        "mathematics-10/triangles": "IV",
        "mathematics-10/circles": "IV",
        "mathematics-10/introduction-to-trigonometry": "V",
        "mathematics-10/some-applications-of-trigonometry": "V",
        "mathematics-10/areas-related-to-circles": "VI",
        "mathematics-10/surface-areas-and-volumes": "VI",
        "mathematics-10/statistics": "VII",
        "mathematics-10/probability": "VII",
    },
}
# The one unit a book's chapters go under when the units cannot hold them
# (the same number and naming as the classes 1-5 holder unit).
BOOK_UNIT_NO = "1"


def _book_unit(subject: str, marks: int, chapters) -> SyllabusUnit:
    """The one unit holding a whole book. It is not a CBSE unit, and the
    chapter view shows its chapters with no unit (studied_chapters)."""
    return SyllabusUnit(unit_no=BOOK_UNIT_NO, name=f"{subject} chapters", marks=marks, chapters=tuple(chapters))


def _is_book_unit(unit: SyllabusUnit, subject: str) -> bool:
    return unit.unit_no == BOOK_UNIT_NO and unit.name == f"{subject} chapters"


def _name_key(text: str) -> str:
    return " ".join("".join(ch if ch.isalnum() else " " for ch in text.lower()).split())


def book_chapters_for(subject: str, grade: int, doc: SyllabusDocument) -> list[SyllabusChapter]:
    """The book's own chapters in book order: the whole book as its contents
    page prints it (ncert_books.json: every class 1-5 book, and Hindi 6-9,
    whose contents trees are missing or garbled), else the taxonomy file (the
    textbook's contents pages), else the syllabus file's top-level list."""
    listed = book_chapters(subject, grade)
    if listed:
        return [SyllabusChapter(id=c["id"], name=c["name"]) for c in listed]
    contents = taxonomy_chapters(subject, grade)
    if contents:
        return [SyllabusChapter(id=cid, name=name) for cid, name in contents.items()]
    return list(doc.chapters)


def units_holding_book_chapters(subject: str, grade: int, doc: SyllabusDocument,
                                chapters: list[SyllabusChapter]) -> list[SyllabusUnit]:
    """The units to seed for a syllabus whose units list no chapters, with
    the book's chapters placed in them (D118). Every chapter goes under its
    CBSE unit when the explicit map or an exact unit name places it; if any
    chapter is left over, the whole book goes under one unit instead, so
    no chapter is put in a unit by a guess."""
    explicit = _CHAPTER_UNITS.get((subject, grade), {})
    by_no = {u.unit_no: u for u in doc.units}
    by_name = {_name_key(u.name): u for u in doc.units}
    placed: dict[str, list[SyllabusChapter]] = {u.unit_no: [] for u in doc.units}
    for c in chapters:
        unit = by_no.get(explicit.get(c.id, "")) or by_name.get(_name_key(c.name))
        if unit is None:
            marks = sum(u.marks for u in doc.units) or doc.total_marks
            return [_book_unit(subject, marks, chapters)]
        placed[unit.unit_no].append(c)
    return [SyllabusUnit(unit_no=u.unit_no, name=u.name, marks=u.marks, chapters=tuple(placed[u.unit_no]))
            for u in doc.units]


# The unit of a language syllabus that is the textbook ("Poorvi Textbook",
# "Literature", "Pathyapustak Vasant"); its other units are skills (reading,
# grammar, writing) taught from no book chapter.
_TEXTBOOK_UNIT = re.compile(r"textbook|literature|pathyapustak", re.IGNORECASE)
LANGUAGES = ("English", "Hindi")


def _book_title(subject: str, grade: int) -> Optional[str]:
    listed = book_chapters(subject, grade)
    if listed:
        # Every book the class reads from, in book order: class 10 English is First Flight and
        # Footprints without Feet, and naming only the first misnamed the other's lessons.
        titles = list(dict.fromkeys(c.get("bookTitle") for c in listed if c.get("bookTitle")))
        return " and ".join(titles) or None
    path = cbse_syllabus._DATA_DIR / "taxonomy" / f"{subject.strip().replace(' ', '_')}_{grade}.json"
    return json.loads(path.read_text(encoding="utf-8")).get("book") if path.exists() else None


def units_with_the_current_book(subject: str, grade: int, doc: SyllabusDocument,
                                book: list[SyllabusChapter]) -> Optional[list[SyllabusUnit]]:
    """The units to seed when the syllabus file's chapters are not the book a
    school teaches from now, or None when they are.

    Measured 2026-10-04: Social Science 7-9 seeded 0 chapters of the current
    book (Our Pasts, not Exploring Society), Social Science 6 missed 4 of its
    14, and English and Hindi 6-9 seeded only skill headings ("Reading
    Comprehension", "Vasant Bhag 2 (Kavita evam Kahani)"), no lesson at all.

    A language keeps its skill units and its textbook unit holds the book's
    lessons, named after the book; any other subject takes the book's
    chapters the way D118 does (units_holding_book_chapters)."""
    listed = [c for u in doc.units for c in u.chapters]
    if not book or not listed:
        return None
    if {_name_key(c.name) for c in listed} >= {_name_key(c.name) for c in book}:
        return None
    if subject in LANGUAGES:
        holders = [u for u in doc.units if _TEXTBOOK_UNIT.search(u.name)]
        if len(holders) != 1:
            return None
        title = _book_title(subject, grade)
        return [SyllabusUnit(unit_no=u.unit_no, marks=u.marks,
                             name=(f"Textbook: {title}" if title else u.name) if u is holders[0] else u.name,
                             chapters=tuple(book) if u is holders[0] else u.chapters)
                for u in doc.units]
    return units_holding_book_chapters(subject, grade, doc, book)


def _current_book_units(subject: str, grade: int, doc: SyllabusDocument) -> Optional[list[SyllabusUnit]]:
    """The units the seed takes in place of the syllabus file's when the file
    lists another book than the one the class studies now (#136), else None.
    Never for a file with no units, or one whose units list no chapters (D118)."""
    if not doc.units or (doc.chapters and not any(u.chapters for u in doc.units)):
        return None
    return units_with_the_current_book(subject, grade, doc, book_chapters_for(subject, grade, doc))


def seeded_units(subject: str, grade: int, doc: SyllabusDocument) -> list[SyllabusUnit]:
    """The units a school is seeded with for one class and subject, each
    holding the chapters of the book the class studies now."""
    if not doc.units and doc.chapters:
        # No CBSE marks table (classes 1-5): the book's chapters, in book
        # order, under one unit that claims no marks.
        return [_book_unit(subject, 0, doc.chapters)]
    if doc.chapters and not any(u.chapters for u in doc.units):
        # D118: the book's own chapters, under their CBSE units where the
        # course structure places them (units_holding_book_chapters).
        return units_holding_book_chapters(subject, grade, doc, book_chapters_for(subject, grade, doc))
    return _current_book_units(subject, grade, doc) or list(doc.units)


def unit_chapters(unit: SyllabusUnit, doc: SyllabusDocument) -> list[SyllabusChapter]:
    """A seeded unit's chapters: its own list; none where the file lists the
    book's chapters at top level; else the unit stands in for its one chapter
    (a skill unit of a language: "Reading Comprehension")."""
    if unit.chapters:
        return list(unit.chapters)
    if doc.chapters:
        return []
    return [SyllabusChapter(id=_slug(unit.name), name=unit.name)]


def studied_chapters(subject: str, grade: int) -> list[tuple[Optional[SyllabusUnit], SyllabusChapter]]:
    """(unit, chapter) for every chapter the class studies now, in the order
    the chapter view lists them.

    Where the seed takes the current book in place of the syllabus file's
    chapters, those are the chapters. Elsewhere the file's own
    (`SyllabusDocument.all_chapters`) already are: measured 2026-10-13 on every
    class 1-10, they are the seeded chapters id for id (Mathematics 10 in book
    order rather than by CBSE unit). Then any chapter of the current NCERT book
    that neither lists. A chapter the CBSE marks table does not place in a unit
    has no unit, never the holder unit standing in for one."""
    doc = load_syllabus(subject, grade)
    if doc is None:
        return []
    chapters = doc.all_chapters()
    current = _current_book_units(subject, grade, doc)
    if current is not None:
        chapters = [(None if _is_book_unit(u, subject) else u, c) for u in current for c in unit_chapters(u, doc)]
    listed = {c.id for _u, c in chapters}
    return chapters + [(None, SyllabusChapter(id=c["id"], name=c["name"]))
                       for c in book_chapters(subject, grade) if c["id"] not in listed]
