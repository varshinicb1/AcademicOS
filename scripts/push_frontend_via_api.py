"""Same technique as push_via_api.py: push Flutter source to a fresh GitHub
repo purely via the Git Data API (no local .git working tree, no local disk
needed beyond reading the existing files) -- the C: drive is essentially
full, so a normal `git push` isn't reliable right now.
"""
from __future__ import annotations

import base64
import subprocess
import sys
from pathlib import Path

import requests

REPO = "varshinicb1/academicos-frontend-src"
ROOT = Path(r"C:\Users\varsh\OneDrive\Documents\Sarvam\AcademicOS\frontend")
API = "https://api.github.com"

SKIP_DIRS = {".dart_tool", "build", ".git", "android", "ios", "linux", "macos", "windows",
            "test", ".idea"}


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
    for sub in ("lib", "web"):
        base = ROOT / sub
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.is_file() and not any(part in SKIP_DIRS for part in p.parts):
                files.append(p)
    for name in ("pubspec.yaml", "pubspec.lock", "analysis_options.yaml"):
        p = ROOT / name
        if p.exists():
            files.append(p)
    return files


def main() -> None:
    files = collect_files()
    print(f"{len(files)} files to push")

    api("PUT", f"/repos/{REPO}/contents/README.md",
        json={"message": "init", "content": base64.b64encode(b"init").decode()})

    tree_entries = []
    for i, f in enumerate(files):
        rel = f.relative_to(ROOT).as_posix()
        content = f.read_bytes()
        b64 = base64.b64encode(content).decode("ascii")
        blob = api("POST", f"/repos/{REPO}/git/blobs", json={"content": b64, "encoding": "base64"})
        tree_entries.append({"path": rel, "mode": "100644", "type": "blob", "sha": blob["sha"]})
        if (i + 1) % 20 == 0:
            print(f"  {i + 1}/{len(files)} blobs created")

    workflow = """\
name: Build and deploy web frontend
on:
  workflow_dispatch: {}
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: subosito/flutter-action@v2
        with:
          channel: stable
      - run: flutter pub get
      - run: dart run build_runner build --delete-conflicting-outputs
      - run: |
          flutter build web --release \\
            --base-href=/academicos-frontend/ \\
            --dart-define=ACADEMICOS_API=https://academicos-backend.onrender.com/api/v1
      - name: Deploy to academicos-frontend (Pages)
        run: |
          cd build/web
          git init -q
          git config user.email "ci@academicos"
          git config user.name "AcademicOS CI"
          git checkout -q -b master
          git add -A
          git commit -q -m "Deploy $(date -u +%Y-%m-%dT%H:%M:%SZ) (source ${{ github.sha }})"
          git remote add origin https://x-access-token:${{ secrets.DEPLOY_PAT }}@github.com/varshinicb1/academicos-frontend.git
          git push -f origin master
"""
    blob = api("POST", f"/repos/{REPO}/git/blobs",
               json={"content": base64.b64encode(workflow.encode()).decode(), "encoding": "base64"})
    tree_entries.append({"path": ".github/workflows/build-deploy.yml", "mode": "100644", "type": "blob",
                         "sha": blob["sha"]})

    print("creating tree...")
    tree = api("POST", f"/repos/{REPO}/git/trees", json={"tree": tree_entries})

    parent_ref = api("GET", f"/repos/{REPO}/git/refs/heads/main")
    parent_sha = parent_ref["object"]["sha"]

    print("creating commit...")
    commit = api("POST", f"/repos/{REPO}/git/commits", json={
        "message": "Flutter web source for CI builds (local disk full)",
        "tree": tree["sha"],
        "parents": [parent_sha],
    })

    print("updating ref...")
    api("PATCH", f"/repos/{REPO}/git/refs/heads/main", json={"sha": commit["sha"], "force": True})

    print("DONE. Commit:", commit["sha"])


if __name__ == "__main__":
    main()
