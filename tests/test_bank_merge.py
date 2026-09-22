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
            # The relink's stamp of the official row it verified: without it
            # the merge takes the label for a pre-Task-15 one.
            "metadata": {"schemeCode": "31/1/1", "schemeQNo": i},
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


# Real 1-mark SQP stems whose (A)-(D) labels do not parse as exactly A,B,C,D
# once each. They stayed short_answer and were served with keys nobody
# checked; the first key below answers only the first of two fused questions.
_REPEATED_BLOCKS = (
    # SQP Mathematics (Standard) X 2025-26 Q18: a tangent MCQ fused with the
    # assertion-reason directions that follow it -- A-D appear twice.
    "The length of a tangent drawn to a circle of radius 9 cm from a point at a distance of "
    "41cm from the centre of the circle is (A) 40cm (B) 9cm (C) 41cm (D) 50cm DIRECTIONS: In "
    "the question number 19 and 20, a statement of Assertion (A) is followed by a statement of "
    "Reason (R). Choose the correct option: (A) Both assertion (A) and reason (R) are true and "
    "reason (R) is the correct explanation of assertion (A) (B) Both assertion (A) and reason "
    "(R) are true and reason (R) is not the explanation of assertion (A) (C) Assertion (A) is "
    "true but reason (R) is false. (D) Assertion (A) is false but reason (R) is true.")
_ASSERTION_REASON = (
    # SQP Home Science X 2024-25 Q17: "Assertion (A)" puts an A label before the options.
    "Given below are two statements labeled as Assertion (A) and Reason (R) ASSERTION (A): "
    "Energy management is a strategy which helps to utilize energy (CBQ) to maximum. REASON "
    "(R): Energy management helps in doing productive work in more time. Select the most "
    "appropriate answer from the options given below: (A) Both A and R are true and R is the "
    "correct explanation of A. (B) Both A and R are true but R is not the correct explanation "
    "of A. (C) A is true but R is false. (D) A is false but R is true.")


@pytest.mark.parametrize("stem,answer", [
    (_REPEATED_BLOCKS, "(A) 40cm Since, tangent is perpendicular to the radius at the point of "
                       "contact In ∆OPT, right angled at T OP2=OT2+TP2 412=92+TP2 TP=40cm"),
    (_ASSERTION_REASON, "(C) A is true but R is false."),
])
def test_an_mcq_whose_labels_do_not_parse_is_still_gated_as_an_mcq(stem, answer):
    """21 served 1-mark SQP rows carried all four (A)-(D) labels, repeated or out of
    order, and skipped the MCQ gate as short_answer."""
    rec = sqp_inline(answer=answer, stem=stem)
    out, reason = bm.normalise(rec)
    assert reason == "mcq-options-unresolved"
    assert out["type"] == "mcq" and out["metadata"]["typeInferred"] is True


def test_a_one_mark_item_missing_an_option_label_is_not_retyped():
    """Only the full A-D set marks an MCQ: "Assertion (A) ... Reason (R)" alone is not one."""
    out, reason = bm.normalise(sqp_inline(stem_tail="Assertion (A) and Reason (R) (B) are named."))
    assert reason is None and out["type"] == "short_answer"


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


def test_a_parenthesised_section_heading_is_stripped_from_the_stem():
    """SQP Home Science X 2024-25 Q18 ends "... (D) A is false but R is true. SECTION C
    (SHORT ANSWER QUESTIONS)"; the parenthesis kept the heading from being stripped."""
    out, _ = bm.normalise(sqp_inline(stem_tail="(A) avoid (B) control (C) forget (D) understand "
                                               "SECTION C (SHORT ANSWER QUESTIONS)"))
    assert out["stem"].endswith("(D) understand")


def test_page_furniture_is_stripped_from_a_served_answer():
    """Keys carry the headings too: a teacher reading the model answer of a
    non-MCQ row must not see the next section's title or the page footer."""
    footer = (" *Please note that the assessment scheme of the Academic Session 2024-25 will "
              "continue in the current session i.e. 2025-26.* Page of 13")
    rec = board(7, id="cbse:sqp:ClassX_2024_25:Home Science:20", source="cbse_sample_paper",
                stem="Explain two ways in which energy can be managed at home.")
    heading = " SECTION C (SHORT ANSWER QUESTION)"
    rec["answerScheme"]["modelAnswer"] = "Plan the work and use labour saving devices." + heading
    rec["answerScheme"]["markingPoints"][0]["description"] = "Plan the work." + footer
    out, reason = bm.normalise(rec)
    assert reason is None and out["type"] == "short_answer"
    assert out["answerScheme"]["modelAnswer"] == "Plan the work and use labour saving devices."
    assert out["answerScheme"]["markingPoints"][0]["description"] == "Plan the work."


@pytest.mark.parametrize("text,expected", [
    # "(A)" after a heading is an option, not the heading's title: a heading
    # inside the text is left for `_INNER_SECTION`, a leading one goes alone
    ("Pick one. SECTION A (A) avoid (B) control", "Pick one. SECTION A (A) avoid (B) control"),
    ("SECTION A (A) avoid (B) control", "(A) avoid (B) control"),
    # SQP Mathematics (Standard) X 2025-26 Q31: mixed case, in brackets, after a page number
    ("Find their present ages. Page of 8 (Section – D) Section D consists of 4 questions",
     "Find their present ages."),
    # SQP Tangkhul XII 2025-26 Q9
    ("Khili morphophonemics hokhala? Page of 7 SECTION D (Literature)",
     "Khili morphophonemics hokhala?"),
    # prose that names a section is not a heading
    ("Explain Section 39 of the Companies Act.", "Explain Section 39 of the Companies Act."),
])
def test_furniture_is_stripped_and_content_is_kept(text, expected):
    assert bm._strip_furniture(text) == expected


def test_a_stem_that_runs_across_a_section_break_is_excluded():
    """SQP Political Science XII 2023-24 Q4 (6 marks) ran on into Section E and was
    served with a key from another question entirely."""
    rec = board(8, id="cbse:sqp:ClassXII_2023_24:Political Science:4", source="cbse_sample_paper",
                marks=6, stem="4) Why did the Janata party fail to remain in power for a full "
                              "term? SECTION-E (24 MARKS) 27 2+2+2 Explain the factors that make "
                              "European Union a highly influential =6 regional organisation. "
                              "28 'Reforming the UN means restructuring of the Security "
                              "Council'. Justify (CB) this statement with suitable arguments.")
    assert bm.normalise(rec)[1] == "stem-spans-sections"


@pytest.mark.parametrize("answer,reason", [
    # SQP Hindustani Music (Percussion) X 2024-25 Q8: the whole key is the next heading
    ("SECTION-B", "no-answer"),
    # SQP Hindustani Music (Vocal) XII 2023-24 Q8: the key runs on into Section B
    ("3. SECTION-B Brief explanation and types of Kan, Gamak, Murchhana, Khatka", "answer-bleed"),
])
def test_a_key_that_is_or_crosses_a_section_heading_is_excluded(answer, reason):
    _check_key(answer, reason)


@pytest.mark.parametrize("answer,kept", [
    # SQP Applied Mathematics XII 2022-23 Q25: the next section's instructions
    ("= 25% Section – C Each question carries 3-mark weightage", "= 25%"),
    # SQP Geography XII 2022-23 Q23
    ("for e-commerce and carrying out money transactions SECTION C Question numbers 24 to 28 "
     "are Long Answer based questions.", "for e-commerce and carrying out money transactions"),
])
def test_a_key_ending_in_its_next_sections_instructions_is_kept(answer, kept):
    out, reason = _check_key(answer, None)
    assert out["answerScheme"]["modelAnswer"] == kept


def _check_key(answer, reason):
    rec = board(9, id="cbse:sqp:ClassX_2024_25:Hindustani Music (Percussion):8",
                source="cbse_sample_paper", stem="Name the ten pranas of tala and describe two.")
    rec["answerScheme"]["modelAnswer"] = answer
    rec["answerScheme"]["markingPoints"][0]["description"] = answer
    out, got = bm.normalise(rec)
    assert got == reason
    return out, got


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


# ---- stems after their furniture is stripped (Task 41) ------------------------

def _raw_sqp(paper, subject, q, *, stem, answer, marks, grade, page, chapter_ids=(),
             family=None, meta_extra=None):
    """A raw cbse-sqp record, field for field as academicos-data/corpus/cbse-sqp/
    questions.json carries it (checked equal to the three real rows below)."""
    rid = f"cbse:sqp:{paper}:{subject}:{q}"
    doc = f"cbse-sqp:{paper}:{subject}"
    return {
        "id": rid, "questionBankId": doc, "subject": subject, "grade": grade,
        "chapterIds": list(chapter_ids), "topic": "", "difficulty": "medium",
        "type": "short_answer", "stem": stem, "stemLatex": "", "parts": [],
        "answerScheme": {
            "totalMarks": marks,
            "markingPoints": [{"id": f"{rid}:mp1", "description": answer, "marks": marks,
                               "keyword": "", "isRequired": True, "synonyms": []}],
            "rubricLevels": [], "commonErrors": [], "alternativeAnswers": [],
            "modelAnswer": answer, "modelAnswerLatex": "", "hasPartialCredit": True,
            "metadata": {}, "provenance": "cbse_marking_scheme", "sourcePaperCode": "",
            "sourceDocumentId": doc},
        "estimatedTimeMinutes": marks * 2, "marks": marks, "language": "en",
        "source": "cbse_sample_paper", "qualityScore": 0.95,
        "tags": ["cbse", "sample-paper", paper],
        "createdAt": "2026-09-18T00:00:00Z", "updatedAt": "2026-09-18T00:00:00Z",
        "metadata": {"questionKey": str(q), "alternativeOf": None, "options": 0,
                     "joinedFrom": "sqp+ms-pair", "subjectFamily": family or subject,
                     **(meta_extra or {})},
        "diagramAssetId": None, "mapAssetId": None, "graphAssetId": None, "tableAssetId": None,
        "rights": {"origin": "CBSE", "redistribution": "unknown", "basis": "",
                   "attribution": "Central Board of Secondary Education, sample question paper "
                                  "and marking scheme"},
        "provenance": {"sourceDocumentId": doc, "pageNumber": page, "boundingBox": None,
                       "method": "pdf_native", "confidence": 0.95},
        "calibration": {"measured": False, "sampleSize": 0, "facility": None,
                        "discrimination": None, "basis": "assigned"},
        "version": 1, "reviewState": "published", "supersededBy": None,
    }


def computer_applications_19():
    """Served at c45acef with stem '' -- the leading heading took the whole question."""
    return _raw_sqp(
        "ClassX_2024_25", "Computer Applications", 19, grade=10, marks=2, page=4,
        stem="Section – C Page of 7 The following HTML statements are not written properly. "
             "Re-write the correct",
        answer="SMS MMS 1 mark for each correct difference. Short Message Service Multimedia "
               "message Service. One can send only It allows one to send Images, plain text. "
               "Videos, Audio, GIF’s, PDF’s and Text. SECTION C")


def geography_23():
    """Served at c45acef: a stem that starts mid-sentence, with another question's key."""
    key = ("1. The Internet is the most effective and advanced personal communication system "
           "in India. 2. Enables the user to establish direct access to the word of knowledge "
           "and information. 3. It's like a huge central warehouse of data with detailed "
           "information on various topics. 4. Provides information on low cost 5. Its being "
           "used increasingly for e-commerce and carrying out money transactions SECTION C "
           "Question numbers 24 to 28 are Long Answer based questions.")
    return _raw_sqp(
        "ClassXII_2022_23", "Geography", 23, grade=12, marks=3, page=12,
        chapter_ids=["transport-communication"],
        meta_extra={"chapterTag": {"chapterId": "transport-communication", "score": 0.3365,
                                   "method": "embedding_chapter_v1", "inferred": True}},
        stem="advanced personal communication system in India. SECTION C Question numbers 24 "
             "to 28 are Long Answer based questions.",
        answer=key)


def kathakali_5():
    """Served at c45acef as short_answer: lowercase a)-d) options, key never checked."""
    return _raw_sqp(
        "ClassXII_2025_26", "Kathakali", 5, grade=12, marks=1, page=1, family="Dance",
        stem="How many styles are there in Kathakali? a) 1 b) 3 c) 4 d) 2 *Please note that "
             "the assessment scheme of the Academic Session 2024-25 will continue in the "
             "current session i.e. 2025-26.",
        answer="3")


