"""Curriculum hierarchy reads are authenticated and scoped to the caller's
school -- docs/PRD.md section 10's hard constraint, "every query scoped by
`school_id`; role gates enforced".

Until 2026-09-21 the hierarchy reads in curriculum/routes.py (academic years
-> grades -> subjects -> books -> units/chapters -> topics with their
subtopics) had no auth dependency at all. A module comment justified it as
"public official-curriculum content", but the rows are not public: seed_cbse10
creates every year/grade/subject/book/unit/chapter per school, and topics and
subtopics are a school's own admin-approved decomposition (extraction.py:
AI DRAFT -> ADMIN REVIEW -> DATABASE). The product audit measured the leak
twice: a school_2 principal got 200 on school_1's approved topics, and
`GET /academic-years?school_id=school_1` answered with no token at all.

These tests pin the boundary the file's writes already had -- 401 with no
token, 403 for another school's row, 404 for an id that doesn't exist -- and
that the owning school's principal, an assigned teacher and an enrolled-school
student still read their own rows.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from test_assessment_routes_auth import _boot_client, _register

BASE = "/api/v1/curriculum"
QUESTION_SEARCH = "/api/v1/questions/search"
PRINCIPAL_KEY = "test-bootstrap-key"


def _search_body(subtopic_ids: list[str]) -> dict:
    """The body assessment_create_page.dart sends when a teacher narrows
    question search to picked subtopics (QuestionSearchParams.subtopicIds)."""
    return {"subject": "Science", "grade": 10, "subtopicIds": subtopic_ids}


def _bearer(user: dict) -> dict:
    return {"Authorization": f"Bearer {user['token']}"}


def _seed_tree(client, auth: dict, label: str) -> SimpleNamespace:
    """One school's real hierarchy: the CBSE Class 10 seed (year -> grade ->
    5 subjects -> books -> units -> chapters) plus one manually-added topic
    and subtopic under the Science book's first chapter. Ids below the grade
    are read straight from the store, not through the routes under test, so
    a broken read can't also break the fixture that is meant to catch it."""
    from academicos.curriculum import routes as curriculum_routes

    seeded = client.post(f"{BASE}/seed/cbse10", json={
        "academicYearLabel": "2026-27", "startDate": "2026-06-01", "endDate": "2027-03-31",
    }, headers=auth)
    assert seeded.status_code == 200, seeded.text
    body = seeded.json()

    store = curriculum_routes._require()
    science = next(s for s in store.subjects_for_grade(body["gradeId"]) if s.name == "Science")
    book = store.books_for_subject(science.id)[0]
    unit = store.units_for_book(book.id)[0]
    chapter = store.chapters_for_book(book.id)[0]

    topic = client.post(f"{BASE}/chapters/{chapter.id}/topics",
                        json={"name": f"{label} topic"}, headers=auth)
    assert topic.status_code == 200, topic.text
    subtopic = client.post(f"{BASE}/topics/{topic.json()['id']}/subtopics",
                           json={"name": f"{label} subtopic"}, headers=auth)
    assert subtopic.status_code == 200, subtopic.text

    return SimpleNamespace(
        year=body["academicYearId"], grade=body["gradeId"], subject=science.id,
        book=book.id, unit=unit.id, chapter=chapter.id,
        topic=topic.json()["id"], subtopic=subtopic.json()["id"],
        subject_ids={s.id for s in store.subjects_for_grade(body["gradeId"])},
        unit_ids=[u.id for u in store.units_for_book(book.id)],
        chapter_ids=[c.id for c in store.chapters_for_book(book.id)],
    )


def _keyed_reads(t: SimpleNamespace) -> list[tuple[str, str]]:
    """Every hierarchy read keyed by a school-owned row, labelled by the row
    whose ownership decides it. There is no read keyed by a unit or topic id:
    a book's units come from /books/{id}/units, and a chapter's topics (with
    their subtopics nested) from /chapters/{id}/topics."""
    return [
        ("academic year", f"{BASE}/academic-years/{t.year}/grades"),
        ("grade", f"{BASE}/grades/{t.grade}/subjects"),
        ("subject", f"{BASE}/subjects/{t.subject}/books"),
        ("book (units)", f"{BASE}/books/{t.book}/units"),
        ("book (chapters)", f"{BASE}/books/{t.book}/chapters"),
        ("chapter (topics + subtopics)", f"{BASE}/chapters/{t.chapter}/topics"),
    ]


