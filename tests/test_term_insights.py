"""Exam coverage and time saved, per term (scorecard items 5.1, 5.2, 6.1-6.3).

PRD section 12.6 gives the principal four metrics, two of them "this term":
(a) which classes and subjects have had a paper set this term, and which have
not; (b) time saved this term, labelled estimated. Decision 11 compares time
saved "per term". The audit of 2026-09-26 found neither computable: the report
was all-time, had no class or subject breakdown, and the builder's and the
hand-picked path's audit rows carried no class or subject at all.

These tests pin:
  * every generation path records the paper's class and subject;
  * the report reads a window of the school's own calendar dates (IST), and
    attributes an older entry that lacks a class through its assessment --
    one it cannot attribute is counted, never dropped;
  * exam coverage names what was set and what was not, against the classes
    6-10 the school itself declared for the term's year;
  * a term carries its own manual baseline, set by the principal alone, and a
    rename or re-date of the term keeps it;
  * `/paper-timing` reports the term covering the school's today, a named
    term on request, and says so -- never a silent all-time figure -- when no
    term covers today.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from academicos.assessment import paper_timing as pt
from test_paper_swap_pick import GEN, seeded  # noqa: F401
from test_paper_templates import BASE, _boot_client, _register

IST = timezone(timedelta(hours=5, minutes=30))
BOOTSTRAP = "test-bootstrap-key"


def _today():
    return datetime.now(IST).date()


def _iso(d) -> str:
    return d.isoformat()


# ------------------------------------------------------------------ the report

def _append(data_root, action, *, school_id="s1", seconds=6.0, assessment_id=None, **details):
    from academicos.assessment.audit_log import get_audit_log
    get_audit_log(data_root).append(
        action, assessment_id=assessment_id,
        details={"paperId": "p", "schoolId": school_id, "generationSeconds": seconds, **details})


def test_the_report_reads_only_the_window_it_is_given(tmp_path):
    _append(tmp_path, "template_paper_generated", subject="Science", grade=10)
    today = _today()
    inside = pt.report(tmp_path, school_id="s1", start_date=_iso(today - timedelta(days=1)),
                       end_date=_iso(today + timedelta(days=1)))
    before = pt.report(tmp_path, school_id="s1", start_date="2020-04-01", end_date="2020-09-30")
    assert inside.papers == 1
    assert before.papers == 0


def test_papers_are_counted_per_class_and_subject(tmp_path):
    _append(tmp_path, "template_paper_generated", subject="Science", grade=10)
    _append(tmp_path, "quick_paper_generated", subject="Science", grade=10)
    _append(tmp_path, "id_curated_paper_generated", subject="Mathematics", grade=9)
    rep = pt.report(tmp_path, school_id="s1")
    assert rep.papers_by_class_subject == {(10, "Science"): 2, (9, "Mathematics"): 1}
    assert rep.unattributed == 0


def test_an_older_entry_is_attributed_through_its_assessment_or_counted_as_unattributed(tmp_path):
    """Entries written before this change carry no class or subject. They are
    attributed through the assessment they record, and one that cannot be is
    still a paper -- counted as unattributed, not dropped."""
    _append(tmp_path, "template_paper_generated", assessment_id="a1")
    _append(tmp_path, "template_paper_generated", assessment_id="gone")
    known = {"a1": ("Science", 8)}
    rep = pt.report(tmp_path, school_id="s1", attribute=known.get)
    assert rep.papers == 2
    assert rep.papers_by_class_subject == {(8, "Science"): 1}
    assert rep.unattributed == 1


def test_a_term_baseline_replaces_the_default_and_says_where_it_came_from(tmp_path):
    _append(tmp_path, "template_paper_generated", subject="Science", grade=10, seconds=60.0)
    rep = pt.report(tmp_path, school_id="s1", baseline=(90.0, "set by the principal for Term 1"))
    assert rep.baseline_minutes_per_paper == 90.0
    assert rep.baseline_provenance == "set by the principal for Term 1"
    assert rep.estimated_minutes_saved_per_paper == 89.0


def test_exam_coverage_names_what_was_set_and_what_was_not(tmp_path):
    _append(tmp_path, "template_paper_generated", subject="Science", grade=10)
    _append(tmp_path, "template_paper_generated", subject="science", grade=10)
    rep = pt.report(tmp_path, school_id="s1")
    cov = pt.exam_coverage(rep, universe=[(10, "Science"), (10, "Mathematics"), (9, "Science")])
    assert cov["covered"] == [{"grade": 10, "subject": "Science", "papers": 2}]
    assert cov["notYet"] == [{"grade": 9, "subject": "Science"},
                             {"grade": 10, "subject": "Mathematics"}]
    assert cov["classesDeclared"] is True


def test_exam_coverage_without_declared_classes_cannot_list_what_is_missing(tmp_path):
    _append(tmp_path, "template_paper_generated", subject="Science", grade=10)
    cov = pt.exam_coverage(pt.report(tmp_path, school_id="s1"), universe=None)
    assert cov["covered"] == [{"grade": 10, "subject": "Science", "papers": 1}]
    assert cov["notYet"] == [] and cov["classesDeclared"] is False


# ------------------------------------------------------------------ the routes

def _school(tmp_path, *, grades=((10, ("Science", "Mathematics")), (9, ("Science",)))):
    """A school year around today, with the classes and subjects the school
    declared. Returns the store and the year."""
    from academicos.curriculum.store import get_curriculum_store
    store = get_curriculum_store(tmp_path)
    today = _today()
    year = store.create_academic_year(school_id="school_1", label="2026-27",
                                      start_date=_iso(today - timedelta(days=200)),
                                      end_date=_iso(today + timedelta(days=200)))
    for number, subjects in grades:
        g = store.create_grade(academic_year_id=year.id, number=number)
        for name in subjects:
            store.create_subject(grade_id=g.id, name=name)
    return store, year


def _term(store, year, *, name="Term 1", days_back=30, days_on=30):
    today = _today()
    return store.create_term(academic_year_id=year.id, name=name,
                             start_date=_iso(today - timedelta(days=days_back)),
                             end_date=_iso(today + timedelta(days=days_on)))


def _users(client):
    principal = _register(client, "school_1", "head@example.com", role="principal",
                          principal_key=BOOTSTRAP)
    teacher = _register(client, "school_1", "ana@example.com")
    return principal, teacher


def _set_papers(client, teacher):
    """One paper by each path the web app and API offer, all Science 10."""
    tid = client.post(BASE, json={
        "name": "Unit test", "grade": 10, "subject": "Science", "examType": "unit_test",
        "totalMarks": 8, "durationMinutes": 40,
        "sections": [{"title": "Section A", "questionCount": 2, "marksEach": 1},
                     {"title": "Section B", "questionCount": 2, "marksEach": 3}],
        "scope": {"chapterIds": ["ch1"]}}, headers=teacher).json()["id"]
    assert client.post(GEN, json={"templateId": tid}, headers=teacher).status_code == 200
    r = client.post("/api/v1/papers/quick-generate", headers=teacher, json={
        "subject": "Science", "grade": 10, "chapterIds": ["ch1"], "totalMarks": 20})
    assert r.status_code == 200, r.text
    r = client.post("/api/v1/papers/generate-from-ids", headers=teacher, json={
        "subject": "Science", "grade": 10, "questionIds": ["o0", "o1"]})
    assert r.status_code == 200, r.text


def test_every_generation_path_records_the_class_and_subject(tmp_path, monkeypatch, seeded):
    from academicos.assessment.audit_log import get_audit_log
    with _boot_client(tmp_path, monkeypatch) as client:
        _, teacher = _users(client)
        _set_papers(client, teacher)
        audit = get_audit_log(tmp_path)
        for action in pt.GENERATION_ACTIONS:
            rows = audit.for_action(action)
            assert len(rows) == 1, action
            details = rows[0]["details"]
            assert (details.get("subject"), details.get("grade")) == ("Science", 10), action


def test_paper_timing_reports_this_term_with_exam_coverage(tmp_path, monkeypatch, seeded):
    with _boot_client(tmp_path, monkeypatch) as client:
        principal, teacher = _users(client)
        store, year = _school(tmp_path)
        term = _term(store, year)
        _set_papers(client, teacher)
        r = client.get("/api/v1/paper-timing", headers=principal)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["scope"] == "term"
        assert body["term"] == {"id": term.id, "name": "Term 1",
                                "startDate": term.start_date, "endDate": term.end_date,
                                "manualBaselineMinutes": None}
        assert body["papers"] == 3
        assert body["papersByPath"] == {"quick": 1, "builder": 1, "hand-picked": 1}
        assert body["examCoverage"]["covered"] == [{"grade": 10, "subject": "Science", "papers": 3}]
        assert body["examCoverage"]["notYet"] == [{"grade": 9, "subject": "Science"},
                                                  {"grade": 10, "subject": "Mathematics"}]
        assert body["examCoverage"]["classesDeclared"] is True


def test_an_earlier_term_reports_only_its_own_papers(tmp_path, monkeypatch, seeded):
    with _boot_client(tmp_path, monkeypatch) as client:
        principal, teacher = _users(client)
        store, year = _school(tmp_path)
        earlier = _term(store, year, name="Term 1", days_back=120, days_on=-60)
        _term(store, year, name="Term 2", days_back=30, days_on=30)
        _set_papers(client, teacher)
        body = client.get(f"/api/v1/paper-timing?termId={earlier.id}", headers=principal).json()
        assert body["scope"] == "term" and body["term"]["name"] == "Term 1"
        assert body["papers"] == 0
        assert body["examCoverage"]["covered"] == []
        assert len(body["examCoverage"]["notYet"]) == 3


def test_with_no_term_covering_today_it_says_so_rather_than_passing_all_time_as_a_term(
        tmp_path, monkeypatch, seeded):
    with _boot_client(tmp_path, monkeypatch) as client:
        principal, teacher = _users(client)
        _set_papers(client, teacher)
        body = client.get("/api/v1/paper-timing", headers=principal).json()
        assert body["scope"] == "allTime" and body["term"] is None
        assert "no term" in body["scopeNote"].lower()
        assert body["papers"] == 3
        assert body["examCoverage"]["classesDeclared"] is False


def test_another_schools_term_is_refused(tmp_path, monkeypatch, seeded):
    from academicos.curriculum.store import get_curriculum_store
    with _boot_client(tmp_path, monkeypatch) as client:
        principal, _ = _users(client)
        store = get_curriculum_store(tmp_path)
        today = _today()
        other = store.create_academic_year(school_id="school_2", label="2026-27",
                                           start_date=_iso(today - timedelta(days=10)),
                                           end_date=_iso(today + timedelta(days=10)))
        t = store.create_term(academic_year_id=other.id, name="Term 1",
                              start_date=_iso(today), end_date=_iso(today))
        assert client.get(f"/api/v1/paper-timing?termId={t.id}",
                          headers=principal).status_code == 403
        assert client.get("/api/v1/paper-timing?termId=term_missing",
                          headers=principal).status_code == 404


BASELINE = "/api/v1/curriculum/terms/{}/baseline"


def test_the_principal_sets_a_terms_baseline_and_the_report_uses_it(tmp_path, monkeypatch, seeded):
    from academicos.assessment.audit_log import get_audit_log
    with _boot_client(tmp_path, monkeypatch) as client:
        principal, teacher = _users(client)
        store, year = _school(tmp_path)
        term = _term(store, year)
        assert client.put(BASELINE.format(term.id), json={"minutes": 60},
                          headers=teacher).status_code == 403
        r = client.put(BASELINE.format(term.id), json={"minutes": 60}, headers=principal)
        assert r.status_code == 200, r.text
        assert r.json()["manualBaselineMinutes"] == 60
        _set_papers(client, teacher)
        body = client.get("/api/v1/paper-timing", headers=principal).json()
        assert body["baselineMinutesPerPaper"] == 60
        assert body["term"]["manualBaselineMinutes"] == 60
        assert "Term 1" in body["baselineProvenance"] and "principal" in body["baselineProvenance"]
        # The change is on the record: a baseline moves the saving a principal quotes.
        rows = get_audit_log(tmp_path).for_action("paper_baseline_set")
        assert rows and rows[0]["details"]["minutes"] == 60


def test_a_baseline_must_be_a_sensible_number_and_can_be_cleared(tmp_path, monkeypatch, seeded):
    with _boot_client(tmp_path, monkeypatch) as client:
        principal, _ = _users(client)
        store, year = _school(tmp_path)
        term = _term(store, year)
        for bad in (0, -5, 100_000):
            assert client.put(BASELINE.format(term.id), json={"minutes": bad},
                              headers=principal).status_code == 422, bad
        client.put(BASELINE.format(term.id), json={"minutes": 50}, headers=principal)
        r = client.put(BASELINE.format(term.id), json={"minutes": None}, headers=principal)
        assert r.status_code == 200 and r.json()["manualBaselineMinutes"] is None
        body = client.get("/api/v1/paper-timing", headers=principal).json()
        assert "declared default" in body["baselineProvenance"]


def test_editing_a_terms_dates_keeps_its_baseline(tmp_path, monkeypatch, seeded):
    """PUT /terms/{id} replaces name and dates; the web term editor does not
    know the baseline, so it must not be the thing that wipes it."""
    with _boot_client(tmp_path, monkeypatch) as client:
        principal, _ = _users(client)
        store, year = _school(tmp_path)
        term = _term(store, year)
        client.put(BASELINE.format(term.id), json={"minutes": 75}, headers=principal)
        r = client.put(f"/api/v1/curriculum/terms/{term.id}", headers=principal, json={
            "name": "First term", "startDate": term.start_date, "endDate": term.end_date})
        assert r.status_code == 200, r.text
        assert r.json()["manualBaselineMinutes"] == 75
        assert store.get_term(term.id).manual_baseline_minutes == 75


def test_an_existing_terms_table_gains_the_baseline_column(tmp_path):
    """A school's database from before this change has a terms table without
    the column; opening it must add the column, not fail on the first read."""
    import sqlite3
    from academicos.curriculum.store import CurriculumStore
    db = tmp_path / "old.sqlite"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE terms (id TEXT PRIMARY KEY, school_id TEXT NOT NULL, "
                 "academic_year_id TEXT NOT NULL, name TEXT NOT NULL, start_date TEXT NOT NULL, "
                 "end_date TEXT NOT NULL, UNIQUE(academic_year_id, name))")
    conn.execute("INSERT INTO terms VALUES ('term_old','school_1','year_1','Term 1',"
                 "'2026-04-01','2026-09-30')")
    conn.commit()
    conn.close()
    store = CurriculumStore(db)
    assert store.get_term("term_old").manual_baseline_minutes is None


def test_a_paper_counts_once_and_only_while_it_exists(tmp_path, monkeypatch, seeded):
    """D42: Generate pressed again on the same choices made the same paper
    under a second id and both counted, a regeneration on one assessment
    counted the paper it replaced, and a deleted paper still counted. The
    term report's time saved reads the same figures."""
    with _boot_client(tmp_path, monkeypatch) as client:
        principal, teacher = _users(client)
        store, year = _school(tmp_path)
        _term(store, year)
        tid = client.post(BASE, json={
            "name": "Unit test", "grade": 10, "subject": "Science", "examType": "unit_test",
            "totalMarks": 8, "durationMinutes": 40,
            "sections": [{"title": "Section A", "questionCount": 2, "marksEach": 1},
                         {"title": "Section B", "questionCount": 2, "marksEach": 3}],
            "scope": {"chapterIds": ["ch1"]}}, headers=teacher).json()["id"]
        first, again = (client.post(GEN, json={"templateId": tid}, headers=teacher).json() for _ in range(2))
        assert first["assessmentId"] != again["assessmentId"]
        # Generate pressed again prints other questions now (QA P-03): two papers.
        assert ([q["questionId"] for s in first["paper"]["sections"] for q in s["questions"]]
                != [q["questionId"] for s in again["paper"]["sections"] for q in s["questions"]])
        quick = client.post("/api/v1/papers/quick-generate", headers=teacher, json={
            "subject": "Science", "grade": 10, "chapterIds": ["ch1"], "totalMarks": 20}).json()
        assert client.delete(f"/api/v1/assessments/{quick['assessmentId']}", headers=teacher).status_code == 200
        picked = client.post("/api/v1/papers/generate-from-ids", headers=teacher, json={
            "subject": "Science", "grade": 10, "questionIds": ["o0", "o1"]}).json()
        r = client.post("/api/v1/papers/generate-from-ids", headers=teacher, json={
            "subject": "Science", "grade": 10, "questionIds": ["o2", "o3"],
            "assessmentId": picked["assessmentId"]})
        assert r.status_code == 200, r.text
        # The same questions again, on a new assessment: the same paper twice.
        twin = client.post("/api/v1/papers/generate-from-ids", headers=teacher, json={
            "subject": "Science", "grade": 10, "questionIds": ["o2", "o3"]})
        assert twin.status_code == 200 and twin.json()["assessmentId"] != picked["assessmentId"]

        body = client.get("/api/v1/paper-timing", headers=principal).json()
        assert body["papers"] == 3, "6 presses, 3 papers that still exist"
        assert body["papersByPath"] == {"builder": 2, "hand-picked": 1}
        assert body["examCoverage"]["covered"] == [{"grade": 10, "subject": "Science", "papers": 3}]
        assert body["estimatedMinutesSavedTotal"] == pytest.approx(3 * body["estimatedMinutesSavedPerPaper"], abs=0.1)
        term = client.get("/api/v1/dashboard/term", headers=principal)
        assert term.status_code == 200, term.text
        saved = term.json()["timeSaved"]
        assert saved["papers"] == 3 and saved["estimated"] is True
        assert term.json()["exams"]["papersSet"] == 3
