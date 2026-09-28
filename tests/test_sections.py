"""Sections are rows of their own (M1.1, docs/plans/m1-school-data-model.md).

Until M1.1 a section was an optional label on a Grade row: a student was
enrolled in "grade 10", nothing could be enrolled, listed or reported per
section, and the v3 timetable (SCH-2), homework per section (TA-4) and the
student app (SA-1) had nothing to hang on. Now every grade has at least one
Section; a student is enrolled in a section; the principal adds, renames and
removes sections and names a class teacher; each of those is audited.

The migration test runs on a copy of a seeded school's database with the
sections table and column taken away, which is what every live school's
database looks like before this change reaches it.

These run through the real HTTP routes as authenticated users.
"""
from __future__ import annotations

import shutil
import sqlite3
from types import SimpleNamespace

import pytest

from academicos.curriculum.models import DEFAULT_SECTION_NAME
from academicos.curriculum.seed_cbse10 import seed_cbse_grade
from academicos.curriculum.store import CurriculumStore, SectionInUse

from _auth_helpers import register_invited
from test_blob_factory import clean_env, shared_gcs  # noqa: F401 - fixtures used by name
from test_assessment_routes_auth import _boot_client, _register

BASE = "/api/v1/curriculum"
PRINCIPAL_KEY = "test-bootstrap-key"
YEAR = {"academicYearLabel": "2026-27", "startDate": "2026-04-01", "endDate": "2027-03-31"}


def _bearer(user: dict) -> dict:
    return {"Authorization": f"Bearer {user['token']}"}


# --------------------------------------------------------------------- #
# The migration: every live school's database before M1.1
# --------------------------------------------------------------------- #

def _pre_sections_copy(src: CurriculumStore, tmp_path) -> "Path":
    """A copy of `src`'s database as it was before M1.1: no sections table,
    no student_enrollments.section_id."""
    src.close()
    dst = tmp_path / "pre_m11.sqlite"
    shutil.copy(src.db_path, dst)
    conn = sqlite3.connect(dst)
    conn.execute("DROP INDEX IF EXISTS idx_se_section")
    conn.execute("ALTER TABLE student_enrollments DROP COLUMN section_id")
    conn.execute("DROP TABLE sections")
    conn.commit()
    conn.close()
    return dst


def test_the_migration_gives_every_seeded_grade_one_section_and_places_its_students(tmp_path):
    store = CurriculumStore(tmp_path / "live.sqlite")
    nine = seed_cbse_grade(store, school_id="school_1", academic_year_label="2026-27",
                           start_date="2026-04-01", end_date="2027-03-31", grade_number=9)
    ten = seed_cbse_grade(store, school_id="school_1", academic_year_label="2026-27",
                          start_date="2026-04-01", end_date="2027-03-31", grade_number=10)
    # A grade row that carried the old label: its section keeps that name.
    labelled = store.create_grade(academic_year_id=ten.academic_year_id, number=8, section="Rose")
    store.enroll_student(school_id="school_1", student_id="stu_9", grade_id=nine.grade_id)
    store.enroll_student(school_id="school_1", student_id="stu_10", grade_id=ten.grade_id)
    store.enroll_student(school_id="school_1", student_id="stu_8", grade_id=labelled.id)

    migrated = CurriculumStore(_pre_sections_copy(store, tmp_path))
    by_grade = {g: migrated.sections_for_grade(g)
                for g in (nine.grade_id, ten.grade_id, labelled.id)}
    assert {g: [s.name for s in secs] for g, secs in by_grade.items()} == {
        nine.grade_id: [DEFAULT_SECTION_NAME],
        ten.grade_id: [DEFAULT_SECTION_NAME],
        labelled.id: ["Rose"],
    }
    for sec in (secs[0] for secs in by_grade.values()):
        assert sec.school_id == "school_1"
        assert sec.academic_year_id == ten.academic_year_id
    for student, grade in (("stu_9", nine.grade_id), ("stu_10", ten.grade_id),
                           ("stu_8", labelled.id)):
        e = migrated.enrollment_for_student(student)
        assert e.grade_id == grade
        assert e.section_id == by_grade[grade][0].id

    # Idempotent: a second start adds nothing and moves no one.
    path = migrated.db_path
    migrated.close()
    again = CurriculumStore(path)
    assert len(again.sections_for_year(ten.academic_year_id)) == 3
    assert again.enrollment_for_student("stu_10").section_id == by_grade[ten.grade_id][0].id
    again.close()


