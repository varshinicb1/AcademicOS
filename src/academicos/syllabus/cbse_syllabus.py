"""Real CBSE Class X syllabus: units, chapters, and official marks-weightage.

Data source: academicos-data/syllabus/*.json, hand-verified against the
official 2025-26 CBSE curriculum PDFs (cbseacademic.nic.in/curriculum_2026.html)
-- see each JSON's "source" field for the exact document and section (each
subject's PDF covers both Class IX and Class X; the Class X table was
extracted specifically, since the two years have different unit/chapter/marks
breakdowns).

CBSE gives marks-weightage per unit, not time/hours -- there is no official
"how many periods should this take" figure (the curriculum's own Section 3.3
explicitly leaves timetable design to individual schools). Anything in this
package that derives a suggested *time* budget (see timetable.py) is doing so
as a documented proportional estimate from marks-weightage, not quoting an
official number.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parents[3] / "academicos-data" / "syllabus"


@dataclass(frozen=True)
class SyllabusChapter:
    id: str
    name: str


@dataclass(frozen=True)
class SyllabusUnit:
    unit_no: str
    name: str
    marks: int
    chapters: tuple[SyllabusChapter, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class SyllabusDocument:
    subject: str
    grade: int
    total_marks: int
    source: str
    units: tuple[SyllabusUnit, ...]
    # The textbook's own chapters, for a class whose book does not divide into
    # the CBSE unit table this file records marks against. Read from the
    # file's top-level "chapters", and carrying the taxonomy's ids
    # ("mathematics-6/number-play") so that the id a question is tagged with
    # and the id a teacher picks are one vocabulary. Marks stay on the units:
    # CBSE weights a unit, and which chapter sits in which unit is not
    # something this file claims unless the file says so.
    chapters: tuple[SyllabusChapter, ...] = field(default_factory=tuple)

    def all_chapters(self) -> list[tuple[SyllabusUnit | None, SyllabusChapter]]:
        """Flattened (unit, chapter) pairs -- for subjects whose CBSE table
        has no sub-chapter list (e.g. Mathematics, English), each unit stands
        in for its own single chapter, since that's the finest breakdown
        CBSE's own document gives.

        Where the file lists the book's chapters at top level, those are the
        chapters, and a unit with no chapter list of its own does NOT also
        stand in for one: doing both would offer the same class two chapter
        lists from two different editions of its book.
        """
        out: list[tuple[SyllabusUnit | None, SyllabusChapter]] = []
        for c in self.chapters:
            out.append((None, c))
        for u in self.units:
            if u.chapters:
                for c in u.chapters:
                    out.append((u, c))
            elif not self.chapters:
                out.append((u, SyllabusChapter(id=_slug(u.name), name=u.name)))
        return out


def _slug(text: str) -> str:
    return "-".join(text.lower().replace("&", "and").split())[:60]


_FILENAME_BY_SUBJECT = {
    "Mathematics": "Mathematics_10.json",
    "Science": "Science_10.json",
    "Social Science": "Social_Science_10.json",
    "English": "English_10.json",
    "Hindi": "Hindi_10.json",
}


def _resolve_syllabus_file(subject: str, grade: int) -> Path | None:
    slug = subject.strip().replace(" ", "_")
    candidates = [
        f"{slug}_{grade}.json",
        f"{subject}_{grade}.json",
    ]
    if grade == 10:
        legacy = _FILENAME_BY_SUBJECT.get(subject)
        if legacy:
            candidates.append(legacy)
    for c in candidates:
        p = _DATA_DIR / c
        if p.exists():
            return p
    return None


@lru_cache(maxsize=None)
def load_syllabus(subject: str, grade: int) -> SyllabusDocument | None:
    path = _resolve_syllabus_file(subject, grade)
    if path is None or not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    units = tuple(
        SyllabusUnit(
            unit_no=u["unit_no"], name=u["name"], marks=u["marks"],
            chapters=tuple(SyllabusChapter(id=c["id"], name=c["name"]) for c in u.get("chapters", [])),
        )
        for u in data["units"]
    )
    return SyllabusDocument(
        subject=data["subject"], grade=data["grade"], total_marks=data["total_marks"],
        source=data["source"], units=units,
        chapters=tuple(SyllabusChapter(id=c["id"], name=c["name"])
                       for c in data.get("chapters", [])),
    )


@lru_cache(maxsize=None)
def taxonomy_chapters(subject: str, grade: int) -> dict[str, str]:
    """{taxonomy chapter id: the name the book prints it under}, or {}.

    The taxonomy trees are the textbooks' own contents pages and are what the
    tagger writes `taxonomyChapterId` from. A caller that has a tag and needs
    the syllabus chapter it belongs to matches on this name: where the
    syllabus file and the taxonomy read the same edition (Science 6, Science
    10) the names are the same words, and where they do not, no name matches
    and the caller is told so rather than guessing.
    """
    path = _DATA_DIR / "taxonomy" / f"{subject.strip().replace(' ', '_')}_{grade}.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {c["id"]: c["name"] for c in data.get("chapters", [])}


def list_available_syllabi() -> list[tuple[str, int]]:
    """Returns sorted list of (subject, grade) tuples available on disk."""
    out: list[tuple[str, int]] = []
    if not _DATA_DIR.exists():
        return out
    for f in _DATA_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if "subject" in data and "grade" in data:
                out.append((data["subject"], int(data["grade"])))
        except Exception:
            continue
    return sorted(set(out), key=lambda x: (x[1], x[0]))


def get_available_subjects_for_grade(grade: int) -> list[str]:
    """Returns available subject names for the requested grade."""
    return sorted([s for s, g in list_available_syllabi() if g == grade])

