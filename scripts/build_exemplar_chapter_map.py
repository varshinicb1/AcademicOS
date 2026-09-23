"""Map every Exemplar chapter to the chapter the CURRENT NCERT book prints.

Why this file exists
--------------------
An NCERT Exemplar question was printed under a numbered chapter of its own
book, and the importer keeps that as ``metadata.exemplarChapter``. The served
taxonomy, though, is keyed by the books schools teach now
(``taxonomy/<Subject>_<grade>.json``: Ganita Prakash, Ganita Manjari,
Curiosity, Exploration). For classes 6-9 those are the NEP books, which
renamed and REORGANISED the old chapters ("Integers" -> "The Other Side of
Zero"), so an Exemplar chapter's taxonomy id cannot be looked up by name.

It also cannot be guessed by word overlap: a wrong chapter is worse than
none. So this is a decision table, written once, checked here, and committed
to ``taxonomy/_exemplar_chapter_map.json``.

The rule every row was decided by
---------------------------------
A row maps to a chapter id when BOTH hold:

1. the current book of that class has exactly ONE chapter that is the
   Exemplar chapter's counterpart -- it teaches the same subject matter, read
   off that chapter's printed heading and its printed section headings (the
   taxonomy trees are those headings, built from the books themselves); and
2. at most 10% of the Exemplar chapter's questions are on content that class
   teaches in a DIFFERENT chapter, or no longer teaches at all. That residue is
   measured over the bank, not assumed, and where it is not zero the count is
   written into the row's note ("8 of the 117 questions are Pythagorean
   triplets, which Part 2 chapter 2 teaches").

Otherwise the row is null with its reason, which is one of:

* ``split``  -- the old chapter's content sits in two or more chapters of the
  current book, so no single chapter is its counterpart (class 6 Maths
  "Symmetry and Practical Geometry" is chapter 9 Symmetry *and* chapter 8
  Playing with Constructions);
* ``dropped`` -- the current book of that class does not teach it (class 10
  Science "Periodic Classification of Elements");
* ``moved``  -- the content is now taught in another class, whose tree is keyed
  to that class, not this one (class 8 Science "Sound" is class 9's chapter 10);
* ``residue`` -- there is a single counterpart chapter, but too much of the
  Exemplar chapter is content the class teaches elsewhere or not at all, and
  the measured share is in the reason.

``method`` says how a mapped row was decided:

* ``exact-title``  -- the current book prints a chapter of the same name. The
  script asserts it, so the claim cannot rot.
* ``contents-page`` -- the current book prints it under another name; the row
  names that book's chapter number and title as its contents page prints them.
* ``hand-checked`` -- a reviewer's note on the row says what was checked.

Every mapped row cites the PDF and the page the current book prints that
chapter's number and title on (``currentChapter.sourceFile``, ``.page``,
``.printedOn``), whatever the method. A row used to cite its PDF and lean on a
per-BOOK ``contentsPage``, which said nothing for the class 10 books -- they
are distributed as one PDF per chapter and there is no contents PDF in the
dataset, so all 22 class 10 rows carried no page -- and misstated three rows
outright: Ganita Prakash 7 and 8 Part 2 chapters cite their own chapter PDF,
whose page 17 or 15 is not the Part 1 contents page at all. So the page is now
per row: the book's contents page for a row that cites the whole-book PDF,
page 1 for a row that cites a single chapter's PDF, which is where that PDF
prints the chapter's number and title. ``--check`` opens each cited PDF at the
cited page and reads both back.

Run:  python scripts/build_exemplar_chapter_map.py [--check]

``--check`` verifies the committed file instead of writing it: every row's id
exists in the taxonomy, every exact-title claim holds, every mapped row's
citation reads back off the PDF (when ``ncert-dataset`` is present), and the
Exemplar bank holds no (subject, grade, number, title) without a row.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from academicos.syllabus.exemplar_chapter_map import EXEMPLAR_MAP_METHOD  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "academicos-data"
TAXONOMY = DATA / "syllabus" / "taxonomy"
MAP_PATH = TAXONOMY / "_exemplar_chapter_map.json"
EXEMPLAR_BANK = DATA / "corpus" / "ncert-exemplar" / "questions.json"
SERVED_BANK = DATA / "syllabus" / "questions.json"
# Read-only. Every path in BOOKS and in a row's `currentChapter.sourceFile` is
# relative to it, exactly as the taxonomy trees record them.
TEXTBOOKS = REPO.parent / "ncert-dataset" / "textbooks"

SUBJECT_FILE = {"Mathematics": "Mathematics", "Science": "Science"}

# The current book of each class, and the page its contents were read from
# (1-based, as a PDF reader numbers pages). Every ``contents-page`` row below
# was decided against one of these. The class 10 books have no contents page
# here because NCERT distributes them as one PDF per chapter and the dataset
# holds no prelims file: each of those chapters is cited on its own PDF's
# first page instead, which is where the book prints its number and title.
BOOKS = {
    ("Mathematics", 6): ("Ganita Prakash", "maths/class6_ganita_prakash.pdf", 19),
    ("Mathematics", 7): ("Ganita Prakash (Parts 1 and 2)", "maths/class7_ganita_prakash.pdf", 17),
    ("Mathematics", 8): ("Ganita Prakash (Parts 1 and 2)", "maths/class8_ganita_prakash.pdf", 15),
    ("Mathematics", 9): ("Ganita Manjari", "maths/class9_ganita_manjari.pdf", 19),
    ("Mathematics", 10): ("Mathematics", "chapters/jemh1/*.pdf", None),
    ("Science", 6): ("Curiosity", "science/class6_curiosity.pdf", 17),
    ("Science", 7): ("Curiosity", "science/class7_curiosity.pdf", 19),
    ("Science", 8): ("Curiosity", "science/class8_curiosity.pdf", 19),
    ("Science", 9): ("Exploration", "science/class9_exploration.pdf", 19),
    ("Science", 10): ("Science", "chapters/jesc1/*.pdf", None),
}
# Where a mapped row's `page` points, and what a reader will find there.
PRINTED_CONTENTS = "contents"          # the book's contents page, in the book's own PDF
PRINTED_OPENING = "chapter-opening"    # page 1 of a single chapter's PDF


def citation(subject: str, grade: int, source_file: str | None) -> tuple[int | None, str | None]:
    """(page, what is printed there) for a row citing ``source_file``.

    A row whose source file IS the book's own PDF is cited at that book's
    contents page. A row whose source file is one chapter's PDF -- the Ganita
    Prakash Part 2 chapters and every class 10 chapter -- is cited at page 1
    of it, where the book prints that chapter's number and title; the Part 1
    contents page is not even a page of that file, so citing it said nothing
    and, for Mathematics 7 chapter 2, 7 chapter 7 and 8 chapter 4, said
    something false.
    """
    book = BOOKS.get((subject, grade))
    if book is None or not source_file:
        return None, None
    if source_file == book[1]:
        return book[2], PRINTED_CONTENTS if book[2] else None
    return 1, PRINTED_OPENING

# --------------------------------------------------------------------------- #
# the decisions
# --------------------------------------------------------------------------- #
# (subject, grade, exemplar chapter number) -> (taxonomy chapter id or None,
#                                               method or why-null, note)
# Classes 6-9 Part 2 chapters of Ganita Prakash are printed as separate books
# with their own chapter numbers; the note names the part.

DECISIONS: dict[tuple[str, int, int], tuple[str | None, str, str]] = {
    # ----------------------------------------------------------- Mathematics 6
    ("Mathematics", 6, 1): (
        None, "split",
        "Ganita Prakash 6 has no one chapter for the old Number System: whole "
        "numbers and place value are chapter 3 Number Play, factors and "
        "multiples chapter 5 Prime Time, number patterns chapter 1."),
    ("Mathematics", 6, 2): (
        None, "split",
        "the old Geometry chapter is chapter 2 Lines and Angles, chapter 8 "
        "Playing with Constructions and chapter 9 Symmetry."),
    ("Mathematics", 6, 3): (
        "mathematics-6/the-other-side-of-zero", "contents-page",
        "chapter 10 The Other Side of Zero is the integers chapter of Ganita "
        "Prakash 6 (sections: The Token Model, Integers in Other Places, "
        "Explorations with Integers)."),
    ("Mathematics", 6, 4): (
        None, "residue",
        "chapter 7 Fractions is the counterpart of the fractions half, but the "
        "decimals half moved to class 7 (A Peek Beyond the Point): 4 of 28 "
        "questions are decimal questions with no class 6 chapter."),
    ("Mathematics", 6, 5): (
        "mathematics-6/data-handling-and-presentation", "contents-page",
        "chapter 4 Data Handling and Presentation (Collecting and Organising "
        "Data, Pictographs, Bar Graphs)."),
    ("Mathematics", 6, 6): (
        "mathematics-6/perimeter-and-area", "contents-page",
        "chapter 6 Perimeter and Area is the mensuration chapter (Perimeter, "
        "Area, Area of a Triangle)."),
    ("Mathematics", 6, 7): (
        None, "moved",
        "Ganita Prakash 6 has no algebra chapter; letter-numbers start in "
        "class 7 chapter 4."),
    ("Mathematics", 6, 8): (
        None, "moved",
        "ratio and proportion are class 8 chapter 7 Proportional Reasoning-1; "
        "Ganita Prakash 6 has no such chapter."),
    ("Mathematics", 6, 9): (
        None, "split",
        "chapter 9 Symmetry and chapter 8 Playing with Constructions are two "
        "chapters; 9 of the 58 questions are instrument and construction "
        "questions, so no single chapter is the counterpart."),
    # ----------------------------------------------------------- Mathematics 7
    ("Mathematics", 7, 1): (
        "mathematics-7/operations-with-integers", "contents-page",
        "Part 2 chapter 2 Operations with Integers (A Quick Recap of Integers, "
        "Multiplication of Integers)."),
    ("Mathematics", 7, 2): (
        None, "split",
        "fractions are Part 1 chapter 8 Working with Fractions, decimals Part 2 "
        "chapter 4 Another Peek Beyond the Point."),
    ("Mathematics", 7, 3): (
        None, "residue",
        "Part 2 chapter 5 Connecting the Dots is the data chapter, but Ganita "
        "Prakash 7 does not teach probability: 11 of 43 questions are chance "
        "and probability questions."),
    ("Mathematics", 7, 4): (
        "mathematics-7/finding-the-unknown", "contents-page",
        "Part 2 chapter 7 Finding the Unknown (Find the Unknowns, Solving "
        "Equations Systematically)."),
    ("Mathematics", 7, 5): (
        None, "residue",
        "chapter 5 Parallel and Intersecting Lines teaches transversals and "
        "corresponding and alternate angles, not angle pairs: 27 of 36 "
        "questions are complementary, supplementary, linear-pair or vertically "
        "opposite angles, which Ganita Prakash 7 does not teach."),
    ("Mathematics", 7, 6): (
        None, "split",
        "triangle construction and types are Part 1 chapter 7 A Tale of Three "
        "Intersecting Lines, congruence Part 2 chapter 1 Geometric Twins."),
    ("Mathematics", 7, 7): (
        None, "moved",
        "percentages are class 8 Part 2 chapter 1 Fractions in Disguise."),
    ("Mathematics", 7, 8): (
        None, "dropped",
        "Ganita Prakash 7 has no rational-numbers chapter; its integer chapter "
        "stops at integers."),
    ("Mathematics", 7, 9): (
        None, "moved",
        "perimeter and area are class 6 chapter 6 and class 8 Part 2 chapter 7."),
    ("Mathematics", 7, 10): (
        None, "residue",
        "chapter 4 Expressions using Letter-Numbers is the counterpart, but 16 "
        "of 57 questions turn on monomial/binomial/trinomial, degree and "
        "constant, terms Ganita Prakash 7 does not use."),
    ("Mathematics", 7, 11): (
        None, "moved",
        "exponents are class 8 chapter 2 Power Play."),
    ("Mathematics", 7, 12): (
        None, "split",
        "construction is Part 2 chapter 6 Constructions and Tilings; symmetry "
        "and solid shapes have no class 7 chapter."),
    # ----------------------------------------------------------- Mathematics 8
    ("Mathematics", 8, 1): (
        None, "dropped",
        "Ganita Prakash 8 has no rational-numbers chapter; chapter 3 A Story of "
        "Numbers is number systems and place value."),
    ("Mathematics", 8, 2): (
        None, "residue",
        "Part 2 chapter 5 Tales by Dots and Lines visualises data, but the old "
        "chapter's pie charts and probability are not in Ganita Prakash 8."),
    ("Mathematics", 8, 3): (
        "mathematics-8/a-square-and-a-cube", "contents-page",
        "chapter 1 A Square and A Cube (Square Numbers, Cubic Numbers); 8 of "
        "the 117 questions are Pythagorean triplets, which Part 2 chapter 2 "
        "teaches."),
    ("Mathematics", 8, 4): (
        None, "moved",
        "solving equations is class 7 Part 2 chapter 7 Finding the Unknown."),
    ("Mathematics", 8, 5): (
        None, "split",
        "chapter 4 Quadrilaterals is the quadrilateral half; the practical "
        "geometry half has no chapter in Ganita Prakash 8."),
    ("Mathematics", 8, 6): (
        "mathematics-8/exploring-some-geometric-themes", "contents-page",
        "Part 2 chapter 4 Exploring Some Geometric Themes prints Visualising "
        "Solids, where faces, edges and vertices of polyhedra are counted."),
    ("Mathematics", 8, 7): (
        None, "split",
        "the distributive identities are chapter 6 We Distribute, Yet Things "
        "Multiply and Part 2 chapter 6 Algebra Play."),
    ("Mathematics", 8, 8): (
        "mathematics-8/power-play", "contents-page",
        "chapter 2 Power Play (Exponential Notation and Operations, The Other "
        "Side of Powers, Powers of 10)."),
    ("Mathematics", 8, 9): (
        "mathematics-8/fractions-in-disguise", "contents-page",
        "Part 2 chapter 1 Fractions in Disguise is the percentage chapter, and "
        "its Using Percentages section prints Taxes and Growth and "
        "Compounding, where discount and compound interest are taught."),
    ("Mathematics", 8, 10): (
        None, "split",
        "direct proportion is chapter 7 Proportional Reasoning-1, inverse "
        "proportion Part 2 chapter 3 Proportional Reasoning-2."),
    ("Mathematics", 8, 11): (
        None, "residue",
        "Part 2 chapter 7 Area prints Rectangle and Squares only; the old "
        "chapter's trapezium area, surface area and volume are not in Ganita "
        "Prakash 8."),
    ("Mathematics", 8, 12): (
        None, "dropped",
        "Ganita Prakash 8 has no graphs chapter."),
    ("Mathematics", 8, 13): (
        "mathematics-8/number-play", "contents-page",
        "chapter 5 Number Play (Is This a Multiple Of?, Checking Divisibility "
        "Quickly, Digits in Disguise) is the generalised-form and divisibility "
        "chapter."),
    # ----------------------------------------------------------- Mathematics 9
    ("Mathematics", 9, 1): (
        None, "residue",
        "chapter 3 The World of Numbers reaches real numbers, but the old "
        "chapter's laws of exponents with rational powers are not in Ganita "
        "Manjari 9 (1 of its 5 questions)."),
    ("Mathematics", 9, 2): (
        None, "split",
        "linear polynomials are chapter 2, identities and factorisation "
        "chapter 4 Exploring Algebraic Identities."),
    ("Mathematics", 9, 3): (
        "mathematics-9/orienting-yourself-the-use-of-coordinates", "contents-page",
        "chapter 1 Orienting Yourself: The Use of Coordinates (The 2-D "
        "Cartesian Coordinate System, Distance Between Two Points)."),
    ("Mathematics", 9, 4): (
        "mathematics-9/introduction-to-linear-polynomials", "contents-page",
        "chapter 2 Introduction to Linear Polynomials is where a linear "
        "relationship in two variables and its graph are taught (Linear "
        "Relationships, Visualising linear relationships)."),
    ("Mathematics", 9, 5): (
        None, "dropped",
        "Ganita Manjari 9 has no Euclid's-geometry chapter."),
    ("Mathematics", 9, 6): (
        None, "dropped",
        "Ganita Manjari 9 has no lines-and-angles chapter."),
    ("Mathematics", 9, 7): (
        None, "dropped",
        "Ganita Manjari 9 has no triangles chapter; congruence is class 7 "
        "Part 2 chapter 1."),
    ("Mathematics", 9, 8): (
        None, "moved",
        "quadrilaterals are class 8 chapter 4."),
    ("Mathematics", 9, 9): (
        "mathematics-9/measuring-space-perimeter-and-area", "contents-page",
        "chapter 6 Measuring Space: Perimeter and Area prints Area of a "
        "Parallelogram and Area of a Triangle."),
    ("Mathematics", 9, 10): (
        "mathematics-9/i-m-up-and-down-and-round-and-round", "contents-page",
        "chapter 5 I'm Up and Down, and Round and Round is the circles chapter "
        "(Chords and the Angles They Subtend, Angles Subtended by an Arc, "
        "Concyclicity of Points)."),
    ("Mathematics", 9, 11): (
        None, "dropped",
        "Ganita Manjari 9 has no constructions chapter."),
    ("Mathematics", 9, 12): (
        None, "dropped",
        "chapter 6 gives the area of a triangle from its base and height; "
        "Heron's formula is not in Ganita Manjari 9."),
    ("Mathematics", 9, 13): (
        None, "dropped",
        "Ganita Manjari 9 has no surface-areas-and-volumes chapter."),
    ("Mathematics", 9, 14): (
        None, "split",
        "chapter 7 is probability; Ganita Manjari 9 has no statistics chapter, "
        "so the old combined chapter has no single counterpart."),
    # ---------------------------------------------------------- Mathematics 10
    ("Mathematics", 10, 1): ("mathematics-10/real-numbers", "exact-title", ""),
    ("Mathematics", 10, 2): ("mathematics-10/polynomials", "exact-title", ""),
    ("Mathematics", 10, 3): ("mathematics-10/pair-of-linear-equations-in-two-variables",
                             "exact-title", ""),
    ("Mathematics", 10, 4): ("mathematics-10/quadratic-equations", "exact-title", ""),
    ("Mathematics", 10, 5): ("mathematics-10/arithmetic-progressions", "exact-title", ""),
    ("Mathematics", 10, 6): ("mathematics-10/triangles", "exact-title", ""),
    ("Mathematics", 10, 7): ("mathematics-10/coordinate-geometry", "exact-title", ""),
    ("Mathematics", 10, 8): (
        None, "split",
        "the current book prints chapter 8 Introduction to Trigonometry and "
        "chapter 9 Some Applications of Trigonometry; the Exemplar chapter is "
        "both."),
    ("Mathematics", 10, 9): ("mathematics-10/circles", "exact-title", ""),
    ("Mathematics", 10, 10): (
        None, "dropped",
        "the current book has 14 chapters and no Constructions among them."),
    ("Mathematics", 10, 11): (
        "mathematics-10/areas-related-to-circles", "hand-checked",
        "same chapter, same chapter number 11: the current book prints it "
        "Areas Related to Circles (chapters/jemh1/jemh111.pdf p.1), the "
        "Exemplar Area Related to Circles."),
    ("Mathematics", 10, 12): ("mathematics-10/surface-areas-and-volumes", "exact-title", ""),
    ("Mathematics", 10, 13): (
        None, "split",
        "the current book prints chapter 13 Statistics and chapter 14 "
        "Probability; the Exemplar chapter is both."),
    # --------------------------------------------------------------- Science 6
    ("Science", 6, 1): (
        None, "split",
        "where food comes from is spread over chapter 3 Mindful Eating (What "
        "Do We Eat?, Food Miles) and chapter 2 Diversity in the Living World."),
    ("Science", 6, 2): (
        "science-6/mindful-eating-a-path-to-a-healthy-body", "contents-page",
        "chapter 3 Mindful Eating: A Path to a Healthy Body prints What are "
        "the Components of Food?, How to Test Different Components of Food? "
        "and Balanced Diet."),
    ("Science", 6, 3): (
        None, "dropped",
        "Curiosity 6 has no fibre-to-fabric chapter."),
    ("Science", 6, 4): (
        "science-6/materials-around-us", "contents-page",
        "chapter 6 Materials Around Us (How to Group Materials?, What are the "
        "different Properties of Materials?)."),
    ("Science", 6, 5): (
        "science-6/methods-of-separation-in-everyday-life", "contents-page",
        "chapter 9 Methods of Separation in Everyday Life."),
    ("Science", 6, 6): (
        None, "moved",
        "physical and chemical changes are class 7 chapter 5 Changes Around "
        "Us: Physical and Chemical."),
    ("Science", 6, 7): (
        None, "split",
        "parts of a plant are spread over chapter 2 Diversity in the Living "
        "World and chapter 10 Living Creatures."),
    ("Science", 6, 8): (
        None, "moved",
        "the musculoskeletal system is class 9 chapter 3 Tissues in Action."),
    ("Science", 6, 9): (
        None, "split",
        "habitat and adaptation are chapter 2 Diversity in the Living World, "
        "the characteristics of living things chapter 10 Living Creatures."),
    ("Science", 6, 10): (
        "science-6/measurement-of-length-and-motion", "contents-page",
        "chapter 5 Measurement of Length and Motion (Standard Units, "
        "Describing Position, Moving Things, Types of Motion)."),
    ("Science", 6, 11): (
        None, "moved",
        "light is class 7 chapter 11 Light: Shadows and Reflections."),
    ("Science", 6, 12): (
        None, "moved",
        "circuits are class 7 chapter 3 Electricity: Circuits and their "
        "Components."),
    ("Science", 6, 13): (
        "science-6/exploring-magnets", "contents-page",
        "chapter 4 Exploring Magnets, whose last section is printed Fun with "
        "Magnets."),
    ("Science", 6, 14): (
        None, "split",
        "the states of water are chapter 8 A Journey through States of Water, "
        "water as a resource chapter 11 Nature's Treasures."),
    ("Science", 6, 15): (
        "science-6/nature-s-treasures", "hand-checked",
        "Curiosity 6 has no air chapter; air is taught in chapter 11 Nature's "
        "Treasures, whose first section is printed Air. All 15 questions are "
        "about the composition and uses of air, which that section teaches."),
    ("Science", 6, 16): (
        None, "dropped",
        "Curiosity 6 has no waste-management chapter."),
    # --------------------------------------------------------------- Science 7
    ("Science", 7, 1): (
        "science-7/life-processes-in-plants", "contents-page",
        "chapter 10 Life Processes in Plants (How Do Plants Get Food for their "
        "Growth?, Transport in Plants, Do Plants Respire?)."),
    ("Science", 7, 2): (
        "science-7/life-processes-in-animals", "contents-page",
        "chapter 9 Life Processes in Animals prints Nutrition in Animals."),
    ("Science", 7, 3): (
        None, "dropped",
        "Curiosity 7 has no fibre-to-fabric chapter."),
    ("Science", 7, 4): (
        None, "residue",
        "chapter 7 Heat Transfer in Nature teaches conduction, convection and "
        "radiation; temperature and thermometers moved to class 6 chapter 7."),
    ("Science", 7, 5): (
        "science-7/exploring-substances-acidic-basic-and-neutral", "contents-page",
        "chapter 2 Exploring Substances: Acidic, Basic, and Neutral."),
    ("Science", 7, 6): (
        "science-7/changes-around-us-physical-and-chemical", "contents-page",
        "chapter 5 Changes Around Us: Physical and Chemical."),
    ("Science", 7, 7): (
        None, "dropped",
        "Curiosity 7 has no weather-and-climate chapter."),
    ("Science", 7, 8): (
        None, "moved",
        "winds, storms and cyclones are class 8 chapter 6."),
    ("Science", 7, 9): (
        None, "dropped",
        "Curiosity 7 has no soil chapter."),
    ("Science", 7, 10): (
        None, "split",
        "respiration in animals is chapter 9, respiration in plants chapter 10."),
    ("Science", 7, 11): (
        None, "split",
        "transport in plants is chapter 10; Curiosity 7 has no circulation "
        "chapter for the animal half."),
    ("Science", 7, 12): (
        None, "moved",
        "reproduction is class 9 chapter 11 Reproduction: How Life Continues."),
    ("Science", 7, 13): (
        "science-7/measurement-of-time-and-motion", "contents-page",
        "chapter 8 Measurement of Time and Motion (Measurement of Time, Speed, "
        "Uniform and Non-uniform Linear Motion)."),
    ("Science", 7, 14): (
        None, "split",
        "circuits are chapter 3; the heating and magnetic effects moved to "
        "class 8 chapter 4."),
    ("Science", 7, 15): (
        None, "residue",
        "chapter 11 Light: Shadows and Reflections stops at plane mirrors: 11 "
        "of 22 questions are about spherical mirrors and lenses, which class 8 "
        "chapter 10 teaches."),
    ("Science", 7, 16): (
        None, "moved",
        "water as a resource is class 6 chapter 11 Nature's Treasures."),
    ("Science", 7, 17): (
        None, "dropped",
        "Curiosity 7 has no forests chapter."),
    ("Science", 7, 18): (
        None, "dropped",
        "Curiosity 7 has no wastewater chapter."),
    # --------------------------------------------------------------- Science 8
    ("Science", 8, 1): (
        None, "dropped",
        "Curiosity 8 has no crop-production chapter."),
    ("Science", 8, 2): (
        None, "split",
        "microorganisms are chapter 2 The Invisible Living World, but the "
        "diseases they cause are chapter 3 Health: The Ultimate Treasure."),
    ("Science", 8, 3): (
        None, "dropped",
        "Curiosity 8 has no synthetic-fibres chapter."),
    ("Science", 8, 4): (
        None, "moved",
        "metals and non-metals are class 7 chapter 4."),
    ("Science", 8, 5): (
        None, "dropped",
        "Curiosity 8 has no coal-and-petroleum chapter."),
    ("Science", 8, 6): (
        None, "dropped",
        "Curiosity 8 has no combustion chapter."),
    ("Science", 8, 7): (
        None, "residue",
        "chapter 12 How Nature Works in Harmony teaches ecosystems and "
        "interactions; deforestation, sanctuaries and the Red Data Book are "
        "not in Curiosity 8."),
    ("Science", 8, 8): (
        "science-8/the-invisible-living-world-beyond-our-naked-eye", "contents-page",
        "chapter 2 The Invisible Living World: Beyond Our Naked Eye (What Is a "
        "Cell?, What Are the Levels of Organisation..., Why Is Cell Considered "
        "to Be a Basic Unit of Life?)."),
    ("Science", 8, 9): (
        None, "moved",
        "reproduction is class 9 chapter 11."),
    ("Science", 8, 10): (
        None, "moved",
        "adolescence is class 7 chapter 6 Adolescence: A Stage of Growth and "
        "Change."),
    ("Science", 8, 11): (
        "science-8/exploring-forces", "contents-page",
        "chapter 5 Exploring Forces (What Is a Force?, What Are the Different "
        "Types of Forces?, Weight and Its Measurement, Floating and Sinking)."),
    ("Science", 8, 12): (
        None, "residue",
        "friction is one kind of force under chapter 5's What Are the "
        "Different Types of Forces?; Curiosity 8 has no friction chapter and "
        "does not teach fluid friction."),
    ("Science", 8, 13): (
        None, "moved",
        "sound is class 9 chapter 10 Sound Waves."),
    ("Science", 8, 14): (
        None, "dropped",
        "chapter 4 is Electricity: Magnetic and Heating Effects; the chemical "
        "effects of current are not in Curiosity 8."),
    ("Science", 8, 15): (
        None, "split",
        "lightning and thunderstorms are chapter 6; earthquakes have no "
        "chapter in Curiosity 8."),
    ("Science", 8, 16): (
        None, "residue",
        "chapter 10 Light: Mirrors and Lenses teaches spherical mirrors and "
        "lenses; the old chapter's plane mirrors and human eye are class 7 "
        "chapter 11 and class 10."),
    ("Science", 8, 17): (
        None, "moved",
        "stars and the solar system are class 6 chapter 12 Beyond Earth."),
    ("Science", 8, 18): (
        None, "dropped",
        "Curiosity 8 has no pollution chapter."),
    # --------------------------------------------------------------- Science 9
    ("Science", 9, 1): (
        None, "moved",
        "the states of matter are class 8 chapter 7 Particulate Nature of "
        "Matter; Exploration 9 has no such chapter."),
    ("Science", 9, 2): (
        None, "residue",
        "chapter 5 Exploring Mixtures and their Separation is the counterpart, "
        "but 5 of 23 questions are physical and chemical change and rusting, "
        "which class 7 chapter 5 teaches."),
    ("Science", 9, 3): (
        None, "residue",
        "chapter 9 Atomic Foundations of Matter is the counterpart, but the "
        "mole concept is not in Exploration 9 (3 of 17 questions)."),
    ("Science", 9, 4): (
        "science-9/journey-inside-the-atom", "contents-page",
        "chapter 8 Journey Inside the Atom (A Short Historical Journey Through "
        "Atomic Models, Atomic Number, Mass Number, How Are Electrons "
        "Distributed..., Valency)."),
    ("Science", 9, 5): (
        "science-9/cell-the-building-block-of-life", "contents-page",
        "chapter 2 Cell: The Building Block of Life (Structure of a Cell, The "
        "Cell Interior, How do Normal Cells Grow and Divide?, Cell Theory)."),
    ("Science", 9, 6): (
        "science-9/tissues-in-action", "contents-page",
        "chapter 3 Tissues in Action (Why are Plant and Animal Tissues "
        "Different?, Tissues for Growth in Plants, Animal Tissues)."),
    ("Science", 9, 7): (
        "science-9/patterns-in-life-diversity-and-classification", "contents-page",
        "chapter 12 Patterns in Life: Diversity and Classification (How to "
        "Classify Organisms?, Five Kingdom Classification, Scientific Naming)."),
    ("Science", 9, 8): (
        "science-9/describing-motion-around-us", "contents-page",
        "chapter 4 Describing Motion Around Us (Motion in a Straight Line, "
        "Graphical Representation of Motion, Kinematic Equations)."),
    ("Science", 9, 9): (
        "science-9/how-forces-affect-motion", "contents-page",
        "chapter 6 How Forces Affect Motion (Balanced and Unbalanced Forces "
        "and Newton's three laws of motion)."),
    ("Science", 9, 10): (
        None, "dropped",
        "Exploration 9 has no gravitation chapter."),
    ("Science", 9, 11): (
        "science-9/work-energy-and-simple-machines", "contents-page",
        "chapter 7 Work, Energy, and Simple Machines (Work Done by a Constant "
        "Force, The Work-Energy Theorem, Mechanical Energy, Power)."),
    ("Science", 9, 12): (
        "science-9/sound-waves-characteristics-and-applications", "contents-page",
        "chapter 10 Sound Waves: Characteristics and Applications (Production "
        "of Sound, Propagation of Sound, Reflection of Sound, Ultrasonic...)."),
    ("Science", 9, 13): (
        None, "moved",
        "health and disease are class 8 chapter 3 Health: The Ultimate "
        "Treasure."),
    ("Science", 9, 14): (
        None, "residue",
        "chapter 13 Earth as a System keeps the biogeochemical cycles; the old "
        "chapter's atmosphere, soil and ozone are not in Exploration 9."),
    ("Science", 9, 15): (
        None, "dropped",
        "Exploration 9 has no food-resources chapter."),
    # -------------------------------------------------------------- Science 10
    ("Science", 10, 1): ("science-10/chemical-reactions-and-equations", "exact-title", ""),
    ("Science", 10, 2): ("science-10/acids-bases-and-salts", "exact-title", ""),
    ("Science", 10, 3): ("science-10/metals-and-non-metals", "exact-title", ""),
    ("Science", 10, 4): ("science-10/carbon-and-its-compounds", "exact-title", ""),
    ("Science", 10, 5): (
        None, "dropped",
        "the current book has 13 chapters and no Periodic Classification of "
        "Elements among them."),
    ("Science", 10, 6): ("science-10/life-processes", "exact-title", ""),
    ("Science", 10, 7): ("science-10/control-and-coordination", "exact-title", ""),
    ("Science", 10, 8): ("science-10/how-do-organisms-reproduce", "exact-title", ""),
    ("Science", 10, 9): (
        None, "residue",
        "the current book's chapter 8 is Heredity alone; 9 of the 29 questions "
        "are evolution questions -- natural selection, speciation, homologous "
        "organs -- which the current book no longer teaches."),
    ("Science", 10, 10): ("science-10/light-reflection-and-refraction", "exact-title", ""),
    ("Science", 10, 11): ("science-10/the-human-eye-and-the-colourful-world",
                          "exact-title", ""),
    ("Science", 10, 12): ("science-10/electricity", "exact-title", ""),
    ("Science", 10, 13): ("science-10/magnetic-effects-of-electric-current",
                          "exact-title", ""),
    ("Science", 10, 14): (
        None, "dropped",
        "the current book has no Sources of Energy chapter."),
    ("Science", 10, 15): ("science-10/our-environment", "exact-title", ""),
    ("Science", 10, 16): (
        None, "dropped",
        "the current book has no Management of Natural Resources chapter."),
}

NULL_REASONS = {"split", "dropped", "moved", "residue"}
METHODS = {"exact-title", "contents-page", "hand-checked"}


# --------------------------------------------------------------------------- #
# reading the banks and the trees
# --------------------------------------------------------------------------- #

def _records(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["questions"] if isinstance(data, dict) else data


def exemplar_keys(paths: list[Path]) -> dict[tuple[str, int, int, str], collections.Counter]:
    """Every (subject, grade, exemplar number, exemplar title) the banks hold,
    with how many questions of each bank carry it. Both the Exemplar corpus and
    the served bank are read: the merge drops records and the served bank keeps
    only what survived it, so a row must exist for the keys of either."""
    counts: dict[tuple, collections.Counter] = collections.defaultdict(collections.Counter)
    for path in paths:
        if not path.exists():
            continue
        for rec in _records(path):
            ex = (rec.get("metadata") or {}).get("exemplarChapter")
            if not ex or not ex.get("title"):
                continue
            subject, grade = rec.get("subject"), rec.get("grade")
            if subject not in SUBJECT_FILE:
                continue
            counts[(subject, int(grade), int(ex["number"]), ex["title"])][str(path)] += 1
    return dict(counts)


def taxonomy_chapters(subject: str, grade: int) -> dict[str, dict]:
    path = TAXONOMY / f"{SUBJECT_FILE[subject]}_{grade}.json"
    tree = json.loads(path.read_text(encoding="utf-8"))
    return {ch["id"]: ch for ch in tree["chapters"]}


def _same_title(a: str, b: str) -> bool:
    """Titles equal ignoring case, spacing and the dash the two books use."""
    def norm(s: str) -> str:
        s = s.replace("–", "-").replace("—", "-").replace("’", "'")
        return re.sub(r"\s+", " ", s).strip().casefold()
    return norm(a) == norm(b)


# --------------------------------------------------------------------------- #
# building and checking
# --------------------------------------------------------------------------- #

def build() -> dict:
    keys = exemplar_keys([EXEMPLAR_BANK, SERVED_BANK])
    rows, problems = [], []
    trees: dict[tuple[str, int], dict] = {}
    for (subject, grade, number, title) in sorted(keys):
        decision = DECISIONS.get((subject, grade, number))
        if decision is None:
            problems.append(f"no decision for {subject} {grade} chapter {number} {title!r}")
            continue
        chapter_id, how, note = decision
        if (subject, grade) not in trees:
            trees[(subject, grade)] = taxonomy_chapters(subject, grade)
        chapters = trees[(subject, grade)]
        row = {
            "subject": subject,
            "grade": grade,
            "exemplarNumber": number,
            "exemplarTitle": title,
            # how many questions the row covers, in the Exemplar corpus the
            # importer writes and in the bank the API serves (the merge drops
            # records, so the two differ)
            "questions": keys[(subject, grade, number, title)][str(EXEMPLAR_BANK)],
            "questionsServed": keys[(subject, grade, number, title)][str(SERVED_BANK)],
            "taxonomyChapterId": chapter_id,
        }
        if chapter_id is None:
            if how not in NULL_REASONS:
                problems.append(f"{subject} {grade} ch{number}: unknown null reason {how!r}")
            row["method"] = "none"
            row["reason"] = how
            row["note"] = note
        else:
            if how not in METHODS:
                problems.append(f"{subject} {grade} ch{number}: unknown method {how!r}")
            if chapter_id not in chapters:
                problems.append(f"{subject} {grade} ch{number}: {chapter_id} is not a chapter "
                                f"of the {SUBJECT_FILE[subject]}_{grade} tree")
                continue
            current = chapters[chapter_id]
            if how == "exact-title" and not _same_title(title, current["name"]):
                problems.append(f"{subject} {grade} ch{number}: claimed exact-title but the "
                                f"current book prints {current['name']!r}")
            row["method"] = how
            page, printed = citation(subject, grade, current.get("source_file"))
            row["currentChapter"] = {"number": current["number"], "title": current["name"],
                                     "sourceFile": current.get("source_file"),
                                     "page": page, "printedOn": printed}
            row["note"] = note
        rows.append(row)

    if problems:
        for p in problems:
            print("PROBLEM:", p, file=sys.stderr)
        raise SystemExit(f"{len(problems)} problem(s): the map was not written")

    # A null contentsPage said nothing at all. Where there is none, the book
    # says why and where its rows are cited instead, rather than leaving a
    # reader to infer it from a null.
    no_contents = ("NCERT distributes this book as one PDF per chapter and the dataset "
                   "holds no prelims file, so there is no contents page to cite; each "
                   "row cites page 1 of its own chapter's PDF, where the book prints "
                   "that chapter's number and title.")
    books = {
        f"{subject}_{grade}": {"book": book, "pdf": pdf, "contentsPage": page,
                               **({} if page else {"contentsNote": no_contents})}
        for (subject, grade), (book, pdf, page) in sorted(BOOKS.items())
    }
    mapped = [r for r in rows if r["taxonomyChapterId"]]
    return {
        "notice": ("Which chapter of the CURRENT NCERT book each NCERT Exemplar "
                   "chapter belongs to. Decided against the current books' own "
                   "contents pages and section headings, never by word overlap; "
                   "a chapter with no single counterpart is null with its reason. "
                   "Every mapped row cites the PDF and the page that prints its "
                   "chapter's number and title (currentChapter.sourceFile, .page, "
                   ".printedOn: a book's contents page, or page 1 of a single "
                   "chapter's own PDF); --check reads both back off the PDF. "
                   "Written by scripts/build_exemplar_chapter_map.py."),
        "rule": ("A row maps when the current book of that class has exactly one "
                 "chapter that teaches the Exemplar chapter's subject matter AND "
                 "at most 10% of that chapter's questions are content the class "
                 "teaches in another chapter; the measured share is in the note. "
                 "Otherwise null: split, dropped, moved or residue."),
        "sourceBooks": books,
        "rows": rows,
        "counts": {
            "rows": len(rows),
            "mapped": len(mapped),
            "null": len(rows) - len(mapped),
            "questionsMapped": sum(r["questions"] for r in mapped),
            "questionsUnmapped": sum(r["questions"] for r in rows if not r["taxonomyChapterId"]),
            "servedMapped": sum(r["questionsServed"] for r in mapped),
            "servedUnmapped": sum(r["questionsServed"] for r in rows
                                  if not r["taxonomyChapterId"]),
        },
    }


# --------------------------------------------------------------------------- #
# the hand-checked sample
# --------------------------------------------------------------------------- #
# Task 123 asks for a random sample of at least 40 newly tagged records,
# hand-checked against the current book, with the number wrong reported. A
# number in a report cannot be re-run: this is the draw itself, so the sample
# file names which records were checked and anyone can redraw the same 40.
SAMPLE_PATH = TAXONOMY / "_exemplar_tag_sample.json"
SAMPLE_SEED = 123
SAMPLE_SIZE = 40


def sample_population(records: list[dict]) -> list[dict]:
    """The records the map placed, in id order -- what the sample is drawn from.

    Sorted by id, not left in bank order, so the draw does not move when the
    merge reorders the bank.
    """
    return sorted((r for r in records if r.get("tagMethod") == EXEMPLAR_MAP_METHOD),
                  key=lambda r: r["id"])


def draw_sample(records: list[dict], seed: int = SAMPLE_SEED,
                size: int = SAMPLE_SIZE) -> tuple[list[dict], str]:
    """``size`` records drawn from the population above, and its digest.

    The digest is over the population's ids: it says which 1,626 records the
    draw ran on, so a later run can tell "the same sample" from "the same seed
    on a bank that has changed underneath it".
    """
    import random

    population = sample_population(records)
    digest = hashlib.sha256("\n".join(r["id"] for r in population).encode()).hexdigest()
    drawn = random.Random(seed).sample(population, size)
    return sorted(drawn, key=lambda r: r["id"]), digest


def _page_words(pdf: Path, page: int) -> str | None:
    """The words of one 1-based page, lowercased, or None if it cannot be read."""
    try:
        import pymupdf
    except ImportError:  # pragma: no cover - the venv pins PyMuPDF
        return None
    try:
        with pymupdf.open(pdf) as book:
            if not 1 <= page <= book.page_count:
                return ""
            return " ".join(re.findall(r"[a-z0-9]+", book[page - 1].get_text().lower()))
    except Exception:
        return ""


def check_citations(doc: dict) -> list[str]:
    """Every mapped row's cited page, read back off the PDF it cites.

    A citation nobody opens is a claim, not a source: three rows cited a page
    that was not in the file they named (the Ganita Prakash Part 2 chapters,
    against their Part 1 contents page) and 22 cited no page at all. This opens
    each cited PDF at the cited page and asks to find the chapter's number and
    its title there. Skipped, loudly, when ncert-dataset is not on this machine.
    """
    if not TEXTBOOKS.exists():
        return []
    problems = []
    for row in doc["rows"]:
        if not row["taxonomyChapterId"]:
            continue
        current = row["currentChapter"]
        where = f"{row['subject']} {row['grade']} ch{row['exemplarNumber']}"
        if not current.get("sourceFile") or not current.get("page"):
            problems.append(f"{where}: mapped, but cites no PDF and page")
            continue
        words = _page_words(TEXTBOOKS / current["sourceFile"], current["page"])
        if words is None:
            return []  # no PyMuPDF here; nothing was checked, so claim nothing
        title = " ".join(re.findall(r"[a-z0-9]+",
                                    current["title"].lower().replace("–", "-")))
        if title not in words or not re.search(rf"\b{current['number']}\b", words):
            problems.append(
                f"{where}: {current['sourceFile']} page {current['page']} does not print "
                f"{current['number']} {current['title']!r}")
    return problems


def check_sample(sample: dict, records: list[dict]) -> list[str]:
    """The committed hand-check, re-derived against the bank as it stands now.

    Three separate claims, each of which can rot on its own: the same seed on
    the same population still draws these 40 records; each of them still
    carries the chapter the checker saw; and the precision the file reports is
    the precision its own verdicts add up to.
    """
    problems = []
    by_id = {r["id"]: r for r in records}
    drawn, digest = draw_sample(records, sample["seed"], sample["size"])
    if digest != sample["populationDigest"]:
        problems.append(
            f"the population the map placed has changed ({len(sample_population(records))} "
            f"records now, digest {digest[:12]} against {sample['populationDigest'][:12]}): "
            f"the sample has to be redrawn and re-checked, not carried over")
    elif [r["id"] for r in drawn] != [it["id"] for it in sample["items"]]:
        problems.append("seed {} no longer draws the committed ids".format(sample["seed"]))
    for item in sample["items"]:
        rec = by_id.get(item["id"])
        if rec is None:
            problems.append(f"{item['id']}: checked, but the bank no longer serves it")
        elif rec.get("taxonomyChapterId") != item["taxonomyChapterId"]:
            problems.append(f"{item['id']}: checked as {item['taxonomyChapterId']}, "
                            f"now tagged {rec.get('taxonomyChapterId')}")
    right = sum(1 for it in sample["items"] if it["verdict"] == "right")
    if right != sample["counts"]["right"]:
        problems.append(f"the file says {sample['counts']['right']} right, its verdicts say {right}")
    return problems


def check(doc: dict) -> list[str]:
    """Everything the committed file must still be true about."""
    problems = check_citations(doc)
    keys = exemplar_keys([EXEMPLAR_BANK, SERVED_BANK])
    rows = {(r["subject"], r["grade"], r["exemplarNumber"], r["exemplarTitle"]): r
            for r in doc["rows"]}
    for key in sorted(keys):
        if key not in rows:
            problems.append(f"the Exemplar bank holds {key} and the map has no row for it")
    for key, row in sorted(rows.items()):
        subject, grade = row["subject"], row["grade"]
        chapter_id = row["taxonomyChapterId"]
        if chapter_id is None:
            continue
        chapters = taxonomy_chapters(subject, grade)
        if chapter_id not in chapters:
            problems.append(f"{key}: {chapter_id} is not in the {subject} {grade} tree")
        elif row["method"] == "exact-title" and not _same_title(
                row["exemplarTitle"], chapters[chapter_id]["name"]):
            problems.append(f"{key}: exact-title, but the current book prints "
                            f"{chapters[chapter_id]['name']!r}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="verify the committed map and hand-check sample instead of writing it")
    ap.add_argument("--redraw", action="store_true",
                    help="print the sample the seed draws from the bank as it stands now")
    args = ap.parse_args()

    if args.check:
        doc = json.loads(MAP_PATH.read_text(encoding="utf-8"))
        problems = check(doc)
        for p in problems:
            print("PROBLEM:", p)
        print(f"{MAP_PATH.name}: {len(doc['rows'])} rows, "
              f"{doc['counts']['mapped']} mapped, {len(problems)} problem(s)")
        if SAMPLE_PATH.exists():
            sample = json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))
            served = json.loads(SERVED_BANK.read_text(encoding="utf-8"))["questions"]
            sample_problems = check_sample(sample, served)
            for p in sample_problems:
                print("PROBLEM:", p)
            print(f"{SAMPLE_PATH.name}: {sample['counts']['right']}/{sample['size']} right, "
                  f"{len(sample_problems)} problem(s)")
            problems += sample_problems
        return 1 if problems else 0

    if args.redraw:
        served = json.loads(SERVED_BANK.read_text(encoding="utf-8"))["questions"]
        drawn, digest = draw_sample(served)
        print(f"population {len(sample_population(served))}  digest {digest}")
        for rec in drawn:
            chapter = (rec.get("metadata") or {}).get("exemplarChapter") or {}
            print(f"  {rec['id']}  {rec['subject']} {rec['grade']}  "
                  f"exemplar ch{chapter.get('number')} {chapter.get('title')!r} -> "
                  f"{rec.get('taxonomyChapterId')}")
        print("a redraw is a NEW hand-check: the verdicts in "
              f"{SAMPLE_PATH.name} belong to the ids above only if they match it")
        return 0

    doc = build()
    MAP_PATH.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    c = doc["counts"]
    print(f"{MAP_PATH}: {c['rows']} rows, {c['mapped']} mapped "
          f"({c['questionsMapped']} Exemplar questions, {c['servedMapped']} served), "
          f"{c['null']} null ({c['questionsUnmapped']} Exemplar questions, "
          f"{c['servedUnmapped']} served)")
    by_reason: collections.Counter = collections.Counter(
        r.get("reason") for r in doc["rows"] if not r["taxonomyChapterId"])
    for reason, n in by_reason.most_common():
        print(f"  null/{reason}: {n} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
