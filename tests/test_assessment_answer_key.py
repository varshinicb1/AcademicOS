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
    KeyedAnswer, PaperKey, build_answer_keys, parse_marking_scheme,
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
