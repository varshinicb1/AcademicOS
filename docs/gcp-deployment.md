# GCP deployment guide — AcademicOS on Google Cloud

Target reader: whoever moves the live service off Render. Assumes a GCP
project with billing enabled (the $50k credit pool covers years of this —
see §7) and owner access to the three GitHub repos (`AcademicOS`,
`academicos-backend`, `academicos-frontend-src`).

Default region everywhere below: **`asia-south1` (Mumbai)** — closest to
the schools, and the only region choice that helps the DPDP Act story in
`docs/compliance.md`. (Precedent: the stale `fly.toml` at the repo root
already used `primary_region = "bom"`.)

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

```bash
gcloud auth login
gcloud config set project PROJECT_ID
gcloud services enable run.googleapis.com artifactregistry.googleapis.com \
  cloudbuild.googleapis.com secretmanager.googleapis.com

gcloud artifacts repositories create academicos \
  --repository-format=docker --location=asia-south1

# secrets (values never touch git)
printf '%s' "$SUPABASE_URL" | gcloud secrets create supabase-url --data-file=-
printf '%s' "$SUPABASE_ANON_KEY" | gcloud secrets create supabase-anon-key --data-file=-
printf '%s' "$BOOTSTRAP_KEY" | gcloud secrets create principal-bootstrap-key --data-file=-
```

Workload Identity Federation (keyless deploys from GitHub Actions) —
do once per repo following
<https://cloud.google.com/iam/docs/workload-identity-federation-with-deployment-pipelines>,
granting the pool's service account `roles/run.admin`,
`roles/artifactregistry.writer`, and `roles/secretmanager.secretAccessor`.

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

## 4. CI/CD: retarget the existing pipeline

Mirror `.github/workflows/deploy-backend.yml`'s test → sync → deploy
shape. In the `academicos-backend` repo's build workflow, replace the
Docker Hub push + Render hook with:

```yaml
- uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: projects/123456789/locations/global/workloadIdentityPools/gh-pool/providers/gh-provider
    service_account: deploy@PROJECT_ID.iam.gserviceaccount.com
- uses: google-github-actions/setup-gcloud@v2
- run: |-
    gcloud builds submit --tag asia-south1-docker.pkg.dev/PROJECT_ID/academicos/backend:${{ github.sha }} .
    gcloud run deploy academicos-backend \
      --image=asia-south1-docker.pkg.dev/PROJECT_ID/academicos/backend:${{ github.sha }} \
      --region=asia-south1
```

Keep the pytest gate in `AcademicOS` exactly as-is — it already caught
real regressions pre-deploy twice. Keep the Render service warm for a
week as instant rollback.

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
3. `curl https://<run-url>/health/storage` → every table `"ok"`,
   `supabase_reachable: true`. If `users`/`sessions` still error, run
   `docs/supabase-setup.sql` first — same prerequisite as on Render.
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

## 8. Phase 2 (optional, +1–2 weeks): Cloud SQL + GCS

Move only for DPDP data residency or because Supabase free-tier limits
(500 MB DB, 1 GB storage) start to bite:

- Cloud SQL for PostgreSQL in asia-south1 (`db-g1-small`, ~$25–35/mo
  all-in): `pg_dump` from Supabase → restore; point the same
  `SUPABASE_KNOWLEDGE_URL`-style env vars at it (the wrapper speaks
  plain PostgREST-shaped REST... no — Cloud SQL is raw Postgres, so this
  needs either PostgREST deployed in front of it or a store-layer
  adapter; size that work honestly before promising it).
- GCS buckets for scan media + curriculum snapshots: `GcsStore` already
  exists in `src/academicos/storage/gcs.py`; each store needs its bucket
  wired where `SupabaseStorage` is used today.
- Private IP for Cloud SQL via a Serverless VPC Connector (~$7–10/mo),
  or public IP + authorized networks + SSL for the lean start.

## 9. Don't-burn-credits checklist

- No Load Balancer for one service (Cloud Run's `*.run.app` URL or
  Firebase rewrites; an LB alone is ~$18/mo before traffic).
- No Cloud SQL until Supabase limits actually bite.
- Cap `--max-instances` (3 is plenty per school; autoscale covers exam
  week, the cap covers billing surprises).
- Set a budget alert at $25/50/100 on the billing account on day one.
- Artifact Registry: keep 2–3 image versions, the 3.3 GB image at
  ~$0.10/GB/mo adds up across dozens of retained tags.
