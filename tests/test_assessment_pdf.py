"""CBSE-format paper renderer (assessment/pdf.py).

Verify the watermark_id parameter threading through _page_furniture/export_pdf:
the generated PDF's actual bytes contain the watermark id text when one is
passed, and contain no watermark text when it is None. PDFs are read back with
PyMuPDF (fitz), the same pattern used elsewhere in this repo.
"""
from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.assessment.pdf import (
    escape,
    export_pdf,
    pdf_safe,
    split_stem_and_options,
)
from academicos.assessment.schemas import (
    GeneratedPaper,
    GeneratedQuestionSchema,
    GeneratedSectionSchema,
    PaperMetadataSchema,
)


def _make_paper(paper_id: str = "paper_ab12cd", title: str = "Mid Term Examination"):
    now = datetime.now(timezone.utc)
    gq = GeneratedQuestionSchema(
        question_id="q1", display_number=1,
        stem="Which of the following is a gas? (A) Oxygen (B) Gold (C) Silver (D) Copper",
        marks=1, bloom_level="remember", difficulty="easy",
    )
    section = GeneratedSectionSchema(
        section_id="section-a", label="A", name="MCQ", questions=[gq], total_marks=1,
    )
    metadata = PaperMetadataSchema(
        assessment_title=title, subject="Science", grade=10, total_marks=1,
        duration_minutes=60, generated_at=now,
    )
    return GeneratedPaper(
        id=paper_id, assessment_id="assess1", sections=[section], metadata=metadata,
        answer_key={"1": "Oxygen"},
    )


def _extract_text(pdf_path: Path) -> str:
    import fitz

    doc = fitz.open(str(pdf_path))
    try:
        return "".join(page.get_text() for page in doc)
    finally:
        doc.close()


WATERMARK = "Z9-TRACE-42"


def test_export_pdf_embeds_watermark_id(tmp_path):
    out = export_pdf(_make_paper(), tmp_path / "a", watermark_id=WATERMARK)
    assert out.exists()
    text = _extract_text(out)
    assert WATERMARK in text
    assert "Confidential" in text
    assert "traceable copy" in text


def test_export_pdf_without_watermark_has_none(tmp_path):
    out = export_pdf(_make_paper(), tmp_path / "b")
    assert out.exists()
    text = _extract_text(out)
    assert WATERMARK not in text
    assert "Confidential" not in text
    assert "traceable copy" not in text
    # ordinary furniture still present
    assert "Q.P. Code" in text
    assert "Page 1" in text


def test_watermark_differs_per_export(tmp_path):
    a = _extract_text(export_pdf(_make_paper(), tmp_path / "a", watermark_id="COPY-001"))
    b = _extract_text(export_pdf(_make_paper(), tmp_path / "b", watermark_id="COPY-002"))
    assert "COPY-001" in a and "COPY-002" in b
    assert "COPY-002" not in a


def test_paper_content_rendered(tmp_path):
    out = export_pdf(_make_paper(), tmp_path / "c")
    text = _extract_text(out)
    assert "Mid Term Examination" in text
    assert "SECTION A" in text
    assert "Maximum Marks: 1" in text


def test_section_note_matches_real_marks_not_just_the_label(tmp_path):
    """Found 2026-09-18 by actually reading a real generated PDF end-to-end:
    a custom blueprint labeled its section "A" but put 2-mark questions in
    it, and the PDF printed "carrying 1 mark each" anyway -- the CBSE-
    standard description was keyed purely off the label, not the section's
    real content. A section literally named A/B/C/D/E must only get the
    canned CBSE description when its questions' marks actually match that
    convention; otherwise the printed note must reflect the real marks."""
    now = datetime.now(timezone.utc)
    two_mark_questions = [
        GeneratedQuestionSchema(question_id=f"q{i}", display_number=i,
                                 stem=f"Question {i}", marks=2,
                                 bloom_level="understand", difficulty="medium")
        for i in range(1, 4)
    ]
    section = GeneratedSectionSchema(
        section_id="section-a", label="A", name="Section A",
        questions=two_mark_questions, total_marks=6,
    )
    metadata = PaperMetadataSchema(
        assessment_title="Custom Blueprint Paper", subject="Science", grade=10,
        total_marks=6, duration_minutes=30, generated_at=now,
    )
    paper = GeneratedPaper(id="paper_custom", assessment_id="assess1",
                           sections=[section], metadata=metadata, answer_key={})
    text = _extract_text(export_pdf(paper, tmp_path / "d"))
    assert "carrying 2 marks each" in text
    assert "carrying 1 mark each" not in text


