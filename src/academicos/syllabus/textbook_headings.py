"""Chapter -> topic -> subtopic headings from the NCERT textbooks. No AI.

Why
---
The bank has to be tagged per chapter, topic and subtopic, and on 2026-09-22
zero questions were linked to any subtopic: the only subtopics in the product
were one demo school's 417, school-scoped. The user chose one board-level tree
built from the section headings of the books the schools actually teach from,
read deterministically from the PDF text layer -- a heading is a line the book
typesets as a heading, never a line a model thought sounded like one.

How a heading is recognised
---------------------------
Every line is rebuilt from PyMuPDF characters (`lines_from_rawdict`) and keeps
its size, font, weight and colour. Within one chapter:

  numbered      "2.1 Diversity in Plants and Animals" is a topic and "2.2.1 How
                to group plants?" a subtopic, when the first number is the
                chapter's and the line is set apart from the body (bold, larger
                or coloured). This is how the maths and science books of every
                class, old and new, mark their sections.
  section       Class 10 History numbers its sections afresh in each chapter:
                "1 The First World War, Khilafat ..." then "1.1 The Idea of
                Satyagraha" (jess302.pdf p2). Tried when the chapter-prefixed
                scheme finds fewer than two topics.
  unnumbered    The new Social Science books (classes 6-9) and Class 10
                Democratic Politics number nothing. Their headings are bold
                lines at least 1.5pt above the body size; the largest such size
                in the chapter is the topic level and the next one down the
                subtopic level (Exploring Society, class 6: 17pt ExtraBold and
                15pt Bold, fees102.pdf pp3, 7). Marked ``headingKind:
                "unnumbered"`` because it is the weaker signal.

What is never a topic, whatever its type: activities, examples, figures,
tables, exercises, boxes ("LET'S EXPLORE", "Think and Reflect", "Probe and
ponder"), and the end-of-chapter matter ("Before we move on", "In a Nutshell",
"What you have learnt"). A numbered line whose text starts in lower case is a
cross-reference in running text ("2.4 and 2.5. They also ...",
class8_curiosity.pdf p36), not a heading.

The measured precision and recall of all this, against headings read off the
pages by hand, are in ``academicos-data/syllabus/taxonomy/_manifest.json``
(`scripts/build_taxonomy.py`).
"""
from __future__ import annotations

import collections
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path


# --------------------------------------------------------------------------- #
# reading
# --------------------------------------------------------------------------- #

@dataclass
class Line:
    """One printed line as the reader sees it, rebuilt from PyMuPDF characters."""
    page: int            # 1-based page in the PDF file
    text: str
    size: float          # the size most of the line's characters are set in
    font: str
    bold: bool
    color: int
    x0: float
    y0: float
    x1: float
    y1: float

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Line":
        return cls(**d)


_BOLD_NAMES = ("bold", "black", "heavy", "semibold", "demi", "halbfett", "extrab")


def _is_bold(font: str, flags: int) -> bool:
    return bool(flags & 16) or any(k in font.lower() for k in _BOLD_NAMES)


def _printed_near(seen: dict, c: str, x: float, y: float) -> bool:
    """The same character already printed within 1.2pt: an overprint copy.

    The copies are nudged a fraction of a point apart (that is how the bold
    is faked), so exact positions do not match; a character is never set
    twice within 1.2pt on purpose (the narrowest glyph, a 6pt superscript
    "l", advances ~1.7pt).
    """
    rx, ry = round(x), round(y)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for sx, sy in seen.get((c, rx + dx, ry + dy), ()):
                if abs(sx - x) < 1.2 and abs(sy - y) < 1.2:
                    return True
    return False


def lines_from_rawdict(page_no: int, raw: dict) -> list[Line]:
    """Rebuild a page's lines from ``page.get_text("rawdict")``.

    Two things in the books defeat PyMuPDF's own lines. Class 10 Science
    fakes bold by printing a heading five times at nearly the same spot, and
    kerned capitals split it mid-word, so ``1.1 CHEMICAL EQUATIONS`` arrives as
    ``1.1 CHEMIC`` x4, ``1.1 CHEMICAL EQUA``, ``AL EQUA`` x4, ``TIONS`` x4
    (jesc101.pdf page 2). So a character already printed at the same place is
    dropped, and what survives on one baseline in one size is joined back.
    """
    seen: dict[tuple, list] = {}
    pieces = []
    for block in raw.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                chars = []
                for ch in span["chars"]:
                    c = ch["c"]
                    x, y = ch["origin"]
                    if _printed_near(seen, c, x, y):
                        continue
                    seen.setdefault((c, round(x), round(y)), []).append((x, y))
                    chars.append((c, ch["bbox"]))
                if not "".join(c for c, _ in chars).strip():
                    continue
                pieces.append({
                    "chars": chars, "size": round(span["size"], 2),
                    "font": span["font"], "flags": span["flags"],
                    "color": span["color"], "base": round(span["origin"][1], 1),
                })
    return _join_pieces(page_no, pieces)


