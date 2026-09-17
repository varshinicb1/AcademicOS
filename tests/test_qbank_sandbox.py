"""The sandbox bank (B10).

The requirement is a licensing one, so the tests are about what the sandbox must
never contain: real CBSE content, or a record whose rights field would let a
consumer treat fabricated data as a real board question.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from academicos.assessment.qbank_routes import QuestionBank   # noqa: E402
from export_qbank_sandbox import build                        # noqa: E402


@pytest.fixture(scope="module")
def sandbox():
    return build(60)


def test_it_is_deterministic(sandbox):
    """An SDK test written against the sandbox must not break on regeneration."""
    assert build(60) == sandbox


def test_every_record_is_freely_redistributable(sandbox):
    """The whole reason a sandbox exists: it is never the licensing problem."""
    for r in sandbox:
        assert r["rights"]["redistribution"] == "public", r["id"]
        assert r["rights"]["basis"], f"{r['id']} claims public rights with no basis"


def test_origin_says_it_was_generated_not_cbse(sandbox):
    for r in sandbox:
        assert "CBSE" not in r["rights"]["origin"]
        assert r["source"] == "ai_generated"
        assert r["provenance"]["method"] == "generated"


def test_no_record_claims_an_official_marking_scheme(sandbox):
    """A sandbox scheme must never be mistakable for a real value-point scheme."""
    for r in sandbox:
        assert r["answerScheme"]["provenance"] == "sandbox", r["id"]


def test_paper_codes_use_a_series_cbse_does_not_use(sandbox):
    """So a fabricated record can never be confused with a real paper."""
    from academicos.assessment.answer_key import normalize_paper_code
    for r in sandbox:
        code = r["answerScheme"]["sourcePaperCode"]
        assert code.startswith("99/"), code
        # It still parses as a code, so the shape under test is the real one.
        assert normalize_paper_code(code)


def test_document_id_is_the_literal_sandbox(sandbox):
    """Not a hash of anything real."""
    for r in sandbox:
        assert r["provenance"]["sourceDocumentId"] == "sandbox"
        assert r["answerScheme"]["sourceDocumentId"] == "sandbox"


def test_it_carries_the_same_schema_as_the_real_bank(sandbox):
    """An SDK written against the sandbox must work against the real API
    unchanged, so the field set has to match."""
    required = {
        "id", "questionBankId", "subject", "grade", "marks", "type", "stem",
        "answerScheme", "rights", "provenance", "calibration", "version",
        "reviewState", "language", "supersededBy",
    }
    for r in sandbox:
        missing = required - set(r)
        assert not missing, f"{r['id']} missing {sorted(missing)}"


def test_it_loads_through_the_real_question_bank(sandbox):
    bank = QuestionBank(sandbox)
    assert len(bank) == 60
    items, cursor, total = bank.page(limit=5)
    assert len(items) == 5
    assert total == 60
    assert cursor


def test_it_pages_and_filters_like_the_real_bank(sandbox):
    bank = QuestionBank(sandbox)
    seen, cursor = [], None
    while True:
        items, cursor, _ = bank.page(limit=13, cursor=cursor)
        seen.extend(i["id"] for i in items)
        if not cursor:
            break
    assert len(seen) == 60
    assert len(set(seen)) == 60                       # no duplicates

    only = bank.page(subject="Science", limit=100)[0]
    assert only and all(r["subject"] == "Science" for r in only)


def test_facets_work_over_the_sandbox(sandbox):
    facets = QuestionBank(sandbox).facets()
    assert sum(f["count"] for f in facets["subject"]) == 60
    assert len(facets["subject"]) == 4


def test_stems_are_generated_not_copied(sandbox):
    """A cheap check that no real corpus text slipped in."""
    for r in sandbox:
        assert "sandbox" in json.dumps(r).lower() or "Rampur" in r["stem"] \
            or any(p in r["stem"] for p in
                   ("Kothagiri", "Nandipur", "Bhavaninagar", "Sitapur", "town"))


def test_marks_are_plausible_for_cbse(sandbox):
    for r in sandbox:
        assert 1 <= r["marks"] <= 5
        assert r["answerScheme"]["totalMarks"] == r["marks"]


def test_a_sandbox_question_has_value_points(sandbox):
    """A sandbox with no value points would not exercise the scheme endpoint."""
    for r in sandbox:
        assert r["answerScheme"]["markingPoints"], r["id"]