def test_section_note_uses_canned_cbse_text_when_marks_do_match(tmp_path):
    """The standard CBSE-blueprint path (label A, 1-mark MCQs) must keep
    printing the descriptive canned text, not just a generic "carrying N
    marks each" -- this is the case the fix in test above must not break."""
    text = _extract_text(export_pdf(_make_paper(), tmp_path / "e"))
    assert "multiple choice questions carrying 1 mark each" in text


def test_section_note_falls_back_to_generic_text_when_marks_vary(tmp_path):
    now = datetime.now(timezone.utc)
    mixed_questions = [
        GeneratedQuestionSchema(question_id="q1", display_number=1, stem="Q1",
                                marks=2, bloom_level="understand", difficulty="medium"),
        GeneratedQuestionSchema(question_id="q2", display_number=2, stem="Q2",
                                marks=3, bloom_level="apply", difficulty="medium"),
    ]
    section = GeneratedSectionSchema(
        section_id="section-a", label="A", name="Section A",
        questions=mixed_questions, total_marks=5,
    )
    metadata = PaperMetadataSchema(
        assessment_title="Mixed Marks Paper", subject="Science", grade=10,
        total_marks=5, duration_minutes=30, generated_at=now,
    )
    paper = GeneratedPaper(id="paper_mixed", assessment_id="assess1",
                           sections=[section], metadata=metadata, answer_key={})
    text = _extract_text(export_pdf(paper, tmp_path / "f"))
    assert "carrying marks as indicated" in text


def test_split_stem_and_options():
    head, options = split_stem_and_options(
        "Which of the following is a gas? (A) Oxygen (B) Gold (C) Silver (D) Copper")
    assert head == "Which of the following is a gas?"
    assert options == ["Oxygen", "Gold", "Silver", "Copper"]


def test_split_stem_and_options_no_options():
    assert split_stem_and_options("State Newton's second law.") == ("State Newton's second law.", [])


def test_split_stem_and_options_non_alpha_start_not_split():
    # Labels must start at (A); "(B) ... (C) ..." is a part label, not options.
    assert split_stem_and_options("(B) second (C) third") == ("(B) second (C) third", [])


def test_split_stem_and_options_out_of_order_not_split():
    head, options = split_stem_and_options("Two parts (A) first (C) third (B) second")
    assert (head, options) == ("Two parts (A) first (C) third (B) second", [])


def test_escape_xml_special_chars():
    assert escape("a < b & c > d") == "a &lt; b &amp; c &gt; d"

from academicos.assessment.pdf import export_answer_key_pdf, pdf_safe  # noqa: E402


def _paper_with(gq, answer="x"):
    now = datetime.now(timezone.utc)
    section = GeneratedSectionSchema(section_id="s", label="A", name="Q",
                                     questions=[gq], total_marks=gq.marks)
    meta = PaperMetadataSchema(assessment_title="T", subject="Science", grade=9,
                               total_marks=gq.marks, duration_minutes=60, generated_at=now)
    return GeneratedPaper(id="p", assessment_id="a", sections=[section],
                          metadata=meta, answer_key={"1": answer})


def _gq(stem, qtype="mcq", marks=1):
    return GeneratedQuestionSchema(question_id="q", display_number=1, stem=stem,
                                   marks=marks, bloom_level="remember",
                                   difficulty="easy", type=qtype)


def test_more_than_four_option_labels_do_not_crash(tmp_path):
    """labels="ABCD" indexed by position raised IndexError on a fifth. A
    repeated label is not a fifth option either: relabelling it (E) shifted
    nothing here but would shift every real option elsewhere, so the stem
    prints verbatim instead."""
    stem = "Pick one. (A) a (B) b (C) c (D) d (D) fifthoption"
    assert split_stem_and_options(stem) == (stem, [])
    text = _extract_text(export_pdf(_paper_with(_gq(stem)), tmp_path))
    assert "(E)" not in text and "(D) d (D) fifthoption" in text


