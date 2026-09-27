"""Give the web bundle's two entry files names that change when their content does.

Flutter web writes `main.dart.js` and `flutter_bootstrap.js` under the same
names on every build. Until 2026-09-26 firebase.json served them
`immutable, max-age=31536000`, so a browser that had loaded the app once never
asked for either again, and ran a four-deploys-old bundle (audit 2026-09-26,
item 8.3). The fix then was `no-cache` everywhere plus `?v=<hash>` URLs; but
Firebase Hosting answers a revalidation with 200 and the full body, so every
visit re-downloaded the whole app, 1.6 MB (audit 2026-09-27, D29).

A long cache is safe only on a name that changes when the content does. So this
renames the two files to `main.dart.<hash>.js` and `flutter_bootstrap.<hash>.js`
and points the bootstrap and index.html at the new names. firebase.json caches
exactly that name shape `immutable` (`HASHED_ENTRY`, which the tests hold equal
to firebase.json's rule) and revalidates everything else. index.html is never
cached, so it is the one file every browser re-reads on every visit, and it
always names the current build.

A deploy that forgets this script ships the plain names, which the immutable
rule does not match: the app is then slow to load, never stale.

Run after `flutter build web` (and after stripping the offline bank):

    python scripts/web_cache_bust.py [frontend/build/web]

Idempotent: on an already-renamed build it checks every name against its
content and changes nothing. It exits non-zero if it cannot find either entry
reference, because a silent no-op would ship a bundle this was meant to fix.
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_WEB = REPO / "frontend" / "build" / "web"

# The names firebase.json may cache for a year. Anchored on both ends, and the
# hash is exactly what `content_hash` writes, so a plain `main.dart.js` never
# matches it.
HASHED_ENTRY = r"^/(main\.dart|flutter_bootstrap)\.[0-9a-f]{12}\.js$"

_MAIN_JS = re.compile(
    r'"mainJsPath":"main\.dart(?:\.[0-9a-f]{12})?\.js(?:\?v=[0-9a-f]+)?"')
_BOOTSTRAP_TAG = re.compile(
    r'src="flutter_bootstrap(?:\.[0-9a-f]{12})?\.js(?:\?v=[0-9a-f]+)?"')
_STALE = re.compile(r"^(main\.dart|flutter_bootstrap)\.[0-9a-f]{12}\.js$")


def content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:12]


def _fail(message: str) -> SystemExit:
    return SystemExit(
        f"web_cache_bust: {message}. Flutter may have changed its build output; "
        "fix this script before deploying.")


def _replace_once(pattern: re.Pattern[str], text: str, new: str,
                  what: str, where: Path) -> str:
    found = len(pattern.findall(text))
    if found != 1:
        raise _fail(f"expected exactly one {what} in {where.name}, found {found}")
    return pattern.sub(new, text)


def _check_named(web: Path, name: str) -> str:
    """The hash in an already-renamed file's name, after checking it is the
    hash of what the file holds."""
    path = web / name
    if not path.exists():
        raise _fail(f"{name} is referenced but missing")
    digest = content_hash(path.read_bytes())
    if f".{digest}.js" not in name:
        raise _fail(f"{name} does not hold the content its name says ({digest})")
    return digest


def _already_busted(web: Path) -> tuple[str, str]:
    index = (web / "index.html").read_text(encoding="utf-8")
    boot = re.findall(r'src="(flutter_bootstrap\.[0-9a-f]{12}\.js)"', index)
    if len(boot) != 1:
        raise _fail("found neither flutter_bootstrap.js nor a renamed bootstrap")
    boot_v = _check_named(web, boot[0])
    main = re.findall(r'"mainJsPath":"(main\.dart\.[0-9a-f]{12}\.js)"',
                      (web / boot[0]).read_text(encoding="utf-8"))
    if len(main) != 1:
        raise _fail(f"{boot[0]} names no renamed main.dart.js")
    return _check_named(web, main[0]), boot_v


def bust(web: Path) -> tuple[str, str]:
    """Rename the two entry files in `web`; return (main hash, bootstrap hash)."""
    main_js = web / "main.dart.js"
    bootstrap = web / "flutter_bootstrap.js"
    index = web / "index.html"
    if not main_js.exists() and not bootstrap.exists():
        return _already_busted(web)
    if list(web.glob("main.dart.js_*.part.js")):
        # dart2js names deferred parts after the main script's URL; renaming
        # it would break them. The app has none today.
        raise _fail("the build has deferred parts (main.dart.js_*.part.js)")

    main_v = content_hash(main_js.read_bytes())
    main_name = f"main.dart.{main_v}.js"
    boot_text = _replace_once(_MAIN_JS, bootstrap.read_bytes().decode("utf-8"),
                              f'"mainJsPath":"{main_name}"', "mainJsPath", bootstrap)
    boot_bytes = boot_text.encode("utf-8")
    boot_v = content_hash(boot_bytes)
    boot_name = f"flutter_bootstrap.{boot_v}.js"
    index_text = _replace_once(_BOOTSTRAP_TAG, index.read_bytes().decode("utf-8"),
                               f'src="{boot_name}"',
                               "flutter_bootstrap.js script tag", index)

    # A build directory that was not cleaned still holds the last run's
    # renamed files; they would be uploaded and never read.
    for old in web.iterdir():
        if _STALE.match(old.name) and old.name not in (main_name, boot_name):
            old.unlink()
    (web / boot_name).write_bytes(boot_bytes)
    bootstrap.unlink()
    main_js.replace(web / main_name)
    index.write_bytes(index_text.encode("utf-8"))
    return main_v, boot_v


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    web = Path(args[0]) if args else DEFAULT_WEB
    main_v, boot_v = bust(web)
    print(f"index.html -> flutter_bootstrap.{boot_v}.js -> main.dart.{main_v}.js")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
