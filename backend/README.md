# This tree is not the live product — read before touching anything here

`backend/` is a **mostly-scaffolded rewrite** (~4k LOC) following the target architecture
documented in `docs/architecture.md` (separate SQLAlchemy/Alembic/Qdrant/MinIO dependency set,
its own `pyproject.toml`, its own `tests/`). Many modules here are stub interfaces, not finished
logic — do not assume anything under `backend/` is running in production or is tested to the
same bar as `src/academicos/`.

**The real, live, tested implementation is `src/academicos/`** (~35k LOC, 1,700+ passing tests,
what actually runs on Render/GCP and what `README.md` at the repo root documents). See
`CLAUDE.md`'s "Project" section for the full comparison between the two trees.

## Do not port fixes between the two trees casually

`src/academicos/` and `backend/academicos/` have diverging schemas and package layouts. A fix
made in one does not automatically apply to the other, and assuming it does has caused real
bugs before.

## When this tree *is* the right place to work

Only when the task is explicitly about the `backend/` rewrite itself, or about
`docs/architecture.md`'s target design. If you arrived here from a general "fix X" or "add Y"
request without either of those being named, you are very likely in the wrong tree — check
`src/academicos/` first.

## Standalone ingestion CLI

`AGENT_TASK_INGESTION.md` (repo root) describes a standalone ingestion CLI that targets
`backend/ingestion/` specifically (`python -m ingestion --resume --workers 4`, state tracked in
a SQLite `ingestion_state` table for auto-resume) — this is the one piece of `backend/` with a
concrete, documented usage pattern independent of the rest of the rewrite.
