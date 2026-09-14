# Deployment

This is the real, current deployment picture — written after auditing the
actual live setup (not the aspirational one), so treat this as the source
of truth over any comment elsewhere that disagrees with it.

## Live target: Render

The backend is live at `https://academicos-backend.onrender.com`, deployed
as an **image-backed Render web service** (Render pulls
`docker.io/varshinicb99/academicos-backend:v1` directly — it does not build
from a git connection to this repo).

Two earlier deploy-target attempts left artifacts in this repo that are
**not** the active deployment:
- `Dockerfile`'s comments used to say "Cloud Run" — stale, corrected
  2026-09-15. Cloud Run was never the live target for the current setup.
- `fly.toml` at the repo root is a real, valid Fly.io config, but nothing
  in `.github/workflows/` or `scripts/` deploys to it. Left in place rather
  than deleted unilaterally (may have been an intentional backup option),
  but don't assume it's live — it isn't wired to anything today.

### CI/CD pipeline (`.github/workflows/deploy-backend.yml`)

On every push to `master` touching `pyproject.toml`, `config/**`,
`src/academicos/**`, or `academicos-data/syllabus/**`:

1. **test** — runs the real pytest suite (all extras) against
   `src/academicos`. A real gate: a failing test blocks the sync stage
   below, so a regression can't reach production undetected.
2. **sync** — mirrors backend-relevant files (excluding the Flutter
   frontend) into a separate `varshinicb1/academicos-backend` repo and
   pushes. That repo's own `build-push.yml` (triggered by this push)
   builds a fresh Docker image and pushes it to Docker Hub, which Render
   picks up automatically (image-backed services redeploy on a new image
   push, not on a git push to this repo).
3. **render-deploy** — polls Render's API (`scripts/render_deploy_status.py`)
   until a deploy newer than a pre-sync snapshot goes live, failing the
   workflow if the new deploy build-fails, is canceled, or never goes live
   within 30 minutes. Needs `RENDER_API_KEY` (secret) and
   `RENDER_SERVICE_ID` (variable) to actually verify the rollout — without
   them the pipeline still syncs and deploys, it just can't confirm it.

### Keep-warm (`.github/workflows/keep-backend-warm.yml`)

Render's free tier spins the container down after ~15 minutes idle, and a
cold start (pulling the image, booting opencv/pymupdf) measured close to
60 seconds. A GitHub Action pings `/health` every 10 minutes so a
teacher/student opening the app never sees that cold-start spinner.

## Data durability: Supabase

**The problem:** an image-backed Render service with no persistent disk
means anything written at runtime — new assessments, grades, scan
sessions, curriculum edits — lives only in the container's ephemeral
filesystem. It survives until the next redeploy or restart, then it's
gone, even though nothing about the data was ever wrong.

**The fix, two different strategies depending on the store's shape:**

- **Flat, single-object stores** (`AssessmentStore`, `PaperStore`,
  `PracticeStore`, `GradedStore`, `ScanSessionStore`, `TemplateStore`,
  `UserStore`, `AuditLog`, `EventStore`) wrap each table in
  `SupabaseTable` (`src/academicos/assessment/supabase_kv.py`) — a
  minimal PostgREST client. Each read/write branches: if Supabase is
  configured, use it; on a live failure (or if unconfigured), fall back
  to local SQLite. Only some of these stores catch a live Supabase
  failure and fall back gracefully (`AssessmentStore`, `EventStore`); the
  others currently let the exception propagate if Supabase is enabled
  but briefly unreachable — a known inconsistency, not yet hardened
  uniformly across all eight.
- **`CurriculumStore`** owns 18 relational tables with real foreign-key
  relationships — wrapping each table individually would mean 18 REST
  call sites and would lose that FK integrity across two storage layers.
  Instead it snapshots/restores the **whole SQLite file** as one blob via
  `SupabaseStorage` (the same class already used for scan-session photo/
  PDF blobs, different bucket): every write debounce-uploads a WAL-
  checkpointed copy of the file, and a fresh container with no local
  state restores the last snapshot before opening the database.

### Required environment variables (set on the Render service, not in
`config/config.toml` — that file is committed)

| Variable | Purpose |
|---|---|
| `SUPABASE_KNOWLEDGE_URL` | Base URL of the Supabase project (e.g. `https://xxxx.supabase.co`) |
| `SUPABASE_KNOWLEDGE_ANON_KEY` | The project's anon/service key used for the REST calls above |

Without both set, every store above falls back to local SQLite — the
service still works, it just reverts to the original ephemeral-disk
behavior. Check whether they're actually configured (and whether Supabase
is currently reachable) via `GET /health/storage` rather than guessing
from the Render dashboard.

**Required Supabase setup** (one-time, in the Supabase project itself):
- A Postgres table per flat store, named to match each
  `SupabaseTable("...")` call (`assessments`, `papers`, `practice_sets`,
  `graded_evaluations`, `scan_sessions`, `school_templates`, `users`,
  `sessions`, `audit_log`, `learner_events`), each with an `id`/`event_id`-
  shaped primary key and a `payload JSONB` column (see `supabase_kv.py`
  for the exact shape each store upserts).
- A Storage bucket named `scan-media` (scan-session photos/PDFs) and
  another named `curriculum-snapshots` (CurriculumStore's whole-file
  snapshots) — both private buckets; the anon key is a server-side-only
  credential here, never shipped to the Flutter client.

## Known gaps (honest, not silently worked around)

- Concurrency: a plain `sqlite3.Connection` opened with
  `check_same_thread=False` is not safe for two threads calling
  `execute()` on it at the same time — confirmed directly (see
  `EventStore`'s `_conn_lock`, added 2026-09-15 after a test reproduced
  `sqlite3.InterfaceError` under real concurrent access). `EventStore` now
  guards every local-SQLite call site; `CurriculumStore` and most other
  stores still don't, which is a real latent risk under true multi-teacher
  concurrent writes to the *local fallback* path specifically (the
  Supabase path doesn't share this risk — each thread makes its own
  independent HTTP request). Flagged, not silently left undocumented;
  hardening every remaining call site is separate follow-up work.
- Supabase error-fallback consistency: see above — only `AssessmentStore`
  and `EventStore` catch a live failure and degrade gracefully today.
- School-data export (`GET /api/v1/curriculum/export`) covers everything
  cleanly `school_id`-scoped: curriculum tree, assessments, paper
  templates, users. It does **not** cover `PaperStore`/`PracticeStore`/
  `ScanSessionStore` — those three have no `school_id` column at all
  (school identity, if present, lives unindexed inside JSON payloads).
  Partitioning them per-school is real follow-up work.
- No import/restore endpoint exists yet for the export bundle above —
  exporting for backup/audit/manual transfer was the concrete ask;
  restoring from an export into a fresh instance is a natural next step
  once the export shape has been validated against real data.
