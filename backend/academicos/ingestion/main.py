"""Main Ingestion Pipeline - Orchestrates all extraction modules."""
from __future__ import annotations

import asyncio
import json
import logging
import signal
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional
import orjson

from .config import settings
from .state import IngestionStateDB, DocumentStatus, get_state_db
from .ocr import EnsembleOCR, get_ensemble_ocr, OCREngineType
from .layout import LayoutAnalyzer, get_layout_analyzer, PageLayout
from .tables import TableExtractor, get_table_extractor, ExtractedTable
from .classification import DocumentClassifier, get_classifier, ClassificationResult, DocumentType
from .quality import QualityScorer, get_quality_scorer, DocumentQuality
from .output import OutputWriter, get_output_writer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(settings.log_dir / f"ingestion_{datetime.now():%Y%m%d}.log")
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class PageResult:
    page_number: int
    text: str
    markdown: str
    ocr_confidence: float
    ocr_engine: OCREngineType
    layout: PageLayout
    tables: list[ExtractedTable]
    figures: list[dict]
    equations: list[dict]
    headings: list[dict]
    qa_pairs: list[dict]
    processing_time_ms: int
    confidence: float


@dataclass
class DocumentResult:
    document_id: str
    source_path: str
    file_size: int
    page_count: int
    classification: ClassificationResult
    pages: list[PageResult]
    quality: DocumentQuality
    processing_time_seconds: float
    timestamp: str
    version: str = "1.0"


