"""Retention periods, enforced once a day (R-A7, NFR-1; docs/compliance.md,
"Retention periods"; docs/data-flows.md lists every category and its period).

The job deletes only what a period written down somewhere says may go. Where
no period is written down, it keeps the data: a period nobody has set is not
a reason to delete.

Rules (each per school):

- expired_sessions: sign-in sessions past their expiry. The lifetime is the
  code's own (`users._SESSION_LIFETIME`, 30 days); an expired session can
  never be used again and `user_for_session` already deletes one it meets.
- expired_sign_in_codes: emailed sign-in codes past their ten minutes
  (`sign_in_codes.LIFETIME`). Only the expired value is deleted, so a fresh
  code issued since stays.
- stale_invites: invites never used that expired or were withdrawn more than
  `ACOS_RETENTION_INVITE_DAYS` days ago. OWNER TO CONFIRM: no document sets
  this period, so with the variable unset nothing is deleted. Used invites
  are always kept (they record how an account joined).

Never deleted here, at any age: the audit log (append-only, hash-chained;
CERT-In's 2022 directions require ICT logs be kept at least
CERT_IN_LOG_MIN_DAYS days, and the job holds no rule over any log), and every
store of a student's work. How long those are kept is the school's DPA
(`docs/dpa-template.md` 6.1, still [FILL IN]) and the owner's decision D6
(`docs/security-review-2026-10.md`).

Every school where something was deleted gets one `retention_purge` audit
entry, written BEFORE the delete, with counts per rule and no token, code or
email. Deleting by key is idempotent: a second run finds nothing and logs
nothing. Deletes never use a clock ahead of the real one, so a scheduler
passing a wrong time cannot purge early.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

log = logging.getLogger(__name__)

CERT_IN_LOG_MIN_DAYS = 180
INVITE_DAYS_ENV = "ACOS_RETENTION_INVITE_DAYS"
ACTION = "retention_purge"
ACTOR = "system:retention"

# What the job never deletes, and why. Read by tests and docs/data-flows.md.
KEPT = {
    "audit_log": f"append-only; CERT-In requires ICT logs be kept at least {CERT_IN_LOG_MIN_DAYS} days",
    "student work (marks, scans, mastery, events)": "no period set: DPA 6.1 is [FILL IN], owner decision D6",
    "used invites": "record how an account joined; erasure finds them",
}


def invite_days() -> Optional[int]:
    """The owner's period for stale invites, or None (keep them). A value that
    is not a whole number of at least 1 is refused: a typo must not purge."""
    raw = os.environ.get(INVITE_DAYS_ENV, "").strip()
    if not raw:
        return None
    try:
        days = int(raw)
    except ValueError:
        log.warning("%s=%r is not a whole number of days; invites are kept", INVITE_DAYS_ENV, raw)
        return None
    if days < 1:
        log.warning("%s=%r is below 1 day; invites are kept", INVITE_DAYS_ENV, raw)
        return None
    return days


def _school_ids(cs, users) -> list[str]:
    ids = set(users.school_ids())
    if cs is not None:
        ids |= {r["school_id"] for r in cs._fetchall("SELECT DISTINCT school_id FROM academic_years")}
    return sorted(i for i in ids if i)


def _expired_codes(ops, emails: list[str], now: datetime) -> list[tuple[str, str]]:
    found = []
    for email in emails:
        row = ops._fetchone("SELECT email, expires_at FROM sign_in_codes WHERE email=?", (email,))
        if row and datetime.fromisoformat(row["expires_at"]) < now:
            found.append((row["email"], row["expires_at"]))
    return found


def _delete_codes(ops, codes: list[tuple[str, str]]) -> None:
    from ..storage.secure_delete import secure_delete, truncate_wal
    with ops._conn_lock:
        with secure_delete(ops.conn):
            for email, expires_at in codes:
                ops.conn.execute("DELETE FROM sign_in_codes WHERE email=? AND expires_at=?", (email, expires_at))
        ops._commit()
        truncate_wal(ops.conn)


def enforce(ops, cs, users, audit, now: Optional[datetime] = None) -> dict[str, dict[str, int]]:
    """Apply every rule to every school. Returns {school_id: {rule: deleted}}
    for the schools where something was deleted. A school that fails is
    logged and the others still run; the failure is then raised, so the
    scheduler retries the job on its next tick."""
    real = datetime.now(timezone.utc)
    now = min(now or real, real)
    days = invite_days()
    out: dict[str, dict[str, int]] = {}
    failed: list[str] = []
    for school in _school_ids(cs, users):
        try:
            people = users.users_for_school(school)
            tokens = users.expired_session_tokens([u.id for u in people], now)
            codes = _expired_codes(ops, sorted({u.email.strip().lower() for u in people if u.email}), now)
            invites = users.stale_invite_codes(school, now - timedelta(days=days)) if days else []
            counts = {"expired_sessions": len(tokens), "expired_sign_in_codes": len(codes),
                      "stale_invites": len(invites)}
            if not any(counts.values()):
                continue
            details: dict[str, Any] = {"schoolId": school, "deleted": counts, "asOf": now.isoformat(),
                                       "periods": {"sessions": "expired", "signInCodes": "expired",
                                                   "invitesDays": days}}
            audit.append(ACTION, actor=ACTOR, details=details)
            if tokens:
                users.delete_sessions_by_token(tokens)
            if codes:
                _delete_codes(ops, codes)
            if invites:
                users.delete_unused_invites(invites)
            out[school] = counts
        except Exception:  # noqa: BLE001 - one school's failure must not stop the others; re-raised below
            log.warning("retention failed for school %s", school, exc_info=True)
            failed.append(school)
    if failed:
        raise RuntimeError(f"retention failed for {len(failed)} school(s): {', '.join(failed)}")
    return out


def job(ops, cs, users, notify, now: datetime) -> int:
    """The automations entry (operations/automations.py JOBS): how many rows went."""
    from ..assessment.audit_log import get_audit_log
    from ..curriculum import routes as cr
    if cr._cfg is None:
        raise RuntimeError("retention needs the configured data root")
    done = enforce(ops, cs, users, get_audit_log(cr._cfg.data_root), now)
    return sum(sum(c.values()) for c in done.values())
