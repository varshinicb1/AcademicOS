"""A finalized grade cannot change silently; the audit log cannot be rewritten.

Audit item 8.5 (reproduced 2026-09-21 by two auditors): a sheet was finalized,
then its marks were changed 0->2 through /award and back through the sheet
review, and the audit row count stayed at 2 before and after. On an AuditLog
SQLite file, a raw UPDATE and a raw DELETE each returned rowcount 1. The
remote append was an upsert, so a replayed id overwrote the original row.
`sheet_evaluated` was logged with actor=None.

These tests hold the fixed contract:

* a mark change on a finalized sheet without a reason is 409 Conflict, on
  every writer (review, award, re-evaluation); with a reason it is applied and
  audited with the real actor, before, after and the reason;
* the audit table refuses UPDATE and DELETE in the database itself;
* an append with an id that already exists fails, locally and remotely;
* verify_chain() finds the row an attacker with file access edited.

Every store is under pytest's tmp_path; nothing touches a live service.
"""
from __future__ import annotations

import sqlite3

import pytest

from academicos.api.main import app
from academicos.assessment import audit_log as audit_mod
from academicos.assessment.audit_log import AuditLog, DuplicateAuditEntry

from _auth_helpers import register_invited
from test_route_inventory import blueprint_body, question_body


# --------------------------------------------------------------------------- #
# a booted app with one evaluated sheet
# --------------------------------------------------------------------------- #

class Sheet:
    def __init__(self, client, headers, teacher_id, aid, student_id, awarded, data_root):
        self.client = client
        self.headers = headers
        self.teacher_id = teacher_id
        self.aid = aid
        self.student_id = student_id
        self.awarded = awarded
        self.data_root = data_root

    @property
    def other_mark(self) -> int:
        """A mark that differs from the current one, inside 0..2."""
        return 0 if self.awarded else 2

    def audit(self) -> list[dict]:
        return audit_mod.get_audit_log(self.data_root).for_assessment(self.aid)

    def finalize(self) -> None:
        r = self.client.post(
            f"/api/v1/evaluations/sheet/{self.aid}/{self.student_id}/finalize",
            json={}, headers=self.headers)
        assert r.status_code == 200, r.text

    def award(self, marks: int, **extra):
        return self.client.post(
            f"/api/v1/evaluations/assessment/{self.aid}/question/q_1/award",
            json={"marks": marks, "studentIds": [self.student_id], **extra},
            headers=self.headers)

    def review(self, marks: int, **extra):
        return self.client.post(
            f"/api/v1/evaluations/sheet/{self.aid}/{self.student_id}/review/q_1",
            json={"action": "edit", "marks": marks, **extra}, headers=self.headers)

    def evaluate(self, **extra):
        return self.client.post("/api/v1/evaluations/sheet", json={
            "assessmentId": self.aid, "studentId": self.student_id,
            "studentName": "Sheeta", "questions": [question_body()],
            "answers": {"q_1": "The solution is x = 2, obtained by subtracting 3 "
                               "from both sides then dividing by 2."},
            "correctOptions": {}, **extra,
        }, headers=self.headers)


@pytest.fixture
def sheet(tmp_path, monkeypatch):
    from academicos.assessment import users as users_mod
    from academicos.curriculum import store as curriculum_store_mod
    from fastapi.testclient import TestClient

    monkeypatch.setenv("ACOS_PRINCIPAL_BOOTSTRAP_KEY", "test-bootstrap-key")
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr(audit_mod, "_INSTANCE", None)
    monkeypatch.setattr(users_mod, "_INSTANCE", None)
    monkeypatch.setattr(curriculum_store_mod, "_INSTANCE", None)
    with TestClient(app) as client:
        teacher = register_invited(client, "school_1", "integrity-t@example.com",
                                   name="Ana Teacher")
        headers = {"Authorization": f"Bearer {teacher['token']}"}
        created = client.post("/api/v1/assessments", json={
            "teacherId": teacher["user"]["id"], "schoolId": "school_1",
            "title": "Integrity", "subject": "Mathematics", "grade": 10,
            "chapterIds": [], "blueprint": blueprint_body(),
        }, headers=headers)
        assert created.status_code == 200, created.text
        s = Sheet(client, headers, teacher["user"]["id"], created.json()["id"],
                  "s_integrity", 0, tmp_path)
        r = s.evaluate()
        assert r.status_code == 200, r.text
        s.awarded = r.json()["totalAwarded"]
        yield s


