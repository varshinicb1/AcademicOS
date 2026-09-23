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
# class 8 maths, unit 1: a title line inside a question, an instruction
# without a range
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def maths8_unit1():
    # heep201.pdf (Unit 1, Rational Numbers) pp. 9-18, from "(C) Exercise"
    # to question 101; answers heep2an.pdf pp. 1-2 ("Unit 1").
    return _parse(8, "Mathematics", "heep201", range(9, 19), 1, "heep2an", [1, 2])


def test_class8_maths_line_equal_to_the_chapter_title_inside_a_question_is_kept(maths8_unit1):
    # heep201 p.16 prints question 62 over two lines, "... where x and y are" /
    # "rational numbers." -- the second equal to the unit's title. Dropped as
    # a running head, the bank served "... where x and y are" keyed False.
    q = _q(maths8_unit1, 62)
    assert q.stem.endswith("where x and y are rational numbers.")
    assert q.answer_text == "False"          # heep2an p.2: "62. False"
    assert ex.exclusion_reason(q) is None


def test_title_line_is_a_running_head_only_where_and_as_heads_are_printed():
    book = _book(8, "Mathematics")
    # A running head at the top of the page is still dropped...
    top = "RATIONAL NUMBERS  15\nRational Numbers\n1. For every rational number x, x + 1 = x."
    assert [t.text for t in ex._chapter_lines([top], book, 1)] == [
        "1. For every rational number x, x + 1 = x."]
    # ...and never a line that continues a sentence, wherever it stands.
    assert not ex._reads_as_head("rational numbers.", "where x and y are")
    assert not ex._reads_as_head("Rational Numbers", "where x and y are")
    assert not ex._reads_as_head("water.", None)
    assert ex._reads_as_head("Rational Numbers", "1. For every rational number x.")


def test_class8_maths_instruction_without_a_range_types_the_questions_after_it(maths8_unit1):
    # heep201 p.15: "In each of the following, state whether the statements
    # are true (T) or false (F)." names no range. It was appended to question
    # 47, and questions 48-99 went out as 3-mark short answers keyed True/False.
    q47 = _q(maths8_unit1, 47)
    assert q47.section_kind == ex.FILL_BLANK
    assert q47.stem.endswith("with denominator as 1 are _________ and _________.")
    assert "state whether" not in q47.stem
    for n in (59, 62, 63, 78, 97):
        q = _q(maths8_unit1, n)
        assert q.section_kind == ex.TRUE_FALSE, n
        rec = ex.to_bank_record(q)
        assert (rec["type"], rec["marks"]) == ("very_short_answer", 1), n
    # Question 100, "Solve the following: Select the rational numbers ...",
    # follows with no instruction between; its answer is a list, not T/F,
    # which ends the true/false run.
    assert _q(maths8_unit1, 99).section_kind == ex.TRUE_FALSE
    for n in (100, 101):
        assert _q(maths8_unit1, n).section_kind == ex.SA, n


def test_a_statement_inside_a_question_is_not_an_open_instruction():
    # feep105 p.8, question 37 part (f): "State whether true or false: The
    # total number ...". It names a kind, but follows a label, not a finished
    # sentence, so it stays in the question.
    book = _book(6, "Mathematics")
    page = ("Exercise\n1. What is the sum of 2 and 3?\n2. Read the graph and answer.\n"
            "(e) Which shoe size is worn by minimum number of students?\n(f)\n"
            "State whether true or false: The total number of students wearing shoe\n"
            "sizes 5 and 8 is the same as the number of students wearing shoe size 6.\n"
            "3. What is the sum of 4 and 5?")
    qs = {q.number: q for q in ex.parse_chapter_pages([page], book, "x.pdf", 5)}
    assert qs["2"].stem.endswith("the same as the number of students wearing shoe size 6.")
    assert qs["3"].section_kind == ex.SA


