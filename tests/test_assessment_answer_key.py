"""assessment/answer_key.py's handling of unreadable marking-scheme PDFs.

Found live 2026-09-18: parse_marking_scheme() caught a corrupt/image-only
PDF's read failure internally and returned an empty list, logging only a
warning -- indistinguishable, to every caller, from "this PDF genuinely has
zero parseable answer keys." scripts/build_answer_keys.py already had a
try/except + a `failed` counter around this exact call, expecting exactly
this failure mode to reach it -- code that could never fire because
parse_marking_scheme swallowed the exception first. build_answer_keys() (the
library function, distinct from the script) had no error handling at all, so
making parse_marking_scheme raise without also fixing that caller would have
turned "one corrupt PDF" into "the whole batch aborts."

This file had zero test coverage before this fix.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.assessment import answer_key as ak
from academicos.assessment.answer_key import (
    KeyedAnswer, PaperKey, _MCQ_PAREN, _PREAMBLE_END, _parse_objective,
    build_answer_keys, parse_marking_scheme,
)
from academicos.config import Config


def _corrupt_pdf(path: Path) -> None:
    path.write_bytes(b"this is not a real pdf file, just garbage bytes")


def test_parse_marking_scheme_raises_on_an_unreadable_pdf(tmp_path):
    bad = tmp_path / "corrupt_MS.pdf"
    _corrupt_pdf(bad)
    with pytest.raises(Exception):
        parse_marking_scheme(bad)


def test_build_answer_keys_counts_unreadable_files_without_aborting_the_batch(tmp_path):
    """The real regression: one corrupt PDF must not crash the whole run, but
    it must be counted as failed, not silently merged into zero answers."""
    corpus = tmp_path / "marking-schemes"
    corpus.mkdir()
    _corrupt_pdf(corpus / "corrupt_one_MS.pdf")
    _corrupt_pdf(corpus / "corrupt_two_MS.pdf")

    cfg = Config(data_root=tmp_path / "data")
    result = build_answer_keys(cfg, [corpus])

    assert result["failed"] == 2, "both corrupt files must be counted as failed"
    assert result["files"] == 2
    assert result["written"] == 0


def test_papers_written_this_run_does_not_collide_with_stats_cumulative_papers(
    tmp_path, monkeypatch
):
    """Found alongside the failure-counting fix, in the same dict literal:
    the returned dict used to have `"papers": papers` (this run's variant
    count) immediately overwritten by `**stats`'s own `"papers"` key (the
    store's cumulative distinct-paper-code count across every run ever).
    Two runs against the same store, each writing one distinct paper code,
    must report `papers_written == 1` both times while the store-cumulative
    `papers` (from **stats) grows to 2 -- proving the two numbers are no
    longer the same key."""
    real_pdf = tmp_path / "fake_MS.pdf"
    real_pdf.write_bytes(b"not read -- parse_marking_scheme is monkeypatched below")
    corpus = tmp_path / "marking-schemes"
    corpus.mkdir()
    (corpus / "one.pdf").write_bytes(b"stand-in path, content unused")

    cfg = Config(data_root=tmp_path / "data")

    def _fake_parse_run_1(path):
        return [PaperKey(paper_code="31/1/1", subject="Science", grade="X",
                         answers={1: KeyedAnswer(q_no=1, correct_option="A",
                                                 answer_text="A")})]

    monkeypatch.setattr(ak, "parse_marking_scheme", _fake_parse_run_1)
    result_1 = build_answer_keys(cfg, [corpus])
    assert result_1["papers_written"] == 1
    assert result_1["papers"] == 1  # store cumulative, same as this run so far

    def _fake_parse_run_2(path):
        return [PaperKey(paper_code="31/1/2", subject="Science", grade="X",
                         answers={1: KeyedAnswer(q_no=1, correct_option="B",
                                                 answer_text="B")})]

    monkeypatch.setattr(ak, "parse_marking_scheme", _fake_parse_run_2)
    result_2 = build_answer_keys(cfg, [corpus])
    assert result_2["papers_written"] == 1, "this run wrote exactly one paper variant"
    assert result_2["papers"] == 2, "the store now holds two distinct paper codes total"


# ---------------------------------------------------------------- parser fix
# Found live 2026-09-20: 1,258 corpus questions had "code present, no answer
# for q_no" even though the answer letter WAS in the marking-scheme PDF text.
# Two parser gaps caused it:
#   1. _PREAMBLE_END looked only for "SECTION A", so Hindi-medium schemes that
#      label the same boundary "खण्ड - क" never had their examiner-instruction
#      preamble cut -- and any preamble numbered-instruction line could be read
#      as an answer.
#   2. Section A objective answers had only two known layouts ("D / text" and
#      "Sol.\\n(letter) text"). A third real-world layout -- the bare letter on
#      its own line immediately after the question number:
#          2.
#          (c)
#          1
#          1
#      -- matched neither, so every objective question of those schemes was
#      silently dropped. The fix adds _MCQ_PAREN for that layout.
#
# Found the same day: _MCQ_PAREN's first cut was too loose. It matched the
# part label of a value-point question rendered in some "set" PDFs as
#     14.
#     (a)
#     • In a few reptiles, ...
# where the lone (a) is a PART label, not an MCQ choice -- swallowing the value
# points as answer_text and storing a wrong option. A real bare-letter MCQ is
# ALWAYS followed by a marks-only line (1 / 1 1 / ½); requiring that line pins
# the letter to the marks column and rejects the value-point layout.
#
# The tests below pin the regressions so a future edit cannot re-lose the
# Hindi-medium science schemes (e.g. 31/2/1, which gained its missing q 2-20).


def test_preamble_end_also_cuts_hindi_section_a_marker():
    body = (
        "INSTRUCTIONS\n"
        "1. You are aware that evaluation strategy is mentioned in the "
        "question paper.\n"
        "2. Check the section for which the answer is expected.\n"
        "खण्ड - क\n"
        "1.\n"
        "(b)\n"
    )
    match = _PREAMBLE_END.search(body)
    assert match is not None, ("Hindi-medium schemes label Section A खण्ड-क; "
                               "the preamble-cut regex must find it")
    answers_body = body[match.start():]
    assert "You are aware" not in answers_body, ("the examiner preamble must be "
                                                 "cut, not treated as answers")


def test_mcq_paren_parses_bare_letter_section_a_layout():
    body = _PREAMBLE_END.sub("", """INSTRUCTIONS