# --------------------------------------------------------------------------- #
# finalized means locked
# --------------------------------------------------------------------------- #

def test_award_on_a_finalized_sheet_needs_a_reason(sheet):
    sheet.finalize()
    before = len(sheet.audit())

    refused = sheet.award(sheet.other_mark)
    assert refused.status_code == 409, refused.text
    assert "reason" in refused.json()["detail"]
    assert len(sheet.audit()) == before, "a refused change must not be logged as made"

    accepted = sheet.award(sheet.other_mark, reason="re-checked against the scheme")
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["updated"] == 1

    entries = sheet.audit()
    assert len(entries) == before + 1
    [entry] = [e for e in entries if e["action"] == "grade_awarded"]
    assert entry["actor"] == sheet.teacher_id
    assert entry["student_id"] == sheet.student_id
    assert entry["details"]["questionId"] == "q_1"
    assert entry["details"]["before"] == sheet.awarded
    assert entry["details"]["after"] == sheet.other_mark
    assert entry["details"]["reason"] == "re-checked against the scheme"
    assert entry["details"]["finalized"] is True
    assert entry["timestamp"]


def test_a_whitespace_reason_is_no_reason(sheet):
    sheet.finalize()
    assert sheet.award(sheet.other_mark, reason="   ").status_code == 409
    assert sheet.review(sheet.other_mark, reason="  ").status_code == 409


def test_review_on_a_finalized_sheet_needs_a_reason(sheet):
    sheet.finalize()
    before = len(sheet.audit())

    refused = sheet.review(sheet.other_mark)
    assert refused.status_code == 409, refused.text
    assert len(sheet.audit()) == before

    accepted = sheet.review(sheet.other_mark, reason="student showed working on p.2")
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["awardedMarks"] == sheet.other_mark

    [entry] = [e for e in sheet.audit() if e["action"] == "sheet_answer_reviewed"]
    assert entry["actor"] == sheet.teacher_id
    assert entry["details"]["before"] == sheet.awarded
    assert entry["details"]["after"] == sheet.other_mark
    assert entry["details"]["reason"] == "student showed working on p.2"
    assert entry["details"]["finalized"] is True


def test_re_evaluating_a_finalized_sheet_needs_a_reason(sheet):
    """evaluate_sheet replaces the whole sheet: the silent-overwrite path the
    audit's probe did not even need /award for."""
    sheet.finalize()
    refused = sheet.evaluate()
    assert refused.status_code == 409, refused.text

    accepted = sheet.evaluate(reason="answer booklet re-scanned")
    assert accepted.status_code == 200, accepted.text
    latest = [e for e in sheet.audit() if e["action"] == "sheet_evaluated"]
    assert any(e["details"].get("reason") == "answer booklet re-scanned"
               and e["details"].get("finalized") is True for e in latest)


def test_before_finalization_changes_are_audited_without_a_reason(sheet):
    r = sheet.review(sheet.other_mark)
    assert r.status_code == 200, r.text
    [entry] = [e for e in sheet.audit() if e["action"] == "sheet_answer_reviewed"]
    assert entry["actor"] == sheet.teacher_id
    assert entry["details"]["before"] == sheet.awarded
    assert entry["details"]["after"] == sheet.other_mark
    assert entry["details"]["finalized"] is False

    r = sheet.award(sheet.awarded)
    assert r.status_code == 200, r.text
    [award] = [e for e in sheet.audit() if e["action"] == "grade_awarded"]
    assert award["actor"] == sheet.teacher_id
    assert award["details"]["before"] == sheet.other_mark
    assert award["details"]["after"] == sheet.awarded


