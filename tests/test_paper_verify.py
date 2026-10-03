"""What `paper_verify.verify` accepts and what it refuses, on a paper built to a real preset."""
from __future__ import annotations

import copy

import pytest

from academicos.assessment import paper_verify, template_presets

PRESET = next(p for p in template_presets.presets(grade=10) if p.id == "preset:cbse:10:mathematics:unit_test")
OPTIONS = " (A) one (B) two (C) three (D) four"


def _paper() -> dict:
    sections, key, n = [], {}, 0
    for index, want in enumerate(PRESET.sections):
        questions = []
        for _ in range(want.question_count):
            n += 1
            stem = f"Question number {n} asks the student to compute the value of expression {n} plus {n}."
            kind = "mcq" if want.marks_each == 1 else "short_answer"
            if kind == "mcq":
                stem += OPTIONS
            questions.append({"questionId": f"q{n}", "displayNumber": n, "stem": stem,
                              "marks": want.marks_each, "type": kind})
            key[str(n)] = "The marking scheme."
        sections.append({"sectionId": f"s{index}", "label": want.title, "questions": questions,
                         "totalMarks": want.question_count * want.marks_each})
    return {"sections": sections, "answerKey": key, "warnings": [],
            "metadata": {"totalMarks": PRESET.total_marks}, "competencyTargetMet": None}


def test_a_paper_that_matches_its_template_is_verified():
    assert paper_verify.verify(_paper(), PRESET) == []


def _problems(mutate) -> list[str]:
    paper = copy.deepcopy(_paper())
    mutate(paper)
    return paper_verify.verify(paper, PRESET)


@pytest.mark.parametrize("mutate, fragment", [
    (lambda p: p["warnings"].append("Competency-based: 1 of 12"), "warnings"),
    (lambda p: p["sections"][0]["questions"].pop(), "questions printed"),
    (lambda p: p["sections"][0]["questions"][0].update(marks=2), "marks"),
    (lambda p: p["sections"].pop(), "sections"),
    (lambda p: p["sections"][0]["questions"][0].update(stem="Short"), "fragment"),
    (lambda p: p["sections"][0]["questions"][0].update(
        stem="Find the value of the expression � in the figure shown." + OPTIONS), "replacement"),
    (lambda p: p["sections"][0]["questions"][1].update(questionId="q1"), "printed twice"),
    (lambda p: p["sections"][0]["questions"][0].update(stem="Find the area of the triangle in the given figure."),
     "does not print"),
    (lambda p: p["sections"][0]["questions"][0].update(
        stem="Which of the following is the value of the sum of two numbers shown?"), "options"),
    (lambda p: p["answerKey"].pop("1"), "no answer"),
    (lambda p: p["sections"][0]["questions"][0].update(displayNumber=9), "question numbers"),
    (lambda p: p.update(competencyTargetMet=False), "competency"),
])
def test_each_defect_is_named(mutate, fragment):
    problems = _problems(mutate)
    assert problems, "the defect passed"
    assert any(fragment in p for p in problems), problems


def test_a_hindi_paper_must_be_devanagari_and_an_english_one_must_not():
    assert any("Devanagari" in p for p in paper_verify.verify(_paper(), PRESET, language="hi"))
    paper = _paper()
    for section in paper["sections"]:
        for q in section["questions"]:
            q["stem"] = "यह एक पर्याप्त लंबा हिंदी प्रश्न है जिसे विद्यार्थी हल करेगा। " + q["stem"].split(" (A)")[0][:0] + (
                "(A) एक (B) दो (C) तीन (D) चार" if q["type"] == "mcq" else "")
    assert not any("Devanagari" in p for p in paper_verify.verify(paper, PRESET, language="hi")), \
        paper_verify.verify(paper, PRESET, language="hi")


def test_a_class_9_10_language_paper_is_held_to_the_kind_each_section_is_headed_with():
    preset = next(p for p in template_presets.presets(grade=10) if p.id == "preset:cbse:10:english:unit_test")
    paper = {"sections": [], "answerKey": {}, "warnings": [], "metadata": {"totalMarks": preset.total_marks},
             "competencyTargetMet": None}
    tags, n = {}, 0
    for index, want in enumerate(preset.sections):
        questions = []
        for _ in range(want.question_count):
            n += 1
            questions.append({"questionId": f"q{n}", "displayNumber": n, "marks": want.marks_each,
                              "type": "mcq" if want.marks_each == 1 else "short_answer",
                              "stem": f"Question {n} asks about something else entirely, number {n}."
                                      + (OPTIONS if want.marks_each == 1 else "")})
            paper["answerKey"][str(n)] = "key"
            tags[f"q{n}"] = next(iter(sorted(paper_templates_kinds(want))))
        paper["sections"].append({"sectionId": f"s{index}", "label": want.title, "questions": questions,
                                  "totalMarks": want.question_count * want.marks_each})
    assert paper_verify.verify(paper, preset, tags=tags) == []
    tags["q1"] = "grammar"        # a grammar question under Reading comprehension
    problems = paper_verify.verify(paper, preset, tags=tags)
    assert any("q1" in p and "grammar" in p for p in problems), problems
    tags.pop("q1")
    assert any("untagged" in p for p in paper_verify.verify(paper, preset, tags=tags))


def paper_templates_kinds(section):
    from academicos.assessment import paper_templates
    return paper_templates.section_kinds(section)
