"""CBSE-format paper renderer (assessment/pdf.py).

Verify the watermark_id parameter threading through _page_furniture/export_pdf:
the generated PDF's actual bytes contain the watermark id text when one is
passed, and contain no watermark text when it is None. PDFs are read back with
PyMuPDF (fitz), the same pattern used elsewhere in this repo.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.assessment.pdf import (
    escape,
    export_pdf,
    split_stem_and_options,
)
from academicos.assessment.schemas import (
    GeneratedPaper,
    GeneratedQuestionSchema,
    GeneratedSectionSchema,
    PaperMetadataSchema,
)


def _make_paper(paper_id: str = "paper_ab12cd", title: str = "Mid Term Examination"):
    now = datetime.now(timezone.utc)
    gq = GeneratedQuestionSchema(
        question_id="q1", display_number=1,
        stem="Which of the following is a gas? (A) Oxygen (B) Gold (C) Silver (D) Copper",
        marks=1, bloom_level="remember", difficulty="easy",
    )
    section = GeneratedSectionSchema(
        section_id="section-a", label="A", name="MCQ", questions=[gq], total_marks=1,
    )
    metadata = PaperMetadataSchema(
        assessment_title=title, subject="Science", grade=10, total_marks=1,
        duration_minutes=60, generated_at=now,
    )
    return GeneratedPaper(
        id=paper_id, assessment_id="assess1", sections=[section], metadata=metadata,
        answer_key={"1": "Oxygen"},
    )


def _extract_text(pdf_path: Path) -> str:
    import fitz

    doc = fitz.open(str(pdf_path))
    try:
        return "".join(page.get_text() for page in doc)
    finally:
        doc.close()


WATERMARK = "Z9-TRACE-42"


def test_export_pdf_embeds_watermark_id(tmp_path):
    out = export_pdf(_make_paper(), tmp_path / "a", watermark_id=WATERMARK)
    assert out.exists()
    text = _extract_text(out)
    assert WATERMARK in text
    assert "Confidential" in text
    assert "traceable copy" in text


def test_export_pdf_without_watermark_has_none(tmp_path):
    out = export_pdf(_make_paper(), tmp_path / "b")
    assert out.exists()
    text = _extract_text(out)
    assert WATERMARK not in text
    assert "Confidential" not in text
    assert "traceable copy" not in text
    # ordinary furniture still present
    assert "Q.P. Code" in text
    assert "Page 1" in text


def test_watermark_differs_per_export(tmp_path):
    a = _extract_text(export_pdf(_make_paper(), tmp_path / "a", watermark_id="COPY-001"))
    b = _extract_text(export_pdf(_make_paper(), tmp_path / "b", watermark_id="COPY-002"))
    assert "COPY-001" in a and "COPY-002" in b
    assert "COPY-002" not in a


def test_paper_content_rendered(tmp_path):
    out = export_pdf(_make_paper(), tmp_path / "c")
    text = _extract_text(out)
    assert "Mid Term Examination" in text
    assert "SECTION A" in text
    assert "Maximum Marks: 1" in text


def test_section_note_matches_real_marks_not_just_the_label(tmp_path):
    """Found 2026-09-18 by actually reading a real generated PDF end-to-end:
    a custom blueprint labeled its section "A" but put 2-mark questions in
    it, and the PDF printed "carrying 1 mark each" anyway -- the CBSE-
    standard description was keyed purely off the label, not the section's
    real content. A section literally named A/B/C/D/E must only get the
    canned CBSE description when its questions' marks actually match that
    convention; otherwise the printed note must reflect the real marks."""
    now = datetime.now(timezone.utc)
    two_mark_questions = [
        GeneratedQuestionSchema(question_id=f"q{i}", display_number=i,
                                 stem=f"Question {i}", marks=2,
                                 bloom_level="understand", difficulty="medium")
        for i in range(1, 4)
    ]
    section = GeneratedSectionSchema(
        section_id="section-a", label="A", name="Section A",
        questions=two_mark_questions, total_marks=6,
    )
    metadata = PaperMetadataSchema(
        assessment_title="Custom Blueprint Paper", subject="Science", grade=10,
        total_marks=6, duration_minutes=30, generated_at=now,
    )
    paper = GeneratedPaper(id="paper_custom", assessment_id="assess1",
                           sections=[section], metadata=metadata, answer_key={})
    text = _extract_text(export_pdf(paper, tmp_path / "d"))
    assert "carrying 2 marks each" in text
    assert "carrying 1 mark each" not in text


def test_section_note_uses_canned_cbse_text_when_marks_do_match(tmp_path):
    """The standard CBSE-blueprint path (label A, 1-mark MCQs) must keep
    printing the descriptive canned text, not just a generic "carrying N
    marks each" -- this is the case the fix in test above must not break."""
    text = _extract_text(export_pdf(_make_paper(), tmp_path / "e"))
    assert "multiple choice questions carrying 1 mark each" in text


