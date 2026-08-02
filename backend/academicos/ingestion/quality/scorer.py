"""Quality Scoring and Validation."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class QualityLevel(str, Enum):
    EXCELLENT = "excellent"      # > 0.9
    GOOD = "good"                # 0.7 - 0.9
    ACCEPTABLE = "acceptable"    # 0.5 - 0.7
    POOR = "poor"                # 0.3 - 0.5
    FAILED = "failed"            # < 0.3


@dataclass
class PageQuality:
    page_number: int
    overall_score: float
    level: QualityLevel
    text_score: float = 0.0
    structure_score: float = 0.0
    table_score: float = 0.0
    figure_score: float = 0.0
    equation_score: float = 0.0
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class DocumentQuality:
    document_id: str
    overall_score: float
    level: QualityLevel
    page_count: int
    pages_scored: int
    page_qualities: list[PageQuality] = field(default_factory=list)
    summary: dict = field(default_factory=dict)


class QualityScorer:
    """Score extraction quality per page and document."""
    
    def __init__(self, 
                 min_text_chars: int = 50,
                 min_confidence: float = 0.5,
                 require_structure: bool = True):
        self.min_text_chars = min_text_chars
        self.min_confidence = min_confidence
        self.require_structure = require_structure
    
    def score_page(self, page_data: dict) -> PageQuality:
        """Score a single page's extraction quality."""
        issues = []
        warnings = []
        
        # Text quality
        text = page_data.get("text", "") or ""
        text_len = len(text.strip())
        text_confidence = page_data.get("ocr_confidence", 1.0)
        
        if text_len == 0:
            text_score = 0.0
            issues.append("no_text_extracted")
        elif text_len < self.min_text_chars:
            text_score = 0.3
            warnings.append(f"low_text_length:{text_len}")
        else:
            text_score = min(1.0, text_confidence * (text_len / 500))
        
        # Structure quality
        structure_score = 0.5  # baseline
        headings = page_data.get("headings", [])
        if headings:
            structure_score += 0.2
        if page_data.get("reading_order"):
            structure_score += 0.15
        if page_data.get("language"):
            structure_score += 0.15
        structure_score = min(1.0, structure_score)
        
        if self.require_structure and not headings:
            warnings.append("no_headings_detected")
        
        # Table quality
        tables = page_data.get("tables", [])
        table_score = 0.0
        if tables:
            table_conf = sum(t.get("confidence", 0) for t in tables) / len(tables)
            table_score = min(1.0, table_conf * (1 + 0.1 * len(tables)))
        else:
            # Not necessarily bad - page might not have tables
            table_score = 0.5
        
        # Figure quality
        figures = page_data.get("figures", [])
        figure_score = 0.5 if figures else 0.3  # Neutral if none
        
        # Equation quality
        equations = page_data.get("equations", [])
        equation_score = 0.5 if equations else 0.3
        
        # Overall weighted score
        weights = {
            "text": 0.4,
            "structure": 0.2,
            "table": 0.15,
            "figure": 0.15,
            "equation": 0.1,
        }
        
        overall = (
            weights["text"] * text_score +
            weights["structure"] * structure_score +
            weights["table"] * table_score +
            weights["figure"] * figure_score +
            weights["equation"] * equation_score
        )
        
        # Determine level
        if overall >= 0.9:
            level = QualityLevel.EXCELLENT
        elif overall >= 0.7:
            level = QualityLevel.GOOD
        elif overall >= 0.5:
            level = QualityLevel.ACCEPTABLE
        elif overall >= 0.3:
            level = QualityLevel.POOR
        else:
            level = QualityLevel.FAILED
        
        return PageQuality(
            page_number=page_data.get("page_number", 0),
            overall_score=round(overall, 3),
            level=level,
            text_score=round(text_score, 3),
            structure_score=round(structure_score, 3),
            table_score=round(table_score, 3),
            figure_score=round(figure_score, 3),
            equation_score=round(equation_score, 3),
            issues=issues,
            warnings=warnings
        )
    
    def score_document(self, document_data: dict) -> DocumentQuality:
        """Score entire document."""
        pages = document_data.get("pages", [])
        page_qualities = [self.score_page(p) for p in pages]
        
        if not page_qualities:
            return DocumentQuality(
                document_id=document_data.get("document_id", ""),
                overall_score=0.0,
                level=QualityLevel.FAILED,
                page_count=0,
                pages_scored=0
            )
        
        overall = sum(p.overall_score for p in page_qualities) / len(page_qualities)
        
        if overall >= 0.9:
            level = QualityLevel.EXCELLENT
        elif overall >= 0.7:
            level = QualityLevel.GOOD
        elif overall >= 0.5:
            level = QualityLevel.ACCEPTABLE
        elif overall >= 0.3:
            level = QualityLevel.POOR
        else:
            level = QualityLevel.FAILED
        
        # Summary stats
        summary = {
            "excellent_pages": sum(1 for p in page_qualities if p.level == QualityLevel.EXCELLENT),
            "good_pages": sum(1 for p in page_qualities if p.level == QualityLevel.GOOD),
            "acceptable_pages": sum(1 for p in page_qualities if p.level == QualityLevel.ACCEPTABLE),
            "poor_pages": sum(1 for p in page_qualities if p.level == QualityLevel.POOR),
            "failed_pages": sum(1 for p in page_qualities if p.level == QualityLevel.FAILED),
            "avg_text_score": round(sum(p.text_score for p in page_qualities) / len(page_qualities), 3),
            "avg_structure_score": round(sum(p.structure_score for p in page_qualities) / len(page_qualities), 3),
            "total_issues": sum(len(p.issues) for p in page_qualities),
            "total_warnings": sum(len(p.warnings) for p in page_qualities),
        }
        
        return DocumentQuality(
            document_id=document_data.get("document_id", ""),
            overall_score=round(overall, 3),
            level=level,
            page_count=len(pages),
            pages_scored=len(page_qualities),
            page_qualities=page_qualities,
            summary=summary
        )
    
    def should_flag_for_review(self, doc_quality: DocumentQuality, 
                                threshold: float = 0.6) -> bool:
        """Check if document needs human review."""
        return doc_quality.overall_score < threshold


def get_quality_scorer(**kwargs) -> QualityScorer:
    """Factory for quality scorer."""
    return QualityScorer(**kwargs)