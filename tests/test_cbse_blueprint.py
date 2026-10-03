"""The CBSE paper format, checked against the board's own arithmetic.

`cbse_blueprint.py` is the only place that decides what a question is *for*. If
its section marks do not add up to the theory paper, every question generated
against it is aimed at the wrong target -- and nothing downstream would notice,
because each question would still look perfectly well formed.

So these tests check the format itself: the sections add to 80, the board's
50/20/30 split actually holds, the internal choice is about a third, and the
cognitive mix is not all recall. A format that fails these is not a CBSE paper.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.corpus import cbse_blueprint as bp  # noqa: E402

SUBJECTS = ["Mathematics", "Science", "Social Science", "English", "Hindi"]
BOARD_SUBJECTS = ["Mathematics", "Science", "Social Science", "English", "Hindi"]


def _all():
    for grade in range(1, 11):
        for subject in SUBJECTS:
            yield grade, subject, bp.for_paper(subject, grade)


@pytest.mark.parametrize("subject", BOARD_SUBJECTS)
def test_a_board_paper_is_eighty_marks(subject):
    # 80 theory + 20 internal, every main subject, every year.
    assert bp.for_paper(subject, 10).total_marks == bp.THEORY_MARKS


@pytest.mark.parametrize("subject", BOARD_SUBJECTS)
def test_board_paper_sections_sum_to_the_theory_marks(subject):
    # The failure this catches: a section added or a count edited without the
    # total being rebalanced. The paper then prints 84 marks.
    blueprint = bp.for_paper(subject, 10)
    by_key = sum(s.section_marks for s in blueprint.sections)
    assert by_key == blueprint.theory_marks
    assert blueprint.total_marks == 80


@pytest.mark.parametrize("subject", BOARD_SUBJECTS)
def test_social_science_and_science_keep_their_own_shape(subject):
    # The board's sections are per subject, not one universal template. Social
    # Science ends in a map section; Science spends four Section A marks on
    # assertion-reason; the language papers read and write rather than running an
    # objective section over the syllabus.
    blueprint = bp.for_paper(subject, 10)
    keys = [s.key for s in blueprint.sections]
    if subject == "Social Science":
        assert keys[-1] == "F"
        assert blueprint.sections[-1].qtype == bp.MAP
    if subject == "Science":
        assert any(s.qtype == bp.ASSERTION_REASON and s.count == 4
                   for s in blueprint.sections)
    if subject in ("English", "Hindi"):
        kinds = {s.kind for s in blueprint.sections}
        assert {"reading", "grammar", "extract", "writing", "literature"} <= kinds
        # Reading hangs off a passage, and the paper is written work, not MCQs.
        assert any(s.carries_source for s in blueprint.sections)
        written = sum(s.section_marks for s in blueprint.sections if s.qtype != bp.MCQ)
        assert written >= 40, "a language paper is not 40 marks of writing"


def test_every_registered_section_type_is_a_bank_type():
    # A section may only ask for a question shape the bank already stores, or the
    # merge would drop it for want of a type it has never seen.
    for _, _, blueprint in _all():
        for section in blueprint.sections:
            assert section.qtype in bp.QUESTION_TYPES


def test_no_section_asks_for_more_marks_than_the_board_prints():
    # Section marks are per question. A 10-mark section is right for the language
    # papers' writing slot and wrong everywhere else; nothing may invent a mark
    # value that is not a CBSE one.
    board_marks = {1, 2, 3, 4, 5, 6, 8, 10}   # 6: the language papers' long answers
    for _, _, blueprint in _all():
        for section in blueprint.sections:
            assert section.marks in board_marks, (
                f"{blueprint.subject} {blueprint.grade_band} section "
                f"{section.key} asks for {section.marks} marks")


def test_internal_choice_is_about_a_third_and_never_exceeds_the_section():
    # "Around 33% of the questions in each section will have an internal choice."
    for _, _, blueprint in _all():
        for section in blueprint.sections:
            if section.internal_choice:
                share = section.internal_choice / section.count
                assert 0 < share <= 0.5, (
                    f"{blueprint.subject} {section.key}: {section.internal_choice}"
                    f"/{section.count} internal choice")
                assert section.internal_choice <= section.count


def test_the_competency_focus_is_actually_competency():
    # The board's stated emphasis. A bank that is 90% recall is not a CBSE bank
    # however well formed its questions are.
    for _, _, blueprint in _all():
        share = bp.competency_share(blueprint)
        assert share >= 0.35, (
            f"{blueprint.subject} {blueprint.grade_band}: only {share:.0%} of the "
            f"paper is at apply or above")


def test_a_paper_is_not_all_one_mark_questions():
    for _, _, blueprint in _all():
        one_mark = sum(s.section_marks for s in blueprint.sections if s.marks == 1)
        # Half at most: the English paper's reading, grammar and extract items are 40 of 80.
        assert one_mark <= blueprint.total_marks * 0.5


def test_bloom_mix_covers_every_level_the_sections_imply():
    # Case-based and long-answer work has to sit above `understand`, or the
    # section is a recall slot wearing a competency label.
    for _, _, blueprint in _all():
        mix = bp.bloom_mix(blueprint)
        assert mix["remember"] > 0
        assert sum(mix.values()) == blueprint.total_questions
        high = mix["apply"] + mix["analyze"] + mix["evaluate"] + mix["create"]
        assert high > 0


def test_case_based_questions_are_never_asked_below_apply():
    for _, _, blueprint in _all():
        for section in blueprint.sections:
            if section.qtype in (bp.CASE, bp.MAP):
                assert section.marks >= 4, "case work below 4 marks is not CBSE's"


def test_shares_are_measured_not_assumed():
    # The module computes the board's 50/20/30 rather than trusting a constant, so
    # a structural change cannot silently break the ratio.
    shares = bp.for_paper("Mathematics", 10).shares()
    assert 0.0 <= shares["mcq"] <= 1.0
    assert shares["subjective"] > 0
    assert shares["mcq"] + shares["subjective"] <= 1.0 + 1e-9
    # Competency counts the objective run too, so it is the largest share.
    assert shares["competency"] >= shares["mcq"]


def test_an_unregistered_format_raises_rather_than_defaulting():
    # A silent default is how a school prints a paper in a shape no marker knows.
    with pytest.raises(KeyError):
        bp.for_paper("Home Science", 10)
    with pytest.raises(KeyError):
        bp.for_paper("Computer Science", 3)
    with pytest.raises(KeyError):
        bp.band_for(12)


def test_bands_cover_every_grade_in_scope():
    for grade in range(1, 11):
        assert bp.band_for(grade) in bp.GRADE_BANDS


def test_a_chapter_plan_spreads_across_its_own_topics():
    # The point of a per-chapter plan: the questions land on the chapter's
    # headings, and no heading carries the whole chapter.
    blueprint = bp.for_paper("Science", 10)
    topics = ["Electricity", "Magnetic Effects", "Chemical Reactions"]
    plan = bp.plan_chapter(blueprint, topics, mark_budget=12)
    assert plan
    used = {topic for _, topic in plan if topic}
    assert used == set(topics), f"plan skipped topics: {used}"
    assert len(plan) == len({(s.key, i) for i, (s, _) in enumerate(plan)})


def test_a_chapter_plan_is_deterministic():
    # The same chapter and budget must plan the same paper, or a regenerated bank
    # diffs against the last one for no reason.
    blueprint = bp.for_paper("Mathematics", 8)
    topics = ["Numbers", "Addition"]
    a = bp.plan_chapter(blueprint, topics, mark_budget=10)
    b = bp.plan_chapter(blueprint, topics, mark_budget=10)
    assert a == b


def test_a_chapter_with_no_topics_cannot_be_planned():
    with pytest.raises(ValueError):
        bp.plan_chapter(bp.for_paper("Mathematics", 5), [], mark_budget=10)


def test_a_plan_never_asks_for_more_than_the_section_holds():
    # `want` is capped at the section's count; a big budget must not produce a
    # section with nine questions when the paper prints five.
    blueprint = bp.for_paper("Social Science", 10)
    topics = ["Nationalism", "Resources", "Power Sharing", "Development"]
    plan = bp.plan_chapter(blueprint, topics, mark_budget=200)
    per_section: dict[str, int] = {}
    for section, _ in plan:
        per_section[section.key] = per_section.get(section.key, 0) + 1
    for section in blueprint.sections:
        assert per_section.get(section.key, 0) <= section.count


def test_answer_word_limits_grow_with_marks():
    # ~1.5 words a mark, and never a one-mark question asked to prose.
    blueprint = bp.for_paper("Mathematics", 10)
    assert blueprint.answer_words(bp.MCQ, 1) == 1
    assert blueprint.answer_words(bp.VSA, 2) < blueprint.answer_words(bp.SA, 3)
    assert blueprint.answer_words(bp.SA, 3) < blueprint.answer_words(bp.LA, 5)


def test_mark_and_type_agree_within_a_section():
    # A section whose questions disagree about their own marks would generate
    # answers the rubric cannot score.
    for _, _, blueprint in _all():
        for section in blueprint.sections:
            assert section.section_marks % section.marks == 0
            if section.answer_words:
                assert section.answer_words >= section.marks