def computer_applications_20():
    """The row after Q19: it opens with the end of Q19's sentence."""
    return _raw_sqp(
        "ClassX_2024_25", "Computer Applications", 20, grade=10, marks=3, page=5,
        stem="statements with underlined corrections. The desired purpose of each statement is "
             "mentioned under it. I. <BODY color=\"red\"> <!--Page background color should be "
             "red--> II. <FONT type=\"arial\"> <!--Type of Font should be Arial--> III. <img "
             "source=\"img_girl.jpg\" size=\"500\" height=\"600\"> <!—Image source should be "
             "img_girl.jpg, width and height both should be 500--> Consider the URL: "
             "https://www.cbse.gov.in and answer the following questions: 3",
        answer="The correct code is 1 mark for each correction. I) <BODY bgcolor = \"red\" > "
               "II) <FONT face=arial> III) <img src=\"img_girl.jpg\" width=\"500\" "
               "height=\"600\"> Page of 5")


def test_a_heading_at_the_start_of_a_stem_is_stripped_alone():
    out, _ = bm.normalise(computer_applications_19())
    assert out["stem"] == ("The following HTML statements are not written properly. "
                           "Re-write the correct")


def test_a_stem_whose_next_question_is_a_fragment_is_excluded():
    """Q19 breaks off mid-sentence -- Q20 holds the rest -- and its key ("SMS MMS ...")
    answers another question. Served, it looked like a real question."""
    result = bm.compose([], [], [computer_applications_19(), computer_applications_20()])
    assert result.questions == []
    assert {e["id"].rsplit(":", 1)[1]: e["reason"] for e in result.excluded} == {
        "19": "stem-runs-on", "20": "stem-fragment"}


def test_a_stem_whose_next_question_opens_with_its_options_is_excluded():
    """SQP Carnatic Music (Percussion) X 2022-23: Q3's stem ends with Q4's question
    ("The left side of the mridangam is known as"); Q4 kept only the options."""
    q3 = _raw_sqp("ClassX_2022_23", "Carnatic Music (Percussion)", 3, grade=10, marks=1,
                  page=1, stem="The number of aksharas in Druva tala a. 9 b. 11 c. 13 d. 15 "
                               "The left side of the mridangam is known as", answer="b. 11")
    q4 = _raw_sqp("ClassX_2022_23", "Carnatic Music (Percussion)", 4, grade=10, marks=1,
                  page=1, stem="a. Chappu b. Toppi c. Choru d. Varu", answer="B")
    result = bm.compose([], [], [q3, q4])
    assert result.questions == []
    assert [e["reason"] for e in result.excluded] == ["stem-runs-on", "stem-fragment"]


def test_a_stem_whose_next_question_is_whole_is_served():
    q20 = computer_applications_20()
    q20["stem"] = "Rewrite these HTML statements with their corrections underlined."
    result = bm.compose([], [], [computer_applications_19(), q20])
    assert [q["id"].rsplit(":", 1)[1] for q in result.questions] == ["19", "20"]


def test_a_fragment_in_another_paper_does_not_exclude_a_stem():
    q20 = computer_applications_20()
    q20["questionBankId"] = "cbse-sqp:ClassX_2023_24:Computer Applications"
    result = bm.compose([], [], [computer_applications_19(), q20])
    assert [q["id"].rsplit(":", 1)[1] for q in result.questions] == ["19"]


def test_a_leading_heading_is_stripped_without_the_text_after_it():
    assert bm._strip_furniture("Section – C Page of 7 Name two protocols used for email.") \
        == "Name two protocols used for email."


@pytest.mark.parametrize("stem", [
    "Section – C Page of 7",
    "SECTION C (SHORT ANSWER QUESTIONS)",
    "*Please note that the assessment scheme of the Academic Session 2024-25 will continue "
    "in the current session i.e. 2025-26.* Page of 13",
    # a heading and its section's instructions: no question after them
    "SECTION B This section consists of 6 questions of 2 marks each.",
    "Section – B Each question carries 2-mark weightage",
    "SECTION C Question numbers 24 to 28 are Long Answer based questions.",
])
def test_a_stem_that_is_all_furniture_is_excluded(stem):
    rec = computer_applications_19()
    rec["stem"] = stem
    assert bm.exclusion_reason(rec) is None      # the raw stem passes the pre-strip gates
    assert bm.normalise(rec)[1] == "stem-empty-after-strip"


def test_a_stem_gutted_by_its_strip_is_excluded_from_the_bank():
    rec = computer_applications_19()
    rec["stem"] = "Section – C Page of 7"
    result = bm.compose([], [], [rec])
    assert result.questions == []
    assert [e["reason"] for e in result.excluded] == ["stem-empty-after-strip"]


@pytest.mark.parametrize("tail", [
    "a. avoid b. control c. forget d. understand",
    "a) avoid b) control c) forget d) understand",
    "(a) avoid (b) control (c) forget (d) understand",
    "A. avoid B. control C. forget D. understand",
    "A) avoid B) control C) forget D) understand",
    "a. avoid b. control c. forget",               # three labels are enough
])
def test_every_option_label_style_makes_an_mcq(tail):
    out, reason = bm.normalise(sqp_inline(stem_tail=tail, answer="(b) control"))
    assert reason is None
    assert out["type"] == "mcq" and out["metadata"]["typeInferred"] is True
    assert out["answerScheme"]["metadata"]["correctOption"] == "B"
    assert out["stem"].count("control") == 1


def test_a_lowercase_option_mcq_goes_through_the_key_check():
    """Kathakali XII 2025-26 Q5: the key "3" is option b)'s text or option 3 of a
    numbered list; correct_letter refuses a bare numeral, so the row is not served."""
    out, reason = bm.normalise(kathakali_5())
    assert out["type"] == "mcq"
    assert reason == "mcq-answer-unresolved"


def test_a_lettered_list_in_the_stem_of_an_mcq_with_option_parts_is_not_its_options():
    """SQP Hindustani Music (Vocal) XII 2025-26 Q6: "a. Kan swar i. ..." are a
    matching list's rows; the parts are the options, and the item is served."""
    rec = cbe_mcq(stem="Match List I with List II. a. Kan swar b. Meend c. Gamak d. Khatka")
    out, reason = bm.normalise(rec)
    assert reason is None
    assert out["answerScheme"]["metadata"]["correctOption"] == "B"


def test_two_lowercase_labels_are_not_an_mcq():
    out, reason = bm.normalise(sqp_inline(stem_tail="a) avoid b) control", answer="control"))
    assert reason is None and out["type"] == "short_answer"


def test_a_stem_that_starts_mid_sentence_is_excluded():
    assert bm.normalise(geography_23())[1] == "stem-fragment"


@pytest.mark.parametrize("stem", [
    # cbe:q:Maths10RK2 -- the first letter of "If" was lost
    "f the lines 3x+2ky – 2 = 0 and 2x+5y+1 = 0 are parallel, then the value of k is",
    # SQP Computer Applications X 2024-25 Q16
    "an internet site having URL as: www.children.com/india/~abc.html Now you want to create "
    "a link to this web page.",
])
def test_a_lowercase_opening_that_is_not_a_label_is_a_fragment(stem):
    rec = geography_23()
    rec["stem"] = stem
    assert bm.normalise(rec)[1] == "stem-fragment"


def test_an_mcq_whose_stem_opens_with_its_options_is_a_fragment():
    """SQP Carnatic Music (Percussion) X 2022-23 Q4: the question was lost, only the
    options and a key "B" survive."""
    rec = kathakali_5()
    rec["stem"] = "a. Chappu b. Toppi c. Choru d. Varu"
    rec["answerScheme"]["modelAnswer"] = "B"
    rec["answerScheme"]["markingPoints"][0]["description"] = "B"
    assert bm.normalise(rec)[1] == "stem-fragment"


@pytest.mark.parametrize("stem", [
    # SQP Carnatic Music (Percussion) X 2022-23 Q9: roman-numeral sub-parts
    "i. Explain the word Tattakaaram ii. Enumerate the Shodasanga with Aksharakala",
    # SQP Sociology XII 2022-23 Q37: lettered sub-questions on a multi-mark item
    "a) Give reasons for declining sex-ratio. b) In your opinion, what steps should be taken?",
    # SQP French X 2022-23 Q6: a part label without its full stop
    "a Trouvez la question. a. Les sandwiches au fromage sont faciles à préparer.",
])
def test_a_stem_that_opens_with_a_part_label_is_not_a_fragment(stem):
    rec = geography_23()
    rec["stem"] = stem
    assert bm.normalise(rec)[1] != "stem-fragment"


# ---- a 1-mark item that holds its group's parts (Task 41 review) -------------

def cbe_group(stem, marks=1, **kw):
    """The CBE shape of cbe:q:Maths9RS7: one item per numbered group, each part
    printed "1 (a)", "1 (b)" -- here under one part's mark, with one part's key."""
    rec = board(7, id="cbe:q:Maths9RS7", subject="Mathematics", grade=9,
                source="cbse_question_bank", type="very_short_answer", marks=marks, stem=stem)
    answer = ("Range = Highest observation – lowest observation = 4.0 – 2.1 = 1.9 kg A1 For "
              "correct answer 1 (b) How many babies weigh below 3.0 kg (1 mark)")
    rec["answerScheme"]["modelAnswer"] = answer
    rec["answerScheme"]["markingPoints"][0]["description"] = answer
    rec.update(kw)
    return rec


@pytest.mark.parametrize("stem", [
    # cbe:q:Maths9RS7: labels first, questions after
    "1 (a) 1 (b) 1 (c) The weights of new born babies in kg are recorded by a hospital. "
    "Find the range of the data. How many babies weigh below 3.0 kg. What is the mean weight.",
    # cbe:q:Maths7SC6: a lead-in, then each part under its label
    "1 Read the graph and answer the following questions. 1 (a) Which is the favourite colour "
    "of most students? 1 (b) Find the ratio of the number of students. 1 (c) What percentage "
    "of all 30 students represents students whose favourite colour is red?",
    # cbe:q:Maths6MG4: two parts, no MCQ shape at all
    "A boy is walking around a rectangular garden of length a metres. 1 (a) What is the "
    "perimeter of the garden? 1 (b) If the breadth b is 5 metres how long does he walk?",
])
def test_a_one_mark_item_holding_its_groups_parts_is_excluded_as_one(stem):
    """Not an MCQ: its (a)-(c) are parts, so an MCQ reason would misreport it."""
    out, reason = bm.normalise(cbe_group(stem))
    assert reason == "stem-holds-group"
    assert out["type"] != "mcq"


def test_a_multi_mark_item_with_numbered_parts_is_kept():
    """cbe:q:Maths9RS6 (5 marks) and its kind are served with their parts."""
    stem = ("1 (a) 1 (b) Two brothers Ashish and Amit wanted to start a business together. "
            "Find each share. Find the ratio of their shares.")
    assert bm.normalise(cbe_group(stem, marks=5))[1] is None


def test_numeric_options_are_not_numbered_parts():
    """SQP Kathak XII 2022-23 Q7: "(a)8 (b)6 (c)12 (d)4" -- the digits are option text."""
    out, reason = bm.normalise(sqp_inline(stem_tail="(a)8 (b)6 (c)12 (d)4", answer="(a) 8"))
    assert reason is None and out["type"] == "mcq"


# ---- options-first, half-question stems, roman and numeric options (Task 41 review 2) --

def painting_xii_3():
    """Served at fa8b78b: the question text is gone, the stem is its options and
    the next question's opening, and the key is a bare label."""
    return _raw_sqp(
        "ClassXII_2023_24", "Painting", 3, grade=12, marks=1, page=2,
        stem="i. Tribal Paintings ii. Company Paintings iii. Bengal School of Painting iv. "
             "Miniature Paintings The painting ‘Nand, Yashoda, and Krishna with kinsmen "
             "going to",
        answer="(iv)")


def carnatic_percussion_x(q):
    """SQP Carnatic Music (Percussion) X 2022-23 Q12-13: part i of Q13 sits at the end
    of Q12's stem, and Q13 was served as its part ii alone."""
    if q == 12:
        return _raw_sqp(
            "ClassX_2022_23", "Carnatic Music (Percussion)", 12, grade=10, marks=2, page=2,
            family="Carnatic Music",
            stem="i. Explain the differences of Left and right side of Mridangam ii. The "
                 "difference of Shadanga and Shodasanga i. Explain the following terms: Choru, "
                 "Varu and Toppi",
            answer="i. Candidates need to explain the different application of left and right "
                   "head of mridangam in performance. ii. Candidate expected to brief about the "
                   "details in both Shadanga and 2 Shodasanga.")
    return _raw_sqp(
        "ClassX_2022_23", "Carnatic Music (Percussion)", 13, grade=10, marks=2, page=2,
        family="Carnatic Music",
        stem="ii. Explain the following term: Tattu, Meetu and Gumki SECTION – C",
        answer="i. Define the term Choru, Varu and Toppi briefly ii. Candidate need to define "
               "the terms briefly. 2 Section – C")


def test_a_one_mark_stem_that_opens_with_roman_options_is_a_fragment():
    assert bm.normalise(painting_xii_3())[1] == "stem-fragment"
    result = bm.compose([], [], [painting_xii_3()])
    assert result.questions == []
    assert [e["reason"] for e in result.excluded] == ["stem-fragment"]


