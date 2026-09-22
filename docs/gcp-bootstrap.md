# GCP bootstrap — the account owner's one-time job

> **Scope.** This stands up the **GCP release only**. It does not touch the live
> **Render release**, and it does not build either client sub-product. See
> [`PRODUCTS_AND_RELEASES.md`](PRODUCTS_AND_RELEASES.md) for the full map.

This is the **only** thing the GCP account owner does. After it, every deploy of
the GCP release happens automatically from GitHub on push to `master`, and the
owner is never needed again.

Budget 15 minutes, most of it waiting on Cloud SQL to provision.

## What the owner runs

Open [Cloud Shell](https://console.cloud.google.com/) (it is pre-authenticated
as the account, and already has `gcloud`, `firebase` and `openssl`), then:

```bash
git clone https://github.com/varshinicb1/AcademicOS.git
cd AcademicOS

PROJECT_ID=your-project-id \
BILLING_ACCOUNT=01ABCD-234567-89EFGH \
bash deploy/gcp/bootstrap.sh
```

`BILLING_ACCOUNT` is optional but recommended — it turns on the spend alert
(50/90/100% of $100). Find it with:

```bash
gcloud billing accounts list
```

Anything else can be overridden; all have defaults:

| Variable | Default | Notes |
|---|---|---|
| `REGION` | `asia-south1` | Mumbai — closest to the schools, and the DPDP story |
| `GITHUB_REPO` | `varshinicb1/AcademicOS` | The **only** repo trusted to deploy |
| `SQL_TIER` | `db-custom-1-3840` | Dedicated core. `db-g1-small` is cheaper but shared-core (trial only; set `SQL_PITR=0` with it). The instance is created with `--edition=ENTERPRISE`: new Postgres instances otherwise default to Enterprise Plus, which rejects every shared-core tier (`Invalid Tier (db-g1-small) for (ENTERPRISE_PLUS) Edition`, 2026-09-22) |
| `SKIP_SQL` / `SKIP_FIREBASE` | `0` | Set to `1` to skip that piece |

The script is **idempotent**. If it fails halfway (a quota, a transient API
error), fix the cause and run it again — it picks up where it left off rather
than erroring on "already exists". Re-running never destroys anything.

## What it creates

- APIs: Run, Artifact Registry, Cloud Build, Secret Manager, Cloud SQL, IAM
  Credentials, Storage, Billing Budgets
- Artifact Registry repo `academicos`
- Service accounts `academicos-deploy` (GitHub Actions) and
  `academicos-runtime` (what the running service is, least privilege)
- **Workload Identity Federation** pool/provider trusting an OIDC token from
  `GITHUB_REPO` only — this is what lets GitHub deploy without any stored key,
  and therefore without anything for anyone to leak or rotate
- Secret Manager entries (placeholders) for the app's secrets
- Cloud SQL Postgres 16 with daily backups + point-in-time recovery
- GCS buckets for scan media, backups, and Cloud Build staging
- Firebase Hosting project link
- A budget alert

## What the owner does *not* do

No service-account JSON keys. No secrets in GitHub. No Docker Hub. No manual
redeploys, ever.

## What the team does once, after the bootstrap

1. **Set the repo variables** (the bootstrap prints these ready to paste):

   ```bash
   gh variable set GCP_PROJECT_ID   --body "your-project-id"
   gh variable set GCP_REGION       --body "asia-south1"
   gh variable set WIF_PROVIDER     --body "projects/…/providers/github"
   gh variable set DEPLOY_SA        --body "academicos-deploy@….iam.gserviceaccount.com"
   gh variable set RUNTIME_SA       --body "academicos-runtime@….iam.gserviceaccount.com"
   gh variable set GCP_SERVICE      --body "academicos-backend"
   gh variable set AR_IMAGE         --body "asia-south1-docker.pkg.dev/…/academicos/backend"
   gh variable set GCS_MEDIA_BUCKET --body "your-project-id-academicos-media"
   gh variable set SQL_CONNECTION   --body "your-project-id:asia-south1:academicos-pg"
   gh variable set CORS_ORIGINS     --body "https://your-project-id.web.app,https://your-project-id.firebaseapp.com"
   ```

2. **Paste the real secret values** (never into git):

   ```bash
   printf '%s' 'https://<proj>.supabase.co' | gcloud secrets versions add supabase-url --data-file=-
   printf '%s' '<anon-key>'                 | gcloud secrets versions add supabase-anon-key --data-file=-
   openssl rand -hex 32 | tr -d '\n'       | gcloud secrets versions add principal-bootstrap-key --data-file=-
   printf '%s' '<sarvam-api-key>'           | gcloud secrets versions add acos-llm-api-key --data-file=-
   ```

   The service **refuses to start** (`ACOS_ENV=production`, see
   `docs/gcp-deployment.md` §4) while `principal-bootstrap-key` or
   `postgres-password` is still `REPLACE_ME` or empty, or the bootstrap key
   is under 32 characters. `acos-llm-api-key` may stay `REPLACE_ME`: that is
   a school without AI features, which answer "not enabled for this school".

3. **Apply the database schema** (and again after any change to
   `deploy/gcp/schema.sql` — CI never applies it; see
   `docs/gcp-deployment.md` §6 step 0):

   ```bash
   PROJECT_ID=vidyuthlabs bash scripts/apply_cloudsql_schema.sh
   ```

4. Push to `master`. `.github/workflows/deploy-gcp.yml` tests, builds, and
   deploys. Watch it in the repo's Actions tab.

## How deploys work after this

```
push to master
   └─ test      pytest (the gate — ~2.5 min, 1163+ cases)
   └─ backend   GitHub OIDC → deploy SA → Cloud Build → Artifact Registry
                → gcloud run deploy → poll /health
   └─ frontend  Flutter web build (API URL baked in) → Firebase Hosting
```

Failure modes are honest: if the pytest gate fails, nothing deploys; if the
service deploys but `/health` never answers, the workflow goes red instead of
declaring success.

## Moving data off Supabase (when ready)

The service keeps using Supabase until you tell it otherwise — Cloud SQL sits
idle and harmless. To cut over:

```bash
python scripts/migrate_supabase_to_cloudsql.py --dry-run   # report only
python scripts/migrate_supabase_to_cloudsql.py             # do it
```

Then verify `GET <service-url>/health/storage` reports
`"durability_backend": "cloudsql"` and every table `"ok"`, and only then remove
the `SUPABASE_*` secrets from the Cloud Run service. Reverting is symmetric:
put them back and the stores prefer Cloud SQL only while `ACOS_POSTGRES_*`
is set.

## Cost

Cloud Run scales to zero. The only always-on cost is the Cloud SQL instance
(~$10–15/mo at `db-f1-micro`). To stop all spend, delete that instance:

```bash
gcloud sql instances delete academicos-pg
```

## Rollback

Nothing here touches Render. The previous deployment stays live and is the
instant rollback path until you choose to decommission it.
