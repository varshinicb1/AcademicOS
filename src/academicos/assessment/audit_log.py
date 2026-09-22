"""Append-only audit log -- the server-side counterpart to the Dart offline
engine's LocalStore.appendAuditLog. Every real grading write and every real
paper export gets a timestamped, immutable record here: who did what, to
which assessment, when. This is the concrete control docs/compliance.md
calls "corruption resistance" and the log-retention half of CERT-In's
6-month requirement.

Local SQLite by default; same Supabase-when-configured pattern as every
other store in this codebase (see supabase_kv.py's module docstring for why:
Render's free tier wipes local disk on every restart, so a durable audit
trail needs the same real persistence everything else got).

Append-only by construction, not by convention. Audit item 8.5 (reproduced
2026-09-21): a raw UPDATE and a raw DELETE on this table each returned
rowcount 1, rewriting the actor and the marks, and the remote append was an
upsert, so a replayed id overwrote the original row. There are now three
layers:

1. **The database refuses.** The local SQLite file has BEFORE UPDATE and
   BEFORE DELETE triggers that RAISE(ABORT). They are created with the schema
   and added to an existing file when it is opened. docs/supabase-setup.sql
   and deploy/gcp/schema.sql declare the same for the remote table: RLS with
   no UPDATE/DELETE policy, those privileges revoked, and a trigger.
2. **An append is an insert.** Locally and remotely, an id that already
   exists raises DuplicateAuditEntry. The entry is not merged, and it is not
   written to the local fallback instead.
3. **Tampering is detectable.** Each entry carries `seq` (1, 2, 3, ...),
   `prev_hash` (the previous entry's `entry_hash`, or 64 zeros for the first)
   and `entry_hash`, the SHA-256 of its canonical content (see _canonical).
   verify_chain() walks the log in seq order and returns the first entry that
   does not fit. Someone with write access to the file who drops the triggers
   and edits or deletes a row is caught by the next entry. The chain cannot
   see the newest entries being removed, because no later entry exists to
   disagree. Keeping an external copy of the latest entry_hash would close
   that gap; it is not built.

Rows written before the chain existed have no seq and no hashes. They are
kept as they are, not re-hashed into the chain. The chain's first entry
(seq 1) records them instead. It is a `audit_chain_started` entry the log
writes itself, before the first real entry, and its details map every
unchained row's id to a hash of its content at that moment. (It is a
separate entry so that no caller's details grow an extra key.) After
that, verify_chain reports an unchained row that is not in the map, one
whose content changed, and a mapped row that is gone. A timestamp cannot do
this job. The review of 2026-09-22 reproduced a raw INSERT of an unchained
`sheet_reviewed` row after the chain began, which verify_chain skipped as
pre-chain, and whoever inserts a row also chooses its timestamp, so a
backdated row would pass any "older than the chain" test. A log with no
chained entry at all has nothing to compare against and is not checked.

The chain proves that nothing was changed or removed. It does not prove who
added an entry: the hash is unkeyed, so anyone allowed to INSERT can append
a correctly chained entry. What stops that is the INSERT privilege itself
(see the audit_log block of docs/supabase-setup.sql).

Each backend (the remote table when configured, local SQLite otherwise) keeps
its own chain. A remote outage still falls back to local SQLite, as it did
before, and those entries chain locally. The writer reads the remote head and
inserts the next seq. The unique index on seq means that when two instances
race for the same seq, one wins and the other retries, so the chain does not
fork.

If a real deployment ever needs to prune old entries, that is a deliberate,
logged, admin-only database operation, not something application code can do.
"""
from __future__ import annotations

import hashlib
import json
import threading
import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import requests

from .supabase_kv import SupabaseUnavailable, is_unique_violation
from .postgres_kv import durable_table

logger = logging.getLogger(__name__)

GENESIS_HASH = "0" * 64

# Retries when another writer took the seq this one read as next. Losing
# more than a handful of races in a row is no longer a race, so after that
# the append raises AuditAppendFailed, which append() does not turn into a
# local-only entry.
_SEQ_RACE_RETRIES = 5

