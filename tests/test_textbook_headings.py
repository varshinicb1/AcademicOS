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

import pytest

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


def test_table_captions_are_not_subtopics_democratic_politics():
    # jess403.pdf p4 and p13 caption their tables in 13pt orange bold -- the
    # sub-section type -- directly above the header row of the grid
    # ("Activities | Men | Women", "Caste and Community groups | Rural | Urban").
    # the chapter's set-apart lines, all of pp4 and 13, and p10 whole (the
    # two-column page, kept once under "jess403_p10")
    lines = sorted(_lines("jess403") + _lines("jess403_p10"), key=lambda ln: ln.page)
    printed = {ln.text for ln in lines}
    assert {"Daily time use (hours: minutes)",
            "Percentage of population living below the poverty line, 1999–— 2000"} <= printed
    heads, kind = th.chapter_headings(lines, 3)
    assert kind == "unnumbered"
    assert [(h.level, h.name, h.page) for h in heads] == [   # jess403.pdf pp2-14
        (1, "Gender and politics", 2),
        (2, "Public/private division", 2),
        (2, "Women’s political representation", 6),
        (1, "Religion, communalism and politics", 8),
        (2, "Communalism", 8),
        (2, "Secular state", 9),
        (1, "Caste and politics", 10),
        (2, "Caste inequalities", 10),
        (2, "Caste in politics", 12),
        (2, "Politics in caste", 14),
    ]


# The row printed under a real heading, as the page sets it: (x0, x1, text,
# size, bold). None of these is the header row of a table.
_ROWS_UNDER_HEADINGS = {
    # hees105.pdf p7: justification spreads "of the Class Representative"
    # into four pieces 14pt apart
    "justified words": [(64.2, 78.8, "of", 12.0, False), (93.1, 114.7, "the", 12.0, False),
                        (129.0, 161.1, "Class", 12.0, False),
                        (175.4, 265.1, "Representative", 12.0, False)],
    # class9_understanding_society_part1.pdf p73, under "Monsoon": a body
    # line with a bold key word, beside a margin note
    "margin note": [(71.4, 317.6, "The climate of India is strongly influenced by", 12.0, False),
                    (318.2, 369.7, "monsoon", 12.0, True),
                    (369.8, 434.3, "winds. The", 12.0, False),
                    (458.4, 513.1, "Monsoon:", 11.5, True)],
    # gees202.pdf p6, under "India and Pakistan": a map's degree labels
    "map labels": [(129, 146, "50°E", 8.0, False), (212, 229, "60°E", 8.0, False),
                   (292, 310, "70°E", 8.0, False), (373, 390, "80°E", 8.0, False)],
}


@pytest.mark.parametrize("row", list(_ROWS_UNDER_HEADINGS))
def test_a_heading_over_text_or_a_map_is_not_a_table_caption(row):
    y = 426.9
    lines = [th.Line(7, "A heading over body text", 15.0, "NotoSerif-Bold", True, 35395,
                     64.2, y, 403.4, y + 21.8)]
    for x0, x1, text, size, bold in _ROWS_UNDER_HEADINGS[row]:
        lines.append(th.Line(7, text, size, "NotoSerif-Bold" if bold else "NotoSerif-Regular",
                             bold, 2301728, x0, y + 30, x1, y + 47))
    lines += [th.Line(7, "body text " * 6, 12.0, "NotoSerif-Regular", False, 2301728,
                      64.2, y + 47 + 17 * k, 434.5, y + 64 + 17 * k) for k in range(20)]
    assert [h.name for h in th.unnumbered_headings(lines)] == ["A heading over body text"]


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


# --------------------------------------------------------------------------- #
# review of 2026-09-22
# --------------------------------------------------------------------------- #

