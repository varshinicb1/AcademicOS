"""Questions a model wrote from a chapter (corpus/ai-cbse-9-10) reach the served bank only
as a checked key: labelled `textbook_grounded` AND carrying the quotes that ground it.
The merge enforces it on the record, so a record from another route cannot get in by
carrying the source name."""
from __future__ import annotations

import copy

from academicos.assessment.qbank_engine import QuestionBank, key_tier
from academicos.corpus import bank_merge as bm
from academicos.corpus import cbse_blueprint as bp
from academicos.corpus import cbse_generate as cg

QUOTE = "The Equator divides the Earth into the Northern and Southern Hemispheres."


def _record(**scheme_over) -> dict:
    chapter = cg.Chapter(
        book_code="jess1", subject="Social Science", grade=10, language="en", number=1,
        title="Resources and Development",
        pages=tuple((p, f"page {p} line {i}") for p in (1, 2) for i in range(30)))
    item = {"qtype": bp.MCQ, "marks": 1, "bloomLevel": "understand", "option": 1,
            "stem": "Which line divides the Earth into the Northern and Southern Hemispheres?",
            "options": {"A": "Prime Meridian", "B": "Equator", "C": "Tropic of Cancer", "D": "Arctic Circle"},
            "correctOption": "B"}
    record = cg.to_record(item, bp.Section("A", "Objective", bp.MCQ, 4, 1), chapter, "Locating places",
                          chapter_id="social-science-10/resources-and-development", topic_id="", model="m")
    scheme = record["answerScheme"]
    scheme["provenance"] = "textbook_grounded"
    scheme.setdefault("metadata", {})["evidence"] = [QUOTE]
    scheme.update(scheme_over)
    return record


def test_a_grounded_record_is_served_with_the_checked_label():
    out = bm.compose([], [], [], ai=[_record()])
    assert out.counts["ai"] == 1
    assert len(out.questions) == 1
    assert QuestionBank.has_answer_key(out.questions[0]) and key_tier(out.questions[0]) == "checked"


def test_a_record_without_the_grounded_label_is_not_served():
    rec = _record()
    rec["answerScheme"].pop("provenance")
    out = bm.compose([], [], [], ai=[rec])
    assert out.questions == []
    assert [e["reason"] for e in out.excluded] == [bm.AI_NOT_GROUNDED]


def test_a_record_labelled_grounded_without_its_quotes_is_not_served():
    for quotes in ([], [""], "a string, not a list", None):
        rec = _record()
        rec["answerScheme"]["metadata"]["evidence"] = quotes
        out = bm.compose([], [], [], ai=[rec])
        assert out.questions == [], quotes
        assert out.excluded and out.excluded[0]["reason"] == bm.AI_NOT_GROUNDED


def test_a_published_copy_of_a_question_wins_over_the_model_written_one():
    base = _record()
    published = copy.deepcopy(base)
    published["id"] = "cbe:published"
    published["answerScheme"]["provenance"] = "cbse_marking_scheme"
    out = bm.compose([], [published], [], ai=[base])
    assert [q["id"] for q in out.questions] == ["cbe:published"]
    assert out.counts["ai"] == 0


def test_a_bank_composed_without_the_source_does_not_report_it():
    assert "ai" not in bm.compose([], [], []).counts


def test_a_language_question_keeps_its_paper_section_through_the_merge():
    """A template section headed Reading or Grammar matches on `metadata.paperSection`
    (assessment/paper_templates), so the merge must not lose it, and the pool must load it."""
    chapter = cg.Chapter(
        book_code="jeff1", subject="English", grade=10, language="en", number=1, title="A Letter",
        pages=tuple((p, f"page {p} line {i}") for p in (1, 2) for i in range(30)))
    passage = " ".join(["The old clock stopped long ago and nobody dared to remove it."] * 3)
    item = {"qtype": bp.MCQ, "marks": 1, "bloomLevel": "understand", "option": 1, "passage": passage,
            "stem": "Why did nobody remove the clock?",
            "options": {"A": "They feared it", "B": "It was costly", "C": "It was lost", "D": "It was new"},
            "correctOption": "A"}
    section = next(s for s in bp.for_paper("English", 10).sections if s.key == "A")
    record = cg.to_record(item, section, chapter, "Reading", chapter_id="english-10/a-letter",
                          topic_id="", model="m")
    record["answerScheme"]["provenance"] = "textbook_grounded"
    record["answerScheme"]["metadata"]["evidence"] = ["The old clock stopped long ago"]
    out = bm.compose([], [], [], ai=[record])
    assert [q["id"] for q in out.questions] == [record["id"]]
    assert out.questions[0]["metadata"]["paperSection"] == "reading"
    from academicos.assessment.schemas import QuestionSchema
    assert QuestionSchema.model_validate(out.questions[0]).metadata["paperSection"] == "reading"