# cbe:q:Science10TM2 as the served bank carries it: a CBE "(a)" sub-question
# label ahead of the real (A)-(D). Taking every label printed "(A) Which
# conclusions are correct?" and shifted the four options to (B)-(E).
_SCIENCE10TM2 = (
    "A student plots the current-voltage graphs of three samples of nichrome wire. "
    "The samples have resistances R1, R2 and R3. The student writes three conclusions: "
    "1. R3 has the lowest resistance 2. The resistors are ohmic 3. R3 dissipates the "
    "most power 1 (a) Which conclusions are correct? (A) 1, 2 and 3 (B) 1 and 2 only "
    "(C) 1 and 3 only (D) 2 and 3 only")


def test_a_sub_question_label_before_the_options_stays_in_the_question():
    head, options = split_stem_and_options(_SCIENCE10TM2)
    assert head.endswith("(a) Which conclusions are correct?")
    assert options == ["1, 2 and 3", "1 and 2 only", "1 and 3 only", "2 and 3 only"]


def test_science10tm2_prints_exactly_a_to_d(tmp_path):
    text = _extract_text(export_pdf(_paper_with(_gq(_SCIENCE10TM2)), tmp_path))
    starts = [line[:3] for line in _option_lines(text) if re.match(r"\([A-Z]\)", line)]
    assert sorted(starts) == ["(A)", "(B)", "(C)", "(D)"], text
    flat = " ".join(text.split())   # the head wraps across lines
    assert "(E)" not in flat and "(a) Which conclusions are correct? (A) 1, 2 and 3" in flat
    assert "(A) Which conclusions" not in flat


def test_an_assertion_label_is_not_option_a():
    """cbse:sqp assertion-reason MCQs: 'Assertion (A) and Reason (R)' came out
    as option (A), the real four as (B)-(E) plus a stray (F)."""
    stem = ("Two statements are given as Assertion (A) and Reason(R). ASSERTION (A): "
            "Caste can divide. REASON (R): It diverts attention. "
            "(A) Both true, R explains A. (B) Both true, R does not explain A. "
            "(C) A true, R false. (D) A false, R true")
    head, options = split_stem_and_options(stem)
    assert "ASSERTION (A): Caste can divide." in head
    assert options == ["Both true, R explains A", "Both true, R does not explain A",
                       "A true, R false", "A false, R true"]


def test_a_repeated_label_with_no_clean_option_run_prints_verbatim():
    """cbse:sqp:ClassXII_2023_24:Home Science:17 -- its options are 'a.'-'d.',
    so its only labels are the two '(A)'s of Assertion and ASSERTION."""
    stem = ("Given below are two statements labeled as Assertion (A) and reason (R). "
            "ASSERTION(A): Your mother is unwell. REASON(R): Bacteria are present. "
            "a. Both true. b. Both true, not explained. c. A true. d. A false.")
    assert split_stem_and_options(stem) == (stem, [])


def test_a_gap_in_the_labels_is_not_an_option_list():
    stem = "Name the parts. (A) root (C) leaf"
    assert split_stem_and_options(stem) == (stem, [])


def test_a_three_option_item_still_grids():
    """cbe:q:Science9TS1 really has three options."""
    stem = "The state of matter which has no fixed shape and no fixed volume is (A) Gas (B) liquid (C) Solid"
    assert split_stem_and_options(stem)[1] == ["Gas", "liquid", "Solid"]


def test_an_option_naming_earlier_options_is_one_option():
    """'Both (A) and (B)' is option (D)'s text. Taking the trailing run from
    the last (A) returned head '... (D) Both' and options ['and', '']."""
    head, options = split_stem_and_options(
        "Which are metals? (A) Iron (B) Copper (C) Sulphur (D) Both (A) and (B)")
    assert head == "Which are metals?"
    assert options == ["Iron", "Copper", "Sulphur", "Both (A) and (B)"]


