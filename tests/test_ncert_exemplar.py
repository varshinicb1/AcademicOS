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
    assert ex.exclusion_reason(_q(science6, 8)) in ("figure-unavailable", "no-answer")
    assert ex.FIGURE_MARK in _q(science6, 8).stem


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
