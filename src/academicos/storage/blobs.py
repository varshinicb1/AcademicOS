"""One factory for the app's blob stores, mirroring postgres_kv.durable_table.

Two call sites keep binary blobs that are school data: scan-session photos and
PDFs (assessment/mobile_scan.py, name "scan-media") and the curriculum store's
whole-file SQLite snapshot (curriculum/store.py, name "curriculum-snapshots").
Both were built against SupabaseStorage's three-member interface -- `enabled`,
`upload(key, data, content_type)`, `download(key) -> bytes` -- and
`durable_blob_store(name)` returns an object with exactly that interface, so
neither call site changes beyond its constructor line.

Precedence, in order:
  1. GCS, when ACOS_GCS_BUCKET is set. On Cloud Run the container disk is
     wiped on every redeploy and scale-to-zero, so this is the only backend
     under which a GCP deployment keeps these blobs at all.
  2. SupabaseStorage, when the Supabase credentials are set (the Render path).
  3. Otherwise the same SupabaseStorage object, disabled. That is the "local"
     backend: both call sites already treat `enabled is False` as "keep the
     file on local disk only", which is the right behaviour for development.
     Returning the disabled object rather than a new local class keeps the
     existing tests that poke `_url`/`_key` on it working unchanged.

Only the environment variable selects GCS -- not config/config.toml's
`gcs_bucket`. That TOML value names a developer bucket for the CLI corpus
sync (cli.py `sync`); reading it here would send every local run's scan
photos into it, or crash on machines without the `gcs` extra.

Objects live under `<ACOS_GCS_PREFIX or "academicos">/<name>/<key>`, one
prefix per purpose, so a bucket lifecycle or IAM rule can target scan media
without touching the snapshots.

Single writer for the curriculum snapshot
-----------------------------------------
The snapshot is ONE object holding the whole SQLite file. If two Cloud Run
instances each hold a local copy, each debounced upload replaces the other's
object wholesale: whatever the other instance wrote since it last restored is
gone, silently. deploy-gcp.yml pins the service to one instance for that
reason; this module is the second line of defence. A store created with
`guard_generations=True` remembers the GCS generation of every object it read
or wrote and uploads with `if_generation_match` set to it (0 -- "must not
exist" -- for an object it never saw). A snapshot someone else wrote in the
meantime therefore fails with HTTP 412, and the upload raises BlobConflict,
logged at ERROR, instead of erasing it. CurriculumStore catches it as a
RequestException like any other failed upload, so the teacher's request still
succeeds; the instance's own later writes stay on its local disk until it is
restarted and restores the newer snapshot. Refusing is the lesser loss: the
alternative destroys the other instance's writes with no trace at all.
"""
from __future__ import annotations

import contextlib
import logging
import os
import threading
from typing import Optional

import requests

from ..config import credential_or_none

logger = logging.getLogger(__name__)

# The names the call sites use; the snapshot store is the only one that needs
# the single-writer precondition (scan keys are unique per session, and a
# re-captured page must overwrite its own earlier upload).
_GUARDED = frozenset({"curriculum-snapshots"})


class BlobUnavailable(requests.exceptions.RequestException):
    """A GCS read or write failed, or the object does not exist.

    A RequestException subclass on purpose, like SupabaseUnavailable: the call
    sites were written against SupabaseStorage, whose failures are requests
    errors, and curriculum/store.py catches exactly that type on both its
    restore and its snapshot path."""


class BlobConflict(BlobUnavailable):
    """A guarded upload was refused: the object changed since this process
    last read or wrote it (GCS precondition failure, HTTP 412)."""


def _gcs_bucket() -> Optional[str]:
    return credential_or_none("ACOS_GCS_BUCKET")


def _is_precondition_failure(exc: BaseException) -> bool:
    # google.api_core.exceptions.PreconditionFailed carries code 412; matched
    # by code rather than by import so this module works without the extra.
    return getattr(exc, "code", None) == 412


class GcsBlobStore:
    """SupabaseStorage's interface over storage/gcs.py's GcsStore."""

    backend = "gcs"
    enabled = True

    def __init__(self, name: str, *, bucket: str, prefix: str,
                 client=None, guard_generations: bool = False):
        from .gcs import GcsStore

        self.name = name
        self._store = GcsStore(bucket, prefix=f"{prefix.strip('/')}/{name}", client=client)
        self._guard = guard_generations
        # key -> generation this process last read (0 = saw it absent) or wrote.
        self._generations: dict[str, int] = {}
        # Guarded stores serialize read-modify-write of _generations; scan
        # media does not need it, and must not queue 40 concurrent requests'
        # photo uploads behind one lock.
        self._lock = threading.Lock() if guard_generations else contextlib.nullcontext()

    def upload(self, key: str, data: bytes, content_type: str) -> None:
        with self._lock:
            expected = self._generations.get(key, 0) if self._guard else None
            try:
                generation = self._store.put_bytes(
                    key, data, content_type, if_generation_match=expected)
            except Exception as exc:
                if self._guard and _is_precondition_failure(exc):
                    logger.error(
                        "REFUSED to overwrite gs://%s/%s: it changed since this "
                        "instance loaded generation %s, so another instance wrote "
                        "it. Keeping the newer object; this instance's writes stay "
                        "local until it restarts and restores. More than one "
                        "instance is running against the %s store -- check "
                        "--max-instances.",
                        self._store.bucket.name, self._store._key(key), expected,
                        self.name)
                    raise BlobConflict(
                        f"refused to overwrite {self.name}/{key}: changed since "
                        f"generation {expected}") from exc
                raise BlobUnavailable(f"GCS upload of {self.name}/{key} failed: {exc}") from exc
            self._generations[key] = generation

    def download(self, key: str) -> bytes:
        with self._lock:
            try:
                found = self._store.get_bytes(key)
            except Exception as exc:
                raise BlobUnavailable(f"GCS download of {self.name}/{key} failed: {exc}") from exc
            if found is None:
                # Seen absent: creating it later is safe, replacing is not.
                self._generations[key] = 0
                raise BlobUnavailable(f"{self.name}/{key} does not exist")
            data, generation = found
            self._generations[key] = generation
            return data


def durable_blob_store(name: str, *, gcs_client=None):
    """The blob backend for one purpose ("scan-media", "curriculum-snapshots").

    See the module docstring for the precedence. `gcs_client` exists for
    tests; production builds the default client from the Cloud Run service
    account."""
    bucket = _gcs_bucket()
    if bucket:
        return GcsBlobStore(
            name, bucket=bucket,
            prefix=os.environ.get("ACOS_GCS_PREFIX", "").strip() or "academicos",
            client=gcs_client, guard_generations=name in _GUARDED)
    from ..assessment.supabase_kv import SupabaseStorage
    return SupabaseStorage(name)


def blob_backend() -> str:
    """"gcs" | "supabase" | "local": what durable_blob_store resolves to now,
    reported by /health/storage next to durability_backend."""
    if _gcs_bucket():
        return "gcs"
    from ..assessment.supabase_kv import _supabase_credentials
    url, key = _supabase_credentials()
    return "supabase" if (url and key) else "local"
