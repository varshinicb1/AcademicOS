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

from _auth_helpers import grant_consent, register_invited
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
        # Grading needs recorded parental consent (authz.require_consent).
        grant_consent("school_1", "s_integrity", "s_integrity_2")
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
    assert broken["seq"] == 4, "seq 1 is the chain-start entry"


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
    assert [r["actor"] for r in remote.rows if r["id"] == "audit_replayed"] == ["u1"]
    assert [r["action"] for r in remote.rows] == [audit_mod.CHAIN_START_ACTION,
                                                  "grade_awarded"]
    # A replay is not an outage: it must not be quietly written to the local
    # fallback either.
    assert log.conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0] == 0


def test_remote_chain_links_and_verifies(tmp_path, monkeypatch):
    remote = FakeRemoteAudit()
    monkeypatch.setattr(audit_mod, "durable_table", lambda name: remote)
    log = _log(tmp_path)
    for i in range(3):
        log.append(f"op{i}", assessment_id="a1", actor="u1")
    # seq 1 is the chain-start entry the log writes before the first real one.
    assert [r["seq"] for r in remote.rows] == [1, 2, 3, 4]
    assert remote.rows[0]["action"] == audit_mod.CHAIN_START_ACTION
    assert remote.rows[2]["prev_hash"] == remote.rows[1]["entry_hash"]
    assert log.verify_chain() is None

    remote.rows[2]["actor"] = "someone-else"
    assert log.verify_chain()["id"] == remote.rows[2]["id"]


# --------------------------------------------------------------------------- #
# a row inserted outside the chain is a break, not a legacy row
# --------------------------------------------------------------------------- #

def _raw_insert(log: AuditLog, entry_id: str, timestamp: str, **cols) -> None:
    """What anyone who can INSERT can do: the triggers stop UPDATE and
    DELETE, not INSERT, and nothing makes a raw row carry chain fields."""
    log.conn.execute(
        "INSERT INTO audit_log (id, timestamp, action, assessment_id, student_id, "
        "actor, details) VALUES (?,?,?,?,?,?,?)",
        (entry_id, timestamp, cols.get("action", "sheet_reviewed"),
         cols.get("assessment_id", "a1"), cols.get("student_id", "s2"),
         cols.get("actor"), "{}"))
    log.conn.commit()


@pytest.mark.parametrize("timestamp", [
    "2099-01-01T00:00:00+00:00",   # written after the chain began
    "2001-01-01T00:00:00+00:00",   # backdated to look older than the chain
])
def test_verify_chain_reports_an_unchained_row_inserted_after_the_chain_began(
        tmp_path, timestamp):
    """Reproduced 2026-09-22 in review: two chained appends, then a raw
    INSERT of an unchained sheet_reviewed row. verify_chain() returned None,
    because every row without seq was skipped as pre-chain. A timestamp
    cannot tell the two apart, since the inserter picks the timestamp, so the
    first chained entry records which rows were there before it."""
    log = _log(tmp_path)
    log.append("grade_awarded", assessment_id="a1", actor="u1")
    log.append("grade_awarded", assessment_id="a1", actor="u1")
    _raw_insert(log, "audit_forged", timestamp)

    broken = log.verify_chain()
    assert broken is not None
    assert broken["id"] == "audit_forged"
    assert broken["seq"] is None


def _legacy_file(tmp_path, rows: list[tuple]):
    path = tmp_path / "audit.sqlite"
    legacy = sqlite3.connect(str(path))
    legacy.execute("""
        CREATE TABLE audit_log (
          id TEXT PRIMARY KEY, timestamp TEXT NOT NULL, action TEXT NOT NULL,
          assessment_id TEXT, student_id TEXT, actor TEXT,
          details TEXT NOT NULL DEFAULT '{}')""")
    legacy.executemany("INSERT INTO audit_log VALUES (?,?,?,?,?,?,?)", rows)
    legacy.commit()
    legacy.close()
    return path


_LEGACY_ROWS = [
    ("audit_old1", "2026-01-01T00:00:00+00:00", "sheet_evaluated", "a1", "s1", None, "{}"),
    ("audit_old2", "2026-01-02T00:00:00+00:00", "sheet_reviewed", "a1", "s1", None,
     '{"total": 4}'),
]


