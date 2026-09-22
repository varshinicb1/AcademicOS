# The GCP release — AcademicOS on Google Cloud

> **Scope.** This is the second of two backend releases, not a migration of the
> only one. The **Render release** keeps running, unchanged, from the same
> codebase; see `docs/deployment.md`. The two coexist and are switched by
> environment variables, so a rollback is a config change rather than a
> redeploy. For which thing is which (including the two client sub-products —
> offline Mobile, cloud Web), read
> [`PRODUCTS_AND_RELEASES.md`](PRODUCTS_AND_RELEASES.md).

Target reader: whoever stands up the GCP release. Assumes a GCP project with
billing enabled (the $50k credit pool covers decades of this — see §7) and
owner access to the one GitHub repo that matters here, `varshinicb1/AcademicOS`.

The GCP release is deliberately **not** the Render release moved. It is
GCP-native: Cloud Run for compute, Cloud SQL for the twelve durable tables, GCS
for blobs, Secret Manager for secrets, and keyless CI via Workload Identity
Federation so that no service-account key exists anywhere. The GCP deploy
injects no Supabase credentials at all: structured data is in Cloud SQL and
blobs (scan media, the curriculum snapshot) are in GCS. §8 has the per-store
census, including the stores that are still container-disk-only on Cloud Run
and therefore open data-loss items.

Default region everywhere below: **`asia-south1` (Mumbai)** — closest to
the schools, and the only region choice that helps the DPDP Act story in
`docs/compliance.md`. (Precedent: the now-removed `fly.toml` that used to sit
at the repo root already used `primary_region = "bom"`.)

## 1. What moves where (phase 1: compute only)

| Piece today | GCP target | Notes |
|---|---|---|
| Backend on Render free tier | **Cloud Run** service `academicos-backend` | Same `Dockerfile` — `$PORT` handling and baked `academicos-data/` already work; nothing to change |
| Docker Hub image | **Artifact Registry** (`academicos/backend`) | Keeps the image private; ~3.3 GB, mostly torch/opencv + baked corpus |
| GH Actions → Docker Hub → Render | GH Actions → Artifact Registry → Cloud Run | Same three-stage shape as `.github/workflows/deploy-backend.yml`; auth via Workload Identity Federation (no stored keys) |
| Flutter web on GitHub Pages | **Firebase Hosting** (or keep Pages) | Only move it if you want the web app on the school's own domain with Google-managed SSL; Pages works fine and is free |
| Supabase Postgres + Storage | **unchanged** | Deliberately not moved in phase 1 — zero data migration, zero new failure modes. Phase 2 (§8) covers Cloud SQL + GCS |
| Secrets in Render dashboard | **Secret Manager** | Principal bootstrap key, LLM key, Cloud SQL password. The GCP deploy no longer injects the Supabase secrets (§8) |

One shared Cloud Run service can serve **all** schools — every route is
already `school_id`-scoped server-side. Per-school services buy isolation
at ~N× the bill; don't split unless a contract requires it.

## 2. One-time setup

**Now a single idempotent script** — see `docs/gcp-bootstrap.md` for the
account owner's runbook. Nothing in this section is typed by hand any more:

```bash
PROJECT_ID=… BILLING_ACCOUNT=… bash deploy/gcp/bootstrap.sh
```

That script enables the APIs, creates the Artifact Registry repo, the two
service accounts, the Secret Manager entries, Cloud SQL (with backups + PITR),
the GCS buckets, the Firebase link, and the budget alert — and establishes
Workload Identity Federation, replacing the manual "follow the console walk-
through once per repo" step this document used to require. It is idempotent,
so a half-finished run is repaired by re-running it.

## 3. Backend: deploy to Cloud Run

```bash
# build + push (or keep doing this in CI — §4)
gcloud builds submit --tag \
  asia-south1-docker.pkg.dev/PROJECT_ID/academicos/backend:v1 \
  --gcs-source-staging-dir=gs://PROJECT_ID-cloudbuild/source \
  /path/to/academicos-backend

gcloud run deploy academicos-backend \
  --image=asia-south1-docker.pkg.dev/PROJECT_ID/academicos/backend:v1 \
  --region=asia-south1 --platform=managed \
  --allow-unauthenticated \
  --port=8080 --cpu=1 --memory=1Gi \
  --concurrency=40 --timeout=300 \
  --min-instances=0 --max-instances=1 \
  --set-secrets=ACOS_PRINCIPAL_BOOTSTRAP_KEY=principal-bootstrap-key:latest \
  --set-env-vars=ACOS_GCS_BUCKET=PROJECT_ID-academicos-media
```