@pytest.mark.parametrize("stem", [
    "1. Tribal Paintings 2. Company Paintings 3. Bengal School 4. Miniature Paintings",
    "a] Tribal Paintings b] Company Paintings c] Bengal School d] Miniature Paintings",
    "(i) Tribal Paintings (ii) Company Paintings (iii) Bengal School (iv) Miniature Paintings",
])
def test_a_one_mark_stem_that_opens_with_options_in_any_style_is_a_fragment(stem):
    rec = painting_xii_3()
    rec["stem"] = stem
    assert bm.normalise(rec)[1] == "stem-fragment"


def test_a_multi_mark_stem_that_opens_with_its_sub_parts_is_a_question():
    """Three labelled parts under 3 marks are the question's parts, not options."""
    rec = painting_xii_3()
    rec["marks"] = rec["answerScheme"]["totalMarks"] = 3
    rec["stem"] = ("i. Define tempera. ii. Name one binder used in it. iii. Explain why it "
                   "dries quickly.")
    assert bm.normalise(rec)[1] is None


@pytest.mark.parametrize("tail,answer", [
    ("i. avoid ii. control iii. forget iv. understand", "(ii)"),
    ("i) avoid ii) control iii) forget iv) understand", "ii"),
    ("(i) avoid (ii) control (iii) forget (iv) understand", "ii. control"),
    ("1. avoid 2. control 3. forget 4. understand", "2."),
    ("1) avoid 2) control 3) forget 4) understand", "2"),
    ("a] avoid b] control c] forget d] understand", "b"),
    ("i. avoid ii. control iii. forget", "(ii)"),             # three labels are enough
])
def test_roman_numeric_and_bracket_options_make_an_mcq(tail, answer):
    out, reason = bm.normalise(sqp_inline(stem_tail=tail, answer=answer))
    assert reason is None
    assert out["type"] == "mcq" and out["metadata"]["typeInferred"] is True
    assert out["answerScheme"]["metadata"]["correctOption"] == "B"
    assert out["stem"].count("control") == 1


def test_roman_and_numeric_options_are_printed_with_the_letters_the_key_uses():
    """The phone reads a student's answer as a letter; "iii" never matches "C"."""
    out, _ = bm.normalise(sqp_inline(stem_tail="i. avoid ii. control iii. forget iv. understand",
                                     answer="(ii)"))
    assert out["stem"] == ("Which word best completes the sentence below? "
                           "(A) avoid (B) control (C) forget (D) understand")


def test_a_real_roman_option_mcq_is_served_with_its_letter():
    """SQP Painting X 2023-24 Q6, served at fa8b78b as short_answer keyed "(iii)"."""
    rec = _raw_sqp("ClassX_2023_24", "Painting", 6, grade=10, marks=1, page=2,
                   stem="Hog brushes are made from which animal hair? i. Squirrel ii. Tiger "
                        "iii. Swine iv. Sheep", answer="(iii)")
    out, reason = bm.normalise(rec)
    assert reason is None and out["type"] == "mcq"
    assert out["answerScheme"]["metadata"]["correctOption"] == "C"
    assert "(C) Swine" in out["stem"]


def test_a_real_bracket_option_mcq_is_served_with_its_letter():
    """SQP Bharatanatyam XII 2022-23 Q7, served at fa8b78b as short_answer keyed "b"."""
    rec = _raw_sqp("ClassXII_2022_23", "Bharatanatyam", 7, grade=12, marks=1, page=2,
                   family="Dance",
                   stem="Dandiya Raas is the folk dance of a] Rajasthan b] Gujarat c] Madhya "
                        "Pradesh d] Maharashtra", answer="b")
    out, reason = bm.normalise(rec)
    assert reason is None and out["type"] == "mcq"
    assert out["answerScheme"]["metadata"]["correctOption"] == "B"


def test_questions_fused_under_numbered_options_are_refused_as_an_mcq():
    """SQP Kathak XII 2024-25 Q4: the tail of Q1 and three numbered MCQs in one stem,
    keyed "2."; served at fa8b78b as short_answer."""
    rec = _raw_sqp("ClassXII_2024_25", "Kathak", 4, grade=12, marks=1, page=1, family="Dance",
                   stem="Satvik 2. How many types of rasas are there? 1. 7 2. 8 3. 9 4. 11 3. "
                        "Speed of time spend in music is called-: 1. Taal 2. Laya 3. Matra 4. "
                        "Vibhaag 4. Choose the name of classical dance of north india. 1. "
                        "Kathakali 2. Kathak 3. Satriya 4. Mohiniattam", answer="2.")
    out, reason = bm.normalise(rec)
    assert out["type"] == "mcq"
    assert reason is not None


@pytest.mark.parametrize("answer", [
    "3",               # option 3, or the option whose text is "3"
    "3. 4.",           # two labels (SQP Kathak XII 2024-25 Q5)
    "C",               # a letter where the options are numbered
    "3. SECTION-B",    # the key ran into the next heading (SQP Odissi XII 2024-25 Q8)
])
def test_an_unclear_numbered_key_is_refused(answer):
    out, reason = bm.normalise(sqp_inline(stem_tail="1. 7 2. 8 3. 3 4. 11", answer=answer))
    assert out["type"] == "mcq"
    assert reason == "mcq-answer-unresolved"


def test_a_stem_that_opens_with_a_later_part_is_a_fragment():
    assert bm.normalise(carnatic_percussion_x(13))[1] == "stem-fragment"


def test_the_stem_holding_the_lost_first_part_runs_on():
    result = bm.compose([], [], [carnatic_percussion_x(12), carnatic_percussion_x(13)])
    assert result.questions == []
    assert {e["id"].rsplit(":", 1)[1]: e["reason"] for e in result.excluded} == {
        "12": "stem-runs-on", "13": "stem-fragment"}


@pytest.mark.parametrize("stem", [
    "b) Give two reasons for the decline in the sex ratio.",
    "(b) Give two reasons for the decline in the sex ratio.",
    "B. Give two reasons for the decline in the sex ratio.",
    "iii. Give two reasons for the decline in the sex ratio.",
])
def test_any_later_part_label_opening_is_a_fragment(stem):
    rec = geography_23()
    rec["stem"] = stem
    assert bm.normalise(rec)[1] == "stem-fragment"


def test_an_initial_is_not_a_part_label():
    rec = geography_23()
    rec["stem"] = "B. R. Ambedkar chaired the drafting committee. Name its other members."
    assert bm.normalise(rec)[1] != "stem-fragment"


@pytest.mark.parametrize("stem,answer", [
    # SQP Applied Mathematics XII 2022-23 Q14: a two-column option grid read by column
    ("An investment of 10,000 becomes 60,000 in 4 years, then the CAGR is given by - 4 4 "
     "c) [6 4 -1] x 100 d) [6 4 + 1] x 100 a) b) 100 100", "(C) option"),
    # SQP Mathematics (Standard) X 2024-25 Q15: "C )" as extraction spaced it
    ("The point on the x- axis nearest to the point (-4,-5) is A) (0, 0) B) (-4, 0) "
     "C ) (-5, 0) D) (41, 0)", "B) (-4, 0)"),
])
def test_options_whose_labels_extraction_disordered_are_still_an_mcq(stem, answer):
    """Served at fa8b78b as short_answer: the labels are there, out of order or spaced."""
    out, reason = bm.normalise(sqp_inline(stem=stem, answer=answer))
    assert out["type"] == "mcq"
    assert reason == "mcq-options-unresolved"


# ---- options whose text names the letters they would be printed with (Task 42) --

def carnatic_melodic_x_6():
    """Served at 7b3aae4 as "(A) A & B (B) A & C (C) B & C (D) C & D": its statements
    are labelled A-D, and the paper numbered the options to keep the two apart."""
    return _raw_sqp(
        "ClassX_2023_24", "Carnatic Music (Melodic Instrument)", 6, grade=10, marks=1,
        page=2, family="Carnatic Music",
        stem="Choose the correct statement. * A – Sriranjini is a Shadava raga B – Varnam can "
             "be played in several speeds C – Geetam have several sangatis D – 72 mela karta "
             "scheme is introduced by Tyagaraja. Choose the correct option 1. A & B 2. A & C "
             "3. B & C 4. C & D",
        answer="1.")


def hindustani_vocal_xii_6():
    """Served at 7b3aae4 as "(A) A - I, B - II, ...": a matching list's rows are A-D."""
    return _raw_sqp(
        "ClassXII_2023_24", "Hindustani Music (Vocal)", 6, grade=12, marks=1, page=2,
        family="Hindustani Music",
        stem="Match List I with List II List I List II Sangeet Parijat I. 14 matras Dhamar II. "
             "Saptadhyayi Jhaptala III. Pt. Ahobal Sangeet Ratnakar IV. 10 matras Choose the "
             "correct answer from the options given below: 1. A - I, B - II, C - III, D – IV "
             "2. A-II, B-I, C-III, D-IV 3. A-III, B-I, C-IV, D-II 4. A-IV, B-I, C-III, D-II",
        answer="3.")


@pytest.mark.parametrize("make", [carnatic_melodic_x_6, hindustani_vocal_xii_6])
def test_numbered_options_that_name_letters_are_not_relabelled(make):
    """The phone and evaluate.py score an MCQ by the A-D letters in the answer, so the
    options cannot keep their 1-4 labels; relabelled, "(C) B & C" is ambiguous."""
    out, reason = bm.normalise(make())
    assert out["type"] == "mcq"
    assert reason == "option-labels-collide"
    result = bm.compose([], [], [make()])
    assert result.questions == []
    assert [e["reason"] for e in result.excluded] == ["option-labels-collide"]


def test_numbered_options_that_name_no_letter_are_still_relabelled():
    out, reason = bm.normalise(sqp_inline(stem_tail="1. avoid 2. control 3. forget 4. understand",
                                          answer="2."))
    assert reason is None
    assert "(B) control" in out["stem"]


def test_chapter_name_is_moved_to_the_front_of_tags():
    rec = board(source="cbse_question_bank", subject="Mathematics", grade=6,
                chapterIds=["decimals-6"], tags=["Algebra", "6N1a"])
    out = bm.apply_chapter_names([rec], {("Mathematics", 6, "decimals-6"): "Decimals"})
    assert out[0]["tags"] == ["Decimals", "Algebra", "6N1a"]


def test_board_records_keep_their_tags():
    rec = board(chapterIds=["x"], tags=["Light"])
    assert bm.apply_chapter_names([rec], {("Science", 10, "x"): "Other"})[0]["tags"] == ["Light"]


def test_an_unknown_chapter_leaves_tags_alone():
    rec = board(source="cbse_question_bank", chapterIds=["9N1e"], tags=["Number systems"])
    assert bm.apply_chapter_names([rec], {})[0]["tags"] == ["Number systems"]


def test_a_chapter_name_already_in_the_tags_is_moved_not_repeated():
    rec = board(source="cbse_question_bank", subject="Mathematics", grade=6,
                chapterIds=["decimals-6"], tags=["Algebra", "Decimals"])
    out = bm.apply_chapter_names([rec], {("Mathematics", 6, "decimals-6"): "Decimals"})
    assert out[0]["tags"] == ["Decimals", "Algebra"]


def test_a_known_chapter_with_no_tags_gets_its_name():
    names = {("Mathematics", 6, "decimals-6"): "Decimals"}
    for tags in ([], None):
        rec = board(source="cbse_question_bank", subject="Mathematics", grade=6,
                    chapterIds=["decimals-6"], tags=tags)
        assert bm.apply_chapter_names([rec], names)[0]["tags"] == ["Decimals"]


def test_naming_chapters_leaves_the_input_records_unchanged():
    """The script keeps compose's list; a record edited in place would change it too."""
    rec = board(source="cbse_question_bank", subject="Mathematics", grade=6,
                chapterIds=["decimals-6"], tags=["Algebra"])
    records = [rec]
    bm.apply_chapter_names(records, {("Mathematics", 6, "decimals-6"): "Decimals"})
    assert records[0] is rec
    assert rec["tags"] == ["Algebra"]


def test_unresolved_chapters_counts_only_non_board_records_the_syllabus_misses():
    names = {("Mathematics", 6, "decimals-6"): "Decimals"}
    recs = [
        board(source="cbse_question_bank", subject="Mathematics", grade=6,
              chapterIds=["decimals-6"]),
        board(2, source="cbse_question_bank", subject="Mathematics", grade=6,
              chapterIds=["6N1a"]),
        board(3, source="cbse_question_bank", subject="Mathematics", grade=6, chapterIds=[]),
        board(4, chapterIds=["unknown-board-chapter"]),
    ]
    # A record with no chapter id is not an "unknown chapter id": the two are
    # different gaps (untagged vs. a raw code like 6N1a the syllabus can't name),
    # and folding them together printed 840 where only ~149 were unknown ids.
    assert bm.unresolved_chapters(recs, names) == 1
    assert bm.untagged_chapters(recs) == 1


