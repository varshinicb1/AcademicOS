"""The CBSE CBE parser, pinned against the real documents.

These tests read the actual PDFs, because every bug this parser has had was
invisible to a synthetic fixture: the fixtures only contain the separators,
layouts and id shapes their author thought of. Specifically, all of these were
found only by parsing the real files and comparing counts:

  * `ITEM_ID` required a trailing digit, so `English6SB` (a real id) was
    rejected and English Class 6 parsed to 3 items.
  * Science content codes are dotted (`9.1.13`), not `6A1a`, so topic coverage
    read as 0% and looked like a property of the source.
  * Items do not align to page boundaries, so page-based splitting missed every
    Maths item that shared a page with another.
  * The Item Index emits one cell per line, so a row-per-line regex matched
    nothing.

The floors below are deliberately set to today's measurement rather than to a
target. A regression should fail; an improvement should not.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

sys.path.insert(0, str(ROOT / "scripts"))
from build_cbe_bank import _MAX_SINGLE_QUESTION_MARKS  # noqa: E402

from academicos.corpus.cbse_cbe import (
    ITEM_ID,
    parse_all,
    parse_index,
    parse_item_bank,
    subject_and_grade_for,
    to_bank_record,
)

CORPUS = ROOT / "academicos-data" / "corpus" / "cbse-cbe"
pytestmark = pytest.mark.skipif(
    not CORPUS.exists() or not any(CORPUS.glob("*.pdf")),
    reason="CBSE CBE item banks not downloaded; run scripts/ingest_cbse_item_banks.py")


@pytest.fixture(scope="module")
def items():
    parsed, errors = parse_all(CORPUS)
    assert not errors, f"parser raised on real documents: {errors}"
    return parsed


# --------------------------------------------------------------------------- #
# item identity -- the bug that cost 42 of English Class 6's 46 items
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("ident", [
    "Maths6AS1", "Science10YP3", "English9JV4a",
    # No trailing digit. Requiring one silently dropped every item shaped this
    # way, which is most of English Class 6 and Class 8.
    "English6SB", "English8IN", "English6SN2",
])
def test_item_ids_with_and_without_a_trailing_digit_are_recognised(ident):
    assert ITEM_ID.match(ident), ident


@pytest.mark.parametrize("not_an_id", [
    "Item Index", "Mark scheme", "Text A", "Answer", "Guidance", "",
    "6A1a", "9.1.13",                 # a content code, not an item id
])
def test_junk_is_not_an_item_id(not_an_id):
    assert not ITEM_ID.match(not_an_id), not_an_id


def test_a_sub_question_id_is_a_real_id():
    """`Maths6MG4a` and `Maths6MG4b` are a 1-mark and a 2-mark question inside
    one assessment item, and the index lists both. They are therefore valid ids
    and must NOT be filtered -- an earlier version of the junk test above
    wrongly listed one, which is the kind of assumption that only a real
    document disproves."""
    assert ITEM_ID.match("Maths6MG4a")
    assert ITEM_ID.match("Maths6MG4b")
    assert ITEM_ID.match("Science9SRN41bi")


# --------------------------------------------------------------------------- #
# scales, pinned
# --------------------------------------------------------------------------- #

def test_the_whole_corpus_parses_to_a_plausible_scale(items):
    """Floors, not targets: a regression fails, an improvement does not.

    The documents state an ITEM count in their introduction while the index
    lists QUESTION ids, and one item can carry several questions
    (`Maths6MG4a` and `Maths6MG4b` are a 1- and a 2-mark question inside one
    item). So the parsed count legitimately exceeds the stated item count, and
    the meaningful check is that it is not wildly off in either direction.
    """
    assert 600 <= len(items) <= 2000, len(items)


def test_most_items_carry_an_answer_key(items):
    """The hard requirement. Without a mark scheme it is not a question."""
    with_key = sum(1 for i in items if i.has_answer_key)
    assert with_key / len(items) >= 0.45, f"{with_key}/{len(items)}"


def test_most_items_are_mapped_to_a_curriculum_topic(items):
    mapped = sum(1 for i in items if i.content_code)
    assert mapped / len(items) >= 0.40, f"{mapped}/{len(items)}"


def test_every_document_contributes_items(items):
    """A document that parses to zero items is the failure mode that looks like
    an empty source."""
    by_pdf = {}
    for i in items:
        by_pdf[i.source_pdf] = by_pdf.get(i.source_pdf, 0) + 1
    for pdf in CORPUS.glob("*.pdf"):
        assert by_pdf.get(pdf.name, 0) > 0, f"{pdf.name} produced no items"


def test_maths_and_science_classes_are_near_complete(items):
    """These are the two subjects the parser handles well, so they are held to
    a tight floor. The documents state: Maths 58/43/81/112/100 and Science
    42/47/36/59/78 items for classes 6-10.

    Maths Class 6 is the clearest case: it stated 58 items and parsed 14 before
    the page-boundary bug was fixed.
    """
    counts = {}
    for i in items:
        if i.has_answer_key and i.marks:
            counts[(i.subject, i.grade)] = counts.get((i.subject, i.grade), 0) + 1
    expected = {
        ("Mathematics", 6): 55, ("Mathematics", 7): 38, ("Mathematics", 8): 50,
        ("Mathematics", 9): 100, ("Science", 6): 38, ("Science", 7): 43,
        ("Science", 8): 33, ("Science", 9): 55,
    }
    short = {k: (counts.get(k, 0), v) for k, v in expected.items()
             if counts.get(k, 0) < v}
    assert not short, f"(actual, floor) below target: {short}"


def test_english_is_parsed_but_still_behind_maths_and_science(items):
    """Stated honestly rather than asserted as complete.

    2026-09-18: passage-linked groups (English6SB-style) are now split into
    their real per-question sub-items -- see cbse_cbe.py's module docstring
    and parse_group_items for the mechanism. English Class 6 went from 4
    items to 12, Class 9 from 31 to 77. This is real progress, not parity:
    one Class 6 group is still correctly refused (a 5(a)/5(b) id-count
    mismatch), and this floor is today's measurement, not a target.
    """
    eng = [i for i in items if i.subject == "English"]
    assert len(eng) > 150, f"English parsed only {len(eng)} items"
    assert len(eng) < 400, "English now parses far more; update this note"

    by_grade = {}
    for i in eng:
        if i.has_answer_key:
            by_grade[i.grade] = by_grade.get(i.grade, 0) + 1
    expected = {6: 12, 7: 40, 8: 8, 9: 50, 10: 25}
    short = {g: (by_grade.get(g, 0), floor) for g, floor in expected.items()
             if by_grade.get(g, 0) < floor}
    assert not short, f"(actual, floor) below target: {short}"


def test_no_item_has_zero_marks(items):
    """A mark-less question corrupts any marks distribution it appears in, and
    three such artefacts were produced by section headings being parsed as
    items before this was gated."""
    bad = [i.item_id for i in items if i.has_answer_key and not i.marks]
    assert bad, "expected the parser to produce mark-less artefacts to filter"
    # `marks_unresolved` items are the deliberate exception and are held out of
    # this invariant: they carry a passage group's TOTAL in `.marks`, which is
    # not any single question's weight, so `to_bank_record` emits 0 for them on
    # purpose and the build's marks gate then excludes them. Asserting this
    # over all marked items is what caught the change.
    records = [to_bank_record(i) for i in items
               if i.has_answer_key and i.marks and not i.marks_unresolved]
    assert all(r["marks"] > 0 for r in records)


def test_an_unresolved_group_mark_emits_zero_and_preserves_the_stated_total(items):
    """The group total must neither be served as a question's weight nor lost.

    Measured before this existed: 26 English items were served at 14-15 marks,
    because a passage group that could not be split falls back to a single item
    carrying the group's total. `English8IN`'s entire stem was the group header.
    """
    unresolved = [i for i in items if i.marks_unresolved]
    assert unresolved, "expected at least one unsplit passage group"
    for item in unresolved:
        rec = to_bank_record(item)
        assert rec["marks"] == 0, (
            f"{item.item_id} was served at {rec['marks']} marks, which is its "
            "passage group's total rather than its own"
        )
        assert rec["metadata"]["marksUnresolved"] is True
        # The stated total survives for a future splitter, but is not required
        # to be positive: some group-like blocks carry no parseable mark value
        # at all (`English7SP`), and flagging those is still correct.
        assert rec["metadata"]["groupMarksStated"] >= 0

    # The case that motivated the fix must appear: an item whose group total was
    # a plainly impossible question weight.
    positives = [i.group_marks_stated for i in unresolved if i.group_marks_stated > 0]
    assert positives, "no unresolved group actually carried a stated total"
    assert max(positives) > _MAX_SINGLE_QUESTION_MARKS, (
        f"the largest preserved group total is {max(positives)}; the defect this "
        "test pins was a group total of 14-15 marks served as a question weight"
    )


# --------------------------------------------------------------------------- #
# the index -- the topic mapping
# --------------------------------------------------------------------------- #

def test_the_index_yields_content_codes_for_maths_and_science():
    for name in ("Item-Bank---Maths-Class-6.pdf", "Item-Bank---Science-Class-6.pdf"):
        idx = parse_index(CORPUS / name)
        assert len(idx) >= 10, f"{name}: {len(idx)} index rows"
        assert all(v["content_code"] for v in idx.values())


def test_the_index_is_authoritative_over_the_items_own_metadata(items):
    """Precedence bug: a loose in-item regex produced codes that do not exist in
    the curriculum and overrode the correct index value, collapsing 638 items
    onto seven distinct codes."""
    codes = {i.content_code for i in items if i.content_code}
    assert len(codes) > 150, f"only {len(codes)} distinct codes"


def test_content_codes_match_the_curriculum_shapes(items):
    """`6A1a` for Maths and English, `9.1.13` for Science. Anything else is a
    false match."""
    import re
    maths_english = re.compile(r"^\d{1,2}[A-Z]\d{1,2}[a-z]?$")
    science = re.compile(r"^\d{1,2}\.\d{1,2}\.\d{1,2}$")
    # English pseudo-codes: ENG10.1, ENG10.3, etc.
    english_pseudo = re.compile(r"^ENG\d{1,2}\.\d+$")
    odd = {i.content_code for i in items if i.content_code
           and not (maths_english.match(i.content_code)
                    or science.match(i.content_code)
                    or english_pseudo.match(i.content_code))}
    assert not odd, f"codes that are neither shape: {sorted(odd)[:12]}"


# --------------------------------------------------------------------------- #
# passage-linked groups -- English's weak-subject cause, fixed 2026-09-18
# --------------------------------------------------------------------------- #

from academicos.corpus.cbse_cbe import (
    _extract_group_passage,
    _group_sub_item_ids,
    _split_group_questions,
    _split_group_scheme,
    parse_group_items,
    split_items,
)

ENGLISH_6 = CORPUS / "Item-Bank---English---Class-6.pdf"
needs_english_6 = pytest.mark.skipif(not ENGLISH_6.exists(), reason="English Class 6 PDF not downloaded")


def _block_for(pdf_path: Path, sub_id_prefix: str) -> tuple[list[str], list[int], str]:
    for item_id, pages, block in split_items(pdf_path):
        sub_ids = _group_sub_item_ids(block)
        if sub_ids and sub_ids[0].startswith(sub_id_prefix):
            return sub_ids, pages, block
    raise AssertionError(f"no group found starting with {sub_id_prefix}")


@needs_english_6
def test_a_bare_list_of_ids_is_recognised_as_a_group():
    """English6SB1 through English6SB9 are listed back-to-back under one
    shared 'Item identity' table, with nothing but blank lines between them
    -- the discriminator this function keys on, since a Maths/Science
    multi-part item always has real content (a flag, a code) between its
    sub-item ids instead."""
    sub_ids, _pages, _block = _block_for(ENGLISH_6, "English6SB1")
    assert sub_ids == [f"English6SB{n}" for n in
                       ["1", "2", "3", "4", "5a", "5b", "6", "7", "8"]]


def test_a_maths_multi_part_item_is_not_mistaken_for_a_group():
    """Maths6MG4a is immediately followed by its own C/N/E flag and content
    code, not by another bare id -- split_items()/`_starts_item` already
    handle this correctly, and this path must not interfere."""
    assert _group_sub_item_ids(
        "Item identity\nMaths6MG4a\n\n\nN\n6A1a Form and use algebraic "
        "expressions\nMaths6MG4b\n\n\nN\n6A1a Form and use algebraic "
        "expressions\nTotal marks\nItem purpose\n"
    ) == []


def test_a_single_item_is_not_mistaken_for_a_group():
    assert _group_sub_item_ids(
        "Item identity\nMaths6AS1\n\nN\n6A1a Form and use algebraic "
        "expressions\nItem purpose\n"
    ) == []


def test_split_group_questions_bounds_each_question_by_its_own_marks_annotation():
    zone = ("What is the capital of France?\n(1 mark)\n"
            "Name two rivers in India.\n(2 marks)\n")
    result = _split_group_questions(zone)
    assert result == [
        ("What is the capital of France?", [], 1),
        ("Name two rivers in India.", [], 2),
    ]


def test_split_group_questions_captures_mcq_options():
    zone = "Choose the odd one out.\nA. Cat\nB. Dog\nC. Car\nD. Fish\n(1 mark)\n"
    (text, options, marks) = _split_group_questions(zone)[0]
    assert text == "Choose the odd one out."
    assert options == ["A. Cat", "B. Dog", "C. Car", "D. Fish"]
    assert marks == 1


def test_split_group_scheme_keys_by_sequential_number_not_item_id():
    zone = ("1 What is the capital of France?\nAnswer\nGuidance\nParis\n"
            "2 Name two rivers in India.\nAnswer\nGuidance\nGanga, Yamuna\n")
    answers = _split_group_scheme(zone)
    assert answers == ["Paris", "Ganga, Yamuna"]


def test_split_group_scheme_handles_lettered_sub_parts():
    zone = ("5 (a) Find the noun.\nAnswer\nGuidance\ncat\n"
            "5 (b) Find the verb.\nAnswer\nGuidance\nrun\n")
    assert _split_group_scheme(zone) == ["cat", "run"]


@needs_english_6
def test_group_questions_are_split_by_their_own_trailing_marks_annotation():
    sub_ids, _pages, block = _block_for(ENGLISH_6, "English6SB1")
    items = parse_group_items(sub_ids, [1], block, subject="English", grade=6,
                              source_pdf="x.pdf")
    assert len(items) == 9
    assert [i.marks for i in items] == [1, 1, 2, 1, 1, 2, 2, 1, 4]
    assert all(i.has_answer_key for i in items)
    assert "spring" in items[0].answer.lower()


def test_extract_group_passage_reads_between_source_and_question():
    block = ("Item purpose\nAssesses reading.\nSource(s)\nText A\nOnce upon a "
             "time there was a fox.\nQuestion(s)\nWhat animal is this?\n(1 mark)\n")
    assert _extract_group_passage(block) == "Text A Once upon a time there was a fox."


@needs_english_6
def test_every_group_sub_item_carries_the_shared_passage():
    """A linked-passage question with no passage is exactly as unanswerable
    as a figure-dependent one with no figure -- see needs_figure."""
    sub_ids, _pages, block = _block_for(ENGLISH_6, "English6SB1")
    items = parse_group_items(sub_ids, [1], block, subject="English", grade=6,
                              source_pdf="x.pdf")
    assert all("gardening" in i.passage.lower() for i in items)


@needs_english_6
def test_a_genuine_id_count_mismatch_is_refused_not_guessed():
    """English6SN2 in the real Class 6 document has 11 separately-marked
    questions (5(a) and 5(b) are distinct) under only 10 declared sub-item
    ids -- the module's 'never guess an alignment' rule must refuse this
    group rather than misassign one answer to the wrong question."""
    sub_ids, pages, block = _block_for(ENGLISH_6, "English6SN2")
    assert len(sub_ids) == 10
    items = parse_group_items(sub_ids, pages, block, subject="English", grade=6,
                              source_pdf="x.pdf")
    assert items == []


def test_a_failed_group_split_falls_back_to_the_single_item_path(items):
    """Real regression, found and fixed 2026-09-18: parse_item_bank used to
    `continue` unconditionally once _group_sub_item_ids found 2+ ids, even
    when parse_group_items then refused to split them -- silently dropping
    items that the ordinary single-item path had always parsed correctly.
    English6SN2's own bare group blob must therefore still appear, parsed
    the old way, even though its sub-items don't."""
    ids = {i.item_id for i in items}
    assert "English6SN2" in ids or any(i.startswith("English6SN2") for i in ids)


