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

    # MonkeyPatch, not a raw os.environ assignment: the environment is
    # process-wide, so it must be undone even when setup itself raises. The
    # previous version assigned os.environ BEFORE its try/finally, and CI
    # promptly demonstrated why that is wrong -- the psycopg driver was missing
    # there, the import blew up in setup, the finally never ran, and
    # ACOS_POSTGRES_* stayed set for the rest of the session. Every later test
    # then resolved its store to Postgres instead of Supabase/SQLite and failed
    # in a completely unrelated place (503 expected, 404 returned).
    mp = pytest.MonkeyPatch()
    try:
        for key, value in cfg.items():
            mp.setenv(key, value)
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
                              "school_templates", "audit_log", "papers",
                              "learner_models"):
                    cur.execute(f'TRUNCATE TABLE "{table}"')
        yield
    finally:
        postgres_kv.reset_pools()
        mp.undo()


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


# --------------------------------------------------------------------- #
# audit_log is append-only in the database (audit item 8.5, 2026-09-21)
# --------------------------------------------------------------------- #
# The SQLite half is proven locally in tests/test_grade_integrity.py. These
# prove deploy/gcp/schema.sql gives Postgres the same guarantees: the trigger
# refuses UPDATE and DELETE even for the owner role the service uses, and a
# plain insert of an existing id is SQLSTATE 23505, not an overwrite.

def test_audit_log_update_and_delete_are_refused_by_the_trigger() -> None:
    t = PostgresTable("audit_log")
    t.insert({"id": "log_locked", "timestamp": "2026-09-22T10:00:00+00:00",
              "action": "grade_awarded", "assessment_id": "asmLock",
              "student_id": "s1", "actor": "user_1", "details": {"after": 2}})
    with pytest.raises(PostgresUnavailable, match="append-only"):
        t.update({"actor": "someone-else"}, id="log_locked")
    with pytest.raises(PostgresUnavailable, match="append-only"):
        t.delete(id="log_locked")
    [row] = t.select(id="log_locked")
    assert row["actor"] == "user_1"


def test_insert_of_an_existing_id_is_a_unique_violation() -> None:
    from academicos.assessment.supabase_kv import is_unique_violation

    t = PostgresTable("audit_log")
    row = {"id": "log_once", "timestamp": "2026-09-22T10:00:00+00:00",
           "action": "grade_awarded", "assessment_id": "asmOnce",
           "student_id": "s1", "actor": "user_1", "details": {}}
    t.insert(row)
    with pytest.raises(PostgresUnavailable) as exc:
        t.insert({**row, "actor": "attacker"})
    assert is_unique_violation(exc.value)
    assert [r["actor"] for r in t.select(id="log_once")] == ["user_1"]


def test_audit_log_chain_and_replay_on_real_postgres(tmp_path) -> None:
    from academicos.assessment.audit_log import AuditLog, DuplicateAuditEntry

    log = AuditLog(tmp_path / "audit.sqlite")
    assert isinstance(log._remote, PostgresTable)
    ids = [log.append("grade_awarded", assessment_id="asmChain", student_id="s1",
                      actor="user_1", details={"after": i}) for i in range(3)]
    assert log.verify_chain() is None
    with pytest.raises(DuplicateAuditEntry):
        log.append("grade_awarded", assessment_id="asmChain", actor="attacker",
                   entry_id=ids[0])
    rows = PostgresTable("audit_log").select(assessment_id="asmChain", order="seq.asc")
    assert [r["id"] for r in rows] == ids
    assert rows[1]["prev_hash"] == rows[0]["entry_hash"]
    # Nothing reached the local fallback: the replay was refused, not rerouted.
    assert log.conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0] == 0


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


# --------------------------------------------------------------------- #
# Invite single use on REAL Postgres (Task 301 review, item 2)
# --------------------------------------------------------------------- #
# tests/test_auth_invites_remote.py proves the invite rules against an
# in-memory table that ASSUMES two things Postgres must actually provide:
# a conditional UPDATE filtered on used_at = '' AND revoked_at = '' matches
# at most once under concurrency (READ COMMITTED re-checks the WHERE after
# waiting on the row lock), and '' is a value equality can match. These run
# the same UserStore code on the real server with deploy/gcp/schema.sql.

