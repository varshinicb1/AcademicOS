"""Homework (TA-4, SA-2) through the HTTP routes: a teacher sets it for the
sections they teach, students see it without answers and submit, MCQs mark
themselves, the teacher marks the rest, and everyone is told. The bank is
replaced with four fixed questions so the tests do not depend on the served
bank. 2026-06-01 is a Monday."""
from __future__ import annotations

from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest

from _auth_helpers import grant_consent, register_invited
from test_assessment_routes_auth import _boot_client, _register

MON = "2026-06-01"
NOW = datetime(2026, 6, 1, tzinfo=timezone.utc).isoformat()


def _q(qid, qtype, stem, marks, *, option=None, points=()):
    scheme = {"totalMarks": marks, "modelAnswer": f"model answer for {qid}", "hasPartialCredit": marks > 1,
              "markingPoints": [{"id": f"{qid}:mp{i}", "description": d, "marks": 1, "keyword": k,
                                 "synonyms": [option] if option else []} for i, (d, k) in enumerate(points)],
              "metadata": {"objective": True, "correctOption": option} if option else {}}
    return {"id": qid, "questionBankId": "test", "subject": "Science", "grade": 10, "chapterIds": ["light"],
            "bloomLevel": "remember", "difficulty": "easy", "type": qtype, "stem": stem, "answerScheme": scheme,
            "estimatedTimeMinutes": 2, "marks": marks, "source": "cbse_board_paper", "createdAt": NOW,
            "updatedAt": NOW}


BANK = [
    _q("q1", "mcq", "Which mirror always gives a virtual image? (A) convex (B) concave (C) plane-concave (D) none",
       1, option="A", points=[("Correct option A: convex", "convex")]),
    _q("q2", "mcq", "The unit of power of a lens is (A) metre (B) dioptre (C) watt (D) joule",
       1, option="B", points=[("Correct option B: dioptre", "dioptre")]),
    _q("q3", "short_answer", "State two laws of reflection.", 2,
       points=[("angle of incidence equals angle of reflection", "angle of incidence equals angle of reflection"),
               ("incident ray, normal and reflected ray lie in one plane", "same plane")]),
    _q("q4", "mcq", "Which gas do plants give out in light? (A) CO2 (B) O2 (C) N2 (D) H2", 1, option="B",
       points=[("Correct option B: O2", "O2")]),
]
CHAPTERS = [{"chapter_id": "light", "chapter_name": "Light – Reflection and Refraction", "question_count": 3},
            {"chapter_id": "life", "chapter_name": "Life Processes", "question_count": 1}]


def _h(u):
    return {"Authorization": f"Bearer {u['token']}"}


