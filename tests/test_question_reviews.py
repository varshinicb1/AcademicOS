"""The question bank as a school sees it (operations/question_reviews.py):
coverage by class, subject, chapter and topic with each answer's trust tier;
a review queue of checked answers for the principal or a qbank_review admin;
and a school's rejection keeping that question out of its own papers and
homework only."""
from __future__ import annotations

import pytest

from test_homework import w  # noqa: F401 - `w` is a fixture
from test_paper_swap_pick import _pool, _rec


def _checked(qid, topic, *, provenance="textbook_grounded", source="ai_generated"):
    r = _rec(qid, 2, "light", 1, stem=f"Why does {qid} happen?")
    r["answerScheme"]["provenance"] = provenance
    r["answerScheme"]["metadata"] = {"evidence": [{"quote": "Light travels in straight lines.", "page": 3}]}
    r["source"] = source
    r["metadata"] = {"topicTitle": topic, "chapterName": "Light"}
    return r


@pytest.fixture
def bank(monkeypatch):
    from academicos.assessment import qbank_routes
    from academicos.assessment.qbank_engine import QuestionBank
    records = [_rec("b1", 1, "light", 0), _rec("b2", 3, "light", 2),
               _checked("g1", "Reflection"), _checked("g2", "Reflection"), _checked("g3", "Refraction"),
               _checked("s1", "Refraction", provenance="two_model_solved", source="ncert_textbook")]
    monkeypatch.setattr(qbank_routes, "_bank", QuestionBank(records))
    return records


def test_the_coverage_map_splits_published_and_checked_by_chapter_and_topic(w, bank):
    r = w.c.get("/api/v1/qbank/coverage-map", params={"grade": 10}, headers=w.ana)
    assert r.status_code == 200, r.text
    [science] = r.json()["subjects"]
    assert (science["questions"], science["published"], science["checked"], science["generated"]) == (6, 2, 4, 3)
    [chapter] = science["chapters"]
    assert chapter["chapterName"] == "Light"
    topics = {t["topic"]: t["questions"] for t in chapter["topics"]}
    assert topics["Reflection"] == 2 and topics["Refraction"] == 2
    assert r.json()["pendingReview"] == 4
    assert w.c.get("/api/v1/qbank/coverage-map", headers=w.s1).status_code == 403


def test_a_reviewer_approves_and_rejects_for_their_school_only(w, bank):
    q = w.c.get("/api/v1/qbank/review-queue", params={"grade": 10}, headers=w.p).json()
    assert q["total"] == 4 and q["counts"] == {"pending": 4, "approved": 0, "rejected": 0}
    first = q["items"][0]
    assert first["evidence"][0]["quote"] == "Light travels in straight lines."
    assert w.c.post("/api/v1/qbank/review/g1", json={"decision": "approved"}, headers=w.p).json()["decision"] == "approved"
    assert w.c.post("/api/v1/qbank/review/g2", json={"decision": "rejected", "note": "ambiguous"},
                    headers=w.p).json()["decision"] == "rejected"
    counts = w.c.get("/api/v1/qbank/review-queue", headers=w.p).json()["counts"]
    assert counts == {"pending": 2, "approved": 1, "rejected": 1}
    # another school's queue is untouched
    assert w.c.get("/api/v1/qbank/review-queue", headers=w.p2).json()["counts"]["pending"] == 4
    # teachers without the grant, and students, cannot review
    assert w.c.post("/api/v1/qbank/review/g3", json={"decision": "approved"}, headers=w.ana).status_code == 403
    assert w.c.get("/api/v1/qbank/review-queue", headers=w.s1).status_code == 403
    assert w.c.post("/api/v1/qbank/review/nope", json={"decision": "approved"}, headers=w.p).status_code == 404


def test_a_rejected_question_is_not_drawn_for_that_school(w, bank):
    from academicos.assessment.pool import CURRENT_SCHOOL
    w.c.post("/api/v1/qbank/review/g2", json={"decision": "rejected"}, headers=w.p)
    pool = _pool(bank)
    token = CURRENT_SCHOOL.set("school_1")
    try:
        assert "g2" not in {q.id for q in pool.filter()}
    finally:
        CURRENT_SCHOOL.reset(token)
    token = CURRENT_SCHOOL.set("school_2")
    try:
        assert "g2" in {q.id for q in pool.filter()}, "another school still draws it"
    finally:
        CURRENT_SCHOOL.reset(token)
    assert "g2" in {q.id for q in pool.filter()}, "outside a request nothing is left out"