def test_shared_chapter_labels_finds_one_name_on_several_chapters():
    """Mirrors the phone's picker: a chapter is named by its first question's first tag."""
    def rec(i, cid, tags):
        return board(i, source="cbse_question_bank", subject="Mathematics", grade=6,
                     chapterIds=[cid], tags=tags)
    recs = [rec(1, "6N1a", ["Number systems"]), rec(2, "6N1b", ["Number systems"]),
            rec(3, "6N1b", ["Other"]), rec(4, "decimals-6", ["Decimals"]),
            board(5, chapterIds=["light"], tags=["Light"])]
    assert bm.shared_chapter_labels(recs) == {
        ("Mathematics", 6): {"Number systems": ["6N1a", "6N1b"]}}


# ---- board records: answerable as printed (Task 16) --------------------------
#
# Every stem below is a real served board record, verbatim unless noted, with
# the verified-scheme stamp `board()` carries; the ids are cited so each can be
# checked against academicos-data/syllabus/questions.json.

def real_board(src_q, stem, *, subject="Mathematics", grade=10, marks=1,
               qtype="very_short_answer", answer="x", option=None, options=None):
    """A verified board record: the relink's stamp, and for an objective one
    the letter it verified (answerScheme.metadata.correctOption)."""
    rec = board(1, id=f"cbse:q:src:{src_q}", subject=subject, grade=grade, marks=marks,
                type=qtype, stem=stem)
    scheme = rec["answerScheme"]
    scheme["totalMarks"] = marks
    scheme["modelAnswer"] = answer
    scheme["markingPoints"][0].update(description=answer, marks=marks)
    if option is not None:
        scheme["metadata"].update(objective=True, correctOption=option)
        if options is not None:
            scheme["metadata"]["options"] = options
    return rec


def _served_or_reason(rec):
    result = bm.compose([rec], [], [])
    if result.questions:
        return result.questions[0], None
    return None, result.excluded[0]["reason"]


# Accountancy XII 67/1/2 Q31, verified: "Classify the following items ... :"
# and the items never came through.
CLASSIFY = real_board(
    "988359abbe5fb1502b6f69f9:31",
    "Classify the following items under major heads and sub-heads (if any) in the "
    "Balance Sheet of a company as per Schedule III, Part I of the Companies Act, 2013 :",
    subject="Accountancy", grade=12, marks=3, qtype="long_answer",
    answer="Property, Plant and Equipment")


def test_an_objective_stem_with_no_options_is_options_missing():
    assert _served_or_reason(copy.deepcopy(CLASSIFY)) == (None, "options-missing")


def test_a_one_mark_which_of_the_following_with_no_options_is_options_missing():
    # b0025252f69babc7d87d90f3 Q9's question with its options cut off.
    rec = real_board("b0025252f69babc7d87d90f3:9",
                     "Which one of the following is not a characteristic feature of "
                     "“humus” that is formed during decomposition of detritus ?",
                     subject="Biology", grade=12)
    assert _served_or_reason(rec) == (None, "options-missing")


def test_a_board_stem_pointing_at_a_figure_it_lacks_is_figure_unavailable():
    # Physics XII 55/1/2 Q17, verified.
    rec = real_board(
        "009c1c0b2ba7272fc371da3b:17",
        "Two batteries of emfs 6 V and 3 V and internal resistances 0·8 and 0·2 "
        "respectively are connected in series to an external resistance R, as shown in "
        "figure. Find the value of R so that the potential difference across the 6 V "
        "battery be zero.", subject="Physics", grade=12)
    assert _served_or_reason(rec) == (None, "figure-unavailable")


def test_a_figure_reference_with_an_asset_is_served():
    rec = real_board("009c1c0b2ba7272fc371da3b:17",
                     "Two batteries are connected in series to an external resistance R, "
                     "as shown in figure. Find the value of R so that the potential "
                     "difference across the 6 V battery be zero.",
                     subject="Physics", grade=12)
    rec["diagramAssetId"] = "asset:circuit"
    assert _served_or_reason(rec)[1] is None


@pytest.mark.parametrize("src_q,stem", [
    # English X 7e81f931 Q1: the passage, stopping inside its second paragraph,
    # and not one of its questions.
    ("7e81f931984b4c9a12e55b2c:1",
     "Read the passage given below : (1) If you’re like most kids, you may love snow. Not "
     "only can it get you out of school, but it’s also fun to play with. Who doesn’t love "
     "to sled and build snowmen ? Snow can also be dangerous, too. You may have heard your "
     "parents talk about how difficult it can be to drive in snow. Car accidents aren’t the "
     "only dangers created by snow. If you’re ever skiing in the mountains, you’ll want to "
     "be aware of avalanches. An avalanche is a sudden flow of snow down a slope, such as a "
     "mountain. The amount of snow in an avalanche will vary based on many things, but it "
     "can be such a huge pile that it can bury the bottom of a slope in dozens of feet of "
     "snow. 2/1/1 P.T.O.*^ (2) Avalanches can be caused by many things. Some of them are "
     "natural. For example, new snow"),
    # Mathematics X Q36: the case's opening line, and nothing after it.
    ("94cb306f384779a2121f9f55:36",
     "Rainbow is an arch of colours that is visible in the sky after rain"),
])
def test_a_case_study_with_no_question_is_excluded(src_q, stem):
    rec = real_board(src_q, stem, subject="English", marks=5, qtype="case_study")
    assert _served_or_reason(rec) == (None, "case-study-without-question")


def test_a_case_study_that_asks_its_questions_is_served():
    # Social Science X 32/5/1 Q35, verified (passage shortened).
    rec = real_board(
        "f73780490a16ef016ae67e67:35",
        "Read the given source and answer the questions that follow : Conservation of "
        "Resources At the international level, the Club of Rome advocated resource "
        "conservation for the first time in a more systematic way in 1968. Another "
        "significant contribution was made at the Earth Summit at Rio de Janeiro, Brazil "
        "in 1992. (35.1) Explain the meaning of sustainable development. 1 (35.2) In which "
        "international conference was ‘Agenda-21’ accepted ? 1 (35.3) Explain any two "
        "outcomes of the Summit. 2%1=2 666 -15 22 of",
        subject="Social Science", marks=4, qtype="case_study")
    out, reason = _served_or_reason(rec)
    assert reason is None
    assert out["stem"].endswith("Explain any two outcomes of the Summit. 2%1=2")


@pytest.mark.parametrize("src_q,stem", [
    # Mathematics X 30/1/1 Q30, verified: the volume and pi are gone.
    ("4f6182240b214906a58eaeab:30",
     "A room is in the form of a cylinder surmounted by a hemispherical dome. The base "
     "radius of the hemisphere is half of the height of the cylindrical part. If the room "
     "contains m³ of air, find the height of the cylindrical part. (Use = -)."),
    # Mathematics X f319c93a... Q19: a1/a2 = b1/b2 = c1/c2 flattened into letter
    # pairs and an empty right side.
    ("f319c93abeb1185b0864d200:19",
     "The pair of linear equations a1x + b1y + c1 = 0 and a2x + b2y + c2 = 0 have "
     "infinitely many solutions, if 2 1 2 1 2 1 c c b b a a = = ."),
    # Mathematics X 430/3/3 Q15, verified: "a ≠ b" with the Symbol font's ≠ read as
    # a superscript one.
    ("f01c7b6fd6fca7ef7d9987dc:5",
     "The lines represented by linear equations x = a and y = b (a ¹ b) are 1 (A) "
     "intersecting at (a, b). (B) intersecting at (b, a). (C) parallel. (D) coincident. "
     "/CD1BA/22"),
    # Mathematics X f319c93a... Q34: the triangle sign read as a D.
    ("f319c93abeb1185b0864d200:34",
     "BL and CM are medians of triangles ABC and PQR, respectively, where D ABC ~ D PQR, "
     "prove that AB BD PQ QM = ."),
])
def test_a_stem_that_lost_its_symbols_is_excluded(src_q, stem):
    rec = real_board(src_q, stem, marks=3, qtype="long_answer")
    assert _served_or_reason(rec) == (None, "symbol-loss")


@pytest.mark.parametrize("stem", [
    "Find the area of the corresponding minor sector of a circle of radius 21 cm. "
    "(Use π = 22/7)",
    # f319c93a... Q26 prints pi as p (the Symbol font's pi); a student reads it.
    "Find the area of the corresponding minor sector of a circle of radius 21 cm. "
    "(Use p = 3·14)",
])
def test_a_stem_that_still_carries_its_value_is_not_symbol_loss(stem):
    rec = real_board("f319c93abeb1185b0864d200:26", stem, marks=3, qtype="long_answer")
    assert _served_or_reason(rec)[1] is None


def test_a_hindi_paper_read_through_a_legacy_font_is_garbled():
    # Hindi X bee29b9e3a35e0d50d8af5e9 Q3: all 13 served Hindi stems read like this.
    rec = real_board("bee29b9e3a35e0d50d8af5e9:3",
                     "Wr & (III) {dH$ën : (A) 1-(I), 2-(II), 3-(III) (B) 1-(III), 2-(I), "
                     "3-(II) (C) 1-(II), 2-(III), 3-(I) (D) 1-(II), 2-(I), 3-(III) 3/4/1-4",
                     subject="Hindi", option="A")
    assert _served_or_reason(rec) == (None, "garbled-script")


def test_a_legacy_font_tail_on_an_english_board_stem_is_garbled():
    # Physics XII 55/4/1 Q34, verified: the Hindi copy of the question came through
    # as "{ÛY«wd AmKyU©" after the English (shortened).
    rec = real_board(
        "f64a5fa2eca8fc27010a4acb:34",
        "Answer the following questions based on the above : Find the potential energy "
        "of the dipole. 1 26 of 27 (J) {ÛY«wd AmKyU© 6 10⁻⁷ C-m H$m H$moB© {dÚwV {ÛY«wd "
        "104 N/C Ho$ EH$g_mZ {dÚwV joÌ _| Bg àH$ma pñWV h¡ {H$ {ÛY«wd AmKyU© Am¡a",
        subject="Physics", grade=12, marks=4, qtype="case_study")
    assert _served_or_reason(rec) == (None, "garbled-script")


def test_a_stem_whose_words_were_lost_is_a_fragment():
    # Mathematics X 430/2/2 Q17, verified: the Hindi-medium copy, its words dropped.
    rec = real_board("c0791b53af11069dbcd68a65:17",
                     "21 cm 120° 1 (A) 231 cm² (B) 462 cm² (C) 346.5 cm² (D) 693 cm²",
                     option="B")
    assert _served_or_reason(rec) == (None, "stem-fragment")


@pytest.mark.parametrize("src_q,stem", [
    # Mathematics X 0916a372 Q7: two words of three letters, and a whole question.
    ("0916a372de696613bddff07e:7",
     "Prime factorisation of 424 is : (A) 2 ´ 53 ´ 4 (B) 2 ´ 53 ´ 2 (C) 23 ´ 53 "
     "(D) 24 ´ 53"),
    ("0916a372de696613bddff07e:8", "Solve for x : 2x + 3 = 11"),
])
def test_a_short_whole_question_is_not_a_fragment(src_q, stem):
    rec = real_board(src_q, stem, option="D" if "(D)" in stem else None)
    assert _served_or_reason(rec)[1] is None


@pytest.mark.parametrize("stem", [
    # Social Science X f5f52d3e Q8: a case's question is a fill-in MCQ.
    "Study the table and answer the question that follows : Year 1990 1800 The "
    "attendance percentage of this country of the age group of 14 and 15 years is "
    "__________. (A) 90 percent (B) 80 percent (C) 70 percent (D) 60 percent",
    # History XII 01e0c514 Q9: its question is an assertion to judge.
    "Read the source and answer the questions that follow : Assertion (A) : Francois "
    "Bernier has called the Mughal king as the king of barbarians . Reason (R) : Crown "
    "ownership of land was its reason.",
    # Chemistry XII 1c8ab2d6 Q34: numbered statements to account for.
    "Answer the following questions : (i) Transition metals form complexes. (ii) Cr2⁺ is "
    "reducing in nature while with the same d-orbital configuration (d4) Mn3⁺ is an "
    "oxidising agent. (iii) Zn has lowest enthalpy of atomization.",
])
def test_a_case_study_that_asks_by_options_or_numbered_parts_is_served(stem):
    rec = real_board("f5f52d3e0580aac4355f9205:8", stem, subject="Social Science",
                     marks=1, qtype="case_study", option="A" if "(D)" in stem else None)
    if "Assertion" in stem:
        rec["answerScheme"]["metadata"].update(objective=True, correctOption="C")
    assert _served_or_reason(rec)[1] is None


# -- repairs --

