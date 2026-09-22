"""bank_merge: contract, normalisation, gates, composition."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from academicos.corpus import bank_merge as bm  # noqa: E402

TS = "2026-09-19T00:00:00+00:00"


def board(i=1, **kw):
    rec = {
        "id": f"cbse:q:src:{'a' * 24}:{i}", "questionBankId": "cbse-pilot",
        "subject": "Science", "grade": 10, "chapterIds": [], "competencyIds": [],
        "bloomLevel": "understand", "difficulty": "easy", "type": "short_answer",
        "stem": f"Explain why the sky appears blue during the day, question {i}.",
        "stemLatex": "", "parts": [],
        "answerScheme": {"totalMarks": 2, "markingPoints": [
            {"id": "mp1", "description": "Scattering of light", "marks": 2,
             "keyword": "scattering", "isRequired": True, "synonyms": []}],
            "rubricLevels": [], "commonErrors": [], "alternativeAnswers": [],
            "modelAnswer": "Scattering of light", "modelAnswerLatex": "",
            "provenance": "cbse_marking_scheme"},
        "estimatedTimeMinutes": 4, "marks": 2, "language": "en",
        "source": "cbse_board_paper", "qualityScore": 0.8, "tags": [],
        "createdAt": TS, "updatedAt": TS, "metadata": {},
    }
    rec.update(kw)
    return rec


def cbe_mcq(i=1, answer="B. control", **kw):
    rec = board(i, id=f"cbe:q:English9X{i}", subject="Mathematics", grade=7,
                source="cbse_question_bank", type="mcq", marks=1,
                stem="Which of these is the largest number? Select one option.")
    rec["parts"] = [{"id": f"p{i}", "partNumber": 1, "text": t, "marks": 0,
                     "answerType": "singleChoice", "alternativeAnswers": []}
                    for t in ("A. avoid", "B. control", "C. forget", "D. understand")]
    rec["answerScheme"] = {"totalMarks": 1, "markingPoints": [
        {"id": "mp1", "description": answer, "marks": 1, "keyword": "",
         "isRequired": True, "synonyms": []}],
        "rubricLevels": [], "commonErrors": [], "alternativeAnswers": [],
        "modelAnswer": answer, "modelAnswerLatex": "", "provenance": "cbse_marking_scheme"}
    rec.update(kw)
    return rec


# ---- contract ---------------------------------------------------------------

def test_a_board_record_satisfies_the_contract():
    assert bm.contract_errors(board()) == []


@pytest.mark.parametrize("key", ["competencyIds", "bloomLevel", "stemLatex", "createdAt"])
def test_a_missing_required_field_is_reported(key):
    rec = board()
    del rec[key]
    assert any(key in e for e in bm.contract_errors(rec))


def test_a_part_without_text_latex_is_reported():
    """259 CBE rows failed on the phone for exactly this."""
    rec = cbe_mcq()
    assert any("textLatex" in e for e in bm.contract_errors(rec))


@pytest.mark.parametrize("key,value", [
    ("bloomLevel", "memorise"), ("difficulty", "tricky"),
    ("type", "essay"), ("source", "cbse_textbook"),
])
def test_a_value_the_phone_would_silently_default_is_reported(key, value):
    """The phone maps an unknown source to ncert_textbook -- a provenance mislabel."""
    assert any(key in e for e in bm.contract_errors(board(**{key: value})))


def test_a_boolean_is_not_a_number():
    assert any("marks" in e for e in bm.contract_errors(board(marks=True)))


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
    assert bm.correct_letter([answer], OPTS) == expected


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
    assert bm.correct_letter([answer], OPTS) is None


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
    assert bm.correct_letter([answer], options) is None


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
    assert bm.correct_letter([answer], options) == expected


# ---- normalisation ----------------------------------------------------------

def test_cbe_mcq_becomes_inline_objective_mcq():
    out, reason = bm.normalise(cbe_mcq())
    assert reason is None
    assert out["parts"] == []
    assert "(A) avoid" in out["stem"] and "(D) understand" in out["stem"]
    meta = out["answerScheme"]["metadata"]
    assert meta["objective"] is True and meta["correctOption"] == "B"
    assert bm.contract_errors(out) == []


def test_an_mcq_with_no_recoverable_key_is_refused():
    _, reason = bm.normalise(cbe_mcq(answer="Read the following passage and choose"))
    assert reason == "mcq-answer-unresolved"


def _with_options(rec, texts):
    rec["parts"] = [{**rec["parts"][0], "text": t} for t in texts]
    return rec


@pytest.mark.parametrize("texts", [
    # cbe:q:Maths10AS4 -- a student cannot choose between two options that read alike
    ("A. 34", "B. 34", "C. 35", "D. 35"),
    # cbe:q:Maths7SC4 -- extraction lost the maths; all four read "4 m"
    ("A. 4 𝑚", "B. 4 𝑚", "C. 4 𝑚", "D. 4 𝑚"),
    # an option with no text
    ("A. avoid", "B. control", "C.", "D. understand"),
    # cbe:q:Maths9IM4 -- options C and D were fused into one part
    ("A. -7", "B. −1", "C. D. 7   (1 mark)"),
])
def test_options_a_student_could_not_answer_from_are_refused(texts):
    _, reason = bm.normalise(_with_options(cbe_mcq(answer="B"), texts))
    assert reason == "mcq-options-unresolved"


def test_assertion_reason_options_that_open_with_a_label_are_not_fused():
    """SQP History XII 2025-26 Q10: "(A) is correct but ..." is an option, not a fusion."""
    key = "A. Both (A) and (R) are correct and (R) is the correct explanation of (A)."
    rec = _with_options(cbe_mcq(answer=key), (
        "A. Both (A) and (R) are correct and (R) is the correct explanation of (A).",
        "B. Both (A) and (R) are correct and (R) is not the correct explanation of (A).",
        "C. (A) is correct but (R) is not correct.",
        "D. (R) is correct but (A) is not correct."))
    out, reason = bm.normalise(rec)
    assert reason is None
    assert out["answerScheme"]["metadata"]["correctOption"] == "A"


def sqp_inline(stem_tail="(A) avoid (B) control (C) forget (D) understand",
               answer="(b) control", **kw):
    """The SQP shape: typed short_answer, options written into the stem."""
    rec = board(5, id="cbse:sqp:ClassX_2023_24:Science:5", source="cbse_sample_paper",
                type="short_answer", marks=1,
                stem=f"Which word best completes the sentence below? {stem_tail}")
    rec["answerScheme"]["modelAnswer"] = answer
    rec["answerScheme"]["markingPoints"][0]["description"] = answer
    rec.update(kw)
    return rec


def test_an_inline_mcq_typed_short_answer_is_served_as_an_mcq():
    """97 served SQP rows were 4-option MCQs typed short_answer: no key check, no objective scheme."""
    out, reason = bm.normalise(sqp_inline())
    assert reason is None
    assert out["type"] == "mcq" and out["metadata"]["typeInferred"] is True
    assert out["answerScheme"]["metadata"]["correctOption"] == "B"
    assert bm.contract_errors(out) == []


def test_an_inline_mcq_keeps_its_options_once():
    out, _ = bm.normalise(sqp_inline())
    assert out["stem"].count("(A) avoid") == 1 and out["stem"].count("(D) understand") == 1
    assert out["parts"] == []


def test_an_inline_mcq_clears_its_parts():
    rec = sqp_inline()
    rec["parts"] = [{"id": "p1", "partNumber": 1, "text": "Answer in one word.", "marks": 1,
                     "answerType": "textShort", "alternativeAnswers": []}]
    out, reason = bm.normalise(rec)
    assert reason is None and out["parts"] == []


@pytest.mark.parametrize("stem_tail,answer,reason", [
    # SQP Mathematics (Standard) 2023-24 Q11 -- options A-C lost in extraction
    ("(A) (B) (C) (D) 7", "(d) 7", "mcq-options-unresolved"),
    # SQP Mathematics (Basic, VIC) 2023-24 Q13 -- A and B both read "60∘"
    ("(A) 60∘ (B) 60∘ (C) 90∘ (D) 30∘", "(a) 60∘", "mcq-options-unresolved"),
    # SQP Kathak 2022-23 Q8 -- the key is the next section header
    ("(A) avoid (B) control (C) forget (D) understand", "(b) SECTION-B", "mcq-answer-unresolved"),
])
def test_an_inferred_mcq_goes_through_the_same_gate(stem_tail, answer, reason):
    assert bm.normalise(sqp_inline(stem_tail, answer))[1] == reason


def test_a_multi_mark_item_with_inline_options_is_not_retyped():
    """A 3-mark case study may list (A)-(D); it is not one MCQ."""
    out, reason = bm.normalise(sqp_inline(marks=3))
    assert reason is None and out["type"] == "short_answer"
    assert "typeInferred" not in out["metadata"]


@pytest.mark.parametrize("patch,reason", [
    # cbe:q:Science9DT3 -- a sub-part carrying its group's 8 marks
    ({"marks": 8}, "mcq-marks-implausible"),
    ({"stem": "1(a) Which structure is only present in a eukaryotic cell?"}, "mcq-part-of-group"),
    ({"stem": "1 (a) The female reproductive part of a flower consists of:"}, "mcq-part-of-group"),
])
def test_what_is_not_a_single_mcq_is_refused(patch, reason):
    assert bm.normalise(cbe_mcq(**patch))[1] == reason


def test_a_two_mark_cbe_mcq_is_kept():
    """cbe:q:Maths9SM1 is a real 2-mark MCQ; 71 raw CBE MCQs carry 2 marks."""
    out, reason = bm.normalise(cbe_mcq(marks=2))
    assert reason is None and out["marks"] == 2


def test_fewer_than_three_options_is_refused():
    """cbe:q:Maths9AN6: parts "A. x-axis", "B. y-axis" are two questions, not options."""
    rec = _with_options(cbe_mcq(answer="A. x-axis at (0.5, 0)", marks=1), ("A. x-axis", "B. y-axis"))
    assert bm.normalise(rec)[1] == "mcq-options-unresolved"


def test_when_the_stem_and_the_parts_disagree_the_item_is_refused():
    """SQP History XII 2025-26 Q19: the stem's (A)-(D) are a matching table's columns."""
    rec = cbe_mcq(answer="D. i - d, ii - a, iii - b, iv - c",
                  stem="Match the following. (A) 1917 (B) 1918 (C) 1919 (D) 1915 Please note "
                       "that the assessment scheme of the Academic Session 2024-25 will continue")
    rec = _with_options(rec, ("A. i - b, ii - c, iii - a, iv - d", "B. i - c, ii - a, iii - b, iv - d",
                              "C. i - c, ii - d, iii - b, iv - a", "D. i - d, ii - a, iii - b, iv - c"))
    assert bm.normalise(rec)[1] == "mcq-options-unresolved"


def test_when_the_stem_and_the_parts_agree_the_options_are_not_repeated():
    rec = cbe_mcq(stem="Which of these is the largest? (A) avoid (B) control (C) forget (D) understand")
    out, reason = bm.normalise(rec)
    assert reason is None
    assert out["stem"].count("(B) control") == 1 and out["parts"] == []
    assert out["answerScheme"]["metadata"]["correctOption"] == "B"


def test_page_furniture_is_stripped_from_an_inline_mcq():
    """SQP Engineering Graphics XII 2025-26 Q11: the footer ran into option D, and so into the key."""
    footer = (" *Please note that the assessment scheme of the Academic Session 2024-25 will "
              "continue in the current session i.e. 2025-26.* Page of 13")
    out, reason = bm.normalise(sqp_inline(answer="(d) understand",
                                          stem_tail="(A) avoid (B) control (C) forget (D) understand"
                                          + footer))
    assert reason is None
    assert "Please note" not in out["stem"] and out["stem"].endswith("(D) understand")
    assert out["answerScheme"]["modelAnswer"] == "understand"


def test_a_trailing_section_heading_is_stripped():
    """SQP Geography XII 2022-23 Q17 ran on into the next section's instructions."""
    out, _ = bm.normalise(sqp_inline(stem_tail="(A) avoid (B) control (C) forget (D) understand "
                                               "SECTION B Question numbers 18-23 are SA type questions."))
    assert out["stem"].endswith("(D) understand")


