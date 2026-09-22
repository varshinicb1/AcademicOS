"""The NCERT textbook heading extractor, run against the real PDFs.

Source (b) of the decomposition templates is "the textbook's own printed
headings". That claim is only worth anything if the thing that reads them is in
this repo and can be re-run: the first version of this work consumed prebuilt
heading trees copied in from a scratch directory, so the committed templates
could not be regenerated once that directory was gone.

So these tests read the actual books under
`C:/Users/varsh/OneDrive/Documents/Sarvam/ncert-dataset/textbooks` (raw data,
read-only, outside the repo) and skip where they are not present.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

TEXTBOOKS = Path("C:/Users/varsh/OneDrive/Documents/Sarvam/ncert-dataset/textbooks")
CLASS_6_SCIENCE = TEXTBOOKS / "science" / "class6_curiosity.pdf"
CLASS_6_SOCIAL = TEXTBOOKS / "chapters" / "fees1"


def _require(path: Path):
    if not path.exists():
        pytest.skip(f"NCERT textbook not present at {path}")
    pytest.importorskip("pymupdf")


@pytest.fixture(scope="module")
def class6_science():
    """Reading a 272-page book takes about half a minute, so every test in this
    module shares one extraction."""
    _require(CLASS_6_SCIENCE)
    from academicos.syllabus.textbook_headings import extract_chapters
    return extract_chapters(CLASS_6_SCIENCE, TEXTBOOKS)


@pytest.fixture(scope="module")
def class6_social():
    _require(CLASS_6_SOCIAL)
    from academicos.syllabus.textbook_headings import extract_chapters
    return extract_chapters(CLASS_6_SOCIAL, TEXTBOOKS)


def _chapter(chapters, name_fragment: str):
    return next(c for c in chapters if name_fragment.lower() in c.name.lower())


# ---------------- what the book actually prints ----------------

def test_it_reads_the_printed_numbered_headings_of_a_class_6_science_chapter(class6_science):
    """Curiosity's chapter 2 prints 2.1, 2.2 (with 2.2.1 and 2.2.2 inside it)
    and 2.3. Not a count assertion -- the words and the numbers both have to be
    the book's."""
    ch = _chapter(class6_science, "Diversity in the Living World")
    assert ch.number == 2
    assert [(t.number, t.name) for t in ch.topics] == [
        ("2.1", "Diversity in Plants and Animals Around Us"),
        ("2.2", "How to Group Plants and Animals?"),
        ("2.3", "Plants and Animals in Different Surroundings"),
    ]
    grouping = ch.topics[1]
    assert [(s.number, s.title) for s in grouping.subtopics] == [
        ("2.2.1", "How to group plants?"),
        ("2.2.2", "How to group animals?"),
    ]


def test_a_heading_wrapped_over_two_printed_lines_comes_back_whole(class6_science):
    """"2.3 Plants and Animals in Different" / "Surroundings" is one heading
    set over two lines; storing the first line alone would put a truncated
    topic name in front of a principal."""
    ch = _chapter(class6_science, "Diversity in the Living World")
    assert ch.topics[2].name == "Plants and Animals in Different Surroundings"


def test_every_extracted_heading_is_printed_verbatim_on_the_page_it_reports(class6_science):
    """The precision measurement, run rather than trusted: each heading's own
    words must appear on the page the extractor says it was printed on, and the
    heading number must be printed right before them. 71/71 nodes across the
    whole of Curiosity when this was written.

    The page text is put through the extractor's own `_clean` first, because
    some headings have a decorative bullet glyph between the number and the
    words that extracts as U+0007 ("6.3.1 <BEL>Observe and identify appearance
    of materials"). Dropping it is the thing being tested, not something to
    test around."""
    pymupdf = pytest.importorskip("pymupdf")
    from academicos.syllabus.textbook_headings import _clean

    doc = pymupdf.open(CLASS_6_SCIENCE)
    try:
        pages = {i: _clean(doc[i].get_text()) for i in range(doc.page_count)}
    finally:
        doc.close()

    checked = 0
    wrong = []
    for chapter in class6_science:
        for topic in chapter.topics:
            for number, title, page in (
                    [(topic.number, topic.name, topic.page)]
                    + [(s.number, s.title, s.page) for s in topic.subtopics]):
                checked += 1
                text = pages[page]
                words = " ".join(title.split())
                if words not in text:
                    wrong.append((number, title, page, "words not on the page"))
                elif number and f"{number} {words[:20]}" not in text:
                    # The number is printed immediately before the title, so a
                    # heading attached to the wrong number would show up here.
                    wrong.append((number, title, page, "number not before the words"))
    assert checked >= 60, "the extractor stopped finding Curiosity's headings"
    assert wrong == [], f"{len(wrong)} of {checked} headings are not printed as reported: {wrong[:5]}"


