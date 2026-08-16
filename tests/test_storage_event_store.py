"""Edge-case coverage of EventStore (src/academicos/storage/event_store.py).

This is a *companion* to the pre-existing tests/test_event_store.py (which
covers the happy-path append/monotonic-seq/roundtrip/since_seq/replay/stats);
it deliberately does not rewrite those and focuses on the corners:
payload persistence, durability across reopen, the UNIQUE(learner_id, seq)
constraint, batch appends, limit/ordering, incremental replay and the
event-id scheme.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from academicos.algorithms.learner_model import Interaction, LearnerModel
from academicos.storage.event_store import EventStore


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "events.sqlite"


@pytest.fixture
def store(db_path: Path) -> EventStore:
    s = EventStore(db_path)
    yield s
    s.close()


def _interaction(**kw) -> Interaction:
    kw.setdefault("concept_id", "fractions")
    kw.setdefault("kind", "answer")
    kw.setdefault("outcome", 1.0)
    return Interaction(**kw)


def test_payload_persisted_as_exact_json(store: EventStore) -> None:
    payload = {"mode": "practice", "nested": {"tags": [1, 2], "ok": True}}
    event_id, _ = store.append("alice", _interaction(), payload=payload)
    row = store.conn.execute(
        "SELECT payload FROM learner_events WHERE event_id=?", (event_id,)
    ).fetchone()
    assert row is not None
    assert row["payload"] == json.dumps(payload)  # exact serialized form
    assert json.loads(row["payload"]) == payload
    assert isinstance(row["payload"], str)


def test_append_without_payload_stores_null(store: EventStore) -> None:
    event_id, _ = store.append("alice", _interaction())
    row = store.conn.execute(
        "SELECT payload FROM learner_events WHERE event_id=?", (event_id,)
    ).fetchone()
    assert row["payload"] is None


def test_close_and_reopen_events_survive(db_path: Path) -> None:
    s = EventStore(db_path)
    s.append("alice", _interaction(concept_id="c", kind="answer", outcome=1.0))
    s.append("alice", _interaction(concept_id="c", kind="answer", outcome=0.0))
    s.append("bob", _interaction(concept_id="d", kind="watch"))
    s.close()

    s2 = EventStore(db_path)
    assert s2.last_seq("alice") == 2
    assert s2.last_seq("bob") == 1
    assert s2.learner_ids() == ["alice", "bob"]
    events = s2.events("alice")
    assert len(events) == 2
    assert [e.outcome for e in events] == [1.0, 0.0]
    s2.close()


def test_unique_learner_seq_rejects_duplicate_seq(store: EventStore) -> None:
    store.append("alice", _interaction())
    cols = ("learner_id", "seq", "event_id", "kind", "concept_id", "outcome",
            "bloom", "difficulty", "affect", "duration_sec", "ts", "payload")
    with pytest.raises(sqlite3.IntegrityError):
        store.conn.execute(
            "INSERT INTO learner_events (learner_id, seq, event_id, kind,"
            " concept_id, outcome, bloom, difficulty, affect, duration_sec, ts, payload)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            ("alice", 1, "ev:alice:different-id", "answer", "c", 1.0,
             None, None, None, None, "ts", None),
        )
        store.conn.commit()


def test_duplicate_event_id_rejected_even_for_other_learner(store: EventStore) -> None:
    store.append("alice", _interaction())
    with pytest.raises(sqlite3.IntegrityError):
        store.conn.execute(
            "INSERT INTO learner_events (learner_id, seq, event_id, kind,"
            " concept_id, outcome, bloom, difficulty, affect, duration_sec, ts, payload)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            ("bob", 1, "ev:alice:1", "answer", "c", 1.0,
             None, None, None, None, "ts", None),
        )
        store.conn.commit()


def test_append_many_then_last_seq(store: EventStore) -> None:
    n = store.append_many("alice", [_interaction() for _ in range(4)])
    assert n == 4
    assert store.last_seq("alice") == 4
    assert len(store.events("alice")) == 4


def test_append_many_empty_returns_zero(store: EventStore) -> None:
    assert store.append_many("alice", []) == 0
    assert store.last_seq("alice") == 0


def test_events_limit_truncates(store: EventStore) -> None:
    store.append_many("alice", [_interaction(outcome=float(i)) for i in range(1, 6)])
    got = store.events("alice", limit=2)
    assert len(got) == 2
    assert [e.outcome for e in got] == [1.0, 2.0]


def test_events_limit_combined_with_since_seq(store: EventStore) -> None:
    store.append_many("alice", [_interaction(outcome=float(i)) for i in range(1, 6)])
    got = store.events("alice", since_seq=2, limit=2)
    assert [e.outcome for e in got] == [3.0, 4.0]


def test_events_ordered_strictly_by_seq(store: EventStore) -> None:
    store.append_many("alice", [_interaction(outcome=float(i)) for i in (0.5, 0.0, 1.0, 0.25)])
    rows = store.conn.execute(
        "SELECT seq FROM learner_events WHERE learner_id='alice' ORDER BY seq"
    ).fetchall()
    assert [r["seq"] for r in rows] == [1, 2, 3, 4]
    assert [e.outcome for e in store.events("alice")] == [0.5, 0.0, 1.0, 0.25]


def test_replay_into_existing_model_is_incremental(store: EventStore) -> None:
    store.append("alice", _interaction(concept_id="c", outcome=1.0))
    store.append("alice", _interaction(concept_id="c", outcome=0.0))
    m = store.replay("alice")
    assert m.concepts["c"].attempts == 2
    assert m.concepts["c"].correct == 1

    store.append("alice", _interaction(concept_id="c", outcome=1.0))
    m2 = store.replay("alice", m)
    assert m2 is m
    assert m2.concepts["c"].attempts == 3
    assert m2.concepts["c"].correct == 2
    assert m2.concepts["c"].mastery == store.replay("alice").concepts["c"].mastery


def test_stats_zero_events_returns_zeros_not_none(store: EventStore) -> None:
    st = store.stats("nobody")
    assert st["events"] == 0
    assert st["answers"] == 0
    assert st["correct"] == 0
    assert st["kinds"] == {}
    assert st["first_ts"] is None
    assert st["last_ts"] is None


def test_stats_kinds_excludes_zero_and_answers_floor(store: EventStore) -> None:
    store.append_many("alice", [
        _interaction(kind="watch"),
        _interaction(kind="watch"),
    ])
    st = store.stats("alice")
    assert st["events"] == 2
    assert st["answers"] == 0
    assert st["correct"] == 0
    assert st["kinds"] == {"watch": 2}


def test_event_id_format(store: EventStore) -> None:
    eid1, seq1 = store.append("alice", _interaction())
    eid2, seq2 = store.append("bob", _interaction())
    assert eid1 == "ev:alice:1"
    assert eid2 == "ev:bob:1"
    assert seq1 == 1 and seq2 == 1
    eid3, seq3 = store.append("alice", _interaction())
    assert eid3 == "ev:alice:2"
    assert seq3 == 2


def test_events_returns_interaction_objects_without_payload(store: EventStore) -> None:
    store.append("alice", _interaction(), payload={"secret": "x"})
    got = store.events("alice")
    assert len(got) == 1
    assert isinstance(got[0], Interaction)
    assert not hasattr(got[0], "payload")