# Rows per remote read in verify_chain. PostgREST caps a response at its
# max-rows setting (1000 by default) without saying so, so the read pages by
# id until a page comes back empty. It does not stop at a short page, because
# a server cap below this number makes every page short.
_REMOTE_PAGE = 1000

# The action of the seq-1 entry that lists the pre-chain rows.
CHAIN_START_ACTION = "audit_chain_started"

TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_log (
  id            TEXT PRIMARY KEY,
  timestamp     TEXT NOT NULL,
  action        TEXT NOT NULL,
  assessment_id TEXT,
  student_id    TEXT,
  actor         TEXT,
  details       TEXT NOT NULL DEFAULT '{}',
  seq           INTEGER,
  prev_hash     TEXT,
  entry_hash    TEXT
);
"""

# The columns the chain added. ALTER TABLE ADD COLUMN on a pre-chain file
# changes the schema and no row, so the triggers below do not stop it (and
# need not).
_CHAIN_COLUMNS = (("seq", "INTEGER"), ("prev_hash", "TEXT"), ("entry_hash", "TEXT"))

INDEXES_AND_TRIGGERS = """
CREATE INDEX IF NOT EXISTS idx_audit_assessment ON audit_log(assessment_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);
CREATE UNIQUE INDEX IF NOT EXISTS idx_audit_seq ON audit_log(seq);
CREATE TRIGGER IF NOT EXISTS audit_log_no_update BEFORE UPDATE ON audit_log
BEGIN
  SELECT RAISE(ABORT, 'audit_log is append-only: UPDATE refused');
END;
CREATE TRIGGER IF NOT EXISTS audit_log_no_delete BEFORE DELETE ON audit_log
BEGIN
  SELECT RAISE(ABORT, 'audit_log is append-only: DELETE refused');
END;
"""


class DuplicateAuditEntry(Exception):
    """An append whose id is already in the log. It is a replay, a bug or an
    attempt to overwrite history, not an outage, so nothing retries it
    somewhere else."""


class AuditAppendFailed(SupabaseUnavailable):
    """The remote table answered, but the append could not be completed: the
    seq race was lost _SEQ_RACE_RETRIES times, or the id lookup that tells a
    replay from a lost race failed after a conflict.

    This is not an outage, so append() does not write the entry to local
    SQLite. On Render that disk is wiped on restart, and a grade saved with
    its only audit entry there would lose the entry. It subclasses
    SupabaseUnavailable so the app-level handler answers 503, and the
    grading routes audit before they save, so no grade is written."""


def _canonical(entry: dict[str, Any]) -> bytes:
    """The bytes an entry's hash covers: every stored field except entry_hash
    itself, as sorted-key compact JSON. `details` is hashed as the parsed
    object, so SQLite's JSON text and Postgres' JSONB give the same hash."""
    body = {
        "id": entry["id"], "seq": int(entry["seq"]), "timestamp": entry["timestamp"],
        "action": entry["action"], "assessment_id": entry.get("assessment_id"),
        "student_id": entry.get("student_id"), "actor": entry.get("actor"),
        "details": entry.get("details") or {}, "prev_hash": entry["prev_hash"],
    }
    return json.dumps(body, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def _entry_hash(entry: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(entry)).hexdigest()


def _is_chained(row: dict[str, Any]) -> bool:
    return row.get("seq") is not None or bool(row.get("entry_hash"))


def _legacy_hash(row: dict[str, Any]) -> str:
    """A pre-chain row's content hash, for the seq-1 entry's map. 16 hex
    characters (64 bits) keeps the map small for a large legacy log and is
    still far beyond forging a matching edit."""
    body = {k: row.get(k) for k in ("id", "timestamp", "action", "assessment_id",
                                     "student_id", "actor")}
    body["details"] = row.get("details") or {}
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _chain_start(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """The seq-1 entry, which records every unchained row present when the
    chain began."""
    entry = {
        "id": f"audit_{uuid.uuid4().hex[:12]}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": CHAIN_START_ACTION, "assessment_id": None, "student_id": None,
        "actor": None,
        "details": {"legacy_rows": {r["id"]: _legacy_hash(r)
                                    for r in rows if not _is_chained(r)}},
        "seq": 1, "prev_hash": GENESIS_HASH,
    }
    entry["entry_hash"] = _entry_hash(entry)
    return entry


def _insert_row(conn: sqlite3.Connection, entry: dict[str, Any]) -> None:
    conn.execute(
        """INSERT INTO audit_log (id, timestamp, action, assessment_id, student_id,
                                  actor, details, seq, prev_hash, entry_hash)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (entry["id"], entry["timestamp"], entry["action"], entry["assessment_id"],
         entry["student_id"], entry["actor"], json.dumps(entry["details"]),
         entry["seq"], entry["prev_hash"], entry["entry_hash"]),
    )


