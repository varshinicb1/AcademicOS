# Monitoring and alerting (R-A4, NFR-7)

What the backend writes, and the uptime check and alert policies the **owner** creates in Google Cloud.
Nothing here is run by CI or by an agent: these are commands for the owner, run once from a shell signed in
to the project (`gcloud auth login`). They change no code and no deploy file.

R-A4 is accepted when a deliberately failing check produces an alert in the owner's inbox (step 6).

## 1. What the backend logs

Since R-A4 (`src/academicos/api/request_logging.py`):

- **A request id on every request.** The caller's `X-Request-ID` is kept when it is 8-64 characters of
  letters, digits, `.`, `_` or `-`; otherwise a new one is made. It comes back in the `X-Request-ID`
  response header (exposed to the web client through CORS), so an error report can quote it.
- **The school on every log line written while a signed-in request runs.** It is the signed-in user's
  `school_id`, bound where auth resolves the user (`auth_routes.get_current_user`), never a value from the
  request.
- **One access line per request** on the `academicos.access` logger: method, the route's *template*
  (`/api/v1/students/{sid}`, so no ids), status, duration in ms, request id and school id. No query
  string, header, token, email or body. uvicorn's own access line (raw path and query) is switched off.
- **JSON on Cloud Run.** When `K_SERVICE` is set (Cloud Run sets it) or `ACOS_LOG_FORMAT=json`, every
  record is one JSON line with Cloud Logging's fields: `severity`, `message`, `time`, `httpRequest`
  (method, status, latency) on access lines, and `logging.googleapis.com/trace` / `spanId` when the
  request came through Google's front end. Locally it is plain text with `[rid=... school=...]` appended;
  `ACOS_LOG_FORMAT=text` forces text anywhere.
- **Errors** are unchanged: an unhandled exception is still written as a Cloud Error Reporting event
  (`api/error_tracking.py`), and its access line has severity `ERROR`.

The trace link needs the project id, which Cloud Run does not put in the environment. It is read from
`ACOS_GCP_PROJECT` (or `GOOGLE_CLOUD_PROJECT`). Adding that variable to the service is a deploy change, so
it is the owner's call; without it, everything above works and only the link from a log line to its trace
is missing.

Useful Logs Explorer queries (Cloud Run service `academicos-backend`):

```text
jsonPayload.request_id="<id from the X-Request-ID header>"
jsonPayload.logger="academicos.access" AND jsonPayload.school_id="<school id>"
jsonPayload.logger="academicos.access" AND severity>=ERROR
```

## 2. Before you start

Billing must be active on the project. Uptime checks, alerting and email notifications do not work on a
project without a billing account, and policies created before it is linked never fire.

```bash
export PROJECT_ID="<your-project-id>"          # placeholder: the GCP project of the live backend
export OWNER_EMAIL="<owner@example.com>"       # placeholder: where alerts go
export REGION="asia-south1"                    # the Cloud Run region of academicos-backend
export SERVICE="academicos-backend"
export HOST="academicos-backend-2eskom55ta-el.a.run.app"

gcloud config set project "$PROJECT_ID"
gcloud billing projects describe "$PROJECT_ID" --format="value(billingEnabled)"   # must print True
gcloud services enable monitoring.googleapis.com logging.googleapis.com clouderrorreporting.googleapis.com
```

No secret is needed for any step below.

## 3. The email channel

```bash
gcloud beta monitoring channels create \
  --display-name="AcademicOS owner" --type=email \
  --channel-labels=email_address="$OWNER_EMAIL"

export CHANNEL=$(gcloud beta monitoring channels list \
  --filter="labels.email_address=\"$OWNER_EMAIL\"" --format="value(name)" | head -1)
echo "$CHANNEL"   # projects/<id>/notificationChannels/<n>
```

Google sends a verification email to the address; alerts are delivered once it is confirmed.

## 4. The uptime check on `/health`

`/health` is public and unauthenticated, and answers 200 with the running commit.

```bash
gcloud monitoring uptime create academicos-health \
  --resource-type=uptime-url \
  --resource-labels=host="$HOST",project_id="$PROJECT_ID" \
  --protocol=https --path=/health --port=443 \
  --period=1 --timeout=10 \
  --regions=asia-pacific,europe,usa-oregon

export CHECK_ID=$(gcloud monitoring uptime list-configs \
  --filter='displayName="academicos-health"' --format="value(name)" | sed 's#.*/##')
echo "$CHECK_ID"
```

## 5. Alert policies

Each policy is written to a file and created from it. The thresholds are starting points (estimated, not
measured against live traffic); tune them after a week of real use.

### 5.1 Uptime: `/health` failing from two or more regions for a minute

```bash
cat > /tmp/acos-uptime.json <<EOF
{
  "displayName": "AcademicOS: /health is down",
  "combiner": "OR",
  "conditions": [{
    "displayName": "Uptime check failing",
    "conditionThreshold": {
      "filter": "metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\" AND resource.type=\"uptime_url\" AND metric.label.check_id=\"$CHECK_ID\"",
      "aggregations": [{
        "alignmentPeriod": "60s",
        "perSeriesAligner": "ALIGN_NEXT_OLDER",
        "crossSeriesReducer": "REDUCE_COUNT_FALSE",
        "groupByFields": ["resource.label.project_id", "resource.label.host"]
      }],
      "comparison": "COMPARISON_GT",
      "thresholdValue": 1,
      "duration": "60s",
      "trigger": {"count": 1}
    }
  }],
  "notificationChannels": ["$CHANNEL"],
  "documentation": {"content": "The backend's /health is failing. See docs/incident-response-runbook.md.", "mimeType": "text/markdown"}
}
EOF
gcloud alpha monitoring policies create --policy-from-file=/tmp/acos-uptime.json
```

