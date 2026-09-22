"""Coverage for CurriculumStore's Supabase snapshot/restore durability fix.

CurriculumStore was the last store AGENTS.md's inventory listed as
"Deferred (Target for Path B)" -- everything else durability-critical
already had a Supabase path. Unlike the flat single-object stores, this
one snapshots/restores the whole SQLite file as a blob via SupabaseStorage
rather than wrapping each of its 18 tables individually (see the module
docstring in curriculum/store.py for why). The mechanism is
storage/snapshot_sync.py, tested directly in tests/test_snapshot_sync.py;
these tests prove CurriculumStore is wired to it, through the actual
mechanism: restore-on-fresh-container is the concrete "redeploy doesn't
wipe the curriculum" scenario this whole pass exists to fix.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import requests

from academicos.curriculum.store import CurriculumStore


def _enable_remote(store: CurriculumStore) -> None:
    store._snapshots.remote._url = "https://fake-project.supabase.co"
    store._snapshots.remote._key = "fake-key"
    assert store._snapshots.remote.enabled


def test_no_remote_by_default(tmp_path: Path) -> None:
    store = CurriculumStore(tmp_path / "curriculum.sqlite")
    assert store._snapshots.remote.enabled is False
    store.create_board("CBSE", "cbse")  # must not attempt any network call
    store.close()


def test_snapshot_uploads_after_write_when_enabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = CurriculumStore(tmp_path / "curriculum.sqlite")
    _enable_remote(store)
    store._snapshots._last_upload_at = 0.0  # force past the debounce window

    uploaded: list[tuple[str, bytes, str]] = []
    monkeypatch.setattr(
        store._snapshots.remote, "upload",
        lambda key, data, content_type: uploaded.append((key, data, content_type)),
    )

    store.create_board("CBSE", "cbse")

    assert len(uploaded) == 1
    key, data, content_type = uploaded[0]
    assert key == "curriculum.sqlite"
    assert content_type == "application/x-sqlite3"
    assert data.startswith(b"SQLite format 3")  # a real, complete db file, not a fragment
    store.close()




def test_snapshot_upload_failure_does_not_break_the_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = CurriculumStore(tmp_path / "curriculum.sqlite")
    _enable_remote(store)
    store._snapshots._last_upload_at = 0.0

    def _raise(*args, **kwargs):
        raise requests.exceptions.ConnectionError("simulated failure")

    monkeypatch.setattr(store._snapshots.remote, "upload", _raise)

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
    store1._snapshots._last_upload_at = 0.0
    snapshots: list[bytes] = []
    monkeypatch.setattr(
        store1._snapshots.remote, "upload",
        lambda key, data, content_type: snapshots.append(data),
    )
    board = store1.create_board("CBSE", "cbse")
    store1._snapshots._last_upload_at = 0.0  # past the debounce window again for the 2nd write
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

    # CurriculumStore.__init__ constructs its SnapshotSync, which builds its
    # own blob store (storage/blobs.py's durable_blob_store, SupabaseStorage
    # when only Supabase is configured) and restores before __init__ has
    # returned an instance to monkeypatch -- so the fake has to be injected by
    # patching the factory storage/snapshot_sync.py uses, not by patching an
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
        "academicos.storage.snapshot_sync.durable_blob_store", fake_supabase_storage_ctor
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


def _fake_supabase_storage(monkeypatch: pytest.MonkeyPatch, download):
    from academicos.assessment.supabase_kv import SupabaseStorage
    fake_storage = SupabaseStorage("curriculum-snapshots")
    fake_storage._url = "https://fake-project.supabase.co"
    fake_storage._key = "fake-key"
    monkeypatch.setattr(fake_storage, "download", download)
    monkeypatch.setattr(fake_storage, "upload", lambda key, data, content_type: None)
    monkeypatch.setattr(
        "academicos.storage.snapshot_sync.durable_blob_store", lambda bucket: fake_storage
    )
    return fake_storage


def _http_error(status: int, body: str) -> requests.exceptions.HTTPError:
    response = requests.Response()
    response.status_code = status
    response._content = body.encode()
    return requests.exceptions.HTTPError(f"{status} error", response=response)


@pytest.mark.parametrize("status,body", [
    # Supabase Storage answers a missing object with 400 + a not_found body
    # on older deployments and a plain 404 on newer ones; both mean first boot.
    (400, '{"statusCode":"404","error":"not_found","message":"Object not found"}'),
    (404, '{"error":"not_found"}'),
])
def test_no_snapshot_yet_falls_back_to_fresh_empty_db(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, status: int, body: str
) -> None:
    db_path = tmp_path / "curriculum.sqlite"

    def _missing(key: str):
        raise _http_error(status, body)

    _fake_supabase_storage(monkeypatch, _missing)
    store = CurriculumStore(db_path)  # first-ever boot: a fresh db, no error
    try:
        assert store.list_boards() == []
        board = store.create_board("CBSE", "cbse")
        assert store.get_board(board.id) is not None
    finally:
        store.close()


def test_unreachable_snapshot_store_refuses_to_boot_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unreachable is not "no snapshot yet". This used to fall through to an
    empty database too, which served a blank curriculum as if it were real --
    and whatever an admin re-entered into it was overwritten by nothing and
    lost at the next restart. Now the constructor fails (503 at the route, a
    failed startup at boot) and the next attempt restores properly."""
    from academicos.storage.blobs import CurriculumNotDurable
    db_path = tmp_path / "curriculum.sqlite"

    def _raise(key: str):
        raise requests.exceptions.ConnectionError("unreachable")

    _fake_supabase_storage(monkeypatch, _raise)
    with pytest.raises(CurriculumNotDurable):
        CurriculumStore(db_path)
    assert not db_path.exists()

    def _server_error(key: str):
        raise _http_error(500, "internal error")

    _fake_supabase_storage(monkeypatch, _server_error)
    with pytest.raises(CurriculumNotDurable):
        CurriculumStore(db_path)
