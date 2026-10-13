# Deployment — the Render release (retired)

> **Retired on 2026-10-13. Nothing on this page describes the live system.**
> Production is Cloud Run and Firebase Hosting, deployed by
> `.github/workflows/deploy-gcp.yml` on every merge to `master`
> ([`gcp-deployment.md`](gcp-deployment.md), [`deploy-by-hand.md`](deploy-by-hand.md)).
> The Render sync workflow (`deploy-backend.yml`), its keep-warm ping
> (`keep-backend-warm.yml`), `scripts/render_deploy_status.py` and the two
> one-off push scripts were removed that day. The page is kept because it
> records why the stores are built the way they are: the Supabase fallback and
> the whole-file snapshot restore below began here.

> **Scope (historical).** This document describes **one of two backend releases**. The other
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

### CI/CD pipeline and keep-warm (removed 2026-10-13)

`.github/workflows/deploy-backend.yml` ran the test suite, mirrored the backend
into `varshinicb1/academicos-backend` (whose own workflow built the Docker Hub
image Render pulled), and polled Render's API until the new deploy went live.
`.github/workflows/keep-backend-warm.yml` pinged `/health` every 10 minutes to
keep the free-tier container from idling. Both were removed once Render stopped
being used: the sync job had failed on every run since 2026-10-12 (the runner
ran out of disk installing every optional extra), and the ping spent Actions
minutes on a service no school uses.

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
| `ACOS_PRINCIPAL_BOOTSTRAP_KEY` | Operator secret. With a `schoolId`, creates that school's FIRST principal at `/auth/register`; refused (403) once the school has one. Unset means nobody can register as principal. |
| `ACOS_SEED_DEMO_USERS` | **Leave unset in production.** `1` seeds `teacher@school.com` / `principal@school.com` with a published password into `demo_school`, for a local demo only. |

**Accounts (since 2026-09-21):** nobody joins a school by typing its id.
The operator creates each new school's first principal with the bootstrap
key above; that principal then invites every teacher and student from the
web admin console (Roster > Invite people, or `POST /api/v1/auth/invites`),
and `/auth/register` takes the account's school and role from the invite.
There are no demo accounts on a deployment unless `ACOS_SEED_DEMO_USERS` is
set; before this change they were re-created on every Render cold start
(the local users table is empty after each restart). Accounts created before
the change keep their stored school and role, and the code cannot tell a
self-asserted membership from a real one, so review each school's roster
(`GET /api/v1/auth/users`) once after deploying, and delete
`principal@school.com` / `teacher@school.com` from the Supabase `users`
table if they are there.

Without both Supabase variables set, every store above falls back to local SQLite — the
service still works, it just reverts to the original ephemeral-disk
behavior. Check whether they're actually configured (and whether Supabase
is currently reachable) via `GET /health/storage` rather than guessing
from the Render dashboard.

**Before merging invite registration (2026-09-21) to `master`: run the
SQL first.** A push to `master` reaches Render with no manual gate (sync,
image build, auto-redeploy), so the order has to be kept by hand:

1. In the live Supabase project's SQL editor, run `docs/supabase-setup.sql`
   (it is `if not exists`-guarded; the new table is `invites`).
2. Confirm `invites` exists in the Supabase table editor. `/health/storage`
   cannot tell you yet: the deploy before this change does not probe
   `invites` (it was added to `_DURABLE_TABLES` in the same change).
3. Only then merge. After the new deploy is live, wait one 30s TTL and
   check `/health/storage` for `"invites": "ok"`. If the table is missing,
   `durability_reachable` is `false` and `tables.invites` starts with
   `error:` (tests/test_supabase_failure_surfaces.py pins this), every
   invite create/list/revoke/redeem answers 503, and the only way to add
   an account is the principal bootstrap key; and since 2026-09-22 a
   missing `users` table makes registration a 503 too, instead of saving
   the account to the local disk that the next cold start wipes.

The endpoint answers HTTP 200 either way; the verdict is the
`durability_reachable` field (and the legacy `supabase_reachable`, which the
Flutter client and the cutover runbook read). It is deliberately not a
failing health check: nothing points Render's health check at it, and a
Supabase blip must not make Render kill a container that can still serve
reads.

**Required Supabase setup** (one-time, in the Supabase project itself):
- **Run `docs/supabase-setup.sql`** in the project's SQL editor. It
  provisions the Postgres tables (`assessments`, `papers`,
  `practice_sets`, `graded_evaluations`, `scan_sessions`,
  `school_templates`, `users`, `sessions`, `invites`, `audit_log`,
  `learner_events`, `parental_consents`; re-run it after 2026-09-21 to add
  `invites`, which registration now needs; until it exists, creating,
  listing, revoking and redeeming invites all answer 503 rather than
  saving codes on Render's ephemeral disk, and `/health/storage` names the
  missing table)
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
