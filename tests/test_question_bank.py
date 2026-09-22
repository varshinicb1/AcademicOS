"""The question bank: answer-key relink, enrichment, and the no-invention rule.

Every fixture here is synthetic and lives in tmp_path, except the two tests at
the end which assert against the real corpus on disk -- those are the ones that
would have caught the paper-code separator bug, because a synthetic fixture only
contains the separators its author thought of.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.assessment.answer_key import normalize_paper_code
from academicos.assessment.question_bank import (
    AnswerKeyIndex,
    assigned_calibration,
    enrich_all,
    enrich_record,
    load_parsed_source,
    parse_question_id,
    relink_answer_schemes,
    rights_for_cbse_board_paper,
)

ANSWER_KEYS_SCHEMA = """
CREATE TABLE answer_keys (
  subject TEXT, grade TEXT, paper_code TEXT, q_no INTEGER,
  correct_option TEXT, answer_text TEXT, value_points TEXT, marks REAL,
  source TEXT
);
"""


def make_answer_keys(path: Path, rows: list[tuple]) -> Path:
    con = sqlite3.connect(path)
    con.executescript(ANSWER_KEYS_SCHEMA)
    con.executemany("INSERT INTO answer_keys VALUES (?,?,?,?,?,?,?,?,?)", rows)
    con.commit()
    con.close()
    return path


def make_parse_tree(parse_dir: Path, doc_hash: str, pages: list[tuple[int, str]],
                    doc_type: str = "question_paper") -> Path:
    parse_dir.mkdir(parents=True, exist_ok=True)
    p = parse_dir / f"src_{doc_hash}.json"
    p.write_text(json.dumps({
        "document_id": f"src:{doc_hash}",
        "doc_type": doc_type,
        "pages": [{"page_no": n, "kind": "text", "text": t} for n, t in pages],
    }), encoding="utf-8")
    return p


def question(doc_hash: str, q_no: int, *, marks: int = 3, stem: str = "x" * 80,
             scheme: dict | None = None) -> dict:
    """One wire-shaped record, as `questions.json` stores it."""
    return {
        "id": f"cbse:q:src:{doc_hash}:{q_no}",
        "questionBankId": f"src:{doc_hash}",
        "subject": "Science",
        "grade": 10,
        "marks": marks,
        "stem": stem,
        "answerScheme": scheme or {"totalMarks": marks, "markingPoints": []},
    }


# --------------------------------------------------------------------------- #
# id parsing
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("qid,expected", [
    ("cbse:q:src:af50a3f7e666fdea9cee608f:4", ("af50a3f7e666fdea9cee608f", 4)),
    ("cbse:q:src:00112233445566778899aabb:39", ("00112233445566778899aabb", 39)),
])
def test_parse_question_id_accepts_the_canonical_shape(qid, expected):
    assert parse_question_id(qid) == expected


@pytest.mark.parametrize("qid", [
    "", "cbse:q:src:short:4", "af50a3f7e666fdea9cee608f:4",
    "cbse:q:src:af50a3f7e666fdea9cee608f", "cbse:q:src:af50a3f7e666fdea9cee608f:x",
    None,
])
def test_parse_question_id_rejects_everything_else(qid):
    assert parse_question_id(qid) is None


# --------------------------------------------------------------------------- #
# paper code normalisation -- the bug that cost 3,364 answer keys
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("raw,expected", [
    ("31/1/1", "31/1/1"),
    ("31-1-1", "31/1/1"),
    ("31.1.1", "31/1/1"),
    ("31_1_1", "31/1/1"),
    ("X_086_31-1-1 to 3 Science_MS.pdf", "31/1/1"),
    ("X_086_31.1.1 to 31.1.3 in HINDI.pdf", "31/1/1"),
    ("X_086_31_1-1 to 3_Science _HINDI_Med.pdf", "31/1/1"),
    ("XII_042_Physics_MS_55_7_1,2,3_hindi_med.pdf", "55/7/1"),
    ("55-3-1,2,3 English Version.pdf", "55/3/1"),
    ("MS Science (086) 31-8-1 to 3) in HINDI.pdf", "31/8/1"),
])
def test_paper_code_normalisation_covers_every_separator_the_corpus_uses(raw, expected):
    """A `[/-]`-only pattern indexed 1,040 of 4,483 rows. These are the real
    filename shapes it dropped."""
    assert normalize_paper_code(raw) == expected


@pytest.mark.parametrize("raw", [
    "science set 6.pdf", "2025_086_Science_31-1-1_Science.pdf", "notes.pdf",
])
def test_paper_code_does_not_invent_a_code(raw):
    """`086` is a subject code and `2025` is a year; neither is a paper code."""
    got = normalize_paper_code(raw)
    assert got in ("", "31/1/1")  # the third is a real code embedded in a path
    if raw.startswith("2025"):
        assert got == "31/1/1"


def test_year_digits_are_never_read_as_a_series():
    """`2025-1-1` must not yield `25/1/1` or `025/1/1`."""
    assert normalize_paper_code("2025-1-1") == ""


# --------------------------------------------------------------------------- #
# subject code must not be spliced into the paper code
#
# English board papers carry single-digit first components (`1/5/1`, `2/1/1`),
# unlike Science/Maths (`31/1/1`). A pattern requiring two or three leading
# digits cannot see them at all, and — worse — when the marking scheme's header
# puts the subject code immediately before the paper code
# (`MS-English Core/301/1-5-1`) it matches the SUBJECT code plus the first two
# components instead, yielding `301/1/5`. That is wrong twice over: the code
# does not exist, and every set of a paper collapses onto one key, so three
# distinct marking schemes overwrite each other.
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("raw,expected", [
    # the marking-scheme header shapes, read straight off the parsed page
    ("MS-English Core/301/1-5-1", "1/5/1"),
    ("MS-English Core/301/1-1-1", "1/1/1"),
    # the filename shapes for the same papers
    ("XII_301_1_1_1_MS.pdf", "1/1/1"),
    ("XII_301_1_4_2_MS.pdf", "1/4/2"),
    # class X English, which uses a `2/` series
    ("MS-English Lan Lit/184/2-1-1", "2/1/1"),
])
def test_subject_code_is_not_spliced_into_the_paper_code(raw, expected):
    assert normalize_paper_code(raw) == expected


def test_each_set_of_a_paper_keeps_its_own_code():
    """Sets 1/2/3 of one paper must not collapse onto a single key.

    `301/1-1-1`, `301/1-1-2` and `301/1-1-3` are three different marking
    schemes. Splicing the subject code mapped all three to `301/1/1`, so
    whichever was ingested last silently overwrote the other two.
    """
    codes = {normalize_paper_code(f"MS-English Core/301/1-1-{n}") for n in (1, 2, 3)}
    assert codes == {"1/1/1", "1/1/2", "1/1/3"}


@pytest.mark.parametrize("raw,expected", [
    ("1/5/1", "1/5/1"),
    ("2/1/1", "2/1/1"),
    ("2/4/1-14", "2/4/1"),
])
def test_single_digit_series_codes_are_read(raw, expected):
    """English question-paper headers lead with a one-digit series number."""
    assert normalize_paper_code(raw) == expected


# --------------------------------------------------------------------------- #
# the answer key index
# --------------------------------------------------------------------------- #

def test_index_keys_by_code_not_filename(tmp_path):
    db = make_answer_keys(tmp_path / "ak.db", [
        ("Science", "X", "31/1/1", 1, "D", "chlorine", '[["point one here", 1.0]]', 1.0,
         "X_086_31-1-1 to 3 Science_MS.pdf"),
        ("Science", "X", "31/1/1", 2, None, "because", '[["step a here", 0.0]]', 3.0,
         "X_086_31-1-1 to 3 Science_MS.pdf"),
        ("Science", "X", "32/2/1", 1, "A", "copper", '[["only one", 1.0]]', 1.0,
         "X_086_Set-2 (32.2.1 to 32.2.3) in ENGLISH.pdf"),
    ])
    idx = AnswerKeyIndex(db)
    assert idx.rows_total == 3
    assert idx.rows_keyed == 3
    assert idx.codes == {"31/1/1", "32/2/1"}
    assert idx.candidates("31/1/1", 2)[0].answer_text == "because"
    assert idx.candidates("31-1-1", 1)[0].correct_option == "D"   # any separator
    assert idx.candidates("31/1/1", 99) == []                      # absent q_no
    assert idx.candidates("99/9/9", 1) == []                       # absent code


def test_index_skips_filenames_with_no_code(tmp_path):
    """A file that names no paper is not guessed at."""
    db = make_answer_keys(tmp_path / "ak.db", [
        ("Science", "X", None, 1, "D", "x", "[]", 1.0, "science set 6.pdf"),
    ])
    idx = AnswerKeyIndex(db)
    assert idx.rows_total == 1
    assert idx.rows_keyed == 0
    assert idx.codes == set()


def test_index_survives_a_bad_question_number(tmp_path):
    db = make_answer_keys(tmp_path / "ak.db", [
        ("Science", "X", None, "not-a-number", "D", "x", "[]", 1.0,
         "X_086_31-1-1 MS.pdf"),
    ])
    idx = AnswerKeyIndex(db)
    assert idx.rows_keyed == 0


def test_missing_db_is_not_an_error(tmp_path):
    idx = AnswerKeyIndex(tmp_path / "nope.db")
    assert idx.rows_total == 0
    assert idx.candidates("31/1/1", 1) == []


@pytest.mark.parametrize("raw,expected", [
    ('[["step one here", 1.0], ["step two here", 0.5]]', 2),
    ('["bare string point"]', 1),
    ("[]", 0),
    (None, 0),
    ("not json", 0),
    ('[["", 1.0]]', 0),        # blank text is not a point
])
def test_value_point_parsing_is_defensive(tmp_path, raw, expected):
    db = make_answer_keys(tmp_path / "ak.db", [
        ("Science", "X", None, 1, "D", "x", raw, 1.0, "X_086_31-1-1 MS.pdf"),
    ])
    idx = AnswerKeyIndex(db)
    assert len(idx.candidates("31/1/1", 1)[0].value_points) == expected


# --------------------------------------------------------------------------- #
# parse trees
# --------------------------------------------------------------------------- #

def test_parse_tree_finds_the_code_in_a_page_header(tmp_path):
    make_parse_tree(tmp_path, "a" * 24, [
        (1, "Series X_086  31/1/1  Science  Page 1 of 27  " + "body " * 40),
        (2, "more body " * 60),
    ])
    src = load_parsed_source(tmp_path, "a" * 24)
    assert src is not None
    assert src.paper_code == "31/1/1"
    assert src.page_count == 2


def test_parse_tree_finds_a_single_digit_english_series_code(tmp_path):
    """English board papers head with `1/4/1`, not `31/1/1`.

    Verbatim from the parsed header of `src_e03ed43175ba6cd1401c4522` (English
    XII, 13 questions). A code hint requiring two leading digits skipped every
    English paper in the corpus, so all 207 English questions reached the bank
    with no marking scheme attached.
    """
    make_parse_tree(tmp_path, "f" * 24, [
        (1, "1/4/1 \nH 1 H  \nP.T.O.\nCandidates must write the Q.P. Code \n"
            "on the title page of the answer-book.\n" + "body " * 40),
    ])
    src = load_parsed_source(tmp_path, "f" * 24)
    assert src is not None
    assert src.paper_code == "1/4/1"


def test_parse_tree_carries_no_code_when_the_header_has_none(tmp_path):
    make_parse_tree(tmp_path, "b" * 24, [(1, "just some prose " * 40)])
    src = load_parsed_source(tmp_path, "b" * 24)
    assert src is not None
    assert src.paper_code == ""


def test_missing_parse_tree_returns_none(tmp_path):
    assert load_parsed_source(tmp_path, "c" * 24) is None


def test_page_lookup_ignores_a_probe_too_short_to_be_distinctive(tmp_path):
    make_parse_tree(tmp_path, "d" * 24, [(1, "the quick brown fox " * 20)])
    src = load_parsed_source(tmp_path, "d" * 24)
    assert src.page_containing("the quick") is None      # < 24 chars


def test_page_lookup_matches_across_line_breaks(tmp_path):
    """The page text keeps PDF line breaks; the stem does not. Normalising only
    the probe made every page lookup return None."""
    make_parse_tree(tmp_path, "e" * 24, [
        (1, "cover page only"),
        (2, "Explain why the reaction of lead\nnitrate with potassium iodide\nis a double displacement reaction."),
    ])
    src = load_parsed_source(tmp_path, "e" * 24)
    page = src.page_containing(
        "Explain why the reaction of lead nitrate with potassium iodide")
    assert page == 2


# --------------------------------------------------------------------------- #
# the relink
# --------------------------------------------------------------------------- #

# Q22's official answer must answer Q22: since Task 15 the relink attaches
# only what `scheme_verify` accepts for the question.
Q22_ANSWER = "Lead nitrate reacts with potassium iodide to give a yellow precipitate"
Q22_POINTS = ('[["Lead iodide is formed as a yellow precipitate", 1.0], '
              '["It is a double displacement reaction", 2.0]]')


def _setup(tmp_path):
    db = make_answer_keys(tmp_path / "ak.db", [
        ("Science", "X", None, 1, "D", "opt d", '[["p1", 1.0]]', 1.0,
         "X_086_31-1-1 MS.pdf"),
        ("Science", "X", None, 22, None, Q22_ANSWER, Q22_POINTS, 3.0,
         "X_086_31-1-1 MS.pdf"),
    ])
    parse = tmp_path / "parse"
    make_parse_tree(parse, "a" * 24, [
        (1, "Series 31/1/1 Science " + "body " * 40),
        (2, "22. Explain the reaction of lead nitrate with potassium iodide in water. " + "x " * 40),
    ])
    stem22 = "Explain the reaction of lead nitrate with potassium iodide"
    return AnswerKeyIndex(db), parse, stem22


def test_relink_attaches_an_official_scheme(tmp_path):
    idx, parse, stem22 = _setup(tmp_path)
    recs = [question("a" * 24, 22, marks=3, stem=stem22)]
    rep = relink_answer_schemes(recs, idx, parse_dir=parse)

    assert rep.newly_attached == 1
    assert rep.with_scheme == 1
    sch = recs[0]["answerScheme"]
    assert sch["provenance"] == "cbse_marking_scheme"
    assert sch["sourcePaperCode"] == "31/1/1"
    assert len(sch["markingPoints"]) == 2
    assert recs[0]["provenance"]["pageNumber"] == 2


def test_relink_replaces_an_existing_scheme_with_the_verified_official_one(tmp_path):
    """A scheme the corpus already carries is not trusted on sight. It is
    verified against the question, and the official candidate the verifier
    accepts is what gets labelled -- so the provenance field records the same
    guarantee a freshly attached scheme gets. Before Task 15 the existing
    content was kept and labelled whenever ANY key existed for the question
    number, which is how 30.5% of the labelled schemes came to be wrong.
    """
    idx, parse, stem22 = _setup(tmp_path)
    existing = {"totalMarks": 3, "markingPoints": [{
        "id": "k", "description": "Lead nitrate and potassium iodide give yellow lead iodide",
        "marks": 3}]}
    recs = [question("a" * 24, 22, stem=stem22, scheme=existing)]
    rep = relink_answer_schemes(recs, idx, parse_dir=parse)

    assert rep.already_had_scheme == 1
    assert rep.verified_existing_scheme == 1
    assert rep.newly_attached == 0
    assert rep.quarantined == {}
    sch = recs[0]["answerScheme"]
    assert sch["modelAnswer"] == Q22_ANSWER
    assert sch["provenance"] == "cbse_marking_scheme"
    assert sch["sourcePaperCode"] == "31/1/1"
    assert sch["sourceDocumentId"] == "src:" + "a" * 24


def test_relink_does_not_serve_a_scheme_no_official_key_verifies(tmp_path):
    """Existing content no official key accounts for is never labelled --
    that would be the fabrication the relink exists to prevent -- and since
    Task 151 it is not served unlabelled either (user decision 2026-09-22,
    correctness first): it goes to the quarantine as unbacked-key, whole, for
    a person to review. It used to be kept: on-topic is not the board's
    answer."""
    idx, parse, stem22 = _setup(tmp_path)
    make_parse_tree(parse, "f" * 24, [(1, "Series 99/9/9 Science " + "body " * 40)])
    kept = "Lead nitrate and potassium iodide give yellow lead iodide"
    existing = {"totalMarks": 3, "markingPoints": [{"id": "k", "description": kept, "marks": 3}]}
    recs = [question("f" * 24, 1, stem=stem22, scheme=existing)]
    rep = relink_answer_schemes(recs, idx, parse_dir=parse)

    assert rep.already_had_scheme == 1
    assert rep.verified_existing_scheme == 0
    assert rep.existing_scheme_removed == 1
    assert rep.quarantined == {"unbacked-key": 1}
    assert rep.with_scheme == 0
    sch = recs[0]["answerScheme"]
    assert sch["markingPoints"] == [] and sch["modelAnswer"] == ""
    assert sch.get("provenance") != "cbse_marking_scheme"
    [entry] = rep.quarantine
    assert entry["scheme"]["markingPoints"][0]["description"] == kept


def test_relink_removes_an_unlabelled_scheme_that_answers_another_question(tmp_path):
    """Unlabelled is not harmless: the scorer and the teacher read it all the same."""
    idx, parse, stem22 = _setup(tmp_path)
    make_parse_tree(parse, "f" * 24, [(1, "Series 99/9/9 Science " + "body " * 40)])
    existing = {"totalMarks": 3, "markingPoints": [
        {"id": "k", "description": "Refraction of light through a glass slab", "marks": 3}]}
    recs = [question("f" * 24, 1, stem=stem22, scheme=existing)]
    rep = relink_answer_schemes(recs, idx, parse_dir=parse)

    assert rep.quarantined == {"content-mismatch": 1}
    assert rep.with_scheme == 0
    assert recs[0]["answerScheme"]["markingPoints"] == []


def test_relink_reports_a_series_with_nothing_that_matches(tmp_path):
    """The series is in the index, but no row shares a word with the stem and
    none sits under the question's own number -- distinct from the series
    being absent entirely, and the report says which. (Before the content
    join this was "code present, no answer for q_no".)"""
    idx, parse, _ = _setup(tmp_path)
    recs = [question("a" * 24, 5)]
    rep = relink_answer_schemes(recs, idx, parse_dir=parse)

    assert rep.newly_attached == 0
    assert rep.no_matching_candidate == 1
    assert rep.code_not_in_answer_keys == 0


def test_relink_reports_an_unknown_code(tmp_path):
    idx, parse, _ = _setup(tmp_path)
    make_parse_tree(parse, "f" * 24, [(1, "Series 99/9/9 Science " + "body " * 40)])
    recs = [question("f" * 24, 1)]
    rep = relink_answer_schemes(recs, idx, parse_dir=parse)

    assert rep.code_not_in_answer_keys == 1
    assert rep.newly_attached == 0


def test_relink_never_attaches_a_scheme_with_no_points(tmp_path):
    """The no-invention rule. A scheme attributed to CBSE with zero value
    points would be a false attribution, which is worse than no scheme."""
    idx, parse, _ = _setup(tmp_path)
    # q_no 1 exists but its value_points list is a single point; q_no 22 is fine.
    recs = [question("a" * 24, 1), question("a" * 24, 22)]
    relink_answer_schemes(recs, idx, parse_dir=parse)
    for rec in recs:
        sch = rec["answerScheme"]
        if sch.get("provenance") == "cbse_marking_scheme":
            assert sch["markingPoints"], f"{rec['id']} claims CBSE with no points"


def test_relink_attaches_an_objective_scheme_for_a_letter_only_answer(tmp_path):
    """A 31/2/1-style objective key carries only a correct-option letter and
    no value points. The scheme must keep the letter -- a one-marks point
    naming the option, a two-level rubric, and metadata.correctOption so the
    grading path can score it. Before the objective branch, the letter was
    silently dropped and 53 corpus records were left with empty markingPoints.
    """
    db = make_answer_keys(tmp_path / "ak.db", [
        ("Science", "X", None, 1, "B", "lysosome", "[]", 1.0,
         "X_086_31-1-1 MS.pdf"),
    ])
    parse = tmp_path / "parse"
    make_parse_tree(parse, "a" * 24, [
        (1, "Series 31/1/1 Science " + "body " * 40),
        (2, "Which cell organelle is known as the suicide bag of the cell? " + "x " * 40),
    ])
    stem = ("Which cell organelle is known as the suicide bag of the cell? "
            "(A) mitochondrion  (B) lysosome  (C) ribosome  (D) golgi apparatus")
    idx = AnswerKeyIndex(db)
    recs = [question("a" * 24, 1, marks=1, stem=stem)]
    rep = relink_answer_schemes(recs, idx, parse_dir=parse)

    assert rep.newly_attached == 1
    sch = recs[0]["answerScheme"]
    assert sch["provenance"] == "cbse_marking_scheme"
    assert sch["sourcePaperCode"] == "31/1/1"
    assert len(sch["markingPoints"]) == 1
    mp = sch["markingPoints"][0]
    assert mp["description"] == "Correct option B: lysosome"
    assert mp["keyword"] == "lysosome"
    assert mp["isRequired"] is True
    assert mp["synonyms"] == ["B"]
    assert sch["metadata"]["objective"] is True
    assert sch["metadata"]["correctOption"] == "B"
    assert sch["metadata"]["options"]["A"] == "mitochondrion"
    assert [l["label"] for l in sch["rubricLevels"]] == ["Correct", "Incorrect"]
    assert any("distractor" in e for e in sch["commonErrors"])
    assert sch["hasPartialCredit"] is False


def test_relink_refuses_a_letter_when_the_stem_carries_no_options(tmp_path):
    """Most 31/2/1 stems carry no (A)-(D) option text (40 of 53 records).
    Before Task 15 the letter alone became the scheme. A letter that no
    option in the stem can be checked against ties nothing to this question
    -- 2 of the 3 such served keys checked by hand keyed the wrong verdict of
    an assertion-reason item -- so it is no longer labelled official."""
    db = make_answer_keys(tmp_path / "ak.db", [
        ("Science", "X", None, 14, "B", "", "[]", 1.0,
         "X_086_31-1-1 MS.pdf"),
    ])
    parse = tmp_path / "parse"
    make_parse_tree(parse, "a" * 24, [
        (1, "Series 31/1/1 Science " + "body " * 40),
    ])
    idx = AnswerKeyIndex(db)
    recs = [question("a" * 24, 14, marks=1, stem="An electricity line x " * 30)]
    rep = relink_answer_schemes(recs, idx, parse_dir=parse)

    assert rep.newly_attached == 0
    assert rep.rejected == {"unreadable-options": 1}
    assert rep.all_candidates_rejected == 1
    sch = recs[0]["answerScheme"]
    assert sch.get("provenance") != "cbse_marking_scheme"
    assert sch["markingPoints"] == []


def test_relink_is_blocked_by_a_question_id_it_cannot_read(tmp_path):
    idx, parse, _ = _setup(tmp_path)
    recs = [{"id": "not-a-canonical-id", "stem": "x" * 80, "marks": 1,
             "answerScheme": {"totalMarks": 1, "markingPoints": []}}]
    rep = relink_answer_schemes(recs, idx, parse_dir=parse)
    assert rep.no_source_hash == 1


# --------------------------------------------------------------------------- #
# enrichment
# --------------------------------------------------------------------------- #

def test_enrich_sets_the_standalone_asset_fields():
    rec = question("a" * 24, 1)
    enrich_record(rec)
    assert rec["rights"]["origin"] == "CBSE"
    # Unsettled legal position must fail closed, not default to permissive.
    assert rec["rights"]["redistribution"] == "unknown"
    assert rec["calibration"]["measured"] is False
    assert rec["calibration"]["basis"] == "assigned"
    assert rec["version"] == 1
    assert rec["reviewState"] == "published"
    assert rec["language"] == "en"


def test_enrich_is_idempotent():
    """Running the pipeline twice must not double-bump a version or reset a
    rights decision someone has since recorded."""
    rec = question("a" * 24, 1)
    enrich_record(rec)
    rec["version"] = 7
    rec["rights"]["redistribution"] = "private-only"
    enrich_record(rec)
    assert rec["version"] == 7
    assert rec["rights"]["redistribution"] == "private-only"


def test_enrich_marks_everything_published_and_rights_cleared():
    recs = [question("a" * 24, i) for i in range(1, 6)]
    counts = enrich_all(recs)
    assert counts == {
        "total": 5, "rights_set": 5, "published": 5,
        "with_provenance": 0, "with_page": 0, "with_official_scheme": 0,
    }


def test_rights_defaults_are_the_restrictive_answer():
    rights = rights_for_cbse_board_paper()
    assert rights.redistribution == "unknown"
    assert rights.basis == ""
    assert "CBSE" in rights.attribution or "Central Board" in rights.attribution


def test_calibration_declares_itself_assigned():
    cal = assigned_calibration()
    assert cal.measured is False
    assert cal.sample_size == 0
    assert cal.facility is None


def test_relink_counts_a_carried_official_scheme_as_covered(tmp_path):
    """A CBE/SQP record keeps its builder's scheme and must count toward coverage."""
    rec = {"id": "cbe:q:Maths7X1", "answerScheme": {
        "provenance": "cbse_marking_scheme", "modelAnswer": "5",
        "markingPoints": [{"description": "5"}]}}
    before = json.dumps(rec, sort_keys=True)
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", []))
    report = relink_answer_schemes([rec], idx, parse_dir=tmp_path)
    assert json.dumps(rec, sort_keys=True) == before
    assert report.carried_official == 1
    assert report.with_scheme == 1