def test_neither_a_nor_b_is_one_option():
    head, options = split_stem_and_options(
        "Which statements are true? (a) only i (b) only ii (c) both (a) and (b) "
        "(d) neither (a) nor (b)")
    assert head == "Which statements are true?"
    assert options == ["only i", "only ii", "both (a) and (b)", "neither (a) nor (b)"]


# The served bank (compose() at 1e3e30f, 4475 rows) as it carries these stems.
_E268_2 = (  # cbse:q:src:e268efcf2e142b7e0591b8ed:2, passage trimmed
    "As time passed, ‘Vova Watch Company’ transformed from a struggling enterprise to "
    "a profit making enterprise. Identify the leadership style of Ravi Kumar : "
    "(A) Autocratic leadership style (B) Democratic leadership style "
    "(C) Free-rein leadership style (D) Both (A) and (B) 11-")
_HISTORY_XII_2025_10 = (  # cbse:sqp:ClassXII_2025_26:History:10, verbatim
    "There are two statements marked as Assertion (A) and Reason (R). Read the statements "
    "and choose the appropriate option. Assertion (A): Lingayats did not practice funerary "
    "rites such as cremation, prescribed in the Dharmashastras. Reason (R): Lingayats "
    "believe that on death the devotee will be united with Shiva and will not return to "
    "this world. Options: A. Both (A) and (R) are correct and (R) is the correct "
    "explanation of (A). B. Both (A) and (R) are correct and (R) is not the correct "
    "explanation of (A). C. (A) is correct but (R) is not correct. D. (R) is correct but "
    "(A) is not correct (A) Both (A) and (R) are correct and (R) is the correct "
    "explanation of (A). (B) Both (A) and (R) are correct and (R) is not the correct "
    "explanation of (A). (C) (A) is correct but (R) is not correct. (D) (R) is correct "
    "but (A) is not correct")
_BBD21_6 = (  # cbse:q:src:bbd21b0e42bac3cafc7a33a0:6, verbatim (its (c), (d) were lost upstream)
    "Assertion (A) : Increase in the value of liabilities on reconstitution of a firm is "
    "debited to Revaluation Account. Reason (R) : Increase in the value of liabilities is "
    "a loss. 1 Select the correct alternative from the following : (a) Assertion (A) is "
    "correct, but Reason (R) is wrong. (b) Assertion (A) is wrong, but Reason (R) is "
    "correct.")
_9081575F_7 = (  # cbse:q:src:9081575f9ac53e99a3ff660c:7, verbatim: "both" before a real label
    "The number of chromosomes in a cell division is halved. This kind of cell division "
    "is observed in : (A) Only testis (B) Only ovary (C) Ovary and testis both "
    "(D) All cells of the body")

_872D1DD8_1 = (  # cbse:q:src:872d1dd81acb76a5b3aff133:1, verbatim: "neither" option
    "A function f : R+ ® R (where R+ is the set of all non-negative real numbers) defined "
    "by f(x) = 4x + 3 is : (A) one-one but not onto (B) onto but not one-one "
    "(C) both one-one and onto (D) neither one-one nor onto")
_4F618224_8 = (  # cbse:q:src:4f6182240b214906a58eaeab:8, verbatim: "neither" mid-list
    "In triangles ABC and DEF, B = E, F = C and AB = 3 DE. Then, the two triangles are : "
    "(A) congruent but not similar (B) congruent as well as similar "
    "(C) neither congruent nor similar (D) similar but not congruent")
_9365570E_11 = (  # cbse:q:src:9365570e1f6928bdf661841d:11, verbatim: "neither" option
    "The function f(x) = x|x|is 1 (A) continuous and differentiable at x = 0. "
    "(B) continuous but not differentiable at x = 0. (C) differentiable but not "
    "continuous at x = 0. (D) neither differentiable nor continuous at x = 0.")


