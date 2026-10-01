"""Build the chapter -> topic trees for the primary classes, 1-5.

``scripts/build_taxonomy.py`` builds the classes 6-10 trees from the typography
of the NCERT PDFs in ``ncert-dataset/textbooks``. The primary books are not
there: they were read for the exercise bank and left as chapter text under
``bank-pipeline/chapters_text/<book>/<nn>.txt``, each chapter transcribed to
``bank-pipeline/transcriptions/textbook/<book>-<nn>.json``.

Those transcriptions already name what the tree needs, so this builder reads
them rather than the PDFs: the book (class, subject, title, language), the
chapter (number, title), and the chapter's topic headings. A heading carries
the line it starts with, which locates it in the chapter text and so gives its
printed page. Nothing here is inferred -- every id comes from the same
``chapter_id`` the exercise bank used, so a chapter in this tree is the chapter
a record already points at.

Outputs, under ``academicos-data/syllabus/taxonomy/``, in the same shape
``build_taxonomy.py`` writes::

  <Subject>_<grade>.json   {subject, grade, book, source_files, chapters}

so ``TopicTagger`` and ``merge_question_banks.py`` read 1-5 the way they read
6-10. Run ``scripts/build_taxonomy_text.py`` afterwards: the tagger's tokenizer
index does not know these chapters until it is rebuilt.

Run:  python scripts/build_taxonomy_primary.py [--check] [--transcriptions DIR]
                                               [--chapters-text DIR] [--out DIR]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from academicos.corpus import textbook as tb
from academicos.syllabus import textbook_headings as th

REPO = Path(__file__).resolve().parents[1]
# Where the pipeline leaves them; the worktree keeps neither, so both default
# off REPO.parent like build_taxonomy.py's --root does, and both are overridable.
DEFAULT_TRANSCRIPTIONS = REPO.parent / "bank-pipeline" / "transcriptions" / "textbook"
DEFAULT_CHAPTERS_TEXT = REPO.parent / "bank-pipeline" / "chapters_text"
DEFAULT_OUT = REPO / "academicos-data" / "syllabus" / "taxonomy"

# The primary classes this builder covers. EVS starts at class 3, which is
# where the books on disk start; a gap is left, not filled with a guess.
PRIMARY_GRADES = (1, 2, 3, 4, 5)

# How a chapter name and a heading reached us, for the audit fields the
# classes 6-10 trees carry.
NAME_SOURCE = "transcription-chapter-title"
HEADING_KIND = "transcribed-heading-anchor"
CHAPTER_TEXT = "transcribed-chapter-text"

PAGE_MARK = re.compile(r"\[page (\d+)\]")


def _norm(text: str) -> str:
    """Compare like with like: the book prints curly quotes, dashes and tick
    marks the transcription may have written as ASCII or dropped."""
    s = unicodedata.normalize("NFKC", str(text or ""))
    s = s.replace("\u2019", "'").replace("\u2018", "'")
    s = s.replace("\u201c", '"').replace("\u201d", '"')
    s = s.replace("\u2013", "-").replace("\u2014", "-")
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def _page_marks(text: str) -> list[tuple[int, int]]:
    """(offset, page) for every ``[page N]`` marker, in reading order."""
    return [(m.start(), int(m.group(1))) for m in PAGE_MARK.finditer(text)]


def _page_at(marks: list[tuple[int, int]], offset: int) -> int | None:
    """The page printed at ``offset``: the last marker at or before it."""
    page = None
    for start, number in marks:
        if start > offset:
            break
        page = number
    return page


def _find(norm_text: str, anchor: str) -> int:
    """Where ``anchor`` sits in the normalised chapter text, or -1. Falls back
    to the anchor's opening words, which survive a line the book broke oddly."""
    if not anchor:
        return -1
    pos = norm_text.find(anchor)
    if pos >= 0:
        return pos
    head = " ".join(anchor.split()[:6])
    return norm_text.find(head) if head else -1


def _chapter_text(chapters_text: Path, code: str, number: int) -> str | None:
    for name in (f"{int(number):02d}.txt", f"{number}.txt"):
        path = chapters_text / str(code) / name
        if path.is_file():
            return path.read_text(encoding="utf-8", errors="replace")
    return None