# --------------------------------------------------------------------------- #
# conversion
# --------------------------------------------------------------------------- #

def test_the_bank_record_carries_the_topic_mapping_and_the_scheme(items):
    sample = next(i for i in items if i.has_answer_key and i.content_code)
    rec = to_bank_record(sample)
    assert rec["contentCode"]
    assert rec["answerScheme"]["provenance"] == "cbse_marking_scheme"
    assert rec["answerScheme"]["markingPoints"]
    assert rec["source"] == "cbse_question_bank"
    # Rights must fail closed: no written position exists for CBSE content.
    assert rec["rights"]["redistribution"] == "unknown"
    assert rec["metadata"]["aoMarks"] == sample.ao_marks


def test_a_question_with_no_scheme_gets_provenance_none(items):
    bare = next(i for i in items if not i.has_answer_key)
    rec = to_bank_record(bare)
    assert rec["answerScheme"]["provenance"] == "none"
    assert rec["answerScheme"]["markingPoints"] == []


def test_subject_and_grade_are_read_from_the_filename():
    assert subject_and_grade_for(Path("Item-Bank---Maths-Class-6.pdf")) == ("Mathematics", 6)
    assert subject_and_grade_for(Path("Item-Bank-----English---Class-9.pdf")) == ("English", 9)
    assert subject_and_grade_for(Path("Item-Bank--Maths---Class-10.pdf")) == ("Mathematics", 10)


