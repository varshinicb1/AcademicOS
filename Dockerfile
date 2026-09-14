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
RUN pip install --no-cache-dir -e ".[api,mobile-scan]"

COPY config/ ./config/

# Baked into the image, not mounted from a volume: this Render deploy has
# no persistent disk (Render's free web-service tier wipes local disk on
# every redeploy/restart/spin-down, SQLite files included), so without
# this the deployed backend would start with zero questions/chapters/
# templates — an empty, useless API. Default ACOS_DATA_ROOT resolution
# (cwd()/academicos-data) picks this up as-is.
#
# Corrected 2026-09-15: earlier comments here said "Cloud Run" -- stale
# from an earlier deploy target that was never the one actually shipped.
# The real, live target is Render (academicos-backend.onrender.com, kept
# warm by .github/workflows/keep-backend-warm.yml, deployed via
# .github/workflows/deploy-backend.yml's test -> sync -> Docker Hub ->
# Render pipeline). A stale fly.toml also exists at the repo root from
# another earlier attempt -- not the active deploy either; see
# docs/deployment.md.
COPY academicos-data/ ./academicos-data/

# Render injects the listen port via $PORT (default 8080, matching
# render.yaml/dashboard config) — the app must bind to whatever it sends,
# not a value baked into the image.
ENV PORT=8080
EXPOSE 8080

# This only solves READ access to the pre-existing baked-in corpus.
# Anything written at runtime that needs to survive a redeploy/restart --
# new assessments, grades, scan sessions, curriculum edits -- now goes
# through the Supabase-backed durability path instead (SupabaseTable
# per-row for the flat stores, whole-file snapshot/restore for
# CurriculumStore) when SUPABASE_KNOWLEDGE_URL/SUPABASE_KNOWLEDGE_ANON_KEY
# are set on the Render service -- see AGENTS.md's storage inventory and
# docs/deployment.md. Without those env vars set, this reverts to the
# original POC behavior: runtime writes are ephemeral again.
CMD ["sh", "-c", "python -m academicos.cli serve --host 0.0.0.0 --port ${PORT}"]