def test_the_migration_never_guesses_a_section_for_a_grade_that_has_several(tmp_path):
    store = CurriculumStore(tmp_path / "c.sqlite")
    year = store.create_academic_year(school_id="s", label="y", start_date="2026-04-01",
                                      end_date="2027-03-31")
    grade = store.create_grade(academic_year_id=year.id, number=10)
    store.create_section(grade_id=grade.id, name="B")
    # A row written by code that predates sections: a grade, no section.
    store._exec("INSERT INTO student_enrollments (id, school_id, student_id, grade_id, created_at) "
                "VALUES ('enroll_old', 's', 'stu_old', ?, '2026-04-01')", (grade.id,))
    store._commit()
    store._migrate_sections()
    assert store.enrollment_for_student("stu_old").section_id is None
    store.close()


# --------------------------------------------------------------------- #
# The migration during a rollout: two instances, one snapshot blob
# --------------------------------------------------------------------- #
# Cloud Run runs the old and the new release side by side for a moment. The
# new one migrates the snapshot it restored; if that upload happened at boot,
# the old one's next upload would be refused and its unsaved edits moved to
# conflicts/. And a conflict can reload a snapshot the old release wrote,
# which has no sections at all.

def _publish_pre_sections_snapshot(tmp_path, env) -> None:
    """Upload, as the only snapshot, a seeded school's database in the shape
    every live one has before M1.1. Built with no bucket configured, so
    building it uploads nothing; `env` is the monkeypatch the GCS fake uses."""
    from academicos.storage.blobs import durable_blob_store
    from test_blob_factory import BUCKET

    env.delenv("ACOS_GCS_BUCKET")
    local = CurriculumStore(tmp_path / "build" / "curriculum.sqlite")
    seeded = seed_cbse_grade(local, school_id="school_1", academic_year_label="2026-27",
                             start_date="2026-04-01", end_date="2027-03-31", grade_number=10)
    local.enroll_student(school_id="school_1", student_id="stu_10", grade_id=seeded.grade_id)
    path = _pre_sections_copy(local, tmp_path)
    env.setenv("ACOS_GCS_BUCKET", BUCKET)
    durable_blob_store("curriculum-snapshots").upload(
        "curriculum.sqlite", path.read_bytes(), "application/x-sqlite3")


def _tables_in(data: bytes, tmp_path) -> set[str]:
    path = tmp_path / "inspect.sqlite"
    path.write_bytes(data)
    conn = sqlite3.connect(path)
    try:
        return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        conn.close()


def test_a_new_instance_migrates_without_uploading_until_a_real_edit(shared_gcs, clean_env, tmp_path):
    from test_blob_factory import _snapshot

    _publish_pre_sections_snapshot(tmp_path, clean_env)
    before = _snapshot(shared_gcs)

    new = CurriculumStore(tmp_path / "new" / "curriculum.sqlite")
    other = CurriculumStore(tmp_path / "other" / "curriculum.sqlite")
    assert _snapshot(shared_gcs)["generation"] == before["generation"], \
        "starting uploaded the migration, so the instance it replaces would lose its next save"
    year = new.academic_years_for_school("school_1")[0]
    [first] = new.sections_for_year(year.id)
    # Both instances derived the same row from the same snapshot.
    assert [s.id for s in other.sections_for_year(year.id)] == [first.id]
    assert new.enrollment_for_student("stu_10").section_id == first.id

    # The next real edit carries the migration with it.
    new.create_section(grade_id=first.grade_id, name="B")
    after = _snapshot(shared_gcs)
    assert after["generation"] > before["generation"]
    assert "sections" in _tables_in(after["data"], tmp_path)
    other.close()
    new.close()


