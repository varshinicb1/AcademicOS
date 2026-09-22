"""storage/snapshot_sync.py: one SQLite file kept in sync with one blob.

Why these tests exist: the snapshot sync (restore on start, debounced upload,
upload lock, generation-guarded conflict handling, conflict copy, reload,
wedge, shutdown flush) used to live inside CurriculumStore, a curriculum
domain class, where it could only be tested through board and year writes.
It now lives in storage/, and these tests drive it directly: a bare sqlite3
connection with one table, the same in-memory GCS fake as
tests/test_blob_factory.py (real generation semantics, HTTP 412 on a stale
precondition), and no network.

The store-level tests that prove CurriculumStore is wired to it stay in
tests/test_blob_factory.py and tests/test_curriculum_store_supabase.py.
"""
from __future__ import annotations

import logging
import sqlite3
import threading
import time
from pathlib import Path

import pytest
import requests

# The fake and its fixtures are shared with the blob-factory tests on purpose:
# one fake, one set of GCS assumptions (tests/test_gcs_blob_integration.py
# checks them against the real service).
from test_blob_factory import (  # noqa: F401 - fixtures are used by name
    BUCKET,
    FakeGcsClient,
    _boards_in,
    _conflict_copies,
    _fresh_blob_status,
    _snapshot,
    clean_env,
    shared_gcs,
)

from academicos.storage import blobs
from academicos.storage.blobs import CurriculumNotDurable
from academicos.storage.snapshot_sync import SnapshotSync, flush_all_snapshots


class Db:
    """A SQLite file with one `boards` table, synced by a SnapshotSync --
    the smallest thing that uses the sync the way CurriculumStore does: one
    shared connection, one RLock, every commit through sync.commit()."""

    def __init__(self, db_path: Path, **kw):
        self.lock = threading.RLock()
        # Constructing the sync restores the remote snapshot BEFORE the
        # connection opens, exactly as CurriculumStore.__init__ does.
        self.sync = SnapshotSync("curriculum-snapshots", "curriculum.sqlite",
                                 db_path, self.lock, **kw)
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("CREATE TABLE IF NOT EXISTS boards (code TEXT PRIMARY KEY)")
        self.sync.commit(self.conn)       # a schema no-op: must not upload

    def add(self, code: str) -> None:
        with self.lock:
            self.conn.execute("INSERT INTO boards (code) VALUES (?)", (code,))
        self.sync.commit(self.conn)

    def codes(self) -> set[str]:
        with self.lock:
            return {r[0] for r in self.conn.execute("SELECT code FROM boards")}

    def close(self) -> None:
        self.sync.close()
        self.conn.close()


def _db(tmp_path: Path, name: str, **kw) -> Db:
    return Db(tmp_path / name / "curriculum.sqlite", **kw)


# --------------------------------------------------------------------------- #
# upload
# --------------------------------------------------------------------------- #

def test_a_commit_that_changed_rows_uploads_the_whole_file(shared_gcs, tmp_path: Path) -> None:
    db = _db(tmp_path, "a")
    assert "academicos/curriculum-snapshots/curriculum.sqlite" not in \
        shared_gcs.bucket(BUCKET).objects, "a schema-only commit must not upload"
    db.add("cbse")
    stored = _snapshot(shared_gcs)
    assert stored["content_type"] == "application/x-sqlite3"
    assert stored["data"].startswith(b"SQLite format 3")   # a real db, not a WAL fragment
    assert _boards_in(stored["data"], tmp_path) == {"cbse"}
    db.close()


def test_disabled_remote_is_a_plain_commit(clean_env, tmp_path: Path) -> None:
    """Local dev: no bucket, no Supabase. The sync must be a no-op that still
    commits, or every local write would be lost at connection close."""
    db = _db(tmp_path, "local")
    assert db.sync.remote.enabled is False
    db.add("cbse")
    db.close()
    conn = sqlite3.connect(str(tmp_path / "local" / "curriculum.sqlite"))
    try:
        assert {r[0] for r in conn.execute("SELECT code FROM boards")} == {"cbse"}
    finally:
        conn.close()


