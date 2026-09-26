"""Give the web bundle's two entry files URLs that change when their content does.

Flutter web writes `main.dart.js` and `flutter_bootstrap.js` under the same
names on every build. Until 2026-09-26 firebase.json served them
`immutable, max-age=31536000`, so a browser that had loaded the app once never
asked for either again, and ran a four-deploys-old bundle (audit 2026-09-26,
item 8.3). firebase.json now revalidates every file, but a browser still
holding the immutable copy will not ask.

index.html is never cached (`no-store`), so it is the one file every browser
re-reads on every visit. This script makes it load
`flutter_bootstrap.js?v=<hash of the bootstrap>`, and makes the bootstrap's
build config load `main.dart.js?v=<hash of main.dart.js>`. A new build means
new URLs, which the browser has never cached, so it fetches them. Hosting
ignores the query when it looks up the file; Flutter's loader checks only the
path's last segment, which the query is not part of.

Run after `flutter build web` (and after stripping the offline bank):

    python scripts/web_cache_bust.py [frontend/build/web]

Idempotent: a second run replaces an existing `?v=` rather than adding one.
It exits non-zero if it cannot find either URL, because a silent no-op would
ship a bundle that stale browsers never re-fetch.
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_WEB = REPO / "frontend" / "build" / "web"

_MAIN_JS = re.compile(r'"mainJsPath":"main\.dart\.js(?:\?v=[0-9a-f]+)?"')
_BOOTSTRAP_TAG = re.compile(r'src="flutter_bootstrap\.js(?:\?v=[0-9a-f]+)?"')


def content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:12]


def _replace_once(pattern: re.Pattern[str], text: str, new: str,
                  what: str, where: Path) -> str:
    found = len(pattern.findall(text))
    if found != 1:
        raise SystemExit(
            f"web_cache_bust: expected exactly one {what} in {where}, found "
            f"{found}. Flutter may have changed its build output; fix this "
            "script before deploying, or returning browsers keep the old app.")
    return pattern.sub(new, text)


def bust(web: Path) -> tuple[str, str]:
    """Rewrite the two entry URLs in `web`; return (main hash, bootstrap hash)."""
    main_js = web / "main.dart.js"
    bootstrap = web / "flutter_bootstrap.js"
    index = web / "index.html"

    main_v = content_hash(main_js.read_bytes())
    boot_text = _replace_once(_MAIN_JS, bootstrap.read_text(encoding="utf-8"),
                              f'"mainJsPath":"main.dart.js?v={main_v}"',
                              "mainJsPath", bootstrap)
    bootstrap.write_text(boot_text, encoding="utf-8", newline="")

    boot_v = content_hash(bootstrap.read_bytes())
    index_text = _replace_once(_BOOTSTRAP_TAG, index.read_text(encoding="utf-8"),
                               f'src="flutter_bootstrap.js?v={boot_v}"',
                               "flutter_bootstrap.js script tag", index)
    index.write_text(index_text, encoding="utf-8", newline="")
    return main_v, boot_v


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    web = Path(args[0]) if args else DEFAULT_WEB
    main_v, boot_v = bust(web)
    print(f"index.html -> flutter_bootstrap.js?v={boot_v}; "
          f"bootstrap -> main.dart.js?v={main_v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
