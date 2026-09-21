"""The one grade parser. See src/academicos/assessment/grades.py."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from academicos.assessment import grades  # noqa: E402


@pytest.mark.parametrize("raw,expected", [
    (6, 6), (7, 7), (10, 10), (12, 12),
    ("6", 6), ("9", 9), ("12", 12),
    ("VI", 6), ("vii", 7), ("VIII", 8), ("IX", 9), ("X", 10), ("XII", 12),
    ("7th", 7), ("1st", 1), ("2nd", 2), ("3rd", 3), ("10th", 10),
    ("Class 7", 7), ("Grade IX", 9), (" 8 ", 8),
])
def test_to_int_reads_every_shape_the_code_uses(raw, expected):
    assert grades.to_int(raw) == expected


@pytest.mark.parametrize("raw", [0, 13, -1, "", "XIII", "abc", None, True, 7.5])
def test_to_int_refuses_what_is_not_a_school_grade(raw):
    assert grades.to_int(raw) is None


@pytest.mark.parametrize("raw,expected", [
    (6, "VI"), (7, "VII"), (8, "VIII"), (9, "IX"), (10, "X"), (11, "XI"), (12, "XII"),
    ("9", "IX"), ("IX", "IX"),
])
def test_to_roman(raw, expected):
    assert grades.to_roman(raw) == expected


def test_to_roman_raises_rather_than_defaulting_to_ten():
    """The bug this replaces: `romans.get(grade, "X")` turned 6 and 7 into 10."""
    with pytest.raises(ValueError):
        grades.to_roman(13)


@pytest.mark.parametrize("a,b,expected", [
    ("IX", "9", True), ("9", "IX", True), ("VIII", 8, True), ("X", "10th", True),
    ("X", "9", False), ("VI", "VII", False), ("X", "junk", False), ("junk", "junk", False),
])
def test_matches_compares_as_integers(a, b, expected):
    assert grades.matches(a, b) is expected
