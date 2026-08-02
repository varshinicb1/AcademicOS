"""Layout Analysis - Document structure extraction."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum
from typing import List

logger = logging.getLogger(__name__)


class BlockType(str, Enum):
    TEXT = "text"
    TITLE = "title"
    HEADING = "heading"
    LIST = "list"
    TABLE = "table"
    FIGURE = "figure"
    EQUATION = "equation"
    HEADER = "header"
    FOOTER = "footer"
    PAGE_NUMBER = "page_number"
    FOOTNOTE = "footnote"


@dataclass
class LayoutBlock:
    type: BlockType
    bbox: list[float]  # [x1, y1, x2, y2] normalized 0-1
    text: str = ""
    confidence: float = 0.0
    level: int = 0  # Heading level (1-6)
    metadata: dict = field(default_factory=dict)


@dataclass
class PageLayout:
    page_number: int
    width: float
    height: float
    blocks: list[LayoutBlock] = field(default_factory=list)
    reading_order: list[int] = field(default_factory=list)  # Block indices in reading order
    language: str = "en"


class LayoutAnalyzer:
    """Document layout analysis using pdfplumber + optional LayoutParser."""
    
    def __init__(self, use_layoutparser: bool = False):
        self.use_layoutparser = use_layoutparser
        self._lp_model = None
        
        if use_layoutparser:
            self._init_layoutparser()
    
    def _init_layoutparser(self):
        try:
            import layoutparser as lp
            self._lp_model = lp.Detectron2LayoutModel(
                'lp://PubLayNet/ppyolov2_r50vd_dcn_365e/config',
                extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.8],
                label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"}
            )
            logger.info("LayoutParser initialized")
        except Exception as e:
            logger.warning(f"LayoutParser not available: {e}")
            self.use_layoutparser = False
    
    def analyze_page(self, pdf_path: Path, page_num: int) -> PageLayout:
        """Analyze layout of a single page."""
        # First, get basic structure from pdfplumber
        layout = self._analyze_with_pdfplumber(pdf_path, page_num)
        
        # Enhance with LayoutParser if available
        if self.use_layoutparser and self._lp_model:
            layout = self._enhance_with_layoutparser(pdf_path, page_num, layout)
        
        # Detect reading order
        layout.reading_order = self._compute_reading_order(layout.blocks)
        
        return layout
    
    def _analyze_with_pdfplumber(self, pdf_path: Path, page_num: int) -> PageLayout:
        """Basic layout from pdfplumber."""
        import pdfplumber
        
        with pdfplumber.open(pdf_path) as pdf:
            if page_num >= len(pdf.pages):
                return PageLayout(page_number=page_num, width=0, height=0)
            
            page = pdf.pages[page_num]
            width, height = page.width, page.height
            
            blocks = []
            
            # Extract text with positions
            chars = page.chars
            if chars:
                # Group chars into lines by y-position
                lines = self._group_chars_into_lines(chars, height)
                
                for line in lines:
                    text = "".join(c["text"] for c in line)
                    if not text.strip():
                        continue
                    
                    # Determine block type
                    block_type = self._classify_text_block(text, line)
                    level = self._get_heading_level(text, line) if block_type == BlockType.HEADING else 0
                    
                    # Compute bbox
                    x0 = min(c["x0"] for c in line) / width
                    y0 = min(c["top"] for c in line) / height
                    x1 = max(c["x1"] for c in line) / width
                    y1 = max(c["bottom"] for c in line) / height
                    
                    blocks.append(LayoutBlock(
                        type=block_type,
                        bbox=[x0, y0, x1, y1],
                        text=text.strip(),
                        confidence=0.9,
                        level=level
                    ))
            
            # Detect tables
            tables = page.find_tables()
            for table in tables:
                bbox = table.bbox
                blocks.append(LayoutBlock(
                    type=BlockType.TABLE,
                    bbox=[bbox[0]/width, bbox[1]/height, bbox[2]/width, bbox[3]/height],
                    text="[TABLE]",
                    confidence=0.8
                ))
            
            # Detect images/figures
            images = page.images
            for img in images:
                blocks.append(LayoutBlock(
                    type=BlockType.FIGURE,
                    bbox=[img["x0"]/width, img["top"]/height, img["x1"]/width, img["bottom"]/height],
                    text="[FIGURE]",
                    confidence=0.7
                ))
            
            return PageLayout(
                page_number=page_num,
                width=width,
                height=height,
                blocks=blocks
            )
    
    def _group_chars_into_lines(self, chars: list[dict], page_height: float, 
                                 y_tolerance: float = 3.0) -> list[list[dict]]:
        """Group characters into lines by vertical position."""
        if not chars:
            return []
        
        # Sort by y (top) then x
        sorted_chars = sorted(chars, key=lambda c: (c["top"], c["x0"]))
        
        lines = []
        current_line = [sorted_chars[0]]
        
        for char in sorted_chars[1:]:
            # Check if same line (similar y position)
            avg_y = sum(c["top"] for c in current_line) / len(current_line)
            if abs(char["top"] - avg_y) <= y_tolerance:
                current_line.append(char)
            else:
                # Sort line by x
                current_line.sort(key=lambda c: c["x0"])
                lines.append(current_line)
                current_line = [char]
        
        if current_line:
            current_line.sort(key=lambda c: c["x0"])
            lines.append(current_line)
        
        return lines
    
    def _classify_text_block(self, text: str, line: list[dict]) -> BlockType:
        """Classify text block type."""
        text = text.strip()
        
        # Check for list items
        if text.startswith(("•", "-", "*", "·", "–", "—")) or \
           (len(text) > 2 and text[0].isdigit() and text[1] in ".):"):
            return BlockType.LIST
        
        # Check for all caps (possible heading)
        if text.isupper() and len(text) > 3:
            return BlockType.HEADING
        
        # Check for title case
        if text.istitle() and len(text.split()) <= 8:
            return BlockType.TITLE
        
        return BlockType.TEXT
    
    def _get_heading_level(self, text: str, line: list[dict]) -> int:
        """Estimate heading level from font size."""
        if not line:
            return 1
        avg_size = sum(c.get("size", 12) for c in line) / len(line)
        if avg_size >= 18:
            return 1
        elif avg_size >= 16:
            return 2
        elif avg_size >= 14:
            return 3
        return 4
    
    def _enhance_with_layoutparser(self, pdf_path: Path, page_num: int, 
                                    layout: PageLayout) -> PageLayout:
        """Enhance layout with LayoutParser deep learning model."""
        try:
            import layoutparser as lp
            import fitz
            
            # Render page to image
            doc = fitz.open(pdf_path)
            page = doc[page_num]
            pix = page.get_pixmap(dpi=150)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            doc.close()
            
            # Detect layout
            lp_layout = self._lp_model.detect(img)
            
            # Convert to our format
            for block in lp_layout:
                bbox = [block.x_1 / img.width, block.y_1 / img.height,
                        block.x_2 / img.width, block.y_2 / img.height]
                
                # Map LP types to our types
                type_map = {
                    "Text": BlockType.TEXT,
                    "Title": BlockType.TITLE,
                    "List": BlockType.LIST,
                    "Table": BlockType.TABLE,
                    "Figure": BlockType.FIGURE,
                }
                block_type = type_map.get(block.type, BlockType.TEXT)
                
                layout.blocks.append(LayoutBlock(
                    type=block_type,
                    bbox=bbox,
                    text="",  # Would need OCR to fill
                    confidence=block.score,
                    metadata={"layoutparser_type": block.type}
                ))
            
        except Exception as e:
            logger.debug(f"LayoutParser enhancement failed: {e}")
        
        return layout
    
    def _compute_reading_order(self, blocks: list[LayoutBlock]) -> list[int]:
        """Compute reading order (top-to-bottom, left-to-right)."""
        # Sort by y center, then x center
        indexed = [(i, b) for i, b in enumerate(blocks)]
        indexed.sort(key=lambda x: (
            (x[1].bbox[1] + x[1].bbox[3]) / 2,  # y center
            (x[1].bbox[0] + x[1].bbox[2]) / 2   # x center
        ))
        return [i for i, _ in indexed]


def get_layout_analyzer(use_layoutparser: bool = False) -> LayoutAnalyzer:
    """Factory for layout analyzer."""
    return LayoutAnalyzer(use_layoutparser=use_layoutparser)