def test_a_commit_inside_the_window_is_deferred_not_uploaded_at_once(
        shared_gcs, tmp_path: Path) -> None:
    db = _db(tmp_path, "a")
    db.add("cbse")                       # past the window: uploads now
    db.add("icse")                       # inside the 30 s window: deferred
    assert _boards_in(_snapshot(shared_gcs)["data"], tmp_path) == {"cbse"}
    db.close()                           # close's final flush carries it
    assert _boards_in(_snapshot(shared_gcs)["data"], tmp_path) == {"cbse", "icse"}


def test_edits_inside_the_debounce_window_are_uploaded_after_it(
        shared_gcs, tmp_path: Path) -> None:
    """The debounce used to DROP a commit that landed inside the window: no
    dirty flag, no trailing upload. An admin's burst of edits then reached GCS
    only as its first edit, and the rest died with the container. Two commits
    a moment apart must both be in the remote object once the window has
    passed, with no further commit to carry them."""
    db = _db(tmp_path, "a", debounce_seconds=0.6)   # the 30 s window, scaled
    db.add("cbse")
    assert _boards_in(_snapshot(shared_gcs)["data"], tmp_path) == {"cbse"}
    time.sleep(0.2)
    db.add("icse")

    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        if _boards_in(_snapshot(shared_gcs)["data"], tmp_path) == {"cbse", "icse"}:
            break
        time.sleep(0.05)
    assert _boards_in(_snapshot(shared_gcs)["data"], tmp_path) == {"cbse", "icse"}
    db.close()


def test_a_failed_upload_does_not_fail_the_commit_and_is_retried(
        shared_gcs, tmp_path: Path) -> None:
    db = _db(tmp_path, "a")
    shared_gcs.fail_reads_and_writes = True
    db.add("cbse")                                   # must not raise
    assert db.codes() == {"cbse"}
    assert blobs.blob_status()["curriculum_snapshot_upload_failures"] == 1
    assert db.sync._timer is not None, "a failed upload must re-arm the retry"

    shared_gcs.fail_reads_and_writes = False
    assert db.sync.flush() is True                   # the retry lands
    assert _boards_in(_snapshot(shared_gcs)["data"], tmp_path) == {"cbse"}
    db.close()


def test_flush_all_snapshots_uploads_every_pending_edit(shared_gcs, tmp_path: Path) -> None:
    """Cloud Run sends SIGTERM and allows 10 s; api/main.py's shutdown hook
    calls flush_all_snapshots() inside that window. Whatever the debounce is
    still holding must go now or it dies with the container."""
    db = _db(tmp_path, "a")
    db.add("cbse")                                   # uploads
    db.add("icse")                                   # held by the debounce
    db.add("state")
    assert _boards_in(_snapshot(shared_gcs)["data"], tmp_path) == {"cbse"}
    flush_all_snapshots()
    assert _boards_in(_snapshot(shared_gcs)["data"], tmp_path) == {"cbse", "icse", "state"}
    db.close()


def test_close_stops_the_trailing_timer(shared_gcs, tmp_path: Path) -> None:
    """No timer may touch a connection the owner has closed."""
    db = _db(tmp_path, "a")
    db.add("cbse")
    db.add("icse")
    assert db.sync._timer is not None
    db.close()
    assert db.sync._timer is None
    assert db.sync.flush() is True                   # closed: nothing to do, no error


# --------------------------------------------------------------------------- #
# restore on start
# --------------------------------------------------------------------------- #

def test_a_fresh_file_restores_the_last_snapshot(shared_gcs, tmp_path: Path) -> None:
    seed = _db(tmp_path, "seed")
    seed.add("cbse")
    seed.close()
    fresh = _db(tmp_path, "fresh")
    assert fresh.codes() == {"cbse"}
    fresh.close()


