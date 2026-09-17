"""The question-bank MCP server.

Exercised through the real SDK's in-memory client, so the test drives the same
protocol path a host does -- tool registration, argument validation, result
serialisation -- rather than calling the underlying functions directly.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.mcp.qbank_server import Corpus, build_server


def record(i: int, *, marks: int = 2, topic: str = "Algebra",
           subject: str = "Mathematics", grade: int = 8, scheme: bool = True) -> dict:
    qid = f"t:q:{i}"
    return {
        "id": qid, "questionBankId": "t:doc", "subject": subject, "grade": grade,
        "chapterIds": [topic], "topic": topic, "contentCode": f"8{topic[:1]}1a",
        "marks": marks, "type": "mcq" if i % 2 else "short_answer",
        "difficulty": "easy", "bloomLevel": "understand",
        "stem": f"Question {i} about {topic}",
        "tags": [topic], "language": "en", "reviewState": "published", "version": 1,
        "answerScheme": ({
            "totalMarks": marks, "provenance": "cbse_marking_scheme",
            "markingPoints": [{"id": "mp1", "description": "the answer", "marks": marks}],
            "modelAnswer": "",
        } if scheme else {"totalMarks": marks, "markingPoints": [], "provenance": "none"}),
        "rights": {"origin": "CBSE", "redistribution": "unknown", "basis": ""},
        "provenance": {"sourceDocumentId": "t:doc", "pageNumber": 3},
        "calibration": {"measured": False, "basis": "assigned"},
        "supersededBy": None,
    }


@pytest.fixture(scope="module")
def corpus() -> Corpus:
    records = [
        record(i, marks=(i % 5) + 1, topic="Algebra" if i % 2 else "Geometry")
        for i in range(1, 41)
    ]
    # 8 of them carry no marking scheme at all.
    records += [record(100 + i, scheme=False, marks=2) for i in range(8)]
    return Corpus(records)


def call(corpus: Corpus, tool: str, args: dict | None = None) -> dict:
    """Invoke a tool through the real MCP client, in memory, with no transport.

    The result arrives as a JSON text block, not as `structured_content`:
    this SDK serialises a `dict` return into a `TextContent` unless the tool
    declares a structured output schema. That is a normal MCP shape and every
    client can read it, so the tools are left as they are and the parse happens
    here. `structured_content` is still preferred when present, so this keeps
    working if the tools later gain a schema.
    """
    from mcp import Client

    mcp = build_server(corpus)
    args = args or {}

    async def run():
        async with Client(mcp) as client:
            result = await client.call_tool(tool, args)
            assert not result.is_error, f"{tool} returned an error"
            if result.structured_content is not None:
                return result.structured_content
            for block in result.content or []:
                text = getattr(block, "text", None)
                if text:
                    return json.loads(text)
            raise AssertionError(f"{tool} returned no readable content")

    return asyncio.run(run())


# --------------------------------------------------------------------------- #
# registration
# --------------------------------------------------------------------------- #

def test_the_seven_tools_are_registered(corpus):
    mcp = build_server(corpus)
    names = {t.name for t in asyncio.run(mcp.list_tools())}
    assert names == {
        "search_questions", "get_question", "get_answer_key", "list_topics",
        "marks_distribution", "coverage_report", "build_paper",
    }


def test_every_tool_has_a_description(corpus):
    """An MCP tool with no description is unusable by an agent -- the
    description is the only thing telling the model when to call it."""
    mcp = build_server(corpus)
    for t in asyncio.run(mcp.list_tools()):
        assert t.description and len(t.description) > 20, t.name


# --------------------------------------------------------------------------- #
# the answer-key rule
# --------------------------------------------------------------------------- #

def test_search_excludes_questions_with_no_answer_key_by_default(corpus):
    """The requirement: without an answer key, no question."""
    body = call(corpus, "search_questions", {"limit": 200})
    assert body["count"] == 40, "the 8 scheme-less records must not be served"
    for q in body["questions"]:
        assert q["hasAnswerKey"] is True


def test_an_agent_can_audit_the_unanswerable_set_only_by_asking(corpus):
    body = call(corpus, "search_questions", {"answer_key_state": "none", "limit": 200})
    assert body["count"] == 8
    for q in body["questions"]:
        assert q["hasAnswerKey"] is False


def test_official_scheme_filter_available(corpus):
    body = call(corpus, "search_questions", {"answer_key_state": "official", "limit": 200})
    assert body["count"] == 40


def test_the_scheme_travels_with_a_search_result(corpus):
    """An agent assembling a paper needs the answer, not a second round trip."""
    body = call(corpus, "search_questions", {"limit": 1})
    q = body["questions"][0]
    assert q["answerScheme"]["provenance"] == "cbse_marking_scheme"
    assert q["answerScheme"]["markingPoints"]


# --------------------------------------------------------------------------- #
# filtering
# --------------------------------------------------------------------------- #

def test_filters_narrow_the_set(corpus):
    body = call(corpus, "search_questions", {"subject": "Mathematics", "grade": 8,
                                             "limit": 200})
    assert body["count"] == 40
    assert call(corpus, "search_questions", {"grade": 9, "limit": 200})["count"] == 0


def test_topic_filter_matches_the_content_code_too(corpus):
    by_topic = call(corpus, "search_questions", {"topic": "Algebra", "limit": 200})
    assert by_topic["count"] == 20


def test_marks_filter(corpus):
    one = call(corpus, "search_questions", {"marks": 1, "limit": 200})
    assert one["count"] == 8
    assert all(q["marks"] == 1 for q in one["questions"])


def test_keyword_filter(corpus):
    body = call(corpus, "search_questions", {"keyword": "Geometry", "limit": 200})
    assert body["count"] == 20


# --------------------------------------------------------------------------- #
# get_question / get_answer_key
# --------------------------------------------------------------------------- #

def test_get_question_returns_the_whole_record(corpus):
    q = call(corpus, "get_question", {"question_id": "t:q:1"})
    assert q["id"] == "t:q:1"
    assert q["rights"]["origin"] == "CBSE"
    assert q["provenance"]["pageNumber"] == 3


def test_get_question_says_so_when_absent(corpus):
    assert "error" in call(corpus, "get_question", {"question_id": "nope"})


def test_get_answer_key_is_scheme_only(corpus):
    body = call(corpus, "get_answer_key", {"question_id": "t:q:1"})
    assert body["hasAnswerKey"] is True
    assert body["provenance"] == "cbse_marking_scheme"
    assert "stem" not in body


def test_get_answer_key_reports_none_rather_than_pretending(corpus):
    body = call(corpus, "get_answer_key", {"question_id": "t:q:100"})
    assert body["hasAnswerKey"] is False
    assert body["provenance"] == "none"
    assert body["markingPoints"] == []


# --------------------------------------------------------------------------- #
# topics and marks distribution
# --------------------------------------------------------------------------- #

def test_list_topics_reports_counts_and_marks_spread(corpus):
    body = call(corpus, "list_topics", {"subject": "Mathematics", "grade": 8})
    assert body["count"] >= 2
    algebra = next(t for t in body["topics"] if t["topic"] == "Algebra")
    assert algebra["count"] == 20
    assert algebra["withAnswerKey"] == 20
    assert algebra["marksDistribution"]


def test_marks_distribution_reports_what_is_missing(corpus):
    """The requirement is 'all ranges of questions based on marks distribution',
    so a report that lists only what exists hides the gap."""
    body = call(corpus, "marks_distribution",
                {"subject": "Mathematics", "grade": 8, "topic": "Algebra"})
    assert body["total"] == 20
    # The fixture carries 1-5 mark questions; 6 is a real mark value in the
    # curriculum and is genuinely absent, so the tool must say so rather than
    # reporting only what it found.
    assert body["missingMarks"] == [6]


def test_marks_distribution_names_the_gaps_when_there_are_any(corpus):
    body = call(corpus, "marks_distribution",
                {"subject": "Mathematics", "grade": 8, "topic": "Geometry"})
    present = {d["marks"] for d in body["distribution"]}
    for m in body["missingMarks"]:
        assert m not in present


# --------------------------------------------------------------------------- #
# coverage -- the honesty tool
# --------------------------------------------------------------------------- #

def test_coverage_report_counts_the_unanswerable_rather_than_hiding_them(corpus):
    body = call(corpus, "coverage_report")
    assert body["questions"] == 48
    assert body["withAnswerKey"] == 40
    assert body["answerKeyCoverage"] == pytest.approx(40 / 48, abs=0.001)
    assert "excluded from every search by default" in body["note"]


# --------------------------------------------------------------------------- #
# build_paper
# --------------------------------------------------------------------------- #

def test_build_paper_fills_the_sections(corpus):
    body = call(corpus, "build_paper", {
        "subject": "Mathematics", "grade": 8,
        "sections": [{"marks": 1, "count": 3}, {"marks": 2, "count": 2}],
    })
    assert body["complete"] is True
    assert body["questionCount"] == 5
    assert body["totalMarks"] == 3 * 1 + 2 * 2
    assert body["gaps"] == []


def test_build_paper_reports_a_shortfall_instead_of_returning_a_short_paper(corpus):
    """Silently returning fewer questions than asked is how a teacher ends up
    holding a paper that does not sum to its own blueprint."""
    body = call(corpus, "build_paper", {
        "subject": "Mathematics", "grade": 8,
        "sections": [{"marks": 1, "count": 50}],
    })
    assert body["complete"] is False
    assert body["gaps"] and body["gaps"][0]["shortfall"] > 0


def test_build_paper_never_reuses_a_question(corpus):
    body = call(corpus, "build_paper", {
        "subject": "Mathematics", "grade": 8,
        "sections": [{"marks": 1, "count": 4}, {"marks": 1, "count": 4}],
    })
    ids = [q["id"] for q in body["questions"]]
    assert len(ids) == len(set(ids))


def test_build_paper_only_uses_questions_it_can_mark(corpus):
    body = call(corpus, "build_paper", {
        "subject": "Mathematics", "grade": 8,
        "sections": [{"marks": 2, "count": 10}],
    })
    assert all(q["hasAnswerKey"] for q in body["questions"])


# --------------------------------------------------------------------------- #
# resources
# --------------------------------------------------------------------------- #

def test_resources_are_registered_and_readable(corpus):
    from mcp import Client

    mcp = build_server(corpus)

    async def run():
        async with Client(mcp) as client:
            listed = await client.list_resources()
            return [str(r.uri) for r in listed.resources]

    uris = asyncio.run(run())
    assert any("catalog" in u for u in uris)