def test_an_option_that_runs_on_into_the_next_section_is_refused():
    """SQP Home Science X 2024-25 Q14: option D was a whole case-study passage."""
    passage = " ".join(["Time and energy are two important resources but these are limited."] * 5)
    rec = sqp_inline(stem_tail=f"(A) avoid (B) control (C) forget (D) understand {passage}",
                     answer="(d) understand")
    assert bm.normalise(rec)[1] == "mcq-options-unresolved"


def test_missing_bloom_is_inferred_and_marked_as_inferred():
    rec = cbe_mcq()
    rec["type"] = "short_answer"
    rec["parts"] = []
    del rec["bloomLevel"]
    out, _ = bm.normalise(rec)
    assert out["bloomLevel"] in bm.BLOOM_LEVELS
    assert out["metadata"]["bloomInferred"] is True


def test_a_passage_is_prepended_to_the_stem():
    rec = cbe_mcq()
    rec["type"] = "short_answer"
    rec["parts"] = []
    rec["metadata"] = {"passage": "Almonds grow in California orchards."}
    out, _ = bm.normalise(rec)
    assert out["stem"].index("Almonds grow") < out["stem"].index("largest number")


def test_normalise_does_not_mutate_its_input():
    rec = cbe_mcq()
    before = copy.deepcopy(rec)
    bm.normalise(rec)
    assert rec == before