def test_a_true_false_or_fill_in_question_carries_its_instruction(maths8_unit1):
    # The kind reached the student only as "very_short_answer", so heep201's
    # "... x + 1 = x." went out keyed False with nothing asking true or false.
    # heep201 p.15: "In each of the following, state whether the statements
    # are true (T) or false (F)." -- id exemplar:q:8:mathematics:1:-:62.
    tf = "State whether the statements are true (T) or false (F): "
    q = _q(maths8_unit1, 62)
    assert q.stem.startswith(tf)
    assert q.stem.endswith("where x and y are rational numbers.")
    assert q.instruction == tf.rstrip()
    assert ex.to_bank_record(q)["stem"] == q.stem
    assert ex.exclusion_reason(q) is None
    # heep201 p.13: "In questions 26 to 47, fill in the blanks to make the
    # statements true." -- the range goes, the book's words stay
    # (exemplar:q:8:mathematics:1:-:29; heep2an p.1 "29. positive rational number").
    q29 = _q(maths8_unit1, 29)
    assert q29.stem == ("Fill in the blanks to make the statements true: "
                        "The reciprocal of a positive rational number is ___________.")
    assert ex.exclusion_reason(q29) is None
    # Question 100 ends the true/false run (its answer is a list): it goes
    # back to short answer and loses the true/false lead-in with the kind.
    q100 = _q(maths8_unit1, 100)
    assert q100.section_kind == ex.SA and q100.instruction == ""
    assert "true (T)" not in q100.stem


def test_an_instruction_that_points_back_makes_its_questions_shared_stimulus():
    # gemp109 pp.21-22: "Observe all the four triangles FAB, EAB, DAB and CAB
    # as shown in Fig. 9.28", then "Now answer Questions 62 to 65:". Question
    # 62, "All triangles have the same base and the same altitude.", is about
    # the drawn triangles; served alone it was keyed True, which is false.
    book = _book(7, "Mathematics")
    page = ("Exercise\nIn questions 1 to 3, state whether the statements are True or False.\n"
            "1. All congruent triangles are equal in area.\n"
            "Now answer Questions 2 to 3:\n"
            "2. All triangles have the same base and the same altitude.\n"
            "3. All triangles are congruent.")
    qs = {q.number: q for q in ex.parse_chapter_pages([page], book, "x.pdf", 9)}
    assert not qs["1"].shared_stimulus
    assert qs["1"].stem == ("State whether the statements are True or False: "
                            "All congruent triangles are equal in area.")
    for n in ("2", "3"):
        assert qs[n].shared_stimulus, n
        qs[n].chapter_verified = True        # the snippet prints no "UNIT 9" head
        assert ex.exclusion_reason(qs[n]) == "shared-stimulus", n


def test_a_range_instruction_becomes_a_lead_in_in_the_books_words():
    lead = ex._question_instruction
    # feep102 p.9, feep103 p.8, gemp101 p.14, heep204 p.11
    assert lead("State whether the statements given in questions 32 to 41 are true (T) "
                "or false (F).") == "State whether the statements are true (T) or false (F):"
    assert lead("In questions 50 to 58, fill in the blanks using <, = or >.") == (
        "Fill in the blanks using <, = or >:")
    assert lead("In Questions 72 to 108, state whether the statements are True or False.") == (
        "State whether the statements are True or False:")
    assert lead("In each of the questions 1 to 16, fill in the blanks:") == "Fill in the blanks:"


# --------------------------------------------------------------------------- #
# the rendering path on real pages
# --------------------------------------------------------------------------- #

class _Point:
    def __init__(self, x, y):
        self.x, self.y = x, y


class _Rect:
    def __init__(self, x0, y0, x1, y1):
        self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1
        self.width, self.height = x1 - x0, y1 - y0


class _DrawnPage:
    def __init__(self, *rules):
        self.rules = rules

    def get_drawings(self):
        return [{"rect": _Rect(*r), "items": [("l", _Point(r[0], r[1]), _Point(r[2], r[3]))]}
                for r in self.rules]


def _line(x0, y0, x1, y1, text, block=0):
    return ex._Line(x0, y0, x1, y1, 12.0, y1 - 3, text, block)


def test_a_fraction_bar_between_two_lines_loses_both():
    # gemp110 p.24, question 93 (boxes as PyMuPDF 1.28 measures them): "7"
    # over "8 – x", the bar in the gap between. The stacked-line rule needs
    # the boxes to overlap, which they do not here, so without the bar the
    # question read "7 8 – x".
    seven = _line(179.0, 88.6, 185.3, 101.2, "7")
    denom = _line(170.4, 106.4, 193.4, 120.4, "8 – x")
    prose = _line(192.4, 189.0, 560.8, 201.0, "Critical Thinking Write two different")
    ex._mark_drawn_math([seven, denom, prose], _DrawnPage((170.3, 103.4, 194.0, 103.4)))
    assert seven.text == ex.LOSS + "7" and denom.text == ex.LOSS + "8 – x"
    assert not prose.text.startswith(ex.LOSS)
    # An underline under a line of prose, with prose below, is no fraction.
    a = _line(138.0, 300.0, 560.0, 312.0, "The rational number lies to the right of zero")
    b = _line(138.0, 316.0, 560.0, 328.0, "on the number line.")
    ex._mark_drawn_math([a, b], _DrawnPage((300.0, 313.5, 340.0, 313.5)))
    assert not a.text.startswith(ex.LOSS) and not b.text.startswith(ex.LOSS)


