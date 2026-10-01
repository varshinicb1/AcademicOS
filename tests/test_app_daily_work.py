"""Homework and marks as the teacher and student apps use them (v3 audit,
areas 4 and 5). These defects were found:

  * N-4-5: one student without parental consent refused a whole section's
    paper marks, naming an internal id.
  * N-5-1: a student was shown the staff wording ("record it under Classes").
  * TA-7: a teacher had no notice that homework was being handed in.
"""
from __future__ import annotations

from test_homework import _create, w  # noqa: F401 - `w` is a fixture
from test_marks_entry import _cell, _put, paper  # noqa: F401 - `paper` is a fixture


def _revoke(student_id):
    from academicos.assessment import consent_routes
    consent_routes._require_store().revoke_consent(school_id="school_1", student_id=student_id,
                                                   revoked_by="test-fixture")


def test_marks_save_for_the_consented_and_name_the_rest(w, paper):  # noqa: F811
    _revoke(w.ids["s2"])
    r = _put(w, paper, {"entries": [_cell(w, "s1", "q1", 1), _cell(w, "s2", "q1", 1)]})
    assert r.status_code == 200, r.text
    grid = r.json()
    assert grid["withoutConsent"] == ["Bhavna"], "named, not an internal id"
    rows = {x["studentId"]: x for x in grid["rows"]}
    assert rows[w.ids["s1"]]["total"] == 1 and rows[w.ids["s2"]]["total"] is None
    # Only students without consent: still refused, by name.
    only = _put(w, paper, {"entries": [_cell(w, "s2", "q1", 1)]})
    assert only.status_code == 409 and "Bhavna" in only.json()["detail"] and "user_" not in only.json()["detail"]


def test_a_student_without_consent_reads_their_own_wording(w):
    hw = _create(w, "ana").json()
    _revoke(w.ids["s1"])
    r = w.c.post(f"/api/v1/my-homework/{hw['id']}/submit", json={"answers": {"q1": "A"}}, headers=w.s1)
    assert r.status_code == 409
    detail = r.json()["detail"]
    assert "parent's consent" in detail and "Classes" not in detail and "user_" not in detail


def test_the_teacher_hears_homework_is_coming_in(w):
    hw = _create(w, "ana").json()
    ana = w.c.get("/api/v1/auth/me", headers=w.ana).json()["id"]
    for who in (w.s1, w.s2):
        assert w.c.post(f"/api/v1/my-homework/{hw['id']}/submit", json={"answers": {"q1": "A"}},
                        headers=who).status_code == 200
    items = [i for i in w.c.get("/api/v1/notifications", headers=w.ana).json()["items"]
             if i["kind"] == "homework_submitted"]
    assert len(items) == 1, "once a day per homework, not once per student"
    assert "Asha handed in Light practice (1 of 2 so far)" in items[0]["body"]
    assert items[0]["link"] == f"/homework/{hw['id']}"
    assert ana


def test_a_student_and_their_parent_hear_a_tests_marks_once(w, paper):  # noqa: F811
    assert _put(w, paper, {"entries": [_cell(w, "s1", "q1", 1), _cell(w, "s1", "q3", 2)]}).status_code == 200
    assert _put(w, paper, {"entries": [_cell(w, "s1", "q2", 1)]}).status_code == 200
    told = [i for i in w.c.get("/api/v1/notifications", headers=w.s1).json()["items"] if i["kind"] == "test_marks"]
    assert len(told) == 1, "once per paper, not on every save"
    assert told[0]["title"] == "Marks: Light test" and "3 out of 4" in told[0]["body"]
    assert told[0]["link"] == "/my-learning"
