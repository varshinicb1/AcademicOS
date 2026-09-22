#!/usr/bin/env python
"""Move live data from Supabase PostgREST into Cloud SQL (Postgres).

Run this ONCE, between provisioning Cloud SQL and removing the Supabase env
vars from the Cloud Run service. Until you run it, the deployed service keeps
reading and writing Supabase and Cloud SQL just sits idle, so there is no
window where the app is pointing at an empty database.

Why it does not reuse ``SupabaseTable``
--------------------------------------
``SupabaseTable.select()`` has no offset, and PostgREST caps a single response
at the project's ``max-rows`` (1000 by default on Supabase). Paging through a
real school's data with only ``limit`` would silently stop at row 1000. This
script talks to the REST endpoint directly so it can page with
``limit`` + ``offset``, and reports the counts it saw so a short read is
visible rather than assumed.

Usage
-----
    # from the repo root, with the venv active
    python scripts/migrate_supabase_to_cloudsql.py --dry-run
    python scripts/migrate_supabase_to_cloudsql.py

Reads (env):
    SUPABASE_KNOWLEDGE_URL, SUPABASE_KNOWLEDGE_ANON_KEY   -- source
    ACOS_POSTGRES_HOST/PORT/DB/USER/PASSWORD              -- destination

Safe to re-run: every write is an upsert on the table's primary key, so a
second run converges rather than duplicating.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from academicos.assessment import postgres_kv  # noqa: E402
from academicos.assessment.postgres_kv import PostgresTable  # noqa: E402

PAGE_SIZE = 1000

# table -> primary key spec (must match both schema.sql and each store's
# on_conflict= argument), plus the columns the Cloud SQL schema defines.
TABLES: dict[str, dict[str, Any]] = {
    "assessments": {
        "conflict": "id",
        "columns": ["id", "school_id", "teacher_id", "created_at", "payload"],
    },
    "papers": {"conflict": "id", "columns": ["id", "payload"]},
    "practice_sets": {"conflict": "id", "columns": ["id", "payload"]},
    "scan_sessions": {
        "conflict": "id", "columns": ["id", "assessment_id", "payload"],
    },
    "graded_evaluations": {
        "conflict": "assessment_id,student_id",
        "columns": ["assessment_id", "student_id", "payload"],
    },
    "users": {
        "conflict": "id",
        "columns": ["id", "school_id", "name", "email", "password_hash",
                    "password_salt", "role", "created_at"],
    },
    "sessions": {
        "conflict": "token",
        "columns": ["token", "user_id", "created_at", "expires_at"],
    },
    "invites": {
        "conflict": "code",
        "columns": ["code", "school_id", "role", "email", "created_by", "created_at",
                    "expires_at", "used_by", "used_at", "revoked_at"],
    },
    "audit_log": {
        "conflict": "id",
        # seq/prev_hash/entry_hash: the hash chain (audit_log.py). Dropping
        # them in transit would turn every migrated entry into an unchained
        # legacy row that verify_chain() can no longer check.
        "columns": ["id", "timestamp", "action", "assessment_id", "student_id",
                    "actor", "details", "seq", "prev_hash", "entry_hash"],
    },
    "school_templates": {
        "conflict": "id", "columns": ["id", "school_id", "is_default", "payload"],
    },
    "learner_events": {
        "conflict": "event_id",
        "columns": ["learner_id", "seq", "event_id", "kind", "concept_id",
                    "outcome", "bloom", "difficulty", "affect", "duration_sec",
                    "ts", "payload"],
    },
    "parental_consents": {
        "conflict": "school_id,student_id",
        "columns": ["id", "school_id", "student_id", "guardian_name",
                    "guardian_relationship", "method", "status", "purpose",
                    "notes", "recorded_by", "recorded_at", "revoked_at",
                    "revoked_by"],
    },
}


def _source() -> tuple[str, dict[str, str]]:
    import os
    url = os.environ.get("SUPABASE_KNOWLEDGE_URL", "").strip().rstrip("/")
    key = os.environ.get("SUPABASE_KNOWLEDGE_ANON_KEY", "").strip()
    if not (url and key):
        raise SystemExit(
            "ERROR: SUPABASE_KNOWLEDGE_URL / SUPABASE_KNOWLEDGE_ANON_KEY must be "
            "set to read the source data."
        )
    return url, {"apikey": key, "Authorization": f"Bearer {key}"}


def _fetch_all(url: str, headers: dict[str, str], table: str) -> list[dict[str, Any]]:
    """Page the whole table. PostgREST reports the true total via
    Content-Range when asked for an exact count."""
    rows: list[dict[str, Any]] = []
    offset = 0
    while True:
        r = requests.get(
            f"{url}/rest/v1/{table}",
            headers={**headers, "Range-Unit": "items",
                     "Range": f"{offset}-{offset + PAGE_SIZE - 1}",
                     "Prefer": "count=exact"},
            params={"select": "*", "order": "1.asc"},
            timeout=60,
        )
        if r.status_code == 416:  # range past the end of the table
            break
        if not r.ok:
            raise SystemExit(
                f"ERROR: reading {table!r} from Supabase failed "
                f"(HTTP {r.status_code}): {r.text[:300]}"
            )
        page = r.json()
        if not page:
            break
        rows.extend(page)
        if len(page) < PAGE_SIZE:
            break
        offset += PAGE_SIZE

    declared = r.headers.get("Content-Range", "")
    if declared and "/" in declared:
        total = declared.rsplit("/", 1)[-1].strip()
        if total.isdigit() and int(total) != len(rows):
            print(f"    !! {table}: fetched {len(rows)} of {total} declared rows")
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true",
                    help="read and report, write nothing")
    ap.add_argument("--only", nargs="*", default=None,
                    help="restrict to these tables")
    args = ap.parse_args()

    if not postgres_kv.postgres_configured():
        raise SystemExit(
            "ERROR: Cloud SQL is not configured. Set ACOS_POSTGRES_HOST, "
            "ACOS_POSTGRES_DB, ACOS_POSTGRES_USER and ACOS_POSTGRES_PASSWORD."
        )

    url, headers = _source()
    tables = args.only or list(TABLES)
    unknown = [t for t in tables if t not in TABLES]
    if unknown:
        raise SystemExit(f"ERROR: unknown table(s): {', '.join(unknown)}")

    total_rows = 0
    for table in tables:
        spec = TABLES[table]
        print(f"\n== {table}")
        try:
            rows = _fetch_all(url, headers, table)
        except requests.exceptions.RequestException as exc:
            print(f"    source unreachable, skipping: {exc}")
            continue

        if not rows:
            print("    (empty)")
            continue

        allowed = set(spec["columns"])
        kept: list[dict[str, Any]] = []
        dropped: set[str] = set()
        for row in rows:
            extra = set(row) - allowed
            if extra:
                dropped |= extra
            kept.append({k: v for k, v in row.items() if k in allowed})
        if dropped:
            print(f"    note: ignoring columns not in the Cloud SQL schema: "
                  f"{', '.join(sorted(dropped))}")

        if args.dry_run:
            print(f"    would upsert {len(kept)} row(s)")
            total_rows += len(kept)
            continue

        target = PostgresTable(table)
        written = 0
        for row in kept:
            try:
                target.upsert(row, on_conflict=spec["conflict"])
                written += 1
            except Exception as exc:  # noqa: BLE001 - report and continue
                print(f"    FAILED on {row.get(spec['conflict'].split(',')[0])!r}: {exc}")

        # Verify by reading back, rather than trusting the write count.
        back = len(target.select())
        status = "ok" if back >= len(kept) else "SHORT"
        print(f"    {status}: wrote {written}, source {len(kept)}, destination now {back}")
        total_rows += written

    verb = "would migrate" if args.dry_run else "migrated"
    print(f"\n{verb} {total_rows} row(s) across {len(tables)} table(s).")
    if not args.dry_run:
        print("Next: verify with the service's /health/storage, then remove the "
              "SUPABASE_* env vars from the Cloud Run service to cut over.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