@pytest.fixture
def w(tmp_path, monkeypatch):
    from academicos.curriculum import routes as cr
    from academicos.operations import homework_routes as hr
    from academicos.operations.store import OperationsStore

    monkeypatch.setattr(OperationsStore, "deliver_inline", True)
    monkeypatch.setattr(hr, "_bank_questions", lambda subject, grade, chapter_ids=None: [
        q for q in BANK if not chapter_ids or ("light" in chapter_ids and q["id"] != "q4")
        or ("life" in chapter_ids and q["id"] == "q4")])
    monkeypatch.setattr(hr, "_bank_chapters", lambda subject, grade: CHAPTERS)
    with _boot_client(tmp_path, monkeypatch) as c:
        p = _register(c, "school_1", "p1@example.com", "Priya", principal_key="test-bootstrap-key")
        p2 = _register(c, "school_2", "p2@example.com", "Ravi", principal_key="test-bootstrap-key")
        ana = _register(c, "school_1", "ana@example.com", "Ana")
        bala = _register(c, "school_1", "bala@example.com", "Bala")
        s1 = register_invited(c, "school_1", "s1@example.com", name="Asha", role="student")
        s2 = register_invited(c, "school_1", "s2@example.com", name="Bhavna", role="student")
        s3 = register_invited(c, "school_1", "s3@example.com", name="Charu", role="student")
        monkeypatch.setattr(cr, "_school_today", lambda: date(2026, 6, 1))
        store = cr._require()
        year = store.create_academic_year(school_id="school_1", label="2026-27", start_date="2026-04-01",
                                          end_date="2027-03-31")
        g10 = store.create_grade(academic_year_id=year.id, number=10)
        g9 = store.create_grade(academic_year_id=year.id, number=9)
        [a10] = store.sections_for_grade(g10.id)
        b10 = store.create_section(grade_id=g10.id, name="B")
        [a9] = store.sections_for_grade(g9.id)
        sci10 = store.create_subject(grade_id=g10.id, name="Science")
        sci9 = store.create_subject(grade_id=g9.id, name="Science")
        store.set_allocation(section_id=a10.id, subject_id=sci10.id, teacher_id=ana["user"]["id"], periods_per_week=6)
        store.set_allocation(section_id=b10.id, subject_id=sci10.id, teacher_id=bala["user"]["id"], periods_per_week=6)
        store.set_allocation(section_id=a9.id, subject_id=sci9.id, teacher_id=bala["user"]["id"], periods_per_week=6)
        ids = {n: u["user"]["id"] for n, u in (("s1", s1), ("s2", s2), ("s3", s3))}
        store.enroll_student(school_id="school_1", student_id=ids["s1"], section_id=a10.id)
        store.enroll_student(school_id="school_1", student_id=ids["s2"], section_id=a10.id)
        store.enroll_student(school_id="school_1", student_id=ids["s3"], section_id=b10.id)
        grant_consent("school_1", ids["s1"], ids["s2"], ids["s3"])
        yield SimpleNamespace(c=c, p=_h(p), p2=_h(p2), ana=_h(ana), bala=_h(bala), s1=_h(s1), s2=_h(s2), s3=_h(s3),
                              ids=ids, a10=a10.id, b10=b10.id, a9=a9.id, sci10=sci10.id, sci9=sci9.id,
                              year=year.id, store=store)


def _create(w, who, **body):
    payload = {"subjectId": w.sci10, "sectionIds": [w.a10], "title": "Light practice", "dueDate": "2026-06-03",
               "questionIds": ["q1", "q2", "q3"]}
    payload.update(body)
    return w.c.post("/api/v1/homework", json=payload, headers=getattr(w, who))


def test_a_teacher_sets_homework_only_where_they_teach(w):
    r = _create(w, "ana")
    assert r.status_code == 200, r.text
    hw = r.json()
    assert hw["status"] == "published" and hw["totalMarks"] == 4 and hw["students"] == 2
    assert hw["sectionNames"] == ["10-A"] and [q["id"] for q in hw["questions"]] == ["q1", "q2", "q3"]
    assert _create(w, "ana", sectionIds=[w.b10]).status_code == 403          # Bala teaches 10-B
    assert _create(w, "p", sectionIds=[w.a10, w.b10]).status_code == 200    # the principal may
    assert _create(w, "ana", sectionIds=[w.a9]).status_code == 422          # class 9 does not study sci10
    assert _create(w, "p2").status_code == 403                               # another school's subject
    assert _create(w, "s1").status_code == 403                               # students cannot set homework
    assert _create(w, "ana", dueDate="2026-05-31").status_code == 422
    assert _create(w, "ana", questionIds=["q1", "nope"]).status_code == 422
    assert _create(w, "ana", questionIds=[]).status_code == 422


def test_questions_can_be_picked_from_chapters(w):
    r = _create(w, "ana", questionIds=[], chapterIds=["light"], count=2)
    assert r.status_code == 200, r.text
    picked = [q["id"] for q in r.json()["questions"]]
    assert len(picked) == 2 and set(picked) <= {"q1", "q2", "q3"}


