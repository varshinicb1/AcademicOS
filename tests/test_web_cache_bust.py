"""The web bundle's entry files get names that change when their content does.

Until 2026-09-26 firebase.json served `main.dart.js` and `flutter_bootstrap.js`
as `immutable` for a year, and Flutter writes both under the same names every
build, so a browser that had loaded the app once never asked for them again
(audit 2026-09-26, item 8.3). `no-cache` fixed that and cost a full download
on every visit, because Hosting answers a revalidation with 200 (D29).
scripts/web_cache_bust.py renames both to `<name>.<hash>.js`; firebase.json
caches that shape for a year and revalidates the rest, and index.html, never
cached, always names the current build.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import re

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]

spec = importlib.util.spec_from_file_location(
    "web_cache_bust", REPO / "scripts" / "web_cache_bust.py")
wcb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wcb)

# The two lines Flutter 3.x writes, as the real build output has them.
BOOTSTRAP = ('(()=>{var x=1})();\n'
             'if (!window._flutter) { window._flutter = {}; }\n'
             '_flutter.buildConfig = {"engineRevision":"5a2a6a42","builds":'
             '[{"compileTarget":"dart2js","renderer":"canvaskit",'
             '"mainJsPath":"main.dart.js"},{}]};\n'
             '_flutter.loader.load();\n')
INDEX = ('<!DOCTYPE html><html><head><base href="/"></head><body>\n'
         '  <script src="flutter_bootstrap.js" async></script>\n'
         '</body></html>\n')


@pytest.fixture()
def web(tmp_path):
    d = tmp_path / "web"
    d.mkdir()
    (d / "main.dart.js").write_text("main();", encoding="utf-8")
    (d / "flutter_bootstrap.js").write_text(BOOTSTRAP, encoding="utf-8")
    (d / "index.html").write_text(INDEX, encoding="utf-8")
    return d


def _read(web):
    index = (web / "index.html").read_text(encoding="utf-8")
    boot_name = re.search(r'src="([^"]+)"', index).group(1)
    boot = (web / boot_name).read_text(encoding="utf-8")
    main_name = re.search(r'"mainJsPath":"([^"]+)"', boot).group(1)
    return boot_name, main_name


def _names(web):
    return sorted(p.name for p in web.iterdir())


def test_both_entry_files_are_named_by_their_content(web):
    main_v, boot_v = wcb.bust(web)
    boot_name, main_name = _read(web)
    assert (boot_name, main_name) == (f"flutter_bootstrap.{boot_v}.js", f"main.dart.{main_v}.js")
    assert wcb.content_hash((web / main_name).read_bytes()) == main_v
    assert wcb.content_hash((web / boot_name).read_bytes()) == boot_v
    assert (web / main_name).read_text(encoding="utf-8") == "main();"
    # One copy of each: the plain names are gone, so nothing uploads twice.
    assert _names(web) == sorted([boot_name, main_name, "index.html"])


def test_a_new_build_gets_new_names_and_drops_the_old_ones(web):
    wcb.bust(web)
    before = _read(web)
    (web / "main.dart.js").write_text("main(); // next build", encoding="utf-8")
    (web / "flutter_bootstrap.js").write_text(BOOTSTRAP, encoding="utf-8")
    (web / "index.html").write_text(INDEX, encoding="utf-8")
    wcb.bust(web)
    after = _read(web)
    assert before[0] != after[0] and before[1] != after[1]
    assert _names(web) == sorted([*after, "index.html"])


def test_running_it_twice_changes_nothing(web):
    wcb.bust(web)
    first = {p.name: p.read_bytes() for p in web.iterdir()}
    wcb.bust(web)
    assert {p.name: p.read_bytes() for p in web.iterdir()} == first


def test_a_renamed_file_that_was_edited_afterwards_fails_loudly(web):
    wcb.bust(web)
    _boot, main_name = _read(web)
    (web / main_name).write_text("main(); // patched by hand", encoding="utf-8")
    with pytest.raises(SystemExit, match="does not hold the content"):
        wcb.bust(web)


def test_a_build_it_does_not_recognise_fails_loudly(web):
    """If Flutter changes how it names the entry point, a silent no-op would
    ship a bundle this exists to fix."""
    (web / "flutter_bootstrap.js").write_text("_flutter.loader.load();", encoding="utf-8")
    with pytest.raises(SystemExit, match="mainJsPath"):
        wcb.bust(web)
    assert (web / "main.dart.js").exists()  # nothing renamed on the way out


def test_deferred_parts_stop_it(web):
    """dart2js names deferred parts after the main script's URL."""
    (web / "main.dart.js_1.part.js").write_text("part();", encoding="utf-8")
    with pytest.raises(SystemExit, match="deferred parts"):
        wcb.bust(web)


def test_firebase_caches_exactly_the_names_it_writes(web):
    """The immutable rule is the script's pattern, it matches what the script
    writes, and it matches no plain name: a deploy that skips the script is
    slow, never stale."""
    rules = json.loads((REPO / "firebase.json").read_text(encoding="utf-8"))["hosting"]["headers"]
    immutable = [r for r in rules
                 if any("immutable" in h["value"] for h in r["headers"])]
    assert [r.get("regex") for r in immutable] == [wcb.HASHED_ENTRY]
    pattern = re.compile(wcb.HASHED_ENTRY)
    wcb.bust(web)
    for name in _read(web):
        assert pattern.match("/" + name), name
    for plain in ("/main.dart.js", "/flutter_bootstrap.js", "/index.html", "/flutter.js",
                  "/main.dart.js?v=0a164747aba1", "/assets/main.dart.0a164747aba1.js",
                  "/main.dart.0a164747aba.js", "/favicon.png"):
        assert not pattern.match(plain), plain


def test_both_deploy_paths_run_it_after_the_build():
    ci = (REPO / ".github" / "workflows" / "deploy-gcp.yml").read_text(encoding="utf-8")
    by_hand = (REPO / "docs" / "deploy-by-hand.md").read_text(encoding="utf-8")
    for text in (ci, by_hand):
        assert "web_cache_bust.py" in text
        assert text.index("flutter build web") < text.index("web_cache_bust.py")
