"""Answer-quality metrics tests (ported from RAG-Enhanced-NCERT-Tutor, MIT)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.eval.metrics import (bleu1, exact_match, rouge_l, token_f1)


def test_token_f1_identical_is_one():
    assert token_f1("fractions have numerators and denominators",
                    "fractions have numerators and denominators") == 1.0


def test_token_f1_no_overlap_is_zero():
    assert token_f1("perimeter of a square", "photosynthesis in plants") == 0.0


def test_token_f1_partial_overlap():
    f1 = token_f1("add fractions with the same denominator",
                  "add fractions with different denominators")
    assert 0.0 < f1 < 1.0


def test_token_f1_insensitive_to_case():
    assert token_f1("Water vapour", "water VAPOUR") == 1.0


def test_exact_match_normalizes_whitespace_and_case():
    assert exact_match("  What   is Perimeter ", "what is perimeter") == 1.0
    assert exact_match("perimeter", "area") == 0.0


def test_rouge_l_identical_is_one():
    assert rouge_l("a parallelogram has opposite sides parallel",
                   "a parallelogram has opposite sides parallel") == 1.0


def test_rouge_l_subsequence_preserves_order():
    r = rouge_l("first second third fourth", "first third fourth")
    assert r == pytest.approx(2 * 0.75 / 1.75)  # P=1.0, R=0.75


def test_rouge_l_no_common_tokens_is_zero():
    assert rouge_l("alpha beta", "gamma delta") == 0.0


def test_bleu1_identical_is_one():
    assert bleu1("water vapour is a gas", "water vapour is a gas") == 1.0


def test_bleu1_penalizes_short_candidates():
    short = bleu1("perimeter is the total length of the boundary",
                  "perimeter length")
    long = bleu1("perimeter is the total length of the boundary",
                 "perimeter is the total length of the boundary")
    assert 0.0 < short < long


def test_empty_candidates():
    assert bleu1("some reference", "") == 0.0
    assert token_f1("", "") == 1.0
    assert rouge_l("", "anything") == 0.0