def _join_pieces(page_no: int, pieces: list[dict]) -> list[Line]:
    """Join same-baseline, same-size pieces that touch horizontally."""
    groups: list[list[dict]] = []
    for p in pieces:
        ink = [b for c, b in p["chars"] if not c.isspace()]
        p["x0"] = min(b[0] for b in ink)
        p["x1"] = max(b[2] for b in ink)
        for g in groups:
            last = g[-1]
            if (abs(last["base"] - p["base"]) <= 1.0
                    and abs(last["size"] - p["size"]) <= 0.6
                    and -0.5 * p["size"] <= p["x0"] - last["x1"]
                    <= max(p["size"], last["size"]) * 1.2):
                g.append(p)
                break
        else:
            groups.append([p])
    out = []
    for g in groups:
        g.sort(key=lambda p: p["x0"])
        text = ""
        prev_x1 = None
        weight: dict[tuple, int] = {}
        for p in g:
            for c, b in p["chars"]:
                if (prev_x1 is not None and b[0] - prev_x1 > p["size"] * 0.2
                        and not text.endswith(" ") and c != " "):
                    text += " "
                text += c
                prev_x1 = b[2]
            k = (p["size"], p["font"], p["flags"], p["color"])
            weight[k] = weight.get(k, 0) + sum(1 for c, _ in p["chars"] if not c.isspace())
        size, font, flags, color = max(weight, key=weight.get)
        boxes = [b for p in g for _, b in p["chars"]]
        out.append(Line(
            page=page_no, text=" ".join(text.split()), size=size, font=font,
            bold=_is_bold(font, flags), color=color,
            x0=round(min(b[0] for b in boxes), 1), y0=round(min(b[1] for b in boxes), 1),
            x1=round(max(b[2] for b in boxes), 1), y1=round(max(b[3] for b in boxes), 1)))
    return out


def read_lines(path: Path) -> list[Line]:
    """Every line of every page of one PDF. The one PDF-touching function."""
    from academicos.corpus.ncert_exemplar import _pymupdf, require_verified_pymupdf
    require_verified_pymupdf()
    fitz = _pymupdf()
    doc = fitz.open(str(path))
    try:
        out: list[Line] = []
        for i, page in enumerate(doc, 1):
            out.extend(lines_from_rawdict(i, page.get_text("rawdict", flags=fitz.TEXTFLAGS_TEXT)))
        return out
    finally:
        doc.close()


# --------------------------------------------------------------------------- #
# headings within one chapter
# --------------------------------------------------------------------------- #

@dataclass
class Heading:
    level: int                  # 1 = topic, 2 = subtopic
    name: str
    page: int
    number: str | None = None   # "2.1", "2.2.1"; None when the book prints none
    kind: str = "numbered"      # numbered | section | unnumbered


def body_style(lines: list[Line]) -> tuple[float, str]:
    """The (size, font) most characters are set in."""
    sizes: collections.Counter = collections.Counter()
    fonts: collections.Counter = collections.Counter()
    for ln in lines:
        n = len(ln.text)
        sizes[ln.size] += n
        fonts[ln.font] += n
    if not sizes:
        return 0.0, ""
    return sizes.most_common(1)[0][0], fonts.most_common(1)[0][0]


def _whitish(color: int) -> bool:
    return all(((color >> s) & 0xFF) >= 0xE0 for s in (16, 8, 0))


def _blackish(color: int) -> bool:
    return all(((color >> s) & 0xFF) <= 0x40 for s in (16, 8, 0))


# Box labels, feature panels and end matter. Matched against the start of the
# heading, case- and apostrophe-insensitively.
_NOT_TOPICS = (
    "activity", "activities", "example", "examples", "fig ", "fig.", "figure", "table",
    "exercise", "exercises", "box", "project", "projects", "discuss", "source",
    "let's explore", "let us explore", "think about it", "don't miss out",
    "before we move on", "questions, activities", "questions and activities",
    "the big questions", "big questions", "keywords", "key words", "glossary",
    "in a nutshell", "let us enhance", "exploratory projects", "probe and ponder",
    "ever heard of", "know a scientist", "at a glance", "revise, reflect",
    "the journey beyond", "chapter summary", "summary", "figure it out",
    "think and reflect", "what you have learnt", "overview", "do you know",
    "did you know", "fun facts", "try this", "try these", "math talk", "puzzle time",
    "notes for", "a note on", "write in brief", "points to ponder", "remember",
    "happy investigating", "questions", "let's work", "let us work", "summing up",
    "sources for information", "chapter", "additional project", "additional activit",
    "suggested reading", "notes", "class activity", "answer the following",
)


