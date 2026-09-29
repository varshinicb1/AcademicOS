"""Parents (M1.5, SA-6): a guardian invite for one student, the parent
account it creates, what that account can and cannot see, consent given and
withdrawn by the parent, and the principal linking and unlinking."""
from __future__ import annotations

from test_homework import _create, w  # noqa: F401 - `w` is a fixture

PASSWORD = "correct horse battery"


def _h(body):
    return {"Authorization": f"Bearer {body['token']}"}


def _parent(w, student="s1", email="mum@example.com", name="Meena", relation="mother"):
    r = w.c.post(f"/api/v1/students/{w.ids[student]}/guardian-invites", json={"relation": relation}, headers=w.p)
    assert r.status_code == 200, r.text
    reg = w.c.post("/api/v1/auth/register", json={"inviteCode": r.json()["code"], "name": name, "email": email,
                                                  "password": PASSWORD})
    assert reg.status_code == 200, reg.text
    return reg.json()


def test_a_guardian_invite_makes_a_parent_linked_to_that_child(w):
    mum = _parent(w)
    assert mum["user"]["role"] == "parent"
    h = _h(mum)
    [child] = w.c.get("/api/v1/my-children", headers=h).json()
    assert child["studentId"] == w.ids["s1"] and child["name"] == "Asha" and child["relation"] == "mother"
    assert child["sectionName"] == "10-A" and child["consent"] == "granted"
    guardians = w.c.get(f"/api/v1/students/{w.ids['s1']}/guardians", headers=w.ana).json()
    assert [(g["name"], g["relation"]) for g in guardians] == [("Meena", "mother")]
    assert w.c.get("/api/v1/my-children", headers=w.s1).status_code == 403


def test_a_parent_sees_only_their_childs_pages(w):
    h = _h(_parent(w))
    s1, s2 = w.ids["s1"], w.ids["s2"]
    assert w.c.get("/api/v1/auth/me", headers=h).status_code == 200
    assert w.c.get("/api/v1/notifications", headers=h).status_code == 200
    # every other route refuses a parent before its handler runs
    for path in ("/api/v1/curriculum/my-day?date=2026-06-01", f"/api/v1/students/{s1}/learning",
                 f"/api/v1/knowledge/{s1}", "/api/v1/homework", "/api/v1/my-homework", "/api/v1/my-learning",
                 "/api/v1/curriculum/academic-years", f"/api/v1/curriculum/day?date=2026-06-01&sectionId={w.a10}"):
        r = w.c.get(path, headers=h)
        assert r.status_code == 403, f"{path} -> {r.status_code}"
    for part in ("timetable", "homework", "learning", "consent"):
        assert w.c.get(f"/api/v1/children/{s1}/{part}", headers=h).status_code == 200, part
        assert w.c.get(f"/api/v1/children/{s2}/{part}", headers=h).status_code == 404, part
    assert w.c.get(f"/api/v1/children/{s1}/day", params={"date": "2026-06-01"}, headers=h).status_code == 200
    assert w.c.get(f"/api/v1/children/{s1}/homework", headers=w.ana).status_code == 403


def test_the_parent_sees_homework_status_and_hears_the_marks(w):
    h = _h(_parent(w))
    hw = _create(w, "ana", questionIds=["q1", "q2"]).json()
    [item] = w.c.get(f"/api/v1/children/{w.ids['s1']}/homework", headers=h).json()
    assert item["id"] == hw["id"] and item["myStatus"] == "not_submitted"
    w.c.post(f"/api/v1/my-homework/{hw['id']}/submit", json={"answers": {"q1": "A", "q2": "B"}}, headers=w.s1)
    [item] = w.c.get(f"/api/v1/children/{w.ids['s1']}/homework", headers=h).json()
    assert item["myStatus"] == "graded" and item["marks"] == 2
    inbox = w.c.get("/api/v1/notifications", headers=h).json()["items"]
    assert any(i["kind"] == "homework_graded" and "2 out of 2" in i["body"] for i in inbox)
    learning = w.c.get(f"/api/v1/children/{w.ids['s1']}/learning", headers=h).json()
    assert learning["sources"]["homework"] == 1


def test_the_parent_gives_and_withdraws_consent(w):
    h = _h(_parent(w))
    s1 = w.ids["s1"]
    out = w.c.delete(f"/api/v1/children/{s1}/consent", headers=h).json()
    assert out["status"] == "revoked"
    hw = _create(w, "ana", questionIds=["q1"]).json()
    assert w.c.post(f"/api/v1/my-homework/{hw['id']}/submit", json={"answers": {"q1": "A"}},
                    headers=w.s1).status_code == 409
    out = w.c.post(f"/api/v1/children/{s1}/consent", headers=h).json()
    assert out["status"] == "granted" and out["guardianName"] == "Meena"
    assert out["method"] == "Parent account (in-app confirmation)"
    assert w.c.post(f"/api/v1/my-homework/{hw['id']}/submit", json={"answers": {"q1": "A"}},
                    headers=w.s1).status_code == 200


def test_the_principal_links_and_unlinks(w):
    mum = _parent(w)
    pid = mum["user"]["id"]
    h = _h(mum)
    body = {"parentId": pid, "studentId": w.ids["s3"], "relation": "mother"}
    assert w.c.post("/api/v1/guardianships", json=body, headers=w.ana).status_code == 403
    assert w.c.post("/api/v1/guardianships", json=body, headers=w.p2).status_code == 403
    assert w.c.post("/api/v1/guardianships", json={**body, "relation": "aunt"}, headers=w.p).status_code == 422
    assert w.c.post("/api/v1/guardianships", json={**body, "parentId": w.ids["s2"]}, headers=w.p).status_code == 422
    assert w.c.post("/api/v1/guardianships", json=body, headers=w.p).status_code == 200
    assert {c["studentId"] for c in w.c.get("/api/v1/my-children", headers=h).json()} == {w.ids["s1"], w.ids["s3"]}
    assert w.c.delete(f"/api/v1/guardianships/{pid}/{w.ids['s3']}", headers=w.p).status_code == 200
    assert w.c.delete(f"/api/v1/guardianships/{pid}/{w.ids['s3']}", headers=w.p).status_code == 404
    assert [c["studentId"] for c in w.c.get("/api/v1/my-children", headers=h).json()] == [w.ids["s1"]]
    assert w.c.get(f"/api/v1/children/{w.ids['s3']}/homework", headers=h).status_code == 404


def test_parents_are_invited_only_for_a_student(w):
    r = w.c.post("/api/v1/auth/invites", json={"role": "parent"}, headers=w.p)
    assert r.status_code == 400 and "guardian-invites" in r.json()["detail"]
    assert w.c.post(f"/api/v1/students/{w.ids['s1']}/guardian-invites", json={}, headers=w.ana).status_code == 403
    assert w.c.post(f"/api/v1/students/{w.ids['s1']}/guardian-invites", json={}, headers=w.p2).status_code == 403
    assert w.c.post(f"/api/v1/students/{w.ids['s1']}/guardian-invites", json={"relation": "aunt"},
                    headers=w.p).status_code == 422


def test_the_staff_directory_gives_names_not_emails(w):
    rows = w.c.get("/api/v1/staff", headers=w.ana).json()
    assert {r["name"] for r in rows} >= {"Ana", "Bala", "Priya"}
    assert all(set(r) == {"id", "name", "role"} for r in rows), "no emails in a picker"
    assert w.c.get("/api/v1/staff", headers=w.s1).status_code == 403
    mum = _parent(w)
    assert w.c.get("/api/v1/staff", headers=_h(mum)).status_code == 403