class DocumentProcessor:
    """Process a single document through the full pipeline."""
    
    def __init__(self, 
                 state_db: IngestionStateDB,
                 ocr: EnsembleOCR,
                 layout_analyzer: LayoutAnalyzer,
                 table_extractor: TableExtractor,
                 classifier: DocumentClassifier,
                 quality_scorer: QualityScorer,
                 output_writer: OutputWriter):
        self.state_db = state_db
        self.ocr = ocr
        self.layout_analyzer = layout_analyzer
        self.table_extractor = table_extractor
        self.classifier = classifier
        self.quality_scorer = quality_scorer
        self.output_writer = output_writer
    
    def process(self, doc_state, source_root: Path) -> DocumentResult:
        """Process a single document."""
        import time
        start_time = time.time()
        
        pdf_path = source_root / doc_state.source_path
        doc_state = self.state_db.get_document(doc_state.document_id)
        
        # Open PDF to get page count
        import fitz
        doc = fitz.open(pdf_path)
        page_count = len(doc)
        doc.close()
        
        self.state_db.start_processing(doc_state.document_id, page_count)
        
        # Extract first few pages for classification
        first_pages_text = ""
        for p in range(min(3, page_count)):
            native_text, _ = self.ocr.extract_native_text(pdf_path, p)
            first_pages_text += native_text + "\n"
        
        # Classify
        classification = self.classifier.classify(pdf_path, first_pages_text)
        
        # Process each page
        pages = []
        for page_num in range(page_count):
            page_start = time.time()
            
            # OCR
            ocr_result = self.ocr.process_page(pdf_path, page_num)
            
            # Layout
            layout = self.layout_analyzer.analyze_page(pdf_path, page_num)
            
            # Tables
            tables = self.table_extractor.extract_page(pdf_path, page_num)
            
            # Figures (from layout)
            figures = [
                {"bbox": b.bbox, "type": "figure", "caption": ""}
                for b in layout.blocks if b.type.value == "figure"
            ]
            
            # Equations (placeholder - would need math detector)
            equations = []
            
            # Headings
            headings = [
                {"level": b.level, "text": b.text, "bbox": b.bbox}
                for b in layout.blocks if b.type.value in ("heading", "title")
            ]
            
            # Q/A pairs (placeholder)
            qa_pairs = []
            
            # Build page result
            page_result = PageResult(
                page_number=page_num + 1,
                text=ocr_result.text,
                markdown=self._to_markdown(ocr_result.text, layout, tables),
                ocr_confidence=ocr_result.confidence,
                ocr_engine=ocr_result.engine,
                layout=layout,
                tables=tables,
                figures=figures,
                equations=equations,
                headings=headings,
                qa_pairs=qa_pairs,
                processing_time_ms=int((time.time() - page_start) * 1000),
                confidence=ocr_result.confidence
            )
            
            pages.append(page_result)
            
            # Update progress
            self.state_db.update_page_progress(
                doc_state.document_id, 
                page_num + 1, 
                page_num + 1,
                ocr_result.confidence
            )
        
        # Build document data for quality scoring
        doc_data = {
            "document_id": doc_state.document_id,
            "pages": [
                {
                    "page_number": p.page_number,
                    "text": p.text,
                    "ocr_confidence": p.ocr_confidence,
                    "headings": p.headings,
                    "tables": [{"confidence": t.confidence} for t in p.tables],
                    "figures": p.figures,
                    "equations": p.equations,
                    "reading_order": p.layout.reading_order,
                    "language": p.layout.language,
                }
                for p in pages
            ]
        }
        
        # Quality scoring
        quality = self.quality_scorer.score_document(doc_data)
        
        # Flag for review if needed
        if self.quality_scorer.should_flag_for_review(quality):
            self.state_db.flag_for_review(doc_state.document_id, 
                f"Quality score {quality.overall_score:.2f} below threshold")
        
        # Write output
        output_path = self.output_writer.write_document(
            doc_state.document_id,
            doc_state.source_path,
            pdf_path.stat().st_size,
            page_count,
            classification,
            pages,
            quality
        )
        
        processing_time = time.time() - start_time
        
        # Complete
        self.state_db.complete_document(
            doc_state.document_id, 
            output_path, 
            classification.doc_type.value
        )
        
        return DocumentResult(
            document_id=doc_state.document_id,
            source_path=doc_state.source_path,
            file_size=pdf_path.stat().st_size,
            page_count=page_count,
            classification=classification,
            pages=pages,
            quality=quality,
            processing_time_seconds=processing_time,
            timestamp=datetime.now().isoformat()
        )
    
    def _to_markdown(self, text: str, layout: PageLayout, tables: list[ExtractedTable]) -> str:
        """Convert page content to structured markdown."""
        md_parts = []
        
        # Add headings and text in reading order
        for block_idx in layout.reading_order:
            if block_idx < len(layout.blocks):
                block = layout.blocks[block_idx]
                if block.type.value in ("heading", "title"):
                    prefix = "#" * min(block.level + 1, 6) + " "
                    md_parts.append(f"{prefix}{block.text}")
                elif block.type.value == "text":
                    md_parts.append(block.text)
                elif block.type.value == "list":
                    md_parts.append(f"- {block.text}")
        
        # Add tables
        for table in tables:
            if table.markdown:
                md_parts.append("\n" + table.markdown + "\n")
        
        return "\n\n".join(md_parts)


def process_document_worker(args: tuple) -> tuple[str, bool, str]:
    """Worker function for multiprocessing."""
    doc_state_dict, source_root_str, settings_dict = args
    
    # Recreate objects in worker
    from .state import IngestionStateDB, DocumentState, DocumentStatus
    from .ocr import get_ensemble_ocr
    from .layout import get_layout_analyzer
    from .tables import get_table_extractor
    from .classification import get_classifier
    from .quality import get_quality_scorer
    from .output import get_output_writer
    from .config import IngestionSettings
    
    # Restore settings
    settings_obj = IngestionSettings(**settings_dict)
    
    source_root = Path(source_root_str)
    state_db = IngestionStateDB(settings_obj.state_db)
    
    doc_state = DocumentState(**doc_state_dict)
    
    try:
        ocr = get_ensemble_ocr(
            paddleocr_lang=settings_obj.paddleocr_lang,
            tesseract_lang=settings_obj.tesseract_lang,
            use_gpu=settings_obj.use_gpu,
            force_ocr_min_chars=settings_obj.force_ocr_min_chars,
            confidence_threshold=settings_obj.ocr_confidence_threshold
        )
        layout_analyzer = get_layout_analyzer(use_layoutparser=settings_obj.use_layoutparser)
        table_extractor = get_table_extractor(
            engines=settings_obj.table_engines,
            min_accuracy=settings_obj.table_min_accuracy
        )
        classifier = get_classifier(use_llm=settings_obj.use_llm_classification)
        quality_scorer = get_quality_scorer(
            min_confidence=settings_obj.min_page_confidence
        )
        output_writer = get_output_writer(settings_obj.output_dir)
        
        processor = DocumentProcessor(
            state_db, ocr, layout_analyzer, table_extractor,
            classifier, quality_scorer, output_writer
        )
        
        result = processor.process(doc_state, source_root)
        return result.document_id, True, ""
        
    except Exception as e:
        logger.error(f"Worker error for {doc_state.source_path}: {e}")
        state_db.fail_document(doc_state.document_id, str(e))
        return doc_state.document_id, False, str(e)
    finally:
        state_db.close()