def _norm_words(text: str) -> str:
    t = unicodedata.normalize("NFKD", text).lower().replace("’", "'")
    return re.sub(r"\s+", " ", t).strip()


def _not_a_topic(name: str) -> bool:
    t = _norm_words(name)
    return any(t == k or t.startswith(k + " ") or t.startswith(k + ":")
               or (k.endswith((" ", ".")) and t.startswith(k)) for k in _NOT_TOPICS)


_NUMBERED = re.compile(r"^(\d{1,2})\.(\d{1,2})(?:\.(\d{1,2}))?\.?\s*(.*)$")
_SECTION = re.compile(r"^(\d{1,2})\s+(\S.*)$")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


_LIGATURES = {"\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl", "\ufb03": "ffi", "\ufb04": "ffl"}


def _clean(text: str) -> str:
    """One line of heading text as printed: control characters out, ligatures
    spelt ("Reﬂ ection" -> "Reflection", class7_curiosity.pdf p179), no space
    before a comma ("Trade , trade routes", gees105.pdf p9)."""
    text = _CONTROL.sub(" ", text)
    for lig, letters in _LIGATURES.items():
        text = re.sub(lig + r"\s?(?=[a-z])", letters, text).replace(lig, letters)
    text = re.sub(r"\s+([,;:?!])", r"\1", text)
    # a raised ordinal run into the next word: "11thand 12th Centuries" (gees204.pdf p1)
    text = re.sub(r"(\d(?:st|nd|rd|th))(?=[a-z]{2})", r"\1 ", text)
    return " ".join(text.split()).strip(" -–—:")


# A line opening with one of these is the second line of something else (a
# table caption "... INDIA AND ITS NEIGHBOURS" / "FOR 2023", jess201.pdf p12).
_FRAGMENT_START = {"and", "or", "of", "for", "with", "to"}


def _starts_like_a_title(text: str) -> bool:
    t = text.lstrip("‘'\"“(")
    if not t or t.split()[0].lower() in _FRAGMENT_START:
        return False
    return t[0].isupper() or t[0].isdigit() or not t[0].isascii()


def _latin_share(text: str) -> float:
    letters = [ch for ch in text if ch.isalpha()]
    return sum(ch.isascii() for ch in letters) / len(letters) if letters else 0.0


def _foreign_script(name: str, lines: list[Line]) -> bool:
    """A Devanagari epigraph in an English book (Curiosity 6 opens chapter 9
    with a Kabir doha in 18pt bold, class6_curiosity.pdf p181) is not a
    heading; a heading shares the script of the book's running text."""
    book_latin = _latin_share("".join(ln.text for ln in lines[:400])) >= 0.5
    return book_latin != (_latin_share(name) >= 0.5)


def _set_apart(ln: Line, body: float, body_font: str) -> bool:
    """Typeset unlike running text: bold, larger, or coloured in another font."""
    return (ln.bold or ln.size >= body + 0.9
            or (not _blackish(ln.color) and ln.font != body_font))


def _continuation(prev: Line, ln: Line) -> bool:
    """``ln`` carries on the heading ``prev`` on the next printed line."""
    return (ln.page == prev.page and abs(ln.size - prev.size) < 0.3
            and ln.font == prev.font and ln.color == prev.color
            and -0.5 * ln.size <= ln.y0 - prev.y1 <= 0.8 * ln.size
            and (abs(ln.x0 - prev.x0) <= max(40.0, 3 * ln.size)       # ragged right
                 or abs(ln.x0 + ln.x1 - prev.x0 - prev.x1) <= 6 * ln.size))  # centred


def _with_continuations(lines: list[Line], i: int, stop) -> tuple[str, int]:
    """Text of the heading at ``lines[i]`` plus its wrapped lines below.

    Looks a few lines ahead, because in reading order a margin note at the
    same height can sit between a heading and its second line.
    """
    text, j = lines[i].text, i
    while len(text) < 160:
        nxt = next((k for k in range(j + 1, min(j + 5, len(lines)))
                    if _continuation(lines[j], lines[k])), None)
        if nxt is None or stop(lines[nxt].text):
            break
        j = nxt
        text += " " + lines[j].text
    return text, j


