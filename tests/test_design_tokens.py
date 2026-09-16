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
  * `design/tokens.css` edited by hand, or not rebuilt after a token change
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

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
