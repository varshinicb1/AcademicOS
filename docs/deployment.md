# Deployment — the Render release

> **Scope.** This document describes **one of two backend releases**. The other
> is the GCP release (`docs/gcp-deployment.md`). It also does not deploy either
> client sub-product — the offline **Mobile** app and the cloud **Web** app are
> separate deliverables with their own build flags. If that distinction is not
> already clear, read [`PRODUCTS_AND_RELEASES.md`](PRODUCTS_AND_RELEASES.md)
> first; it is the source of truth for which thing is which.

This is the real, current picture of the **Render release** — written after
auditing the actual live setup (not the aspirational one), so treat this as the
source of truth *for that release* over any comment elsewhere that disagrees
with it.

## Live target: Render

The backend is live at `https://academicos-backend.onrender.com`, deployed
as an **image-backed Render web service** (Render pulls
`docker.io/varshinicb99/academicos-backend:v1` directly — it does not build
from a git connection to this repo).

Two earlier deploy-target attempts left artifacts in this repo that are
**not** part of this release:
- `Dockerfile`'s comments used to say "Cloud Run", which was stale when
  corrected on 2026-09-15 — at that time Cloud Run was an abandoned attempt and
  Render was the only target. **That is no longer the whole story:** Cloud Run is
  now the target of the deliberately separate **GCP release**
  (`docs/gcp-deployment.md`), which is written and reviewed but has never been
  executed. Cloud Run is still not live, but it is no longer dead either — don't
  read the old "stale comment" note as a reason to ignore it.
- `fly.toml` at the repo root was a real, valid Fly.io config, but nothing
  in `.github/workflows/` or `scripts/` ever deployed to it. Removed
  2026-09-18 after explicit confirmation — it was a third, undocumented
  deployment story alongside the real ones (Render, live; GCP, written but
  unrun), which is exactly the kind of contradiction that causes an agent
  reading the repo cold to guess wrong about what's actually deployed.

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

> This section is specific to the **Render release**. The GCP release uses Cloud
> SQL for the same eleven tables and GCS for blobs; see
> `docs/gcp-deployment.md`. Both go through the same store-level factory
> (`postgres_kv.durable_table`), which prefers Cloud SQL when `ACOS_POSTGRES_*`
> is set and Supabase otherwise — so the two releases share this codebase but
> never the same database.

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
  uniformly across all eight. What did get hardened (2026-09-15): that
  propagated failure is now a typed `SupabaseUnavailable` with the table,
  status and PostgREST body, answered by one app-level handler in
  `api/main.py` as a 503 naming the table — never the bare, information-
  free 500 the missing `users`/`sessions` tables produced.
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
- **Run `docs/supabase-setup.sql`** in the project's SQL editor. It
  provisions all ten Postgres tables (`assessments`, `papers`,
  `practice_sets`, `graded_evaluations`, `scan_sessions`,
  `school_templates`, `users`, `sessions`, `audit_log`, `learner_events`)
  with the exact column shapes each store reads/writes — these are real
  columns, not just an `id` + `payload JSONB`: PostgREST filters and orders
  on columns (e.g. `select(email=eq.…)`, `order="seq.desc"`), and
  `graded_evaluations`/`learner_events` need their composite uniqueness for
  upserts and pagination to work at all. The file is `if not exists`-
  guarded, so re-running it on a partially-set-up project is safe.
- A Storage bucket named `scan-media` (scan-session photos/PDFs) and
  another named `curriculum-snapshots` (CurriculumStore's whole-file
  snapshots) — both private buckets; the anon key is a server-side-only
  credential here, never shipped to the Flutter client.
- Verify with `GET /health/storage`: it probes every table in the SQL file
  and reports each one by name (`"tables": {"users": "ok", …}`), so a
  missing or mis-shaped table is visible in one request instead of
  surfacing as a 500 on the first auth call. Answers are cached 30s and
  refreshes are single-flighted (the probe is 10x-amplified upstream
  traffic, and an uncached version managed only ~4 rps on the free tier
  while starving real requests of threads) — so after provisioning a
  table, allow one TTL before trusting a still-red answer. This is how
  the 2026-09-15 incident (missing `users`/`sessions`, all auth routes
  500ing while the endpoint still said "reachable") stays visible if it
  ever regresses.

## Known gaps (honest, not silently worked around)

- Concurrency: a plain `sqlite3.Connection` opened with
  `check_same_thread=False` is not safe for two threads calling
  `execute()` on it at the same time — confirmed directly (see
  `EventStore`'s `_conn_lock`, added 2026-09-15 after a test reproduced
  `sqlite3.InterfaceError` under real concurrent access, and
  `CurriculumStore`'s `_exec`/`_fetchone`/`_fetchall` helpers, added the
  same day after a Render stress test caught concurrent curriculum reads
  returning rows with all-`None` fields). `EventStore` and
  `CurriculumStore` now guard every local-SQLite call site; most other
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
