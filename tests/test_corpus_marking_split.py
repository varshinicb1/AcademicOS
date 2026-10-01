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
SERVED = ROOT / "academicos-data" / "syllabus" / "questions.json"


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


def test_a_worked_solutions_steps_split_where_the_scheme_codes_them():
    """cbe:q:Maths6KK3 -- 2 marks, and the scheme prints the two steps of the
    working with the mark each earns: "M1 perimeter of top surface 10.45 +
    4.36 + 10.45 + 4.36 or equivalent" and "A1 = 29 .82cm" (Item-Bank---Maths-
    Class-6.pdf p31). M is the method mark, A the accurate result; the digit
    is that step's marks, and the last line of each step is its result."""
    answer = ("29.82cm M1 perimeter of top surface 10.45 + 4.36 + 10.45 + 4.36 "
              "or equivalent A1 = 29 .82cm Allow 2 Marks for correct answer")
    split = ms.split_answer(answer, 2)
    assert split.rule == ms.STEP_MARKS
    assert [p.marks for p in split.points] == [1, 1]
    assert split.points[0].description.startswith("M1 perimeter of top surface")
    assert split.points[1].description.startswith("A1 = 29 .82cm")
    assert not split.all_or_nothing


def test_a_three_step_solution_carries_the_mark_the_board_codes_on_each_step():
    """cbe:q:Maths8DB4 -- 3 marks over "M1 4 x 2(12+8) OR equivalent OR 160
    seen", "M1 their 160 x 5", "A1 Rs 800" (Item-Bank---Maths-Class-8.pdf
    p75). A student who reaches 160 and stops has earned one of the three."""
    answer = ("Rs. 800 M1 4 x 2(12+8) OR equivalent OR 160 seen M1 their 160 x 5 "
              "A1 Rs 800 Allow missing units")
    split = ms.split_answer(answer, 3)
    assert split.rule == ms.STEP_MARKS
    assert [p.marks for p in split.points] == [1, 1, 1]
    assert split.points[1].description.startswith("M1 their 160 x 5")


def test_step_codes_that_do_not_account_for_the_marks_are_not_a_split():
    """cbe:q:Maths9GB8 -- a 4-mark question whose served key carries "M1 A1 –
    to find correct inner radius and use correct formula". Two marks of the
    four are printed; where the other two went, the key does not say."""
    answer = ("𝑟 = 9cm Surface area = 2𝜋𝑟2 = 508.68 cm2 Cost of painting = "
              "508.68 cm2 × 2 = ₹ 1017.36 M1 A1 – to find correct inner radius "
              "and use correct formula")
    split = ms.split_answer(answer, 4)
    assert split.rule == ""
    assert [p.marks for p in split.points] == [4]


def test_a_step_code_with_nothing_beneath_it_is_not_a_value_point():
    """cbe:q:Maths9LK5 -- "... ⇒ x = 1000 M1 to use the angle sum property of
    a triangle. A1": the A1 closes the key with no step of its own, so what
    it was awarded for is not in the text."""
    answer = ("x = 1000 (x – 400)+ (x – 200) +( 𝑥 2 - 100) = 1800 ⇒ x = 1000 "
              "M1 to use the angle sum property of a triangle. A1")
    split = ms.split_answer(answer, 2)
    assert split.rule == ""
    assert len(split.points) == 1


def test_a_mark_printed_after_each_value_point_is_read():
    """The annotation Task 124 names first -- "... 1" -- printed against each
    point of a list rather than once for the list ("1 mark each")."""
    answer = "(i) Definition of refraction 1 (ii) Statement of the two laws 2"
    split = ms.split_answer(answer, 3)
    assert split.rule == ms.MARKS_PRINTED
    assert [p.marks for p in split.points] == [1, 2]
    # The annotation is not part of what the point says.
    assert split.points[0].description == "(i) Definition of refraction"


def test_a_number_that_is_the_answer_is_not_a_printed_mark():
    """Every Exemplar maths key whose items ARE numbers -- "a) 8 b) 13"
    (exemplar:q:8:mathematics:3:-:97), "(i) 49 (ii) 28"
    (exemplar:q:7:mathematics:1:-:125) -- ends each item in a digit that is
    the answer. A mark is printed BESIDE a point that says something; a bare
    number on its own is the point itself."""
    assert ms.split_answer("a) 8 b) 13", 3).rule == ""
    assert ms.split_answer("(i) 49 (ii) 28", 3).rule == ""
    # ... including when the numbers do add up to the question's marks.
    assert ms.split_answer("(i) 1 (ii) 2", 3).rule == ""


