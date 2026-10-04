"""Append-only audit log (assessment/audit_log.py).

Verify an appended entry is retrievable via for_assessment(), that the log is
append-only (the database itself refuses UPDATE and DELETE), and that
entries for different assessment_ids don't leak into each other's results.
SQLite-backed via tmp_path — never the real data root.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.assessment import audit_log
from academicos.assessment.audit_log import AuditLog


def _log(tmp_path: Path) -> AuditLog:
    return AuditLog(tmp_path / "audit.sqlite")


def test_append_and_retrieve(tmp_path):
    log = _log(tmp_path)
    entry_id = log.append("grade.updated", assessment_id="a1", student_id="s1",
                          actor="teacher@school.org",
                          details={"before": 2, "after": 4})
    rows = log.for_assessment("a1")
    assert len(rows) == 1
    r = rows[0]
    assert r["id"] == entry_id
    assert r["action"] == "grade.updated"
    assert r["assessment_id"] == "a1"
    assert r["student_id"] == "s1"
    assert r["actor"] == "teacher@school.org"
    assert r["details"] == {"before": 2, "after": 4}
    assert r["timestamp"]


def test_the_database_refuses_update_and_delete(tmp_path):
    """Behavioural, not by name. The test here used to check only that
    AuditLog had no method called update or delete. The 2026-09-21 audit
    (item 8.5) then ran a raw UPDATE and a raw DELETE on the same file and
    each returned rowcount 1. Now the file's own triggers refuse both, from any
    connection, and the row is unchanged afterwards."""
    log = _log(tmp_path)
    entry_id = log.append("grade.updated", assessment_id="a1", actor="teacher_1",
                          details={"before": 2, "after": 4})

    other = sqlite3.connect(str(tmp_path / "audit.sqlite"))
    try:
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            other.execute("UPDATE audit_log SET actor='x', details='{}' WHERE id=?",
                          (entry_id,))
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            other.execute("DELETE FROM audit_log WHERE id=?", (entry_id,))
    finally:
        other.close()

    [row] = log.for_assessment("a1")
    assert row["actor"] == "teacher_1"
    assert row["details"] == {"before": 2, "after": 4}
    assert log.verify_chain() is None


def test_assessment_ids_do_not_leak(tmp_path):
    log = _log(tmp_path)
    log.append("evaluate", assessment_id="a1", student_id="s1", details={"score": 4})
    log.append("evaluate", assessment_id="a2", student_id="s2", details={"score": 2})
    log.append("export", assessment_id="a1", details={"fmt": "pdf"})

    a1 = log.for_assessment("a1")
    a2 = log.for_assessment("a2")
    assert [r["assessment_id"] for r in a1] == ["a1", "a1"]
    assert [r["assessment_id"] for r in a2] == ["a2"]
    assert len(a1) == 2
    assert len(a2) == 1


def test_entry_without_assessment_id_is_never_returned(tmp_path):
    log = _log(tmp_path)
    log.append("evaluate", assessment_id="a1")
    log.append("system.boot", assessment_id=None, details={"note": "no assessment"})
    rows = log.for_assessment("a1")
    assert len(rows) == 1
    assert all(r["assessment_id"] == "a1" for r in rows)


def test_details_default_to_empty_dict(tmp_path):
    log = _log(tmp_path)
    entry_id = log.append("evaluate", assessment_id="a1")
    r = log.for_assessment("a1")[0]
    assert r["id"] == entry_id
    assert r["details"] == {}


def test_timestamp_order_descending(tmp_path):
    log = _log(tmp_path)
    log.append("first", assessment_id="a")
    log.append("second", assessment_id="a")
    rows = log.for_assessment("a")
    assert len(rows) == 2
    stamps = [r["timestamp"] for r in rows]
    assert stamps == sorted(stamps, reverse=True)


def test_multiple_entries_retained_in_order(tmp_path):
    log = _log(tmp_path)
    ids = {log.append(f"op{i}", assessment_id="a") for i in range(5)}
    rows = log.for_assessment("a")
    assert {r["id"] for r in rows} == ids
    assert {r["action"] for r in rows} == {f"op{i}" for i in range(5)}


def test_get_audit_log_uses_data_root(tmp_path, monkeypatch):
    monkeypatch.setattr(audit_log, "_INSTANCE", None)
    log = audit_log.get_audit_log(tmp_path)
    assert isinstance(log, AuditLog)
    db = tmp_path / "audit" / "audit_log.sqlite"
    assert db.exists()
    entry_id = log.append("evaluate", assessment_id="a1")
    assert log.for_assessment("a1")[0]["id"] == entry_id

def test_concurrent_reads_and_appends_do_not_break_the_connection(tmp_path):
    """Stress test 2026-10-04: at 50 users, 5 of 564 term reports answered 500 -- for_action read the
    shared sqlite3 connection without its lock while another request used it ("bad parameter or other
    API misuse", or an IndexError mid-row)."""
    import threading
    from academicos.assessment.audit_log import AuditLog

    log = AuditLog(tmp_path / "audit.sqlite")
    for i in range(50):
        log.append("paper_generated", assessment_id=f"a{i % 5}", actor="t1", details={"i": i})
    errors = []

    def reader():
        try:
            for _ in range(60):
                assert len(log.for_action("paper_generated")) >= 50
                log.for_assessment("a1")
        except Exception as e:  # noqa: BLE001 - recorded and asserted below
            errors.append(repr(e))

    def writer():
        try:
            for i in range(40):
                log.append("paper_generated", assessment_id="a9", actor="t2", details={"w": i})
        except Exception as e:  # noqa: BLE001
            errors.append(repr(e))

    threads = [threading.Thread(target=reader) for _ in range(8)] + [threading.Thread(target=writer) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == [], errors[:3]
