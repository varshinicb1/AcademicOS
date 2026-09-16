"""Generate design/tokens.css from design/tokens.json.

One source of truth, one generated artifact, one guard. Writing the CSS by hand
as well would create a second copy of every value, which is exactly the drift
this system exists to prevent -- and the file a coding agent is most likely to
edit by hand.

Regenerate after any token change:

    python scripts/build_tokens_css.py

`scripts/check_design_tokens.py` verifies the generated file is current and
rejects raw hex/px values in application source.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOKENS = REPO / "design" / "tokens.json"
OUT = REPO / "design" / "tokens.css"

HEADER = """/* ===========================================================================
 * AcademicOS design tokens -- GENERATED FILE, DO NOT EDIT.
 *
 * Source:      design/tokens.json
 * Regenerate:  python scripts/build_tokens_css.py
 *
 * Editing this file by hand will be overwritten, and will fail
 * scripts/check_design_tokens.py. Add the value to tokens.json instead.
 *
 * Emoji are forbidden in this product. Use a Lucide icon or a text label.
 * =========================================================================== */
"""


def _px(v: float | int) -> str:
    return f"{v}px" if isinstance(v, (int, float)) and v != 0 else "0"


def main() -> int:
    t = json.loads(TOKENS.read_text(encoding="utf-8"))
    lines: list[str] = []

    def group(name: str) -> None:
        lines.append("")
        lines.append(f"  /* -- {name} " + "-" * max(0, 62 - len(name)) + " */")

    def decl(var: str, value: str) -> None:
        lines.append(f"  --{var}: {value};")

    lines.append(":root {")

    # colour -----------------------------------------------------------------
    group("brand")
    for k, v in t["color"]["brand"].items():
        if k != "comment":
            decl(f"color-brand-{k}", v)

    group("neutral")
    for k, v in t["color"]["neutral"].items():
        if k != "comment":
            decl(f"color-neutral-{k}", v)

    group("semantic (fg / bg / border)")
    for status, triple in t["color"]["semantic"].items():
        if status == "comment":
            continue
        for part, v in triple.items():
            decl(f"color-{status}-{part}", v)

    group("data visualisation")
    for i, v in enumerate(t["color"]["dataViz"]["series"], start=1):
        decl(f"color-series-{i}", v)

    # typography -------------------------------------------------------------
    group("typography")
    decl("font-ui", t["typography"]["family"]["ui"])
    decl("font-mono", t["typography"]["family"]["mono"])
    for name, spec in t["typography"]["size"].items():
        decl(f"text-{name}", _px(spec["px"]))
        decl(f"leading-{name}", _px(spec["lineHeight"]))
    for name, w in t["typography"]["weight"].items():
        decl(f"font-{name}", str(w))

    # space ------------------------------------------------------------------
    group("space (4px base, matches the Tailwind scale)")
    for k, v in t["space"]["scale"].items():
        decl(f"space-{k}", _px(v))

    # shape ------------------------------------------------------------------
    group("interactive fills (every button state resolves to one of these)")
    for k, v in t["interactive"].items():
        if k != "comment":
            decl(f"btn-{k}", v)

    group("radius")
    for k, v in t["radius"].items():
        decl(f"radius-{k}", _px(v))

    group("border width")
    for k, v in t["border"]["width"].items():
        decl(f"border-{k}", _px(v))

    group("shadow (two levels; cards use a border instead)")
    for k, v in t["shadow"].items():
        if k != "comment":
            decl(f"shadow-{k}", v)

    # stacking ---------------------------------------------------------------
    group("z-index (fixed ladder; never invent a value)")
    for k, v in t["zIndex"].items():
        if k != "comment":
            decl(f"z-{k}", str(v))

    # motion -----------------------------------------------------------------
    group("motion")
    for k, v in t["motion"]["duration"].items():
        decl(f"duration-{k}", f"{v}ms")
    for k, v in t["motion"]["easing"].items():
        decl(f"ease-{k}", v)

    # layout -----------------------------------------------------------------
    group("layout")
    for k, v in t["layout"].items():
        if k == "comment" or isinstance(v, dict):
            continue
        decl(f"layout-{k}", _px(v))
    for k, v in t["layout"]["breakpoint"].items():
        decl(f"breakpoint-{k}", _px(v))

    group("density")
    for mode, spec in t["density"].items():
        for k, v in spec.items():
            if k != "use":
                decl(f"{mode}-{k}", _px(v))

    # focus, targets ---------------------------------------------------------
    group("focus + targets")
    decl("focus-ring", t["focus"]["ring"])
    for k, v in t["targets"].items():
        if k != "comment":
            decl(f"target-{k}", _px(v))

    lines.append("}")
    lines.append("")
    lines.append("@media (prefers-reduced-motion: reduce) {")
    lines.append("  :root { --duration-instant: 0ms; --duration-fast: 0ms; --duration-normal: 0ms; }")
    lines.append("}")
    lines.append("")

    OUT.write_text(HEADER + "\n".join(lines), encoding="utf-8")
    count = sum(1 for line in lines if line.strip().startswith("--"))
    print(f"wrote {OUT.relative_to(REPO)} -- {count} custom properties")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