def test_inline_options_are_printed_as_a_to_d_with_the_verified_letter():
    from academicos.assessment.pdf import split_stem_and_options

    # Mathematics X 430/5/1 Q12, verified A.
    rec = real_board("0b3c7b807dcc7e88fd1809df:17",
                     "The sum of the first 100 even natural numbers is : (a) 10100 "
                     "(b) 2550 (c) 5050 (d) 10010", answer="10100", option="A",
                     options={"A": "10100", "B": "2550", "C": "5050", "D": "10010"})
    result = bm.compose([rec], [], [])
    out = result.questions[0]
    assert out["stem"] == ("The sum of the first 100 even natural numbers is : "
                           "(A) 10100 (B) 2550 (C) 5050 (D) 10010")
    head, options = split_stem_and_options(out["stem"])
    assert head.strip() == "The sum of the first 100 even natural numbers is :"
    assert options == ["10100", "2550", "5050", "10010"]
    assert out["answerScheme"]["metadata"]["correctOption"] == "A"
    assert out["parts"] == []
    assert bm.contract_errors(out) == []
    assert result.repairs["options-inline"] == 1


def test_the_mark_printed_before_the_options_is_dropped():
    # Mathematics X 430/2/2 Q12, verified A: "... is called a 1 (A) secant".
    rec = real_board("c0791b53af11069dbcd68a65:8",
                     "A line intersecting a circle in two distinct points is called a 1 "
                     "(A) secant (B) chord (C) diameter (D) tangent", answer="secant",
                     option="A")
    out, reason = _served_or_reason(rec)
    assert reason is None
    assert out["stem"] == ("A line intersecting a circle in two distinct points is called a "
                           "(A) secant (B) chord (C) diameter (D) tangent")


def test_an_mcq_whose_verified_key_names_no_printed_option_is_refused():
    rec = real_board("c0791b53af11069dbcd68a65:8",
                     "A line intersecting a circle in two distinct points is called a "
                     "(A) secant (B) chord (C) diameter", answer="tangent", option="D")
    assert _served_or_reason(rec) == (None, "mcq-answer-unresolved")


def test_a_one_mark_mcq_with_no_verified_letter_is_refused():
    rec = real_board("c0791b53af11069dbcd68a65:8",
                     "A line intersecting a circle in two distinct points is called a "
                     "(A) secant (B) chord (C) diameter (D) tangent", answer="secant")
    assert _served_or_reason(rec) == (None, "mcq-answer-unresolved")


def test_a_multi_mark_question_in_parts_is_not_read_as_options():
    rec = real_board("7d85e69ac9a355f7b0d2eac0:32",
                     "(a) Explain any five challenges faced by political parties in India. "
                     "(b) Suggest any five measures to reform political parties.",
                     subject="Social Science", marks=5, qtype="long_answer")
    out, reason = _served_or_reason(rec)
    assert reason is None and out["stem"] == rec["stem"]


# CBSE's four assertion-reason options, word for word as the Home Science X
# 2024-25 SQP prints them (cbse:sqp:ClassX_2024_25:Home Science:17).
AR_OPTIONS = [
    "Both A and R are true and R is the correct explanation of A.",
    "Both A and R are true but R is not the correct explanation of A.",
    "A is true but R is false.",
    "A is false but R is true.",
]
AR_STEM = ("Assertion (A) : The amount of ozone in the atmosphere began to drop sharply "
           "in the 1980s. Reason (R) : The oxygen atoms combine with molecular oxygen to "
           "form ozone.")


def test_an_assertion_reason_item_gets_the_four_standard_options():
    from academicos.assessment.pdf import split_stem_and_options

    # Science X af50a3f7e666fdea9cee608f Q20, key B.
    rec = real_board("af50a3f7e666fdea9cee608f:20", AR_STEM, subject="Science",
                     answer="(B)", option="B")
    result = bm.compose([rec], [], [])
    out = result.questions[0]
    head, options = split_stem_and_options(out["stem"])
    assert head.strip() == AR_STEM
    assert [o.rstrip(".") for o in options] == [o.rstrip(".") for o in AR_OPTIONS]
    assert out["answerScheme"]["metadata"]["correctOption"] == "B"
    assert bm.contract_errors(out) == []
    assert result.repairs["assertion-reason-options"] == 1


def test_an_assertion_reason_item_that_prints_its_options_is_not_given_them_twice():
    # stem_options cannot read these labels -- the "(A)" of "Assertion (A)"
    # comes first -- so only has_option_labels tells the options are there.
    stem = AR_STEM + " " + " ".join(f"({k}) {v}" for k, v in zip("ABCD", AR_OPTIONS))
    rec = real_board("af50a3f7e666fdea9cee608f:20", stem, subject="Science",
                     answer="(B)", option="B")
    out, reason, repairs, _ = bm.repair_board(rec)
    assert "assertion-reason-options" not in repairs
    assert out["stem"] == stem
    assert out["stem"].count(AR_OPTIONS[0]) == 1


def test_an_assertion_reason_item_that_prints_its_options_with_no_verified_letter_is_refused():
    stem = AR_STEM + " " + " ".join(f"({k}) {v}" for k, v in zip("ABCD", AR_OPTIONS))
    rec = real_board("af50a3f7e666fdea9cee608f:20", stem, subject="Science", answer="(B)")
    assert _served_or_reason(rec) == (None, "mcq-answer-unresolved")


# Mathematics XII a52469d5f185d77194f532dd Q9 as served: Q9 and Q10 fused, each
# with its own (A)-(D). stem_options reads neither set; the PDF's
# split_stem_and_options prints Q10's options under a letter verified for Q9.
FUSED = ("The Cartesian equations of a line are given as 6x – 2 = 3y + 1 = 2z – 2 The "
         "direction ratios of the line are : (A) 2, – 1, 3 (B) 1, – 2, – 3 (C) 1, 2, 3 "
         "(D) 3, 1, 2 10. The solution set of the inequation 2x + 3y < 6 is : (A) open "
         "half-plane not containing origin (B) whole xy-plane except the points lying on "
         "the line 2x + 3y = 6 (C) open half-plane containing origin (D) half-plane "
         "containing the origin and the points lying on the line 2x + 3y = 6 666 "
         "65(B)-11 8 of")


@pytest.mark.parametrize("stem,marks,qtype", [
    (FUSED, 1, "very_short_answer"),
    (FUSED, 2, "mcq"),
    # SQP Mathematics (Standard) X 2024-25 Q15's shape on a board record: a
    # space before the bracket, none after it -- the labels do not parse.
    ("The coordinates of the point where the line 2x + y = 4 cuts the x-axis are "
     "A) (0, 0) B) (-4, 0) C ) (-5, 0) D) (2, 0)", 1, "very_short_answer"),
])
def test_a_board_objective_stem_whose_printed_labels_do_not_parse_is_refused(stem, marks, qtype):
    rec = real_board("a52469d5f185d77194f532dd:9", stem, grade=12, marks=marks, qtype=qtype,
                     answer="(D)", option="D")
    assert _served_or_reason(rec) == (None, "mcq-options-unresolved")


def test_an_assertion_reason_item_with_no_verified_letter_is_refused():
    rec = real_board("af50a3f7e666fdea9cee608f:20", AR_STEM, subject="Science",
                     answer="(B)")
    assert _served_or_reason(rec) == (None, "mcq-answer-unresolved")


# Accountancy XII 67/2/1 Q25, as served: the rupee sign extracted as "<".
RUPEE_STEM = ("Trisha died on 31st July, 2022. According to the partnership deed, the "
              "executors of the deceased partner were entitled to : (ii) Salary @ < 15,000 "
              "per quarter. (iv) Share of profits from the closure of the last accounting "
              "year 2019 -20, 2020 -21 and 2021 -22 were < 1,00,000, < 2,00,000 and "
              "< 1,50,000 respectively. Particulars Amount (<) Assets")


def test_the_rupee_sign_read_as_less_than_is_restored_in_a_commerce_paper():
    rec = real_board("4d332115f14c6aeeaa34b438:25", RUPEE_STEM, subject="Accountancy",
                     grade=12, marks=6, qtype="long_answer")
    out, reason, repairs, _ = bm.repair_board(rec)
    assert reason is None
    assert "Salary @ ₹ 15,000 per quarter" in out["stem"]
    assert "were ₹ 1,00,000, ₹ 2,00,000 and ₹ 1,50,000 respectively" in out["stem"]
    assert "Particulars Amount (₹) Assets" in out["stem"]
    assert "<" not in out["stem"]
    assert repairs == ["rupee-sign-restored"]
    result = bm.compose([rec], [], [])
    assert result.repairs["rupee-sign-restored"] == 1


@pytest.mark.parametrize("stem,restored", [
    # Accountancy XII be7fd19527d3a0bcac687817 Q22: after a dash, no space.
    ("Debtors -< 40,000 Stock -< 50,000 Plant -< 60,000",
     "Debtors -₹ 40,000 Stock -₹ 50,000 Plant -₹ 60,000"),
    # Accountancy XII d4ab284479dbd2fbc3a07c7f Q26: after a word, a comma, a full stop.
    ("a purchase consideration of < 40,00,000. < 20,00,000 were paid",
     "a purchase consideration of ₹ 40,00,000. ₹ 20,00,000 were paid"),
    # A Balance Sheet's head (Accountancy XII be7fd19527d3a0bcac687817 Q22).
    ("Balance Sheet as at 31st March, 2023 Liabilities Amount < Assets Amount < Capitals :",
     "Balance Sheet as at 31st March, 2023 Liabilities Amount ₹ Assets Amount ₹ Capitals :"),
    # An MCQ's options: "(a) < 36,000 (b) < 18,000".
    ("interest on loan : (a) < 36,000 (b) < 18,000",
     "interest on loan : (a) ₹ 36,000 (b) ₹ 18,000"),
    # A comparison is left as printed: after a number or a one-letter variable.
    ("if 0 < 1 and x < 5", "if 0 < 1 and x < 5"),
    # SQP Economics XII 2024-25 Q10: "Receipts < Payments" is a less-than.
    ("C. Receipts < Payments on current account", "C. Receipts < Payments on current account"),
])
def test_restore_rupee(stem, restored):
    assert bm.restore_rupee(stem) == restored


@pytest.mark.parametrize("src_q,stem", [
    ("d4ab284479dbd2fbc3a07c7f:26",
     "On 31st March, 2022 it decided to write off discount on issue of debentures. It had "
     "a credit balance of < Pass necessary journal entries for the above transaction."),
    ("4d332115f14c6aeeaa34b438:26",
     "Discount on issue of debentures was written off. The company had a balance of < on "
     "the same date in its Securities Premium. Pass the necessary journal entries."),
])
def test_a_commerce_stem_whose_amount_was_lost_with_its_sign_is_symbol_loss(src_q, stem):
    rec = real_board(src_q, stem, subject="Accountancy", grade=12, marks=6,
                     qtype="long_answer")
    assert _served_or_reason(rec) == (None, "symbol-loss")


def test_the_rupee_repair_is_made_only_in_commerce_papers():
    # Mathematics X: "withdraw < 2,000" is a rupee sign too, but "x < 2" in a
    # Mathematics paper is not, and a Mathematics stem is not read this way.
    rec = real_board("4d332115f14c6aeeaa34b438:25", RUPEE_STEM, subject="Mathematics",
                     marks=6, qtype="long_answer")
    out, _, repairs, _ = bm.repair_board(rec)
    assert out["stem"] == RUPEE_STEM and repairs == []


@pytest.mark.parametrize("src_q,stem,cleaned", [
    # Biology XII 57/1/1 Q2, verified B: the paper's series "-11" after option D.
    ("784bd959b5f48fd5620f57e6:2",
     "Which one of the following hormones is secreted by the human placenta that helps in "
     "the maintenance of pregnancy ? (A) Relaxin (B) Human Chorionic Gonadotropin "
     "(C) Oxytocin (D) Human Placental Lactogen -11",
     "Which one of the following hormones is secreted by the human placenta that helps in "
     "the maintenance of pregnancy ? (A) Relaxin (B) Human Chorionic Gonadotropin "
     "(C) Oxytocin (D) Human Placental Lactogen"),
    # Biology XII 57/5/2 Q9, verified B: "/22" after option D, the mark before (A).
    ("b0025252f69babc7d87d90f3:9",
     "Which one of the following is not a characteristic feature of “humus” that is formed "
     "during decomposition of detritus ? 1 (A) amorphous, colloidal, dark coloured "
     "substance (B) amorphous, colloidal, light coloured substance (C) substance resistant "
     "to microbial action (D) colloidal substance /22",
     "Which one of the following is not a characteristic feature of “humus” that is formed "
     "during decomposition of detritus ? (A) amorphous, colloidal, dark coloured "
     "substance (B) amorphous, colloidal, light coloured substance (C) substance resistant "
     "to microbial action (D) colloidal substance"),
])
def test_page_furniture_is_cleaned_from_a_board_stem_not_dropped(src_q, stem, cleaned):
    rec = real_board(src_q, stem, subject="Biology", grade=12, option="B")
    result = bm.compose([rec], [], [])
    assert [q["stem"] for q in result.questions] == [cleaned]
    assert result.repairs["page-furniture-stripped"] == 1


