"""Self-practice (SA-4): a student practises from the bank, objective
questions first, marked at once, fed into progress, and never the questions
they answered in the last two weeks."""
from __future__ import annotations

from test_homework import _create, w  # noqa: F401 - `w` is a fixture


def test_practice_is_marked_and_counts_as_practice(w):
    assert w.c.post("/api/v1/my-practice", json={}, headers=w.s1).status_code == 409, "nothing marked yet"
    r = w.c.post("/api/v1/my-practice", json={"subject": "Science", "count": 3}, headers=w.s1)
    assert r.status_code == 200, r.text
    first = r.json()
    ids = [q["id"] for q in first["questions"]]
    assert len(ids) == 3 and set(ids) == {"q1", "q2", "q4"}, "the objective ones first"
    assert "answerScheme" not in str(first)
    done = w.c.post(f"/api/v1/my-practice/{first['id']}/submit",
                    json={"answers": {"q1": "A", "q2": "C", "q4": "B"}}, headers=w.s1).json()
    assert done["marks"] == 2 and done["maxMarks"] == 3 and done["evaluations"][0]["modelAnswer"]
    assert w.c.post(f"/api/v1/my-practice/{first['id']}/submit", json={"answers": {}},
                    headers=w.s1).status_code == 409
    assert w.c.get("/api/v1/my-learning", headers=w.s1).json()["sources"]["practice"] == 1

    # spaced revision: what was just answered is not asked again
    again = w.c.post("/api/v1/my-practice", json={"subject": "Science", "count": 3}, headers=w.s1).json()
    assert [q["id"] for q in again["questions"]] == ["q3"]
    assert [p["id"] for p in w.c.get("/api/v1/my-practice", headers=w.s1).json()] == [again["id"], first["id"]]


def test_practice_is_the_students_own(w):
    p = w.c.post("/api/v1/my-practice", json={"subject": "Science"}, headers=w.s1).json()
    assert w.c.get(f"/api/v1/my-practice/{p['id']}", headers=w.s2).status_code == 404
    assert w.c.post("/api/v1/my-practice", json={"subject": "Science"}, headers=w.ana).status_code == 403


def test_a_revise_row_practises_its_chapter_whatever_id_names_it(w, monkeypatch):
    """N-5-2: "Revise next" names a chapter by the tagger's id, the bank by
    the chapter view's. Class 10 Science differs on all 13 chapters, so
    every Practise link answered 422 although the bank held the questions."""
    from academicos.operations import homework_routes as hr
    asked: list = []
    real = hr._bank_questions

    def spy(subject, grade, chapter_ids=None):
        asked.append(chapter_ids)
        return real(subject, grade, chapter_ids)

    monkeypatch.setattr(hr, "_bank_questions", spy)
    r = w.c.post("/api/v1/my-practice", json={"subject": "Science",
                                               "chapterIds": ["science-10/acids-bases-and-salts"]}, headers=w.s1)
    assert asked[-1] == ["acids-bases-salts"], "translated to the id the bank files under"
    assert r.status_code in (200, 422), r.text


def _science_paper(w, day):
    if w.store.get_calendar_for_year(w.year) is None:
        w.store.create_calendar(academic_year_id=w.year, weekly_off_days=["sunday"], alternate_saturday_rule="none")
    exam = w.c.post("/api/v1/exams", json={"name": "Half yearly", "startDate": day, "endDate": day,
                                            "grades": [10], "academicYearId": w.year}, headers=w.p)
    assert exam.status_code == 200, exam.text
    sheet = w.c.put(f"/api/v1/exams/{exam.json()['id']}/datesheet", json={"papers": [
        {"grade": 10, "subjectId": w.sci10, "date": day, "startTime": "09:30", "endTime": "12:30"}]}, headers=w.p)
    assert sheet.status_code == 200, sheet.text
    assert w.c.post(f"/api/v1/exams/{exam.json()['id']}/publish", headers=w.p).status_code == 200
    return sheet.json()["papers"][0]["id"]


def test_exam_preparation_practises_the_papers_subject(w):
    """SA-4: an exam preparation mode before a scheduled exam."""
    paper = _science_paper(w, "2026-06-10")
    r = w.c.post("/api/v1/my-practice", json={"examPaperId": paper}, headers=w.s1)
    assert r.status_code == 200, r.text
    assert r.json()["subject"] == "Science"
    assert len(r.json()["questions"]) == 4, "a longer set: every question the (four-question) bank has"
    assert w.c.post("/api/v1/my-practice", json={"examPaperId": "nope"}, headers=w.s1).status_code == 404


def test_exam_preparation_refuses_a_paper_already_written(w, monkeypatch):
    from datetime import date
    from academicos.curriculum import routes as cr
    paper = _science_paper(w, "2026-06-03")
    monkeypatch.setattr(cr, "_school_today", lambda: date(2026, 6, 4))
    assert w.c.post("/api/v1/my-practice", json={"examPaperId": paper}, headers=w.s1).status_code == 409


def test_taught_chapters_are_named_as_the_bank_files_them(monkeypatch):
    """A chapter the section was taught, found by its printed name."""
    from types import SimpleNamespace as NS
    from academicos.curriculum import routes as cr
    from academicos.operations import practice_routes as pr
    lessons = [NS(status="completed", section_id="sec", subtopic_id="st1"),
               NS(status="scheduled", section_id="sec", subtopic_id="st2"),
               NS(status="completed", section_id="other", subtopic_id="st2")]
    fake = NS(enrollment_for_student=lambda _id: NS(section_id="sec"),
              academic_years_for_school=lambda _s: [NS(start_date="2026-04-01", end_date="2027-03-31")],
              scheduled_lessons_for_date_range=lambda *_a: lessons,
              get_subtopic=lambda i: NS(topic_id="t" + i), get_topic=lambda i: NS(chapter_id="c" + i),
              get_chapter=lambda i: NS(name={"ctst1": "Acids, Bases and Salts", "ctst2": "Light"}[i]))
    monkeypatch.setattr(cr, "_require", lambda: fake)
    me = NS(id="s1", school_id="school_1")
    assert pr._taught_chapters(me, "Science", 10, "2026-06-10") == ["acids-bases-salts"], \
        "only completed lessons of the student's own section"
