"""The web host's Content-Security-Policy (firebase.json), held as a contract.

Until 2026-10-04 it was `frame-ancestors 'none'` only, which stops framing but does nothing about script an
attacker manages to inject. The policy below was tried against the built web app in a browser (signed in, every
student page, no violation) and against a probe: the pinned pdf.js loads, another unpkg script and an inline script
are blocked. These tests keep it from being loosened by accident."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

FIREBASE = Path(__file__).resolve().parents[1] / "firebase.json"


def _policy() -> dict[str, list[str]]:
    cfg = json.loads(FIREBASE.read_text(encoding="utf-8"))
    headers = [h for rule in cfg["hosting"]["headers"] for h in rule["headers"]]
    values = [h["value"] for h in headers if h["key"] == "Content-Security-Policy"]
    assert len(values) == 1, "exactly one Content-Security-Policy header"
    out: dict[str, list[str]] = {}
    for part in values[0].split(";"):
        bits = part.split()
        if bits:
            out[bits[0]] = bits[1:]
    return out


def test_scripts_run_only_from_this_site_and_two_named_places():
    script = _policy()["script-src"]
    assert "'self'" in script
    assert "'wasm-unsafe-eval'" in script, "CanvasKit is WebAssembly"
    for banned in ("'unsafe-inline'", "'unsafe-eval'", "*", "https:", "http:", "data:", "blob:"):
        assert banned not in script, f"script-src must not allow {banned}"
    others = [s for s in script if not s.startswith("'")]
    assert sorted(others) == [
        "https://unpkg.com/pdfjs-dist@3.2.146/build/",
        "https://www.gstatic.com",
    ], "the Flutter engine's CanvasKit, and the PDF preview's pdf.js pinned to one version's folder"


def test_nothing_else_is_loosened():
    p = _policy()
    assert p["default-src"] == ["'self'"]
    assert p["object-src"] == ["'none'"]
    assert p["base-uri"] == ["'self'"]
    assert p["form-action"] == ["'self'"]
    assert p["frame-ancestors"] == ["'none'"]
    for directive, sources in p.items():
        assert "*" not in sources, directive
        assert "'unsafe-eval'" not in sources, directive


def test_the_app_may_call_its_own_backend_and_no_other_api():
    connect = _policy()["connect-src"]
    backends = [s for s in connect if s.endswith(".run.app")]
    assert len(backends) == 1 and backends[0].startswith("https://"), backends
    assert not any(s.startswith("http://") for s in connect), "no plain-http origin in production"
    assert "https://accounts.google.com" not in connect, (
        "Google sign-in is off in production; enabling it means adding Google's four GSI entries "
        "(docs/gcp-deployment.md, 'Content-Security-Policy')")


def test_only_style_may_be_inline():
    p = _policy()
    assert "'unsafe-inline'" in p["style-src"], "Flutter web writes inline style"
    for directive in p:
        if directive != "style-src":
            assert "'unsafe-inline'" not in p[directive], directive


@pytest.mark.parametrize("key", ["Strict-Transport-Security", "X-Content-Type-Options", "X-Frame-Options"])
def test_the_other_security_headers_are_still_set(key):
    cfg = json.loads(FIREBASE.read_text(encoding="utf-8"))
    assert key in [h["key"] for rule in cfg["hosting"]["headers"] for h in rule["headers"]]