def test_pre_chain_rows_are_accepted_and_a_later_legacy_looking_row_is_not(tmp_path):
    log = AuditLog(_legacy_file(tmp_path, _LEGACY_ROWS))
    log.append("grade_awarded", assessment_id="a1", actor="u1")
    log.append("grade_awarded", assessment_id="a1", actor="u1")
    assert log.verify_chain() is None, "rows that predate the chain are not breaks"

    # Backdated to sit among the real legacy rows.
    _raw_insert(log, "audit_old3", "2026-01-01T12:00:00+00:00", student_id="s1")
    assert log.verify_chain()["id"] == "audit_old3"


def test_an_edited_pre_chain_row_is_reported(tmp_path):
    log = AuditLog(_legacy_file(tmp_path, _LEGACY_ROWS))
    log.append("grade_awarded", assessment_id="a1", actor="u1")
    log.conn.execute("DROP TRIGGER audit_log_no_update")
    log.conn.execute("UPDATE audit_log SET details='{\"total\": 9}' WHERE id='audit_old2'")
    log.conn.commit()
    broken = log.verify_chain()
    assert broken is not None
    assert broken["seq"] is None


def test_a_deleted_pre_chain_row_is_reported(tmp_path):
    log = AuditLog(_legacy_file(tmp_path, _LEGACY_ROWS))
    log.append("grade_awarded", assessment_id="a1", actor="u1")
    log.conn.execute("DROP TRIGGER audit_log_no_delete")
    log.conn.execute("DELETE FROM audit_log WHERE id='audit_old1'")
    log.conn.commit()
    assert log.verify_chain() is not None


# --------------------------------------------------------------------------- #
# the remote read is paged; a capped response is not an intact chain
# --------------------------------------------------------------------------- #

class CappedRemoteAudit(FakeRemoteAudit):
    """PostgREST returns at most max-rows (1000 by default) per response and
    says nothing when it cuts one short. This fake does the same at `cap`."""

    def __init__(self, cap: int):
        super().__init__()
        self.cap = cap

    def select(self, order=None, limit=None, gt=None, **eq):
        return super().select(order=order, limit=limit, gt=gt, **eq)[:self.cap]


def test_remote_verify_reads_past_the_response_cap(tmp_path, monkeypatch):
    remote = CappedRemoteAudit(cap=7)
    monkeypatch.setattr(audit_mod, "durable_table", lambda name: remote)
    log = _log(tmp_path)
    for i in range(23):
        log.append(f"op{i}", assessment_id="a1", actor="u1", details={"i": i})
    assert log.verify_chain() is None

    # Past the first capped page: an unpaged read never sees this row.
    victim = next(r for r in remote.rows if r["seq"] == 20)
    victim["actor"] = "someone-else"
    assert log.verify_chain()["id"] == victim["id"]


def test_remote_verify_sees_a_raw_insert_past_the_cap(tmp_path, monkeypatch):
    remote = CappedRemoteAudit(cap=5)
    monkeypatch.setattr(audit_mod, "durable_table", lambda name: remote)
    log = _log(tmp_path)
    for i in range(12):
        log.append(f"op{i}", assessment_id="a1", actor="u1")
    remote.rows.append({"id": "zzz_forged", "timestamp": "2001-01-01T00:00:00+00:00",
                        "action": "sheet_reviewed", "assessment_id": "a1",
                        "student_id": "s2", "actor": None, "details": {},
                        "seq": None, "prev_hash": None, "entry_hash": None})
    assert log.verify_chain()["id"] == "zzz_forged"


def test_remote_pre_chain_rows_are_accepted(tmp_path, monkeypatch):
    remote = CappedRemoteAudit(cap=3)
    for i in range(5):
        remote.rows.append({"id": f"audit_legacy{i}",
                            "timestamp": f"2026-01-0{i + 1}T00:00:00+00:00",
                            "action": "sheet_evaluated", "assessment_id": "a1",
                            "student_id": "s1", "actor": None, "details": {"i": i},
                            "seq": None, "prev_hash": None, "entry_hash": None})
    monkeypatch.setattr(audit_mod, "durable_table", lambda name: remote)
    log = _log(tmp_path)
    for i in range(4):
        log.append(f"op{i}", assessment_id="a1", actor="u1")
    assert log.verify_chain() is None


