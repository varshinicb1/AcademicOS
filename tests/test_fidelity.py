"""The bank rebuild of 2026-09-28: what the source extractions broke is repaired
where the repair is certain and refused where it is not (corpus/fidelity.py).

Every stem here is a served record's, copied as the audits of 2026-09-27 and
2026-09-28 found it; every "kept" case is a false positive a first draft of the
rules made on the real bank, and is here so it cannot come back.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.corpus import bank_merge  # noqa: E402
from academicos.corpus.fidelity import (  # noqa: E402
    CBE_SOURCE, SQP_SOURCE, figure_missing, repair_source, restore_control_symbols,
    scrambled_math,
)

SERVED = ROOT / "academicos-data" / "syllabus" / "questions.json"


def _cbe(stem: str, key: str = "an answer", *, marks: int = 2, type_: str = "short_answer",
         subject: str = "Mathematics", rid: str = "cbe:q:Maths9XX1") -> dict:
    return {"id": rid, "source": CBE_SOURCE, "subject": subject, "grade": 9, "marks": marks,
            "type": type_, "stem": stem,
            "answerScheme": {"modelAnswer": key, "markingPoints": [{"description": key, "marks": marks}]}}


def _reason(rec: dict) -> str | None:
    return repair_source(rec)[2]


# ---- refused: what no repair can put back ---------------------------------

@pytest.mark.parametrize("stem", [
    "Rohan painted 512512 of a wall white and 1313 of the wall yellow.",        # Maths6KK5
    "Which of the following is equivalent to 578578 ? (A) 5.78 (B) 5.8",         # Maths6AJ3
    "Calculate the following. 1 (a) 56+2956+29  1 (b) 534−138534−138",          # Maths6KK6
])
def test_a_fraction_extracted_twice_is_refused(stem):
    assert _reason(_cbe(stem)) == "fraction-doubled"


def test_a_year_or_a_number_that_repeats_is_not_a_doubled_fraction():
    assert _reason(_cbe("Describe the trends in Fig.1 from 2020 to 2040.")) is None
    # Outside CBE the rule is not read at all: "5050" is the sum of 1..100.
    board = {**_cbe("(A) 10100 (B) 2550 (C) 5050 (D) 10010"), "source": "cbse_board_paper"}
    assert _reason(board) is None


@pytest.mark.parametrize("stem", [
    "Find the circumference of a circle whose radius is 7cm. Use 𝜋= 7 .",          # Maths8DG1
    "a hint that if (𝑥+ 𝑥 ) = Rs. 7 then the amount is Rs. (𝑥3 + 𝑥3).",            # Maths9AG3
    "If 𝑥2 + 𝑥2 = 34, and x > 0, find the value of 𝑥3 + 𝑥3 - 9.",                  # Maths9AN7
    "find the value of (𝛼+ 𝛽) × ( 𝛽+ 𝛼)",                                          # Maths10AKP10
    "In every minute she is collecting 𝑡ℎ of the water flowing through the canal", # Maths9JJ9
    "the angles of a triangle are (x – 400), (x – 200) and ( 𝑥 2 - 100)",          # Maths9LK5
    "Simplify the following expression. 𝑠𝑖𝑛3𝜃+ 𝑐𝑜𝑠3𝜃 𝑠𝑖𝑛𝜃+ 𝑐𝑜𝑠𝜃",               # Maths10SK5
    "What is the area of a rectangle with length 9y and breadth 4y2 (A) 4y³ (B) 36y³",  # Maths8BS2
])
def test_a_lost_symbol_fraction_or_exponent_is_refused(stem):
    assert _reason(_cbe(stem)) == "symbol-loss"


def test_an_italic_word_before_a_number_is_not_a_lost_fraction():
    # Maths9AG4 reads "3x−2 = 0 and 2y−1 = 0", "and" set in italic.
    assert _reason(_cbe("Draw the graph of 3 𝑥−2 = 0 𝑎𝑛𝑑 2𝑦−1 = 0")) is None
    # Maths10SS8: alpha + beta - alpha*beta is what the key computes.
    assert _reason(_cbe("find the value of 𝛼+ 𝛽−𝛼𝛽 (A) 4 √3 (B) -3")) is None


def test_part_labels_run_together_ahead_of_their_text_are_refused():
    assert _reason(_cbe("1 (a) 1 (b) Two students in class of IX named Ria and Ravya")) == "parts-detached"
    assert _reason(_cbe("1 (a) Find the perimeter.  1 (b) Find the area.")) is None


def test_a_key_for_one_part_of_several_is_refused():
    rec = _cbe("1 (a) Describe a method to obtain clean water.  1 (b) Identify the method ...",
               "B. Filtration", marks=4, subject="Science")                          # Science6RAJ6b
    assert _reason(rec) == "key-covers-one-part"
    assert _reason(_cbe("Name the process.", "B. Filtration", marks=1)) is None


def test_an_sqp_mathematics_stem_in_math_italic_is_scrambled():
    rec = {"source": SQP_SOURCE, "subject": "Mathematics (Standard)",
           "stem": "If 𝜃 = 30𝑜 then the value of 3tan𝜃 is 1 3 A)1 B) C ) (D) not defined √3 √3"}
    assert scrambled_math(rec)
    assert not scrambled_math({**rec, "stem": "Mitul invested ₹ 3,50,000 in a fund."})
    assert not scrambled_math({**rec, "subject": "Physics"})


# ---- the visual a stem points at ------------------------------------------

@pytest.mark.parametrize("stem", [
    "The given bar graph represents the number of tickets sold.",       # Maths6AT5
    "Use the bar graph to answer the following questions",              # Maths7PS5
    "1. Rhizopus is a type of fungi. Fig.1 shows Rhizopus growing.",    # Science6SRN2
    "1. In figure 1 given above, O is the centre",                      # Math10MM8
    "1 A diagram of a neuron is shown. Which row is correct?",          # Science9ML2
    "Two lenses are shown. Which statement is correct about lens A?",   # Science10GK2
    "In the above triangle, ABC is an isosceles triangle",              # Maths9LK3
    "The details of books they could collect are tabulated above.",     # Maths10AD8
    "find the cost of painting the toy. 4) Diagram not drawn to scale", # Maths10AKP8
    "A student plots the current-voltage graphs of three samples",      # Science10TM2
    "Read the above bar graph and answer the following questions.",     # Maths9NM6
    "The following histogram shows the frequency distribution",         # Exemplar 8.2.105
])
def test_a_visual_the_stem_points_at_is_missing(stem):
    assert figure_missing(stem)


@pytest.mark.parametrize("stem", [
    "What kind of change is shown by tearing of paper?",                              # Exemplar 7.6.13
    "Read the above passage and draw a neat and labelled diagram of Tanpura",         # SQP Hindustani 15
    "Calculate the 3-month moving average. Plot the graph to represent the trend.",   # SQP Applied Maths
    "Draw a pie chart to show this information.",                                     # Maths8PN7
    "She has a square chart paper of side 60cm. How many cards can she make?",       # Exemplar 6.6.50
])
def test_a_stem_that_asks_for_a_visual_or_names_one_in_passing_is_kept(stem):
    assert not figure_missing(stem)


# ---- repaired: certain transformations ------------------------------------

def test_the_source_mark_column_and_total_line_go():
    rec, made, _ = repair_source(_cbe("Give your answer in simplest form.   4)"))
    assert rec["stem"] == "Give your answer in simplest form."
    rec, made, _ = repair_source(_cbe("Suggest why the farmer uses fungicide.  (Total 10 marks)"))
    assert rec["stem"] == "Suggest why the farmer uses fungicide."
    assert "total-marks-removed" in made
    rec, _, _ = repair_source(_cbe("Represent -1/3 on a number line.  (Total mark 1)"))   # Maths8PM3
    assert rec["stem"] == "Represent -1/3 on a number line."


def test_a_key_is_cut_where_it_runs_into_the_next_item():
    key = ("44cm. Allow one mark for correct answer only. Maths8PD4 This assessment item is "
           "designed to assess the end of class assessments for CBSE schools.")
    rec, _, _ = repair_source(_cbe("Find the circumference.", key, rid="cbe:q:Maths8DG1"))
    assert rec["answerScheme"]["modelAnswer"] == "44cm. Allow one mark for correct answer only."
    rec, _, _ = repair_source(_cbe("x", "Rs. 322 ... = 322 Maths9NM2", rid="cbe:q:Maths9AG3"))
    assert rec["answerScheme"]["modelAnswer"] == "Rs. 322 ... = 322"


def test_mark_codes_are_written_out_in_a_mathematics_key_only():
    rec, _, _ = repair_source(_cbe("q", "Rs 40,000 M1 (100−85) × 50000 A1 Rs 7,500 B1 more"))
    assert rec["answerScheme"]["modelAnswer"] == (
        "Rs 40,000 [1 mark: method] (100−85) × 50000 [1 mark: answer] Rs 7,500 [1 mark] more")
    rec, _, _ = repair_source(_cbe("q", "Vitamin B1 deficiency", subject="Science"))
    assert rec["answerScheme"]["modelAnswer"] == "Vitamin B1 deficiency"


def test_math_italic_reads_as_plain_letters_and_a_flattened_exponent_is_raised():
    rec, _, _ = repair_source(_cbe("The amount is given by the expression 12𝑥2 + 11𝑥−15.",
                                   "𝑚1: 𝑚2 = 1:2 (𝑥1, 𝑦1)"))
    assert rec["stem"] == "The amount is given by the expression 12x² + 11x−15."
    # In a key a digit after a letter is as often a subscript: letters only.
    assert rec["answerScheme"]["modelAnswer"] == "m1: m2 = 1:2 (x1, y1)"
    rec, _, _ = repair_source(_cbe("If ∠𝐴= 36𝑜. Find the volume in 𝑐𝑚3."))
    assert rec["stem"] == "If ∠A= 36°. Find the volume in cm³."


def test_the_item_bank_header_before_a_question_goes():
    stem = ("Item identity AO1 marks AO2 marks C/N/E* Content Reference(s) Marks Maths8PW4 N 8G1d "
            "Apply Euler’s relation *C = Calculator required Item purpose The question assesses "
            "Source(s) Source information: book/journal, author, publisher, website link etc. "
            "1 The number of edges of a prism is 9. (A) 2 (B) 4 (C) 5 (D) 9")
    rec, made, _ = repair_source(_cbe(stem, type_="mcq", marks=1, rid="cbe:q:Maths8PW4"))
    assert rec["stem"].startswith("1 The number of edges")
    assert "item-header-removed" in made
    # The same header opening with the item bank's own sentence, and its
    # reference line left between two parts (cbe:q:Maths9DP8).
    stem = ("This assessment item is designed to assess the end of class assessments for CBSE "
            "schools. Item identity AO1 marks Maths9DP8a C 9M2a Calculate the surface areas. "
            "Item purpose This question assesses volume. Sources and diagrams Questions Meera’s "
            "bedroom has 3 closets. 1 (a) Which closet? Show your working.  Subject Class Question "
            "reference/Filename Maths Maths9DP8 1 (b) Calculate the total surface area.")
    rec, _, _ = repair_source(_cbe(stem, marks=6, rid="cbe:q:Maths9DP8"))
    assert rec["stem"] == ("Meera’s bedroom has 3 closets. 1 (a) Which closet? Show your working. "
                           "1 (b) Calculate the total surface area.")
    # With nothing after it, the header is still a header, and refused.
    assert bank_merge._HEADER.match("Item identity AO1 marks AO2 marks")


def test_the_exemplar_symbol_font_control_characters_are_restored():
    assert restore_control_symbols(
        "It is given that \x04\x02ABC ~ \x04\x02DFE, \x01A =30°, PQ\x01 RS and PD \x03 QR") == \
        "It is given that ΔABC ~ ΔDFE, ∠A =30°, PQ∥ RS and PD ⊥ QR"
    # Everywhere, the options in its parts included, so the key still matches one.
    rec = {"id": "exemplar:q:10:mathematics:6:6.1:9", "source": "ncert_exemplar", "type": "mcq",
           "stem": "\x01A =30°", "parts": [{"options": ["\x01F = 50°", "\x01F = 100°"]}],
           "answerScheme": {"modelAnswer": "\x01F = 100°", "markingPoints": []}}
    fixed, made, _ = repair_source(rec)
    assert fixed["parts"][0]["options"] == ["∠F = 50°", "∠F = 100°"]
    assert fixed["answerScheme"]["modelAnswer"] == "∠F = 100°"
    assert made == ["control-symbols-restored"]


def test_empty_option_labels_after_an_open_question_go():
    rec = {"id": "exemplar:q:7:science:4:-:18", "source": "ncert_exemplar", "type": "short_answer",
           "stem": "In which direction should the windows preferably face and why? (A) (B)",
           "answerScheme": {"modelAnswer": "towards the sea", "markingPoints": []}}
    assert repair_source(rec)[0]["stem"] == "In which direction should the windows preferably face and why?"


def test_the_question_number_is_left_as_printed():
    """Stripped before the gates, "1 (a) ... 1 (b)" on a 1-mark item stopped
    reading as a group and cbe:q:Maths6MG4 was served (a 3-mark question keyed
    for one part under 1 mark); stripped after them, the value-point splitter
    split three keys wrongly. The number is what the other rules read."""
    rec, _, _ = repair_source(_cbe("1 (a) Calculate the fraction.  1 (b) Convert it.", "x 1 (b) y"))
    assert rec["stem"] == "1 (a) Calculate the fraction.  1 (b) Convert it."
    assert rec["answerScheme"]["modelAnswer"] == "x 1 (b) y"
    raw = _cbe("A boy walks around a garden. 1 (a) What is the perimeter?  1 (b) How far does "
               "he walk each day?", "2(a+b)", marks=1, type_="very_short_answer")
    raw, _, reason = repair_source(raw)
    assert reason is None
    _, reason = bank_merge.normalise(raw)
    assert reason == "stem-holds-group"


# ---- the rebuilt bank -------------------------------------------------------

@pytest.mark.skipif(not SERVED.exists(), reason="served bank not built")
def test_the_served_bank_holds_none_of_the_audits_examples():
    served = {r["id"]: r for r in json.loads(SERVED.read_text(encoding="utf-8"))["questions"]}
    gone = ["Maths6KK5", "Maths6KK6", "Maths6AJ3", "Maths6AT5", "Maths7PS5", "Maths8PM2",
            "Maths9JJ1", "Maths8DG1", "Maths8BS2", "Maths9LK3", "Maths9DP7", "Math10MM8",
            "Science6SRN2", "Science9ML2", "Science9SD2", "Science10TM2", "Science10GK2",
            "Science10DP1", "Science10SK4", "Science10RR31d", "Maths9AG3", "Maths10AD8",
            "SCIENCE7ARP", "Maths10AKP8", "Science6RAJ6b", "Maths9AG4"]
    assert [g for g in gone if f"cbe:q:{g}" in served] == []
    texts = [(r["id"], r["stem"] + " " + str((r.get("answerScheme") or {}).get("modelAnswer") or ""))
             for r in served.values()]
    assert [i for i, t in texts if "This assessment item is designed" in t] == []
    assert [i for i, t in texts if any(c in t for c in "\x01\x02\x03\x04")] == []
    cbe = [r for r in served.values() if r.get("source") == CBE_SOURCE]
    assert [r["id"] for r in cbe if any(0x1D400 <= ord(c) <= 0x1D7FF for c in r["stem"])] == []
    # The source's mark column ("...   4)") and its total line, both spellings.
    assert [r["id"] for r in cbe if re.search(r"\s{2,}\d{1,2}\)\s*$", r["stem"])] == []
    assert [r["id"] for r in cbe if re.search(r"\(Total\s+(?:\d+\s+)?marks?\b", r["stem"], re.I)] == []