def test_section_note_falls_back_to_generic_text_when_marks_vary(tmp_path):
    now = datetime.now(timezone.utc)
    mixed_questions = [
        GeneratedQuestionSchema(question_id="q1", display_number=1, stem="Q1",
                                marks=2, bloom_level="understand", difficulty="medium"),
        GeneratedQuestionSchema(question_id="q2", display_number=2, stem="Q2",
                                marks=3, bloom_level="apply", difficulty="medium"),
    ]
    section = GeneratedSectionSchema(
        section_id="section-a", label="A", name="Section A",
        questions=mixed_questions, total_marks=5,
    )
    metadata = PaperMetadataSchema(
        assessment_title="Mixed Marks Paper", subject="Science", grade=10,
        total_marks=5, duration_minutes=30, generated_at=now,
    )
    paper = GeneratedPaper(id="paper_mixed", assessment_id="assess1",
                           sections=[section], metadata=metadata, answer_key={})
    text = _extract_text(export_pdf(paper, tmp_path / "f"))
    assert "carrying marks as indicated" in text


def test_split_stem_and_options():
    head, options = split_stem_and_options(
        "Which of the following is a gas? (A) Oxygen (B) Gold (C) Silver (D) Copper")
    assert head == "Which of the following is a gas?"
    assert options == ["Oxygen", "Gold", "Silver", "Copper"]


def test_split_stem_and_options_no_options():
    assert split_stem_and_options("State Newton's second law.") == ("State Newton's second law.", [])


def test_split_stem_and_options_non_alpha_start_not_split():
    # Labels must start at (A); "(B) ... (C) ..." is a part label, not options.
    assert split_stem_and_options("(B) second (C) third") == ("(B) second (C) third", [])


def test_split_stem_and_options_out_of_order_not_split():
    head, options = split_stem_and_options("Two parts (A) first (C) third (B) second")
    assert (head, options) == ("Two parts (A) first (C) third (B) second", [])


def test_escape_xml_special_chars():
    assert escape("a < b & c > d") == "a &lt; b &amp; c &gt; d"

from academicos.assessment.pdf import export_answer_key_pdf, pdf_safe  # noqa: E402


def _paper_with(gq, answer="x"):
    now = datetime.now(timezone.utc)
    section = GeneratedSectionSchema(section_id="s", label="A", name="Q",
                                     questions=[gq], total_marks=gq.marks)
    meta = PaperMetadataSchema(assessment_title="T", subject="Science", grade=9,
                               total_marks=gq.marks, duration_minutes=60, generated_at=now)
    return GeneratedPaper(id="p", assessment_id="a", sections=[section],
                          metadata=meta, answer_key={"1": answer})


def _gq(stem, qtype="mcq", marks=1):
    return GeneratedQuestionSchema(question_id="q", display_number=1, stem=stem,
                                   marks=marks, bloom_level="remember",
                                   difficulty="easy", type=qtype)


def test_more_than_four_option_labels_do_not_crash(tmp_path):
    """labels="ABCD" indexed by position raised IndexError on a fifth."""
    stem = "Pick one. (A) a (B) b (C) c (D) d (D) fifthoption"
    text = _extract_text(export_pdf(_paper_with(_gq(stem)), tmp_path))
    assert "(E)" in text and "fifthoption" in text


def test_a_question_taller_than_a_page_exports(tmp_path):
    """Each question was one Table row, which cannot split: LayoutError, HTTP 500."""
    stem = "Explain in detail. " + ("This sentence is deliberately long. " * 900)
    assert export_pdf(_paper_with(_gq(stem, "long_answer", 5)), tmp_path).exists()


