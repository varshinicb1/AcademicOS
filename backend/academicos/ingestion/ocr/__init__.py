"""OCR Module - Unified interface for all OCR engines."""
from __future__ import annotations

from .ensemble import EnsembleOCR, UnifiedOCRResult, OCREngineType, get_ensemble_ocr
from .paddleocr_engine import PaddleOCREngine, OCRResult as PaddleResult, get_paddleocr_engine
from .tesseract_engine import TesseractEngine, TesseractResult, get_tesseract_engine
from .preprocess import preprocess_for_ocr, render_pdf_page_to_image, crop_to_content

__all__ = [
    "EnsembleOCR",
    "UnifiedOCRResult",
    "OCREngineType",
    "get_ensemble_ocr",
    "PaddleOCREngine",
    "PaddleResult",
    "get_paddleocr_engine",
    "TesseractEngine",
    "TesseractResult",
    "get_tesseract_engine",
    "preprocess_for_ocr",
    "render_pdf_page_to_image",
    "crop_to_content",
]