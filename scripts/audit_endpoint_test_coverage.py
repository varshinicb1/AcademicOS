"""Measure how much of the API surface is actually exercised by tests.

Two different questions, deliberately separated:

  * "mentioned" -- the path string appears anywhere in the test suite. This is
    misleadingly high, because tests/test_route_inventory.py enumerates every
    route in a list for contract purposes without calling most of them.

  * "called" -- the path appears as the immediate argument of an HTTP client
    call (.get/.post/.put/.patch/.delete). That is the closest static proxy for
    "a test actually exercised this route".
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
os.environ.setdefault("ACOS_DATA_ROOT", str(REPO / "academicos-data"))

from academicos.api.main import app  # noqa: E402

PARAM = re.compile(r"\{[^}]+\}")


def paths() -> list[str]:
    return [p for p in app.openapi()["paths"] if p.startswith(("/api/", "/v1/"))]


def suite_text() -> str:
    return "\n".join(
        f.read_text(encoding="utf-8", errors="ignore")
        for f in (REPO / "tests").glob("test_*.py")
    )


def mentioned(path: str, blob: str) -> bool:
    pattern = PARAM.sub('[^/"]+', path)
    return re.search(pattern, blob, re.IGNORECASE) is not None


def called(path: str, blob: str) -> bool:
    """True when the path appears as a quoted argument to an HTTP client call.

    Two forms are tried, because both are used in this suite and checking only
    the first undercounts badly:
      * the full path, e.g. client.get("/api/v1/syllabus/Science/10")
      * the path with the /api/v1 prefix stripped, e.g. a helper that prepends
        it -- client.get("/curriculum/reporting/coverage")
    """
    variants = [path]
    for prefix in ("/api/v1", "/v1"):
        if path.startswith(prefix):
            variants.append(path[len(prefix):])
    for variant in variants:
        # Parameters become "anything up to the next slash": this suite writes
        # dict subscripts inside f-strings, e.g. f".../units/{u1['id']}/sequence",
        # whose single quotes broke a [^"']* substitution.
        body = PARAM.sub('[^/]*', variant)
        # The path may be followed by a query string before the closing quote
        # (client.get(f"/api/v1/.../coverage?academic_year_id={id}")) -- matching
        # the quote directly after the path silently skipped every such call.
        pattern = r'\.(get|post|put|patch|delete)\(\s*f?["\']' + body + r'[?"\']'
        if re.search(pattern, blob, re.IGNORECASE):
            return True
    return False


def main() -> int:
    ps = paths()
    blob = suite_text()
    m = [p for p in ps if mentioned(p, blob)]
    c = [p for p in ps if called(p, blob)]
    total = len(ps)

    print(f"API paths                          : {total}")
    print(f"  mentioned anywhere in a test     : {len(m):>3}  ({round(len(m) * 100 / total)}%)"
          "   <- inflated by the route-inventory list")
    print(f"  passed to an HTTP client call    : {len(c):>3}  ({round(len(c) * 100 / total)}%)")
    print()
    miss = [p for p in ps if p not in c]
    print(f"invoked by no test call ({len(miss)}):")
    for p in sorted(miss):
        print("   ", p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
