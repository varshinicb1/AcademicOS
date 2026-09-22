#!/usr/bin/env python
"""Copy the blob data (curriculum snapshot, scan media) from Supabase Storage to GCS.

The companion of migrate_supabase_to_cloudsql.py, which moves the JSONB
tables. Before the GCP deploy dropped its Supabase secrets, the service kept
two kinds of blob in Supabase Storage (storage/blobs.py): the curriculum
store's whole-file SQLite snapshot and scan-session photos/PDFs. After it,
both are read from GCS -- where, until this script runs, neither exists:

  * the curriculum store would find no snapshot. It now refuses to boot empty
    on GCS unless ACOS_CURRICULUM_ALLOW_EMPTY_BOOT=1 (storage/snapshot_sync.py
    `SnapshotSync._restore`), so the service fails loudly instead of serving
    a blank curriculum as if it were the school's.
  * every scan artifact captured before the cutover would read back as "not
    found" (mobile_scan.fetch_storage_bytes returns None).

Run it ONCE, before the first deploy without the Supabase secrets (or right
after, while that deploy is failing its startup on the empty-boot guard).

Usage
-----
    python scripts/migrate_supabase_blobs_to_gcs.py --dry-run
    python scripts/migrate_supabase_blobs_to_gcs.py

Reads (env):
    SUPABASE_KNOWLEDGE_URL, SUPABASE_KNOWLEDGE_ANON_KEY   -- source
    ACOS_GCS_BUCKET (+ optional ACOS_GCS_PREFIX)           -- destination,
        the same values the Cloud Run service gets, so objects land exactly
        where durable_blob_store() will look; Application Default Credentials.

Safety:
  * The curriculum snapshot is uploaded with if_generation_match=0 ("only if
    absent"). If GCS already has one -- the service booted and an admin has
    been editing there -- it is left untouched and reported: overwriting it
    would erase those edits. Resolve by hand.
  * Every copied object is read back from GCS and compared byte for byte; a
    mismatch or a failure makes the exit status non-zero.
  * Scan media is keyed per session, so re-running converges (same key, same
    bytes).
"""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterator

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from academicos.storage import blobs  # noqa: E402

SNAPSHOT_BUCKET = "curriculum-snapshots"
SNAPSHOT_KEY = "curriculum.sqlite"      # CurriculumStore._SNAPSHOT_KEY
SCAN_BUCKET = "scan-media"
LIST_PAGE = 100                          # Supabase Storage's list page cap


class SupabaseBlobSource:
    """Read side of Supabase Storage: list a bucket recursively, download.

    Supabase's list endpoint returns one "folder" level per call, with folders
    as entries whose `id` is null, so listing recurses. `session` is
    injectable so the tests never reach a network."""

    def __init__(self, url: str, key: str, session: Any = requests):
        self.url = url.rstrip("/")
        self._headers = {"apikey": key, "Authorization": f"Bearer {key}"}
        self._session = session

    def list_keys(self, bucket: str, prefix: str = "") -> Iterator[str]:
        offset = 0
        while True:
            r = self._session.post(
                f"{self.url}/storage/v1/object/list/{bucket}",
                json={"prefix": prefix, "limit": LIST_PAGE, "offset": offset,
                      "sortBy": {"column": "name", "order": "asc"}},
                headers=self._headers, timeout=60)
            r.raise_for_status()
            page = r.json()
            for item in page:
                name = f"{prefix}/{item['name']}" if prefix else item["name"]
                if item.get("id") is None:          # a folder
                    yield from self.list_keys(bucket, name)
                else:
                    yield name
            if len(page) < LIST_PAGE:
                return
            offset += LIST_PAGE

    def download(self, bucket: str, key: str) -> bytes:
        r = self._session.get(f"{self.url}/storage/v1/object/{bucket}/{key}",
                              headers=self._headers, timeout=120)
        r.raise_for_status()
        return r.content


@dataclass
class Report:
    copied: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.failed


def _content_type(key: str) -> str:
    low = key.lower()
    if low.endswith(".pdf"):
        return "application/pdf"
    if low.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if low.endswith(".png"):
        return "image/png"
    if low.endswith(".json"):
        return "application/json"
    return "application/octet-stream"


