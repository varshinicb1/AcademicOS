"""A school chooses its book edition: one per subject per academic year.

PRD 12.7 (decided 2026-09-18): "Book edition: one per subject per year,
chosen by the school." The 2026-09-21 audit scored it 0: create_book was
called only by seed_cbse10, there was no route to add or choose a book,
books_for_subject enforced nothing, and the web admin silently used
books.first.id -- a second book on a subject would have been ignored or
picked at random, depending on SQLite's row order.

The rule lives in the store (a primary key on (academic_year_id,
subject_id)), not only the route. A subject with exactly one book -- every
seeded subject today -- treats it as selected, so nothing already working
breaks. Choosing a new edition never re-points lessons already scheduled
from the old one; the response says how many there are instead.

These run through the real HTTP routes as authenticated users.
"""
from __future__ import annotations

import sqlite3
from types import SimpleNamespace

import pytest

from test_assessment_routes_auth import _boot_client, _register

BASE = "/api/v1/curriculum"
PRINCIPAL_KEY = "test-bootstrap-key"


def _bearer(user: dict) -> dict:
    return {"Authorization": f"Bearer {user['token']}"}


@pytest.fixture
def world(tmp_path, monkeypatch):
    with _boot_client(tmp_path, monkeypatch) as client:
        p1 = _register(client, "school_1", "p1@example.com", "Priya Principal",
                       principal_key=PRINCIPAL_KEY)
        p2 = _register(client, "school_2", "p2@example.com", "Ravi Principal",
                       principal_key=PRINCIPAL_KEY)
        teacher = _register(client, "school_1", "t1@example.com", "Ana Teacher")
        assert p1["user"]["role"] == p2["user"]["role"] == "principal"
        assert teacher["user"]["role"] == "teacher"
        from academicos.curriculum import routes as curriculum_routes
        store = curriculum_routes._require()
        board = store.create_board(name="CBSE", code="CBSE")
        year = store.create_academic_year(school_id="school_1", label="2026-27",
                                          start_date="2026-04-01", end_date="2027-03-31")
        grade = store.create_grade(academic_year_id=year.id, number=10)
        subject = store.create_subject(grade_id=grade.id, name="Mathematics")
        # Exactly what seed_cbse10 creates for every seeded subject today.
        seeded = store.create_book(subject_id=subject.id, board_id=board.id,
                                   title="CBSE Class 10 Mathematics — official curriculum (NCERT)",
                                   status="ready")
        yield SimpleNamespace(client=client, store=store, board=board.id, year=year.id,
                              subject=subject.id, seeded=seeded.id,
                              p1=_bearer(p1), p2=_bearer(p2), teacher=_bearer(teacher))


def _add_book(w, auth=None, **overrides):
    body = {"title": "Mathematics Part I", "publisher": "RD Sharma, 2026 edition",
            "boardId": w.board}
    body.update(overrides)
    return w.client.post(f"{BASE}/subjects/{w.subject}/books", json=body, headers=auth or w.p1)


def _select(w, book_id: str, auth=None):
    return w.client.put(f"{BASE}/subjects/{w.subject}/selected-book", json={"bookId": book_id},
                        headers=auth or w.p1)


def _selected(w, auth=None):
    return w.client.get(f"{BASE}/subjects/{w.subject}/selected-book", headers=auth or w.p1)


# --------------------------------------------------------------------- #
# Existing data keeps working
# --------------------------------------------------------------------- #

def test_a_subject_with_one_seeded_book_reports_it_as_selected(world):
    r = _selected(world)
    assert r.status_code == 200, r.text
    assert r.json()["id"] == world.seeded and r.json()["selected"] is True
    listed = world.client.get(f"{BASE}/subjects/{world.subject}/books", headers=world.p1).json()
    assert [(b["id"], b["selected"]) for b in listed] == [(world.seeded, True)]


def test_a_teacher_of_the_school_can_read_the_selected_book(world):
    r = _selected(world, auth=world.teacher)
    assert r.status_code == 200 and r.json()["id"] == world.seeded


def test_another_school_cannot_read_the_selected_book(world):
    assert _selected(world, auth=world.p2).status_code == 403


# --------------------------------------------------------------------- #
# Adding a second book
# --------------------------------------------------------------------- #

def test_a_principal_adds_a_second_book_and_the_seeded_one_stays_selected(world):
    r = _add_book(world)
    assert r.status_code == 200, r.text
    added = r.json()
    assert added["title"] == "Mathematics Part I"
    assert added["publisher"] == "RD Sharma, 2026 edition"
    assert added["boardId"] == world.board and added["subjectId"] == world.subject
    assert added["selected"] is False, "adding a book is not choosing it"
    # Two books and no explicit choice used to mean "whichever row came
    # first"; the one book the subject was already using stays the edition.
    assert _selected(world).json()["id"] == world.seeded
    listed = world.client.get(f"{BASE}/subjects/{world.subject}/books", headers=world.p1).json()
    assert {b["id"]: b["selected"] for b in listed} == {world.seeded: True, added["id"]: False}