# --------------------------------------------------------------------------- #
# losing the seq race is a failed append, not a local-only entry
# --------------------------------------------------------------------------- #

class RacingRemoteAudit(FakeRemoteAudit):
    """Another writer takes the seq this one read as next, `losses` times:
    each of those inserts finds a rival row already at its seq."""

    def __init__(self, losses: int, fail_id_lookup: bool = False):
        super().__init__()
        self.losses = losses
        self.fail_id_lookup = fail_id_lookup
        self.inserts = 0

    def insert(self, row):
        self.inserts += 1
        if self.losses > 0:
            self.losses -= 1
            rival = dict(row, id=f"audit_rival{self.inserts}", actor="rival")
            rival["entry_hash"] = audit_mod._entry_hash(rival)
            self.rows.append(rival)
        super().insert(row)

    def select(self, order=None, limit=None, gt=None, **eq):
        if self.fail_id_lookup and "id" in eq:
            from academicos.assessment.supabase_kv import SupabaseUnavailable
            raise SupabaseUnavailable(table="audit_log", op="select", status=500)
        return super().select(order=order, limit=limit, gt=gt, **eq)


def _local_count(log: AuditLog) -> int:
    return log.conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]


def test_a_lost_seq_race_is_retried(tmp_path, monkeypatch):
    remote = RacingRemoteAudit(losses=2)
    monkeypatch.setattr(audit_mod, "durable_table", lambda name: remote)
    log = _log(tmp_path)
    entry_id = log.append("grade_awarded", assessment_id="a1", actor="u1")

    assert remote.inserts == 3
    [mine] = [r for r in remote.rows if r["id"] == entry_id]
    assert mine["seq"] == 3, "the retry re-reads the head and takes the next seq"
    assert log.verify_chain() is None
    assert _local_count(log) == 0


def test_exhausting_the_seq_race_fails_the_append(tmp_path, monkeypatch):
    remote = RacingRemoteAudit(losses=audit_mod._SEQ_RACE_RETRIES)
    monkeypatch.setattr(audit_mod, "_sleep", lambda _s: None)
    monkeypatch.setattr(audit_mod, "durable_table", lambda name: remote)
    log = _log(tmp_path)
    with pytest.raises(audit_mod.AuditAppendFailed):
        log.append("grade_awarded", assessment_id="a1", actor="u1")
    assert remote.inserts == audit_mod._SEQ_RACE_RETRIES
    # The remote is reachable; this is not an outage, so the entry must not
    # land on a disk Render wipes on restart.
    assert _local_count(log) == 0


def test_a_failed_id_lookup_after_a_conflict_fails_the_append(tmp_path, monkeypatch):
    # The first loss is on the chain-start entry, which re-reads the head
    # without an id lookup; the second is on the real entry.
    remote = RacingRemoteAudit(losses=2, fail_id_lookup=True)
    monkeypatch.setattr(audit_mod, "durable_table", lambda name: remote)
    log = _log(tmp_path)
    with pytest.raises(audit_mod.AuditAppendFailed):
        log.append("grade_awarded", assessment_id="a1", actor="u1")
    assert _local_count(log) == 0


class ThreadedRemoteAudit(FakeRemoteAudit):
    """FakeRemoteAudit as a real server behaves under concurrent requests:
    each call is atomic (the unique checks and the write happen together), and
    a network round trip separates the head read from the insert, which is
    the window two appenders race in."""

    def __init__(self):
        super().__init__()
        import threading
        self._server = threading.Lock()

    def select(self, order=None, limit=None, gt=None, **eq):
        import time
        time.sleep(0.002)
        with self._server:
            return [dict(r) for r in super().select(order=order, limit=limit, gt=gt, **eq)]

    def insert(self, row):
        import time
        time.sleep(0.002)
        with self._server:
            super().insert(row)