def copy_curriculum_snapshot(source: SupabaseBlobSource,
                             dest_factory: Callable[[], Any],
                             *, dry_run: bool = False) -> Report:
    """`dest_factory()` builds a fresh blob store each call (the read-back
    must not trust the writer's in-memory generation)."""
    report = Report()
    try:
        data = source.download(SNAPSHOT_BUCKET, SNAPSHOT_KEY)
    except requests.exceptions.RequestException as exc:
        if blobs.is_not_found(exc):
            print("    no curriculum snapshot in Supabase Storage: nothing to copy. "
                  "If this school genuinely has no curriculum yet, deploy once with "
                  "ACOS_CURRICULUM_ALLOW_EMPTY_BOOT=1.")
            report.skipped.append(SNAPSHOT_KEY)
            return report
        print(f"    FAILED reading the Supabase snapshot: {exc}")
        report.failed.append(SNAPSHOT_KEY)
        return report
    if not data.startswith(b"SQLite format 3"):
        print(f"    FAILED: the Supabase object is not a SQLite file ({len(data)} bytes)")
        report.failed.append(SNAPSHOT_KEY)
        return report
    if dry_run:
        print(f"    would copy {SNAPSHOT_KEY} ({len(data)} bytes)")
        report.copied.append(SNAPSHOT_KEY)
        return report

    dest = dest_factory()
    try:
        # Guarded store, key never seen by it: if_generation_match=0.
        dest.upload(SNAPSHOT_KEY, data, "application/x-sqlite3")
    except blobs.BlobConflict:
        print("    SKIPPED: GCS already holds a curriculum snapshot. The service has "
              "booted and may have written to it; overwriting would erase those "
              "edits. Compare the two by hand.")
        report.skipped.append(SNAPSHOT_KEY)
        return report
    except requests.exceptions.RequestException as exc:
        print(f"    FAILED writing the snapshot to GCS: {exc}")
        report.failed.append(SNAPSHOT_KEY)
        return report
    _verify(dest_factory(), SNAPSHOT_KEY, data, report)
    return report


def copy_scan_media(source: SupabaseBlobSource, dest_factory: Callable[[], Any],
                    *, dry_run: bool = False) -> Report:
    report = Report()
    try:
        keys = list(source.list_keys(SCAN_BUCKET))
    except requests.exceptions.RequestException as exc:
        print(f"    FAILED listing Supabase bucket {SCAN_BUCKET!r}: {exc}")
        report.failed.append("<list>")
        return report
    print(f"    {len(keys)} object(s) in Supabase {SCAN_BUCKET!r}")
    dest = dest_factory()
    for key in keys:
        try:
            data = source.download(SCAN_BUCKET, key)
        except requests.exceptions.RequestException as exc:
            print(f"    FAILED reading {key}: {exc}")
            report.failed.append(key)
            continue
        if dry_run:
            report.copied.append(key)
            continue
        try:
            dest.upload(key, data, _content_type(key))
        except requests.exceptions.RequestException as exc:
            print(f"    FAILED writing {key}: {exc}")
            report.failed.append(key)
            continue
        _verify(dest, key, data, report)
    verb = "would copy" if dry_run else "copied"
    print(f"    {verb} {len(report.copied)}, failed {len(report.failed)}")
    return report


def _verify(dest: Any, key: str, data: bytes, report: Report) -> None:
    """Read back rather than trust the write."""
    try:
        back = dest.download(key)
    except requests.exceptions.RequestException as exc:
        print(f"    FAILED read-back of {key}: {exc}")
        report.failed.append(key)
        return
    if back != data:
        print(f"    FAILED: {key} read back {len(back)} bytes, sent {len(data)}")
        report.failed.append(key)
        return
    report.copied.append(key)


def main(argv: list[str] | None = None, *, session: Any = requests,
         gcs_client: Any = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="read and report, write nothing")
    ap.add_argument("--only", choices=["curriculum", "scan-media"], default=None)
    args = ap.parse_args(argv)

    url = os.environ.get("SUPABASE_KNOWLEDGE_URL", "").strip()
    key = os.environ.get("SUPABASE_KNOWLEDGE_ANON_KEY", "").strip()
    if not (url and key):
        raise SystemExit("ERROR: SUPABASE_KNOWLEDGE_URL / SUPABASE_KNOWLEDGE_ANON_KEY "
                         "must be set to read the source blobs.")
    if blobs.blob_backend() != "gcs":
        raise SystemExit("ERROR: ACOS_GCS_BUCKET must name the service's media bucket.")

    source = SupabaseBlobSource(url, key, session=session)
    reports: list[Report] = []
    if args.only in (None, "curriculum"):
        print(f"\n== {SNAPSHOT_BUCKET}/{SNAPSHOT_KEY}")
        reports.append(copy_curriculum_snapshot(
            source, lambda: blobs.durable_blob_store(SNAPSHOT_BUCKET, gcs_client=gcs_client),
            dry_run=args.dry_run))
    if args.only in (None, "scan-media"):
        print(f"\n== {SCAN_BUCKET}")
        reports.append(copy_scan_media(
            source, lambda: blobs.durable_blob_store(SCAN_BUCKET, gcs_client=gcs_client),
            dry_run=args.dry_run))

    failed = sum(len(r.failed) for r in reports)
    if failed:
        print(f"\n{failed} object(s) FAILED; re-run after fixing the cause (safe to re-run).")
        return 1
    print("\nDone. Next: deploy, then check /health/storage (blob_backend=gcs) and "
          "that the curriculum screens show the school's data.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