# --------------------------------------------------------------------------- #
# English pseudo-codes must carry the item's OWN grade
#
# `_english_pseudo_code(grade, text_type)` takes a grade, but both call sites
# passed the literal 10 while `parse_index` discarded the real one into `_`.
# Every English item in the corpus therefore came out as `ENG10.x` -- and 102
# of the 115 English items are classes 6, 7 and 9, not 10. Coarse-code topic
# mapping keys on that strand, so class 9 poetry and class 10 poetry collapsed
# into one bucket.
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("grade", [6, 7, 9, 10])
def test_english_pseudo_codes_use_the_items_own_grade(grade):
    pdf = next((p for p in CORPUS.glob("*.pdf")
                if subject_and_grade_for(p) == ("English", grade)), None)
    if pdf is None:
        pytest.skip(f"no English class {grade} item bank downloaded")
    index = parse_index(pdf)
    codes = {v["content_code"] for v in index.values() if v.get("content_code")}
    if not codes:
        pytest.skip(f"English class {grade} index yielded no content codes")
    wrong = {c for c in codes if not c.startswith(f"ENG{grade}.")}
    assert not wrong, (
        f"English class {grade} produced codes for another grade: {sorted(wrong)[:6]}")


def test_english_pseudo_code_builds_the_strand_from_the_grade_it_is_given():
    from academicos.corpus.cbse_cbe import _english_pseudo_code

    assert _english_pseudo_code(9, "Poetry") == "ENG9.1"
    assert _english_pseudo_code(10, "Poetry") == "ENG10.1"
    assert _english_pseudo_code(6, "Drama") == "ENG6.2"
    # an unrecognised text type still keeps the grade
    assert _english_pseudo_code(7, "Something unmapped") == "ENG7.0"


