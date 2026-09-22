# =============================================================================
# AcademicOS backend image.
#
# ONE image serves BOTH backend releases (see docs/PRODUCTS_AND_RELEASES.md):
#   * Render release  -- Render pulls this image from Docker Hub. Durability via
#                        Supabase, because ACOS_POSTGRES_* is not set there.
#   * GCP release     -- Cloud Build pushes this image to Artifact Registry and
#                        Cloud Run serves it, with ACOS_POSTGRES_* set so the
#                        stores bind to Cloud SQL instead.
# Which backend a running container uses is decided entirely by environment
# variables at runtime, never by the image. Neither release builds either
# client sub-product (Web / offline Android) from here.
# =============================================================================
FROM python:3.12-slim

# libgl1/libglib2.0-0: opencv-python-headless still dlopens libGL at import
# time even in headless mode, and python:slim doesn't ship it.
# --no-install-recommends (not --no-install-recurse-suggests, which this
# Debian trixie-based image's apt rejects outright) keeps the image lean.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml ./
COPY src/ ./src/
# postgres: the Cloud SQL durability backend (assessment/postgres_kv.py).
# gcs: Cloud Storage for scan media / curriculum snapshots.
# mcp: the question-bank MCP server (academicos.mcp.qbank_server). The image's
#   CMD runs `cli serve` only, so the SDK is not on the serving path -- but the
#   bank is sold as one product with two surfaces (PRD Q5), and an image that
#   cannot run `python -m academicos.mcp.qbank_server` ships half of it. The
#   sse/streamable-http transports also need [api]'s uvicorn, which is here.
RUN pip install --no-cache-dir -e ".[api,mcp,mobile-scan,postgres,gcs]"

COPY config/ ./config/

# Baked into the image, not mounted from a volume: neither release has a
# persistent disk, so without this the deployed backend starts with zero
# questions, chapters and templates -- an empty, useless API. Default
# ACOS_DATA_ROOT resolution (cwd()/academicos-data) picks this up as-is.
#
# Measured, not assumed: the tracked corpus is 6.5 MB, almost all of it
# syllabus/questions.json. (An earlier comment here claimed a "3.3 GB image
# mostly baked corpus" -- it was wrong on both counts: the corpus is 6.5 MB,
# and the pip layer is 463 MB, with no torch at all.)
COPY academicos-data/ ./academicos-data/

# Non-root. A numeric UID is used rather than useradd so the slim base needs
# no extra package. /app is chowned because the stores fall back to writing
# SQLite (users.db, assessments.db, scan sessions) under ACOS_DATA_ROOT
# whenever Cloud SQL and Supabase are both unreachable -- that has to work for
# a non-root process, and shipping a root container is the finding a security
# review stops on. Everything durable lives in Cloud SQL regardless; these
# files are per-instance scratch.
RUN chown -R 1001:1001 /app
ENV HOME=/tmp
USER 1001:1001

# Both releases inject the listen port via $PORT (Render and Cloud Run both
# default to 8080) -- the app must bind to whatever is sent, not to a value
# baked into the image.
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "python -m academicos.cli serve --host 0.0.0.0 --port ${PORT}"]
