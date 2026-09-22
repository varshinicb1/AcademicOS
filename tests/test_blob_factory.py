"""The blob factory (storage/blobs.py) and the two blob call sites it serves.

Why these tests exist: on GCP, scan-media photos/PDFs and the curriculum
snapshot used to go through SupabaseStorage only. With the Supabase secrets
removed from the Cloud Run service, both would silently have stayed on
container disk -- which Cloud Run throws away on every redeploy and every
scale-to-zero. The factory routes them to GCS when ACOS_GCS_BUCKET is set.

The curriculum snapshot is one blob holding a whole SQLite file, so two
Cloud Run instances each uploading their own copy would overwrite each other.
The GCS path therefore writes with a generation precondition and refuses to
replace a snapshot it did not load; the two-instance test below is that exact
scenario.

No network: `google-cloud-storage` is replaced by an in-memory fake that
implements the generation semantics GCS documents (every write bumps the
object generation; `if_generation_match=0` means "only if absent"; a mismatch
is HTTP 412).
"""
from __future__ import annotations

import logging
import sys
import types
from pathlib import Path

import pytest
import requests

from academicos.assessment.supabase_kv import SupabaseStorage
from academicos.storage import blobs
from academicos.storage.blobs import blob_backend, durable_blob_store


# --------------------------------------------------------------------------- #
# in-memory GCS fake with real generation semantics
# --------------------------------------------------------------------------- #

class FakePreconditionFailed(Exception):
    """Stands in for google.api_core.exceptions.PreconditionFailed."""
    code = 412


class FakeGcsBlob:
    def __init__(self, bucket: "FakeGcsBucket", name: str):
        self._bucket = bucket
        self.name = name
        obj = bucket.objects.get(name)
        self.generation = obj["generation"] if obj else None

    def upload_from_string(self, data: bytes, content_type: str | None = None,
                           if_generation_match: int | None = None) -> None:
        current = self._bucket.objects.get(self.name)
        current_gen = current["generation"] if current else 0
        if if_generation_match is not None and if_generation_match != current_gen:
            raise FakePreconditionFailed(
                f"412 generation {current_gen} != expected {if_generation_match}")
        self._bucket.client.counter += 1
        self._bucket.objects[self.name] = {
            "data": bytes(data), "content_type": content_type,
            "generation": self._bucket.client.counter,
        }
        self.generation = self._bucket.client.counter

    def download_as_bytes(self, if_generation_match: int | None = None) -> bytes:
        obj = self._bucket.objects[self.name]
        if if_generation_match is not None and if_generation_match != obj["generation"]:
            raise FakePreconditionFailed("412 changed between metadata and read")
        return obj["data"]


class FakeGcsBucket:
    def __init__(self, client: "FakeGcsClient", name: str):
        self.client = client
        self.name = name
        self.objects: dict[str, dict] = {}

    def blob(self, name: str) -> FakeGcsBlob:
        return FakeGcsBlob(self, name)

    def get_blob(self, name: str) -> FakeGcsBlob | None:
        return FakeGcsBlob(self, name) if name in self.objects else None


class FakeGcsClient:
    def __init__(self):
        self.buckets: dict[str, FakeGcsBucket] = {}
        self.counter = 0

    def bucket(self, name: str) -> FakeGcsBucket:
        return self.buckets.setdefault(name, FakeGcsBucket(self, name))


BUCKET = "vidyuthlabs-academicos-media"


@pytest.fixture
def clean_env(monkeypatch):
    """No backend configured unless a test sets one."""
    for name in ("ACOS_GCS_BUCKET", "ACOS_GCS_PREFIX", "SUPABASE_KNOWLEDGE_URL",
                 "SUPABASE_KNOWLEDGE_ANON_KEY", "ACOS_POSTGRES_HOST",
                 "ACOS_POSTGRES_DB", "ACOS_POSTGRES_USER"):
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