DATASET = ROOT.parent / "ncert-dataset" / "exemplar"
needs_dataset = pytest.mark.skipif(not DATASET.exists(), reason="ncert-dataset not on disk")


@pytest.fixture(scope="module")
def rendered():
    """Real files through `read_pdf` (render_page, classify_fonts,
    _mark_stacked, _mark_drawn_math): one render per file."""
    cache: dict[str, list[str]] = {}

    def get(folder: str, stem: str) -> list[str]:
        if stem not in cache:
            cache[stem] = ex.read_pdf(DATASET / folder / f"{stem}.pdf")
        return cache[stem]
    return get


@needs_dataset
@pytest.mark.parametrize("folder,stem,page", [
    ("classVII/mathematics", "gemp110", 24),   # a built-up fraction
    ("classX/science", "jeep102", 1),          # headings in a font shifted below ASCII
    ("classIX/mathematics", "ieep201", 4),     # radicals drawn as vector paths
])
def test_rendering_a_real_page_matches_its_fixture(rendered, folder, stem, page):
    # The parser tests run on these fixtures; a renderer change that alters
    # them must show up here, not pass unnoticed.
    assert rendered(folder, stem)[page - 1] == PAGES[(stem, page)]


@needs_dataset
def test_real_page_built_up_fraction_is_lost(rendered):
    pages = rendered("classVII/mathematics", "gemp110")
    lines = pages[23].split("\n")
    at = lines.index(ex.LOSS + "93.")
    assert lines[at + 1:at + 3] == [ex.LOSS + "7", ex.LOSS + "8 – x"]
    qs = ex.parse_chapter_pages(pages, _book(7, "Mathematics"), "gemp110.pdf", 10)
    q93 = next(q for q in qs if q.number == "93")
    q93.answer_text = "Seven divided by the difference of eight and x."
    assert ex.exclusion_reason(q93) == "symbol-loss"


@needs_dataset
def test_real_page_shifted_heading_font_and_drawn_radicals(rendered):
    assert rendered("classX/science", "jeep102")[0].startswith("Multiple  Choice  Questions\n")
    radicals = rendered("classIX/mathematics", "ieep201")[3].split("\n")
    # "2√3 + √3 is equal to": the radicals are drawn, so both lines are lost.
    at = radicals.index(ex.LOSS + "10. 2 3+")
    assert radicals[at + 1] == ex.LOSS + "3 is equal to"


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
        # A bare true/false statement is a 1-marker. Maths 9-10 "Short Answer
        # Questions with Reasoning" ("... Justify whether it is true or
        # false.") are 2-markers by the book's own section, keyed T/F.
        if (answer.strip() in ("True", "False") and r["marks"] != 1
                and r["metadata"]["sectionKind"] != ex.VSA):
            bad.append(f"{r['id']}: a true/false statement in a {r['marks']}-mark slot")
    assert not bad, bad[:20]


# --------------------------------------------------------------------------- #
# the PDF library the bank was verified on
# --------------------------------------------------------------------------- #

def test_the_running_pymupdf_is_the_one_the_bank_was_verified_on():
    # PyMuPDF 1.27.2.3 fails three of these tests and writes 10 more records,
    # their stacked fractions flattened into plain digits. The pin in
    # pyproject.toml, the lock and the guard must all name this version.
    import pymupdf

    assert pymupdf.VersionBind == ex.VERIFIED_PYMUPDF
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert f'"pymupdf=={ex.VERIFIED_PYMUPDF}"' in pyproject
    ex.require_verified_pymupdf()             # does not raise


