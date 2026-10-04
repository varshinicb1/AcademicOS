"""The generator's own rules, and the validator that enforces them.

`cbse_blueprint` decides what the paper looks like; this checks that a question
put in front of it is a question for that paper, and that a question the model
returned is one that survives being checked.

The validator tests are the ones that matter most. The schema already stops a
malformed answer arriving -- a wrong mark value will not parse. What the schema
cannot stop is a well-formed answer that is not a question: a stem that names the
text it was written from, four options where two say the same thing, a
three-mark question carrying two marking points. Those are the failures that
reach a real paper, so they get the tests.
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.corpus import cbse_blueprint as bp          # noqa: E402
from academicos.corpus import cbse_generate as cg           # noqa: E402


def _mcq_section(marks: int = 1) -> bp.Section:
    return bp.Section("A", "Objective", bp.MCQ, 4, marks)


def _sa_section(marks: int = 3) -> bp.Section:
    return bp.Section("C", "Short Answer", bp.SA, 4, marks, answer_words=45)


def _good_mcq(**over) -> dict:
    item = {"qtype": bp.MCQ, "marks": 1, "bloomLevel": "understand",
            "stem": "Meera buys 4 apples at Rs 15 each. How much does she pay?",
            "options": {"A": "Rs 45", "B": "Rs 50", "C": "Rs 60", "D": "Rs 75"},
            "correctOption": "C", "option": 1}
    item.update(over)
    return item


def _good_sa(**over) -> dict:
    item = {"qtype": bp.SA, "marks": 3, "bloomLevel": "apply",
            "stem": "A tap fills a tank in 12 minutes. Show how long 3 such taps "
                    "take, and state the method you used.",
            "modelAnswer": "Time is inversely proportional: 12/3 = 4 minutes.",
            "markingPoints": ["States the inverse relation",
                              "Divides 12 by 3", "Gives 4 minutes"],
            "option": 1}
    item.update(over)
    return item


# --------------------------------------------------------------------------- #
# the validator
# --------------------------------------------------------------------------- #

def test_a_well_formed_question_is_kept():
    assert cg.validate(_good_mcq(), _mcq_section()) is None
    assert cg.validate(_good_sa(), _sa_section()) is None


def test_marks_must_be_the_marks_the_section_prints():
    # A 3-mark question sitting in a 1-mark section is the failure a schema
    # catches and a bank would otherwise ship.
    assert cg.validate(_good_mcq(marks=3), _mcq_section(1)) == "wrong-marks"


def test_the_type_must_be_the_sections_type():
    assert cg.validate(_good_mcq(qtype=bp.SA), _mcq_section()) == "wrong-type"


def test_an_empty_or_tiny_stem_is_refused():
    assert cg.validate(_good_mcq(stem=""), _mcq_section()) == "empty-stem"
    assert cg.validate(_good_mcq(stem="Why?"), _mcq_section()) == "stem-too-short"


@pytest.mark.parametrize("tell", [
    "According to the text, what is the capital?",
    "Based on the text above, choose one.",
    "In the chapter, how many sides does it have?",
    "As an AI, I would say the answer is 4.",
])
def test_a_stem_that_names_its_own_source_is_refused(tell):
    # A student must not be able to tell the question was written by reading it.
    assert cg.validate(_good_mcq(stem=tell), _mcq_section()) == "stem-names-the-text"


def test_options_must_be_four_and_labelled_abcd():
    assert cg.validate(_good_mcq(options={"A": "1", "B": "2", "C": "3"}),
                       _mcq_section()) == "options-not-abcd"
    assert cg.validate(_good_mcq(options={"1": "x", "2": "y", "3": "z", "4": "w"}),
                       _mcq_section()) == "options-not-abcd"


def test_options_that_say_the_same_thing_are_refused():
    # The gate `mcq_shape.answerable` already exists in the repo for exactly this,
    # and was never wired into this path. Two options reading alike means the
    # question has fewer than four answers and a student can eliminate by eye.
    item = _good_mcq(options={"A": "Rs 45", "B": "Rs 45", "C": "Rs 60",
                              "D": "Rs 75"}, correctOption="A")
    assert cg.validate(item, _mcq_section()) == "options-not-answerable"


def test_an_empty_option_is_refused():
    item = _good_mcq(options={"A": "Rs 45", "B": "", "C": "Rs 60", "D": "Rs 75"})
    assert cg.validate(item, _mcq_section()) == "options-not-answerable"


def test_the_correct_option_must_name_a_real_option():
    assert cg.validate(_good_mcq(correctOption="E"), _mcq_section()) == "no-correct-option"
    # An option that is only whitespace is caught a step earlier, as an option
    # that is not there at all -- which is the more useful reason to report.
    item = _good_mcq(options={"A": "   ", "B": "Rs 50", "C": "Rs 60", "D": "Rs 75"},
                     correctOption="A")
    assert cg.validate(item, _mcq_section()) == "options-not-answerable"


def test_a_written_question_needs_a_model_answer():
    assert cg.validate(_good_sa(modelAnswer=""), _sa_section(3)) == "no-model-answer"
    assert cg.validate(_good_sa(markingPoints=[]), _sa_section(3)) == \
        "no-marking-points"
    # More mark-bearing steps than marks is over-specified, not a finer scheme.
    assert cg.validate(_good_sa(markingPoints=["a", "b", "c", "d"]),
                       _sa_section(3)) == "too-many-marking-points"
    # Fewer is fine: a 3-mark answer can be scored in two steps.
    assert cg.validate(_good_sa(markingPoints=["a", "b"]), _sa_section(3)) is None


def test_a_case_study_needs_a_passage_worth_reading():
    section = bp.Section("E", "Case Based", bp.CASE, 3, 4, answer_words=50)
    item = {"qtype": bp.CASE, "marks": 4, "bloomLevel": "apply",
            "stem": "Answer the questions that follow.",
            "passage": "Too short.", "modelAnswer": "x", "option": 1}
    assert cg.validate(item, section) == "case-passage-too-short"
    item["passage"] = (
        "Ravi cycles to school every morning. He covers 3 km in 20 minutes, "
        "and the same road home in 15 minutes, because he rides against a "
        "wind on the way back. His father thinks he should leave ten minutes "
        "earlier, which would mean starting at a quarter to eight. Ravi says "
        "he would rather turn back earlier and meet his friends near the "
        "bridge, where they usually stop before going in.")
    assert len(item["passage"].split()) >= 60
    assert cg.validate(item, section) is None


def test_an_unknown_bloom_level_is_refused():
    assert cg.validate(_good_mcq(bloomLevel="creative"), _mcq_section()) == "bad-bloom"


# --------------------------------------------------------------------------- #
# the quality failures a live run actually produced
# --------------------------------------------------------------------------- #

def test_distractors_that_are_the_answer_walked_by_one_are_refused():
    # From a live Workers AI run on the Fundamental Theorem of Arithmetic: the
    # factorisation of 91 came back as 7x13, 7x14, 7x15, 7x16. Four distinct
    # options, so the shape gate passes, and a student who cannot factorise
    # anything can still pick one.
    item = _good_mcq(
        stem="Which of these is the prime factorisation of 91?",
        options={"A": "7 x 13", "B": "7 x 14", "C": "7 x 15", "D": "7 x 16"},
        correctOption="A")
    assert cg.validate(item, _mcq_section()) == "distractor-ladder"


def test_a_ladder_of_two_is_still_a_ladder():
    item = _good_mcq(
        stem="Which of these is the prime factorisation of 91?",
        options={"A": "7 x 13", "B": "7 x 12", "C": "5 x 17", "D": "11 x 8"},
        correctOption="A")
    # Only one distractor sits next to the answer, so this is allowed: the other
    # two are wrong for a different reason.
    assert cg.validate(item, _mcq_section()) is None
    item["options"] = {"A": "7 x 13", "B": "7 x 14", "C": "7 x 15", "D": "7 x 16"}
    assert cg.validate(item, _mcq_section()) == "distractor-ladder"


def test_a_large_jump_is_not_a_ladder():
    # 7x13 against 7x40 is a wrong answer, not a giveaway.
    item = _good_mcq(
        stem="Which of these is the prime factorisation of 91?",
        options={"A": "7 x 13", "B": "7 x 40", "C": "9 x 11", "D": "13 x 7"},
        correctOption="A")
    assert cg.validate(item, _mcq_section()) is None


def test_a_stem_that_trails_off_is_not_a_question():
    # Also from the live run: "The prime factorisation of the number 12 is".
    assert cg.validate(_good_mcq(stem="The prime factorisation of 12 is"),
                       _mcq_section()) == "stem-is-not-a-question"


def test_a_stem_that_asks_for_a_form_is_not_a_question():
    assert cg.validate(_good_mcq(stem="State the prime factorisation of 12."),
                       _mcq_section()) == "stem-is-not-a-question"
    assert cg.validate(_good_mcq(stem="Write the factors of 12 in order."),
                       _mcq_section()) == "stem-is-not-a-question"


def test_a_real_question_is_kept():
    assert cg.validate(
        _good_mcq(stem="Which of these is the prime factorisation of 91?"),
        _mcq_section()) is None


def test_a_key_that_always_lands_on_a_is_reported():
    # The live run put the key at A in both of its questions, despite being told
    # not to. A single A is not a fault; a run of them is a paper a student can
    # score in without reading the questions.
    def _rec(key: str) -> dict:
        return {"answerScheme": {"metadata": {"correctOption": key}}}

    skewed = cg.audit_key_distribution([_rec("A")] * 7 + [_rec("B"), _rec("C")])
    assert skewed["total"] == 9
    assert skewed["largest"] == "A"
    assert skewed["biased"] is True
    assert round(skewed["share"]["A"], 2) == 0.78

    even = cg.audit_key_distribution([_rec(k) for k in "ABCABCABC"])
    assert even["biased"] is False
    assert even["largest"] == "A"


def test_a_run_with_few_mcqs_is_not_called_biased():
    # Two questions is not a pattern.
    assert cg.audit_key_distribution(
        [{"answerScheme": {"metadata": {"correctOption": "A"}}}] * 2
    )["biased"] is False


def test_key_audit_ignores_questions_without_options():
    written = {"answerScheme": {"metadata": {}}}
    assert cg.audit_key_distribution([written, written])["total"] == 0


def test_the_live_run_items_are_now_all_refused():
    # Every one of the three faults from the real run, together, so a regression
    # in any of the three is caught. Which of two reasons is reported first is not
    # the point; that the item is refused is.
    ladder = _good_mcq(stem="The prime factorisation of the number 91 is",
                       options={"A": "7 x 13", "B": "7 x 14", "C": "7 x 15",
                                "D": "7 x 16"}, correctOption="A")
    assert cg.validate(ladder, _mcq_section()) in {
        "distractor-ladder", "stem-is-not-a-question"}

    trailing = _good_mcq(stem="The prime factorisation of the number 12 is")
    assert cg.validate(trailing, _mcq_section()) == "stem-is-not-a-question"

    # The same item with a well-formed stem and honest distractors survives, so
    # the checks are not simply refusing everything.
    good = _good_mcq(stem="Which of these is the prime factorisation of 12?",
                     options={"A": "2 x 2 x 3", "B": "2 x 3 x 5",
                              "C": "4 x 3 x 1", "D": "2 x 2 x 2"},
                     correctOption="A")
    assert cg.validate(good, _mcq_section()) is None


def _gen_script(name: str):
    """Load `scripts/gen_cbse_chapter.py` for its grouping helpers.

    Registered in `sys.modules` before it runs, because it imports dataclasses
    that look themselves up there.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        name, ROOT / "scripts" / "gen_cbse_chapter.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.modules.pop(name, None)
    return mod


