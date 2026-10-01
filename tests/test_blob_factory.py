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

import base64
import hashlib
import logging
import sqlite3
import sys
import time
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
        # GCS reports md5 as base64 of the raw digest, not hex.
        self.md5_hash = obj["md5"] if obj else None

    def upload_from_string(self, data: bytes, content_type: str | None = None,
                           if_generation_match: int | None = None) -> None:
        client = self._bucket.client
        if client.fail_reads_and_writes:
            raise ConnectionError("simulated GCS outage")
        current = self._bucket.objects.get(self.name)
        current_gen = current["generation"] if current else 0
        if if_generation_match is not None and if_generation_match != current_gen:
            raise FakePreconditionFailed(
                f"412 generation {current_gen} != expected {if_generation_match}")
        client.counter += 1
        self._bucket.objects[self.name] = {
            "data": bytes(data), "content_type": content_type,
            "generation": client.counter,
            "md5": base64.b64encode(hashlib.md5(bytes(data)).digest()).decode(),
        }
        self.generation = client.counter
        if client.lose_next_upload_response:
            # The write landed, the response did not; the client's
            # conditional retry then re-sends against the generation it just
            # created and gets 412. This is that retry's view.
            client.lose_next_upload_response = False
            self.generation = None
            raise FakePreconditionFailed("412 on retry of a write that already landed")

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
        if self.client.fail_reads_and_writes:
            raise ConnectionError("simulated GCS outage")
        return FakeGcsBlob(self, name) if name in self.objects else None


class FakeGcsClient:
    def __init__(self):
        self.buckets: dict[str, FakeGcsBucket] = {}
        self.counter = 0
        self.fail_reads_and_writes = False
        self.lose_next_upload_response = False

    def bucket(self, name: str) -> FakeGcsBucket:
        return self.buckets.setdefault(name, FakeGcsBucket(self, name))


BUCKET = "vidyuthlabs-academicos-media"


@pytest.fixture(autouse=True)
def _fresh_blob_status():
    """The conflict/failure counters are process-wide on purpose (health reads
    them); each test starts from zero."""
    blobs.reset_status()
    yield
    blobs.reset_status()


@pytest.fixture
def clean_env(monkeypatch):
    """No backend configured unless a test sets one."""
    for name in ("ACOS_GCS_BUCKET", "ACOS_GCS_PREFIX", "SUPABASE_KNOWLEDGE_URL",
                 "SUPABASE_KNOWLEDGE_ANON_KEY", "ACOS_POSTGRES_HOST",
                 "ACOS_POSTGRES_DB", "ACOS_POSTGRES_USER",
                 "ACOS_CURRICULUM_ALLOW_EMPTY_BOOT"):
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
    # Most tests below start from an empty bucket on purpose (two instances,
    # one snapshot), which is exactly the boot the guard refuses without this
    # acknowledgement. The guard itself is tested with it removed.
    clean_env.setenv("ACOS_CURRICULUM_ALLOW_EMPTY_BOOT", "1")
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


def test_download_of_missing_object_raises_blob_not_found(shared_gcs) -> None:
    """A missing object is BlobNotFound -- distinct from "GCS unreachable" --
    so the curriculum restore can tell a first boot from an outage. Still a
    RequestException, so callers written against SupabaseStorage keep
    working."""
    store = durable_blob_store("curriculum-snapshots")
    with pytest.raises(blobs.BlobNotFound):
        store.download("curriculum.sqlite")
    assert issubclass(blobs.BlobNotFound, requests.exceptions.RequestException)


def test_unreachable_gcs_is_not_reported_as_not_found(shared_gcs) -> None:
    shared_gcs.fail_reads_and_writes = True
    store = durable_blob_store("curriculum-snapshots")
    with pytest.raises(blobs.BlobUnavailable) as info:
        store.download("curriculum.sqlite")
    assert not isinstance(info.value, blobs.BlobNotFound)


# --------------------------------------------------------------------------- #
# curriculum snapshot: single writer, through CurriculumStore
#
# The mechanism itself (debounce, trailing upload, conflict copy, reload,
# wedge) is tested directly in tests/test_snapshot_sync.py. What stays here
# proves the store is wired to it: its writes reach GCS, its constructor
# restores and refuses, a refused write answers 503 from a store method, and
# the app's shutdown hook flushes a store's pending edits.
# --------------------------------------------------------------------------- #

def _snapshot(client: FakeGcsClient) -> dict:
    return client.bucket(BUCKET).objects["academicos/curriculum-snapshots/curriculum.sqlite"]


