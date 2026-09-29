"""The day as it runs carries subject, section and teacher names, so a
student, a parent or a teacher reads "10-B Maths" without a second call."""
from __future__ import annotations

from test_cover_routes import BASE, MON, w  # noqa: F401 - `w` is a fixture


def test_a_students_day_names_its_periods(w):
    rows = w.c.get(f"{BASE}/my-day", params={"date": MON}, headers=w.stu).json()
    assert [(r["period"], r["subjectName"], r["sectionName"]) for r in rows] == [(1, "Maths", "10-B"),
                                                                                  (2, "Science", "10-B")]
    assert all(r["teacherName"] for r in rows)


def test_a_teachers_day_names_its_sections(w):
    rows = w.c.get(f"{BASE}/my-day", params={"date": MON}, headers=w.t["ana"]).json()
    assert {(r["sectionName"], r["subjectName"]) for r in rows} == {("10-A", "Science"), ("10-B", "Science")}
