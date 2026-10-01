"""Report cards (REQUIREMENTS EX-8): a term's marks for one student, by subject
and exam type, with totals, percentages and CBSE grade bands; as JSON, as a
PDF headed with the school's own name, and a section's cards in one PDF.

Built on the homework world (test_homework.w): 10-A has Asha (s1) and
Bhavna (s2), 10-B has Charu (s3); Ana teaches Science to 10-A. Today is
2026-06-01, inside Term 1 (April to September).
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from academicos.assessment.schemas import (GeneratedPaper, GeneratedQuestionSchema, GeneratedSectionSchema,
                                           PaperMetadataSchema)

from test_guardians import _h, _parent
from test_homework import w  # noqa: F401 - `w` is a fixture


def _paper(pid, subject, grade, exam_type, on, marks):
    """A paper with one question per mark value in `marks`."""
    qs = [GeneratedQuestionSchema(question_id=f"{pid}_q{i}", display_number=i + 1, stem=f"Q{i}", marks=m,
                                  bloom_level="remember", difficulty="easy") for i, m in enumerate(marks)]
    return GeneratedPaper(
        id=pid, assessment_id=f"a_{pid}",
        sections=[GeneratedSectionSchema(section_id="s", label="A", name="All", questions=qs,
                                         total_marks=sum(marks))],
        metadata=PaperMetadataSchema(assessment_title=f"{subject} {exam_type}", subject=subject, grade=grade,
                                     total_marks=sum(marks), duration_minutes=60, exam_type=exam_type,
                                     generated_at=datetime.fromisoformat(on).replace(tzinfo=timezone.utc)),
        answer_key={})


@pytest.fixture
def rc(w):
    from academicos.assessment import routes as ar
    from academicos.operations.routes import store as ops

    term = w.store.create_term(academic_year_id=w.year, name="Term 1", start_date="2026-04-01",
                               end_date="2026-09-30")
    papers = ar._require_papers()
    s1, s2 = w.ids["s1"], w.ids["s2"]
    plan = [
        # (paper, {student: marks per question}, absent)
        (_paper("p_ut", "Science", 10, "unit_test", "2026-05-10", [5, 5]), {s1: [4, 4], s2: [5, 5]}, []),
        (_paper("p_hy", "Science", 10, "half_yearly", "2026-09-20", [20, 20]), {s1: [15, 15], s2: [10, 10]}, []),
        (_paper("p_m1", "Mathematics", 10, "unit_test", "2026-05-12", [10, 10]), {s2: [20, 0]}, [s1]),
        (_paper("p_m2", "Mathematics", 10, "periodic", "2026-07-01", [10, 10]), {s1: [9, 9], s2: [5, 5]}, []),
        # Not on the card: last year's term, class 9, and a paper with no marks for s1.
        (_paper("p_old", "Science", 10, "annual", "2026-03-20", [50]), {s1: [50]}, []),
        (_paper("p_g9", "Science", 9, "unit_test", "2026-05-10", [10]), {s1: [10]}, []),
        (_paper("p_none", "English", 10, "unit_test", "2026-05-10", [10]), {s2: [7]}, []),
    ]
    for paper, by_student, absent in plan:
        papers.save(paper, school_id="school_1")
        entries = [(sid, q.question_id, m) for sid, ms in by_student.items()
                   for q, m in zip(paper.sections[0].questions, ms)]
        ops().save_marks(paper.id, entries, absent=absent, present=[], entered_by="teacher")
    w.term = term.id
    return w


def _card(w, who, student="s1", **params):
    return w.c.get(f"/api/v1/report-cards/students/{w.ids[student]}", params=params, headers=who)


def test_a_card_adds_up_the_terms_marks_by_subject_with_grade_bands(rc):
    r = _card(rc, rc.p)
    assert r.status_code == 200, r.text
    card = r.json()
    assert (card["studentName"], card["section"], card["termName"]) == ("Asha", "10-A", "Term 1")
    by = {s["subject"]: s for s in card["subjects"]}
    assert set(by) == {"Science", "Mathematics"}, "last year's, class 9's and an unmarked paper are left out"
    sci = by["Science"]
    assert [(p["examTypeLabel"], p["obtained"], p["maximum"]) for p in sci["papers"]] == \
        [("Unit test", 8.0, 10), ("Half-yearly", 30.0, 40)]
    assert (sci["obtained"], sci["maximum"], sci["percent"], sci["band"]) == (38.0, 50, 76.0, "B1")
    maths = by["Mathematics"]
    assert [(p["examTypeLabel"], p["absent"]) for p in maths["papers"]] == [("Unit test", True), ("Periodic test", False)]
    assert (maths["obtained"], maths["maximum"], maths["band"]) == (18.0, 20, "A2"), "an absence counts for neither side (90%: A2)"
    assert (card["obtained"], card["maximum"], card["percent"], card["band"]) == (56.0, 70, 80.0, "B1")
    assert "not recorded here" in card["note"]
    assert "rank" not in r.text.lower() and "position" not in r.text.lower()


def test_who_may_read_a_card(rc):
    assert _card(rc, rc.s1).status_code == 200, "the student"
    assert _card(rc, rc.s2).status_code == 403, "a classmate"
    mum = _h(_parent(rc))
    assert _card(rc, mum).status_code == 200, "the linked parent"
    assert _card(rc, mum, student="s2").status_code == 403, "not another child"
    assert _card(rc, rc.ana).status_code == 403, "a subject teacher who is not the class teacher"
    [a10] = [s for s in rc.store.sections_for_year(rc.year) if s.id == rc.a10]
    rc.store.update_section(a10.id, class_teacher_id=rc.store.allocation_for(rc.a10, rc.sci10).teacher_id)
    assert _card(rc, rc.ana).status_code == 200, "now Ana is 10-A's class teacher"
    assert _card(rc, rc.p2).status_code == 403, "another school's principal"


def test_reads_of_someone_elses_card_are_logged(rc):
    from academicos.assessment.audit_log import get_audit_log
    from academicos.curriculum import routes as cr
    _card(rc, rc.s1)
    _card(rc, rc.p)
    reads = [e for e in get_audit_log(cr._cfg.data_root).for_action("pii_read")
             if e["details"].get("what") == "report_card"]
    assert len(reads) == 1, "the student's own read is not a read of someone else's data"


def test_the_pdf_is_headed_with_the_schools_name_and_prints_the_marks(rc, tmp_path):
    import fitz
    rc.c.put("/api/v1/curriculum/school-profile", json={"name": "Sunrise Public School"}, headers=rc.p)
    r = rc.c.get(f"/api/v1/report-cards/students/{rc.ids['s1']}/pdf", headers=rc.p)
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"
    (tmp_path / "c.pdf").write_bytes(r.content)
    with fitz.open(str(tmp_path / "c.pdf")) as doc:
        assert doc.page_count == 1
        text = doc[0].get_text()
    for expected in ("Sunrise Public School", "Report card: Term 1", "Asha", "Class 10-A", "Science", "38/50",
                     "B1", "Unit test: AB/20", "56/70", "Class teacher", "Principal"):
        assert expected in text, expected


def test_a_sections_cards_come_as_one_pdf_in_name_order(rc, tmp_path):
    import fitz
    r = rc.c.get(f"/api/v1/report-cards/sections/{rc.a10}/pdf", headers=rc.p)
    assert r.status_code == 200, r.text
    (tmp_path / "s.pdf").write_bytes(r.content)
    with fitz.open(str(tmp_path / "s.pdf")) as doc:
        assert doc.page_count == 2
        assert "Asha" in doc[0].get_text() and "Bhavna" in doc[1].get_text()
    assert rc.c.get(f"/api/v1/report-cards/sections/{rc.a10}/pdf", headers=rc.s1).status_code == 403
    assert rc.c.get(f"/api/v1/report-cards/sections/{rc.a10}/pdf", headers=rc.ana).status_code == 403


def test_a_day_in_no_term_asks_for_the_term(rc, monkeypatch):
    from datetime import date
    from academicos.curriculum import routes as cr
    monkeypatch.setattr(cr, "_school_today", lambda: date(2026, 12, 1))
    r = _card(rc, rc.p)
    assert r.status_code == 409 and "termId" in r.json()["detail"]
    assert _card(rc, rc.p, termId=rc.term).status_code == 200


def test_a_paper_with_only_some_marks_entered_is_incomplete_and_counts_for_neither_side(rc, tmp_path):
    """v3 audit N-2-10: a paper whose marks were only partly entered was
    totalled over the whole paper and graded, as on the marks grid. It reads
    "incomplete" and, like an absence, counts for neither side."""
    import fitz
    from academicos.assessment import routes as ar
    from academicos.operations.routes import store as ops
    part = _paper("p_part", "Science", 10, "periodic", "2026-07-15", [10, 10, 10])
    ar._require_papers().save(part, school_id="school_1")
    ops().save_marks(part.id, [(rc.ids["s1"], "p_part_q0", 2)], absent=[], present=[], entered_by="teacher")
    card = _card(rc, rc.p).json()
    sci = {s["subject"]: s for s in card["subjects"]}["Science"]
    [line] = [p for p in sci["papers"] if p["paperId"] == "p_part"]
    assert (line["incomplete"], line["absent"], line["obtained"], line["maximum"]) == (True, False, None, 30)
    assert all(p["incomplete"] is False for p in sci["papers"] if p["paperId"] != "p_part")
    assert (sci["obtained"], sci["maximum"], sci["percent"], sci["band"]) == (38.0, 50, 76.0, "B1"), \
        "2 of 30 is not a 6.7% paper"
    assert (card["obtained"], card["maximum"], card["band"]) == (56.0, 70, "B1")
    r = rc.c.get(f"/api/v1/report-cards/students/{rc.ids['s1']}/pdf", headers=rc.p)
    (tmp_path / "p.pdf").write_bytes(r.content)
    with fitz.open(str(tmp_path / "p.pdf")) as doc:
        text = doc[0].get_text()
    assert "Periodic test: incomplete/30" in text and "38/50" in text
