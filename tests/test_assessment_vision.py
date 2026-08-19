"""Audit regression tests for assessment/vision.ocr_page (C1).

The OCR retry loop must distinguish a *capture failure* (every Sarvam Vision
call raises) from a *genuinely blank page* (calls succeed but recover no
text). A capture failure must propagate as VisionError so the callers in
scan.py / mobile_scan.py record "OCR failed" and the ocr_failed_pages
detector routes the page to review — otherwise a failed transcription is
silently treated as a confident blank. Both callers already catch Exception,
so re-raising is safe. A/B: the raise path failed on the old code (which
returned an empty PageOCR).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.assessment import vision  # noqa: E402
from academicos.assessment.vision import VisionError, ocr_page  # noqa: E402


def test_ocr_page_reraises_when_every_pass_fails(tmp_path, monkeypatch):
    def boom(*args, **kwargs):
        raise VisionError("vision job timed out")

    monkeypatch.setattr(vision, "extract", boom)
    with pytest.raises(VisionError):
        ocr_page(tmp_path / "page.png", 1, workdir=tmp_path / "out",
                 crop_furniture=False)


def test_ocr_page_returns_blank_when_calls_succeed_without_text(tmp_path, monkeypatch):
    monkeypatch.setattr(vision, "extract", lambda *a, **k: "")
    page = ocr_page(tmp_path / "page.png", 1, workdir=tmp_path / "out",
                    crop_furniture=False)
    assert page.text == ""
    assert page.warnings == ["no text recovered from this page"]


def test_ocr_page_votes_across_successful_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(vision, "extract", lambda *a, **k: "Q.1) x = 2")
    page = ocr_page(tmp_path / "page.png", 1, workdir=tmp_path / "out",
                    crop_furniture=False)
    assert page.text == "Q.1) x = 2"
