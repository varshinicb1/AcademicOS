"""The web client's Coverage & Pace fixture is what the route really returns.

The 2026-09-21 product audit found the principal's Coverage & Pace screen
reading field names the backend never sends (coveragePercent, totalCount,
completedCount, plannedCount, pacePercent) where CoverageReportResponse
sends coveragePct, totalLessons, completedLessons, plannedToDate and pacePct.
Every subject showed '0.0% covered' and '0/0 lessons', and the headline pace
read 100% for a school 89 lessons behind. Nothing caught it because the
Flutter side was only ever tested against hand-written JSON.

frontend/test/fixtures/coverage_report.json is now a payload captured from
GET /curriculum/reporting/coverage through TestClient, and
frontend/test/widget/coverage_report_test.dart parses it. This test re-runs
the same capture and fails if the route's output and the committed fixture
differ, so a renamed or added field breaks here instead of silently zeroing
the screen again.

Regenerate after an intended contract change (then re-run the Dart test):

    PYTHONPATH=src python tests/test_curriculum_coverage_fixture.py --write

Generated ids (year_/subj_/book_/chap_ + uuid hex, user ids) differ every
run, so both sides are normalised to stable placeholders by order of first
appearance before comparing. Every figure is compared exactly.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_assessment_routes_auth import _boot_client, _register  # noqa: E402

FIXTURE = (Path(__file__).resolve().parents[1]
           / "frontend" / "test" / "fixtures" / "coverage_report.json")
PRINCIPAL_KEY = "test-bootstrap-key"
AS_OF = "2026-09-14"

# Keys whose values are generated per run; replaced by <key-stem>_<n>.
_GENERATED_ID_KEYS = ("academicYearId", "subjectId", "bookId", "chapterId", "teacherId")


def _normalise(payload: dict) -> dict:
    seen: dict[tuple[str, str], str] = {}

    def walk(node):
        if isinstance(node, dict):
            out = {}
            for k, v in node.items():
                if k in _GENERATED_ID_KEYS and isinstance(v, str):
                    stem = k[:-2]
                    count = sum(1 for (key, _) in seen if key == k)
                    v = seen.setdefault((k, v), f"{stem}_{count + 1}")
                out[k] = walk(v)
            return out
        if isinstance(node, list):
            return [walk(x) for x in node]
        return node

    return walk(payload)


def _lesson(store, school, year, book, subtopic, date, status="scheduled", by=None):
    lesson = store.create_scheduled_lesson(school_id=school, academic_year_id=year,
                                           book_id=book, subtopic_id=subtopic, date=date)
    if status != "scheduled":
        store.mark_lesson(lesson.id, status=status, note=None, completed_by=by)
    return lesson


def _subtopics(store, book_id: str, chapter_names: list[str], per_chapter: int) -> list[list[str]]:
    unit = store.create_unit(book_id=book_id, canonical_id=f"{book_id}_u1", unit_no="1", name="Unit 1")
    out = []
    for ci, name in enumerate(chapter_names):
        ch = store.create_chapter(canonical_id=f"{book_id}_c{ci}", unit_id=unit.id, name=name, seq=ci)
        tp = store.create_topic(chapter_id=ch.id, canonical_id=f"{book_id}_c{ci}_t", name=f"{name} basics")
        out.append([
            store.create_subtopic(topic_id=tp.id, canonical_id=f"{book_id}_c{ci}_s{i}",
                                  name=f"{name} part {i + 1}", seq=i).id
            for i in range(per_chapter)
        ])
    return out


def capture_coverage_payload(tmp_path: Path, monkeypatch) -> dict:
    """A small real school: Grade 7 Mathematics is behind (taught, skipped
    and overdue lessons, a teacher assigned); Grade 10 Science has lessons
    only after the as-of date, so nothing was due yet -- the case the
    backend reports as pacePct 100.0 with plannedToDate 0."""
    with _boot_client(tmp_path, monkeypatch) as client:
        principal = _register(client, "school_1", "p1@example.com", "Priya Principal",
                              principal_key=PRINCIPAL_KEY)
        teacher = _register(client, "school_1", "t1@example.com", "Tara Teacher")
        from academicos.curriculum import routes as curriculum_routes
        store = curriculum_routes._require()
        school = "school_1"
        year = store.create_academic_year(school_id=school, label="2026-27",
                                          start_date="2026-06-01", end_date="2027-03-31").id
        board = store.create_board(name="CBSE", code="CBSE")
        teacher_id = teacher["user"]["id"]

        g7 = store.create_grade(academic_year_id=year, number=7)
        maths = store.create_subject(grade_id=g7.id, name="Mathematics", code="MATH7")
        maths_book = store.create_book(subject_id=maths.id, board_id=board.id, title="Mathematics 7")
        store.assign_teacher(school_id=school, teacher_id=teacher_id, book_id=maths_book.id)
        fractions, integers = _subtopics(store, maths_book.id, ["Fractions", "Integers"], 3)
        # Integers (chapters sort by name, so Fractions is listed first in
        # the payload but taught second): 2 taught, 1 overdue.
        _lesson(store, school, year, maths_book.id, integers[0], "2026-09-01", "completed", teacher_id)
        _lesson(store, school, year, maths_book.id, integers[1], "2026-09-02", "completed", teacher_id)
        _lesson(store, school, year, maths_book.id, integers[2], "2026-09-03")
        # Fractions: 1 skipped, 1 overdue, 1 due on the as-of date, 1 future.
        _lesson(store, school, year, maths_book.id, fractions[0], "2026-09-08", "skipped", teacher_id)
        _lesson(store, school, year, maths_book.id, fractions[1], "2026-09-10")
        _lesson(store, school, year, maths_book.id, fractions[2], AS_OF)
        _lesson(store, school, year, maths_book.id, fractions[0], "2026-09-21")

        g10 = store.create_grade(academic_year_id=year, number=10)
        science = store.create_subject(grade_id=g10.id, name="Science", code="SCI10")
        science_book = store.create_book(subject_id=science.id, board_id=board.id, title="Science 10")
        (reactions,) = _subtopics(store, science_book.id, ["Chemical Reactions"], 2)
        _lesson(store, school, year, science_book.id, reactions[0], "2026-09-15")
        _lesson(store, school, year, science_book.id, reactions[1], "2026-09-16")

        r = client.get("/api/v1/curriculum/reporting/coverage",
                       params={"academic_year_id": year, "as_of_date": AS_OF},
                       headers={"Authorization": f"Bearer {principal['token']}"})
        assert r.status_code == 200, r.text
        return _normalise(r.json())


def test_committed_fixture_matches_what_the_route_returns(tmp_path, monkeypatch):
    assert FIXTURE.exists(), (
        f"{FIXTURE} is missing -- regenerate it with "
        "`python tests/test_curriculum_coverage_fixture.py --write`")
    live = capture_coverage_payload(tmp_path, monkeypatch)
    committed = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert live == committed, (
        "GET /curriculum/reporting/coverage no longer matches the web client's fixture. "
        "If the contract change is intended, regenerate with --write and update "
        "CoverageReport.fromJson (frontend/lib/data/datasources/api/curriculum_api.dart).")


def test_fixture_exercises_behind_and_nothing_due_yet(tmp_path, monkeypatch):
    # The two cases the screen got wrong must stay in the fixture, or the
    # Dart test stops guarding them: a subject behind schedule, and one with
    # nothing planned to date (backend pacePct 100.0 -- not "on track").
    live = capture_coverage_payload(tmp_path, monkeypatch)
    by_name = {s["subjectName"]: s for s in live["subjects"]}
    assert by_name["Mathematics"]["variance"] < 0
    assert by_name["Mathematics"]["gradeNumber"] == 7
    assert by_name["Mathematics"]["teacherName"] == "Tara Teacher"
    assert by_name["Science"]["plannedToDate"] == 0
    assert by_name["Science"]["pacePct"] == 100.0
    assert live["overallVariance"] < 0


if __name__ == "__main__":
    if "--write" not in sys.argv:
        sys.exit("usage: python tests/test_curriculum_coverage_fixture.py --write")
    import tempfile

    mp = pytest.MonkeyPatch()
    try:
        # The SQLite stores stay open on Windows until exit, hence the flag.
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            payload = capture_coverage_payload(Path(tmp), mp)
    finally:
        mp.undo()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {FIXTURE}")
