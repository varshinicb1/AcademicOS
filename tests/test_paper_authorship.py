"""Who may change a paper, and who may take it or its answer key away (QA P-09).

Until 2026-10-01 every paper route checked only that the caller was staff of
the paper's school. QA found a teacher could swap, pick or remove questions
on a colleague's paper, change its status, and download its answer key
before the exam. Now:

  * changing a paper is for its author, the principal, and a teacher holding
    the exams grant;
  * downloading it (paper, Word file or answer key) is for those, plus the
    colleague asked to review it, plus any staff member once the exam has
    been held (colleagues mark the scripts);
  * any other colleague still reads the questions on screen, without the
    answer key.
"""
from __future__ import annotations

from test_paper_swap_pick import _generate, _pick, _swap, seeded  # noqa: F401 (fixture)
from test_homework import w  # noqa: F401 (fixture)
from test_paper_templates import _boot_client


def _join(client, email: str, role: str = "teacher", principal_key=None) -> tuple[dict, str]:
    from _auth_helpers import invite_code

    body = {"name": email.split("@")[0], "email": email, "password": "correct horse battery"}
    if principal_key:
        body.update(schoolId="school_1", principalKey=principal_key)
    else:
        body["inviteCode"] = invite_code("school_1", role)
    r = client.post("/api/v1/auth/register", json=body)
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}, r.json()["user"]["id"]


def _takes(client, headers, pid: str) -> list[int]:
    """The status of each way a paper leaves the system."""
    out = [client.post(f"/api/v1/papers/{pid}/export/{fmt}", headers=headers).status_code
           for fmt in ("pdf", "docx", "answer-key")]
    out.append(client.get(f"/api/v1/papers/{pid}/file", params={"format": "answer-key"},
                          headers=headers).status_code)
    return out


def test_a_colleague_cannot_change_or_take_a_paper_but_reads_its_questions(
        tmp_path, monkeypatch, seeded):
    with _boot_client(tmp_path, monkeypatch) as client:
        ana, _ = _join(client, "ana@example.com")
        bob, _ = _join(client, "bob@example.com")
        paper = _generate(client, ana, setCount=2)
        pid, aid = paper["id"], paper["assessmentId"]
        for code in _takes(client, ana, pid):
            assert code == 200

        for r in (_swap(client, bob, pid, "1"), _pick(client, bob, pid, "1", "o5"),
                  client.delete(f"/api/v1/papers/{pid}/questions/1", headers=bob)):
            assert r.status_code == 403, r.text
            assert "author" in r.json()["detail"]
        asm = client.get(f"/api/v1/assessments/{aid}", headers=ana).json()
        assert client.put(f"/api/v1/assessments/{aid}", json={**asm, "title": "Bob's now"},
                          headers=bob).status_code == 403
        assert client.patch(f"/api/v1/assessments/{aid}/status", json={"status": "draft"},
                            headers=bob).status_code == 403
        assert _takes(client, bob, pid) == [403, 403, 403, 403]
        assert client.post(f"/api/v1/papers/{pid}_set_B/export/answer-key",
                           headers=bob).status_code == 403

        seen = client.get(f"/api/v1/papers/{pid}", headers=bob)
        assert seen.status_code == 200
        body = seen.json()
        assert body["answerKey"] == {} and all(s["answerKey"] == {} for s in body["sets"])
        assert body["sections"] == client.get(f"/api/v1/papers/{pid}", headers=ana).json()["sections"]
        assert client.get(f"/api/v1/papers/{pid}", headers=ana).json()["answerKey"]
        assert client.get(f"/api/v1/papers/{pid}_set_B", headers=bob).json()["answerKey"] == {}

        # Nothing Bob tried changed the paper.
        assert client.get(f"/api/v1/assessments/{aid}", headers=ana).json()["title"] == asm["title"]


def test_the_principal_and_an_exams_admin_may_change_and_take_it(tmp_path, monkeypatch, seeded):
    with _boot_client(tmp_path, monkeypatch) as client:
        ana, _ = _join(client, "ana@example.com")
        cara, cara_id = _join(client, "cara@example.com")
        principal, _ = _join(client, "priya@example.com", principal_key="test-bootstrap-key")
        pid = _generate(client, ana)["id"]

        assert _swap(client, principal, pid, "1").status_code == 200
        assert _takes(client, principal, pid) == [200, 200, 200, 200]

        assert _swap(client, cara, pid, "2").status_code == 403
        grant = client.post("/api/v1/admin/grants", json={"userId": cara_id, "capability": "exams"},
                            headers=principal)
        assert grant.status_code == 200, grant.text
        assert _swap(client, cara, pid, "2").status_code == 200
        assert _takes(client, cara, pid) == [200, 200, 200, 200]