def test_marks_for_a_named_component_are_read_when_they_account_for_the_marks():
    """cbe:q:English9AM33 -- "Award 1 mark for a valid explanation of
    'daunting'. Award 1 mark for a valid explanation of 'venture'."
    (Item-Bank-----English---Class-9.pdf p36). The two explanations are the
    answer column of a two-row table that flattens into one line, so nothing
    in the answer reads as a list -- but the board named its two points and
    what each is worth."""
    answer = ("‘venture’ suggests the transformation is risky / daring (however expressed) "
              "‘daunting’ suggests the venture is intimidating / formidable (however "
              "expressed) Award 1 mark for a valid explanation of ‘daunting’. "
              "Award 1 mark for a valid explanation of ‘venture’.")
    split = ms.split_answer(answer, 2)
    assert split.rule == ms.MARKS_FOR
    assert [p.marks for p in split.points] == [1, 1]
    assert "daunting" in split.points[0].description
    assert "venture" in split.points[1].description




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


def test_any_one_of_the_following_is_not_divided_equally():
    """"Any one of the following" over three reasons on a 3-mark question:
    the board awards all three marks to whichever ONE the student gives, so
    1/1/1 tells a teacher that two thirds of the answer is missing when it is
    not. Which single point carries the three marks is not something a scheme
    can record, so the key stays whole and says it is all or nothing."""
    answer = ("Any one of the following: (i) Reason A here (ii) Reason B here "
              "(iii) Reason C here")
    split = ms.split_answer(answer, 3)
    assert split.rule == ""
    assert [p.marks for p in split.points] == [3]


def test_any_one_of_each_part_is_an_instruction_inside_the_parts():
    """cbse:sqp:ClassXII_2022_23:Home Science:29 -- "Give one role of each of
    the following- a. ... b. ... c. ...", 3 marks, and the scheme closes "Any
    other, Any one role of each". The "any one" is one ROLE per part, not one
    part of the three, so the three parts still carry a mark each."""
    answer = ("a.Assistant manager of front office- 3x1=3 1. Organizes and supervises "
              "front office in absence of front office manager 2. Ensures smooth "
              "functioning of the front office b.Chef de parties- Supervision of some "
              "sections of kitchen c.Floor supervisor of housekeeping department- "
              "Responsible for cleanliness and maintenance of guest room "
              "Any other, Any one role of each")
    split = ms.split_answer(answer, 3)
    assert split.rule == ms.LIST_EQUAL
    assert [p.marks for p in split.points] == [1, 1, 1]


def test_a_statement_before_the_list_is_not_a_lead_in():
    """cbse:sqp:ClassXII_2025_26:Sociology:24 -- the marking scheme prints
    THREE bullets against 2 marks and the parser lost the first bullet's
    marker, so the key reads "Workers get exhausted earlier than otherwise.
    <bullet> ... <bullet> ...". Splitting the two that kept their bullet gives
    a mark each to two of the board's three points and none to the third: a
    mark placed where the board did not put it. Text before the list that ENDS
    a sentence is a statement of its own, not an introduction to the list, and
    no value point accounts for it -- so the key stays whole."""
    answer = ("Workers get exhausted earlier than otherwise. • Workers will take "
              "voluntary retirement. • Increased productivity, efficiency and profit.")
    split = ms.split_answer(answer, 2)
    assert split.rule == ""
    assert [p.marks for p in split.points] == [2]
    assert split.all_or_nothing


def test_a_key_holding_its_neighbours_answers_is_not_split():
    """exemplar:q:9:mathematics:3:3.3:8 -- the Exemplar answers file prints
    its exercise as one run, "8. C, D, E, G 10. (7, 0), (0, -7) 11. (i) (0, 0)
    (ii) (0,- 4) (iii) (5, 0)", and this record's key kept all of it. The list
    at the end is question 11's answer; question 8's own answer is "C, D, E,
    G", in front of it. Splitting the list would award this question's three
    marks to another question's answer."""
    answer = ("C, D, E, G 10. (7, 0), (0, –7) 11. (i) (0, 0) (ii) (0,– 4) "
              "(iii) (5, 0)")
    split = ms.split_answer(answer, 3)
    assert split.rule == ""
    assert [p.marks for p in split.points] == [3]


