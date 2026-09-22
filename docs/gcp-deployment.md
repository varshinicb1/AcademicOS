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
GCP-native: Cloud Run for compute, Cloud SQL for the eleven durable tables, GCS
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
  to 10 upstream selects (cached 30s server-side, but still).

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
`AR_IMAGE`, `GCS_MEDIA_BUCKET`, `SQL_CONNECTION`, `CORS_ORIGINS` — and app
secrets, which live in Secret Manager and are injected via `--set-secrets`.

Note the frontend job depends on the backend job: the API URL is baked into
the Dart build, so it must be compiled *after* the backend URL is known.

Keep the Render service warm for a week as instant rollback.


## 5. Frontend web: Firebase Hosting (optional move)

```bash
cd frontend
flutter build web --release \
  --dart-define=ACADEMICOS_API=https://academicos-backend-xxx.a.run.app/api/v1
firebase init hosting   # public dir: build/web, single-page rewrites on
firebase deploy --only hosting
```

Then attach the school's domain in the Firebase console (free Google-
managed SSL). Skip this entirely if GitHub Pages is fine — the app only
cares about the `ACADEMICOS_API` value baked in at build time.

## 6. Cutover + verification (do this, in this order)

1. Deploy backend to Cloud Run; leave Render untouched.
2. `curl https://<run-url>/health` → `{"status":"ok"}`.
3. `curl https://<run-url>/health/storage` → `durability_backend` set,
   `durability_reachable: true`, every table `"ok"`. On Supabase, if
   `users`/`sessions` error, run `docs/supabase-setup.sql` first — same
   prerequisite as on Render. On Cloud SQL, apply
   `deploy/gcp/schema.sql` first. `blob_backend` must read `"gcs"`;
   `"local"` means `ACOS_GCS_BUCKET` is missing and scan photos/PDFs and the
   curriculum snapshot are going to container disk, which Cloud Run discards.
4. Rebuild the web app with the new `ACADEMICOS_API` and deploy it.
5. End-to-end, against the Cloud Run URL:
   - register → login → `GET /assessments` returns 200 (not 401);
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

## 8. Phase 2: Cloud SQL + GCS (structured data and blobs DONE; three stores open)

Structured data is now first-class on GCP — this is no longer a future
project:

- **Cloud SQL Postgres** in `asia-south1` is provisioned by the bootstrap
  (daily backups, PITR), `deploy/gcp/schema.sql` defines all 11 tables, and
  `src/academicos/assessment/postgres_kv.py` implements the Cloud SQL backend
  behind the same interface the stores already used. All 11 stores now call
  `durable_table(...)`, which prefers Cloud SQL whenever `ACOS_POSTGRES_*` is
  set and otherwise falls back to Supabase — so the cutover is an env-var
  change, and the reverse is too.
- **Migration** is `scripts/migrate_supabase_to_cloudsql.py` (paged, so it does
  not silently stop at PostgREST's 1000-row cap; idempotent on re-run).

- **Blob storage** goes through one factory, `storage/blobs.py`'s
  `durable_blob_store(name)`, mirroring `durable_table`: GCS when
  `ACOS_GCS_BUCKET` is set, else Supabase Storage when its credentials are
  set, else local disk only. Objects land at
  `gs://<bucket>/academicos/scan-media/...` and
  `gs://<bucket>/academicos/curriculum-snapshots/curriculum.sqlite`.
  `/health/storage` reports `blob_backend` (`gcs`/`supabase`/`local`) next to
  `durability_backend`. Only the env var selects GCS — `config.toml`'s
  `gcs_bucket` is the CLI corpus-sync dev bucket and is ignored here.
- **The Supabase secrets are no longer injected** into the GCP service.

### The curriculum snapshot has exactly one writer

`CurriculumStore` keeps 18 FK-linked tables in a local SQLite file and
persists the whole file as one object. Exact behaviour: on boot, if the local
file does not exist, it downloads the snapshot and writes it to disk before
opening; after every commit it checkpoints the WAL and uploads the whole file,
debounced to once per 30 s (a commit inside the window is not uploaded until
a later commit falls outside it). Two instances would each upload their own
copy and each would replace the other's wholesale. Two guards:

1. `deploy-gcp.yml` sets `--max-instances=1`. Lift it only when
   `CurriculumStore` moves to Cloud SQL.
2. The GCS snapshot write carries a generation precondition
   (`if_generation_match`). The store remembers the generation it restored
   or last wrote (0 — "must not exist" — if it never saw the object), so a
   snapshot another instance wrote in between fails with HTTP 412. The
   upload is refused and logged at ERROR (`REFUSED to overwrite ...`) instead
   of erasing the newer snapshot. The request still succeeds; that
   instance's later curriculum writes stay on its local disk only until it
   restarts and restores the newer snapshot. A refusal in the logs therefore
   means two instances ran at once — during a revision rollout Cloud Run can
   briefly run the old and the new revision together, so check for it after
   every deploy that happened while an admin was editing the calendar.

Remaining limit even with one instance: the last commits inside the 30 s
debounce window are not uploaded until a later commit, so an instance killed
right after an edit can lose that edit.

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
| `ConsentStore` (`assessment/consent.py`) | parental consent (DPDP) | Cloud SQL `parental_consents` (not yet in the `/health/storage` probe list) |
| `CurriculumStore` (`curriculum/store.py`) | calendars, sequences, timetable, enrolments | container SQLite + GCS snapshot, one instance (above) |
| `KnowledgeStore` (`assessment/knowledge.py`, JSON files) | per-student mastery history | **container disk only — OPEN.** It talks to Supabase's `learner_models` over raw REST and has no Cloud SQL table; with the Supabase secrets gone it writes local JSON. Fix: a `learner_models` table in `deploy/gcp/schema.sql` and `durable_table("learner_models")` in the store (not a constructor swap) |
| `SourceRegistry` + `LocalStore` via `assessment/ingest_routes.py` | a school's own uploaded papers/marking schemes | **container disk only — OPEN.** The file store could become `GcsStore`, but the registry row is local SQLite too, so both need moving together |
| `ApiKeyStore` (`assessment/api_keys.py`) | partner API keys (hashed) and quota counters | **container disk only — OPEN.** Not student data, but a redeploy revokes every issued key |
| `AnswerKeyStore` (`assessment/answer_key.py`) | CBSE marking schemes | baked into the image (corpus content, not school data) |
| `GraphStore`, `ChunkIndex`, `SourceRegistry` for the corpus (`graph/store.py`, `retrieval/index.py`, `storage/registry.py`) | CBSE/NCERT knowledge graph and index | baked into the image; rebuilt by the pipeline, not written by schools |
| question-bank reads (`assessment/question_bank.py`, `assessment/pool.py`) | question corpus | read-only |
| `QuestionBankStore` (`assessment/qbank_store.py`) | item versions/review states | not constructed by the API |
| embedding cache (`assessment/embedding_chapter_tagger.py`) | chapter-tag embeddings | container disk; derived, safe to lose |

Data already in Supabase (prior scan media, the current curriculum snapshot,
`learner_models`) is not copied by `scripts/migrate_supabase_to_cloudsql.py`,
which moves the eleven JSONB tables only.

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