class IngestionPipeline:
    """Main ingestion pipeline with multiprocessing and resume support."""
    
    def __init__(self, settings_override: dict = None):
        self.settings = settings
        if settings_override:
            for k, v in settings_override.items():
                setattr(self.settings, k, v)
        
        self.state_db = get_state_db(self.settings.state_db)
        self.output_writer = get_output_writer(self.settings.output_dir)
        
        # Initialize components
        self.ocr = get_ensemble_ocr(
            paddleocr_lang=self.settings.paddleocr_lang,
            tesseract_lang=self.settings.tesseract_lang,
            use_gpu=self.settings.use_gpu,
            force_ocr_min_chars=self.settings.force_ocr_min_chars,
            confidence_threshold=self.settings.ocr_confidence_threshold
        )
        self.layout_analyzer = get_layout_analyzer(
            use_layoutparser=self.settings.use_layoutparser
        )
        self.table_extractor = get_table_extractor(
            engines=self.settings.table_engines,
            min_accuracy=self.settings.table_min_accuracy
        )
        self.classifier = get_classifier(
            use_llm=self.settings.use_llm_classification
        )
        self.quality_scorer = get_quality_scorer(
            min_confidence=self.settings.min_page_confidence
        )
        
        self.processor = DocumentProcessor(
            self.state_db, self.ocr, self.layout_analyzer,
            self.table_extractor, self.classifier,
            self.quality_scorer, self.output_writer
        )
        
        # Signal handling
        self._shutdown = False
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self._shutdown = True
    
    def discover_documents(self) -> list[Path]:
        """Discover all PDF files in source directories."""
        pdfs = []
        for source_dir in self.settings.source_dirs:
            if source_dir.exists():
                for pdf in source_dir.rglob("*.pdf"):
                    # Skip hidden and temp files
                    if not any(part.startswith(".") for part in pdf.parts):
                        pdfs.append(pdf)
        return sorted(pdfs)
    
    def register_documents(self, pdfs: list[Path]) -> list:
        """Register all discovered documents in state DB."""
        registered = []
        for pdf in pdfs:
            # Compute relative path from first matching source dir
            relative_path = None
            for source_dir in self.settings.source_dirs:
                try:
                    relative_path = pdf.relative_to(source_dir)
                    source_root = source_dir
                    break
                except ValueError:
                    continue
            
            if relative_path is None:
                logger.warning(f"PDF not under any source dir: {pdf}")
                continue
            
            doc_state = self.state_db.register_document(pdf, str(relative_path))
            registered.append((doc_state, source_root))
        
        return registered
    
    def run(self, resume: bool = False, retry_failed: bool = False, 
            workers: int = None, single_file: Path = None):
        """Run the ingestion pipeline."""
        
        workers = workers or self.settings.max_workers
        
        if single_file:
            # Single file mode
            pdfs = [single_file]
        else:
            pdfs = self.discover_documents()
        
        logger.info(f"Discovered {len(pdfs)} PDF files")
        
        # Register documents
        registered = self.register_documents(pdfs)
        logger.info(f"Registered {len(registered)} documents")
        
        # Determine which to process
        if retry_failed:
            to_process = [(s, r) for s, r in registered if s.status == DocumentStatus.FAILED]
            logger.info(f"Retrying {len(to_process)} failed documents")
        elif resume:
            to_process = [(s, r) for s, r in registered 
                         if s.status in (DocumentStatus.PENDING, DocumentStatus.PROCESSING)]
            logger.info(f"Resuming {len(to_process)} pending/processing documents")
        else:
            to_process = [(s, r) for s, r in registered if s.status == DocumentStatus.PENDING]
            logger.info(f"Processing {len(to_process)} new documents")
        
        if not to_process:
            logger.info("Nothing to process")
            return
        
        # Process documents
        if workers == 1:
            # Sequential (easier debugging)
            for doc_state, source_root in to_process:
                if self._shutdown:
                    break
                try:
                    self.processor.process(doc_state, source_root)
                except Exception as e:
                    logger.error(f"Failed {doc_state.source_path}: {e}")
                    self.state_db.fail_document(doc_state.document_id, str(e))
        else:
            # Parallel
            self._run_parallel(to_process, workers)
        
        # Print final stats
        stats = self.state_db.get_stats()
        logger.info(f"Pipeline complete. Stats: {stats}")
        
        # Print OCR stats
        ocr_stats = self.ocr.get_stats()
        logger.info(f"OCR Stats: {ocr_stats}")
    
    def _run_parallel(self, to_process: list, workers: int):
        """Run processing in parallel using ProcessPoolExecutor."""
        import multiprocessing
        multiprocessing.set_start_method('spawn', force=True)
        
        # Prepare worker args
        settings_dict = {
            "source_dirs": [str(d) for d in self.settings.source_dirs],
            "output_dir": str(self.settings.output_dir),
            "state_db": str(self.settings.state_db),
            "max_workers": self.settings.max_workers,
            "paddleocr_lang": self.settings.paddleocr_lang,
            "tesseract_lang": self.settings.tesseract_lang,
            "use_gpu": self.settings.use_gpu,
            "use_layoutparser": self.settings.use_layoutparser,
            "table_engines": self.settings.table_engines,
            "table_min_accuracy": self.settings.table_min_accuracy,
            "force_ocr_min_chars": self.settings.force_ocr_min_chars,
            "ocr_confidence_threshold": self.settings.ocr_confidence_threshold,
            "min_page_confidence": self.settings.min_page_confidence,
            "use_llm_classification": self.settings.use_llm_classification,
        }
        
        worker_args = []
        for doc_state, source_root in to_process:
            worker_args.append((
                {
                    "document_id": doc_state.document_id,
                    "source_path": doc_state.source_path,
                    "file_hash": doc_state.file_hash,
                    "status": doc_state.status.value,
                    "pages_total": doc_state.pages_total,
                    "pages_done": doc_state.pages_done,
                    "current_page": doc_state.current_page,
                    "error_message": doc_state.error_message,
                    "retry_count": doc_state.retry_count,
                    "output_path": doc_state.output_path,
                    "classification": doc_state.classification,
                },
                str(source_root),
                settings_dict
            ))
        
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(process_document_worker, args): args[0]["document_id"] 
                      for args in worker_args}
            
            for future in as_completed(futures):
                if self._shutdown:
                    executor.shutdown(wait=False, cancel_futures=True)
                    break
                
                doc_id = futures[future]
                try:
                    result_id, success, error = future.result()
                    if not success:
                        logger.error(f"Worker failed for {result_id}: {error}")
                except Exception as e:
                    logger.error(f"Worker exception for {doc_id}: {e}")


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AcademicOS PDF Ingestion Pipeline")
    parser.add_argument("--resume", action="store_true", help="Resume from last checkpoint")
    parser.add_argument("--retry-failed", action="store_true", help="Retry only failed documents")
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel workers")
    parser.add_argument("--file", type=Path, help="Process single file")
    parser.add_argument("--debug", action="store_true", help="Debug mode")
    parser.add_argument("--stats", action="store_true", help="Show stats and exit")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    pipeline = IngestionPipeline()
    
    if args.stats:
        stats = pipeline.state_db.get_stats()
        print(json.dumps(stats, indent=2))
        return
    
    pipeline.run(
        resume=args.resume,
        retry_failed=args.retry_failed,
        workers=args.workers,
        single_file=args.file
    )


if __name__ == "__main__":
    main()