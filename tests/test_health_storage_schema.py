"""/health/storage names a table the Cloud SQL schema is missing.

Why this exists: deploy/gcp/schema.sql gained `learner_models` (KnowledgeStore,
2026-09-22), and nothing applies schema.sql to an existing Cloud SQL instance
-- not the workflow, not bootstrap.sh. On an already-provisioned service every
mastery read and write then answers 503 ("relation does not exist") while the
deploy's own check, GET /health, answers 200. /health/storage now reports, for
every required table, whether it exists, and a top-level `status` that is not
"ok" while any is missing; scripts/apply_cloudsql_schema.sh is the fix.

The required-table list is ONE list, main.py's _DURABLE_TABLES (the tables
the stores actually open); the test below pins it to exactly the tables
schema.sql creates, so neither can gain a table the other lacks. schema.sql
itself is not read at runtime: deploy/ is not in the container image.

No database: the Postgres adapter is replaced by a fake that raises exactly
what PostgresTable raises for a missing relation -- PostgresUnavailable caused
by psycopg's UndefinedTable (SQLSTATE 42P01).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

import academicos.api.main as main_mod
from academicos.assessment import postgres_kv
from academicos.assessment.postgres_kv import PostgresUnavailable

SCHEMA = Path(__file__).resolve().parents[1] / "deploy" / "gcp" / "schema.sql"


class FakeUndefinedTable(Exception):
    """Stands in for psycopg.errors.UndefinedTable."""
    sqlstate = "42P01"


class FakeConnectionError(Exception):
    """Stands in for psycopg.OperationalError: no SQLSTATE for a missing table."""
    sqlstate = "08006"


class FakePostgresTable:
    def __init__(self, name: str, missing: set[str], down: bool):
        self.name, self.missing, self.down = name, missing, down

    def select(self, **_kw):
        if self.down:
            cause = FakeConnectionError("could not connect to server")
            raise PostgresUnavailable(table=self.name, op="select", body=str(cause),
                                      cause=cause) from cause
        if self.name in self.missing:
            cause = FakeUndefinedTable(f'relation "{self.name}" does not exist')
            raise PostgresUnavailable(table=self.name, op="select", body=str(cause),
                                      cause=cause) from cause
        return []


@pytest.fixture
def cloud_sql(monkeypatch):
    """Cloud SQL as the active backend, with a fake adapter. Call the yielded
    function with the tables to leave out (and down=True for an outage)."""
    for name in ("SUPABASE_KNOWLEDGE_URL", "SUPABASE_KNOWLEDGE_ANON_KEY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(postgres_kv, "postgres_configured", lambda: True)

    def configure(*missing: str, down: bool = False) -> None:
        monkeypatch.setattr(main_mod, "durable_table",
                            lambda name: FakePostgresTable(name, set(missing), down))
        main_mod._probe_cache.update(at=0.0, body=None)   # no stale verdicts

    yield configure
    main_mod._probe_cache.update(at=0.0, body=None)


def _schema_tables() -> set[str]:
    text = SCHEMA.read_text(encoding="utf-8")
    return set(re.findall(r"(?im)^\s*CREATE TABLE IF NOT EXISTS\s+([a-z_]+)\s*\(", text))


def test_required_tables_are_exactly_what_schema_sql_creates() -> None:
    assert _schema_tables(), "the regex found no tables; this test would be vacuous"
    assert set(main_mod._DURABLE_TABLES) == _schema_tables()


def test_a_missing_table_is_named_and_status_is_not_ok(cloud_sql) -> None:
    cloud_sql("learner_models")
    body = main_mod.health_storage()
    assert body["durability_backend"] == "cloudsql"
    assert body["status"] != "ok"
    assert body["missing_tables"] == ["learner_models"]
    assert body["table_exists"]["learner_models"] is False
    assert all(body["table_exists"][t] is True
               for t in main_mod._DURABLE_TABLES if t != "learner_models")
    assert body["tables"]["learner_models"].startswith("error:")
    assert "apply_cloudsql_schema.sh" in body["status_detail"]


def test_every_table_present_is_ok(cloud_sql) -> None:
    cloud_sql()
    body = main_mod.health_storage()
    assert body["status"] == "ok"
    assert body["missing_tables"] == []
    assert set(body["table_exists"]) == set(main_mod._DURABLE_TABLES)
    assert all(body["table_exists"].values())


def test_an_outage_is_not_reported_as_a_missing_table(cloud_sql) -> None:
    """Unreachable Cloud SQL says nothing about the schema; telling an operator
    to re-apply schema.sql during an outage would send them the wrong way."""
    cloud_sql(down=True)
    body = main_mod.health_storage()
    assert body["status"] == "unreachable"
    assert body["missing_tables"] == []
    assert all(v is None for v in body["table_exists"].values())


def test_no_backend_has_its_own_status(monkeypatch) -> None:
    for name in ("SUPABASE_KNOWLEDGE_URL", "SUPABASE_KNOWLEDGE_ANON_KEY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(postgres_kv, "postgres_configured", lambda: False)
    body = main_mod.health_storage()
    assert body["durability_backend"] == "none"
    assert body["status"] == "unconfigured"
    assert body["missing_tables"] == []


def test_the_fix_is_one_command_and_the_runbook_requires_it() -> None:
    """The health message points at a script; the script must exist, apply
    schema.sql through the Cloud SQL proxy path the bootstrap documents, and
    the deploy runbook must make it a required step."""
    root = SCHEMA.parents[2]
    script = (root / "scripts" / "apply_cloudsql_schema.sh").read_text(encoding="utf-8")
    assert "gcloud sql connect" in script
    assert "deploy/gcp/schema.sql" in script
    assert "set -euo pipefail" in script
    runbook = (root / "docs" / "gcp-deployment.md").read_text(encoding="utf-8")
    assert "scripts/apply_cloudsql_schema.sh" in runbook
    assert re.search(r"before the first deploy.*after (any|every) (change to|schema change)",
                     runbook, re.IGNORECASE | re.DOTALL)