def test_a_scan_finalize_cannot_overwrite_a_finalized_sheet(sheet):
    """finalize_scan_session saves the scan's marks over the graded sheet for
    the same assessment/student. It has no reason field, so over a finalized
    sheet it is refused before anything (PDFs, graded store, mastery) is
    written; corrections go through review or award with a reason."""
    from academicos.assessment import mobile_scan

    sheet.finalize()
    created = sheet.client.post("/api/v1/scan/sessions", json={
        "assessmentId": sheet.aid, "studentId": sheet.student_id, "studentName": "S",
    }, headers=sheet.headers)
    assert created.status_code == 200, created.text
    session = mobile_scan.get_session(created.json()["id"])
    session.review = [mobile_scan.ReviewItem(
        question_id="q_1", display_number=1, stem="stem", max_marks=2,
        student_answer="answer", awarded_marks=0, verdict="blank", confidence=0.9,
        reasoning="", marking_points=[], ocr_warnings=[], needs_review=False,
        status="approved", teacher_marks=0,
    )]
    mobile_scan.save_session(session)

    r = sheet.client.post(f"/api/v1/scan/sessions/{session.id}/finalize",
                          headers=sheet.headers)
    assert r.status_code == 409, r.text
    assert mobile_scan.get_session(session.id).status != "finalized"


def test_evaluating_a_sheet_records_the_callers_id(sheet):
    [entry] = [e for e in sheet.audit() if e["action"] == "sheet_evaluated"]
    assert entry["actor"] == sheet.teacher_id


def test_finalize_records_the_callers_id(sheet):
    sheet.finalize()
    [entry] = [e for e in sheet.audit() if e["action"] == "sheet_reviewed"]
    assert entry["actor"] == sheet.teacher_id


# --------------------------------------------------------------------------- #
# the audit table itself
# --------------------------------------------------------------------------- #

def _log(tmp_path) -> AuditLog:
    return AuditLog(tmp_path / "audit.sqlite")


def test_raw_update_and_delete_on_the_audit_table_raise(tmp_path):
    log = _log(tmp_path)
    entry_id = log.append("grade_awarded", assessment_id="a1", actor="u1",
                          details={"before": 0, "after": 2})
    with pytest.raises(sqlite3.DatabaseError, match="append-only"):
        log.conn.execute("UPDATE audit_log SET actor='someone-else' WHERE id=?", (entry_id,))
    log.conn.rollback()
    with pytest.raises(sqlite3.DatabaseError, match="append-only"):
        log.conn.execute("DELETE FROM audit_log WHERE id=?", (entry_id,))
    log.conn.rollback()
    [row] = log.for_assessment("a1")
    assert row["actor"] == "u1"


def test_an_existing_database_gets_the_triggers_on_open(tmp_path):
    """A log created before this change has no triggers and no chain columns;
    opening it must add both, and its old rows must survive untouched."""
    path = tmp_path / "audit.sqlite"
    legacy = sqlite3.connect(str(path))
    legacy.executescript("""
        CREATE TABLE audit_log (
          id TEXT PRIMARY KEY, timestamp TEXT NOT NULL, action TEXT NOT NULL,
          assessment_id TEXT, student_id TEXT, actor TEXT,
          details TEXT NOT NULL DEFAULT '{}');
        INSERT INTO audit_log VALUES
          ('audit_old', '2026-01-01T00:00:00+00:00', 'sheet_evaluated', 'a1', 's1', NULL, '{}');
    """)
    legacy.commit()
    legacy.close()

    log = AuditLog(path)
    with pytest.raises(sqlite3.DatabaseError, match="append-only"):
        log.conn.execute("DELETE FROM audit_log WHERE id='audit_old'")
    log.conn.rollback()
    log.append("grade_awarded", assessment_id="a1", actor="u1")
    assert {r["id"] for r in log.for_assessment("a1")} >= {"audit_old"}
    assert log.verify_chain() is None


def test_appending_an_existing_id_fails(tmp_path):
    log = _log(tmp_path)
    log.append("grade_awarded", assessment_id="a1", actor="u1", entry_id="audit_fixed")
    with pytest.raises(DuplicateAuditEntry):
        log.append("grade_awarded", assessment_id="a1", actor="attacker",
                   entry_id="audit_fixed")
    [row] = log.for_assessment("a1")
    assert row["actor"] == "u1"


