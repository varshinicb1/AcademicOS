"""Defects found by driving every workflow on production's commit (aa301d2)
with a fresh school, 2026-10-01:

  * a logo whose header is right but whose data is broken was accepted, and
    then every paper, answer key and report the school exported failed (the
    renderer decodes images lazily, so the "a bad logo must not kill the
    export" guard never saw the error), with the server's file path in the
    message;
  * the answer key printed an answer twice when its one value point carries it;
  * any teacher of the school could overwrite any paper's marks;
  * school insights counted only scanned sheets, so a school that typed its
    marks read 0 students and 0 papers;
  * a principal approving a review they were asked for left the paper "under
    review", to be approved a second time from the paper.
"""
from __future__ import annotations

import pytest

from test_assessment_pdf import _boot_with_paper, _make_paper
from test_assessment_routes_auth import _assessment_body, _register
from test_homework import w  # noqa: F401 - `w` is a fixture
from test_marks_entry import _cell, _put, paper  # noqa: F401 - `paper` is a fixture
from test_school_profile import _png


def _broken_png() -> bytes:
    """A PNG signature and header over data that does not decompress."""
    good = _png()
    return good[:33] + good[33:41] + b"\x00" * 24 + good[-12:]


def test_a_logo_that_cannot_be_decoded_is_refused_and_never_stops_an_export(tmp_path, monkeypatch):
    from academicos.curriculum.school_profile import image_is_printable
    assert image_is_printable(_png()) and not image_is_printable(_broken_png())

    client, teacher_auth, paper_id = _boot_with_paper(tmp_path, monkeypatch)
    try:
        principal = _register(client, "school_1", "p1@example.com", "Priya", principal_key="test-bootstrap-key")
        p_auth = {"Authorization": f"Bearer {principal['token']}"}
        base = "/api/v1/curriculum/school-profile"
        assert client.put(base, json={"name": "Sunrise Public School"}, headers=p_auth).status_code == 200
        bad = client.post(f"{base}/logo", files={"file": ("l.png", _broken_png(), "image/png")}, headers=p_auth)
        assert bad.status_code == 422 and "could not be read" in bad.json()["detail"]
        assert client.post(f"{base}/logo", files={"file": ("l.png", _png(), "image/png")},
                           headers=p_auth).status_code == 200

        # A logo stored before this check (or damaged on disk) prints nothing
        # instead of stopping every export.
        [stored] = list((tmp_path / "school-media").glob("logo_*"))
        stored.write_bytes(_broken_png())
        for fmt in ("pdf", "answer-key", "docx"):
            r = client.post(f"/api/v1/papers/{paper_id}/export/{fmt}", headers=teacher_auth)
            assert r.status_code == 200, (fmt, r.text)
            got = client.get(r.json()["url"].replace("/api/v1", "/api/v1", 1), headers=teacher_auth)
            assert got.status_code == 200 and len(got.content) > 1000, fmt
    finally:
        client.__exit__(None, None, None)


def test_a_render_error_names_its_cause_but_no_server_path():
    from academicos.assessment.routes import _render_cause
    windows = ValueError("identity=[ImageReader@0x1c3 filename='C:\\Users\\x\\AppData\\data\\logo_s1.png'] broken")
    linux = ValueError("cannot open '/app/academicos-data/school-media/logo_s1.png': broken data stream")
    assert _render_cause(windows) == "identity=[ImageReader@0x1c3 filename='<file>'] broken"
    assert "/app" not in _render_cause(linux) and "broken data stream" in _render_cause(linux)
    assert _render_cause(ValueError("Flowable too large on page 2; ratio 3/4 km/h")) == \
        "Flowable too large on page 2; ratio 3/4 km/h"
    assert _render_cause(ValueError()) == "ValueError"


def _question(model: str, points: list[tuple[str, int]], marks: int, **scheme_meta):
    from academicos.assessment.schemas import AnswerSchemeSchema, MarkingPointSchema, QuestionSchema
    return QuestionSchema(
        id="q", question_bank_id="b", subject="Mathematics", grade=10, bloom_level="remember",
        difficulty="easy", type="mcq" if scheme_meta.get("objective") else "short_answer", stem="?",
        estimated_time_minutes=1, marks=marks, source="teacher_created", created_at="2026-10-01T00:00:00Z",
        updated_at="2026-10-01T00:00:00Z",
        answer_scheme=AnswerSchemeSchema(total_marks=marks, model_answer=model, metadata=scheme_meta,
                                         marking_points=[MarkingPointSchema(id=f"p{i}", description=d, marks=m)
                                                         for i, (d, m) in enumerate(points)]))


def test_the_answer_key_says_an_answer_once():
    from academicos.assessment.paper import answer_key_entry
    mcq = _question("three decimal places", [("Correct option C: three decimal places", 1)], 1, objective=True)
    assert answer_key_entry(mcq) == "Correct option C: three decimal places [1m]"
    whole = _question("Rs 26400", [("Rs 26400", 5)], 5)
    entry = answer_key_entry(whole)
    assert entry.startswith("Rs 26400 [5m]") and entry.count("Rs 26400") == 1
    assert "all or nothing" in entry, "the all-or-nothing note still prints"
    steps = _question("HCF = 6", [("30 = 2 x 3 x 5", 1), ("HCF = 6", 1)], 2)
    assert answer_key_entry(steps).count("HCF = 6") == 2, "a split answer keeps its points"
    different = _question("x = 4", [("uses the quadratic formula", 2)], 2)
    assert "x = 4" in answer_key_entry(different) and "quadratic formula" in answer_key_entry(different)


