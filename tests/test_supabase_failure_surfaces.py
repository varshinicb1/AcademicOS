"""Regression tests for the 2026-09-15 production incident: the Supabase
`users`/`sessions` tables were missing on the live Render deployment, so
/auth/login, /auth/register and /auth/me all answered a bare 500 — while
GET /health/storage still reported "supabase_reachable": true because it
only ever probed the `assessments` table.

Three contracts, all against a stub PostgREST that 404s named tables with
a real PGRST205-shaped body:
1. SupabaseTable raises SupabaseUnavailable carrying the table, status and
   body — and it stays a requests.RequestException subclass, so the stores
   that fall back to local SQLite (AssessmentStore, EventStore) keep
   catching it exactly as before.
2. api/main.py's app-level handler turns an uncaught SupabaseUnavailable on
   a non-fallback route into an honest 503, never a bare 500.
3. /health/storage probes every durability-critical table and names the
   broken one instead of a single-table blanket verdict.
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Iterator

import pytest
import requests

from academicos.api.main import _DURABLE_TABLES
from academicos.assessment.supabase_kv import SupabaseTable, SupabaseUnavailable


class _StubPostgrest(BaseHTTPRequestHandler):
    """Minimal PostgREST stand-in: 404s each table named in `broken` with a
    real PGRST205-shaped body, answers every other /rest/v1 read with an
    empty result set. Storage API paths 404 too — that is the normal
    "no snapshot uploaded yet" case CurriculumStore already handles."""

    broken: tuple[str, ...] = ()

    def _respond(self, status: int, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?")[0]
        if path.startswith("/rest/v1/"):
            table = path.rsplit("/", 1)[-1]
            if table in self.broken:
                return self._respond(404, json.dumps({
                    "code": "PGRST205",
                    "message": f"Could not find the table 'public.{table}' in the schema cache",
                }).encode())
            return self._respond(200, b"[]")
        return self._respond(404, b'{"error":"not found"}')

    def log_message(self, *args) -> None:  # keep pytest output clean
        return


@pytest.fixture()
def stub_postgrest(monkeypatch) -> Iterator:
    """Starts the stub on a free port and points the Supabase env vars at
    it. Call the yielded factory with the table names to break."""
    servers: list[ThreadingHTTPServer] = []

    def _start(*broken: str) -> str:
        stub_cls = type("Stub", (_StubPostgrest,), {"broken": tuple(broken)})
        server = ThreadingHTTPServer(("127.0.0.1", 0), stub_cls)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers.append(server)
        base = f"http://127.0.0.1:{server.server_port}"
        monkeypatch.setenv("SUPABASE_KNOWLEDGE_URL", base)
        monkeypatch.setenv("SUPABASE_KNOWLEDGE_ANON_KEY", "test-anon-key")
        return base

    yield _start
    for server in servers:
        server.shutdown()
        server.server_close()


def test_missing_table_raises_typed_error_that_sqlite_fallback_still_catches(
        stub_postgrest) -> None:
    stub_postgrest("users")
    with pytest.raises(SupabaseUnavailable) as excinfo:
        SupabaseTable("users").select(email="nobody@example.test")
    err = excinfo.value
    assert err.table == "users"
    assert err.status == 404
    assert "PGRST205" in str(err)

    # The fallback contract: stores catch requests.exceptions.RequestException
    # around their remote calls and must keep swallowing this.
    with pytest.raises(requests.exceptions.RequestException):
        SupabaseTable("users").select()


def test_auth_route_answers_503_not_500_when_the_users_table_is_missing(
        stub_postgrest, tmp_path, monkeypatch) -> None:
    from test_assessment_routes_auth import _boot_client

    stub_postgrest("users", "sessions")
    with _boot_client(tmp_path, monkeypatch) as client:
        r = client.post("/api/v1/auth/register", json={
            "schoolId": "school_1", "name": "QA", "email": "qa@example.test",
            "password": "correct horse battery",
        })
        assert r.status_code == 503, r.text
        detail = r.json()["detail"]
        assert "storage backend unavailable" in detail
        assert "users" in detail


def test_health_storage_names_each_broken_table(
        stub_postgrest, tmp_path, monkeypatch) -> None:
    from test_assessment_routes_auth import _boot_client

    stub_postgrest("users", "sessions")
    with _boot_client(tmp_path, monkeypatch) as client:
        r = client.get("/health/storage")
    assert r.status_code == 200
    body = r.json()
    assert body["supabase_configured"] is True
    assert body["supabase_reachable"] is False
    assert set(body["tables"]) == set(_DURABLE_TABLES)
    assert body["tables"]["assessments"] == "ok"
    assert body["tables"]["users"].startswith("error:")
    assert "PGRST205" in body["tables"]["users"]
    assert body["tables"]["sessions"].startswith("error:")
