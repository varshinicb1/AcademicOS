# Handover: AcademicOS — continue "fix all" workstream

You're picking up work in `C:\Users\varsh\OneDrive\Documents\Sarvam\AcademicOS` (Windows,
not a git submodule setup, branch `master`, nothing pushed to a remote in this workstream).
Read `CLAUDE.md` at the repo root first — it's the canonical project map (two parallel Python
trees, the Flutter Web/Mobile split, the Supabase/Cloud SQL durability pattern). This handover
only covers what changed recently and what's still open; it doesn't replace CLAUDE.md.

## Environment gotcha — read before running anything

The C: drive hit **0 bytes free** twice this session. It's fixed now (~20GB free), but the fix
was structural: `.venv` and `academicos-data` were moved to `D:\AcademicOS-venv` and
`D:\AcademicOS-academicos-data`, with NTFS junctions (`mklink /J`) left at the original paths
(`C:\...\AcademicOS\.venv`, `C:\...\AcademicOS\academicos-data`) so every existing reference
keeps working transparently. **Do not delete or "fix" these junctions** — they're not broken
symlinks, they're intentional. If disk space gets tight again, check `~/.gradle/caches`,
`frontend/build`, `frontend/.dart_tool`, and pip cache before anything more drastic — do NOT
attempt `Stop-Service wuauserv` / `Dism.exe` cleanup, both require real Windows elevation and
will fail outright in a sandboxed shell.

## Current git state — nothing committed yet

`git status --short` shows real, working, uncommitted changes across ~24 modified files plus a
handful of new untracked files (an OpenAPI reference doc/generator, a design-system doc, and
`docs/frontend-platform-decision.md` — a prior pass's recommendation doc on the React/Next.js
question, already written, not yet acted on). **Do not commit anything without explicit
instruction from the user** — there's a lot of independent work mixed into this one working
tree (auth/authz hardening from an earlier pass, this session's school_id + dead-code fixes).
If you're asked to commit, consider whether it should be split into multiple commits by concern
rather than one giant one.

## What's DONE and verified this session (real test numbers, not estimates)

1. **Question-bank web-bundle leak fixed** — `frontend/lib/presentation/settings/pages/settings_page.dart`
   now gates the "Download Data" tile behind `_kOfflineBuild` like its siblings, and
   `.github/workflows/deploy-gcp.yml` strips `build/web/assets/assets/corpus/questions.json`
   after `flutter build web --release`. Documented in `docs/PRODUCTS_AND_RELEASES.md` that any
   manual `flutter build web` (e.g. for GitHub Pages) must do this deletion too — the CI step
   only covers the GCP path.

2. **42 confirmed-dead frontend API methods deleted**, full dependency chain (repository
   interfaces → impls → use cases → DI registrations → offline mirror in `local_api_client.dart`).
   Verified via `scripts/audit_frontend_backend_contract.py` (76 matched calls, unchanged) and
   `flutter analyze` (0 new errors). `tests/test_frontend_backend_contract.py`'s `KNOWN_GAPS` is
   now empty — do not silently re-add entries to it without checking whether the call is
   actually reachable first.

3. **school_id column added to 3 previously-unscoped backend stores** — `PaperStore`,
   `PracticeStore`, `ScanSessionStore` (`src/academicos/assessment/*_store.py`). Threaded through
   every real save call site (`routes.py`, `pillar_routes.py`, `mobile_routes.py`,
   `mobile_scan.py`), plus `curriculum/routes.py`'s school-export route now actually covers these
   three stores. SQL migration files (`docs/supabase-setup.sql`, `deploy/gcp/schema.sql`) updated
   with explicit `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` (not just `CREATE TABLE IF NOT
   EXISTS`, which would silently no-op against the live Supabase project's already-existing
   tables). New test file `tests/test_school_scoped_stores.py` (8 tests) covers save/list
   round-trips, pre-existing-DB migration safety, and a regression test for a clobber-prevention
   COALESCE fix in `ScanSessionStore.save()`.

   **A genuine production bug was found and fixed while writing that test**: in all three
   stores, the `SCHEMA` constant's `CREATE INDEX ... ON <table>(school_id)` ran *before*
   `_migrate()` got a chance to `ALTER TABLE ADD COLUMN school_id` — so opening a real
   pre-2026-09-17 database (the exact scenario the migration exists for) would crash with
   `sqlite3.OperationalError: no such column: school_id` instead of migrating cleanly. Fixed by
   moving index creation into `_migrate()`, after the column-add. If you touch any of these three
   store files again, preserve that ordering (see the docstring on `PaperStore._migrate()`,
   which the other two reference).

4. **Confirmed test baseline** (both suites run clean after the disk-space fix, from scratch):
   - Backend: `pytest tests/` → **1184 passed, 14 skipped (all environment-gated — Cloud SQL
     adapter tests needing `ACOS_TEST_PG_*` env vars, plus 2 route-inventory tests that skip on
     out-of-order collection), 1 xfailed, 0 failures.**
   - Frontend: `flutter test` → **115 passed, 2 failed** — both failures are pre-existing
     integration tests (`assessment_api_integration_test.dart`,
     `assessment_parse_test.dart`) that hit `http://localhost:8000` and require a real backend
     running locally; they're not run in a sandboxed environment and are unrelated to any change
     made this session.

## What's PENDING

1. **React/Next.js Phase 1 ("freeze contract")** — user explicitly said "Start it now (Phase 1:
   freeze contract)" in response to a scoping question about the proposed Web-client migration
   documented in `docs/frontend-platform-decision.md`. Concretely: generate a TypeScript client
   from the backend's live OpenAPI schema and commit it as the frozen contract Phase 1 exists to
   establish. **Not started at all** — confirmed no `package.json`/`next.config.*` exist anywhere
   in the repo yet. This is the most likely "next thing" to pick up.