def test_a_conflict_that_reloads_an_older_releases_snapshot_migrates_it(shared_gcs, clean_env, tmp_path):
    import threading
    from academicos.storage.blobs import CurriculumNotDurable
    from academicos.storage.snapshot_sync import SnapshotSync
    from test_blob_factory import _conflict_copies

    _publish_pre_sections_snapshot(tmp_path, clean_env)
    new = CurriculumStore(tmp_path / "new" / "curriculum.sqlite")
    year = new.academic_years_for_school("school_1")[0]
    [grade] = new.grades_for_year(year.id)

    # The old release, still serving, saves an edit of its own: a snapshot in
    # its shape, with no sections table.
    lock = threading.RLock()
    old_path = tmp_path / "old" / "curriculum.sqlite"
    old_sync = SnapshotSync("curriculum-snapshots", "curriculum.sqlite", old_path, lock)
    old_conn = sqlite3.connect(str(old_path), check_same_thread=False)
    with lock:
        old_conn.execute("INSERT INTO boards (id, name, code) VALUES ('board_st', 'State', 'ST')")
    old_sync.commit(old_conn)

    # The new release's next save is refused and it reloads the old one's.
    with pytest.raises(CurriculumNotDurable):
        new.create_section(grade_id=grade.id, name="B")
    assert len(_conflict_copies(shared_gcs)) == 1
    assert new.get_board_by_code("ST") is not None, "the old release's snapshot was not reloaded"
    assert [s.name for s in new.sections_for_grade(grade.id)] == ["A"], \
        "the reloaded snapshot was not migrated"
    assert new.enrollment_for_student("stu_10").section_id is not None

    # And it is not wedged: the retry lands.
    new._snapshots._last_upload_at = 0.0
    new.create_section(grade_id=grade.id, name="B")
    assert [s.name for s in new.sections_for_grade(grade.id)] == ["A", "B"]
    old_sync.close()
    old_conn.close()
    new.close()


# --------------------------------------------------------------------- #
# The store's rules
# --------------------------------------------------------------------- #

@pytest.fixture
def store(tmp_path):
    s = CurriculumStore(tmp_path / "c.sqlite")
    yield s
    s.close()


def _year_and_grade(store):
    year = store.create_academic_year(school_id="s", label="y", start_date="2026-04-01",
                                      end_date="2027-03-31")
    return year, store.create_grade(academic_year_id=year.id, number=10)


def test_a_new_grade_starts_with_section_a(store):
    _, grade = _year_and_grade(store)
    assert [s.name for s in store.sections_for_grade(grade.id)] == ["A"]


def test_section_names_are_unique_in_a_class_whatever_the_case(store):
    _, grade = _year_and_grade(store)
    store.create_section(grade_id=grade.id, name="Lotus")
    with pytest.raises(ValueError, match="already has a section named 'Lotus'"):
        store.create_section(grade_id=grade.id, name="  lotus ")
    with pytest.raises(ValueError, match="needs a name"):
        store.create_section(grade_id=grade.id, name="   ")


def test_a_section_with_students_or_a_class_last_section_is_not_removed(store):
    _, grade = _year_and_grade(store)
    a = store.sections_for_grade(grade.id)[0]
    b = store.create_section(grade_id=grade.id, name="B")
    store.enroll_student(school_id="s", student_id="stu", section_id=b.id)
    with pytest.raises(SectionInUse, match="1 student"):
        store.delete_section(b.id)
    store.enroll_student(school_id="s", student_id="stu", section_id=a.id)
    store.delete_section(b.id)
    with pytest.raises(SectionInUse, match="at least one section"):
        store.delete_section(a.id)


# --------------------------------------------------------------------- #
# Through the routes
# --------------------------------------------------------------------- #

@pytest.fixture
def world(tmp_path, monkeypatch):
    with _boot_client(tmp_path, monkeypatch) as client:
        p1 = _register(client, "school_1", "p1@example.com", "Priya Principal",
                       principal_key=PRINCIPAL_KEY)
        p2 = _register(client, "school_2", "p2@example.com", "Ravi Principal",
                       principal_key=PRINCIPAL_KEY)
        teacher = _register(client, "school_1", "t1@example.com", "Ana Teacher")
        other_teacher = _register(client, "school_2", "t2@example.com", "Omar Teacher")
        s1 = register_invited(client, "school_1", "s1@example.com", name="Asha", role="student")
        s2 = register_invited(client, "school_1", "s2@example.com", name="Ben", role="student")
        seeded = client.post(f"{BASE}/seed/cbse", json={**YEAR, "grade": 10},
                             headers=_bearer(p1))
        assert seeded.status_code == 200, seeded.text
        seeded2 = client.post(f"{BASE}/seed/cbse", json={**YEAR, "grade": 10},
                              headers=_bearer(p2))
        assert seeded2.status_code == 200, seeded2.text
        yield SimpleNamespace(
            client=client, p1=_bearer(p1), p2=_bearer(p2), teacher=_bearer(teacher),
            teacher_id=teacher["user"]["id"], other_teacher_id=other_teacher["user"]["id"],
            s1=s1["user"]["id"], s2=s2["user"]["id"], s1_auth=_bearer(s1),
            year=seeded.json()["academicYearId"], grade=seeded.json()["gradeId"],
            year2=seeded2.json()["academicYearId"], grade2=seeded2.json()["gradeId"])


