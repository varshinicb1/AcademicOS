"""The public catalog summarises each pool once: converting every question
on every call took ~1 s of CPU and a burst of catalog calls starved the one-CPU
release (production load check, 2026-10-01)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.api.main import app  # noqa: E402
from academicos.assessment import pillar_routes  # noqa: E402
from academicos.assessment import pool as pool_module  # noqa: E402

SERVED_BANK = ROOT / "academicos-data" / "syllabus" / "questions.json"


@pytest.mark.skipif(not SERVED_BANK.exists(), reason="served bank not built")
def test_catalog_converts_each_pool_once_and_answers_the_same(tmp_path, monkeypatch):
    calls = {"n": 0}
    real = pillar_routes.to_question_schema

    def counting(q):
        calls["n"] += 1
        return real(q)

    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr(pillar_routes, "to_question_schema", counting)
    pool_module._CACHE.clear()
    try:
        with TestClient(app) as client:
            # Under pytest a pool skips the baked bank unless asked (pool._load_baked_questions).
            pillar_routes._cfg._load_baked_questions = True
            first = client.get("/api/v1/catalog")
            assert first.status_code == 200
            after_first = calls["n"]
            assert after_first > 0 and first.json()["totalQuestions"] > 0, "the catalog read no questions"
            second = client.get("/api/v1/catalog")
            assert second.json() == first.json()
            assert calls["n"] == after_first, "the second call converted every question again"
            # A rebuilt pool is summarised afresh (the cache lives on the pool).
            pool_module._CACHE.clear()
            client.get("/api/v1/catalog")
            assert calls["n"] == 2 * after_first
    finally:
        pool_module._CACHE.clear()


def test_pool_warmup_is_off_under_pytest_and_by_switch(monkeypatch):
    """The boot warm-up never runs in the suite (tests swap banks), and an
    operator can turn it off; otherwise it starts one daemon thread."""
    import threading
    started = []
    monkeypatch.setattr(threading, "Thread", lambda *a, **k: started.append(k) or type(
        "T", (), {"start": lambda self: None})())
    pillar_routes._start_pool_warmup(pillar_routes._cfg or object())
    assert started == [], "warm-up ran under pytest"
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setenv("ACOS_WARM_POOLS", "0")
    pillar_routes._start_pool_warmup(object())
    assert started == []
    monkeypatch.setenv("ACOS_WARM_POOLS", "1")
    pillar_routes._start_pool_warmup(object())
    assert len(started) == 1 and started[0]["daemon"] is True and started[0]["name"] == "pool-warmup"
