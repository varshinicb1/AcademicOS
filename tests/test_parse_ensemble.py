"""Hermetic tests for the parse layer.

Covers EnsembleParser selection/fusion with stubbed providers, the real
PdfTextParser on tiny born-digital PDFs, and TesseractParser /
UnlimitedOcrParser with mocked OCR/VLM dependencies. No network, no real
tesseract, no real VLM.
"""
import sys
import types
from pathlib import Path

import pytest
import fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.models.document import Page, ParseResult, ParsedDocument
from academicos.models.enums import BlockKind, DocType, ExtractionMethod, PageKind
from academicos.parse.base import ParserProvider
from academicos.parse.ensemble import EnsembleParser
from academicos.parse.pdftext import PdfTextParser
from academicos.parse.pytesseract import TesseractParser
from academicos.parse.unlimited import UnlimitedOcrParser


def _pdf(tmp_path: Path, name: str, lines: list[str]) -> Path:
    doc = fitz.open()
    page = doc.new_page()
    y = 72
    for line in lines:
        page.insert_text((72, y), line, fontsize=11)
        y += 18
    out = tmp_path / name
    doc.save(out)
    doc.close()
    return out


def _page(page_no: int, text: str, quality: float = 1.0) -> Page:
    return Page(page_no=page_no, kind=PageKind.TEXT, text=text, quality=quality)


def _res(method: str, pages: list[Page], confidence: float) -> ParseResult:
    return ParseResult(document_id="doc1", method=method, pages=pages, confidence=confidence)


class _Stub(ParserProvider):
    def __init__(self, result: ParseResult):
        self._result = result

    def parse(self, document_path, document_id, max_pages=500):
        return self._result


class _Raises(ParserProvider):
    def parse(self, document_path, document_id, max_pages=500):
        raise RuntimeError("boom")


# --------------------------------------------------------------------------- #
# Ensemble selection & fusion
# --------------------------------------------------------------------------- #

def test_ensemble_scanned_pdf_prefers_ocr_over_empty_native():
    ep = EnsembleParser()
    ep.providers = {
        # native returns full pages of empty text: text yield 0 -> score 0
        "pdf_native": _Stub(_res("pdf_native", [_page(1, "", 0.9)], 0.9)),
        "unlimited_ocr": _Stub(_res("unlimited_ocr",
                                     [_page(1, "O" * 80, 1.0)], 0.9)),
    }
    doc = ep.parse(Path("x.pdf"), "doc1", DocType.QUESTION_PAPER)
    assert doc.metadata["winner"] == "unlimited_ocr"
    assert doc.pages[0].text == "O" * 80
    assert doc.provenance[0].method == ExtractionMethod.UNLIMITED_OCR
    assert doc.provenance[0].confidence.score == 0.9


def test_ensemble_born_digital_prefers_native():
    ep = EnsembleParser()
    native_pages = [_page(1, "A" * 100, 1.0), _page(2, "B" * 100, 1.0)]
    ep.providers = {
        "pdf_native": _Stub(_res("pdf_native", native_pages, 0.9)),
        "unlimited_ocr": _Stub(_res("unlimited_ocr", [_page(1, "C" * 100, 1.0)],
                                    0.5)),
    }
    doc = ep.parse(Path("x.pdf"), "doc1", DocType.QUESTION_PAPER)
    assert doc.metadata["winner"] == "pdf_native"
    assert [p.text for p in doc.pages] == ["A" * 100, "B" * 100]
    assert doc.provenance[0].method == ExtractionMethod.PDF_NATIVE


def test_ensemble_per_page_fusion_replaces_low_quality_native_page():
    ep = EnsembleParser()
    # native wins overall (higher confidence) but page 1 is low quality...
    ep.providers = {
        "pdf_native": _Stub(_res("pdf_native",
                                 [_page(1, "A" * 100, 0.4), _page(2, "B" * 100, 1.0)],
                                 0.9)),
        "unlimited_ocr": _Stub(_res("unlimited_ocr",
                                     [_page(1, "C" * 100, 1.0), _page(2, "D" * 100, 1.0)],
                                     0.5)),
    }
    doc = ep.parse(Path("x.pdf"), "doc1", DocType.QUESTION_PAPER)
    assert doc.metadata["winner"] == "pdf_native"
    # page 1 was swapped for the OCR version and re-tagged
    assert doc.pages[0].text == "C" * 100
    assert doc.pages[0].metadata.get("provider") == "unlimited_ocr"
    # page 2 kept the native parse untouched
    assert doc.pages[1].text == "B" * 100
    assert doc.pages[1].metadata.get("provider") != "unlimited_ocr"