def test_a_call_never_mixes_sections():
    # The schema pins the section's type and marks, so a call cannot hold items
    # from two sections. Grouping is the cost lever and this is its hard limit.
    mod = _gen_script("gen_chapter")
    blueprint = bp.for_paper("Mathematics", 10)
    plan = []
    for section in blueprint.sections:
        for _ in range(section.count):
            plan.append((section, "topic"))
    for group in mod.group_plan(plan, per_call=3):
        keys = {(s.key, s.qtype, s.marks) for s, _ in group}
        assert len(keys) == 1, f"a call mixes sections: {keys}"
        assert len(group) <= 3


def test_grouping_collapses_the_calls_without_losing_items():
    # Nine one-question calls pay for the chapter nine times; grouping is the
    # largest cost lever in the pipeline. A cheaper bank must not be a shorter one.
    mod = _gen_script("gen_chapter2")
    plan = [(_sa_section(3), "t")] * 9
    assert len(mod.group_plan(plan, per_call=3)) == 3
    assert len(mod.group_plan(plan, per_call=1)) == 9
    flat = [item for group in mod.group_plan(plan, per_call=3) for item in group]
    assert len(flat) == 9


def test_a_group_keeps_more_than_one_topic():
    # A model writing the third question can see the first two, which is what
    # stops it restating the same sentence -- the fault the first real run showed.
    mod = _gen_script("gen_chapter3")
    section = _mcq_section(1)
    topics = ["Addition", "Subtraction", "Fractions", "Shapes"]
    plan = [(section, topics[i % len(topics)]) for i in range(6)]
    groups = mod.group_plan(plan, per_call=3)
    assert len(groups[0]) == 3
    assert len({topic for _, topic in groups[0]}) > 1


def _mcq_record(correct: str = "C", record_id: str = "q") -> dict:
    """A stored MCQ, the shape `rebalance_keys` actually works on."""
    section = bp.for_paper("Mathematics", 10).sections[0]
    record = cg.to_record(_good_mmq(correctOption=correct), section, _chapter(), "t",
                          chapter_id="c", topic_id="", model="m")
    record["id"] = record_id
    return record


def _good_mmq(**over) -> dict:
    item = _good_mcq(**over)
    item.pop("option", None)
    return item


def test_a_run_where_the_key_is_never_a_gets_leveled():
    # A free-tier run came back with the key on B 6 times, C 38, D 34 and never on
    # A. Every one of those 78 questions is individually well formed; the fault is
    # only visible in aggregate, and a student who spots it scores full marks
    # without reading anything.
    records = [_mcq_record("C", f"q{i}") for i in range(40)]
    audit = cg.audit_key_distribution(records)
    assert audit["biased"] is True
    assert "A" not in audit["counts"]

    report = cg.rebalance_keys(records)
    assert report["rotated"] > 0
    after = cg.audit_key_distribution(records)
    assert after["biased"] is False
    assert "A" in after["counts"]


def test_rebalancing_keeps_the_options_and_the_answer_unchanged():
    # Only the letters may move. The stem, the four option texts, the distractors
    # and the answer itself have to survive, or a rebalance would be editing
    # questions rather than levelling a paper.
    records = [_mcq_record("D", "only")] + [_mcq_record("D", f"x{i}")
                                            for i in range(10)]
    target = records[0]
    before_options = dict(target["answerScheme"]["metadata"]["options"])
    before_answer = target["answerScheme"]["modelAnswer"]
    before_stem = target["stem"]
    cg.rebalance_keys(records)
    assert target["stem"] == before_stem
    assert sorted(target["answerScheme"]["metadata"]["options"]) == ["A", "B", "C", "D"]
    assert sorted(target["answerScheme"]["metadata"]["options"].values()) == \
        sorted(before_options.values())
    assert target["answerScheme"]["modelAnswer"] == before_answer


def test_rebalancing_does_not_drop_records_with_colliding_ids():
    # It once keyed its work by id, which silently collapsed 78 records to 37
    # because two sections of a chapter both return position 1 from the model. A
    # rebalance that discards half the bank is worse than the bias it was fixing.
    records = [_mcq_record("C", "same-id") for _ in range(8)]
    before = len(records)
    report = cg.rebalance_keys(records)
    assert report["mcqs"] == before
    assert all(r["answerScheme"]["metadata"].get("correctOption") in "ABCD"
               for r in records)


