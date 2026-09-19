"""Design-system enforcement, as a test.

`scripts/check_design_tokens.py` is the implementation; this makes it part of the
gate that already runs before any deploy, rather than a script somebody has to
remember. Same reasoning as `tests/test_openapi_contract.py`: a rule in prose
gets ignored, a failing build does not.

Catches, in the order they tend to fire:
  * an emoji anywhere in application source -- the design system bans them
  * a raw hex colour that is not a token
  * an off-scale spacing or size value
  * `outline: none` with no replacement focus ring
  * `design/tokens.css` (and its generated copy under `web/`) edited by hand,
    or not rebuilt after a token change

The last four tests exist because this check has already failed twice in ways
that produced a green build:

  * `web/src/**/*.{ts,tsx,css}` matched zero files -- pathlib has no brace
    expansion -- so no line of the React client was ever read.
  * Comment stripping only skipped whole-line comments, so a `/* ... */`
    block's continuation line was scanned as code and the checker flagged its
    own explanatory comment.

Both were silent. `test_every_scan_glob_matches_files` and
`test_comment_content_is_not_scanned` are the ratchets.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
_CHECKER = REPO / "scripts" / "check_design_tokens.py"


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_design_tokens", _CHECKER)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_generated_token_css_is_current():
    checker = _load_checker()
    findings = checker.check_tokens_css_current()
    assert not findings, (
        "design/tokens.css does not match design/tokens.json.\n"
        "Run: python scripts/build_tokens_css.py  and commit the result.\n"
        + "\n".join(findings)
    )


def test_no_design_system_violations_in_source():
    checker = _load_checker()
    files = checker._source_files()
    findings = checker.check_source(files)
    assert not findings, (
        f"{len(findings)} design-system violation(s) across {len(files)} file(s):\n"
        + "\n".join(f"  {f}" for f in findings)
        + "\n\nEvery value must come from design/tokens.json. Add it there and "
          "rebuild; never hardcode. Emoji are banned outright."
    )


def test_emoji_detector_actually_detects():
    """A guard that never fires is worse than none -- it grants false confidence.

    Pins both directions: real pictographs are caught, ordinary typography
    (arrows, mathematical symbols) is not, so the check does not become noise
    that people learn to skip.
    """
    checker = _load_checker()
    flagged = {
        "rocket": "\U0001F680",
        "white heavy check": "\u2705",
        "books": "\U0001F4DA",
        "check mark (a Lucide icon, not a glyph)": "\u2713",
    }
    allowed = {
        "ascii": "Schedule generated",
        "right arrow": "\u2192",
        "double arrow": "\u21D2",
        "black star": "\u2605",
        "em dash": "\u2014",
    }
    for label, ch in flagged.items():
        assert checker.EMOJI.search(f"x{ch}y"), f"{label} should be flagged as emoji"
    for label, ch in allowed.items():
        assert not checker.EMOJI.search(f"x{ch}y"), f"{label} must not be flagged"


def test_every_scan_glob_matches_files():
    """A glob that matches nothing is a guard that guards nothing.

    This is not hypothetical. `web/src/**/*.{ts,tsx,css}` read as correct and
    matched zero files, because pathlib has no brace expansion. The checker
    reported "design tokens: OK" for weeks while never reading a line of the
    React client.
    """
    checker = _load_checker()
    for pattern in checker.SCAN_GLOBS:
        prefix = pattern.split("*")[0].rstrip("/")
        if not (REPO / prefix).exists():
            continue  # the tree this pattern targets is not present yet
        matches = [p for p in REPO.glob(pattern) if p.is_file()]
        assert matches, (
            f"SCAN_GLOBS entry {pattern!r} matched no files, but {prefix}/ exists. "
            f"The glob is wrong, or the tree moved. Fix the glob -- do not delete "
            f"the entry, and do not assume the file extension is the problem."
        )


def test_web_client_source_is_scanned():
    """The React client must be inside the guard, not merely near it."""
    if not (REPO / "web" / "src").is_dir():
        return
    checker = _load_checker()
    scanned = [f.relative_to(REPO).as_posix() for f in checker._source_files()]
    web = [f for f in scanned if f.startswith("web/src/")]
    assert web, "no file under web/src/ was scanned -- the React client is unguarded"
    assert any(f.endswith("app/globals.css") for f in web), scanned
    assert any(f.endswith("app/layout.tsx") for f in web), scanned


def test_checker_fails_on_a_react_violation():
    """End-to-end proof the detectors bite on .tsx/.ts/.css under web/src."""
    checker = _load_checker()
    probe = REPO / "web" / "src" / "lib" / "__design_probe.ts"
    probe.parent.mkdir(parents=True, exist_ok=True)
    try:
        probe.write_text(
            "export const probe = {\n"
            '  emoji: "\U0001F600",\n'
            '  hex: "#FF00AA",\n'
            '  px: "13px",\n'
            '  focus: "outline: none",\n'
            "};\n",
            encoding="utf-8",
        )
        findings = checker.check_source([probe])
    finally:
        probe.unlink(missing_ok=True)

    joined = "\n".join(findings)
    assert len(findings) == 4, f"expected 4 findings, got:\n{joined}"
    assert "emoji" in joined
    assert "raw colour" in joined
    assert "off-scale" in joined
    assert "outline: none" in joined


def test_comment_content_is_not_scanned():
    """Comments may describe or reference a value without failing the build.

    Specifically: the continuation line of a block comment is still a comment,
    even when it does not begin with a comment marker.
    """
    checker = _load_checker()
    probe = REPO / "web" / "src" / "lib" / "__design_probe_comment.ts"
    probe.parent.mkdir(parents=True, exist_ok=True)
    try:
        probe.write_text(
            "/* A block comment mentioning #FF00AA, 13px, outline: none, and \U0001F600.\n"
            "   Continuation line, no comment marker, still #ABCDEF and \U0001F680.\n"
            "   The --focus-ring token is referenced here too. */\n"
            "export const ok = 1;\n",
            encoding="utf-8",
        )
        findings = checker.check_source([probe])
    finally:
        probe.unlink(missing_ok=True)

    assert not findings, "comment text must not be scanned:\n" + "\n".join(findings)


def test_generated_web_token_copy_is_current():
    """The copy inside web/ is generated too, and must not drift from the JSON."""
    if not (REPO / "web").is_dir():
        return
    checker = _load_checker()
    findings = checker.check_tokens_css_current()
    assert not findings, (
        "generated token CSS is stale.\n"
        "Run: python scripts/build_tokens_css.py  and commit the result.\n"
        + "\n".join(findings)
    )


# --------------------------------------------------------------------------- #
# the off-scale check is scoped to spacing, and still bites
# --------------------------------------------------------------------------- #
# Narrowing a check is exactly the change that can silently disable it, so the
# scope is pinned in both directions: off-scale SPACING must be caught, and a
# component's intrinsic size must not be. Before this was scoped, a single
# hand-written stylesheet produced 55 false positives from `width: 390px` and
# `height: 76px`, which is the "cry wolf" failure that gets a check ignored.

def _probe_css(checker, lines: list[str]) -> list[str]:
    probe = (REPO / "design" / "__scope_probe.html").resolve()
    probe.parent.mkdir(parents=True, exist_ok=True)
    try:
        probe.write_text("<style>\n" + "\n".join(lines) + "\n</style>\n", encoding="utf-8")
        return checker.check_source([probe])
    finally:
        probe.unlink(missing_ok=True)


@pytest.mark.parametrize("declaration", [
    "  .x { padding: 13px; }",
    "  .x { gap: 7px; }",
    "  .x { margin-top: 9px; }",
    "  .x { font-size: 15px; }",
    "  .x { border-radius: 5px; }",
    "  .x { padding: 12px 13px; }",
])
def test_off_scale_spacing_is_caught(declaration):
    checker = _load_checker()
    findings = _probe_css(checker, [declaration])
    assert findings, f"off-scale spacing slipped through: {declaration}"


@pytest.mark.parametrize("declaration", [
    "  .x { width: 390px; }",         # a phone frame
    "  .x { height: 76px; }",         # a calendar cell
    "  .x { max-width: 900px; }",
    "  .x { grid-template-columns: 260px 1fr; }",
])
def test_component_dimensions_are_not_treated_as_spacing(declaration):
    """These have no spacing token to come from, and flagging them is noise."""
    checker = _load_checker()
    findings = _probe_css(checker, [declaration])
    assert not findings, f"a component dimension was wrongly flagged: {findings}"


@pytest.mark.parametrize("declaration", [
    "  .x { padding: var(--space-3); }",
    "  .x { padding: 12px; }",
    "  .x { gap: 8px; }",
    "  .x { border-radius: 6px; }",
    "  .x { border: 1px solid red; }",
])
def test_on_scale_and_tokenised_spacing_passes(declaration):
    checker = _load_checker()
    findings = _probe_css(checker, [declaration])
    assert not findings, f"a valid declaration was flagged: {findings}"


def test_scope_probe_does_not_outlive_the_test():
    """These tests write into design/; nothing may be left behind."""
    assert not (REPO / "design" / "__scope_probe.html").exists()


# --- the staleness check must not disagree with git about line endings -----

def test_a_crlf_working_file_is_not_reported_stale():
    """`core.autocrlf=true` on Windows gives a CRLF working file.

    The checker regenerates and compares, and the generator writes the platform
    separator -- so a byte comparison reported "stale" on every Windows
    checkout while `git diff` was empty and regenerating changed nothing. A
    check that disagrees with git about whether a file changed is a check
    nobody can act on.
    """
    checker = _load_checker()
    target = REPO / "design" / "tokens.css"
    original = target.read_bytes()
    try:
        as_lf = original.replace(b"\r\n", b"\n")
        target.write_bytes(as_lf.replace(b"\n", b"\r\n"))
        assert not checker.check_tokens_css_current(), (
            "a CRLF working file was reported stale; line endings are not "
            "staleness"
        )
    finally:
        target.write_bytes(original)
    assert target.read_bytes() == original, "the test did not restore the file"


def test_genuine_staleness_is_still_detected():
    """The complement: normalising EOLs must not blind the check.

    A test that only proves false positives are gone is worthless if it also
    stopped catching the real thing.
    """
    checker = _load_checker()
    target = REPO / "design" / "tokens.css"
    original = target.read_bytes()
    try:
        with open(target, "a", encoding="utf-8", newline="") as fh:
            fh.write("\n:root { --not-a-real-token: 1px; }\n")
        assert target.read_bytes() != original, "the fixture failed to change the file"
        findings = checker.check_tokens_css_current()
        assert findings, "a real content change was NOT reported as stale"
    finally:
        target.write_bytes(original)
    assert target.read_bytes() == original, "the test did not restore the file"
    assert not checker.check_tokens_css_current()
