"""Design-system enforcement. Fails when the UI would drift from the tokens.

Three checks, in order of how often they catch something real:

1. **No emoji.** The product bans them outright -- labels, buttons, empty
   states, errors, UI strings in test fixtures. An icon set exists so that
   emoji are never the only way to say something. This is the check most likely
   to fire, because emoji are the easiest thing to reach for.

2. **No raw colour or off-scale size.** Application source must reference a
   token, never a literal. A hardcoded `#4F46E5` or `13px` is invisible drift:
   it renders fine, survives review, and quietly diverges from every other
   screen. This is the check that stops an AI agent inventing a value.

3. **The generated CSS is current.** `design/tokens.css` is built from
   `design/tokens.json`; if the two disagree, someone edited the generated file
   or forgot to rebuild.

Exit code 1 on any finding, so it can be a CI gate.

    python scripts/check_design_tokens.py
    python scripts/check_design_tokens.py --quiet
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOKENS_JSON = REPO / "design" / "tokens.json"
TOKENS_CSS = REPO / "design" / "tokens.css"

# Where application source lives. Extend when the React client lands.
#
# One extension per pattern, deliberately. A `{ts,tsx,css}` brace group looks
# tidier and matches NOTHING -- pathlib has no brace expansion, so it silently
# matched zero files and this checker reported OK while never reading a single
# line of the React client. tests/test_design_tokens.py now asserts every glob
# matches real files, so the same hole cannot reopen quietly.
SCAN_GLOBS = [
    "frontend/lib/**/*.dart",
    "web/src/**/*.ts",
    "web/src/**/*.tsx",
    "web/src/**/*.css",
    # Static HTML only -- NOT `web/**/*.html`, which also matches Turbopack's
    # build output under web/.next/.
    "web/public/**/*.html",
    # design/screens.html is the review surface a human marks up. It is held to
    # the same rules as product code on purpose: a mockup that uses a raw hex or
    # an emoji teaches the wrong thing to everyone who reads it, and the whole
    # point of that file is to be read.
    "design/**/*.html",
]

# Never scanned: generated output, vendored code, docs, research, and the token
# files themselves (tokens.css legitimately contains raw hex -- it IS the
# mapping from token name to value).
SKIP_PARTS = (
    "node_modules", ".dart_tool", "build", "dist", ".git",
    ".next", "out", "coverage", ".turbo",
    "docs/research", "vendor", "design/tokens.css", "design/tokens.json",
    # Generated from design/tokens.json, exactly like design/tokens.css. It
    # legitimately contains raw hex, non-4px type sizes and breakpoint widths;
    # staleness against the JSON is enforced separately.
    "web/src/styles/tokens.css",
)


def _blank_comments(text: str, *, line_comments: bool) -> str:
    """Replace comment contents with spaces, preserving line numbering exactly.

    The check used to skip any line *starting* with a comment marker. That only
    handles whole-line comments: the continuation of a `/* ... */` block whose
    next line began with a backtick was scanned as code, and the checker flagged
    its own explanatory comment. Blanking is precise and keeps line numbers
    valid, so a finding still points at the real line.

    `line_comments` is False for CSS, where `//` is not a comment and occurs
    inside URLs.
    """
    out: list[str] = []
    i, n = 0, len(text)
    in_block = False
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if in_block:
            if c == "*" and nxt == "/":
                in_block = False
                out.append("  ")
                i += 2
            else:
                out.append("\n" if c == "\n" else " ")
                i += 1
        elif c == "/" and nxt == "*":
            in_block = True
            out.append("  ")
            i += 2
        elif line_comments and c == "/" and nxt == "/":
            while i < n and text[i] != "\n":
                out.append(" ")
                i += 1
        else:
            out.append(c)
            i += 1
    return "".join(out)

# Emoji and pictographic ranges. Calibrated to catch what "no emoji" means in a
# UI and NOT to flag ordinary typography: mathematical arrows (U+2190-21FF) and
# geometric shapes (U+2B00-2BFF) are deliberately excluded, because a doc arrow
# or a star in prose is not an emoji and flagging it would train people to
# ignore this check. Dingbats (U+2700-27BF, which includes check marks) ARE
# included: the design system says those become Lucide icons, not text glyphs.
EMOJI = re.compile(
    "["
    "\U0001F300-\U0001FAFF"  # symbols, pictographs, faces, transport, flags
    "\U0001F000-\U0001F2FF"  # enclosed characters, mahjong, dominoes
    "\U0001F1E6-\U0001F1FF"  # regional indicators (flag pairs)
    "\U0001F900-\U0001F9FF"  # supplemental symbols and pictographs
    "\U00002700-\U000027BF"  # dingbats, including check marks and crosses
    "\U0000FE0F"             # variation selector-16 (emoji presentation)
    "]+",
    flags=re.UNICODE,
)

HEX = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b")
# A px value that is not on the 4px scale (styles only -- Dart layout numbers
# are not CSS and are checked by their own conventions).
OFF_SCALE_PX = re.compile(r"\b(\d{1,3})px\b")

# Which declarations the off-scale check applies to.
#
# The rule's own message is "the space scale is 4px based" -- it is about
# SPACING, not about every pixel in a stylesheet. Applied to every declaration
# it flagged `width: 390px` (a phone frame) and `height: 76px` (a calendar cell)
# as spacing violations: 55 false positives in one file. That is exactly the
# failure mode the emoji regex's comment warns about -- a check that cries wolf
# trains people to skip it, and then it catches nothing.
#
# So it is narrowed to the properties that genuinely have tokens, which keeps
# every real guard and drops the noise. Deliberately excluded: `width`,
# `height`, `max-width`, `grid-template-*` and media-query conditions, which
# describe a component's intrinsic size or a breakpoint and have no spacing
# token to come from.
SPACING_PROPS = frozenset({
    "margin", "margin-top", "margin-right", "margin-bottom", "margin-left",
    "padding", "padding-top", "padding-right", "padding-bottom", "padding-left",
    "gap", "row-gap", "column-gap",
    "top", "right", "bottom", "left", "inset",
    "font-size", "line-height",
    "border-radius",
})

# Stops at a quote or angle bracket as well as at `;`/`{`/`}`.
#
# Without the quote stop, an inline `style="font-size:var(--text-sm)"` captured
# everything to the end of the line -- through the closing quote, the `>`, and
# all the prose after it -- so the words "26px for the compact variant" in a
# sentence were reported as an off-scale declaration. An attribute value ends at
# its quote; the regex has to know that.
_DECLARATION = re.compile(r"([-a-zA-Z]+)\s*:\s*([^;{}\"'<>]+)")

ALLOWED_PX = {0, 1, 2, 4, 6, 8, 10, 12, 16, 20, 24, 28, 32, 40, 44, 48, 56, 64, 720, 999}


def _declarations(line: str):
    """Yield (property, value) pairs from one line of CSS."""
    for m in _DECLARATION.finditer(line):
        yield m.group(1).lower(), m.group(2)


def _skip(path: Path) -> bool:
    """True when `path` is generated, vendored, or otherwise out of scope.

    Matching is per path *component*, not by substring. Substring matching was a
    silent hole: the entry `"out"` made `web/src/app/layout.tsx` invisible
    (lay-out), and `"build"` hid every Dart file with "build" in its name --
    including whole feature folders. A skip rule that quietly excludes real
    source is worse than no rule, because the check still reports OK.

    An entry containing "/" is matched as an exact file or a subtree.
    """
    rel = path.relative_to(REPO).as_posix()
    parts = set(rel.split("/"))
    for entry in SKIP_PARTS:
        if "/" in entry:
            if rel == entry or rel.startswith(f"{entry}/"):
                return True
        elif entry in parts:
            return True
    return False


def _source_files() -> list[Path]:
    seen: dict[Path, None] = {}
    for pattern in SCAN_GLOBS:
        for p in REPO.glob(pattern):
            if p.is_file() and not _skip(p):
                seen[p] = None
    return sorted(seen)


def _normalize_eol(text: str) -> str:
    """Line-ending-insensitive view of generated file content.

    A generated CSS file is compared against a fresh regeneration. The two can
    differ in line endings alone -- the generator writes the platform separator,
    while a checkout under `core.autocrlf=true` may hold either -- and that is
    not staleness.
    """
    return text.replace("\r\n", "\n").replace("\r", "\n")


def check_tokens_css_current() -> list[str]:
    """Every generated token CSS must match design/tokens.json.

    Two files are generated from one source: design/tokens.css, and a copy under
    web/src/styles/ (Turbopack will not import CSS from outside its project
    root). Both are checked, so neither can be hand-edited or left un-rebuilt.
    """
    targets = [TOKENS_CSS]
    if (REPO / "web").is_dir():
        targets.append(REPO / "web" / "src" / "styles" / "tokens.css")

    missing = [t for t in targets if not t.exists()]
    if missing:
        names = ", ".join(str(t.relative_to(REPO)) for t in missing)
        return [f"{names} missing -- run scripts/build_tokens_css.py"]

    before = {t: t.read_text(encoding="utf-8") for t in targets}
    subprocess.run(
        [sys.executable, str(REPO / "scripts" / "build_tokens_css.py")],
        cwd=REPO, capture_output=True, check=False,
    )

    findings: list[str] = []
    for target in targets:
        after = target.read_text(encoding="utf-8")
        # Compare CONTENT, not bytes. This check exists to catch a token that
        # was changed in tokens.json without regenerating the CSS -- not to
        # enforce a line ending.
        #
        # Comparing raw bytes made the test fail on every Windows checkout
        # (`core.autocrlf=true` gives a CRLF working file, while a file written
        # by any LF-producing tool is not). It reported "stale" while `git diff`
        # was empty and regenerating changed nothing, because git normalises
        # EOLs and this did not. A check that disagrees with git about whether a
        # file changed is a check nobody can act on.
        if _normalize_eol(before[target]) != _normalize_eol(after):
            findings.append(
                f"{target.relative_to(REPO)} is stale relative to design/tokens.json "
                f"-- run scripts/build_tokens_css.py and commit the result"
            )
        # Leave the tree exactly as found, byte for byte. `newline=""` disables
        # Python's EOL translation, which would otherwise rewrite the file with
        # the platform separator and turn a no-op check into a working-tree
        # change that git then reports as a modification.
        if before[target] != after:
            target.write_text(before[target], encoding="utf-8", newline="")
    return findings


def check_source(files: list[Path]) -> list[str]:
    token_colours = set()
    raw = json.loads(TOKENS_JSON.read_text(encoding="utf-8"))

    def collect(node):
        if isinstance(node, str):
            if node.startswith("#") and len(node) in (4, 7):
                token_colours.add(node.upper())
        elif isinstance(node, dict):
            for v in node.values():
                collect(v)
        elif isinstance(node, list):
            for v in node:
                collect(v)

    collect(raw)

    findings: list[str] = []
    for f in files:
        rel = f.relative_to(REPO).as_posix()
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            # The file vanished between globbing and reading -- a build tool
            # rewriting its own output, typically. Not a design finding.
            continue
        line_comments = rel.endswith((".ts", ".tsx", ".dart"))
        code = _blank_comments(text, line_comments=line_comments)
        for lineno, line in enumerate(code.splitlines(), start=1):
            for m in EMOJI.finditer(line):
                findings.append(
                    f"{rel}:{lineno}: emoji {m.group()!r} -- emoji are banned. "
                    f"Use a Lucide icon or a text label."
                )

            if rel.endswith((".css", ".tsx", ".ts", ".html")):
                for m in HEX.finditer(line):
                    if m.group().upper() not in token_colours:
                        findings.append(
                            f"{rel}:{lineno}: raw colour {m.group()} -- use a token "
                            f"from design/tokens.json (or add it there first)."
                        )
                if rel.endswith((".css", ".html")):
                    # CSS and HTML have real property names, so an off-scale
                    # value can be judged against the property it sits on.
                    for prop, value in _declarations(line):
                        if prop not in SPACING_PROPS:
                            continue
                        for m in OFF_SCALE_PX.finditer(value):
                            if int(m.group(1)) not in ALLOWED_PX:
                                findings.append(
                                    f"{rel}:{lineno}: off-scale {prop} value {m.group()} -- "
                                    f"the space scale is 4px based; use a token."
                                )
                else:
                    # TypeScript and Dart have no CSS property context, so there
                    # is nothing to scope by: any bare px literal is a hardcoded
                    # value with no token behind it. Checked unscoped, which is
                    # stricter than the CSS rule on purpose -- `"13px"` in a
                    # component is a magic number, not an intrinsic dimension.
                    for m in OFF_SCALE_PX.finditer(line):
                        if int(m.group(1)) not in ALLOWED_PX:
                            findings.append(
                                f"{rel}:{lineno}: off-scale size {m.group()} -- the space "
                                f"scale is 4px based; use a token."
                            )
                if re.search(r"outline\s*:\s*(none|0)", line) and "focus-ring" not in line:
                    findings.append(
                        f"{rel}:{lineno}: 'outline: none' without a replacement focus "
                        f"ring -- keyboard users lose their position. Use --focus-ring."
                    )
    return findings


def main() -> int:
    # Findings can contain non-Latin characters (that is the point of the emoji
    # check). The default Windows console codec is cp1252 and would raise while
    # printing the very violation it just found.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):  # pragma: no cover - older/odd stdout
        pass

    quiet = "--quiet" in sys.argv
    files = _source_files()
    findings = check_tokens_css_current() + check_source(files)

    if not quiet:
        print(f"scanned {len(files)} source file(s)")

    if not findings:
        print("design tokens: OK")
        return 0

    print(f"\n{len(findings)} design-system violation(s):\n")
    for f in findings:
        print(f"  {f}")
    print(
        "\nEvery value must come from design/tokens.json. Add the token there and "
        "rebuild with scripts/build_tokens_css.py; never hardcode."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
