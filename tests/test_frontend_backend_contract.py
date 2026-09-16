"""Frontend/backend API contract ratchet.

The Flutter app and the FastAPI backend are written independently, and nothing
used to check that the paths they agree on are actually the same paths. They
are not: 46 distinct calls in `api_client.dart` target routes that do not exist
on the backend (`/answer-sheets/*`, `/mastery/*`, `/analytics/*`, `/reports/*`,
`/notifications/*`, `/questions` CRUD, ...). Those are dormant -- the UI drives
`PillarApi` almost exclusively, and every `ApiClient` method the UI does call
maps to a real route -- so they do not break anything today. They are a trap
for whoever wires the next screen to one of them.

This test does not require the backlog to be paid down. It pins it:

  * a NEW frontend call with no backend route fails the build;
  * an entry on the allowlist that has since been fixed or removed also fails,
    so the list cannot rot into a lie.

That converts "we think the contract is fine" into a checked invariant while
the cleanup is scheduled rather than rushed.
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
#
# Every entry here is a method on `api_client.dart` that no screen calls. The
# backend equivalents, where one exists, are named so the eventual fix is
# mechanical rather than a re-investigation.
KNOWN_GAPS: dict[tuple[str, str], str] = {
    # Answer-sheet CRUD belongs to /api/v1/scan/sessions/* + /evaluations/*.
    ("POST", "/answer-sheets"): "no route; scan flow uses /scan/sessions",
    ("GET", "/answer-sheets"): "no route; scan flow uses /scan/sessions",
    ("GET", "/answer-sheets/*"): "no route; scan flow uses /scan/sessions/{id}",
    ("POST", "/answer-sheets/*/evaluate"): "no route; use /evaluations/sheet",
    ("GET", "/answer-sheets/*/evaluations"): "no route; use /evaluations/sheet",
    ("POST", "/answer-sheets/*/finalize"): "no route; use /evaluations/sheet/.../finalize",
    ("POST", "/answer-sheets/*/ocr"): "no route; OCR lives inside /scan/sessions/{id}/process",
    ("POST", "/answer-sheets/*/segment"): "no route; segmentation lives in /scan/sessions",
    ("POST", "/answer-sheets/*/vision"): "no route; Sarvam Vision is called from the client",
    ("POST", "/answer-sheets/*/process"): "no route; use /scan/sessions/{id}/process",
    # Mastery is served by /api/v1/knowledge/{student_id}.
    ("GET", "/mastery/*"): "use /knowledge/{student_id}",
    ("GET", "/mastery/*/misconceptions"): "no route",
    ("GET", "/mastery/*/recommendations"): "no route",
    ("GET", "/mastery/*/weak-concepts"): "no route",
    ("PUT", "/mastery/*"): "no route",
    ("POST", "/mastery/attempt"): "no route",
    # Analytics is served by /api/v1/insights/*.
    ("GET", "/analytics/assessment/*"): "use /insights/class/{assessment_id}",
    ("GET", "/analytics/class/*"): "use /insights/class/{assessment_id}",
    ("GET", "/analytics/school/*"): "use /insights/school/{school_id}",
    ("GET", "/analytics/student/*"): "no route",
    # Reports and notifications have no backend implementation at all.
    ("POST", "/reports/*/export/*"): "no route",
    ("POST", "/reports/bulk"): "no route",
    ("POST", "/reports/generate"): "no route",
    ("GET", "/reports/parent/*/*"): "no route",
    ("POST", "/notifications"): "no route",
    ("PATCH", "/notifications/*/read"): "no route",
    ("GET", "/notifications/*"): "no route",
    ("POST", "/notifications/whatsapp"): "no route",
    # Question bank is search/optimize only -- no CRUD surface exists.
    ("POST", "/questions"): "no route; bank is read-only (/questions/search)",
    ("GET", "/questions/*"): "no route; use /questions/search",
    ("PUT", "/questions/*"): "no route",
    ("DELETE", "/questions/*"): "no route",
    ("POST", "/questions/batch"): "no route",
    # Misc mismatches.
    ("POST", "/papers/*/format"): "use /papers/{id}/export/{fmt}",
    ("POST", "/schools/*/templates"): "use POST /schools/{id}/school-templates",
    ("GET", "/blueprints/*"): "no route; only /blueprints/generate exists",
    ("PUT", "/blueprints/*"): "no route; only /blueprints/generate exists",
    ("POST", "/evaluations"): "use /evaluations/sheet",
    ("POST", "/evaluations/review"): "use /evaluations/sheet/{a}/{s}/review/{q}",
    ("POST", "/practice"): "use /practice/generate",
    ("GET", "/practice/*"): "no route",
    ("GET", "/practice/student/*"): "no route",
}

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
    sudden collapse means the scan broke, not that the contract improved."""
    matched, _ = audit.compare()
    assert len(matched) >= 70, (
        f"only {len(matched)} frontend calls matched a backend route -- the "
        "audit probably failed to parse the Dart call sites"
    )
