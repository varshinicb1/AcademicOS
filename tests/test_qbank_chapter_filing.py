"""The question-bank API and the MCP server file chapters the way the builder does.

Audit D39 (2026-09-27): `f9ead42` moved the builder onto
`assessment/chapter_filing.py` and left `/v1 ?chapter_id=` and the MCP `topic`
filter matching each record's raw `chapterIds`. Over the 124 named class 6-10
Mathematics/Science chapters the surfaces reached: chapter view 2,297,
`pool.filter` 2,297, `/v1` 1,266, MCP topic by id 1,268, MCP by name 79.
Mathematics 6 "Lines and Angles" printed 14 questions on a paper, of which `/v1`
could return 0. D10, carried with it: "Life Processes" found 0 over MCP while
"life-processes" found 69, and "10.1.1" was listed at 1 and searched at 6.

These run on the committed served bank, like tests/test_chapter_filing.py,
whose fixture this borrows: the chapter view is the builder's picker, and that
file already holds the picker equal to the paths a paper draws through.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.api.main import app  # noqa: E402
from academicos.assessment import pillar_routes, pool as pool_module  # noqa: E402
from academicos.assessment import qbank_routes  # noqa: E402
from academicos.assessment.qbank_engine import QuestionBank  # noqa: E402
from academicos.mcp.qbank_server import Corpus  # noqa: E402

SERVED_BANK = ROOT / "academicos-data" / "syllabus" / "questions.json"
CORE = [(subject, grade) for grade in range(6, 11) for subject in ("Mathematics", "Science")]
EVERYTHING = 100_000

pytestmark = pytest.mark.skipif(not SERVED_BANK.exists(), reason="served bank not built")


@pytest.fixture(scope="module")
def records() -> list[dict]:
    return json.loads(SERVED_BANK.read_text(encoding="utf-8"))["questions"]


@pytest.fixture
def views(tmp_path, monkeypatch) -> dict[tuple[str, int], list[dict]]:
    """The builder's chapter picker for every class 6-10 Maths/Science pair."""
    from academicos.assessment import audit_log, users as users_mod
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr(audit_log, "_INSTANCE", None)
    monkeypatch.setattr(users_mod, "_INSTANCE", None)
    pool_module._CACHE.clear()
    try:
        with TestClient(app) as client:
            pillar_routes._cfg._load_baked_questions = True
            out = {}
            for subject, grade in CORE:
                r = client.get(f"/api/v1/catalog/{subject}/{grade}/chapters")
                assert r.status_code == 200, r.text
                out[(subject, grade)] = r.json()
            yield out
    finally:
        pool_module._CACHE.clear()


def _chapters(views):
    for (subject, grade), entries in views.items():
        for e in entries:
            if e["questionCount"]:
                yield subject, grade, e


def test_v1_chapter_id_reaches_what_the_picker_counts(views, records):
    bank = QuestionBank(records)
    shown = reached = 0
    wrong = []
    for subject, grade, e in _chapters(views):
        _items, _cursor, total = bank.page(subject=subject, grade=grade,
                                           chapter_id=e["chapterId"], limit=1)
        shown += e["questionCount"]
        reached += total
        if total != e["questionCount"]:
            wrong.append((subject, grade, e["chapterId"], e["questionCount"], total))
    assert wrong == [], wrong[:10]
    assert shown == reached and shown > 4000, (shown, reached)


def test_v1_chapter_id_alone_stays_in_its_class(views, records):
    """A chapter id names one class's book, so it needs no subject or grade
    beside it and reaches no other class. It may reach the same class's
    variants: "Mathematics (Standard)" 10 has no syllabus file of its own, so
    its records keep their own tag, and four of them are tagged
    `mathematics-10/real-numbers` -- which is what they are about."""
    bank = QuestionBank(records)
    for subject, grade, e in _chapters(views):
        if e["chapterId"] == "unmapped":
            continue
        items, _cursor, _total = bank.page(chapter_id=e["chapterId"], limit=EVERYTHING)
        assert {r["grade"] for r in items} == {grade}, (subject, grade, e["chapterId"])
        assert {r["subject"].split(" (")[0] for r in items} == {subject}, e["chapterId"]
        assert sum(1 for r in items if r["subject"] == subject) == e["questionCount"]