@pytest.fixture
def shared_gcs(clean_env):
    """Every `storage.Client()` built during the test is the same fake -- two
    CurriculumStores then really do share one bucket, like two Cloud Run
    instances do."""
    client = FakeGcsClient()
    google = types.ModuleType("google")
    google.__path__ = []
    cloud = types.ModuleType("google.cloud")
    cloud.__path__ = []
    storage_mod = types.ModuleType("google.cloud.storage")
    storage_mod.Client = lambda *a, **k: client
    clean_env.setitem(sys.modules, "google", google)
    clean_env.setitem(sys.modules, "google.cloud", cloud)
    clean_env.setitem(sys.modules, "google.cloud.storage", storage_mod)
    clean_env.setenv("ACOS_GCS_BUCKET", BUCKET)
    return client


# --------------------------------------------------------------------------- #
# backend selection
# --------------------------------------------------------------------------- #

def test_gcs_wins_when_the_bucket_is_set(clean_env) -> None:
    clean_env.setenv("ACOS_GCS_BUCKET", BUCKET)
    # Supabase configured too: GCS must still win, or a half-migrated service
    # would keep writing school data outside GCP.
    clean_env.setenv("SUPABASE_KNOWLEDGE_URL", "https://proj.supabase.co")
    clean_env.setenv("SUPABASE_KNOWLEDGE_ANON_KEY", "real-anon-key")
    fake = FakeGcsClient()
    store = durable_blob_store("scan-media", gcs_client=fake)
    assert store.enabled is True
    assert store.backend == "gcs"
    assert blob_backend() == "gcs"

    store.upload("sess_1/raw.pdf", b"%PDF-1.4", "application/pdf")
    # Per-purpose prefix under the configured root prefix.
    assert list(fake.bucket(BUCKET).objects) == ["academicos/scan-media/sess_1/raw.pdf"]


def test_supabase_when_only_supabase_is_configured(clean_env) -> None:
    clean_env.setenv("SUPABASE_KNOWLEDGE_URL", "https://proj.supabase.co")
    clean_env.setenv("SUPABASE_KNOWLEDGE_ANON_KEY", "real-anon-key")
    store = durable_blob_store("scan-media")
    assert isinstance(store, SupabaseStorage)
    assert store.enabled is True
    assert blob_backend() == "supabase"


def test_local_when_nothing_is_configured(clean_env) -> None:
    store = durable_blob_store("scan-media")
    # Disabled: both call sites then keep the file on local disk only.
    assert store.enabled is False
    assert blob_backend() == "local"


def test_bucket_placeholder_is_not_a_bucket(clean_env) -> None:
    """bootstrap.sh's REPLACE_ME must never become a bucket name."""
    from academicos.config import SUPABASE_PLACEHOLDER
    clean_env.setenv("ACOS_GCS_BUCKET", SUPABASE_PLACEHOLDER)
    assert blob_backend() == "local"
    assert durable_blob_store("scan-media").enabled is False


def test_toml_dev_bucket_is_ignored(clean_env) -> None:
    """config/config.toml names a dev bucket for the CLI corpus sync. The
    blob factory must read only the deploy env var, or every local run would
    try to write school data into that bucket."""
    from academicos.config import Config
    assert Config.load().gcs_bucket  # the TOML value really is set ...
    assert blob_backend() == "local"  # ... and still does not select GCS


# --------------------------------------------------------------------------- #
# scan media round trip through the real call site
# --------------------------------------------------------------------------- #

def test_scan_media_round_trip_through_gcs(shared_gcs, tmp_path: Path, monkeypatch) -> None:
    from academicos.assessment import mobile_scan
    monkeypatch.setattr(mobile_scan, "_storage", durable_blob_store("scan-media"))

    photo = tmp_path / "page_001.jpg"
    photo.write_bytes(b"\xff\xd8\xff\xe0 fake jpeg bytes")
    key = mobile_scan._upload("scan_abc", "raw/page_001.jpg", photo, "image/jpeg")

    assert key == "scan_abc/raw/page_001.jpg"
    stored = shared_gcs.bucket(BUCKET).objects["academicos/scan-media/scan_abc/raw/page_001.jpg"]
    assert stored["content_type"] == "image/jpeg"
    assert mobile_scan.fetch_storage_bytes(key) == photo.read_bytes()
    # A key that was never uploaded is None, not an exception.
    assert mobile_scan.fetch_storage_bytes("scan_abc/missing.jpg") is None


