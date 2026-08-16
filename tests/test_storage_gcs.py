"""Coverage of GcsStore (src/academicos/storage/gcs.py) with a stubbed client.

`google-cloud-storage` is NOT installed (optional `gcs` extra), so we inject a
minimal fake `google.cloud.storage` module into sys.modules. The fakes only
record calls — they verify the *wiring* (prefixing, method calls, name
stripping), not the real GCS SDK.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

from academicos.storage.gcs import GcsStore


class FakeBlob:
    def __init__(self, name: str):
        self.name = name
        self.calls: list[tuple] = []
        self.size = 0

    def upload_from_filename(self, local_path: str) -> None:
        self.calls.append(("upload_from_filename", local_path))

    def download_to_filename(self, local_path: str) -> None:
        self.calls.append(("download_to_filename", local_path))

    def exists(self) -> bool:
        self.calls.append(("exists",))
        return True

    def delete(self) -> None:
        self.calls.append(("delete",))


class FakeBucket:
    def __init__(self, name: str):
        self.name = name
        self.blobs: dict[str, FakeBlob] = {}

    def blob(self, name: str) -> FakeBlob:
        return self.blobs.setdefault(name, FakeBlob(name))


class FakeClient:
    def __init__(self):
        self.buckets: dict[str, FakeBucket] = {}

    def bucket(self, name: str) -> FakeBucket:
        return self.buckets.setdefault(name, FakeBucket(name))

    def list_blobs(self, bucket: FakeBucket, prefix: str = "") -> list[FakeBlob]:
        return [b for b in bucket.blobs.values() if b.name.startswith(prefix)]


@pytest.fixture
def fake_storage(monkeypatch) -> None:
    google = types.ModuleType("google")
    google.__path__ = []
    cloud = types.ModuleType("google.cloud")
    cloud.__path__ = []
    storage_mod = types.ModuleType("google.cloud.storage")
    storage_mod.Client = FakeClient
    monkeypatch.setitem(sys.modules, "google", google)
    monkeypatch.setitem(sys.modules, "google.cloud", cloud)
    monkeypatch.setitem(sys.modules, "google.cloud.storage", storage_mod)


def test_no_bucket_raises_value_error(fake_storage) -> None:
    with pytest.raises(ValueError):
        GcsStore("")


def test_key_prefixing(fake_storage) -> None:
    s = GcsStore("bucket", prefix="academicos")
    assert s._key("foo/bar") == "academicos/foo/bar"
    assert s._key("/foo/bar/") == "academicos/foo/bar"
    assert s._key("foo") == "academicos/foo"


def test_key_empty_prefix_is_bare(fake_storage) -> None:
    s = GcsStore("bucket", prefix="")
    assert s._key("foo/bar") == "foo/bar"
    assert s._key("/foo/bar/") == "foo/bar"


def test_put_uploads_prefixed_name(fake_storage, tmp_path: Path) -> None:
    s = GcsStore("bucket", prefix="academicos")
    src = tmp_path / "in.bin"
    src.write_bytes(b"hello")
    s.put(src, "docs/obj.bin")
    blob = s.bucket.blob("academicos/docs/obj.bin")
    assert ("upload_from_filename", str(src)) in blob.calls
    # nothing written to the unprefixed key
    assert ("upload_from_filename", str(src)) not in s.bucket.blob("docs/obj.bin").calls


def test_get_downloads_and_creates_parent_dir(fake_storage, tmp_path: Path) -> None:
    s = GcsStore("bucket", prefix="academicos")
    dst = tmp_path / "deep" / "nested" / "out.bin"
    got = s.get("docs/obj.bin", dst)
    assert got == dst
    assert dst.parent.is_dir()
    blob = s.bucket.blob("academicos/docs/obj.bin")
    assert ("download_to_filename", str(dst)) in blob.calls


def test_exists_and_size_roundtrip(fake_storage) -> None:
    s = GcsStore("bucket", prefix="academicos")
    assert s.exists("docs/obj.bin") is True
    blob = s.bucket.blob("academicos/docs/obj.bin")
    assert ("exists",) in blob.calls
    blob.size = 7
    assert s.size("docs/obj.bin") == 7


def test_keys_strips_prefix(fake_storage, tmp_path: Path) -> None:
    s = GcsStore("bucket", prefix="academicos")
    src = tmp_path / "in.bin"
    src.write_bytes(b"x")
    for key in ("docs/obj.bin", "docs/other.bin", "notes/a.txt"):
        s.put(src, key)
    assert sorted(s.keys()) == ["docs/obj.bin", "docs/other.bin", "notes/a.txt"]
    assert sorted(s.keys("docs")) == ["docs/obj.bin", "docs/other.bin"]
    assert s.keys("zz") == []


def test_keys_with_empty_prefix_returns_full_names(fake_storage, tmp_path: Path) -> None:
    s = GcsStore("bucket", prefix="")
    src = tmp_path / "in.bin"
    src.write_bytes(b"x")
    s.put(src, "foo/bar")
    s.put(src, "baz.txt")
    assert sorted(s.keys()) == ["baz.txt", "foo/bar"]


def test_delete_calls_through(fake_storage) -> None:
    s = GcsStore("bucket", prefix="academicos")
    s.delete("docs/obj.bin")
    blob = s.bucket.blob("academicos/docs/obj.bin")
    assert ("delete",) in blob.calls