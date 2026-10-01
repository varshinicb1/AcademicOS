"""Exam days and exam duty in the cover engine and the plans (v3 audit
N-3-12). The engine read only the timetable, substitution duties and
make-ups. On the day of a Class 10 paper it proposed invigilators as
substitutes during their paper, showed grade 10's day as regular teaching
through the paper, and left 10-A's Science lesson in the plan that day.

test_cover_routes' world: 2026-06-01 is a Monday, and period n runs from
(7+n):00 to (7+n):45. 10-A has Science (Ana) in P1 and Maths (Bala) in P2;
10-B has Maths (Bala) in P1 and Science (Ana) in P2; 9-A has Science
(Chitra) in P1 and Maths (Dev) in P3. The paper here is Class 10 Science,
09:00-09:45: grade 10's period 2. Dev invigilates 10-A, Bala 10-B.
"""
from __future__ import annotations

from academicos.curriculum import scheduling

from test_cover_routes import BASE, MON, _apply, w  # noqa: F401 - `w` is a fixture


def _publish_paper(w, start="09:00", end="09:45") -> str:
    r = w.c.post("/api/v1/exams", json={"name": "Unit test 1", "startDate": MON, "endDate": "2026-06-06",
                                         "grades": [10], "academicYearId": w.year}, headers=w.p)
    assert r.status_code == 200, r.text
    eid = r.json()["id"]
    paper = _datesheet(w, eid, start, end)
    roster = w.c.put(f"/api/v1/exams/{eid}/invigilation", json={"duties": [
        {"examPaperId": paper, "sectionId": w.a10, "teacherId": w.uid["dev"]},
        {"examPaperId": paper, "sectionId": w.b10, "teacherId": w.uid["bala"]}]}, headers=w.p)
    assert roster.status_code == 200, roster.text
    assert w.c.post(f"/api/v1/exams/{eid}/publish", headers=w.p).status_code == 200
    return eid


def _datesheet(w, eid: str, start: str, end: str) -> str:
    r = w.c.put(f"/api/v1/exams/{eid}/datesheet", json={"papers": [
        {"grade": 10, "subjectId": w.sci10, "date": MON, "startTime": start, "endTime": end}]}, headers=w.p)
    assert r.status_code == 200, r.text
    return r.json()["papers"][0]["id"]


def _decide(w, leave) -> dict:
    subs = w.c.post(f"{BASE}/leave-requests/{leave['id']}/decision", json={"approve": True},
                    headers=w.p).json()["substitutions"]
    return {(s["sectionId"], s["period"]): s for s in subs}


def test_an_invigilator_is_not_proposed_during_their_paper(w):
    """Chitra is away and 9-A has Science in period 2 as well. Dev and Bala
    invigilate then, so neither may cover it; Ana's 10-B is in the exam
    hall, so she is free, and she teaches Science. Before the fix Dev, the
    invigilator, was the only one offered."""
    [sci9] = {e.subject_id for e in w.store.timetable_for_section(w.a9) if e.period == 1}
    [mat9] = {e.subject_id for e in w.store.timetable_for_section(w.a9) if e.period == 3}
    w.store.replace_section_timetable(w.a9, [{"day_of_week": 0, "period": p, "subject_id": s}
                                             for p, s in ((1, sci9), (2, sci9), (3, mat9))])
    _publish_paper(w)
    subs = _decide(w, _apply(w, "chitra").json())
    duty = subs[(w.a9, 2)]
    cands = [c["teacherId"] for c in w.c.get(f"{BASE}/substitutions/{duty['id']}/candidates", headers=w.p).json()]
    assert cands == [w.uid["ana"]], "Dev and Bala are invigilating 09:00-09:45"
    assert (duty["substituteId"], duty["mode"]) == (w.uid["ana"], "substitute")
    # Period 1 is before the paper: Dev is free then.
    assert subs[(w.a9, 1)]["substituteId"] == w.uid["dev"]


