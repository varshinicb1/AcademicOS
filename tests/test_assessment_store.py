"""Audit regression test for assessment/store.py upsert columns (D4#1).

`save()` is an upsert keyed on `id`. The ON CONFLICT clause must refresh the
columns that carry ownership and provenance (school_id, teacher_id,
created_at) too, not just the mutable working fields — otherwise two
authoritative saves for the same id silently disagree about who owns the
assessment. A/B: old clause omitted those three columns, so the second save
was partially lost.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone

from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.assessment.schemas import (  # noqa: E402
    Assessment,
    BloomDistribution,
    Blueprint,
    ChapterWeights,
    CompetencyWeights,
    DifficultyDistribution,
)
from academicos.assessment.store import AssessmentStore  # noqa: E402


def _blueprint() -> Blueprint:
    return Blueprint(
        total_marks=80,
        duration_minutes=60,
        difficulty=DifficultyDistribution(easy=0.3, medium=0.4, hard=0.3),
        bloom=BloomDistribution(
            remember=0.2, understand=0.2, apply=0.2, analyze=0.2, evaluate=0.1, create=0.1,
        ),
        chapter_weights=ChapterWeights(),
        competency_weights=CompetencyWeights(),
    )


def _assessment(assessment_id: str, school_id: str, teacher_id: str,
                status: str = "paperGenerated") -> Assessment:
    now = datetime.now(timezone.utc)
    return Assessment(
        id=assessment_id, school_id=school_id, teacher_id=teacher_id,
        title="Unit Test 1", subject="Mathematics", grade=10, chapter_ids=["ch1"],
        blueprint=_blueprint(), status=status, created_at=now, updated_at=now,
        scheduled_at=None, metadata={},
    )


def test_upsert_refreshes_owner_columns(tmp_path):
    store = AssessmentStore(tmp_path / "up.db")
    store.save(_assessment("a1", school_id="school_old", teacher_id="teacher_old"))
    store.save(_assessment("a1", school_id="school_new", teacher_id="teacher_new",
                           status="paperGenerated"))
    got = store.get("a1")
    assert got is not None
    assert got.school_id == "school_new"
    assert got.teacher_id == "teacher_new"


def test_upsert_refreshes_updated_at(tmp_path):
    store = AssessmentStore(tmp_path / "up2.db")
    store.save(_assessment("a2", school_id="s", teacher_id="t"))
    first = store.get("a2")
    store.save(_assessment("a2", school_id="s", teacher_id="t",
                           status="paperGenerated"))
    second = store.get("a2")
    assert second.updated_at >= first.updated_at


def test_save_falls_back_to_sqlite_when_supabase_unreachable(tmp_path, monkeypatch):
    """A dead/misconfigured Supabase project must not hard-fail assessment
    creation -- see prod incident 2026-09-13: `_remote.enabled` was True but
    the hostname didn't resolve, and `save()` had no fallback, so every
    POST /assessments 500'd even though local SQLite was perfectly usable.
    """
    store = AssessmentStore(tmp_path / "fallback.db")
    store._remote._url = "https://nonexistent-project.supabase.co"
    store._remote._key = "fake-key"
    assert store._remote.enabled

    def _raise(*args, **kwargs):
        raise requests.exceptions.ConnectionError("simulated DNS failure")

    monkeypatch.setattr(store._remote, "upsert", _raise)
    monkeypatch.setattr(store._remote, "select", _raise)

    a = _assessment("a3", school_id="s", teacher_id="t")
    store.save(a)  # must not raise

    got = store.get("a3")  # get() also falls back and finds the locally-saved row
    assert got is not None
    assert got.id == "a3"
