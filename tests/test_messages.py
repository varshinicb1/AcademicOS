"""MSG-1 teacher-parent messaging: a parent writes to their child's teachers
(and only them), the teacher replies, each side hears of the other's message
and sees it unread until they open it; nobody else reads it; staff write only
to parents of students they teach; erasing the student or the parent takes
the conversation with them. Cover fixture: Asha is in 10-B, taught by Ana
(Science) and Bala (Maths); Chitra teaches 9-A only."""
from __future__ import annotations

from test_cover_routes import w  # noqa: F401 - `w` is a fixture
from test_parent_notices import _h, _items, _parent


def _start(w, headers, student, with_id, body="Hello"):
    return w.c.post("/api/v1/conversations", json={"studentId": student, "withId": with_id, "body": body},
                    headers=headers)


def test_a_parent_writes_to_a_teacher_and_the_teacher_replies(w):
    sid, mum = _parent(w)
    contacts = w.c.get(f"/api/v1/children/{sid}/contacts", headers=_h(mum))
    assert contacts.status_code == 200, contacts.text
    roles = {c["name"]: c["role"] for c in contacts.json()}
    assert roles == {"Ana": "Science teacher", "Bala": "Maths teacher", "Priya": "principal"}

    r = _start(w, _h(mum), sid, w.uid["ana"], "Asha was unwell yesterday. Can she submit the worksheet on Friday?")
    assert r.status_code == 200, r.text
    conv = r.json()
    assert conv["withName"] == "Ana" and conv["studentName"] == "Asha" and conv["messages"][0]["mine"] is True

    [notice] = _items(w, w.t["ana"], "message_received")
    assert notice["title"] == "Message from Meena" and notice["body"].startswith("About Asha: Asha was unwell")
    assert notice["link"] == f"/school/messages/{conv['id']}"
    [mine] = w.c.get("/api/v1/conversations", headers=w.t["ana"]).json()
    assert mine["unread"] == 1 and mine["withName"] == "Meena"

    opened = w.c.get(f"/api/v1/conversations/{conv['id']}", headers=w.t["ana"])
    assert opened.status_code == 200 and opened.json()["messages"][0]["mine"] is False
    assert w.c.get("/api/v1/conversations", headers=w.t["ana"]).json()[0]["unread"] == 0
    r = w.c.post(f"/api/v1/conversations/{conv['id']}/messages", json={"body": "Yes, Friday is fine."},
                 headers=w.t["ana"])
    assert r.status_code == 200 and len(r.json()["messages"]) == 2
    assert _items(w, _h(mum), "message_received")[0]["title"] == "Message from Ana"
    assert w.c.get("/api/v1/conversations", headers=_h(mum)).json()[0]["unread"] == 1

    # writing again opens no second conversation
    assert _start(w, _h(mum), sid, w.uid["ana"], "Thank you").json()["id"] == conv["id"]
    assert len(w.c.get("/api/v1/conversations", headers=_h(mum)).json()) == 1


def test_nobody_outside_the_conversation_reads_it_and_parents_reach_only_their_childs_teachers(w):
    sid, mum = _parent(w)
    conv = _start(w, _h(mum), sid, w.uid["ana"]).json()
    for who in (w.t["bala"], w.t["chitra"], w.stu, w.p2, w.p):
        assert w.c.get(f"/api/v1/conversations/{conv['id']}", headers=who).status_code == 404
        assert w.c.post(f"/api/v1/conversations/{conv['id']}/messages", json={"body": "x"},
                        headers=who).status_code == 404
    r = _start(w, _h(mum), sid, w.uid["chitra"])
    assert r.status_code == 403 and "class teacher" in r.json()["detail"]
    assert w.c.get("/api/v1/conversations", headers=w.stu).status_code == 403
    assert w.c.post("/api/v1/conversations", json={"studentId": sid, "withId": w.uid["ana"], "body": ""},
                    headers=_h(mum)).status_code == 422


def test_staff_write_only_to_parents_of_students_they_teach(w):
    sid, mum = _parent(w)
    parent_id = mum["user"]["id"]
    assert _start(w, w.t["chitra"], sid, parent_id).status_code == 403
    assert _start(w, w.t["bala"], sid, w.uid["ana"]).status_code == 404, "Ana is not Asha's parent"
    r = _start(w, w.t["bala"], sid, parent_id, "Asha did very well in the Maths test.")
    assert r.status_code == 200, r.text
    assert _items(w, _h(mum), "message_received")[0]["body"] == "About Asha: Asha did very well in the Maths test."
    assert _start(w, w.p, sid, parent_id).status_code == 200, "the principal reaches any parent of the school"
    assert _start(w, w.p2, sid, parent_id).status_code in (403, 404), "not another school's principal"


def test_a_parent_whose_link_ended_reads_but_cannot_write(w):
    sid, mum = _parent(w)
    conv = _start(w, _h(mum), sid, w.uid["ana"]).json()
    assert w.c.delete(f"/api/v1/guardianships/{mum['user']['id']}/{sid}", headers=w.p).status_code == 200
    r = w.c.post(f"/api/v1/conversations/{conv['id']}/messages", json={"body": "x"}, headers=_h(mum))
    assert r.status_code == 403 and "link" in r.json()["detail"]


def test_erasing_the_student_or_the_parent_takes_the_conversation(w):
    from academicos.operations.routes import store
    sid, mum = _parent(w)
    _start(w, _h(mum), sid, w.uid["ana"])
    preview = store().forget_parent(mum["user"]["id"], email="mum@example.com", dry_run=True)
    assert preview["conversations"] == 1 and preview["conversation_messages"] == 1
    counts = store().forget_student(sid, school_id="school_1", email="s1@example.com", name="Asha")
    assert counts["conversations"] == 1 and counts["conversation_messages"] == 1
    assert _items(w, w.t["ana"], "message_received") == [], "the teacher's notice named the student"