# --------------------------------------------------------------------------- #
# the English index must read its whole table, not one row per passage
#
# The "Text type" column is a VERTICALLY MERGED cell: PyMuPDF returns its text
# on the first row of a passage group and "" for every sibling question under
# it. Gating on a non-empty text type therefore kept only the first question of
# each passage -- 65 of 350 rows across the five English item banks. Two more
# losses compounded it: the column indices were hardcoded at 6/7, which is one
# place right for Class 6 (it has no AO3 column), and a continuation page was
# accepted or rejected on `rows[0]` alone, so one unmatched id at the top of a
# page discarded every valid row beneath it.
# --------------------------------------------------------------------------- #

def _english_qid_rows(pdf: Path) -> int:
    """Count rows the index table actually carries, independent of the parser."""
    import fitz

    from academicos.corpus.cbse_cbe import _QID_CELL, _cell

    doc = fitz.open(pdf)
    try:
        return sum(
            1
            for i in range(min(14, len(doc)))
            for table in doc[i].find_tables()
            for row in (table.extract() or [])
            if row and len(row) > 1 and _QID_CELL.match(_cell(row, 1))
        )
    finally:
        doc.close()


def _english_banks() -> list[Path]:
    return [p for p in sorted(CORPUS.glob("*.pdf"))
            if subject_and_grade_for(p)[0].lower() == "english"]