def test_concurrent_pii_reads_on_one_instance_all_append(tmp_path, monkeypatch):
    """The scan review screen loads every page image of a session at once,
    and each GET is a record_pii_read. Reproduced at e8315e0: 16 concurrent
    remote appends each read the same head, one won per round, and the rest
    ran out of their 5 retries with AuditAppendFailed, a 503 and a broken
    image. Appends from one process are now serialised, so none of them
    races another."""
    from concurrent.futures import ThreadPoolExecutor
    import threading
    remote = ThreadedRemoteAudit()
    monkeypatch.setattr(audit_mod, "durable_table", lambda name: remote)
    log = _log(tmp_path)
    n = 16
    start = threading.Barrier(n)

    def read(page: int) -> str:
        start.wait()
        return audit_mod.record_pii_read(log, actor="t1", what="scan_page_image",
                                         student_id="s1", assessment_id="a1", page=page)

    with ThreadPoolExecutor(max_workers=n) as pool:
        ids = list(pool.map(read, range(n)))

    assert len(set(ids)) == n
    seqs = sorted(r["seq"] for r in remote.rows)
    assert seqs == list(range(1, n + 2)), "contiguous: the chain start, then one per read"
    assert log.verify_chain() is None
    assert _local_count(log) == 0


def test_a_lost_race_backs_off_with_jitter_before_retrying(tmp_path, monkeypatch):
    """Two instances cannot share a lock, so between them a lost race is
    still possible. The loser waits a random, growing time before re-reading
    the head, so two losers do not collide again in lockstep."""
    slept: list[float] = []
    monkeypatch.setattr(audit_mod, "_sleep", slept.append)
    remote = RacingRemoteAudit(losses=3)
    monkeypatch.setattr(audit_mod, "durable_table", lambda name: remote)
    log = _log(tmp_path)
    log.append("grade_awarded", assessment_id="a1", actor="u1")

    assert len(slept) == 3, "one wait per lost race, none before the first try"
    for attempt, delay in enumerate(slept):
        ceiling = min(audit_mod._SEQ_RACE_BACKOFF_CAP,
                      audit_mod._SEQ_RACE_BACKOFF_BASE * 2 ** attempt)
        assert 0 <= delay <= ceiling


def test_a_failed_audit_append_is_a_503_and_saves_no_grade(sheet, monkeypatch):
    log = audit_mod.get_audit_log(sheet.data_root)

    def refuse(*_a, **_k):
        raise audit_mod.AuditAppendFailed(table="audit_log", op="insert",
                                          body="lost the seq race 5 times")
    monkeypatch.setattr(log, "append", refuse)

    r = sheet.award(sheet.other_mark)
    assert r.status_code == 503, r.text
    assert _grid_mark(sheet) == sheet.awarded


# --------------------------------------------------------------------------- #
# a remote table that answers 4xx is misconfigured, not down
# --------------------------------------------------------------------------- #

class RefusingRemoteAudit(FakeRemoteAudit):
    """The remote table answers, but refuses the insert: 400 is PostgREST's
    PGRST204 (a chain column the manual SQL has not added yet), 401/403 is RLS
    or a revoked privilege, 404 a missing table; None is no connection at all
    and 5xx the server itself failing."""

    def __init__(self, status):
        super().__init__()
        self.status = status

    def insert(self, row):
        from academicos.assessment.supabase_kv import SupabaseUnavailable
        raise SupabaseUnavailable(table="audit_log", op="insert", status=self.status,
                                  body="PGRST204 Could not find the 'seq' column")


@pytest.mark.parametrize("status", [400, 401, 403, 404])
def test_a_4xx_from_the_remote_insert_fails_the_append(tmp_path, monkeypatch, status):
    """A 4xx is a configuration error. On Render the local file is wiped on
    restart, so a `sheet_reviewed` entry written there instead would vanish
    and quietly unlock the sheet."""
    remote = RefusingRemoteAudit(status)
    monkeypatch.setattr(audit_mod, "durable_table", lambda name: remote)
    log = _log(tmp_path)
    with pytest.raises(audit_mod.AuditAppendFailed):
        log.append("sheet_reviewed", assessment_id="a1", student_id="s1", actor="u1")
    assert _local_count(log) == 0


@pytest.mark.parametrize("status", [None, 408, 429, 500, 503])
def test_an_outage_still_falls_back_to_local_disk(tmp_path, monkeypatch, status):
    remote = RefusingRemoteAudit(status)
    monkeypatch.setattr(audit_mod, "durable_table", lambda name: remote)
    log = _log(tmp_path)
    log.append("grade_awarded", assessment_id="a1", actor="u1")
    assert _local_count(log) == 2, "the chain-start entry and the real one"


