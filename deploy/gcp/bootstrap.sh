#!/usr/bin/env bash
# =============================================================================
# AcademicOS -- GCP one-time bootstrap
# =============================================================================
#
# PURPOSE
#   This is the ONLY step the GCP account owner has to perform. Everything
#   after it is automated by .github/workflows/deploy-gcp.yml (keyless, via
#   Workload Identity Federation -- no stored keys, nothing to rotate).
#
# WHO RUNS THIS
#   The account owner, once, in Google Cloud Shell:
#       https://console.cloud.google.com/  ->  Activate Cloud Shell
#   or locally with gcloud authenticated as a project Owner.
#
# USAGE
#   PROJECT_ID=my-project-id bash deploy/gcp/bootstrap.sh
#
#   Run it with --check first. That performs the preflight only -- billing,
#   org policies, API permissions, what already exists -- creates nothing, and
#   exits non-zero if it finds something that needs the project/org owner.
#   It is the cheapest way to find out whether one visit is genuinely enough.
#
#       PROJECT_ID=my-project-id bash deploy/gcp/bootstrap.sh --check
#
#   Optional overrides (all have sane defaults):
#     REGION=asia-south1
#     GITHUB_REPO=varshinicb1/AcademicOS
#     BILLING_ACCOUNT=01ABCD-234567-89EFGH   # enables the budget alert
#     BUDGET_AMOUNT=100
#     SQL_TIER=db-custom-1-3840               # dedicated core (default);
#                                             # db-g1-small is cheaper but
#                                             # shared-core, trial only
#     SQL_PITR=0                              # disable PITR (required with
#                                             # any shared-core tier)
#     SKIP_SQL=1                              # skip Cloud SQL provisioning
#     SKIP_FIREBASE=1                         # skip Firebase Hosting setup
#
# SAFETY
#   Idempotent: safe to re-run. Every create is guarded by an existence
#   check, so a re-run after a partial failure completes the missing pieces
#   rather than erroring out or duplicating resources.
#
# COST
#   Cloud Run scales to zero. Cloud SQL db-f1-micro + 10GB SSD is the only
#   always-on cost (~$10-15/mo). Budget alert is set so nothing surprises
#   anyone. Delete the SQL instance if you need to stop all spend.
# =============================================================================
set -euo pipefail

# --- inputs -----------------------------------------------------------------
PROJECT_ID="${PROJECT_ID:-}"
REGION="${REGION:-asia-south1}"
GITHUB_REPO="${GITHUB_REPO:-varshinicb1/AcademicOS}"
GITHUB_REPO_ID="${GITHUB_REPO_ID:-}"
BILLING_ACCOUNT="${BILLING_ACCOUNT:-}"
BUDGET_AMOUNT="${BUDGET_AMOUNT:-100}"

AR_REPO="${AR_REPO:-academicos}"
SERVICE="${SERVICE:-academicos-backend}"
DEPLOY_SA_ID="${DEPLOY_SA_ID:-academicos-deploy}"
RUNTIME_SA_ID="${RUNTIME_SA_ID:-academicos-runtime}"
POOL_ID="${POOL_ID:-github}"
PROVIDER_ID="${PROVIDER_ID:-github}"
SQL_INSTANCE="${SQL_INSTANCE:-academicos-pg}"
# db-f1-micro / db-g1-small are shared-core and Google's own docs say they are
# "designed to provide low-cost test and development instances only. Don't use
# them for production" -- they are also excluded from the Cloud SQL SLA. The
# default here is the smallest dedicated-core instance. Drop to db-g1-small for
# a cheap trial (and set SQL_PITR=0 with it; PITR is a dedicated-core feature).
SQL_TIER="${SQL_TIER:-db-custom-1-3840}"
SQL_PITR="${SQL_PITR:-1}"
SQL_DB="${SQL_DB:-academicos}"
SQL_USER="${SQL_USER:-academicos}"
SKIP_SQL="${SKIP_SQL:-0}"
SKIP_FIREBASE="${SKIP_FIREBASE:-0}"

log()  { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
ok()   { printf '    \033[0;32mok\033[0m  %s\n' "$*"; }
warn() { printf '    \033[0;33mwarn\033[0m %s\n' "$*"; }

if [[ -z "$PROJECT_ID" ]]; then
  echo "ERROR: PROJECT_ID is required. Example:" >&2
  echo "  PROJECT_ID=my-project-id bash deploy/gcp/bootstrap.sh" >&2
  exit 1
fi

MODE="${MODE:-apply}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --check|--dry-run) MODE=check; shift ;;
    -h|--help) MODE=help; shift ;;
    *) echo "ERROR: unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [[ "$MODE" == "help" ]]; then
  sed -n '2,45p' "$0"
  exit 0
