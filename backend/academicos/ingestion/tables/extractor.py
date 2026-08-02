"""Table Extraction - Multi-engine ensemble."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)


class TableEngine(str, Enum):
    PDFPLUMBER = "pdfplumber"
    CAMELOT = "camelot"
    TRANSFORMER = "transformer"


@dataclass
class TableCell:
    text: str
    row: int
    col: int
    rowspan: int = 1
    colspan: int = 1
    bbox: list[float] = None  # [x1, y1, x2, y2] normalized 0-1


@dataclass
class ExtractedTable:
    engine: TableEngine
    page_number: int
    bbox: list[float]  # [x1, y1, x2, y2] normalized
    rows: int
    cols: int
    cells: list[TableCell]
    markdown: str
    csv: str
    confidence: float
    raw_data: dict = None


class TableExtractor:
    """Ensemble table extractor using multiple engines."""
    
    def __init__(self, engines: list[TableEngine] = None, 
                 min_accuracy: float = 0.7):
        self.engines = engines or [TableEngine.PDFPLUMBER, TableEngine.CAMELOT]
        self.min_accuracy = min_accuracy
    
    def extract_page(self, pdf_path: Path, page_num: int) -> list[ExtractedTable]:
        """Extract all tables from a page using all engines."""
        all_tables = []
        
        for engine in self.engines:
            try:
                if engine == TableEngine.PDFPLUMBER:
                    tables = self._extract_pdfplumber(pdf_path, page_num)
                elif engine == TableEngine.CAMELOT:
                    tables = self._extract_camelot(pdf_path, page_num)
                else:
                    continue
                
                for table in tables:
                    if table.confidence >= self.min_accuracy:
                        all_tables.append(table)
            except Exception as e:
                logger.debug(f"{engine.value} failed on page {page_num}: {e}")
        
        # Deduplicate overlapping tables (IoU-based)
        return self._deduplicate_tables(all_tables)
    
    def _extract_pdfplumber(self, pdf_path: Path, page_num: int) -> list[ExtractedTable]:
        """Extract tables using pdfplumber."""
        import pdfplumber
        tables = []
        
        with pdfplumber.open(pdf_path) as pdf:
            if page_num >= len(pdf.pages):
                return []
            
            page = pdf.pages[page_num]
            page_tables = page.extract_tables()
            
            if not page_tables:
                return []
            
            for i, table_data in enumerate(page_tables):
                if not table_data or len(table_data) < 2:
                    continue
                
                # Convert to markdown and CSV
                markdown = self._table_to_markdown(table_data)
                csv = self._table_to_csv(table_data)
                
                # Estimate confidence from cell fill rate
                fill_rate = self._compute_fill_rate(table_data)
                
                tables.append(ExtractedTable(
                    engine=TableEngine.PDFPLUMBER,
                    page_number=page_num,
                    bbox=[0, 0, 1, 1],  # pdfplumber doesn't give bbox easily
                    rows=len(table_data),
                    cols=len(table_data[0]) if table_data else 0,
                    cells=[],
                    markdown=markdown,
                    csv=csv,
                    confidence=fill_rate,
                    raw_data={"table_data": table_data}
                ))
        
        return tables
    
    def _extract_camelot(self, pdf_path: Path, page_num: int) -> list[ExtractedTable]:
        """Extract tables using Camelot."""
        try:
            import camelot
        except ImportError:
            return []
        
        tables = []
        try:
            # Camelot uses 1-indexed pages
            camelot_tables = camelot.read_pdf(
                str(pdf_path), 
                pages=str(page_num + 1),
                flavor='lattice',  # Try lattice first
                suppress_stdout=True
            )
            
            if camelot_tables.n == 0:
                # Try stream flavor
                camelot_tables = camelot.read_pdf(
                    str(pdf_path),
                    pages=str(page_num + 1),
                    flavor='stream',
                    suppress_stdout=True
                )
            
            for i, table in enumerate(camelot_tables):
                if table.df.empty:
                    continue
                
                # Convert to list of lists
                table_data = table.df.values.tolist()
                if len(table_data) < 2:
                    continue
                
                markdown = self._table_to_markdown(table_data)
                csv = table.df.to_csv(index=False)
                
                # Camelot provides accuracy
                confidence = getattr(table, 'accuracy', 0.8) / 100.0
                
                # Get bbox from camelot
                bbox = [0, 0, 1, 1]
                if hasattr(table, '_bbox'):
                    bbox = table._bbox
                
                tables.append(ExtractedTable(
                    engine=TableEngine.CAMELOT,
                    page_number=page_num,
                    bbox=bbox,
                    rows=len(table_data),
                    cols=len(table_data[0]) if table_data else 0,
                    cells=[],
                    markdown=markdown,
                    csv=csv,
                    confidence=confidence,
                    raw_data={"camelot_report": table.parsing_report}
                ))
        except Exception as e:
            logger.debug(f"Camelot failed: {e}")
        
        return tables
    
    def _table_to_markdown(self, table_data: list[list]) -> str:
        """Convert table data to markdown."""
        if not table_data:
            return ""
        
        # Header
        header = table_data[0]
        md = "| " + " | ".join(str(c) if c else "" for c in header) + " |\n"
        md += "| " + " | ".join("---" for _ in header) + " |\n"
        
        # Rows
        for row in table_data[1:]:
            md += "| " + " | ".join(str(c) if c else "" for c in row) + " |\n"
        
        return md
    
    def _table_to_csv(self, table_data: list[list]) -> str:
        """Convert table data to CSV."""
        import csv
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(table_data)
        return output.getvalue()
    
    def _compute_fill_rate(self, table_data: list[list]) -> float:
        """Compute cell fill rate as confidence proxy."""
        if not table_data:
            return 0.0
        total = sum(len(row) for row in table_data)
        filled = sum(1 for row in table_data for cell in row if cell and str(cell).strip())
        return filled / max(total, 1)
    
    def _deduplicate_tables(self, tables: list[ExtractedTable]) -> list[ExtractedTable]:
        """Remove duplicate tables based on bbox overlap (IoU)."""
        if len(tables) <= 1:
            return tables
        
        # Sort by confidence descending
        tables.sort(key=lambda t: t.confidence, reverse=True)
        
        kept = []
        for table in tables:
            is_dup = False
            for kept_table in kept:
                if self._iou(table.bbox, kept_table.bbox) > 0.5:
                    is_dup = True
                    break
            if not is_dup:
                kept.append(table)
        
        return kept
    
    def _iou(self, bbox1: list[float], bbox2: list[float]) -> float:
        """Compute IoU of two normalized bboxes."""
        x1 = max(bbox1[0], bbox2[0])
        y1 = max(bbox1[1], bbox2[1])
        x2 = min(bbox1[2], bbox2[2])
        y2 = min(bbox1[3], bbox2[3])
        
        if x2 <= x1 or y2 <= y1:
            return 0.0
        
        inter = (x2 - x1) * (y2 - y1)
        area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
        area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
        
        return inter / (area1 + area2 - inter) if (area1 + area2 - inter) > 0 else 0.0


def get_table_extractor(engines: list[str] = None, 
                        min_accuracy: float = 0.7) -> TableExtractor:
    """Factory for table extractor."""
    engine_enums = [TableEngine(e) for e in (engines or ["pdfplumber", "camelot"])]
    return TableExtractor(engines=engine_enums, min_accuracy=min_accuracy)