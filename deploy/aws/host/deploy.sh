#!/bin/bash
# deploy.sh <image> <web origins>  -- run by GitHub Actions through SSM after install.sh.
#   <web origins>: comma-separated https origins of the web console (ACOS_CORS_ORIGINS).
#
# Starts PostgreSQL and the Cloudflare Tunnel if they are not running, then
# swaps the API container for <image>. If the new one does not answer /health
# with its own commit within the deadline, the previous image is put back and
# the deploy fails, so a bad release never stays serving.
#
# One API container at a time is a correctness limit, not a cost one: the
# curriculum and operations stores are SQLite files (CLAUDE.md, "Storage").
set -euo pipefail
IMAGE="$1"
export ACOS_CORS_ORIGINS="${2:?web origins (ACOS_CORS_ORIGINS) required}"
. /etc/academicos/stack.env
export AWS_REGION AWS_DEFAULT_REGION="$AWS_REGION"
ROOT=/opt/academicos
NET=acos
/opt/academicos-bin/render-env.sh
. /etc/academicos/infra.env

docker network inspect "$NET" >/dev/null 2>&1 || docker network create "$NET"

# ---------------------------------------------------------------- PostgreSQL
if [ -z "$(docker ps -q -f name=^db$)" ]; then
  docker rm -f db >/dev/null 2>&1 || true
  docker run -d --name db --network "$NET" --restart unless-stopped \
    --env-file /etc/academicos/db.env -v "$ROOT/pg:/var/lib/postgresql/data" \
    --memory 512m --shm-size 128m \
    --health-cmd 'pg_isready -U academicos' --health-interval 5s \
    postgres:16-alpine
fi
for _ in $(seq 1 60); do
  [ "$(docker inspect -f '{{.State.Health.Status}}' db)" = healthy ] && break; sleep 2
done
# Every statement in schema.sql is IF NOT EXISTS, so applying it on every deploy
# is how a table added to it reaches this database before the code that uses it
# (on GCP this was a manual step, scripts/apply_cloudsql_schema.sh, and a missed
# run left /health/storage at "schema_missing").
if ! out="$(docker exec -i db psql -v ON_ERROR_STOP=1 -q -U academicos academicos \
            <"$(dirname "$0")/schema.sql" 2>&1)"; then
  echo "$out" >&2; echo "schema.sql failed to apply" >&2; exit 1
fi

# ---------------------------------------------------------------- Cloudflare Tunnel
# The only way in from the internet. Restarted when its token changes.
if [ -n "${CLOUDFLARED_TOKEN:-}" ]; then
  want="$(printf '%s' "$CLOUDFLARED_TOKEN" | sha256sum | cut -c1-16)"
  have="$(docker inspect -f '{{index .Config.Labels "token"}}' cloudflared 2>/dev/null || true)"
  if [ "$want" != "$have" ] || [ -z "$(docker ps -q -f name=^cloudflared$)" ]; then
    docker rm -f cloudflared >/dev/null 2>&1 || true
    docker run -d --name cloudflared --network "$NET" --restart unless-stopped \
      --label "token=$want" -e TUNNEL_TOKEN="$CLOUDFLARED_TOKEN" \
      cloudflare/cloudflared:latest tunnel --no-autoupdate run
  fi
else
  echo "WARNING: /academicos/infra/cloudflared-token is not set; the API is not reachable from the internet" >&2
fi

# ---------------------------------------------------------------- API
aws ecr get-login-password | docker login --username AWS --password-stdin "${ECR_REPO%%/*}" >/dev/null
docker pull "$IMAGE"
want_commit="$(docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' "$IMAGE" | sed -n 's/^ACOS_BUILD_COMMIT=//p')"
previous="$(docker inspect -f '{{.Config.Image}}' app 2>/dev/null || true)"

start_app() {
  docker rm -f app >/dev/null 2>&1 || true
  # The corpus is baked into the image at /app/academicos-data; the school's
  # files live on the data volume at /data. Each start refreshes the corpus
  # copy (questions, syllabus, taxonomy) and leaves everything else alone.
  docker run -d --name app --network "$NET" --restart unless-stopped \
    --env-file /etc/academicos/app.env -v "$ROOT/data:/data" \
    -p 127.0.0.1:8080:8080 --memory 1200m \
    --log-opt max-size=20m --log-opt max-file=5 \
    "$1" sh -c 'cp -a /app/academicos-data/. /data/ && exec python -m academicos.cli serve --host 0.0.0.0 --port 8080'
}

healthy() {  # healthy <commit>
  for _ in $(seq 1 60); do
    body="$(curl -fsS -m 5 http://127.0.0.1:8080/health 2>/dev/null || true)"
    if [ -n "$body" ] && [ "$(echo "$body" | jq -r .commit 2>/dev/null)" = "$1" ]; then return 0; fi
    [ -z "$(docker ps -q -f name=^app$)" ] && return 1      # exited (production guard refused?)
    sleep 3
  done
  return 1
}

start_app "$IMAGE"
if healthy "$want_commit"; then
  echo "serving $want_commit"
  docker image prune -af --filter "until=168h" >/dev/null || true
  exit 0
fi
echo "NEW RELEASE FAILED its health check; last log lines:" >&2
docker logs --tail 60 app >&2 || true
if [ -n "$previous" ] && [ "$previous" != "$IMAGE" ]; then
  echo "rolling back to $previous" >&2
  start_app "$previous"
fi
exit 1