@pytest.mark.parametrize("text,expected", [
    ("x cos 60 + y cos 0 + sin 30 - cot 45 = 5 # 15| P a g e",
     "x cos 60 + y cos 0 + sin 30 - cot 45 = 5"),
    ("Find the mode of the data. # 17| P a g e P.T.O.", "Find the mode of the data."),
    ("(D) Papal State # 4 of", "(D) Papal State"),
    ("(D) < 70,000 666 -11 6 of", "(D) < 70,000"),
    ("(D) x z < y z 666 465-11 4 of", "(D) x z < y z"),
    ("(D) 90° /DA2AB/21", "(D) 90°"),
    ("How were the languages grouped ? /21/BBCA2 Page 28 of 32",
     "How were the languages grouped ?"),
    ("Read" + chr(1) + "the" + chr(1) + "following" + chr(5) + "extract",
     "Read the following extract"),
    ("Explain the working of an AC generator. 11-", "Explain the working of an AC generator."),
    ("Faites la question neuf. (vii) 20 10 of", "Faites la question neuf. (vii) 20"),
    # values, not furniture
    ("(A) 11 (B) -11", "(A) 11 (B) -11"),
    ("If x = -11, find y.", "If x = -11, find y."),
    ("Name the part of a flower. 2", "Name the part of a flower. 2"),
])
def test_board_page_furniture(text, expected):
    assert bm.strip_board_furniture(text) == expected


def test_a_stem_that_is_only_furniture_is_excluded_as_page_furniture():
    # Mathematics X db32b7ab98169b625243c09e Q35: a page footer and a few numbers.
    rec = real_board("db32b7ab98169b625243c09e:35", "7 cm² cm 14 cm = # 17| P a g e P.T.O.",
                     marks=5, qtype="case_study")
    assert _served_or_reason(rec) == (None, "page-furniture")


# -- near-duplicates --

# Mathematics X, two papers of one series (f319c93a... Q9, b23bc2e5... Q15): one
# question, extracted with different tails.
QUADRATIC_1 = ("Which of the following is not a quadratic equation ? (A) (x – 2)₂ + 1 = "
               "2x – 3 (B) (2x – 1) (x – 3) = (x + 5) (x – 1) (C) x(x + 1) + 8 = (x + 2) "
               "(x – 2) (D) 2x + x 3 = 5 14-")
QUADRATIC_2 = ("Which of the following is not a quadratic equation ? (A) (x – 2)₂ + 1 = "
               "2x – 3 (B) (2x – 1) (x – 3) = (x + 5) (x – 1) (C) x(x + 1) + 8 = (x + 2) "
               "(x – 2) (D) 2x + x 3 =")


def test_near_identical_stems_are_one_question():
    assert bm.near_duplicate_score(QUADRATIC_1, QUADRATIC_2) >= bm.NEAR_DUPLICATE_MIN


def test_two_real_questions_that_share_most_words_are_not_duplicates():
    # SQP Bharatanatyam XII 2024-25 Q8 and 2025-26 Q8: the same options, but one
    # asks for Krishna's bow and the other for Shiva's -- different keys.
    krishna = ("What is Lord Krishna’s bow called? a) Gandeev b) Pinak c) Dhanush "
               "d) Sarang")
    shiva = ("What is the name of Lord Shiva’s bow called? a) Gandeev b) Pinak "
             "c) Dhanush d) Sarang")
    assert bm.near_duplicate_score(krishna, shiva) < bm.NEAR_DUPLICATE_MIN


BAG = ("A bag contains 5 red, 8 white, 4 green and 7 black balls. If one ball is drawn "
       "at random, find the probability that it is not green.")


@pytest.mark.parametrize("other", [
    BAG.replace("not green", "not black"),                 # a word moved in from elsewhere
    BAG.replace("5 red, 8 white", "8 red, 5 white"),       # two numbers swapped
    BAG.replace("If one ball", "If one white ball").replace("not green", "not black"),
])
def test_questions_that_reuse_each_others_words_are_not_duplicates(other):
    # Every word of one is a word of the other, so word SETS call them one
    # question; which word stands where is the question.
    assert bm.near_duplicate_score(BAG, other) < bm.NEAR_DUPLICATE_MIN
    result = bm.compose([real_board("f319c93abeb1185b0864d200:30", BAG, option=None,
                                    marks=2, qtype="short_answer"),
                         real_board("b23bc2e537566a04afbf4415:30", other, option=None,
                                    marks=2, qtype="short_answer")], [], [])
    assert len(result.questions) == 2


def test_a_near_duplicate_board_record_is_withheld_whole():
    first = real_board("f319c93abeb1185b0864d200:9", QUADRATIC_1, option="D")
    second = real_board("b23bc2e537566a04afbf4415:15", QUADRATIC_2, option="D")
    result = bm.compose([first, second], [], [])
    assert [q["id"] for q in result.questions] == [first["id"]]
    assert [(e["id"], e["reason"]) for e in result.excluded] == [
        (second["id"], "duplicate-stem")]
    assert result.withheld == [second]


def test_a_near_duplicate_collapses_to_the_record_with_the_verified_scheme():
    verified = real_board("f319c93abeb1185b0864d200:9", QUADRATIC_1, option="D")
    sqp = copy.deepcopy(verified)
    sqp.update(id="cbse:sqp:ClassX_2024_25:Mathematics:9", source="cbse_sample_paper",
               stem=QUADRATIC_2)
    sqp["answerScheme"]["metadata"] = {}
    sqp["answerScheme"]["modelAnswer"] = sqp["answerScheme"]["markingPoints"][0][
        "description"] = "(D) 2x + x 3 ="
    assert bm.compose([], [], [copy.deepcopy(sqp)]).questions  # alone, it is served
    result = bm.compose([verified], [], [sqp])
    assert [q["id"] for q in result.questions] == [verified["id"]]
    assert [e["reason"] for e in result.excluded] == ["duplicate-stem"]


# -- every exclusion recorded; excluded board records kept whole --

def test_a_board_record_the_fidelity_gate_excludes_is_recorded_and_kept_whole():
    rec = copy.deepcopy(CLASSIFY)
    result = bm.compose([rec], [], [])
    assert result.excluded == [{"id": rec["id"], "source": "cbse_board_paper",
                                "reason": "options-missing", "subject": "Accountancy",
                                "grade": 12, "stem": rec["stem"][:200]}]
    assert result.withheld == [CLASSIFY]


def test_a_repaired_board_record_leaves_its_input_unchanged():
    rec = real_board("0b3c7b807dcc7e88fd1809df:17",
                     "The sum of the first 100 even natural numbers is : (a) 10100 "
                     "(b) 2550 (c) 5050 (d) 10010", answer="10100", option="A")
    before = copy.deepcopy(rec)
    bm.compose([rec], [], [])
    assert rec == before


# -- the web registry path uses the same filters --

@pytest.mark.parametrize("name", ["needs_missing_figure", "looks_truncated",
                                  "has_broken_options", "looks_mangled"])
def test_the_pool_filters_live_in_bank_merge(name):
    from academicos.assessment import pool

    assert getattr(pool, name) is getattr(bm, name)
    assert getattr(bm, name).__module__ == bm.__name__


@pytest.mark.parametrize("fn,text,rejected", [
    ("needs_missing_figure", "In the given figure, find the value of x.", True),
    ("needs_missing_figure", "In the given figure, which is right? (a) 1 (b) 2 (c) 3", False),
    ("looks_truncated", "Select the correct option from the following", True),
    ("looks_truncated", "The products of the reaction are :", True),
    ("looks_truncated", "Which of the following is a metal? (A) Na (B) Cl", False),
    ("has_broken_options", "Pick one (a) 12 (c) 14 (d) 15", True),
    ("has_broken_options", "Pick one (a) 12 (b) (c) 14 (d) 15", True),
    ("has_broken_options", "(a) Explain the process of digestion in humans", False),
    ("looks_mangled", "{H$gr Xn©U à{H«$`m _hmoX {H$gr", True),
    ("looks_mangled", "Explain the process of photosynthesis in green plants.", False),
])
def test_the_pool_still_rejects_what_it_rejected(fn, text, rejected):
    from academicos.assessment import pool

    assert bool(getattr(pool, fn)(text)) is rejected


@pytest.mark.parametrize("stem,marks", [
    # A typed MCQ worth 2 marks (the served board set has 5 such records).
    ("A line intersecting a circle in two distinct points is called a "
     "(A) secant (B) chord (C) diameter (D) tangent", 2),
    # A 1-mark MCQ that prints three options.
    ("A line intersecting a circle in two distinct points is called a "
     "(A) secant (B) chord (C) diameter", 1),
])
def test_a_typed_mcq_with_no_verified_letter_is_refused_whatever_its_marks(stem, marks):
    # With no verified correctOption there is no answer key to print, so the
    # MCQ is refused whatever its marks or option count.
    rec = real_board("c0791b53af11069dbcd68a65:8", stem, answer="secant",
                     marks=marks, qtype="mcq")
    assert _served_or_reason(rec) == (None, "mcq-answer-unresolved")


def test_a_stem_that_adds_or_drops_a_negation_is_a_different_question():
    # "is correct" and "is not correct" ask for opposite answers. Share every
    # other word and they still must not collapse into one question.
    yes = ("Which of the following statements about photosynthesis in green plants "
           "is correct? Give a reason for your answer.")
    no = yes.replace("is correct", "is not correct")
    assert bm.near_duplicate_score(yes, no) < bm.NEAR_DUPLICATE_MIN
    result = bm.compose([real_board("f319c93abeb1185b0864d200:30", yes, option=None,
                                    marks=2, qtype="short_answer"),
                         real_board("b23bc2e537566a04afbf4415:30", no, option=None,
                                    marks=2, qtype="short_answer")], [], [])
    assert len(result.questions) == 2


# ---- NCERT Exemplar: a further source through the same gates (Task 11) --------

EXEMPLAR_BANK = (Path(__file__).resolve().parents[1] / "academicos-data" / "corpus"
                 / "ncert-exemplar" / "questions.json")


def exemplar_mcq(**kw):
    """The shape corpus/ncert_exemplar.py builds (the bank's first record):
    one part holding the options as a list, NCERT's answer in the scheme."""
    rid = "exemplar:q:6:mathematics:1:-:1"
    answer = "(C) 400000"
    rec = board(1, id=rid, questionBankId="ncert-exemplar:class6-mathematics/feep101.pdf",
                subject="Mathematics", grade=6, type="mcq", marks=1,
                source="ncert_exemplar", tags=["Number System"],
                stem="The product of the place values of two 2’s in 428721 is")
    rec["parts"] = [{"id": f"{rid}:p1", "partNumber": 1, "text": "", "textLatex": "",
                     "marks": 1, "answerType": "singleChoice",
                     "options": ["4", "40000", "400000", "40000000"],
                     "correctOption": "c", "expectedAnswer": answer,
                     "alternativeAnswers": []}]
    rec["answerScheme"] = {"totalMarks": 1, "markingPoints": [
        {"id": f"{rid}:mp1", "description": answer, "marks": 1, "keyword": "",
         "isRequired": True, "synonyms": []}],
        "rubricLevels": [], "commonErrors": [], "alternativeAnswers": [],
        "modelAnswer": answer, "modelAnswerLatex": "", "hasPartialCredit": False,
        "metadata": {"answerFile": "feep1an.pdf"}, "provenance": "ncert_exemplar_answer",
        "sourcePaperCode": "", "sourceDocumentId": "feep1an.pdf"}
    rec["metadata"] = {"sectionKind": "mcq_single", "correctOptions": ["c"]}
    rec.update(kw)
    return rec


def exemplar_short(**kw):
    rec = board(2, id="exemplar:q:9:science:1:-:40", source="ncert_exemplar",
                subject="Science", grade=9, type="short_answer", marks=2,
                stem="Why is ice at 273 K more effective in cooling than water at the same temperature?")
    rec["answerScheme"] = {**rec["answerScheme"], "metadata": {},
                           "modelAnswer": "Ice absorbs its latent heat of fusion as it melts.",
                           "provenance": "ncert_exemplar_answer"}
    rec.update(kw)
    return rec


def test_an_exemplar_mcq_is_served_inline_with_ncerts_own_key():
    result = bm.compose([], [], [], exemplar=[exemplar_mcq()])
    assert result.counts["exemplar"] == 1 and len(result.questions) == 1
    out = result.questions[0]
    assert out["parts"] == []
    assert "(A) 4 (B) 40000 (C) 400000 (D) 40000000" in out["stem"]
    scheme = out["answerScheme"]
    assert scheme["metadata"]["correctOption"] == "C"
    # NCERT's answer, never relabelled as a CBSE marking scheme.
    assert scheme["provenance"] == "ncert_exemplar_answer"
    assert bm.contract_errors(out) == []


