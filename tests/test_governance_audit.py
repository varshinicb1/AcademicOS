"""The evidence rule, and the audit ledger underneath it.

`governance/audit.py` had NO test coverage at all, and the audit that found that
also found that `Verifier` is imported nowhere and called nowhere -- it is
re-exported from `governance/__init__.py` and that is all. So the repository's
stated principle, *"evidence-first: every fact remembers where it came from"*,
has a guard that nothing invokes.

These tests cover the behaviour that exists. One of them pins the fact that it
is not wired in, so that stops being invisible.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from academicos.governance.audit import AuditLog, Verifier  # noqa: E402
from academicos.models.common import (  # noqa: E402
    Confidence,
    ExtractionMethod,
    Provenance,
    SourceSpan,
)


def _prov(*, document_id="doc-1", page=1, score=0.9):
    return Provenance(
        source=SourceSpan(document_id=document_id, page=page),
        method=ExtractionMethod.LLM,
        confidence=Confidence(method=ExtractionMethod.LLM, score=score),
    )


# --- the ledger -----------------------------------------------------------

def test_the_ledger_is_append_only_and_survives_a_reopen(tmp_path):
    path = tmp_path / "audit.jsonl"
    log = AuditLog(path)
    log.record("extract", "doc-1", {"n": 1})
    log.record("extract", "doc-1", {"n": 2})

    # A fresh object over the same file sees both, which is the point of a
    # ledger rather than an in-memory list.
    assert [e["payload"]["n"] for e in AuditLog(path).tail()] == [1, 2]


def test_tailing_a_ledger_that_does_not_exist_is_empty_not_an_error(tmp_path):
    assert AuditLog(tmp_path / "nope.jsonl").tail() == []


def test_the_ledger_records_provenance_when_given_it(tmp_path):
    path = tmp_path / "audit.jsonl"
    AuditLog(path).record("extract", "doc-1", provenance=_prov())
    entry = AuditLog(path).tail()[-1]
    assert entry["provenance"]["source"]["document_id"] == "doc-1"


def test_tail_returns_the_LAST_n_not_the_first_n(tmp_path):
    """Off-by-one bait: `[-n:]` is right, `[:n]` would silently pass on small data."""
    path = tmp_path / "audit.jsonl"
    log = AuditLog(path)
    for i in range(10):
        log.record("e", "s", {"n": i})
    assert [e["payload"]["n"] for e in log.tail(3)] == [7, 8, 9]


def test_a_corrupt_line_raises_rather_than_being_skipped(tmp_path):
    """Fail loud. A ledger that silently drops unreadable lines is not a ledger.

    This is asserted so the behaviour is a decision rather than an accident: if
    it is changed to skip bad lines, that change has to argue with this test.
    """
    path = tmp_path / "audit.jsonl"
    AuditLog(path).record("e", "s", {"n": 1})
    with open(path, "a", encoding="utf-8") as fh:
        fh.write("{not json\n")
    with pytest.raises(json.JSONDecodeError):
        AuditLog(path).tail()


# --- the evidence rule ----------------------------------------------------

def test_evidence_with_no_provenance_is_refused():
    ok, reason = Verifier.check_evidence(None)
    assert not ok and "provenance" in reason


def test_evidence_without_a_document_id_is_refused():
    ok, reason = Verifier.check_evidence(_prov(document_id=""))
    assert not ok and "document_id" in reason


def test_evidence_below_the_confidence_floor_is_refused():
    ok, reason = Verifier.check_evidence(_prov(score=0.49))
    assert not ok and "confidence" in reason


def test_the_confidence_floor_is_inclusive():
    """0.5 passes; the check is `< 0.5`, not `<=`.

    Pinned because the boundary is exactly the sort of thing a later `<=` would
    change without anyone noticing which side of it real data sits on.
    """
    ok, _ = Verifier.check_evidence(_prov(score=0.5))
    assert ok


def test_good_evidence_passes():
    ok, reason = Verifier.check_evidence(_prov())
    assert ok and reason == "ok"


def test_the_page_requirement_is_enforced_by_the_MODEL_not_the_checker():
    """`REQUIRED = ("document_id", "page")` is declared but `page` is never read.

    That looked like an unenforced invariant. It is not: `SourceSpan.page` is
    `Field(ge=1)`, so pydantic refuses to construct a provenance without one.
    Asserted here so the next reader does not "fix" a hole that the type system
    already closed.

    `REQUIRED` itself is genuinely unused by any code path -- recorded rather
    than quietly deleted, because deleting it is a decision about the public
    surface of this class.
    """
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        SourceSpan(document_id="d", page=0)
    with pytest.raises(ValidationError):
        SourceSpan(document_id="d", page=None)
    assert Verifier.REQUIRED == ("document_id", "page")
    source = (REPO / "src" / "academicos" / "governance"
              / "audit.py").read_text(encoding="utf-8")
    assert "REQUIRED" not in source.split("REQUIRED =")[1].split("\n\n")[1], (
        "REQUIRED is now read somewhere -- update this test and the docstring"
    )


# --- quoted-snippet verification -----------------------------------------

def test_a_short_snippet_is_refused_regardless_of_containment():
    """Under 8 characters it is not evidence, even if it technically appears."""
    ok, score = Verifier.validate_text_provenance("cell", "the cell membrane")
    assert not ok and score == 0.0


def test_a_real_quote_from_the_source_verifies():
    src = "The light reaction occurs in the thylakoid membrane and splits water."
    ok, score = Verifier.validate_text_provenance(
        "occurs in the thylakoid membrane", src)
    assert ok and score == 1.0


def test_verification_ignores_case_and_collapses_whitespace():
    """PDF text arrives with arbitrary line breaks; a quote must survive that."""
    src = "The   light reaction\noccurs in the\n  thylakoid membrane"
    ok, _ = Verifier.validate_text_provenance(
        "LIGHT REACTION occurs in the thylakoid", src)
    assert ok


def test_a_quote_that_is_not_in_the_source_fails():
    ok, score = Verifier.validate_text_provenance(
        "mitochondrial matrix", "the thylakoid membrane splits water")
    assert not ok and score == 0.0


def test_an_empty_snippet_is_refused():
    assert Verifier.validate_text_provenance("", "anything at all")[0] is False


# --- the guard is not wired in -------------------------------------------

def test_the_verifier_is_never_called_anywhere():
    """Pins a real gap so it stays visible.

    `Verifier` is re-exported from `governance/__init__.py` and called from
    nowhere else, so the repository's "no fact without provenance" rule has a
    guard that nothing invokes. The consequence is visible in
    `graph/builder.py::build_triples`, which writes LLM-extracted triples with a
    hardcoded `Confidence(score=0.9)` and no evidence check at all.

    This is deliberately written as a PASSING test that describes the current
    state, not a failing one that demands a fix: wiring the Verifier into the
    write path would currently be a no-op, because everything upstream asserts
    0.9. The useful fix is to make the confidence MEASURED first -- and the PRD
    already forbids unmeasured accuracy claims (non-goal 4).

    When the Verifier IS wired in, this test fails and should be replaced by one
    asserting the write path refuses bad evidence.
    """
    hits = []
    for path in (REPO / "src").rglob("*.py"):
        if path.name == "audit.py" and path.parent.name == "governance":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if "check_evidence" in text or "validate_text_provenance" in text:
            hits.append(path.relative_to(REPO).as_posix())
    assert not hits, (
        "the Verifier is now referenced outside its own module -- wiring it in "
        f"is the change this test was pinning, so replace it: {hits}"
    )


def test_the_graph_builder_asserts_a_confidence_it_never_measured():
    """The concrete consequence, pinned at the site.

    `build_triples` sets `score=0.9` for LLM extraction. Nothing measures that,
    and the PRD's non-goal 4 says no unmeasured accuracy claim should be made.
    Recorded here because it is the reason wiring the Verifier in would be
    cosmetic today.
    """
    src = (REPO / "src" / "academicos" / "graph"
           / "builder.py").read_text(encoding="utf-8")
    assert "score=0.9" in src, (
        "the hardcoded 0.9 has gone -- if confidence is now measured, the "
        "Verifier can be wired in for real and this test should be removed"
    )