def _boards_in(data: bytes, tmp_path: Path) -> set[str]:
    """The board codes inside a snapshot blob, read with plain sqlite3."""
    path = tmp_path / f"inspect_{time.monotonic_ns()}.sqlite"
    path.write_bytes(data)
    conn = sqlite3.connect(str(path))
    try:
        return {r[0] for r in conn.execute("SELECT code FROM boards")}
    finally:
        conn.close()


def test_curriculum_store_uses_gcs_on_gcp(shared_gcs, tmp_path: Path) -> None:
    from academicos.curriculum.store import CurriculumStore
    store = CurriculumStore(tmp_path / "a" / "curriculum.sqlite")
    assert store._snapshots.remote.backend == "gcs"
    store.create_board("CBSE", "cbse")
    assert _snapshot(shared_gcs)["data"].startswith(b"SQLite format 3")
    assert _boards_in(_snapshot(shared_gcs)["data"], tmp_path) == {"cbse"}
    store.close()




def test_shutdown_flushes_edits_still_inside_the_window(
        shared_gcs, tmp_path: Path, monkeypatch) -> None:
    """Cloud Run sends SIGTERM and allows 10 s. The app's shutdown hook must
    upload whatever the debounce is still holding, or the last edits before a
    deploy are lost with the container."""
    from academicos.curriculum import store as store_mod
    import academicos.api.main as main_mod
    monkeypatch.setattr(store_mod, "_INSTANCE", None)

    store = store_mod.get_curriculum_store(tmp_path)
    store._snapshots._last_upload_at = 0.0
    store.create_board("CBSE", "cbse")       # uploads
    store.create_board("ICSE", "icse")       # held by the 30 s debounce
    store.create_board("State", "state")
    assert _boards_in(_snapshot(shared_gcs)["data"], tmp_path) == {"cbse"}

    # Registered with the app, so uvicorn runs it on SIGTERM.
    assert main_mod._shutdown in main_mod.app.router.on_shutdown
    main_mod._shutdown()

    assert _boards_in(_snapshot(shared_gcs)["data"], tmp_path) == {"cbse", "icse", "state"}
    store.close()




def test_empty_gcs_boot_needs_an_explicit_acknowledgement(
        shared_gcs, tmp_path: Path, monkeypatch) -> None:
    """Before the GCS move the snapshot lived in Supabase Storage. The first
    GCS-backed boot finds no object, and "no object" used to mean "first
    boot": the service came up with an empty curriculum as if it were the
    real one -- the outcome the unreachable-GCS guard exists to prevent,
    reached by a different road. On GCS an empty start now needs
    ACOS_CURRICULUM_ALLOW_EMPTY_BOOT=1 (a genuinely new school); otherwise
    boot fails and names the migration script."""
    from academicos.curriculum.store import CurriculumStore
    from academicos.storage.blobs import CurriculumNotDurable
    monkeypatch.delenv("ACOS_CURRICULUM_ALLOW_EMPTY_BOOT")
    db_path = tmp_path / "fresh" / "curriculum.sqlite"
    with pytest.raises(CurriculumNotDurable) as info:
        CurriculumStore(db_path)
    assert "migrate_supabase_blobs_to_gcs.py" in str(info.value)
    assert "ACOS_CURRICULUM_ALLOW_EMPTY_BOOT" in str(info.value)
    assert not db_path.exists(), "a refused boot must leave nothing to boot from"


def test_an_allowed_empty_boot_saves_its_snapshot_so_the_next_deploy_starts(
        shared_gcs, tmp_path: Path, monkeypatch) -> None:
    """The live GCP service first booted with ACOS_CURRICULUM_ALLOW_EMPTY_BOOT=1
    and nobody edited a curriculum afterwards. A schema-only start commits no
    row change, so no snapshot was ever uploaded, and the next deploy
    (revision 00003, 2026-09-22) refused to start: "no curriculum snapshot in
    GCS". The acknowledgement is a FIRST-boot variable, so the empty
    curriculum is saved at once and the next boot restores it."""
    from academicos.curriculum import store as store_mod
    monkeypatch.setattr(store_mod, "_INSTANCE", None)
    monkeypatch.setenv("ACOS_CURRICULUM_ALLOW_EMPTY_BOOT", "1")
    first = store_mod.get_curriculum_store(tmp_path / "boot1")
    assert _boards_in(_snapshot(shared_gcs)["data"], tmp_path) == set()
    first.close()

    monkeypatch.setattr(store_mod, "_INSTANCE", None)
    monkeypatch.delenv("ACOS_CURRICULUM_ALLOW_EMPTY_BOOT")
    second = store_mod.get_curriculum_store(tmp_path / "boot2")   # the next deploy
    assert second.list_boards() == []
    second.close()


