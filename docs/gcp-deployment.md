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
Federation so that no service-account key exists anywhere. The one piece still
running on Supabase is blob storage — see §8, which is the blocking item before
"pure GCP" is literally true.

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
| Secrets in Render dashboard | **Secret Manager** | `SUPABASE_KNOWLEDGE_URL`, `SUPABASE_KNOWLEDGE_ANON_KEY`, principal bootstrap key |

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
  --min-instances=0 --max-instances=3 \
  --set-secrets=SUPABASE_KNOWLEDGE_URL=supabase-url:latest,SUPABASE_KNOWLEDGE_ANON_KEY=supabase-anon-key:latest \
  --set-env-vars=ACOS_PRINCIPAL_BOOTSTRAP_KEY_SECRET=principal-bootstrap-key
```

Notes (all learned the hard way on Render):

- `--concurrency=40` matches the anyio threadpool ceiling the 2026-09-15
  stress test measured (~198 rps for cheap endpoints on one worker).
  Raise `--max-instances` before raising concurrency.
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
   `users`/`sessions`/`invites` error, run `docs/supabase-setup.sql` first — same
   prerequisite as on Render. On Cloud SQL, apply
   `deploy/gcp/schema.sql` first.
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

## 8. Phase 2: Cloud SQL + GCS (structured data DONE; blob storage open)

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

Still open:

- **Blob storage** (scan-media photos/PDFs in `mobile_scan.py`, curriculum
  snapshots in `curriculum/store.py`) still goes through `SupabaseStorage`.
  `GcsStore` exists in `src/academicos/storage/gcs.py` and the `gcs` extra is
  installed in the image, but each call site needs its bucket wired. Until
  that is done, do **not** remove the Supabase secrets — the JSONB tables would
  move but blob writes would fall back to container-local disk and be lost on
  the next redeploy.
- Connection sizing: Cloud Run runs at `--concurrency=40`, so the adapter
  bounds its pool (`ACOS_POSTGRES_POOL_MAX`, default 10). Raise the Cloud SQL
  tier before raising that — a `db-f1-micro` tops out well below 40 backends.
- Private IP via a Serverless VPC Connector (~$7–10/mo) if the public IP path
  is not acceptable for the DPDP posture.

## 9. Don't-burn-credits checklist

- No Load Balancer for one service (Cloud Run's `*.run.app` URL or
  Firebase rewrites; an LB alone is ~$18/mo before traffic).
- No Cloud SQL until Supabase limits actually bite.
- Cap `--max-instances` (3 is plenty per school; autoscale covers exam
  week, the cap covers billing surprises).
- Set a budget alert at $25/50/100 on the billing account on day one.
- Artifact Registry: keep 2–3 image versions, the 3.3 GB image at
  ~$0.10/GB/mo adds up across dozens of retained tags.