# ---- gates ------------------------------------------------------------------

@pytest.mark.parametrize("patch,reason", [
    ({"metadata": {"needsFigure": True, "figureState": "attached"}}, "figure-unavailable"),
    ({"stem": "PART- B has two sections: Section - B1 Supplementary"}, "header-as-stem"),
    ({"stem": "Q5."}, "stem-too-short"),
])
def test_gate(patch, reason):
    rec = board(source="cbse_question_bank", **patch)
    assert bm.exclusion_reason(rec) == reason


def test_cbe_english_without_a_passage_is_excluded():
    rec = board(source="cbse_question_bank", subject="English")
    assert bm.exclusion_reason(rec) == "passage-unavailable"


def test_cbe_english_with_a_passage_is_kept():
    rec = board(source="cbse_question_bank", subject="English",
                metadata={"passage": "A long reading passage."})
    assert bm.exclusion_reason(rec) is None


def test_an_answer_that_is_question_text_is_excluded():
    rec = board(source="cbse_sample_paper")
    rec["answerScheme"]["modelAnswer"] = "Read the following data and select the appropriate option"
    assert bm.exclusion_reason(rec) == "answer-is-question-text"


def test_an_answer_far_longer_than_its_marks_is_excluded():
    rec = board(source="cbse_sample_paper", marks=1)
    rec["answerScheme"]["modelAnswer"] = "x " * 5000
    assert bm.exclusion_reason(rec) == "answer-bleed"


