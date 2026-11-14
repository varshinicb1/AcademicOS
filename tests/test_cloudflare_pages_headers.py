"""deploy/cloudflare/pages_headers.py: the web console's headers on Cloudflare Pages
are firebase.json's, with the API origin swapped and the cache rules translated."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("pages_headers", REPO / "deploy/cloudflare/pages_headers.py")
pages_headers = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pages_headers)

API = "https://api.example.in"


def _rules(text: str) -> dict[str, list[str]]:
    rules: dict[str, list[str]] = {}
    current = None
    for line in text.splitlines():
        if not line.startswith(" "):
            current = line
            rules[current] = []
        else:
            rules[current].append(line.strip())
    return rules


@pytest.fixture(scope="module")
def rules() -> dict[str, list[str]]:
    firebase = json.loads((REPO / "firebase.json").read_text(encoding="utf-8"))
    return _rules(pages_headers.render(firebase, API))


def test_every_firebase_header_is_on_every_page(rules):
    firebase = json.loads((REPO / "firebase.json").read_text(encoding="utf-8"))
    site = next(r for r in firebase["hosting"]["headers"] if r.get("source") == "**")
    keys = {line.split(":", 1)[0] for line in rules["/*"]}
    assert keys == {h["key"] for h in site["headers"]}


def test_csp_points_at_the_new_api_and_not_cloud_run(rules):
    csp = next(line for line in rules["/*"] if line.startswith("Content-Security-Policy:"))
    assert pages_headers.CLOUD_RUN_ORIGIN not in csp
    assert f"connect-src 'self' blob: data: {API}" in csp
    assert f"img-src 'self' data: blob: {API}" in csp


def test_only_hashed_entry_files_are_cached_long(rules):
    long_cached = {path for path, lines in rules.items()
                   if any("max-age=31536000" in line and "Cache-Control" in line for line in lines)}
    assert long_cached == set(pages_headers.HASHED_ENTRY_GLOBS)
    for glob in pages_headers.HASHED_ENTRY_GLOBS:
        # Pages merges matching rules: the site-wide no-cache must be detached first.
        assert rules[glob][0] == "! Cache-Control"


def test_the_document_is_never_cached(rules):
    for path in ("/index.html", "/"):
        assert "Cache-Control: no-cache, no-store, must-revalidate" in rules[path]
        assert "! Cache-Control" in rules[path]


def test_firebase_regex_still_matches_the_translated_rule():
    # If firebase.json's hashed-entry regex changes, the glob translation must too.
    firebase = json.loads((REPO / "firebase.json").read_text(encoding="utf-8"))
    regexes = [r["regex"] for r in firebase["hosting"]["headers"] if "regex" in r]
    assert regexes == [pages_headers.HASHED_ENTRY_REGEX]


@pytest.mark.parametrize("bad", ["http://api.example.in", "https://api.example.in/", "api.example.in"])
def test_refuses_a_bad_api_origin(bad):
    firebase = json.loads((REPO / "firebase.json").read_text(encoding="utf-8"))
    with pytest.raises(ValueError):
        pages_headers.render(firebase, bad)
