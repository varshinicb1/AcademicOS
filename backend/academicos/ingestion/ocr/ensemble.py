"""Ensemble OCR - Auto-selects best engine per page."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from PIL import Image

from .paddleocr_engine import PaddleOCREngine, OCRResult as PaddleResult
from .tesseract_engine import TesseractEngine, TesseractResult

logger = logging.getLogger(__name__)


class OCREngineType(str, Enum):
    PADDLEOCR = "paddleocr"
    TESSERACT = "tesseract"
    NATIVE = "native"  # pdfplumber/PyMuPDF text extraction


@dataclass
class UnifiedOCRResult:
    """Unified result from any OCR engine."""
    text: str
    confidence: float
    bbox: list[list[float]]
    engine: OCREngineType
    word_count: int = 0
    char_count: int = 0
    
    @classmethod
    def from_paddle(cls, r: PaddleResult) -> 'UnifiedOCRResult':
        return cls(
            text=r.text,
            confidence=r.confidence,
            bbox=r.bbox,
            engine=OCREngineType.PADDLEOCR,
            word_count=len(r.text.split()),
            char_count=len(r.text)
        )
    
    @classmethod
    def from_tesseract(cls, r: TesseractResult) -> 'UnifiedOCRResult':
        return cls(
            text=r.text,
            confidence=r.confidence,
            bbox=r.bbox,
            engine=OCREngineType.TESSERACT,
            word_count=len(r.text.split()),
            char_count=len(r.text)
        )
    
    @classmethod
    def from_native(cls, text: str, page_bbox: list[list[float]], 
                    confidence: float = 0.95) -> 'UnifiedOCRResult':
        return cls(
            text=text,
            confidence=confidence,
            bbox=page_bbox,
            engine=OCREngineType.NATIVE,
            word_count=len(text.split()),
            char_count=len(text)
        )


class EnsembleOCR:
    """Auto-selects best OCR engine per page based on content type."""
    
    def __init__(self, 
                 paddleocr_lang: str = "en",
                 tesseract_lang: str = "eng+hin",
                 use_gpu: bool = False,
                 force_ocr_min_chars: int = 50,
                 confidence_threshold: float = 0.6):
        
        self.force_ocr_min_chars = force_ocr_min_chars
        self.confidence_threshold = confidence_threshold
        
        # Initialize engines lazily
        self._paddleocr: Optional[PaddleOCREngine] = None
        self._tesseract: Optional[TesseractEngine] = None
        self._paddleocr_lang = paddleocr_lang
        self._tesseract_lang = tesseract_lang
        self._use_gpu = use_gpu
        
        # Stats
        self.stats = {
            "native": 0,
            "paddleocr": 0,
            "tesseract": 0,
            "failed": 0
        }
    
    @property
    def paddleocr(self) -> PaddleOCREngine:
        if self._paddleocr is None:
            self._paddleocr = PaddleOCREngine(
                lang=self._paddleocr_lang, 
                use_gpu=self._use_gpu
            )
        return self._paddleocr
    
    @property
    def tesseract(self) -> Optional[TesseractEngine]:
        if self._tesseract is None:
            try:
                self._tesseract = TesseractEngine(lang=self._tesseract_lang)
            except Exception as e:
                logger.warning(f"Tesseract unavailable: {e}")
                self._tesseract = None
        return self._tesseract
    
    def extract_native_text(self, pdf_path: Path, page_num: int) -> tuple[str, list[list[float]]]:
        """Extract native text from PDF page using pdfplumber + PyMuPDF."""
        text_parts = []
        page_bbox = [[0, 0], [0, 0], [0, 0], [0, 0]]
        
        # Try pdfplumber first (better structure)
        try:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                if page_num < len(pdf.pages):
                    page = pdf.pages[page_num]
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                    page_bbox = [[0, 0], [page.width, 0], [page.width, page.height], [0, page.height]]
        except Exception as e:
            logger.debug(f"pdfplumber failed: {e}")
        
        # Fallback to PyMuPDF
        if not text_parts:
            try:
                import fitz
                doc = fitz.open(pdf_path)
                page = doc[page_num]
                text = page.get_text("text")
                if text:
                    text_parts.append(text)
                rect = page.rect
                page_bbox = [[0, 0], [rect.width, 0], [rect.width, rect.height], [0, rect.height]]
                doc.close()
            except Exception as e:
                logger.debug(f"PyMuPDF failed: {e}")
        
        full_text = "\n".join(text_parts)
        return full_text, page_bbox
    
    def should_ocr(self, native_text: str) -> bool:
        """Decide if OCR is needed based on native text quality."""
        if not native_text or not native_text.strip():
            return True
        if len(native_text.strip()) < self.force_ocr_min_chars:
            return True
        # Check for garbled text (too many special chars)
        special_ratio = sum(1 for c in native_text if not c.isalnum() and c not in " \n\t.,;:!?()-") / max(len(native_text), 1)
        if special_ratio > 0.3:
            return True
        return False
    
    def process_page(self, pdf_path: Path, page_num: int) -> UnifiedOCRResult:
        """Process a single page with best available method."""
        
        # 1. Try native text extraction first
        native_text, page_bbox = self.extract_native_text(pdf_path, page_num)
        
        if not self.should_ocr(native_text):
            self.stats["native"] += 1
            return UnifiedOCRResult.from_native(native_text, page_bbox)
        
        # 2. Need OCR - try PaddleOCR first (best for mixed scripts)
        if self.paddleocr.is_available():
            try:
                paddle_results = self.paddleocr.ocr_pdf_page(pdf_path, page_num)
                if paddle_results:
                    # Combine all text blocks
                    combined_text = "\n".join(r.text for r in paddle_results)
                    avg_conf = sum(r.confidence for r in paddle_results) / len(paddle_results)
                    
                    if avg_conf >= self.confidence_threshold:
                        self.stats["paddleocr"] += 1
                        return UnifiedOCRResult(
                            text=combined_text,
                            confidence=avg_conf,
                            bbox=paddle_results[0].bbox if paddle_results else page_bbox,
                            engine=OCREngineType.PADDLEOCR,
                            word_count=len(combined_text.split()),
                            char_count=len(combined_text)
                        )
            except Exception as e:
                logger.warning(f"PaddleOCR failed for page {page_num}: {e}")
        
        # 3. Fallback to Tesseract
        if self.tesseract and self.tesseract.is_available():
            try:
                tesseract_results = self.tesseract.ocr_pdf_page(pdf_path, page_num)
                if tesseract_results:
                    combined_text = "\n".join(r.text for r in tesseract_results)
                    avg_conf = sum(r.confidence for r in tesseract_results) / len(tesseract_results)
                    
                    if avg_conf >= self.confidence_threshold * 0.8:  # Lower threshold for fallback
                        self.stats["tesseract"] += 1
                        return UnifiedOCRResult(
                            text=combined_text,
                            confidence=avg_conf,
                            bbox=tesseract_results[0].bbox if tesseract_results else page_bbox,
                            engine=OCREngineType.TESSERACT,
                            word_count=len(combined_text.split()),
                            char_count=len(combined_text)
                        )
            except Exception as e:
                logger.warning(f"Tesseract failed for page {page_num}: {e}")
        
        # 4. Return native text even if poor (better than nothing)
        self.stats["failed"] += 1
        logger.warning(f"All OCR failed for page {page_num}, returning native text")
        return UnifiedOCRResult.from_native(
            native_text if native_text else "[OCR_FAILED]", 
            page_bbox, 
            confidence=0.3
        )
    
    def get_stats(self) -> dict:
        total = sum(self.stats.values())
        if total == 0:
            return self.stats
        return {
            **self.stats,
            "native_pct": round(self.stats["native"] / total * 100, 1),
            "paddleocr_pct": round(self.stats["paddleocr"] / total * 100, 1),
            "tesseract_pct": round(self.stats["tesseract"] / total * 100, 1),
            "failed_pct": round(self.stats["failed"] / total * 100, 1),
        }


def get_ensemble_ocr(**kwargs) -> EnsembleOCR:
    """Factory for ensemble OCR."""
    return EnsembleOCR(**kwargs)