def test_an_exemplar_answer_is_an_answer_key():
    """The served bank's one "has an answer key" rule reads content, so
    NCERT's answer counts as one -- before the merge and after it."""
    from academicos.assessment.qbank_routes import QuestionBank

    result = bm.compose([], [], [], exemplar=[exemplar_mcq(), exemplar_short()])
    assert result.counts["exemplar"] == 2
    for rec in [exemplar_mcq(), exemplar_short(), *result.questions]:
        assert QuestionBank.has_answer_key(rec)
    assert {q["answerScheme"]["provenance"] for q in result.questions} == {"ncert_exemplar_answer"}


def test_an_exemplar_record_goes_through_the_fidelity_gate():
    figure = exemplar_short(id="exemplar:q:9:science:1:-:41",
                            stem="Study the figure given below and name the process shown in it.")
    no_answer = exemplar_short(id="exemplar:q:9:science:1:-:42")
    no_answer["answerScheme"] = {**no_answer["answerScheme"], "modelAnswer": "",
                                 "markingPoints": []}
    result = bm.compose([], [], [], exemplar=[figure, no_answer])
    assert result.questions == []
    assert sorted(e["reason"] for e in result.excluded) == ["figure-referenced", "no-answer"]
    assert all(e["source"] == "ncert_exemplar" for e in result.excluded)


def test_an_exemplar_copy_of_a_cbse_question_is_a_duplicate():
    """CBSE's own sources come first; an Exemplar item asking the same thing
    is left out, not served twice."""
    served = board(3, subject="Science", grade=9,
                   stem="Why is ice at 273 K more effective in cooling than water at the same temperature?")
    result = bm.compose([served], [], [], exemplar=[exemplar_short()])
    assert result.counts == {"board": 1, "cbe": 0, "sqp": 0, "exemplar": 0}
    assert [e["reason"] for e in result.excluded] == ["duplicate-stem"]


def test_exemplar_mcq_options_with_a_fifth_choice_are_not_read_as_four():
    rec = exemplar_mcq()
    rec["parts"][0]["options"] = ["4", "40000", "400000", "40000000", "4000"]
    result = bm.compose([], [], [], exemplar=[rec])
    assert result.questions == []
    assert [e["reason"] for e in result.excluded] == ["mcq-options-unresolved"]


@pytest.mark.skipif(not EXEMPLAR_BANK.exists(), reason="Exemplar bank not built")
def test_every_served_exemplar_mcq_keeps_ncerts_letter():
    """Measured on the real bank: the letter the merge reads from NCERT's
    answer text is the letter the builder parsed (metadata.correctOptions)."""
    import json

    rows = json.loads(EXEMPLAR_BANK.read_text(encoding="utf-8"))["questions"]
    result = bm.compose([], [], [], exemplar=rows)
    by_id = {r["id"]: r for r in rows}
    mcqs = [q for q in result.questions if q["type"] == "mcq"]
    assert mcqs, "no Exemplar MCQ served"
    for q in mcqs:
        want = [c.upper() for c in by_id[q["id"]]["metadata"]["correctOptions"]]
        assert [q["answerScheme"]["metadata"]["correctOption"]] == want, q["id"]
        assert q["answerScheme"]["provenance"] == "ncert_exemplar_answer"


# ---- the relink after the merge strips no key the merge served (Task 11) -----
#
# enrich_question_bank.py runs again after the merge. At 8e92ed9 that second
# relink would have removed the keys of 67 served non-board records (37
# Exemplar, 30 CBE/SQP) and left them served keyless: the relink re-read their
# options with the board verifier's readers, which differ from the merge's.
# Each case below is a real record of those 67.

def _relinked(questions, tmp_path):
    from academicos.assessment.question_bank import AnswerKeyIndex, relink_answer_schemes
    from test_scheme_verify import make_answer_keys

    served = copy.deepcopy(questions)
    report = relink_answer_schemes(served, AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", [])),
                                   parse_dir=tmp_path)
    return served, report


def _cbe_listed(rid, stem, options, answer, **kw):
    rec = cbe_mcq(id=rid, stem=stem, answer=answer, **kw)
    return _with_options(rec, [f"{l}. {t}" for l, t in zip("ABCD", options)])


# cbe:q:Maths9SM2 -- the option opens with the article "a", which the key
# reader took for an "(a)" label and cut: "rational number" named no option.
MATHS9SM2 = _cbe_listed(
    "cbe:q:Maths9SM2", "The number 0.318564318564318564………is:",
    ["a natural number", "an integer", "a rational number", "an irrational number"],
    "C. a rational number (1)", grade=9)
# cbe:q:Science10MS2 -- numbered statements before the (A)-(D) options: the
# relink read "1. Abstinence ... 4. Oral pill" as the options.
SCIENCE10MS2 = _cbe_listed(
    "cbe:q:Science10MS2",
    "Some methods of birth control are listed. 1. Abstinence 2. Condom 3. Inter-Uterine "
    "Device 4. Oral pill 1 (a) Which methods limit the spread of sexually transmitted diseases?",
    ["1 and 2 only", "2 and 3 only", "2 and 4 only", "3 and 4 only"], "A.",
    subject="Science", grade=10)


@pytest.mark.parametrize("raw", [MATHS9SM2, SCIENCE10MS2], ids=lambda r: r["id"])
def test_a_served_cbe_key_survives_the_relink_after_the_merge(raw, tmp_path):
    result = bm.compose([], [copy.deepcopy(raw)], [])
    assert len(result.questions) == 1, result.excluded
    served, report = _relinked(result.questions, tmp_path)
    assert report.quarantined == {}
    assert served[0]["answerScheme"] == result.questions[0]["answerScheme"]


def test_a_served_exemplar_key_survives_the_relink_after_the_merge(tmp_path):
    """exemplar:q:6:science:11:-:6 keyed "(c) A shoe box" (the article "A"
    was cut as a label), and exemplar:q:6:mathematics:1:-:99, a fill-in-the-
    blanks item whose "(a) ... (b) ..." blanks the relink read as options."""
    shadow = exemplar_mcq(id="exemplar:q:6:science:11:-:6", subject="Science",
                          stem="Which of the following can never form a circular shadow?")
    shadow["parts"][0].update(options=["A ball", "A flat disc", "A shoe box",
                                       "An ice cream cone"], expectedAnswer="(c) A shoe box")
    shadow["answerScheme"]["modelAnswer"] = "(c) A shoe box"
    shadow["answerScheme"]["markingPoints"][0]["description"] = "(c) A shoe box"
    shadow["metadata"]["correctOptions"] = ["c"]
    blanks = exemplar_short(id="exemplar:q:6:mathematics:1:-:99", subject="Mathematics",
                            grade=6, type="very_short_answer", marks=1,
                            stem="Fill in the blanks to make the statements true: (a) 10 million "
                                 "= _____ crore. (b) 10 lakh = _____ million.")
    blanks["answerScheme"]["modelAnswer"] = "(a) 1 (b) 1"
    blanks["answerScheme"]["markingPoints"][0]["description"] = "(a) 1 (b) 1"
    result = bm.compose([], [], [], exemplar=[shadow, blanks])
    assert result.counts["exemplar"] == 2, result.excluded
    served, report = _relinked(result.questions, tmp_path)
    assert report.quarantined == {}
    assert [q["answerScheme"] for q in served] == [q["answerScheme"] for q in result.questions]


def test_a_key_the_relink_rejects_is_not_served():
    """SQP Mathematics (Standard) X 2024-25 Q19: an assertion-reason item keyed
    "B)" whose stem prints no options, so nothing ties the letter to it (the
    relink's unreadable-options). The merge served it at 8e92ed9; the relink
    after it would have left it served with no key. One verifier decides."""
    ar = _raw_sqp("ClassX_2024_25", "Mathematics (Standard)", 19, grade=10, marks=1, page=3,
                  stem="Assertion (A): HCF of any two consecutive even natural numbers is "
                       "always 2. Reason (R): Even natural numbers are divisible by 2.",
                  answer="B)")
    result = bm.compose([], [], [ar])
    assert result.questions == []
    assert [e["reason"] for e in result.excluded] == ["key-rejected"]


SERVED_BANK = Path(__file__).resolve().parents[1] / "academicos-data" / "syllabus" / "questions.json"


@pytest.mark.skipif(not SERVED_BANK.exists(), reason="served bank not built")
def test_the_relink_strips_no_served_non_board_key(tmp_path):
    """The pipeline's invariant, on the committed served bank: every CBE, SQP
    and Exemplar key the merge served passes the relink that runs after it."""
    import json

    rows = [r for r in json.loads(SERVED_BANK.read_text(encoding="utf-8"))["questions"]
            if r.get("source") != bm.BOARD_SOURCE]
    assert rows
    _, report = _relinked(rows, tmp_path)
    assert report.quarantined == {}


# ---- symbol-font private-use glyphs (Task 121) -------------------------------
#
# The source PDFs write °, ρ, ∠, × and the rest with a symbol font, and the
# extraction kept the font's own code points (U+F0B0, U+F072, ...) instead of
# the characters. Nothing drew them: 45 served records printed a hole where a
# symbol belonged, and Science 9 PS1's options read alike without their ρ.

CBE_BANK = (Path(__file__).resolve().parents[1] / "academicos-data" / "corpus"
            / "cbse-cbe" / "questions.json")


def real_cbe(record_id: str) -> dict:
    """A record from the real CBE bank, so the glyphs are the ones it holds."""
    import json

    rows = json.loads(CBE_BANK.read_text(encoding="utf-8"))["questions"]
    return next(r for r in rows if r["id"] == record_id)


@pytest.mark.parametrize("text,restored", [
    # Adobe Symbol 0x72 rho, 0x2F slash (cbe:q:Science9PS1's options).
    ("W \uf072 \uf02f g", "W ρ / g"),
    # 0xB0 degree, 0x61 alpha, 0xD0 angle (cbe:q:Maths9MS6).
    ("2\uf061 + 50\uf0b0. Find \uf0d0BAC", "2α + 50°. Find ∠BAC"),
    # 0x57 Omega (cbe:q:Science10SD1's resistors), 0x44 Delta (cbe:q:Maths9BS8).
    ("R1 20 \uf057 In \uf044ACE use Pythagoras", "R1 20 Ω In ΔACE use Pythagoras"),
    # 0xB4 multiply, 0xB8 divide (cbe:q:Maths6RB5), 0x5C therefore, 0xDE implies.
    ("26.16 \uf0b8 4 = 6.54 \uf0b4 1 \uf05c x \uf0de y", "26.16 ÷ 4 = 6.54 × 1 ∴ x ⇒ y"),
    # 0xB7 bullet, the marking-scheme bullet of 1,449 SQP lines.
    ("\uf0b7 Deriving the expression", "• Deriving the expression"),
    # Text with no symbol-font character is returned unchanged, byte for byte.
    ("Find the value of m.", "Find the value of m."),
])
def test_restore_symbol_font(text, restored):
    assert bm.restore_symbol_font(text) == restored


@pytest.mark.skipif(not CBE_BANK.exists(), reason="CBE bank not built")
def test_a_served_record_keeps_its_rho_instead_of_a_symbol_font_code_point():
    """cbe:q:Science9PS1: without ρ its options read "(A) W g (B) W / g (C) W g /
    (D) W / g" -- two of them alike, so the question cannot be answered."""
    result = bm.compose([], [real_cbe("cbe:q:Science9PS1")], [])
    assert [q["id"] for q in result.questions] == ["cbe:q:Science9PS1"]
    stem = result.questions[0]["stem"]
    assert "weight W and density ρ" in stem
    assert "(A) W ρ g (B) W ρ / g (C) W g / ρ (D) W / ρ g" in stem
    assert bm.private_use_glyph(stem) is None
    scheme = result.questions[0]["answerScheme"]
    assert scheme["metadata"]["options"]["B"] == "W ρ / g"
    assert result.repairs["symbol-font-restored"] == 1


@pytest.mark.skipif(not CBE_BANK.exists(), reason="CBE bank not built")
def test_a_private_use_glyph_the_table_does_not_cover_is_excluded():
    """cbe:q:Maths10PS2's key writes its two implication arrows in a font that is
    not Symbol (U+F0F0 is undefined there, and the same code is a Wingdings
    arrow), so nothing here can say what the character was."""
    result = bm.compose([], [real_cbe("cbe:q:Maths10PS2")], [])
    assert result.questions == []
    assert [e["reason"] for e in result.excluded] == ["private-use-glyph"]