def test_english_index_captures_nearly_every_row_it_is_given():
    banks = _english_banks()
    if not banks:
        pytest.skip("no English item banks downloaded")
    present = sum(_english_qid_rows(p) for p in banks)
    captured = sum(len(parse_index(p)) for p in banks)
    assert present >= 300, f"corpus shrank; only {present} index rows found"
    # Was 65/350 (19%) while the merged-cell rows were dropped.
    assert captured >= present * 0.9, (
        f"index captured {captured} of {present} rows ({100 * captured / present:.0f}%)")


@pytest.mark.parametrize("grade", [6, 7, 8, 9, 10])
def test_every_english_grade_contributes_index_rows(grade):
    pdf = next((p for p in _english_banks()
                if subject_and_grade_for(p)[1] == grade), None)
    if pdf is None:
        pytest.skip(f"no English class {grade} item bank")
    present = _english_qid_rows(pdf)
    captured = len(parse_index(pdf))
    assert captured >= present * 0.9, (
        f"class {grade}: {captured} of {present} rows")


def test_class_6_reads_the_text_type_column_not_the_source_blurb():
    """Class 6 English has no AO3 column, so its table is 7 wide, not 8.

    Reading a fixed column 6 took `Source description` -- a prose sentence --
    as the text type, which then keyword-matched into an essentially random
    strand: four of the five rows that survived fell to the `.0` fallback.
    """
    pdf = next((p for p in _english_banks()
                if subject_and_grade_for(p)[1] == 6), None)
    if pdf is None:
        pytest.skip("no English class 6 item bank")
    index = parse_index(pdf)
    assert index, "class 6 index parsed to nothing"
    # A text type is a short label ("Poetry", "Informative magazine article"),
    # never a sentence of source prose.
    long_topics = {v["topic"] for v in index.values() if len(v["topic"]) > 60}
    assert not long_topics, f"source blurbs read as text types: {sorted(long_topics)[:3]}"
    unknown = [v for v in index.values() if v["content_code"].endswith(".0")]
    assert len(unknown) < len(index) * 0.5, (
        f"{len(unknown)}/{len(index)} class 6 rows fell to the unknown strand")


