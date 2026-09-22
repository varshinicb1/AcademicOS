#!/usr/bin/env bash
# =============================================================================
# Apply deploy/gcp/schema.sql to the Cloud SQL instance. Safe to re-run.
# =============================================================================
#
# WHY THIS EXISTS
#   Nothing else applies the schema. bootstrap.sh creates the instance, the
#   database and the user; deploy-gcp.yml builds and deploys; neither runs
#   schema.sql. So a table added to schema.sql after an instance was
#   provisioned -- learner_models was, on 2026-09-22 -- does not exist there,
#   and every request that touches it answers 503 ("relation does not exist")
#   while GET /health still answers 200. GET /health/storage names it:
#   `status: "schema_missing"`, `missing_tables: [...]`.
#
# WHEN (required, docs/gcp-deployment.md section 6)
#   - before the first deploy to a new instance;
#   - after ANY change to deploy/gcp/schema.sql, before the deploy that
#     ships code using it.
#   Every statement in schema.sql is IF NOT EXISTS, so re-running is harmless.
#
# WHO / WHERE
#   A project owner, from Cloud Shell (already authenticated, psql installed)
#   or any machine with gcloud + psql, from the repo root:
#
#       PROJECT_ID=vidyuthlabs bash scripts/apply_cloudsql_schema.sh
#
#   `gcloud sql connect` allowlists the caller's IP on the instance's public
#   IP for five minutes; the instance needs a public IP for that path (the
#   bootstrap's default). The database password is read from the
#   `postgres-password` secret bootstrap.sh stored, unless PGPASSWORD is set.
#
#   Optional overrides (defaults match deploy/gcp/bootstrap.sh):
#     SQL_INSTANCE=academicos-pg  SQL_DB=academicos  SQL_USER=academicos
# =============================================================================
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?set PROJECT_ID, e.g. PROJECT_ID=vidyuthlabs}"
SQL_INSTANCE="${SQL_INSTANCE:-academicos-pg}"
SQL_DB="${SQL_DB:-academicos}"
SQL_USER="${SQL_USER:-academicos}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCHEMA="${ROOT}/deploy/gcp/schema.sql"
[[ -f "$SCHEMA" ]] || { echo "ERROR: $SCHEMA not found" >&2; exit 1; }
command -v psql >/dev/null || { echo "ERROR: psql not found (Cloud Shell has it)" >&2; exit 1; }

if [[ -z "${PGPASSWORD:-}" ]]; then
  PGPASSWORD="$(gcloud secrets versions access latest --secret=postgres-password \
                  --project "$PROJECT_ID")"
fi
export PGPASSWORD

echo "Applying deploy/gcp/schema.sql to ${PROJECT_ID}:${SQL_INSTANCE}/${SQL_DB} as ${SQL_USER}"
# ON_ERROR_STOP: without it psql reports an error, carries on, and exits 0,
# so a half-applied schema would look like success.
{ echo '\set ON_ERROR_STOP on'; cat "$SCHEMA"; } \
  | gcloud sql connect "$SQL_INSTANCE" --project "$PROJECT_ID" \
      --user="$SQL_USER" --database="$SQL_DB" --quiet

echo "Done. Confirm with: curl -s https://<run-url>/health/storage"
echo "  -> \"status\": \"ok\" and \"missing_tables\": [] (the probe caches for 30 s)."