def _sections(w, auth=None, year=None):
    r = w.client.get(f"{BASE}/academic-years/{year or w.year}/sections", headers=auth or w.p1)
    assert r.status_code == 200, r.text
    return r.json()


def _add(w, name, auth=None, grade=None, **extra):
    return w.client.post(f"{BASE}/grades/{grade or w.grade}/sections",
                         json={"name": name, **extra}, headers=auth or w.p1)


def _enroll(w, student, **body):
    return w.client.post(f"{BASE}/student-enrollments", json={"studentId": student, **body},
                         headers=w.p1)


def _roster(w, section_id):
    r = w.client.get(f"{BASE}/sections/{section_id}/students", headers=w.p1)
    assert r.status_code == 200, r.text
    return [row["studentId"] for row in r.json()]


def _audit(action):
    """The action's entries, oldest first (for_action returns newest first)."""
    from academicos.assessment.audit_log import get_audit_log
    from academicos.curriculum import routes as curriculum_routes
    return list(reversed(get_audit_log(curriculum_routes._cfg.data_root).for_action(action)))


def test_seeding_a_class_gives_it_section_a(world):
    [only] = _sections(world)
    assert only["name"] == "A" and only["gradeNumber"] == 10
    assert only["gradeId"] == world.grade and only["studentCount"] == 0


def test_a_student_enrolled_in_10b_is_not_in_10as_roster(world):
    [a] = _sections(world)
    b = _add(world, "B")
    assert b.status_code == 200, b.text
    b = b.json()

    assert _enroll(world, world.s1, sectionId=a["id"]).status_code == 200
    r = _enroll(world, world.s2, sectionId=b["id"])
    assert r.status_code == 200, r.text
    assert r.json()["sectionId"] == b["id"] and r.json()["gradeId"] == world.grade

    assert _roster(world, a["id"]) == [world.s1]
    assert _roster(world, b["id"]) == [world.s2]
    assert {s["name"]: s["studentCount"] for s in _sections(world)} == {"A": 1, "B": 1}


def test_grade_alone_enrolls_in_a_one_section_class_and_is_refused_for_two(world):
    [a] = _sections(world)
    r = _enroll(world, world.s1, gradeId=world.grade)
    assert r.status_code == 200, r.text
    assert r.json()["sectionId"] == a["id"]

    assert _add(world, "B").status_code == 200
    r = _enroll(world, world.s2, gradeId=world.grade)
    assert r.status_code == 422
    assert "2 sections (A, B)" in r.json()["detail"]
    assert _enroll(world, world.s2).status_code == 422


def test_moving_a_student_is_audited_with_the_section_they_left(world):
    [a] = _sections(world)
    b = _add(world, "B").json()
    _enroll(world, world.s1, sectionId=a["id"])
    _enroll(world, world.s1, sectionId=b["id"])
    _enroll(world, world.s1, sectionId=b["id"])       # no change, no entry
    moves = [e for e in _audit("student_enrolled") if e["student_id"] == world.s1]
    assert [(m["details"]["previousSectionId"], m["details"]["sectionId"]) for m in moves] == [
        (None, a["id"]), (a["id"], b["id"])]
    assert _roster(world, a["id"]) == [] and _roster(world, b["id"]) == [world.s1]


def test_names_are_checked_and_unknown_fields_refused(world):
    assert _add(world, "b").status_code == 200
    dup = _add(world, " B ")
    assert dup.status_code == 422 and "already has a section named 'b'" in dup.json()["detail"]
    assert _add(world, "   ").status_code == 422
    assert _add(world, "x" * 21).status_code == 422
    assert _add(world, "C", classTeacher="oops").status_code == 422