def reading_order(lines: list[Line]) -> list[Line]:
    """Page by page; top to bottom, column by column on a two-column page.

    PyMuPDF's content-stream order put "2.1 The Aristocracy and the New
    Middle Class" before its topic "2 The Making of Nationalism in Europe"
    (jess301.pdf p8, y=535 vs 55), so lines are re-sorted by height. But a
    plain top-to-bottom sort reads across columns: Democratic Politics ends
    its left column with "Caste and politics" (y=607) and opens the right
    one with its first sub-section "Caste inequalities" (y=71, jess403.pdf
    p10). A page is two-column when at least 8 body-size lines end before
    68% of its text width and 8 start after 60%.
    """
    body, _ = body_style(lines)
    by_page: dict[int, list[Line]] = collections.defaultdict(list)
    for ln in lines:
        by_page[ln.page].append(ln)
    out: list[Line] = []
    for page in sorted(by_page):
        pl = by_page[page]
        width = max(ln.x1 for ln in pl)
        body_lines = [ln for ln in pl if abs(ln.size - body) < 0.6]
        left = [ln for ln in body_lines if ln.x1 < 0.68 * width]
        right = [ln for ln in body_lines if ln.x0 > 0.6 * width]
        if len(left) >= 8 and len(right) >= 8:
            split = min(ln.x0 for ln in right) - 5
            key = lambda ln: (ln.x0 >= split, round(ln.y0), ln.x0)
        else:
            key = lambda ln: (round(ln.y0), ln.x0)
        out.extend(sorted(pl, key=key))
    return out


def numbered_headings(lines: list[Line], chapter: int) -> list[Heading]:
    """"N.k Title" topics and "N.k.m Title" subtopics of chapter N, in order.

    A number is taken once, at its first appearance, and only if it comes
    after the previous one: running heads and cross-references repeat numbers
    out of order, headings do not.
    """
    body, body_font = body_style(lines)
    out: list[Heading] = []
    seen: set[tuple] = set()
    last: tuple = (0, 0)
    for i, ln in enumerate(lines):
        m = _NUMBERED.match(ln.text)
        if not m or int(m.group(1)) != chapter or not _set_apart(ln, body, body_font):
            continue
        k = int(m.group(2))
        sub = int(m.group(3)) if m.group(3) else 0
        text, _ = _with_continuations(lines, i, lambda t: bool(_NUMBERED.match(t)))
        name = _clean(_NUMBERED.match(text).group(4))
        if (not name or not _starts_like_a_title(name) or _not_a_topic(name)
                or len(name) > 150 or sum(ch.isalpha() for ch in name) < 3):
            continue
        key = (k, sub)
        if key in seen or key <= last:
            continue
        seen.add(key)
        last = key
        number = f"{chapter}.{k}" + (f".{sub}" if sub else "")
        out.append(Heading(level=2 if sub else 1, name=name, page=ln.page, number=number))
    return out


def unnumbered_subtopics(lines: list[Line], topics: list[Heading]) -> list[Heading]:
    """Unnumbered sub-headings under numbered topics, merged in page order.

    Ganita Prakash numbers its topics ("5.4 Prime Factorisation", 17pt red)
    but not the sub-sections under them ("Divisibility by 4", 14pt blue,
    class6_ganita_prakash.pdf p184). Taken only when a chapter has no
    numbered subtopic: bold, not white, set between body and topic size, and
    only the one (size, font, colour) most used for such lines -- a third,
    smaller level (13pt black "Idli-Vada Game") stays out.
    """
    if not topics:
        return topics
    body, _ = body_style(lines)
    k = _position(lines, topics[0])
    top = lines[k].size if k >= 0 else body + 4
    cands = []
    for i, ln in enumerate(lines):
        if (ln.bold and not _whitish(ln.color) and body + 0.9 <= ln.size <= top - 0.9
                and not _NUMBERED.match(ln.text) and not ln.text[:1].isdigit()):
            text, _ = _with_continuations(lines, i, lambda t: False)
            name = _clean(text)
            if (sum(ch.isalpha() for ch in name) >= 3 and len(name) <= 110
                    and _starts_like_a_title(name) and not _not_a_topic(name)
                    and not name.endswith((",", ";", ".")) and not _foreign_script(name, lines)):
                cands.append((ln, name, i))
    if not cands:
        return topics
    style = collections.Counter((ln.size, ln.font, ln.color) for ln, _, _ in cands).most_common(1)[0][0]
    # a continuation line was also a candidate on its own: keep the first
    taken, subs = set(), []
    for ln, name, i in cands:
        if (ln.size, ln.font, ln.color) != style or i in taken:
            continue
        _, j = _with_continuations(lines, i, lambda t: False)
        taken.update(range(i, j + 1))
        subs.append((ln, Heading(2, name, ln.page, None, "numbered")))
    # interleave by position in reading order
    index = {id(ln): k for k, ln in enumerate(lines)}
    merged = [(_position(lines, t), t) for t in topics]
    merged += [(index[id(ln)], h) for ln, h in subs]
    merged.sort(key=lambda kv: kv[0])
    return [h for _, h in merged]


