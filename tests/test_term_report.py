"""The principal's term report (ADM-2) and its Excel/PDF export (ADM-4):
one term, filtered by class, section or subject, aggregates only, and every
download audited."""
from __future__ import annotations

import io
import zipfile

from test_homework import _create, w  # noqa: F401 - `w` is a fixture


def _term(w):
    return w.store.create_term(academic_year_id=w.year, name="Term 1", start_date="2026-04-01",
                               end_date="2026-09-30")


def _homework_handed_in(w):
    from academicos.operations.routes import store
    hw = _create(w, "ana", questionIds=["q1", "q2"]).json()
    w.c.post(f"/api/v1/my-homework/{hw['id']}/submit", json={"answers": {"q1": "A", "q2": "C"}}, headers=w.s1)
    s = store()
    with s._conn_lock:     # set on the school's (patched) today, not the machine's
        s.conn.execute("UPDATE homework SET published_at=? WHERE id=?", ("2026-05-30T04:00:00+00:00", hw["id"]))
        s._commit()
    return hw


def test_the_term_report_counts_and_filters(w):
    term = _term(w)
    _homework_handed_in(w)
    r = w.c.get("/api/v1/dashboard/term", headers=w.p)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["scope"]["kind"] == "term" and d["scope"]["termId"] == term.id and d["scope"]["asOf"] == "2026-06-01"
    assert d["homework"]["issued"] == 1 and d["homework"]["expected"] == 2 and d["homework"]["handedIn"] == 1
    assert [(b["grade"], b["subject"], b["questions"]) for b in d["bank"]] == [(9, "Science", 4), (10, "Science", 4)]
    assert {(c["grade"], c["subject"]) for c in d["exams"]["notYet"]} == {(9, "Science"), (10, "Science")}
    assert d["timeSaved"]["estimated"] is True and d["timeSaved"]["papers"] == 0
    [progress] = d["progress"]
    assert progress["grade"] == 10 and progress["studentsWithEvidence"] == 1
    assert "name" not in str(d["progress"]).lower(), "aggregates only"

    b10 = w.c.get("/api/v1/dashboard/term", params={"sectionId": w.b10}, headers=w.p).json()
    assert b10["filters"] == {"grade": 10, "sectionId": w.b10, "sectionName": "10-B", "subject": None}
    assert b10["homework"]["issued"] == 0 and b10["progress"] == []
    nine = w.c.get("/api/v1/dashboard/term", params={"grade": 9}, headers=w.p).json()
    assert [b["grade"] for b in nine["bank"]] == [9] and nine["homework"]["issued"] == 0
    maths = w.c.get("/api/v1/dashboard/term", params={"subject": "maths"}, headers=w.p).json()
    assert maths["bank"] == [] and maths["homework"]["issued"] == 0 and maths["exams"]["notYet"] == []

    assert w.c.get("/api/v1/dashboard/term", params={"sectionId": w.a9, "grade": 10},
                   headers=w.p).status_code == 422
    assert w.c.get("/api/v1/dashboard/term", params={"sectionId": "nope"}, headers=w.p).status_code == 404
    assert w.c.get("/api/v1/dashboard/term", headers=w.ana).status_code == 403
    assert w.c.get("/api/v1/dashboard/term", params={"termId": term.id}, headers=w.p2).status_code == 403


def test_a_class_the_bank_cannot_serve_is_not_no_paper_yet(w, monkeypatch):
    """D117: "not yet" listed class-subject pairs the bank has no question for
    (Hindi 6-10, Social Science 6-9, English 7-8), so the report read "Class 6
    Hindi: no paper yet" -- a gap of the bank's, put on the teachers. The
    catalog's count now separates the two."""
    from academicos.operations import homework_routes as hr
    _term(w)
    monkeypatch.setattr(hr, "_bank_question_count", lambda subject, grade: 0 if grade == 9 else 4)
    d = w.c.get("/api/v1/dashboard/term", headers=w.p).json()
    assert [(c["grade"], c["subject"]) for c in d["exams"]["notYet"]] == [(10, "Science")]
    assert [(c["grade"], c["subject"]) for c in d["exams"]["noQuestions"]] == [(9, "Science")]
    x = w.c.get("/api/v1/dashboard/term/export", params={"format": "xlsx"}, headers=w.p)
    assert x.status_code == 200, x.text
    exams_sheet = zipfile.ZipFile(io.BytesIO(x.content)).read("xl/worksheets/sheet3.xml").decode()
    assert "the question bank has no questions for this class yet" in exams_sheet


def test_with_no_term_it_is_the_year_so_far_and_says_so(w):
    """D43: the note named "calendar setup", which is no page of the web
    app; it now names the console tab that declares terms, and links it."""
    d = w.c.get("/api/v1/dashboard/term", headers=w.p).json()
    assert d["scope"]["kind"] == "year" and d["scope"]["name"] == "2026-27"
    assert "Declare this year's terms on the School Admin console, under Calendar & Setup" in d["scope"]["note"]
    assert d["scope"]["noteLink"] == "/admin?tab=calendar-setup"


