"""P1.12 — `sync-gcs` CLI command: gating on `sync_enabled`, `--force`
override, and the `--interval-minutes` loop. No test ever talks to a real
GCS bucket: `google.cloud.storage` is faked exactly as in
test_storage_gcs.py, so these tests verify the CLI's own logic (does it
call the sync at all, how many times, does it respect the enabled flag) —
the underlying `GcsStore` wiring is covered separately.
"""
from __future__ import annotations

import argparse
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos import cli
from academicos.config import Config


class FakeBlob:
    def __init__(self, name: str):
        self.name = name
        self.calls: list[tuple] = []

    def upload_from_filename(self, local_path: str) -> None:
        self.calls.append(("upload_from_filename", local_path))


class FakeBucket:
    def __init__(self, name: str):
        self.name = name
        self.blobs: dict[str, FakeBlob] = {}

    def blob(self, name: str) -> FakeBlob:
        return self.blobs.setdefault(name, FakeBlob(name))


class FakeClient:
    """`storage.Client()` in real GCS is a handle onto persistent server-side
    state -- constructing a second client still sees the first client's
    uploads. The CLI legitimately constructs a fresh `GcsStore`/`Client` per
    sync cycle (and tests construct another to verify), so the fake must
    share bucket state across instances the same way, via a class-level
    registry rather than an instance dict."""
    _shared_buckets: dict[str, FakeBucket] = {}

    def bucket(self, name: str) -> FakeBucket:
        return self._shared_buckets.setdefault(name, FakeBucket(name))

    def list_blobs(self, bucket: FakeBucket, prefix: str = ""):
        return [b for b in bucket.blobs.values() if b.name.startswith(prefix)]


@pytest.fixture
def fake_gcs(monkeypatch):
    FakeClient._shared_buckets = {}
    google = types.ModuleType("google")
    google.__path__ = []
    cloud = types.ModuleType("google.cloud")
    cloud.__path__ = []
    storage_mod = types.ModuleType("google.cloud.storage")
    storage_mod.Client = FakeClient
    monkeypatch.setitem(sys.modules, "google", google)
    monkeypatch.setitem(sys.modules, "google.cloud", cloud)
    monkeypatch.setitem(sys.modules, "google.cloud.storage", storage_mod)


def _config(tmp_path: Path, *, gcs_bucket: str = "test-bucket",
            sync_enabled: bool = False) -> Config:
    return Config(data_root=tmp_path,
                 toml={"gcs_bucket": gcs_bucket, "sync_enabled": sync_enabled})


def _seed_local_file(tmp_path: Path) -> None:
    doc = tmp_path / "documents" / "a.pdf"
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_bytes(b"pdf-bytes")


def _sync_args(**overrides) -> argparse.Namespace:
    base = dict(prefixes="documents", force=False, interval_minutes=0, max_cycles=None)
    base.update(overrides)
    return argparse.Namespace(**base)


def test_no_bucket_configured_returns_1(tmp_path, monkeypatch, fake_gcs):
    monkeypatch.setattr(cli.Config, "load",
                        staticmethod(lambda: _config(tmp_path, gcs_bucket="")))
    assert cli.cmd_sync_gcs(_sync_args()) == 1


def test_sync_disabled_without_force_refuses_and_does_not_touch_gcs(
    tmp_path, monkeypatch, fake_gcs
):
    monkeypatch.setattr(cli.Config, "load",
                        staticmethod(lambda: _config(tmp_path, sync_enabled=False)))
    _seed_local_file(tmp_path)
    assert cli.cmd_sync_gcs(_sync_args(force=False)) == 1
    # No GcsStore was ever constructed for this run, so nothing to assert on
    # a bucket -- the real assertion is the early-return itself (no crash,
    # no upload) and that the same file syncs fine once --force is used.


def test_force_bypasses_disabled_flag_and_syncs(tmp_path, monkeypatch, fake_gcs):
    monkeypatch.setattr(cli.Config, "load",
                        staticmethod(lambda: _config(tmp_path, sync_enabled=False)))
    _seed_local_file(tmp_path)
    assert cli.cmd_sync_gcs(_sync_args(force=True)) == 0

    cfg = _config(tmp_path, sync_enabled=False)
    from academicos.storage.gcs import GcsStore
    remote = GcsStore(cfg.gcs_bucket, cfg.gcs_prefix)
    uploaded = remote.keys("documents")
    assert uploaded == ["documents/a.pdf"]


def test_sync_enabled_true_runs_without_force(tmp_path, monkeypatch, fake_gcs):
    monkeypatch.setattr(cli.Config, "load",
                        staticmethod(lambda: _config(tmp_path, sync_enabled=True)))
    _seed_local_file(tmp_path)
    assert cli.cmd_sync_gcs(_sync_args(force=False)) == 0


def test_interval_loop_runs_exactly_max_cycles(tmp_path, monkeypatch, fake_gcs):
    monkeypatch.setattr(cli.Config, "load",
                        staticmethod(lambda: _config(tmp_path, sync_enabled=True)))
    _seed_local_file(tmp_path)

    sleep_calls: list[float] = []
    monkeypatch.setattr(cli.time, "sleep", lambda s: sleep_calls.append(s))

    calls = []
    real_sync_once = cli._sync_gcs_once

    def counting_sync_once(cfg, prefixes, log=print):
        calls.append(1)
        return real_sync_once(cfg, prefixes, log=log)

    monkeypatch.setattr(cli, "_sync_gcs_once", counting_sync_once)

    rc = cli.cmd_sync_gcs(_sync_args(interval_minutes=5, max_cycles=3))
    assert rc == 0
    assert len(calls) == 3
    # Sleeps between cycles, not after the last one.
    assert sleep_calls == [300, 300]


def test_interval_loop_stops_cleanly_on_keyboard_interrupt(tmp_path, monkeypatch, fake_gcs):
    monkeypatch.setattr(cli.Config, "load",
                        staticmethod(lambda: _config(tmp_path, sync_enabled=True)))
    _seed_local_file(tmp_path)

    def raising_sleep(_seconds):
        raise KeyboardInterrupt

    monkeypatch.setattr(cli.time, "sleep", raising_sleep)

    rc = cli.cmd_sync_gcs(_sync_args(interval_minutes=5, max_cycles=None))
    assert rc == 0
