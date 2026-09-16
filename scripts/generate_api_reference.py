"""Generate docs/api-reference.md from the live OpenAPI schema.

The reference is generated rather than hand-maintained on purpose: a
hand-written endpoint list is stale within a week, and this project already has
one documented case of that (`TRANSCRIPT_REQUIREMENTS_MATRIX.md`'s summary).
Regenerate with:

    python scripts/generate_api_reference.py

Run it whenever routes change. The output is a plain markdown file, so it
diffs cleanly in review and a stale reference is visible as a missing commit.
"""
from __future__ import annotations

import os
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
os.environ.setdefault("ACOS_DATA_ROOT", str(REPO / "academicos-data"))

from academicos.api.main import app  # noqa: E402

HEADER = """# API reference (generated)

**Do not edit by hand.** Generated from the running application's OpenAPI
schema by `scripts/generate_api_reference.py`.

* **Base URL (Render release):** `https://academicos-backend.onrender.com`
* **Base URL (GCP release):** the Cloud Run service URL
* **Path prefix:** every operation is under `/api/v1` (the older `/v1/*`
  corpus/agent surface is also present and is now authenticated)
* **Live schema:** `GET /openapi.json` · **Interactive docs:** `GET /docs`

`Auth` is `bearer` when the operation requires an authenticated caller
(`Depends(get_current_user)` or `require_principal`), and `open` when it does
not. This column is derived from the schema's `security` field, which is only
populated because the auth dependency declares `HTTPBearer` — see
[`api.md`](api.md#contract-discipline).
"""

DOMAIN_TITLES = {
    "/api/v1/assessments": "Assessments",
    "/api/v1/auth": "Authentication",
    "/api/v1/blueprints": "Blueprints",
    "/api/v1/catalog": "Catalog",
    "/api/v1/consent": "Parental consent (DPDP)",
    "/api/v1/curriculum": "Curriculum, calendar, scheduling & reporting",
    "/api/v1/evaluations": "Evaluations",
    "/api/v1/ingest": "Document ingestion",
    "/api/v1/insights": "Insights",
    "/api/v1/knowledge": "Learner knowledge & mastery",
    "/api/v1/mail": "Paper delivery",
    "/api/v1/papers": "Question papers",
    "/api/v1/practice": "Practice",
    "/api/v1/questions": "Question bank",
    "/api/v1/scan": "Scan & capture",
    "/api/v1/schools": "School templates",
    "/api/v1/syllabus": "Syllabus & pacing",
    "/health": "Health & diagnostics",
    "/v1": "Legacy corpus & agent surface",
}


def domain_of(path: str) -> str:
    for prefix in sorted(DOMAIN_TITLES, key=len, reverse=True):
        if path == prefix or path.startswith(prefix + "/"):
            return prefix
    return "Other"


def clean(text: str | None) -> str:
    """OpenAPI summaries are the first docstring line; collapse to one line."""
    if not text:
        return ""
    line = text.strip().splitlines()[0].strip()
    line = " ".join(line.split())
    if line.endswith("."):
        line = line[:-1]
    # Keep the table readable and free of pipe-breaking characters.
    return line.replace("|", "\\|")


def main() -> int:
    spec = app.openapi()
    grouped: dict[str, list[tuple[str, str, str, str]]] = defaultdict(list)

    for path, ops in spec["paths"].items():
        for method, op in ops.items():
            if method not in ("get", "post", "put", "patch", "delete"):
                continue
            grouped[domain_of(path)].append((
                method.upper(),
                path,
                "bearer" if op.get("security") else "open",
                clean(op.get("summary") or op.get("description")),
            ))

    total = sum(len(v) for v in grouped.values())
    secured = sum(1 for v in grouped.values() for r in v if r[2] == "bearer")

    out = [HEADER, ""]
    out.append(f"**{total} operations** across {len(grouped)} domains — "
               f"{secured} require authentication, {total - secured} are open.\n")
    out.append("## Contents\n")
    for prefix in sorted(grouped, key=lambda p: DOMAIN_TITLES.get(p, p)):
        title = DOMAIN_TITLES.get(prefix, prefix)
        anchor = title.lower().replace(" & ", "--").replace(" ", "-")
        anchor = "".join(c for c in anchor if c.isalnum() or c in "-_")
        out.append(f"- [{title}](#{anchor}) — {len(grouped[prefix])} operations")
    out.append("")

    for prefix in sorted(grouped, key=lambda p: DOMAIN_TITLES.get(p, p)):
        title = DOMAIN_TITLES.get(prefix, prefix)
        rows = sorted(grouped[prefix], key=lambda r: (r[1], r[0]))
        out.append(f"\n## {title}\n")
        out.append("| Method | Path | Auth | Purpose |")
        out.append("|---|---|---|---|")
        for method, path, auth, summary in rows:
            out.append(f"| `{method}` | `{path}` | {auth} | {summary} |")
        out.append("")

    target = REPO / "docs" / "api-reference.md"
    target.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"wrote {target.relative_to(REPO)} — {total} operations, {secured} authenticated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
