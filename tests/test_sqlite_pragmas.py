"""AGENTS.md section 3 claims an invariant that was not true.

It states that EVERY SQLite connection in `src/academicos/` runs
`PRAGMA journal_mode=WAL` and `PRAGMA busy_timeout=60000`. Measured before this
test existed: 21 `sqlite3.connect` call sites, 17 setting WAL and 19 setting
busy_timeout. The worst offender was `ConsentStore`, which set NEITHER, under
multi-threaded FastAPI, on the store holding DPDP consent records.

A documented invariant with no test is a comment. This turns it into one, at the
source level, so a new store cannot be added without the pragmas and nothing
notices.

Two exceptions are honoured, and only two, each because WAL is not merely
optional there but impossible:
  * a read-only connection cannot set the journal mode -- it is a write
  * the fixture connections in tests are not in `src/`
"""
from __future__ import annotations

import ast
import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
SRC = REPO / "src" / "academicos"

# (relative path, function name) -> why WAL is not required here.
# Keyed on the exact function so a NEW connection cannot inherit an exemption.
WAL_EXEMPT = {
    ("assessment/question_bank.py", "_load"):
        "opened read-only via a `mode=ro` URI; setting the journal mode is a "
        "write and raises 'attempt to write a readonly database'",
}


def _rel(path: pathlib.Path) -> str:
    """Path relative to src/academicos, posix-style.

    The exemption key uses this rather than `path.name`, because two packages
    can each hold a `store.py` and a bare filename would let one inherit the
    other's waiver.
    """
    return path.relative_to(SRC).as_posix()


def _connect_sites() -> list[tuple[pathlib.Path, str, int, str]]:
    """Every `<something>sqlite3.connect(...)` inside a function under src/."""
    sites: list[tuple[pathlib.Path, str, int, str]] = []
    for path in sorted(SRC.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        if "sqlite3.connect(" not in text:
            continue
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            segment = ast.get_source_segment(text, node) or ""
            if "sqlite3.connect(" in segment:
                sites.append((path, node.name, node.lineno, segment))
    return sites


def test_the_scan_finds_the_connections():
    """Guard the guard: if the scanner stops matching, the test below is vacuous."""
    sites = _connect_sites()
    assert len(sites) >= 15, (
        f"only found {len(sites)} sqlite3.connect sites under src/. The "
        "invariant test below would pass by finding nothing."
    )


def test_every_connection_sets_busy_timeout():
    missing = []
    for path, func, lineno, segment in _connect_sites():
        if "PRAGMA busy_timeout" not in segment:
            missing.append(f"{path.relative_to(REPO)}:{lineno} ({func})")
    assert not missing, (
        "AGENTS.md section 3 mandates `PRAGMA busy_timeout=60000` on every "
        "SQLite connection. Without it, a concurrent write raises "
        "'database is locked' immediately instead of waiting.\n  "
        + "\n  ".join(missing)
    )


def test_every_connection_sets_wal_except_the_documented_readonly_one():
    missing = []
    for path, func, lineno, segment in _connect_sites():
        if "PRAGMA journal_mode=WAL" in segment:
            continue
        if (_rel(path), func) in WAL_EXEMPT:
            continue
        missing.append(f"{path.relative_to(REPO)}:{lineno} ({func})")
    assert not missing, (
        "AGENTS.md section 3 mandates `PRAGMA journal_mode=WAL` on every SQLite "
        "connection. Exempt only a genuinely read-only connection, and add it to "
        "WAL_EXEMPT with a reason.\n  " + "\n  ".join(missing)
    )


def test_the_exemption_list_has_not_rotted():
    """An exemption for a connection that no longer exists is a stale waiver.

    Same principle as `KNOWN_GAPS` in the frontend/backend contract test: an
    allowlist that outlives its reason silently widens the hole it was meant to
    describe.
    """
    live = {(_rel(path), func) for path, func, _ln, _seg in _connect_sites()}
    for key, reason in WAL_EXEMPT.items():
        assert key in live, (
            f"WAL_EXEMPT entry {key} no longer matches any connection -- remove "
            f"it rather than leaving a waiver for code that is gone. Reason "
            f"was: {reason}"
        )
        assert reason.strip(), f"WAL_EXEMPT entry {key} has no reason"


def test_the_consent_store_is_not_exempt():
    """The specific store that had neither pragma must never be exempted."""
    assert ("assessment/consent.py", "__init__") not in WAL_EXEMPT