@pytest.mark.parametrize("stem,options", [
    (_E268_2, ["Autocratic leadership style", "Democratic leadership style",
               "Free-rein leadership style", "Both (A) and (B) 11-"]),
    (_HISTORY_XII_2025_10, [
        "Both (A) and (R) are correct and (R) is the correct explanation of (A)",
        "Both (A) and (R) are correct and (R) is not the correct explanation of (A)",
        "(A) is correct but (R) is not correct",
        "(R) is correct but (A) is not correct"]),
    (_BBD21_6, ["Assertion (A) is correct, but Reason (R) is wrong",
                "Assertion (A) is wrong, but Reason (R) is correct"]),
    (_9081575F_7, ["Only testis", "Only ovary", "Ovary and testis both",
                   "All cells of the body"]),
    (_872D1DD8_1, ["one-one but not onto", "onto but not one-one",
                   "both one-one and onto", "neither one-one nor onto"]),
    (_4F618224_8, ["congruent but not similar", "congruent as well as similar",
                   "neither congruent nor similar", "similar but not congruent"]),
    (_9365570E_11, ["continuous and differentiable at x = 0",
                    "continuous but not differentiable at x = 0",
                    "differentiable but not continuous at x = 0",
                    "neither differentiable nor continuous at x = 0"]),
], ids=["e268:2", "History-XII-2025-26:10", "bbd21:6", "9081575f:7",
        "872d1dd8:1", "4f618224:8", "9365570e:11"])
def test_served_stems_whose_options_name_other_options_split_correctly(stem, options):
    head, got = split_stem_and_options(stem)
    assert got == options
    assert head and stem.startswith(head)


@pytest.mark.parametrize("stem,head,options", [
    ("Which? (A) x (B) y (C) z (D) All of (A), (B) and (C)",
     "Which?", ["x", "y", "z", "All of (A), (B) and (C)"]),
    ("Which? (A) x (B) y (C) z (D) (A), (B) and (C)",
     "Which?", ["x", "y", "z", "(A), (B) and (C)"]),
    ("Which? (A) x (B) y (C) z (D) A and B, i.e. (A) & (B)",
     "Which?", ["x", "y", "z", "A and B, i.e. (A) & (B)"]),
], ids=["all-of-comma-list", "bare-comma-list", "ie-ampersand"])
def test_a_comma_or_ampersand_list_of_mentions_is_one_option(stem, head, options):
    """A mention after ', ' or ' & ' has no naming word before it. The real
    run failed on it, and the run starting at the mention '(A)' won, printing
    head '... (D) All of' and options [',', 'and', '']."""
    assert split_stem_and_options(stem) == (head, options)


def test_a_run_whose_options_are_only_joiners_is_not_an_option_list():
    """If no clean run exists, print the stem as written, never junk options."""
    stem = "Pick one; see (A), (B) and (C) above"
    assert split_stem_and_options(stem) == (stem, [])


def test_one_word_options_like_both_and_neither_still_split():
    head, options = split_stem_and_options("Which? (A) i (B) ii (C) both (D) neither")
    assert options == ["i", "ii", "both", "neither"]


def test_a_delta_that_means_change_in_is_not_a_triangle():
    """pdf_safe runs on every subject; the geometry mapping printed an
    Economics 'Increase in Income (ΔY)' as 'triangle Y'."""
    assert pdf_safe("Increase in Income (ΔY)") == "Increase in Income (delta Y)"
    assert pdf_safe("Energy released = ∆m × 931.5 MeV") == "Energy released = delta m × 931.5 MeV"
    assert pdf_safe("∆\U0001d438\U0001d43c\U0001d43c > ∆EIV") == "delta EII > delta EIV"


def test_a_geometry_triangle_is_still_a_triangle():
    assert pdf_safe("∆OAB is an equilateral triangle") == "triangle OAB is an equilateral triangle"
    assert pdf_safe("Δ ABC ~ Δ PQR") == "triangle ABC ~ triangle PQR"
    # Italic vertex letters, as CBE Maths writes them.
    assert pdf_safe("∆\U0001d443\U0001d446\U0001d444 ~ ∆QSR") == "triangle PSQ ~ triangle QSR"