def first_broken_link(rows: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """Return the first entry that does not fit the chain, or None if the
    chain is intact.

    The result is {"id", "seq", "reason"}. The chain is walked first. Then
    the unchained rows are compared with the list the seq-1 entry recorded;
    see the module docstring."""
    chained = [r for r in rows if _is_chained(r)]
    # A row whose seq was stripped sorts last, where it is reported.
    chained.sort(key=lambda r: (r.get("seq") is None, int(r.get("seq") or 0)))
    prev_hash, expected_seq = GENESIS_HASH, 1
    for row in chained:
        reason = None
        if row.get("seq") is None or not row.get("entry_hash"):
            reason = "chain fields were removed from an entry after the chain began"
        elif int(row["seq"]) != expected_seq:
            reason = f"expected seq {expected_seq}: an entry before this one is missing"
        elif row.get("prev_hash") != prev_hash:
            reason = "prev_hash does not match the previous entry's hash"
        elif _entry_hash(row) != row["entry_hash"]:
            reason = "the content no longer matches its hash: the entry was edited"
        if reason:
            return {"id": row.get("id"), "seq": row.get("seq"), "reason": reason}
        prev_hash, expected_seq = row["entry_hash"], expected_seq + 1
    if not chained:
        return None
    # The chain is intact, so chained[0] is seq 1 and its record is genuine.
    # A chain begun before the record existed vouches for no unchained row.
    first = chained[0]
    recorded = ((first.get("details") or {}).get("legacy_rows") or {}
                if first.get("action") == CHAIN_START_ACTION else {})
    unchained = sorted((r for r in rows if not _is_chained(r)),
                       key=lambda r: str(r.get("id")))
    for row in unchained:
        want = recorded.get(row.get("id"))
        if want is None:
            return {"id": row.get("id"), "seq": None,
                    "reason": "an unchained entry that was not in the log when the "
                              "chain began: it was inserted outside the chain"}
        if _legacy_hash(row) != want:
            return {"id": row.get("id"), "seq": None,
                    "reason": "a pre-chain entry no longer matches the hash recorded "
                              "when the chain began: it was edited"}
    present = {r.get("id") for r in unchained}
    for entry_id in sorted(recorded):
        if entry_id not in present:
            return {"id": entry_id, "seq": None,
                    "reason": "a pre-chain entry recorded when the chain began is "
                              "missing: it was deleted"}
    return None


class AuditLog:
    def __init__(self, db_path: Path):
        self._remote = durable_table("audit_log")
        self._lock = threading.Lock()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=60000")
        self.conn.executescript(TABLE_SCHEMA)
        have = {r["name"] for r in self.conn.execute("PRAGMA table_info(audit_log)")}
        for name, sql_type in _CHAIN_COLUMNS:
            if name not in have:
                self.conn.execute(f"ALTER TABLE audit_log ADD COLUMN {name} {sql_type}")
        self.conn.executescript(INDEXES_AND_TRIGGERS)
        self.conn.commit()

    def append(self, action: str, *, assessment_id: str | None = None,
              student_id: str | None = None, actor: str | None = None,
              details: dict[str, Any] | None = None,
              entry_id: str | None = None) -> str:
        """Append one entry and return its id.

        `entry_id` is for replaying an entry recorded elsewhere, such as an
        offline device's log. If it is left out, a fresh id is generated.
        Either way, an id that is already in the log raises
        DuplicateAuditEntry."""
        entry = {
            "id": entry_id or f"audit_{uuid.uuid4().hex[:12]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action, "assessment_id": assessment_id,
            "student_id": student_id, "actor": actor, "details": details or {},
        }
        if self._remote.enabled:
            try:
                self._append_remote(entry)
                return entry["id"]
            except (DuplicateAuditEntry, AuditAppendFailed):
                raise
            except (SupabaseUnavailable, requests.exceptions.RequestException):
                logger.warning("Supabase unavailable for audit_log append, falling back to local SQLite", exc_info=True)
        self._append_local(entry)
        return entry["id"]

    def _append_remote(self, entry: dict[str, Any]) -> None:
        for _ in range(_SEQ_RACE_RETRIES):
            head = self._remote.select(order="seq.desc", limit=1, gt={"seq": 0})
            if not head:
                start = _chain_start(self._read_all_remote())
                try:
                    self._remote.insert(dict(start))
                except (SupabaseUnavailable, requests.exceptions.RequestException) as exc:
                    if not is_unique_violation(exc):
                        raise
                    continue    # another writer began the chain; re-read the head
                head = [start]
            entry["seq"] = int(head[0]["seq"]) + 1
            entry["prev_hash"] = head[0]["entry_hash"]
            entry["entry_hash"] = _entry_hash(entry)
            try:
                self._remote.insert(dict(entry))
                return
            except (SupabaseUnavailable, requests.exceptions.RequestException) as exc:
                if not is_unique_violation(exc):
                    raise
                try:
                    replayed = bool(self._remote.select(id=entry["id"]))
                except (SupabaseUnavailable, requests.exceptions.RequestException) as lookup:
                    # The table just answered the insert, so this is not an
                    # outage to route around, and not knowing whether the id
                    # exists is no ground for writing it somewhere else.
                    raise AuditAppendFailed(
                        table="audit_log", op="insert",
                        body="insert conflicted and the id lookup that tells a replay "
                             "from a lost seq race failed") from lookup
                if replayed:
                    raise DuplicateAuditEntry(entry["id"]) from exc
                # The id is new, so another writer took this seq first.
                # Re-read the head and try again.
        raise AuditAppendFailed(table="audit_log", op="insert",
                                body=f"lost the seq race {_SEQ_RACE_RETRIES} times")

    def _read_all_remote(self) -> list[dict[str, Any]]:
        """Every row of the remote table, paged by id (the primary key, so
        the order is total and a page boundary cannot skip or repeat a row).
        See _REMOTE_PAGE for why it stops only at an empty page."""
        rows: list[dict[str, Any]] = []
        last: Optional[str] = None
        while True:
            page = self._remote.select(order="id.asc", limit=_REMOTE_PAGE,
                                       gt={"id": last} if last is not None else None)
            if not page:
                return rows
            rows.extend(page)
            nxt = page[-1]["id"]
            if last is not None and not nxt > last:
                raise SupabaseUnavailable(
                    table="audit_log", op="select",
                    body="paging by id did not advance; the log was not fully read")
            last = nxt

    def _append_local(self, entry: dict[str, Any]) -> None:
        with self._lock:
            try:
                # IMMEDIATE takes the write lock before the head is read, so a
                # second process on the same file cannot read the same head.
                self.conn.execute("BEGIN IMMEDIATE")
                head = self.conn.execute(
                    "SELECT seq, entry_hash FROM audit_log WHERE seq IS NOT NULL "
                    "ORDER BY seq DESC LIMIT 1").fetchone()
                if head is None:
                    legacy = [_row_to_dict(r) for r in self.conn.execute(
                        "SELECT * FROM audit_log WHERE seq IS NULL AND entry_hash IS NULL")]
                    start = _chain_start(legacy)
                    _insert_row(self.conn, start)
                    head = start
                entry["seq"] = int(head["seq"]) + 1
                entry["prev_hash"] = head["entry_hash"]
                entry["entry_hash"] = _entry_hash(entry)
                _insert_row(self.conn, entry)
                self.conn.commit()
            except sqlite3.IntegrityError as exc:
                self.conn.rollback()
                if self.conn.execute("SELECT 1 FROM audit_log WHERE id=?",
                                     (entry["id"],)).fetchone():
                    raise DuplicateAuditEntry(entry["id"]) from exc
                raise
            except BaseException:
                self.conn.rollback()
                raise

    def has_entry(self, action: str, *, assessment_id: str, student_id: str) -> bool:
        """Whether this sheet has any entry with this action.

        This fails closed. When the remote table is configured and cannot be
        read, it raises instead of answering from the local file alone,
        because a False here unlocks a finalized grade (see grade_lock.py).
        The local file is checked too, for entries written during an earlier
        outage."""
        if self._remote.enabled:
            if self._remote.select(action=action, assessment_id=assessment_id,
                                   student_id=student_id, limit=1):
                return True
        with self._lock:
            row = self.conn.execute(
                "SELECT 1 FROM audit_log WHERE action=? AND assessment_id=? "
                "AND student_id=? LIMIT 1",
                (action, assessment_id, student_id)).fetchone()
        return row is not None

    def verify_chain(self) -> Optional[dict[str, Any]]:
        """Return the first broken link in the active backend's chain, or
        None if the chain is intact.

        It reads the remote table when one is configured, and local SQLite
        otherwise. A failed remote read raises, because a log that could not
        be checked must not be reported as intact. The remote read is paged
        (see _read_all_remote): a single select would stop at PostgREST's
        max-rows and check only that part of the log."""
        if self._remote.enabled:
            rows = self._read_all_remote()
        else:
            with self._lock:
                rows = [_row_to_dict(r) for r in self.conn.execute("SELECT * FROM audit_log")]
        return first_broken_link(rows)

    def for_assessment(self, assessment_id: str) -> list[dict[str, Any]]:
        if self._remote.enabled:
            try:
                return self._remote.select(assessment_id=assessment_id, order="timestamp.desc")
            except (SupabaseUnavailable, requests.exceptions.RequestException):
                logger.warning("Supabase unavailable for audit_log for_assessment, falling back to local SQLite", exc_info=True)
        rows = self.conn.execute(
            "SELECT * FROM audit_log WHERE assessment_id=? ORDER BY timestamp DESC",
            (assessment_id,)).fetchall()
        return [_row_to_dict(r) for r in rows]

    def for_action(self, action: str) -> list[dict[str, Any]]:
        if self._remote.enabled:
            try:
                return self._remote.select(action=action, order="timestamp.desc")
            except (SupabaseUnavailable, requests.exceptions.RequestException):
                logger.warning("Supabase unavailable for audit_log for_action, falling back to local SQLite", exc_info=True)
        rows = self.conn.execute(
            "SELECT * FROM audit_log WHERE action=? ORDER BY timestamp DESC",
            (action,)).fetchall()
        return [_row_to_dict(r) for r in rows]


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    d["details"] = json.loads(d.get("details") or "{}")
    return d


_INSTANCE: Optional[dict] = {}
_INSTANCE_LOCK = threading.Lock()


def get_audit_log(data_root: Path) -> AuditLog:
    # Keyed on the RESOLVED PATH, not a bare global.
    #
    # This was `if _INSTANCE is None`, so the FIRST data_root ever passed won
    # for the life of the process and every later call with a different root got
    # that first instance. In production only one root is used, which is why it
    # survived unspotted -- but anywhere a process touches more than one root
    # (tests, a CLI run beside a server, tooling) the store silently reads and
    # writes the WRONG database. For the audit log that means a compliance trail
    # filed against another data root.
    global _INSTANCE
    # `_INSTANCE` is now a PATH-KEYED cache rather than one store. Tests reset it
    # with `monkeypatch.setattr(..., "_INSTANCE", None)` -- a workaround that
    # `tests/test_assessment_governance.py:37` documents in a comment, because a
    # single global meant the second test to run still saw the first test's
    # store. The name and the reset semantics are kept so those ~30 call sites
    # keep working, but the reset is no longer load-bearing: two different data
    # roots now get two different stores by construction.
    if _INSTANCE is None:
        _INSTANCE = {}                      # a caller cleared the cache
    key = str(Path(data_root) / "audit" / "audit_log.sqlite")
    instance = _INSTANCE.get(key)
    if instance is None:
        with _INSTANCE_LOCK:
            instance = _INSTANCE.get(key)
            if instance is None:
                instance = AuditLog(Path(key))
                _INSTANCE[key] = instance
    return instance