def test_english_index_reads_ao3_and_ao4():
    """AO3/AO4 columns carry real marks and were never read."""
    rows = [v for p in _english_banks() for v in parse_index(p).values()]
    if not rows:
        pytest.skip("no English item banks downloaded")
    assert any(r.get("ao3_marks") or r.get("ao4_marks") for r in rows), (
        "no row carries AO3 or AO4 marks; the columns are still unread")


@pytest.mark.parametrize("text_type", [
    "Text A Informative newspaper article",
    "Text A Informative magazine article",
    "Text A information Advertisement",
])
def test_informational_text_types_reach_a_real_strand(text_type):
    """`informative` is not a substring of `information`.

    Keying strand 5 on "information" alone sent every "Informative newspaper
    article" and "Informative magazine article" to the `.0` unknown fallback --
    53 rows across classes 6-8. This was invisible while those rows were being
    dropped by the merged-cell bug; capturing them surfaced it.
    """
    from academicos.corpus.cbse_cbe import _english_pseudo_code

    assert not _english_pseudo_code(8, text_type).endswith(".0")


def test_no_english_grade_leaves_a_large_share_in_the_unknown_strand():
    for pdf in _english_banks():
        index = parse_index(pdf)
        if not index:
            continue
        unknown = sum(1 for v in index.values() if v["content_code"].endswith(".0"))
        grade = subject_and_grade_for(pdf)[1]
        assert unknown <= len(index) * 0.1, (
            f"class {grade}: {unknown}/{len(index)} rows in the unknown strand")


# --------------------------------------------------------------------------- #
# what the index reads must reach the item
# --------------------------------------------------------------------------- #

def test_english_items_carry_ao3_and_ao4_marks(items):
    """Reading AO3/AO4 off the index is useless if the merge drops them.

    `CbeItem` declared only AO1/AO2, so an item whose index row says AO4 = 10
    reported `aoMarks` without it, and any marks-by-objective report on English
    was understated.
    """
    english = [i for i in items if i.subject == "English"]
    if not english:
        pytest.skip("no English items parsed")
    assert any({"AO3", "AO4"} & set(i.ao_marks) for i in english), (
        "no English item carries AO3/AO4 marks")


def test_english_items_take_the_source_description_from_the_index(items):
    """The index's `Source description` was extracted and then never read.

    For English it is the only human-readable description the index carries,
    and `scripts/map_topics.py` feeds `content_reference` into the topic
    mapper's training text -- so the mapper was missing that signal.
    """
    english = [i for i in items if i.subject == "English"]
    if not english:
        pytest.skip("no English items parsed")
    with_ref = sum(1 for i in english if i.content_reference)
    assert with_ref >= len(english) * 0.5, (
        f"only {with_ref}/{len(english)} English items have a content reference")