def test_adding_a_book_needs_a_title_and_a_real_board(world):
    assert _add_book(world, title="  ").status_code == 422
    assert _add_book(world, boardId="board_missing").status_code == 422
    assert len(world.store.books_for_subject(world.subject)) == 1


def test_a_teacher_cannot_add_a_book(world):
    assert _add_book(world, auth=world.teacher).status_code == 403
    assert len(world.store.books_for_subject(world.subject)) == 1


def test_another_school_cannot_add_a_book(world):
    assert _add_book(world, auth=world.p2).status_code == 403
    assert len(world.store.books_for_subject(world.subject)) == 1


# --------------------------------------------------------------------- #
# Selecting
# --------------------------------------------------------------------- #

def test_selecting_the_second_book_makes_it_the_edition(world):
    added = _add_book(world).json()
    r = _select(world, added["id"])
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["book"]["id"] == added["id"] and body["book"]["selected"] is True
    assert body["previousBookId"] == world.seeded
    assert body["previousBookScheduledLessons"] == 0
    assert body["warning"] is None
    assert _selected(world).json()["id"] == added["id"]
    listed = world.client.get(f"{BASE}/subjects/{world.subject}/books", headers=world.p1).json()
    assert {b["id"]: b["selected"] for b in listed} == {world.seeded: False, added["id"]: True}


def test_selecting_enforces_one_book_per_subject_per_year(world):
    added = _add_book(world).json()
    third = _add_book(world, title="Mathematics (Kerala SCERT)").json()
    for book_id in (added["id"], third["id"], added["id"]):
        assert _select(world, book_id).status_code == 200
    rows = world.store._fetchall(
        "SELECT * FROM book_selections WHERE academic_year_id=? AND subject_id=?",
        (world.year, world.subject))
    assert [r["book_id"] for r in rows] == [added["id"]]


def test_the_store_itself_refuses_a_second_selection_row(world):
    """The rule is the table's, not only the route's: a raw second row for
    the same subject and year is refused by SQLite."""
    added = _add_book(world).json()
    world.store.select_book(added["id"])
    with pytest.raises(sqlite3.IntegrityError):
        world.store._exec(
            "INSERT INTO book_selections (academic_year_id, subject_id, book_id, selected_at) "
            "VALUES (?,?,?,?)", (world.year, world.subject, world.seeded, "2026-09-22"))


def test_a_book_of_another_subject_cannot_be_selected(world):
    other = world.store.create_subject(
        grade_id=world.store.get_subject(world.subject).grade_id, name="Science")
    science_book = world.store.create_book(subject_id=other.id, board_id=world.board,
                                           title="Science", status="ready")
    r = _select(world, science_book.id)
    assert r.status_code == 422, r.text
    assert _selected(world).json()["id"] == world.seeded


def test_a_teacher_cannot_select(world):
    added = _add_book(world).json()
    assert _select(world, added["id"], auth=world.teacher).status_code == 403
    assert _selected(world).json()["id"] == world.seeded


def test_another_school_cannot_select(world):
    added = _add_book(world).json()
    assert _select(world, added["id"], auth=world.p2).status_code == 403
    assert _selected(world).json()["id"] == world.seeded


def test_selecting_a_new_book_reports_the_existing_schedule_and_keeps_it(world):
    for day in ("2026-06-01", "2026-06-02", "2026-06-03"):
        world.store.create_scheduled_lesson(school_id="school_1", academic_year_id=world.year,
                                            book_id=world.seeded, subtopic_id="st_1", date=day)
    added = _add_book(world).json()
    r = _select(world, added["id"])
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["previousBookId"] == world.seeded
    assert body["previousBookScheduledLessons"] == 3
    assert body["warning"] and "3 lessons" in body["warning"]
    # The schedule belongs to the old book: nothing is silently re-pointed.
    lessons = world.store.scheduled_lessons_for_book(world.year, world.seeded)
    assert len(lessons) == 3
    assert world.store.scheduled_lessons_for_book(world.year, added["id"]) == []


