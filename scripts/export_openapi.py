"""Export the live application's OpenAPI schema to `contract/openapi.json`.

Phase 1 of the Web-client migration (see `docs/frontend-platform-decision.md`).

Why this file is committed rather than generated on demand: the whole point of
"freeze the contract" is that a change to the API surface shows up as a **diff
in review**, before a client is written against it. A schema generated at build
time would move silently under the client and reproduce exactly the failure this
is meant to prevent -- 46 frontend calls that targeted routes which had never
existed, invisible until someone wired up a screen.

Serialisation is sorted and stable so the committed file only changes when the
API does. `tests/test_openapi_contract.py` regenerates and compares, failing CI
if the committed copy is stale.

Regenerate after any route change:

    python scripts/export_openapi.py
    npx --yes openapi-typescript@latest contract/openapi.json -o contract/api-types.ts
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
# Not set globally at import time: this module is imported by a test, and
# mutating os.environ process-wide from an import previously broke unrelated
# tests in this repo. Config falls back to cwd()/academicos-data.
os.environ.setdefault("ACOS_DATA_ROOT", str(REPO / "academicos-data"))

CONTRACT = REPO / "contract" / "openapi.json"
TYPES = REPO / "contract" / "api-types.ts"


def schema_text() -> str:
    """The OpenAPI schema, serialised deterministically.

    Single source of truth for both the exporter and the staleness test, so the
    two can never disagree about what "the schema" is.
    """
    from academicos.api.main import app

    return json.dumps(app.openapi(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> int:
    text = schema_text()
    CONTRACT.parent.mkdir(parents=True, exist_ok=True)
    CONTRACT.write_text(text, encoding="utf-8")

    spec = json.loads(text)
    ops = sum(
        len([m for m in methods if m in ("get", "post", "put", "patch", "delete")])
        for methods in spec["paths"].values()
    )
    secured = sum(
        1
        for methods in spec["paths"].values()
        for m, op in methods.items()
        if m in ("get", "post", "put", "patch", "delete") and op.get("security")
    )
    print(f"wrote {CONTRACT.relative_to(REPO)}")
    print(f"  {len(spec['paths'])} paths, {ops} operations, {secured} authenticated")
    print(f"  next: npx --yes openapi-typescript@latest "
          f"{CONTRACT.relative_to(REPO)} -o {TYPES.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
