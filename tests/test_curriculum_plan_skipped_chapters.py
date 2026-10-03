"""A plan names every chapter it leaves out for want of subtopics, and does
not call itself complete (audit D119).

Before: schedule_book walked units -> chapters -> topics -> subtopics, so a
chapter with no approved subtopic contributed nothing and was never
mentioned. A Science 6 plan put the whole year into 5 of its 12 chapters and
still answered `allSubtopicsScheduled: true`.
"""
from __future__ import annotations

from datetime import date

from academicos.curriculum import calendar as calendar_mod
from academicos.curriculum import scheduling

from test_section_plans import store  # noqa: F401  (fixture)


def _book_with_gaps(store):
    board = store.create_board(name="CBSE", code="CBSE")
    year = store.create_academic_year(school_id="school_1", label="2026-27",
                                      start_date="2026-06-01", end_date="2027-03-31")
    grade = store.create_grade(academic_year_id=year.id, number=6)
    subject = store.create_subject(grade_id=grade.id, name="Science")
    book = store.create_book(subject_id=subject.id, board_id=board.id, title="Curiosity")
    unit = store.create_unit(canonical_id="u:1", book_id=book.id, unit_no="1", name="Science chapters",
                             marks=80, seq=0)
    taught = store.create_chapter(canonical_id="c:1", unit_id=unit.id, name="Diversity in the Living World", seq=0)
    topic = store.create_topic(canonical_id="t:1", chapter_id=taught.id, name="Grouping", seq=0)
    for s in range(3):
        store.create_subtopic(canonical_id=f"st:{s}", topic_id=topic.id, name=f"Subtopic {s}", seq=s)
    store.create_chapter(canonical_id="c:2", unit_id=unit.id, name="The Wonderful World of Science", seq=1)
    bare = store.create_chapter(canonical_id="c:3", unit_id=unit.id, name="Exploring Magnets", seq=2)
    store.create_topic(canonical_id="t:3", chapter_id=bare.id, name="Magnetic poles", seq=0)
    store.create_calendar(academic_year_id=year.id, weekly_off_days=["sunday"], alternate_saturday_rule="none")
    store.create_period_configuration(school_id="school_1", academic_year_id=year.id, period_minutes=40)
    calendar_mod.compute_teaching_time_estimates(store, academic_year_id=year.id, book_id=book.id,
                                                 periods_per_week=6)
    return year.id, book.id


def test_a_plan_names_the_chapters_it_leaves_out(store):
    year, book = _book_with_gaps(store)
    r = scheduling.schedule_book(store, school_id="school_1", academic_year_id=year, book_id=book,
                                 periods_per_week=6, from_date="2026-06-01")
    assert r.lessons_created > 0 and not r.subtopics_unscheduled and not r.subtopics_without_estimate
    assert r.chapters_without_subtopics == ("The Wonderful World of Science", "Exploring Magnets")
    assert r.all_subtopics_scheduled is False, "two of three chapters are not in the plan"
    assert "2 of 3 chapters have no approved subtopics" in r.warning
    assert "Exploring Magnets" in r.warning


def test_the_routes_report_the_left_out_chapters(tmp_path, monkeypatch):
    """Science 6 as a school seeds it: 12 chapters, and the proposed topics
    give subtopics to only some of them."""
    from test_assessment_routes_auth import _boot_client, _register
    from test_web_school_setup import BASE, PRINCIPAL_KEY

    from academicos.curriculum import routes as curriculum_routes

    with _boot_client(tmp_path, monkeypatch) as client:
        monkeypatch.setattr(curriculum_routes, "_school_today", lambda: date(2026, 6, 1))
        principal = _register(client, "school_1", "head@school1.test", "Head", principal_key=PRINCIPAL_KEY)
        auth = {"Authorization": f"Bearer {principal['token']}"}
        assert client.post(f"{BASE}/seed/cbse", headers=auth, json={
            "grade": 6, "academicYearLabel": "2026-27", "startDate": "2026-04-01",
            "endDate": "2027-03-31"}).status_code == 200
        year = client.get(f"{BASE}/academic-years", params={"school_id": "school_1"}, headers=auth).json()[0]["id"]
        client.post(f"{BASE}/academic-years/{year}/calendar", headers=auth,
                    json={"weeklyOffDays": ["sunday"], "alternateSaturdayRule": "none"})
        client.post(f"{BASE}/academic-years/{year}/bell-schedules", headers=auth,
                    json={"name": "Main", "slots": [{"start": f"{8 + i:02d}:00", "end": f"{8 + i:02d}:45"}
                                                    for i in range(7)]})
        grade = client.get(f"{BASE}/academic-years/{year}/grades", headers=auth).json()[0]["id"]
        section = client.get(f"{BASE}/academic-years/{year}/sections", headers=auth).json()[0]["id"]
        science = next(s["id"] for s in client.get(f"{BASE}/grades/{grade}/subjects", headers=auth).json()
                       if s["name"] == "Science")
        assert client.put(f"{BASE}/sections/{section}/allocations/{science}", headers=auth,
                          json={"teacherId": principal["user"]["id"], "periodsPerWeek": 6}).status_code == 200

        built = client.post(f"{BASE}/academic-years/{year}/lesson-plans", headers=auth,
                            json={"approveProposedTopics": True})
        assert built.status_code == 200, built.text
        [plan] = built.json()["plans"]
        left_out = plan["chaptersWithoutSubtopics"]
        assert left_out and plan["lessonsCreated"] > 0
        assert "chapters have no approved subtopics" in plan["warning"]

        book = client.get(f"{BASE}/subjects/{science}/selected-book", headers=auth).json()["id"]
        chapters = client.get(f"{BASE}/books/{book}/chapters", headers=auth).json()
        dated = {c["name"] for c in chapters} - set(left_out)
        assert len(dated) + len(left_out) == len(chapters) == 12

        again = client.post(f"{BASE}/books/{book}/schedule", params={"academic_year_id": year}, headers=auth,
                            json={"sectionId": section, "force": True})
        assert again.status_code == 200, again.text
        assert again.json()["allSubtopicsScheduled"] is False
        assert again.json()["chaptersWithoutSubtopics"] == left_out