def test_students_are_told_and_see_it_without_answers(w):
    hw = _create(w, "ana").json()
    inbox = w.c.get("/api/v1/notifications", headers=w.s1).json()
    item = next(i for i in inbox["items"] if i["kind"] == "homework_assigned")
    assert item["title"] == "New homework: Science" and "Due 2026-06-03" in item["body"]
    assert item["link"] == f"/my-homework/{hw['id']}"
    assert not any(i["kind"] == "homework_assigned" for i in w.c.get("/api/v1/notifications", headers=w.s3).json()["items"])

    [mine] = w.c.get("/api/v1/my-homework", headers=w.s1).json()
    assert mine["myStatus"] == "not_submitted" and mine["overdue"] is False
    detail = w.c.get(f"/api/v1/my-homework/{hw['id']}", headers=w.s1).json()
    assert "answerScheme" not in str(detail) and "model answer" not in str(detail)
    assert [q["id"] for q in detail["questions"]] == ["q1", "q2", "q3"]
    assert w.c.get("/api/v1/my-homework", headers=w.s3).json() == []                        # 10-B
    assert w.c.get(f"/api/v1/my-homework/{hw['id']}", headers=w.s3).status_code == 404
    assert w.c.get("/api/v1/my-homework", headers=w.ana).status_code == 403                 # students only


def test_an_all_mcq_homework_is_final_at_once(w):
    hw = _create(w, "ana", questionIds=["q1", "q2"]).json()
    r = w.c.post(f"/api/v1/my-homework/{hw['id']}/submit", json={"answers": {"q1": "A", "q2": "(C)"}}, headers=w.s1)
    assert r.status_code == 200, r.text
    out = r.json()
    assert out["myStatus"] == "graded" and out["marks"] == 1
    assert [e["awardedMarks"] for e in out["evaluations"]] == [1, 0]
    assert out["evaluations"][0]["modelAnswer"] == "model answer for q1"
    inbox = w.c.get("/api/v1/notifications", headers=w.s1).json()["items"]
    assert any(i["kind"] == "homework_graded" and "1 out of 2" in i["body"] for i in inbox)
    again = w.c.post(f"/api/v1/my-homework/{hw['id']}/submit", json={"answers": {"q1": "A", "q2": "B"}}, headers=w.s1)
    assert again.status_code == 409                                          # marked; cannot change


def test_a_written_answer_waits_for_the_teacher(w):
    hw = _create(w, "ana").json()
    answers = {"q1": "A", "q2": "B", "q3": "The angle of incidence equals the angle of reflection, and the "
                                          "incident ray, the normal and the reflected ray lie in the same plane."}
    out = w.c.post(f"/api/v1/my-homework/{hw['id']}/submit", json={"answers": answers}, headers=w.s1).json()
    assert out["myStatus"] == "submitted" and out["marks"] is None and out["evaluations"] == []
    # a resend before marking is accepted and counted
    out = w.c.post(f"/api/v1/my-homework/{hw['id']}/submit", json={"answers": answers}, headers=w.s1).json()
    assert out["myStatus"] == "submitted"
    assert w.c.post(f"/api/v1/my-homework/{hw['id']}/submit", json={"answers": {"zz": "A"}},
                    headers=w.s1).status_code == 422

    rows = {r["studentId"]: r for r in w.c.get(f"/api/v1/homework/{hw['id']}/submissions", headers=w.ana).json()}
    s1, s2 = rows[w.ids["s1"]], rows[w.ids["s2"]]
    assert s1["status"] == "submitted" and s1["attempts"] == 2 and s1["needsReview"] >= 1
    assert s2["status"] == "not_submitted" and s2["studentName"] == "Bhavna"
    assert w.c.get(f"/api/v1/homework/{hw['id']}/submissions", headers=w.bala).status_code == 403

    bad = w.c.post(f"/api/v1/homework/{hw['id']}/submissions/{w.ids['s1']}/grade", json={"marks": {"q3": 5}},
                   headers=w.ana)
    assert bad.status_code == 422
    assert w.c.post(f"/api/v1/homework/{hw['id']}/submissions/{w.ids['s2']}/grade", json={"marks": {}},
                    headers=w.ana).status_code == 404
    g = w.c.post(f"/api/v1/homework/{hw['id']}/submissions/{w.ids['s1']}/grade",
                 json={"marks": {"q3": 2}, "feedback": "Well written."}, headers=w.ana)
    assert g.status_code == 200, g.text
    assert g.json()["marks"] == 4 and g.json()["status"] == "graded"
    mine = w.c.get(f"/api/v1/my-homework/{hw['id']}", headers=w.s1).json()
    assert mine["marks"] == 4 and mine["feedback"] == "Well written."
    assert any(i["kind"] == "homework_graded" for i in w.c.get("/api/v1/notifications", headers=w.s1).json()["items"])