class OperationalError(Exception):
    """Named like psycopg's: a refused connection, an admin shutdown, a pool
    timeout. psycopg raises it for SQLSTATE classes 08/53/57/58, or with no
    SQLSTATE at all when the server was never reached."""
    sqlstate = None


class UndefinedColumn(Exception):
    """Shaped like psycopg.errors.UndefinedColumn (a ProgrammingError): the
    Cloud SQL schema is behind the code."""
    sqlstate = "42703"


class CloudSqlRemoteAudit(FakeRemoteAudit):
    def __init__(self, cause):
        super().__init__()
        self.cause = cause

    def insert(self, row):
        from academicos.assessment.postgres_kv import PostgresUnavailable
        raise PostgresUnavailable(table="audit_log", op="insert",
                                  body=str(self.cause), cause=self.cause) from self.cause


def test_a_cloud_sql_schema_error_fails_the_append(tmp_path, monkeypatch):
    remote = CloudSqlRemoteAudit(UndefinedColumn('column "seq" does not exist'))
    monkeypatch.setattr(audit_mod, "durable_table", lambda name: remote)
    log = _log(tmp_path)
    with pytest.raises(audit_mod.AuditAppendFailed):
        log.append("grade_awarded", assessment_id="a1", actor="u1")
    assert _local_count(log) == 0


def test_a_cloud_sql_connection_error_falls_back(tmp_path, monkeypatch):
    remote = CloudSqlRemoteAudit(OperationalError("connection refused"))
    monkeypatch.setattr(audit_mod, "durable_table", lambda name: remote)
    log = _log(tmp_path)
    log.append("grade_awarded", assessment_id="a1", actor="u1")
    assert _local_count(log) == 2


def _grid_mark(sheet, student_id=None) -> int:
    """The mark stored for q_1, read from the graded store itself.

    Not through GET .../question/q_1: since Task 305 that read writes a
    pii_read audit entry before it answers (docs/compliance.md box 2), so
    with the audit log deliberately broken it is refused with 503 as well.
    These tests are about what a refused WRITE left in the store."""
    from academicos.assessment import pillar_routes

    graded = pillar_routes._require_graded().for_assessment(sheet.aid)
    [evaluation] = [ev for q, ev in graded[student_id or sheet.student_id] if q.id == "q_1"]
    return int(evaluation.awarded_marks)


def test_a_400_from_the_remote_insert_is_a_503_and_saves_no_grade(sheet):
    log = audit_mod.get_audit_log(sheet.data_root)
    log._remote = RefusingRemoteAudit(400)
    local_before = _local_count(log)

    r = sheet.award(sheet.other_mark)
    assert r.status_code == 503, r.text
    assert _grid_mark(sheet) == sheet.awarded
    assert _local_count(log) == local_before


# --------------------------------------------------------------------------- #
# the lock read fails closed
# --------------------------------------------------------------------------- #

class UnreadableRemoteAudit(FakeRemoteAudit):
    def select(self, order=None, limit=None, gt=None, **eq):
        from academicos.assessment.supabase_kv import SupabaseUnavailable
        raise SupabaseUnavailable(table="audit_log", op="select",
                                  body="connection reset by peer")


def test_an_unreadable_lock_is_a_503_and_saves_no_grade(sheet):
    """grade_lock decides 'finalized' from has_entry. If the remote log cannot
    be read, the local file alone could say 'not finalized' for a sheet that
    is, so the write is refused instead."""
    log = audit_mod.get_audit_log(sheet.data_root)
    log._remote = UnreadableRemoteAudit()

    r = sheet.award(sheet.other_mark)
    assert r.status_code == 503, r.text
    assert _grid_mark(sheet) == sheet.awarded
    assert not [e for e in sheet.audit() if e["action"] == "grade_awarded"]


# --------------------------------------------------------------------------- #
# finalize: the lock entry is written before mastery moves
# --------------------------------------------------------------------------- #

