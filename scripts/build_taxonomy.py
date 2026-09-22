"""Build the board-level chapter -> topic -> subtopic trees, classes 6-10.

One tree per subject and class, from the section headings of the NCERT
textbooks the schools teach from in 2026-27 (``ncert-dataset/textbooks``):
the new books for classes 6-8 and the new class 9 books on disk, the current
books for class 10. Headings are read by `academicos.syllabus.textbook_headings`
-- typography and numbering only, no model.

Outputs, under ``academicos-data/syllabus/taxonomy/``:

  <Subject>_<grade>.json   the tree: {subject, grade, book, source_files,
                           chapters: [{id, name, number, topics: [{id, name,
                           page, subtopics: [{id, name, page}]}]}]}. Ids are
                           slugs "subject-grade/chapter/topic/subtopic"
                           ("science-7/..."), unique across every tree, so a
                           class 7 and a class 8 question never share a tag,
                           and a tag survives a rebuild as long as the book's
                           heading does.
  _manifest.json           counts per tree, every chapter with no topics and
                           why, the page offsets found, the measured precision
                           and recall against ``_hand_checked.json``, and every
                           chapter-list mismatch between the existing syllabus
                           files and the books, with the list the book gives.

English and Hindi are chapter-level only: their chapters are lessons and
poems, which have no section headings to make topics of.

Run:  python scripts/build_taxonomy.py [--check] [--root DIR] [--cache DIR]

``--check`` prints the counts and the precision without writing. ``--cache``
keeps each PDF's rebuilt lines as JSON (keyed by file size, mtime and the
reading code), so a rerun does not re-read 1 GB of PDF.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import inspect
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from academicos.corpus import ncert_exemplar as ex  # noqa: E402
from academicos.syllabus import textbook_headings as th  # noqa: E402

DEFAULT_ROOT = REPO.parent / "ncert-dataset" / "textbooks"
OUT_DIR = REPO / "academicos-data" / "syllabus" / "taxonomy"
SYLLABUS = REPO / "academicos-data" / "syllabus"
HAND_CHECKED = OUT_DIR / "_hand_checked.json"


@dataclass(frozen=True)
class Source:
    """One book, or one part of a book, as it sits on disk."""
    book: str
    path: str                        # a PDF (whole book) or a folder of chapter PDFs
    contents: tuple[int, ...] = ()   # contents pages of a whole book
    part: int | None = None
    strand: str | None = None        # "History", ... for Class 10 Social Science
    # Titles the text layer does not carry, typed from the printed opening
    # page and checked against the CBSE 2025-26 course structure: jemh1 sets
    # them in split small capitals ("R" 28pt + "EAL" 19.6pt), jess1 and jess2
    # draw them, and jess3 opens three chapters on a section page.
    typed_titles: tuple[tuple[int, str], ...] = ()
    # The book's heading type, where the automatic size ranking misreads it
    # (see th.HeadingStyle), and the pages that are not the chapter's text.
    styles: tuple | None = None
    skip_first_page: bool = False
    # Why chapters of this book yield no topics, when that is known from the
    # page rather than from a count.
    no_topics_note: str | None = None
    # Names set in the book's heading type that head a story or case, not a
    # section, dropped by exact name (after th._clean).
    story_titles: frozenset = frozenset()


TREES: dict[tuple[str, int], list[Source]] = {
    ("Mathematics", 6): [Source("Ganita Prakash", "maths/class6_ganita_prakash.pdf", (19,))],
    # The class 7 PDF carries both parts; part 2 is read from its chapter
    # files, part 1 from the book up to its "Learning Material Sheets".
    ("Mathematics", 7): [Source("Ganita Prakash Part 1", "maths/class7_ganita_prakash.pdf", (17,), 1),
                         Source("Ganita Prakash Part 2", "chapters/gegp2", (), 2)],
    ("Mathematics", 8): [Source("Ganita Prakash Part 1", "maths/class8_ganita_prakash.pdf", (15,), 1),
                         Source("Ganita Prakash Part 2", "chapters/hegp2", (), 2)],
    ("Mathematics", 9): [Source("Ganita Manjari", "maths/class9_ganita_manjari.pdf", (19,))],
    ("Mathematics", 10): [Source("Mathematics", "chapters/jemh1", typed_titles=(
        (1, "Real Numbers"), (2, "Polynomials"), (3, "Pair of Linear Equations in Two Variables"),
        (4, "Quadratic Equations"), (5, "Arithmetic Progressions"), (6, "Triangles"),
        (7, "Coordinate Geometry"), (8, "Introduction to Trigonometry"),
        (9, "Some Applications of Trigonometry"), (10, "Circles"),
        (11, "Areas Related to Circles"), (12, "Surface Areas and Volumes"),
        (13, "Statistics"), (14, "Probability")))],
    ("Science", 6): [Source("Curiosity", "science/class6_curiosity.pdf", (17,))],
    ("Science", 7): [Source("Curiosity", "science/class7_curiosity.pdf", (19,))],
    ("Science", 8): [Source("Curiosity", "science/class8_curiosity.pdf", (19,))],
    ("Science", 9): [Source("Exploration", "science/class9_exploration.pdf", (19,))],
    ("Science", 10): [Source("Science", "chapters/jesc1")],
    ("Social Science", 6): [Source("Exploring Society: India and Beyond", "chapters/fees1")],
    ("Social Science", 7): [Source("Exploring Society: India and Beyond Part 1", "chapters/gees1", (), 1),
                            Source("Exploring Society: India and Beyond Part 2", "chapters/gees2", (), 2)],
    # A class election told as a story in the 15pt sub-section type, with its
    # own 14pt parts "Campaigning", "Voting day", "The results" (hees105.pdf
    # pp7-9): an illustration under "Bridging Barriers...", not a section.
    ("Social Science", 8): [Source("Exploring Society: India and Beyond Part 1", "chapters/hees1", (), 1,
                                   story_titles=frozenset({
                                       "Election for class representative — Grade 8, Suryodaya School"})),
                            Source("Exploring Society: India and Beyond Part 2", "chapters/hees2", (), 2)],
    ("Social Science", 9): [Source("Understanding Society: India and Beyond Part 1",
                                   "social_science/class9_understanding_society_part1.pdf", (23,), 1)],
    ("Social Science", 10): [
        Source("India and the Contemporary World II", "chapters/jess3", strand="History", typed_titles=(
            (1, "The Rise of Nationalism in Europe"), (2, "Nationalism in India"),
            (3, "The Making of a Global World"), (4, "The Age of Industrialisation"),
            (5, "Print Culture and the Modern World"))),
        Source("Contemporary India II", "chapters/jess1", strand="Geography",
               no_topics_note=(
                   "Contemporary India II draws its section headings as graphics: the text "
                   "layer holds only a heading's initials (12pt 'R', 'P' at jess101.pdf p2 "
                   "y=568) or nothing, and no line of the chapter is set above 10.5pt; "
                   "no topic can be read without OCR."),
               typed_titles=(
            (1, "Resources and Development"), (2, "Forest and Wildlife Resources"),
            (3, "Water Resources"), (4, "Agriculture"), (5, "Minerals and Energy Resources"),
            (6, "Manufacturing Industries"), (7, "Lifelines of National Economy"))),
        Source("Democratic Politics II", "chapters/jess4", strand="Political Science"),
        Source("Understanding Economic Development", "chapters/jess2", strand="Economics",
               styles=(th.HeadingStyle(13.5, 14.5, white=True, caps=True),
                       th.HeadingStyle(17.5, 18.5)),
               skip_first_page=True,     # "Notes for the teacher"
               # Boxed stories set in the same 18pt type as the sub-sections:
               # two workers side by side (jess202.pdf p13) and a consumer's
               # case told in instalments (jess205.pdf pp6-7). Not "(1)
               # Festival Season" / "(2) Swapna's Problem" (jess203.pdf p6):
               # they are the two halves of "Two Different Credit Situations",
               # and were read as its subtopics in _hand_checked.json.
               story_titles=frozenset({"Kanta", "Kamal", "Reji’s Suffering", "Waiting..."}),
               typed_titles=((1, "Development"), (2, "Sectors of the Indian Economy"),
                             (3, "Money and Credit"), (4, "Globalisation and the Indian Economy"),
                             (5, "Consumer Rights")))],
    ("English", 6): [Source("Poorvi", "english/class6_poorvi.pdf", (15,))],
    ("English", 7): [Source("Poorvi", "english/class7_poorvi.pdf", (13,))],
    ("English", 8): [Source("Poorvi", "english/class8_poorvi.pdf", (15,))],
    ("English", 9): [Source("Kaveri", "english/class9_kaveri.pdf", (17,))],
    ("Hindi", 9): [Source("Ganga", "hindi/class9_ganga.pdf", (17,))],
}
CHAPTER_LEVEL_ONLY = {"English", "Hindi"}

# What the dataset does not hold, reported rather than silently absent.
NOT_ON_DISK = {
    ("English", 10): "no class 10 English textbook in ncert-dataset/textbooks",
    ("Hindi", 6): "no class 6 Hindi textbook (Malhar) in ncert-dataset/textbooks",
    ("Hindi", 7): "no class 7 Hindi textbook in ncert-dataset/textbooks",
    ("Hindi", 8): "no class 8 Hindi textbook in ncert-dataset/textbooks",
    ("Hindi", 10): "no class 10 Hindi textbook in ncert-dataset/textbooks",
}
# What CBSE's 2025-26 course structures (cbse-dataset/curriculum-2026/web_material/
# CurriculumMain26/Sec/*_Sec_2025-26.pdf) say about Class 10 chapters, read off
# the course-structure pages. Carried on the chapter as "cbse2025_26" so a paper
# builder can see that a chapter is project-only before it asks for questions.
CBSE_2025_26 = {
    ("Science", None, 8): "the course names it 'Heredity and Evolution'; the book prints 'Heredity'",
    ("Science", None, 10): "scattering of light 'excluding colour of the sun at sunrise and sunset'",
    ("Social Science", "History", 3): ("board examination covers subtopics 1 to 1.3 (Pre-modern "
                                       "World to Conquest, Disease and Trade); 2 to 4.4 are an "
                                       "interdisciplinary project"),
    ("Social Science", "History", 4): "assessed as part of Periodic Assessment only",
    ("Social Science", "Geography", 7): "only map pointing is evaluated in the board examination",
    ("Social Science", "Economics", 4): ("split between the board examination and an "
                                         "interdisciplinary project; the course structure lists "
                                         "which sections go where (Social_Science_Sec_2025-26.pdf "
                                         "p13) in an order the text layer does not keep -- check "
                                         "the page before relying on the split"),
    ("Social Science", "Economics", 5): "project work only",
}
CBSE_SCIENCE_NOTE = ("CBSE 2025-26: information in the NCERT book's boxes is not assessed in the "
                     "year-end examination (Science_Sec_2025-26.pdf, note for teachers)")

PARTIAL = {
    ("Social Science", 9): "only Part 1 of Understanding Society is on disk; Part 2's chapters are missing",
}


# --------------------------------------------------------------------------- #
# reading, cached
# --------------------------------------------------------------------------- #

def reader_key() -> str:
    """What the rebuilt lines depend on besides the PDF: the reading code and
    the PyMuPDF version."""
    h = hashlib.sha256()
    for fn in (th._is_bold, th._printed_near, th.lines_from_rawdict, th._join_pieces,
               th.read_lines):
        h.update(inspect.getsource(fn).encode())
    h.update(repr(th._BOLD_NAMES).encode())
    h.update(str(getattr(ex._pymupdf(), "VersionBind", "")).encode())
    return h.hexdigest()[:16]


def make_reader(cache: Path | None):
    key = reader_key()

    def read(path: Path) -> list[th.Line]:
        st = path.stat()
        slot = cache / f"{path.stem}.json" if cache else None
        if slot and slot.exists():
            data = json.loads(slot.read_text(encoding="utf-8"))
            if (data.get("size") == st.st_size and data.get("mtime") == int(st.st_mtime)
                    and data.get("reader") == key):
                return [th.Line.from_dict(d) for d in data["lines"]]
        lines = th.read_lines(path)
        if slot:
            slot.parent.mkdir(parents=True, exist_ok=True)
            slot.write_text(json.dumps({"size": st.st_size, "mtime": int(st.st_mtime),
                                        "reader": key,
                                        "lines": [ln.to_dict() for ln in lines]},
                                       ensure_ascii=False), encoding="utf-8")
        return lines
    return read


# --------------------------------------------------------------------------- #
# chapters
# --------------------------------------------------------------------------- #

@dataclass
class RawChapter:
    number: int
    name: str
    name_source: str       # contents | display | typed
    source_file: str
    first_page: int | None
    last_page: int | None
    lines: list
    printed_page: int | None = None


# Contents entries that are not lessons: back matter of the language books.
BACK_MATTER = re.compile(r"^(appendix|glossary|answer key|image credits|graph paper)\b", re.I)
LESSON_NO = re.compile(r"^(\d{1,2})\.\s+")


def _chapters_of_book(src: Source, lines: list, rel: str, problems: list,
                      chapter_level: bool) -> list[RawChapter]:
    entries = th.parse_contents(lines, list(src.contents))
    numbered = [e for e in entries if e.number is not None]
    if numbered:
        chapter_entries = numbered
        after = [e for e in entries if e.number is None
                 and e.printed_page > max(n.printed_page for n in numbered)]
    else:
        chapter_entries = [e for e in entries if not BACK_MATTER.match(e.title)]
        after = [e for e in entries if BACK_MATTER.match(e.title)]
    if chapter_level:
        # Lessons and poems: the name and printed page are what is needed; the
        # PDF page of a poem is not located reliably (its title is often set
        # in body-size type), so none is claimed.
        return [RawChapter(i + 1, LESSON_NO.sub("", e.title), "contents", rel, None, None, [],
                           e.printed_page) for i, e in enumerate(chapter_entries)]
    starts = th.locate_chapter_starts(lines, chapter_entries, max(src.contents))
    folios = th.printed_page_numbers(lines)
    last_pdf = max((ln.page for ln in lines), default=0)
    # the page before the first back-matter entry ("Learning Material Sheets")
    book_end = folios.get(after[0].printed_page - 1) if after else last_pdf
    missing = [e.title for e, (p, _) in zip(chapter_entries, starts) if p is None]
    if missing:
        problems.append({"file": rel, "problem": "chapter start page not found", "chapters": missing})
    out = []
    for i, e in enumerate(chapter_entries):
        number = e.number if e.number is not None else i + 1
        first, how = starts[i]
        last = None
        if first is not None:
            nxt = next((p for p, _ in starts[i + 1:] if p is not None), None)
            last = nxt - 1 if nxt else (book_end or last_pdf)
        body = [ln for ln in lines if first is not None and first <= ln.page <= last]
        out.append(RawChapter(number, e.title, "contents", rel, first, last, body))
    return out


def _chapters_of_folder(src: Source, folder: Path, read, root: Path) -> list[RawChapter]:
    typed = dict(src.typed_titles)
    out = []
    for pdf in sorted(folder.glob("*.pdf")):
        number = int(pdf.stem[-2:])
        lines = read(pdf)
        # fees101.pdf opens with the book's introduction; chapter 1 starts
        # where its 72pt numeral stands (p7).
        start = next((ln.page for ln in lines if ln.size >= 36 and ln.text.strip() == str(number)),
                     1)
        body = [ln for ln in lines if ln.page >= start]
        if number in typed:
            name, how = typed[number], "typed"
        else:
            name, how = th.display_title(lines, start), "display"
        out.append(RawChapter(number, name, how, pdf.relative_to(root).as_posix(), start,
                              max((ln.page for ln in lines), default=start), body))
    return out


def tree_prefix(subject: str, grade: int) -> str:
    """The first segment of every id in one tree: "social-science-7".

    Chapter slugs alone repeat across trees ("number-play" is a chapter of
    Mathematics 6, 7 and 8; "number-play/digits-in-disguise" a subtopic of
    both 7 and 8), so a tag on a class 7 question would also name class 8.
    """
    return f"{th.slug(subject)}-{grade}"


def _display_name(name: str) -> str:
    return th.title_case(name) if len(name) > 3 else name


def build_tree(subject: str, grade: int, sources: list[Source], root: Path, read,
               problems: list) -> dict:
    chapter_level = subject in CHAPTER_LEVEL_ONLY
    prefix = tree_prefix(subject, grade)
    chapters, used = [], set()
    files = []
    for src in sources:
        path = root / src.path
        if path.is_dir():
            raws = _chapters_of_folder(src, path, read, root)
            files += sorted({r.source_file for r in raws})
        else:
            rel = path.relative_to(root).as_posix()
            files.append(rel)
            raws = _chapters_of_book(src, read(path), rel, problems, chapter_level)
        for r in raws:
            cid = th._unique(f"{prefix}/{th.slug(r.name)}", used)
            ch = {"id": cid, "name": r.name, "number": r.number, "book": src.book}
            if src.part:
                ch["part"] = src.part
            if src.strand:
                ch["strand"] = src.strand
            ch["source_file"] = r.source_file
            if chapter_level:
                ch["printedPage"] = r.printed_page
            else:
                ch["pages"] = [r.first_page, r.last_page]
            ch["nameSource"] = r.name_source
            note = CBSE_2025_26.get((subject, src.strand, r.number)) if grade == 10 else None
            if note:
                ch["cbse2025_26"] = note
            if chapter_level:
                ch["headingKind"] = "chapter-level-only"
                ch["topics"] = []
            elif not r.lines:
                ch["headingKind"] = "none"
                ch["noTopicsReason"] = "chapter pages not located in the PDF"
                ch["topics"] = []
            else:
                skip = frozenset({r.first_page}) if src.skip_first_page else frozenset()
                heads, kind = th.chapter_headings(r.lines, r.number, skip, src.styles)
                heads = [h for h in heads if h.name not in src.story_titles]
                for h in heads:
                    h.name = _display_name(h.name)
                topics, orphans = th.build_topics(cid, heads)
                ch["headingKind"] = kind
                if orphans:
                    ch["orphanSubtopicsDropped"] = orphans
                if not topics:
                    ch["noTopicsReason"] = src.no_topics_note or _why_none(r.lines, kind)
                ch["topics"] = topics
            chapters.append(ch)
    books = list(dict.fromkeys(s.book for s in sources))
    tree = {"subject": subject, "grade": grade,
            "book": books[0] if len(books) == 1 else books,
            "source_files": files, "chapters": chapters}
    if (subject, grade) == ("Science", 10):
        tree["note"] = CBSE_SCIENCE_NOTE
    if chapter_level:
        tree["note"] = ("Chapter level only: the chapters are lessons and poems, "
                        "which carry no section headings to make topics of.")
    if subject == "Hindi":
        tree["nameWarning"] = (
            "Names are the PDF text layer's, which drops or displaces Devanagari "
            "conjuncts and matras (e.g. the contents' author column reads 'प्ेमचंद'); "
            "check a name against the printed page before showing it to a student.")
    return tree


def _why_none(lines: list, kind: str) -> str:
    body, font = th.body_style(lines)
    return (f"no numbered heading and no bold heading line >= {body + 1.5:g}pt "
            f"(body {body:g}pt {font}) outside boxes and activities")


# --------------------------------------------------------------------------- #
# measurement and comparison
# --------------------------------------------------------------------------- #

def _key(name: str) -> str:
    return re.sub(r"[^a-z0-9ऀ-ॿ]", "", th.slug(name)) if name else ""


def measure(trees: dict, gold: dict) -> dict:
    """Precision and recall of the extracted headings against hand-read ones."""
    by_file: dict[tuple[str, int], dict] = {}
    for t in trees.values():
        for ch in t["chapters"]:
            by_file[(ch["source_file"], ch["number"])] = ch
    rows, fam = [], collections.defaultdict(lambda: collections.Counter())
    for g in gold.get("chapters", []):
        ch = by_file.get((g["file"], g["chapter"]))
        # a subtopic counts only under the right topic
        got = set()
        if ch:
            for t in ch["topics"]:
                got.add(("", _key(t["name"])))
                got.update((_key(t["name"]), _key(s["name"])) for s in t["subtopics"])
        want = {(_key(h.get("parent", "")), _key(h["name"])) for h in g["headings"]}
        hit = got & want
        row = {"family": g["family"], "file": g["file"], "chapter": g["chapter"],
               "extracted": len(got), "handRead": len(want), "correct": len(hit),
               "precision": round(len(hit) / len(got), 3) if got else None,
               "recall": round(len(hit) / len(want), 3) if want else None,
               "wrong": sorted("/".join(k for k in pair if k) for pair in got - want),
               "missed": sorted("/".join(k for k in pair if k) for pair in want - got)}
        rows.append(row)
        for k in ("extracted", "handRead", "correct"):
            fam[g["family"]][k] += row[k]
            fam["all"][k] += row[k]
    summary = {f: {"precision": round(c["correct"] / c["extracted"], 3) if c["extracted"] else None,
                   "recall": round(c["correct"] / c["handRead"], 3) if c["handRead"] else None,
                   **c} for f, c in fam.items()}
    return {"byFamily": summary, "chapters": rows}


def compare_syllabus(tree: dict) -> dict | None:
    """Every chapter the syllabus file and the book disagree on."""
    path = SYLLABUS / f'{tree["subject"].replace(" ", "_")}_{tree["grade"]}.json'
    if not path.exists():
        return None
    syl = ex.load_syllabus(path)
    book = [(ch["number"], ch["name"]) for ch in tree["chapters"]]
    syl_keys = {ex._tokens(n): (cid, n) for cid, n in syl}
    book_keys = {ex._tokens(n): n for _, n in book}
    only_syl = [{"id": cid, "name": n} for cid, n in syl if ex._tokens(n) not in book_keys]
    only_book = [n for _, n in book if ex._tokens(n) not in syl_keys]
    # Mathematics_6.json files "Patterns in Mathematics" under the id
    # "knowing-our-numbers": an id sharing no word with its own name.
    id_name = [{"id": cid, "name": n} for cid, n in syl
               if not set(cid.split("-")) & set(th.slug(n).split("-"))]
    return {"syllabusFile": path.relative_to(REPO).as_posix(),
            "syllabusChapters": len(syl), "bookChapters": len(book),
            "matched": len(syl) - len(only_syl),
            "inSyllabusNotInBook": only_syl, "inBookNotInSyllabus": only_book,
            "idDisagreesWithName": id_name,
            "proposedChapterList": ([{"number": ch["number"], "name": ch["name"],
                                      "id": ch["id"], **({"part": ch["part"]} if "part" in ch else {}),
                                      **({"strand": ch["strand"]} if "strand" in ch else {})}
                                     for ch in tree["chapters"]]
                                    if (only_syl or only_book) else None)}


# --------------------------------------------------------------------------- #
# invariants: a tree that breaks one is not written
# --------------------------------------------------------------------------- #

def _num(n: str) -> tuple[int, ...]:
    return tuple(int(x) for x in n.split("."))


def invariant_errors(tree: dict) -> list[str]:
    """What must hold of every tree before it is written.

    - pages never go back: topic, its subtopics, the next topic, ... in the
      order the tree lists them (a topic sorted out of place shows here);
    - in a chapter with numbered headings, the numbers ascend, topics and
      the subtopics under each;
    - chapter numbers ascend within a part (Ganita Prakash 7 and 8 and
      Exploring Society 7 and 8 restart at 1 for Part 2) or strand (Class 10
      Social Science: History 1-5, Geography 1-7, ...), and no (part,
      strand, number) repeats: a book that restarts its numbering must say
      where, or two chapters answer to one number;
    - no topic or subtopic is a box label, panel or end matter
      (`th._not_a_topic`), and no unnumbered one is a line cut off
      mid-phrase (`th._dangling`). A numbered heading that ends that way is
      the book's own heading with its formula drawn rather than typed ("3.5.1
      The Proof of Irrationality of" + a drawn root 2, class9_ganita_manjari.pdf
      p73); it is kept and listed by `cut_short`.
    """
    errs = []
    where = f'{tree["subject"]}_{tree["grade"]}'
    # parts in their own order, strands in the order the tree lists them
    strands = list(dict.fromkeys(ch.get("strand") or "" for ch in tree["chapters"]))
    keyed = [(ch.get("part") or 0, strands.index(ch.get("strand") or ""), ch["number"])
             for ch in tree["chapters"]]
    if keyed != sorted(set(keyed)):
        errs.append(f"{where}: chapter numbers repeat or go back within a part/strand: "
                    f"{[ch['number'] for ch in tree['chapters']]}")
    for ch in tree["chapters"]:
        at = f'{where} ch{ch["number"]} ({ch["source_file"]})'
        seq = []
        for t in ch["topics"]:
            seq.append(t)
            seq.extend(t["subtopics"])
        pages = [h["page"] for h in seq]
        if pages != sorted(pages):
            errs.append(f"{at}: pages go back: {pages}")
        tnums = [_num(t["number"]) for t in ch["topics"] if t.get("number")]
        if tnums != sorted(set(tnums)):
            errs.append(f'{at}: topic numbers out of order: {[t.get("number") for t in ch["topics"]]}')
        for t in ch["topics"]:
            snums = [_num(s["number"]) for s in t["subtopics"] if s.get("number")]
            if snums != sorted(set(snums)):
                errs.append(f'{at}: subtopic numbers out of order under {t["name"]!r}')
        for h in seq:
            numbered = bool(h.get("number"))
            if th._not_a_topic(h["name"], numbered) or (th._dangling(h["name"]) and not numbered):
                errs.append(f'{at}: box label or fragment as a heading: {h["name"]!r} p{h["page"]}')
    return errs


def cut_short(tree: dict) -> list[dict]:
    """Numbered headings whose text layer ends mid-phrase (see invariant_errors)."""
    return [{"chapter": ch["number"], "number": h.get("number"), "name": h["name"],
             "page": h["page"], "file": ch["source_file"]}
            for ch in tree["chapters"] for t in ch["topics"] for h in [t, *t["subtopics"]]
            if h.get("number") and th._dangling(h["name"])]


def number_gaps(tree: dict) -> list[dict]:
    """Numbers missing from a numbered chapter's sequence ("5.3" between 5.2
    and 5.4): a heading the extractor did not read, reported, not guessed."""
    out = []
    for ch in tree["chapters"]:
        tops = [t for t in ch["topics"] if t.get("number")]
        if not tops:
            continue
        missing = []
        have = {_num(t["number"])[-1] for t in tops}
        first = tops[0]["number"]
        prefix = first.rsplit(".", 1)[0] + "." if "." in first else ""
        missing += [f"{prefix}{k}" for k in range(1, max(have) + 1) if k not in have]
        for t in tops:
            subs = {_num(s["number"])[-1] for s in t["subtopics"] if s.get("number")}
            if subs:
                missing += [f'{t["number"]}.{k}' for k in range(1, max(subs) + 1) if k not in subs]
        if missing:
            out.append({"number": ch["number"], "name": ch["name"], "file": ch["source_file"],
                        "missing": missing})
    return out


# --------------------------------------------------------------------------- #

def counts(tree: dict) -> dict:
    chs = tree["chapters"]
    return {"chapters": len(chs),
            "topics": sum(len(c["topics"]) for c in chs),
            "subtopics": sum(len(t["subtopics"]) for c in chs for t in c["topics"]),
            "headingKinds": dict(collections.Counter(c["headingKind"] for c in chs)),
            "chaptersWithoutTopics": [{"number": c["number"], "name": c["name"],
                                       "file": c["source_file"],
                                       "why": c.get("noTopicsReason", c["headingKind"])}
                                      for c in chs if not c["topics"]],
            "numberGaps": number_gaps(tree),
            "namesCutShort": cut_short(tree)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report only, write nothing")
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--cache", type=Path, default=None)
    args = ap.parse_args()
    if not args.root.exists():
        print(f"no textbooks at {args.root}", file=sys.stderr)
        return 1
    try:
        ex.require_verified_pymupdf()
    except RuntimeError as e:
        print(f"refusing to build: {e}", file=sys.stderr)
        return 2
    read = make_reader(args.cache)
    problems: list = []
    trees = {}
    for (subject, grade), sources in TREES.items():
        trees[(subject, grade)] = build_tree(subject, grade, sources, args.root, read, problems)

    gold = json.loads(HAND_CHECKED.read_text(encoding="utf-8")) if HAND_CHECKED.exists() else {}
    precision = measure(trees, gold)
    manifest = {
        "builtFrom": "ncert-dataset/textbooks (read-only), scripts/build_taxonomy.py",
        "pymupdf": ex.VERIFIED_PYMUPDF,
        "trees": {f"{s}_{g}": counts(t) for (s, g), t in sorted(trees.items())},
        "notOnDisk": {f"{s}_{g}": why for (s, g), why in NOT_ON_DISK.items()},
        "partial": {f"{s}_{g}": why for (s, g), why in PARTIAL.items()},
        "locatingProblems": problems,
        "precision": precision,
        "syllabusMismatches": {f"{s}_{g}": compare_syllabus(t)
                               for (s, g), t in sorted(trees.items())},
    }
    for name, c in manifest["trees"].items():
        print(f'{name:22s} chapters {c["chapters"]:3d}  topics {c["topics"]:4d}  '
              f'subtopics {c["subtopics"]:4d}  no-topics {len(c["chaptersWithoutTopics"]):2d}  '
              f'{c["headingKinds"]}')
    for fam, s in sorted(precision["byFamily"].items()):
        print(f"precision {fam:8s} {s['precision']}  recall {s['recall']}  "
              f"({s['correct']}/{s['extracted']} extracted, {s['correct']}/{s['handRead']} hand-read)")
    for p in problems:
        print("problem:", p)
    for name, c in manifest["trees"].items():
        for g in c["numberGaps"]:
            print(f'gap: {name} ch{g["number"]} ({g["file"]}): {", ".join(g["missing"])}')
    errors = [e for t in trees.values() for e in invariant_errors(t)]
    for e in errors:
        print("INVARIANT:", e, file=sys.stderr)
    if errors:
        print(f"refusing to write: {len(errors)} invariant violations", file=sys.stderr)
        return 3
    if args.check:
        return 0
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for (subject, grade), tree in trees.items():
        (OUT_DIR / f'{subject.replace(" ", "_")}_{grade}.json').write_text(
            json.dumps(tree, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (OUT_DIR / "_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {len(trees)} trees to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