(CI, `.github/workflows/deploy-gcp.yml`, is the authoritative command: it also
sets the Cloud SQL socket and `ACOS_POSTGRES_*`. `--max-instances=1` is a
correctness limit until the curriculum store leaves its snapshot — §8.)

Notes (all learned the hard way on Render):

- `--concurrency=40` matches the anyio threadpool ceiling the 2026-09-15
  stress test measured (~198 rps for cheap endpoints on one worker).
  Do not raise `--max-instances` above 1 until CurriculumStore is on
  Cloud SQL (§8); a larger instance is the lever until then.
- `--timeout=300`: OCR uploads and the mobile-scan pipeline exceed Cloud
  Run's 60s default.
- `--min-instances=0` keeps you near free-tier; the 3.3 GB image
  cold-starts slowly (Render measured ~60s; Cloud Run streams layers so
  expect 20–40s). If teachers complain about first-load-of-the-day, set
  `--min-instances=1` during school hours only (~$35/mo for 1 vCPU/1 GiB)
  rather than 24/7.
- Health check path is `/health` (cheap). Do NOT point uptime checks at
  `/health/storage` more often than every few minutes — one call fans out
  to 12 upstream selects (cached 30s server-side, but still).

## 4. CI/CD: already wired

`.github/workflows/deploy-gcp.yml` implements the whole pipeline and needs no
editing — it runs on every push to `master`:

```
test      -> pytest (the gate; a red suite deploys nothing)
backend   -> Cloud Build (layer-cached) -> Artifact Registry
          -> gcloud run deploy -> poll /health until it answers
frontend  -> flutter build web --dart-define=ACADEMICOS_API=<live backend URL>
          -> firebase deploy --only hosting
```

Auth is keyless (Workload Identity Federation): GitHub's OIDC token is
exchanged for short-lived credentials, so there is no service-account key
stored in the repo. The only inputs are repo *variables* (not secrets) —
`GCP_PROJECT_ID`, `GCP_REGION`, `WIF_PROVIDER`, `DEPLOY_SA`, `GCP_SERVICE`,
`AR_IMAGE`, `GCS_MEDIA_BUCKET`, `SQL_CONNECTION`, `CORS_ORIGINS`,
`GCS_TEST_BUCKET` — and app secrets, which live in Secret Manager and are
injected via `--set-secrets`.

`GCS_TEST_BUCKET` (`vidyuthlabs-academicos-ci-test`, a scratch bucket whose
objects auto-delete after a day) is what the backend job runs
`tests/test_gcs_blob_integration.py` against before it builds anything. With
it unset the job **fails**: the curriculum snapshot's single-writer guarantee
would otherwise ship without ever having run against real GCS (§8). The only
way past is the repo variable `ALLOW_UNVERIFIED_GCS=true`, which deploys with
a warning — an emergency override, to be deleted once the bucket variable is
set.

CI does **not** apply `deploy/gcp/schema.sql`. That is a manual step, §6.

**Build identity.** The workflow passes the commit it is deploying to Cloud
Build (`_COMMIT_SHA`, `_BUILT_AT`), the Dockerfile bakes them in as
`ACOS_BUILD_COMMIT` / `ACOS_BUILT_AT`, and `GET /health` answers
`{"status": "ok", "commit": "<sha>", "builtAt": "<utc time>"}`. After the
deploy the job polls `/health` and **fails unless `commit` equals the commit
it deployed** (`deploy/gcp/check_served_commit.py`). The 2026-09-21 audit
found the Render release serving a build 4+ days older than its source,
reporting `0.1.0` and nothing else; this is the check that would have caught
it. `commit: "unknown"` means an image built outside the workflow.

**Production guard.** The deploy sets `ACOS_ENV=production`, and the service
also treats a Cloud SQL socket host (`ACOS_POSTGRES_HOST=/cloudsql/...`) as
production. There, startup fails, with one `REFUSING TO START (production
config): ...` log line per problem, if:

- `ACOS_PRINCIPAL_BOOTSTRAP_KEY` or `ACOS_POSTGRES_PASSWORD` is empty or the
  bootstrap placeholder `REPLACE_ME`;