def test_submitting_needs_the_parents_consent(w):
    from academicos.assessment import consent_routes
    hw = _create(w, "ana", questionIds=["q1"]).json()
    consent_routes._require_store().revoke_consent(school_id="school_1", student_id=w.ids["s2"],
                                                   revoked_by="test-fixture")
    r = w.c.post(f"/api/v1/my-homework/{hw['id']}/submit", json={"answers": {"q1": "A"}}, headers=w.s2)
    assert r.status_code == 409


def test_remind_close_and_late(w, monkeypatch):
    from academicos.curriculum import routes as cr
    hw = _create(w, "ana", questionIds=["q1"]).json()
    w.c.post(f"/api/v1/my-homework/{hw['id']}/submit", json={"answers": {"q1": "A"}}, headers=w.s1)
    r = w.c.post(f"/api/v1/homework/{hw['id']}/remind", headers=w.ana)
    assert r.json() == {"reminded": 1}
    w.c.post(f"/api/v1/homework/{hw['id']}/remind", headers=w.ana)
    due = [i for i in w.c.get("/api/v1/notifications", headers=w.s2).json()["items"] if i["kind"] == "homework_due"]
    assert len(due) == 1, "pressed twice in a day, told once"

    monkeypatch.setattr(cr, "_school_today", lambda: date(2026, 6, 5))
    [mine] = w.c.get("/api/v1/my-homework", headers=w.s2).json()
    assert mine["overdue"] is True
    late = w.c.post(f"/api/v1/my-homework/{hw['id']}/submit", json={"answers": {"q1": "B"}}, headers=w.s2)
    assert late.status_code == 200
    rows = {r["studentId"]: r for r in w.c.get(f"/api/v1/homework/{hw['id']}/submissions", headers=w.ana).json()}
    assert rows[w.ids["s2"]]["late"] is True and rows[w.ids["s1"]]["late"] is False

    assert w.c.post(f"/api/v1/homework/{hw['id']}/close", headers=w.ana).json()["status"] == "closed"
    assert w.c.post(f"/api/v1/homework/{hw['id']}/publish", headers=w.ana).status_code == 409
    assert w.c.post(f"/api/v1/homework/{hw['id']}/remind", headers=w.ana).status_code == 409


def test_a_draft_is_hidden_until_published(w):
    hw = _create(w, "ana", publish=False).json()
    assert hw["status"] == "draft"
    assert w.c.get("/api/v1/my-homework", headers=w.s1).json() == []
    assert not any(i["kind"] == "homework_assigned"
                   for i in w.c.get("/api/v1/notifications", headers=w.s1).json()["items"])
    assert w.c.post(f"/api/v1/homework/{hw['id']}/publish", headers=w.ana).json()["status"] == "published"
    assert len(w.c.get("/api/v1/my-homework", headers=w.s1).json()) == 1
    assert any(i["kind"] == "homework_assigned" for i in w.c.get("/api/v1/notifications", headers=w.s1).json()["items"])


