"""A multi-mark key is split into the value points its source printed.

Every example below is a served record as the bank carries it at c734a69 --
the id is quoted so the split can be checked against the source document.

The re-audit of 2026-09-23 measured all 2,449 served multi-mark questions
carrying exactly ONE marking point worth all the marks, so the printed key
reads "- <the whole answer> [5m]" and a teacher cannot give 3 of 5. These
tests hold `corpus/marking_split.py` to the two halves of the fix: split
where the source shows the split, and NEVER where it does not.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.corpus import marking_split as ms  # noqa: E402

HAND_CHECK = ROOT / "tests" / "fixtures" / "marking_split_handcheck.json"


# --------------------------------------------------------------------------- #
# splits the source prints
# --------------------------------------------------------------------------- #

def test_a_numbered_list_splits_into_its_items_with_the_marks_cbse_prints():
    """cbse:sqp:ClassX_2023_24:Home Science:22 -- the scheme prints "1+1=2"
    over two numbered reasons, so each reason is worth its own mark."""
    answer = ("Two reasons of preferring soaps over detergents are- 1+1=2 Soaps are- "
              "1. Cheap 2. Environment friendly(biodegradable)")
    split = ms.split_answer(answer, 2)
    assert split.rule == ms.MARKS_PRINTED
    assert [p.marks for p in split.points] == [1, 1]
    assert split.points[0].description.startswith("1. Cheap")
    assert "Environment friendly" in split.points[1].description
    assert not split.all_or_nothing


def test_any_two_of_the_following_sets_each_point_to_total_over_n_and_records_anyof():
    """cbse:sqp:ClassX_2022_23:Home Science:22 -- three ways are listed for a
    2-mark question and the scheme ends "Any other, Any two". Each listed way
    is worth 2/2 = 1, and the scheme records that only two of them are
    awarded."""
    answer = ("Two ways to maintain a good posture while working at home- 2x1=2 "
              "1. Do not work in static posture, change the posture in between. "
              "2. For pushing heavy objects, we should crouch and bend knees. "
              "3. While drying clothes, bucket should be placed on a high stool. "
              "Any other, Any two")
    split = ms.split_answer(answer, 2)
    assert split.rule == ms.ANY_OF
    assert split.any_of == 2
    assert [p.marks for p in split.points] == [1, 1, 1]
    # The instruction is not a value point: it does not ride on the last one.
    assert "Any other" not in split.points[-1].description


def test_a_lettered_answer_splits_one_point_per_part_the_book_prints():
    """exemplar:q:6:science:6:-:15 -- "Give one example in each case (a)..(e)",
    5 marks, and the answer prints all five. One part, one mark."""
    answer = ("(a) Heating of an iron rod. (b) Baking of chapati. (c) Formation of ice "
              "from water. (d) Formation of salt solution. (e) Mixing of cement and water.")
    split = ms.split_answer(answer, 5)
    assert split.rule == ms.LIST_EQUAL
    assert [p.marks for p in split.points] == [1, 1, 1, 1, 1]
    assert split.points[2].description.startswith("(c) Formation of ice")


def test_a_lead_in_before_the_first_item_is_not_a_value_point():
    """exemplar:q:9:science:14:-:45 -- "Hint—(i) ... (ii) ... (iii) ...". The
    "Hint—" lead-in carries no mark, and the three reasons carry one each."""
    answer = ("Hint—(i) Thermal pollution (ii) Addition of poisonous (mercury) compounds "
              "in water (iii) Due to blockage of gills with any pollutant.")
    split = ms.split_answer(answer, 3)
    assert [p.marks for p in split.points] == [1, 1, 1]
    assert split.points[0].description.startswith("(i) Thermal pollution")


def test_one_mark_for_each_is_read_as_the_per_point_value():
    """cbe:q:English9MH12 -- "Award 1 mark for each point, up to a maximum of
    2 marks", printed under two bulleted points on a 2-mark question."""
    answer = ("• Committing to become a better version of ourselves "
              "• Thinking about travel / exotic locations "
              "Award 1 mark for each point, up to a maximum of 2 marks.")
    split = ms.split_answer(answer, 2)
    assert split.rule == ms.MARKS_EACH
    assert [p.marks for p in split.points] == [1, 1]


# --------------------------------------------------------------------------- #
# splits the source does NOT print
# --------------------------------------------------------------------------- #

