"""Rate limiting for sensitive endpoints (auth brute-force protection).

A limiter is a sliding window of hits per key. A named limiter keeps its hits
in Cloud SQL whenever Cloud SQL is configured (R-A3, NFR-2), so every
instance and every restart counts the same hits: with `--max-instances=2` a
limit is not doubled, and a deploy does not reset a teacher's daily
sign-in-code allowance. Without Cloud SQL (local development, tests) and for an
unnamed limiter, hits are kept in this process's memory, as they always were.

Shared hits (table `rate_limit_hits`, created by the first limiter that needs
it, since the rows are disposable and no store reads them):

- one row per hit, timed by the database's clock, never the instance's, so
  two instances agree on the window;
- each check runs in one transaction holding an advisory lock on the
  (limiter, key) pair, so two instances cannot both take the last slot;
- expired rows go as their key is checked, and a limiter's stale rows at most
  once a minute.

If Cloud SQL fails mid-request, the limiter falls back to this instance's
memory for that request and logs it (at most once a minute): limits still
hold per instance, and a database outage never turns into a sign-in outage
of its own.
"""
from __future__ import annotations

import collections
import logging
import os
import threading
import time
from typing import Any, Callable, Optional

from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)

_TABLE = "rate_limit_hits"
_DDL = (
    "CREATE TABLE IF NOT EXISTS rate_limit_hits ("
    " limiter TEXT NOT NULL, key TEXT NOT NULL, at TIMESTAMPTZ NOT NULL DEFAULT now())",
    "CREATE INDEX IF NOT EXISTS idx_rate_limit_hits ON rate_limit_hits (limiter, key, at)",
)
# Two instances creating the table at once collide in the catalog; this lock
# makes the second wait for the first.
_DDL_LOCK = 7_360_224_501
_SWEEP_EVERY_S = 60.0
_WARN_EVERY_S = 60.0


class _SharedHits:
    """The hits of every named limiter, in Cloud SQL."""

    def __init__(self) -> None:
        self._ready = False
        self._ready_lock = threading.Lock()
        self._swept: dict[str, float] = {}

    def _run(self, op: str, fn: Callable[[Any], Any]) -> Any:
        from ..assessment.postgres_kv import PostgresUnavailable, _get_pool
        pool = _get_pool()
        if pool is None:
            raise PostgresUnavailable(table=_TABLE, op=op, body="Cloud SQL is not configured")
        try:
            with pool.connection() as conn:
                if not self._ready:
                    with self._ready_lock:
                        if not self._ready:
                            with conn.cursor() as cur:
                                cur.execute("SELECT pg_advisory_xact_lock(%s)", (_DDL_LOCK,))
                                for sql in _DDL:
                                    cur.execute(sql)
                            conn.commit()
                            self._ready = True
                with conn.cursor() as cur:
                    return fn(cur)
        except PostgresUnavailable:
            raise
        except Exception as exc:  # noqa: BLE001 - normalised so the limiter can fall back
            raise PostgresUnavailable(table=_TABLE, op=op, body=str(exc)[:300], cause=exc) from exc

    def take(self, name: str, key: str, limit: int, window: float, *, count: bool) -> Optional[int]:
        """Seconds until `key` may try again, or None; with `count`, a None also records the hit."""
        def fn(cur: Any) -> Optional[int]:
            cur.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", (f"{name}\x1f{key}",))
            if time.monotonic() - self._swept.get(name, 0.0) > _SWEEP_EVERY_S:
                cur.execute("DELETE FROM rate_limit_hits WHERE limiter = %s"
                            " AND at <= now() - make_interval(secs => %s)", (name, window))
                self._swept[name] = time.monotonic()
            else:
                cur.execute("DELETE FROM rate_limit_hits WHERE limiter = %s AND key = %s"
                            " AND at <= now() - make_interval(secs => %s)", (name, key, window))
            cur.execute("SELECT count(*), EXTRACT(EPOCH FROM min(at) + make_interval(secs => %s) - now())"
                        " FROM rate_limit_hits WHERE limiter = %s AND key = %s", (window, name, key))
            hits, left = cur.fetchone()
            if hits >= limit:
                return max(1, int(left or 0) + 1)
            if count:
                cur.execute("INSERT INTO rate_limit_hits (limiter, key) VALUES (%s, %s)", (name, key))
            return None
        return self._run("take", fn)

    def add(self, name: str, key: str) -> None:
        self._run("add", lambda cur: cur.execute(
            "INSERT INTO rate_limit_hits (limiter, key) VALUES (%s, %s)", (name, key)))

    def clear(self, name: str) -> None:
        self._run("clear", lambda cur: cur.execute("DELETE FROM rate_limit_hits WHERE limiter = %s", (name,)))


_SHARED = _SharedHits()
_LOCAL = object()          # "no shared answer: use this instance's memory"
_warned_at: dict[str, float] = {}


def _fell_back(name: str, exc: Exception) -> None:
    now = time.monotonic()
    if now - _warned_at.get(name, -_WARN_EVERY_S) >= _WARN_EVERY_S:
        _warned_at[name] = now
        logger.warning("rate limiter %s: Cloud SQL failed (%s); limiting on this instance only", name, exc)


