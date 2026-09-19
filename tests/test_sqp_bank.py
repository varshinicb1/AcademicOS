"""The SQP+MS bank, and the gates it must hold.

The parser existed and worked for a while without being wired into anything, so
the gap this closes is the fourth item on the PRD's critical path: "the SQP
parser is still not wired in". These tests are about the *bank*, not the parser
-- the parser has its own file.

The gates are the same three the CBE build applies, and they are asserted here
rather than assumed to carry over:
  * Q1 -- no answer key, no question
  * no mark value, no question
  * an implausible mark value is a block total, not a question's weight
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from build_cbe_bank import _MAX_SINGLE_QUESTION_MARKS  # noqa: E402

SQP_DIR = REPO / "academicos-data" / "corpus" / "cbse-sqp"
BANK = SQP_DIR / "questions.json"
HAVE_PDFS = any(SQP_DIR.rglob("*-SQP.pdf"))
needs_pdfs = pytest.mark.skipif(
    not HAVE_PDFS, reason="SQP PDFs not present (not committed)")


@pytest.fixture(scope="module")
def bank():
    if not BANK.exists():
        pytest.skip("SQP bank not built; run scripts/build_sqp_bank.py")
    return json.loads(BANK.read_text(encoding="utf-8"))


def test_the_bank_is_wired_into_the_served_corpus():
    """A bank nothing reads is the exact gap this closes.

    The MCP server must load it, or the file is written and the coverage claim
    is still a lie.
    """
    from academicos.mcp.qbank_server import load_corpus

    corpus = load_corpus()
    ids = {r.get("id") for r in corpus.records}
    assert any(str(i).startswith("cbse:sqp:") for i in ids), (
        "load_corpus does not read the SQP bank, so none of its records are "
        "served and the coverage gap is unchanged"
    )


def test_social_science_is_served_which_is_the_whole_point():
    """Social Science has no CBE coverage at all.

    The CBE item banks are Maths, Science and English. Sample papers are the
    only source that carries Social Science, which is why this build exists.
    """
    from academicos.mcp.qbank_server import load_corpus

    corpus = load_corpus()
    ss = [r for r in corpus.records if r.get("subject") == "Social Science"]
    assert ss, "no Social Science records are served; the gap is still open"
    assert all(r["grade"] == 10 for r in ss)


# --- the gates ------------------------------------------------------------

@needs_pdfs
def test_every_served_question_carries_a_real_scheme_answer(bank):
    """Q1, asserted on the output rather than trusted from the parser.

    `parse_pair` refuses to join a question with a scheme entry it cannot key,
    so anything emitted should have a real answer. Checked anyway, because a
    gate nobody verifies is a gate that has already failed once.
    """
    for rec in bank["questions"]:
        scheme = rec["answerScheme"]
        has_answer = bool(
            (scheme.get("modelAnswer") or "").strip()
            or any((p.get("text") or "").strip() for p in scheme["markingPoints"])
        )
        assert has_answer, f"{rec['id']} was served with no answer key"
        assert scheme["provenance"] == "cbse_marking_scheme"


@needs_pdfs
def test_every_served_question_has_a_plausible_mark_value(bank):
    """No zero-mark, and no block total served as a question's weight."""
    for rec in bank["questions"]:
        assert 0 < rec["marks"] <= _MAX_SINGLE_QUESTION_MARKS, (
            f"{rec['id']} has marks={rec['marks']}, outside "
            f"1..{_MAX_SINGLE_QUESTION_MARKS}"
        )


@needs_pdfs
def test_the_marks_spread_matches_what_the_paper_states(bank):
    """The Class X Social Science paper states its own mark scheme.

    "VSA carry 2 marks, SA 3 marks, LA 5 marks, CBQ (1+2+1=4)". A spread that
    contains anything else means the marks column was misread -- which is how
    page numbers were once served as mark values in the CBE parser.
    """
    values = sorted({r["marks"] for r in bank["questions"]})
    assert values, "no marks at all"
    assert max(values) <= 5, (
        f"a served question carries {max(values)} marks; class X Social Science "
        f"has none above 5. Values: {values}"
    )


@needs_pdfs
def test_every_record_is_attributed_and_rights_are_not_claimed(bank):
    """Rights stay `unknown` until counsel says otherwise.

    The product decision was "proceed, revisit if challenged" -- that is an
    accepted risk, not a redistribution permission, and the records must not
    imply otherwise.
    """
    for rec in bank["questions"]:
        assert rec["rights"]["origin"] == "CBSE"
        assert rec["rights"]["redistribution"] == "unknown"
        assert rec["provenance"]["method"] == "pdf_native"
        assert rec["answerScheme"]["provenance"] == "cbse_marking_scheme"


@needs_pdfs
def test_hindi_yields_nothing_and_that_is_recorded_not_hidden(bank):
    """The Hindi pairs parse to zero records, for a known reason.

    Both files extract through a legacy font encoding, so the text is not
    Unicode and no parser recovers it. Asserted so the shortfall stays visible:
    a silent zero would read as "Hindi is covered" (PRD rule Q4).
    """
    subjects = {r["subject"] for r in bank["questions"]}
    assert "Hindi" not in subjects, (
        "Hindi records appeared -- if the encoding was fixed, remove this test "
        "and update the coverage claim"
    )