def test_rebalancing_nothing_is_a_no_op():
    assert cg.rebalance_keys([]) == {"mcqs": 0, "rotated": 0}
    record = _mcq_record()
    record["answerScheme"]["metadata"].pop("correctOption", None)
    assert cg.rebalance_keys([record]) == {"mcqs": 0, "rotated": 0}


def test_a_repeat_of_a_question_the_bank_already_has_is_found():
    # Generating a question the bank already holds spends a daily neuron against a
    # quota the whole run is rationed by, and dilutes the one thing a paid bank is
    # for. The existing corpora are ~9,300 questions, so this is not theoretical.
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "collect_dup", ROOT / "scripts" / "collect_ai_cbse.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["collect_dup"] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception:                              # noqa: BLE001
        pytest.skip("the collector needs the corpus to import")

    existing = [mod._tokens("Find the HCF of 12, 15 and 20")]
    # Same question with a different opening word.
    assert mod._is_duplicate(
        mod._tokens("The HCF of 12, 15 and 20"), existing, 0.72)
    # Same numbers, different question.
    assert not mod._is_duplicate(
        mod._tokens("Find the LCM of 12, 15 and 20"), existing, 0.72)
    # Unrelated.
    assert not mod._is_duplicate(
        mod._tokens("Describe the causes of the French Revolution"),
        existing, 0.72)


def test_the_dedup_ignores_punctuation_and_case():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "collect_dup2", ROOT / "scripts" / "collect_ai_cbse.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["collect_dup2"] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception:                              # noqa: BLE001
        pytest.skip("the collector needs the corpus to import")
    a = mod._tokens("What is the HCF of 6, 72 and 120?")
    b = mod._tokens("what is the hcf of 6 72 and 120")
    assert a == b
    # Stopwords carry no meaning, so they cannot create a false match.
    assert mod._tokens("find the value of x") == mod._tokens("value of x")


def test_the_prompt_asks_for_the_number_of_questions_wanted():
    # The count reaches the model, or grouping saves calls and returns one
    # question anyway.
    section = bp.for_paper("Mathematics", 10).sections[0]
    _, _, three = cg.build_prompt(_chapter(), section, "", count=3,
                                  bank_subject="Mathematics")
    assert "Write 3 question" in three
    _, _, one = cg.build_prompt(_chapter(), section, "", count=1,
                                bank_subject="Mathematics")
    assert "Write 1 question" in one


def test_the_written_sections_cap_the_model_answer_length():
    # 74% of a Gemini call is output tokens, measured, so an uncapped worked
    # solution is where the money goes. A mark scheme is not an essay.
    for section in (_sa_section(3),
                    bp.Section("D", "Long Answer", bp.LA, 4, 5, answer_words=75),
                    bp.Section("E", "Case Based", bp.CASE, 3, 4, answer_words=50)):
        system, _, _ = cg.build_prompt(_chapter(), section, "", count=1,
                                       bank_subject="Mathematics")
        assert "not an essay" in system or "in total" in system, section.key


def test_the_cheap_model_is_kept_away_from_the_case_based_section():
    # flash-lite is five times cheaper on output, which is worth having where the
    # whole output is four options -- and not on a case-based passage.
    mod = _gen_script("gen_chapter4")
    lite = mod.model_for(bp.Section("A", "Objective", bp.MCQ, 4, 1), True, "gemini")
    strong = mod.model_for(bp.Section("E", "Case Based", bp.CASE, 3, 4), True,
                           "gemini")
    assert lite == mod.GEMINI_LITE
    assert strong == mod.GEMINI_MODEL
    # The workers provider has no cheap model worth using, so it is one model.
    assert mod.model_for(bp.Section("A", "Objective", bp.MCQ, 4, 1), True,
                         "workers") == mod.WORKERS_MODEL


def test_cached_input_is_priced_at_a_tenth_of_fresh():
    # Caching is only worth having if it is priced in. If the rates ever converge,
    # this fails rather than quietly reporting a saving that is not there.
    assert mod_rate("GEMINI_CACHED_PER_M") * 10 == pytest.approx(
        mod_rate("GEMINI_IN_PER_M"), rel=0.01)


def mod_rate(name: str) -> float:
    return _gen_script("gen_chapter_rates").__dict__[name]


def test_a_cached_read_costs_less_than_a_fresh_one():
    mod = _gen_script("gen_chapter5")
    fresh = mod._cost_of({"prompt_tokens": 10_000, "completion_tokens": 100})
    cached = mod._cost_of({"prompt_tokens": 10_000, "cached_tokens": 10_000,
                           "completion_tokens": 100})
    assert cached < fresh / 5
    # The strong model costs more than the cheap one on the same call.
    lite = mod._cost_of({"prompt_tokens": 10_000, "completion_tokens": 100},
                        mod.GEMINI_LITE)
    assert lite < fresh


# --------------------------------------------------------------------------- #
# the second live run: numbering, multi-part stems, and a false premise
# --------------------------------------------------------------------------- #

def test_a_stem_carrying_the_papers_own_number_is_cleaned():
    # From a real run on the Fundamental Theorem of Arithmetic:
    # "1. Find the HCF of 6, 72 and 120 using their prime factors."
    for stem, want in [
        ("1. Find the HCF of 6, 72 and 120.", "Find the HCF of 6, 72 and 120."),
        ("Q3. State the prime factors of 15015.",
         "State the prime factors of 15015."),
        ("I. Is 5 - sqrt(3) rational?", "Is 5 - sqrt(3) rational?"),
        ("(ii) Verify the identity.", "Verify the identity."),
        ("3) Find the LCM.", "Find the LCM."),
    ]:
        assert cg.strip_question_number(stem) == want, stem


def test_a_stem_without_a_number_is_left_alone():
    for stem in ("Find the HCF of 6, 72 and 120.",
                 "Which of these is the prime factorisation of 12?",
                 "A student walks 3 km. How long does it take?"):
        assert cg.strip_question_number(stem) == stem


def test_a_stem_that_is_really_several_questions_is_refused():
    # From a real run: "I. Is 5 - sqrt(3) rational or irrational? II. What property
    # of irrational numbers is being used in this proof?" -- offered as one 2-mark
    # item. A bank entry is one question; the paper numbers them.
    section = bp.Section("B", "Very Short Answer", bp.VSA, 4, 2)
    item = {"qtype": bp.VSA, "marks": 2, "bloomLevel": "apply",
            "stem": "I. Is 5 - sqrt(3) rational or irrational? II. What property "
                    "of irrational numbers is used here?",
            "modelAnswer": "Irrational; the difference of a rational and an "
                           "irrational is irrational.",
            "markingPoints": ["States it is irrational",
                              "Names the property"], "option": 1}
    assert cg.validate(item, section) == "stem-is-several-questions"


def test_a_stem_asking_to_verify_something_false_is_refused():
    # From a real run: "Find the LCM and HCF of 140 and 156 ... and verify that
    # LCM x HCF = product of the two numbers." That identity only holds for coprime
    # pairs, so it is false for 140 and 156. The model computed it correctly and
    # said so -- and the question is still unaskable, because the student is told to
    # prove something that is not so.
    item = _good_sa(
        stem="Find the LCM and HCF of 140 and 156, and verify that "
             "LCM x HCF equals the product of the two numbers.",
        modelAnswer="LCM = 16380, HCF = 4, so LCM x HCF = 65520, but the product "
                    "140 x 156 = 21840. The two are not equal.")
    assert cg.validate(item, _sa_section(3)) == "premise-not-supported"


def test_a_true_statement_to_verify_is_kept():
    # The same wording, on a pair the identity does hold for, must survive.
    item = _good_sa(
        stem="Find the LCM and HCF of 12 and 15, and verify that LCM x HCF "
             "equals the product of the two numbers.",
        modelAnswer="12 = 2^2 x 3, 15 = 3 x 5. HCF = 3, LCM = 60. "
                    "LCM x HCF = 180 = 12 x 15, therefore as required.")
    assert cg.validate(item, _sa_section(3)) is None