def test_a_failed_finalize_entry_leaves_mastery_untouched(sheet, monkeypatch):
    """If the finalize entry cannot be written, the sheet is not locked, and
    the client's retry must not fold the same evaluations into mastery twice."""
    from academicos.assessment import pillar_routes

    recorded: list[str] = []
    monkeypatch.setattr(pillar_routes._knowledge, "record_sheet",
                        lambda student_id, graded, source: recorded.append(student_id))
    log = audit_mod.get_audit_log(sheet.data_root)
    real_append = log.append

    def refuse_finalize(action, **kw):
        if action != "sheet_reviewed":
            return real_append(action, **kw)
        raise audit_mod.AuditAppendFailed(table="audit_log", op="insert",
                                          body="lost the seq race 5 times")
    monkeypatch.setattr(log, "append", refuse_finalize)

    r = sheet.client.post(
        f"/api/v1/evaluations/sheet/{sheet.aid}/{sheet.student_id}/finalize",
        json={}, headers=sheet.headers)
    assert r.status_code == 503, r.text
    assert recorded == []

    monkeypatch.setattr(log, "append", real_append)
    sheet.finalize()
    assert recorded == [sheet.student_id]


# --------------------------------------------------------------------------- #
# POST /evaluations/answer re-grades one answer
# --------------------------------------------------------------------------- #

def _evaluate_one(sheet, **extra):
    return sheet.client.post("/api/v1/evaluations/answer", json={
        "assessmentId": sheet.aid, "studentId": sheet.student_id,
        "question": question_body(), "studentAnswer": "x = 2", **extra,
    }, headers=sheet.headers)


def test_evaluate_one_is_audited_with_before_and_after(sheet):
    r = _evaluate_one(sheet)
    assert r.status_code == 200, r.text
    [entry] = [e for e in sheet.audit() if e["action"] == "answer_evaluated"]
    assert entry["actor"] == sheet.teacher_id
    assert entry["student_id"] == sheet.student_id
    assert entry["details"]["questionId"] == "q_1"
    assert entry["details"]["before"] == sheet.awarded
    assert entry["details"]["after"] == r.json()["awardedMarks"]
    assert entry["details"]["finalized"] is False
    assert "reason" not in entry["details"]


def test_evaluate_one_on_a_finalized_sheet_needs_a_reason(sheet):
    sheet.finalize()
    before = len(sheet.audit())

    refused = _evaluate_one(sheet)
    assert refused.status_code == 409, refused.text
    assert "reason" in refused.json()["detail"]
    assert len(sheet.audit()) == before
    assert _grid_mark(sheet) == sheet.awarded

    accepted = _evaluate_one(sheet, reason="answer re-read from the original booklet")
    assert accepted.status_code == 200, accepted.text
    [entry] = [e for e in sheet.audit() if e["action"] == "answer_evaluated"]
    assert entry["actor"] == sheet.teacher_id
    assert entry["details"]["before"] == sheet.awarded
    assert entry["details"]["after"] == accepted.json()["awardedMarks"]
    assert entry["details"]["reason"] == "answer re-read from the original booklet"
    assert entry["details"]["finalized"] is True


# --------------------------------------------------------------------------- #
# a bulk award is refused whole
# --------------------------------------------------------------------------- #

def test_a_bulk_award_touching_one_finalized_sheet_is_refused_whole(sheet):
    """Two targets, one finalized, no reason: 409, and neither sheet is saved
    or logged, not even the unlocked one (award_across_students checks every
    lock before the first write). The unlocked student is listed first, so a
    route that wrote as it went would already have saved it."""
    other = "s_integrity_2"
    r = sheet.client.post("/api/v1/evaluations/sheet", json={
        "assessmentId": sheet.aid, "studentId": other, "studentName": "Other",
        "questions": [question_body()],
        "answers": {"q_1": "The solution is x = 2, obtained by subtracting 3 "
                           "from both sides then dividing by 2."},
        "correctOptions": {},
    }, headers=sheet.headers)
    assert r.status_code == 200, r.text
    other_mark = r.json()["totalAwarded"]
    assert other_mark == sheet.awarded, "same answer, same mark: both targets change"
    sheet.finalize()

    refused = sheet.award(sheet.other_mark, studentIds=[other, sheet.student_id])
    assert refused.status_code == 409, refused.text
    assert _grid_mark(sheet) == sheet.awarded
    assert _grid_mark(sheet, other) == other_mark
    all_entries = audit_mod.get_audit_log(sheet.data_root).for_action("grade_awarded")
    assert all_entries == []


