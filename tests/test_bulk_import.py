"""Bulk import and export (M1.6): a dry run shows every row's outcome and
writes nothing, an apply with an error row is refused whole, and imported
people join through invites that enrol and link them when they register."""
from __future__ import annotations

from test_homework import w  # noqa: F401 - `w` is a fixture

PASSWORD = "correct horse battery"


def _imp(w, kind, text, dry=True, who=None):
    return w.c.post(f"/api/v1/admin/import/{kind}", params={"dryRun": str(dry).lower()},
                    json={"csv": text, "academicYearId": w.year}, headers=who or w.p)


def _join(w, code, email, name="New Person"):
    r = w.c.post("/api/v1/auth/register", json={"inviteCode": code, "name": name, "email": email,
                                                "password": PASSWORD})
    assert r.status_code == 200, r.text
    return r.json()


def test_sections_dry_run_then_apply(w):
    text = "Grade,Section,Class teacher email\n10,B,\n10,C,ana@example.com\n11,A,\n13,A,\n10,c,\n"
    out = _imp(w, "sections", text).json()
    assert [(r["row"], r["status"]) for r in out["rows"]] == [(2, "skip"), (3, "ok"), (4, "ok"), (5, "error"),
                                                              (6, "skip")]
    assert "class teacher Ana" in out["rows"][1]["message"] and out["applied"] is False
    assert {g.number for g in w.store.grades_for_year(w.year)} == {9, 10}, "a dry run writes nothing"
    refused = _imp(w, "sections", text, dry=False)
    assert refused.status_code == 422 and refused.json()["detail"]["rows"][0]["row"] == 5
    ok = _imp(w, "sections", text.replace("13,A,\n", ""), dry=False).json()
    assert ok["applied"] and ok["counts"] == {"ok": 2, "skip": 2, "error": 0}
    grades = {g.number: g for g in w.store.grades_for_year(w.year)}
    assert {s.name for s in w.store.sections_for_grade(grades[10].id)} == {"A", "B", "C"}
    assert 11 in grades
    again = _imp(w, "sections", "grade,section\n10,C\n").json()
    assert again["rows"][0]["status"] == "skip", "an applied file imports again as all skipped"


def test_teachers_become_invites(w):
    out = _imp(w, "teachers", "name,email\nAna,ana@example.com\nNew Teacher,new.t@example.com\nx,not-an-email\n")
    assert [r["status"] for r in out.json()["rows"]] == ["skip", "ok", "error"]
    done = _imp(w, "teachers", "name,email\nNew Teacher,new.t@example.com\n", dry=False).json()
    code = done["rows"][0]["inviteCode"]
    assert code and _join(w, code, "new.t@example.com")["user"]["role"] == "teacher"


def test_students_are_enrolled_and_parents_linked_when_they_join(w):
    out = _imp(w, "students", "name,email,grade,section\nNina,nina@example.com,10,B\nAsha,s1@example.com,10,B\n"
                              "Zed,zed@example.com,10,Z\n").json()
    assert [r["status"] for r in out["rows"]] == ["ok", "ok", "error"]
    assert out["rows"][1]["message"].startswith("move Asha into 10-B")
    done = _imp(w, "students", "name,email,grade,section\nNina,nina@example.com,10,B\n", dry=False).json()
    student_code = done["rows"][0]["inviteCode"]

    parents = _imp(w, "parents", "name,email,student_email,relation\nRaj,raj@example.com,nina@example.com,father\n"
                                 "X,x@example.com,nobody@example.com,father\n").json()
    assert [r["status"] for r in parents["rows"]] == ["ok", "error"]
    done = _imp(w, "parents", "name,email,student_email,relation\nRaj,raj@example.com,nina@example.com,father\n",
                dry=False).json()
    raj = _join(w, done["rows"][0]["inviteCode"], "raj@example.com", "Raj")
    h = {"Authorization": f"Bearer {raj['token']}"}
    assert w.c.get("/api/v1/my-children", headers=h).json() == [], "Nina has not joined yet"
    nina = _join(w, student_code, "nina@example.com", "Nina")
    e = w.store.enrollment_for_student(nina["user"]["id"])
    assert e is not None and e.section_id == w.b10
    [child] = w.c.get("/api/v1/my-children", headers=h).json()
    assert child["name"] == "Nina" and child["relation"] == "father" and child["sectionName"] == "10-B"


def test_allocations_and_holidays(w):
    out = _imp(w, "allocations", "grade,section,subject,teacher_email,periods_per_week\n"
                                 "10,A,Science,bala@example.com,5\n10,A,History,bala@example.com,5\n"
                                 "10,B,Science,bala@example.com,6\n").json()
    assert [r["status"] for r in out["rows"]] == ["ok", "error", "skip"]
    _imp(w, "allocations", "grade,section,subject,teacher_email,periods_per_week\n10,A,science,bala@example.com,5\n",
         dry=False)
    a = w.store.allocation_for(w.a10, w.sci10)
    assert a.periods_per_week == 5 and a.teacher_id != w.ids["s1"]

    assert _imp(w, "holidays", "date,name\n2026-10-20,Diwali\n").json()["rows"][0]["status"] == "error"
    w.store.create_calendar(academic_year_id=w.year, weekly_off_days=["sunday"], alternate_saturday_rule="none")
    text = "date,end_date,name,kind\n2026-10-20,2026-10-24,Diwali break,holiday\n2027-06-01,,Too late,holiday\n"
    assert [r["status"] for r in _imp(w, "holidays", text).json()["rows"]] == ["ok", "error"]
    _imp(w, "holidays", "date,end_date,name,kind\n2026-10-20,2026-10-24,Diwali break,holiday\n", dry=False)
    csv_out = w.c.get("/api/v1/admin/export/holidays", params={"academicYearId": w.year}, headers=w.p).text
    assert "2026-10-20,2026-10-24,Diwali break,holiday" in csv_out


def test_templates_exports_and_who_may(w):
    t = w.c.get("/api/v1/admin/import/students/template", headers=w.p)
    assert t.status_code == 200 and t.text.splitlines()[0] == "name,email,grade,section"
    sections = w.c.get("/api/v1/admin/export/sections", params={"academicYearId": w.year}, headers=w.p).text
    assert "10,B," in sections and sections.splitlines()[0] == "grade,section,class_teacher_email"
    people = w.c.get("/api/v1/admin/export/people", headers=w.p).text
    assert "Asha,s1@example.com,student,10,A" in people
    assert w.c.get("/api/v1/admin/export/timetable", headers=w.p).status_code == 200
    assert _imp(w, "sections", "grade,section\n10,D\n", who=w.ana).status_code == 403
    assert _imp(w, "widgets", "a\n1\n").status_code == 404
    assert _imp(w, "students", "name,email\nA,a@example.com\n").status_code == 422      # grade, section missing
    assert w.c.post("/api/v1/admin/import/sections", json={"csv": "grade,section\n10,D\n", "academicYearId": w.year},
                    headers=w.p2).status_code == 403