def test_legacy_font_garble_is_excluded():
    """Consecutive Indic vowel signs cannot occur in correctly spelled text."""
    rec = board(source="cbse_sample_paper",
                stem="মনিিোচরোপয "
                     "নিিো নিিো নিিো")
    assert bm.exclusion_reason(rec) == "garbled-script"


@pytest.mark.parametrize("subject,stem", [
    # visarga straight after a vowel sign is correct Hindi: "dukh" (sorrow)
    ("Hindi", "दुःख दुःख दुःख दुःख के कारण"),
    # decomposed Bengali o-kar (U+09C7 U+09BE) is two vowel signs before NFC
    ("Assamese", "কোন কোন কোন কোন প্রশ্ন"),
])
def test_correct_indic_text_is_not_flagged_as_garbled(subject, stem):
    rec = board(source="cbse_sample_paper", subject=subject, stem=stem)
    assert bm.exclusion_reason(rec) is None


def test_garble_in_the_answer_is_excluded():
    rec = board(source="cbse_sample_paper", subject="Hindi", stem="निम्नलिखित प्रश्न का उत्तर दीजिए।")
    rec["answerScheme"]["modelAnswer"] = "মনিিো নিিো " \
                                         "নিিো নিিো"
    assert bm.exclusion_reason(rec) == "garbled-script"


@pytest.mark.parametrize("subject,stem", [
    # SQP Malayalam X 2025-26 Q5, extracted through a legacy font
    ("Malayalam", "X∂ncn°p∂ ]Øv tNmZyßfn¬ GsX¶nepw GsgÆØn\\v icnbpØcw sXcs™SpsØgpXpI."),
    # SQP Odia X 2022-23 Q10
    ("Odia", "Êz bûeZ @bò~û^ @«MðZ Kû~ðýKâcKê _âgõiû Keò iÚû^úd"),
])
def test_a_language_paper_not_in_its_own_script_is_excluded(subject, stem):
    rec = board(source="cbse_sample_paper", subject=subject, stem=stem)
    assert bm.exclusion_reason(rec) == "garbled-script"


def test_indic_code_points_in_a_maths_item_are_excluded():
    """SQP Mathematics (Standard) X 2023-24 Q27: a maths font misread as Oriya."""
    rec = board(source="cbse_sample_paper", subject="Mathematics (Standard)",
                stem="If alpha and beta are zeroes of the polynomial ଶଶଵ, find ହ.")
    assert bm.exclusion_reason(rec) == "garbled-script"


