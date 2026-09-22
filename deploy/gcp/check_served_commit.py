"""Fail unless the live service reports the commit this deploy built.

    curl -fsS "$URL/health" | python3 deploy/gcp/check_served_commit.py "$GITHUB_SHA"

Why: the 2026-09-21 audit (item 8.3) found the live release serving a build at
least 4 days older than its source -- missing 8 operations -- and nothing could
tell, because /health said only {"status": "ok"}. A 200 from /health proves a
service is up, not that it is the one just deployed (a failed rollout leaves
the previous revision serving). GET /health now carries the commit baked into
the image (Dockerfile BUILD_COMMIT), and this compares it.

Exit 0 on a match; 1 otherwise, printing both commits. Standard library only:
it runs on the bare GitHub runner.
"""
from __future__ import annotations

import json
import sys


def check(body: str, expected: str) -> tuple[bool, str]:
    try:
        served = json.loads(body).get("commit")
    except (ValueError, AttributeError):
        return False, f"/health did not answer JSON; expected commit {expected}"
    if served == expected:
        return True, f"serving the deployed commit {expected}"
    return False, f"/health reports commit {served!r}, but this deploy built {expected}"


def main(argv: list[str]) -> int:
    if len(argv) != 2 or not argv[1].strip():
        print("usage: check_served_commit.py <expected-commit> < health.json", file=sys.stderr)
        return 2
    ok, message = check(sys.stdin.read(), argv[1].strip())
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
