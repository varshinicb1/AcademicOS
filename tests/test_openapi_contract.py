"""Ratchet: the committed API contract must match the live application.

`contract/openapi.json` is the frozen schema that Phase 1 of the Web-client
migration builds on (see `docs/frontend-platform-decision.md`). A frozen artifact
that silently drifts is worse than no artifact at all -- this project already
shipped 46 frontend calls that targeted routes which had never existed, and
nothing caught it until an audit was run by hand.

So the committed copy is regenerated here and compared. Change a route without
re-exporting and CI fails with the diff, in review, before a client is written
against a schema that is no longer true.
"""
from __future__ import annotations

import difflib
import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
_EXPORT = REPO / "scripts" / "export_openapi.py"
CONTRACT = REPO / "contract" / "openapi.json"
TYPES = REPO / "contract" / "api-types.ts"


def _load_exporter():
    spec = importlib.util.spec_from_file_location("export_openapi", _EXPORT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def exporter():
    return _load_exporter()


def test_committed_openapi_contract_is_current(exporter):
    assert CONTRACT.is_file(), (
        "contract/openapi.json is missing. Run: python scripts/export_openapi.py"
    )
    committed = CONTRACT.read_text(encoding="utf-8")
    live = exporter.schema_text()
    if committed == live:
        return

    diff = list(difflib.unified_diff(
        committed.splitlines(), live.splitlines(),
        fromfile="committed", tofile="live", lineterm="", n=1,
    ))
    pytest.fail(
        "contract/openapi.json is stale -- the API changed without re-exporting.\n"
        "Run:  python scripts/export_openapi.py\n"
        "then: npx --yes openapi-typescript@latest contract/openapi.json "
        "-o contract/api-types.ts\n"
        "and commit both.\n\n" + "\n".join(diff[:60])
    )


def test_generated_types_are_present_and_non_trivial():
    assert TYPES.is_file(), (
        "contract/api-types.ts is missing. Run: npx --yes openapi-typescript@latest "
        "contract/openapi.json -o contract/api-types.ts"
    )
    text = TYPES.read_text(encoding="utf-8")
    # Existence alone proves nothing -- an empty or truncated generation still
    # "exists". Anchor on a route that must be in any real generation.
    assert '"/api/v1/assessments"' in text, (
        "contract/api-types.ts does not contain the assessments path -- it looks "
        "empty or truncated, not merely stale"
    )
    assert '"/api/v1/curriculum/academic-years"' in text