def test_a_class_sitting_a_paper_is_not_taught_and_needs_no_cover(w):
    _publish_paper(w)
    day = w.c.get(f"{BASE}/day", params={"date": MON, "sectionId": w.b10}, headers=w.p).json()
    assert [(r["period"], r["kind"]) for r in day] == [(1, "regular"), (2, "exam")]
    assert day[1]["teacherId"] is None and "Science paper, 09:00-09:45" in day[1]["note"]
    assert day[1]["changed"] is True
    student = w.c.get(f"{BASE}/my-day", params={"date": MON}, headers=w.stu).json()
    assert [r["kind"] for r in student] == ["regular", "exam"], "the 10-B student sees the paper"
    bala = w.c.get(f"{BASE}/my-day", params={"date": MON}, headers=w.t["bala"]).json()
    assert {(r["sectionId"], r["kind"]) for r in bala} == {(w.b10, "regular"), (w.a10, "exam")}
    # Ana's leave that day: her 10-B period is the paper, so only 10-A's needs anyone.
    subs = _decide(w, _apply(w, "ana").json())
    assert set(subs) == {(w.a10, 1)}
    # Grade 9 does not sit it.
    day9 = w.c.get(f"{BASE}/day", params={"date": MON, "sectionId": w.a9}, headers=w.p).json()
    assert {r["kind"] for r in day9} == {"regular"}


def _science_book(w) -> str:
    """A grade-10 Science book: 3 subtopics of 2 periods each."""
    st = w.store
    board = st.create_board(name="CBSE", code="CBSE")
    book = st.create_book(subject_id=w.sci10, board_id=board.id, title="Science")
    unit = st.create_unit(canonical_id="u:1", book_id=book.id, unit_no="1", name="Unit 1", marks=20, seq=0)
    chapter = st.create_chapter(canonical_id="c:1", unit_id=unit.id, name="Chapter 1", seq=0)
    topic = st.create_topic(canonical_id="t:1", chapter_id=chapter.id, name="Topic 1", seq=0)
    for i in range(3):
        sub = st.create_subtopic(canonical_id=f"st:{i}", topic_id=topic.id, name=f"Subtopic {i}", seq=i)
        st.create_teaching_time_estimate(subtopic_id=sub.id, academic_year_id=w.year, estimated_minutes=90,
                                         estimated_periods=2)
    return book.id


def _dates(w, book_id: str, section_id: str) -> list[str]:
    return [l.date for l in w.store.scheduled_lessons_for_book(w.year, book_id, section_id)
            if l.status == "scheduled"]


def test_a_plan_moves_off_the_paper_and_back_when_the_paper_moves(w):
    """10-B's Science (Monday period 2, inside the paper) moves on a week;
    10-A's (period 1, before it) stays. Re-timing the paper to 10:00, when
    grade 10 has no period, gives 10-B its Monday lesson back."""
    book = _science_book(w)
    for section in (w.a10, w.b10):
        scheduling.schedule_book(w.store, school_id="school_1", academic_year_id=w.year, book_id=book,
                                 periods_per_week=1, from_date=MON, section_id=section)
    mondays = ["2026-06-01", "2026-06-08", "2026-06-15", "2026-06-22", "2026-06-29", "2026-07-06"]
    assert _dates(w, book, w.a10) == _dates(w, book, w.b10) == mondays

    eid = _publish_paper(w)
    assert _dates(w, book, w.b10) == mondays[1:] + ["2026-07-13"], "nothing is taught during the paper"
    assert _dates(w, book, w.a10) == mondays, "10-A's Science is before the paper"
    # A regenerate keeps the period off too.
    scheduling.schedule_book(w.store, school_id="school_1", academic_year_id=w.year, book_id=book,
                             periods_per_week=1, from_date=MON, section_id=w.b10, force=True)
    assert _dates(w, book, w.b10)[0] == "2026-06-08"

    _datesheet(w, eid, "10:00", "10:45")
    assert _dates(w, book, w.b10) == mondays
    day = w.c.get(f"{BASE}/day", params={"date": MON, "sectionId": w.b10}, headers=w.p).json()
    assert {r["kind"] for r in day} == {"regular"}
