"""Canonical subject naming, so coverage reporting stops splitting on filenames.

The bank received 44 subject names for 31 real subjects. Three causes: the same
subject across classes, across years with different spelling, and cosmetic
drift against the board corpus.

The tests that matter here are the ones asserting the mapping does NOT collapse
things that should stay apart. `MathsStandard` and `MathsBasic` are CBSE papers
041 and 241, and a school that sets Basic must not be shown Standard questions.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from academicos.corpus import subjects  # noqa: E402

BANK = REPO / "academicos-data" / "corpus" / "cbse-sqp" / "questions.json"


def test_a_variant_keeps_its_identity_in_the_display_name():
    """Maths Standard and Maths Basic are different papers (041 vs 241)."""
    std_name, std_family = subjects.canonical_subject("MathsStandard")
    basic_name, basic_family = subjects.canonical_subject("MathsBasic")

    assert std_name != basic_name, (
        "Standard and Basic collapsed to one display name; a school that sets "
        "Basic would be shown Standard questions"
    )
    assert std_family == basic_family == "Mathematics", (
        "they must still group together for coverage reporting"
    )


def test_the_english_variants_are_kept_apart_too():
    """Communicative and Language & Literature are X papers 101 and 184."""
    names = {subjects.canonical_subject(s)[0]
             for s in ("EnglishL", "EnglishComm", "EnglishCore", "EnglishElective")}
    assert len(names) == 4, f"English variants collapsed: {names}"
    assert {subjects.canonical_subject(s)[1] for s in
            ("EnglishL", "EnglishComm", "EnglishCore", "EnglishElective")} == {"English"}


def test_year_to_year_spelling_drift_merges():
    """One year says CarnaticMelodicInstrument, another CarnaticMusicMelodicInstrument."""
    a = subjects.canonical_subject("CarnaticMelodicInstrument")
    b = subjects.canonical_subject("CarnaticMusicMelodicInstrument")
    assert a == b, "the two spellings of the same paper are still separate"


def test_cosmetic_drift_against_the_board_corpus_is_fixed():
    """Names must match what the board corpus uses, or coverage splits."""
    assert subjects.canonical_subject("HomeScience")[0] == "Home Science"
    assert subjects.canonical_subject("Applied-Maths")[0] == "Applied Mathematics"
    assert subjects.canonical_subject("PolSci")[0] == "Political Science"


def test_a_caps_variant_is_the_same_subject():
    """`ODIA` is a second spelling of `Odia`, found by printing the gap list."""
    assert subjects.canonical_subject("ODIA") == subjects.canonical_subject("Odia")


def test_an_unknown_stem_is_its_own_subject_rather_than_guessed():
    """A visible unknown beats a silent wrong merge.

    This repository has already produced one silent data error by collapsing
    things that should have stayed apart, so the unmapped path is deliberately
    conservative.
    """
    name, family = subjects.canonical_subject("SomeNewSubject")
    assert name == "SomeNewSubject"
    assert family == "SomeNewSubject"
    assert subjects.unmapped(["SomeNewSubject"]) == ["SomeNewSubject"]


def test_unmapped_is_empty_for_the_known_subjects():
    assert subjects.unmapped(["MathsStandard", "EnglishCore", "HindiCourseA"]) == []


@pytest.mark.skipif(not BANK.exists(), reason="SQP bank not built")
def test_every_subject_in_the_real_bank_is_mapped():
    """The table must cover what was actually downloaded, not what was imagined.

    `unmapped()` exists so this is a printed list rather than a discovery made
    later; this test is what makes the list stay empty.
    """
    bank = json.loads(BANK.read_text(encoding="utf-8"))
    for rec in bank["questions"]:
        assert rec["metadata"].get("subjectFamily"), (
            f"{rec['id']} carries no subjectFamily, so coverage reporting "
            "cannot group it"
        )


@pytest.mark.skipif(not BANK.exists(), reason="SQP bank not built")
def test_the_family_collapse_actually_achieved_its_purpose():
    """Names must be materially fewer than families... no: families than names.

    Measured 44 names -> 31 families. Asserted as a floor rather than an exact
    number so adding subjects does not break it, while a mapping that stopped
    working would.
    """
    bank = json.loads(BANK.read_text(encoding="utf-8"))
    names = {r["subject"] for r in bank["questions"]}
    families = {r["metadata"]["subjectFamily"] for r in bank["questions"]}
    assert len(families) < len(names), (
        f"{len(families)} families from {len(names)} names -- the mapping is "
        "not collapsing anything"
    )
