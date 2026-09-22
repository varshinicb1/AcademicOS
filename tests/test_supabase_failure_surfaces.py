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

import collections
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Iterator

import pytest
import requests

from academicos.api.main import _DURABLE_TABLES
from academicos.assessment.supabase_kv import SupabaseTable, SupabaseUnavailable

from _auth_helpers import invite_code


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
            self.server.counter[table] += 1
            if table in self.broken:
                return self._respond(404, json.dumps({
                    "code": "PGRST205",
                    "message": f"Could not find the table 'public.{table}' in the schema cache",
                }).encode())
            return self._respond(200, b"[]")
        self.server.counter[path] += 1
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
        server.counter = collections.Counter()
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers.append(server)
        base = f"http://127.0.0.1:{server.server_port}"
        monkeypatch.setenv("SUPABASE_KNOWLEDGE_URL", base)
        monkeypatch.setenv("SUPABASE_KNOWLEDGE_ANON_KEY", "test-anon-key")
        return base

    _start.servers = servers  # type: ignore[attr-defined]
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


def test_auth_route_falls_back_to_sqlite_when_the_users_table_is_missing(
        stub_postgrest, tmp_path, monkeypatch) -> None:
    from test_assessment_routes_auth import _boot_client

    stub_postgrest("users", "sessions")
    with _boot_client(tmp_path, monkeypatch) as client:
        r = client.post("/api/v1/auth/register", json={
            "inviteCode": invite_code("school_1"), "name": "QA", "email": "qa@example.test",
            "password": "correct horse battery",
        })
        # UserStore gracefully falls back to local SQLite so teachers/students
        # are not locked out when Supabase users/sessions tables are missing
        assert r.status_code == 200, r.text
        body = r.json()
        assert "token" in body
        assert body["user"]["email"] == "qa@example.test"


def test_non_fallback_route_answers_503_not_500_when_table_is_missing(
        stub_postgrest, tmp_path, monkeypatch) -> None:
    from test_assessment_routes_auth import _boot_client

    stub_postgrest("papers")
    with _boot_client(tmp_path, monkeypatch) as client:
        reg = client.post("/api/v1/auth/register", json={
            "inviteCode": invite_code("school_1"), "name": "QA", "email": "qa@example.test",
            "password": "correct horse battery",
        })
        assert reg.status_code == 200
        token = reg.json()["token"]
        r = client.get("/api/v1/papers/paper_missing",
                       headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 503, r.text
        detail = r.json()["detail"]
        assert "storage backend unavailable" in detail
        assert "papers" in detail


def test_health_storage_names_each_broken_table(
        stub_postgrest, tmp_path, monkeypatch) -> None:
    import academicos.api.main as main_mod
    from test_assessment_routes_auth import _boot_client

    stub_postgrest("users", "sessions")
    main_mod._probe_cache.update(at=0.0, body=None)  # no stale verdicts
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


def test_storage_probe_result_is_cached_until_ttl(stub_postgrest, tmp_path, monkeypatch) -> None:
    """The stress-test follow-up: one /health/storage call fans out to one
    upstream select per table, so repeats within the TTL must be served
    from the cache (zero new upstream hits), and only a TTL expiry (or an
    explicit reset) may re-probe."""
    import academicos.api.main as main_mod
    from test_assessment_routes_auth import _boot_client

    stub_postgrest()  # nothing broken: every table answers []
    main_mod._probe_cache.update(at=0.0, body=None)
    server = stub_postgrest.servers[-1]
    with _boot_client(tmp_path, monkeypatch) as client:
        baseline = sum(server.counter.values())
        first = client.get("/health/storage")
        assert first.status_code == 200
        assert first.json()["supabase_reachable"] is True
        assert sum(server.counter.values()) - baseline == len(main_mod._DURABLE_TABLES)

        second = client.get("/health/storage")
        assert second.json() == first.json()
        assert sum(server.counter.values()) - baseline == len(main_mod._DURABLE_TABLES), \
            "repeat call inside the TTL must not touch upstream again"

        main_mod._probe_cache.update(at=0.0, body=None)
        third = client.get("/health/storage")
        assert third.json()["supabase_reachable"] is True
        assert sum(server.counter.values()) - baseline == 2 * len(main_mod._DURABLE_TABLES), \
            "an expired reset cache must re-probe upstream"


def test_deployment_placeholder_is_treated_as_unconfigured(monkeypatch) -> None:
    """The GCP bootstrap creates every Secret Manager entry with the literal
    value REPLACE_ME, so Cloud Run can start before real credentials are pasted.

    That value is a non-empty string, so `bool(url and key)` reported Supabase
    as *configured* -- which pointed SupabaseStorage at the host `REPLACE_ME`.
    Scan-media uploads and curriculum snapshots would then fail with a DNS
    error on a deployment that otherwise looked perfectly healthy. Both the
    HTTP clients and Config must agree it means "absent".
    """
    from academicos.assessment.supabase_kv import SupabaseStorage, SupabaseTable
    from academicos.config import SUPABASE_PLACEHOLDER, Config

    monkeypatch.setenv("SUPABASE_KNOWLEDGE_URL", SUPABASE_PLACEHOLDER)
    monkeypatch.setenv("SUPABASE_KNOWLEDGE_ANON_KEY", SUPABASE_PLACEHOLDER)

    assert SupabaseTable("assessments").enabled is False
    assert SupabaseStorage("scan-media").enabled is False
    assert Config.load().supabase_enabled is False


def test_real_credentials_still_enable_supabase(monkeypatch) -> None:
    """Guard against over-correcting the placeholder rule into never enabling."""
    from academicos.assessment.supabase_kv import SupabaseStorage, SupabaseTable
    from academicos.config import Config

    monkeypatch.setenv("SUPABASE_KNOWLEDGE_URL", "https://proj.supabase.co/")
    monkeypatch.setenv("SUPABASE_KNOWLEDGE_ANON_KEY", "real-anon-key")

    table = SupabaseTable("assessments")
    assert table.enabled is True
    # The trailing slash must still be stripped, as it was before the refactor.
    assert table._url == "https://proj.supabase.co"
    assert SupabaseStorage("scan-media").enabled is True
    assert Config.load().supabase_enabled is True
