"""The web bundle's entry files get URLs that change when their content does.

Until 2026-09-26 firebase.json served `main.dart.js` and `flutter_bootstrap.js`
as `immutable` for a year, and Flutter writes both under the same names every
build, so a browser that had loaded the app once never asked for them again
(audit 2026-09-26, item 8.3). The header is fixed, but a browser holding the old
copy still will not ask. index.html is never cached, so the URLs it leads to are
the lever: scripts/web_cache_bust.py makes index.html load
`flutter_bootstrap.js?v=<hash>` and the bootstrap load `main.dart.js?v=<hash>`.
"""
from __future__ import annotations

import importlib.util
import pathlib

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


def _urls(web):
    boot = (web / "flutter_bootstrap.js").read_text(encoding="utf-8")
    index = (web / "index.html").read_text(encoding="utf-8")
    return boot, index


def test_both_entry_urls_carry_a_content_hash(web):
    wcb.bust(web)
    boot, index = _urls(web)
    main_v = wcb.content_hash((web / "main.dart.js").read_bytes())
    boot_v = wcb.content_hash((web / "flutter_bootstrap.js").read_bytes())
    assert f'"mainJsPath":"main.dart.js?v={main_v}"' in boot
    assert f'src="flutter_bootstrap.js?v={boot_v}"' in index


def test_a_new_build_gets_new_urls(web):
    wcb.bust(web)
    _, before = _urls(web)
    (web / "main.dart.js").write_text("main(); // next build", encoding="utf-8")
    (web / "flutter_bootstrap.js").write_text(BOOTSTRAP, encoding="utf-8")
    (web / "index.html").write_text(INDEX, encoding="utf-8")
    wcb.bust(web)
    _, after = _urls(web)
    assert before != after


def test_running_it_twice_changes_nothing(web):
    wcb.bust(web)
    first = _urls(web)
    wcb.bust(web)
    assert _urls(web) == first
    boot, index = first
    assert boot.count("?v=") == 1 and index.count("?v=") == 1


def test_a_build_it_does_not_recognise_fails_loudly(web):
    """If Flutter changes how it names the entry point, a silent no-op would
    ship a bundle stale browsers never re-fetch -- the defect this exists for."""
    (web / "flutter_bootstrap.js").write_text("_flutter.loader.load();", encoding="utf-8")
    with pytest.raises(SystemExit, match="mainJsPath"):
        wcb.bust(web)


def test_both_deploy_paths_run_it_after_the_build():
    ci = (REPO / ".github" / "workflows" / "deploy-gcp.yml").read_text(encoding="utf-8")
    by_hand = (REPO / "docs" / "deploy-by-hand.md").read_text(encoding="utf-8")
    for text in (ci, by_hand):
        assert "web_cache_bust.py" in text
        assert text.index("flutter build web") < text.index("web_cache_bust.py")