def test_empty_boot_guard_does_not_apply_off_gcs(clean_env, tmp_path: Path) -> None:
    """Local dev (no bucket) never restores and must keep starting empty."""
    from academicos.curriculum.store import CurriculumStore
    store = CurriculumStore(tmp_path / "curriculum.sqlite")
    assert store.list_boards() == []
    store.close()


def test_boot_refuses_to_start_empty_when_gcs_is_unreachable(
        shared_gcs, tmp_path: Path) -> None:
    """Unreachable is not "no snapshot yet". Starting empty here serves a blank
    curriculum as if it were real, and the admin who re-enters it loses it all
    at the next deploy. The constructor must fail so the container fails its
    startup probe and Cloud Run retries it."""
    from academicos.curriculum.store import CurriculumStore
    from academicos.storage.blobs import CurriculumNotDurable
    seed = CurriculumStore(tmp_path / "seed" / "curriculum.sqlite")
    seed.create_board("CBSE", "cbse")         # a real snapshot exists remotely
    seed.close()

    shared_gcs.fail_reads_and_writes = True
    db_path = tmp_path / "fresh" / "curriculum.sqlite"
    with pytest.raises(CurriculumNotDurable):
        CurriculumStore(db_path)
    assert not db_path.exists(), "a failed restore must leave nothing to boot from"

    shared_gcs.fail_reads_and_writes = False  # the retry Cloud Run makes
    store = CurriculumStore(db_path)
    assert store.get_board_by_code("cbse") is not None
    store.close()


def test_stale_curriculum_snapshot_write_is_refused(shared_gcs, tmp_path: Path, caplog) -> None:
    """Two instances, one snapshot blob -- the overlap every Cloud Run rollout
    has, since --max-instances is per revision. B restores A's snapshot and
    writes after it; A -- still holding the generation it last wrote -- must
    NOT replace B's snapshot with its own older copy of the database.

    And A must not stay stuck: it used to keep its stale generation for good,
    so every later upload 412'd, every request still said "saved", and health
    showed nothing. Now the refused write answers 503 (a real "not saved"),
    A reloads the newer snapshot, health names the conflict, and A's next
    write lands on top of B's."""
    from academicos.curriculum.store import CurriculumStore
    from academicos.storage.blobs import CurriculumNotDurable
    import academicos.api.main as main_mod

    a = CurriculumStore(tmp_path / "a" / "curriculum.sqlite")
    a._snapshots._last_upload_at = 0.0
    a.create_board("CBSE", "cbse")                              # A uploads
    b = CurriculumStore(tmp_path / "b" / "curriculum.sqlite")   # restores A's
    b._snapshots._last_upload_at = 0.0
    b.create_board("State", "state")                            # B writes after A
    after_b = _snapshot(shared_gcs)

    a._snapshots._last_upload_at = 0.0
    with caplog.at_level(logging.ERROR, logger="academicos.storage.blobs"):
        with pytest.raises(CurriculumNotDurable):
            a.create_board("ICSE", "icse")

    assert _snapshot(shared_gcs) == after_b, "A silently erased B's snapshot"
    assert any("refused" in r.getMessage().lower() for r in caplog.records)
    status = main_mod.health_storage()["blob_status"]
    assert status["curriculum_snapshot_conflict"] is True
    assert status["curriculum_snapshot_conflict_count"] == 1
    assert status["curriculum_snapshot_conflict_at"]

    # A reloaded B's snapshot: B's board is there, A's refused one is not.
    assert a.get_board_by_code("state") is not None
    assert a.get_board_by_code("icse") is None

    # ... so A's retry succeeds and carries B's data with it.
    a._snapshots._last_upload_at = 0.0
    a.create_board("ICSE", "icse")
    assert _snapshot(shared_gcs)["generation"] > after_b["generation"]
    assert _boards_in(_snapshot(shared_gcs)["data"], tmp_path) == {"cbse", "state", "icse"}
    a.close()
    b.close()


def _conflict_copies(client: FakeGcsClient) -> dict[str, dict]:
    prefix = "academicos/curriculum-snapshots/conflicts/"
    return {k: v for k, v in client.bucket(BUCKET).objects.items() if k.startswith(prefix)}








def test_conflict_is_a_503_not_a_500(shared_gcs) -> None:
    """api/main.py maps SupabaseUnavailable (and its subclasses) to 503."""
    from academicos.assessment.supabase_kv import SupabaseUnavailable
    from academicos.storage.blobs import CurriculumNotDurable
    assert issubclass(CurriculumNotDurable, SupabaseUnavailable)