def test_a_question_taller_than_a_page_exports(tmp_path):
    """Each question was one Table row, which cannot split: LayoutError, HTTP 500."""
    stem = "Explain in detail. " + ("This sentence is deliberately long. " * 900)
    text = _extract_text(export_pdf(_paper_with(_gq(stem, "long_answer", 5)), tmp_path))
    # Every sentence, on whichever page it landed: a split that dropped the
    # overflow would still export a file.
    assert " ".join(text.split()).count("deliberately long") == 900


def test_an_answer_taller_than_a_page_exports(tmp_path):
    paper = _paper_with(_gq("Explain photosynthesis fully.", "long_answer", 5),
                        answer="Value point. " * 3000)
    text = _extract_text(export_answer_key_pdf(paper, tmp_path))
    # >= rather than ==: a table header repeated on each page may add more.
    assert " ".join(text.split()).count("Value point") >= 3000


def test_subparts_of_a_descriptive_question_are_not_gridded_as_options(tmp_path):
    stem = "Two brothers share money. (a) Find each share. (b) Explain. (c) Check. (d) State."
    text = _extract_text(export_pdf(_paper_with(_gq(stem, "long_answer", 4)), tmp_path))
    assert "(A)" not in text and "(a) Find each share" in text


def test_math_italic_letters_survive():
    """'12𝑥2 + 11𝑥−15' printed as '122 + 11−15' -- the variable vanished."""
    assert pdf_safe("12\U0001d4652 + 11\U0001d465−15") == "12x2 + 11x-15"


def _option_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip().startswith("(")]


def test_a_paper_typed_mcq_still_grids_its_options(tmp_path):
    stem = "Which of these is a gas? (A) Oxygen (B) Gold (C) Silver (D) Copper"
    text = _extract_text(export_pdf(_paper_with(_gq(stem, "mcq", 1)), tmp_path))
    assert any(line.startswith("(A)") for line in _option_lines(text))
    assert "gas? (A)" not in text


def test_a_board_one_mark_mcq_typed_very_short_answer_grids_its_options(tmp_path):
    """The board records in questions.json type 1-mark MCQs very_short_answer
    (586 splittable stems, 538 with exactly four options, against 46 typed mcq).
    The objective gate ran their options inline into the stem."""
    stem = ("In the formula of mode given by mode = l + f1 denotes the : "
            "(A) frequency of the modal class (B) frequency of class preceding modal class "
            "(C) frequency of class succeeding modal class (D) cumulative frequency of modal class")
    text = _extract_text(export_pdf(_paper_with(_gq(stem, "very_short_answer", 1)), tmp_path))
    starts = [line[:3] for line in _option_lines(text)]
    for label in ("(A)", "(B)", "(C)", "(D)"):
        assert label in starts, (label, text)
    assert "denotes the : (A)" not in text


def _boot_with_paper(tmp_path, monkeypatch):
    from test_assessment_routes_auth import _boot_client, _register
    from test_route_inventory import blueprint_body, question_body

    client = _boot_client(tmp_path, monkeypatch)
    client.__enter__()
    teacher = _register(client, "school_1", "render-fail@example.com")
    auth = {"Authorization": f"Bearer {teacher['token']}"}
    created = client.post("/api/v1/assessments", json={
        "teacherId": teacher["user"]["id"], "schoolId": "school_1",
        "title": "Render Failure", "subject": "Mathematics", "grade": 10,
        "chapterIds": [], "blueprint": blueprint_body(),
    }, headers=auth)
    assert created.status_code == 200, created.text
    gen = client.post("/api/v1/papers/generate", json={
        "assessmentId": created.json()["id"], "blueprint": blueprint_body(),
        "selectedQuestions": [question_body()],
        "template": {"id": "t1", "schoolId": "school_1", "name": "Default"},
    }, headers=auth)
    assert gen.status_code == 200, gen.text
    return client, auth, gen.json()["id"]


