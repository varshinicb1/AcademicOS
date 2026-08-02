"""Image preprocessing for OCR optimization."""
from __future__ import annotations

import logging
import cv2
import numpy as np
from PIL import Image
from typing import Optional

logger = logging.getLogger(__name__)


def preprocess_for_ocr(image: np.ndarray | Image.Image, 
                       deskew: bool = True,
                       denoise: bool = True,
                       enhance_contrast: bool = True,
                       binarize: bool = False) -> np.ndarray:
    """Preprocess image for better OCR results."""
    
    if isinstance(image, Image.Image):
        image = np.array(image.convert("RGB"))
    
    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image.copy()
    
    # Deskew
    if deskew:
        gray = _deskew(gray)
    
    # Denoise
    if denoise:
        gray = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)
    
    # Enhance contrast
    if enhance_contrast:
        gray = _enhance_contrast(gray)
    
    # Binarize (optional, can hurt some OCR engines)
    if binarize:
        gray = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
    
    return gray


def _deskew(image: np.ndarray) -> np.ndarray:
    """Deskew image using minAreaRect on text contours."""
    try:
        # Threshold
        _, thresh = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return image
        
        # Get largest contour (assume it's the text block)
        largest = max(contours, key=cv2.contourArea)
        
        # Get minimum area rectangle
        rect = cv2.minAreaRect(largest)
        angle = rect[-1]
        
        # Correct angle
        if angle < -45:
            angle = 90 + angle
        
        # Only rotate if significant skew
        if abs(angle) > 0.5:
            h, w = image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(image, M, (w, h), 
                                     flags=cv2.INTER_CUBIC, 
                                     borderMode=cv2.BORDER_REPLICATE)
            return rotated
    except Exception:
        pass
    
    return image


def _enhance_contrast(image: np.ndarray) -> np.ndarray:
    """Enhance contrast using CLAHE."""
    try:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(image)
    except Exception:
        return image


def render_pdf_page_to_image(pdf_path: str, page_num: int, dpi: int = 200) -> np.ndarray:
    """Render PDF page to OpenCV image."""
    import fitz
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    pix = page.get_pixmap(dpi=dpi)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    doc.close()
    return np.array(img)


def crop_to_content(image: np.ndarray, padding: int = 10) -> np.ndarray:
    """Crop image to content bounding box."""
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    coords = cv2.findNonZero(thresh)
    if coords is None:
        return image
    
    x, y, w, h = cv2.boundingRect(coords)
    x = max(0, x - padding)
    y = max(0, y - padding)
    w = min(image.shape[1] - x, w + 2 * padding)
    h = min(image.shape[0] - y, h + 2 * padding)
    
    return image[y:y+h, x:x+w]