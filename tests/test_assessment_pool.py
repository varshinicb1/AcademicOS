"""assessment/pool.py::build_pool's registry-error handling.

Found live 2026-09-18 (an end-to-end verification session, not a report from
reading the code): a registry query failure (locked database, missing table,
any sqlite3.OperationalError) used to be swallowed into `rows = []` --
indistinguishable from "no question papers exist for this subject/grade".
get_pool() caches its result per (subject, grade) forever, so a single
transient failure at the wrong moment permanently zeroed out that subject/
grade's question pool for the rest of the process's life, with nothing in any
log to explain why. This file exists because pool.py had zero dedicated test
coverage before this fix -- its corpus-reading machinery is otherwise only
exercised indirectly through routes tests that always run against a healthy
registry.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.assessment import pool as pool_module
from academicos.assessment.pool import build_pool, get_pool
from academicos.config import Config


def _make_config_with_broken_registry(tmp_path: Path) -> Config:
    """A registry.sqlite that exists but is missing the `sources` table --
    the query itself raises sqlite3.OperationalError, the same exception
    class a locked database raises. Deterministic and fast, unlike actually
    contending a file lock from a second connection."""
    cfg = Config(data_root=tmp_path)
    conn = sqlite3.connect(cfg.registry_db)
    conn.execute("CREATE TABLE not_sources (id TEXT)")
    conn.commit()
    conn.close()
    return cfg


def test_build_pool_raises_on_registry_query_failure_instead_of_returning_empty(tmp_path):
    cfg = _make_config_with_broken_registry(tmp_path)
    with pytest.raises(sqlite3.OperationalError):
        build_pool(cfg, subject="Science", grade="X")


def test_get_pool_does_not_cache_a_failed_build(tmp_path, monkeypatch):
    """The real bug: get_pool's cache assignment must not run when the
    underlying build fails, or a transient error becomes permanent for the
    life of the process."""
    monkeypatch.setattr(pool_module, "_CACHE", {})
    cfg = _make_config_with_broken_registry(tmp_path)

    with pytest.raises(sqlite3.OperationalError):
        get_pool(cfg, subject="Science", grade="X")
    assert ("Science", "X") not in pool_module._CACHE, (
        "a failed build must not be cached -- otherwise every future call "
        "for this subject/grade silently replays the empty pool forever"
    )

    # Fix the registry (simulating the lock clearing / table existing on
    # retry) and confirm a subsequent call succeeds and *does* get cached --
    # proving the failure above didn't leave the pool machinery in a broken
    # state, only refused to memoize the bad result.
    conn = sqlite3.connect(cfg.registry_db)
    conn.execute(
        "CREATE TABLE sources (source_id TEXT, doc_type TEXT, subject TEXT, "
        "grade TEXT, academic_year TEXT)"
    )
    conn.commit()
    conn.close()
    pool = get_pool(cfg, subject="Science", grade="X")
    assert pool.questions == []
    assert ("Science", "X") in pool_module._CACHE
