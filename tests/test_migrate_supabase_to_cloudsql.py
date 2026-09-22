"""Tests for scripts/migrate_supabase_to_cloudsql.py.

The paging loop is the risky part: PostgREST caps one response at the
project's max-rows (1000 by default), so a migration that asked for
everything in one request would silently move the first 1000 rows of every
table and report success. These tests drive a stub PostgREST that honours
Range headers, over a table deliberately larger than one page.
"""
from __future__ import annotations

import collections
import importlib.util
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterator

import pytest

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "migrate_supabase_to_cloudsql.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("migrate_supabase_to_cloudsql", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


migrate = _load_module()


class _StubPostgrest(BaseHTTPRequestHandler):
    """Serves `rows` for one table, honouring `Range: lo-hi` the way
    PostgREST does (200 + Content-Range, or 416 past the end)."""

    rows: list[dict[str, Any]] = []
    table: str = "papers"

    def do_GET(self) -> None:  # noqa: N802
        path, _, query = self.path.partition("?")
        table = path.rsplit("/", 1)[-1]
        self.server.requests.append((table, query))
        if table != self.table:
            return self._send(404, b'{"message":"not found"}')

        rows = self.rows
        total = len(rows)
        rng = self.headers.get("Range")
        if rng:
            lo_s, _, hi_s = rng.partition("-")
            lo, hi = int(lo_s), int(hi_s)
        else:
            lo, hi = 0, total - 1
        if lo >= total:
            return self._send(416, b"[]", content_range=f"*/{total}")
        page = rows[lo:hi + 1]
        self._send(200, json.dumps(page).encode(),
                   content_range=f"{lo}-{lo + len(page) - 1}/{total}")

    def _send(self, status: int, body: bytes, content_range: str | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        if content_range:
            self.send_header("Content-Range", content_range)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args) -> None:  # keep pytest output clean
        return


@pytest.fixture()
def stub_source(monkeypatch) -> Iterator:
    servers: list[ThreadingHTTPServer] = []

    def _start(rows: list[dict[str, Any]], table: str = "papers"):
        stub_cls = type("Stub", (_StubPostgrest,), {"rows": rows, "table": table})
        server = ThreadingHTTPServer(("127.0.0.1", 0), stub_cls)
        server.requests = []
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers.append(server)
        base = f"http://127.0.0.1:{server.server_port}"
        monkeypatch.setenv("SUPABASE_KNOWLEDGE_URL", base)
        monkeypatch.setenv("SUPABASE_KNOWLEDGE_ANON_KEY", "test-anon-key")
        return server

    _start.servers = servers  # type: ignore[attr-defined]
    yield _start
    for server in servers:
        server.shutdown()
        server.server_close()


def test_paging_fetches_past_the_first_thousand_rows(stub_source) -> None:
    """2500 rows must arrive whole -- not truncated at the PostgREST cap."""
    rows = [{"id": f"paper_{i:05d}", "payload": {"n": i}} for i in range(2500)]
    server = stub_source(rows)
    url, headers = migrate._source()

    fetched = migrate._fetch_all(url, headers, "papers")

    assert len(fetched) == 2500
    assert fetched[0]["id"] == "paper_00000"
    assert fetched[-1]["id"] == "paper_02499"
    # Must have taken more than one request, or the cap was never exercised.
    assert len(server.requests) >= 3


def test_paging_stops_cleanly_on_an_empty_table(stub_source) -> None:
    stub_source([])
    url, headers = migrate._source()
    assert migrate._fetch_all(url, headers, "papers") == []


def test_paging_exact_page_boundary_does_not_loop_forever(stub_source) -> None:
    """Exactly PAGE_SIZE rows: the last response is full, so a naive loop
    would request one more page forever if 416 were not handled."""
    rows = [{"id": f"paper_{i:05d}"} for i in range(migrate.PAGE_SIZE)]
    stub_source(rows)
    url, headers = migrate._source()
    assert len(migrate._fetch_all(url, headers, "papers")) == migrate.PAGE_SIZE