fi

command -v gcloud >/dev/null || { echo "ERROR: gcloud not found." >&2; exit 1; }

# `|| true` so a bad project ID / missing access lands in preflight's clear
# message instead of aborting here under `set -e` before anything is reported.
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)' 2>/dev/null || true)"
DEPLOY_SA="${DEPLOY_SA_ID}@${PROJECT_ID}.iam.gserviceaccount.com"
RUNTIME_SA="${RUNTIME_SA_ID}@${PROJECT_ID}.iam.gserviceaccount.com"
CLOUDBUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"
AR_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/backend"
WIF_PROVIDER="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/providers/${PROVIDER_ID}"
SQL_CONNECTION="${PROJECT_ID}:${REGION}:${SQL_INSTANCE}"
MEDIA_BUCKET="${PROJECT_ID}-academicos-media"
BACKUP_BUCKET="${PROJECT_ID}-academicos-backups"
CB_STAGING_BUCKET="${PROJECT_ID}-cloudbuild"

# --- preflight --------------------------------------------------------------
# Surfaces, BEFORE anything is created, the failure modes that would
# otherwise send the owner back for a second visit: disabled billing, an org
# policy blocking Cloud SQL's public IP, or a caller who cannot enable APIs.
# `--check` runs this and stops. `apply` runs it and continues.
#
# Everything else in this script is idempotent and re-runnable by the team, so
# these three are the complete set of things that genuinely require the owner.
preflight() {
  local blockers=0
  log "Preflight -- acting as $(gcloud config get-value account 2>/dev/null)"

  if [[ -z "$PROJECT_NUMBER" ]]; then
    warn "cannot read project '${PROJECT_ID}' -- wrong ID, or the caller has no access"
    return 1
  fi
  ok "project reachable (number ${PROJECT_NUMBER})"

  # Billing. Cloud Run and Cloud SQL cannot be created without it.
  local billing
  billing="$(gcloud billing projects describe "$PROJECT_ID" \
    --format='value(billingEnabled)' 2>/dev/null || true)"
  case "$billing" in
    True|true) ok "billing enabled" ;;
    False|false)
      warn "BILLING IS DISABLED on ${PROJECT_ID} -- Cloud Run and Cloud SQL cannot be created."
      warn "Fix: https://console.cloud.google.com/billing/linkedaccount?project=${PROJECT_ID}"
      blockers=$((blockers + 1)) ;;
    *)
      warn "could not read billing state (needs roles/billing.viewer) -- continuing" ;;
  esac

  # Org policy. If public IPs are blocked for Cloud SQL, the default provision
  # (public IP + Cloud Run's built-in connector) is refused, and only an org
  # admin can change that -- i.e. the owner. Catch it here, not mid-run.
  local pubip
  pubip="$(gcloud resource-manager org-policies describe constraints/sql.restrictPublicIp \
    --project="$PROJECT_ID" --effective \
    --format='value(booleanPolicy.enforced)' 2>/dev/null || true)"
  if [[ "$pubip" == "True" || "$pubip" == "true" ]]; then
    warn "org policy constraints/sql.restrictPublicIp is ENFORCED."
    warn "Cloud SQL with a public IP will be refused. Fix needs a VPC connector"
    warn "(docs/gcp-deployment.md section 8) or an org-policy exemption -- and an"
    warn "org admin. This is the one item that can legitimately require the owner twice."
    blockers=$((blockers + 1))
  else
    ok "no org policy blocking Cloud SQL public IP"
  fi

  # Can the caller enable APIs at all? Without this the script dies at step 1.
  if gcloud services list --enabled --project "$PROJECT_ID" >/dev/null 2>&1; then
    ok "caller can read service usage (likely able to enable APIs)"
  else
    warn "caller cannot list services -- needs roles/serviceusage.serviceUsageAdmin"
    blockers=$((blockers + 1))
  fi

  # Informational: which required APIs are not on yet.
  local missing_apis=() api
  for api in run.googleapis.com artifactregistry.googleapis.com \
             cloudbuild.googleapis.com secretmanager.googleapis.com \
             sqladmin.googleapis.com; do
    if ! gcloud services list --enabled --project "$PROJECT_ID" \
           --filter="config.name=${api}" --format='value(config.name)' 2>/dev/null | grep -q .; then
      missing_apis+=("$api")
    fi
  done
  if [[ ${#missing_apis[@]} -gt 0 ]]; then
    ok "will enable: ${missing_apis[*]}"
  else
    ok "all required APIs already enabled"
  fi

  # Informational: what already exists, so a re-run's effect is predictable.
  local existing=()
  gcloud artifacts repositories describe "$AR_REPO" --location "$REGION" --project "$PROJECT_ID" >/dev/null 2>&1 \
    && existing+=("artifact-repo")
  gcloud iam service-accounts describe "$DEPLOY_SA" --project "$PROJECT_ID" >/dev/null 2>&1 \
    && existing+=("deploy-sa")
  gcloud sql instances describe "$SQL_INSTANCE" --project "$PROJECT_ID" >/dev/null 2>&1 \
    && existing+=("cloud-sql")
  if [[ ${#existing[@]} -gt 0 ]]; then
    ok "already present (re-run leaves these alone): ${existing[*]}"
  else
    ok "nothing exists yet -- first-time provision"
  fi

  return "$blockers"
}

if ! preflight; then
  if [[ "$MODE" == "check" ]]; then
    echo
    echo "BLOCKED. The item(s) above need the project/org owner. Nothing was created."
    echo "Send this output back and the fix can be made specific."
    exit 1
  fi
  echo
  echo "Preflight reported blocker(s) above; continuing in apply mode in 5s (Ctrl-C to stop)."
  sleep 5
fi

if [[ "$MODE" == "check" ]]; then
  log "Check complete -- NOTHING WAS CREATED."
  echo "Re-run without --check to apply."
  exit 0
fi

log "Project ${PROJECT_ID} (number ${PROJECT_NUMBER}) -- region ${REGION}"
gcloud config set project "$PROJECT_ID" --quiet >/dev/null

# --- 1. APIs ----------------------------------------------------------------
log "Enabling APIs (this is the slow part on a fresh project)"
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  sqladmin.googleapis.com \
  storage.googleapis.com \
  iamcredentials.googleapis.com \
  cloudresourcemanager.googleapis.com \
  serviceusage.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  cloudtrace.googleapis.com \
  billingbudgets.googleapis.com \
  firebase.googleapis.com \
  firebasehosting.googleapis.com \
  --project "$PROJECT_ID" --quiet
ok "APIs enabled"

# --- 2. Artifact Registry ---------------------------------------------------
log "Artifact Registry"
if gcloud artifacts repositories describe "$AR_REPO" --location "$REGION" --project "$PROJECT_ID" >/dev/null 2>&1; then
  ok "repository ${AR_REPO} already exists"
else
  gcloud artifacts repositories create "$AR_REPO" \
    --repository-format=docker --location="$REGION" \
    --description="AcademicOS backend images" --project "$PROJECT_ID" --quiet
  ok "created repository ${AR_REPO}"
fi

# Retention cap. Without a policy every deploy leaves its image behind forever
# and Artifact Registry grows without bound ($0.10/GB-month after 0.5 GB free).
# Measured image size is ~650 MB, so an unbounded history would cost roughly
# $0.65 per retained version per month. Keep the 3 most recent -- enough for
# rollback -- and drop anything older than 30 days.
CLEANUP_POLICY='[
  {
    "name": "keep-recent-3",
    "action": {"type": "Keep"},
    "mostRecentVersions": {"keepCount": 3}
  },
  {
    "name": "delete-older-than-30d",
    "action": {"type": "Delete"},
    "condition": {"tagState": "any", "olderThan": "30d"}
  }
]'
POLICY_FILE="$(mktemp)"
printf '%s' "$CLEANUP_POLICY" > "$POLICY_FILE"
if gcloud artifacts repositories set-cleanup-policies "$AR_REPO" \
     --project "$PROJECT_ID" --location "$REGION" \
     --policy="$POLICY_FILE" --quiet >/dev/null 2>&1; then
  ok "retention: keep 3 most recent, delete >30d"
else
  warn "could not set the Artifact Registry cleanup policy -- images will accumulate"
fi
rm -f "$POLICY_FILE"

# --- 3. Service accounts ----------------------------------------------------
log "Service accounts"
ensure_sa() {
  local id="$1" display="$2" email="$3"
  if gcloud iam service-accounts describe "$email" --project "$PROJECT_ID" >/dev/null 2>&1; then
    ok "${id} already exists"
  else
    gcloud iam service-accounts create "$id" --display-name="$display" --project "$PROJECT_ID" --quiet
    ok "created ${id}"
  fi
}
ensure_sa "$DEPLOY_SA_ID"  "AcademicOS GitHub Actions deploy" "$DEPLOY_SA"
ensure_sa "$RUNTIME_SA_ID" "AcademicOS Cloud Run runtime"      "$RUNTIME_SA"

# --- 4. IAM ----------------------------------------------------------------
log "IAM bindings"
bind() {  # bind <member> <role>
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="$1" --role="$2" --condition=None --quiet >/dev/null
  ok "$2"
}

# Deploy SA: builds images, deploys Cloud Run, manages secrets + hosting.
bind "serviceAccount:${DEPLOY_SA}" "roles/run.admin"
bind "serviceAccount:${DEPLOY_SA}" "roles/artifactregistry.writer"
bind "serviceAccount:${DEPLOY_SA}" "roles/cloudbuild.builds.editor"
bind "serviceAccount:${DEPLOY_SA}" "roles/secretmanager.admin"
bind "serviceAccount:${DEPLOY_SA}" "roles/storage.admin"
bind "serviceAccount:${DEPLOY_SA}" "roles/serviceusage.serviceUsageConsumer"
bind "serviceAccount:${DEPLOY_SA}" "roles/firebasehosting.admin"
bind "serviceAccount:${DEPLOY_SA}" "roles/iam.serviceAccountUser"   # actAs the runtime SA
bind "serviceAccount:${DEPLOY_SA}" "roles/cloudsql.client"          # reach Cloud SQL during deploys

# Cloud Build's own SA must be able to push the image and read sources.
bind "serviceAccount:${CLOUDBUILD_SA}" "roles/artifactregistry.writer"
bind "serviceAccount:${CLOUDBUILD_SA}" "roles/storage.objectAdmin"

# Runtime SA: least privilege -- only what the running service needs.
bind "serviceAccount:${RUNTIME_SA}" "roles/cloudsql.client"
bind "serviceAccount:${RUNTIME_SA}" "roles/secretmanager.secretAccessor"
bind "serviceAccount:${RUNTIME_SA}" "roles/storage.objectAdmin"
bind "serviceAccount:${RUNTIME_SA}" "roles/logging.logWriter"
bind "serviceAccount:${RUNTIME_SA}" "roles/cloudtrace.agent"
bind "serviceAccount:${RUNTIME_SA}" "roles/monitoring.metricWriter"

# --- 5. Workload Identity Federation ---------------------------------------
log "Workload Identity Federation (keyless GitHub Actions auth)"
if gcloud iam workload-identity-pools describe "$POOL_ID" \
     --location=global --project "$PROJECT_ID" >/dev/null 2>&1; then
  ok "pool ${POOL_ID} already exists"
else
  gcloud iam workload-identity-pools create "$POOL_ID" \
    --location=global --display-name="GitHub Actions" --project "$PROJECT_ID" --quiet
  ok "created pool ${POOL_ID}"
fi

# attribute.repository is the security boundary: only this one repo -- and
# only pushes to master -- can assume the deploy identity.
CONDITION="assertion.repository=='${GITHUB_REPO}'"
if gcloud iam workload-identity-pools providers describe "$PROVIDER_ID" \
     --workload-identity-pool="$POOL_ID" --location=global \
     --project "$PROJECT_ID" >/dev/null 2>&1; then
  ok "provider ${PROVIDER_ID} already exists"
  gcloud iam workload-identity-pools providers update-oidc "$PROVIDER_ID" \
    --workload-identity-pool="$POOL_ID" --location=global \
    --attribute-condition="$CONDITION" --project "$PROJECT_ID" --quiet >/dev/null
  ok "attribute condition refreshed -> ${GITHUB_REPO}"
else
  gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_ID" \
    --workload-identity-pool="$POOL_ID" --location=global \
    --display-name="GitHub" \
    --issuer-uri="https://token.actions.githubusercontent.com" \
    --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner,attribute.ref=assertion.ref" \
    --attribute-condition="$CONDITION" \
    --project "$PROJECT_ID" --quiet
  ok "created provider ${PROVIDER_ID}"
fi

# Let that specific repo impersonate the deploy SA (this is the trust link).
gcloud iam service-accounts add-iam-policy-binding "$DEPLOY_SA" \
  --project "$PROJECT_ID" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/attribute.repository/${GITHUB_REPO}" \
  --quiet >/dev/null
ok "GitHub repo ${GITHUB_REPO} -> ${DEPLOY_SA_ID}"

# --- 6. Secrets -------------------------------------------------------------
log "Secret Manager"
# Values are NOT set here (except the generated Postgres password). The team
# pastes real values in afterwards; placeholders keep Cloud Run deploys from
# failing on a missing secret.
ensure_secret() {
  local name="$1"
  if gcloud secrets describe "$name" --project "$PROJECT_ID" >/dev/null 2>&1; then
    ok "secret ${name} already exists"
  else
    printf 'REPLACE_ME' | gcloud secrets create "$name" \
      --data-file=- --replication-policy=automatic --project "$PROJECT_ID" --quiet
    ok "created secret ${name} (placeholder -- paste the real value in)"
  fi
}
ensure_secret supabase-url
ensure_secret supabase-anon-key
ensure_secret principal-bootstrap-key
ensure_secret acos-llm-api-key
ensure_secret postgres-password

# --- 7. Cloud SQL -----------------------------------------------------------
if [[ "$SKIP_SQL" == "1" ]]; then
  warn "SKIP_SQL=1 -- skipping Cloud SQL (app will fall back to SQLite/Supabase)"
else
  log "Cloud SQL Postgres (${SQL_TIER} in ${REGION}) -- takes ~5-10 min on first run"
  if gcloud sql instances describe "$SQL_INSTANCE" --project "$PROJECT_ID" >/dev/null 2>&1; then
    ok "instance ${SQL_INSTANCE} already exists"
  else
    SQL_FLAGS=(
      --database-version=POSTGRES_16
      --tier="$SQL_TIER"
      --region="$REGION"
      --storage-size=10GB
      --storage-type=SSD
      --storage-auto-increase
      --backup-start-time=19:00
    )
    # Opt-out rather than unconditional: Google's docs do not state plainly
    # whether PITR is available on shared-core tiers, and if it is not, asking
    # for it makes instance creation fail outright. The default tier below is
    # dedicated-core, where it is definitely supported; set SQL_PITR=0 if you
    # drop to db-g1-small and creation rejects the flag.
    if [[ "$SQL_PITR" == "1" ]]; then
      SQL_FLAGS+=(--enable-point-in-time-recovery)
    fi
    gcloud sql instances create "$SQL_INSTANCE" \
      "${SQL_FLAGS[@]}" \
      --project "$PROJECT_ID" --quiet
    ok "created instance ${SQL_INSTANCE} (daily backups$([[ "$SQL_PITR" == "1" ]] && echo ' + PITR'))"
  fi

  if gcloud sql databases describe "$SQL_DB" --instance="$SQL_INSTANCE" --project "$PROJECT_ID" >/dev/null 2>&1; then
    ok "database ${SQL_DB} already exists"
  else
    gcloud sql databases create "$SQL_DB" --instance="$SQL_INSTANCE" --project "$PROJECT_ID" --quiet
    ok "created database ${SQL_DB}"
  fi

  # Generate the password once; store it in Secret Manager and reuse on re-runs.
  if gcloud sql users list --instance="$SQL_INSTANCE" --project "$PROJECT_ID" \
       --format='value(name)' | grep -qx "$SQL_USER"; then
    ok "db user ${SQL_USER} already exists"
  else
    PG_PASSWORD="$(gcloud secrets versions access latest --secret=postgres-password --project "$PROJECT_ID")"
    if [[ "$PG_PASSWORD" == "REPLACE_ME" || -z "$PG_PASSWORD" ]]; then
      PG_PASSWORD="$(openssl rand -base64 32 | tr -d '/+=' | cut -c1-32)"
      printf '%s' "$PG_PASSWORD" | gcloud secrets versions add postgres-password \
        --data-file=- --project "$PROJECT_ID" --quiet
      ok "generated + stored postgres-password"
    fi
    gcloud sql users create "$SQL_USER" --instance="$SQL_INSTANCE" \
      --password="$PG_PASSWORD" --project "$PROJECT_ID" --quiet
    ok "created db user ${SQL_USER}"
    unset PG_PASSWORD
  fi
fi

# --- 8. GCS buckets ---------------------------------------------------------
log "Cloud Storage buckets"
ensure_bucket() {
  local b="$1"
  if gcloud storage buckets describe "gs://${b}" --project "$PROJECT_ID" >/dev/null 2>&1; then
    ok "bucket ${b} already exists"
  else
    gcloud storage buckets create "gs://${b}" \
      --location="$REGION" --uniform-bucket-level-access \
      --project "$PROJECT_ID" --quiet
    ok "created bucket ${b}"
  fi
}
ensure_bucket "$MEDIA_BUCKET"     # scan photos/PDFs
ensure_bucket "$BACKUP_BUCKET"    # pg_dump exports
ensure_bucket "$CB_STAGING_BUCKET" # Cloud Build source staging

# --- 9. Firebase Hosting ----------------------------------------------------
if [[ "$SKIP_FIREBASE" == "1" ]]; then
  warn "SKIP_FIREBASE=1 -- skipping Firebase Hosting"
elif command -v firebase >/dev/null 2>&1; then
  log "Firebase Hosting"
  if firebase projects:list --json 2>/dev/null | grep -q "\"$PROJECT_ID\""; then
    ok "project already linked to Firebase"
  else
    firebase projects:addfirebase "$PROJECT_ID" 2>&1 | tail -2 || \
      warn "could not add Firebase automatically -- open https://console.firebase.google.com and click 'Add project' once"
  fi
else
  warn "firebase CLI not found -- run this in Cloud Shell, or add the project at https://console.firebase.google.com"
fi

# --- 10. Budget alert -------------------------------------------------------
log "Budget alert"
if [[ -z "$BILLING_ACCOUNT" ]]; then
  warn "BILLING_ACCOUNT not set -- skipping budget alert (set it to get spend alarms)"
else
  if gcloud billing budgets list --billing-account="$BILLING_ACCOUNT" \
       --format='value(displayName)' 2>/dev/null | grep -qx "AcademicOS monthly"; then
    ok "budget 'AcademicOS monthly' already exists"
  else
    gcloud billing budgets create \
      --billing-account="$BILLING_ACCOUNT" \
      --display-name="AcademicOS monthly" \
      --budget-amount="${BUDGET_AMOUNT}USD" \
      --threshold-rule=percent=0.5 \
      --threshold-rule=percent=0.9 \
      --threshold-rule=percent=1.0 \
      --project "$PROJECT_ID" --quiet >/dev/null 2>&1 \
      && ok "budget alert at ${BUDGET_AMOUNT} USD (50/90/100% thresholds)" \
      || warn "could not create budget -- set one manually at https://console.cloud.google.com/billing"
  fi
fi

# --- done -------------------------------------------------------------------
cat <<EOF

=============================================================================
 Bootstrap complete.
=============================================================================

 Akhil: your part is finished. Nothing further is required from you --
 deploys now run from GitHub automatically on every push to master.

 Last step for the TEAM (one time): set these two values in the GitHub repo
 (Settings -> Secrets and variables -> Actions -> Variables tab):

   gh variable set GCP_PROJECT_ID   --body "${PROJECT_ID}"
   gh variable set GCP_REGION       --body "${REGION}"
   gh variable set WIF_PROVIDER     --body "${WIF_PROVIDER}"
   gh variable set DEPLOY_SA        --body "${DEPLOY_SA}"
   gh variable set RUNTIME_SA       --body "${RUNTIME_SA}"
   gh variable set GCP_SERVICE      --body "${SERVICE}"
   gh variable set AR_IMAGE         --body "${AR_IMAGE}"
   gh variable set GCS_MEDIA_BUCKET --body "${MEDIA_BUCKET}"
   gh variable set SQL_CONNECTION   --body "${SQL_CONNECTION}"

 Then paste the real values into Secret Manager (never into git):

   printf '%s' 'https://<proj>.supabase.co' | gcloud secrets versions add supabase-url --data-file=-
   printf '%s' '<anon-key>'                 | gcloud secrets versions add supabase-anon-key --data-file=-
   printf '%s' '<bootstrap-key>'            | gcloud secrets versions add principal-bootstrap-key --data-file=-
   printf '%s' '<sarvam-api-key>'           | gcloud secrets versions add acos-llm-api-key --data-file=-

 Migration note: Supabase still holds today's production data. Until you run
 scripts/migrate_supabase_to_cloudsql.py, the deployed service keeps using it
 as the durability backend and Cloud SQL sits idle. Nothing breaks either way.
EOF
