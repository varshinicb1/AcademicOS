"""Consent must fail closed, and its audit trail must not fail silently.

Two defects are pinned here, both of which reported success while being wrong:

  1. `ParentalConsentRecord.from_row` read a missing or empty status as
     GRANTED. A partial payload, a schema drift or a truncated write would grant
     permission to process a minor's data, and nothing would look wrong.
  2. Both consent routes wrote their audit record inside
     `except Exception: pass`, so the consent write returned 200 with an
     incomplete trail and no signal anywhere. CERT-In requires the trail.

Both are DPDP-relevant, which is why the assertions are about refusing rather
than about log text.
"""
from __future__ import annotations

import pathlib
import sqlite3
import sys

import pytest
from fastapi import HTTPException

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from academicos.assessment import consent_routes  # noqa: E402
from academicos.assessment.consent import (  # noqa: E402
    ConsentStore,
    ParentalConsentRecord,
)


def _row(**over):
    row = {
        "id": "c1",
        "school_id": "s1",
        "student_id": "st1",
        "guardian_name": "A Parent",
        "guardian_relationship": "parent",
        "method": "signed form",
        "status": "granted",
        "purpose": "assessment_and_grading",
        "notes": None,
        "recorded_by": "u1",
        "recorded_at": "2026-01-01T00:00:00Z",
        "revoked_at": None,
        "revoked_by": None,
    }
    row.update(over)
    return row


# --- the status must fail closed -----------------------------------------

def test_a_valid_status_is_read_through():
    assert ParentalConsentRecord.from_row(_row(status="granted")).status == "granted"
    assert ParentalConsentRecord.from_row(_row(status="revoked")).status == "revoked"


@pytest.mark.parametrize("bad", [None, "", "   ", "\t"])
def test_a_missing_or_empty_status_is_refused(bad):
    """The core fix. `row.get("status") or "granted"` returned granted here."""
    with pytest.raises(ValueError, match="no status"):
        ParentalConsentRecord.from_row(_row(status=bad))


def test_a_missing_status_key_is_refused_not_defaulted():
    row = _row()
    del row["status"]
    with pytest.raises(ValueError, match="no status"):
        ParentalConsentRecord.from_row(row)


def test_a_revoked_status_is_never_coerced_to_granted():
    """`or` fires on falsy, and a status of "0" or "false" must not read as yes."""
    for value in ("0", "false", "denied"):
        assert ParentalConsentRecord.from_row(_row(status=value)).status == value


def test_the_refusal_names_the_record():
    """A bare ValueError in a route handler is untraceable; name the record."""
    with pytest.raises(ValueError, match="c1"):
        ParentalConsentRecord.from_row(_row(id="c1", status=None))


# --- the store's connection must satisfy the AGENTS.md invariant ----------

def test_the_consent_store_sets_wal_and_busy_timeout(tmp_path):
    store = ConsentStore(tmp_path / "consent.sqlite")
    try:
        assert store.conn.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
        assert store.conn.execute("PRAGMA busy_timeout").fetchone()[0] == 60000
    finally:
        store.conn.close()


def test_the_consent_store_actually_works(tmp_path):
    """A pragma assertion on a broken store is not worth much."""
    store = ConsentStore(tmp_path / "consent.sqlite")
    try:
        rec = store.record_consent(
            school_id="s1", student_id="st1", guardian_name="A Parent",
            guardian_relationship="parent", method="signed form",
            recorded_by="u1",
        )
        assert rec.status == "granted"
        assert store.get_consent("s1", "st1") is not None
    finally:
        store.conn.close()


# --- the audit trail must fail loudly ------------------------------------

class _FailingAudit:
    def append(self, *_a, **_kw):
        raise sqlite3.OperationalError("disk I/O error")


class _OkAudit:
    def __init__(self):
        self.calls = []

    def append(self, action, **kw):
        self.calls.append({"action": action, **kw})


def test_a_missing_audit_store_refuses_rather_than_proceeding(monkeypatch):
    """Was `if audit:` -- a None store skipped the write entirely, silently."""
    monkeypatch.setattr(consent_routes, "_audit", None)
    monkeypatch.setattr(consent_routes, "get_audit_log",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("no store")))
    with pytest.raises(HTTPException) as exc:
        consent_routes._audit_or_refuse("x", actor_id="u1", consent_id="r1",
                                       student_id="st1", details={})
    assert exc.value.status_code == 503


def test_a_failing_audit_write_refuses_rather_than_reporting_success(monkeypatch):
    """Was `except Exception: pass` -- the route returned 200 on an incomplete trail."""
    monkeypatch.setattr(consent_routes, "_audit", _FailingAudit())
    with pytest.raises(HTTPException) as exc:
        consent_routes._audit_or_refuse("x", actor_id="u1", consent_id="r1",
                                       student_id="st1", details={})
    assert exc.value.status_code == 503
    assert "audit" in exc.value.detail.lower()


def test_a_working_audit_write_records_and_returns(monkeypatch):
    audit = _OkAudit()
    monkeypatch.setattr(consent_routes, "_audit", audit)
    consent_routes._audit_or_refuse("parental_consent_recorded", actor_id="u1",
                                   consent_id="r1", student_id="st1",
                                   details={"k": "v"})
    assert len(audit.calls) == 1
    assert audit.calls[0]["action"] == "parental_consent_recorded"
    assert audit.calls[0]["student_id"] == "st1"
    assert audit.calls[0]["actor"] == "u1"
    assert audit.calls[0]["details"]["consent_id"] == "r1"


def test_a_REAL_audit_log_accepts_the_call(tmp_path, monkeypatch):
    """The only test here that could have caught the `.record` bug.

    Every fake in this file implements whichever method the code happens to
    call, so a fake can never reveal that the real class lacks it. The consent
    routes called `audit.record(...)` for their entire life; `AuditLog` has only
    `append`. Real class, real call, real row asserted.
    """
    from academicos.assessment.audit_log import AuditLog

    audit = AuditLog(tmp_path / "audit.sqlite")
    monkeypatch.setattr(consent_routes, "_audit", audit)
    consent_routes._audit_or_refuse(
        "parental_consent_recorded", actor_id="u1", consent_id="c1",
        student_id="st1", details={"school_id": "s1"})

    rows = audit.for_action("parental_consent_recorded")
    assert len(rows) == 1, "the consent audit write produced no row"
    assert rows[0]["actor"] == "u1"
    assert rows[0]["student_id"] == "st1"


def test_no_silent_swallow_remains_in_the_consent_routes():
    """A source-level guard, in the style of the append-only store test.

    The failure mode is a future edit reintroducing `except Exception: pass`
    around an audit write, which no behavioural test would catch because the
    route would still return its normal response.
    """
    text = (REPO / "src" / "academicos" / "assessment"
            / "consent_routes.py").read_text(encoding="utf-8")
    assert "except Exception:\n            pass" not in text
    assert "except Exception:\n                pass" not in text
