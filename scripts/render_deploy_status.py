"""Check the latest Render deploy for an image-backed service.

Works for services that Render does NOT build from a Git repo (image-backed):
Render has no commit info for such services, so this answers "is the newest
deploy live?" rather than "is commit X live?".

Usage:
    python scripts/render_deploy_status.py --service-id srv-xxxx --no-wait
    python scripts/render_deploy_status.py --service-id srv-xxxx --wait 600
    python scripts/render_deploy_status.py --service-id srv-xxxx --print-latest-id
    python scripts/render_deploy_status.py --service-id srv-xxxx \
        --after dep-xxxx --wait 1800

    --after dep-xxxx waits until a deploy NEWER than dep-xxxx exists and goes
    live. Needed when a deploy is triggered indirectly (e.g. a CI pipeline
    builds an image, Render then starts the deploy): right after the trigger,
    the latest deploy is still the old one, and "is it live?" would
    false-positive on it.

Env:
    RENDER_API_KEY  (required)

Exit codes:
    0  latest deploy is live (immediately or within --wait)
    1  latest deploy failed, was canceled/deactivated, or API error
    2  still in progress when --wait elapsed (or --no-wait and not yet live)
"""

from __future__ import annotations

import argparse
import os
import sys
import time

import requests

API = "https://api.render.com/v1"

TERMINAL_OK = {"live"}
TERMINAL_BAD = {"build_failed", "update_failed", "canceled", "deactivated"}
HUMAN = {
    "created": "queued",
    "queued": "queued",
    "build_in_progress": "building",
    "pre_deploy_in_progress": "pre-deploy",
    "update_in_progress": "rolling out",
}


def fetch_latest_deploy(service_id: str, api_key: str) -> dict:
    resp = requests.get(
        f"{API}/services/{service_id}/deploys",
        params={"limit": 1},
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
        timeout=30,
    )
    if resp.status_code == 401:
        raise RuntimeError("Render API rejected the key (401): check RENDER_API_KEY")
    if resp.status_code == 404:
        raise RuntimeError(f"Service {service_id} not found (404): check the service ID")
    resp.raise_for_status()
    deploys = resp.json()
    if not deploys:
        raise RuntimeError(f"Service {service_id} has no deploys yet")
    return deploys[0]["deploy"]


def describe(deploy: dict) -> str:
    status = deploy.get("status", "unknown")
    label = HUMAN.get(status, status)
    last_event = deploy.get("finishedAt") or deploy.get("startedAt") or deploy.get("createdAt")
    return f"{deploy.get('id', '?')} status={status} ({label}), last event {last_event}"


def poll(service_id: str, api_key: str, after_id: str | None, timeout_s: int, interval_s: int) -> int:
    deadline = time.monotonic() + timeout_s
    while True:
        deploy = fetch_latest_deploy(service_id, api_key)
        if after_id and deploy.get("id") == after_id:
            print(f"[render] {time.strftime('%H:%M:%S')} no new deploy yet (latest is {after_id})", flush=True)
            if time.monotonic() >= deadline:
                print(f"[render] no deploy newer than {after_id} appeared within {timeout_s}s")
                return 2
            time.sleep(interval_s)
            continue
        status = deploy.get("status", "unknown")
        print(f"[render] {time.strftime('%H:%M:%S')} {describe(deploy)}", flush=True)
        if status in TERMINAL_OK:
            print("[render] latest deploy is live -> OK")
            return 0
        if status in TERMINAL_BAD:
            print(f"[render] deploy reached terminal failure: {status}")
            return 1
        if time.monotonic() >= deadline:
            print(f"[render] still '{status}' after {timeout_s}s")
            return 2
        time.sleep(interval_s)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--service-id", required=True, help="Render service ID (srv-...)")
    parser.add_argument("--wait", type=int, default=600, help="Max seconds to wait for live (default 600)")
    parser.add_argument("--interval", type=int, default=20, help="Seconds between polls (default 20)")
    parser.add_argument("--no-wait", action="store_true", help="Check once and exit (exit 2 if not live)")
    parser.add_argument("--after", default=None, metavar="DEPLOY_ID",
                        help="Wait for a deploy newer than this ID to go live (see docstring)")
    parser.add_argument("--print-latest-id", action="store_true",
                        help="Print the latest deploy ID and exit (exit 2 if not live)")
    args = parser.parse_args()

    api_key = os.environ.get("RENDER_API_KEY")
    if not api_key:
        print("error: RENDER_API_KEY is not set", file=sys.stderr)
        return 1

    try:
        deploy = fetch_latest_deploy(args.service_id, api_key)
        if args.print_latest_id:
            print(deploy["id"])
            return 0
        if args.no_wait:
            print(f"[render] latest deploy: {describe(deploy)}")
            status = deploy.get("status", "unknown")
            if status in TERMINAL_OK:
                return 0
            return 1 if status in TERMINAL_BAD else 2
        return poll(args.service_id, api_key, args.after, args.wait, args.interval)
    except requests.RequestException as exc:
        print(f"error: Render API request failed: {exc}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