def test_wrapped_numbered_topic_keeps_its_place_and_its_subtopics():
    # class7_ganita_prakash.pdf p216: "5.4 Parallel and Perpendicular Lines in
    # Paper" / "Folding", 16pt bold on two lines, then the 14pt sub-head
    # "Notations" (p217). Found again by its text, the joined name is in no
    # single line: 5.4 sorted to the front and its sub-head went under 5.3.
    heads, kind = th.chapter_headings(_lines("class7_ganita_prakash_ch5"), 5)
    assert kind == "numbered"
    assert [h.number for h in heads if h.level == 1] == [f"5.{k}" for k in range(1, 10)]
    assert [h.page for h in heads] == sorted(h.page for h in heads)
    topics, orphans = th.build_topics("lines-and-angles", heads)
    assert orphans == 0
    by_number = {t["number"]: t for t in topics}
    assert by_number["5.4"]["name"] == "Parallel and Perpendicular Lines in Paper Folding"
    assert [s["name"] for s in by_number["5.4"]["subtopics"]] == ["Notations"]      # p217
    assert [s["name"] for s in by_number["5.1"]["subtopics"]] == ["Measurements and Geometry"]
    assert by_number["5.3"]["subtopics"] == []


def test_unnumbered_subtopics_refuses_a_topic_it_cannot_place():
    lines = th.reading_order(_lines("class7_ganita_prakash_ch5"))
    unplaced = th.Heading(1, "Parallel and Perpendicular Lines in Paper Folding", 216, "5.4")
    with pytest.raises(ValueError):
        th.unnumbered_subtopics(lines, [unplaced])


def test_panel_labels_are_not_subtopics_class6_curiosity():
    # class6_curiosity.pdf pp249-272: "More to know!" is printed 16 times and
    # "Do you know?" 5 times in 14pt ExtraBold, the chapter's most used
    # sub-head type; the sections under 12.3 are 15pt ("The Sun", p256).
    heads, kind = th.chapter_headings(_lines("class6_curiosity_ch12"), 12)
    assert kind == "numbered"
    subs = [h.name for h in heads if h.level == 2]
    assert subs == ["The Sun", "Planets", "Natural Satellites", "Asteroids", "Comets"]


def test_ganita_prakash_sub_sections_are_the_blue_heads_not_the_panels():
    # class6_ganita_prakash.pdf pp200-221: 14pt blue sub-sections; 13pt black
    # "Matha Pachchi!" (a game, p204), "Teacher's Note" (boxed, pp207-213),
    # "Let's Explore!" (twice, p212) and run-in heads are not subtopics.
    heads, _ = th.chapter_headings(_lines("class6_ganita_prakash_ch6"), 6)
    topics, _ = th.build_topics("perimeter-and-area", heads)
    assert [(t["number"], [s["name"] for s in t["subtopics"]]) for t in topics] == [
        ("6.1", ["Perimeter of a rectangle", "Perimeter of a square", "Perimeter of a triangle",
                 "Perimeter of a regular polygon"]),
        ("6.2", []),
        ("6.3", []),
    ]


@pytest.mark.parametrize("label", [
    "Do you know?", "Do You Know?", "Let’s Explore!", "Before we move on...",
    "Before we move on …", "Before we move on…", "Additional Activity / Project",
    "Additional Projects / Activities", "Suggested Readings", "Suggested Reading",
    "More to know!", "More to do!", "Think it over!", "Teacher’s Note", "Discussion",
    "Let’s Play a Game #1", "Puzzle!", "True or False", "True or false",
    "Mind the Mistake, Mend the Mistake!", "Figure it Out", "Activity 4.1: Let us explore",
    "Box 2", "Summary:",
])
def test_box_labels_match_whatever_follows_the_key(label):
    assert th._not_a_topic(label)


@pytest.mark.parametrize("name", [
    "Sources of Energy", "Puzzles and Patterns", "Projectile Motion", "Discussing Democracy",
    "Moreover", "Tables and Chairs",
])
def test_headings_that_only_start_like_a_label_are_kept(name):
    assert not th._not_a_topic(name)


