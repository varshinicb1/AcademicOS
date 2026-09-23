"""Give each class 6-10 Maths/Science syllabus file the chapters of the book
its class actually studies, under the ids the bank is tagged with.

Why
---
Two chapter vocabularies grew up separately and only one reached a teacher.
`chapterIds` on a record is an old-syllabus slug, a CBSE unit name or a CBE
content code; `taxonomyChapterId` is the chapter of the NCERT book the tagger
read (`academicos-data/syllabus/taxonomy/`), which commit 075c9ab raised to
2,289 of the 4,576 class 6-10 Mathematics/Science records. The catalog route
grouped by `chapterIds` alone, so none of those 2,289 tags was visible:
Mathematics 6 filed 69 of 446 served questions, Science 6 filed 8 of 247.

Reading the tag is not enough on its own, because for most classes the
syllabus file and the taxonomy describe DIFFERENT EDITIONS of the book, so no
id and no name is shared between them (measured 2026-09-23):

    Mathematics 7   taxonomy "Operations with Integers"  file "Integers"      0/15 names shared
    Mathematics 8   taxonomy "A Square and A Cube"       file "Squares and
                                                              Square Roots"   0/14
    Mathematics 9   taxonomy "The World of Numbers"      file "Number Systems" 0/8
    Science 7       taxonomy "Life Processes in Animals" file "Nutrition in
                                                              Animals"        0/12
    Science 8       taxonomy "The Invisible Living World" file old book       0/13
    Science 9       taxonomy "Cell: The Building Block
                              of Life"                   file "The Fundamental
                                                              Unit of Life"   0/13

and two files are wrong in their own way:

    Mathematics 6   the file carries the NEW book's chapter NAMES zipped
                    positionally onto the OLD book's chapter IDS -- id
                    "knowing-our-numbers" is named "Patterns in Mathematics"
                    and "integers-6" is named "Data Handling and
                    Presentation", 9 of its 11 rows. Eleven questions tagged
                    "basic-geometrical-ideas" were offered to a teacher under
                    a chapter titled "Fractions". It also lists an eleventh
                    chapter, "Ratio and Proportion", that Ganita Prakash does
                    not have.
    Mathematics 10  the file is CBSE's 7 marks-bearing UNITS with no chapter
                    list at all, so each unit stood in for a chapter; the book
                    has 14 chapters, and 319 records are tagged to them.

So for those eight pairs this writes the book's chapters into the file, at top
level, with the taxonomy's own ids -- one vocabulary for the tag and the pick.
The units keep their marks (official CBSE weightage for classes 9 and 10) and
lose their old-edition chapter lists; no chapter is assigned to a unit here,
because which chapter sits in which unit is not something these files record
and this script will not invent it.

Science 6 and Science 10 are left alone: their files already read the same
edition as the taxonomy, every taxonomy chapter matches one of their chapters
by name, and the catalog route bridges tag to chapter on that name. The script
asserts that, so a later taxonomy rebuild onto a new edition fails here loudly
instead of leaving a stale file behind.

Run
---
    python scripts/syllabus_chapters_from_taxonomy.py          # report only
    python scripts/syllabus_chapters_from_taxonomy.py --write
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "academicos-data" / "syllabus"
TAXONOMY = DATA / "taxonomy"

# Why each pair is treated the way it is -- see the module docstring. Spelt out
# rather than sniffed at runtime: a heuristic that decides "this file is the
# wrong edition" would one day decide it about a file that is right.
REWRITE = {
    ("Mathematics", 6): "new book's names on the old book's ids, zipped positionally",
    ("Mathematics", 7): "file lists the pre-2024 book; taxonomy read Ganita Prakash 7",
    ("Mathematics", 8): "file lists the pre-2024 book; taxonomy read Ganita Prakash 8",
    ("Mathematics", 9): "file lists the CBSE IX course structure; taxonomy read Ganita Manjari",
    ("Mathematics", 10): "file is 7 CBSE units with no chapter list; the book has 14 chapters",
    ("Science", 7): "file lists the pre-2024 book; taxonomy read Curiosity 7",
    ("Science", 8): "file lists the pre-2024 book; taxonomy read Curiosity 8",
    ("Science", 9): "file lists the CBSE IX course structure; taxonomy read Exploration",
}
KEEP = {
    ("Science", 6): "file and taxonomy both read Curiosity; all 12 names match",
    ("Science", 10): "file and taxonomy both read the current book; all 13 names match",
}


def norm(text: str) -> str:
    """A chapter name reduced to its letters and digits, so that an en dash, a
    colon or an ampersand cannot make two spellings of one chapter differ."""
    text = (text.replace("–", "-").replace("—", "-")
                .replace("’", "'").replace("…", ""))
    return re.sub(r"[^a-z0-9]", "", text.lower())


def file_chapters(doc: dict) -> list[tuple[str, str]]:
    out = [(c["id"], c["name"]) for u in doc["units"] for c in u.get("chapters", [])]
    out += [(c["id"], c["name"]) for c in doc.get("chapters", [])]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true",
                    help="write the files; without it, only report")
    args = ap.parse_args()

    changed = 0
    for (subject, grade), reason in sorted(REWRITE.items()) + sorted(KEEP.items()):
        sp = DATA / f"{subject.replace(' ', '_')}_{grade}.json"
        tp = TAXONOMY / f"{subject.replace(' ', '_')}_{grade}.json"
        if not sp.exists() or not tp.exists():
            print(f"!! {subject} {grade}: missing {'syllabus' if not sp.exists() else 'taxonomy'} file")
            return 2
        doc = json.loads(sp.read_text(encoding="utf-8"))
        book = json.loads(tp.read_text(encoding="utf-8"))["chapters"]

        if (subject, grade) in KEEP:
            have = {norm(n) for _i, n in file_chapters(doc)}
            missing = [c["name"] for c in book if norm(c["name"]) not in have]
            if missing:
                print(f"!! {subject} {grade} is on the KEEP list because its file and the "
                      f"taxonomy read one edition, but {len(missing)} taxonomy chapters no "
                      f"longer match a chapter of the file by name: {missing[:3]}")
                return 2
            print(f"   {subject} {grade}: kept as it is -- {reason}")
            continue

        before = file_chapters(doc)
        doc["chapters"] = [{"id": c["id"], "name": c["name"]} for c in book]
        for unit in doc["units"]:
            unit["chapters"] = []
        print(f" ~ {subject} {grade}: {len(before)} chapters -> {len(book)} from the book "
              f"({reason})")
        if args.write:
            sp.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")
            changed += 1

    print(f"\n{changed} file(s) written" if args.write else "\nreport only; pass --write")
    return 0


if __name__ == "__main__":
    sys.exit(main())
