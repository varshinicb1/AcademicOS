"""The 2026-09-15 Render stress test caught this live: concurrent
GET /curriculum/boards reads returned rows whose fields all read back as
None (then 500'd in pydantic validation), because every method shared one
unlocked sqlite3 connection. These tests hammer the real store from many
threads at once -- with every statement funneled through the _exec /
_fetchone / _fetchall lock helpers, all reads must come back intact and
all writes must land, with zero exceptions.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest

from academicos.curriculum.store import CurriculumStore


@pytest.fixture
def store(tmp_path):
    s = CurriculumStore(tmp_path / "curriculum.sqlite")
    yield s
    s.close()


def test_concurrent_reads_never_return_corrupt_rows(store) -> None:
    board = store.create_board(name="CBSE", code="CBSE")
    errors: list[BaseException] = []

    def read_many() -> None:
        try:
            for _ in range(50):
                boards = store.list_boards()
                assert boards, "board vanished mid-read"
                for b in boards:
                    assert b.id and b.name and b.code, f"corrupt row: {b!r}"
                assert store.get_board(board.id) == board
        except BaseException as exc:  # noqa: BLE001 -- collected, asserted below
            errors.append(exc)

    with ThreadPoolExecutor(max_workers=16) as pool:
        for _ in range(16):
            pool.submit(read_many)

    assert not errors, f"{len(errors)} reader threads failed, first: {errors[0]!r}"


def test_concurrent_readers_and_writers_all_land(store) -> None:
    errors: list[BaseException] = []
    created: list[str] = []
    import threading

    created_lock = threading.Lock()

    def write_many(worker: int) -> None:
        try:
            for i in range(10):
                b = store.create_board(name=f"Board {worker}-{i}", code=f"B{worker}-{i}")
                assert b.id and b.name and b.code
                with created_lock:
                    created.append(b.id)
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    def read_many() -> None:
        try:
            for _ in range(50):
                for b in store.list_boards():
                    assert b.id and b.name and b.code, f"corrupt row: {b!r}"
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(write_many, w) for w in range(4)]
        futures += [pool.submit(read_many) for _ in range(8)]
        for f in futures:
            f.result()

    assert not errors, f"{len(errors)} threads failed, first: {errors[0]!r}"
    assert len(created) == 40
    assert len(set(created)) == 40
    for board_id in created:
        fetched = store.get_board(board_id)
        assert fetched is not None and fetched.id == board_id