@pytest.fixture
def pg_user_store(tmp_path):
    import psycopg
    from academicos.assessment.users import UserStore

    cfg = _test_cfg()
    assert cfg is not None
    with psycopg.connect(host=cfg["ACOS_POSTGRES_HOST"], port=cfg["ACOS_POSTGRES_PORT"],
                         dbname=cfg["ACOS_POSTGRES_DB"], user=cfg["ACOS_POSTGRES_USER"],
                         password=cfg["ACOS_POSTGRES_PASSWORD"], autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute('TRUNCATE TABLE "users", "sessions", "invites"')
    store = UserStore(tmp_path / "users.sqlite", principal_bootstrap_key="k")
    assert isinstance(store._remote_invites, PostgresTable)
    yield store
    store.conn.close()


def test_conditional_claim_matches_once_on_real_postgres(pg_user_store) -> None:
    code = pg_user_store.create_invite(school_id="s1", role="teacher", created_by="p1").code
    t = PostgresTable("invites")
    t.update({"used_by": "u1", "used_at": "t1"}, code=code, used_at="", revoked_at="")
    t.update({"used_by": "u2", "used_at": "t2"}, code=code, used_at="", revoked_at="")
    assert [r["used_by"] for r in t.select(code=code)] == ["u1"]


def test_many_threads_racing_on_one_invite_have_one_winner_on_real_postgres(
        pg_user_store) -> None:
    import threading

    from academicos.assessment.users import RegistrationRefused

    code = pg_user_store.create_invite(school_id="s1", role="teacher", created_by="p1").code
    n = 8
    barrier = threading.Barrier(n)
    winners, refused, errors = [], [], []

    def attempt(i: int) -> None:
        barrier.wait()
        try:
            winners.append(pg_user_store.register(
                invite_code=code, name=f"Racer {i}", email=f"racer-{i}@example.com",
                password="correct horse battery"))
        except RegistrationRefused:
            refused.append(i)
        except Exception as exc:  # noqa: BLE001 - reported below
            errors.append(exc)

    threads = [threading.Thread(target=attempt, args=(i,)) for i in range(n)]
    for th in threads:
        th.start()
    for th in threads:
        th.join(timeout=120)

    assert errors == []
    assert len(winners) == 1 and len(refused) == n - 1
    [row] = PostgresTable("invites").select(code=code)
    assert row["used_by"] == winners[0].id
    assert [u["email"] for u in PostgresTable("users").select()] == [winners[0].email]


def test_duplicate_email_on_real_postgres_is_email_already_registered(
        pg_user_store) -> None:
    """The unique index answers SQLSTATE 23505, which UserStore reports as
    EmailAlreadyRegistered and releases the loser's invite. Simulates the
    race by inserting the row directly after get_by_email would have passed."""
    from academicos.assessment.users import EmailAlreadyRegistered

    first = pg_user_store.create_invite(school_id="s1", role="teacher", created_by="p1").code
    second = pg_user_store.create_invite(school_id="s1", role="teacher", created_by="p1").code
    pg_user_store.register(invite_code=first, name="A", email="dup@example.com",
                           password="correct horse battery")
    # Skip the pre-check so the insert itself meets the index, as the loser
    # of a real race does.
    original = pg_user_store.get_by_email
    pg_user_store.get_by_email = lambda email: None  # type: ignore[method-assign]
    try:
        with pytest.raises(EmailAlreadyRegistered):
            pg_user_store.register(invite_code=second, name="B", email="dup@example.com",
                                   password="correct horse battery")
    finally:
        pg_user_store.get_by_email = original  # type: ignore[method-assign]
    [row] = PostgresTable("invites").select(code=second)
    assert (row["used_by"], row["used_at"]) == ("", "")
    assert len(PostgresTable("users").select(email="dup@example.com")) == 1

def test_knowledge_store_mastery_history_round_trips_through_real_jsonb(
        tmp_path: Path, monkeypatch) -> None:
    """KnowledgeStore writes its payload through psycopg's Jsonb and reads
    rows[0]["payload"] back expecting a dict. tests/test_knowledge_store_durable.py
    covers that only against an in-memory FakeTable; this is the real driver
    and the real column type. Also the migration guard on a real empty table."""
    from datetime import datetime, timezone
    from academicos.assessment.evaluate import Evaluation
    from academicos.assessment.knowledge import KnowledgeStore, LearnerModelsNotMigrated
    from academicos.assessment.schemas import (
        AnswerSchemeSchema, MarkingPointSchema, QuestionSchema)

    monkeypatch.delenv("ACOS_LEARNER_MODELS_ALLOW_EMPTY", raising=False)
    now = datetime.now(timezone.utc)
    question = QuestionSchema(
        id="q1", question_bank_id="bank1", subject="math", grade=10,
        chapter_ids=["c1"], competency_ids=[], bloom_level="understand",
        difficulty="medium", type="short_answer", stem="s", parts=[],
        answer_scheme=AnswerSchemeSchema(
            total_marks=4, metadata={},
            marking_points=[MarkingPointSchema(id="mp1", description="d", marks=4,
                                               keyword="k")]),
        estimated_time_minutes=2, marks=4, language="en", source="teacher_created",
        quality_score=0.7, tags=[], created_at=now, updated_at=now)
    ev = Evaluation(question_id="q1", awarded_marks=3, max_marks=4, verdict="partial",
                    confidence=0.9, reasoning="", ocr_warnings=[], needs_review=False)

    first = KnowledgeStore(tmp_path / "c1")
    assert isinstance(first._table, PostgresTable)
    with pytest.raises(LearnerModelsNotMigrated):      # table truncated above
        first.load("stu_pg")

    monkeypatch.setenv("ACOS_LEARNER_MODELS_ALLOW_EMPTY", "1")
    first.record_evaluations("stu_pg", [(question, ev)])
    monkeypatch.delenv("ACOS_LEARNER_MODELS_ALLOW_EMPTY")

    raw = PostgresTable("learner_models").select(student_id="stu_pg")[0]["payload"]
    assert isinstance(raw, dict), "JSONB must come back as an object, not a string"
    second = KnowledgeStore(tmp_path / "c2")            # a fresh container
    model = second.load("stu_pg")                       # a row exists: guard passes
    assert model.concepts["c1"].attempts == 1
    assert model.concepts["c1"].history[0].outcome == 0.75
