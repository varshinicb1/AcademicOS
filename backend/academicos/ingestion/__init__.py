"""AcademicOS Ingestion Pipeline - Free/Local PDF Processing."""
from __future__ import annotations

from .config import settings, IngestionSettings
from .state import IngestionStateDB, DocumentState, DocumentStatus, get_state_db
from .ocr import EnsembleOCR, UnifiedOCRResult, OCREngineType, get_ensemble_ocr
from .layout import LayoutAnalyzer, PageLayout, LayoutBlock, BlockType, get_layout_analyzer
from .tables import TableExtractor, ExtractedTable, TableEngine, get_table_extractor
from .classification import DocumentClassifier, ClassificationResult, DocumentType, get_classifier
from .quality import QualityScorer, PageQuality, DocumentQuality, QualityLevel, get_quality_scorer
from .output import OutputWriter, get_output_writer
from .main import IngestionPipeline, DocumentProcessor, main

__all__ = [
    # Config
    "settings",
    "IngestionSettings",
    # State
    "IngestionStateDB",
    "DocumentState",
    "DocumentStatus",
    "get_state_db",
    # OCR
    "EnsembleOCR",
    "UnifiedOCRResult",
    "OCREngineType",
    "get_ensemble_ocr",
    # Layout
    "LayoutAnalyzer",
    "PageLayout",
    "LayoutBlock",
    "BlockType",
    "get_layout_analyzer",
    # Tables
    "TableExtractor",
    "ExtractedTable",
    "TableEngine",
    "get_table_extractor",
    # Classification
    "DocumentClassifier",
    "ClassificationResult",
    "DocumentType",
    "get_classifier",
    # Quality
    "QualityScorer",
    "PageQuality",
    "DocumentQuality",
    "QualityLevel",
    "get_quality_scorer",
    # Output
    "OutputWriter",
    "get_output_writer",
    # Main
    "IngestionPipeline",
    "DocumentProcessor",
    "main",
]

__version__ = "1.0.0"