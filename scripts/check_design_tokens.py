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
SCAN_GLOBS = [
    "frontend/lib/**/*.dart",
    "web/src/**/*.{ts,tsx,css}",
    "web/**/*.html",
]

# Never scanned: generated output, vendored code, docs, research, and the token
# files themselves (tokens.css legitimately contains raw hex -- it IS the
# mapping from token name to value).
SKIP_PARTS = (
    "node_modules", ".dart_tool", "build", "dist", ".git",
    "docs/research", "vendor", "design/tokens.css", "design/tokens.json",
)

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

ALLOWED_PX = {0, 1, 2, 4, 6, 8, 10, 12, 16, 20, 24, 28, 32, 40, 44, 48, 56, 64, 720, 999}


def _skip(path: Path) -> bool:
    rel = path.relative_to(REPO).as_posix()
    return any(part in rel for part in SKIP_PARTS)


def _source_files() -> list[Path]:
    seen: dict[Path, None] = {}
    for pattern in SCAN_GLOBS:
        for p in REPO.glob(pattern):
            if p.is_file() and not _skip(p):
                seen[p] = None
    return sorted(seen)


def check_tokens_css_current() -> list[str]:
    if not TOKENS_CSS.exists():
        return [f"{TOKENS_CSS.relative_to(REPO)} is missing -- run scripts/build_tokens_css.py"]
    before = TOKENS_CSS.read_text(encoding="utf-8")
    subprocess.run(
        [sys.executable, str(REPO / "scripts" / "build_tokens_css.py")],
        cwd=REPO, capture_output=True, check=False,
    )
    after = TOKENS_CSS.read_text(encoding="utf-8")
    if before != after:
        TOKENS_CSS.write_text(before, encoding="utf-8")  # leave the tree as found
        return [
            "design/tokens.css is stale relative to design/tokens.json -- "
            "run scripts/build_tokens_css.py and commit the result"
        ]
    return []


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
        text = f.read_text(encoding="utf-8", errors="ignore")
        for lineno, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith(("//", "#", "///", "*", "/*")):
                continue  # a comment may describe or reference a value

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