# --------------------------------------------------------------------------- #
# a decision that changes no mark needs no reason, and is still logged
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("action", ["approve", "edit"])
def test_a_no_change_review_on_a_finalized_sheet_needs_no_reason(sheet, action):
    sheet.finalize()
    body = {"action": action}
    if action == "edit":
        body["marks"] = sheet.awarded
    r = sheet.client.post(
        f"/api/v1/evaluations/sheet/{sheet.aid}/{sheet.student_id}/review/q_1",
        json=body, headers=sheet.headers)
    assert r.status_code == 200, r.text
    assert r.json()["awardedMarks"] == sheet.awarded

    [entry] = [e for e in sheet.audit() if e["action"] == "sheet_answer_reviewed"]
    assert entry["actor"] == sheet.teacher_id
    assert entry["details"]["before"] == sheet.awarded
    assert entry["details"]["after"] == sheet.awarded
    assert entry["details"]["finalized"] is True
    assert entry["details"]["decision"] == action
    assert "reason" not in entry["details"]


# --------------------------------------------------------------------------- #
# re-finalizing never counts a sheet into mastery twice (Task 306)
# --------------------------------------------------------------------------- #
#
# Task 303 made a finalized sheet correctable with a reason. The obvious
# teacher workflow is then "correct, press Finalize again", and before this
# fix every Finalize appended the whole sheet to the student's learner model
# again: two presses, two copies of every answer in mastery. These tests read
# the stored learner model, not a call count.

def _sheet_answers(sheet) -> list[tuple[str, float]]:
    """Every answer interaction on the student's stored learner model."""
    from academicos.assessment import pillar_routes
    model = pillar_routes._knowledge.load(sheet.student_id)
    return [(i.concept_id, i.outcome)
            for state in model.concepts.values() for i in state.history
            if i.kind == "answer"]


def _finalize_entries(sheet) -> list[dict]:
    return [e for e in sheet.audit() if e["action"] == "sheet_reviewed"]


def _post_finalize(sheet):
    return sheet.client.post(
        f"/api/v1/evaluations/sheet/{sheet.aid}/{sheet.student_id}/finalize",
        json={}, headers=sheet.headers)


def test_finalizing_twice_counts_the_sheet_into_mastery_once(sheet):
    from academicos.assessment import pillar_routes

    sheet.finalize()
    once = _sheet_answers(sheet)
    assert once == [("ch1", round(sheet.awarded / 2, 4))]
    stored_after_first = pillar_routes._knowledge.load(sheet.student_id).updated_at

    again = _post_finalize(sheet)
    assert again.status_code == 200, again.text
    assert again.json()["totalAwarded"] == sheet.awarded
    assert _sheet_answers(sheet) == once
    # Nothing changed, so nothing was written: not the learner model, and not
    # a second finalize entry.
    assert pillar_routes._knowledge.load(sheet.student_id).updated_at == stored_after_first
    assert len(_finalize_entries(sheet)) == 1


def test_re_finalizing_after_a_correction_replaces_the_sheets_contribution(sheet):
    from academicos.assessment import pillar_routes

    sheet.finalize()
    corrected = sheet.review(sheet.other_mark, reason="re-checked against the scheme")
    assert corrected.status_code == 200, corrected.text

    again = _post_finalize(sheet)
    assert again.status_code == 200, again.text
    assert again.json()["totalAwarded"] == sheet.other_mark

    # The corrected mark, once. The first finalize's answer is gone, not kept
    # alongside it.
    assert _sheet_answers(sheet) == [("ch1", round(sheet.other_mark / 2, 4))]
    state = pillar_routes._knowledge.load(sheet.student_id).concepts["ch1"]
    assert state.attempts == 1
    assert state.correct == (1 if sheet.other_mark / 2 >= 0.5 else 0)
    [view] = pillar_routes._knowledge.mastery(sheet.student_id)
    assert view.evidence_count == 1

    entries = _finalize_entries(sheet)
    assert len(entries) == 2, "a re-finalize that changed mastery is audited"
    assert sorted(e["details"]["refinalized"] for e in entries) == [False, True]


