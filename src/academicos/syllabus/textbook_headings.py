"""Deterministic extraction of an NCERT textbook's own chapter and section
headings, straight from the PDFs with PyMuPDF.

This is source (b) of the decomposition templates (see
`scripts/export_decomposition_templates.py`). The syllabus JSONs stop at
chapter level, so a freshly seeded school has nothing below Chapter; the
textbooks themselves carry the missing level as printed headings -- "2.2 How to
Group Plants and Animals?", "2.2.1 How to group plants?" -- and those are the
book's own words, not a model's guess at them.

Why font metrics and not a regex over plain text: the same numeric shape occurs
constantly in body prose. Measured on class6_curiosity.pdf 2026-09-23, matching
`^\\d{1,2}(\\.\\d{1,2}){1,2}\\s+\\S` over the raw page lines returns 105 lines, of
which 33 carry a number that is no section of that book ("2.6 that the plants
and animals", "35.0 g", "10.4 cm-1.0 cm = 9.4 cm", "37.0 degC") and the rest
repeat the real headings. Every printed heading in that book is set in a BOLD
face at a size above the body size and no body line is, so adding "bold and
larger than body text" to the numbering rule takes the same book to 71
headings, each of which `tests/test_textbook_headings.py` finds printed
verbatim on the page this module reports, with its number immediately before
it.

Two heading styles, because NCERT prints two:

  * NUMBERED (Curiosity, Ganita Prakash, Exploration): "2.2", "2.2.1". The
    number gives the nesting, so nothing has to be inferred.
  * UNNUMBERED (the Class 6-8 Social Science books, which ship as one PDF per
    chapter): headings are distinguished only by their face and size. Those are
    read as SIZE TIERS, and only for a book that prints no numbered heading at
    all -- see `_tiers` for the two rules that keep a recurring box label
    ("LET'S EXPLORE", "Questions") from being mistaken for a section.

Deliberately no fuzzier fallback. A heading list scraped from the Contents page
or a similarity match on titles would put text under a heading it does not
belong to, which is worse for the principal reviewing the proposal than a
chapter that honestly reports having no breakdown.

Nothing here writes anything: it reads read-only PDFs and returns a tree.
`scripts/export_decomposition_templates.py` maps that tree onto syllabus
chapters and commits it.

    from academicos.syllabus.textbook_headings import extract_chapters
    for ch in extract_chapters(Path(".../textbooks/science/class6_curiosity.pdf")):
        print(ch.number, ch.name, [t.number for t in ch.topics])
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional, Sequence

# PyMuPDF's span flag bit for a bold face. Some NCERT titles are set in faces
# whose flag is not set but whose name says what they are ("NotoSans-SemiBold",
# "NotoSerif-ExtraBold"), so the name is checked too.
_FLAG_BOLD = 1 << 4
_BOLD_NAMES = ("bold", "black", "heavy", "semib", "extrab")

# "2.1", "2.2.1" -- at most three levels, because NCERT never prints a fourth
# and a longer run of dotted numbers in a textbook is a figure reference or a
# measurement, not a heading.
_NUMBERED = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){1,2})[\s \t.:)]+(\S.*)$")

# A chapter opener prints its number alone at display size beside the title.
_PURE_INT = re.compile(r"^\d{1,2}$")

# Both ratios are floors, not descriptions of a typical book, and both were too
# high until 2026-09-23. Measured across the books this repo actually reads:
# Curiosity 6 prints its numeral at 5.5x the body size, Exploration 9 at 5.9x,
# the Social Science chapter PDFs at 5.5x -- but Ganita Manjari 9 prints its at
# 22.6pt against an 11.0pt body (2.05x) and its titles at 16.0pt (1.45x). At
# 2.5x/1.5x that book yielded ONE chapter, its front cover, and none of its
# eight real chapters; Poorvi 6, Ganga 9 and Understanding Society 9 yielded
# nothing at all. The floors exist to keep a bold run-in from being read as a
# chapter opener, and 1.8x/1.4x still sits far above every heading size in
# these books; the opener rules below (one lone numeral on the page, a title in
# a single size class, nothing before chapter 1) are what actually does the
# separating.
_MIN_CHAPTER_NUMERAL_RATIO = 1.8   # x body size
_MIN_TITLE_RATIO = 1.4             # x body size
# A chapter title may be set in two sizes ("Health:" at 26pt over "The Ultimate
# Treasure" at 24pt, Curiosity 8) but not in three unrelated ones. Anything
# printed below this share of the largest title line on the opener page is
# furniture, not part of the name: Exploration 9's literal word "Chapter"
# (21.2pt against a 26pt title, 0.82) and the Social Science books' "Questions"
# box label (18pt against 30pt, 0.60) were both being folded into the title.
_MIN_HEADING_RATIO = 1.05          # x body size; headings sit just above body
_TITLE_SIZE_BAND = 0.9             # x the largest title line on the page
# A numbered line that is NOT bold is a heading only if it is set well clear of
# the body. Ganita Manjari 9 is the one book here that sets its sections
# unbolded -- "3.5 Irrational Numbers" is NotoSerif-Regular at 14pt over an
# 11pt body, while its SUBsections are NotoSerif-Bold at 12pt -- so the
# bold-only rule read its 27 subsections and none of its 53 sections, leaving
# every chapter with zero topics. Measured across the other five numbered books
# (Curiosity 6/7/8, Exploration 9, Ganita Prakash 6): not one line in any of
# them matches the numbering, clears the body size and is unbolded, so this
# branch admits nothing anywhere else.
_MIN_UNBOLD_HEADING_RATIO = 1.2    # x body size

# Unnumbered mode only (see `_tiers`).
_MIN_TIER_DISTINCT = 0.5           # share of occurrences that must be unique
_MIN_TIER_CHAPTER_SHARE = 0.25     # share of chapters the tier must appear in
_MIN_TIER_OCCURRENCES = 5          # a face used three times is a flourish


def _clean(text: str) -> str:
    """Collapse whitespace and drop the control codepoints the NCERT PDFs carry
    inside a heading's text run: the bullet glyph in "6.3.1 Observe and
    identify..." extracts as U+0007, which would otherwise end up stored in a
    topic name and shown to a principal."""
    return " ".join("".join(
        " " if unicodedata.category(c) in ("Cc", "Cf") else c for c in text).split())


@dataclass(frozen=True)
class _Line:
    text: str
    size: float
    font: str
    bold: bool
    file: str
    page: int
    block: int
    # Position in the PDF's own content stream (file, then page, block, line).
    # Chapter titles are ordered by this and not by bbox: where the display
    # numeral sits inside the title's line, that line's bbox is stretched to
    # the numeral's full height and would sort above the line printed above it.
    index: int = 0
    # (text, size) per span, kept because a chapter opener sometimes sets the
    # display numeral as one span INSIDE the title line ("Storms, and
    # Cyclones 6" in class8_curiosity) rather than on a line of its own.
    spans: tuple[tuple[str, float], ...] = ()

    @property
    def where(self) -> tuple[str, int]:
        return (self.file, self.page)

    def without(self, display_size: float) -> str:
        """This line's text with any span set at `display_size` removed -- the
        chapter numeral, when it shares the title's line."""
        return _clean("".join(t for t, s in self.spans if s != display_size))

    def size_without(self, display_size: float) -> float:
        """The size this line is really set in once the display numeral's spans
        are taken out. `size` is the LEAD span's size, and Poorvi's "Unit 1"
        drop-caps the U at the numeral's own 27.1pt, so the line reports 27.1
        while the words on it are 19pt -- enough to make a page's furniture
        outrank its title."""
        rest = [s for t, s in self.spans if s != display_size and t.strip()]
        return max(rest) if rest else self.size