def test_a_question_that_only_asks_is_not_caught_by_the_premise_check():
    item = _good_sa(stem="Find the HCF of 140 and 156.",
                    modelAnswer="HCF = 4.")
    assert cg.validate(item, _sa_section(3)) is None


def test_a_record_does_not_carry_the_papers_number():
    section = bp.Section("B", "Very Short Answer", bp.VSA, 4, 2)
    item = {"qtype": bp.VSA, "marks": 2, "bloomLevel": "apply",
            "stem": "1. Find the HCF of 6, 72 and 120 using their prime factors.",
            "modelAnswer": "6",
            "markingPoints": ["Prime factorisation", "HCF is 6"], "option": 1}
    record = cg.to_record(item, section, _chapter(), "t", chapter_id="c",
                          topic_id="", model="m")
    assert record["stem"] == "Find the HCF of 6, 72 and 120 using their prime factors."


# --------------------------------------------------------------------------- #
# the schema
# --------------------------------------------------------------------------- #

def test_the_schema_pins_the_marks_and_the_type():
    # The point of the schema: the model's answer is checked against the
    # blueprint before it is even parsed, so a wrong-mark question cannot be
    # produced at all rather than being produced and caught.
    #
    # The marks value travels as a *string* enum, not `const` and not an integer
    # enum. Cloudflare Workers AI accepts `const`; Gemini rejects it. Cloudflare
    # accepts an integer enum; Gemini rejects that with "(TYPE_STRING), 4" -- it
    # will not put a number in an enum at all. A string enum is the form both hold.
    schema = cg._schema(_sa_section(3), 2)
    item = schema["properties"]["questions"]["items"]
    assert item["properties"]["marks"]["enum"] == ["3"]
    assert item["properties"]["marks"]["type"] == "string"
    assert "const" not in item["properties"]["marks"]
    assert item["properties"]["qtype"]["enum"] == [bp.SA]
    assert item["required"][:2] == ["qtype", "marks"]


def test_marks_are_compared_as_a_number_however_they_arrive():
    # The schema says "3"; the model may hand back "3" or 3 depending on provider.
    for marks in ("3", 3, " 3 "):
        assert cg.validate(_good_sa(marks=marks), _sa_section(3)) is None
    for marks in ("4", 4, "", None, "three"):
        assert cg.validate(_good_sa(marks=marks), _sa_section(3)) == "wrong-marks"


def test_parse_item_turns_the_string_marks_back_into_a_number():
    assert cg.parse_item({"marks": "4"})["marks"] == 4
    assert cg.parse_item({"marks": 4})["marks"] == 4
    # Nonsense is left as None so `validate` reports `wrong-marks` rather than
    # raising on int().
    assert cg.parse_item({"marks": "four"})["marks"] is None


def test_the_schema_uses_no_json_schema_key_either_provider_rejects():
    # The shared subset only. `minItems`/`maxItems` are Workers AI only and
    # `const` is Workers AI only, so a schema using either stops working the moment
    # the provider is switched. Caught here rather than by a 400 in production.
    allowed = {"type", "enum", "properties", "required", "items", "description"}
    for section in (_mcq_section(1), _sa_section(3),
                    bp.Section("E", "Case Based", bp.CASE, 3, 4)):
        schema = cg._schema(section, 2)

        def walk(node):
            assert set(node) <= allowed, set(node) - allowed
            for prop in (node.get("properties") or {}).values():
                walk(prop)
            if isinstance(node.get("items"), dict):
                walk(node["items"])

        walk(schema)
        # And every enum is a list of strings, which is the only kind both take.
        def walk_enums(node):
            for value in (node.get("enum") or []):
                assert isinstance(value, str), value
            for prop in (node.get("properties") or {}).values():
                walk_enums(prop)
            if isinstance(node.get("items"), dict):
                walk_enums(node["items"])

        walk_enums(schema)


def test_the_schema_only_asks_for_options_where_the_type_has_them():
    mcq = cg._schema(_mcq_section(1), 3)["properties"]["questions"]["items"]
    sa = cg._schema(_sa_section(3), 3)["properties"]["questions"]["items"]
    assert "options" in mcq["properties"] and "correctOption" in mcq["properties"]
    assert "options" not in sa["properties"]
    assert "markingPoints" not in mcq["properties"]


def test_a_marking_scheme_must_be_worth_the_marks():
    # A scheme is worth the section's marks; how many points express that is the
    # board's business. An earlier version required one point per mark and refused
    # 12 of 27 completions on one chapter, because a 5-mark answer scored in three
    # steps -- "2 for the factorisation, 2 for the product, 1 for the conclusion" --
    # is how CBSE writes a 5-mark answer.
    section = bp.Section("D", "Long Answer", bp.LA, 3, 5)
    three_points = {"qtype": bp.LA, "marks": 5, "bloomLevel": "apply",
                    "stem": "Show that 7 - sqrt(5) is irrational.",
                    "modelAnswer": "A contradiction.", "option": 1,
                    "markingPoints": ["Assume the contrary",
                                      "Derive a contradiction",
                                      "Conclude"]}
    assert cg.validate(three_points, section) is None
    record = cg.to_record(three_points, section, _chapter(), "t", chapter_id="c",
                          topic_id="", model="m")
    points = record["answerScheme"]["markingPoints"]
    assert sum(p["marks"] for p in points) == 5
    assert record["answerScheme"]["totalMarks"] == 5


def test_a_scheme_with_no_points_is_refused():
    section = bp.Section("D", "Long Answer", bp.LA, 3, 5)
    item = {"qtype": bp.LA, "marks": 5, "bloomLevel": "apply",
            "stem": "Show that 7 - sqrt(5) is irrational.",
            "modelAnswer": "A contradiction.", "markingPoints": [], "option": 1}
    assert cg.validate(item, section) == "no-marking-points"


def test_a_padded_scheme_is_refused():
    # A scheme with many more points than marks is padding, not a mark scheme.
    section = bp.Section("D", "Long Answer", bp.LA, 3, 5)
    item = {"qtype": bp.LA, "marks": 5, "bloomLevel": "apply",
            "stem": "Show that 7 - sqrt(5) is irrational.",
            "modelAnswer": "x", "option": 1,
            "markingPoints": [f"step {i}" for i in range(11)]}
    assert cg.validate(item, section) == "too-many-marking-points"


def test_every_section_in_every_blueprint_produces_a_scheme_worth_its_marks():
    # The invariant the corrected rule exists to protect: a stored question is
    # always worth exactly the marks the paper prints for it, whatever shape the
    # model's marking points came back in.
    for subject in ("Mathematics", "Science", "Social Science", "English", "Hindi"):
        for grade in (5, 8, 10):
            for section in bp.for_paper(subject, grade).sections:
                if section.qtype not in (bp.VSA, bp.SA, bp.LA):
                    continue
                for count in (1, 2, 3, 5, 7):
                    points = cg._marking_points([f"p{i}" for i in range(count)],
                                                section.marks)
                    assert sum(p["marks"] for p in points) == section.marks, (
                        subject, grade, section.key, count)
                    assert all(p["marks"] >= 1 for p in points)


# --------------------------------------------------------------------------- #
# the prompt
# --------------------------------------------------------------------------- #

def _chapter(language: str = "en", grade: int = 10) -> cg.Chapter:
    return cg.Chapter(
        book_code="jemh1", subject="Mathematics", grade=grade, language=language,
        number=1, title="Real Numbers",
        pages=tuple((p, line) for p in (1, 2, 3) for line in
                    (f"page {p} line {i}" for i in range(40))))


def test_the_prompt_states_the_paper_the_section_belongs_to():
    section = bp.for_paper("Mathematics", 10).sections[0]
    system, _, _ = cg.build_prompt(_chapter(), section, "", count=1,
                                   bank_subject="Mathematics")
    assert "Section A" in system
    assert "80 marks" in system
    assert "exactly 1 mark" in system


