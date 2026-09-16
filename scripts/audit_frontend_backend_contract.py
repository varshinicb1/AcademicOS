"""Compare every frontend HTTP call site against the real backend route table.

Frontend paths come from the actual `_dio.METHOD('...')` call sites in
frontend/lib; backend paths come from the live FastAPI OpenAPI schema. Both
are normalised to a *shape* (path segments, with parameter segments collapsed)
so that `/assessments/$id` correctly matches `/api/v1/assessments/{assessment_id}`
despite the different parameter names.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

# NOTE: `academicos.api.main` is imported lazily, inside backend_routes(), and
# this module deliberately never touches os.environ at import time. It used to
# `os.environ.setdefault("ACOS_DATA_ROOT", ...)` at module scope, which is
# process-wide and permanent -- importing this from a test silently repointed
# every later test's Config at the repo's real corpus and broke
# tests/test_fsrs.py::test_cmd_revise_prints_plan. Config falls back to
# cwd()/academicos-data, so running this from the repo root needs no env var at
# all.

CALL_RE = re.compile(r"""_dio\s*\.\s*(get|post|put|patch|delete)\s*\(\s*['"]([^'"]+)['"]""")
# also catch the sarvam vision client which uses a computed base url
CALL_RE2 = re.compile(r"""\.\s*(get|post|put|patch|delete)\s*\(\s*['"]\$_baseUrl([^'"]*)['"]""")


def shape(path: str) -> str:
    """Collapse parameter segments so /a/$id and /a/{x} compare equal."""
    parts = []
    for seg in path.split("/"):
        if not seg:
            continue
        if seg.startswith("$") or seg.startswith("{") or seg.startswith(":"):
            parts.append("*")
        elif seg.startswith("$") or "{" in seg:
            parts.append("*")
        else:
            # strip interpolation inside a segment
            parts.append("*" if "$" in seg or "{" in seg else seg)
    return "/" + "/".join(parts)


def backend_routes() -> dict[tuple[str, str], str]:
    from academicos.api.main import app  # imported lazily; see note above

    out = {}
    for p, ops in app.openapi().get("paths", {}).items():
        p2 = p
        if p2.startswith("/api/v1"):
            p2 = p2[len("/api/v1"):] or "/"
        for m in ops:
            out[(m.upper(), shape(p2))] = p
    return out


def frontend_calls() -> list[tuple[str, str, str]]:
    rows = []
    for f in sorted((REPO / "frontend" / "lib").rglob("*.dart")):
        text = f.read_text(encoding="utf-8", errors="ignore")
        for m in CALL_RE.finditer(text):
            line = text[: m.start()].count("\n") + 1
            rows.append((m.group(1).upper(), m.group(2), f"{f.name}:{line}"))
        for m in CALL_RE2.finditer(text):
            line = text[: m.start()].count("\n") + 1
            rows.append((m.group(1).upper(), "/sarvam-vision" + m.group(2), f"{f.name}:{line}"))
    return rows


def compare() -> tuple[list[tuple[str, str, str]], list[tuple[str, str, str]]]:
    """Return (matched, unmatched) as (method, path, where) triples.

    Exposed as a function so tests/test_frontend_backend_contract.py can use
    the exact same comparison the CLI prints -- one implementation, so the
    ratchet test and the report can never disagree.
    """
    be = backend_routes()
    fe = frontend_calls()
    seen: set[tuple[str, str]] = set()
    matched: list[tuple[str, str, str]] = []
    unmatched: list[tuple[str, str, str]] = []
    for method, path, where in fe:
        key = (method, shape(path))
        if key in seen:
            continue
        seen.add(key)
        (matched if key in be else unmatched).append((method, path, where))
    return matched, unmatched


def main() -> int:
    be = backend_routes()
    matched, unmatched = compare()

    print(f"backend operations : {len(be)}")
    print(f"distinct frontend calls: {len(matched) + len(unmatched)}")
    print(f"  matched   : {len(matched)}")
    print(f"  UNMATCHED : {len(unmatched)}")
    print()
    if unmatched:
        print("=== FRONTEND CALLS WITH NO BACKEND ROUTE ===")
        for method, path, where in sorted(unmatched, key=lambda r: r[1]):
            print(f"  {method:<7} {path:<52} ({where})")
    print()
    print("=== MATCHED (frontend -> backend) ===")
    for method, path, where in sorted(matched, key=lambda r: r[1]):
        print(f"  {method:<7} {path:<52} -> {be[(method, shape(path))]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
