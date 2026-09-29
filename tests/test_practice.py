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