def test_rename_and_class_teacher_are_audited_before_and_after(world):
    [a] = _sections(world)
    url = f"{BASE}/sections/{a['id']}"
    r = world.client.patch(url, json={"name": "Rose", "classTeacherId": world.teacher_id},
                           headers=world.p1)
    assert r.status_code == 200, r.text
    assert r.json()["name"] == "Rose" and r.json()["classTeacherId"] == world.teacher_id

    # A field left out is unchanged; null clears the class teacher.
    r = world.client.patch(url, json={"classTeacherId": None}, headers=world.p1)
    assert r.json()["name"] == "Rose" and r.json()["classTeacherId"] is None
    assert world.client.patch(url, json={"name": None}, headers=world.p1).status_code == 422

    [first, second] = [e["details"] for e in _audit("section_updated")]
    assert first["before"] == {"name": "A", "classTeacherId": None}
    assert first["after"] == {"name": "Rose", "classTeacherId": world.teacher_id}
    assert second["before"]["classTeacherId"] == world.teacher_id
    assert second["after"] == {"name": "Rose", "classTeacherId": None}


def test_a_class_teacher_is_staff_of_the_same_school(world):
    [a] = _sections(world)
    url = f"{BASE}/sections/{a['id']}"
    student = world.client.patch(url, json={"classTeacherId": world.s1}, headers=world.p1)
    assert student.status_code == 422
    other = world.client.patch(url, json={"classTeacherId": world.other_teacher_id},
                               headers=world.p1)
    assert other.status_code == 403
    assert world.client.patch(url, json={"classTeacherId": "user_nobody"},
                              headers=world.p1).status_code == 404


def test_removing_a_section_keeps_students_and_the_last_section(world):
    [a] = _sections(world)
    b = _add(world, "B").json()
    _enroll(world, world.s1, sectionId=b["id"])
    busy = world.client.delete(f"{BASE}/sections/{b['id']}", headers=world.p1)
    assert busy.status_code == 409 and "enrolled" in busy.json()["detail"]

    _enroll(world, world.s1, sectionId=a["id"])
    assert world.client.delete(f"{BASE}/sections/{b['id']}", headers=world.p1).status_code == 200
    last = world.client.delete(f"{BASE}/sections/{a['id']}", headers=world.p1)
    assert last.status_code == 409 and "at least one section" in last.json()["detail"]
    assert [s["name"] for s in _sections(world)] == ["A"]
    assert [e["details"]["before"]["name"] for e in _audit("section_deleted")] == ["B"]
    assert [e["details"]["after"]["name"] for e in _audit("section_created")] == ["B"]


def test_another_school_cannot_see_or_change_these_sections(world):
    [a] = _sections(world)
    [theirs] = _sections(world, auth=world.p2, year=world.year2)
    assert world.client.get(f"{BASE}/academic-years/{world.year}/sections",
                            headers=world.p2).status_code == 403
    assert _add(world, "Z", auth=world.p2).status_code == 403
    assert world.client.patch(f"{BASE}/sections/{a['id']}", json={"name": "Z"},
                              headers=world.p2).status_code == 403
    assert world.client.delete(f"{BASE}/sections/{a['id']}", headers=world.p2).status_code == 403
    assert world.client.get(f"{BASE}/sections/{a['id']}/students",
                            headers=world.p2).status_code == 403
    # Nor can a principal enroll their own student in another school's section.
    assert _enroll(world, world.s1, sectionId=theirs["id"]).status_code == 403


def test_teachers_read_sections_and_students_do_not(world):
    assert [s["name"] for s in _sections(world, auth=world.teacher)] == ["A"]
    assert _add(world, "B", auth=world.teacher).status_code == 403
    assert world.client.get(f"{BASE}/academic-years/{world.year}/sections",
                            headers=world.s1_auth).status_code == 403


def test_the_school_export_carries_its_sections(world):
    _add(world, "B")
    body = world.client.get(f"{BASE}/export", headers=world.p1).json()
    [grade] = body["curriculum"][0]["grades"]
    assert [s["name"] for s in grade["sections"]] == ["A", "B"]