def test_download_of_missing_object_raises_a_request_exception(shared_gcs) -> None:
    """curriculum/store.py's restore path catches RequestException only; a
    missing first snapshot must land there, not crash the constructor."""
    store = durable_blob_store("curriculum-snapshots")
    with pytest.raises(requests.exceptions.RequestException):
        store.download("curriculum.sqlite")


# --------------------------------------------------------------------------- #
# curriculum snapshot: single writer
# --------------------------------------------------------------------------- #

def _snapshot(client: FakeGcsClient) -> dict:
    return client.bucket(BUCKET).objects["academicos/curriculum-snapshots/curriculum.sqlite"]


def test_curriculum_store_uses_gcs_on_gcp(shared_gcs, tmp_path: Path) -> None:
    from academicos.curriculum.store import CurriculumStore
    store = CurriculumStore(tmp_path / "a" / "curriculum.sqlite")
    assert store._remote_storage.backend == "gcs"
    assert _snapshot(shared_gcs)["data"].startswith(b"SQLite format 3")
    store.close()


def test_stale_curriculum_snapshot_write_is_refused(shared_gcs, tmp_path: Path, caplog) -> None:
    """Two instances, one snapshot blob. Instance B restores A's snapshot and
    writes after it; A -- still holding the generation it last wrote -- must
    NOT replace B's snapshot with its own older copy of the database."""
    from academicos.curriculum.store import CurriculumStore

    a = CurriculumStore(tmp_path / "a" / "curriculum.sqlite")   # uploads gen 1
    b = CurriculumStore(tmp_path / "b" / "curriculum.sqlite")   # restores gen 1
    b._last_snapshot_at = 0.0
    b.create_board("CBSE", "cbse")                              # B writes after A
    after_b = _snapshot(shared_gcs)

    a._last_snapshot_at = 0.0
    with caplog.at_level(logging.ERROR, logger="academicos.storage.blobs"):
        a.create_board("ICSE", "icse")   # must not raise into the request either

    assert _snapshot(shared_gcs) == after_b, "A silently erased B's snapshot"
    assert any("refused" in r.getMessage().lower() for r in caplog.records)

    # B loaded what it is overwriting, so B keeps working.
    b._last_snapshot_at = 0.0
    b.create_board("State", "state")
    assert _snapshot(shared_gcs)["generation"] > after_b["generation"]
    a.close()
    b.close()


def test_guarded_write_to_a_snapshot_never_loaded_is_refused(shared_gcs) -> None:
    """An instance that skipped the restore (local db already on disk) never
    saw the remote generation; it may create the object, never replace it."""
    other = durable_blob_store("curriculum-snapshots")
    other.upload("curriculum.sqlite", b"other instance", "application/x-sqlite3")

    fresh = durable_blob_store("curriculum-snapshots")
    with pytest.raises(blobs.BlobConflict):
        fresh.upload("curriculum.sqlite", b"mine", "application/x-sqlite3")
    assert _snapshot(shared_gcs)["data"] == b"other instance"


def test_scan_media_is_not_generation_guarded(shared_gcs) -> None:
    """Scan keys are unique per session; re-uploading one (a re-captured page)
    must overwrite, so only the snapshot store carries the precondition."""
    a = durable_blob_store("scan-media")
    a.upload("s/raw.pdf", b"v1", "application/pdf")
    durable_blob_store("scan-media").upload("s/raw.pdf", b"v2", "application/pdf")
    assert a.download("s/raw.pdf") == b"v2"


# --------------------------------------------------------------------------- #
# /health/storage reports the blob backend in use
# --------------------------------------------------------------------------- #

def test_health_storage_reports_blob_backend(clean_env) -> None:
    import academicos.api.main as main_mod

    assert main_mod.health_storage()["blob_backend"] == "local"
    clean_env.setenv("ACOS_GCS_BUCKET", BUCKET)
    body = main_mod.health_storage()
    assert body["blob_backend"] == "gcs"
    assert "durability_backend" in body