1. preamble instruction line with prose after the number
खण्ड - क
1.
(b)
1
1
2.
(c)
1
1
3.
(a)
1
1
4.
(d)
1 1
5.
(a)
    1
    1
खण्ड - ख
21.
(a) • this is a value point, not an objective answer
""")
    answers = _parse_objective(body)
    assert {q: a.correct_option for q, a in answers.items()} == {
        1: "B", 2: "C", 3: "A", 4: "D", 5: "A",
    }, "bare-letter Section A answers must be recovered for q 1-20"
    for a in answers.values():
        assert a.answer_text == "", ("the marks column must not leak into "
                                     "answer_text for the bare-letter layout")
    assert 21 not in answers, "value-point blocks must stay out of Section A"


def test_mcq_paren_does_not_read_prose_instruction_as_answer():
    """The preamble instruction '2. Check the section...' is prose on the same
    line, so it must not be misread as letter-alone Section A answer."""
    body = _PREAMBLE_END.sub("", """1. You are aware that evaluation strategy is
     mentioned in the question paper.
2. Check the section for which the answer is expected.
खण्ड - क
1.
(b)
1
1
""")
    answers = _parse_objective(body)
    assert answers == {1: ak.KeyedAnswer(q_no=1, correct_option="B",
                                         answer_text="", marks=1.0)}


def test_mcq_paren_does_not_read_valuepoint_part_label_as_mcq_option():
    """The English 'set' PDF (X_086_Set-.2...) renders some Section A
    questions as value-point blocks whose parts start with a lone (a)/(b) on
    their own line, e.g. q14 of 31/2/1:
        14.
        (a)
        • In a few reptiles, ...
    A real bare-letter MCQ always has a marks-only line right after the letter,
    so _MCQ_PAREN must reject this layout instead of storing option (a) and
    swallowing the value points as answer_text (true answer: B)."""
    body = _PREAMBLE_END.sub("", """INSTRUCTIONS
1. preamble instruction line
खण्ड - क
13.
(d)
1
1
14.
(a)
• In a few reptiles, the temperature at which fertilised eggs
  are kept determine whether the animal developing from the
  eggs will be male or female.
• In snails, individuals can change sex. (or any other
  suitable example)
(b) Male sex chromosome Female sex chromosome
    Male has a mismatched pair i.e, ‘XY’ chromosomes.
    Female has a perfect pair i.e. ‘XX’ chromosomes.
2
2
15.
(b)
1
1
करणें
""")
    answers = _parse_objective(body)
    assert answers[13].correct_option == "D"
    assert answers[15].correct_option == "B"
    assert 14 not in answers, ("a value-point part label (a) is not an MCQ "
                               "option and must not be stored as one")
    for a in answers.values():
        assert a.answer_text == ""
