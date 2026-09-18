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

from academicos.assessment.answer_key import build_answer_keys, parse_marking_scheme
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