def _position(lines: list[Line], h: Heading) -> int:
    """Index of the line a heading was read from (-1 if not found)."""
    return next((k for k, ln in enumerate(lines)
                 if ln.page == h.page and h.name in _clean(ln.text)), -1)


def section_headings(lines: list[Line]) -> list[Heading]:
    """"1 Title" topics and "1.1 Title" subtopics numbered afresh per chapter.

    The topic line must be well above body size (jess302.pdf p2: 18pt against
    11.5pt), or a list item "1 Power is shared among ..." would count.
    """
    body, body_font = body_style(lines)
    out: list[Heading] = []
    topic = 0
    subs: set[int] = set()
    for i, ln in enumerate(lines):
        m = _SECTION.match(ln.text)
        if m and ln.bold and ln.size >= body + 3 and int(m.group(1)) == topic + 1:
            text, _ = _with_continuations(lines, i, lambda t: bool(_SECTION.match(t)))
            name = _clean(_SECTION.match(text).group(2))
            if _starts_like_a_title(name) and not _not_a_topic(name):
                topic += 1
                subs = set()
                out.append(Heading(1, name, ln.page, str(topic), "section"))
            continue
        m = _NUMBERED.match(ln.text)
        if (m and not m.group(3) and topic and int(m.group(1)) == topic
                and _set_apart(ln, body, body_font)):
            k = int(m.group(2))
            text, _ = _with_continuations(
                lines, i, lambda t: bool(_NUMBERED.match(t) or _SECTION.match(t)))
            name = _clean(_NUMBERED.match(text).group(4))
            if k in subs or (subs and k < max(subs)) or not _starts_like_a_title(name):
                continue
            if _not_a_topic(name):
                continue
            subs.add(k)
            out.append(Heading(2, name, ln.page, f"{topic}.{k}", "section"))
    return out


def unnumbered_headings(lines: list[Line], skip_pages: frozenset = frozenset()) -> list[Heading]:
    """Bold headings of a book that numbers nothing, in two size levels.

    Candidates are bold, not white (white type sits on a picture or a panel),
    at least 1.5pt above body size and below chapter-title size (24pt). The
    largest candidate size in the chapter is the topic level; the next size at
    least 0.9pt smaller is the subtopic level; anything smaller is ignored.
    """
    body, _ = body_style(lines)
    cands: list[tuple[Line, str]] = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if (ln.page not in skip_pages and ln.bold and not _whitish(ln.color)
                and body + 1.5 <= ln.size < 24 and not ln.text[:1].isdigit()):
            text, j = _with_continuations(lines, i, lambda t: False)
            name = _clean(text)
            if (sum(ch.isalpha() for ch in name) >= 3 and len(name) <= 110
                    and not _not_a_topic(name) and not name.endswith((",", ";"))
                    and _starts_like_a_title(name) and not _foreign_script(name, lines)):
                cands.append((ln, name))
            i = j + 1
            continue
        i += 1
    # Sizes within 0.6pt are one level: gees105.pdf sets the same sub-heading
    # style at 15pt and 15.43pt (pp6, 17).
    levels: list[list[float]] = []
    for size in sorted({ln.size for ln, _ in cands}, reverse=True):
        if levels and levels[-1][0] - size <= 0.6:
            levels[-1].append(size)
        else:
            levels.append([size])
    if not levels:
        return []
    top = set(levels[0])
    second = set(levels[1]) if len(levels) > 1 and levels[0][-1] - levels[1][0] >= 0.9 else set()
    out = []
    for ln, name in cands:
        if ln.size in top:
            out.append(Heading(1, name, ln.page, None, "unnumbered"))
        elif ln.size in second:
            out.append(Heading(2, name, ln.page, None, "unnumbered"))
    return out