@pytest.fixture
def world(tmp_path, monkeypatch):
    with _boot_client(tmp_path, monkeypatch) as client:
        p1 = _register(client, "school_1", "p1@example.com", "Priya Principal",
                       principal_key=PRINCIPAL_KEY)
        p2 = _register(client, "school_2", "p2@example.com", "Ravi Principal",
                       principal_key=PRINCIPAL_KEY)
        assert p1["user"]["role"] == p2["user"]["role"] == "principal"
        teacher = _register(client, "school_1", "t1@example.com", "Ana Teacher")
        student = client.post("/api/v1/auth/register", json={
            "schoolId": "school_1", "name": "Sam Student", "email": "s1@example.com",
            "password": "correct horse battery", "role": "student",
        })
        assert student.status_code == 200, student.text

        s1 = _seed_tree(client, _bearer(p1), "School one")
        s2 = _seed_tree(client, _bearer(p2), "School two")

        assigned = client.post(f"{BASE}/teacher-assignments", json={
            "teacherId": teacher["user"]["id"], "bookId": s1.book,
        }, headers=_bearer(p1))
        assert assigned.status_code == 200, assigned.text

        yield SimpleNamespace(
            client=client, s1=s1, s2=s2,
            p1=_bearer(p1), p2=_bearer(p2), teacher=_bearer(teacher),
            student=_bearer(student.json()),
        )


def test_every_curriculum_read_needs_a_token(world):
    """No token -> 401 on every read, including /boards and the
    school_id-query /academic-years the audit reached anonymously."""
    reads = [("boards", f"{BASE}/boards", None),
             ("academic years", f"{BASE}/academic-years", {"school_id": "school_1"})]
    reads += [(label, path, None) for label, path in _keyed_reads(world.s1)]

    failures = []
    for label, path, params in reads:
        r = world.client.get(path, params=params)
        if r.status_code != 401:
            failures.append(f"{label}: GET {path} -> {r.status_code}")
    r = world.client.post(f"{BASE}/questions/by-subtopics", json={"subtopicIds": [world.s1.subtopic]})
    if r.status_code != 401:
        failures.append(f"subtopic: POST questions/by-subtopics -> {r.status_code}")
    r = world.client.post(QUESTION_SEARCH, json=_search_body([world.s1.subtopic]))
    if r.status_code != 401:
        failures.append(f"subtopic: POST {QUESTION_SEARCH} -> {r.status_code}")
    assert not failures, "anonymous curriculum reads:\n" + "\n".join(failures)


def test_another_schools_principal_is_refused_every_row(world):
    """school_2's principal, holding a valid token, gets 403 on each of
    school_1's rows -- the same 403 the file's writes return for a
    cross-school id -- and never the rows themselves."""
    failures = []
    for label, path in _keyed_reads(world.s1):
        r = world.client.get(path, headers=world.p2)
        if r.status_code != 403:
            failures.append(f"{label}: GET {path} -> {r.status_code} {r.text[:120]}")
    r = world.client.post(f"{BASE}/questions/by-subtopics",
                          json={"subtopicIds": [world.s1.subtopic]}, headers=world.p2)
    if r.status_code != 403:
        failures.append(f"subtopic: POST questions/by-subtopics -> {r.status_code}")
    # The subtopic filter the web client actually sends (by-subtopics has no
    # caller in frontend/lib). A foreign id is refused even mixed in with the
    # caller's own, not silently dropped from the filter.
    for ids in ([world.s1.subtopic], [world.s2.subtopic, world.s1.subtopic]):
        r = world.client.post(QUESTION_SEARCH, json=_search_body(ids), headers=world.p2)
        if r.status_code != 403:
            failures.append(f"subtopic: POST {QUESTION_SEARCH} {ids} -> {r.status_code}")
    assert not failures, "cross-school curriculum reads not refused:\n" + "\n".join(failures)

    # school_1's approved topic name must not come back in any form.
    leaked = world.client.get(f"{BASE}/chapters/{world.s1.chapter}/topics", headers=world.p2)
    assert "School one topic" not in leaked.text


def test_academic_years_school_id_cannot_name_another_school(world):
    """The query parameter is checked against the caller's own school, not
    trusted: school_2 asking for school_1's years is refused, and asking for
    its own returns only its own."""
    theirs = world.client.get(f"{BASE}/academic-years", params={"school_id": "school_1"},
                              headers=world.p2)
    assert theirs.status_code == 403
    assert world.s1.year not in theirs.text

    own = world.client.get(f"{BASE}/academic-years", params={"school_id": "school_2"},
                           headers=world.p2)
    assert own.status_code == 200
    assert [y["id"] for y in own.json()] == [world.s2.year]


