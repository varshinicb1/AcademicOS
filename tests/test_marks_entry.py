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
    assert _put(w, paper, {"entries": [_cell(w, "s1", "q3", 3)]}).status_code == 422
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