@dataclass(frozen=True)
class HeadingStyle:
    """A book's own heading type, for a book the size ranking misreads.

    Understanding Economic Development (Class 10) sets its sections as 14pt
    white capitals on a coloured band and its sub-sections in 18pt dark type
    (jess203.pdf pp2, 4: "MONEY AS A MEDIUM OF EXCHANGE", "Cheque Payments"),
    so the larger size is the lower level and the topic level is white --
    both of which the automatic rule exists to refuse.
    """
    min_size: float
    max_size: float
    white: bool = False
    caps: bool = False


def _matches(ln: Line, st: HeadingStyle) -> bool:
    return (st.min_size <= ln.size <= st.max_size and _whitish(ln.color) == st.white
            and (not st.caps or ln.text.upper() == ln.text))


def styled_headings(lines: list[Line], topic: HeadingStyle, sub: HeadingStyle | None = None,
                    skip_pages: frozenset = frozenset()) -> list[Heading]:
    """Headings in a declared type style (see `HeadingStyle`), in reading order."""
    out: list[Heading] = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        level = (1 if _matches(ln, topic) else 2 if sub and _matches(ln, sub) else 0)
        if level and ln.page not in skip_pages and not ln.text[:1].isdigit():
            text, j = _with_continuations(lines, i, lambda t: False)
            name = _clean(text)
            if (sum(ch.isalpha() for ch in name) >= 3 and not _not_a_topic(name)
                    and _starts_like_a_title(name) and not _foreign_script(name, lines)):
                out.append(Heading(level, name, ln.page, None, "styled"))
            i = j + 1
            continue
        i += 1
    return out


def chapter_headings(lines: list[Line], chapter: int, skip_pages: frozenset = frozenset(),
                     styles: tuple[HeadingStyle, HeadingStyle | None] | None = None
                     ) -> tuple[list[Heading], str]:
    """The best-supported heading scheme for one chapter, and its name.

    Numbered (the strongest signal) or per-chapter section numbers, then
    unnumbered bold headings; ``"none"`` when nothing qualifies.
    """
    lines = reading_order(lines)
    if styles:
        found = styled_headings(lines, styles[0], styles[1], skip_pages)
        return found, ("styled" if found else "none")
    found = numbered_headings(lines, chapter)
    sec = section_headings(lines)
    # History numbers sections afresh, so chapter 2's "2.1 The Movement in the
    # Towns" also reads as chapter-prefixed; the section scheme, which sees
    # the "1 ..", "2 .." topics too, finds more (jess302.pdf: 4+7 against 3).
    if sum(h.level == 1 for h in sec) >= 2 and len(sec) > len(found):
        return sec, "section"
    # One numbered topic is enough: after "Summary" is dropped, Class 10
    # Maths chapter 9 has only "9.1 Heights and Distances" (jemh109.pdf).
    if any(h.level == 1 for h in found):
        if not any(h.level == 2 for h in found):
            found = unnumbered_subtopics(lines, found)
        return found, "numbered"
    un = unnumbered_headings(lines, skip_pages)
    if un:
        return un, "unnumbered"
    return [], "none"


# --------------------------------------------------------------------------- #
# the tree
# --------------------------------------------------------------------------- #

def slug(text: str) -> str:
    """A stable, readable id segment: ASCII-folded, lower case, hyphenated.

    Devanagari is kept as it is (folding would erase it); everything else is
    reduced to letters and digits so the id does not change with the book's
    punctuation or a curly apostrophe.
    """
    t = unicodedata.normalize("NFKD", text)
    t = "".join(ch for ch in t if not unicodedata.combining(ch) or "ऀ" <= ch <= "ॿ")
    t = t.lower().replace("&", " and ")
    t = re.sub(r"[^\wऀ-ॿ]+", "-", t).strip("-_")
    return t[:60].rstrip("-") or "untitled"


def _unique(base: str, used: set[str]) -> str:
    sid, n = base, 2
    while sid in used:
        sid, n = f"{base}-{n}", n + 1
    used.add(sid)
    return sid


