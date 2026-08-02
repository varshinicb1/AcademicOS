"""Tesseract OCR Engine Wrapper (fallback)."""
from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class TesseractResult:
    text: str
    confidence: float
    bbox: list[list[int]]
    engine: str = "tesseract"


class TesseractEngine:
    """Tesseract OCR wrapper - lightweight fallback."""
    
    def __init__(self, lang: str = "eng+hin", config: str = "--oem 3 --psm 6"):
        self.lang = lang
        self.config = config
        self._verify_install()
    
    def _verify_install(self):
        try:
            result = subprocess.run(
                ["tesseract", "--version"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError("Tesseract not found")
            logger.info(f"Tesseract available: {result.stdout.split()[1]}")
        except Exception as e:
            logger.warning(f"Tesseract not available: {e}")
            raise
    
    def is_available(self) -> bool:
        try:
            subprocess.run(["tesseract", "--version"], capture_output=True, timeout=2)
            return True
        except Exception:
            return False
    
    def ocr_image(self, image: np.ndarray | Image.Image | Path) -> list[TesseractResult]:
        """Run Tesseract on image."""
        if isinstance(image, (str, Path)):
            image = Image.open(image).convert("RGB")
        elif isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            image.save(tmp.name, "PNG")
            tmp_path = tmp.name
        
        try:
            # Run tesseract with hOCR output for bounding boxes
            hocr_path = tmp_path.replace(".png", ".hocr")
            cmd = [
                "tesseract", tmp_path, 
                tmp_path.replace(".png", ""),
                "-l", self.lang,
                "--psm", "6",  # Assume uniform block of text
                "hocr"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.error(f"Tesseract failed: {result.stderr}")
                return []
            
            # Parse hOCR for text and bounding boxes
            return self._parse_hocr(hocr_path)
            
        except Exception as e:
            logger.error(f"Tesseract error: {e}")
            return []
        finally:
            # Cleanup
            for f in [tmp_path, hocr_path]:
                try:
                    Path(f).unlink(missing_ok=True)
                except Exception:
                    pass
    
    def _parse_hocr(self, hocr_path: str) -> list[TesseractResult]:
        """Parse hOCR output for structured results."""
        try:
            from bs4 import BeautifulSoup
            with open(hocr_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, "html.parser")
            
            results = []
            for ocrx_word in soup.find_all(class_="ocrx_word"):
                title = ocrx_word.get("title", "")
                # Format: bbox x1 y1 x2 y2; x_wconf 95
                bbox = [0, 0, 0, 0]
                conf = 0.0
                for part in title.split(";"):
                    part = part.strip()
                    if part.startswith("bbox"):
                        bbox = list(map(int, part.split()[1:5]))
                    elif part.startswith("x_wconf"):
                        conf = int(part.split()[1]) / 100.0
                
                text = ocrx_word.get_text(strip=True)
                if text:
                    results.append(TesseractResult(
                        text=text,
                        confidence=conf,
                        bbox=[[bbox[0], bbox[1]], [bbox[2], bbox[1]], 
                              [bbox[2], bbox[3]], [bbox[0], bbox[3]]],
                        engine="tesseract"
                    ))
            
            # Also get full page text from ocr_page
            full_text = soup.find(class_="ocr_page")
            if full_text:
                page_text = full_text.get_text(" ", strip=True)
                if page_text and not results:
                    # Fallback: single block
                    results.append(TesseractResult(
                        text=page_text,
                        confidence=0.5,
                        bbox=[[0, 0], [image_width, 0], [image_width, image_height], [0, image_height]],
                        engine="tesseract"
                    ))
            
            return results
        except Exception as e:
            logger.error(f"hOCR parse error: {e}")
            return []


def get_tesseract_engine(lang: str = "eng+hin") -> Optional[TesseractEngine]:
    """Get Tesseract engine if available."""
    try:
        return TesseractEngine(lang=lang)
    except Exception:
        return None