### 5.2 5xx rate: more than 5 server errors in 5 minutes

```bash
cat > /tmp/acos-5xx.json <<EOF
{
  "displayName": "AcademicOS: 5xx responses",
  "combiner": "OR",
  "conditions": [{
    "displayName": "5xx count over 5 minutes",
    "conditionThreshold": {
      "filter": "metric.type=\"run.googleapis.com/request_count\" AND resource.type=\"cloud_run_revision\" AND resource.label.service_name=\"$SERVICE\" AND metric.label.response_code_class=\"5xx\"",
      "aggregations": [{
        "alignmentPeriod": "300s",
        "perSeriesAligner": "ALIGN_DELTA",
        "crossSeriesReducer": "REDUCE_SUM",
        "groupByFields": ["resource.label.service_name"]
      }],
      "comparison": "COMPARISON_GT",
      "thresholdValue": 5,
      "duration": "0s",
      "trigger": {"count": 1}
    }
  }],
  "notificationChannels": ["$CHANNEL"],
  "documentation": {"content": "Server errors on academicos-backend. Find them in Logs Explorer with jsonPayload.logger=\"academicos.access\" AND severity>=ERROR, then follow a request_id.", "mimeType": "text/markdown"}
}
EOF
gcloud alpha monitoring policies create --policy-from-file=/tmp/acos-5xx.json
```

### 5.3 Latency: p95 above 2 seconds for 10 minutes

```bash
cat > /tmp/acos-latency.json <<EOF
{
  "displayName": "AcademicOS: p95 latency",
  "combiner": "OR",
  "conditions": [{
    "displayName": "p95 request latency above 2000 ms",
    "conditionThreshold": {
      "filter": "metric.type=\"run.googleapis.com/request_latencies\" AND resource.type=\"cloud_run_revision\" AND resource.label.service_name=\"$SERVICE\"",
      "aggregations": [{
        "alignmentPeriod": "300s",
        "perSeriesAligner": "ALIGN_PERCENTILE_95",
        "crossSeriesReducer": "REDUCE_MAX",
        "groupByFields": ["resource.label.service_name"]
      }],
      "comparison": "COMPARISON_GT",
      "thresholdValue": 2000,
      "duration": "600s",
      "trigger": {"count": 1}
    }
  }],
  "notificationChannels": ["$CHANNEL"],
  "documentation": {"content": "Requests are slow. The access lines carry duration_ms and the route template; sort by them to find the slow route.", "mimeType": "text/markdown"}
}
EOF
gcloud alpha monitoring policies create --policy-from-file=/tmp/acos-latency.json
```

Model routes (AI marking, OCR) are slower than the rest by nature. If they keep this policy noisy, add a
second, looser policy for them rather than raising this one.

### 5.4 New Error Reporting groups

Error Reporting groups the backend's `ReportedErrorEvent` lines and the apps' reports on its own. Its
notification for a **new** group is set in the console, not with gcloud:

1. Cloud Console, **Error Reporting**, then **Configure notifications**.
2. Choose the email channel created in step 3 ("AcademicOS owner").
3. Save. A first-seen error group (and a resolved one that comes back) now emails the owner.

## 6. Prove an alert fires (the R-A4 acceptance test)

Create a check that is meant to fail, alert on it, wait for the email, then delete both.

```bash
gcloud monitoring uptime create acos-alert-drill \
  --resource-type=uptime-url \
  --resource-labels=host="$HOST",project_id="$PROJECT_ID" \
  --protocol=https --path=/this-path-does-not-exist --port=443 \
  --period=1 --timeout=10 --regions=asia-pacific,europe,usa-oregon

export DRILL_ID=$(gcloud monitoring uptime list-configs \
  --filter='displayName="acos-alert-drill"' --format="value(name)" | sed 's#.*/##')
sed -e "s/$CHECK_ID/$DRILL_ID/" -e 's#/health is down#alert drill (delete me)#' \
  /tmp/acos-uptime.json > /tmp/acos-drill.json
gcloud alpha monitoring policies create --policy-from-file=/tmp/acos-drill.json
```

Within about 5 minutes the owner's inbox gets an "alert drill" incident. Record the time it arrived, then
remove the drill:

```bash
gcloud alpha monitoring policies list --filter='displayName:"alert drill"' --format="value(name)" \
  | xargs -r -n1 gcloud alpha monitoring policies delete --quiet
gcloud monitoring uptime delete "$DRILL_ID" --quiet
```

The real check never touches the drill path, and the drill sends no credential and creates nothing on the
live site.

## 7. What is not covered here

- Log-based metrics per school (requests or errors by `school_id`). The fields are in the logs; a metric
  can be added once a school asks for its own numbers. Per-school usage is already at `/api/v1/ops/usage`.
- Paging (SMS, phone). Email only, as R-A4 asks.
- Uptime of the web console on Firebase Hosting. Add a second uptime check on `vidyuthlabs.web.app` the
  same way as step 4 if wanted.
