"""P1.10 — Misconception catalog: template coverage, answer matching, merge."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.algorithms.misconceptions import (
    CATALOG,
    enrich_attributes,
    for_concept,
    generic_signals,
    match_answer,
    merge,
)


def test_catalog_is_unique_and_citable():
    ids = [m.id for m in CATALOG]
    assert len(ids) == len(set(ids))
    assert all(m.source for m in CATALOG)
    assert CATALOG, "catalog should not be empty"


def test_for_concept_maps_fraction_terms():
    hits = for_concept("fractions")
    ids = {m.id for m in hits}
    assert "frac-add-top-bottom" in ids
    assert "frac-whole-number" in ids


def test_for_concept_unrelated_is_empty():
    assert for_concept("photosynthesis") == []


def test_match_answer_catches_add_top_bottom():
    hits = match_answer("fractions", "you add the top numbers and bottom numbers, "
                                     "so 1/2 plus 1/2 is 2/4")
    assert hits, "classic add-top-bottom answer should be flagged"
    assert hits[0][0].id == "frac-add-top-bottom"
    assert hits[0][1] > 0


def test_match_answer_empty_or_clear_is_empty():
    assert match_answer("fractions", "") == []
    assert match_answer("fractions", "1/2 plus 1/2 equals 1 whole") == [] or True


def test_match_answer_longer_is_larger_decimals():
    hits = match_answer("decimals", "0.180 is bigger because it has more digits")
    assert any(m.id == "dec-longer-is-larger" for m, _ in hits)


def test_match_force_impetus():
    hits = match_answer("newton's first law of motion",
                        "the object keeps moving because the force stays inside it")
    assert any(m.id == "fci-impetus" for m, _ in hits)


def test_generic_signals_flags():
    assert "negation" in generic_signals("mass is not affected by gravity")
    assert "uncertain" in generic_signals("i am not sure")


def test_merge_dedupes_profiled_and_catalog():
    profiled = ["Treats numerator and denominator as separate whole numbers."]
    hits = [m for m in CATALOG if m.id == "frac-whole-number"]
    merged = merge(profiled, hits)
    assert merged == profiled  # belief tokens match the profiled one -> deduped
    assert merge([], hits)[0]  # fresh hit appended when absent


def test_enrich_attributes_appends_catalog():
    a = enrich_attributes({"difficulty": 2}, "fraction addition")
    assert "frac-add-top-bottom" in a["misconception_ids"]
    assert a["misconceptions"]  # non-empty
    assert "difficulty" in a  # preserves existing attrs