def collect(transcriptions: Path, chapters_text: Path) -> tuple[dict, list[dict]]:
    """The tree per (subject, grade) and what could not be read."""
    books: dict[tuple[str, int], list[dict]] = defaultdict(list)
    problems: list[dict] = []

    for path in sorted(transcriptions.glob("*.json")):
        if path.name.endswith(".solve2.json"):
            continue  # the second model's answers, not a chapter
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            problems.append({"file": path.name, "problem": f"unreadable: {exc}"})
            continue
        book = doc.get("book") or {}
        grade = book.get("class")
        if not grade or int(grade) not in PRIMARY_GRADES:
            continue
        grade = int(grade)
        subject = tb.bank_subject(book.get("subject"))
        chapter = doc.get("chapter") or {}
        title = chapter.get("title")
        if not title:
            problems.append({"file": path.name, "problem": "no chapter title"})
            continue
        number = int(chapter.get("number") or 0)
        books[(subject, grade)].append(
            {"book": book, "chapter": chapter, "topics": doc.get("topics") or [],
             "file": path.name}
        )

    trees: dict[tuple[str, int], dict] = {}
    for (subject, grade), entries in books.items():
        entries.sort(key=lambda e: (int(e["chapter"].get("number") or 0),
                                    e["book"].get("code") or ""))
        used: set[str] = set()
        chapters: list[dict] = []
        seen_titles: set[str] = set()
        source_files: list[str] = []
        book_titles: list[str] = []

        for entry in entries:
            book, chapter = entry["book"], entry["chapter"]
            code = book.get("code") or ""
            title = chapter["title"]
            number = int(chapter.get("number") or 0)

            text = _chapter_text(chapters_text, code, number)
            if text is None:
                problems.append({"file": entry["file"],
                                 "problem": f"no chapter text for {code}/{number:02d}"})
                continue
            marks = _page_marks(text)
            norm_text = _norm(text)
            pages = [p for _, p in marks]
            rel = f"{chapters_text.name}/{code}/{number:02d}.txt"

            # The book's own chapter id, so this chapter is the one a record
            # already points at; _unique only fires on a genuine title clash.
            cid = th._unique(tb.chapter_id(subject, grade, title), used)
            if cid != tb.chapter_id(subject, grade, title):
                problems.append({"file": entry["file"],
                                 "problem": f"duplicate chapter title {title!r}"})
            if title.casefold() in seen_titles:
                problems.append({"file": entry["file"],
                                 "problem": f"chapter {title!r} already in this tree"})
            seen_titles.add(title.casefold())

            used_t: set[str] = set()
            topics: list[dict] = []
            last_page = 0
            for head in entry["topics"]:
                name = (head.get("title") or "").strip()
                if not name:
                    continue
                # The same filters the classes 6-10 builder applies. A primary
                # book's activity boxes and end matter print as headings, and a
                # tree that offers "Project Work" as a topic is offering a piece
                # of the furniture.
                if th._not_a_topic(name) or th._dangling(name):
                    problems.append({"file": entry["file"],
                                     "problem": f"not a topic: {name!r}"})
                    continue
                offset = _find(norm_text, _norm(head.get("startsWith")))
                page = _page_at(marks, offset) if offset >= 0 else None
                if page is None:
                    problems.append({"file": entry["file"],
                                     "problem": f"heading {name!r} not located in the text"})
                elif page < last_page:
                    # The transcription lists the headings in reading order, so a
                    # page before the one above it means the anchor matched the
                    # wrong place -- "Writing letters Q-Z" once resolved to page 2
                    # because its opening words also open an earlier activity. A
                    # wrong page is worse than a missing topic, and the audit
                    # cannot sort a page it does not have, so the heading goes.
                    problems.append({"file": entry["file"],
                                     "problem": f"heading {name!r} resolved to page "
                                                f"{page}, before the heading above it "
                                                f"(page {last_page})"})
                    continue
                if page is not None:
                    last_page = page
                topics.append({"id": th._unique(f"{cid}/{th.slug(name)}", used_t),
                               "name": name, "page": page,
                               # The tree schema carries a subtopic list on every
                               # topic, and `build_taxonomy.invariant_errors` walks
                               # it. The primary books' headings are one level
                               # deep, so this is empty rather than absent --
                               # omitting the key is a KeyError in the audit, not
                               # a shorter tree.
                               "subtopics": []})

            chapter_entry = {
                "id": cid, "name": title, "number": number,
                "book": book.get("title") or code,
                "source_file": rel,
                "pages": [min(pages), max(pages)] if pages else None,
                "nameSource": NAME_SOURCE,
                "headingKind": HEADING_KIND,
                "topics": topics,
            }
            if not topics:
                chapter_entry["noTopicsReason"] = "the transcription named no heading"
            if not pages:
                chapter_entry["pages"] = None
            chapters.append(chapter_entry)
            if book.get("title"):
                book_titles.append(book["title"])
            source_files.append(rel)

        if not chapters:
            continue
        titles = list(dict.fromkeys(book_titles))
        trees[(subject, grade)] = {
            "subject": subject, "grade": grade,
            "book": titles[0] if len(titles) == 1 else titles,
            "source_files": sorted(set(source_files)),
            "chapters": chapters,
        }
    return trees, problems


def _report(trees: dict, out: Path) -> None:
    print(f"{'file':<22} {'ch':>3} {'topics':>7} {'noPage':>7}")
    for (subject, grade), tree in sorted(trees.items()):
        chs = tree["chapters"]
        topics = [t for c in chs for t in c["topics"]]
        missing = sum(1 for t in topics if t.get("page") is None)
        print(f"{subject + '_' + str(grade) + '.json':<22} {len(chs):>3} "
              f"{len(topics):>7} {missing:>7}")
    total_ch = sum(len(t["chapters"]) for t in trees.values())
    total_tp = sum(len(c["topics"]) for t in trees.values() for c in t["chapters"])
    print(f"\n{len(trees)} trees, {total_ch} chapters, {total_tp} topics -> {out}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="print what would be written, and write nothing")
    ap.add_argument("--transcriptions", type=Path, default=DEFAULT_TRANSCRIPTIONS)
    ap.add_argument("--chapters-text", type=Path, default=DEFAULT_CHAPTERS_TEXT)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    if not args.transcriptions.is_dir():
        print(f"no transcriptions at {args.transcriptions}; pass --transcriptions")
        return 2

    trees, problems = collect(args.transcriptions, args.chapters_text)
    if not trees:
        print("no primary-class chapters found")
        return 2
    _report(trees, args.out)

    if problems:
        print(f"\n{len(problems)} problems:")
        for p in problems[:20]:
            print(f"   {p['file']}: {p['problem']}")
        if len(problems) > 20:
            print(f"   ... and {len(problems) - 20} more")

    if args.check:
        print("\n--check: nothing written")
        return 1 if problems else 0

    args.out.mkdir(parents=True, exist_ok=True)
    for (subject, grade), tree in trees.items():
        path = args.out / f"{subject}_{grade}.json"
        path.write_text(json.dumps(tree, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    print(f"wrote {len(trees)} trees to {args.out}")
    print("now run scripts/build_taxonomy_text.py so the tagger's tokenizer "
          "index knows these chapters")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