def test_first_boot_with_no_snapshot_starts_fresh(shared_gcs, tmp_path: Path) -> None:
    db = _db(tmp_path, "a")                          # BlobNotFound, acknowledged
    assert db.codes() == set()
    db.close()


def test_empty_gcs_boot_needs_an_explicit_acknowledgement(
        shared_gcs, tmp_path: Path, monkeypatch) -> None:
    """On GCS, "no object" is also what a service migrated off Supabase sees
    before the copy script runs; starting empty there serves a blank
    curriculum as if it were the school's."""
    monkeypatch.delenv("ACOS_CURRICULUM_ALLOW_EMPTY_BOOT")
    db_path = tmp_path / "fresh" / "curriculum.sqlite"
    with pytest.raises(CurriculumNotDurable) as info:
        SnapshotSync("curriculum-snapshots", "curriculum.sqlite", db_path, threading.RLock())
    assert "migrate_supabase_blobs_to_gcs.py" in str(info.value)
    assert "ACOS_CURRICULUM_ALLOW_EMPTY_BOOT" in str(info.value)
    assert not db_path.exists(), "a refused boot must leave nothing to boot from"


def test_unreachable_remote_refuses_to_start_empty(shared_gcs, tmp_path: Path) -> None:
    """Unreachable is not "no snapshot yet". The constructor must raise and
    leave no local file, so the retry Cloud Run makes restores properly."""
    seed = _db(tmp_path, "seed")
    seed.add("cbse")
    seed.close()

    shared_gcs.fail_reads_and_writes = True
    db_path = tmp_path / "fresh" / "curriculum.sqlite"
    with pytest.raises(CurriculumNotDurable):
        SnapshotSync("curriculum-snapshots", "curriculum.sqlite", db_path, threading.RLock())
    assert not db_path.exists()

    shared_gcs.fail_reads_and_writes = False
    fresh = Db(db_path)
    assert fresh.codes() == {"cbse"}
    fresh.close()


def test_an_existing_local_file_is_never_overwritten_by_the_remote(
        shared_gcs, tmp_path: Path) -> None:
    """A container that already has its file (a restart within one disk
    lifetime) keeps it; the remote copy may be older."""
    seed = _db(tmp_path, "seed")
    seed.add("cbse")
    seed.close()
    local = _db(tmp_path, "local")                   # restores {cbse}
    local.close()
    other = _db(tmp_path, "other")                   # remote moves on to {cbse, state}
    other.add("state")
    other.close()
    again = _db(tmp_path, "local")                   # file exists: no restore
    assert again.codes() == {"cbse"}
    again.close()


# --------------------------------------------------------------------------- #
# single writer: conflict, copy, reload, wedge
# --------------------------------------------------------------------------- #

def test_stale_write_is_refused_reloaded_and_the_retry_lands(
        shared_gcs, tmp_path: Path, caplog) -> None:
    """Two instances, one snapshot blob -- every Cloud Run rollout. B restores
    A's snapshot and writes after it; A must not replace B's snapshot with its
    older copy, must answer the refused edit with a real "not saved"
    (CurriculumNotDurable -> 503), must reload B's snapshot, and its retry
    must land on top of B's."""
    a = _db(tmp_path, "a")
    a.add("cbse")
    b = _db(tmp_path, "b")                           # restores A's
    b.add("state")
    after_b = _snapshot(shared_gcs)

    a.sync._last_upload_at = 0.0                     # past A's window
    with caplog.at_level(logging.ERROR, logger="academicos.storage.blobs"):
        with pytest.raises(CurriculumNotDurable):
            a.add("icse")

    assert _snapshot(shared_gcs) == after_b, "A silently erased B's snapshot"
    assert any("refused" in r.getMessage().lower() for r in caplog.records)
    assert blobs.blob_status()["curriculum_snapshot_conflict_count"] == 1
    assert a.codes() == {"cbse", "state"}            # B's view, A's refused edit gone

    a.sync._last_upload_at = 0.0
    a.add("icse")
    assert _snapshot(shared_gcs)["generation"] > after_b["generation"]
    assert _boards_in(_snapshot(shared_gcs)["data"], tmp_path) == {"cbse", "state", "icse"}
    a.close()
    b.close()