def test_mcp_topic_by_chapter_id_reaches_what_the_picker_counts(views, records):
    corpus = Corpus(records)
    wrong = []
    for subject, grade, e in _chapters(views):
        n = len(corpus.search(subject=subject, grade=grade, topic=e["chapterId"],
                              limit=EVERYTHING))
        if n != e["questionCount"]:
            wrong.append((subject, grade, e["chapterId"], e["questionCount"], n))
    assert wrong == [], wrong[:10]


def test_mcp_topic_by_chapter_name_reaches_the_same_questions(views, records):
    """D10: an agent asks for "Life Processes", the name the book prints."""
    corpus = Corpus(records)
    wrong = []
    for subject, grade, e in _chapters(views):
        if e["chapterId"] == "unmapped":
            continue
        n = len(corpus.search(subject=subject, grade=grade, topic=e["chapterName"],
                              limit=EVERYTHING))
        if n != e["questionCount"]:
            wrong.append((subject, grade, e["chapterName"], e["questionCount"], n))
    assert wrong == [], wrong[:10]


def test_list_topics_counts_each_chapter_as_the_picker_does(views, records):
    corpus = Corpus(records)
    wrong = []
    for (subject, grade), entries in views.items():
        listed = {t["topic"]: t["count"] for t in corpus.topics(subject=subject, grade=grade)}
        for e in entries:
            if e["questionCount"] and listed.get(e["chapterId"], 0) != e["questionCount"]:
                wrong.append((subject, grade, e["chapterId"], e["questionCount"],
                              listed.get(e["chapterId"], 0)))
    assert wrong == [], wrong[:10]


def test_every_listed_topic_searches_to_its_listed_count(records):
    """D10: "10.1.1" was listed at 1 and searched at 6, because a listed label
    was matched as a substring of "10.1.10", "10.1.11" and the rest."""
    corpus = Corpus(records)
    wrong = []
    for subject, grade in CORE:
        for t in corpus.topics(subject=subject, grade=grade):
            n = len(corpus.search(subject=subject, grade=grade, topic=t["topic"],
                                  limit=EVERYTHING))
            if n != t["count"]:
                wrong.append((subject, grade, t["topic"], t["count"], n))
    assert wrong == [], wrong[:10]


def test_the_audits_reproduction_over_http(tmp_path):
    """Mathematics 6 "Lines and Angles": 16 in the picker, 0 on `/v1`."""
    qbank_routes.init(tmp_path / "keys.sqlite", SERVED_BANK)
    api = FastAPI()
    api.include_router(qbank_routes.router)
    plaintext, _ = qbank_routes._store.create(school_id="s", scopes=["questions:read"],
                                              quota_per_minute=60)
    r = TestClient(api).get(
        "/v1/questions", headers={"Authorization": f"Bearer {plaintext}"},
        params={"chapter_id": "mathematics-6/lines-and-angles", "limit": 1})
    assert r.status_code == 200, r.text
    assert r.json()["totalMatching"] > 0, r.json()


def test_a_record_carrying_two_spellings_of_its_chapter_is_counted_once():
    """40 listed, 38 searched: a question filed as "Heredity" (its taxonomy name) and "heredity" (its
    chapter id) was one bucket's count twice."""
    rec = {"id": "q1", "subject": "Science", "grade": 10, "marks": 2, "type": "short_answer",
           "stem": "Why do traits of parents reach their offspring?", "chapterIds": ["heredity"],
           "taxonomyChapterId": "science-10/heredity", "topic": "Heredity", "source": "cbse_board_paper",
           "answerScheme": {"totalMarks": 2, "provenance": "cbse_marking_scheme", "modelAnswer": "genes",
                            "markingPoints": [{"id": "a", "description": "genes", "marks": 2}]}}
    corpus = Corpus([rec])
    topics = [t for t in corpus.topics(subject="Science", grade=10, require_answer_key=False)
              if t["topic"].lower() == "heredity"]
    assert [t["count"] for t in topics] == [1], topics
