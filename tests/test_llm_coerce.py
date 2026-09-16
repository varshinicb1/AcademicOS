"""Strict coercion of model output (OWASP LLM10, Improper Output Handling).

The first test in this file is the regression for the bug that motivated the
module: `bool("false") is True`, which silently inverted the critic's retrieval
decision. It is written first deliberately -- if it ever passes again by
accident, the reason this file exists is gone.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.llm.coerce import as_bool, as_choice, as_float, as_int, as_text


# --------------------------------------------------------------------------- #
# as_bool
# --------------------------------------------------------------------------- #

def test_the_bug_that_motivated_this_module():
    """`bool("false")` is True in Python. This is why we do not use `bool`."""
    assert bool("false") is True          # the footgun
    assert as_bool("false", True) is False  # the fix


@pytest.mark.parametrize("value", ["false", "FALSE", " False ", "no", "n", "0", "off", "none", "null", ""])
def test_false_literals(value):
    assert as_bool(value, True) is False


@pytest.mark.parametrize("value", ["true", "TRUE", " true ", "yes", "y", "1", "on", "t"])
def test_true_literals(value):
    assert as_bool(value, False) is True


@pytest.mark.parametrize("value,expected", [(True, True), (False, False)])
def test_real_booleans_round_trip(value, expected):
    assert as_bool(value, not expected) is expected


@pytest.mark.parametrize("value,expected", [(0, False), (1, True), (0.0, False), (2.5, True)])
def test_numbers_use_arithmetic_truth(value, expected):
    assert as_bool(value, not expected) is expected


@pytest.mark.parametrize("value", ["maybe", "unknown", None, [], {}, "2"])
def test_unknown_values_fall_back_and_are_reported(value):
    problems: list[str] = []
    assert as_bool(value, False, problems=problems, field="retrieve") is False
    assert problems, f"{value!r} should have been reported"
    assert "retrieve" in problems[0]


def test_clean_input_records_no_problems():
    problems: list[str] = []
    as_bool("yes", False, problems=problems)
    as_int(4, 0, problems=problems)
    as_choice("full", ("full", "partial"), "none", problems=problems)
    assert problems == []


def test_problems_is_optional():
    """Callers that do not care must not have to pass a list."""
    assert as_bool("garbage", True) is True


# --------------------------------------------------------------------------- #
# as_int
# --------------------------------------------------------------------------- #

def test_int_from_string_and_integral_float():
    assert as_int("4", 0) == 4
    assert as_int(4.0, 0) == 4


def test_non_integral_float_is_rejected_not_rounded():
    """4.7 is a different thing than the model meant; refuse rather than guess."""
    problems: list[str] = []
    assert as_int(4.7, 3, problems=problems) == 3
    assert problems


@pytest.mark.parametrize("value", ["not-an-int", "3 things", "", None, [1], {}])
def test_non_integers_fall_back(value):
    assert as_int(value, 7) == 7


def test_bool_is_not_accepted_as_an_int():
    """`True` is an `int` subclass in Python; silently reading it as 1 hides a type error."""
    problems: list[str] = []
    assert as_int(True, 5, problems=problems) == 5
    assert problems


def test_int_is_clamped_and_reported():
    problems: list[str] = []
    assert as_int(0, 3, lo=1, hi=5, problems=problems) == 1
    assert as_int(99, 3, lo=1, hi=5, problems=problems) == 5
    assert len(problems) == 2


# --------------------------------------------------------------------------- #
# as_float
# --------------------------------------------------------------------------- #

def test_float_from_string():
    assert as_float("0.75", 0.0) == pytest.approx(0.75)


@pytest.mark.parametrize("value", ["nan", float("nan")])
def test_nan_is_rejected(value):
    """A NaN reaching a score comparison makes every comparison false.

    That reads downstream as "no path was best" rather than as a parse failure,
    which is the worst possible presentation of a bad value.
    """
    problems: list[str] = []
    result = as_float(value, 0.5, problems=problems)
    assert result == 0.5
    assert not math.isnan(result)
    assert problems


@pytest.mark.parametrize("value", [float("inf"), float("-inf"), "inf"])
def test_infinity_is_rejected(value):
    assert as_float(value, 0.5) == 0.5


def test_float_is_clamped():
    assert as_float(2.0, 0.0, lo=0.0, hi=1.0) == 1.0
    assert as_float(-1.0, 0.0, lo=0.0, hi=1.0) == 0.0


# --------------------------------------------------------------------------- #
# as_choice
# --------------------------------------------------------------------------- #

def test_choice_accepts_allowlisted_values_case_insensitively():
    allowed = ("full", "partial", "none")
    assert as_choice("full", allowed, "none") == "full"
    assert as_choice("FULL", allowed, "none") == "full"
    assert as_choice(" Partial ", allowed, "none") == "partial"


@pytest.mark.parametrize("value", ["mostly supported", "partially", "", None, 7, []])
def test_choice_rejects_anything_outside_the_allowlist(value):
    """An invented label must not be bucketed into a nearby real one.

    "mostly supported" is not "partial"; guessing that it is turns a model's
    uncertainty into our false precision.
    """
    problems: list[str] = []
    assert as_choice(value, ("full", "partial", "none"), "none", problems=problems) == "none"
    assert problems


# --------------------------------------------------------------------------- #
# as_text
# --------------------------------------------------------------------------- #

def test_text_passthrough():
    assert as_text("hello") == "hello"


def test_text_from_scalars():
    assert as_text(42) == "42"
    assert as_text(True) == "True"


def test_text_null_and_containers_fall_back():
    assert as_text(None, "fallback") == "fallback"
    assert as_text({}, "fallback") == "fallback"
    assert as_text([], "fallback") == "fallback"


def test_truncation_is_reported():
    """A truncated answer is materially different from a short one."""
    problems: list[str] = []
    assert as_text("abcdefghij", max_chars=4, problems=problems) == "abcd"
    assert problems and "truncated" in problems[0]


def test_no_truncation_records_nothing():
    problems: list[str] = []
    assert as_text("abc", max_chars=10, problems=problems) == "abc"
    assert problems == []
