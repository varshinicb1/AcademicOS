"""The product is AcademicOS. It used to also be AssessmentOS in several real,
user-facing places -- found 2026-09-18: every generated exam paper's PDF
metadata (`author=`), every mailed paper's footer text, every corrected
answer-sheet PDF, every progress-report PDF, and the default `generated_by`
field on GeneratedPaper's metadata all printed "AssessmentOS" while the
product markets itself everywhere else (README, PRD, the app itself) as
"AcademicOS". Not a typo in one place -- the same wrong name baked into
seven real source files, so a real teacher's real printed exam paper carried
the wrong brand.

This scans the actual source tree rather than pinning the seven fixed call
sites individually, so a new occurrence anywhere is caught the same way the
original ones would have been, had this test existed first.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SRC = ROOT / "src" / "academicos"


def test_no_source_file_says_assessmentos():
    offenders = []
    for path in SRC.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "AssessmentOS" in text:
            offenders.append(str(path.relative_to(ROOT)))
    assert not offenders, (
        f"found the old product name 'AssessmentOS' in: {offenders} -- "
        "the product is AcademicOS everywhere, including generated PDFs, "
        "mail text, and schema defaults"
    )