def test_a_numbered_panel_is_the_books_section():
    # gegp207.pdf p18 numbers it "7.3"; class6_ganita_prakash.pdf p69 does not
    assert not th._not_a_topic("Mind the Mistake, Mend the Mistake", numbered=True)
    assert th._not_a_topic("Mind the Mistake, Mend the Mistake", numbered=False)


@pytest.mark.parametrize("name,cut", [
    ("Steps to follow: Start with a", True),       # class6_ganita_prakash.pdf p97
    ("More to", True),                              # class6_curiosity.pdf p96
    ("The Proof of Irrationality of", True),
    ("Settling In", False), ("Powers of 10", False), ("Where to?", False),
    ("What is soluble in water; what is not?", False),
])
def test_dangling_line_ends(name, cut):
    assert th._dangling(name) is cut


def test_numbered_heading_in_lower_case_is_read_when_next_in_sequence():
    # jemh105.pdf p8: "5.3 nth Term of an AP", 12pt Times-Bold
    heads, _ = th.chapter_headings(_lines("jemh105"), 5)
    assert [(h.number, h.name) for h in heads] == [
        ("5.1", "Introduction"), ("5.2", "Arithmetic Progressions"),
        ("5.3", "nth Term of an AP"), ("5.4", "Sum of First n Terms of an AP")]


def test_numbered_subtopic_in_lower_case_class10_science():
    # jesc102.pdf p13: "2.4.2 pH of Salts", 14pt coloured
    heads, _ = th.chapter_headings(_lines("jesc102"), 2)
    assert [h.number for h in heads if h.number.startswith("2.4")] == [
        "2.4", "2.4.1", "2.4.2", "2.4.3", "2.4.4"]
    assert next(h.name for h in heads if h.number == "2.4.2") == "pH of Salts"


def test_numbered_heading_opening_with_of():
    # gegp205.pdf p1: "5.1 Of Questions and Statements", 16pt bold
    heads, _ = th.chapter_headings(_lines("gegp205"), 5)
    assert [(h.number, h.name) for h in heads if h.level == 1] == [
        ("5.1", "Of Questions and Statements"), ("5.2", "Representative Values"),
        ("5.3", "Visualising Data"), ("5.4", "Data Detective")]


def test_hanging_second_line_of_a_numbered_heading_is_joined():
    # jesc102.pdf: every numbered heading is read whole, none ends mid-phrase
    heads, _ = th.chapter_headings(_lines("jesc102"), 2)
    assert not [h.name for h in heads if th._dangling(h.name)]
    assert next(h.name for h in heads if h.number == "2.1.3") == (
        "How do Metal Carbonates and Metal Hydrogencarbonates React with Acids?")


# --------------------------------------------------------------------------- #
# Task 7021: lettered sub-headings
# --------------------------------------------------------------------------- #

def test_lettered_sub_headings_are_subtopics_with_clean_names_gees102():
    # gees102.pdf pp5-11: "Weather Instruments" (17pt) is followed by "a)
    # Temperature" .. "e) Humidity", 15pt bold in the sub-section colour. Read
    # as a title, "a) ..." starts in lower case and all five were dropped.
    heads, kind = th.chapter_headings(_lines("gees102"), 2)
    assert kind == "unnumbered"
    assert [(h.level, h.name, h.page) for h in heads] == [
        (1, "Weather and its Elements", 2),
        (2, "What is weather?", 2),
        (2, "Observing Nature’s clues", 4),
        (1, "Weather Instruments", 5),
        (2, "Temperature", 5),
        (2, "Precipitation", 7),
        (2, "Atmospheric pressure", 8),
        (2, "Wind", 10),
        (2, "Humidity", 11),
        (1, "Weather Stations", 13),
        (2, "An automated weather station", 13),
        (1, "Predicting the Weather", 13),
    ]