def test_ensemble_provider_failure_does_not_kill_pipeline():
    ep = EnsembleParser()
    ep.providers = {
        "pdf_native": _Raises(),
        "tesseract": _Stub(_res("tesseract", [_page(1, "T" * 90, 0.75)], 0.7)),
    }
    doc = ep.parse(Path("x.pdf"), "doc1", DocType.QUESTION_PAPER)
    assert doc.metadata["winner"] == "tesseract"
    assert doc.pages[0].text == "T" * 90


def test_ensemble_skips_unknown_priority_names():
    ep = EnsembleParser(priority=["not_a_provider", "pdf_native"])
    ep.providers = {"pdf_native": _Stub(_res("pdf_native", [_page(1, "A" * 90)], 0.9))}
    doc = ep.parse(Path("x.pdf"), "doc1", DocType.QUESTION_PAPER)
    assert doc.metadata["winner"] == "pdf_native"


def test_ensemble_raises_when_no_provider_produces_output():
    ep = EnsembleParser()
    ep.providers = {"pdf_native": _Stub(ParseResult(document_id="d", method="pdf_native"))}
    with pytest.raises(RuntimeError):
        ep.parse(Path("x.pdf"), "doc1", DocType.QUESTION_PAPER)


def test_ensemble_tie_goes_to_first_in_priority():
    ep = EnsembleParser()
    same = [_page(1, "A" * 100, 1.0)]
    ep.providers = {
        "pdf_native": _Stub(_res("pdf_native", same, 0.5)),
        "tesseract": _Stub(_res("tesseract", [_page(1, "B" * 100, 1.0)], 0.5)),
    }
    doc = ep.parse(Path("x.pdf"), "doc1", DocType.QUESTION_PAPER)
    # identical score -> max() keeps the first key in insertion order (priority)
    assert doc.metadata["winner"] == "pdf_native"


def test_ensemble_empty_text_page_gets_empty_placeholder():
    ep = EnsembleParser()
    ep.providers = {
        "pdf_native": _Stub(_res("pdf_native", [_page(1, "A" * 100, 1.0)], 0.9)),
        "unlimited_ocr": _Stub(_res("unlimited_ocr", [_page(1, "B" * 100, 1.0)], 0.8)),
    }
    doc = ep.parse(Path("x.pdf"), "doc1", DocType.QUESTION_PAPER)
    assert len(doc.pages) == 1


def test_page_score_zero_for_empty_result():
    assert EnsembleParser._page_score(ParseResult(document_id="d", method="m")) == 0.0


def test_page_score_zero_when_no_usable_text():
    r = ParseResult(document_id="d", method="m", pages=[_page(1, "short", 0.9)], confidence=0.9)
    assert EnsembleParser._page_score(r) == 0.0


def test_page_score_is_confidence_times_quality_times_yield():
    r = ParseResult(document_id="d", method="m",
                    pages=[_page(1, "x" * 80, 1.0), _page(2, "y" * 80, 0.5)],
                    confidence=0.8)
    assert EnsembleParser._page_score(r) == pytest.approx(0.8 * 0.75 * 1.0)


def test_has_usable_text_threshold():
    ep = EnsembleParser()
    good = ParsedDocument(document_id="d", doc_type=DocType.QUESTION_PAPER, title="t",
                          pages=[_page(1, "x" * 80), _page(2, "y" * 80), _page(3, "z" * 80),
                                 _page(4, ""), _page(5, "")],
                          full_text="")
    assert ep.has_usable_text(good) is True
    bad = ParsedDocument(document_id="d", doc_type=DocType.QUESTION_PAPER, title="t",
                         pages=[_page(1, "x" * 80), _page(2, ""), _page(3, ""), _page(4, "")],
                         full_text="")
    assert ep.has_usable_text(bad) is False