def build_topics(chapter_id: str, headings: list[Heading]) -> tuple[list[dict], int]:
    """Nest subtopics under the topic before them. Returns (topics, orphans).

    An orphan is a subtopic with no topic before it in the chapter, or whose
    number names another topic; it is counted and dropped rather than hung
    under a guessed parent.
    """
    topics: list[dict] = []
    used_t: set[str] = set()
    used_s: dict[str, set] = {}
    orphans = 0
    for h in headings:
        if h.level == 1:
            tid = _unique(f"{chapter_id}/{slug(h.name)}", used_t)
            t = {"id": tid, "name": h.name, "page": h.page}
            if h.number:
                t["number"] = h.number
            t["subtopics"] = []
            used_s[tid] = set()
            topics.append(t)
            continue
        if not topics or (h.number and topics[-1].get("number")
                          and not h.number.startswith(topics[-1]["number"] + ".")):
            orphans += 1
            continue
        t = topics[-1]
        s = {"id": _unique(f'{t["id"]}/{slug(h.name)}', used_s[t["id"]]),
             "name": h.name, "page": h.page}
        if h.number:
            s["number"] = h.number
        t["subtopics"].append(s)
    return topics, orphans


# --------------------------------------------------------------------------- #
# chapters of a whole book, from its contents page
# --------------------------------------------------------------------------- #

@dataclass
class ContentsEntry:
    title: str
    printed_page: int
    number: int | None = None      # "Chapter N" when the contents says so
    title_parts: list[str] = field(default_factory=list)


_CHAPTER_MARK = re.compile(r"^chapter\s+(\d{1,2})\b\s*(.*)$", re.I)
_UNIT_MARK = re.compile(r"^unit\s+\d+\b", re.I)
_ARABIC = re.compile(r"^\d{1,3}$")
_ROMAN = re.compile(r"^[ivxlc]+$", re.I)


def _rows(lines: list[Line]) -> list[list[Line]]:
    rows: list[list[Line]] = []
    for ln in sorted(lines, key=lambda l: (l.y1, l.x0)):
        if rows and abs(rows[-1][0].y1 - ln.y1) <= 3.5:
            rows[-1].append(ln)
        else:
            rows.append([ln])
    return [sorted(r, key=lambda l: l.x0) for r in rows]


def parse_contents(lines: list[Line], pages: list[int]) -> list[ContentsEntry]:
    """Entries of a printed contents page: title, printed start page, number.

    A row that ends in an arabic page number closes an entry; "Chapter N"
    opens one. A plain row before the closing row is the start of a wrapped
    title (Poorvi 8: "A Tale of Valour: Major Somnath Sharma" / "and the
    Battle of Badgam  49"); a plain row in lower case straight after a closed
    entry is the end of one (Ganita Manjari: "Predicting What Comes Next:
    Exploring Sequences  174" / "and Progressions"). Bold rows with no page
    number head the contents' own units ("Unit 2: Wit and Humour",
    "गद्य खंड"). Only the leftmost text of a row is title: the class 9 Hindi
    contents prints the author in a second column.
    """
    entries: list[ContentsEntry] = []
    open_: ContentsEntry | None = None
    pending: list[str] = []
    for p in pages:
        for row in _rows([ln for ln in lines if ln.page == p]):
            texts = [_clean(ln.text) for ln in row]
            row = [ln for ln, t in zip(row, texts) if t]
            texts = [t for t in texts if t]
            if not texts or (len(texts) == 1 and (
                    texts[0].lower().replace(" ", "") in ("contents", "content")
                    or _ARABIC.match(texts[0]) or _ROMAN.match(texts[0]))):
                continue
            num = None
            if len(row) > 1 and _ARABIC.match(texts[-1]):
                num = int(texts[-1])
                row, texts = row[:-1], texts[:-1]
            elif len(row) > 1 and _ROMAN.match(texts[-1]):
                pending = []
                continue            # front matter: Foreword, About the Book
            m = _CHAPTER_MARK.match(texts[0])
            if m:
                open_ = ContentsEntry("", 0, int(m.group(1)))
                pending = []
                rest = " ".join(t for t in [m.group(2)] + texts[1:] if t)
                if rest:
                    open_.title_parts.append(rest)
                if num is not None:
                    open_.printed_page = num
                    entries.append(open_)
                    open_ = None
                continue
            first = texts[0]
            if num is None:
                if row[0].bold or _UNIT_MARK.match(first):
                    pending = []
                elif open_ is not None:
                    open_.title_parts.append(first)
                elif entries and not pending and first[:1].islower():
                    entries[-1].title_parts.append(first)
                else:
                    pending.append(first)
                continue
            if open_ is not None:
                open_.title_parts.append(first)
                open_.printed_page = num
                entries.append(open_)
                open_ = None
            else:
                entries.append(ContentsEntry("", num, None, pending + [first]))
            pending = []
    for e in entries:
        e.title = _clean(" ".join(e.title_parts))
    return entries


def _letters(text: str) -> str:
    return re.sub(r"[^a-zऀ-ॿ]", "", unicodedata.normalize("NFKD", text).lower())