def test_the_prompt_names_the_language_and_not_the_other_one():
    section = bp.for_paper("Mathematics", 10).sections[0]
    english, _, _ = cg.build_prompt(_chapter("en"), section, "", count=1,
                                    bank_subject="Mathematics")
    hindi, _, _ = cg.build_prompt(_chapter("hi"), section, "", count=1,
                                  bank_subject="Mathematics")
    assert "in English" in english
    assert "in Hindi" in hindi
    # An English-medium paper must not be told to print Devanagari digits: that
    # is a marking-scheme error, not a style choice.
    assert "Latin numerals" in english
    assert "Devanagari numerals" in hindi


def test_the_prompt_forbids_naming_the_text():
    section = bp.for_paper("Mathematics", 10).sections[0]
    system, _, _ = cg.build_prompt(_chapter(), section, "", count=1,
                                   bank_subject="Mathematics")
    assert "Never mention the chapter" in system
    assert "Use only what the chapter text" in system


def test_the_user_text_carries_the_chapter_and_its_pages():
    section = bp.for_paper("Mathematics", 10).sections[0]
    _, _, user = cg.build_prompt(_chapter(), section, "", count=1,
                                 bank_subject="Mathematics")
    assert "jemh1" in user
    assert "chapter text" in user
    assert "page" in user


# --------------------------------------------------------------------------- #
# the topic window
# --------------------------------------------------------------------------- #

def _window_chapter() -> cg.Chapter:
    lines = ([("Real Numbers", )] if False else [])
    pages = []
    for page, heading in ((1, "Real Numbers"), (1, "Introduction"),
                          (1, "A prime number has two factors."),
                          (2, "The Fundamental Theorem of Arithmetic"),
                          (2, "Every integer greater than one can be written."),
                          (2, "This is unique."),
                          (3, "Revisiting Irrational Numbers"),
                          (3, "The square root of two is irrational.")):
        pages.append((page, heading))
    return cg.Chapter(book_code="jemh1", subject="Mathematics", grade=10,
                      language="en", number=1, title="Real Numbers",
                      pages=tuple(pages))


def test_a_topic_window_stops_at_the_next_topic():
    chapter = _window_chapter()
    topics = ["Introduction", "The Fundamental Theorem of Arithmetic",
              "Revisiting Irrational Numbers"]
    window = chapter.topic_window("The Fundamental Theorem of Arithmetic", topics)
    texts = [line for _, line in window]
    assert texts[0] == "The Fundamental Theorem of Arithmetic"
    assert "Every integer greater than one can be written." in texts
    # The next topic's heading closes the window, and its body is not in it.
    assert "Revisiting Irrational Numbers" not in texts
    assert "The square root of two is irrational." not in texts


def test_the_last_topic_runs_to_the_end_of_the_chapter():
    chapter = _window_chapter()
    topics = ["Introduction", "The Fundamental Theorem of Arithmetic",
              "Revisiting Irrational Numbers"]
    window = chapter.topic_window("Revisiting Irrational Numbers", topics)
    assert "The square root of two is irrational." in [line for _, line in window]


def test_a_topic_that_is_not_in_the_text_falls_back_to_the_whole_chapter():
    # Better a wide window than a wrong narrow one: the model still gets the
    # chapter, and the record says the topic was not located.
    chapter = _window_chapter()
    window = chapter.topic_window("A Heading This Chapter Does Not Have",
                                  ["Introduction"])
    assert len(window) == len(chapter.pages)


def test_no_topic_means_the_whole_chapter():
    chapter = _window_chapter()
    assert len(chapter.topic_window("", ["Introduction"])) == len(chapter.pages)


# --------------------------------------------------------------------------- #
# the record
# --------------------------------------------------------------------------- #

def test_a_record_is_marked_generated_and_carries_its_provenance():
    section = bp.for_paper("Mathematics", 10).sections[0]
    record = cg.to_record(_good_mcq(), section, _chapter(), "Real Numbers",
                          chapter_id="mathematics-10/real-numbers",
                          topic_id="t-1", model="@cf/test")
    # Nothing generated may ever read as lifted from a board paper or a book.
    assert record["source"] == "ai_generated"
    assert record["provenance"]["method"] == "cbse-blueprint-generation"
    assert record["provenance"]["model"] == "@cf/test"
    assert record["provenance"]["section"] == "A Objective"
    assert record["provenance"]["pages"]
    assert record["chapterIds"] == ["mathematics-10/real-numbers"]
    assert record["taxonomyTopicId"] == "t-1"


def test_an_mcq_record_prints_its_options_from_the_stem_and_keeps_the_key_out_of_it():
    # The paper's printer (pdf.split_stem_and_options) and the merge's MCQ gate read the
    # options out of the stem, as every served board question carries them. Options held
    # only in the answer scheme print as a question with no choices. The scheme keeps
    # them too, with the key; the stem never says which one is right.
    from academicos.assessment.pdf import split_stem_and_options
    section = bp.for_paper("Mathematics", 10).sections[0]
    record = cg.to_record(_good_mcq(), section, _chapter(), "t",
                          chapter_id="c", topic_id="", model="m")
    meta = record["answerScheme"]["metadata"]
    assert meta["options"]["C"] == "Rs 60"
    assert meta["correctOption"] == "C"
    head, options = split_stem_and_options(record["stem"])
    assert head == "Meera buys 4 apples at Rs 15 each. How much does she pay?"
    assert options == ["Rs 45", "Rs 50", "Rs 60", "Rs 75"]
    assert record["stem"].count("(A)") == 1


def test_a_case_record_prints_its_passage_in_the_stem():
    section = bp.Section("E", "Case Based", bp.CASE, 2, 4)
    item = {"qtype": bp.CASE, "marks": 4, "bloomLevel": "apply", "option": 1,
            "passage": "A village digs a well and finds four layers of soil.",
            "stem": "(a) Name the top layer. (b) Why is the lowest layer called bedrock?",
            "modelAnswer": "(a) Top soil. (b) It is unweathered parent rock."}
    record = cg.to_record(item, section, _chapter(), "t", chapter_id="c", topic_id="", model="m")
    assert record["stem"].startswith("A village digs a well and finds four layers of soil.")
    assert record["stem"].endswith("called bedrock?")


def test_a_record_names_each_page_once():
    section = bp.for_paper("Mathematics", 10).sections[0]
    record = cg.to_record(_good_mcq(), section, _chapter(), "t",
                          chapter_id="c", topic_id="", model="m")
    assert record["provenance"]["pages"] == [1, 2, 3]


def test_an_mcq_records_its_model_answer_as_the_correct_option():
    # Every consumer that renders `modelAnswer` -- the answer view, the export,
    # the marking screen -- would otherwise show nothing for an objective
    # question, with the key sitting unread in the metadata.
    section = bp.for_paper("Mathematics", 10).sections[0]
    record = cg.to_record(_good_mcq(), section, _chapter(), "t",
                          chapter_id="c", topic_id="", model="m")
    assert record["answerScheme"]["modelAnswer"] == "Rs 60"


def test_a_written_record_carries_one_marking_point_per_mark():
    section = bp.Section("C", "Short Answer", bp.SA, 4, 3, answer_words=45)
    record = cg.to_record(_good_sa(), section, _chapter(), "t",
                          chapter_id="c", topic_id="", model="m")
    points = record["answerScheme"]["markingPoints"]
    assert len(points) == 3
    assert sum(p["marks"] for p in points) == 3
    assert record["marks"] == 3
    assert record["answerScheme"]["totalMarks"] == 3


def test_the_id_is_unique_per_section_and_option():
    section = bp.for_paper("Mathematics", 10).sections[0]
    a = cg.to_record(_good_mcq(option=1), section, _chapter(), "t",
                     chapter_id="c", topic_id="", model="m")
    b = cg.to_record(_good_mcq(option=2), section, _chapter(), "t",
                     chapter_id="c", topic_id="", model="m")
    assert a["id"] != b["id"]
    assert a["id"].startswith("ai:cbse:jemh1:01:A")


# --------------------------------------------------------------------------- #
# the prompt-folder bridge and the groundedness check (a model run elsewhere,
# e.g. an opencode session, answers files; the same validator judges them)
# --------------------------------------------------------------------------- #
CHAPTER_TEXT = (
    "Chapter 1: Development\n"
    "Haryana has a per capita income of Rs 264,000 a year. Kerala has a per capita\n"
    "income of Rs 175,000. In Kerala the infant mortality rate is 12 per 1,000 live births.\n"
)


