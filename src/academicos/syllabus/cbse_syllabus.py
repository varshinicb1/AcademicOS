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

    def all_chapters(self) -> list[tuple[SyllabusUnit, SyllabusChapter]]:
        """Flattened (unit, chapter) pairs -- for subjects whose CBSE table
        has no sub-chapter list (e.g. Mathematics, English), each unit stands
        in for its own single chapter, since that's the finest breakdown
        CBSE's own document gives."""
        out: list[tuple[SyllabusUnit, SyllabusChapter]] = []
        for u in self.units:
            if u.chapters:
                for c in u.chapters:
                    out.append((u, c))
            else:
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
    )


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


# What a CBSE school should be able to set up for a grade -- DECLARED here, not
# derived from the files on disk.
#
# The distinction is the whole of PRD item 3 ("a grade with no syllabus file for
# a subject seeds the ones that do exist and REPORTS the ones that don't").
# Deriving the list from `list_available_syllabi()` makes "expected" and
# "present" the same set by construction, so nothing is ever reported missing
# and a genuinely absent subject just isn't there: measured 2026-09-23, seeding
# grade 11 returned subjects_skipped == [] while History_11.json,
# Geography_11.json and Political_Science_11.json do not exist and their
# grade-12 equivalents do.
#
# Grades 6-10 are the CBSE secondary core. Grades 11-12 list the electives this
# repo carries syllabus data for in either year; a school does not teach all of
# them, but a missing FILE for one is still a data gap worth naming rather than
# a curriculum choice this module can make on a school's behalf.
_SECONDARY_CORE = ("English", "Hindi", "Mathematics", "Science", "Social Science")
_SENIOR_SECONDARY = (
    "Accountancy", "Biology", "Business Studies", "Chemistry", "Economics",
    "English", "Geography", "Hindi", "History", "Mathematics", "Physics",
    "Political Science",
)
EXPECTED_SUBJECTS_BY_GRADE: dict[int, tuple[str, ...]] = {
    **{g: _SECONDARY_CORE for g in range(6, 11)},
    **{g: _SENIOR_SECONDARY for g in (11, 12)},
}


def get_expected_subjects_for_grade(grade: int) -> list[str]:
    """Every subject a seed for this grade should try, whether or not a file
    exists: the declared list, plus anything on disk that isn't in it (a new
    subject file should be seeded, not ignored because the list is older)."""
    return sorted(set(EXPECTED_SUBJECTS_BY_GRADE.get(grade, ()))
                  | set(get_available_subjects_for_grade(grade)))


def get_missing_subjects_for_grade(grade: int) -> list[str]:
    """Expected subjects with no syllabus file for this grade."""
    available = set(get_available_subjects_for_grade(grade))
    return sorted(s for s in EXPECTED_SUBJECTS_BY_GRADE.get(grade, ())
                  if s not in available)

