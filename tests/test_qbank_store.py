"""Item versioning, review states, and the per-item audit trail (C1, C2)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.assessment.qbank_store import (
    STATES,
    TRANSITIONS,
    QuestionBankStore,
    ReviewStateError,
    payload_hash,
)


@pytest.fixture
def store(tmp_path):
    s = QuestionBankStore(tmp_path / "qbank.sqlite")
    yield s
    s.close()


def item(stem: str = "Balance the equation", marks: int = 3) -> dict:
    return {"id": "cbse:q:src:deadbeefdeadbeefdeadbeef:1", "stem": stem, "marks": marks}


# --------------------------------------------------------------------------- #
# C1 -- versioning
# --------------------------------------------------------------------------- #

def test_first_record_is_version_one(store):
    v = store.record(item()["id"], item())
    assert v.version == 1
    assert v.state == "published"


def test_a_correction_is_a_new_version_not_an_edit(store):
    qid = item()["id"]
    store.record(qid, item("Balance the equation"))
    v2 = store.record(qid, item("Balance the following equation"))

    assert v2.version == 2
    # The point of versioning: what was served stays retrievable.
    assert store.at_version(qid, 1)["stem"] == "Balance the equation"
    assert store.at_version(qid, 2)["stem"] == "Balance the following equation"


def test_rerunning_the_pipeline_does_not_manufacture_a_version(store):
    """The scheme-attachment pass is idempotent; it must not bury real edits."""
    qid = item()["id"]
    store.record(qid, item())
    again = store.record(qid, item())
    assert again.version == 1
    assert store.counts()["versions"] == 1


def test_identical_content_under_a_new_state_is_a_new_version(store):
    qid = item()["id"]
    store.record(qid, item(), state="draft")
    v = store.record(qid, item(), state="in_review")
    assert v.version == 2
    assert v.state == "in_review"


def test_payload_hash_ignores_bookkeeping_fields():
    """A state change or a timestamp is not a content change."""
    a = {"id": "x", "stem": "s", "updatedAt": "2026-01-01", "reviewState": "draft", "version": 1}
    b = {"id": "x", "stem": "s", "updatedAt": "2026-09-17", "reviewState": "published", "version": 9}
    assert payload_hash(a) == payload_hash(b)


def test_payload_hash_changes_with_content():
    assert payload_hash({"stem": "a"}) != payload_hash({"stem": "b"})


# --------------------------------------------------------------------------- #
# C1 -- review states
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("path", [
    ("draft", "in_review"), ("draft", "published"), ("in_review", "published"),
    ("in_review", "draft"), ("published", "superseded"),
    ("published", "in_review"), ("superseded", "in_review"),
])
def test_legal_transitions_are_accepted(store, path):
    frm, to = path
    qid = item()["id"]
    store.record(qid, item(), state=frm)
    v = store.transition(qid, to)
    assert v.state == to


@pytest.mark.parametrize("path", [
    ("draft", "superseded"),      # cannot retire something never published
    ("superseded", "published"),  # must pass back through review
    ("in_review", "superseded"),
])
def test_illegal_transitions_are_refused(store, path):
    frm, to = path
    qid = item()["id"]
    store.record(qid, item(), state=frm)
    with pytest.raises(ReviewStateError):
        store.transition(qid, to)


def test_a_no_op_transition_is_refused(store):
    """Accepting published -> published would leave the trail ambiguous about
    whether anything actually happened."""
    qid = item()["id"]
    store.record(qid, item(), state="published")
    with pytest.raises(ReviewStateError, match="already"):
        store.transition(qid, "published")


def test_transition_on_an_unknown_item_is_refused(store):
    with pytest.raises(ReviewStateError, match="unknown question"):
        store.transition("nope", "published")


def test_an_unknown_state_is_refused(store):
    with pytest.raises(ReviewStateError, match="unknown review state"):
        store.record(item()["id"], item(), state="nonsense")


def test_every_transition_uses_states_in_the_vocabulary():
    for frm, to in TRANSITIONS:
        assert frm in STATES and to in STATES


def test_transition_preserves_content_and_keeps_the_old_state_readable(store):
    qid = item()["id"]
    store.record(qid, item("keep me"), state="draft")
    store.transition(qid, "in_review")
    store.transition(qid, "published")

    assert store.at_version(qid, 1)["stem"] == "keep me"
    history = store.history(qid)
    assert [h.state for h in history] == ["draft", "in_review", "published"]


# --------------------------------------------------------------------------- #
# C2 -- audit trail
# --------------------------------------------------------------------------- #

def test_every_write_leaves_an_audit_row(store):
    qid = item()["id"]
    store.record(qid, item(), actor="extractor", note="initial import")
    store.transition(qid, "in_review", actor="reviewer", note="sent for review")
    rows = store.audit(question_id=qid)

    assert len(rows) == 2
    actions = {r["action"] for r in rows}
    assert actions == {"create", "transition"}
    assert all(r["question_id"] == qid for r in rows)


def test_audit_records_who_and_why(store):
    qid = item()["id"]
    store.record(qid, item(), actor="pipeline", note="relinked marking scheme")
    row = store.audit(question_id=qid)[0]
    assert row["actor"] == "pipeline"
    assert row["note"] == "relinked marking scheme"
    assert row["to_state"] == "published"
    assert row["at"]


def test_audit_records_both_ends_of_a_transition(store):
    qid = item()["id"]
    store.record(qid, item(), state="draft")
    store.transition(qid, "in_review", actor="R. Menon")
    row = [r for r in store.audit(question_id=qid) if r["action"] == "transition"][0]
    assert (row["from_state"], row["to_state"]) == ("draft", "in_review")


def test_audit_is_newest_first_and_scoped(store):
    a, b = "q-a", "q-b"
    store.record(a, {"id": a, "stem": "a"})
    store.record(b, {"id": b, "stem": "b"})
    assert len(store.audit(question_id=a)) == 1
    assert len(store.audit(limit=10)) == 2


# --------------------------------------------------------------------------- #
# supersede, not delete
# --------------------------------------------------------------------------- #

def test_supersede_retires_without_deleting(store):
    old, new = "q-old", "q-new"
    store.record(old, {"id": old, "stem": "old"})
    store.record(new, {"id": new, "stem": "new"})
    v = store.supersede(old, by=new, actor="R. Menon")

    assert v.state == "superseded"
    # Still resolvable -- a paper from last term must still reconstruct.
    assert store.at_version(old, 1) is not None
    assert store.latest(old).state == "superseded"


def test_supersede_records_the_replacement(store):
    old, new = "q-old", "q-new"
    store.record(old, {"id": old, "stem": "old"})
    store.record(new, {"id": new, "stem": "new"})
    store.supersede(old, by=new)
    payload = store.at_version(old, store.latest(old).version)
    assert payload["supersededBy"] == new
    assert new in store.audit(question_id=old)[0]["note"]


def test_cannot_supersede_with_a_replacement_that_does_not_exist(store):
    store.record("q-old", {"id": "q-old", "stem": "old"})
    with pytest.raises(ReviewStateError, match="does not exist"):
        store.supersede("q-old", by="ghost")


def test_counts_report_latest_state_per_item(store):
    store.record("q1", {"id": "q1", "stem": "a"}, state="published")
    store.record("q2", {"id": "q2", "stem": "b"}, state="draft")
    store.transition("q2", "in_review")
    counts = store.counts()
    assert counts["items"] == 2
    assert counts["published"] == 1
    assert counts["in_review"] == 1
    assert counts["draft"] == 0          # q2 left draft
    assert counts["audit_rows"] == 3


# --------------------------------------------------------------------------- #
# the append-only invariant, asserted against the source
# --------------------------------------------------------------------------- #

def test_the_store_never_updates_or_deletes_content_rows():
    """`supersede` and friends must not mutate history.

    Checked against the module's own SQL rather than by trusting the docstring,
    because the failure mode is a future edit quietly adding an UPDATE that makes
    the audit trail a lie.
    """
    src = (ROOT / "src" / "academicos" / "assessment" / "qbank_store.py").read_text(
        encoding="utf-8")
    writes = _table_writes(src)

    deletes = [w for w in writes if w[0] == "DELETE FROM"]
    updates = [w for w in writes if w[0] == "UPDATE"]
    assert deletes == [], f"the store must never delete: {deletes}"

    # Exactly one UPDATE is allowed: the supersede pointer, which records a
    # retirement rather than rewriting question content. Assert it sits inside
    # `supersede`, by name, rather than by guessing at surrounding text.
    assert len(updates) == 1, f"unexpected UPDATE statements: {updates}"
    before = src[:src.index("UPDATE question_versions")]
    enclosing = before[before.rindex("    def "):].split("(")[0].strip()
    assert enclosing == "def supersede", (
        f"the only UPDATE allowed is the supersede pointer; found one in {enclosing}")


def _table_writes(src: str) -> list[tuple[str, str]]:
    """Every statement that touches a content table, as (verb, table).

    Matched by keyword rather than by parsing quoted strings: the module's
    triple-quoted docstrings misalign naive quote pairing, which made the first
    version of this check silently find zero statements and pass for the wrong
    reason.
    """
    import re
    pattern = re.compile(
        r"\b(SELECT|INSERT INTO|UPDATE|DELETE FROM)\s+"
        r"(question_versions|question_audit)\b", re.I)
    return [(m.group(1).upper(), m.group(2)) for m in pattern.finditer(src)]


def test_the_write_detector_actually_detects():
    """Guard the guard: a detector that finds nothing passes vacuously."""
    sample = "INSERT INTO question_versions (a) VALUES (?)"
    assert _table_writes(sample) == [("INSERT INTO", "question_versions")]
    assert _table_writes("DELETE FROM question_audit") == [("DELETE FROM", "question_audit")]


# --------------------------------------------------------------------------- #
# durability contract
# --------------------------------------------------------------------------- #

def test_the_store_sets_the_repo_mandated_pragmas(tmp_path):
    """AGENTS.md section 3 requires WAL and a busy timeout on every SQLite
    connection in this codebase."""
    s = QuestionBankStore(tmp_path / "q.sqlite")
    try:
        assert s.conn.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
        assert s.conn.execute("PRAGMA busy_timeout").fetchone()[0] == 60000
    finally:
        s.close()