def test_a_different_pymupdf_is_refused(monkeypatch):
    import pymupdf

    monkeypatch.setattr(pymupdf, "VersionBind", "1.27.2.3")
    with pytest.raises(RuntimeError, match=r"1\.27\.2\.3.*1\.28\.2"):
        ex.require_verified_pymupdf()
    with pytest.raises(RuntimeError, match="PyMuPDF"):
        ex.read_pdf(Path("never-opened.pdf"))


@pytest.mark.skipif(not BUILT.exists(), reason="Exemplar bank not built")
def test_committed_true_false_and_fill_in_records_carry_their_instruction():
    """577 served records lost the book's instruction (Task 701 review)."""
    records = {r["id"]: r for r in json.loads(BUILT.read_text(encoding="utf-8"))["questions"]}
    # feep101: "XXIX = 31", keyed F -- answerable only if it asks true or false.
    q = records["exemplar:q:6:mathematics:1:-:45"]
    assert re.fullmatch(r"State whether .*true.*false.*: XXIX = 31", q["stem"], re.I), q["stem"]
    assert q["answerScheme"]["modelAnswer"] == "False"
    # feep103 p.8: "0 _______ 1", keyed "<" -- only with the symbols allowed.
    q = records["exemplar:q:6:mathematics:3:-:52"]
    assert re.fullmatch(r"Fill in the blanks using <, = or >: 0 _+ 1", q["stem"]), q["stem"]
    assert q["answerScheme"]["modelAnswer"] == "<"
    bad = []
    for r in records.values():
        kind, stem = r["metadata"]["sectionKind"], r["stem"]
        lead = stem.split(":", 1)[0].lower() if ":" in stem else ""
        if kind == ex.TRUE_FALSE and not ("true" in lead and "false" in lead):
            bad.append(f"{r['id']}: {stem[:60]}")
        if kind == ex.FILL_BLANK and "fill in" not in lead:
            bad.append(f"{r['id']}: {stem[:60]}")
    assert not bad, (len(bad), bad[:10])


def test_a_derived_difficulty_and_bloom_level_say_they_were_derived(maths6):
    """Exemplar prints neither a difficulty nor a Bloom level, so
    `_difficulty_for` reads them off the marks and every record gets
    "understand". Unflagged, `selection.difficulty_signal` took the guess for a
    judgement: every marks value then held exactly one difficulty, and
    foundation, standard and advanced returned the SAME 38 questions for
    Mathematics 9 (re-audit, 2026-09-23). The other importers already flag what
    they supply (bank_merge, assessment/mapping)."""
    rec = ex.to_bank_record(_q(maths6, 2), "")
    assert rec["metadata"]["difficultyInferred"] is True
    assert rec["metadata"]["bloomInferred"] is True


# --------------------------------------------------------------------------- #
# the Exemplar chapter map (taxonomy/_exemplar_chapter_map.json)
# --------------------------------------------------------------------------- #
# An Exemplar question was printed under a numbered chapter of its own book,
# which the importer keeps as `metadata.exemplarChapter`; the served taxonomy is
# keyed by the CURRENT books. The map is that correspondence, decided once
# against the current books' contents pages (scripts/build_exemplar_chapter_map.py).

DATA = ROOT / "academicos-data"
CHAPTER_MAP = DATA / "syllabus" / "taxonomy" / "_exemplar_chapter_map.json"
EXEMPLAR_BANK = DATA / "corpus" / "ncert-exemplar" / "questions.json"
SERVED_BANK = DATA / "syllabus" / "questions.json"
SUBJECT_FILE = {"Mathematics": "Mathematics", "Science": "Science"}


def _map_rows() -> list[dict]:
    return json.loads(CHAPTER_MAP.read_text(encoding="utf-8"))["rows"]


def _bank_chapter_keys() -> set[tuple]:
    """Every (subject, grade, number, title) the Exemplar records carry, in the
    corpus the importer writes and in the bank the API serves."""
    keys = set()
    for path in (EXEMPLAR_BANK, SERVED_BANK):
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for rec in (data["questions"] if isinstance(data, dict) else data):
            chapter = (rec.get("metadata") or {}).get("exemplarChapter")
            if chapter and chapter.get("title") and rec.get("subject") in SUBJECT_FILE:
                keys.add((rec["subject"], int(rec["grade"]),
                          int(chapter["number"]), chapter["title"]))
    return keys