def test_lists_are_scoped_to_who_teaches(w):
    mine = _create(w, "ana").json()
    theirs = _create(w, "p", sectionIds=[w.b10], title="B only").json()
    assert {h["id"] for h in w.c.get("/api/v1/homework", headers=w.ana).json()} == {mine["id"]}
    assert {h["id"] for h in w.c.get("/api/v1/homework", headers=w.bala).json()} == {theirs["id"]}
    assert {h["id"] for h in w.c.get("/api/v1/homework", headers=w.p).json()} == {mine["id"], theirs["id"]}
    assert w.c.get("/api/v1/homework", headers=w.p2).json() == []
    assert w.c.get(f"/api/v1/homework/{mine['id']}", headers=w.p2).status_code == 403
    assert w.c.get(f"/api/v1/homework/{mine['id']}", headers=w.bala).status_code == 403


def test_the_suggestion_follows_the_sections_plan(w):
    s = w.store
    board = s.create_board(name="CBSE", code="CBSE")
    book = s.create_book(subject_id=w.sci10, board_id=board.id, title="Science")
    s.select_book(book.id)
    unit = s.create_unit(canonical_id="u1", book_id=book.id, unit_no="1", name="Natural phenomena")
    ch = s.create_chapter(canonical_id="c1", unit_id=unit.id, name="Light - Reflection and Refraction")
    topic = s.create_topic(canonical_id="t1", chapter_id=ch.id, name="Reflection")
    sub = s.create_subtopic(canonical_id="st1", topic_id=topic.id, name="Laws of reflection")
    s.create_scheduled_lesson(school_id="school_1", academic_year_id=w.year, book_id=book.id, subtopic_id=sub.id,
                              date="2026-05-29", section_id=w.a10)
    r = w.c.get("/api/v1/homework/suggestion", params={"sectionId": w.a10, "subjectId": w.sci10}, headers=w.ana)
    assert r.status_code == 200, r.text
    out = r.json()
    assert out["lessonFound"] and out["date"] == "2026-05-29" and out["subtopicName"] == "Laws of reflection"
    assert [c["chapterId"] for c in out["bankChapters"]] == ["light"] and out["note"] is None
    assert {q["id"] for q in out["questions"]} == {"q1", "q2", "q3"}
    none = w.c.get("/api/v1/homework/suggestion", params={"sectionId": w.b10, "subjectId": w.sci10},
                   headers=w.ana).json()
    assert none["lessonFound"] is False and len(none["bankChapters"]) == 2
    assert w.c.get("/api/v1/homework/suggestion", params={"sectionId": w.a9, "subjectId": w.sci10},
                   headers=w.ana).status_code == 422


def test_chapter_picks_filter_by_type_and_skip_what_the_section_had(w):
    first = _create(w, "ana", questionIds=[], chapterIds=["light"], count=1, types=["short_answer"]).json()
    assert [q["id"] for q in first["questions"]] == ["q3"]
    assert _create(w, "ana", questionIds=[], chapterIds=["light"], types=["long_answer"]).status_code == 422
    second = _create(w, "ana", questionIds=[], chapterIds=["light"], count=2, title="Again").json()
    assert "q3" not in {q["id"] for q in second["questions"]}, "10-A already had q3"


def test_marked_homework_counts_in_the_principals_school_insights(w):
    """QA S-04: four students enrolled, homework marked 4/5, and School
    insights read "0 Students, 0% mastery": it counted only marked papers."""
    url = "/api/v1/insights/school/school_1"
    before = w.c.get(url, headers=w.p).json()
    assert before["students"] == 3 and before["studentsWithEvidence"] == 0 and before["subjects"] == []

    hw = _create(w, "ana").json()
    w.c.post(f"/api/v1/my-homework/{hw['id']}/submit", json={"answers": {"q1": "A", "q2": "B"}}, headers=w.s1)
    g = w.c.post(f"/api/v1/homework/{hw['id']}/submissions/{w.ids['s1']}/grade", json={"marks": {"q3": 2}},
                 headers=w.ana)
    assert g.status_code == 200, g.text
    after = w.c.get(url, headers=w.p).json()
    assert after["students"] == 3 and after["studentsWithEvidence"] == 1
    [science] = after["subjects"]
    assert (science["subject"], science["grade"], science["students"]) == ("Science", 10, 1)
    assert after["averageMastery"] > 0
