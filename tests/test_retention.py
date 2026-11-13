"""Retention periods enforced by the daily job (R-A7, NFR-1;
operations/retention.py): old data purged, young data kept, other schools
untouched, an audit entry per school, nothing deleted without a written
period, and the audit log kept at every age (CERT-In: 180 days minimum)."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from academicos.assessment.audit_log import AuditLog
from academicos.assessment.users import UserStore
from academicos.operations import retention
from academicos.operations.store import get_operations_store

NOW = datetime.now(timezone.utc)


def _ago(**kw) -> str:
    return (NOW - timedelta(**kw)).isoformat()


@pytest.fixture
def s(tmp_path, monkeypatch):
    monkeypatch.delenv(retention.INVITE_DAYS_ENV, raising=False)
    users = UserStore(tmp_path / "users.sqlite")
    ops = get_operations_store(tmp_path)
    audit = AuditLog(tmp_path / "audit" / "audit_log.sqlite")
    made = {}
    for school in ("school_a", "school_b"):
        for who in ("old", "young"):
            u = users._insert_user(user_id=f"{school}-{who}", school_id=school, name=who,
                                   email=f"{who}@{school}.example", password="pw-long-enough", role="student")
            made[(school, who)] = u
            users.create_session(u.id)
            ops.issue_code(u.email)
    # In each school: the "old" person's session and code expired, the "young" one's did not.
    for school in ("school_a", "school_b"):
        users.conn.execute("UPDATE sessions SET expires_at=? WHERE user_id=?", (_ago(days=1), f"{school}-old"))
        ops._exec("UPDATE sign_in_codes SET expires_at=? WHERE email=?", (_ago(minutes=11), f"old@{school}.example"))
    users.conn.commit()
    ops._commit()

    class S:
        pass
    out = S()
    out.users, out.ops, out.audit, out.made = users, ops, audit, made
    return out


def _sessions(s, uid):
    return s.users.conn.execute("SELECT COUNT(*) FROM sessions WHERE user_id=?", (uid,)).fetchone()[0]


def _code(s, email):
    return s.ops._fetchone("SELECT 1 AS x FROM sign_in_codes WHERE email=?", (email,)) is not None


def _purges(s):
    return [r for r in s.audit.for_action(retention.ACTION)]


def test_expired_sessions_and_codes_go_and_live_ones_stay(s):
    done = retention.enforce(s.ops, None, s.users, s.audit)
    assert done == {sch: {"expired_sessions": 1, "expired_sign_in_codes": 1, "stale_invites": 0}
                    for sch in ("school_a", "school_b")}
    for school in ("school_a", "school_b"):
        assert _sessions(s, f"{school}-old") == 0 and not _code(s, f"old@{school}.example")
        assert _sessions(s, f"{school}-young") == 1 and _code(s, f"young@{school}.example")


def test_one_audit_entry_per_school_naming_no_token_or_email(s):
    tokens = [r[0] for r in s.users.conn.execute("SELECT token FROM sessions")]
    retention.enforce(s.ops, None, s.users, s.audit)
    entries = _purges(s)
    assert sorted(e["details"]["schoolId"] for e in entries) == ["school_a", "school_b"]
    assert all(e["actor"] == retention.ACTOR for e in entries)
    text = json.dumps(entries)
    assert "@" not in text and not any(t in text for t in tokens)
    assert s.audit.verify_chain() is None


def test_a_second_run_deletes_and_logs_nothing(s):
    retention.enforce(s.ops, None, s.users, s.audit)
    assert retention.enforce(s.ops, None, s.users, s.audit) == {}
    assert len(_purges(s)) == 2


def test_another_schools_rows_are_untouched(s, monkeypatch):
    """Scoped per school: a school whose people have nothing expired gets no
    delete and no entry, whatever another school has."""
    s.users.conn.execute("UPDATE sessions SET expires_at=? WHERE user_id='school_b-old'", (_ago(days=-5),))
    s.users.conn.commit()
    s.ops._exec("UPDATE sign_in_codes SET expires_at=? WHERE email='old@school_b.example'", (_ago(minutes=-5),))
    s.ops._commit()
    done = retention.enforce(s.ops, None, s.users, s.audit)
    assert list(done) == ["school_a"]
    assert _sessions(s, "school_b-old") == 1 and _code(s, "old@school_b.example")
    assert [e["details"]["schoolId"] for e in _purges(s)] == ["school_a"]


def test_a_clock_ahead_of_the_real_one_does_not_purge_early(s):
    s.users.conn.execute("UPDATE sessions SET expires_at=? WHERE user_id='school_a-young'", (_ago(days=-2),))
    s.users.conn.commit()
    retention.enforce(s.ops, None, s.users, s.audit, now=NOW + timedelta(days=30))
    assert _sessions(s, "school_a-young") == 1


def test_invites_are_kept_unless_the_owner_sets_a_period(s, monkeypatch):
    users = s.users
    stale = users.create_invite(school_id="school_a", role="teacher", created_by="p")
    fresh = users.create_invite(school_id="school_a", role="teacher", created_by="p")
    used = users.create_invite(school_id="school_a", role="teacher", created_by="p")
    other = users.create_invite(school_id="school_b", role="teacher", created_by="p")
    for code in (stale.code, used.code, other.code):
        users.conn.execute("UPDATE invites SET expires_at=? WHERE code=?", (_ago(days=100), code))
    users.conn.execute("UPDATE invites SET expires_at=? WHERE code=?", (_ago(days=10), fresh.code))
    users.conn.execute("UPDATE invites SET used_by='x', used_at=? WHERE code=?", (_ago(days=101), used.code))
    users.conn.commit()

    def codes(school):
        return {i.code for i in users.invites_for_school(school)}

    retention.enforce(s.ops, None, users, s.audit)                     # no period set: all kept
    assert codes("school_a") == {stale.code, fresh.code, used.code}

    monkeypatch.setenv(retention.INVITE_DAYS_ENV, "not-a-number")       # a typo must not purge
    retention.enforce(s.ops, None, users, s.audit)
    assert stale.code in codes("school_a")

    monkeypatch.setenv(retention.INVITE_DAYS_ENV, "90")
    done = retention.enforce(s.ops, None, users, s.audit)
    assert codes("school_a") == {fresh.code, used.code}, "older than 90 days and unused goes; used stays"
    assert codes("school_b") == set(), "school_b's own stale invite went in its own pass"
    assert done["school_a"]["stale_invites"] == 1 and done["school_b"]["stale_invites"] == 1


def test_the_audit_log_is_kept_at_every_age(s, monkeypatch):
    """CERT-In's 2022 directions: ICT logs kept at least 180 days. The job has
    no rule over any log, so entries 1, 179, 181 and 400 days old all stay,
    with every rule switched on."""
    assert retention.CERT_IN_LOG_MIN_DAYS == 180 and "audit_log" in retention.KEPT
    for i, days in enumerate((1, 179, 181, 400)):
        s.audit.conn.execute(
            "INSERT INTO audit_log (id, timestamp, action, details) VALUES (?,?,?,?)",
            (f"aged_{i}", _ago(days=days), "pii_read", "{}"))
    s.audit.conn.commit()
    before = {r[0] for r in s.audit.conn.execute("SELECT id FROM audit_log")}
    monkeypatch.setenv(retention.INVITE_DAYS_ENV, "1")
    retention.enforce(s.ops, None, s.users, s.audit)
    after = {r[0] for r in s.audit.conn.execute("SELECT id FROM audit_log")}
    assert before <= after and {"aged_0", "aged_1", "aged_2", "aged_3"} <= after
    added = {r["action"] for r in s.audit.for_action(retention.ACTION)}
    assert len(_purges(s)) == 2 and added == {retention.ACTION}
    assert s.audit.verify_chain() is None, "the aged rows are kept, so the chain still checks"


def test_an_audit_failure_deletes_nothing(s, monkeypatch):
    def refuse(*a, **kw):
        raise RuntimeError("log down")
    monkeypatch.setattr(s.audit, "append", refuse)
    with pytest.raises(RuntimeError, match="2 school"):
        retention.enforce(s.ops, None, s.users, s.audit)
    assert _sessions(s, "school_a-old") == 1 and _code(s, "old@school_a.example")


def test_it_is_one_daily_job_in_the_automations():
    from academicos.operations import automations
    [entry] = [j for j in automations.JOBS if j[0] == "retention"]
    assert entry[2] == "day" and entry[4] is retention.job