def test_a_music_paper_may_quote_its_script():
    rec = board(source="cbse_sample_paper", subject="Hindustani Music (Vocal)",
                stem="Write the notation of the bandish सा रे ग म in Teentaal.")
    assert bm.exclusion_reason(rec) is None


def test_a_dance_paper_named_after_a_language_is_not_a_language_paper():
    """Manipuri Dance is written in English; reading it as Manipuri excluded all 37 rows."""
    rec = board(source="cbse_sample_paper", subject="Manipuri Dance",
                stem="Name the traditional costume worn by Radha in Ras Leela.")
    assert bm.exclusion_reason(rec) is None


def test_a_general_instructions_block_is_a_header():
    """SQP Mathematics (Standard) X 2023-24 Q8 was served with this as its stem."""
    rec = board(source="cbse_sample_paper",
                stem="Draw neat figures wherever required. Take π =22/7 wherever required.")
    assert bm.exclusion_reason(rec) == "header-as-stem"


@pytest.mark.parametrize("stem", [
    # cbe:q:Maths9NM2
    "Which equation fits the data given in the above table? (A) y = x - 2 (B) y = 2x - 1",
    "The diagram above shows two right-angled triangles. Find the angle ACD.",
    "In the given figure, PQ and PR are tangents to a circle centred at O.",
    "Observe the given map and answer the following questions.",
    "Observing the graph given above, find the coordinates of the orange tree.",
])
def test_a_stem_that_points_at_a_missing_figure_is_excluded(stem):
    rec = board(source="cbse_question_bank", stem=stem)
    assert bm.exclusion_reason(rec) == "figure-referenced"


def test_a_following_table_is_inline_and_kept():
    """A "following table" is extracted after the stem, as text."""
    rec = board(source="cbse_sample_paper",
                stem="Find the mean from the following table. Length 118-126 127-135 Leaves 3 5")
    assert bm.exclusion_reason(rec) is None


# ---- composition ------------------------------------------------------------

def test_board_records_pass_through_unchanged():
    b = board()
    result = bm.compose([copy.deepcopy(b)], [], [])
    assert result.questions == [b]


def test_non_board_rows_already_in_the_served_bank_are_rebuilt_from_source():
    """Idempotency: a second run must not keep the first run's CBE rows."""
    stale = cbe_mcq(9)
    result = bm.compose([board(), stale], [], [])
    assert [q["id"] for q in result.questions] == [board()["id"]]


def test_a_duplicate_of_a_board_question_is_dropped_in_favour_of_the_board():
    b = board(stem="Explain why the sky appears blue during the day, question 1.")
    dup = board(2, id="cbse:sqp:X:Science:1", source="cbse_sample_paper",
                stem=b["stem"])
    result = bm.compose([b], [], [dup])
    assert [q["id"] for q in result.questions] == [b["id"]]
    assert result.excluded[0]["reason"] == "duplicate-stem"


def test_an_id_already_served_is_excluded_as_a_duplicate():
    first = cbe_mcq(1)
    again = cbe_mcq(1, stem="A different question with the same id, asked again here.")
    result = bm.compose([], [first, again], [])
    assert [q["id"] for q in result.questions] == [first["id"]]
    assert [e["reason"] for e in result.excluded] == ["duplicate-id"]


def test_a_board_row_that_breaks_the_contract_fails_the_whole_merge():
    """Board rows pass through untouched, so one that breaks the contract is not repaired."""
    bad = board()
    del bad["competencyIds"]
    with pytest.raises(bm.ContractError) as err:
        bm.compose([bad], [], [])
    assert err.value.record_id == bad["id"]


def test_every_exclusion_is_recorded_with_its_reason():
    fig = board(3, id="cbe:q:F1", source="cbse_question_bank",
                metadata={"needsFigure": True})
    result = bm.compose([], [fig], [])
    assert result.questions == []
    assert result.excluded == [{"id": "cbe:q:F1", "source": "cbse_question_bank",
                                "reason": "figure-unavailable", "subject": "Science",
                                "grade": 10, "stem": fig["stem"][:200]}]


def test_a_contract_violation_after_normalising_fails_the_whole_merge(monkeypatch):
    monkeypatch.setattr(bm, "normalise", lambda rec: ({"id": rec["id"]}, None))
    with pytest.raises(bm.ContractError):
        bm.compose([], [board(4, id="cbe:q:Z", source="cbse_question_bank")], [])
