import pytest
from fastapi import HTTPException

from academicos.api.rate_limit import RateLimiter, login_limiter, register_limiter


def test_rate_limiter_basic_window(monkeypatch):
    monkeypatch.setenv("ACOS_TEST_RATE_LIMIT", "1")
    limiter = RateLimiter(max_requests=3, window_seconds=10.0)
    limiter.reset()

    # First 3 should pass without exception
    limiter.check("user1")
    limiter.check("user1")
    limiter.check("user1")

    # 4th request from same key must raise 429
    with pytest.raises(HTTPException) as exc_info:
        limiter.check("user1")
    assert exc_info.value.status_code == 429
    assert "Rate limit exceeded" in exc_info.value.detail
    assert "Retry-After" in exc_info.value.headers

    # Different key should still pass
    limiter.check("user2")

    # Reset clears records
    limiter.reset()
    limiter.check("user1")


def test_rate_limiter_env_disable(monkeypatch):
    monkeypatch.setenv("ACOS_TEST_RATE_LIMIT", "1")
    limiter = RateLimiter(max_requests=1, window_seconds=10.0)
    limiter.reset()
    limiter.check("user1")

    monkeypatch.setenv("ACOS_DISABLE_RATE_LIMIT", "1")
    # Should not raise even though limit was 1
    limiter.check("user1")
    limiter.check("user1")


def test_auth_route_rate_limiting_triggers_429(tmp_path, monkeypatch):
    from test_assessment_routes_auth import _boot_client

    # Ensure rate limit is active
    monkeypatch.setenv("ACOS_TEST_RATE_LIMIT", "1")
    monkeypatch.delenv("ACOS_DISABLE_RATE_LIMIT", raising=False)
    login_limiter.reset()
    login_limiter.max_requests = 2  # temporarily lower threshold for quick test

    with _boot_client(tmp_path, monkeypatch) as client:
        # Attempt 1 -> 401 (invalid creds, not 429)
        r1 = client.post("/api/v1/auth/login", json={"email": "bad@test.com", "password": "wrongpassword"})
        assert r1.status_code == 401

        # Attempt 2 -> 401
        r2 = client.post("/api/v1/auth/login", json={"email": "bad@test.com", "password": "wrongpassword"})
        assert r2.status_code == 401

        # Attempt 3 -> 429 Too Many Requests
        r3 = client.post("/api/v1/auth/login", json={"email": "bad@test.com", "password": "wrongpassword"})
        assert r3.status_code == 429
        assert "Rate limit exceeded" in r3.json()["detail"]

    # Restore default
    login_limiter.max_requests = 20
    login_limiter.reset()