@dataclass(frozen=True)
class Heading:
    """One printed section heading, with the file and page it was printed on so
    a reviewer can go and look at it. `number` is None for a book that does not
    number its sections."""
    title: str
    page: int                      # 0-based page index, as PyMuPDF counts them
    source_file: str
    number: Optional[str] = None

    @property
    def chapter_number(self) -> Optional[int]:
        return int(self.number.split(".")[0]) if self.number else None

    @property
    def level(self) -> int:
        """1 for "2.2" (a topic), 2 for "2.2.1" (a subtopic)."""
        return self.number.count(".") if self.number else 1

    @property
    def parent_number(self) -> Optional[str]:
        if self.number and self.number.count(".") > 1:
            return self.number.rsplit(".", 1)[0]
        return None


@dataclass(frozen=True)
class ExtractedTopic:
    name: str
    page: int
    number: Optional[str] = None
    subtopics: tuple[Heading, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ExtractedChapter:
    number: int
    name: str
    page: int
    source_file: str
    topics: tuple[ExtractedTopic, ...] = field(default_factory=tuple)


# ---------------- reading the PDFs ----------------

def _open(pdf_path: Path):
    try:
        import pymupdf                      # PyMuPDF >= 1.24 name
    except ImportError:                     # pragma: no cover - older wheels
        import fitz as pymupdf
    return pymupdf.open(pdf_path)


def pdf_files(source: Path) -> list[Path]:
    """One PDF, or every PDF in a directory in filename order -- NCERT ships
    the Social Science books as one file per chapter (`fees101.pdf` ...), and
    the whole directory is one book."""
    if source.is_dir():
        return sorted(p for p in source.glob("*.pdf"))
    return [source]


def _lines(paths: Sequence[Path], root: Optional[Path] = None) -> list[_Line]:
    """Every text line across the book, with the font facts the heading rules
    need. Continuation lines are NOT merged here -- `_merge_wrapped` does that,
    because it needs to know which line started a heading."""
    out: list[_Line] = []
    for path in paths:
        name = path.relative_to(root).as_posix() if root else path.name
        doc = _open(path)
        try:
            for page_no in range(doc.page_count):
                blocks = doc[page_no].get_text("dict")["blocks"]
                for block_no, block in enumerate(blocks):
                    if block.get("type") != 0:      # 0 = text, 1 = image
                        continue
                    for line in block["lines"]:
                        spans = [s for s in line["spans"] if s["text"].strip()]
                        if not spans:
                            continue
                        text = _clean("".join(s["text"] for s in spans))
                        if not text:
                            continue
                        lead = spans[0]
                        font = lead["font"]
                        out.append(_Line(
                            text=text, size=round(lead["size"], 1), font=font,
                            bold=bool(lead["flags"] & _FLAG_BOLD)
                                 or any(n in font.lower() for n in _BOLD_NAMES),
                            file=name, page=page_no, block=block_no, index=len(out),
                            spans=tuple((s["text"], round(s["size"], 1)) for s in spans)))
        finally:
            doc.close()
    return out


def body_size(lines: Iterable[_Line]) -> float:
    """The book's running-text size: the size that the most CHARACTERS are set
    in. Counting lines instead would be swayed by the many short lines in
    captions and margin notes; counting characters lands on the prose."""
    weight: dict[float, int] = {}
    for ln in lines:
        weight[ln.size] = weight.get(ln.size, 0) + len(ln.text)
    return max(weight, key=lambda s: weight[s]) if weight else 0.0


# ---------------- chapter openers ----------------

def _opener_title(page_lines: list[_Line], numeral_size: float,
                  base: float) -> Optional[tuple[str, _Line]]:
    """The chapter title printed on one opener page, or None.

    Size only, no bold test: Ganita Prakash and Poorvi set their chapter titles
    in display faces (LuckiestGuy) that PyMuPDF reports as neither bold-flagged
    nor bold-named, and requiring bold found no chapter at all in either book.
    On a page that already prints a lone display numeral, size is the signal --
    but it has to be read as a CLASS, not as a threshold, because an opener page
    carries three kinds of large text:

      * the title, in one size or two adjacent ones;
      * page furniture at a distinctly smaller size -- the word "Chapter"
        (Exploration 9), "CHAPTER" (Social Science), "Probe and ponder"
        (Curiosity 8);
      * unrelated large text elsewhere on the page -- the "Questions" box
        heading, Poorvi's unit theme printed a dozen blocks below the lesson
        title.

    So: take every line that has words at title size, keep the ones within
    `_TITLE_SIZE_BAND` of the largest (which drops the furniture), and then keep
    only the run of CONSECUTIVE lines that contains that largest one (which
    drops the unrelated text further down the page). Both halves are needed --
    Curiosity 7 splits one title across two blocks at 30pt and 28pt, so a
    single-size or single-block rule truncates it to "Basic, and Neutral".
    """
    cands = []
    for ln in sorted(page_lines, key=lambda l: l.index):
        text = ln.without(numeral_size)
        if sum(c.isalpha() for c in text) < 3:
            continue
        size = ln.size_without(numeral_size)
        if size >= base * _MIN_TITLE_RATIO:
            cands.append((ln, text, size))
    if not cands:
        return None

    top = max(size for _, _, size in cands)
    runs: list[list[tuple[_Line, str, float]]] = []
    for cand in cands:
        if cand[2] < top * _TITLE_SIZE_BAND:
            continue
        if runs and cand[0].index == runs[-1][-1][0].index + 1:
            runs[-1].append(cand)
        else:
            runs.append([cand])
    run = next(r for r in runs if any(size == top for _, _, size in r))
    return " ".join(" ".join(text for _, text, _ in run).split()), run[0][0]


def _chapter_openers(lines: list[_Line]) -> tuple[dict[int, _Line], dict[int, str]]:
    """({chapter number: the line its title starts on}, {chapter number: title}).

    An NCERT chapter opens on a page that prints its number alone at display
    size (72pt against 13pt body in Curiosity) beside the chapter title. Both
    facts are required: front matter ("Foreword", "Contents") is set at title
    size too but never carries a lone display numeral, and the big decorative
    "?" that opens several spreads carries no letters.
    """
    base = body_size(lines)
    by_page: dict[tuple[str, int], list[_Line]] = {}
    for ln in lines:
        by_page.setdefault(ln.where, []).append(ln)

    found: list[tuple[int, str, _Line]] = []
    for page_lines in sorted(by_page.values(), key=lambda g: g[0].index):
        # The numeral is looked for per SPAN, not per line: class8_curiosity
        # sets "6" inside the title's own line, class6_curiosity gives it a line
        # of its own, and both are the same chapter opener.
        numerals = [(ln, text.strip(), size) for ln in page_lines
                    for text, size in ln.spans
                    if _PURE_INT.match(text.strip())
                    and size >= base * _MIN_CHAPTER_NUMERAL_RATIO]
        if len(numerals) != 1:
            continue
        _, numeral_text, numeral_size = numerals[0]
        title = _opener_title(page_lines, numeral_size, base)
        if title is None:
            continue
        found.append((int(numeral_text), title[0], title[1]))

    found = _drop_front_matter(found)
    out: dict[int, tuple[str, _Line]] = {}
    for number, title, line in found:
        # A number printed twice at display size (a part divider reusing it)
        # keeps its first, i.e. opening, page.
        out.setdefault(number, (title, line))
    return ({n: ln for n, (_, ln) in out.items()},
            {n: t for n, (t, _) in out.items()})


def _drop_front_matter(found: list[tuple[int, str, _Line]]) -> list[tuple[int, str, _Line]]:
    """Everything printed before the chapter numbered 1 is front matter.

    Ganita Manjari 9's cover sets the GRADE -- "9" -- alone at 43.8pt beside
    "GANITA MANJARI", which is a lone display numeral next to a title and so is
    indistinguishable from a chapter opener by the page's own metrics. It is
    distinguishable by position: it is printed 20 pages before chapter 1. Books
    whose chapter 1 is never recognised keep every candidate, because then
    there is no evidence to cut on.
    """
    first = next((i for i, (number, _, _) in enumerate(found) if number == 1), None)
    return found[first:] if first is not None else found


# ---------------- numbered headings ----------------

def _merge_wrapped(lines: list[_Line], start: int) -> tuple[str, int]:
    """A printed heading that runs over two lines ("2.3 Plants and Animals in
    Different" / "Surroundings") is one heading. PyMuPDF keeps both lines in the
    same block at the same size and font, so the continuation rule is exactly
    that -- same block, same size, same font, and not itself a new heading."""
    head = lines[start]
    parts = [head.text]
    i = start + 1
    while (i < len(lines) and lines[i].where == head.where
           and lines[i].block == head.block and lines[i].size == head.size
           and lines[i].font == head.font
           and not _NUMBERED.match(lines[i].text)):
        parts.append(lines[i].text)
        i += 1
    return " ".join(" ".join(parts).split()), i


def _numbered_headings(lines: list[_Line]) -> list[Heading]:
    """Every numbered section heading the book prints, in reading order.

    The rule, and only this rule: the line starts with a dotted section number
    and is set apart from the body text -- bold and a touch larger, or, for a
    book that does not bold its sections, plainly larger (see
    `_MIN_UNBOLD_HEADING_RATIO`).
    """
    base = body_size(lines)
    cutoff = base * _MIN_HEADING_RATIO
    unbold_cutoff = base * _MIN_UNBOLD_HEADING_RATIO
    out: list[Heading] = []
    seen: set[str] = set()
    i = 0
    while i < len(lines):
        ln = lines[i]
        m = _NUMBERED.match(ln.text)
        apart = ln.size > cutoff if ln.bold else ln.size >= unbold_cutoff
        if not (m and apart):
            i += 1
            continue
        text, nxt = _merge_wrapped(lines, i)
        m = _NUMBERED.match(text) or m
        number, title = m.group(1), m.group(2).strip()
        # The same number printed twice is the chapter's own recap list, not a
        # second section. First occurrence wins -- that is the one on the page
        # where the section actually begins.
        if number not in seen and title:
            seen.add(number)
            out.append(Heading(number=number, title=title, page=ln.page,
                               source_file=ln.file))
        i = nxt
    return out


# ---------------- unnumbered headings (size tiers) ----------------

def _tiers(lines: list[_Line], openers: dict[int, _Line]) -> list[tuple[str, float]]:
    """The one or two (font, size) classes that a book WITHOUT numbered
    sections uses for its headings, largest first.

    Three rules separate a heading class from the furniture that a textbook
    also sets bold and large, measured on the Class 6 Social Science book:

      * a heading is written once. A class whose lines repeat the same words
        over and over is a box label -- "LET'S EXPLORE" (117 lines, 3 distinct
        strings), "Questions" (13 lines, 1 string), "CHAPTER".
      * a heading class is used again and again. The decorative pull-quote
        words that open a spread ("Ocean", "Life", 27pt) are unique strings but
        appear three times in the whole book.
      * a heading class is used across chapters, not inside one.

    The classes are counted from the pages that are NOT chapter openers: an
    opener prints the chapter title, its subtitle and the word "CHAPTER" in the
    title face, and those are exactly the lines a size rule cannot tell from a
    section heading. Headings themselves are still collected from every page,
    because a chapter that starts on its opener page prints its first heading
    there ("Family", in fees109.pdf).
    """
    base = body_size(lines)
    opener_pages = {ln.where for ln in openers.values()}
    title_size = max((ln.size for ln in openers.values()), default=float("inf"))
    chapters = {ln.file for ln in openers.values()} or {ln.file for ln in lines}

    buckets: dict[tuple[str, float], list[_Line]] = {}
    for ln in lines:
        if ln.bold and base < ln.size < title_size and ln.where not in opener_pages:
            buckets.setdefault((ln.font, ln.size), []).append(ln)

    kept: list[tuple[str, float]] = []
    for key, group in buckets.items():
        if len(group) < _MIN_TIER_OCCURRENCES:
            continue
        distinct = len({ln.text.lower() for ln in group}) / len(group)
        share = len({ln.file for ln in group}) / len(chapters)
        if distinct >= _MIN_TIER_DISTINCT and share >= _MIN_TIER_CHAPTER_SHARE:
            kept.append(key)
    kept.sort(key=lambda k: k[1], reverse=True)
    return kept[:2]


def _tiered_headings(lines: list[_Line],
                     openers: dict[int, _Line]) -> list[tuple[int, Heading]]:
    """(level, heading) in reading order, where level 1 is a topic and level 2
    a subtopic. An unnumbered book carries no number to nest by, so the tier's
    rank IS the level."""
    tiers = _tiers(lines, openers)
    if not tiers:
        return []
    levels = {key: i + 1 for i, key in enumerate(tiers)}
    opener_indexes = {o.index for o in openers.values()}
    out: list[tuple[int, Heading]] = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        level = levels.get((ln.font, ln.size))
        if level is None or ln.index in opener_indexes:
            i += 1
            continue
        # Same continuation rule as the numbered path.
        parts = [ln.text]
        j = i + 1
        while (j < len(lines) and lines[j].where == ln.where
               and lines[j].block == ln.block and lines[j].size == ln.size
               and lines[j].font == ln.font):
            parts.append(lines[j].text)
            j += 1
        out.append((level, Heading(number=None, title=" ".join(" ".join(parts).split()),
                                   page=ln.page, source_file=ln.file)))
        i = j
    return out


# ---------------- public API ----------------

def extract_headings(source: Path, root: Optional[Path] = None) -> list[Heading]:
    """Every section heading the book prints, in reading order. `source` is one
    PDF or a directory of one-chapter PDFs."""
    lines = _lines(pdf_files(source), root)
    numbered = _numbered_headings(lines)
    if numbered:
        return numbered
    openers, _ = _chapter_openers(lines)
    return [h for _, h in _tiered_headings(lines, openers)]


def extract_chapters(source: Path, root: Optional[Path] = None) -> list[ExtractedChapter]:
    """The book as Chapter -> Topic -> Subtopic, from its own printed headings.

    A chapter the book opens but prints no heading inside (the literature
    readers, Curiosity's own chapters 1 and 9) comes back with an empty
    `topics` rather than being dropped: "this chapter has no sub-structure to
    extract" and "this chapter was missed" are different answers, and the
    export's manifest reports them differently.
    """
    paths = pdf_files(source)
    lines = _lines(paths, root)
    opener_lines, opener_titles = _chapter_openers(lines)

    numbered = _numbered_headings(lines)
    if numbered:
        return _nest_numbered(numbered, opener_lines, opener_titles)
    return _nest_tiered(_tiered_headings(lines, opener_lines), opener_lines, opener_titles)


def _chapter_order(openers: dict[int, _Line]) -> list[int]:
    return [n for n, _ in sorted(openers.items(), key=lambda kv: kv[1].index)]


def _nest_numbered(headings: list[Heading], openers: dict[int, _Line],
                   titles: dict[int, str]) -> list[ExtractedChapter]:
    by_chapter: dict[int, list[Heading]] = {}
    for h in headings:
        # A heading whose chapter the book never opened is not attached to a
        # guess; it is dropped, and the count difference is visible in the
        # export's report.
        if h.chapter_number in openers:
            by_chapter.setdefault(h.chapter_number, []).append(h)

    out: list[ExtractedChapter] = []
    for number in _chapter_order(openers):
        subs: dict[str, list[Heading]] = {}
        for h in by_chapter.get(number, []):
            if h.parent_number:
                subs.setdefault(h.parent_number, []).append(h)
        topics = tuple(
            ExtractedTopic(number=h.number, name=h.title, page=h.page,
                           subtopics=tuple(subs.get(h.number or "", ())))
            for h in by_chapter.get(number, []) if h.level == 1)
        line = openers[number]
        out.append(ExtractedChapter(number=number, name=titles[number], page=line.page,
                                    source_file=line.file, topics=topics))
    return out


def _nest_tiered(headings: list[tuple[int, Heading]], openers: dict[int, _Line],
                 titles: dict[int, str]) -> list[ExtractedChapter]:
    """Unnumbered books carry no chapter number in the heading, so a heading
    belongs to the chapter whose file it is printed in -- NCERT ships these
    books as one PDF per chapter, which is why the unnumbered path only has to
    handle that shape."""
    by_file: dict[str, int] = {ln.file: n for n, ln in openers.items()}
    grouped: dict[int, list[tuple[int, Heading]]] = {}
    for level, h in headings:
        number = by_file.get(h.source_file)
        if number is not None:
            grouped.setdefault(number, []).append((level, h))

    out: list[ExtractedChapter] = []
    for number in _chapter_order(openers):
        topics: list[ExtractedTopic] = []
        for level, h in grouped.get(number, []):
            if level == 1:
                topics.append(ExtractedTopic(number=None, name=h.title, page=h.page))
            elif topics:      # a subtopic before any topic has no parent: dropped
                last = topics[-1]
                topics[-1] = ExtractedTopic(
                    number=None, name=last.name, page=last.page,
                    subtopics=last.subtopics + (h,))
        line = openers[number]
        out.append(ExtractedChapter(number=number, name=titles[number], page=line.page,
                                    source_file=line.file, topics=tuple(topics)))
    return out
