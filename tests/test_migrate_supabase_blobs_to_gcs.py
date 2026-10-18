"""scripts/migrate_supabase_blobs_to_gcs.py -- the curriculum snapshot and scan
media move from Supabase Storage to GCS.

Why this exists: after the GCP deploy dropped its Supabase secrets, both blob
kinds are read from GCS, where nothing had been copied. The curriculum store
then saw "no snapshot" and came up empty as if that were the school's real
curriculum, and every pre-cutover scan artifact read back as missing. The doc
told the operator to copy the objects by hand; nothing did it or checked it.

No network: Supabase Storage is a fake session answering the two REST calls
the script makes, GCS is test_blob_factory's in-memory fake with real
generation semantics.
"""
from __future__ import annotations

import importlib.util
import sqlite3
import sys
import types
from pathlib import Path

import pytest
import requests

from academicos.storage import blobs
from store_backend import sqlite_only

ROOT = Path(__file__).resolve().parents[1]
BUCKET = "school-media"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod        # dataclasses resolve annotations through it
    spec.loader.exec_module(mod)
    return mod


migrate = _load("migrate_supabase_blobs_to_gcs",
                ROOT / "scripts" / "migrate_supabase_blobs_to_gcs.py")
FakeGcsClient = _load("_blob_fakes", ROOT / "tests" / "test_blob_factory.py").FakeGcsClient


class FakeResponse:
    def __init__(self, status: int, *, body=None, content: bytes = b""):
        self.status_code = status
        self._body = body
        self.content = content
        self.text = "" if status < 400 else '{"error":"not_found"}'

    def json(self):
        return self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"HTTP {self.status_code}", response=self)


class FakeSupabaseStorage:
    """Supabase Storage's list + download, one folder level per list call,
    folders as entries with id None -- the shape the real endpoint returns."""

    def __init__(self, objects: dict[str, dict[str, bytes]], page: int = 100):
        self.objects = objects
        self.page = page
        self.list_calls = 0

    def post(self, url, json, headers, timeout):
        self.list_calls += 1
        bucket = url.rsplit("/", 1)[1]
        prefix = json["prefix"]
        base = f"{prefix}/" if prefix else ""
        entries: dict[str, dict] = {}
        for key in sorted(self.objects.get(bucket, {})):
            if not key.startswith(base):
                continue
            rest = key[len(base):]
            head, _, tail = rest.partition("/")
            entries[head] = {"name": head, "id": None if tail else f"id-{key}"}
        items = list(entries.values())
        off = json["offset"]
        return FakeResponse(200, body=items[off:off + min(json["limit"], self.page)])

    def get(self, url, headers, timeout):
        bucket, key = url.split("/storage/v1/object/", 1)[1].split("/", 1)
        data = self.objects.get(bucket, {}).get(key)
        if data is None:
            return FakeResponse(400)   # older Supabase: 400 + not_found body
        return FakeResponse(200, content=data)


def _sqlite_bytes(tmp_path: Path, codes: list[str]) -> bytes:
    path = tmp_path / "src.sqlite"
    conn = sqlite3.connect(str(path))
    conn.execute("CREATE TABLE boards (id TEXT, name TEXT, code TEXT)")
    for c in codes:
        conn.execute("INSERT INTO boards VALUES (?, ?, ?)", (c, c, c))
    conn.commit()
    conn.close()
    return path.read_bytes()


