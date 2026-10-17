"""R-A3 (NFR-2): rate limits hold across instances and restarts.

The cross-process tests start real Python processes against a real Postgres,
as the Cloud SQL adapter tests do (tests/test_postgres_kv.py), and skip
without one:

    $env:ACOS_TEST_PG_HOST="localhost"   (and _PORT, _DB, _USER, _PASSWORD)

CI runs them against its postgres:16 service. The fallback and naming tests
need no database.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from fastapi import HTTPException

from academicos.api import rate_limit as rl
from academicos.api.rate_limit import RateLimiter
from academicos.assessment import postgres_kv
from academicos.assessment.postgres_kv import PostgresUnavailable

SRC = Path(__file__).resolve().parents[1] / "src"


def _pg_env() -> dict[str, str] | None:
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


needs_pg = pytest.mark.skipif(_pg_env() is None, reason="set ACOS_TEST_PG_HOST to run the shared limiter tests")

# One app instance: it loads the module that defines the limiter and calls it.
_INSTANCE = r"""
import importlib, sys, time
module, attr, how, key, n, start = sys.argv[1:7]
limiter = getattr(importlib.import_module(module), attr)
from fastapi import HTTPException
while time.time() < float(start):
    time.sleep(0.005)
allowed = 0
for _ in range(int(n)):
    if how == "check":
        try:
            limiter.check(key)
            allowed += 1
        except HTTPException as exc:
            assert exc.status_code == 429, exc
    elif how == "record":
        limiter.record(key)
    else:
        allowed += limiter.blocked(key) is None
print(allowed)
"""


@pytest.fixture
def pg(monkeypatch):
    env = _pg_env()
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    postgres_kv.reset_pools()
    import psycopg
    with psycopg.connect(host=env["ACOS_POSTGRES_HOST"], port=env["ACOS_POSTGRES_PORT"],
                         dbname=env["ACOS_POSTGRES_DB"], user=env["ACOS_POSTGRES_USER"],
                         password=env["ACOS_POSTGRES_PASSWORD"], autocommit=True) as conn:
        conn.execute("DROP TABLE IF EXISTS rate_limit_hits")
    rl._SHARED._ready = False
    yield env
    postgres_kv.reset_pools()


def _instances(env, module, attr, how, key, per_instance, *, count=2):
    """`count` app processes, started together, each calling the limiter
    `per_instance` times; what each one was allowed."""
    child_env = {**os.environ, **env, "PYTHONPATH": str(SRC), "ACOS_TEST_RATE_LIMIT": "1"}
    child_env.pop("ACOS_DISABLE_RATE_LIMIT", None)
    start = time.time() + 4.0       # every process imported and waiting before the first call
    procs = [subprocess.Popen([sys.executable, "-c", _INSTANCE, module, attr, how, key, str(per_instance),
                               str(start)], env=child_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True) for _ in range(count)]
    out = []
    for p in procs:
        stdout, stderr = p.communicate(timeout=120)
        assert p.returncode == 0, stderr[-2000:]
        out.append(int(stdout.strip().splitlines()[-1]))
    return out


@needs_pg
def test_two_instances_share_the_sign_in_limit_exactly(pg):
    """300 sign-ins a minute per address: two instances racing 200 each are
    allowed 300 between them, not 300 each."""
    allowed = _instances(pg, "academicos.api.rate_limit", "login_limiter", "check", "login:203.0.113.7", 200)
    assert sum(allowed) == 300, allowed
    assert min(allowed) > 0, "both instances took part"


@needs_pg
def test_the_daily_code_limit_holds_across_instances_and_a_restart(pg):
    """30 code verifications a day per email: two instances allow 30 in all,
    and an instance started afterwards (a deploy) allows none."""
    module, attr, key = "academicos.operations.sign_in_codes", "_daily_verify_limiter", "email:asha@school.test"
    assert sum(_instances(pg, module, attr, "check", key, 20)) == 30
    assert _instances(pg, module, attr, "check", key, 5, count=1) == [0]
    # Another email is untouched.
    assert _instances(pg, module, attr, "check", "email:bala@school.test", 3, count=1) == [3]


@needs_pg
def test_wrong_passwords_on_one_instance_lock_the_account_on_another(pg):
    module, attr, key = "academicos.api.rate_limit", "account_failures", "login-failures:ana@school.test"
    _instances(pg, module, attr, "record", key, rl.ACCOUNT_FAILURES, count=1)
    assert _instances(pg, module, attr, "blocked", key, 1, count=1) == [0], "the second instance sees the lock"


@needs_pg
def test_limiters_with_the_same_key_do_not_share_hits(pg, monkeypatch):
    """`ip:...` is a key of both code limiters: each counts its own."""
    monkeypatch.setenv("ACOS_TEST_RATE_LIMIT", "1")
    a = RateLimiter(max_requests=1, window_seconds=60, name="test_a")
    b = RateLimiter(max_requests=1, window_seconds=60, name="test_b")
    a.check("ip:198.51.100.1")
    b.check("ip:198.51.100.1")
    with pytest.raises(HTTPException) as exc:
        a.check("ip:198.51.100.1")
    assert exc.value.status_code == 429 and int(exc.value.headers["Retry-After"]) >= 59


def test_a_cloud_sql_failure_falls_back_to_this_instances_memory(monkeypatch, caplog):
    """A database outage must not stop sign-in, nor lift the limit: the
    request is limited on this instance, and the failure is logged."""
    monkeypatch.setenv("ACOS_TEST_RATE_LIMIT", "1")
    monkeypatch.setattr(postgres_kv, "postgres_configured", lambda: True)

    def down(*_a, **_k):
        raise PostgresUnavailable(table="rate_limit_hits", op="take", body="connection refused")

    monkeypatch.setattr(rl._SHARED, "take", down)
    monkeypatch.setattr(rl._SHARED, "add", down)
    rl._warned_at.clear()
    limiter = RateLimiter(max_requests=2, window_seconds=60, name="test_fallback")
    limiter.check("k")
    limiter.check("k")
    with pytest.raises(HTTPException):
        limiter.check("k")
    limiter.record("f")
    assert limiter.blocked("f") is None
    assert sum("limiting on this instance only" in r.message for r in caplog.records) == 1, "logged once a minute"


def test_an_unnamed_limiter_never_touches_cloud_sql(monkeypatch):
    monkeypatch.setenv("ACOS_TEST_RATE_LIMIT", "1")
    monkeypatch.setattr(postgres_kv, "postgres_configured", lambda: True)
    monkeypatch.setattr(rl._SHARED, "take", lambda *a, **k: pytest.fail("an unnamed limiter is local"))
    limiter = RateLimiter(max_requests=1, window_seconds=60)
    limiter.check("k")
    with pytest.raises(HTTPException):
        limiter.check("k")


def test_every_limiter_the_app_defines_is_named_and_names_are_unique():
    """The keys repeat across limiters, so the name is what keeps their shared
    hits apart; an unnamed one would quietly stay per instance."""
    import importlib
    names = []
    for module in ("academicos.api.rate_limit", "academicos.operations.sign_in_codes",
                   "academicos.operations.google_sign_in"):
        for value in vars(importlib.import_module(module)).values():
            if isinstance(value, RateLimiter):
                names.append(value.name)
    assert len(names) == 7 and None not in names, names
    assert len(set(names)) == len(names), names
