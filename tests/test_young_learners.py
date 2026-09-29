"""Young learners (SA-7): in classes 1-5 the parent does the app with the
child -- the parent opens the child's homework and hands in the answers,
audited as the parent's action; from class 6 the child hands in their own.
The app learns the class from my-timetable and my-children."""
from __future__ import annotations

from _auth_helpers import grant_consent, register_invited
from test_guardians import PASSWORD, _h, _parent
from test_homework import _create, w  # noqa: F401 - `w` is a fixture


def _class_three(w):
    """A class 3 section with EVS taught by Ana, and one child in it."""
    g3 = w.store.create_grade(academic_year_id=w.year, number=3)
    [a3] = w.store.sections_for_grade(g3.id)
    evs = w.store.create_subject(grade_id=g3.id, name="EVS")
    w.store.set_allocation(section_id=a3.id, subject_id=evs.id, teacher_id=w.c.get(
        "/api/v1/auth/me", headers=w.ana).json()["id"], periods_per_week=5)
    kid = register_invited(w.c, "school_1", "kid@example.com", name="Chintu", role="student")
    w.store.enroll_student(school_id="school_1", student_id=kid["user"]["id"], section_id=a3.id)
    grant_consent("school_1", kid["user"]["id"])
    invite = w.c.post(f"/api/v1/students/{kid['user']['id']}/guardian-invites", json={"relation": "father"},
                      headers=w.p).json()
    dad = w.c.post("/api/v1/auth/register", json={"inviteCode": invite["code"], "name": "Dev", "email": "dad@example.com",
                                                  "password": PASSWORD}).json()
    return kid, dad, a3.id, evs.id


def test_a_parent_hands_in_a_young_childs_homework(w):
    from academicos.assessment.audit_log import get_audit_log
    from academicos.curriculum import routes as cr
    kid, dad, a3, evs = _class_three(w)
    hw = _create(w, "ana", subjectId=evs, sectionIds=[a3], questionIds=["q1", "q2"]).json()
    h, kid_id = _h(dad), kid["user"]["id"]

    [child] = w.c.get("/api/v1/my-children", headers=h).json()
    assert child["grade"] == 3
    assert w.c.get("/api/v1/curriculum/my-timetable", headers=_h(kid)).json()["grade"] == 3

    detail = w.c.get(f"/api/v1/children/{kid_id}/homework/{hw['id']}", headers=h)
    assert detail.status_code == 200, detail.text
    assert [q["id"] for q in detail.json()["questions"]] == ["q1", "q2"]
    assert not any(k in q for q in detail.json()["questions"]
                   for k in ("answerKey", "modelAnswer", "markingScheme", "correctOption")), "no answers before marking"

    r = w.c.post(f"/api/v1/children/{kid_id}/homework/{hw['id']}/submit", json={"answers": {"q1": "A", "q2": "B"}},
                 headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["myStatus"] == "graded" and r.json()["marks"] == 2
    [entry] = get_audit_log(cr._cfg.data_root).for_action("homework_submitted_by_guardian")
    assert entry["actor"] == dad["user"]["id"] and entry["details"]["studentId"] == kid_id


def test_from_class_six_children_hand_in_their_own(w):
    mum = _h(_parent(w))           # Asha is in 10-A
    hw = _create(w, "ana", questionIds=["q1"]).json()
    r = w.c.post(f"/api/v1/children/{w.ids['s1']}/homework/{hw['id']}/submit", json={"answers": {"q1": "A"}},
                 headers=mum)
    assert r.status_code == 403 and "hand in their own" in r.json()["detail"]
    # reading it is fine, and nobody else's child can be reached
    assert w.c.get(f"/api/v1/children/{w.ids['s1']}/homework/{hw['id']}", headers=mum).status_code == 200
    assert w.c.get(f"/api/v1/children/{w.ids['s2']}/homework/{hw['id']}", headers=mum).status_code == 404
    assert w.c.post(f"/api/v1/children/{w.ids['s1']}/homework/{hw['id']}/submit", json={"answers": {}},
                    headers=w.ana).status_code == 403
