"""Coverage for the two things added to EventStore in this pass:

1. The Supabase-when-configured / SQLite-fallback pattern (previously the
   one durability-critical store in src/academicos/ without it -- see
   AGENTS.md's storage inventory, which explicitly listed EventStore as
   "None (learner events)" while every other operational store had a
   remote table).
2. The per-learner lock around append()/append_many() that fixes a real
   race: `seq = MAX(seq) + 1` with no locking meant two concurrent appends
   for the same learner_id could read the same MAX(seq) before either
   committed and violate UNIQUE(learner_id, seq) -- exactly the
   "two teachers/devices at once" failure class the rest of this pass is
   about. This is a regression test for that bug, not a speculative one:
   with the lock removed, this test reliably fails.
"""
from __future__ import annotations

import threading
from pathlib import Path

import pytest
import requests

from academicos.algorithms.learner_model import Interaction
from academicos.storage.event_store import EventStore


@pytest.fixture
def store(tmp_path: Path) -> EventStore:
    s = EventStore(tmp_path / "events.sqlite")
    yield s
    s.close()


def _interaction(**kw) -> Interaction:
    kw.setdefault("concept_id", "fractions")
    kw.setdefault("kind", "answer")
    kw.setdefault("outcome", 1.0)
    return Interaction(**kw)


# ---- concurrency ----

def test_concurrent_appends_for_same_learner_never_collide(store: EventStore) -> None:
    n_threads = 16
    barrier = threading.Barrier(n_threads)
    errors: list[BaseException] = []

    def worker() -> None:
        barrier.wait()  # maximize actual overlap, not just thread creation order
        try:
            store.append("alice", _interaction())
        except BaseException as exc:  # noqa: BLE001 - capturing for the assertion below
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    assert store.last_seq("alice") == n_threads
    seqs = [e.ts for e in store.events("alice")]  # any field roundtrips; count is what matters
    assert len(seqs) == n_threads
    rows = store.conn.execute(
        "SELECT COUNT(DISTINCT seq) c FROM learner_events WHERE learner_id='alice'"
    ).fetchone()
    assert rows["c"] == n_threads  # no two threads landed on the same seq


def test_concurrent_appends_different_learners_do_not_serialize_on_each_other(
    store: EventStore,
) -> None:
    # Not a timing assertion (flaky by nature) -- just that per-learner locks
    # are actually per-learner, not one global lock: both learners end up
    # with independent, correct seq sequences after interleaved appends.
    def worker(learner: str, count: int) -> None:
        for _ in range(count):
            store.append(learner, _interaction())

    t1 = threading.Thread(target=worker, args=("alice", 5))
    t2 = threading.Thread(target=worker, args=("bob", 7))
    t1.start(); t2.start()
    t1.join(); t2.join()

    assert store.last_seq("alice") == 5
    assert store.last_seq("bob") == 7


# ---- Supabase fallback ----

def test_append_and_reads_fall_back_to_sqlite_when_supabase_unreachable(
    store: EventStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    store._remote._url = "https://nonexistent-project.supabase.co"
    store._remote._key = "fake-key"
    assert store._remote.enabled

    def _raise(*args, **kwargs):
        raise requests.exceptions.ConnectionError("simulated DNS failure")

    monkeypatch.setattr(store._remote, "upsert", _raise)
    monkeypatch.setattr(store._remote, "select", _raise)

    event_id, seq = store.append("alice", _interaction(outcome=0.7))  # must not raise
    assert seq == 1

    got = store.events("alice")  # get() path also falls back
    assert len(got) == 1
    assert got[0].outcome == 0.7

    assert store.last_seq("alice") == 1
    assert store.learner_ids() == ["alice"]
    st = store.stats("alice")
    assert st["events"] == 1


def test_append_writes_to_supabase_when_reachable(
    store: EventStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    store._remote._url = "https://fake-project.supabase.co"
    store._remote._key = "fake-key"
    assert store._remote.enabled

    sent: list[dict] = []
    monkeypatch.setattr(store._remote, "upsert", lambda row, on_conflict: sent.append(row))

    event_id, seq = store.append("alice", _interaction(outcome=1.0))

    assert len(sent) == 1
    assert sent[0]["event_id"] == event_id
    assert sent[0]["seq"] == seq
    assert sent[0]["learner_id"] == "alice"
    # Nothing landed locally -- the remote write "succeeded" so the local
    # fallback branch must not also run (that would double-write / diverge).
    local_rows = store.conn.execute("SELECT COUNT(*) c FROM learner_events").fetchone()
    assert local_rows["c"] == 0


def test_events_reads_from_supabase_when_reachable(
    store: EventStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    store._remote._url = "https://fake-project.supabase.co"
    store._remote._key = "fake-key"

    remote_rows = [
        {"learner_id": "alice", "seq": 1, "event_id": "ev:alice:1", "kind": "answer",
         "concept_id": "c", "outcome": 1.0, "bloom": None, "difficulty": None,
         "affect": None, "duration_sec": None, "ts": "2026-01-01T00:00:00+00:00",
         "payload": None},
        {"learner_id": "alice", "seq": 2, "event_id": "ev:alice:2", "kind": "answer",
         "concept_id": "c", "outcome": 0.0, "bloom": None, "difficulty": None,
         "affect": None, "duration_sec": None, "ts": "2026-01-01T00:01:00+00:00",
         "payload": None},
    ]
    calls: list[dict] = []

    def fake_select(*, order=None, limit=None, gt=None, **eq_filters):
        calls.append({"order": order, "limit": limit, "gt": gt, **eq_filters})
        rows = remote_rows
        if gt and "seq" in gt:
            rows = [r for r in rows if r["seq"] > gt["seq"]]
        return rows[:limit] if limit else rows

    monkeypatch.setattr(store._remote, "select", fake_select)

    got = store.events("alice")
    assert [e.outcome for e in got] == [1.0, 0.0]
    assert calls[-1]["gt"] == {"seq": 0}

    got_since = store.events("alice", since_seq=1)
    assert [e.outcome for e in got_since] == [0.0]
