"""Notifications that run themselves (NTF-2, NTF-3): the evening-before exam
reminder for students and invigilators, the term report on a term's last
day, and a holiday declared -- lessons on it move to the next teaching days
and the people affected are told."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from _auth_helpers import grant_consent, register_invited
from test_curriculum_reschedule_integrity import BASE, _seed_book, principal_world  # noqa: F401 - fixture
from test_exams import _exam, _sheet, w  # noqa: F401 - `w` is a fixture

IST = timezone(timedelta(hours=5, minutes=30))


def _inbox(w, who):
    return w.c.get("/api/v1/notifications", headers=who).json()["items"]


def test_the_evening_before_an_exam_students_and_invigilators_hear(w):
    from academicos.operations.routes import run_automations
    eid = _exam(w)
    _sheet(w, eid, [(10, "Science", "2026-06-02"), (9, "Maths", "2026-06-03")])
    w.c.post(f"/api/v1/exams/{eid}/invigilation/auto", headers=w.p)
    evening = datetime(2026, 6, 1, 17, 30, tzinfo=IST).astimezone(timezone.utc)
    assert run_automations(evening)["exam_reminders"] == 0, "not before the exam is published"
    w.c.post(f"/api/v1/exams/{eid}/publish", headers=w.p)
    from academicos.operations.routes import store
    with store()._conn_lock:
        store().conn.execute("DELETE FROM automation_runs")
        store()._commit()
    assert run_automations(evening)["exam_reminders"] > 0
    [reminder] = [i for i in _inbox(w, w.stu) if i["kind"] == "exam_reminder"]
    assert reminder["title"] == "Exam tomorrow: Science" and "Unit test 1" in reminder["body"]
    duties = [n for n in ("ana", "bala", "chitra", "dev")
              if any(i["kind"] == "duty_reminder" for i in _inbox(w, w.t[n]))]
    assert duties, "an invigilator with a paper tomorrow hears"
    assert run_automations(evening + timedelta(hours=1))["exam_reminders"] == "done"


def test_on_a_terms_last_day_the_principal_hears_its_report_is_ready(w):
    from academicos.operations.routes import run_automations
    w.store.create_term(academic_year_id=w.year, name="Term 1", start_date="2026-04-01", end_date="2026-06-01")
    before = datetime(2026, 5, 31, 16, 0, tzinfo=IST).astimezone(timezone.utc)
    assert run_automations(before)["term_report"] == 0
    last = datetime(2026, 6, 1, 16, 0, tzinfo=IST).astimezone(timezone.utc)
    assert run_automations(last)["term_report"] == 1
    [item] = [i for i in _inbox(w, w.p) if i["kind"] == "term_report_ready"]
    assert item["title"] == "Term report: Term 1" and item["link"] == "/school/term-report"


def test_a_holiday_moves_the_lessons_on_it_and_tells_who_is_affected(principal_world, monkeypatch):
    from academicos.curriculum import routes as cr
    w = principal_world
    book = _seed_book(w.store, school_id="school_1", periods_per_week=6)
    monkeypatch.setattr(cr, "_school_today", lambda: date(2026, 6, 1))
    [section] = w.store.sections_for_grade(w.store.get_subject(w.store.get_book(book.book).subject_id).grade_id)
    stu = register_invited(w.client, "school_1", "kid@example.com", name="Kid", role="student")
    w.store.enroll_student(school_id="school_1", student_id=stu["user"]["id"], section_id=section.id)
    grant_consent("school_1", stu["user"]["id"])
    invite = w.client.post(f"/api/v1/students/{stu['user']['id']}/guardian-invites", json={"relation": "father"},
                           headers=w.auth).json()["code"]
    dad = w.client.post("/api/v1/auth/register", json={"inviteCode": invite, "name": "Ravi", "email": "dad@example.com",
                                                       "password": "correct horse battery"}).json()
    day = book.lessons[2].date
    on_day = [l.id for l in book.lessons if l.date == day]

    r = w.client.post(f"{BASE}/academic-years/{book.year}/holidays",
                      json={"date": day, "label": "Rain closure"}, headers=w.auth)
    assert r.status_code == 200, r.text
    assert r.json()["lessonsMoved"] > 0 and r.json()["notMoved"] == []
    after = {l.id: l for l in w.store.scheduled_lessons_for_book(book.year, book.book)}
    assert all(after[i].date != day for i in on_day), "nothing is left on the holiday"
    inbox = w.client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {stu['token']}"}).json()["items"]
    [told] = [i for i in inbox if i["kind"] == "holiday_declared"]
    assert told["title"] == "Holiday: Rain closure" and "10-A move to the next teaching days" in told["body"] and told["body"].count("Lessons for") == 1
    # N-8-7: the child's parent hears the same notice, once.
    inbox = w.client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {dad['token']}"}).json()["items"]
    [told] = [i for i in inbox if i["kind"] == "holiday_declared"]
    assert "10-A move to the next teaching days" in told["body"] and told["body"].count("Lessons for") == 1 and told["link"] == "/my-children"

    quiet = w.client.post(f"{BASE}/academic-years/{book.year}/holidays",
                          json={"date": "2027-01-26", "label": "Republic Day", "moveLessons": False}, headers=w.auth)
    assert quiet.status_code == 200 and quiet.json()["lessonsMoved"] is None


def test_a_holiday_imported_from_a_file_moves_lessons_and_tells_who_is_affected(principal_world, monkeypatch):
    """N-8-6: the Excel/CSV import added the day only, bypassing the holiday
    route's reflow and notices, so a year's holiday list imported after plans
    existed left lessons dated on the holidays and told no one."""
    from academicos.curriculum import routes as cr
    w = principal_world
    book = _seed_book(w.store, school_id="school_1", periods_per_week=6)
    monkeypatch.setattr(cr, "_school_today", lambda: date(2026, 6, 1))
    [section] = w.store.sections_for_grade(w.store.get_subject(w.store.get_book(book.book).subject_id).grade_id)
    stu = register_invited(w.client, "school_1", "kid@example.com", name="Kid", role="student")
    w.store.enroll_student(school_id="school_1", student_id=stu["user"]["id"], section_id=section.id)
    day = book.lessons[2].date
    on_day = [l.id for l in book.lessons if l.date == day]

    r = w.client.post("/api/v1/admin/import/holidays", params={"dryRun": "false"}, headers=w.auth,
                      json={"csv": f"date,name\n{day},Rain closure\n", "academicYearId": book.year})
    assert r.status_code == 200, r.text
    assert r.json()["applied"] is True and r.json()["counts"]["ok"] == 1
    after = {l.id: l for l in w.store.scheduled_lessons_for_book(book.year, book.book)}
    assert all(after[i].date != day for i in on_day), "nothing is left on the imported holiday"
    inbox = w.client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {stu['token']}"}).json()["items"]
    [told] = [i for i in inbox if i["kind"] == "holiday_declared"]
    assert told["title"] == "Holiday: Rain closure" and "move to the next teaching days" in told["body"]