def printed_page_numbers(lines: list[Line]) -> dict[int, int]:
    """Printed page number -> PDF page, from the folios in the page margins.

    A constant offset does not hold: Ganita Prakash 6 puts five unnumbered
    pages between chapters 1 and 2 (printed 12 is PDF 32, printed 14 is PDF
    39). A folio is a line of digits only, within 70pt of the top or bottom
    edge, no larger than body type; a number claimed by two pages is dropped.
    """
    body, _ = body_style(lines)
    bottom = max((ln.y1 for ln in lines), default=0)
    seen: dict[int, set] = collections.defaultdict(set)
    for ln in lines:
        t = ln.text.strip()
        if (_ARABIC.match(t) and ln.size <= body + 0.5
                and (ln.y0 >= bottom - 70 or ln.y1 <= 70)):
            seen[int(t)].add(ln.page)
    return {n: next(iter(ps)) for n, ps in seen.items() if len(ps) == 1}


def locate_chapter_starts(lines: list[Line], entries: list[ContentsEntry],
                          after_page: int) -> list[tuple[int | None, str]]:
    """The PDF page each entry starts on, and how it was found.

    ``title``: the first page after the previous chapter's start whose
    display type (>= body + 2.5pt) contains the first 14 letters of the
    entry's title. ``folio``: failing that, the page printed one before the
    entry's start page, plus one. ``None`` when neither is there.
    """
    body, _ = body_style(lines)
    display: dict[int, str] = collections.defaultdict(str)
    for ln in reading_order(lines):
        if ln.page > after_page and ln.size >= body + 2.5:
            display[ln.page] += _letters(ln.text)
    folios = printed_page_numbers(lines)
    out: list[tuple[int | None, str]] = []
    prev = after_page
    for e in entries:
        key = _letters(e.title)[:14]
        found = None
        if len(key) >= 4:
            found = next((p for p in sorted(display) if p > prev and key in display[p]), None)
        if found is not None:
            out.append((found, "title"))
        elif e.printed_page - 1 in folios and folios[e.printed_page - 1] + 1 > prev:
            found = folios[e.printed_page - 1] + 1
            out.append((found, "folio"))
        else:
            out.append((None, "not-found"))
        if found is not None:
            prev = found
    return out


def title_case(text: str) -> str:
    """Display type in capitals ("GEOMETRIC TWINS") as the contents prints it."""
    if not text.isupper():
        return text
    small = {"a", "an", "and", "as", "at", "by", "for", "in", "of", "on", "or", "the", "to", "with"}

    def word(i: int, w: str) -> str:
        if len(w) > 1 and not re.search(r"[AEIOUY]", w):
            return w                       # an acronym: GDP, not Gdp
        w = w.lower()
        return w if (i and w in small) else w[:1].upper() + w[1:]
    return " ".join(word(i, w) for i, w in enumerate(text.split()))


def display_title(lines: list[Line], page: int) -> str:
    """A chapter-PDF's title: its display lines (>= 24pt) on the opening page.

    Numerals, the word "CHAPTER"/"Chapter N"/"Chapter I" and single letters
    (drop caps) are not title. White type is: Ganita Prakash 8 part 2 sets
    its titles white on a picture (hegp201.pdf p1).
    """
    rows = []
    for ln in lines:
        t = ln.text.strip()
        if (ln.page == page and ln.size >= 24 and len(t) > 1
                and not re.fullmatch(r"[\d\W]+", t)
                and not re.match(r"^chapter(\s+(\d+|[ivxlc]+))?$", t, re.I)):
            rows.append(ln)
    rows.sort(key=lambda ln: (ln.y0, ln.x0))
    # Lines in one size are one phrase; a change of size is a kicker and its
    # title: "Grassroots Democracy – Part 1" (24pt) over "Governance" (26pt),
    # fees110.pdf p1, reads "Grassroots Democracy – Part 1: Governance".
    seen: set[str] = set()
    groups: list[tuple[float, list[str]]] = []
    for ln in rows:
        if ln.text in seen:
            continue
        seen.add(ln.text)
        if groups and abs(groups[-1][0] - ln.size) <= 0.6:
            groups[-1][1].append(ln.text)
        else:
            groups.append((ln.size, [ln.text]))
    # a line broken after a hyphen joins without a space ("Baudhāyana-" /
    # "Pythagoras Theorem", hegp202.pdf p1)
    return ": ".join(title_case(_clean(" ".join(parts).replace("- ", "-")))
                     for _, parts in groups)
