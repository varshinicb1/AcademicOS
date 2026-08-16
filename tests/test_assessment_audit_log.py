"""Append-only audit log (assessment/audit_log.py).

Verify an appended entry is retrievable via for_assessment(), that the log is
append-only (no update/delete path exists in application code), and that
entries for different assessment_ids don't leak into each other's results.
SQLite-backed via tmp_path — never the real data root.
"""
from __future__ import annotations

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


def test_append_is_append_only_no_update_delete():
    # The point of this module: application code must never UPDATE or DELETE.
    for forbidden in ("update", "delete", "remove", "edit", "patch", "update_entry"):
        assert not hasattr(AuditLog, forbidden), f"AuditLog must not expose {forbidden!r}"


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