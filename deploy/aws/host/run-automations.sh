#!/bin/bash
# Every 5 minutes (academicos-automations.timer): the scheduled jobs (NTF-2
# reminders, digests, webhook retries), as Cloud Scheduler did on GCP.
set -euo pipefail
key="$(sed -n 's/^ACOS_CRON_KEY=//p' /etc/academicos/app.env)"
curl -fsS -m 120 -X POST -H "X-Cron-Key: $key" http://127.0.0.1:8080/api/v1/automations/run >/dev/null