def test_prose_with_no_structure_keeps_one_point_and_says_it_is_all_or_nothing():
    """exemplar:q:10:science:15:-:30 -- a 3-mark answer in one sentence. The
    book prints no steps, so the key keeps one point and SAYS it is all or
    nothing rather than letting a teacher assume steps exist."""
    answer = ("An aquarium is an artificial and incomplete ecosystem in contrast to a "
              "pond/lake which are natural, self-sustaining and complete ecosystems.")
    split = ms.split_answer(answer, 3)
    assert split.rule == ""
    assert [p.marks for p in split.points] == [3]
    assert split.all_or_nothing


def test_a_list_that_does_not_divide_the_marks_is_not_split():
    """exemplar:q:9:science:15:-:24 -- six one-word answers (a)..(f) on a
    3-mark question. Half a mark each is not a mark this bank can carry
    (MarkingPoint.marks is an int on the phone), and any other allocation
    would be ours, not the book's."""
    answer = ("(a) organic farming (b) mixed cropping (c) inter cropping "
              "(d) crop rotation (e) weeds (f) pathogen")
    split = ms.split_answer(answer, 3)
    assert split.rule == ""
    assert [p.marks for p in split.points] == [3]


def test_a_half_mark_split_is_refused_rather_than_rounded_to_zero():
    """cbse:sqp:ClassX_2023_24:Mathematics (Standard, VIC):25 -- the scheme
    prints "½" against each of four steps of a 2-mark proof. int(0.5) is 0,
    which would print "[0m]" against a step that is worth something."""
    answer = "½ AB = 10 ½ BC = 10 ½ AC = 10√2 ½ Since AB = BC, therefore ABC is isosceles"
    split = ms.split_answer(answer, 2)
    assert split.rule == ""
    assert [p.marks for p in split.points] == [2]


def test_an_arithmetic_split_that_does_not_line_up_with_the_list_is_refused():
    """"2+1=3" over three listed points says the first is worth 2 and one of
    the other two is worth 1 -- which one, the scheme does not say here. An
    equal split would tell the teacher a mark belongs to a point the board did
    not award it for, so nothing is split."""
    answer = "2+1=3 (i) Statement of the law (ii) Its explanation (iii) One example"
    split = ms.split_answer(answer, 3)
    assert split.rule == ""
    assert [p.marks for p in split.points] == [3]


def test_a_letter_inside_a_bracket_is_not_a_list_label():
    """exemplar:q:8:mathematics:7:-:88 -- eighteen factorisations, of which
    the served key holds a few: "i) 6b (a + 2c) ii) – y (x + a) iii) x (ax² –
    bx + c) ...". The a, b and c that close its expressions read as a
    three-item list, so a 3-mark question was split into three points of
    someone else's arithmetic."""
    answer = ("i) 6b (a + 2c) ii) – y (x + a) iii) x (ax² – bx + c) "
              "iv) lmn (lm + mn – ln) v) 3r (pq – 2p²q²r – 5r)")
    split = ms.split_answer(answer, 3)
    assert split.rule == ""
    assert len(split.points) == 1


def test_a_sentence_that_names_its_parts_is_not_a_list_of_them():
    """exemplar:q:6:mathematics:3:-:71 -- "(a), (b) and (c). The number on the
    right is greater." is one answer to three parts, not three answers."""
    split = ms.split_answer("(a), (b) and (c). The number on the right is greater.", 3)
    assert split.rule == ""
    assert len(split.points) == 1


def test_an_internal_choice_answer_is_not_split():
    """cbse:sqp:ClassX_2023_24:Hindustani Music (Vocal):10 -- one key holding
    BOTH branches of an "OR". Its list items come from two different answers,
    so splitting would mix them."""
    answer = ("The candidate is expected to write date & place of birth, parentage. "
              "(OR) (i) A brief explanation of Meend (ii) Tarana (iii) Aalap")
    split = ms.split_answer(answer, 2)
    assert split.rule == ""
    assert len(split.points) == 1


def test_a_one_mark_question_is_never_split():
    split = ms.split_answer("(i) True (ii) False", 1)
    assert [p.marks for p in split.points] == [1]


def test_an_upper_case_a_and_b_are_the_two_branches_of_an_internal_choice():
    """cbse:sqp:ClassXII_2025_26:Kathakali:9 -- "(A) Name the kathakali
    Veshams. (OR) (B) Write a short note about Kalamandalam Krishnan Nair."
    Each branch is worth the whole 2 marks; splitting them 1+1 halves both."""
    answer = ("(A) Pacha, Kathi, Thadi, Kari, Minukku (B) Kalamandalam Krishnan Nair "
              "is a world renowned Kathakali artist of the 20th century.")
    split = ms.split_answer(answer, 2)
    assert split.rule == ""
    assert len(split.points) == 1


