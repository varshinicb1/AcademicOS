"""Retry policy: classification, `Retry-After`, and full-jitter backoff.

The policy is pure, so these assert exact numbers rather than observing that
"something waited". `rand` is injected, which makes the jitter deterministic:
`rand=0.0` is the bottom of the full-jitter range, `rand=1.0` is the capped top.
"""
from __future__ import annotations

import sys
from email.utils import parsedate_to_datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.llm.resilience import (
    DEFAULT_POLICY,
    RETRYABLE_STATUS,
    RetryPolicy,
    backoff_sequence,
    is_retryable_status,
    parse_retry_after,
)


# --------------------------------------------------------------------------- #
# retryable status classification
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("status", sorted(RETRYABLE_STATUS))
def test_transient_statuses_are_retryable(status):
    assert is_retryable_status(status) is True


@pytest.mark.parametrize("status", [200, 201, 204, 400, 401, 403, 404, 409, 422, 451])
def test_deterministic_statuses_are_not_retryable(status):
    """Retrying a 400/401/403/404/422 spends the provider's quota for the same answer."""
    assert is_retryable_status(status) is False


def test_502_and_504_are_retryable():
    """These were the gap in the previous implementation, which retried only 429/500/503.

    502 and 504 are the most common transient failures in front of a hosted
    model -- edge errors and upstream slowness -- so omitting them meant the
    retry logic skipped the failures it most needed to handle.
    """
    assert is_retryable_status(502) is True
    assert is_retryable_status(504) is True


# --------------------------------------------------------------------------- #
# Retry-After
# --------------------------------------------------------------------------- #

def test_retry_after_delta_seconds():
    assert parse_retry_after({"Retry-After": "30"}) == 30.0


def test_retry_after_zero():
    assert parse_retry_after({"retry-after": "0"}) == 0.0


def test_retry_after_negative_is_floored_at_zero():
    assert parse_retry_after({"Retry-After": "-5"}) == 0.0


def test_retry_after_http_date_is_converted_to_a_delta():
    """RFC 9110 permits the HTTP-date form and providers do send it.

    The previous `int(value)` parse silently fell through to the computed
    backoff for this form, so a server asking for 30s got a few hundred
    milliseconds instead.
    """
    raw = "Wed, 21 Oct 2026 07:28:00 GMT"
    target = parsedate_to_datetime(raw).timestamp()
    assert parse_retry_after({"Retry-After": raw}, now=target - 30) == pytest.approx(30.0, abs=0.01)


def test_retry_after_http_date_in_the_past_is_zero():
    raw = "Wed, 21 Oct 2026 07:28:00 GMT"
    target = parsedate_to_datetime(raw).timestamp()
    assert parse_retry_after({"Retry-After": raw}, now=target + 100) == 0.0


@pytest.mark.parametrize("value", ["", "  ", "soon", "in a bit", "1.2.3"])
def test_unparseable_retry_after_returns_none(value):
    """None means "no instruction" -> use the computed backoff, never "retry now"."""
    assert parse_retry_after({"Retry-After": value}) is None


@pytest.mark.parametrize("headers", [None, {}, {"X-Other": "1"}])
def test_absent_retry_after_returns_none(headers):
    assert parse_retry_after(headers) is None


def test_retry_after_header_lookup_is_case_insensitive():
    assert parse_retry_after({"RETRY-AFTER": "4"}) == 4.0


# --------------------------------------------------------------------------- #
# delay_for: full jitter
# --------------------------------------------------------------------------- #

def test_full_jitter_bottom_of_range_is_zero():
    """Full jitter is uniform in [0, capped]; rand=0 is the bottom."""
    policy = RetryPolicy(base_delay_s=1.0, max_delay_s=20.0)
    assert policy.delay_for(0, rand=lambda: 0.0) == 0.0


def test_full_jitter_top_of_range_is_the_capped_exponential():
    policy = RetryPolicy(base_delay_s=1.0, max_delay_s=20.0)
    assert policy.delay_for(0, rand=lambda: 1.0) == pytest.approx(1.0)
    assert policy.delay_for(1, rand=lambda: 1.0) == pytest.approx(2.0)
    assert policy.delay_for(2, rand=lambda: 1.0) == pytest.approx(4.0)


def test_exponential_growth_is_capped():
    policy = RetryPolicy(base_delay_s=1.0, max_delay_s=5.0)
    # 2 ** 10 = 1024s uncapped; the ceiling must hold.
    assert policy.delay_for(10, rand=lambda: 1.0) == pytest.approx(5.0)


def test_jitter_actually_spreads_values():
    """The delay must be a draw from [0, capped], not a constant.

    Without this, a "full jitter" implementation that returned the capped value
    every time would pass every other test in this file. At attempt 2 the cap is
    `base * 2**2` = 4.0s, so `delay / 4.0` must equal the draw.
    """
    policy = RetryPolicy(base_delay_s=1.0, max_delay_s=20.0)
    draws = [0.05, 0.40, 0.75, 0.99, 0.2]
    delays = [policy.delay_for(2, rand=lambda d=d: d) for d in draws]
    assert delays == pytest.approx([d * 4.0 for d in draws])
    assert len(set(delays)) == len(draws)


def test_retry_after_takes_precedence_over_the_computed_curve():
    policy = RetryPolicy(base_delay_s=1.0, max_delay_s=20.0)
    # attempt 0 would compute <=1s; the server asked for 6s and knows better.
    assert policy.delay_for(0, retry_after_s=6.0, rand=lambda: 1.0) == pytest.approx(6.0)


def test_retry_after_is_clamped_to_the_ceiling():
    """A server asking for a day must not park a worker thread for a day."""
    policy = RetryPolicy(base_delay_s=1.0, max_delay_s=20.0)
    assert policy.delay_for(0, retry_after_s=86_400.0) == pytest.approx(20.0)


# --------------------------------------------------------------------------- #
# should_retry and construction
# --------------------------------------------------------------------------- #

def test_should_retry_requires_both_budget_and_a_retryable_reason():
    policy = RetryPolicy(max_attempts=3)
    assert policy.should_retry(0, retryable=True) is True
    assert policy.should_retry(1, retryable=True) is True
    assert policy.should_retry(2, retryable=True) is False  # last attempt
    assert policy.should_retry(0, retryable=False) is False  # pointless anyway


def test_retries_counts_additional_attempts():
    assert RetryPolicy(max_attempts=1).retries == 0
    assert RetryPolicy(max_attempts=4).retries == 3


def test_backoff_sequence_length_matches_retries():
    assert len(backoff_sequence(RetryPolicy(max_attempts=4))) == 3
    assert backoff_sequence(RetryPolicy(max_attempts=1)) == []


@pytest.mark.parametrize("max_attempts", [0, -1])
def test_max_attempts_must_be_positive(max_attempts):
    with pytest.raises(ValueError):
        RetryPolicy(max_attempts=max_attempts)


def test_default_policy_is_four_attempts_capped_at_twenty_seconds():
    """Pin the shipped values so a silent change is a test failure."""
    assert DEFAULT_POLICY.max_attempts == 4
    assert DEFAULT_POLICY.max_delay_s == 20.0