def test_a_lead_in_that_runs_into_its_list_still_introduces_it():
    """The other side of the rule, so it cannot be read as "any prose before a
    list refuses the split". exemplar:q:6:science:2:-:16 prints "Vitamins and
    minerals are very important because they help in (a) ... (b) ... (c) ...":
    the text before the list does not end a sentence, the items complete it,
    and each of the three carries a mark of the three."""
    answer = ("Vitamins and minerals are very important because they help in "
              "(a) protecting our body against diseases. (b) growth. "
              "(c) maintaining good health.")
    split = ms.split_answer(answer, 3)
    assert split.rule == ms.LIST_EQUAL
    assert [p.marks for p in split.points] == [1, 1, 1]


def test_a_case_studys_parts_are_not_divided_equally():
    """cbse:sqp:ClassXII_2022_23:Applied Mathematics:38 -- a case study whose
    three parts the paper's own general instructions weight 1, 1 and 2 ("Each
    case study comprises of 3 case-based questions, where 2 VSA type questions
    are of 1 mark each and 1 SA type question is of 2 marks", Applied-Maths-
    SQP.pdf p1). The per-part marks are printed in a margin column extraction
    drops, so an equal division is the one allocation we know is wrong."""
    stem = ("CASE STUDY - III Based on the above information, answer the following "
            "questions. a) Find the value of k. 1 b) What is the probability that "
            "Sonali will get admission? c) Calculate the mathematical expectation.")
    answer = ("CASE STUDY - III a) ⇒𝑘= 1 4 b) P (X = 2,3,4) = 23 24 "
              "c) ∴ E(X) = 3 weeks")
    split = ms.split_answer(answer, 6, stem)
    assert split.rule == ""
    assert [p.marks for p in split.points] == [6]


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
    # As the served bank prints it since the extraction repair of 2026-10-01
    # (dde445a), which took the "1 " off the labels after the first as leaked
    # marks: one numbered label, then plain ones. Still a group.
    repaired = ("1 (a) State two points of difference between the bacterial and the animal "
                "cell.  (b) Explain how salt prevents food spoilage.  (c) Justify with two "
                "examples that microorganisms can be beneficial.")
    assert ms.split_answer(answer, 6, repaired).rule == ""
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


def test_an_echo_that_differs_from_its_stem_only_in_spacing_is_still_cut():
    """cbse:sqp:ClassXII_2024_25:French:10 -- the key repeats the exercise
    instruction with a space before its colon ("préposition :" against the
    paper's "préposition:"), and cbse:sqp:ClassXII_2022_23:French:4C breaks
    the run at "y/en/ etc" against "y/en/etc". Comparing character by
    character stops at the space and leaves the whole question standing, so
    the comparison ignores spacing and the cut still lands on the colon."""
    stem = ("Complétez avec une préposition: a. Ma femme a mis des pâtes cuire dans "
            "une casserole. b. Mon étudiant a décidé quitter ses études.")
    answer = ("Complétez avec une préposition : a. Ma femme a mis des pâtes pour cuire "
              "dans une casserole. b. Mon étudiant a décidé de quitter ses études")
    assert ms.strip_stem_echo(stem, answer).startswith("a. Ma femme a mis des pâtes pour")


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
    """127 keys read against their source PDF -- every CBSE marking scheme,
    CBE item bank and Exemplar answer booklet the rules fire on, across all
    six rules, plus the four keys they are held back from. A rule change that
    moves any of them has to be re-judged against the source, not against this
    file."""
    sample = json.loads(HAND_CHECK.read_text(encoding="utf-8"))["samples"]
    assert len([r for r in sample if r["rule"]]) >= 40
    for row in sample:
        split = ms.split_answer(row["answer"], row["marks"], row["stem"])
        got = [[p.description, p.marks] for p in split.points]
        assert split.rule == row["rule"], row["id"]
        assert got == [list(p) for p in row["points"]], row["id"]
        assert split.any_of == row["anyOf"], row["id"]
        assert ms.awardable_marks(split) == row["marks"], row["id"]


