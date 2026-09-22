"""Chapter -> topic -> subtopic headings read from the NCERT textbooks.

Every fixture is real text-layer output (``tests/_textbook_lines.py``, keyed by
file with the 1-based page on each line). What is asserted is what the page
prints, read off the PDF page cited beside it -- because each rule in the
extractor was forced by something a made-up snippet would not have: a heading
printed five times over itself, a sub-heading set 0.43pt larger on one page, a
history book that numbers its sections afresh in every chapter.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _textbook_lines import CHAPTERS, CONTENTS_PAGES, JESC101_P2_HEADING_RAW  # noqa: E402

from academicos.syllabus import textbook_headings as th  # noqa: E402


def _lines(key: str) -> list[th.Line]:
    src = CHAPTERS.get(key) or CONTENTS_PAGES[key]
    return [th.Line(*t) for t in src]


def _outline(heads: list[th.Heading]) -> list[tuple]:
    return [(h.level, h.number, h.name) for h in heads]


# --------------------------------------------------------------------------- #
# reading the page
# --------------------------------------------------------------------------- #

def test_overprinted_heading_is_read_once():
    # jesc101.pdf p2: the heading is printed five times, nudged apart, and
    # kerning splits it into "1.1 CHEMIC" / "AL EQUA" / "TIONS" pieces.
    lines = th.lines_from_rawdict(2, JESC101_P2_HEADING_RAW)
    texts = [ln.text for ln in lines]
    assert texts == ["1.1 CHEMICAL EQUATIONS"]


# --------------------------------------------------------------------------- #
# numbered books
# --------------------------------------------------------------------------- #

def test_numbered_headings_found_in_order_class10_science():
    heads, kind = th.chapter_headings(_lines("jesc101"), 1)
    assert kind == "numbered"
    assert _outline(heads) == [          # jesc101.pdf pp2, 3, 6, 8, 10-13
        (1, "1.1", "CHEMICAL EQUATIONS"),
        (2, "1.1.1", "Writing a Chemical Equation"),
        (2, "1.1.2", "Balanced Chemical Equations"),
        (1, "1.2", "TYPES OF CHEMICAL REACTIONS"),
        (2, "1.2.1", "Combination Reaction"),
        (2, "1.2.2", "Decomposition Reaction"),
        (2, "1.2.3", "Displacement Reaction"),
        (2, "1.2.4", "Double Displacement Reaction"),
        (2, "1.2.5", "Oxidation and Reduction"),
        (1, "1.3", "HAVE YOU OBSERVED THE EFFECTS OF OXIDATION REACTIONS IN EVERYDAY LIFE?"),
        (2, "1.3.1", "Corrosion"),
        (2, "1.3.2", "Rancidity"),
    ]
    assert [h.page for h in heads][:4] == [2, 3, 3, 6]


def test_activities_boxes_and_end_matter_are_not_topics():
    lines = _lines("jesc101")
    # the page really prints them, set apart like headings ...
    printed = {ln.text for ln in lines}
    assert {"Activity 1.1", "What you have learnt", "Do You Know?"} <= printed
    # ... and none becomes a topic
    names = {h.name for h in th.chapter_headings(lines, 1)[0]}
    assert not any(n.startswith(("Activity", "What you", "Do You", "Q U E S", "E X E R"))
                   for n in names)


def test_captions_and_activities_rejected_class6_science():
    lines = _lines("class6_curiosity_ch2")
    printed = {ln.text for ln in lines}
    # class6_curiosity.pdf p28-29, p40: an activity, a table caption, a box
    assert "Activity 2.1: Let us explore and record" in printed
    assert "Table 2.1: Observations of different plants around us" in printed
    assert "Know a scientist" in printed
    heads, kind = th.chapter_headings(lines, 2)
    assert kind == "numbered"
    assert _outline(heads) == [
        (1, "2.1", "Diversity in Plants and Animals Around Us"),         # p28
        (1, "2.2", "How to Group Plants and Animals?"),                  # p32
        (2, "2.2.1", "How to group plants?"),                            # p33
        (2, "2.2.2", "How to group animals?"),                           # p38
        (1, "2.3", "Plants and Animals in Different Surroundings"),     # p41, two lines
    ]


def test_history_numbers_sections_afresh_per_chapter():
    # jess302.pdf (Nationalism in India, chapter 2) numbers "1 ...", "1.1 ...":
    # read as chapter-prefixed it would keep only the "2.x" subsections.
    heads, kind = th.chapter_headings(_lines("jess302"), 2)
    assert kind == "section"
    assert [(h.level, h.name) for h in heads if h.level == 1] == [
        (1, "The First World War, Khilafat and Non-Cooperation"),       # p2
        (1, "Differing Strands within the Movement"),                   # p6
        (1, "Towards Civil Disobedience"),                              # p10
        (1, "The Sense of Collective Belonging"),                       # p18
    ]
    assert [h.name for h in heads if h.number and h.number.startswith("1.")] == [
        "The Idea of Satyagraha", "The Rowlatt Act", "Why Non-cooperation?"]


# --------------------------------------------------------------------------- #
# unnumbered books
# --------------------------------------------------------------------------- #

def test_unnumbered_bold_headings_new_social_science_book():
    lines = _lines("fees102")
    printed = {ln.text.strip() for ln in lines}
    # fees102.pdf p2-13: box labels and end matter, typeset in bold display type
    assert {"LET’S EXPLORE", "Before we move on …", "Questions, activities and projects"} <= printed
    heads, kind = th.chapter_headings(lines, 2)
    assert kind == "unnumbered"
    assert all(h.kind == "unnumbered" and h.number is None for h in heads)
    assert [(h.level, h.name, h.page) for h in heads] == [
        (1, "The Distribution of Water and Land on the Earth", 3),     # 17pt, two lines
        (1, "Oceans", 5),
        (2, "Oceans and disasters", 7),                                 # 15pt
        (1, "Continents", 8),
        (2, "Islands", 10),
        (1, "Oceans and Life", 11),
    ]


def test_chapter_without_sections_gets_no_topics_not_its_epigraph():
    lines = _lines("class6_curiosity_ch9")
    # class6_curiosity.pdf p181 opens with a Kabir doha, 18pt bold; the
    # chapter's only other set-apart lines are activities and boxes.
    assert any(ln.text.startswith("साधु ऐसा चाहिए") and ln.size == 18.0 for ln in lines)
    heads, kind = th.chapter_headings(lines, 9)
    assert (heads, kind) == ([], "none")


def test_heading_in_a_font_named_regular_is_still_found():
    # fees105.pdf p3, p7: the PDF names the heading font NotoSerif-Regular, but
    # it is printed 17pt in red on 13pt body -- without these the chapter had
    # no topics at all.
    heads, kind = th.chapter_headings(_lines("fees105"), 5)
    assert kind == "unnumbered"
    assert [(h.level, h.name, h.page) for h in heads] == [
        (1, "How Indians Named India", 3),
        (1, "How Foreigners Named India", 7),
    ]


def test_one_heading_style_at_two_sizes_is_one_level():
    # gees105.pdf sets its sub-headings at 15pt (p6, p9, p19, p28-29) and at
    # 15.43pt (pp17-18); read as two sizes, 15pt fell below the subtopic level.
    heads, _ = th.chapter_headings(_lines("gees105"), 5)
    subs = [h.name for h in heads if h.level == 2]
    assert subs == [
        "Features of an empire", "Trade, trade routes and guilds",
        "The story of Kauṭilya", "The rise of Chandragupta Maurya",
        "Kauṭilya’s concept of a kingdom",
        "Some Contributions of the Mauryas", "Life and people", "Art and architecture",
    ]
    assert [h.name for h in heads if h.level == 1][:2] == ["What is an Empire?",
                                                            "The Rise of Magadha"]


def test_two_column_page_is_read_column_by_column():
    # jess403.pdf p10: "Caste and politics" closes the left column (y=607);
    # its first sub-section "Caste inequalities" opens the right one (y=71).
    order = [ln.text for ln in th.reading_order(_lines("jess403_p10"))
             if ln.text in ("Caste and politics", "Caste inequalities")]
    assert order == ["Caste and politics", "Caste inequalities"]


# --------------------------------------------------------------------------- #
# contents pages
# --------------------------------------------------------------------------- #

def test_contents_title_wrapped_after_its_page_number():
    entries = th.parse_contents(_lines("class9_ganita_manjari_p19"), [19])
    assert [(e.number, e.printed_page) for e in entries][:2] == [(1, 1), (2, 16)]
    assert entries[7].title == "Predicting What Comes Next: Exploring Sequences and Progressions"
    # "Graph Paper" (p197) is listed, but not as a "Chapter N"
    assert [e.number for e in entries].count(None) == 1
    assert entries[-1].title == "Graph Paper" and entries[-1].number is None


def test_contents_title_wrapped_before_its_page_number():
    entries = th.parse_contents(_lines("class8_poorvi_p15"), [15])
    titles = [e.title for e in entries]
    assert len(titles) == 15                            # 5 units x 3 lessons
    assert titles[3] == "A Tale of Valour: Major Somnath Sharma and the Battle of Badgam"
    assert titles[-1] == ("Bibha Chowdhuri: The Beam of Light that Lit the Path for "
                          "Women in Indian Science")
    assert "Unit 2: Values and Dispositions" not in titles


# --------------------------------------------------------------------------- #
# ids
# --------------------------------------------------------------------------- #

def test_ids_are_stable_slugs_across_rebuilds():
    heads, _ = th.chapter_headings(_lines("jesc101"), 1)
    first, _ = th.build_topics("chemical-reactions-and-equations", heads)
    again, _ = th.build_topics("chemical-reactions-and-equations",
                               th.chapter_headings(_lines("jesc101"), 1)[0])
    ids = [t["id"] for t in first] + [s["id"] for t in first for s in t["subtopics"]]
    assert ids == [t["id"] for t in again] + [s["id"] for t in again for s in t["subtopics"]]
    assert first[0]["id"] == "chemical-reactions-and-equations/chemical-equations"
    assert first[0]["subtopics"][0]["id"] == (
        "chemical-reactions-and-equations/chemical-equations/writing-a-chemical-equation")


def test_slug_ignores_punctuation_and_keeps_devanagari():
    assert th.slug("India’s Long Road to Independence") == "india-s-long-road-to-independence"
    assert th.slug("Reﬂection of Light") == th.slug("Reflection of Light")
    assert th.slug("दो बैलों की कथा").startswith("द")


def test_same_heading_twice_gets_distinct_ids():
    heads = [th.Heading(1, "Introduction", 1, None, "unnumbered"),
             th.Heading(1, "Introduction", 9, None, "unnumbered")]
    topics, _ = th.build_topics("ch", heads)
    assert [t["id"] for t in topics] == ["ch/introduction", "ch/introduction-2"]
