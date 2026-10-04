"""Marks entry and result analysis (EX-8): a grid of marks per question for
a section, bounded by each question's marks, consent-gated, analysed by
question, chapter and class, and fed into learning progress."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from test_assessment_routes_auth import _assessment_body
from test_homework import BANK, w  # noqa: F401 - `w` is a fixture


@pytest.fixture
def paper(w, monkeypatch):
    from academicos.assessment import marks_routes
    from academicos.assessment import routes as ar
    from academicos.assessment.schemas import (GeneratedPaper, GeneratedQuestionSchema, GeneratedSectionSchema,
                                               PaperMetadataSchema, QuestionSchema)
    monkeypatch.setattr(marks_routes, "_bank_schemas", lambda subject, grade, qids: {
        q["id"]: QuestionSchema.model_validate(q) for q in BANK if q["id"] in qids})
    created = w.c.post("/api/v1/assessments", json=_assessment_body("asmt_marks"), headers=w.ana)
    assert created.status_code == 200, created.text
    aid = created.json()["id"]
    qs = [GeneratedQuestionSchema(question_id=q["id"], display_number=i + 1, stem=q["stem"], marks=q["marks"],
                                  bloom_level="remember", difficulty="easy") for i, q in enumerate(BANK[:3])]
    p = GeneratedPaper(id="paper_marks", assessment_id=aid,
                       sections=[GeneratedSectionSchema(section_id="A", label="A", name="Section A", total_marks=4,
                                                        questions=qs)],
                       metadata=PaperMetadataSchema(assessment_title="Light test", subject="Science", grade=10,
                                                    total_marks=4, duration_minutes=40,
                                                    generated_at=datetime.now(timezone.utc), generated_by="test",
                                                    version="1.0"))
    ar._require_papers().save(p, school_id="school_1")
    return "paper_marks"


def _put(w, paper, body, who=None, section=None):
    return w.c.put(f"/api/v1/papers/{paper}/marks", params={"sectionId": section or w.a10}, json=body,
                   headers=who or w.ana)


def _cell(w, student, q, m):
    return {"studentId": w.ids[student], "questionId": q, "marks": m}


def test_entering_marks_fills_the_grid(w, paper):
    r = _put(w, paper, {"entries": [_cell(w, "s1", "q1", 1), _cell(w, "s1", "q2", 1), _cell(w, "s1", "q3", 2)],
                        "absent": [w.ids["s2"]]})
    assert r.status_code == 200, r.text
    grid = r.json()
    assert grid["totalMarks"] == 4 and [q["number"] for q in grid["questions"]] == ["A1", "A2", "A3"]
    rows = {x["studentId"]: x for x in grid["rows"]}
    assert rows[w.ids["s1"]]["total"] == 4 and rows[w.ids["s1"]]["percent"] == 100 and rows[w.ids["s1"]]["band"] == "A1"
    assert rows[w.ids["s2"]]["absent"] is True and rows[w.ids["s2"]]["total"] is None
    # correcting one cell keeps the others
    grid = _put(w, paper, {"entries": [_cell(w, "s1", "q3", 1)]}).json()
    assert {x["studentId"]: x for x in grid["rows"]}[w.ids["s1"]]["total"] == 3
    assert w.c.get("/api/v1/my-learning", headers=w.s1).json()["sources"]["test"] == 1


def test_marks_are_bounded_and_consented(w, paper):
    from academicos.assessment import consent_routes
    too_many = _put(w, paper, {"entries": [_cell(w, "s1", "q3", 3)]})
    assert too_many.status_code == 422
    # The grid's own number and the child's name, never the bank id (QA P-19).
    assert too_many.json()["detail"] == "A3 for Asha: 3 is more than its 2 marks"
    assert _put(w, paper, {"entries": [_cell(w, "s1", "zz", 1)]}).status_code == 422
    assert _put(w, paper, {"entries": [_cell(w, "s1", "q1", 1)], "absent": [w.ids["s1"]]}).status_code == 422
    assert _put(w, paper, {"entries": [{"studentId": "nobody", "questionId": "q1", "marks": 1}]}).status_code == 422
    consent_routes._require_store().revoke_consent(school_id="school_1", student_id=w.ids["s2"],
                                                   revoked_by="test-fixture")
    assert _put(w, paper, {"entries": [_cell(w, "s2", "q1", 1)]}).status_code == 409
    assert _put(w, paper, {"entries": [_cell(w, "s1", "q1", 1)]}, who=w.s1).status_code == 403
    assert w.c.get(f"/api/v1/papers/{paper}/marks", headers=w.p2).status_code == 403


def test_the_analysis(w, paper):
    _put(w, paper, {"entries": [_cell(w, "s1", "q1", 1), _cell(w, "s1", "q2", 0), _cell(w, "s1", "q3", 2),
                                _cell(w, "s2", "q1", 0), _cell(w, "s2", "q2", 0), _cell(w, "s2", "q3", 1)]})
    a = w.c.get(f"/api/v1/papers/{paper}/analysis", params={"sectionId": w.a10}, headers=w.ana).json()
    by_q = {q["questionId"]: q for q in a["questions"]}
    assert by_q["q2"]["facility"] == 0 and by_q["q1"]["facility"] == 0.5 and by_q["q3"]["facility"] == 0.75
    assert a["weakest"][0] == "A2"
    assert a["summary"]["students"] == 2 and a["summary"]["meanPercent"] == 50.0
    assert a["summary"]["bands"]["B1"] == 1 and a["summary"]["bands"]["E"] == 1      # 75% and 25%
    assert [c["name"] for c in a["chapters"]] == ["light"] and a["chapters"][0]["questions"] == 3


def test_a_partly_entered_row_is_incomplete_and_left_out_of_the_class_figures(w, paper):
    """v3 audit N-2-10: a row with only some cells entered was graded over the
    whole paper (5 of 38 cells read 5.0, 6.2%, band E) and averaged into the
    class. It is now marked incomplete, ungraded, and left out of the class
    figures; its entered cells still count for their questions."""
    r = _put(w, paper, {"entries": [_cell(w, "s1", "q1", 1), _cell(w, "s1", "q2", 1), _cell(w, "s1", "q3", 2),
                                    _cell(w, "s2", "q3", 1)]})
    assert r.status_code == 200, r.text
    rows = {x["studentId"]: x for x in r.json()["rows"]}
    done, part = rows[w.ids["s1"]], rows[w.ids["s2"]]
    assert done["complete"] is True and (done["total"], done["percent"], done["band"]) == (4, 100, "A1")
    assert part["complete"] is False and part["marks"] == {"q3": 1}, "what was entered is kept"
    assert (part["total"], part["percent"], part["band"]) == (None, None, None), "not graded as a whole paper"
    grid = w.c.get(f"/api/v1/papers/{paper}/marks", params={"sectionId": w.a10}, headers=w.ana).json()
    assert {x["studentId"]: x["complete"] for x in grid["rows"]} == {w.ids["s1"]: True, w.ids["s2"]: False}

    a = w.c.get(f"/api/v1/papers/{paper}/analysis", params={"sectionId": w.a10}, headers=w.ana).json()
    s = a["summary"]
    assert (s["students"], s["absent"], s["incomplete"]) == (2, 0, 1)
    assert (s["meanPercent"], s["medianPercent"], s["lowestPercent"]) == (100.0, 100.0, 100.0)
    assert s["bands"]["A1"] == 1 and sum(s["bands"].values()) == 1, "the incomplete row has no band"
    by_q = {q["questionId"]: q for q in a["questions"]}
    assert (by_q["q3"]["attempted"], by_q["q3"]["facility"]) == (2, 0.75), "entered cells count for their question"
    assert (by_q["q1"]["attempted"], by_q["q1"]["facility"]) == (1, 1.0), "a missing cell is not a zero"

    # Entering the rest grades the row and brings it into the class figures.
    _put(w, paper, {"entries": [_cell(w, "s2", "q1", 0), _cell(w, "s2", "q2", 0)]})
    a = w.c.get(f"/api/v1/papers/{paper}/analysis", params={"sectionId": w.a10}, headers=w.ana).json()
    assert a["summary"]["incomplete"] == 0 and a["summary"]["meanPercent"] == 62.5
    assert a["summary"]["bands"]["E"] == 1


# ---- measured difficulty (EX-3) ----------------------------------------------
#
# Audit 2026-09-30: no source in the bank judges a question's difficulty, so
# Foundation, Standard and Advanced printed identical questions on 14/14
# pairs. The marks teachers enter now measure it: each question's facility
# (mean score over maximum) across every paper, student and school that sat
# it, published from 20 answers, stored as an aggregate only (API-5).

def test_marks_measure_each_questions_facility_without_naming_a_student(w, paper):
    from academicos.assessment import facility
    from academicos.assessment import routes as ar
    from academicos.operations.routes import store

    base = ar._require_papers().get(paper)
    papers = [paper] + [f"{paper}_{i}" for i in range(2, 8)]
    for pid in papers[1:]:
        ar._require_papers().save(base.model_copy(update={"id": pid}), school_id="school_1")

    def sit(pid, q1=(1, 0, 1)):
        # q1 (1 mark): 2 of 3 scored; q2 (1 mark): nobody; q3 (2 marks): 3 of 6.
        cells = [_cell(w, s, "q1", m) for s, m in zip(("s1", "s2", "s3"), q1)]
        cells += [_cell(w, s, "q2", 0) for s in ("s1", "s2", "s3")]
        cells += [_cell(w, s, "q3", m) for s, m in zip(("s1", "s2", "s3"), (2, 1, 0))]
        r = _put(w, pid, {"entries": cells})
        assert r.status_code == 200, r.text

    for pid in papers[:6]:
        sit(pid)
    assert facility.lookup(["q1", "q2", "q3"]) == {}, "18 answers: not yet a measurement"
    sit(papers[6])
    measured = facility.lookup(["q1", "q2", "q3"])
    assert measured["q1"] == (pytest.approx(14 / 21), 21)
    assert measured["q2"] == (0.0, 21) and measured["q3"] == (0.5, 21)
    assert [facility.difficulty_from(measured[q][0]) for q in ("q1", "q2", "q3")] == ["medium", "hard", "medium"]

    # Entering a paper's marks again replaces its part; it does not add to it.
    sit(papers[0], q1=(1, 1, 1))
    assert facility.lookup(["q1"])["q1"] == (pytest.approx(15 / 21), 21)
    # An absent student's cells leave the measurement with them.
    assert _put(w, papers[6], {"absent": [w.ids["s3"]]}).status_code == 200
    assert facility.lookup(["q1"])["q1"] == (pytest.approx(14 / 20), 20)

    # Aggregates only: nothing in the facility tables names a student.
    with store()._conn_lock:
        for table in ("question_facility", "question_facility_parts"):
            columns = {r[1] for r in store().conn.execute(f"PRAGMA table_info({table})")}
            assert not {c for c in columns if "student" in c}, (table, columns)
            assert not any(w.ids[s] in str(tuple(row)) for row in store().conn.execute(f"SELECT * FROM {table}")
                           for s in ("s1", "s2", "s3"))


def test_an_attempt_any_section_is_marked_out_of_its_printed_marks():
    """Review 2026-10-04: an "attempt any 2 of 3" section was counted as 3, so the 80-mark English and
    Hindi papers were graded out of 94, a perfect script read about 85%, and its row was never complete
    until the unanswered question got a mark."""
    from academicos.assessment.marks_routes import paper_score, paper_total
    from academicos.assessment.schemas import (GeneratedPaper, GeneratedQuestionSchema, GeneratedSectionSchema,
                                               PaperMetadataSchema)

    def q(qid, n, marks):
        return GeneratedQuestionSchema(question_id=qid, display_number=n, stem="s", marks=marks,
                                       bloom_level="remember", difficulty="easy")
    paper = GeneratedPaper(id="p", assessment_id="a", metadata=PaperMetadataSchema(
        assessment_title="t", subject="English", grade=10, total_marks=8, duration_minutes=60,
        generated_at=datetime.now(timezone.utc)), sections=[
        GeneratedSectionSchema(section_id="A", label="A", name="Section A (attempt any 2 of 3)", total_marks=2,
                               questions=[q("a1", 1, 1), q("a2", 2, 1), q("a3", 3, 1)]),
        GeneratedSectionSchema(section_id="B", label="B", name="Section B", total_marks=6,
                               questions=[q("b1", 4, 3), q("b2", 5, 3)]),
    ])
    assert paper_total(paper) == 8
    assert paper_score(paper, {"a1": 1, "a2": 1, "b1": 3, "b2": 3}) == 8      # two answered: complete
    assert paper_score(paper, {"a1": 1, "a2": 0, "a3": 1, "b1": 3, "b2": 3}) == 8  # best two of three
    assert paper_score(paper, {"a1": 1, "b1": 3, "b2": 3}) is None           # one of the two missing
    assert paper_score(paper, {"a1": 1, "a2": 1, "b1": 3}) is None           # a plain section needs every mark
    assert paper_score(paper, {}) is None
