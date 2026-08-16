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

# Baked into the image, not mounted from a volume: this Cloud Run deploy has
# no persistent disk, so without this the deployed backend would start with
# zero questions/chapters/templates — an empty, useless API. Default
# ACOS_DATA_ROOT resolution (cwd()/academicos-data) picks this up as-is.
COPY academicos-data/ ./academicos-data/

# Cloud Run injects the listen port via $PORT (default 8080) — the app must
# bind to whatever it sends, not a value baked into the image.
ENV PORT=8080
EXPOSE 8080

# NOTE: this only solves READ access to the pre-existing corpus. Anything
# written at runtime — new assessments, scan sessions, evaluations — still
# lives only in the container's ephemeral filesystem and is lost on every
# redeploy or cold start. Fine for an initial POC; a real deployment needs
# a persistent store (Cloud SQL, GCS-backed volume, etc.) before this is
# used for actual student data.
CMD ["sh", "-c", "python -m academicos.cli serve --host 0.0.0.0 --port ${PORT}"]
