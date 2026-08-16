"""Mobile scan-and-grade orchestration (assessment/mobile_scan.py).

Regression tests for the `ocr_failed_pages` / `force_review` logic added
today: a question with no matched answer segment on a session that had a real
OCR failure anywhere must route to review with an OCR-outage warning —
distinct from a genuine blank (no OCR failure in the session), which must not.

Sessions/pages/questions are constructed in-process; the Sarvam LLM call is
stubbed out. No HTTP, no real Sarvam API, no add_page() (which would hit the
real capture pipeline).
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.assessment.evaluate import Evaluation
from academicos.assessment.mobile_scan import (
    CapturedPage,
    ReviewItem,
    ScanSession,
    process_session,
    review_decision,
)
from academicos.assessment.schemas import (
    AnswerSchemeSchema,
    GeneratedQuestionSchema,
    MarkingPointSchema,
    QuestionSchema,
)


def _question(qid: str, marks: int = 2) -> QuestionSchema:
    now = datetime.now(timezone.utc)
    scheme = AnswerSchemeSchema(
        total_marks=marks,
        marking_points=[MarkingPointSchema(id="mp1", description="correct",
                                           marks=marks, keyword="answer")],
        metadata={},
    )
    return QuestionSchema(
        id=qid, question_bank_id="bank1", subject="science", grade=10,
        chapter_ids=["c1"], competency_ids=[], bloom_level="understand",
        difficulty="medium", type="short_answer", stem=f"stem {qid}", parts=[],
        answer_scheme=scheme, estimated_time_minutes=2, marks=marks, language="en",
        source="teacher_created", quality_score=0.7, tags=[], created_at=now,
        updated_at=now,
    )


def _generated(qid: str, display_number: int, marks: int = 2) -> GeneratedQuestionSchema:
    return GeneratedQuestionSchema(
        question_id=qid, display_number=display_number, stem=f"stem {qid}",
        marks=marks, bloom_level="understand", difficulty="medium",
    )


def _page(page_no: int, ocr_text: str, warnings: list[str] | None = None,
          tmp_path: Path | None = None) -> CapturedPage:
    return CapturedPage(
        page_no=page_no,
        raw_path=Path(str(tmp_path or Path("raw"))) / f"raw_{page_no}.jpg",
        processed_path=Path(str(tmp_path or Path("proc"))) / f"proc_{page_no}.jpg",
        cropped=False, ocr_text=ocr_text, warnings=warnings or [],
    )


def _session(*pages: CapturedPage) -> ScanSession:
    return ScanSession(id="scan_test", assessment_id="a1", student_id="s1",
                       student_name="Student", pages=list(pages))


# The LLM boundary: return a confident, non-review "genuine blank" verdict so
# the test isolates process_session's own force_review logic.
def _stub_llm(monkeypatch):
    def fake_evaluate_answer_llm(question, scheme, student_answer, *, concept_label=None):
        return Evaluation(
            question_id=question.id, awarded_marks=0, max_marks=question.marks,
            verdict="blank", confidence=0.95,
            reasoning="No answer written for this question.",
            ocr_warnings=[], needs_review=False,
        )
    monkeypatch.setattr(
        "academicos.assessment.mobile_scan.llm_evaluate.evaluate_answer_llm",
        fake_evaluate_answer_llm,
    )


def test_ocr_failure_forces_review_on_unmatched_question(monkeypatch, tmp_path):
    _stub_llm(monkeypatch)
    # Page OCR itself failed (network/provider error) -> empty text + warning.
    session = _session(_page(1, "", ["OCR failed: vision job timed out"], tmp_path))
    q = _question("q1")
    items = process_session(session, {"q1": q}, [_generated("q1", 1)])

    item = items[0]
    assert item.student_answer == ""
    assert item.needs_review is True
    assert item.verdict == "blank"
    assert any("OCR failed on page(s)" in w for w in item.ocr_warnings)
    assert any("may be an OCR outage" in w for w in item.ocr_warnings)
    assert any("verify manually" in w for w in item.ocr_warnings)


def test_ocr_failure_detection_is_case_insensitive(monkeypatch, tmp_path):
    _stub_llm(monkeypatch)
    session = _session(_page(1, "", ["Ocr FAILED during capture of page 1"], tmp_path))
    q = _question("q1")
    items = process_session(session, {"q1": q}, [_generated("q1", 1)])
    assert items[0].needs_review is True
    assert any("OCR failed on page" in w for w in items[0].ocr_warnings)


def test_genuine_blank_without_ocr_failure_not_forced(monkeypatch, tmp_path):
    _stub_llm(monkeypatch)
    # Clean page, no OCR failure anywhere — student genuinely left it blank.
    session = _session(_page(1, "", [], tmp_path))
    q = _question("q1")
    items = process_session(session, {"q1": q}, [_generated("q1", 1)])

    item = items[0]
    assert item.verdict == "blank"
    assert item.needs_review is False
    assert item.ocr_warnings == ["no answer found under this question number"]
    assert not any("OCR failed" in w for w in item.ocr_warnings)
    assert not any("outage" in w for w in item.ocr_warnings)


def test_matched_answer_not_forced_by_ocr_failure_on_other_page(monkeypatch, tmp_path):
    _stub_llm(monkeypatch)
    # Page 2 OCR failed, but question 1's answer was found on a clean page 1.
    # force_review must only fire for *unmatched* questions, not matched ones.
    session = _session(
        _page(1, "Q.1) (B) 5", [], tmp_path),
        _page(2, "", ["OCR failed: vision job timed out"], tmp_path),
    )
    q = _question("q1")
    items = process_session(session, {"q1": q}, [_generated("q1", 1)])
    item = items[0]
    assert item.student_answer == "(B) 5"
    assert item.needs_review is False
    assert not any("OCR failed" in w for w in item.ocr_warnings)
    assert item.page_numbers == [1]


def test_ocr_failure_forces_each_unmatched_question(monkeypatch, tmp_path):
    _stub_llm(monkeypatch)
    # One OCR-failed page, three questions: the matched one stays calm, the
    # two unmatched ones all route to review with the outage warning.
    session = _session(
        _page(1, "Q.1) (B) 5", [], tmp_path),
        _page(2, "", ["OCR failed: network error"], tmp_path),
    )
    q1, q2, q3 = _question("q1"), _question("q2"), _question("q3")
    items = process_session(
        session, {"q1": q1, "q2": q2, "q3": q3},
        [_generated("q1", 1), _generated("q2", 2), _generated("q3", 3)],
    )
    by_num = {i.display_number: i for i in items}
    assert by_num[1].needs_review is False
    assert by_num[1].student_answer == "(B) 5"
    assert by_num[2].needs_review is True
    assert any("OCR failed on page" in w for w in by_num[2].ocr_warnings)
    assert by_num[3].needs_review is True
    assert any("OCR failed on page" in w for w in by_num[3].ocr_warnings)
    # every unmatched question names the failed page(s) explicitly
    assert any("page(s) [2]" in w for w in by_num[2].ocr_warnings)


def test_no_pages_raises():
    session = _session()
    with pytest.raises(RuntimeError):
        process_session(session, {}, [])


def test_items_sorted_by_display_number(monkeypatch, tmp_path):
    _stub_llm(monkeypatch)
    session = _session(_page(1, "Q.2) (B) 5\nQ.1) (A) 4", [], tmp_path))
    q1, q2 = _question("q1"), _question("q2")
    items = process_session(
        session, {"q1": q1, "q2": q2},
        [_generated("q2", 2), _generated("q1", 1)],  # deliberately out of order
    )
    assert [i.display_number for i in items] == [1, 2]
    assert session.status == "reviewing"


def test_review_decision_and_final_totals(monkeypatch, tmp_path):
    _stub_llm(monkeypatch)
    session = _session(_page(1, "Q.1) (B) 5", [], tmp_path))
    q = _question("q1", marks=2)
    items = process_session(session, {"q1": q}, [_generated("q1", 1, marks=2)])
    item = items[0]
    assert item.final_marks == 0  # stub returns blank verdict
    updated = review_decision(session, q.id, "edit", marks=2, comment="full credit")
    assert updated.status == "edited"
    assert updated.teacher_marks == 2
    assert updated.final_marks == 2
    assert review_decision(session, q.id, "approve").status == "approved"
    awarded, maximum = _finalize(session)
    assert (awarded, maximum) == (2, 2)


def _finalize(session):
    return sum(i.final_marks for i in session.review), sum(i.max_marks for i in session.review)