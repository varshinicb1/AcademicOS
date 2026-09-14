"""Coverage for CurriculumStore's Supabase snapshot/restore durability fix.

CurriculumStore was the last store AGENTS.md's inventory listed as
"Deferred (Target for Path B)" -- everything else durability-critical
already had a Supabase path. Unlike the flat single-object stores, this
one snapshots/restores the whole SQLite file as a blob via SupabaseStorage
rather than wrapping each of its 18 tables individually (see the module
docstring in curriculum/store.py for why). These tests exercise the actual
mechanism: restore-on-fresh-container is the concrete "redeploy doesn't
wipe the curriculum" scenario this whole pass exists to fix.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import requests

from academicos.curriculum.store import CurriculumStore


def _enable_remote(store: CurriculumStore) -> None:
    store._remote_storage._url = "https://fake-project.supabase.co"
    store._remote_storage._key = "fake-key"
    assert store._remote_storage.enabled


def test_no_remote_by_default(tmp_path: Path) -> None:
    store = CurriculumStore(tmp_path / "curriculum.sqlite")
    assert store._remote_storage.enabled is False
    store.create_board("CBSE", "cbse")  # must not attempt any network call
    store.close()


def test_snapshot_uploads_after_write_when_enabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = CurriculumStore(tmp_path / "curriculum.sqlite")
    _enable_remote(store)
    store._last_snapshot_at = 0.0  # force past the debounce window

    uploaded: list[tuple[str, bytes, str]] = []
    monkeypatch.setattr(
        store._remote_storage, "upload",
        lambda key, data, content_type: uploaded.append((key, data, content_type)),
    )

    store.create_board("CBSE", "cbse")

    assert len(uploaded) == 1
    key, data, content_type = uploaded[0]
    assert key == "curriculum.sqlite"
    assert content_type == "application/x-sqlite3"
    assert data.startswith(b"SQLite format 3")  # a real, complete db file, not a fragment
    store.close()


def test_snapshot_debounced_within_window(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = CurriculumStore(tmp_path / "curriculum.sqlite")
    _enable_remote(store)
    store._last_snapshot_at = 0.0

    uploaded: list[bytes] = []
    monkeypatch.setattr(
        store._remote_storage, "upload",
        lambda key, data, content_type: uploaded.append(data),
    )

    store.create_board("CBSE", "cbse")   # first write: past debounce, uploads
    store.create_board("ICSE", "icse")   # second write: within debounce window, skipped

    assert len(uploaded) == 1
    store.close()


def test_snapshot_upload_failure_does_not_break_the_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = CurriculumStore(tmp_path / "curriculum.sqlite")
    _enable_remote(store)
    store._last_snapshot_at = 0.0

    def _raise(*args, **kwargs):
        raise requests.exceptions.ConnectionError("simulated failure")

    monkeypatch.setattr(store._remote_storage, "upload", _raise)

    board = store.create_board("CBSE", "cbse")  # must not raise
    assert store.get_board(board.id) is not None
    store.close()


def test_restore_on_fresh_container_recovers_real_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The actual durability scenario: a container with no prior local
    state (fresh Render deploy) restores the last snapshot instead of
    starting empty."""
    db_path = tmp_path / "curriculum.sqlite"

    # --- "old container": write real data, capture what gets uploaded ---
    store1 = CurriculumStore(db_path)
    _enable_remote(store1)
    store1._last_snapshot_at = 0.0
    snapshots: list[bytes] = []
    monkeypatch.setattr(
        store1._remote_storage, "upload",
        lambda key, data, content_type: snapshots.append(data),
    )
    board = store1.create_board("CBSE", "cbse")
    store1._last_snapshot_at = 0.0  # past the debounce window again for the 2nd write
    year = store1.create_academic_year(
        school_id="school_1", label="2026-27", start_date="2026-06-01", end_date="2027-04-30",
    )
    store1.close()
    assert snapshots  # sanity: the write above did trigger a real upload
    last_snapshot = snapshots[-1]

    # --- simulate a fresh container: same path, but no local file (as if
    # Render just spun up a brand-new one from the baked image) ---
    db_path.unlink()
    assert not db_path.exists()

    # CurriculumStore.__init__ constructs its own SupabaseStorage internally
    # and checks `.enabled` before __init__ has returned an instance to
    # monkeypatch -- so the fake has to be injected by patching the
    # SupabaseStorage constructor the module uses, not by patching an
    # instance after the fact.
    from academicos.assessment.supabase_kv import SupabaseStorage
    fake_storage = SupabaseStorage("curriculum-snapshots")
    fake_storage._url = "https://fake-project.supabase.co"
    fake_storage._key = "fake-key"
    monkeypatch.setattr(fake_storage, "download", lambda key: last_snapshot)
    # __init__'s own final _commit() will try to re-snapshot after restoring
    # (enabled + past debounce on a fresh instance) -- not under test here.
    monkeypatch.setattr(fake_storage, "upload", lambda key, data, content_type: None)

    def fake_supabase_storage_ctor(bucket: str) -> SupabaseStorage:
        assert bucket == "curriculum-snapshots"
        return fake_storage

    monkeypatch.setattr(
        "academicos.curriculum.store.SupabaseStorage", fake_supabase_storage_ctor
    )

    store2 = CurriculumStore(db_path)  # should restore from `last_snapshot` before opening
    try:
        assert store2.get_board(board.id) is not None
        assert store2.get_board(board.id).code == "cbse"
        restored_years = store2.academic_years_for_school("school_1")
        assert len(restored_years) == 1
        assert restored_years[0].label == "2026-27"
    finally:
        store2.close()


def test_restore_failure_falls_back_to_fresh_empty_db(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = tmp_path / "curriculum.sqlite"
    assert not db_path.exists()

    from academicos.assessment.supabase_kv import SupabaseStorage
    fake_storage = SupabaseStorage("curriculum-snapshots")
    fake_storage._url = "https://fake-project.supabase.co"
    fake_storage._key = "fake-key"

    def _raise(key: str):
        raise requests.exceptions.ConnectionError("no snapshot yet / unreachable")

    monkeypatch.setattr(fake_storage, "download", _raise)
    monkeypatch.setattr(
        "academicos.curriculum.store.SupabaseStorage", lambda bucket: fake_storage
    )

    store = CurriculumStore(db_path)  # must not raise -- falls through to a fresh db
    try:
        assert store.list_boards() == []
        board = store.create_board("CBSE", "cbse")
        assert store.get_board(board.id) is not None
    finally:
        store.close()
