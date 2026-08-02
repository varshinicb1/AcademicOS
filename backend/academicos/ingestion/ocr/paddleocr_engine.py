"""PaddleOCR Engine Wrapper."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    text: str
    confidence: float
    bbox: list[list[int]]  # [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
    engine: str = "paddleocr"


class PaddleOCREngine:
    """PaddleOCR wrapper with optimized settings for academic documents."""
    
    _instance: Optional['PaddleOCREngine'] = None
    _ocr = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, lang: str = "en", use_gpu: bool = False, 
                 use_angle_cls: bool = True):
        if self._ocr is not None:
            return
        
        try:
            from paddleocr import PaddleOCR
            self._ocr = PaddleOCR(
                use_angle_cls=use_angle_cls,
                lang=lang,
                use_gpu=use_gpu,
                show_log=False,
                enable_mkldnn=not use_gpu,  # CPU optimization
                cpu_threads=4,
                # Accuracy settings
                det_algorithm="DB",
                rec_algorithm="SVTR_LCNet",
                det_db_thresh=0.3,
                det_db_box_thresh=0.5,
                det_db_unclip_ratio=1.6,
                max_batch_size=10,
                rec_batch_num=6,
            )
            logger.info(f"PaddleOCR initialized: lang={lang}, gpu={use_gpu}")
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")
            self._ocr = None
            raise
    
    def is_available(self) -> bool:
        return self._ocr is not None
    
    def ocr_image(self, image: np.ndarray | Image.Image | Path) -> list[OCRResult]:
        """Run OCR on a single image/page."""
        if self._ocr is None:
            return []
        
        try:
            # Convert to numpy if needed
            if isinstance(image, (str, Path)):
                image = np.array(Image.open(image).convert("RGB"))
            elif isinstance(image, Image.Image):
                image = np.array(image.convert("RGB"))
            
            result = self._ocr.ocr(image, cls=True)
            
            if not result or not result[0]:
                return []
            
            ocr_results = []
            for line in result[0]:
                bbox, (text, conf) = line
                # Normalize bbox to [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
                norm_bbox = [[float(p[0]), float(p[1])] for p in bbox]
                ocr_results.append(OCRResult(
                    text=text,
                    confidence=float(conf),
                    bbox=norm_bbox,
                    engine="paddleocr"
                ))
            
            return ocr_results
            
        except Exception as e:
            logger.error(f"PaddleOCR error: {e}")
            return []
    
    def ocr_pdf_page(self, pdf_path: Path, page_num: int, 
                     dpi: int = 200) -> list[OCRResult]:
        """OCR a specific PDF page by rendering to image."""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(pdf_path)
            page = doc[page_num]
            pix = page.get_pixmap(dpi=dpi)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            doc.close()
            return self.ocr_image(img)
        except Exception as e:
            logger.error(f"Failed to render PDF page {page_num}: {e}")
            return []


def get_paddleocr_engine(lang: str = "en", use_gpu: bool = False) -> PaddleOCREngine:
    """Get or create singleton PaddleOCR engine."""
    return PaddleOCREngine(lang=lang, use_gpu=use_gpu)