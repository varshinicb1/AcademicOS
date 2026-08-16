"""Deep coverage of LocalStore (src/academicos/storage/base.py).

Complements test_ingest_registry.py, which only touches LocalStore through
the ingestion pipeline. These tests exercise the object-store contract
directly against pytest tmp_path.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from academicos.storage.base import LocalStore


@pytest.fixture
def root(tmp_path: Path) -> Path:
    return tmp_path / "docs"


@pytest.fixture
def store(root: Path) -> LocalStore:
    return LocalStore(root)


def test_init_creates_root(tmp_path: Path) -> None:
    root = tmp_path / "deep" / "nested" / "root"
    s = LocalStore(root)
    assert s.root.is_dir()


def test_put_get_binary_roundtrip(store: LocalStore, tmp_path: Path) -> None:
    src = tmp_path / "blob.bin"
    data = bytes(range(256)) * 4
    src.write_bytes(data)
    store.put(src, "blob.bin")
    dst = tmp_path / "out.bin"
    got = store.get("blob.bin", dst)
    assert got == dst
    assert dst.read_bytes() == data


def test_put_creates_parent_dirs_for_nested_keys(store: LocalStore, tmp_path: Path) -> None:
    src = tmp_path / "a.bin"
    src.write_bytes(b"x")
    store.put(src, "nested/deep/path/a.bin")
    assert (store.root / "nested" / "deep" / "path" / "a.bin").is_file()


def test_get_writes_into_nested_local_path(store: LocalStore, tmp_path: Path) -> None:
    src = tmp_path / "a.bin"
    src.write_bytes(b"payload")
    store.put(src, "a.bin")
    dst = tmp_path / "sub" / "nested" / "deep" / "out.bin"
    got = store.get("a.bin", dst)
    assert got == dst
    assert dst.read_bytes() == b"payload"
    assert dst.parent.is_dir()


def test_exists_present_and_missing(store: LocalStore, tmp_path: Path) -> None:
    assert store.exists("none.bin") is False
    src = tmp_path / "a.bin"
    src.write_bytes(b"x")
    store.put(src, "a.bin")
    assert store.exists("a.bin") is True
    assert store.exists("a.bin/extra") is False
    assert store.exists("") is False


def test_size_matches_written_bytes(store: LocalStore, tmp_path: Path) -> None:
    src = tmp_path / "a.bin"
    src.write_bytes(b"1234567890")
    store.put(src, "a.bin")
    assert store.size("a.bin") == 10


def test_keys_returns_relative_forward_slash_paths(store: LocalStore, tmp_path: Path) -> None:
    for i in range(3):
        p = tmp_path / f"f{i}.bin"
        p.write_bytes(b"x")
        store.put(p, f"sub/f{i}.bin")
    store.put(tmp_path / "f0.bin", "top.bin")
    keys = set(store.keys())
    assert keys == {"sub/f0.bin", "sub/f1.bin", "sub/f2.bin", "top.bin"}
    assert all("/" in k or k == "top.bin" for k in keys)
    assert not any("\\" in k for k in keys)


def test_keys_prefix_filter(store: LocalStore, tmp_path: Path) -> None:
    (tmp_path / "a.bin").write_bytes(b"a")
    (tmp_path / "b.bin").write_bytes(b"b")
    (tmp_path / "c.bin").write_bytes(b"c")
    store.put(tmp_path / "a.bin", "aa/1.bin")
    store.put(tmp_path / "b.bin", "ab/2.bin")
    store.put(tmp_path / "c.bin", "b/3.bin")
    assert set(store.keys("aa")) == {"aa/1.bin"}
    assert set(store.keys("ab")) == {"ab/2.bin"}
    assert set(store.keys("b")) == {"b/3.bin"}
    assert set(store.keys("a")) == set()  # literal path prefix, not substring
    assert store.keys("zz") == []


def test_delete_removes_and_is_silent_when_missing(store: LocalStore, tmp_path: Path) -> None:
    (tmp_path / "a.bin").write_bytes(b"x")
    store.put(tmp_path / "a.bin", "a.bin")
    assert store.exists("a.bin")
    store.delete("a.bin")
    assert store.exists("a.bin") is False
    store.delete("a.bin")  # must not raise
    assert store.keys() == []


def test_reopen_persists_objects(root: Path, tmp_path: Path) -> None:
    (tmp_path / "a.bin").write_bytes(b"aaa")
    (tmp_path / "b.bin").write_bytes(b"b.bin")
    s1 = LocalStore(root)
    s1.put(tmp_path / "a.bin", "p/q/a.bin")
    s1.put(tmp_path / "b.bin", "b.bin")
    s2 = LocalStore(root)
    assert s2.exists("p/q/a.bin") is True
    assert s2.exists("b.bin") is True
    dst = tmp_path / "out.bin"
    s2.get("b.bin", dst)
    assert dst.read_bytes() == b"b.bin"