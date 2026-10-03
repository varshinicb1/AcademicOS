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

from academicos.corpus import marking_split  # noqa: E402
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
    # Sample papers are class 10; the class 9 Social Science records are the model-written ones
    # (corpus/ai-cbse-9-10), served only as a checked key.
    assert all(r["grade"] == 10 for r in ss if r.get("source") != "ai_generated")


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
        # `description` is the canonical marking-point field, used by the CBE,
        # board and sandbox corpora alike. This checked only `text` -- which the
        # SQP builder emitted for one commit -- so it would have passed while
        # the record carried nothing a grader could use. Both are accepted here
        # to match `QuestionBank.has_answer_key`; the canonical one is asserted
        # separately below.
        has_answer = bool(
            (scheme.get("modelAnswer") or "").strip()
            or any((p.get("description") or p.get("text") or "").strip()
                   for p in scheme["markingPoints"])
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
def test_the_social_science_marks_spread_matches_what_that_paper_states(bank):
    """The Class X Social Science paper states its own mark scheme.

    "VSA carry 2 marks, SA 3 marks, LA 5 marks, CBQ (1+2+1=4)". A Social Science
    spread containing anything else means the marks column was misread -- which
    is how page numbers were once served as mark values in the CBE parser.

    Scoped to Social Science on purpose. It was a whole-bank assertion while the
    bank held one paper; now it spans 47 subjects and a 10-mark question is
    ordinary in several of them, so a global cap of 5 would be wrong. The global
    ceiling is asserted separately above.
    """
    ss = [r["marks"] for r in bank["questions"] if r["subject"] == "Social Science"]
    assert ss, "no Social Science records"
    assert max(ss) <= 5, f"class X Social Science has no question above 5: {sorted(set(ss))}"


@needs_pdfs
def test_every_grade_is_a_real_school_year(bank):
    """Grades come from the folder name, and a prefix match got this wrong.

    `"ClassXII_2025_26".startswith("ClassX")` is True, so an earlier version
    labelled every Class XII paper as Class 10 -- and dict ordering made
    "ClassX" win every time. Caught by reading the per-subject output, where
    Applied-Maths and HomeScience were reported as class 10.
    """
    grades = {r["grade"] for r in bank["questions"]}
    assert grades <= {10, 12}, f"unexpected grade(s): {sorted(grades)}"
    assert 12 in grades, (
        "no Class XII records -- the number is present in the corpus, so a "
        "prefix match has swallowed it again"
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


@needs_pdfs
def test_the_marking_points_use_the_canonical_shape(bank):
    """Every corpus must shape marking points the same way.

    Measured: CBE, board and sandbox all use `description` with `id`, `marks`,
    `keyword`, `isRequired` and `synonyms`. The SQP builder emitted a bare
    `{"text", "marks"}` for one commit, which made it the only corpus with a
    different shape -- and a gate that knew only `text` then filtered every SQP
    record out while reporting a healthy count. Shape drift is silent, so it is
    asserted rather than assumed.
    """
    required = {"id", "description", "marks", "keyword", "isRequired", "synonyms"}
    for rec in bank["questions"]:
        for point in rec["answerScheme"]["markingPoints"]:
            missing = required - set(point)
            assert not missing, (
                f"{rec['id']} marking point is missing {sorted(missing)}; the "
                f"corpora have drifted apart again"
            )
            assert point["description"].strip(), f"{rec['id']} has an empty description"


# --------------------------------------------------------------------------- #
# value points (Task 124)
# --------------------------------------------------------------------------- #

def _sqp_question(text: str, answer: str, marks: int):
    from academicos.corpus.cbse_sqp import Question, SqpQuestion

    return SqpQuestion(question=Question(number=22, text=text, marks=marks, page=5),
                       answer=answer, scheme_marks=marks)


def test_a_scheme_that_prints_its_split_becomes_a_point_a_mark():
    """cbse:sqp:ClassX_2023_24:Home Science:22 as the marking scheme prints
    it: "Two reasons of preferring soaps over detergents are- 1+1=2 Soaps
    are- 1. Cheap 2. Environment friendly(biodegradable)"."""
    from build_sqp_bank import _record

    item = _sqp_question(
        "Present two reasons of preferring soaps over detergents.",
        "Two reasons of preferring soaps over detergents are- 1+1=2 Soaps are- "
        "1. Cheap 2. Environment friendly(biodegradable) Any other, Any two", 2)
    scheme = _record(item, subject="Home Science", grade=10,
                     year="ClassX_2023_24")["answerScheme"]
    assert [p["marks"] for p in scheme["markingPoints"]] == [1, 1]
    assert scheme["metadata"]["markSplit"] == "marks-printed"
    assert scheme["hasPartialCredit"] is True


def test_an_any_two_of_the_following_scheme_records_what_it_awards():
    """cbse:sqp:ClassX_2024_25:Home Science:26 -- five motor abilities under
    "1X3=3" and "Any other, Any three": each is worth a mark, and only three
    are given."""
    from build_sqp_bank import _record

    item = _sqp_question(
        "Enumerate three motor abilities of a 6-year-old child.",
        "Three motor abilities of 6-year-old child- 1X3=3 1.Runs with speed "
        "2.Rides bicycle with training wheels 3. Pours liquid in containers "
        "4.Ties lace 5.Dances / Swims Any other, Any three", 3)
    scheme = _record(item, subject="Home Science", grade=10,
                     year="ClassX_2024_25")["answerScheme"]
    assert [p["marks"] for p in scheme["markingPoints"]] == [1, 1, 1, 1, 1]
    assert scheme["metadata"]["anyOf"] == 3
    # Five listed, three awarded: what a student can earn is still the
    # question's marks.
    assert marking_split.awardable_marks(scheme) == 3
    assert all(p["isRequired"] is False for p in scheme["markingPoints"])


def test_a_key_that_opened_with_its_own_question_no_longer_does():
    """cbse:sqp:ClassXII_2022_23:Psychology:22 -- the scheme page ran the
    question and its answer together, so the key repeated all 192 characters
    of the question before answering it."""
    from build_sqp_bank import _record

    stem = ("Vinita holds a negative attitude towards individuals of a particular "
            "community. She avoids interacting or helping them in college. Identify "
            "and explain the behaviour being exhibited by Vinita.")
    item = _sqp_question(stem, f"{stem} Ans.: Discrimination", 2)
    scheme = _record(item, subject="Psychology", grade=12,
                     year="ClassXII_2022_23")["answerScheme"]
    assert scheme["modelAnswer"] == "Ans.: Discrimination"
    assert stem[:40] not in scheme["markingPoints"][0]["description"]