def test_verify_chain_passes_on_a_clean_log(tmp_path):
    log = _log(tmp_path)
    for i in range(5):
        log.append(f"op{i}", assessment_id="a1", actor="u1", details={"i": i})
    assert log.verify_chain() is None


def test_verify_chain_reports_the_edited_entry(tmp_path):
    log = _log(tmp_path)
    ids = [log.append(f"op{i}", assessment_id="a1", actor="u1",
                      details={"after": i}) for i in range(4)]
    # An attacker with write access to the file can drop the trigger; the
    # chain is what still tells on them.
    log.conn.execute("DROP TRIGGER audit_log_no_update")
    log.conn.execute("UPDATE audit_log SET details=? WHERE id=?",
                     ('{"after": 99}', ids[2]))
    log.conn.commit()

    broken = log.verify_chain()
    assert broken is not None
    assert broken["id"] == ids[2]
    assert broken["seq"] == 3


def test_verify_chain_reports_a_deleted_entry(tmp_path):
    log = _log(tmp_path)
    ids = [log.append(f"op{i}", assessment_id="a1") for i in range(4)]
    log.conn.execute("DROP TRIGGER audit_log_no_delete")
    log.conn.execute("DELETE FROM audit_log WHERE id=?", (ids[1],))
    log.conn.commit()

    broken = log.verify_chain()
    assert broken is not None
    assert broken["id"] == ids[2], "the entry after the hole is the first broken link"


# --------------------------------------------------------------------------- #
# the remote append is an insert
# --------------------------------------------------------------------------- #

class _Conflict(Exception):
    status = 409


class FakeRemoteAudit:
    """Shaped like SupabaseTable/PostgresTable, with a primary key on id and
    a unique seq -- the constraints docs/supabase-setup.sql declares."""

    enabled = True

    def __init__(self):
        self.rows: list[dict] = []
        self.upserts = 0

    def select(self, order=None, limit=None, gt=None, **eq):
        rows = [r for r in self.rows if all(r.get(k) == v for k, v in eq.items())]
        for col, floor in (gt or {}).items():
            rows = [r for r in rows if r.get(col) is not None and r[col] > floor]
        if order:
            col, _, direction = order.partition(".")
            rows.sort(key=lambda r: (r.get(col) is None, r.get(col)),
                      reverse=direction == "desc")
        return rows[:limit] if limit else rows

    def insert(self, row):
        from academicos.assessment.supabase_kv import SupabaseUnavailable
        if any(r["id"] == row["id"] or r["seq"] == row["seq"] for r in self.rows):
            raise SupabaseUnavailable(table="audit_log", op="insert", status=409,
                                      body="duplicate key value violates unique constraint")
        self.rows.append(dict(row))

    def upsert(self, row, on_conflict):
        self.upserts += 1
        raise AssertionError("the audit log must never upsert")


def test_remote_append_inserts_and_a_replayed_id_fails(tmp_path, monkeypatch):
    remote = FakeRemoteAudit()
    monkeypatch.setattr(audit_mod, "durable_table", lambda name: remote)
    log = _log(tmp_path)

    first = log.append("grade_awarded", assessment_id="a1", actor="u1",
                       entry_id="audit_replayed")
    assert first == "audit_replayed"
    with pytest.raises(DuplicateAuditEntry):
        log.append("grade_awarded", assessment_id="a1", actor="attacker",
                   entry_id="audit_replayed")

    assert remote.upserts == 0
    assert [r["actor"] for r in remote.rows] == ["u1"]
    # A replay is not an outage: it must not be quietly written to the local
    # fallback either.
    assert log.conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0] == 0


def test_remote_chain_links_and_verifies(tmp_path, monkeypatch):
    remote = FakeRemoteAudit()
    monkeypatch.setattr(audit_mod, "durable_table", lambda name: remote)
    log = _log(tmp_path)
    for i in range(3):
        log.append(f"op{i}", assessment_id="a1", actor="u1")
    assert [r["seq"] for r in remote.rows] == [1, 2, 3]
    assert remote.rows[1]["prev_hash"] == remote.rows[0]["entry_hash"]
    assert log.verify_chain() is None

    remote.rows[1]["actor"] = "someone-else"
    assert log.verify_chain()["id"] == remote.rows[1]["id"]