def test_the_hand_checked_precision_is_at_least_0_95():
    """Under 0.95, only the rules that held ship (Task 124). Measured over the
    keys that SHIP a split -- a key the rules refuse cannot be a wrong split,
    and the sample keeps it (`verdict: none`) only so the reason stays with
    the record. 122 of 123 on 2026-09-24. The one that ships wrong is
    exemplar:q:9:mathematics:14:14.2:2, where the book answers "Median will be
    a good representative of the data, because (i) ... (ii) ..." and the split
    gives both marks to the two reasons: naming the median is half of what the
    stem asks, and its mark goes to a point that is not it."""
    sample = json.loads(HAND_CHECK.read_text(encoding="utf-8"))["samples"]
    shipped = [r for r in sample if r["rule"]]
    wrong = [r for r in shipped if r["verdict"] == "wrong"]
    assert len(shipped) - len(wrong) >= 0.95 * len(shipped), [r["id"] for r in wrong]
    # A row that ships no split is not a pass mark: it says so.
    assert all(r["verdict"] == "none" for r in sample if not r["rule"])
    # Nor is a wrong one recorded without the reading that found it wrong.
    assert all(r["why"] for r in sample if r["verdict"] != "correct")


def test_every_split_the_rules_fire_on_the_served_bank_is_hand_checked():
    """The sampling gate, and the reason it exists.

    Precision is only measured where a key was read against its source, so a
    rule the check never reached is a claim with no evidence under it. When
    this sample was first written it held every any-of, step-marks,
    marks-each, marks-printed and marks-for split but only 24 of the 74
    `list-equal` ones -- the highest-volume rule, and the only one whose
    allocation is ours (divide the marks over the parts the source shows)
    rather than a transcription of what the board printed. Reading the other
    fifty found two wrong splits and one key that had swallowed its
    neighbours' answers; the statement lead-in rule refuses all three.

    Every key the rules split on the served bank is now in the sample, by id,
    whether the bank still carries it as one lump point (the split is then
    predicted, as scripts/check_marking_split.py predicts it) or a rebuild has
    already written the split into the record.
    """
    if not SERVED.exists():                       # a checkout without the bank
        return
    raw = json.loads(SERVED.read_text(encoding="utf-8"))
    records = raw["questions"] if isinstance(raw, dict) else raw
    checked = {row["id"] for row in
               json.loads(HAND_CHECK.read_text(encoding="utf-8"))["samples"]}

    missing = []
    for record in records:
        scheme = record.get("answerScheme") or {}
        points = scheme.get("markingPoints") or []
        rule = (scheme.get("metadata") or {}).get("markSplit")
        if not rule:
            if len(points) != 1:
                continue
            marks = int(record.get("marks") or 0)
            key = points[0].get("description") or ""
            if marks <= 1 or not key.strip():
                continue
            stem = record.get("stem") or ""
            rule = ms.split_answer(ms.strip_stem_echo(stem, key), marks, stem).rule
        if rule and record.get("id") not in checked:
            missing.append(record.get("id"))
    assert not missing, missing[:20]


def test_a_split_that_awards_more_than_the_question_is_refused():
    """cbse:sqp:ClassXII_2022_23:Psychology:21, a 2-mark question, came out of
    the rebuild with SIX points of 1 mark: the scheme lists six ethical
    principles and prints "(1+1)", meaning any two of them. Read as six
    required points it tells a teacher to award 6 marks on a 2-mark question.
    Where the marks do not add up and the source never said "any N", there is
    no split to be had."""
    answer = ("Informed consent needs to be taken 2. Confidentiality of the client "
              "should be maintained 3. Alleviating personal distress and suffering "
              "should be the goal 4. Integrity of the practitioner-client relationship "
              "is important 5. Respect for human rights and dignity 6. Professional "
              "competence and skills are essential (1+1)")
    points, extras = ms.value_points(answer, 2, "q")
    assert len(points) == 1, [p["description"] for p in points]
    assert extras.get("allOrNothing") is True


def test_a_point_that_is_the_annotation_and_not_the_answer_is_refused():
    """cbse:sqp:ClassXII_2023_24:Informatics Practices:19 split into
    "correct explanation) (1 mark for correct example)" and "correct example)"
    -- the marking instruction chopped up, with no answer in it. A value point
    a teacher cannot mark against is worse than one lump they can."""
    answer = "(1 mark for correct explanation) (1 mark for correct example)"
    points, extras = ms.value_points(answer, 2, "q")
    assert len(points) == 1, [p["description"] for p in points]
