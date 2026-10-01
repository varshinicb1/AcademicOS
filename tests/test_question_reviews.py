"""The question bank as a school sees it (operations/question_reviews.py):
coverage by class, subject, chapter and topic with each answer's trust tier;
a review queue of checked answers for the principal or a qbank_review admin;
and a school's rejection keeping that question out of its own papers and
homework only."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from test_homework import w  # noqa: F401 - `w` is a fixture
from test_paper_swap_pick import _rec


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


def test_a_rejected_question_is_not_drawn_for_that_school(w, monkeypatch):
    """Over HTTP, as the web draws: a rejection in school 1 keeps the question
    out of school 1's homework, and a hand-picked rejected question is refused
    by name. Review of #54: the rejection used to ride a context variable set
    in a sync dependency, which never reached the endpoint -- its test set the
    variable by hand, so the feature did nothing over HTTP and passed."""
    from academicos.assessment import qbank_routes
    from academicos.assessment.qbank_engine import QuestionBank
    from academicos.operations import homework_routes as hr
    from academicos.operations.question_reviews import usable
    monkeypatch.setattr(qbank_routes, "_bank", QuestionBank([_checked(q, "Reflection") for q in ("q1", "q2", "q3")]))
    assert w.c.post("/api/v1/qbank/review/q2", json={"decision": "rejected"}, headers=w.p).status_code == 200

    drawn = w.c.post("/api/v1/homework", json={
        "subjectId": w.sci10, "sectionIds": [w.a10], "title": "Light", "dueDate": "2026-06-03",
        "chapterIds": ["light"], "count": 3}, headers=w.ana)
    assert drawn.status_code == 200, drawn.text
    assert "q2" not in {q["id"] for q in drawn.json()["questions"]}

    picked = w.c.post("/api/v1/homework", json={
        "subjectId": w.sci10, "sectionIds": [w.a10], "title": "Light", "dueDate": "2026-06-03",
        "questionIds": ["q1", "q2"]}, headers=w.ana)
    assert picked.status_code == 422 and "rejected" in picked.text and "q2" in picked.text

    # The shared bank is untouched, and another school still draws the question.
    bank = hr._bank_questions("Science", 10, ["light"])
    assert "q2" in {q["id"] for q in bank}
    q2 = SimpleNamespace(id="q2")
    assert usable([q2], "school_2") == [q2] and usable([q2], "school_1") == []


def test_a_rejection_never_changes_the_cached_bank():
    """`bank_usable` returns a copy without the school's rejections; the bank
    `paper_edit.bank_for` caches for every school keeps them."""
    from academicos.assessment.paper_edit import Bank
    from academicos.operations import question_reviews as qr

    class Q:
        def __init__(self, i):
            self.id = i
    qs = tuple(Q(i) for i in ("a", "b", "c"))
    bank = Bank(qs, {q.id: q for q in qs}, frozenset({"a", "b"}))
    original = qr.rejected_for
    try:
        qr.rejected_for = lambda school: frozenset({"b"}) if school == "school_1" else frozenset()
        mine = qr.bank_usable(bank, "school_1")
        assert [q.id for q in mine.questions] == ["a", "c"] and "b" not in mine.by_id and mine.keyed == {"a"}
        assert qr.bank_usable(bank, "school_2") is bank
        assert [q.id for q in bank.questions] == ["a", "b", "c"], "the cached bank is unchanged"
    finally:
        qr.rejected_for = original
