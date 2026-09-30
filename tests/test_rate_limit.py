import pytest
from fastapi import HTTPException

from academicos.api.rate_limit import RateLimiter, get_client_ip, login_limiter, register_limiter


class _FakeClient:
    def __init__(self, host: str) -> None:
        self.host = host


class _FakeRequest:
    """Minimal stand-in for fastapi.Request -- get_client_ip only reads
    .headers.get(...) and .client.host."""

    def __init__(self, headers: dict[str, str], client_host: str | None = "203.0.113.9"):
        self.headers = headers
        self.client = _FakeClient(client_host) if client_host is not None else None


def test_get_client_ip_uses_rightmost_forwarded_hop_not_leftmost():
    """Security fix 2026-09-17: the leftmost X-Forwarded-For entry is
    whatever the ORIGINAL caller claimed -- trusting it let an attacker
    reset their own rate-limit bucket by sending a fresh fake value on every
    request. The rightmost hop is the one the platform's own edge proxy
    appends (Render/Cloud Run both append, not trust-and-forward), so that's
    the one real client-identity signal here."""
    spoofed = _FakeRequest({"x-forwarded-for": "1.2.3.4"})
    assert get_client_ip(spoofed) == "1.2.3.4"  # single hop: still the real signal

    chained = _FakeRequest({"x-forwarded-for": "9.9.9.9, 203.0.113.9"})
    # 9.9.9.9 is attacker-claimed; 203.0.113.9 is what the trusted edge appended.
    assert get_client_ip(chained) == "203.0.113.9"

    multi_spoof = _FakeRequest({"x-forwarded-for": "1.1.1.1, 2.2.2.2, 203.0.113.9"})
    assert get_client_ip(multi_spoof) == "203.0.113.9"


def test_get_client_ip_falls_back_to_request_client_host_when_no_header():
    no_header = _FakeRequest({}, client_host="198.51.100.1")
    assert get_client_ip(no_header) == "198.51.100.1"


def test_get_client_ip_handles_missing_client_and_empty_header():
    assert get_client_ip(_FakeRequest({}, client_host=None)) == "unknown"
    assert get_client_ip(_FakeRequest({"x-forwarded-for": "  "}, client_host="198.51.100.1")) \
        == "198.51.100.1"


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
    login_limiter.max_requests = 300
    login_limiter.reset()


def test_a_class_behind_one_address_can_sign_in_and_register_together():
    """A school's pupils share one NAT address: the per-network limits must
    let a full class through in a minute (N-9-4)."""
    from academicos.api.rate_limit import ACCOUNT_FAILURES
    assert login_limiter.max_requests >= 200
    assert register_limiter.max_requests >= 100
    assert ACCOUNT_FAILURES <= 10


def test_wrong_passwords_lock_one_account_not_the_network(tmp_path, monkeypatch):
    from academicos.api.rate_limit import ACCOUNT_FAILURES, account_failures
    from test_assessment_routes_auth import _boot_client, _register

    monkeypatch.setenv("ACOS_TEST_RATE_LIMIT", "1")
    monkeypatch.delenv("ACOS_DISABLE_RATE_LIMIT", raising=False)
    login_limiter.reset()
    account_failures.reset()
    with _boot_client(tmp_path, monkeypatch) as client:
        _register(client, "school_1", "victim@example.com")
        _register(client, "school_1", "other@example.com")
        for _ in range(ACCOUNT_FAILURES):
            r = client.post("/api/v1/auth/login", json={"email": "victim@example.com", "password": "guess guess guess"})
            assert r.status_code == 401
        # Locked, even with the right password: the guesser learns nothing.
        locked = client.post("/api/v1/auth/login", json={"email": "Victim@Example.com", "password": "correct horse battery"})
        assert locked.status_code == 429 and "Retry-After" in locked.headers
        # Another account from the same address signs in.
        ok = client.post("/api/v1/auth/login", json={"email": "other@example.com", "password": "correct horse battery"})
        assert ok.status_code == 200, ok.text
    login_limiter.reset()
    account_failures.reset()