def test_only_the_papers_teachers_enter_its_marks(w, paper):  # noqa: F811
    cara = _register(w.c, "school_1", "cara@example.com", "Cara")
    cara_h = {"Authorization": f"Bearer {cara['token']}"}
    body = {"entries": [_cell(w, "s1", "q1", 1)]}
    assert _put(w, paper, body, who=cara_h).status_code == 403, "a teacher who does not teach it"
    assert _put(w, paper, body, who=w.bala).status_code == 403, "Bala teaches science, not this maths paper"
    assert _put(w, paper, body).status_code == 200, "the author"
    assert _put(w, paper, body, who=w.p).status_code == 200, "the principal"
    assert w.c.get(f"/api/v1/papers/{paper}/marks", params={"sectionId": w.a10},
                   headers=cara_h).status_code == 200, "reading the grid stays open to staff"
    # A teacher of the paper's subject in its class may, as may an exams admin.
    maths = w.store.create_subject(grade_id=w.store.get_section(w.b10).grade_id, name="Mathematics")
    w.store.set_allocation(section_id=w.b10, subject_id=maths.id, teacher_id=w.c.get(
        "/api/v1/auth/me", headers=w.bala).json()["id"], periods_per_week=6)
    assert _put(w, paper, body, who=w.bala).status_code == 200
    grant = w.c.post("/api/v1/admin/grants", json={"userId": cara["user"]["id"], "capability": "exams"},
                     headers=w.p)
    assert grant.status_code == 200, grant.text
    assert _put(w, paper, body, who=cara_h).status_code == 200


def test_typed_marks_count_in_school_insights(w, paper, monkeypatch):  # noqa: F811
    from academicos.assessment import marks_routes
    from academicos.assessment.schemas import QuestionSchema
    from test_homework import BANK
    monkeypatch.setattr(marks_routes, "_bank_schemas", lambda subject, grade, qids: {
        q["id"]: QuestionSchema.model_validate({**q, "chapterIds": ["light"]}) for q in BANK if q["id"] in qids})
    before = w.c.get("/api/v1/insights/school/school_1", headers=w.p).json()
    assert before["students"] == 0 and before["assessments"] == 0
    assert _put(w, paper, {"entries": [_cell(w, "s1", "q1", 1), _cell(w, "s2", "q1", 0)]}).status_code == 200
    after = w.c.get("/api/v1/insights/school/school_1", headers=w.p).json()
    assert after["students"] == 2 and after["assessments"] == 1, after
    assert w.c.get("/api/v1/insights/school/school_1", headers=w.p2).status_code == 403


def test_the_principal_approving_a_review_locks_the_paper(w):
    r = w.c.post("/api/v1/assessments", json=_assessment_body("asmt_e2e_review"), headers=w.ana)
    aid = r.json()["id"]
    w.c.patch(f"/api/v1/assessments/{aid}/status", json={"status": "paperGenerated"}, headers=w.ana)
    principal = w.c.get("/api/v1/auth/me", headers=w.p).json()["id"]
    assert w.c.post(f"/api/v1/assessments/{aid}/review-request", json={"reviewerId": principal},
                    headers=w.ana).status_code == 200
    ok = w.c.post(f"/api/v1/assessments/{aid}/review-decision", json={"decision": "approve"}, headers=w.p)
    assert ok.status_code == 200 and ok.json()["state"] == "approved"
    assert w.c.get(f"/api/v1/assessments/{aid}", headers=w.ana).json()["status"] == "principalApproved"
    told = [i for i in w.c.get("/api/v1/notifications", headers=w.ana).json()["items"]
            if i["kind"] == "paper_review_decided"]
    assert told and "approved and locked it" in told[0]["body"]
    ready = [i for i in w.c.get("/api/v1/notifications", headers=w.p).json()["items"]
             if i["title"].startswith("Paper ready to approve")]
    assert ready == [], "the principal is not asked to approve what they just approved"


def test_an_exams_admin_cannot_approve_their_own_paper(w):
    ana = w.c.get("/api/v1/auth/me", headers=w.ana).json()["id"]
    assert w.c.post("/api/v1/admin/grants", json={"userId": ana, "capability": "exams"},
                    headers=w.p).status_code == 200
    r = w.c.post("/api/v1/assessments", json=_assessment_body("asmt_e2e_own"), headers=w.ana)
    aid = r.json()["id"]
    w.c.patch(f"/api/v1/assessments/{aid}/status", json={"status": "paperGenerated"}, headers=w.ana)
    assert w.c.patch(f"/api/v1/assessments/{aid}/approve", headers=w.ana).status_code == 403
    assert w.c.patch(f"/api/v1/assessments/{aid}/approve", headers=w.p).status_code == 200


@pytest.mark.parametrize("text", ["declared default"])
def test_the_term_report_names_no_server_setting(text):
    from academicos.assessment import paper_timing
    assert text in paper_timing._DEFAULT_PROVENANCE
    assert "ACOS_" not in paper_timing._DEFAULT_PROVENANCE