# --------------------------------------------------------------------------- #
# PdfTextParser
# --------------------------------------------------------------------------- #

def test_pdftext_extracts_text_and_blocks(tmp_path):
    path = _pdf(tmp_path, "qp.pdf", ["Section A", "1. What is photosynthesis? (2 marks)"])
    res = PdfTextParser().parse(path, "doc1")
    assert res.pages
    page = res.pages[0]
    assert page.kind == PageKind.TEXT
    assert page.quality == 1.0
    assert "photosynthesis" in page.text
    assert page.blocks
    assert page.blocks[0].kind in (BlockKind.HEADING, BlockKind.PARAGRAPH)
    for b in page.blocks:
        assert b.bbox.x0 <= b.bbox.x1
        assert 0.0 <= b.bbox.x0 <= 1.0
    assert res.confidence == pytest.approx(0.9)


def test_pdftext_marks_blank_page(tmp_path):
    doc = fitz.open()
    doc.new_page()
    out = tmp_path / "blank.pdf"
    doc.save(out)
    doc.close()
    res = PdfTextParser().parse(out, "doc1")
    assert res.pages[0].kind == PageKind.BLANK
    assert res.pages[0].text == ""


def test_pdftext_respects_max_pages(tmp_path):
    doc = fitz.open()
    for _ in range(3):
        page = doc.new_page()
        page.insert_text((72, 72), "Some real content for this page.", fontsize=11)
    out = tmp_path / "multi.pdf"
    doc.save(out)
    doc.close()
    res = PdfTextParser().parse(out, "doc1", max_pages=2)
    assert len(res.pages) == 2


def test_pdftext_kind_classification():
    assert PdfTextParser._kind(1, "an image", 0, []) == BlockKind.FIGURE
    assert PdfTextParser._kind(0, "Photosynthesis", 0, []) == BlockKind.HEADING
    assert PdfTextParser._kind(0, "Section A)", 0, []) == BlockKind.HEADING
    assert PdfTextParser._kind(0, "Short Heading With Spaces", 0, []) == BlockKind.PARAGRAPH
    assert PdfTextParser._kind(0, "This is a long paragraph of body text.", 0, []) == BlockKind.PARAGRAPH


def test_restore_vector_dashes_noop_without_dashes():
    from academicos.parse.pdftext import _restore_vector_dashes
    text = "2y - 5 = 0"
    assert _restore_vector_dashes([], [], text) == text


def test_restore_vector_dashes_splices_minus(tmp_path):
    from academicos.parse import pdftext as pt
    # draw two text words and a thin filled rect between them
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 100), "2y", fontsize=11)
    page.insert_text((120, 100), "5 = 0", fontsize=11)
    shape = page.new_shape()
    shape.draw_rect(fitz.Rect(104, 94, 114, 96))
    shape.finish(color=(0, 0, 0), fill=(0, 0, 0))
    shape.commit()
    out = tmp_path / "dash.pdf"
    doc.save(out)
    doc.close()

    with fitz.open(out) as doc2:
        page2 = doc2[0]
        dashes = pt._drawn_dash_rects(page2)
        words = page2.get_text("words")
        text = page2.get_text("text")
    assert dashes, "drawn dash rect should be detected"
    restored = pt._restore_vector_dashes(dashes, words, text)
    assert "2y -5" in restored


# --------------------------------------------------------------------------- #
# TesseractParser (mocked pytesseract / PIL)
# --------------------------------------------------------------------------- #

