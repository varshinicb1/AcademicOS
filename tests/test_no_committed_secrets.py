"""A secret must never be committed again.

On 2026-09-18 a Groq API key (`gsk...`) was found in `config/config.toml` in
three commits -- `b761a8a`, `c51cd99`, `d00b9e9` -- and removed by `915b18d`.
The key was verified revoked (HTTP 403 against the provider), so the historical
exposure is moot and history was deliberately NOT rewritten for it.

What remained was recurrence. The file IS tracked (`.gitignore` does not cover
it) and it holds real configuration, so the next person editing it is one line
away from the same mistake. This is the guard.

Why a test rather than a pre-commit hook
----------------------------------------
A hook only runs for contributors who installed it; CI runs this for everyone,
and this repo already gates on `pytest tests -q`. It also means the check is
visible in the same place as every other invariant.

The allowlist is deliberate, narrow, and asserted to be non-empty-of-reason:
test fixtures DO contain fake keys, and a check that cannot tell a fixture from
a credential would be turned off within a week.
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]

# Real credential shapes. Length floors are set so a placeholder like
# "sk-test" or "test-anon-key" does not match: a check that fires on fixtures
# gets disabled, and a disabled check protects nothing.
PATTERNS = {
    "groq": r"gsk_[A-Za-z0-9]{30,}",
    "openai/anthropic": r"sk-[A-Za-z0-9_\-]{32,}",
    "google": r"AIza[0-9A-Za-z_\-]{33,}",
    "github": r"ghp_[A-Za-z0-9]{36}",
    "github fine-grained": r"github_pat_[A-Za-z0-9_]{40,}",
    "gitlab": r"glpat-[A-Za-z0-9_\-]{20,}",
    "huggingface": r"hf_[A-Za-z0-9]{34,}",
    "replicate": r"r8_[A-Za-z0-9]{30,}",
    "xai": r"xai-[A-Za-z0-9]{40,}",
    "perplexity": r"pplx-[A-Za-z0-9]{40,}",
    "aws access key": r"AKIA[0-9A-Z]{16}",
    "stripe live": r"sk_live_[A-Za-z0-9]{20,}",
    "slack": r"xox[baprs]-[A-Za-z0-9\-]{20,}",
    "private key block": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "jwt": r"eyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.",
    # A Supabase service role key is a JWT; the anon key is public by design and
    # is not flagged, which is why only `service_role` is matched by name.
    "service role": r"service_role[\"']?\s*[:=]\s*[\"'][A-Za-z0-9_\-\.]{40,}",
}

# Files allowed to match, each for a stated reason. Empty of real credentials.
ALLOWLIST: dict[str, str] = {}

COMPILED = {name: re.compile(pat) for name, pat in PATTERNS.items()}


def _tracked_files() -> list[pathlib.Path]:
    out = subprocess.run(["git", "ls-files"], cwd=REPO,
                         capture_output=True, text=True, check=True)
    return [REPO / line for line in out.stdout.splitlines() if line.strip()]


def _scan() -> list[tuple[str, str, int]]:
    """`(path, pattern name, line number)` for every tracked match."""
    hits: list[tuple[str, str, int]] = []
    for path in _tracked_files():
        rel = path.relative_to(REPO).as_posix()
        if rel in ALLOWLIST:
            continue
        if not path.is_file() or path.stat().st_size > 5_000_000:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for name, regex in COMPILED.items():
                if regex.search(line):
                    hits.append((rel, name, i))
    return hits


def test_no_credential_is_committed_to_the_working_tree():
    """The recurrence guard.

    Reports the PATH and PATTERN NAME only -- never the matched text, because a
    test failure is itself logged and pasted around.
    """
    hits = _scan()
    assert not hits, (
        "a credential-shaped string is committed:\n  "
        + "\n  ".join(f"{p}:{n} (line {i})" for p, n, i in hits)
        + "\nMove it to an environment variable, rotate it at the provider, and "
          "add the path to ALLOWLIST only if it is a fixture."
    )


def test_the_scanner_actually_matches_something():
    """Guard the guard. A regex that matches nothing passes vacuously.

    Every pattern is exercised against a synthetic value of the right shape, so
    a typo in one of them cannot silently disable that class of check.
    """
    # Built by concatenation, never as a literal. The first version wrote the
    # samples inline and the scanner then flagged THIS FILE -- lines 124 and 125,
    # its own private-key and JWT samples. That is the "fires on fixtures" failure
    # this test's docstring warns about, applied to itself: a literal that
    # demonstrates a pattern necessarily matches it.
    A = "a"
    samples = {
        "groq": "gsk" + "_" + A * 40,
        "openai/anthropic": "sk" + "-" + A * 40,
        "google": "AI" + "za" + A * 35,
        "github": "ghp" + "_" + A * 36,
        "github fine-grained": "github" + "_pat_" + A * 45,
        "gitlab": "glpat" + "-" + A * 25,
        "huggingface": "hf" + "_" + A * 36,
        "replicate": "r8" + "_" + A * 35,
        "xai": "xai" + "-" + A * 45,
        "perplexity": "pplx" + "-" + A * 45,
        "aws access key": "AKI" + "A" + "A" * 16,
        "stripe live": "sk_live" + "_" + A * 25,
        "slack": "xoxb" + "-" + A * 25,
        "private key block": "-----BEGIN RSA " + "PRIVATE KEY-----",
        "jwt": "eyJhbGciOiJIUzI1NiJ9" + "." + "eyJzdWIiOiIxIn0.",
        "service role": "service" + "_role = \"" + A * 50 + "\"",
    }
    assert set(samples) == set(PATTERNS), (
        "every pattern needs a sample, or one is untested: "
        f"{set(PATTERNS) ^ set(samples)}"
    )
    for name, sample in samples.items():
        assert COMPILED[name].search(sample), f"pattern {name!r} matches nothing"


def test_placeholders_and_fixtures_do_not_match():
    """The check must not fire on the fake keys the suite legitimately uses.

    A scanner that flags `test-anon-key` and `sk-test` gets disabled, and then
    it protects nothing -- which is worse than not having it, because the
    protection is assumed.
    """
    harmless = [
        "test-anon-key", "test-key-123", "sk-test", "SUPABASE_PLACEHOLDER",
        "not-a-real-key", "changeme", "", "service_role",
        "https://proj.supabase.co/",
    ]
    for value in harmless:
        for name, regex in COMPILED.items():
            assert not regex.search(value), (
                f"{name!r} matched the harmless value {value!r}; the pattern is "
                "too loose and will fire on fixtures"
            )


def test_the_allowlist_entries_are_justified_and_used():
    """A stale waiver is a silent hole, the same principle as KNOWN_GAPS."""
    for rel, reason in ALLOWLIST.items():
        assert reason.strip(), f"ALLOWLIST entry {rel} has no reason"
        assert (REPO / rel).exists(), (
            f"ALLOWLIST waives {rel}, which no longer exists -- remove it"
        )