def test_body_prose_that_looks_like_a_heading_number_is_not_one(class6_science):
    """Why the rule is font metrics AND numbering, not numbering alone.
    Curiosity's prose is full of "37.0 degC", "Fig. 2.6 that the plants and
    animals", "10.4 cm-1.0 cm = 9.4 cm" -- a regex over the plain text picks
    all of them up. None may reach a topic name."""
    pymupdf = pytest.importorskip("pymupdf")

    doc = pymupdf.open(CLASS_6_SCIENCE)
    try:
        raw = [ln.strip() for i in range(doc.page_count)
               for ln in doc[i].get_text().splitlines()]
    finally:
        doc.close()
    numbered = re.compile(r"^\d{1,2}(\.\d{1,2}){1,2}\s+\S")
    naive = [ln for ln in raw if numbered.match(ln)]

    extracted = {t.name for c in class6_science for t in c.topics}
    extracted |= {s.title for c in class6_science for t in c.topics for s in t.subtopics}

    assert len(naive) > len(extracted), (
        "the naive rule is supposed to be the loose one; the comparison is stale")
    for name in extracted:
        assert not re.match(r"^[\u00b0%]|^(cm|km|g|kg)\b", name), name
    # The measurements the naive rule sweeps in are not in the result.
    assert not any("°C" in n for n in extracted)


def test_a_chapter_the_book_prints_no_headings_inside_is_reported_not_dropped(class6_science):
    """Curiosity's chapters 1 and 9 genuinely print no numbered heading (only
    "Activity 9.1:" boxes). Returning them with no topics is the honest answer;
    dropping them would make "this chapter has no breakdown" indistinguishable
    from "the extractor missed it", and item 5c is about reporting exactly
    that difference."""
    separation = _chapter(class6_science, "Methods of Separation")
    assert separation.topics == ()
    assert sum(1 for c in class6_science if c.topics) >= 9


def test_the_chapter_title_is_the_books_own_full_title(class6_science):
    """A title cut short at its first line ("Mindful Eating: A Path") would not
    match the syllabus chapter it belongs to, and the export matches on the
    title."""
    names = {c.name for c in class6_science}
    assert "Mindful Eating: A Path to a Healthy Body" in names
    assert "Living Creatures: Exploring their Characteristics" in names


# ---------------- the unnumbered books ----------------

def test_a_book_that_numbers_nothing_is_read_by_size_tier(class6_social):
    """NCERT's Class 6 Social Science book ships as one PDF per chapter and
    numbers no section. Its headings are distinguished only by face and size,
    so they are read as tiers -- and the chapter titles still have to be the
    book's own."""
    names = {c.name for c in class6_social}
    assert "Oceans and Continents" in names
    ch = _chapter(class6_social, "Oceans and Continents")
    assert [t.name for t in ch.topics] == [
        "The Distribution of Water and Land on the Earth",
        "Oceans", "Continents", "Oceans and Life",
    ]
    assert all(t.number is None for t in ch.topics)
    assert [s.title for s in ch.topics[1].subtopics] == ["Oceans and disasters"]


def test_a_recurring_box_label_is_not_mistaken_for_a_heading(class6_social):
    """The rule that makes the tier approach safe. "LET'S EXPLORE", "DON'T MISS
    OUT" and "Questions" are all bold, all larger than the body text, and all
    printed dozens of times -- a heading is written once, so a class whose
    lines repeat the same words is furniture, not a section."""
    topics = {t.name.lower() for c in class6_social for t in c.topics}
    topics |= {s.title.lower() for c in class6_social for t in c.topics
               for s in t.subtopics}
    for label in ("let's explore", "let’s explore", "don't miss out",
                  "don’t miss out", "think about it", "questions"):
        assert label not in topics, f"{label!r} was read as a section heading"
