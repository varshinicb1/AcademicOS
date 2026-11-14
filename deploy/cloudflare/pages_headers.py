"""Write Cloudflare Pages' `_headers` from firebase.json, the one source of the web
console's security and cache headers.

    python3 deploy/cloudflare/pages_headers.py frontend/build/web https://api.example.in

firebase.json stays the source (tests/test_production_guard.py holds its rules),
so the two hosts can never drift. Two translations:

  * The API origin. firebase.json's CSP names the Cloud Run URL in connect-src and
    img-src; on Pages the console talks to the API at the given origin instead.
  * Cache rules. Pages has no regex rules and merges every rule that matches a
    path, so the content-hashed entry files (scripts/web_cache_bust.py) get a glob
    and detach the site-wide `Cache-Control: no-cache` with `! Cache-Control`
    before setting their own. Only those files may be cached for long (AGENTS.md
    6.7).

Pages serves index.html for unknown paths when the build has no 404.html, which
is firebase.json's `"source": "**" -> /index.html` rewrite, so no `_redirects`.
Standard library only: it runs on the bare GitHub runner.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CLOUD_RUN_ORIGIN = "https://academicos-backend-2eskom55ta-el.a.run.app"

# firebase.json's one regex rule, as the globs Pages understands.
HASHED_ENTRY_GLOBS = ("/main.dart.*.js", "/flutter_bootstrap.*.js")
HASHED_ENTRY_REGEX = r"^/(main\.dart|flutter_bootstrap)\.[0-9a-f]{12}\.js$"


def render(firebase: dict, api_origin: str) -> str:
    if not api_origin.startswith("https://") or api_origin.endswith("/"):
        raise ValueError(f"api origin must be https://host with no trailing slash, got {api_origin!r}")
    lines: list[str] = []
    for rule in firebase["hosting"]["headers"]:
        if rule.get("source") == "**":
            paths, detach = ["/*"], False
        elif rule.get("regex") == HASHED_ENTRY_REGEX:
            paths, detach = list(HASHED_ENTRY_GLOBS), True
        elif "source" in rule and "*" not in rule["source"]:
            paths, detach = [rule["source"]], True
        else:
            raise ValueError(f"firebase.json rule has no Pages translation: {rule}")
        for path in paths:
            lines.append(path)
            for h in rule["headers"]:
                if detach:
                    lines.append(f"  ! {h['key']}")
                value = h["value"].replace(CLOUD_RUN_ORIGIN, api_origin)
                lines.append(f"  {h['key']}: {value}")
    # Pages answers /index.html by redirecting to /; the document itself is served
    # at "/", so give "/" the same never-cache rule.
    index_rule = next((r for r in firebase["hosting"]["headers"] if r.get("source") == "/index.html"), None)
    if index_rule:
        lines.append("/")
        for h in index_rule["headers"]:
            lines.append(f"  ! {h['key']}")
            lines.append(f"  {h['key']}: {h['value']}")
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        return 2
    out_dir, api_origin = Path(argv[1]), argv[2]
    firebase = json.loads((REPO / "firebase.json").read_text(encoding="utf-8"))
    text = render(firebase, api_origin)
    (out_dir / "_headers").write_text(text, encoding="utf-8")
    print(f"wrote {out_dir / '_headers'} for API {api_origin}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
