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


def test_a_served_written_mcq_keeps_its_quote_and_names_us_not_cbse():
    """Review 2026-10-04: the MCQ key rebuild dropped the chapter quote, so all 53 written MCQs were
    served as textbook_grounded with no evidence; and every written question was attributed to a CBSE
    previous year paper in the question-bank API's `book`."""
    from academicos.assessment.question_bank import enrich_record

    out = bm.compose([], [], [], ai=[_record()])
    assert out.questions[0]["type"] == "mcq"
    assert out.questions[0]["answerScheme"]["metadata"]["evidence"] == [QUOTE]
    rec = enrich_record({**_record(), "source": "ai_generated"})
    assert rec["rights"]["origin"] == "AcademicOS"
    assert "CBSE" not in rec["rights"]["attribution"]
    # A record already carrying the CBSE default is corrected; a board question keeps CBSE's.
    stale = enrich_record({**_record(), "source": "ai_generated",
                           "rights": {"origin": "CBSE", "redistribution": "unknown", "basis": "",
                                      "attribution": "Central Board of Secondary Education, previous year question paper"}})
    assert stale["rights"]["origin"] == "AcademicOS"
    board = enrich_record({"id": "cbse:q:1", "source": "cbse_board_paper"})
    assert board["rights"]["origin"] == "CBSE"


def test_the_served_bank_has_no_written_question_under_cbse_and_no_written_mcq_without_its_quote():
    import json
    from pathlib import Path
    served = json.loads((Path(__file__).resolve().parents[1] / "academicos-data/syllabus/questions.json")
                        .read_text(encoding="utf-8"))["questions"]
    written = [q for q in served if q.get("source") == "ai_generated"]
    assert written, "the class 9-10 written questions are in the served bank"
    assert all((q.get("rights") or {}).get("origin") == "AcademicOS" for q in written)
    # A written MCQ's key is the chapter's own words, or -- a sum from the textbook
    # transcriptions (2026-10-14) -- an answer a second model solved alike
    # (corpus/textbook.py, `two_model_solved`). Never neither.
    assert all(((q.get("answerScheme") or {}).get("metadata") or {}).get("evidence")
               or (q.get("answerScheme") or {}).get("provenance") == "two_model_solved"
               for q in written if q["type"] == "mcq")