- the principal bootstrap key is shorter than 32 characters;
- CORS allows `*`, or any origin is not `https://` (which is what an unset
  `CORS_ORIGINS` gives: the localhost dev list);
- `ACOS_DEMO_ACCOUNTS` is on (the demo principal's password is `password123`;
  demo accounts are otherwise never seeded in production);
- an LLM key is set and an LLM feature's base URL is not a host in
  `docs/compliance.md`'s LLM provider table.

A revision that fails to start never becomes ready, so the previous one keeps
serving and the `/health` commit check turns the job red. Local, dev and test
runs are never refused.

**CORS.** `CORS_ORIGINS` is the Firebase Hosting origins, comma-separated;
for vidyuthlabs: `https://vidyuthlabs.web.app,https://vidyuthlabs.firebaseapp.com`.
In production only these are answered; the `*.web.app` / `*.onrender.com`
wildcards the app accepts in development (any Firebase site, not just this
one) are switched off. Add a school's custom domain here when it is attached.

**LLM provider: explicit, and the school's decision.** One Secret Manager
entry, `acos-llm-api-key`, is injected under both names the code reads:
`SARVAM_API_KEY` (scan OCR, `assessment/vision.py`; AI marking,
`assessment/llm_evaluate.py`; curriculum extraction, `llm/sarvam.py`) and
`ACOS_LLM_API_KEY` (the doubt critic). The critic's endpoint is
`ACOS_LLM_BASE_URL` / `ACOS_LLM_MODEL`, set from the optional `LLM_BASE_URL`
/ `LLM_MODEL` repo variables; unset, it falls back to `config/config.toml`,
whose `llm_base_url` is Groq, which the production guard refuses because no
document lists Groq as a vendor. With the secret left at `REPLACE_ME` no
provider is called at all: scan capture and AI marking answer
**501 `{"code": "llm_not_enabled"}`** ("not enabled for this school") instead
of storing blank pages or a booklet of needs-review zeros.

| Env var (Cloud Run) | Set from | Read by |
|---|---|---|
| `SARVAM_API_KEY` | secret `acos-llm-api-key` | scan OCR, AI marking, curriculum extraction |
| `ACOS_LLM_API_KEY` | secret `acos-llm-api-key` | doubt critic |
| `ACOS_LLM_BASE_URL` | repo variable `LLM_BASE_URL` (optional) | doubt critic |
| `ACOS_LLM_MODEL` | repo variable `LLM_MODEL` (optional) | doubt critic |

Note the frontend job depends on the backend job: the API URL is baked into
the Dart build, so it must be compiled *after* the backend URL is known.

Keep the Render service warm for a week as instant rollback.


## 5. Frontend web: Firebase Hosting (optional move)

The workflow's frontend job does this on every deploy; by hand it is:

```bash
cd frontend
flutter build web --release \
  --dart-define=ACADEMICOS_API=https://academicos-backend-xxx.a.run.app/api/v1
rm -f build/web/assets/assets/corpus/questions.json   # offline-only asset
cd .. && firebase deploy --only hosting --project vidyuthlabs
```

Never pass `ACADEMICOS_OFFLINE` to a web build (that is the standalone
Android app). `firebase.json` at the repo root holds the Hosting config:
public dir `frontend/build/web`, single-page rewrites, and on every response
`Strict-Transport-Security`, `X-Content-Type-Options: nosniff`,
`Referrer-Policy: strict-origin-when-cross-origin`, and
`Content-Security-Policy: frame-ancestors 'none'` (plus `X-Frame-Options:
DENY` for older browsers). The CSP restricts framing only, on purpose: a
`script-src` would have to allow `'wasm-unsafe-eval'` and `blob:` for the
Flutter renderers, and getting that wrong blanks the app.

Then attach the school's domain in the Firebase console (free Google-
managed SSL). Skip this entirely if GitHub Pages is fine — the app only
cares about the `ACADEMICOS_API` value baked in at build time.

## 6. Cutover + verification (do this, in this order)

