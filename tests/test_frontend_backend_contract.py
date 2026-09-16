"""Frontend/backend API contract ratchet.

The Flutter app and the FastAPI backend are written independently, and nothing
used to check that the paths they agree on are actually the same paths. As of
2026-09-16 they did not: 42 distinct calls in `api_client.dart` (and their
`local_api_client.dart` offline mirrors, and the repository/use-case layers
above them) targeted routes that never existed on the backend
(`/answer-sheets/*`, `/mastery/*`, `/analytics/*`, `/reports/*`,
`/notifications/*`, `/questions` CRUD, ...). They were dormant -- the UI drives
`PillarApi` almost exclusively, and every `ApiClient` method the UI does call
maps to a real route -- so none of it broke anything live. It was still a trap
for whoever wired the next screen to one of them.

2026-09-17: deleted rather than built out. Confirmed via an exhaustive
reachability trace (screen, bloc, use case, and DI resolution, in both build
variants) that all 42 had zero live callers, so removing them was the lower-
risk of the two options the CTO review posed ("delete the fictional surface,
or build the missing endpoints"). KNOWN_GAPS below is empty as a result.

This test still isn't retired: it remains the ratchet against the same class
of drift recurring --

  * a NEW frontend call with no backend route fails the build;
  * a KNOWN_GAPS entry that no longer corresponds to a real gap also fails,
    so the list cannot silently rot into a lie the next time this happens.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
_SCRIPT = REPO / "scripts" / "audit_frontend_backend_contract.py"


def _load_audit():
    spec = importlib.util.spec_from_file_location("audit_frontend_backend_contract", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Known, accepted drift: (METHOD, normalised path) -> why it is allowed.
# Empty since the 2026-09-17 cleanup -- every entry that used to live here was
# a dead api_client.dart method, now deleted. A future justified gap goes
# here the same way the old ones did: a real reason, and a note on what the
# real route (if any) is.
KNOWN_GAPS: dict[tuple[str, str], str] = {}

# Third-party calls, not our API. sarvam_vision_ocr.dart talks to Sarvam's
# hosted Vision job API, so having no route in our OpenAPI is correct. Both
# spellings appear: the scanner records the literal `$_baseUrl/...` from the
# interpolated call, and a normalised `/sarvam-vision/...` alias.
_EXTERNAL_PREFIXES = ("/sarvam-vision", "$_baseUrl")


@pytest.fixture(scope="module")
def audit():
    # Deliberately does NOT touch os.environ: this fixture is module-scoped and
    # the environment is process-wide, so setting ACOS_DATA_ROOT here leaked
    # into every later test and broke test_fsrs. The audit module resolves
    # Config from cwd (the repo root) by itself.
    return _load_audit()


def test_no_new_frontend_call_without_a_backend_route(audit):
    """A new unmapped call is a bug: it will 404 the moment it is wired up."""
    _, unmatched = audit.compare()
    unexpected = [
        (m, p, where)
        for m, p, where in unmatched
        if not p.startswith(_EXTERNAL_PREFIXES)
        and (m, audit.shape(p)) not in KNOWN_GAPS
    ]
    assert not unexpected, (
        "frontend calls with no backend route (add the route, or add a "
        "justified entry to KNOWN_GAPS in this file):\n"
        + "\n".join(f"  {m:<7} {p:<52} ({w})" for m, p, w in unexpected)
    )


def test_allowlist_has_not_rotted(audit):
    """If a gap was fixed or the call site removed, its allowlist entry must
    go too -- otherwise the list slowly becomes fiction."""
    _, unmatched = audit.compare()
    live = {(m, audit.shape(p)) for m, p, _ in unmatched
            if not p.startswith(_EXTERNAL_PREFIXES)}
    stale = sorted(set(KNOWN_GAPS) - live)
    assert not stale, (
        "these KNOWN_GAPS entries no longer correspond to a real unmapped "
        "call -- delete them from tests/test_frontend_backend_contract.py:\n"
        + "\n".join(f"  {m} {p}" for m, p in stale)
    )


def test_matched_surface_does_not_regress(audit):
    """Sanity floor: the app's real API surface is large and must stay so. A
    sudden collapse means the scan broke, not that the contract improved.
    Re-verified unchanged at 76 after the 2026-09-17 dead-code cleanup below
    (confirmed by running scripts/audit_frontend_backend_contract.py
    directly) -- deleting the 42 dead methods removed only unmatched calls,
    by construction, so this floor still holds with no need to lower it.
    """
    matched, _ = audit.compare()
    assert len(matched) >= 70, (
        f"only {len(matched)} frontend calls matched a backend route -- the "
        "audit probably failed to parse the Dart call sites"
    )