def test_a_symbol_outside_the_printed_fields_is_repaired_too():
    """780 served SQP records carry a top-level `metadata.options` map -- a
    different field from the `answerScheme.metadata.options` the scheme holds
    -- and 313 carry `metadata.contentReference`. A stem repaired while those
    were left is the same stem/key disagreement the repair exists to prevent,
    one field further out, so the repair walks every string in the record."""
    rec = board(source="cbse_question_bank", stem="What is the density ?",
                metadata={"options": {"B": "W  / g"},
                          "contentReference": "density "},
                tags=["50"])
    out, restored, glyph = bm.repair_symbol_font(rec)
    assert restored and glyph is None
    assert out["stem"] == "What is the density ρ?"
    assert out["metadata"] == {"options": {"B": "W ρ / g"}, "contentReference": "density ρ"}
    assert out["tags"] == ["50°"]
    assert rec["metadata"]["contentReference"] == "density ", "the input is left as it was"


@pytest.mark.skipif(not CBE_BANK.exists(), reason="CBE bank not built")
def test_an_uncoverable_glyph_a_student_never_reads_does_not_cost_the_question():
    """The gate is narrower than the repair on purpose: a question is refused
    because a student or a scorer would read a hole, not because a provenance
    field carries one. `contentReference` prints nowhere."""
    rec = real_cbe("cbe:q:Science9PS1")
    rec = {**rec, "metadata": {**(rec.get("metadata") or {}),
                               "contentReference": "NCERT IX  1.3"}}
    result = bm.compose([], [rec], [])
    assert [q["id"] for q in result.questions] == ["cbe:q:Science9PS1"]


def test_a_record_already_out_of_scope_keeps_its_own_reason():
    """The glyph gate runs after `source_reason`, not before it. Placed first
    it relabelled records that were out of scope anyway: 12 of the 23 it
    excluded at 64dd21a were answer-bleed, figure-referenced or garbled-script
    as well, so the --check tally overstated this change's cost by about half
    and hid a dozen answer-bleed records behind the wrong label."""
    rec = board(source="cbse_question_bank",
                stem="From the graph given above, read the current  through "
                     "the resistor and state what it shows about the circuit.")
    result = bm.compose([], [rec], [])
    assert [e["reason"] for e in result.excluded] == ["figure-referenced"]


def test_a_glyph_is_still_the_reason_when_nothing_else_refuses_the_record():
    rec = board(source="cbse_question_bank",
                stem="State the current  through the resistor and give a "
                     "reason for your answer in terms of the circuit shown.")
    result = bm.compose([], [rec], [])
    assert [e["reason"] for e in result.excluded] == ["private-use-glyph"]


def test_a_board_record_loses_no_symbol_in_print():
    rec = board(stem="The angle subtended at the centre is 50\uf0b0. Find \uf0d0BOC in "
                     "terms of \uf061 and give a reason for your answer.")
    out, reason, repairs, _ = bm.repair_board(rec)
    assert reason is None
    assert out["stem"] == ("The angle subtended at the centre is 50°. Find ∠BOC in "
                           "terms of α and give a reason for your answer.")
    assert repairs == ["symbol-font-restored"]
    assert bm.compose([rec], [], []).repairs["symbol-font-restored"] == 1


def test_a_board_record_with_an_uncovered_glyph_is_withheld_whole():
    rec = board(stem="Ca + H2O \uf0e0 Ca(OH)2. Name the gas evolved and give a reason.")
    result = bm.compose([rec], [], [])
    assert result.questions == []
    assert [e["reason"] for e in result.excluded] == ["private-use-glyph"]
    assert result.withheld == [rec]


def test_a_board_record_already_out_of_scope_keeps_its_own_reason():
    """The board path orders the gates as the CBE/SQP path does: the glyph is
    the reason only when nothing more informative refuses the record. Filed
    first it would read "private-use-glyph" for a record no figure can be
    drawn for -- the exact mislabelling `test_a_record_already_out_of_scope_
    keeps_its_own_reason` records on the other path, and `_merge_excluded.json`
    is what decides which defects get worked next."""
    rec = board(stem="From the graph given above, read the current  through "
                     "the resistor and state what it shows about the circuit.")
    result = bm.compose([rec], [], [])
    assert [e["reason"] for e in result.excluded] == ["figure-unavailable"]
    assert result.withheld == [rec]


def test_a_glyph_in_the_withheld_key_provenance_does_not_cost_the_question():
    """`answerScheme.metadata.conflictingKeys` is provenance: the relink's copy
    of a key it removed, as it was removed, kept so the next relink compares
    the same two answers and so a person reviewing one sees the code point the
    extractor produced (question_bank._restore_scheme_symbols leaves it raw for
    that reason). No student and no scorer reads it, so a private-use character
    there is not a hole anyone would see -- the gate's own rule -- and the
    repair must not rewrite the copy either.

    46 of the 15,605 rows in answer_keys.db carry a private-use character the
    table cannot name, and a conflicting key is copied verbatim from such a
    row; 0 served records carry `conflictingKeys` today, so this bites on the
    next merge -> enrich -> merge cycle."""
    held = {"existing": {"modelAnswer": "Ca + H2O  Ca(OH)2, 30",
                         "provenance": "cbse_marking_scheme"},
            "join": {"modelAnswer": "30"}}
    rec = board()
    rec["answerScheme"]["metadata"] = dict(rec["answerScheme"]["metadata"],
                                           conflictingKeys=copy.deepcopy(held))
    fixed, reason, repairs, glyph = bm.repair_board(rec)
    assert (reason, glyph, repairs) == (None, None, [])
    assert fixed["answerScheme"]["metadata"]["conflictingKeys"] == held, (
        "the provenance copy is left exactly as the relink wrote it")
    result = bm.compose([rec], [], [])
    assert [q["id"] for q in result.questions] == [rec["id"]]


@pytest.mark.skipif(not SERVED_BANK.exists(), reason="served bank not built")
def test_no_served_record_holds_a_private_use_glyph():
    """The bank the web and the APK read: no hole where a symbol belongs.

    Two assertions, one per scope, because the repair and the gate have
    different ones. Nothing the table can name may survive ANYWHERE in a
    record -- that is what `repair_symbol_font` walks every string for, so a
    failure here always has a code path that fixes it. And nothing a student
    or a scorer reads may hold a private-use character at all: that is the
    gate's scope, and a record failing it is one the merge should have
    excluded as private-use-glyph."""
    import json

    def strings(value):
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict):
            for item in value.values():
                yield from strings(item)
        elif isinstance(value, list):
            for item in value:
                yield from strings(item)

    rows = json.loads(SERVED_BANK.read_text(encoding="utf-8"))["questions"]
    restorable = [r["id"] for r in rows
                  if any(bm.restore_symbol_font(s) != s for s in strings(r))]
    assert restorable == []
    printed = [{k: r.get(k) for k in bm._SYMBOL_PRINTED_FIELDS}
               | {"answerScheme": bm.printed_scheme(r.get("answerScheme")),
                  "passage": (r.get("metadata") or {}).get("passage")} for r in rows]
    holes = [r["id"] for r, p in zip(rows, printed)
             if bm.PRIVATE_USE.search(json.dumps(p, ensure_ascii=False))]
    assert holes == []


# ---- chapter ids a teacher sees (Task 121) -----------------------------------
#
# A CBE content code ("10A2b", "9.1.6") is not a chapter: printed in a chapter
# list it reads "10A2B", and the same chapter then appears under several ids
# (Mathematics 10 listed "Trigonometry" three times at f90f42c).

MATHS_10 = {"number-systems": "Number Systems", "algebra": "Algebra",
            "trigonometry": "Trigonometry", "mensuration": "Mensuration",
            "statistics-and-probability": "Statistics and Probability"}


def cbe_coded(i, code, **kw):
    """A CBE record tagged with nothing but its content code, as the builder
    leaves one the chapter tagger could not place."""
    return board(i, id=f"cbe:q:Maths10X{i}", source="cbse_question_bank",
                 subject="Mathematics", chapterIds=[code],
                 tags=kw.pop("tags", [code]), grade=kw.pop("grade", 10), **kw)


def test_a_content_code_the_records_name_becomes_its_syllabus_chapter():
    """"Number systems" is what CBSE calls the 10N strand on the records that
    carry a topic; the strand is the syllabus unit a teacher picks."""
    recs = [cbe_coded(1, "10N1a", tags=["Number systems", "10N1a"]),
            cbe_coded(2, "10N1c")]
    out, counts = bm.resolve_chapter_ids(recs, {("Mathematics", 10): MATHS_10})
    assert [r["chapterIds"] for r in out] == [["number-systems"], ["number-systems"]]
    assert counts == {"resolved": 2, "dropped": 0}


def test_one_chapter_is_listed_once_however_many_codes_reach_it():
    recs = [cbe_coded(1, "trigonometry", tags=["Trigonometry"]),
            cbe_coded(2, "10T1c", tags=["Trigonometry", "10T1c"]),
            cbe_coded(3, "10T2a", tags=["Trigonometry", "10T2a"])]
    out, _ = bm.resolve_chapter_ids(recs, {("Mathematics", 10): MATHS_10})
    assert {cid for r in out for cid in r["chapterIds"]} == {"trigonometry"}


def test_a_code_no_chapter_name_matches_is_dropped_not_shown():
    """Nothing here can say which class 9 chapter the "9G2b" geometry strand
    is, and a teacher must never be offered "9G2B" as a chapter."""
    rec = cbe_coded(1, "9G2b", grade=9, tags=["Geometry", "9G2b"])
    out, counts = bm.resolve_chapter_ids([rec], {("Mathematics", 9): {"circles-9": "Circles"}})
    assert out[0]["chapterIds"] == []
    assert counts == {"resolved": 0, "dropped": 1}
    assert rec["chapterIds"] == ["9G2b"], "the input records are left as they were"


def test_a_taxonomy_chapter_names_the_syllabus_chapter():
    """The topic tagger's chapter (Task 703) where the record carries no topic
    and no strand name: "science-10/acids-bases-and-salts"."""
    rec = board(source="cbse_question_bank", subject="Science", grade=10,
                chapterIds=["10.4.3"], tags=["10.4.3"],
                taxonomyChapterId="science-10/acids-bases-and-salts")
    out, counts = bm.resolve_chapter_ids(
        [rec], {("Science", 10): {"acids-bases-salts": "Acids, Bases and Salts"}},
        taxonomy_names={"science-10/acids-bases-and-salts": "Acids, Bases and Salts"})
    assert out[0]["chapterIds"] == ["acids-bases-salts"]
    assert counts == {"resolved": 1, "dropped": 0}


def test_a_chapter_the_syllabus_knows_is_left_alone():
    rec = cbe_coded(1, "algebra", tags=["Algebra"])
    out, counts = bm.resolve_chapter_ids([rec], {("Mathematics", 10): MATHS_10})
    assert out[0]["chapterIds"] == ["algebra"]
    assert counts == {"resolved": 0, "dropped": 0}


def test_a_subject_with_no_syllabus_keeps_the_ids_it_has():
    """Nothing to check against: Home Science and the SQP arts subjects have no
    syllabus file, so their ids are left exactly as they are."""
    rec = board(source="cbse_sample_paper", subject="Home Science", grade=10,
                chapterIds=["meal-planning"])
    out, counts = bm.resolve_chapter_ids([rec], {})
    assert out[0]["chapterIds"] == ["meal-planning"]
    assert counts == {"resolved": 0, "dropped": 0}


def test_a_slug_shaped_unknown_id_does_not_borrow_another_chapters_strand():
    """`coarse_code` was written for CBSE content codes and degenerates for
    anything else: coarse_code("algebra-extra") and
    coarse_code("arithmetic-progressions") are both "A". Two unrelated
    slug-shaped ids would share one strand pool, and a pool naming exactly one
    chapter resolved every id in it to that chapter -- questions filed under a
    chapter they do not belong to, with no signal. Only a content-coded id
    (`bm.CONTENT_CODE`) has a strand; anything else is dropped."""
    names_itself = cbe_coded(1, "algebra-extra", tags=["Algebra"])
    unrelated = cbe_coded(2, "arithmetic-progressions", tags=["Arithmetic Progressions"])
    out, counts = bm.resolve_chapter_ids([names_itself, unrelated],
                                         {("Mathematics", 10): MATHS_10})
    assert [r["chapterIds"] for r in out] == [["algebra"], []]
    assert counts == {"resolved": 1, "dropped": 1}


def test_a_content_coded_id_still_takes_its_strands_name():
    """The guard above must not cost the case it was built for: "10A2b" is a
    content code, so it still takes the name its strand's siblings carry."""
    recs = [cbe_coded(1, "10A1a", tags=["Algebra", "10A1a"]), cbe_coded(2, "10A2b")]
    out, counts = bm.resolve_chapter_ids(recs, {("Mathematics", 10): MATHS_10})
    assert [r["chapterIds"] for r in out] == [["algebra"], ["algebra"]]
    assert counts == {"resolved": 2, "dropped": 0}