def test_the_report_downloads_as_excel_and_pdf_and_is_audited(w):
    from academicos.assessment.audit_log import get_audit_log
    from academicos.curriculum import routes as cr
    _term(w)
    _homework_handed_in(w)
    x = w.c.get("/api/v1/dashboard/term/export", params={"format": "xlsx", "grade": 10}, headers=w.p)
    assert x.status_code == 200, x.text
    assert x.headers["content-type"].startswith("application/vnd.openxmlformats-officedocument.spreadsheetml")
    assert 'filename="term-report-Term-1-2026-06-01.xlsx"' in x.headers["content-disposition"]
    z = zipfile.ZipFile(io.BytesIO(x.content))
    book = z.read("xl/workbook.xml").decode()
    for sheet in ("Summary", "Syllabus", "Exams", "Homework", "Question bank", "Progress"):
        assert f'name="{sheet}"' in book
    assert "Term report: Term 1 (class 10)" in z.read("xl/worksheets/sheet1.xml").decode()

    p = w.c.get("/api/v1/dashboard/term/export", params={"format": "pdf"}, headers=w.p)
    assert p.status_code == 200 and p.content.startswith(b"%PDF")
    assert w.c.get("/api/v1/dashboard/term/export", params={"format": "doc"}, headers=w.p).status_code == 422
    assert w.c.get("/api/v1/dashboard/term/export", headers=w.bala).status_code == 403
    audit = get_audit_log(cr._cfg.data_root).for_action("term_report_exported")
    assert len(audit) == 2 and {a["details"]["grade"] for a in audit} == {10, None}


def test_the_workbook_keeps_formulas_as_text():
    from academicos.operations.xlsx import workbook
    z = zipfile.ZipFile(io.BytesIO(workbook([("A/B:C", [["name", "n"], ["=HYPERLINK(1)", -3], ["x&y", 2.5]])])))
    sheet = z.read("xl/worksheets/sheet1.xml").decode()
    assert "'=HYPERLINK(1)" in sheet and "<v>-3</v>" in sheet and "x&amp;y" in sheet
    assert 'name="ABC"' in z.read("xl/workbook.xml").decode()


def test_the_downloads_carry_the_schools_name_and_address(w):
    """QA S-11: the term report's header was "Term report: Term 2" only."""
    import fitz
    _term(w)
    w.store.set_school_profile("school_1", name="Sunrise Public School", address="1 School Road, Pune",
                               affiliation="CBSE 1130456", updated_by="p")
    p = w.c.get("/api/v1/dashboard/term/export", params={"format": "pdf"}, headers=w.p)
    with fitz.open(stream=p.content, filetype="pdf") as doc:
        first = " ".join(doc[0].get_text().split())
    assert first.index("Sunrise Public School") < first.index("Term report")
    assert "1 School Road, Pune | CBSE 1130456" in first
    x = w.c.get("/api/v1/dashboard/term/export", params={"format": "xlsx"}, headers=w.p)
    sheet = zipfile.ZipFile(io.BytesIO(x.content)).read("xl/worksheets/sheet1.xml").decode()
    assert sheet.index("Sunrise Public School") < sheet.index("Term report")


def test_a_plan_that_cannot_finish_is_said_even_when_not_behind(w):
    """D35: a section's plan laid on fewer periods than its syllabus needs left
    subtopics with no date, and the report said "behind: no". Each row now
    counts the subtopics with no day in the year's plan, and the summary the
    class-subjects that cannot finish."""
    _term(w)
    s = w.store
    board = s.create_board(name="CBSE", code="CBSE")
    book = s.create_book(subject_id=w.sci10, board_id=board.id, title="Science 10")
    unit = s.create_unit(book_id=book.id, canonical_id="d35-u1", unit_no="1", name="Unit 1")
    chapter = s.create_chapter(canonical_id="d35-ch1", unit_id=unit.id, name="Light")
    topic = s.create_topic(chapter_id=chapter.id, canonical_id="d35-tp1", name="Reflection")
    subs = [s.create_subtopic(topic_id=topic.id, canonical_id=f"d35-st{i}", name=f"Part {i}") for i in range(5)]
    # 10-A: two subtopics taught on time, one dated later, one lost its day, one never placed.
    for st, day, status in ((subs[0], "2026-05-20", "completed"), (subs[1], "2026-05-25", "completed"),
                            (subs[2], "2026-08-10", "scheduled"), (subs[3], "2026-08-11", "unscheduled")):
        s.create_scheduled_lesson(school_id="school_1", academic_year_id=w.year, book_id=book.id,
                                  subtopic_id=st.id, date=day, status=status, section_id=w.a10)
    # 10-B: every subtopic has a day.
    for i, st in enumerate(subs):
        s.create_scheduled_lesson(school_id="school_1", academic_year_id=w.year, book_id=book.id,
                                  subtopic_id=st.id, date=f"2026-08-{12 + i}", section_id=w.b10)

    d = w.c.get("/api/v1/dashboard/term", headers=w.p).json()["syllabus"]
    rows = {r["sectionName"]: r for r in d["rows"]}
    assert rows["10-A"]["behind"] is False, "taught everything planned so far"
    assert rows["10-A"]["undatedSubtopics"] == 2, "one lost its day, one was never placed"
    assert rows["10-B"]["undatedSubtopics"] == 0
    assert d["cannotFinish"] == 1 and d["rows"][0]["sectionName"] == "10-A", "the plan that cannot finish leads"