2. **GCP bootstrap execution** (`deploy/gcp/bootstrap.sh`) — written, never run. Requires the
   user's own real GCP project + billing credentials; not something an agent can do
   autonomously. Don't attempt to fake or stub this — surface it back to the user if it comes up.

3. **Commit decision** — the user hasn't said whether to commit the school_id/dead-code/bundle
   fixes yet, or how to split them. Ask before committing/pushing anything (see git-safety note
   above — never `--force`, never skip hooks, never amend rather than create a new commit).

## Key files if you need to reorient fast

- `CLAUDE.md` — project map, read first.
- `docs/PRODUCTS_AND_RELEASES.md` — two backend releases (Render live / GCP written-not-run),
  two Flutter sub-products (Web / offline Mobile).
- `docs/frontend-platform-decision.md` — the React/Next.js migration recommendation (not yet
  acted on beyond the Phase 1 ask above).
- `src/academicos/assessment/{paper,practice,scan_session}_store.py` — the three stores touched
  this session; read their module docstrings before changing them again.
- `tests/test_frontend_backend_contract.py` + `scripts/audit_frontend_backend_contract.py` — the
  ratchet test that will fail CI if a new dead frontend API call appears or a fixed one isn't
  removed from `KNOWN_GAPS`.
- `tests/test_school_scoped_stores.py` — new, covers the school_id work; keep it green.

## House rules already established this session (don't relitigate)

- Never claim something is "done" on an unconfirmed or red test suite — always run the real
  suite and quote real pass/fail counts, not "should work."
- `school_id` is store-level metadata on these three stores, not a field on the domain object
  itself (`GeneratedPaper`, `PracticeSet`, `ScanSession` are unchanged) — this was a deliberate
  choice, don't "fix" it into a schema field without discussing it first.
- Report genuine completion percentage against the full ask, not against just the piece you
  personally touched — the user explicitly wants honest, non-inflated status, every reply.