def test_source_requires_credentials(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("SUPABASE_KNOWLEDGE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_KNOWLEDGE_ANON_KEY", raising=False)
    with pytest.raises(SystemExit):
        migrate._source()


def _pg_cfg() -> dict[str, str] | None:
    host = os.environ.get("ACOS_TEST_PG_HOST", "").strip()
    if not host:
        return None
    return {
        "ACOS_POSTGRES_HOST": host,
        "ACOS_POSTGRES_PORT": os.environ.get("ACOS_TEST_PG_PORT", "5432"),
        "ACOS_POSTGRES_DB": os.environ.get("ACOS_TEST_PG_DB", "postgres"),
        "ACOS_POSTGRES_USER": os.environ.get("ACOS_TEST_PG_USER", "postgres"),
        "ACOS_POSTGRES_PASSWORD": os.environ.get("ACOS_TEST_PG_PASSWORD", ""),
    }


@pytest.mark.skipif(_pg_cfg() is None, reason="set ACOS_TEST_PG_* to run the write path")
def test_end_to_end_migration_lands_rows_in_cloud_sql(stub_source, monkeypatch) -> None:
    """Serve rows from the stub, run the real migration, read them back out
    of Postgres. This is the whole script, minus the network to Google."""
    from academicos.assessment import postgres_kv
    from academicos.assessment.postgres_kv import PostgresTable

    cfg = _pg_cfg()
    assert cfg is not None
    saved = {k: os.environ.get(k) for k in cfg}
    os.environ.update(cfg)
    postgres_kv.reset_pools()
    try:
        import psycopg
        schema = (_SCRIPT.parents[1] / "deploy" / "gcp" / "schema.sql").read_text("utf-8")
        with psycopg.connect(
            host=cfg["ACOS_POSTGRES_HOST"], port=cfg["ACOS_POSTGRES_PORT"],
            dbname=cfg["ACOS_POSTGRES_DB"], user=cfg["ACOS_POSTGRES_USER"],
            password=cfg["ACOS_POSTGRES_PASSWORD"], autocommit=True,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(schema)
                cur.execute("TRUNCATE TABLE papers")

        rows = [{"id": f"mig_{i}", "payload": {"n": i}} for i in range(1200)]
        stub_source(rows, table="papers")

        monkeypatch.setattr("sys.argv", ["migrate", "--only", "papers"])
        assert migrate.main() == 0

        stored = PostgresTable("papers").select()
        assert len(stored) == 1200
        assert {r["id"] for r in stored} == {f"mig_{i}" for i in range(1200)}
    finally:
        postgres_kv.reset_pools()
        for k, previous in saved.items():
            if previous is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = previous


# --------------------------------------------------------------------------- #
# audit_log: inserted, never upserted; a re-run is safe (Task 306)
# --------------------------------------------------------------------------- #
#
# Cloud SQL's audit_log has a BEFORE UPDATE OR DELETE trigger
# (deploy/gcp/schema.sql). An upsert of a row that is already there is an
# UPDATE, so before this fix a second run printed FAILED for every audit row.
# Its seq column is unique too, so rows migrated into an instance that had
# already chained its own entries would collide with them and mix two chains.

class _UniqueViolation(Exception):
    sqlstate = "23505"


class FakeCloudSqlAuditLog:
    """Shaped like PostgresTable over deploy/gcp/schema.sql's audit_log: a
    primary key on id, a unique index on seq, and the append-only trigger."""

    def __init__(self, rows: list[dict[str, Any]] | None = None):
        self.rows: list[dict[str, Any]] = [dict(r) for r in rows or []]

    def select(self, order=None, limit=None, gt=None, **eq):
        rows = [dict(r) for r in self.rows if all(r.get(k) == v for k, v in eq.items())]
        return rows[:limit] if limit else rows

    def insert(self, row: dict[str, Any]) -> None:
        from academicos.assessment.postgres_kv import PostgresUnavailable
        for r in self.rows:
            if r["id"] == row["id"] or (row.get("seq") is not None and r.get("seq") == row["seq"]):
                cause = _UniqueViolation("duplicate key value violates unique constraint")
                raise PostgresUnavailable(table="audit_log", op="insert",
                                          body=str(cause)) from cause
        self.rows.append(dict(row))

    def upsert(self, row: dict[str, Any], on_conflict: str) -> None:
        from academicos.assessment.postgres_kv import PostgresUnavailable
        if any(r["id"] == row["id"] for r in self.rows):
            raise PostgresUnavailable(table="audit_log", op="upsert",
                                      body="audit_log is append-only: UPDATE refused")
        self.rows.append(dict(row))


def _audit_rows(n: int) -> list[dict[str, Any]]:
    from academicos.assessment.audit_log import CHAIN_START_ACTION, GENESIS_HASH, _entry_hash
    rows: list[dict[str, Any]] = []
    prev = GENESIS_HASH
    for i in range(1, n + 1):
        row = {"id": f"audit_src{i:05d}", "timestamp": f"2026-09-0{1 + i % 9}T00:00:00+00:00",
               "action": CHAIN_START_ACTION if i == 1 else "sheet_reviewed",
               "assessment_id": None if i == 1 else "a1", "student_id": None if i == 1 else "s1",
               "actor": None if i == 1 else "t1", "details": {"legacy_rows": {}} if i == 1 else {},
               "seq": i, "prev_hash": prev}
        row["entry_hash"] = _entry_hash(row)
        prev = row["entry_hash"]
        rows.append(row)
    return rows


@pytest.fixture()
def cloud_sql_audit(monkeypatch):
    """Point the script's destination at one fake audit_log table."""
    def _install(target: FakeCloudSqlAuditLog):
        monkeypatch.setattr(migrate.postgres_kv, "postgres_configured", lambda: True)
        monkeypatch.setattr(migrate, "PostgresTable", lambda table: target)
        monkeypatch.setattr("sys.argv", ["migrate", "--only", "audit_log"])
        return target
    return _install


def test_re_running_the_audit_log_migration_fails_nothing(stub_source, cloud_sql_audit,
                                                            capsys) -> None:
    rows = _audit_rows(5)
    stub_source(rows, table="audit_log")
    target = cloud_sql_audit(FakeCloudSqlAuditLog())

    assert migrate.main() == 0
    first = capsys.readouterr().out
    assert "FAILED" not in first
    assert "inserted 5, already migrated 0" in first
    assert len(target.rows) == 5

    assert migrate.main() == 0
    second = capsys.readouterr().out
    assert "FAILED" not in second, second
    assert "inserted 0, already migrated 5" in second
    assert target.rows == rows


def test_a_partial_earlier_run_is_completed(stub_source, cloud_sql_audit, capsys) -> None:
    rows = _audit_rows(4)
    stub_source(rows, table="audit_log")
    target = cloud_sql_audit(FakeCloudSqlAuditLog(rows[:2]))

    assert migrate.main() == 0
    out = capsys.readouterr().out
    assert "FAILED" not in out
    assert "inserted 2, already migrated 2" in out
    assert sorted(r["id"] for r in target.rows) == [r["id"] for r in rows]


def test_migrating_into_an_audit_log_with_its_own_chain_is_refused(
        stub_source, cloud_sql_audit, capsys) -> None:
    """The instance already appended its own entries (seq 1..2). Migrated rows
    would collide on seq and mix two chains, so nothing is written."""
    stub_source(_audit_rows(3), table="audit_log")
    own = [dict(r, id=f"audit_own{i}") for i, r in enumerate(_audit_rows(2))]
    target = cloud_sql_audit(FakeCloudSqlAuditLog(own))

    assert migrate.main() != 0
    out = capsys.readouterr().out
    assert "REFUSED" in out
    assert "2 row(s) that are not in the source" in out
    assert [r["id"] for r in target.rows] == ["audit_own0", "audit_own1"]


def test_the_audit_log_is_never_upserted(stub_source, cloud_sql_audit) -> None:
    stub_source(_audit_rows(2), table="audit_log")
    target = cloud_sql_audit(FakeCloudSqlAuditLog())

    def refuse(row, on_conflict):
        raise AssertionError("audit_log must be inserted, not upserted")
    target.upsert = refuse  # type: ignore[method-assign]
    assert migrate.main() == 0
    assert len(target.rows) == 2


@pytest.mark.skipif(_pg_cfg() is None, reason="set ACOS_TEST_PG_* to run the write path")
def test_audit_log_re_run_against_real_postgres(stub_source, monkeypatch, capsys) -> None:
    """CI-verified: the real trigger and unique indexes from schema.sql."""
    from academicos.assessment import postgres_kv
    from academicos.assessment.postgres_kv import PostgresTable

    cfg = _pg_cfg()
    assert cfg is not None
    saved = {k: os.environ.get(k) for k in cfg}
    os.environ.update(cfg)
    postgres_kv.reset_pools()
    try:
        import psycopg
        schema = (_SCRIPT.parents[1] / "deploy" / "gcp" / "schema.sql").read_text("utf-8")
        with psycopg.connect(
            host=cfg["ACOS_POSTGRES_HOST"], port=cfg["ACOS_POSTGRES_PORT"],
            dbname=cfg["ACOS_POSTGRES_DB"], user=cfg["ACOS_POSTGRES_USER"],
            password=cfg["ACOS_POSTGRES_PASSWORD"], autocommit=True,
        ) as conn:
            with conn.cursor() as cur:
                # A fresh table, so the result does not depend on earlier runs.
                cur.execute("DROP TABLE IF EXISTS audit_log")
                cur.execute(schema)

        rows = _audit_rows(3)
        stub_source(rows, table="audit_log")
        monkeypatch.setattr("sys.argv", ["migrate", "--only", "audit_log"])
        assert migrate.main() == 0
        assert migrate.main() == 0
        out = capsys.readouterr().out
        assert "FAILED" not in out
        assert "inserted 0, already migrated 3" in out
        assert len(PostgresTable("audit_log").select()) == 3
    finally:
        postgres_kv.reset_pools()
        for k, previous in saved.items():
            if previous is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = previous


def test_a_unique_violation_on_an_id_that_is_now_there_counts_as_migrated(
        stub_source, cloud_sql_audit, capsys) -> None:
    """Another run inserted the rows between this run's read of the
    destination and its inserts: the insert's unique violation on id is
    counted as already migrated, not FAILED."""
    rows = _audit_rows(2)
    stub_source(rows, table="audit_log")
    target = cloud_sql_audit(FakeCloudSqlAuditLog(rows))
    real_select = target.select
    calls = {"n": 0}

    def select_empty_first(**kw):
        calls["n"] += 1
        return [] if calls["n"] == 1 else real_select(**kw)
    target.select = select_empty_first  # type: ignore[method-assign]

    assert migrate.main() == 0
    out = capsys.readouterr().out
    assert "FAILED" not in out, out
    assert "inserted 0, already migrated 2" in out


# --------------------------------------------------------------------------- #
# a failed row is a nonzero exit, with no cut-over advice (Task 306 review)
# --------------------------------------------------------------------------- #
#
# An operator or CI job that checks only the exit code must not be told to cut
# over when rows did not land -- least of all when an audit row in Cloud SQL
# has the same id as the source but a different entry_hash, which means the
# two audit trails have diverged.

def test_an_audit_row_with_a_different_hash_exits_nonzero(stub_source, cloud_sql_audit,
                                                          capsys) -> None:
    rows = _audit_rows(3)
    stub_source(rows, table="audit_log")
    diverged = dict(rows[1], entry_hash="0" * 64)
    target = cloud_sql_audit(FakeCloudSqlAuditLog([rows[0], diverged]))

    assert migrate.main() != 0
    out = capsys.readouterr().out
    assert "different entry_hash" in out
    assert "FAILED: audit_log" in out
    assert "Next:" not in out
    # The diverged row is left as it is, for a person to look at.
    assert [r for r in target.rows if r["id"] == rows[1]["id"]] == [diverged]


def test_any_failed_audit_insert_exits_nonzero(stub_source, cloud_sql_audit, capsys) -> None:
    stub_source(_audit_rows(2), table="audit_log")
    target = cloud_sql_audit(FakeCloudSqlAuditLog())

    def broken(row):
        raise RuntimeError("connection reset")
    target.insert = broken  # type: ignore[method-assign]

    assert migrate.main() != 0
    out = capsys.readouterr().out
    assert "FAILED: audit_log" in out
    assert "Next:" not in out


def test_a_failed_upsert_in_any_table_exits_nonzero(stub_source, monkeypatch,
                                                     capsys) -> None:
    stub_source([{"id": "p1", "payload": {}}, {"id": "p2", "payload": {}}], table="papers")

    class HalfBroken:
        rows: list[dict[str, Any]] = []

        def upsert(self, row, on_conflict):
            if row["id"] == "p2":
                raise RuntimeError("value too long")
            self.rows.append(row)

        def select(self, **kw):
            return list(self.rows)

    monkeypatch.setattr(migrate.postgres_kv, "postgres_configured", lambda: True)
    monkeypatch.setattr(migrate, "PostgresTable", lambda table: HalfBroken())
    monkeypatch.setattr("sys.argv", ["migrate", "--only", "papers"])

    assert migrate.main() != 0
    out = capsys.readouterr().out
    assert "FAILED: papers" in out
    assert "Next:" not in out
