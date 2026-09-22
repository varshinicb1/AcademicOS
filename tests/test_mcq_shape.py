"""mcq_shape: reading an MCQ's options and its key, with nothing else in play."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from academicos.corpus import mcq_shape as ms  # noqa: E402


# ---- MCQ answer recovery ----------------------------------------------------

OPTS = {"A": "avoid", "B": "control", "C": "forget", "D": "understand"}


@pytest.mark.parametrize("answer,expected", [
    ("B. control Award 1 mark for the correct answer", "B"),
    ("A – avoid", "A"),
    ("(C) forget", "C"),
    ("D", "D"),
    ("understand Award 1 mark", "D"),          # bare option text, no letter
])
def test_correct_letter_is_recovered(answer, expected):
    assert ms.correct_letter([answer], OPTS) == expected


@pytest.mark.parametrize("answer", [
    "a.A – III; B – IV; C- II; D – I",        # a matching-question key
    "modernity A. 1 & 3 B. 2 &4 C. 2 & 5 D. 1 &",          # bled-in question text
    "Read the following data and select the appropriate option",
    "Fill in the blank: SECTOR CRITERIA USED",
    "Find the odd one out from the following options",
    "something that is no option",
    "",
])
def test_a_wrong_letter_is_never_invented(answer):
    """Returning 'A' for a matching key would ship a confidently wrong answer."""
    assert ms.correct_letter([answer], OPTS) is None


# Every case got a letter from a looser reading (the letter alone, or text
# compared with signs dropped). The ones with an id are real keys from the banks.
@pytest.mark.parametrize("answer,options", [
    # cbe:q:Maths8PR3 -- the letter says A, the value is option C
    ("A. 243", {"A": "343", "B": "340", "C": "243", "D": "342"}),
    # cbe:q:Science6SPA2 -- the letter says C, the word is option D
    ("C. Melt", {"A": "Dissolve", "B": "Evaporate", "C": "Freeze", "D": "Melt"}),
    # cbe:q:Science10NG1 -- the letter says A, the words are option B's
    ("A. Combination reaction", {"A": "a decomposition reaction", "B": "a combination reaction",
                                 "C": "a displacement reaction", "D": "an exothermic reaction"}),
    # cbe:q:Maths10AS3 -- the value is no option at all
    ("B. 6 cm", {"A": "4.0 cm", "B": "8.5 cm", "C": "13.0 cm", "D": "18.0 cm"}),
    # cbe:q:Science9RK6 -- a two-part "write the formula" item, not an MCQ
    ("(a) Na₂CO₃ (1) (b) (NH₄)₂SO₄ (1)",
     {"A": "sodium carbonate", "B": "ammonium sulphate"}),
    # a lowercase matching key: its leading "a-" is not option A
    ("a-iii, b-iv, c-i, d-ii", OPTS),
    # SQP Hindustani Music (Percussion) 2022-23 Q5 -- "3" is option 3 of a numbered
    # list, (A)-(D) are statements; reading it as the text of option D ships D
    ("3", {"A": "12", "B": "10", "C": "6", "D": "3"}),
    # a sign is part of the value: 48 is not -48
    ("-48", {"A": "48", "B": "50", "C": "-50", "D": "12"}),
])
def test_a_letter_its_own_words_contradict_is_refused(answer, options):
    assert ms.correct_letter([answer], options) is None


@pytest.mark.parametrize("answer,options,expected", [
    # signs survive the comparison, so -1 names C and not A
    ("C. -1", {"A": "1", "B": "12", "C": "-1", "D": "-12"}, "C"),
    ("B. 10", {"A": "9", "B": "10", "C": "-10", "D": "8"}, "B"),
    # a trailing mark note is not part of the answer
    ("D. (2, -5)    (1)", {"A": "Q (2, 5)", "B": "Q (-2, 5)", "C": "Q (-2, -5)",
                           "D": "Q (2, -5)"}, "D"),
    # "&" and "and" are the same word; a stray trailing header is tolerated
    ("B. Statement I is true & II is false SECTION-B",
     {"A": "Statement I is False and II is True.", "B": "Statement I is True and II is False.",
      "C": "Statement I and II both are True.", "D": "Statement I and II both are False."}, "B"),
    # a matching-question option IS a set of pairs; the letter's words confirm it
    ("B. a-iii, b-iv, c-i, d-ii",
     {"A": "a-i, b-ii, c-iii, d-iv", "B": "a-iii, b-iv, c-i, d-ii",
      "C": "a-ii, b-i, c-iv, d-iii", "D": "a-iv, b-iii, c-ii, d-i"}, "B"),
])
def test_a_letter_its_own_words_confirm_is_recovered(answer, options, expected):
    assert ms.correct_letter([answer], options) == expected


# ---- option text that names a letter (Task 42) ------------------------------

@pytest.mark.parametrize("texts", [
    # SQP Carnatic Music (Melodic Instrument) X 2023-24 Q6: statements A-D
    ("A & B", "A & C", "B & C", "C & D"),
    # SQP Hindustani Music (Vocal) XII 2023-24 Q6: a matching list's rows
    ("A - I, B - II, C - III, D – IV", "A-II, B-I, C-III, D-IV",
     "A-III, B-I, C-IV, D-II", "A-IV, B-I, C-III, D-II"),
    # SQP Informatics Practices XII 2023-24 Q17: an assertion (A)
    ("Both A and R are true", "A is True but R is False", "A is false but R is True"),
])
def test_option_text_that_names_a_letter_is_found(texts):
    assert ms.names_option_letter(dict(zip("ABCD", texts)))


@pytest.mark.parametrize("texts", [
    ("Squirrel", "Tiger", "Swine", "Sheep"),
    ("Kriti", "Tana Varnam", "Adi", "Dhamar"),
    ("Ahead", "Dance", "Bach", "Cadence"),         # A-D inside a word is no label
])
def test_option_text_without_a_letter_is_not_found(texts):
    assert not ms.names_option_letter(dict(zip("ABCD", texts)))