def _grounded_item(**over):
    item = dict(stem="Which state has an infant mortality rate of 12 per 1,000 live births?",
                options={"A": "Haryana", "B": "Kerala", "C": "Bihar", "D": "Punjab"},
                correctOption="B", modelAnswer="Kerala",
                evidence=["In Kerala the infant mortality rate is 12 per 1,000 live births."])
    item.update(over)
    return item


def test_a_question_quoting_the_text_is_grounded():
    mod = _gen_script("gen_chapter_grounded")
    assert mod.ungrounded(_grounded_item(), CHAPTER_TEXT) is None


def test_a_question_with_no_evidence_is_refused():
    mod = _gen_script("gen_chapter_noevidence")
    assert mod.ungrounded(_grounded_item(evidence=[]), CHAPTER_TEXT) == "no-evidence"
    assert mod.ungrounded({k: v for k, v in _grounded_item().items() if k != "evidence"},
                          CHAPTER_TEXT) == "no-evidence"


def test_a_quote_that_is_not_in_the_text_is_refused():
    # The model "quotes" a sentence the chapter never printed.
    mod = _gen_script("gen_chapter_badquote")
    item = _grounded_item(evidence=["Kerala has the lowest infant mortality in India."])
    assert mod.ungrounded(item, CHAPTER_TEXT) == "evidence-not-in-text"


def test_a_quote_survives_a_line_wrap_and_a_change_of_case():
    mod = _gen_script("gen_chapter_wrap")
    item = _grounded_item(evidence=["HARYANA has a per capita income of Rs 264,000 a year."])
    assert mod.ungrounded(item, CHAPTER_TEXT) is None
    wrapped = _grounded_item(evidence=["Kerala has a per capita income of Rs 175,000."])
    assert mod.ungrounded(wrapped, CHAPTER_TEXT) is None


def test_an_invented_figure_is_refused_even_with_a_real_quote():
    # A true-looking statistic from memory, attached to a real quote.
    mod = _gen_script("gen_chapter_figure")
    item = _grounded_item(stem="Kerala's infant mortality rate was recorded in 2019. "
                               "Which state is this?")
    assert mod.ungrounded(item, CHAPTER_TEXT) == "figure-not-in-text:2019"
    rate_in_stem = _grounded_item(stem="Which state's rate fell to 6 per 1,000?")
    assert mod.ungrounded(rate_in_stem, CHAPTER_TEXT) == "figure-not-in-text:6"
    rate = _grounded_item(modelAnswer="Kerala, at 7 per 1,000")
    assert mod.ungrounded(rate, CHAPTER_TEXT) == "figure-not-in-text:7"


def test_a_figure_with_a_thousands_comma_matches_the_text():
    mod = _gen_script("gen_chapter_comma")
    item = _grounded_item(stem="Which state has a per capita income of Rs 264,000?",
                          evidence=["Haryana has a per capita income of Rs 264,000 a year."])
    assert mod.ungrounded(item, CHAPTER_TEXT) is None


def test_the_bridge_writes_the_prompt_then_reads_the_answer(tmp_path):
    mod = _gen_script("gen_chapter_bridge")
    section = _mcq_section()
    assert mod.bridge_call(tmp_path, 1, "sys", {"type": "object"}, "user", section, "topic") is None
    prompt = json.loads((tmp_path / "p001.json").read_text(encoding="utf-8"))
    assert prompt["system"] == "sys" and prompt["user"] == "user" and prompt["section"] == section.key
    (tmp_path / "r001.json").write_text(json.dumps({"questions": [{"stem": "x"}]}), encoding="utf-8")
    assert mod.bridge_call(tmp_path, 1, "sys", {}, "user", section, "topic") == {"questions": [{"stem": "x"}]}


def test_a_malformed_bridge_answer_is_an_empty_section_not_a_crash(tmp_path):
    mod = _gen_script("gen_chapter_bridge_bad")
    (tmp_path / "r001.json").write_text("{not json", encoding="utf-8")
    assert mod.bridge_call(tmp_path, 1, "s", {}, "u", _mcq_section(), "t") == {"questions": []}
    (tmp_path / "r002.json").write_text("[1, 2]", encoding="utf-8")
    assert mod.bridge_call(tmp_path, 2, "s", {}, "u", _mcq_section(), "t") == {"questions": []}


def test_a_word_limit_or_marks_in_the_stem_is_not_a_fact_to_prove():
    mod = _gen_script("gen_chapter_instruction")
    item = _grounded_item(stem="In about 45 words (3 marks), say which state has 12 per 1,000.")
    assert mod.ungrounded(item, CHAPTER_TEXT) is None
    # ...but a figure that is not an instruction still is.
    item = _grounded_item(stem="In about 45 words, say why 99 children died.")
    assert mod.ungrounded(item, CHAPTER_TEXT) == "figure-not-in-text:99"


INTERLEAVED_TEXT = (
    "Chapter 1\n"
    "Subsoil weathered\n"
    "the states of Punjab, Haryana, western Uttar\n"
    "Top soil the upper soil layer\n"
    "Pradesh, over irrigation is responsible for land\n"
    "degradation due to water logging.\n"
)


def test_a_quote_read_across_interleaved_lines_is_found_line_by_line():
    # A column or a figure's labels sit between two lines of the same sentence.
    mod = _gen_script("gen_chapter_interleaved")
    quote = ("the states of Punjab, Haryana, western Uttar\n"
             "Pradesh, over irrigation is responsible for land\n"
             "degradation due to water logging.")
    item = _grounded_item(stem="Why does irrigation degrade land?", evidence=[quote],
                          options={"A": "a", "B": "b", "C": "c", "D": "d"})
    assert mod.ungrounded(item, INTERLEAVED_TEXT) is None


def test_an_invented_quote_fails_even_line_by_line():
    mod = _gen_script("gen_chapter_invented_lines")
    quote = ("the states of Punjab, Haryana, western Uttar\n"
             "Pradesh, over irrigation is responsible for flooding\n"
             "and nothing else is.")
    item = _grounded_item(stem="Why does irrigation degrade land?", evidence=[quote])
    assert mod.ungrounded(item, INTERLEAVED_TEXT) == "evidence-not-in-text"


HINDI_TEXT = (
    "आज ऐसा कुछ हुआ होगा\n"
    "खूब\n"
    "किसलिए इतनी तृषा रे,\n"
    "भीतर\n"
    "आज सबका मन चुआ होगा।\n"
)


def test_a_hindi_quote_is_checked_against_the_text_not_waved_through():
    # The normaliser kept only ASCII, so every Hindi line became nothing and every Hindi
    # question was refused as having no evidence in the text.
    mod = _gen_script("gen_chapter_hindi")
    item = _grounded_item(stem="इस पंक्ति में कौन-सा शब्द प्यास का भाव देता है?",
                          options={"A": "तृषा", "B": "मन", "C": "आज", "D": "रे"}, correctOption="A",
                          modelAnswer="तृषा",
                          evidence=["किसलिए इतनी तृषा रे,\nआज सबका मन चुआ होगा।"])
    assert mod.ungrounded(item, HINDI_TEXT) is None


def test_an_invented_hindi_quote_is_refused():
    mod = _gen_script("gen_chapter_hindi_invented")
    item = _grounded_item(stem="इस पंक्ति में कौन-सा शब्द प्यास का भाव देता है?", modelAnswer="तृषा",
                          evidence=["किसलिए इतनी प्यास लगी है तुम्हें"])
    assert mod.ungrounded(item, HINDI_TEXT) == "evidence-not-in-text"


def test_a_hindi_stem_ending_in_a_danda_is_a_stem_that_asks():
    assert cg._is_a_question("इस कविता का मूल भाव अपने शब्दों में स्पष्ट कीजिए।")
    assert cg._is_a_question("कवि ने सावन को किसका प्रतीक माना है?")
    assert not cg._is_a_question("कविता में सावन का वर्णन है")


