#!/usr/bin/env bash
# R-A2 restore drill (NFR-4): prove the backups restore, and time it.
#
# The OWNER runs this, from a machine signed in to gcloud as a project owner,
# once billing is active. It never writes to production: it reads the live
# instance's backup settings, restores into a NEW scratch instance, counts rows
# there, and deletes only that scratch instance (after asking).
#
#   PROJECT_ID=vidyuthlabs bash scripts/restore_drill.sh            # PITR clone, 10 minutes ago
#   PROJECT_ID=vidyuthlabs MODE=backup bash scripts/restore_drill.sh # latest automated backup
#   PROJECT_ID=vidyuthlabs bash scripts/restore_drill.sh --check     # settings only, creates nothing
#
# Prints a block to paste into docs/incident-response-runbook.md ("Restore
# drill log"). Costs: a scratch instance at the live tier for the length of the
# drill (usually under an hour), deleted at the end.
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?set PROJECT_ID}"
REGION="${REGION:-asia-south1}"
SQL_INSTANCE="${SQL_INSTANCE:-academicos-pg}"
SQL_DB="${SQL_DB:-academicos}"
MEDIA_BUCKET="${MEDIA_BUCKET:-${PROJECT_ID}-academicos-media}"
MODE="${MODE:-pitr}"                       # pitr | backup
SCRATCH="${SCRATCH:-${SQL_INSTANCE}-drill-$(date -u +%Y%m%d%H%M)}"
CHECK_ONLY=0
[[ "${1:-}" == "--check" ]] && CHECK_ONLY=1

say() { printf '%s\n' "$*"; }
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }

say "== Backup settings on ${PROJECT_ID}/${SQL_INSTANCE}"
backup_cfg=$(gcloud sql instances describe "$SQL_INSTANCE" --project "$PROJECT_ID" \
  --format='value(settings.backupConfiguration.enabled,settings.backupConfiguration.pointInTimeRecoveryEnabled,settings.backupConfiguration.transactionLogRetentionDays,settings.backupConfiguration.backupRetentionSettings.retainedBackups)')
read -r backups_on pitr_on log_days retained <<<"$backup_cfg"
say "automated backups: ${backups_on:-unset}  PITR: ${pitr_on:-unset}  log days: ${log_days:-unset}  retained backups: ${retained:-unset}"
[[ "$backups_on" == "True" ]] || fail "automated backups are off. Turn them on: gcloud sql instances patch $SQL_INSTANCE --backup-start-time=19:00 --project $PROJECT_ID"
if [[ "$pitr_on" != "True" ]]; then
  say "PITR is off. Turn it on: gcloud sql instances patch $SQL_INSTANCE --enable-point-in-time-recovery --project $PROJECT_ID"
  [[ "$MODE" == "pitr" ]] && fail "MODE=pitr needs PITR; rerun with MODE=backup or turn PITR on first"
fi

say "== Media bucket gs://${MEDIA_BUCKET}"
versioning=$(gcloud storage buckets describe "gs://${MEDIA_BUCKET}" --project "$PROJECT_ID" --format='value(versioning_enabled)' || true)
soft_delete=$(gcloud storage buckets describe "gs://${MEDIA_BUCKET}" --project "$PROJECT_ID" --format='value(soft_delete_policy.retentionDurationSeconds)' || true)
say "object versioning: ${versioning:-unset}  soft delete seconds: ${soft_delete:-unset}"
if [[ "$versioning" != "True" ]]; then
  say "Turn versioning on (keeps overwritten and deleted uploads and snapshots recoverable):"
  say "  gcloud storage buckets update gs://${MEDIA_BUCKET} --versioning --project $PROJECT_ID"
  say "  and cap old versions: see docs/incident-response-runbook.md, 'Backups and restore'"
fi

if (( CHECK_ONLY )); then say "== --check: nothing created"; exit 0; fi

say "== Restoring into scratch instance ${SCRATCH} (mode ${MODE})"
read -r -p "Create ${SCRATCH} in ${PROJECT_ID}? This is billed until it is deleted. [y/N] " yn
[[ "$yn" == "y" || "$yn" == "Y" ]] || fail "stopped before creating anything"

start=$(date -u +%s)
if [[ "$MODE" == "pitr" ]]; then
  point=$(date -u -d '-10 minutes' +%Y-%m-%dT%H:%M:%SZ)
  say "point in time: ${point}"
  gcloud sql instances clone "$SQL_INSTANCE" "$SCRATCH" --point-in-time "$point" --project "$PROJECT_ID"
else
  backup_id=$(gcloud sql backups list --instance "$SQL_INSTANCE" --project "$PROJECT_ID" \
    --filter='status=SUCCESSFUL' --sort-by='~windowStartTime' --limit 1 --format='value(id)')
  [[ -n "$backup_id" ]] || fail "no successful backup to restore"
  tier=$(gcloud sql instances describe "$SQL_INSTANCE" --project "$PROJECT_ID" --format='value(settings.tier)')
  gcloud sql instances create "$SCRATCH" --database-version=POSTGRES_16 --edition=ENTERPRISE \
    --tier="$tier" --region="$REGION" --project "$PROJECT_ID" --quiet
  gcloud sql backups restore "$backup_id" --restore-instance="$SCRATCH" \
    --backup-instance="$SQL_INSTANCE" --project "$PROJECT_ID" --quiet
fi
end=$(date -u +%s)
say "restore took $(( (end - start) / 60 )) min $(( (end - start) % 60 )) s"

say "== Row counts on the scratch copy (compare with the live counts printed by /health/storage or the same query on live)"
say "Run, then paste the output into the drill log:"
say "  gcloud sql connect ${SCRATCH} --user=postgres --database=${SQL_DB} --project ${PROJECT_ID}"
say "  -- then in psql:"
say "  SELECT schemaname, relname, n_live_tup FROM pg_stat_user_tables ORDER BY 1, 2;"
say "  (n_live_tup is an estimate; for exact counts use SELECT count(*) on the tables you care about.)"

read -r -p "Delete scratch instance ${SCRATCH} now? [y/N] " yn
if [[ "$yn" == "y" || "$yn" == "Y" ]]; then
  [[ "$SCRATCH" == "$SQL_INSTANCE" ]] && fail "refusing to delete the live instance"
  gcloud sql instances delete "$SCRATCH" --project "$PROJECT_ID" --quiet
  say "deleted ${SCRATCH}"
else
  say "left ${SCRATCH} running; delete it with: gcloud sql instances delete ${SCRATCH} --project ${PROJECT_ID}"
fi

cat <<EOF

== Paste into docs/incident-response-runbook.md, "Restore drill log"
| $(date -u +%Y-%m-%d) | ${MODE} | ${SQL_INSTANCE} -> ${SCRATCH} | $(( (end - start) / 60 )) min | row counts: <paste> | media versioning: ${versioning:-unset} |
EOF