@pytest.mark.parametrize("fmt,fn,action", [
    ("pdf", "export_pdf", "paper_exported"),
    ("answer-key", "export_answer_key_pdf", "answer_key_exported"),
])
def test_a_render_failure_is_a_422_naming_the_cause_and_is_not_audited(
        tmp_path, monkeypatch, fmt, fn, action):
    from academicos.assessment import pdf as pdf_mod
    from academicos.assessment.audit_log import get_audit_log

    client, auth, paper_id = _boot_with_paper(tmp_path, monkeypatch)
    try:
        def boom(*a, **k):
            raise ValueError("stem 7 overflows the frame")

        monkeypatch.setattr(pdf_mod, fn, boom)
        r = client.post(f"/api/v1/papers/{paper_id}/export/{fmt}", headers=auth)
        assert r.status_code == 422, r.text
        assert "stem 7 overflows the frame" in r.json()["detail"]
        assert get_audit_log(tmp_path).for_action(action) == []
    finally:
        client.__exit__(None, None, None)


# ---- a restored symbol must reach the page (Task 121) -----------------------
#
# The merge restores the characters a symbol font took with it
# (corpus/symbol_font.py): U+F072 back to ρ, U+F0B0 back to °. That is only
# half the repair -- a character the registered font has no glyph for prints
# as a notdef box, which PyMuPDF reads back as NUL. These are every character
# the repair puts into the served bank, measured on the merge's own output.

RESTORED_SYMBOLS = (
    # the repaired text, as the record now holds it, and what the page shows
    ("density ρ", "density ρ"),            # cbe:q:Science9PS1
    ("50° at O", "50° at O"),              # cbe:q:Maths9MS6
    ("2α + 1", "2α + 1"),                  # cbe:q:Maths9MS6
    ("find ∠BAC", "find angle BAC"),       # cbe:q:Maths9MS6
    ("6.54 × 4", "6.54 × 4"),              # cbe:q:Maths10AS6
    ("26.16 ÷ 4", "26.16 ÷ 4"),            # cbe:q:Maths6RB5
    ("(Using π = 3.14)", "(Using pi = 3.14)"),   # cbe:q:Maths10AS8
    ("R1 20 Ω", "R1 20 Ω"),                # cbe:q:Science10SD1
    ("x ⇒ y", "x => y"),                   # cbe:q:Maths10AS8's working
    ("∴ altitude", "therefore altitude"),  # Mathematics X f01c7b6f Q27
    ("• Deriving", "- Deriving"),          # the SQP marking schemes' bullet
    ("2⋅4 g/litre", "2·4 g/litre"),        # Biology XII 784bd959 Q27
    ("In ΔACE", "In triangle ACE"),        # cbe:q:Maths9BS8
)


def test_every_restored_symbol_reaches_the_page(tmp_path):
    stem = ("Restored symbols: " + "; ".join(text for text, _ in RESTORED_SYMBOLS)
            + " -- explain each one and give a reason for your answer.")
    paper = _make_paper()
    paper.sections[0].questions[0].stem = stem
    raw = _extract_text(export_pdf(paper, tmp_path / "symbols"))
    assert "\x00" not in raw, "a character the font cannot draw printed as a notdef box"
    printed = " ".join(raw.split())    # the renderer wraps the stem where it must
    for repaired, on_the_page in RESTORED_SYMBOLS:
        assert on_the_page in printed, f"{repaired!r} did not reach the page"


# ---- the table is a guard, not a sample (Task 121 review) -------------------
#
# The section above checks the 13 strings that were measured on the merge's
# output one day. That is a sample: the moment a source supplies Symbol code
# 0x40, `symbol_font.restore_symbol_font` hands the renderer U+2245 CONGRUENT
# -- which Segoe UI has no glyph for -- and nothing stops it. 95 of `SYMBOL`'s
# values are outside Latin-1, and at 64dd21a none of them were in `_PDF_MATH`.
# So the guard is the whole table, plus every non-ASCII character the served
# bank actually holds.