def test_two_calls_for_one_section_do_not_share_record_ids(tmp_path):
    # The model numbers each call's questions 1, 2, 3; two calls for section D both gave
    # "...:D:1" and the collector dropped the second as a duplicate id. A real chapter is read
    # here with answers for two calls of the same section, and every id must be its own.
    import shutil
    import pytest
    pdf_dir = Path(r"C:\Users\varsh\OneDrive\Documents\Sarvam\ncert-dataset\textbooks\chapters\jess2")
    if not (pdf_dir / "jess201.pdf").is_file() or shutil.which("python") is None:
        pytest.skip("the NCERT chapter PDFs are not on this machine")
    mod = _gen_script("gen_chapter_ids")
    folder = tmp_path / "jess2-01"
    folder.mkdir()
    # Prepare the prompts, then answer every call of section D with the same one-question reply.
    mod.generate_chapter("jess2", 1, mark_budget=40, model="m", bridge=folder, per_call=1)
    prompts = sorted(folder.glob("p*.json"))
    d_calls = [p for p in prompts if json.loads(p.read_text(encoding="utf-8"))["section"] == "D"]
    assert len(d_calls) >= 2, "the chapter must have two calls for one section for this to test anything"
    for p in d_calls:
        prompt = json.loads(p.read_text(encoding="utf-8"))
        quote = [l for l in prompt["user"].splitlines() if len(l.split()) > 6][3]
        answer = {"questions": [{
            "qtype": "long_answer", "marks": "5", "bloomLevel": "apply", "option": 1,
            "stem": "Explain in steps what the passage says about the first idea it names. ",
            "modelAnswer": quote, "markingPoints": ["a", "b", "c", "d", "e"], "evidence": [quote]}]}
        (folder / p.name.replace("p", "r", 1)).write_text(json.dumps(answer), encoding="utf-8")
    kept, refused, _ = mod.generate_chapter("jess2", 1, mark_budget=40, model="m", bridge=folder, per_call=1)
    ids = [r["id"] for r in kept]
    assert len(ids) == len(set(ids)), ids


def test_a_second_pass_asks_only_for_its_sections_and_cannot_collide_with_the_first(tmp_path):
    # The paper's proportions give a chapter about one MCQ; a bank needs several. The second pass plans
    # just the named sections, as many as asked, numbered from 100 so its ids never meet the first pass's.
    import pytest
    pdf_dir = Path(r"C:\Users\varsh\OneDrive\Documents\Sarvam\ncert-dataset\textbooks\chapters\jess2")
    if not (pdf_dir / "jess201.pdf").is_file():
        pytest.skip("the NCERT chapter PDFs are not on this machine")
    mod = _gen_script("gen_chapter_pass2")
    folder = tmp_path / "jess2-01-mcq"
    folder.mkdir()
    kw = dict(mark_budget=20, model="m", bridge=folder, per_call=3, only_sections=frozenset({"A"}),
              items_per_section=5, number_from=100)
    mod.generate_chapter("jess2", 1, **kw)
    prompts = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(folder.glob("p*.json"))]
    assert [p["section"] for p in prompts] == ["A", "A"], "five MCQs in calls of three and two"
    for p in prompts:
        n = 3 if p["index"] == 1 else 2
        opts = {k: f"option {k}" for k in "ABCD"}
        quote = [l for l in p["user"].splitlines() if len(l.split()) > 6][2]
        answer = {"questions": [{"qtype": "mcq", "marks": "1", "bloomLevel": "apply", "option": 1,
                                 "stem": f"Which statement does the text make about its second idea, number {i}?",
                                 "options": opts, "correctOption": "ABCD"[i % 4], "evidence": [quote]}
                                for i in range(n)]}
        (folder / f"r{p['index']:03d}.json").write_text(json.dumps(answer), encoding="utf-8")
    kept, _, _ = mod.generate_chapter("jess2", 1, **kw)
    ids = [r["id"] for r in kept]
    assert ids == [f"ai:cbse:jess2:01:A:{n}" for n in range(101, 106)], ids


# --------------------------------------------------------------------------- #
# language kinds: reading, extract, grammar, writing, literature
# --------------------------------------------------------------------------- #

PASSAGE = ("The old clock in the hall had stopped years ago, but nobody dared to remove it. "
           "Every evening the children sat beneath it and told stories about the hands that once "
           "moved, and the grandmother listened and smiled at each one.")


def _english(key: str) -> bp.Section:
    return next(s for s in bp.for_paper("English", 10).sections if s.key == key)


def _reading_item(**over) -> dict:
    item = {"qtype": bp.MCQ, "marks": 1, "bloomLevel": "understand",
            "stem": "Why does the grandmother smile at the children's stories?",
            "options": {"A": "They amuse her", "B": "They fix the clock", "C": "They are in verse",
                        "D": "They end early"},
            "correctOption": "A", "passage": PASSAGE, "option": 1}
    item.update(over)
    return item


@pytest.mark.parametrize("subject", ["English", "Hindi"])
def test_every_language_section_names_its_kind(subject):
    for section in bp.for_paper(subject, 10).sections:
        assert section.kind in {"reading", "grammar", "extract", "writing", "literature"}, section


def test_a_reading_question_carries_its_passage_and_says_what_it_is():
    section = _english("A")
    assert cg.validate(_reading_item(), section) is None
    record = cg.to_record(_reading_item(), section, _chapter(), "t", chapter_id="c", topic_id="",
                          model="m")
    assert record["stem"].startswith(PASSAGE)
    assert "(A) They amuse her" in record["stem"]
    assert record["metadata"] == {"paperSection": "reading"}


def test_a_section_with_no_kind_adds_no_tag():
    record = cg.to_record(_good_mcq(), _mcq_section(), _chapter(), "t", chapter_id="c", topic_id="",
                          model="m")
    assert "metadata" not in record


@pytest.mark.parametrize("passage, reason", [
    ("", "passage-too-short"),
    ("Too short to read.", "passage-too-short"),
    (" ".join(["word"] * 200), "passage-too-long"),
])
def test_a_reading_question_needs_a_passage_worth_reading(passage, reason):
    assert cg.validate(_reading_item(passage=passage), _english("A")) == reason


def test_the_stem_must_not_repeat_the_passage_it_is_printed_under():
    assert cg.validate(_reading_item(stem=PASSAGE + " Why does she smile?"), _english("A")) \
        == "stem-repeats-the-passage"


def test_the_reading_schema_asks_for_a_passage_and_other_mcqs_do_not():
    reading = cg._schema(_english("A"), 3)["properties"]["questions"]["items"]
    assert "passage" in reading["required"]
    plain = cg._schema(_mcq_section(), 3)["properties"]["questions"]["items"]
    assert "passage" not in plain["properties"]


def test_the_prompt_lets_a_reading_question_say_the_passage_and_a_plain_one_not():
    system, _, _ = cg.build_prompt(_chapter(), _english("A"), "t", count=3, bank_subject="English")
    assert 'may say "the passage"' in system and "copy 50-110 words" in system
    system, _, _ = cg.build_prompt(_chapter(), _mcq_section(), "t", count=3, bank_subject="English")
    assert "Never mention the chapter, the text, the passage" in system


def test_a_passage_the_book_does_not_print_is_refused_and_one_it_does_is_kept():
    gen = _gen_script("gen_for_passage")
    text = "intro line of the lesson\n" + PASSAGE + "\nclosing line of the lesson"
    item = _reading_item(evidence=["The old clock in the hall had stopped years ago"])
    assert gen.ungrounded(item, text, _english("A")) is None
    invented = _reading_item(passage="A completely different passage about a river that the "
                                     "lesson never prints anywhere at all, in any of its lines.",
                             evidence=["The old clock in the hall had stopped years ago"])
    assert gen.ungrounded(invented, text, _english("A")) == "passage-not-in-text"
    # a case study's passage is the model's own writing, so it is not held to the text
    case = _english("A")
    assert gen.ungrounded(invented, text, bp.Section("E", "Case Based", bp.CASE, 3, 4)) is None