def test_tesseract_parser_uses_mocked_ocr(tmp_path):
    path = _pdf(tmp_path, "scan.pdf", ["Scanned page one"])
    fake_ts = types.ModuleType("pytesseract")
    fake_ts.image_to_string = lambda img: "Tesseract OCR extracted this line of text"
    fake_pil = types.ModuleType("PIL")
    fake_img = types.ModuleType("PIL.Image")
    fake_img.frombytes = staticmethod(lambda mode, size, data: object())
    fake_pil.Image = fake_img
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setitem(sys.modules, "pytesseract", fake_ts)
    monkeypatch.setitem(sys.modules, "PIL", fake_pil)
    monkeypatch.setitem(sys.modules, "PIL.Image", fake_img)
    try:
        res = TesseractParser().parse(path, "doc1")
    finally:
        monkeypatch.undo()
    assert res.pages
    page = res.pages[0]
    assert page.kind == PageKind.SCAN
    assert page.text == "Tesseract OCR extracted this line of text"
    assert page.quality == pytest.approx(0.75)
    assert res.confidence == pytest.approx(0.7)


# --------------------------------------------------------------------------- #
# UnlimitedOcrParser (mocked service / cli)
# --------------------------------------------------------------------------- #

class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def _patch_requests(monkeypatch, fake_post):
    """requests is imported inside _call_service; inject a fake module."""
    fake = types.ModuleType("requests")
    fake.post = fake_post
    monkeypatch.setitem(sys.modules, "requests", fake)


def test_unlimited_service_mode_parses(tmp_path, monkeypatch):
    path = _pdf(tmp_path, "scan.pdf", ["Scanned page one"])
    payload = {"markdown": "SERVICE OCR TEXT FOR THE PAGE", "confidence": 0.9, "language": "hi"}
    called = {}

    def fake_post(url, files, timeout):
        called["url"] = url
        called["files"] = files
        return _FakeResponse(payload)

    _patch_requests(monkeypatch, fake_post)
    res = UnlimitedOcrParser(mode="service").parse(path, "doc1")
    assert called["url"].endswith("/parse")
    assert "image/png" in called["files"]["image"][2]
    assert res.pages[0].text == "SERVICE OCR TEXT FOR THE PAGE"
    assert res.pages[0].kind == PageKind.MIXED
    assert res.confidence == pytest.approx(0.9)


def test_unlimited_service_unavailable_returns_warning_pages(tmp_path, monkeypatch):
    path = _pdf(tmp_path, "scan.pdf", ["Scanned page one"])

    def boom(*a, **k):
        raise RuntimeError("connection refused")

    _patch_requests(monkeypatch, boom)
    res = UnlimitedOcrParser(mode="service").parse(path, "doc1")
    assert res.pages[0].quality == 0.0
    assert res.pages[0].kind == PageKind.SCAN
    assert res.confidence == 0.0
    assert any("vlm unavailable" in w for w in res.warnings)


def test_unlimited_cli_mode_parses(tmp_path, monkeypatch):
    import academicos.parse.unlimited as unlim
    script = tmp_path / "checkpoint_generate.py"
    script.write_text("")

    class _Proc:
        returncode = 0
        stdout = '{"markdown": "CLI OCR TEXT", "confidence": 0.95}'

    monkeypatch.setattr(unlim.shutil, "which", lambda name: str(script))
    monkeypatch.setattr(unlim.subprocess, "run", lambda *a, **k: _Proc())
    path = _pdf(tmp_path, "scan.pdf", ["Scanned page one"])
    res = UnlimitedOcrParser(mode="cli").parse(path, "doc1")
    assert res.pages[0].text == "CLI OCR TEXT"
    assert res.confidence == pytest.approx(0.9)


def test_unlimited_cli_script_missing_returns_none(tmp_path, monkeypatch):
    import academicos.parse.unlimited as unlim
    monkeypatch.setattr(unlim.shutil, "which", lambda name: None)
    # also make the vendor fallback path not exist
    monkeypatch.setattr(Path, "exists", lambda self: False)
    assert unlim.UnlimitedOcrParser(mode="cli")._call_cli(b"png") is None


def test_unlimited_service_missing_dependency_catches(tmp_path, monkeypatch):
    path = _pdf(tmp_path, "scan.pdf", ["Scanned page one"])

    def boom(*a, **k):
        raise ImportError("requests not installed")

    _patch_requests(monkeypatch, boom)
    res = UnlimitedOcrParser(mode="service").parse(path, "doc1")
    assert res.pages[0].quality == 0.0
    assert res.confidence == 0.0