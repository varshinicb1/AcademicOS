"""SA-7 with NTF-2: in classes 1-5 the parent does the app with the child, so
the evening reminders a young child gets -- homework due tomorrow and not
handed in, an exam paper tomorrow -- reach their linked parents too, once.
From class 6 the parent is not reminded. Cover fixture plus a class 3 section
with one child (Chintu) and his father; Asha in 10-B and her mother are the
older case. 2026-06-01 is a Monday."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from _auth_helpers import grant_consent, register_invited
from test_cover_routes import w  # noqa: F401 - `w` is a fixture
from test_parent_notices import PASSWORD, _h, _items, _parent

IST = timezone(timedelta(hours=5, minutes=30))


def _at(day, hh):
    y, m, d = map(int, day.split("-"))
    return datetime(y, m, d, hh, 0, tzinfo=IST).astimezone(timezone.utc)


def _run(now):
    from academicos.operations.routes import run_automations
    return run_automations(now)


def _class_three(w):
    g3 = w.store.create_grade(academic_year_id=w.year, number=3)
    [a3] = w.store.sections_for_grade(g3.id)
    evs = w.store.create_subject(grade_id=g3.id, name="EVS")
    w.store.set_allocation(section_id=a3.id, subject_id=evs.id, teacher_id=w.uid["ana"], periods_per_week=5)
    kid = register_invited(w.c, "school_1", "kid@example.com", name="Chintu", role="student")
    w.store.enroll_student(school_id="school_1", student_id=kid["user"]["id"], section_id=a3.id)
    grant_consent("school_1", kid["user"]["id"])
    invite = w.c.post(f"/api/v1/students/{kid['user']['id']}/guardian-invites", json={"relation": "father"},
                      headers=w.p).json()
    dad = w.c.post("/api/v1/auth/register", json={"inviteCode": invite["code"], "name": "Dev",
                                                  "email": "dad@example.com", "password": PASSWORD}).json()
    return kid, dad, a3.id, evs.id


def _homework(w, grade, section, subject_id, subject_name, due):
    from academicos.operations.routes import store
    return store().create_homework(school_id="school_1", academic_year_id=w.year, teacher_id=w.uid["ana"],
                                   subject_id=subject_id, subject_name=subject_name, grade=grade, section_ids=[section],
                                   title=f"{subject_name} worksheet", instructions="", chapter_ids=[],
                                   questions=[{"id": "q1", "marks": 1}], due_date=due, created_by=w.uid["ana"],
                                   publish=True)


def test_a_young_childs_parent_hears_of_homework_due_tomorrow_and_an_older_ones_does_not(w):
    _, mum = _parent(w)                       # Asha, class 10
    kid, dad, a3, evs = _class_three(w)
    _homework(w, 3, a3, evs, "EVS", "2026-06-01")
    _homework(w, 10, w.b10, w.sci10, "Science", "2026-06-01")
    _run(_at("2026-05-31", 18))
    _run(_at("2026-05-31", 19))
    [notice] = _items(w, _h(dad), "child_homework_due")
    assert notice["title"] == "Homework due tomorrow: Chintu" and notice["link"] == "/my-children"
    assert notice["body"].startswith("EVS worksheet is due tomorrow")
    assert len(_items(w, _h(kid), "homework_due")) == 1, "the child is still reminded"
    assert _items(w, _h(mum), "child_homework_due") == [], "from class 6 the child does it alone"


def test_a_young_childs_parent_hears_of_an_exam_tomorrow_once(w):
    from academicos.operations.routes import store
    kid, dad, a3, evs = _class_three(w)
    _, mum = _parent(w)
    eid = w.c.post("/api/v1/exams", json={"name": "Unit test 1", "startDate": "2026-06-01", "endDate": "2026-06-05",
                                          "grades": [3, 10]}, headers=w.p).json()["id"]
    r = w.c.put(f"/api/v1/exams/{eid}/datesheet", headers=w.p, json={"papers": [
        {"grade": 3, "subjectId": evs, "date": "2026-06-02"},
        {"grade": 10, "subjectId": w.sci10, "date": "2026-06-02"}]})
    assert r.status_code == 200, r.text
    assert w.c.post(f"/api/v1/exams/{eid}/publish", headers=w.p).status_code == 200
    _run(_at("2026-06-01", 17))
    _run(_at("2026-06-01", 20))
    [notice] = _items(w, _h(dad), "child_exam_reminder")
    assert notice["title"] == "Exam tomorrow: Chintu, EVS" and notice["body"].startswith("Unit test 1: EVS")
    assert _items(w, _h(mum), "child_exam_reminder") == []
    assert store().parents_of([kid["user"]["id"]], school_id="school_1") == [dad["user"]["id"]]