def test_a_map_pointing_question_is_kept_and_needs_no_copied_passage():
    section = next(s for s in bp.for_paper("Social Science", 10).sections if s.qtype == bp.MAP)
    stem = ("On an outline political map of India, locate and label the following: (a) Bhakra Nangal "
            "dam (b) Kandla port (c) Tarapur nuclear power plant (d) Digboi oilfield (e) Kolar gold field.")
    item = {"qtype": bp.MAP, "marks": 5, "bloomLevel": "apply", "stem": stem, "option": 1,
            "modelAnswer": "Punjab; Gujarat; Maharashtra; Assam; Karnataka",
            "markingPoints": ["Bhakra Nangal: Punjab", "Kandla: Gujarat", "Tarapur: Maharashtra",
                              "Digboi: Assam", "Kolar: Karnataka"]}
    assert cg.validate(item, section) is None
    assert "passage" not in cg._schema(section, 1)["properties"]["questions"]["items"]["properties"]
    assert "modelAnswer" in cg._schema(section, 1)["properties"]["questions"]["items"]["required"]
    assert cg.validate({**item, "markingPoints": []}, section) == "no-marking-points"
    record = cg.to_record(item, section, _chapter(), "t", chapter_id="c", topic_id="", model="m")
    assert record["stem"] == stem
    assert sum(p["marks"] for p in record["answerScheme"]["markingPoints"]) == 5


def test_a_question_in_parts_keeps_its_first_label():
    # Stripping the leading "(a)" left "Name the industries ... (b) Explain ...", a case study the
    # stem gate refuses as a broken option list.
    stem = "(a) Name the two industries. (b) Explain which soil process the dust retards."
    assert cg.strip_question_number(stem) == stem
    assert cg.strip_question_number("(a) Name the industry.") == "Name the industry."
    assert cg.strip_question_number("1. Find the HCF of 6 and 72.") == "Find the HCF of 6 and 72."


def test_a_writing_task_may_be_an_instruction_and_a_word_limit_in_devanagari_is_not_a_fact():
    writing = next(s for s in bp.for_paper("Hindi", 10).sections if s.kind == "writing")
    task = {"qtype": writing.qtype, "marks": writing.marks, "bloomLevel": "apply", "option": 1,
            "stem": "अपने विद्यालय के प्रधानाचार्य को पुस्तकालय के लिए नई पुस्तकें मँगवाने हेतु पत्र लिखिए।",
            "modelAnswer": "औपचारिक पत्र", "markingPoints": ["विषय", "प्रारूप", "भाषा"]}
    assert cg.validate(task, writing) is None
    assert cg.validate(task, _mcq_section()) != "stem-is-not-a-question"      # other sections unchanged
    gen = _gen_script("gen_for_devanagari_limit")
    item = {**task, "stem": "लगभग १२० शब्दों में अपने विद्यालय के वार्षिकोत्सव पर एक अनुच्छेद लिखिए।",
            "evidence": ["विद्यालय का वार्षिकोत्सव हर वर्ष मनाया जाता है"]}
    text = "विद्यालय का वार्षिकोत्सव हर वर्ष मनाया जाता है और सब उसमें भाग लेते हैं।"
    assert gen.ungrounded(item, text, writing) is None
    assert gen.ungrounded({**item, "stem": item["stem"].replace("१२०", "१९६०") + " (१९६०)"}, text,
                          writing) == "figure-not-in-text:१९६०"


def test_a_reading_question_is_typed_competency_based_and_still_prints_its_options():
    from academicos.assessment.competency import is_competency_question
    section = _english("A")
    record = cg.to_record(_reading_item(), section, _chapter(), "t", chapter_id="c", topic_id="", model="m")
    assert record["type"] == "competency_based" and is_competency_question(record)
    assert "(A) They amuse her" in record["stem"] and "(D) They end early" in record["stem"]
    extract = cg.to_record(_reading_item(), _english("D"), _chapter(), "t", chapter_id="c", topic_id="", model="m")
    assert extract["type"] == "competency_based" and is_competency_question(extract)
    grammar = cg.to_record(_good_mcq(), _english("B"), _chapter(), "t", chapter_id="c", topic_id="", model="m")
    assert grammar["type"] == "mcq" and not is_competency_question(grammar)


def test_a_hindi_record_is_mended_and_its_quote_still_matches_the_broken_text():
    gen = _gen_script("gen_for_repair")
    broken = "मुझे कोई साधारण निबंध नहीीं लिखन ा है। आज मुझे आदर्श निबंध लिखन ा होगा।"
    section = next(s for s in bp.for_paper("Hindi", 10).sections if s.key == "B")
    item = {"qtype": section.qtype, "marks": section.marks, "bloomLevel": "understand", "option": 1,
            "passage": broken, "stem": "लेखक को क्या लिखन ा है?", "modelAnswer": "आदर्श निबंध लिखन ा",
            "markingPoints": ["निबंध लिखन ा"], "evidence": ["मुझे कोई साधारण निबंध नहीं लिखना है।"]}
    assert gen.ungrounded(item, broken, section) is None
    record = cg.to_record(item, section, _chapter("hi"), "t", chapter_id="c", topic_id="", model="m")
    assert "लिखना" in record["stem"] and "लिखन ा" not in record["stem"] and "नहीीं" not in record["stem"]
    assert record["answerScheme"]["modelAnswer"] == "आदर्श निबंध लिखना"


def test_a_class_9_book_with_no_per_file_tree_is_filed_under_the_class_trees_chapters(tmp_path, monkeypatch):
    gen = _gen_script("gen_for_tree")
    import json as _json
    tax = tmp_path / "taxonomy"
    tax.mkdir()

    def tree(subject, names):
        (tax / f"{subject}_9.json").write_text(_json.dumps({"chapters": [
            {"number": i + 1, "name": n, "id": f"{subject.lower()}-9/{n.lower().replace(' ', '-')}",
             "topics": [{"name": f"{n} topic"}]} for i, n in enumerate(names)]}), encoding="utf-8")

    tree("Science", ["Cells", "Tissues", "Motion"])
    tree("English", ["Lesson A", "Lesson B", "Lesson C", "Lesson D"])
    books = tmp_path / "books"
    for code, count in (("iesc1", 3), ("iebe1", 2)):
        (books / code).mkdir(parents=True)
        for n in range(1, count + 1):
            (books / code / f"{code}{n:02d}.pdf").write_bytes(b"")
    monkeypatch.setattr(gen, "TAXONOMY", tax)
    monkeypatch.setattr(gen, "BOOKS", books)
    one_to_one, also = gen.tree_chapter_for("Science", 9, "iesc1", 2)
    assert (one_to_one["name"], also) == ("Tissues", [])
    first, also = gen.tree_chapter_for("English", 9, "iebe1", 2)       # unit 2 = lessons C and D
    assert (first["name"], also) == ("Lesson C", ["english-9/lesson-d"])
    assert gen.tree_chapter_for("Science", 9, "iebe1", 1) == ({}, [])    # counts that fit neither: not guessed
    record = cg.to_record(_good_mcq(), _mcq_section(), _chapter(), "t", chapter_id="english-9/lesson-c",
                          topic_id="", model="m", also_chapter_ids=("english-9/lesson-d",))
    assert record["chapterIds"] == ["english-9/lesson-c", "english-9/lesson-d"]


def test_a_topic_named_like_the_chapter_is_not_kept_as_a_label():
    # A label equal to the chapter's name made the bank's topic search read the chapter's name as that
    # label alone: 8 of Science 9 "Tissues in Action"'s 52 questions.
    chapter = _chapter()
    same = cg.to_record(_good_mcq(), _mcq_section(), chapter, chapter.title.upper(), chapter_id="c",
                        topic_id="", model="m")
    assert same["topic"] == ""
    other = cg.to_record(_good_mcq(), _mcq_section(), chapter, "Animal Tissues", chapter_id="c", topic_id="",
                         model="m")
    assert other["topic"] == "Animal Tissues"
    assert cg.to_record(_good_mcq(), _mcq_section(), chapter, "", chapter_id="c", topic_id="",
                        model="m")["topic"] == ""