@pytest.fixture
def env(monkeypatch):
    for name in ("ACOS_GCS_PREFIX", "ACOS_POSTGRES_HOST", "ACOS_CURRICULUM_ALLOW_EMPTY_BOOT"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("SUPABASE_KNOWLEDGE_URL", "https://proj.supabase.co")
    monkeypatch.setenv("SUPABASE_KNOWLEDGE_ANON_KEY", "anon")
    monkeypatch.setenv("ACOS_GCS_BUCKET", BUCKET)
    blobs.reset_status()
    yield monkeypatch
    blobs.reset_status()


def _install_fake_gcs(monkeypatch, client: FakeGcsClient) -> None:
    """So CurriculumStore's own durable_blob_store() (no client argument)
    reaches the same fake bucket the script wrote to."""
    google = types.ModuleType("google")
    google.__path__ = []
    cloud = types.ModuleType("google.cloud")
    cloud.__path__ = []
    storage_mod = types.ModuleType("google.cloud.storage")
    storage_mod.Client = lambda *a, **k: client
    monkeypatch.setitem(sys.modules, "google", google)
    monkeypatch.setitem(sys.modules, "google.cloud", cloud)
    monkeypatch.setitem(sys.modules, "google.cloud.storage", storage_mod)


@sqlite_only
def test_copies_snapshot_and_nested_scan_media_then_the_store_boots_from_it(
        env, tmp_path: Path) -> None:
    snapshot = _sqlite_bytes(tmp_path, ["cbse", "icse"])
    media = {f"scan_{i:03d}/raw/page_001.jpg": f"jpeg {i}".encode() for i in range(130)}
    media["scan_000/raw.pdf"] = b"%PDF-1.4"
    source = FakeSupabaseStorage({
        "curriculum-snapshots": {"curriculum.sqlite": snapshot},
        "scan-media": media,
    })
    gcs = FakeGcsClient()

    assert migrate.main([], session=source, gcs_client=gcs) == 0

    objects = gcs.bucket(BUCKET).objects
    assert objects["academicos/curriculum-snapshots/curriculum.sqlite"]["data"] == snapshot
    for key, data in media.items():               # 131 objects, >1 list page
        stored = objects[f"academicos/scan-media/{key}"]
        assert stored["data"] == data
    assert objects["academicos/scan-media/scan_000/raw.pdf"]["content_type"] == "application/pdf"

    # The point of it all: the GCS-backed store now restores the school's
    # curriculum, with no empty-boot acknowledgement needed.
    _install_fake_gcs(env, gcs)
    from academicos.curriculum.store import CurriculumStore
    store = CurriculumStore(tmp_path / "service" / "curriculum.sqlite")
    assert {b.code for b in store.list_boards()} == {"cbse", "icse"}
    store.close()


def test_never_overwrites_a_snapshot_already_in_gcs(env, tmp_path: Path) -> None:
    """If the service already booted on GCS and an admin has been editing,
    copying the old Supabase snapshot over it would erase those edits."""
    gcs = FakeGcsClient()
    live = blobs.durable_blob_store("curriculum-snapshots", gcs_client=gcs)
    live.upload("curriculum.sqlite", b"SQLite format 3\x00 edited on GCS",
                "application/x-sqlite3")
    source = FakeSupabaseStorage({
        "curriculum-snapshots": {"curriculum.sqlite": _sqlite_bytes(tmp_path, ["old"])},
    })
    assert migrate.main(["--only", "curriculum"], session=source, gcs_client=gcs) == 0
    assert gcs.bucket(BUCKET).objects[
        "academicos/curriculum-snapshots/curriculum.sqlite"]["data"].endswith(b"edited on GCS")


def test_missing_supabase_snapshot_is_reported_not_invented(env, capsys) -> None:
    gcs = FakeGcsClient()
    source = FakeSupabaseStorage({})
    assert migrate.main(["--only", "curriculum"], session=source, gcs_client=gcs) == 0
    assert "ACOS_CURRICULUM_ALLOW_EMPTY_BOOT=1" in capsys.readouterr().out
    assert gcs.bucket(BUCKET).objects == {}


def test_dry_run_writes_nothing(env, tmp_path: Path) -> None:
    gcs = FakeGcsClient()
    source = FakeSupabaseStorage({
        "curriculum-snapshots": {"curriculum.sqlite": _sqlite_bytes(tmp_path, ["cbse"])},
        "scan-media": {"s/raw.pdf": b"%PDF"},
    })
    assert migrate.main(["--dry-run"], session=source, gcs_client=gcs) == 0
    assert gcs.bucket(BUCKET).objects == {}


def test_a_failed_copy_is_a_non_zero_exit(env, tmp_path: Path) -> None:
    gcs = FakeGcsClient()
    gcs.fail_reads_and_writes = True
    source = FakeSupabaseStorage({"scan-media": {"s/raw.pdf": b"%PDF"}})
    assert migrate.main(["--only", "scan-media"], session=source, gcs_client=gcs) == 1


def test_refuses_without_a_gcs_destination(env) -> None:
    env.delenv("ACOS_GCS_BUCKET")
    with pytest.raises(SystemExit):
        migrate.main([], session=FakeSupabaseStorage({}))