def test_deferred_edit_that_loses_a_conflict_is_preserved_not_destroyed(
        shared_gcs, tmp_path: Path, caplog) -> None:
    """A uploads; B restores; A commits ICSE inside the debounce window (the
    request already answered success); B writes; A's trailing timer meets B's
    generation. The reload used to throw ICSE away. The losing file must be
    uploaded, byte for byte, to conflicts/ BEFORE the reload, and health and
    the ERROR log must name it."""
    a = _db(tmp_path, "a")
    a.add("cbse")
    b = _db(tmp_path, "b")
    a.add("icse")                                    # deferred, "saved"
    b.add("state")
    after_b = _snapshot(shared_gcs)

    with caplog.at_level(logging.ERROR):
        a.sync._trailing()                           # the timer thread's call, inline

    assert _snapshot(shared_gcs) == after_b
    (copy_key, copy), = _conflict_copies(shared_gcs).items()
    assert _boards_in(copy["data"], tmp_path) == {"cbse", "icse"}
    assert a.codes() == {"cbse", "state"}            # A now serves B's view
    status = blobs.blob_status()
    assert status["curriculum_snapshot_conflict_copies"] == 1
    assert status["curriculum_snapshot_last_conflict_copy"] == copy_key.split(
        "academicos/curriculum-snapshots/", 1)[1]
    assert any(status["curriculum_snapshot_last_conflict_copy"] in r.getMessage()
               for r in caplog.records)
    a.close()
    b.close()


def test_shutdown_flush_that_loses_a_conflict_is_preserved(
        shared_gcs, tmp_path: Path) -> None:
    old = _db(tmp_path, "old")
    old.add("cbse")
    new = _db(tmp_path, "new")
    old.add("icse")                                  # deferred on the old revision
    new.add("state")
    assert old.sync.flush() is False                 # the shutdown hook's call
    (copy,) = _conflict_copies(shared_gcs).values()
    assert _boards_in(copy["data"], tmp_path) == {"cbse", "icse"}
    old.close()
    new.close()


def test_conflict_copy_that_cannot_be_saved_wedges_and_keeps_the_local_file(
        shared_gcs, tmp_path: Path, monkeypatch) -> None:
    """If the losing file cannot be preserved, reloading would destroy it.
    Keep it and wedge (every later commit raises -> 503) instead."""
    a = _db(tmp_path, "a")
    a.add("cbse")
    b = _db(tmp_path, "b")
    a.add("icse")
    b.add("state")

    real_upload = a.sync.remote.upload

    def upload(key, data, content_type):
        if key.startswith("conflicts/"):
            raise blobs.BlobUnavailable("simulated: conflict copy upload failed")
        return real_upload(key, data, content_type)

    monkeypatch.setattr(a.sync.remote, "upload", upload)
    a.sync._trailing()
    assert a.codes() == {"cbse", "icse"}, "the unsaved edit was discarded"
    with pytest.raises(CurriculumNotDurable):
        a.add("more")
    a.close()
    b.close()


def test_a_failed_reload_wedges(shared_gcs, tmp_path: Path, monkeypatch) -> None:
    a = _db(tmp_path, "a")
    a.add("cbse")
    b = _db(tmp_path, "b")
    a.add("icse")
    b.add("state")

    def broken_download(key):
        raise requests.exceptions.ConnectionError("simulated: reload failed")

    monkeypatch.setattr(a.sync.remote, "download", broken_download)
    a.sync._trailing()
    assert _conflict_copies(shared_gcs), "the copy is saved before the reload"
    with pytest.raises(CurriculumNotDurable):
        a.add("more")
    a.close()
    b.close()
