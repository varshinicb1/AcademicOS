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


def test_the_week_names_its_periods(w):
    week = w.c.get(f"{BASE}/my-timetable", headers=w.stu).json()
    assert {(e["period"], e["subjectName"], e["sectionName"]) for e in week["entries"]} == {(1, "Maths", "10-B"),
                                                                                           (2, "Science", "10-B")}


def test_calendar_feed_times_follow_the_bell_past_a_break(w):
    """A bell's slots include breaks: period 2 is the second teaching slot,
    not the second slot."""
    bell = w.store.create_bell_schedule(academic_year_id=w.year, name="With break", slots=[
        {"start": "08:00", "end": "08:45"}, {"start": "08:45", "end": "09:05", "kind": "break"},
        {"start": "09:05", "end": "09:50"}])
    w.store.set_section_bell(w.b10, bell.id)
    url = w.c.get("/api/v1/calendar-feed", headers=w.stu).json()["url"]
    ics = w.c.get("/api/v1/ics/" + url.rsplit("/ics/", 1)[1]).text
    unfolded = ics.replace("\r\n ", "")
    assert "SUMMARY:Science" in unfolded and "T090500" in unfolded, "period 2 starts after the break"
    assert "T084500" not in unfolded.split("SUMMARY:Science")[1].split("END:VEVENT")[0]
