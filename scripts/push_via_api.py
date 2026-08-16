"""One-off: push src/, config/, pyproject.toml, and a CI Dockerfile to a fresh
GitHub repo purely via the GitHub REST/Git Data API -- no local .git working
tree, so it works even with ~0 bytes of free local disk space (which is the
actual blocker: the C: drive is essentially full, unrelated to this repo).
"""
from __future__ import annotations

import base64
import subprocess
import sys
from pathlib import Path

import requests

REPO = "varshinicb1/academicos-backend"
ROOT = Path(r"C:\Users\varsh\OneDrive\Documents\Sarvam\AcademicOS")
API = "https://api.github.com"


def gh_token() -> str:
    return subprocess.check_output(["gh", "auth", "token"], text=True).strip()


TOKEN = gh_token()
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"}


def api(method: str, path: str, **kw):
    r = requests.request(method, f"{API}{path}", headers=HEADERS, timeout=30, **kw)
    if not r.ok:
        print("ERROR", r.status_code, r.text[:500], file=sys.stderr)
    r.raise_for_status()
    return r.json() if r.text else None


def collect_files() -> list[Path]:
    files = []
    for sub in ("src", "config"):
        for p in (ROOT / sub).rglob("*"):
            if p.is_file() and "__pycache__" not in p.parts:
                files.append(p)
    files.append(ROOT / "pyproject.toml")
    return files


def main() -> None:
    files = collect_files()
    print(f"{len(files)} files to push")

    tree_entries = []
    for i, f in enumerate(files):
        rel = f.relative_to(ROOT).as_posix()
        content = f.read_bytes()
        b64 = base64.b64encode(content).decode("ascii")
        blob = api("POST", f"/repos/{REPO}/git/blobs", json={"content": b64, "encoding": "base64"})
        tree_entries.append({"path": rel, "mode": "100644", "type": "blob", "sha": blob["sha"]})
        if (i + 1) % 25 == 0:
            print(f"  {i + 1}/{len(files)} blobs created")

    # CI-only Dockerfile: pulls academicos-data/ from the already-published
    # production image instead of needing it pushed through git (it's 1.3GB
    # of static CBSE corpus data that hasn't changed today).
    ci_dockerfile = """\
FROM varshinicb99/academicos-backend:v1 AS olddata

FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends \\
    libgl1 libglib2.0-0 fonts-dejavu-core \\
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml ./
COPY src/ ./src/
RUN pip install --no-cache-dir -e ".[api,mobile-scan]"
COPY config/ ./config/
COPY --from=olddata /app/academicos-data ./academicos-data
ENV PORT=8080
EXPOSE 8080
CMD ["sh", "-c", "python -m academicos.cli serve --host 0.0.0.0 --port ${PORT}"]
"""
    blob = api("POST", f"/repos/{REPO}/git/blobs",
               json={"content": base64.b64encode(ci_dockerfile.encode()).decode(), "encoding": "base64"})
    tree_entries.append({"path": "Dockerfile", "mode": "100644", "type": "blob", "sha": blob["sha"]})

    workflow = """\
name: Build and push backend image
on:
  workflow_dispatch: {}
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      - uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: varshinicb99/academicos-backend:v1
"""
    blob = api("POST", f"/repos/{REPO}/git/blobs",
               json={"content": base64.b64encode(workflow.encode()).decode(), "encoding": "base64"})
    tree_entries.append({"path": ".github/workflows/build-push.yml", "mode": "100644", "type": "blob",
                         "sha": blob["sha"]})

    print("creating tree...")
    tree = api("POST", f"/repos/{REPO}/git/trees", json={"tree": tree_entries})

    parent_ref = api("GET", f"/repos/{REPO}/git/refs/heads/main")
    parent_sha = parent_ref["object"]["sha"]

    print("creating commit...")
    commit = api("POST", f"/repos/{REPO}/git/commits", json={
        "message": "Backend source for CI Docker builds (local Docker unavailable: disk full)",
        "tree": tree["sha"],
        "parents": [parent_sha],
    })

    print("updating ref...")
    api("PATCH", f"/repos/{REPO}/git/refs/heads/main",
        json={"sha": commit["sha"], "force": True})

    print("DONE. Commit:", commit["sha"])


if __name__ == "__main__":
    main()