def test_other_evidence_survives_a_re_finalize(sheet):
    """Replacing the sheet's contribution removes only the sheet's own
    interactions: practice and other sheets on the same concept stay."""
    from academicos.assessment import pillar_routes

    q = pillar_routes._require_graded().get(sheet.aid, sheet.student_id)
    pillar_routes._knowledge.record_evaluations(sheet.student_id, q)  # e.g. practice
    sheet.finalize()
    assert len(_sheet_answers(sheet)) == 2

    sheet.review(sheet.other_mark, reason="re-checked")
    sheet.finalize()
    assert sorted(_sheet_answers(sheet)) == sorted([
        ("ch1", round(sheet.awarded / 2, 4)),      # the untagged practice answer
        ("ch1", round(sheet.other_mark / 2, 4)),   # the sheet, corrected, once
    ])


def test_a_retry_after_mastery_failed_to_save_records_the_sheet_once(sheet, monkeypatch):
    """The finalize entry is written before mastery moves (f799073). If the
    mastery write then fails, the sheet is locked but uncounted, and the retry
    must count it -- once."""
    from academicos.assessment import pillar_routes
    from academicos.assessment.supabase_kv import SupabaseUnavailable

    real_save = pillar_routes._knowledge.save

    def down(model):
        raise SupabaseUnavailable(table="learner_models", op="upsert", status=503,
                                  body="unavailable")
    monkeypatch.setattr(pillar_routes._knowledge, "save", down)
    failed = _post_finalize(sheet)
    assert failed.status_code == 503, failed.text
    assert _sheet_answers(sheet) == []

    monkeypatch.setattr(pillar_routes._knowledge, "save", real_save)
    sheet.finalize()
    assert _sheet_answers(sheet) == [("ch1", round(sheet.awarded / 2, 4))]
    sheet.finalize()
    assert _sheet_answers(sheet) == [("ch1", round(sheet.awarded / 2, 4))]


def test_a_sheet_finalized_before_the_fix_is_not_re_finalized_blind(sheet):
    """A sheet finalized before this fix put untagged interactions into the
    learner model, which cannot be told apart from practice. Re-finalizing it
    would add the sheet a second time, so it is refused (fail closed)."""
    from academicos.assessment import pillar_routes

    graded = pillar_routes._require_graded().get(sheet.aid, sheet.student_id)
    audit_mod.get_audit_log(sheet.data_root).append(
        "sheet_reviewed", assessment_id=sheet.aid, student_id=sheet.student_id,
        actor=sheet.teacher_id, details={"totalAwarded": sheet.awarded})
    pillar_routes._knowledge.record_evaluations(sheet.student_id, graded)
    before = _sheet_answers(sheet)

    r = _post_finalize(sheet)
    assert r.status_code == 409, r.text
    assert "before" in r.json()["detail"]
    assert _sheet_answers(sheet) == before
    assert len(_finalize_entries(sheet)) == 1


def test_a_scan_finalized_sheet_can_be_corrected_and_re_finalized(sheet, monkeypatch):
    """finalize_scan_session writes the same finalize entry and mastery tag,
    so a scan-finalized sheet corrected with a reason re-finalizes cleanly
    instead of being refused as a pre-fix sheet."""
    from academicos.assessment import mobile_routes, mobile_scan, pillar_routes

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
    # The session has no captured pages and q_1 is not in the scan's question
    # pool. Neither matters to what is under test (the finalize entry and the
    # mastery tag), so the PDF exports and the pool lookup are stubbed.
    [(q1, _ev)] = pillar_routes._require_graded().get(sheet.aid, sheet.student_id)
    monkeypatch.setattr(mobile_routes, "_questions_by_id", lambda *a: {"q_1": q1})
    monkeypatch.setattr(mobile_scan, "export_raw_booklet_pdf", lambda *a, **k: None)
    monkeypatch.setattr(mobile_scan, "export_corrected_pdf", lambda *a, **k: None)

    r = sheet.client.post(f"/api/v1/scan/sessions/{session.id}/finalize",
                          headers=sheet.headers)
    assert r.status_code == 200, r.text
    assert _sheet_answers(sheet) == [("ch1", 0.0)]

    fixed = sheet.review(2, reason="the scan missed the second line")
    assert fixed.status_code == 200, fixed.text
    again = _post_finalize(sheet)
    assert again.status_code == 200, again.text
    assert _sheet_answers(sheet) == [("ch1", 1.0)]
