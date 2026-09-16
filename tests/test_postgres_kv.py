"""Cloud SQL durability-backend tests (assessment/postgres_kv.py).

These run against a REAL PostgreSQL server, never a mock. `PostgresTable`
replaces an HTTP/REST client (SupabaseTable) whose behaviour is entirely
defined by SQL semantics -- upsert conflict resolution, ORDER BY, LIMIT,
`>` pagination, NULL/JSONB round-tripping. Mocking that would test nothing
and would have hidden exactly the bugs this backend exists to avoid
(text-vs-integer ordering, boolean-vs-text filters, composite conflict
targets).

Point them at any throwaway database:

    $env:ACOS_TEST_PG_HOST="localhost"
    $env:ACOS_TEST_PG_PORT="5432"
    $env:ACOS_TEST_PG_DB="academicos_verify"
    $env:ACOS_TEST_PG_USER="postgres"
    $env:ACOS_TEST_PG_PASSWORD="..."

Without those they skip, so the default suite stays hermetic.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from academicos.assessment import postgres_kv
from academicos.assessment.postgres_kv import (
    PostgresTable,
    PostgresUnavailable,
    durable_table,
)

_SQL = Path(__file__).resolve().parents[1] / "deploy" / "gcp" / "schema.sql"


def _test_cfg() -> dict[str, str] | None:
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


pytestmark = pytest.mark.skipif(
    _test_cfg() is None,
    reason="set ACOS_TEST_PG_HOST (and friends) to run Cloud SQL adapter tests",
)


@pytest.fixture(scope="module", autouse=True)
def _configure_and_migrate():
    cfg = _test_cfg()
    assert cfg is not None
    saved = {k: os.environ.get(k) for k in cfg}
    os.environ.update(cfg)
    postgres_kv.reset_pools()

    import psycopg
    conn_kwargs = {
        "host": cfg["ACOS_POSTGRES_HOST"],
        "port": cfg["ACOS_POSTGRES_PORT"],
        "dbname": cfg["ACOS_POSTGRES_DB"],
        "user": cfg["ACOS_POSTGRES_USER"],
        "password": cfg["ACOS_POSTGRES_PASSWORD"],
    }
    schema = _SQL.read_text(encoding="utf-8")
    with psycopg.connect(**conn_kwargs, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(schema)
            # Deterministic starting state for the tables these tests touch.
            for table in ("assessments", "graded_evaluations", "learner_events",
                          "school_templates", "audit_log", "papers"):
                cur.execute(f'TRUNCATE TABLE "{table}"')
    try:
        yield
    finally:
        postgres_kv.reset_pools()
        for k, previous in saved.items():
            if previous is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = previous


def test_configured_and_selected_by_durable_table() -> None:
    assert postgres_kv.postgres_configured() is True
    # With Cloud SQL configured, the factory must prefer it over Supabase.
    assert isinstance(durable_table("assessments"), PostgresTable)


def test_upsert_select_jsonb_roundtrip() -> None:
    t = PostgresTable("assessments")
    payload = {"id": "a1", "title": "Unit Test", "nested": {"marks": [1, 2, 3]},
               "unicode": "अध्याय"}
    t.upsert({"id": "a1", "school_id": "s1", "teacher_id": "t1",
              "created_at": "2026-09-16T10:00:00+00:00", "payload": payload},
             on_conflict="id")

    rows = t.select(id="a1")
    assert len(rows) == 1
    # JSONB must come back as a real object, not a JSON string.
    assert rows[0]["payload"] == payload
    assert rows[0]["payload"]["nested"]["marks"] == [1, 2, 3]
    assert rows[0]["school_id"] == "s1"


def test_upsert_updates_in_place_on_conflict() -> None:
    t = PostgresTable("assessments")
    t.upsert({"id": "a2", "school_id": "s1", "teacher_id": "t1",
              "created_at": "2026-09-16T10:00:00+00:00",
              "payload": {"status": "draft"}}, on_conflict="id")
    t.upsert({"id": "a2", "school_id": "s1", "teacher_id": "t1",
              "created_at": "2026-09-16T10:00:00+00:00",
              "payload": {"status": "approved"}}, on_conflict="id")

    rows = t.select(id="a2")
    assert len(rows) == 1, "upsert must not create a duplicate row"
    assert rows[0]["payload"]["status"] == "approved"


def test_composite_conflict_target() -> None:
    """graded_store upserts on_conflict='assessment_id,student_id'."""
    t = PostgresTable("graded_evaluations")
    t.upsert({"assessment_id": "asm1", "student_id": "stu1", "payload": {"score": 3}},
             on_conflict="assessment_id,student_id")
    t.upsert({"assessment_id": "asm1", "student_id": "stu1", "payload": {"score": 5}},
             on_conflict="assessment_id,student_id")

    rows = t.select(assessment_id="asm1")
    assert len(rows) == 1
    assert rows[0]["payload"]["score"] == 5


def test_order_limit_and_gt_pagination() -> None:
    """EventStore pages with order='seq.asc', gt={'seq': n}, limit=k."""
    t = PostgresTable("learner_events")
    for seq in range(1, 13):  # 12 so "10" > "9" would expose text ordering
        t.upsert({"event_id": f"e{seq}", "learner_id": "L1", "seq": seq,
                  "kind": "practice", "ts": f"2026-09-16T10:{seq:02d}:00+00:00",
                  "payload": {"n": seq}}, on_conflict="event_id")

    first = t.select(learner_id="L1", order="seq.asc", limit=2)
    assert [r["seq"] for r in first] == [1, 2]

    after_nine = t.select(learner_id="L1", order="seq.asc", gt={"seq": 9})
    # Integer comparison: 10, 11, 12 -- not 9-text ordering.
    assert [r["seq"] for r in after_nine] == [10, 11, 12]

    newest = t.select(learner_id="L1", order="seq.desc", limit=1)
    assert newest[0]["seq"] == 12


def test_select_with_no_filters_returns_all() -> None:
    """graded_store.all_student_ids() calls select() with no filters."""
    t = PostgresTable("graded_evaluations")
    t.upsert({"assessment_id": "asmX", "student_id": "sA", "payload": {}},
             on_conflict="assessment_id,student_id")
    t.upsert({"assessment_id": "asmX", "student_id": "sB", "payload": {}},
             on_conflict="assessment_id,student_id")
    rows = t.select()
    assert {"sA", "sB"} <= {r["student_id"] for r in rows}


def test_boolean_stored_as_text_filters_and_sorts_like_supabase() -> None:
    """school_templates filters is_default='true' and orders by it DESC.

    The caller passes a real Python bool on write and the literal string
    "true" on read -- both must resolve consistently.
    """
    t = PostgresTable("school_templates")
    t.upsert({"id": "tpl_default", "school_id": "sZ", "is_default": True,
              "payload": {"template": {"id": "tpl_default"}, "sections": []}},
             on_conflict="id")
    t.upsert({"id": "tpl_other", "school_id": "sZ", "is_default": False,
              "payload": {"template": {"id": "tpl_other"}, "sections": []}},
             on_conflict="id")

    hits = t.select(school_id="sZ", **{"is_default": "true"})
    assert [r["id"] for r in hits] == ["tpl_default"]

    ordered = t.select(school_id="sZ", order="is_default.desc")
    assert ordered[0]["id"] == "tpl_default", "default template must sort first"


def test_update_and_delete() -> None:
    t = PostgresTable("school_templates")
    t.upsert({"id": "tpl_up", "school_id": "sU", "is_default": False,
              "payload": {"v": 1}}, on_conflict="id")

    t.update({"is_default": True}, school_id="sU")
    assert t.select(id="tpl_up")[0]["is_default"] == "true"

    t.delete(id="tpl_up")
    assert t.select(id="tpl_up") == []


def test_audit_log_uses_details_jsonb_column() -> None:
    """audit_log is the one table whose JSONB column is named `details`."""
    t = PostgresTable("audit_log")
    t.upsert({"id": "log1", "timestamp": "2026-09-16T10:00:00+00:00",
              "action": "quick_paper_generated", "assessment_id": "asmA",
              "student_id": None, "actor": "user_1",
              "details": {"paperId": "paper_1", "setCount": 2}}, on_conflict="id")
    rows = t.select(action="quick_paper_generated", order="timestamp.desc")
    assert rows[0]["details"]["setCount"] == 2


def test_unsafe_identifier_is_rejected() -> None:
    with pytest.raises(ValueError):
        PostgresTable('assessments"; DROP TABLE users; --')
    t = PostgresTable("assessments")
    with pytest.raises(ValueError):
        t.select(**{'id"); DROP TABLE users; --': "x"})


def test_unavailable_is_caught_by_the_existing_supabase_handler() -> None:
    """Stores catch SupabaseUnavailable for their SQLite fallback, and
    api/main.py has an app-level handler for it. PostgresUnavailable must be
    a subclass or every one of those would break."""
    from academicos.assessment.supabase_kv import SupabaseUnavailable
    import requests.exceptions as rexc

    assert issubclass(PostgresUnavailable, SupabaseUnavailable)
    assert issubclass(PostgresUnavailable, rexc.RequestException)
