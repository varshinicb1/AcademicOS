"""Every printed thing carries the caller's own school's name, and no
printed thing carries a placeholder or the product's name (audit D41, EX-5).

Review of #49 (2026-09-29) found three holes the first tests did not reach:
- the corrected scan sheet and the progress report read "school_1"'s
  branding for every school; the fix had no test, so reverting it passed;
- the answer key printed no school name at all;
- the page footer (PDF and Word) fell back to "AcademicOS" when the branding
  was a placeholder.
"""
from __future__ import annotations

import zipfile

from academicos.assessment.docx_export import export_docx
from academicos.assessment.pdf import export_answer_key_pdf, export_pdf
from academicos.assessment.schemas import SchoolTemplate

from _auth_helpers import grant_consent, register_invited
from test_assessment_pdf import _extract_text, _make_paper
from test_assessment_routes_auth import _boot_client, _register
from test_route_inventory import blueprint_body, question_body

PLACEHOLDER = SchoolTemplate(id="default", school_id="school_1", name="Default CBSE Template")


def _docx_text(path) -> str:
    with zipfile.ZipFile(path) as z:
        return "".join(z.read(n).decode("utf-8") for n in z.namelist() if n.startswith("word/"))


def test_no_footer_prints_a_placeholder_or_the_products_name(tmp_path):
    paper = _make_paper()
    for text in (_extract_text(export_pdf(paper, tmp_path, template=PLACEHOLDER)),
                 _docx_text(export_docx(paper, tmp_path, template=PLACEHOLDER))):
        assert "Default CBSE Template" not in text
        assert "AcademicOS" not in text
        assert "Q.P. Code" in text, "the paper code still prints"


def test_the_answer_key_prints_the_schools_name(tmp_path):
    paper = _make_paper()
    named = SchoolTemplate(id="t1", school_id="school_1", name="Sunrise Public School")
    assert "Sunrise Public School" in _extract_text(export_answer_key_pdf(paper, tmp_path, template=named))
    unnamed = _extract_text(export_answer_key_pdf(paper, tmp_path, template=PLACEHOLDER))
    assert "Default CBSE Template" not in unnamed and "AcademicOS" not in unnamed
    assert "MARKING SCHEME" in unnamed


def test_a_schools_report_and_corrected_sheet_carry_its_own_name(tmp_path, monkeypatch):
    """School 2's progress report and corrected scan sheet print school 2's
    name, never school 1's: both routes read "school_1" before #49."""
    from academicos.assessment import grade_lock, mobile_routes, mobile_scan, pillar_routes

    client = _boot_client(tmp_path, monkeypatch)
    with client:
        for school, email, name in (("school_1", "p1@example.com", "Alpha Public School"),
                                    ("school_2", "p2@example.com", "Beta Public School")):
            p = _register(client, school, email, "Principal", principal_key="test-bootstrap-key")
            r = client.put("/api/v1/curriculum/school-profile", json={"name": name},
                           headers={"Authorization": f"Bearer {p['token']}"})
            assert r.status_code == 200, r.text

        teacher = register_invited(client, "school_2", "t2@example.com")
        student = register_invited(client, "school_2", "s2@example.com", name="Asha", role="student")
        auth = {"Authorization": f"Bearer {teacher['token']}"}
        sid = student["user"]["id"]
        created = client.post("/api/v1/assessments", json={
            "teacherId": teacher["user"]["id"], "schoolId": "school_2", "title": "Unit test",
            "subject": "Mathematics", "grade": 10, "chapterIds": [], "blueprint": blueprint_body(),
        }, headers=auth)
        assert created.status_code == 200, created.text
        aid = created.json()["id"]
        grant_consent("school_2", sid)
        r = client.post("/api/v1/evaluations/sheet", json={
            "assessmentId": aid, "studentId": sid, "studentName": "Asha",
            "questions": [question_body()], "answers": {"q_1": "an answer"}, "correctOptions": {},
        }, headers=auth)
        assert r.status_code == 200, r.text
        r = client.post(f"/api/v1/evaluations/sheet/{aid}/{sid}/finalize", json={}, headers=auth)
        assert r.status_code == 200, r.text

        report = client.get(f"/api/v1/knowledge/{sid}/report", headers=auth)
        assert report.status_code == 200, report.text
        (tmp_path / "report.pdf").write_bytes(report.content)
        text = _extract_text(tmp_path / "report.pdf")
        assert "Beta Public School" in text and "Alpha Public School" not in text

        # The corrected sheet: the finalize route hands the renderer the
        # caller's school's branding. The render itself is stubbed, as in
        # test_grade_integrity, because the session has no captured pages.
        scan = client.post("/api/v1/scan/sessions", json={
            "assessmentId": aid, "studentId": sid, "studentName": "Asha"}, headers=auth)
        assert scan.status_code == 200, scan.text
        session = mobile_scan.get_session(scan.json()["id"])
        session.review = [mobile_scan.ReviewItem(
            question_id="q_1", display_number=1, stem="stem", max_marks=2, student_answer="answer",
            awarded_marks=0, verdict="blank", confidence=0.9, reasoning="", marking_points=[],
            ocr_warnings=[], needs_review=False, status="approved", teacher_marks=0)]
        mobile_scan.save_session(session)
        # A scan cannot finalize over a sheet already finalized by hand:
        # clear that record so the scan route reaches its render.
        [(q1, _ev)] = pillar_routes._require_graded().get(aid, sid)
        monkeypatch.setattr(grade_lock, "is_finalized", lambda *a, **k: False)
        monkeypatch.setattr(mobile_routes, "_questions_by_id", lambda *a: {"q_1": q1})
        monkeypatch.setattr(mobile_scan, "export_raw_booklet_pdf", lambda *a, **k: None)
        printed = {}
        monkeypatch.setattr(mobile_scan, "export_corrected_pdf",
                            lambda *a, template=None, **k: printed.setdefault("name", template.name))
        r = client.post(f"/api/v1/scan/sessions/{session.id}/finalize", headers=auth)
        assert r.status_code == 200, r.text
        assert printed["name"] == "Beta Public School"