def test_every_chapter_the_map_names_exists_in_the_committed_taxonomy():
    """A mapped row writes its id straight onto a question, so an id the trees
    do not have would serve a chapter no catalog can name."""
    trees: dict[tuple, set] = {}
    for row in _map_rows():
        chapter_id = row["taxonomyChapterId"]
        if chapter_id is None:
            assert row["method"] == "none" and row["reason"] and row["note"], row
            continue
        assert row["method"] in {"exact-title", "contents-page", "hand-checked"}, row
        key = (row["subject"], row["grade"])
        if key not in trees:
            path = DATA / "syllabus" / "taxonomy" / f"{SUBJECT_FILE[key[0]]}_{key[1]}.json"
            trees[key] = {c["id"] for c in json.loads(path.read_text(encoding="utf-8"))["chapters"]}
        assert chapter_id in trees[key], (row["subject"], row["grade"], chapter_id)


def test_the_map_has_a_row_for_every_exemplar_chapter_the_bank_holds():
    """So a new import cannot fall through untagged and unnoticed: a chapter
    with no counterpart is a null row with its reason, never a missing row."""
    rows = {(r["subject"], r["grade"], r["exemplarNumber"], r["exemplarTitle"])
            for r in _map_rows()}
    missing = sorted(_bank_chapter_keys() - rows)
    assert missing == [], missing


def test_an_exact_title_row_really_is_the_same_title():
    """The class 10 books ARE the current books, so most of those rows claim the
    title itself. The claim is checked here, not trusted."""
    for row in _map_rows():
        if row.get("method") != "exact-title":
            continue
        assert row["currentChapter"]["title"].casefold() == row["exemplarTitle"].casefold(), row


def test_every_mapped_row_cites_a_pdf_and_a_page():
    """The task asks a row to cite the PDF and the page the current book prints
    its chapter's number and title on. A per-BOOK contents page could not do it:
    the class 10 books are distributed as one PDF per chapter with no prelims
    file, so all 22 class 10 rows cited no page, and the Ganita Prakash Part 2
    rows cited a Part 1 page that is not in the file they name."""
    for row in _map_rows():
        if not row["taxonomyChapterId"]:
            continue
        current = row["currentChapter"]
        assert current["sourceFile"], row
        assert isinstance(current["page"], int) and current["page"] >= 1, row
        assert current["printedOn"] in {"contents", "chapter-opening"}, row


TAG_SAMPLE = DATA / "syllabus" / "taxonomy" / "_exemplar_tag_sample.json"


@pytest.mark.skipif(not SERVED_BANK.exists(), reason="served bank not built")
def test_the_hand_checked_sample_is_the_one_the_seed_draws_from_this_bank():
    """Task 123 asks for a hand-check of 40 newly tagged records and the number
    wrong. A number in a report cannot be re-run, so the sample itself is
    committed: this re-derives the draw from the bank as it stands, checks the
    40 records still carry the chapter they were checked as, and re-adds the
    verdicts up. A rebuild that changes which records the map places fails here
    rather than letting an old precision stand for a new bank."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_exemplar_chapter_map as builder

    sample = json.loads(TAG_SAMPLE.read_text(encoding="utf-8"))
    served = json.loads(SERVED_BANK.read_text(encoding="utf-8"))["questions"]
    assert builder.check_sample(sample, served) == []


def test_the_sample_clears_the_precision_the_task_set():
    """0.95 on the sample, or the rows that missed do not ship (requirement 3)."""
    sample = json.loads(TAG_SAMPLE.read_text(encoding="utf-8"))
    counts = sample["counts"]
    assert counts["checked"] >= 40, counts
    assert counts["right"] / counts["checked"] >= 0.95, (
        counts, [it for it in sample["items"] if it["verdict"] != "right"])


TEXTBOOKS = ROOT.parent / "ncert-dataset" / "textbooks"


@pytest.mark.skipif(not TEXTBOOKS.exists(), reason="ncert-dataset not on disk")
def test_every_cited_page_really_prints_that_chapters_number_and_title():
    """Read back, not asserted: the citation is only worth the page it names if
    opening it finds the chapter there. This is the check
    `scripts/build_exemplar_chapter_map.py --check` runs, in the suite, so a
    re-decided row cannot keep a citation that has stopped being true."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_exemplar_chapter_map as builder

    doc = json.loads(CHAPTER_MAP.read_text(encoding="utf-8"))
    problems = builder.check_citations(doc)
    assert problems == [], problems
