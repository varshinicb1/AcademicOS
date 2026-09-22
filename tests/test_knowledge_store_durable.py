"""KnowledgeStore (per-student mastery history) persists through durable_table.

Why this exists: KnowledgeStore used to talk to Supabase's `learner_models`
over raw REST and read the Supabase env vars itself. The GCP deploy dropped
those secrets, and with them the store silently moved to local JSON under
/app -- which Cloud Run discards on every redeploy. Every student's history
would have vanished at each deploy with no error anywhere. It now resolves
its table through postgres_kv.durable_table like every other JSONB store, so
on GCP it lands in Cloud SQL.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import pytest

from academicos.assessment import knowledge as knowledge_mod
from academicos.assessment.evaluate import Evaluation
from academicos.assessment.knowledge import KnowledgeStore
from academicos.assessment.postgres_kv import PostgresTable
from academicos.assessment.schemas import (
    AnswerSchemeSchema,
    MarkingPointSchema,
    QuestionSchema,
)

ROOT = Path(__file__).resolve().parents[1]


class FakeTable:
    """durable_table's surface, in memory: one shared 'database' across every
    KnowledgeStore the test builds, like two containers sharing Cloud SQL."""

    def __init__(self, name: str, rows: dict):
        self.table = name
        self.rows = rows
        self.enabled = True

    def select(self, order=None, limit=None, gt=None, **eq):
        assert set(eq) == {"student_id"}
        row = self.rows.get(eq["student_id"])
        return [row] if row else []

    def upsert(self, row, on_conflict):
        assert on_conflict == "student_id"
        self.rows[row["student_id"]] = dict(row)


def _question() -> QuestionSchema:
    now = datetime.now(timezone.utc)
    scheme = AnswerSchemeSchema(
        total_marks=4,
        marking_points=[MarkingPointSchema(id="mp1", description="correct",
                                           marks=4, keyword="answer")],
        metadata={},
    )
    return QuestionSchema(
        id="q1", question_bank_id="bank1", subject="math", grade=10,
        chapter_ids=["c1"], competency_ids=[], bloom_level="understand",
        difficulty="medium", type="short_answer", stem="s", parts=[],
        answer_scheme=scheme, estimated_time_minutes=2, marks=4, language="en",
        source="teacher_created", quality_score=0.7, tags=[], created_at=now,
        updated_at=now,
    )


@pytest.fixture
def clean_env(monkeypatch):
    for name in ("SUPABASE_KNOWLEDGE_URL", "SUPABASE_KNOWLEDGE_ANON_KEY",
                 "ACOS_POSTGRES_HOST", "ACOS_POSTGRES_DB", "ACOS_POSTGRES_USER"):
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


def test_history_survives_a_fresh_container(clean_env, tmp_path: Path) -> None:
    """The redeploy scenario: container 1 records marks, container 2 starts
    with an empty disk and must still see them."""
    shared: dict = {}
    clean_env.setattr(knowledge_mod, "durable_table",
                      lambda name: FakeTable(name, shared))

    first = KnowledgeStore(tmp_path / "container1")
    ev = Evaluation(question_id="q1", awarded_marks=3, max_marks=4,
                    verdict="partial", confidence=0.9, reasoning="",
                    ocr_warnings=[], needs_review=False)
    first.record_evaluations("stu_1", [(_question(), ev)])
    assert list((tmp_path / "container1").iterdir()) == [], \
        "with a durable table configured nothing may land on container disk"

    second = KnowledgeStore(tmp_path / "container2")
    model = second.load("stu_1")
    assert model.concepts["c1"].attempts == 1
    assert model.concepts["c1"].history[0].outcome == 0.75


def test_uses_the_learner_models_table_via_durable_table(clean_env, tmp_path: Path) -> None:
    seen: list[str] = []

    def fake_durable_table(name):
        seen.append(name)
        return FakeTable(name, {})

    clean_env.setattr(knowledge_mod, "durable_table", fake_durable_table)
    KnowledgeStore(tmp_path)
    assert seen == ["learner_models"]


def test_cloud_sql_is_chosen_on_gcp(clean_env, tmp_path: Path) -> None:
    """Cloud SQL configured: the store is bound to Postgres, never to the
    Supabase REST path it used to hard-code."""
    clean_env.setenv("ACOS_POSTGRES_HOST", "/cloudsql/p:r:i")
    clean_env.setenv("ACOS_POSTGRES_DB", "academicos")
    clean_env.setenv("ACOS_POSTGRES_USER", "academicos")
    ks = KnowledgeStore(tmp_path)
    assert isinstance(ks._table, PostgresTable)
    assert ks._table.table == "learner_models"


def test_local_json_when_nothing_is_configured(clean_env, tmp_path: Path) -> None:
    ks = KnowledgeStore(tmp_path)
    assert ks._remote is False
    ev = Evaluation(question_id="q1", awarded_marks=4, max_marks=4,
                    verdict="correct", confidence=0.9, reasoning="",
                    ocr_warnings=[], needs_review=False)
    ks.record_evaluations("stu_1", [(_question(), ev)])
    assert (tmp_path / "stu_1.json").exists()


def test_cloud_sql_schema_and_migration_cover_learner_models() -> None:
    """The table must exist in Cloud SQL, and the Supabase rows already in
    learner_models must be copyable, or the port loses every existing
    student's history instead of the deploy doing so."""
    schema = (ROOT / "deploy" / "gcp" / "schema.sql").read_text(encoding="utf-8")
    assert re.search(r"CREATE TABLE IF NOT EXISTS learner_models\s*\(\s*student_id\s+TEXT PRIMARY KEY",
                     schema)
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "migrate_supabase_to_cloudsql", ROOT / "scripts" / "migrate_supabase_to_cloudsql.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.TABLES["learner_models"] == {
        "conflict": "student_id", "columns": ["student_id", "payload"]}


def test_health_probe_covers_learner_models() -> None:
    import academicos.api.main as main_mod
    assert "learner_models" in main_mod._DURABLE_TABLES
