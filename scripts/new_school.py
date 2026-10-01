"""Onboard a new school: create the single-use invite for its first principal
on the live site and print the link to send them.

    python scripts/new_school.py "St Mary's School, Hyderabad"
    python scripts/new_school.py "St Mary's School" --id stmarys-hyd --days 14

The principal opens the link, which fills in Create account, and types only
their name, email and a password. They then invite their teachers from Setup,
Invite people.

The operator key is read from Secret Manager with your own gcloud login and is
never printed, written to disk or put in a URL.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request

LIVE_API = "https://academicos-backend-2eskom55ta-el.a.run.app/api/v1"


def slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s[:60].strip("-")


def operator_key(project: str) -> str:
    out = subprocess.run(
        ["gcloud", "secrets", "versions", "access", "latest", "--secret=principal-bootstrap-key",
         f"--project={project}"],
        capture_output=True, text=True, shell=sys.platform == "win32")
    if out.returncode != 0:
        sys.exit("could not read the operator key from Secret Manager -- run `gcloud auth login` first")
    return out.stdout.strip()


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("name", help="the school's name, used for the school ID unless --id is given")
    p.add_argument("--id", help="the school ID (3-60 lowercase letters, digits and hyphens)")
    p.add_argument("--days", type=int, default=14, help="how long the link works (1-90, default 14)")
    p.add_argument("--api", default=LIVE_API)
    p.add_argument("--project", default="vidyuthlabs")
    args = p.parse_args()
    school_id = args.id or slug(args.name)
    req = urllib.request.Request(
        f"{args.api}/auth/operator/school-invites", method="POST",
        data=json.dumps({"schoolId": school_id, "expiresInDays": args.days}).encode(),
        headers={"Content-Type": "application/json", "X-Operator-Key": operator_key(args.project)})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = json.loads(r.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        sys.exit(f"refused ({e.code}): {detail}")
    print(f"\nSchool:   {args.name}")
    print(f"School ID: {body['schoolId']}")
    print(f"Expires:  {body['expiresAt'][:10]} (works once)")
    print(f"\nSend this link to the principal:\n\n  {body['link']}\n")
    print("They open it, enter their name, email and a password, and are the school's principal.")
    print("Then: Setup > Invite people > 'Copy invite link' for each teacher.\n")


if __name__ == "__main__":
    main()