# Where a symbol lives, as against a script's own letters: Greek, general
# punctuation, sub/superscripts, currency, combining marks for symbols,
# letterlike, arrows, math operators, misc technical, box drawing, geometric
# shapes, misc symbols, misc/supplemental math, and the Mathematical
# Alphanumeric block. A language paper written in its own script -- the
# Assamese, Bhutia and Tibetan SQPs, whose text is Bengali and Tibetan -- is a
# different problem: no base font here draws those and no ASCII reading
# replaces them, which wants a bundled script font, not a character table.
SYMBOL_BLOCKS = (
    (0x0370, 0x03FF), (0x02B0, 0x02FF), (0x2000, 0x206F), (0x2070, 0x209F),
    (0x20A0, 0x20CF), (0x20D0, 0x20FF), (0x2100, 0x214F), (0x2190, 0x21FF),
    (0x2200, 0x22FF), (0x2300, 0x23FF), (0x2500, 0x257F), (0x25A0, 0x25FF),
    (0x2600, 0x26FF), (0x27C0, 0x27EF), (0x2980, 0x29FF), (0x2A00, 0x2AFF),
    (0x1D400, 0x1D7FF), (0xE000, 0xF8FF), (0xFF01, 0xFF5E),
)


def _is_symbol(ch: str) -> bool:
    return any(lo <= ord(ch) <= hi for lo, hi in SYMBOL_BLOCKS)


def _renders(chars, tmp_path, tag: str) -> list[str]:
    """Which of `chars` the registered font draws as a notdef box, which
    PyMuPDF reads back as NUL. Rendered in batches so the passing path costs
    one PDF per 20 characters; a failing batch is then split to name them."""
    chars = list(chars)
    bad: list[str] = []
    for start in range(0, len(chars), 20):
        batch = chars[start:start + 20]
        paper = _make_paper()
        paper.sections[0].questions[0].stem = (
            "Symbols: " + " ".join(batch) + " -- explain each and give a reason.")
        if "\x00" not in _extract_text(export_pdf(paper, tmp_path / f"{tag}{start}")):
            continue
        for i, ch in enumerate(batch):
            one = _make_paper()
            one.sections[0].questions[0].stem = (
                f"Symbol: {ch} -- explain what it means and give a reason.")
            if "\x00" in _extract_text(export_pdf(one, tmp_path / f"{tag}{start}_{i}")):
                bad.append(ch)
    return bad


def test_every_symbol_the_repair_can_restore_reaches_the_page(tmp_path):
    """Every value of the Adobe Symbol table, not the handful measured once.
    A code the repair covers is a character it WILL put into a record's text
    the day a source uses it, so the renderer has to be able to print it."""
    from academicos.corpus.symbol_font import SYMBOL

    bad = _renders(sorted(set(SYMBOL.values())), tmp_path, "sym")
    assert bad == [], "restorable symbols the renderer prints as a notdef box: " + repr(bad)


@pytest.mark.skipif(not (ROOT / "academicos-data" / "syllabus" / "questions.json").exists(),
                    reason="served bank not built")
def test_every_symbol_in_the_served_bank_reaches_the_page(tmp_path):
    """And every symbol the bank holds today, whatever put it there -- the
    merge's repair, a source's own Unicode, or an extractor's substitution."""
    import json

    def strings(value):
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict):
            for item in value.values():
                yield from strings(item)
        elif isinstance(value, list):
            for item in value:
                yield from strings(item)

    rows = json.loads((ROOT / "academicos-data" / "syllabus" / "questions.json")
                      .read_text(encoding="utf-8"))["questions"]
    chars = sorted({c for r in rows for s in strings(r) for c in s if _is_symbol(c)})
    bad = _renders(chars, tmp_path, "bank")
    assert bad == [], "served characters the renderer prints as a notdef box: " + repr(bad)


def test_an_exponent_prints_as_an_exponent_not_a_digit():
    """`4y³` printed `4y3` -- a different quantity, and the whole point of the
    question. The re-audit of 2026-09-23 found it on cbe:q:Maths8BS2, whose
    options are `(A) 4y³ (B) 9y³ (C) 13y³ (D) 36y³`. A subscript stays a plain
    digit: `H₂O` reads as H2O, the way chemistry is written in ASCII, and no
    subscript changes a value."""
    assert pdf_safe("(A) 4y³ (B) 9y³") == "(A) 4y^3 (B) 9y^3"
    assert pdf_safe("a² + b² = c²") == "a^2 + b^2 = c^2"
    assert pdf_safe("10⁻³") == "10^-3"
    assert pdf_safe("H₂O and CO₂") == "H2O and CO2"
