from pathlib import Path

import pytest

from academicos.algorithms.learner_model import Interaction, LearnerModel
from academicos.storage.event_store import EventStore


@pytest.fixture
def store(tmp_path: Path) -> EventStore:
    s = EventStore(tmp_path / "events.sqlite")
    yield s
    s.close()


def test_append_assigns_monotonic_seq(store: EventStore) -> None:
    a = Interaction(concept_id="fractions", kind="answer", outcome=1.0)
    b = Interaction(concept_id="fractions", kind="answer", outcome=0.0)
    _, seq1 = store.append("alice", a)
    _, seq2 = store.append("alice", b)
    assert seq2 == seq1 + 1
    assert store.last_seq("alice") == seq2
    assert store.last_seq("bob") == 0


def test_events_roundtrip_fields(store: EventStore) -> None:
    i = Interaction(concept_id="fractions", kind="attempt", outcome=0.3,
                    bloom="apply", difficulty=0.6, affect="frustrated",
                    duration_sec=42.0)
    store.append("alice", i)
    got = store.events("alice")
    assert len(got) == 1
    e = got[0]
    assert e.concept_id == "fractions"
    assert e.kind == "attempt"
    assert e.outcome == 0.3
    assert e.bloom == "apply"
    assert e.difficulty == 0.6
    assert e.affect == "frustrated"
    assert e.duration_sec == 42.0
    assert e.ts == i.ts


def test_events_since_seq(store: EventStore) -> None:
    for o in (1.0, 0.0, 0.5):
        store.append("alice", Interaction(concept_id="c", kind="answer", outcome=o))
    got = store.events("alice", since_seq=1)
    assert len(got) == 2
    assert [e.outcome for e in got] == [0.0, 0.5]


def test_replay_rebuilds_model_equivalent_to_manual_observe(store: EventStore) -> None:
    events = [
        Interaction(concept_id="fractions", kind="answer", outcome=1.0),
        Interaction(concept_id="fractions", kind="answer", outcome=0.0),
        Interaction(concept_id="fractions", kind="attempt", outcome=0.3,
                    affect="frustrated"),
        Interaction(concept_id="division", kind="watch", duration_sec=120.0),
    ]
    store.append_many("alice", events)

    manual = LearnerModel(learner_id="alice")
    for i in events:
        manual.observe(i)

    rebuilt = store.replay("alice")
    assert rebuilt.concepts.keys() == {"fractions", "division"}
    for cid, cs in rebuilt.concepts.items():
        assert cs.attempts == manual.concepts[cid].attempts
        assert cs.correct == manual.concepts[cid].correct
        assert cs.mastery == manual.concepts[cid].mastery
        assert cs.last_seen == manual.concepts[cid].last_seen
        assert len(cs.history) == len(manual.concepts[cid].history)


def test_replay_is_deterministic_across_fresh_stores(store: EventStore) -> None:
    events = [Interaction(concept_id="c", kind="answer", outcome=o)
              for o in (1.0, 0.0, 0.5, 1.0, 1.0)]
    store.append_many("alice", events)
    db_path = Path(store.conn.execute("PRAGMA database_list").fetchone()["file"])
    store.close()

    s2 = EventStore(db_path)
    m1 = s2.replay("alice")
    m2 = s2.replay("alice")
    assert m1.concepts["c"].mastery == m2.concepts["c"].mastery
    assert m1.concepts["c"].correct == m2.concepts["c"].correct
    s2.close()


def test_replay_unknown_learner_is_empty(store: EventStore) -> None:
    m = store.replay("nobody")
    assert m.learner_id == "nobody"
    assert m.concepts == {}


def test_stats_aggregates(store: EventStore) -> None:
    store.append_many("alice", [
        Interaction(concept_id="c", kind="answer", outcome=1.0),
        Interaction(concept_id="c", kind="answer", outcome=0.0),
        Interaction(concept_id="d", kind="watch", duration_sec=60.0),
    ])
    st = store.stats("alice")
    assert st["events"] == 3
    assert st["answers"] == 2
    assert st["correct"] == 1
    assert st["kinds"] == {"answer": 2, "watch": 1}


def test_append_with_payload_and_learner_ids(store: EventStore) -> None:
    store.append("alice", Interaction(concept_id="c", kind="answer", outcome=1.0),
                 payload={"mode": "practice", "page": 3})
    store.append("bob", Interaction(concept_id="c", kind="watch"))
    assert store.learner_ids() == ["alice", "bob"]