0. **Apply the Cloud SQL schema — required before the first deploy, and
   again after any change to `deploy/gcp/schema.sql`** (before the deploy
   that ships code using it):

   **First, check for duplicate emails.** A schema change that makes
   `users.email` unique (the invites work, Task 301, drops `idx_users_email`
   and creates a UNIQUE index) fails on a database that already holds two
   accounts with the same email, and the script runs under `ON_ERROR_STOP`,
   so every statement after it (the invites table included) is never
   applied. Run this first (`gcloud sql connect academicos-pg
   --user=academicos --database=academicos --project vidyuthlabs`):

   ```sql
   SELECT lower(email), count(*) FROM users GROUP BY 1 HAVING count(*) > 1;
   ```

   No rows: go ahead. Rows: do not apply the schema yet. For each email, list
   the accounts (`SELECT id, school_id, name, role, created_at FROM users
   WHERE lower(email) = '<email>';`), decide with the school which account is
   the real one, and move or delete the others (their sessions and anything
   they own first) until the query returns nothing. A new, empty database
   (vidyuthlabs' own, 2026-09-22) returns nothing.

   ```bash
   PROJECT_ID=vidyuthlabs bash scripts/apply_cloudsql_schema.sh
   ```

   Nothing else applies it: `bootstrap.sh` creates the instance, database
   and user, and the workflow only builds and deploys. An instance
   provisioned before a table was added (as `learner_models` was, 2026-09-22)
   does not have it, and every request touching it answers 503 while
   `/health` stays green. The script is idempotent (every statement is
   `IF NOT EXISTS`), stops on the first SQL error, and reads the password
   from the `postgres-password` secret. Run it from Cloud Shell.
1. Deploy backend to Cloud Run; leave Render untouched.
2. `curl https://<run-url>/health` → `{"status":"ok","commit":"<the sha you
   pushed>","builtAt":"..."}`. CI checks the commit itself; a different one
   means the new revision did not start: read its logs for `REFUSING TO
   START`.
3. `curl https://<run-url>/health/storage` → `"status": "ok"`,
   `durability_backend` set, `durability_reachable: true`, every table
   `"ok"`. `"status": "schema_missing"` lists the absent tables in
   `missing_tables` (and `table_exists` per table) and names the fix: on
   Cloud SQL, step 0's script; on Supabase, `docs/supabase-setup.sql` (it creates `users`, `sessions` and `invites`).
   `"unreachable"` is an outage, not a schema problem. The probe caches for
   30 s, so allow that long after a fix. `blob_backend` must read `"gcs"`;
   `"local"` means `ACOS_GCS_BUCKET` is missing and scan photos/PDFs and the
   curriculum snapshot are going to container disk, which Cloud Run discards.
   `blob_status` must show `curriculum_snapshot_conflict: false` and zero
   `*_upload_failures`; check it again after every rollout (below).
4. Rebuild the web app with the new `ACADEMICOS_API` and deploy it.
5. End-to-end, against the Cloud Run URL:
   - register the school's first principal (`schoolId` + the bootstrap
     key) → that principal `POST /auth/invites` → register a teacher with
     the invite code alone → login → `GET /assessments` returns 200 (not
     401). Registration without an invite or key is a 403 since 2026-09-21;
   - bad-password login → friendly error, no session wipe;
   - tampered token → 401 and the app routes back to Sign in.
   (`frontend/test/live_backend_auth_test.dart` drives exactly this flow;
   point its `liveBase` at the new URL for a scripted pass.)
6. Watch Cloud Run metrics + logs for one school day, then decommission
   Render (or keep it a week as rollback).

## 7. What it costs (one school, asia-south1 list prices, approximate)

| Setup | Rough burn | $50k runway |
|---|---|---|
| Lean: scale-to-zero, Supabase free tier, Pages/Firebase free tiers | **$2–15/mo** | centuries |
| Comfortable: school-hours min-instance, Cloud SQL small, GCS | **$40–80/mo** | 50–100 years |
| 10 schools, shared service, comfortable | **$60–120/mo** total | decades |

Assumes ~500–1,000 users and 50–300k backend requests/school/month.
Free tiers do the heavy lifting (Cloud Run: 2M req/mo; Cloud Build:
120 min/day; Firebase Hosting: 10 GB + 360 MB/day transfer). Credits
are not the constraint — engineering time is.

## 8. Phase 2: Cloud SQL + GCS (structured data and blobs moved; two stores still on container disk)

Structured data is now first-class on GCP — this is no longer a future
project:

- **Cloud SQL Postgres** in `asia-south1` is provisioned by the bootstrap
  (daily backups, PITR), `deploy/gcp/schema.sql` defines all 12 tables
  (applied by `scripts/apply_cloudsql_schema.sh`, §6 step 0 — never by CI;
  `/health/storage` names any that are missing), and
  `src/academicos/assessment/postgres_kv.py` implements the Cloud SQL backend
  behind the same interface the stores already used. Every JSONB store,
  `KnowledgeStore` included (`learner_models`, since 2026-09-22), calls
  `durable_table(...)`, which prefers Cloud SQL whenever `ACOS_POSTGRES_*` is
  set and otherwise falls back to Supabase — so the cutover is an env-var
  change, and the reverse is too.
- **Migration** is `scripts/migrate_supabase_to_cloudsql.py` (paged, so it does
  not silently stop at PostgREST's 1000-row cap; idempotent on re-run). It
  copies `learner_models` too. **Run it (at least `--only learner_models`)
  before the first deploy without the Supabase secrets**: until that deploy
  the GCP service read and wrote students' mastery history in Supabase, and
  once the secrets are gone those rows are invisible to it. Forgetting is no
  longer silent: on Cloud SQL an empty `learner_models` table answers **503**
  on every mastery read and write (`LearnerModelsNotMigrated`, naming the
  command) instead of treating every student as a brand-new learner. A new
  school with no history sets the `FRESH_INSTALL` repo variable to `1` for
  its first deploy (the workflow then passes
  `ACOS_LEARNER_MODELS_ALLOW_EMPTY=1`), then deletes the variable.
- **Blob migration** is `scripts/migrate_supabase_blobs_to_gcs.py`: it copies
  the curriculum snapshot and every scan-media object from Supabase Storage
  into the service's bucket, reads each one back and compares bytes, and
  never overwrites a snapshot GCS already holds (a service that has booted
  may have edits there). Run it before the first GCS-backed deploy. Without
  it the service does not come up empty: on GCS, "no snapshot" refuses to
  boot unless `ACOS_CURRICULUM_ALLOW_EMPTY_BOOT=1` (set by `FRESH_INSTALL=1`),
  because a migrated service and a genuinely new school look identical.

- **Blob storage** goes through one factory, `storage/blobs.py`'s
  `durable_blob_store(name)`, mirroring `durable_table`: GCS when
  `ACOS_GCS_BUCKET` is set, else Supabase Storage when its credentials are
  set, else local disk only. Objects land at
  `gs://<bucket>/academicos/scan-media/...` and
  `gs://<bucket>/academicos/curriculum-snapshots/curriculum.sqlite`.
  `/health/storage` reports `blob_backend` (`gcs`/`supabase`/`local`) next to
  `durability_backend`. Only the env var selects GCS — `config.toml`'s
  `gcs_bucket` is the CLI corpus-sync dev bucket and is ignored here.
- **The Supabase secrets are no longer injected** into the GCP service. That
  is safe only because nothing on GCP still depended on them: the last store
  that did, `KnowledgeStore`, moved to `durable_table("learner_models")` in
  the same change. Removing the secrets first would have sent every
  student's mastery history to container disk, wiped on each redeploy.

### The curriculum snapshot has exactly one writer

`CurriculumStore` keeps 18 FK-linked tables in a local SQLite file and
persists the whole file as one object. The mechanism is
`storage/snapshot_sync.py`'s `SnapshotSync`: the store constructs it and
routes every commit through it, nothing more (tests:
`tests/test_snapshot_sync.py`). Exact behaviour:

- **Boot.** If the local file does not exist, it downloads the snapshot and
  writes it to disk before opening. "No snapshot yet" (`BlobNotFound`, or
  Supabase's 404 / 400-not_found) starts a fresh database — on GCS only with
  `ACOS_CURRICULUM_ALLOW_EMPTY_BOOT=1`; without it boot fails and names
  `scripts/migrate_supabase_blobs_to_gcs.py`. Any other failure —
  GCS unreachable, a timeout, a 5xx — raises `CurriculumNotDurable` and leaves
  no local file, so app startup fails and Cloud Run retries the container
  instead of serving an empty curriculum as if it were the real one.
- **Upload.** A commit that changed rows marks the snapshot pending. Uploads
  are debounced to one per 30 s, but the debounce only delays: a commit
  inside the window arms one trailing timer for the end of it, a failed
  upload re-arms it (and counts in `blob_status`), and the app's shutdown hook
  (`api/main.py` `_shutdown`, run by uvicorn on Cloud Run's SIGTERM, inside
  the 10 s grace) uploads whatever is still pending. Each upload checkpoints
  the WAL and sends the whole file. A commit that changed nothing (schema
  no-ops at boot) does not upload, so a freshly restored instance does not
  bump the generation under an instance it is overlapping with.

Two instances would each upload their own copy and each would replace the
other's wholesale. `--max-instances=1` does not rule that out: it is per
revision, so every rollout runs the old and new revision side by side for a
while, and Cloud Run can briefly exceed it. Three guards:

1. `deploy-gcp.yml` sets `--max-instances=1`. Lift it only when
   `CurriculumStore` moves to Cloud SQL.
2. The GCS snapshot write carries a generation precondition
   (`if_generation_match`). The store remembers the generation it restored
   or last wrote (0 — "must not exist" — if it never saw the object), so a
   snapshot another instance wrote in between fails with HTTP 412 and is
   refused, logged at ERROR (`REFUSED to overwrite ...`), instead of erased.
   A 412 whose object md5 equals the bytes just sent is this instance's own
   retried upload (the client retries conditional writes; a lost response
   makes the retry 412) and is adopted, not treated as a conflict.
3. After a refusal the instance neither destroys its edits nor stays
   stuck. It first uploads its own whole losing file to
   `curriculum-snapshots/conflicts/<utc>-<revision>-<rand>.sqlite`; only
   after that upload succeeds does it reload the newer snapshot into its
   live connection (which also refreshes its generation). An edit that hit
   the conflict on the request path answers **503** ("not saved, retry").
   `/health/storage` → `blob_status` shows `curriculum_snapshot_conflict:
   true` with a count and time, plus `curriculum_snapshot_conflict_copies`
   and `curriculum_snapshot_last_conflict_copy` (the key). If the copy
   cannot be uploaded, nothing is reloaded: the edits stay in the local
   file and every later curriculum write answers 503 until an operator
   recovers it. A failed reload does the same.

Remaining limit, stated exactly: commits deferred by the 30 s debounce have
already answered 200. When one of them loses a conflict on the timer or the
shutdown flush — typically on the old revision during a rollout — it is not
destroyed, but it leaves the live view: it exists only in the conflict copy
until someone merges it. So after each rollout check
`curriculum_snapshot_conflict_copies` on `/health/storage`; non-zero means
download that object (`gsutil cp gs://<bucket>/academicos/curriculum-snapshots/<key> .`),
compare it with the live snapshot in `sqlite3`, and re-enter or copy the
missing rows. The real fix is moving `CurriculumStore` to Cloud SQL.

### Store census: where each store's data lives on GCP

Every `sqlite3.connect` under `src/academicos`, plus the one JSON-file store.
"Container disk" on Cloud Run means lost on every redeploy and scale-to-zero.

| Store (file) | Holds | On GCP |
|---|---|---|
| `AssessmentStore` (`assessment/store.py`) | assessments | Cloud SQL `assessments` |
| `PaperStore` (`assessment/paper_store.py`) | generated papers | Cloud SQL `papers` |
| `PracticeStore` (`assessment/practice_store.py`) | practice sets | Cloud SQL `practice_sets` |
| `GradedStore` (`assessment/graded_store.py`) | student marks | Cloud SQL `graded_evaluations` |
| `ScanSessionStore` (`assessment/scan_session_store.py`) | scan sessions | Cloud SQL `scan_sessions`; photos/PDFs in GCS `scan-media/` |
| `TemplateStore` (`assessment/school_templates.py`) | school paper templates | Cloud SQL `school_templates` |
| `UserStore` (`assessment/users.py`) | users, sessions | Cloud SQL `users`, `sessions` |
| `AuditLog` (`assessment/audit_log.py`) | audit trail | Cloud SQL `audit_log` |
| `EventStore` (`storage/event_store.py`) | learner events | Cloud SQL `learner_events` |
| `ConsentStore` (`assessment/consent.py`) | parental consent (DPDP) | Cloud SQL `parental_consents` (in the `/health/storage` probe since 2026-09-22) |
| `CurriculumStore` (`curriculum/store.py`) | calendars, sequences, timetable, enrolments | container SQLite + GCS snapshot, one instance (above) |
| `KnowledgeStore` (`assessment/knowledge.py`) | per-student mastery history | Cloud SQL `learner_models` (moved to `durable_table` 2026-09-22; copy the existing Supabase rows with the migration script — an empty table answers 503 until then) |
| `SourceRegistry` + `LocalStore` via `assessment/ingest_routes.py` | a school's own uploaded papers/marking schemes | **container disk only — OPEN.** The file store could become `GcsStore`, but the registry row is local SQLite too, so both need moving together |
| `ApiKeyStore` (`assessment/api_keys.py`) | partner API keys (hashed) and quota counters | **container disk only — OPEN.** Not student data, but a redeploy revokes every issued key |
| `AnswerKeyStore` (`assessment/answer_key.py`) | CBSE marking schemes | baked into the image (corpus content, not school data) |
| `GraphStore`, `ChunkIndex`, `SourceRegistry` for the corpus (`graph/store.py`, `retrieval/index.py`, `storage/registry.py`) | CBSE/NCERT knowledge graph and index | baked into the image; rebuilt by the pipeline, not written by schools |
| question-bank reads (`assessment/question_bank.py`, `assessment/pool.py`) | question corpus | read-only |
| `QuestionBankStore` (`assessment/qbank_store.py`) | item versions/review states | not constructed by the API |
| embedding cache (`assessment/embedding_chapter_tagger.py`) | chapter-tag embeddings | container disk; derived, safe to lose |

Migration order for a school already running on Supabase: (1)
`scripts/migrate_supabase_to_cloudsql.py` — the twelve JSONB tables,
`learner_models` included; (2) `scripts/migrate_supabase_blobs_to_gcs.py` —
the curriculum snapshot and prior scan media (the factory picks one backend,
so scan media left in Supabase are unreadable from GCS); (3) deploy. Both
steps have a guard that fails loudly if skipped (503 on mastery history,
refused curriculum boot); neither can tell a skipped migration from a new
school, which is what `FRESH_INSTALL=1` is for.

Scan-media uploads stay best-effort for the teacher — a failed upload does not
fail the scan — but on GCP that artifact is then on container disk only. Every
such failure is counted in `/health/storage` → `blob_status`
(`scan_media_upload_failures`, `scan_media_upload_failure_at`); a non-zero
count means artifacts that will be gone at the next redeploy.

**Unverified until it has run once:** every GCS generation, precondition,
412-retry and md5 path has been tested only against an in-memory fake
(`tests/test_blob_factory.py`) written to the same assumptions as the code.
`tests/test_gcs_blob_integration.py` checks those assumptions against a real
bucket: create, stale overwrite and a real 412, md5 format, the self-412 on a
retried upload being adopted, the generation-pinned download, and a
conflict-copy key. It is skipped unless `ACOS_GCS_TEST_BUCKET` names a
scratch bucket. `deploy-gcp.yml` runs it before every deploy against the
`GCS_TEST_BUCKET` repo variable and fails on a skip or on zero passes. With
the variable unset the deploy **fails** unless `ALLOW_UNVERIFIED_GCS=true`
is set (§4); it no longer ships on a warning. Likewise the KnowledgeStore JSONB round trip against real
Postgres (`tests/test_postgres_kv.py`) runs only where `ACOS_TEST_PG_*` is set
— the CI `test` job, which gates every deploy.

Still open:
- Connection sizing: Cloud Run runs at `--concurrency=40`, so the adapter
  bounds its pool (`ACOS_POSTGRES_POOL_MAX`, default 10). Raise the Cloud SQL
  tier before raising that — a `db-f1-micro` tops out well below 40 backends.
- Private IP via a Serverless VPC Connector (~$7–10/mo) if the public IP path
  is not acceptable for the DPDP posture.

## 9. Don't-burn-credits checklist

- No Load Balancer for one service (Cloud Run's `*.run.app` URL or
  Firebase rewrites; an LB alone is ~$18/mo before traffic).
- No Cloud SQL until Supabase limits actually bite.
- `--max-instances` is pinned to 1 for correctness (§8), which also caps
  billing. Raise the instance size, not the count, until the curriculum
  store is on Cloud SQL.
- Set a budget alert at $25/50/100 on the billing account on day one.
- Artifact Registry: keep 2–3 image versions, the 3.3 GB image at
  ~$0.10/GB/mo adds up across dozens of retained tags.