class RateLimiter:
    """Thread-safe sliding-window rate limiter. `name` shares it across
    instances through Cloud SQL (see the module docstring); every limiter the
    app defines has one, and names must be unique, because the keys are not
    (`ip:...` and `email:...` are used by more than one limiter)."""

    def __init__(self, max_requests: int, window_seconds: float, name: Optional[str] = None):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.name = name
        self._records: dict[str, collections.deque[float]] = collections.defaultdict(collections.deque)
        self._lock = threading.Lock()

    def _shared(self) -> Optional[_SharedHits]:
        if self.name is None:
            return None
        from ..assessment.postgres_kv import postgres_configured
        return _SHARED if postgres_configured() else None

    def _ask_shared(self, key: str, *, count: bool) -> Any:
        """The shared answer (seconds to wait, or None), or `_LOCAL` when there is none."""
        shared = self._shared()
        if shared is None:
            return _LOCAL
        from ..assessment.postgres_kv import PostgresUnavailable
        try:
            return shared.take(str(self.name), key, self.max_requests, self.window_seconds, count=count)
        except PostgresUnavailable as exc:
            _fell_back(str(self.name), exc)
            return _LOCAL

    def _memory_take(self, key: str, *, count: bool) -> Optional[int]:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            queue = self._records[key]
            # Evict timestamps older than the sliding window
            while queue and queue[0] <= cutoff:
                queue.popleft()
            if len(queue) >= self.max_requests:
                return max(1, int(queue[0] - cutoff) + 1)
            if count:
                queue.append(now)
        return None

    def check(self, key: str) -> None:
        """Check if request is permitted; raise HTTP 429 if window limit exceeded."""
        if self._bypassed():
            return
        retry_after = self._ask_shared(key, count=True)
        if retry_after is _LOCAL:
            retry_after = self._memory_take(key, count=True)
        if retry_after is not None:
            logger.warning("Rate limit exceeded for key %s (max %d in %ds)", key, self.max_requests, self.window_seconds)
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Please try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)},
            )

    def _bypassed(self) -> bool:
        if os.environ.get("ACOS_DISABLE_RATE_LIMIT", "").strip().lower() in ("1", "true", "yes"):
            return True
        # In automated pytest suites, bypass rate limiting unless explicitly testing it
        return "PYTEST_CURRENT_TEST" in os.environ and not os.environ.get("ACOS_TEST_RATE_LIMIT")

    def blocked(self, key: str) -> Optional[int]:
        """Seconds until `key` may try again, or None. Records nothing: for
        a limit on failures, checked before the attempt and counted after it
        fails (`record`)."""
        if self._bypassed():
            return None
        wait = self._ask_shared(key, count=False)
        return self._memory_take(key, count=False) if wait is _LOCAL else wait

    def record(self, key: str) -> None:
        """Count one event (a failed attempt) against `key`."""
        if self._bypassed():
            return
        shared = self._shared()
        if shared is not None:
            from ..assessment.postgres_kv import PostgresUnavailable
            try:
                shared.add(str(self.name), key)
                return
            except PostgresUnavailable as exc:
                _fell_back(str(self.name), exc)
        with self._lock:
            self._records[key].append(time.monotonic())

    def reset(self) -> None:
        """Clear all tracked hits (test isolation), shared ones included."""
        with self._lock:
            self._records.clear()
        shared = self._shared()
        if shared is not None:
            shared.clear(str(self.name))


# Per network (client IP): generous, because a school's whole class signs in
# or registers from one NAT address at once -- 20 sign-ins and 10
# registrations a minute per IP turned the 21st student in a room away
# (audit N-9-4; production check 2026-10-01). Brute force is stopped per
# account instead: a password guessed against one email is refused after
# `ACCOUNT_FAILURES` wrong tries in the window, from any number of addresses.
login_limiter = RateLimiter(max_requests=300, window_seconds=60.0, name="login")
register_limiter = RateLimiter(max_requests=120, window_seconds=60.0, name="register")
ACCOUNT_FAILURES = 10
account_failures = RateLimiter(max_requests=ACCOUNT_FAILURES, window_seconds=15 * 60.0,
                               name="account_failures")


def get_client_ip(request: Request) -> str:
    """Extract real client IP, respecting standard reverse-proxy headers.

    Security fix 2026-09-17 (flagged by automated review): this used to take
    the FIRST (leftmost) value in X-Forwarded-For, which is exactly backwards
    -- the leftmost entry is whatever the ORIGINAL client claimed, so an
    attacker sending `X-Forwarded-For: 1.2.3.4` (or a fresh fake value on
    every request) reset their own rate-limit bucket key on demand,
    completely defeating the brute-force protection this file exists for.

    Both real deployment targets (Render and Cloud Run, see
    docs/PRODUCTS_AND_RELEASES.md) sit their app behind a managed edge proxy
    that APPENDS the true connecting peer's IP as the last hop rather than
    trusting/forwarding whatever the client sent -- so the rightmost value is
    the one the platform itself vouches for, not something a remote client
    can control. There's no fixed, publishable IP allowlist for either
    platform's edge (it's managed infrastructure, not a static IP range), so
    "trust only a known proxy IP" isn't practical here; taking the last hop
    is the standard mitigation when you can't pin the proxy's own address.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        hops = [h.strip() for h in forwarded.split(",") if h.strip()]
        if hops:
            return hops[-1]
    return request.client.host if request.client else "unknown"


def rate_limit_login(request: Request) -> None:
    """FastAPI dependency for login endpoint rate limiting."""
    client_ip = get_client_ip(request)
    login_limiter.check(f"login:{client_ip}")


def rate_limit_register(request: Request) -> None:
    """FastAPI dependency for register endpoint rate limiting."""
    client_ip = get_client_ip(request)
    register_limiter.check(f"register:{client_ip}")