def test_retry_that_sees_its_own_write_is_not_a_conflict(shared_gcs, caplog) -> None:
    """With if_generation_match set, google-cloud-storage retries the upload.
    If the first attempt landed but its response was lost, the retry 412s
    against the generation it just made. That is our own write: adopt it,
    do not declare another instance and wedge the store."""
    store = durable_blob_store("curriculum-snapshots")
    shared_gcs.lose_next_upload_response = True
    with caplog.at_level(logging.ERROR, logger="academicos.storage.blobs"):
        store.upload("curriculum.sqlite", b"mine", "application/x-sqlite3")
    assert not any("refused" in r.getMessage().lower() for r in caplog.records)
    assert blobs.blob_status()["curriculum_snapshot_conflict"] is False

    # The adopted generation is the real one: the next write is accepted.
    store.upload("curriculum.sqlite", b"mine v2", "application/x-sqlite3")
    assert _snapshot(shared_gcs)["data"] == b"mine v2"


def test_real_conflict_with_different_bytes_is_still_refused(shared_gcs) -> None:
    other = durable_blob_store("curriculum-snapshots")
    other.upload("curriculum.sqlite", b"other instance", "application/x-sqlite3")
    fresh = durable_blob_store("curriculum-snapshots")
    with pytest.raises(blobs.BlobConflict):
        fresh.upload("curriculum.sqlite", b"mine", "application/x-sqlite3")
    assert blobs.blob_status()["curriculum_snapshot_conflict_count"] == 1


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
    snapshot_keys = {
        "{0}_snapshot_conflict": False,
        "{0}_snapshot_conflict_count": 0,
        "{0}_snapshot_conflict_at": None,
        "{0}_snapshot_upload_failures": 0,
        "{0}_snapshot_upload_failure_at": None,
        "{0}_snapshot_conflict_copies": 0,
        "{0}_snapshot_last_conflict_copy": None,
        "{0}_snapshot_last_saved_at": None,
    }
    assert body["blob_status"] == {
        **{k.format("curriculum"): v for k, v in snapshot_keys.items()},
        **{k.format("operations"): v for k, v in snapshot_keys.items()},
        "scan_media_upload_failures": 0,
        "scan_media_upload_failure_at": None,
    }


def test_operations_snapshot_that_stops_saving_shows_in_health(shared_gcs, tmp_path: Path) -> None:
    """N-9-2: the operations store (homework, marks, exams, notifications,
    parent links) is a whole-file snapshot like the curriculum. If its uploads
    fail, /health/storage must say so -- it used to report the curriculum and
    scan media only, and read ok while every operations save failed."""
    from academicos.operations.store import OperationsStore
    import academicos.api.main as main_mod

    ops = OperationsStore(tmp_path / "ops" / "operations.sqlite")
    ops._snapshots._last_upload_at = 0.0
    ops.set_settings("u1", language="hi")                     # uploads
    status = main_mod.health_storage()["blob_status"]
    saved_at = status["operations_snapshot_last_saved_at"]
    assert saved_at and status["operations_snapshot_upload_failures"] == 0

    shared_gcs.fail_reads_and_writes = True
    ops._snapshots._last_upload_at = 0.0
    ops.set_settings("u2", language="hi")                     # this save fails
    status = main_mod.health_storage()["blob_status"]
    assert status["operations_snapshot_upload_failures"] == 1
    assert status["operations_snapshot_upload_failure_at"] >= saved_at
    assert status["curriculum_snapshot_upload_failures"] == 0, "counted under its own store"

    shared_gcs.fail_reads_and_writes = False
    assert ops._snapshots.flush() is True                     # the retry lands
    status = main_mod.health_storage()["blob_status"]
    assert status["operations_snapshot_last_saved_at"] >= status["operations_snapshot_upload_failure_at"]
    ops.close()


def test_failed_scan_media_upload_is_counted_in_health(
        shared_gcs, tmp_path: Path, monkeypatch) -> None:
    """A failed scan upload stays best-effort for the teacher (the scan must
    not fail mid-way), but on GCP that artifact then exists only on container
    disk. It must at least be visible: /health/storage counts it."""
    from academicos.assessment import mobile_scan
    import academicos.api.main as main_mod
    monkeypatch.setattr(mobile_scan, "_storage", durable_blob_store("scan-media"))
    photo = tmp_path / "page_001.jpg"
    photo.write_bytes(b"\xff\xd8 jpeg")

    shared_gcs.fail_reads_and_writes = True
    assert mobile_scan._upload("scan_abc", "raw/page_001.jpg", photo, "image/jpeg") == ""

    status = main_mod.health_storage()["blob_status"]
    assert status["scan_media_upload_failures"] == 1
    assert status["scan_media_upload_failure_at"]
