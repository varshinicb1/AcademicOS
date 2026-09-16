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
