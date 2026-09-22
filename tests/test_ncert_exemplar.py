"""NCERT Exemplar, classes 6-10: questions paired with NCERT's own answers.

Every fixture is real page text (``tests/_exemplar_pages.py``, keyed by file
and 1-based page) rendered from the Exemplar PDFs, because each bug found while
building this parser was invisible to a made-up snippet: the class 8 science
options printed in two columns, the class 10 science headings set in a font
shifted 0x1E below ASCII, the answers row "58. No   59. (a) ...", the radical
signs drawn as vector paths. What is asserted is what the book says -- each
expected answer was read off the PDF page cited beside it.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _exemplar_pages import PAGES  # noqa: E402

from academicos.corpus import ncert_exemplar as ex  # noqa: E402


def _book(grade: int, subject: str) -> "ex.Book":
    return next(b for b in ex.BOOKS if b.grade == grade and b.subject == subject)


def _parse(grade, subject, chapter_file, pages, chapter, answer_file, answer_pages):
    book = _book(grade, subject)
    qs = ex.parse_chapter_pages([PAGES[(chapter_file, p)] for p in pages], book,
                                f"{chapter_file}.pdf", chapter)
    key = ex.parse_answer_pages([PAGES[(answer_file, p)] for p in answer_pages], book)
    ex.pair_answers(qs, key, f"{answer_file}.pdf")
    return {(q.scope, q.number): q for q in qs}


def _q(qs, number, scope=""):
    return qs[(scope, str(number))]


# --------------------------------------------------------------------------- #
# class 6
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def maths6():
    # feep102.pdf (Unit 2, Geometry) pp. 3-6; answers feep1an.pdf p. 3 ("Unit 2").
    return _parse(6, "Mathematics", "feep102", [3, 4, 5, 6], 2, "feep1an", [3])


def test_class6_maths_mcq_has_four_options_and_the_books_letter(maths6):
    q = _q(maths6, 2)          # feep102 p.4: "The number of diagonals in a septagon is"
    assert q.stem == "The number of diagonals in a septagon is"
    assert q.options == ["21", "42", "7", "14"]
    assert q.option_labels == ["A", "B", "C", "D"]
    assert q.answer_letters == ["d"]          # feep1an p.3: "2. (D)"
    assert ex.exclusion_reason(q) is None


def test_class6_maths_range_instruction_sets_the_kind_and_the_short_answer(maths6):
    # feep102 p.6: "In questions 17 to 31, fill in the blanks ..." then
    # "17. An angle greater than 180° and less than a complete angle is called".
    q = _q(maths6, 17)
    assert q.section_kind == ex.FILL_BLANK
    assert q.answer_text == "Reflex angle"   # feep1an p.3: "17. Reflex angle"
    assert ex.exclusion_reason(q) is None
    # The instruction is nobody's text: question 16's last option stays clean.
    assert _q(maths6, 16).options[-1] == "neither isosceles nor right triangle"


def test_class6_maths_short_answer_is_paired():
    # feep102 p.13: "58. If two rays intersect, will their point of
    # intersection be the vertex of an angle of which the rays are the two
    # sides?"; feep1an p.4: "58." / "No   59. (a) ...".
    qs = _parse(6, "Mathematics", "feep102", range(3, 14), 2, "feep1an", [3, 4])
    q = _q(qs, 58)
    assert q.section_kind == ex.SA
    assert q.stem.startswith("If two rays intersect, will their point of intersection")
    assert q.answer_text == "No"
    assert ex.exclusion_reason(q) is None


def test_class6_maths_figure_question_is_excluded(maths6):
    q = _q(maths6, 3)          # feep102 p.4: "Number of line segments in Fig. 2.5 is"
    assert q.has_answer
    assert ex.exclusion_reason(q) == "figure-unavailable"


def test_class6_maths_question_without_a_locatable_answer_is_excluded():
    # The same unit against only the part of feep1an p.3 that ends at "10. (B)":
    # question 11's answer is not in the text, so it gets none.
    book = _book(6, "Mathematics")
    answers = PAGES[("feep1an", 3)]
    cut = answers[:answers.index("11. (D)")]
    qs = ex.parse_chapter_pages([PAGES[("feep102", p)] for p in (3, 4, 5, 6)], book,
                                "feep102.pdf", 2)
    ex.pair_answers(qs, ex.parse_answer_pages([cut], book), "feep1an.pdf")
    by = {q.number: q for q in qs}
    assert by["2"].answer_letters == ["d"]
    assert not by["11"].has_answer
    assert ex.exclusion_reason(by["11"]) == "no-answer"


@pytest.fixture(scope="module")
def science6():
    # feep202.pdf (Chapter 2, Components of Food) pp. 1-4; answers feep2an.pdf p. 3.
    return _parse(6, "Science", "feep202", [1, 2, 3, 4], 2, "feep2an", [3])


def test_class6_science_mcq_and_short_answer(science6):
    q = _q(science6, 1)        # feep202 p.1
    assert q.stem == "Which one of the following food item does not provide dietary fibre?"
    assert q.options == ["Whole grains", "Whole pulses", "Fruits and vegetables", "Milk"]
    assert q.answer_letters == ["d"]          # feep2an p.3: "1." / "d"
    assert ex.exclusion_reason(q) is None
    sa = _q(science6, 11)      # feep202 p.4: "Tasty food is not always nutritious ..."
    assert sa.section_kind == ex.SA
    assert sa.answer_text.startswith("Potato chips are tasty but they are not very nutritious.")
    assert ex.exclusion_reason(sa) is None


def test_class6_science_misprinted_option_labels_are_refused(science6):
    # feep202 p.1 prints question 3's options as (a), (b), (d), (d).
    q = _q(science6, 3)
    assert q.options_error
    assert ex.exclusion_reason(q) == "options-unparsed"


def test_class6_science_figure_question_is_excluded(science6):
    # feep202 p.3: "8." then a picture, then "Which of the following food items
    # does not provide any nutrient?" -- the items are only in the picture.
    # feep2an p.3 answers it "8." / "Water", so the answer is found (a chapter
    # title of the same book is not a running head in the answers file) and
    # only the figure rule can refuse it.
    q = _q(science6, 8)
    assert q.answer_text == "Water"
    assert ex.FIGURE_MARK in q.stem
    assert ex.exclusion_reason(q) == "figure-unavailable"


def test_class6_science_question_without_a_locatable_answer_is_excluded():
    # feep2an p.3 cut before "11.": questions 11 onwards find no answer.
    book = _book(6, "Science")
    page = PAGES[("feep2an", 3)]
    cut = page[:page.index("\n11.\n")]
    qs = ex.parse_chapter_pages([PAGES[("feep202", p)] for p in (1, 2, 3, 4)], book,
                                "feep202.pdf", 2)
    ex.pair_answers(qs, ex.parse_answer_pages([cut], book), "feep2an.pdf")
    by = {q.number: q for q in qs}
    assert by["1"].answer_letters == ["d"]
    assert not by["11"].has_answer
    assert ex.exclusion_reason(by["11"]) == "no-answer"


def test_class6_science_answer_line_equal_to_a_chapter_title_is_kept():
    # feep2an p.35, chapter 14 (Water): answer 16 ends on a line reading
    # "water." -- the title of chapter 14. Dropped as a running head, the
    # bank served "... this reduces the availability of ground".
    qs = _parse(6, "Science", "feep214", [1, 2, 3, 4], 14, "feep2an", [34, 35])
    q = _q(qs, 16)             # feep214: "How do the areas covered with concrete affect ..."
    assert q.answer_text.endswith("reduces the availability of ground water.")
    assert ex.exclusion_reason(q) is None


def test_class6_science_answer_that_only_points_elsewhere_is_excluded():
    # feep216 / feep2an p.40: the book answers question 18 (paper pulp) with
    # "Hint: Take help of elders or use internet." and question 19 (the plastic
    # bag ban) with "Give your justification according to your stand ...".
    qs = _parse(6, "Science", "feep216", range(1, 9), 16, "feep2an", [39, 40])
    assert _q(qs, 18).answer_text == "Hint: Take help of elders or use internet."
    assert ex.exclusion_reason(_q(qs, 18)) == "answer-is-a-pointer"
    assert _q(qs, 19).answer_text.startswith("Give your justification according to your stand")
    assert ex.exclusion_reason(_q(qs, 19)) == "answer-is-a-pointer"


# --------------------------------------------------------------------------- #
# class 8
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def maths8():
    # heep204.pdf (Unit 4, Linear Equations in One Variable) pp. 6-9;
    # answers heep2an.pdf p. 16 ("Unit 4").
    return _parse(8, "Mathematics", "heep204", [6, 7, 8, 9], 4, "heep2an", [16])


def test_class8_maths_mcq_and_fill_in(maths8):
    q = _q(maths8, 4)          # heep204 p.7: "The shifting of a number ... is called"
    assert q.options == ["Transposition", "Distributivity", "Commutativity", "Associativity"]
    assert q.answer_letters == ["a"]          # heep2an p.16: "4. (a)"
    assert ex.exclusion_reason(q) is None
    fb = _q(maths8, 16)        # heep204 p.9: "In a linear equation, the ____ power ..."
    assert fb.section_kind == ex.FILL_BLANK
    assert fb.answer_text == "highest"        # heep2an p.16: "16. highest"
    assert ex.exclusion_reason(fb) is None


def test_class8_maths_short_answer_is_paired():
    # heep204 p.12: "Solve the following:" ... "58. 8x – 7 – 3x = 6x – 2x – 3";
    # heep2an p.17: "58. x = 4".
    qs = _parse(8, "Mathematics", "heep204", range(6, 13), 4, "heep2an", [16, 17])
    q = _q(qs, 58)
    assert q.section_kind == ex.SA
    assert q.stem == "8x – 7 – 3x = 6x – 2x – 3"
    assert q.answer_text == "x = 4"
    assert ex.exclusion_reason(q) is None


def test_class8_maths_questions_about_unseen_figures_are_excluded():
    # heep205 pp.16-17: "7. Which of the following figures satisfy the
    # following property?" with options (a) P ... (d) S -- P, Q, R and S are
    # shapes drawn on the page; heep2an p.19 keys it "7. (c)".
    qs = _parse(8, "Mathematics", "heep205", [16, 17], 5, "heep2an", [19])
    for n in (6, 7, 8, 9):
        q = _q(qs, n)
        assert q.options == ["P", "Q", "R", "S"] and q.has_answer, n
        assert ex.exclusion_reason(q) == "figure-unavailable", n
    # "For which of the following figures, all angles are equal?" names its
    # figures in the options: it needs no picture and is served.
    q = _q(qs, 3)
    assert q.options == ["Rectangle", "Kite", "Trapezium", "Rhombus"]
    assert q.answer_letters == ["a"]          # heep2an p.19: "3. (a)"
    assert ex.exclusion_reason(q) is None


def test_class8_maths_answer_that_swallowed_the_next_number_is_not_trusted(maths8):
    # heep2an p.16 prints "17." / "1" / "18." with the 18 set as a lowered
    # fraction part, which renders "_(18.) 6". Entry 17 then holds 18's
    # answer too, so it pairs with nothing rather than with "1 6 5".
    q = _q(maths8, 17)
    assert not q.has_answer
    assert ex.exclusion_reason(q) == "no-answer"


def test_class8_maths_boxed_feature_text_excludes_the_question_it_lands_in(maths8):
    # heep204 p.8: a tinted "one-step equation" panel under question 14.
    assert ex.exclusion_reason(_q(maths8, 14)) == "reading-order"


@pytest.fixture(scope="module")
def science8():
    # heep101.pdf (Chapter 1, Crop Production and Management) pp. 1-3;
    # answers heep1an.pdf pp. 1-2.
    return _parse(8, "Science", "heep101", [1, 2, 3], 1, "heep1an", [1, 2])


def test_class8_science_two_column_options_are_put_back_in_label_order(science8):
    # heep101 p.1 prints "(a) High temperature" / "(c) Low temperature" /
    # "(b) Humidity" / "(d) Rainfall".
    q = _q(science8, 1)
    assert q.options == ["High temperature", "Humidity", "Low temperature", "Rainfall"]
    assert q.answer_letters == ["c"]          # heep1an p.1: "1." / "c"
    assert q.answer_text == "(c) Low temperature"


def test_class8_science_short_answer_is_paired(science8):
    q = _q(science8, 15)       # heep101 p.3: "During which months do farmers grow mustard"
    assert q.section_kind == ex.VSA
    assert q.answer_text == "October to March."   # heep1an p.1: "15. October to March."
    assert ex.exclusion_reason(q) is None


def test_class8_science_question_sentence_after_the_options_goes_back_to_the_stem():
    # heep108 p.1: "3. Read the different combinations of terms given below:"
    # (a)-(d), then "The correct combination of terms with reference to an
    # animal cell is _____." under option (d). heep1an p.20: "3." / "c".
    qs = _parse(8, "Science", "heep108", [1], 8, "heep1an", [20])
    q = _q(qs, 3)
    assert q.stem == ("Read the different combinations of terms given below: The correct "
                      "combination of terms with reference to an animal cell is _____.")
    assert q.options[3] == "cell membrane, ribosome, mitochondria, chloroplast"
    assert q.answer_letters == ["c"]
    assert ex.exclusion_reason(q) is None


def test_class8_science_figure_question_is_excluded(science8):
    q = _q(science8, 20)       # heep101 p.3: "From the word puzzle given as Fig. 1.1 ..."
    assert q.has_answer
    assert ex.exclusion_reason(q) == "figure-unavailable"


def test_class8_science_question_without_a_locatable_answer_is_excluded():
    # heep1an p.1 only: the answers stop at "17. Kharif : Rice ...", so
    # question 19 ("What are organic foods?") finds no answer.
    qs = _parse(8, "Science", "heep101", [1, 2, 3], 1, "heep1an", [1])
    assert ex.exclusion_reason(_q(qs, 19)) == "no-answer"


# --------------------------------------------------------------------------- #
# class 10
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def maths10():
    # jeep201.pdf (Chapter 1, Real Numbers) pp. 2-6; answers jeep2an.pdf pp. 1-2.
    return _parse(10, "Mathematics", "jeep201", [2, 3, 4, 5, 6], 1, "jeep2an", [1, 2])


def test_class10_maths_exercise_scoped_mcq(maths10):
    q = _q(maths10, 1, "1.1")  # jeep201 p.2: "For some integer m, every even integer is of the form"
    assert q.options == ["m", "m + 1", "2m", "2m + 1"]
    assert q.answer_letters == ["c"]          # jeep2an p.1: "EXERCISE 1.1" / "1." / "(C)"
    assert ex.exclusion_reason(q) is None
    # Question 1 of the next exercise is another question with another answer.
    assert _q(maths10, 1, "1.2").answer_text.startswith("No, because an integer")


def test_class10_maths_short_answer_and_the_proofs_the_book_leaves_unanswered(maths10):
    sa = _q(maths10, 8, "1.3")  # jeep201 p.6: "Use Euclid's division algorithm to find the HCF of 441, 567, 693."
    assert sa.section_kind == ex.SA
    assert sa.answer_text == "63"            # jeep2an p.2: "EXERCISE 1.3" / "8." / "63"
    # jeep2an answers exercise 1.3 from 8: questions 1-7 are proofs with no answer.
    proof = _q(maths10, 1, "1.3")
    assert not proof.has_answer
    assert ex.exclusion_reason(proof) == "no-answer"


def test_class10_maths_figure_question_is_excluded(maths10):
    # jeep201 p.4, exercise 1.2 question 8: the answer carries the page's figure.
    assert ex.exclusion_reason(_q(maths10, 8, "1.2")) == "figure-unavailable"


@pytest.fixture(scope="module")
def science10():
    # jeep102.pdf (Chapter 2, Acids, Bases and Salts) pp. 1-4; answers
    # jeep1an.pdf p. 7, whose "2" / "CHAPTER" stands at the END of the page.
    return _parse(10, "Science", "jeep102", [1, 2, 3, 4], 2, "jeep1an", [7])


def test_class10_science_shifted_heading_font_and_end_of_page_chapter_number(science10):
    q = _q(science10, 2)       # jeep102 p.1
    assert q.section_kind == ex.MCQ_SINGLE
    assert q.options == ["Baking powder", "Lime", "Ammonium hydroxide solution",
                         "Hydrochloric acid"]
    assert q.answer_letters == ["d"]          # jeep1an p.7: "2." / "(d)"
    assert ex.exclusion_reason(q) is None


@pytest.fixture(scope="module")
def science10_all():
    # jeep102.pdf pp. 1-8; answers jeep1an.pdf pp. 7-9.
    return _parse(10, "Science", "jeep102", range(1, 9), 2, "jeep1an", [7, 8, 9])


def test_class10_science_short_answer_is_paired(science10_all):
    q = _q(science10_all, 41)  # jeep102 p.8: "What are strong and weak acids? ..."
    assert q.section_kind == ex.SA
    assert q.stem.startswith("What are strong and weak acids?")
    # jeep1an p.9: "41." / "In aqueous solutions strong acids ionise completely ..."
    assert q.answer_text.startswith("In aqueous solutions strong acids ionise completely")
    assert q.answer_text.endswith("Weak acid — Citric acid, acetic acid , formic acid")
    assert ex.exclusion_reason(q) is None


def test_class10_science_arrow_drawn_as_o_is_a_lost_symbol(science10_all):
    # jeep1an p.9, answer 42: "Zn + 2HCl o ZnCl₂ + H₂" -- the reaction arrow
    # extracts as the letter o.
    q = _q(science10_all, 42)
    assert "Zn + 2HCl o ZnCl₂ + H₂" in q.answer_text
    assert ex.exclusion_reason(q) == "symbol-loss"


def test_class10_science_figure_question_is_excluded(science10):
    q = _q(science10, 20)      # jeep102 p.4: "... the following apparatus (Figure 2.1) was set up."
    assert q.has_answer
    assert ex.exclusion_reason(q) == "figure-unavailable"


def test_class10_science_question_without_a_locatable_answer_is_excluded():
    # jeep1an p.7 cut before "5.": questions 5 onwards find no answer.
    book = _book(10, "Science")
    page = PAGES[("jeep1an", 7)]
    cut = page[:page.index("\n5.\n")] + "\n[[display]] 2\nCHAPTER"
    qs = ex.parse_chapter_pages([PAGES[("jeep102", p)] for p in (1, 2, 3, 4)], book,
                                "jeep102.pdf", 2)
    ex.pair_answers(qs, ex.parse_answer_pages([cut], book), "jeep1an.pdf")
    by = {q.number: q for q in qs}
    assert by["2"].answer_letters == ["d"]
    assert ex.exclusion_reason(by["5"]) == "no-answer"


# --------------------------------------------------------------------------- #
# text layer and pairing rules
# --------------------------------------------------------------------------- #

def _dicts(*spans: tuple[str, str]) -> list[dict]:
    return [{"blocks": [{"lines": [{"spans": [{"font": f, "text": t} for f, t in spans]}]}]}]


def test_fonts_are_decoded_from_their_own_text():
    enc = ex.classify_fonts(_dicts(
        # class 10 science headings (jeep102): 0x1E below ASCII, space 0x02
        ("TT45CT00", "/WNVKRNG\x02%JQKEG\x023WGUVKQPU"),
        # class 10 science chapter 7 body (jeep107): 0x1D below, space 0x03
        ("Bookman", "&21752/\x03$1'\x03&225',1$7,21"),
        # class 6-8 maths headings: ASCII moved into the Private Use Area
        ("TT371T00", "".join(chr(0xF000 + ord(c)) for c in "UNIT 2")),
        ("Symbol", chr(0xF0B4)),
    ))
    assert ex.map_glyphs("/WNVKRNG\x02%JQKEG", enc["TT45CT00"]) == "Multiple Choice"
    assert ex.map_glyphs("&21752/", enc["Bookman"]) == "CONTROL"
    assert ex.map_glyphs(chr(0xF055) + chr(0xF04E), enc["TT371T00"]) == "UN"
    assert ex.map_glyphs(chr(0xF0B4), enc["Symbol"]) == "×"


def test_a_pua_letter_that_could_be_latin_or_greek_is_lost_not_guessed():
    enc = ex.classify_fonts(_dicts(("TT560T00", chr(0xF06C))))   # class 9 maths
    assert ex.map_glyphs(chr(0xF06C), enc["TT560T00"]) == ex.LOSS


def test_answers_row_holding_several_answers_is_split():
    # feep1an p.4: "58." / "No   59. (a) ∠AEB,  ∠ADE,  ∠BAE,  ∠BCE"
    book = _book(6, "Mathematics")
    key = ex.parse_answer_pages([PAGES[("feep1an", 3)], PAGES[("feep1an", 4)]], book)
    assert key.answers[(2, "", "58")][0] == "No"
    assert key.answers[(2, "", "59")][0].startswith("(a) ∠AEB")


def test_an_extra_question_printed_after_an_answer_is_not_part_of_it():
    # gemp1a1 p.45: "123. d" / "Extra Question:-" / "Write the name 5 letter
    # of English alphabet which have no line of symmetry" / "124. F, G, ...".
    lines = ["d", "Extra Question:-",
             "Write the name 5 letter of English alphabet which have no line of symmetry"]
    assert ex._answer_text(lines) == "d"


def test_questions_about_unseen_figures():
    # gemp112 p.29: the options are the pictures themselves.
    assert ex.needs_figure("Which of the following figures do not have line symmetry? "
                           "(a) (b) (c) (d)", [])
    assert ex.needs_figure("Which of the following figures satisfy the following property?",
                           ["P", "Q", "R", "S"])
    # vocabulary, not a picture
    assert not ex.needs_figure("Two figures are congruent, if they have the same shape.", [])
    assert not ex.needs_figure("For which of the following figures, diagonals are equal?",
                               ["Trapezium", "Rhombus", "Parallelogram", "Rectangle"])
    assert not ex.needs_figure("Round off to three significant figures.", [])


def test_pointer_answers():
    for a in ("Hint: See pages 223 and 224 of Chapter 18 of NCERT Science textbook for Class VII.",
              "Activity 8.6, Science Textbook, Class VII, NCERT or students may design any "
              "other activity and the teacher may verify the validity of the same.",
              "Students may come up with practical solutions during the course of discussion.",
              "Hint: Describe weaving and knitting."):
        assert ex.is_pointer_answer(a), a
    for a in ("Hint: Life may no longer exist. (See page 227-228 of textbook)",
              "Hint: Evaporation",
              "Hint: Write on the basis of lustre, hardness, softness, roughness or smoothness.",
              "No"):
        assert not ex.is_pointer_answer(a), a


def test_mcq_answer_must_name_an_option_the_question_has():
    letters, _, err = ex._letters_from_answer("(e)", 4)
    assert not letters and err


def test_chapter_mapping_is_exact_not_containment():
    syllabus = [("light-reflection", "Light – Reflection and Refraction"),
                ("symmetry-6", "Symmetry")]
    assert ex.map_chapter("Symmetry", syllabus) == "symmetry-6"
    assert ex.map_chapter("Light", syllabus) is None


# --------------------------------------------------------------------------- #
# the served-bank record
# --------------------------------------------------------------------------- #

def _dart_required_fields() -> dict[str, list[tuple[str, str]]]:
    """``required <Type> <name>`` of each freezed factory in question.dart."""
    src = (ROOT / "frontend/lib/domain/entities/question.dart").read_text(encoding="utf-8")
    out: dict[str, list[tuple[str, str]]] = {}
    for m in re.finditer(r"const factory (\w+)\(\{(.*?)\}\)", src, re.S):
        fields = re.findall(r"required\s+([\w<>?, ]+?)\s+(\w+),", m.group(2))
        out[m.group(1)] = [(t.strip(), n) for t, n in fields]
    return out


def _check(obj: dict, fields: list[tuple[str, str]], where: str) -> None:
    kinds = {"String": str, "int": int, "double": (int, float), "bool": bool,
             "DateTime": str}
    for typ, name in fields:
        assert name in obj and obj[name] is not None, f"{where}.{name} missing"
        base = typ.split("<")[0]
        if base in kinds:
            assert isinstance(obj[name], kinds[base]), f"{where}.{name} is not {typ}"
        elif base == "List":
            assert isinstance(obj[name], list), f"{where}.{name} is not a list"


def test_a_record_passes_the_dart_contract_and_is_sourced_ncert_exemplar(maths6):
    from academicos.assessment.schemas import QuestionSchema

    rec = ex.to_bank_record(_q(maths6, 2), "", current_textbook=False)
    required = _dart_required_fields()
    assert len(required["Question"]) == 21 and "textLatex" in dict(
        (n, t) for t, n in required["QuestionPart"])
    _check(rec, required["Question"], "Question")
    for part in rec["parts"]:
        _check(part, required["QuestionPart"], "QuestionPart")
    _check(rec["answerScheme"], required["AnswerScheme"], "AnswerScheme")
    for mp in rec["answerScheme"]["markingPoints"]:
        _check(mp, required["MarkingPoint"], "MarkingPoint")
    QuestionSchema.model_validate(rec)
    assert rec["source"] == "ncert_exemplar"
    assert rec["answerScheme"]["provenance"] == "ncert_exemplar_answer"
    assert rec["answerScheme"]["sourceDocumentId"] == "feep1an.pdf"
    assert rec["parts"][0]["correctOption"] == "d"
    assert rec["metadata"]["exemplarChapter"] == {"number": 2, "title": "Geometry",
                                                  "exercise": None}
    assert rec["metadata"]["marksBasis"] == "assigned_by_section_kind"
    json.dumps(rec)


def test_the_python_schema_accepts_the_new_provenance_value():
    from academicos.assessment.schemas import AnswerSchemeSchema

    s = AnswerSchemeSchema.model_validate({"totalMarks": 1, "provenance": "ncert_exemplar_answer"})
    assert s.provenance == "ncert_exemplar_answer"


# --------------------------------------------------------------------------- #
# number lines, tables and answer parts the text does not carry
# --------------------------------------------------------------------------- #

def test_class7_maths_question_about_a_drawn_number_line_is_excluded():
    # gemp101 p.9: "7. On the following number line value 'Zero' is shown by
    # the point" / "(a) X (b) Y (c) Z (d) W" -- X, Y, Z, W are points drawn on
    # the line; gemp1a1 p.1: "7. (c)".
    qs = _parse(7, "Mathematics", "gemp101", [8, 9], 1, "gemp1a1", [1])
    q = _q(qs, 7)
    assert q.options == ["X", "Y", "Z", "W"] and q.answer_letters == ["c"]
    assert ex.exclusion_reason(q) == "figure-unavailable"
    # "On the number line, the value of (-3) x 3 lies ..." needs no picture.
    assert ex.exclusion_reason(_q(qs, 9)) is None


def test_class8_maths_table_printed_as_a_picture_is_excluded():
    # heep208 p.18: "129. Astronomy The table shows the mass of the planets
    # ..." and "130. ... The table shows the average distance from each planet
    # ... (a) Complete the table ..."; the tables are not in the text, so
    # neither question can be answered. heep2an p.45 holds both answers.
    qs = _parse(8, "Mathematics", "heep208", range(5, 19), 8, "heep2an", range(42, 46))
    for n in (129, 130):
        q = _q(qs, n)
        assert q.stem.startswith(("Astronomy The table shows", "Investigating Solar System"))
        assert q.has_answer
        assert ex.exclusion_reason(q) == "figure-unavailable", n


def test_class7_maths_table_whose_rows_are_in_the_text_is_kept():
    # gemp101 p.18: "113.The table shows the lowest recorded temperatures for
    # each continent. ..." followed by every row: "Africa / -11°", ...;
    # gemp1a1 p.2: "113. Antarctica, Asia, N. America, ...".
    qs = _parse(7, "Mathematics", "gemp101", range(8, 19), 1, "gemp1a1", [1, 2])
    q = _q(qs, 113)
    assert "Antarctica –129⁰" in q.stem
    assert q.answer_text.startswith("Antarctica, Asia")
    assert ex.exclusion_reason(q) is None
    # gemp107 p.30 Q138 (the ten largest deserts) carries its rows the same way.
    assert not ex.needs_table(
        "Earth Science: The table lists the world’s 10 largest deserts. Largest Deserts in "
        "the World Desert Area (km²) Sahara (Africa) 8,800,000 Gobi (Asia) 1,300,000 "
        "Australian Desert (Australia) 1,250,000 Arabian Desert (Asia) 850,000")


def test_class6_maths_answer_missing_a_sub_part_is_excluded():
    # feep105 p.7: "26. ... (a) Arrange the choices of games in a table using
    # tally marks. (b) Which game is liked by most ... (c) ... minimum ...";
    # feep1an p.9: "26. (a)" / "(b)  Football     (c)  Tennis." -- part (a)
    # was the tally table, drawn, not text.
    qs = _parse(6, "Mathematics", "feep105", range(4, 8), 5, "feep1an", [8, 9])
    q = _q(qs, 26)
    assert q.answer_text == "(a) (b) Football (c) Tennis."
    assert ex.exclusion_reason(q) == "answer-part-missing"


def test_empty_sub_part_labels():
    for a in ("(a) (b) Football (c) Tennis.", "(i) (ii) 4", "a) b) 12", "(A)  (B) yes"):
        assert ex.has_empty_subpart(a), a
    for a in ("(a) and (b)", "(a), (b), (c) and (f)", "(b) Football (c) Tennis",
              "(i) (x + 6) (x + 3) (ii) (3x –1) (2x + 3)", "Correct sequence is – (iii), (iv), (v)",
              "(d) → (e) → (b)", "(a + b) (a – b)"):
        assert not ex.has_empty_subpart(a), a


# --------------------------------------------------------------------------- #
# the built artifact
# --------------------------------------------------------------------------- #

BUILT = ROOT / "academicos-data" / "corpus" / "ncert-exemplar" / "questions.json"


@pytest.mark.skipif(not BUILT.exists(), reason="Exemplar bank not built")
def test_every_written_record_is_servable():
    """What the parser rules promise, checked on what was actually written."""
    from academicos.assessment.schemas import QuestionSchema

    records = json.loads(BUILT.read_text(encoding="utf-8"))["questions"]
    assert records
    ids = [r["id"] for r in records]
    assert len(ids) == len(set(ids)), "duplicate record ids"
    bad: list[str] = []
    for r in records:
        QuestionSchema.model_validate(r)
        options = [o for p in r["parts"] for o in p["options"]]
        answer = r["answerScheme"]["modelAnswer"]
        text = " ".join([r["stem"], *options, answer,
                         *(mp["description"] for mp in r["answerScheme"]["markingPoints"])])
        for mark in (ex.LOSS, "\ufffd", ex.FIGURE_MARK, ex.ASIDE_MARK):
            if mark in text:
                bad.append(f"{r['id']}: contains {mark!r}")
        if ex._FIGURE.search(" ".join([r["stem"], *options, answer])):
            bad.append(f"{r['id']}: figure reference")
        if ex.needs_table(r["stem"]):
            bad.append(f"{r['id']}: table not in the text")
        if r["type"] == "mcq":
            (part,) = r["parts"]
            if len(part["options"]) != 4 or part["correctOption"] not in ("a", "b", "c", "d"):
                bad.append(f"{r['id']}: MCQ options {part['options']!r} / {part['correctOption']!r}")
        elif ex.has_empty_subpart(answer):
            bad.append(f"{r['id']}: answer has an empty sub-part")
        if not answer.strip():
            bad.append(f"{r['id']}: no answer")
    assert not bad, bad[:20]