def test_a_level_of_response_rubric_is_not_a_list_of_value_points():
    """cbe:q:English9MH13 -- two bullets under "Award 2 marks for a clear
    explanation. Award 1 mark for a partial explanation": the bullets are
    strands of one answer marked as a whole, and the board never says a
    bullet is worth a mark."""
    answer = ("• Before we can go on holiday • All the pieces need to fall in place. "
              "Award 2 marks for a clear explanation. Award 1 mark for a partial one.")
    split = ms.split_answer(answer, 2)
    assert split.rule == ""
    assert len(split.points) == 1


def test_a_half_mark_a_point_split_is_not_claimed_to_be_a_mark_a_point():
    """cbse:sqp:ClassX_2022_23:Home Science:24 -- four ways of creating
    variety in meals under "½ x 4 = 2". The board's per-point value is half a
    mark, so the key stays whole."""
    answer = ("Two ways of creating variety in meals are: ½ x 4 = 2 "
              "1. Incorporate different methods of cooking 2. Choose variety of spices "
              "3. By using different consistency of dishes 4. By selecting dishes of "
              "different colours Any other, Any two")
    split = ms.split_answer(answer, 2)
    assert split.rule == ""
    assert [p.marks for p in split.points] == [2]


def test_a_group_items_key_is_not_split_over_the_groups_marks():
    """cbe:q:SCIENCE8JS41c -- a 6-mark group of three sub-parts whose key
    holds only part (a)'s three bullets. Two marks a bullet is the group's
    total divided by one part's points."""
    stem = ("1 (a) State two points of difference between the bacterial and the animal "
            "cell. 1 (b) Explain how salt prevents food spoilage. 1 (c) Justify with "
            "two examples that microorganisms can be beneficial.")
    answer = ("• Bacterial cells have a cell wall which is absent from animal cells. "
              "• Bacterial cells do not have a well-defined nucleus. "
              "• Bacterial cells do not have membrane bound cell organelles.")
    assert ms.split_answer(answer, 6, stem).rule == ""
    # The same answer, for the sub-question it actually answers, still splits.
    one_part = ms.split_answer(answer + " 1 mark for each difference", 3,
                               "1 (a) State three points of difference.")
    assert [p.marks for p in one_part.points] == [1, 1, 1]


# --------------------------------------------------------------------------- #
# the marks always add up
# --------------------------------------------------------------------------- #

def test_every_split_accounts_for_the_questions_marks():
    """The gate Task 121 added stays green: whatever the rule, the points a
    teacher can award add up to the question's marks -- under "any N", N
    points of the printed value."""
    cases = [
        ("(a) Animal husbandry. (b) Animals are provided with proper food, shelter.", 2),
        ("1. Cheap 2. Environment friendly 1+1=2", 2),
        ("(i) x (ii) y (iii) z Any other, Any two 1X2=2", 2),
        ("A single sentence with no structure at all.", 5),
        ("(i) a (ii) b (iii) c (iv) d", 4),
    ]
    for answer, marks in cases:
        split = ms.split_answer(answer, marks)
        assert ms.awardable_marks(split) == marks, (answer, marks)


def test_awardable_marks_reads_a_scheme_as_the_bank_stores_it():
    scheme = {"markingPoints": [{"marks": 1}, {"marks": 1}, {"marks": 1}],
              "metadata": {"anyOf": 2}}
    assert ms.awardable_marks(scheme) == 2
    scheme["metadata"] = {}
    assert ms.awardable_marks(scheme) == 3


def test_value_points_carry_the_wire_shape_and_say_how_they_were_derived():
    points, extras = ms.value_points(
        "(a) Animal husbandry. (b) Proper food, shelter and care.", 2, "rec:1")
    assert [p["id"] for p in points] == ["rec:1:mp1", "rec:1:mp2"]
    assert [p["marks"] for p in points] == [1, 1]
    assert points[0]["isRequired"] is True and points[0]["synonyms"] == []
    assert extras == {"markSplit": ms.LIST_EQUAL}
    _, plain = ms.value_points("One lump of prose.", 4, "rec:2")
    assert plain == {"markSplit": "", "allOrNothing": True}


# --------------------------------------------------------------------------- #
# the question's own text is not its answer
# --------------------------------------------------------------------------- #