def test_own_school_principal_teacher_and_student_read_their_rows(world):
    """The gate must not lock out the people the data belongs to: school_1's
    principal and its assigned teacher read every level with the right rows,
    and a school_1 student can still look up the school's academic years (the
    student progress view's first call, curriculum_api.dart::academicYears)."""
    c, s1 = world.client, world.s1
    for who, auth in (("principal", world.p1), ("assigned teacher", world.teacher)):
        years = c.get(f"{BASE}/academic-years", params={"school_id": "school_1"}, headers=auth)
        assert years.status_code == 200, f"{who}: {years.text}"
        assert [y["id"] for y in years.json()] == [s1.year]

        grades = c.get(f"{BASE}/academic-years/{s1.year}/grades", headers=auth)
        assert grades.status_code == 200, f"{who}: {grades.text}"
        assert [g["id"] for g in grades.json()] == [s1.grade]

        subjects = c.get(f"{BASE}/grades/{s1.grade}/subjects", headers=auth)
        assert subjects.status_code == 200, f"{who}: {subjects.text}"
        assert {s["id"] for s in subjects.json()} == s1.subject_ids

        books = c.get(f"{BASE}/subjects/{s1.subject}/books", headers=auth)
        assert books.status_code == 200, f"{who}: {books.text}"
        assert [b["id"] for b in books.json()] == [s1.book]

        units = c.get(f"{BASE}/books/{s1.book}/units", headers=auth)
        assert units.status_code == 200, f"{who}: {units.text}"
        assert [u["id"] for u in units.json()] == s1.unit_ids

        chapters = c.get(f"{BASE}/books/{s1.book}/chapters", headers=auth)
        assert chapters.status_code == 200, f"{who}: {chapters.text}"
        assert [ch["id"] for ch in chapters.json()] == s1.chapter_ids

        topics = c.get(f"{BASE}/chapters/{s1.chapter}/topics", headers=auth)
        assert topics.status_code == 200, f"{who}: {topics.text}"
        assert [t["id"] for t in topics.json()] == [s1.topic]
        assert [st["id"] for st in topics.json()[0]["subtopics"]] == [s1.subtopic]

        by_subtopic = c.post(f"{BASE}/questions/by-subtopics",
                             json={"subtopicIds": [s1.subtopic]}, headers=auth)
        assert by_subtopic.status_code == 200, f"{who}: {by_subtopic.text}"

        # An id that resolves to no school (force-deleted since the picker
        # loaded) is ignored next to the caller's own, not a 403.
        searched = c.post(QUESTION_SEARCH, json=_search_body([s1.subtopic, "st_deleted"]),
                          headers=auth)
        assert searched.status_code == 200, f"{who}: {searched.text}"

    student_years = c.get(f"{BASE}/academic-years", params={"school_id": "school_1"},
                          headers=world.student)
    assert student_years.status_code == 200, student_years.text
    assert [y["id"] for y in student_years.json()] == [s1.year]


def test_unknown_ids_are_404_like_the_write_routes(world):
    """An id that resolves to no school is a 404 -- the same answer the
    file's writes give (_require_school_owns_*) -- rather than the old
    silent 200 [] that could not be told apart from an empty-but-real row."""
    missing = SimpleNamespace(year="year_missing", grade="grade_missing",
                              subject="subj_missing", book="book_missing",
                              chapter="chap_missing")
    failures = []
    for label, path in _keyed_reads(missing):
        r = world.client.get(path, headers=world.p1)
        if r.status_code != 404:
            failures.append(f"{label}: GET {path} -> {r.status_code}")
    assert not failures, "unknown ids not 404:\n" + "\n".join(failures)


def test_boards_are_shared_reference_data_for_any_signed_in_user(world):
    """Boards are the one global table (no school_id column; CBSE is not any
    one school's row -- the export route omits them for the same reason), so
    any authenticated caller from any school reads the same list."""
    for auth in (world.p1, world.p2, world.teacher, world.student):
        r = world.client.get(f"{BASE}/boards", headers=auth)
        assert r.status_code == 200, r.text
        assert any(b["code"] == "CBSE" for b in r.json())