def test_capital_lettered_sub_headings_lose_their_label_fees114():
    # fees114.pdf pp2, 5, 7: "A. Primary activities" .. "C. Tertiary
    # activities" were kept, with the "A." in the name.
    heads, _ = th.chapter_headings(_lines("fees114"), 14)
    topics, orphans = th.build_topics("ch", heads)
    assert orphans == 0
    by_name = {t["name"]: [s["name"] for s in t["subtopics"]] for t in topics}
    assert by_name["The Classification of Economic Activities into Economic Sectors"] == [
        "Primary activities", "Secondary activities", "Tertiary activities"]


@pytest.mark.parametrize("text,label,rest", [
    ("a) Temperature", "a", "Temperature"),
    ("a. What are the Vedas?", "a", "What are the Vedas?"),
    ("(c) Proximity to the sea", "c", "Proximity to the sea"),
    ("A. Primary activities", "A", "Primary activities"),
    ("B) Secondary activities", "B", "Secondary activities"),
    ("A Tale of Two Cities", None, "A Tale of Two Cities"),       # no label
    ("E. F. Hayward", None, "E. F. Hayward"),                     # initials
    ("Weather Instruments", None, "Weather Instruments"),
])
def test_letter_label_is_read_off_the_front(text, label, rest):
    assert th.letter_label(text) == (label, rest)


def test_a_lone_initial_is_not_a_lettered_heading():
    # "O. Henry" (an author's name in heading type) is not item O of a list:
    # a letter counts as a label only in a run that starts at a/A.
    y = 100.0
    lines = [th.Line(1, "The Gift", 17.0, "NotoSerif-Bold", True, 35395, 64, y, 300, y + 20),
             th.Line(1, "O. Henry", 15.0, "NotoSerif-Bold", True, 35395, 64, y + 60, 300, y + 78)]
    lines += [th.Line(1, "body text " * 6, 12.0, "NotoSerif-Regular", False, 2301728,
                      64, y + 100 + 17 * k, 434, y + 117 + 17 * k) for k in range(30)]
    assert [(h.level, h.name) for h in th.unnumbered_headings(lines)] == [
        (1, "The Gift"), (2, "O. Henry")]


def test_lettered_headings_below_subtopic_level_are_returned_apart_class9_society():
    # class9_understanding_society_part1.pdf pp101-107: under the topic
    # "Bronze Age Civilisations Outside India" (17pt) and its subtopic
    # "Mesopotamian Civilisation" (15pt) the book sets "a. The Sumerians" ..
    # "d. The Babylonians" in 13pt bold italic, a third level. The tree has
    # two levels, so they come back as level 3 -- named without the letter,
    # for the build to list as not represented -- and never as subtopics.
    heads, kind = th.chapter_headings(_lines("class9_understanding_society_ch4"), 4)
    assert kind == "unnumbered"
    assert [(h.name, h.page) for h in heads if h.level == 3] == [
        ("The Sumerians", 103), ("The Akkadians", 105),
        ("The Assyrians", 107), ("The Babylonians", 107)]
    below: list = []
    topics, orphans = th.build_topics("ch", heads, below)
    # the one orphan is p87 "The Invention of Writing: Before and After", 15pt
    # before the first topic; the level-3 headings are not counted as orphans
    assert orphans == 1
    assert [(b["name"], b["under"]) for b in below] == [
        (n, "ch/bronze-age-civilisations-outside-india/mesopotamian-civilisation")
        for n in ("The Sumerians", "The Akkadians", "The Assyrians", "The Babylonians")]
    by_name = {t["name"]: [s["name"] for s in t["subtopics"]] for t in topics}
    assert by_name["Bronze Age Civilisations Outside India"] == [
        "Mesopotamian Civilisation", "Egyptian Civilisation", "The Chinese Civilisation"]
    # a 13pt heading with no letter at that size stays ignored, as before
    assert "How do we know what we know about China?" not in {h.name for h in heads}