def test_a_subject_with_two_books_and_no_choice_has_no_selected_book(world):
    """Two books added straight into the store with no choice recorded (not
    via add_book's path, which keeps the old one): the read says so rather
    than guessing by row order."""
    subject = world.store.create_subject(
        grade_id=world.store.get_subject(world.subject).grade_id, name="English")
    world.store._exec(
        "INSERT INTO books (id, subject_id, board_id, title, status) VALUES (?,?,?,?,?)",
        ("book_a", subject.id, world.board, "A", "ready"))
    world.store._exec(
        "INSERT INTO books (id, subject_id, board_id, title, status) VALUES (?,?,?,?,?)",
        ("book_b", subject.id, world.board, "B", "ready"))
    world.store._commit()
    assert world.store.selected_book_for_subject(subject.id) is None
    r = world.client.get(f"{BASE}/subjects/{subject.id}/selected-book", headers=world.p1)
    assert r.status_code == 404 and "choose" in r.json()["detail"]


# --------------------------------------------------------------------- #
# Every other edition is reported, not only the one chosen just before
# --------------------------------------------------------------------- #

def _schedule(w, book_id: str, days: tuple[str, ...]) -> None:
    for day in days:
        w.store.create_scheduled_lesson(school_id="school_1", academic_year_id=w.year,
                                        book_id=book_id, subtopic_id="st_1", date=day)


def test_a_to_b_to_c_still_reports_the_lessons_of_a(world):
    """Review finding: the count used to cover only the edition chosen just
    before this one. A has 2 lessons; choosing B warned about them; choosing
    C then reported previous=B with 0 lessons and no warning, although A's 2
    lessons were still in scheduled_lessons -- the silent stale schedule
    this task exists to prevent."""
    _schedule(world, world.seeded, ("2026-06-01", "2026-06-02"))
    b = _add_book(world, title="Mathematics B").json()
    c = _add_book(world, title="Mathematics C").json()
    assert _select(world, b["id"]).json()["previousBookScheduledLessons"] == 2
    body = _select(world, c["id"]).json()
    assert body["previousBookId"] == b["id"]
    # The immediately previous edition (B) has none of its own ...
    assert body["previousBookScheduledLessons"] == 0
    # ... but the response still accounts for every other edition.
    assert body["otherEditionsScheduledLessons"] == 2
    by_book = {e["bookId"]: e for e in body["otherEditions"]}
    assert by_book[world.seeded]["scheduledLessons"] == 2
    assert world.seeded in by_book and b["id"] in by_book and c["id"] not in by_book
    assert body["warning"] and "2 lessons" in body["warning"]
    assert "official curriculum" in body["warning"], "names the book that holds them"


def test_the_first_choice_among_several_books_reports_their_lessons(world):
    """No recorded choice and several books: there is no "previous" edition,
    yet lessons scheduled from any of them must still be reported."""
    subject = world.store.create_subject(
        grade_id=world.store.get_subject(world.subject).grade_id, name="English")
    for bid, title in (("book_a", "English A"), ("book_b", "English B")):
        world.store._exec(
            "INSERT INTO books (id, subject_id, board_id, title, status) VALUES (?,?,?,?,?)",
            (bid, subject.id, world.board, title, "ready"))
    world.store._commit()
    _schedule(world, "book_a", ("2026-06-01",))
    r = world.client.put(f"{BASE}/subjects/{subject.id}/selected-book",
                         json={"bookId": "book_b"}, headers=world.p1)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["previousBookId"] is None
    assert body["otherEditionsScheduledLessons"] == 1
    assert body["warning"] and "1 lesson " in body["warning"] and "English A" in body["warning"]


def test_teachers_still_assigned_to_an_old_edition_are_reported(world):
    """Review finding: choosing an edition leaves teacher_assignments on the
    old book untouched (the teacher's own views keep showing its schedule),
    and the response used to say nothing about them."""
    world.store.assign_teacher(school_id="school_1", teacher_id="teacher_x",
                               book_id=world.seeded)
    added = _add_book(world).json()
    body = _select(world, added["id"]).json()
    assert body["otherEditionsTeacherAssignments"] == 1
    by_book = {e["bookId"]: e for e in body["otherEditions"]}
    assert by_book[world.seeded]["teacherAssignments"] == 1
    assert body["warning"] and "1 teacher assignment" in body["warning"]
    # Reported, not moved: the assignment still points at the old book.
    rows = world.store._fetchall(
        "SELECT book_id FROM teacher_assignments WHERE teacher_id=?", ("teacher_x",))
    assert [r["book_id"] for r in rows] == [world.seeded]


def test_no_warning_when_no_other_edition_has_lessons_or_teachers(world):
    added = _add_book(world).json()
    body = _select(world, added["id"]).json()
    assert body["otherEditionsScheduledLessons"] == 0
    assert body["otherEditionsTeacherAssignments"] == 0
    assert body["warning"] is None