def test_an_answer_taller_than_a_page_exports(tmp_path):
    paper = _paper_with(_gq("Explain photosynthesis fully.", "long_answer", 5),
                        answer="Value point. " * 3000)
    assert export_answer_key_pdf(paper, tmp_path).exists()


def test_subparts_of_a_descriptive_question_are_not_gridded_as_options(tmp_path):
    stem = "Two brothers share money. (a) Find each share. (b) Explain. (c) Check. (d) State."
    text = _extract_text(export_pdf(_paper_with(_gq(stem, "long_answer", 4)), tmp_path))
    assert "(A)" not in text and "(a) Find each share" in text


def test_math_italic_letters_survive():
    """'12𝑥2 + 11𝑥−15' printed as '122 + 11−15' -- the variable vanished."""
    assert pdf_safe("12\U0001d4652 + 11\U0001d465−15") == "12x2 + 11x-15"


def _option_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip().startswith("(")]


def test_a_paper_typed_mcq_still_grids_its_options(tmp_path):
    stem = "Which of these is a gas? (A) Oxygen (B) Gold (C) Silver (D) Copper"
    text = _extract_text(export_pdf(_paper_with(_gq(stem, "mcq", 1)), tmp_path))
    assert any(line.startswith("(A)") for line in _option_lines(text))
    assert "gas? (A)" not in text


def test_a_board_one_mark_mcq_typed_very_short_answer_grids_its_options(tmp_path):
    """The board records in questions.json type 1-mark MCQs very_short_answer
    (586 splittable stems, 538 with exactly four options, against 46 typed mcq).
    The objective gate ran their options inline into the stem."""
    stem = ("In the formula of mode given by mode = l + f1 denotes the : "
            "(A) frequency of the modal class (B) frequency of class preceding modal class "
            "(C) frequency of class succeeding modal class (D) cumulative frequency of modal class")
    text = _extract_text(export_pdf(_paper_with(_gq(stem, "very_short_answer", 1)), tmp_path))
    starts = [line[:3] for line in _option_lines(text)]
    for label in ("(A)", "(B)", "(C)", "(D)"):
        assert label in starts, (label, text)
    assert "denotes the : (A)" not in text


def _boot_with_paper(tmp_path, monkeypatch):
    from test_assessment_routes_auth import _boot_client, _register
    from test_route_inventory import blueprint_body, question_body

    client = _boot_client(tmp_path, monkeypatch)
    client.__enter__()
    teacher = _register(client, "school_1", "render-fail@example.com")
    auth = {"Authorization": f"Bearer {teacher['token']}"}
    created = client.post("/api/v1/assessments", json={
        "teacherId": teacher["user"]["id"], "schoolId": "school_1",
        "title": "Render Failure", "subject": "Mathematics", "grade": 10,
        "chapterIds": [], "blueprint": blueprint_body(),
    }, headers=auth)
    assert created.status_code == 200, created.text
    gen = client.post("/api/v1/papers/generate", json={
        "assessmentId": created.json()["id"], "blueprint": blueprint_body(),
        "selectedQuestions": [question_body()],
        "template": {"id": "t1", "schoolId": "school_1", "name": "Default"},
    }, headers=auth)
    assert gen.status_code == 200, gen.text
    return client, auth, gen.json()["id"]


@pytest.mark.parametrize("fmt,fn,action", [
    ("pdf", "export_pdf", "paper_exported"),
    ("answer-key", "export_answer_key_pdf", "answer_key_exported"),
])
def test_a_render_failure_is_a_422_naming_the_cause_and_is_not_audited(
        tmp_path, monkeypatch, fmt, fn, action):
    from academicos.assessment import pdf as pdf_mod
    from academicos.assessment.audit_log import get_audit_log

    client, auth, paper_id = _boot_with_paper(tmp_path, monkeypatch)
    try:
        def boom(*a, **k):
            raise ValueError("stem 7 overflows the frame")

        monkeypatch.setattr(pdf_mod, fn, boom)
        r = client.post(f"/api/v1/papers/{paper_id}/export/{fmt}", headers=auth)
        assert r.status_code == 422, r.text
        assert "stem 7 overflows the frame" in r.json()["detail"]
        assert get_audit_log(tmp_path).for_action(action) == []
    finally:
        client.__exit__(None, None, None)
