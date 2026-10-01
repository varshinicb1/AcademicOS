"""Every section's dated plan in one principal action (N-67-5; ADM-2, ADM-3,
SCH-4).

Before: a school set up on the web had no dated plan. Seeding proposes each
chapter's topics, but approving them was a chapter-at-a-time step on another
tab, and each section and subject was then planned on its own. Coverage read
0 of 0 and the "falling behind" alert could never fire.

This replays a new school the way the web sets it up -- seed class 10, a
calendar, a bell, a second section, allocations -- and asks for the plans.
"""
from __future__ import annotations

from test_assessment_routes_auth import _boot_client, _register
from test_web_school_setup import BASE, PRINCIPAL_KEY, _session


def _school(client, auth, invite):
    from academicos.curriculum.routes import _school_today
    label, start, end = _session(_school_today())
    assert client.post(f"{BASE}/seed/cbse", headers=auth, json={
        "grade": 10, "academicYearLabel": label, "startDate": start, "endDate": end}).status_code == 200
    year = client.get(f"{BASE}/academic-years", params={"school_id": "school_1"}, headers=auth).json()[0]["id"]
    assert client.post(f"{BASE}/academic-years/{year}/calendar", headers=auth,
                       json={"weeklyOffDays": ["sunday"], "alternateSaturdayRule": "none"}).status_code == 200
    slots = [{"start": f"{8 + i:02d}:00", "end": f"{8 + i:02d}:45"} for i in range(7)]
    assert client.post(f"{BASE}/academic-years/{year}/bell-schedules", headers=auth,
                       json={"name": "Main", "slots": slots}).status_code == 200
    grade = client.get(f"{BASE}/academic-years/{year}/grades", headers=auth).json()[0]["id"]
    client.post(f"{BASE}/grades/{grade}/sections", headers=auth, json={"name": "B"})
    sections = {s["name"]: s["id"] for s in client.get(f"{BASE}/academic-years/{year}/sections", headers=auth).json()}
    subjects = {s["name"]: s["id"] for s in client.get(f"{BASE}/grades/{grade}/subjects", headers=auth).json()}
    teacher = invite("Meera")
    for sec in sections.values():
        r = client.put(f"{BASE}/sections/{sec}/allocations/{subjects['Science']}", headers=auth,
                       json={"teacherId": teacher, "periodsPerWeek": 6})
        assert r.status_code == 200, r.text
    return year, sections


def test_one_action_plans_every_section_of_a_new_school(tmp_path, monkeypatch):
    from _auth_helpers import PASSWORD, register_invited
    with _boot_client(tmp_path, monkeypatch) as client:
        principal = _register(client, "school_1", "head@school1.test", "Head", principal_key=PRINCIPAL_KEY)
        auth = {"Authorization": f"Bearer {principal['token']}"}

        def invite(name):
            return register_invited(client, "school_1", f"{name.lower()}@school1.test", name=name,
                                    role="teacher")["user"]["id"]

        year, sections = _school(client, auth, invite)

        # Without the principal's approval nothing proposed becomes curriculum.
        before = client.post(f"{BASE}/academic-years/{year}/lesson-plans", headers=auth, json={})
        assert before.status_code == 200, before.text
        assert before.json()["runsApproved"] == 0
        assert all(p["lessonsCreated"] == 0 for p in before.json()["plans"]) or before.json()["notPlanned"]

        built = client.post(f"{BASE}/academic-years/{year}/lesson-plans", headers=auth,
                            json={"approveProposedTopics": True})
        assert built.status_code == 200, built.text
        body = built.json()
        assert body["runsApproved"] > 0 and body["subtopicsCreated"] > 0
        plans = {p["sectionName"]: p for p in body["plans"]}
        assert set(plans) == {"10-A", "10-B"}, body["notPlanned"]
        assert all(p["lessonsCreated"] > 0 and p["subjectName"] == "Science" for p in plans.values()), body

        # Each section now has its own dated plan.
        book = client.get(f"{BASE}/subjects/{_science(client, auth, year)}/selected-book", headers=auth).json()["id"]
        for sec in sections.values():
            lessons = client.get(f"{BASE}/books/{book}/schedule", headers=auth,
                                 params={"academic_year_id": year, "sectionId": sec}).json()
            assert lessons and all(l["sectionId"] == sec for l in lessons)

        # Again: nothing is approved twice, and the plans are made again, not doubled.
        again = client.post(f"{BASE}/academic-years/{year}/lesson-plans", headers=auth,
                            json={"approveProposedTopics": True}).json()
        assert again["runsApproved"] == 0
        assert {p["sectionName"] for p in again["plans"]} == {"10-A", "10-B"}

        # A teacher cannot.
        teacher = client.post("/api/v1/auth/login", json={"email": "meera@school1.test", "password": PASSWORD})
        assert teacher.status_code == 200, teacher.text
        t = {"Authorization": f"Bearer {teacher.json()['token']}"}
        assert client.post(f"{BASE}/academic-years/{year}/lesson-plans", headers=t, json={}).status_code == 403


def _science(client, auth, year):
    grade = client.get(f"{BASE}/academic-years/{year}/grades", headers=auth).json()[0]["id"]
    return next(s["id"] for s in client.get(f"{BASE}/grades/{grade}/subjects", headers=auth).json()
                if s["name"] == "Science")