def test_a_key_that_repeats_its_stem_no_longer_does():
    """cbse:sqp:ClassXII_2022_23:Psychology:22 -- the key opens with all 192
    characters of the question before answering it."""
    stem = ("Vinita holds a negative attitude towards individuals of a particular "
            "community. She avoids interacting or helping them in college. Identify "
            "and explain the behavioural component of her attitude.")
    answer = stem + " Behavioural component: the way a person acts towards the object."
    assert ms.strip_stem_echo(stem, answer) == (
        "Behavioural component: the way a person acts towards the object.")


def test_an_instruction_line_shared_with_the_stem_goes_with_it():
    """cbse:sqp:ClassX_2022_23:French:9 -- the key repeats the exercise
    instruction, then the marking note, then the answers."""
    stem = ("Mettez au subjonctif: (5 au choix) a. Il est nécessaire que tu ________ "
            "avec ta famille. (venir)")
    answer = ("Mettez au subjonctif: (5 au choix) Each correct answer merits 1 mark "
              "a. Il est nécessaire que tu viennes avec ta famille.")
    assert ms.strip_stem_echo(stem, answer).startswith("Each correct answer merits")


def test_an_answer_that_restates_the_premise_is_left_alone():
    """exemplar:q:9:science:4:-:33 -- "Helium atom has 2 electrons in its
    valence shell..." asked, "...in its outermost shell..." answered. The
    shared opening is not the stem: cutting at the longest common run would
    leave "s outermost shell and its duplet is complete"."""
    stem = "Helium atom has 2 electrons in its valence shell but its valency is not 2, Explain."
    answer = ("Helium atom has 2 electrons in its outermost shell and its duplet is "
              "complete. Hence the valency is zero.")
    assert ms.strip_stem_echo(stem, answer) == answer


def test_a_short_echo_is_left_alone():
    stem = "Define resistance. State its SI unit."
    answer = "Define resistance. The ratio of potential difference to current. Ohm."
    # 19 characters: under the 20 the audit measured on, and nothing worth cutting.
    assert ms.strip_stem_echo(stem, answer) == answer


def test_the_restated_question_before_an_answer_guidance_table_goes():
    """cbe:q:Science9RK5 -- the CBE mark scheme restates each sub-question
    before its Answer|Guidance table (corpus/cbse_cbe.py's own note), so the
    served key reads as three questions with one answer between them."""
    answer = ("4 (cm); 1 (b) Determine the wavelength of the wave. Answer Guidance "
              "20 (cm); 1 (c)(i) The frequency of the wave is 200 Hz. Calculate the "
              "time period of one wave. Answer Guidance (1/200=) 0.005")
    assert ms.strip_restated_questions(answer) == (
        "4 (cm); 1 (b) 20 (cm); 1 (c)(i) (1/200=) 0.005")


def test_an_answer_with_no_restatement_is_untouched():
    answer = "Cactus is the producer; the insect is a primary consumer."
    assert ms.strip_restated_questions(answer) == answer


# --------------------------------------------------------------------------- #
# the measured precision
# --------------------------------------------------------------------------- #

def test_the_hand_checked_sample_still_splits_the_way_it_was_judged():
    """51 splits read against their source PDF on 2026-09-23 -- every CBSE
    marking scheme, CBE item bank and Exemplar answer booklet the rules fired
    on, across all four rules. A rule change that moves any of them has to be
    re-judged against the source, not against this file."""
    sample = json.loads(HAND_CHECK.read_text(encoding="utf-8"))["samples"]
    assert len(sample) >= 40
    for row in sample:
        split = ms.split_answer(row["answer"], row["marks"], row["stem"])
        got = [[p.description, p.marks] for p in split.points]
        assert split.rule == row["rule"], row["id"]
        assert got == [list(p) for p in row["points"]], row["id"]
        assert split.any_of == row["anyOf"], row["id"]
        assert ms.awardable_marks(split) == row["marks"], row["id"]


def test_the_hand_checked_precision_is_at_least_0_95():
    """Under 0.95, only the rules that held ship (Task 124). Measured 50 of 51
    -- the one wrong split is an Applied Mathematics case study whose per-part
    marks ("1", "1", "2") are printed in a margin that extraction dropped."""
    sample = json.loads(HAND_CHECK.read_text(encoding="utf-8"))["samples"]
    wrong = [r for r in sample if r["verdict"] == "wrong"]
    assert len(sample) - len(wrong) >= 0.95 * len(sample), [r["id"] for r in wrong]
