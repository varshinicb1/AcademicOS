"""Learning progress (SA-3): evidence from every marked answer, rolled up to
subject, chapter and topic, what to revise next, and the term by week."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from academicos.operations import learning
from academicos.operations.store import OperationsStore

NOW = datetime(2026, 7, 15, 10, tzinfo=timezone.utc)


def _q(qid, *, subject="Mathematics", grade=10, chapter="mathematics-10/circles", topics=(), chapter_ids=()):
    return SimpleNamespace(id=qid, subject=subject, grade=grade, taxonomy_chapter_id=chapter,
                           topic_ids=list(topics), chapter_ids=list(chapter_ids))


def _ev(got, of=1):
    return SimpleNamespace(awarded_marks=got, max_marks=of)


@pytest.fixture
def ops(tmp_path):
    s = OperationsStore(tmp_path / "ops.sqlite")
    yield s
    s.close()


def test_score_is_recency_weighted_and_cautious_with_little_evidence():
    fresh = {"outcome": 1.0, "occurred_at": NOW.isoformat()}
    assert learning.score([fresh], NOW)["mastery"] == 0.75           # one right answer is not 100%
    assert learning.score([fresh], NOW)["status"] == "early"
    old_wrong = [{"outcome": 0.0, "occurred_at": (NOW - timedelta(days=60)).isoformat()}] * 3
    new_right = [{"outcome": 1.0, "occurred_at": NOW.isoformat()}] * 3
    s = learning.score(old_wrong + new_right, NOW)
    assert s["accuracy"] == 0.5 and s["mastery"] > 0.7, "recent work counts for more"
    assert learning.score([], NOW)["status"] == "not_started"


def test_progress_rolls_up_by_subject_chapter_and_topic(ops):
    tangent = "mathematics-10/circles/tangent-to-a-circle"
    ops.record_learning("s1", [(_q("a", topics=[tangent]), _ev(0)), (_q("b", topics=[tangent]), _ev(0)),
                               (_q("c", topics=[tangent]), _ev(1)), (_q("d"), _ev(1))], "sheet:t1:s1")
    ops.record_learning("s1", [(_q("e", chapter="mathematics-10/real-numbers"), _ev(2, 2))] * 3, None)
    out = ops.learning_progress("s1", now=NOW)
    [maths] = out["subjects"]
    assert maths["subject"] == "Mathematics" and maths["evidence_count"] == 7
    chapters = {c["chapter_id"]: c for c in maths["chapters"]}
    assert chapters["mathematics-10/circles"]["chapter_name"] == "Circles"
    assert chapters["mathematics-10/real-numbers"]["status"] in ("developing", "mastered")
    [topic] = chapters["mathematics-10/circles"]["topics"]
    assert topic["topic_id"] == tangent and topic["evidence_count"] == 3 and topic["status"] == "needs_work"
    # every chapter of the book is listed, the untouched ones as not started, in book order
    assert maths["chapters"][0]["chapter_id"] == "mathematics-10/real-numbers"
    assert any(c["status"] == "not_started" for c in maths["chapters"])
    [first, *_] = out["revise_next"]
    assert first["topic_id"] == tangent and "33% of marks across 3 answers" in first["reason"]
    assert out["sources"] == {"homework": 0, "test": 1, "practice": 1}


def test_a_remarked_sheet_replaces_its_evidence_and_keeps_its_date(ops):
    ops.record_learning("s1", [(_q("a"), _ev(0))], "sheet:t1:s1")
    first = ops.learning_evidence("s1")[0]["occurred_at"]
    ops.record_learning("s1", [(_q("a"), _ev(1))], "sheet:t1:s1")
    [row] = ops.learning_evidence("s1")
    assert row["outcome"] == 1.0 and row["occurred_at"] == first


def test_weeks_run_from_the_term_start_and_show_gaps(ops):
    ops.record_learning("s1", [(_q("a"), _ev(1))], "sheet:t1:s1")
    weeks = ops.learning_progress("s1", now=datetime.now(timezone.utc),
                                  term_start=date.today() - timedelta(days=15))["weekly"]
    assert 3 <= len(weeks) <= 4
    assert weeks[-1]["answered"] == 1 and weeks[-1]["average"] == 1.0
    assert weeks[0]["answered"] == 0 and weeks[0]["average"] is None


# ---------------- through the routes ----------------

from test_homework import _create, w  # noqa: E402,F401 - `w` is a fixture


def test_marked_homework_shows_in_the_students_progress(w):
    hw = _create(w, "ana", questionIds=["q1", "q2"]).json()
    w.c.post(f"/api/v1/my-homework/{hw['id']}/submit", json={"answers": {"q1": "A", "q2": "C"}}, headers=w.s1)
    out = w.c.get("/api/v1/my-learning", headers=w.s1).json()
    assert out["sources"]["homework"] == 1
    [science] = out["subjects"]
    assert science["subject"] == "Science" and science["grade"] == 10 and science["evidenceCount"] == 2
    [light] = [c for c in science["chapters"] if c["chapterId"] == "light"]
    assert light["accuracy"] == 0.5
    assert w.c.get("/api/v1/my-learning", headers=w.ana).status_code == 403              # students only

    sid = w.ids["s1"]
    assert w.c.get(f"/api/v1/students/{sid}/learning", headers=w.ana).json()["sources"]["homework"] == 1
    assert w.c.get(f"/api/v1/students/{sid}/learning", headers=w.s1).status_code == 200  # themselves
    assert w.c.get(f"/api/v1/students/{sid}/learning", headers=w.s2).status_code == 403  # a classmate
    assert w.c.get(f"/api/v1/students/{sid}/learning", headers=w.p2).status_code == 403  # another school


def test_practice_and_sheets_feed_progress_through_the_knowledge_store(w):
    from academicos.assessment import pillar_routes
    from academicos.assessment.evaluate import Evaluation
    from academicos.assessment.schemas import QuestionSchema
    from test_homework import BANK
    _, knowledge, _ = pillar_routes._require()
    q = QuestionSchema.model_validate(BANK[3])
    ev = Evaluation(question_id=q.id, awarded_marks=1, max_marks=1, verdict="fullCredit", confidence=0.9,
                    reasoning="")
    knowledge.record_evaluations(w.ids["s2"], [(q, ev)])
    knowledge.record_sheet(w.ids["s2"], [(q, ev)], "sheet:a1:" + w.ids["s2"])
    out = w.c.get("/api/v1/my-learning", headers=w.s2).json()
    assert out["sources"] == {"homework": 0, "test": 1, "practice": 1}