def test_the_named_reviewer_may_take_it_but_not_change_it(tmp_path, monkeypatch, seeded):
    with _boot_client(tmp_path, monkeypatch) as client:
        ana, _ = _join(client, "ana@example.com")
        dev, dev_id = _join(client, "dev@example.com")
        paper = _generate(client, ana)
        pid, aid = paper["id"], paper["assessmentId"]
        assert _takes(client, dev, pid) == [403, 403, 403, 403]

        r = client.post(f"/api/v1/assessments/{aid}/review-request", json={"reviewerId": dev_id},
                        headers=ana)
        assert r.status_code == 200, r.text
        assert _takes(client, dev, pid) == [200, 200, 200, 200]
        assert client.get(f"/api/v1/papers/{pid}", headers=dev).json()["answerKey"]
        assert _swap(client, dev, pid, "1").status_code == 403


def test_once_the_exam_is_held_any_colleague_may_take_the_key(tmp_path, monkeypatch, seeded):
    from academicos.assessment import routes as ar

    with _boot_client(tmp_path, monkeypatch) as client:
        ana, _ = _join(client, "ana@example.com")
        bob, _ = _join(client, "bob@example.com")
        paper = _generate(client, ana)
        pid, aid = paper["id"], paper["assessmentId"]
        assert _takes(client, bob, pid) == [403, 403, 403, 403]

        store = ar._require()[1]
        held = store.get(aid)
        held.status = "conducted"
        store.save(held)
        assert _takes(client, bob, pid) == [200, 200, 200, 200]
        assert client.get(f"/api/v1/papers/{pid}", headers=bob).json()["answerKey"]
        # Taking it is not changing it.
        assert _swap(client, bob, pid, "1").status_code == 403


# ---- the Papers list (P-09, P-16) -------------------------------------------

def test_the_papers_list_holds_what_a_teacher_has_a_reason_to_see(w):
    """Ana teaches Science 10-A and Bala Science 10-B and 9-A (test_homework's
    school). Bala sees Ana's Science 10 paper (he marks 10-B on it), not her
    Mathematics one; Chitra, who teaches neither, sees none of Ana's until
    she is asked to review one; the principal sees all, with authors."""
    from _auth_helpers import register_invited
    from test_assessment_routes_auth import _assessment_body
    from test_homework import _h

    chitra_body = register_invited(w.c, "school_1", "chitra@example.com", name="Chitra")
    chitra, chitra_id = _h(chitra_body), chitra_body["user"]["id"]

    def make(aid, subject):
        r = w.c.post("/api/v1/assessments", json={**_assessment_body(aid), "subject": subject},
                     headers=w.ana)
        assert r.status_code == 200, r.text
        aid = r.json()["id"]
        assert w.c.patch(f"/api/v1/assessments/{aid}/status", json={"status": "paperGenerated"},
                         headers=w.ana).status_code == 200
        return aid

    sci, maths = make("asmt_sci", "Science"), make("asmt_maths", "Mathematics")

    def listed(h):
        return {a["id"]: a for a in w.c.get("/api/v1/assessments", params={"school_id": "school_1"},
                                            headers=h).json()}

    assert set(listed(w.ana)) == {sci, maths}
    assert set(listed(w.bala)) == {sci}
    assert set(listed(chitra)) == set()
    everyone = listed(w.p)
    assert set(everyone) == {sci, maths}
    assert everyone[sci]["metadata"]["authorName"] == "Ana"

    r = w.c.post(f"/api/v1/assessments/{maths}/review-request", json={"reviewerId": chitra_id},
                 headers=w.ana)
    assert r.status_code == 200, r.text
    assert set(listed(chitra)) == {maths}


def test_the_list_shows_the_printed_marks_and_a_rename_keeps_them(tmp_path, monkeypatch, seeded):
    with _boot_client(tmp_path, monkeypatch) as client:
        ana, _ = _join(client, "ana@example.com")
        paper = _generate(client, ana)
        pid, aid = paper["id"], paper["assessmentId"]

        def row():
            [a] = [a for a in client.get("/api/v1/assessments", params={"school_id": "school_1"},
                                         headers=ana).json() if a["id"] == aid]
            return a

        assert row()["metadata"]["paperMarks"] == 8 and row()["metadata"]["authorName"] == "ana"
        r = client.delete(f"/api/v1/papers/{pid}/questions/1", headers=ana)
        assert r.status_code == 200, r.text
        listed = row()
        assert listed["metadata"]["paperMarks"] == 7 and listed["blueprint"]["totalMarks"] == 8

        # A rename sends back what the client listed; a stale or invented
        # printed total must not overwrite the server's, nor the name be stored.
        renamed = client.put(f"/api/v1/assessments/{aid}", headers=ana, json={
            **listed, "title": "Unit test 2",
            "metadata": {**listed["metadata"], "paperMarks": 99}})
        assert renamed.status_code == 200, renamed.text
        assert row()["title"] == "Unit test 2" and row()["metadata"]["paperMarks"] == 7
        stored = client.get(f"/api/v1/assessments/{aid}", headers=ana).json()["metadata"]
        assert "authorName" not in stored and stored["paperMarks"] == 7
