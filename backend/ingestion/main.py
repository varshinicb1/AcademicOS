"""Main ingestion pipeline entry point."""
from __future__ import annotations

import argparse
import logging
import multiprocessing
import os
import signal
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .state import IngestionStateDB, IngestionStatus, DocumentState

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"ingestion_{datetime.now().strftime('%Y%m%d')}.log"),
    ],
)
logger = logging.getLogger(__name__)


@dataclass
class IngestionConfig:
    """Configuration for the ingestion pipeline."""
    source_paths: list[Path] = field(default_factory=list)
    output_dir: Path = Path("output")
    workers: int = min(4, multiprocessing.cpu_count())
    resume: bool = False
    retry_failed: bool = False
    debug: bool = False
    batch_size: int = 100
    db_path: Path = Path("ingestion_state.db")
    temp_dir: Path = Path("temp_ingest")


@dataclass
class IngestionResult:
    """Result of ingesting a single document."""
    document_id: str
    source_path: str
    success: bool
    pages_processed: int
    error_message: Optional[str] = None
    output_path: Optional[str] = None
    duration_seconds: float = 0.0


class IngestionPipeline:
    """Main pipeline for ingesting PDF documents."""

    def __init__(self, config: IngestionConfig):
        self.config = config
        self.state_db = IngestionStateDB(config.db_path)
        self._running = True
        self._stats = {"total": 0, "success": 0, "failed": 0}
        
        # Setup temp directory
        self.config.temp_dir.mkdir(parents=True, exist_ok=True)
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

    def handle_signal(self, signum: int, frame: Any) -> None:
        """Handle interrupt signals gracefully."""
        logger.info(f"Received signal {signum}, stopping gracefully...")
        self._running = False

    def discover_all_documents(self) -> list[DocumentState]:
        """Discover all documents from source paths."""
        logger.info("Discovering documents...")
        
        all_docs = []
        
        # First, discover loose PDFs
        for source_path in self.config.source_paths:
            if source_path.exists():
                docs = self.state_db.discover_documents([source_path])
                all_docs.extend(docs)
                logger.info(f"  Found {len(docs)} loose PDFs in {source_path}")
        
        # Then discover PDFs in ZIP files
        for source_path in self.config.source_paths:
            if source_path.exists():
                docs = self.state_db.discover_from_zips([source_path])
                all_docs.extend(docs)
                logger.info(f"  Found {len(docs)} PDFs in ZIPs in {source_path}")
        
        logger.info(f"Total documents discovered: {len(all_docs)}")
        return all_docs

    def process_document(self, document: DocumentState) -> IngestionResult:
        """Process a single document."""
        start_time = time.time()
        
        try:
            # Update state to processing
            self.state_db.update_document(
                document.document_id,
                status=IngestionStatus.PROCESSING,
                started_at=datetime.now(),
            )
            
            # Extract the document
            result = self._extract_document(document)
            
            if result.success:
                # Mark as completed
                self.state_db.mark_completed(
                    document.document_id,
                    output_path=result.output_path,
                )
                self._stats["success"] += 1
            else:
                # Mark as failed
                self.state_db.mark_failed(
                    document.document_id,
                    error_message=result.error_message or "Unknown error",
                )
                self._stats["failed"] += 1
            
            self._stats["total"] += 1
            
            return IngestionResult(
                document_id=document.document_id,
                source_path=document.source_path,
                success=result.success,
                pages_processed=result.pages_processed,
                error_message=result.error_message,
                output_path=result.output_path,
                duration_seconds=time.time() - start_time,
            )
            
        except Exception as e:
            logger.error(f"Error processing {document.source_path}: {e}")
            self.state_db.mark_failed(
                document.document_id,
                error_message=str(e),
            )
            self._stats["failed"] += 1
            self._stats["total"] += 1
            return IngestionResult(
                document_id=document.document_id,
                source_path=document.source_path,
                success=False,
                pages_processed=0,
                error_message=str(e),
                duration_seconds=time.time() - start_time,
            )

    def _extract_document(self, document: DocumentState) -> IngestionResult:
        """Extract content from a document."""
        from pathlib import Path
        import json
        
        source_path = Path(document.source_path)
        
        # Handle ZIP files
        if document.source_path.startswith("zip://"):
            return self._extract_from_zip(document)
        
        # Check if file exists
        if not source_path.exists():
            return IngestionResult(
                document_id=document.document_id,
                source_path=document.source_path,
                success=False,
                pages_processed=0,
                error_message=f"File not found: {source_path}",
            )
        
        # Extract using the best available method
        try:
            # Try pdfplumber first
            extracted_data = self._extract_with_pdfplumber(source_path)
            
            if not extracted_data or len(extracted_data.get("pages", [])) == 0:
                # Fallback to PyMuPDF
                extracted_data = self._extract_with_pymupdf(source_path)
            
            if not extracted_data or len(extracted_data.get("pages", [])) == 0:
                # Final fallback to OCR (would need PaddleOCR/Tesseract)
                extracted_data = self._extract_with_ocr(source_path)
            
            if extracted_data:
                # Write output
                output_path = self.config.output_dir / f"{document.document_id}.jsonl"
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(extracted_data, f, ensure_ascii=False, indent=2)
                
                return IngestionResult(
                    document_id=document.document_id,
                    source_path=document.source_path,
                    success=True,
                    pages_processed=len(extracted_data.get("pages", [])),
                    output_path=str(output_path),
                )
            else:
                return IngestionResult(
                    document_id=document.document_id,
                    source_path=document.source_path,
                    success=False,
                    pages_processed=0,
                    error_message="Failed to extract content from document",
                )
                
        except Exception as e:
            logger.error(f"Extraction failed for {source_path}: {e}")
            return IngestionResult(
                document_id=document.document_id,
                source_path=document.source_path,
                success=False,
                pages_processed=0,
                error_message=str(e),
            )

    def _extract_from_zip(self, document: DocumentState) -> IngestionResult:
        """Extract a PDF from a ZIP file."""
        import zipfile
        from pathlib import Path
        
        # Parse the virtual path
        # Format: zip:///path/to/file.zip#member_name
        path_parts = document.source_path[6:].split("#", 1)
        if len(path_parts) != 2:
            return IngestionResult(
                document_id=document.document_id,
                source_path=document.source_path,
                success=False,
                pages_processed=0,
                error_message="Invalid ZIP path format",
            )
        
        zip_path = Path(path_parts[0])
        member_name = path_parts[1]
        
        if not zip_path.exists():
            return IngestionResult(
                document_id=document.document_id,
                source_path=document.source_path,
                success=False,
                pages_processed=0,
                error_message=f"ZIP file not found: {zip_path}",
            )
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                if member_name not in z.namelist():
                    return IngestionResult(
                        document_id=document.document_id,
                        source_path=document.source_path,
                        success=False,
                        pages_processed=0,
                        error_message=f"Member {member_name} not found in {zip_path}",
                    )
                
                # Extract to temp file
                with z.open(member_name) as zf:
                    temp_path = self.config.temp_dir / f"{document.document_id}.pdf"
                    with open(temp_path, "wb") as tf:
                        tf.write(zf.read())
                
                # Process the temp file
                result = self._extract_document_from_path(temp_path, document)
                
                # Cleanup
                temp_path.unlink(missing_ok=True)
                
                return result
        except Exception as e:
            logger.error(f"Failed to extract from ZIP {zip_path}#{member_name}: {e}")
            return IngestionResult(
                document_id=document.document_id,
                source_path=document.source_path,
                success=False,
                pages_processed=0,
                error_message=str(e),
            )

    def _extract_document_from_path(self, path: Path, document: DocumentState) -> IngestionResult:
        """Extract a document from a file path."""
        try:
            extracted_data = self._extract_with_pdfplumber(path)
            
            if not extracted_data or len(extracted_data.get("pages", [])) == 0:
                extracted_data = self._extract_with_pymupdf(path)
            
            if extracted_data:
                output_path = self.config.output_dir / f"{document.document_id}.jsonl"
                import json
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(extracted_data, f, ensure_ascii=False, indent=2)
                
                return IngestionResult(
                    document_id=document.document_id,
                    source_path=document.source_path,
                    success=True,
                    pages_processed=len(extracted_data.get("pages", [])),
                    output_path=str(output_path),
                )
            else:
                return IngestionResult(
                    document_id=document.document_id,
                    source_path=document.source_path,
                    success=False,
                    pages_processed=0,
                    error_message="Failed to extract content",
                )
        except Exception as e:
            return IngestionResult(
                document_id=document.document_id,
                source_path=document.source_path,
                success=False,
                pages_processed=0,
                error_message=str(e),
            )

    def _extract_with_pdfplumber(self, path: Path) -> Optional[dict]:
        """Extract text and tables using pdfplumber."""
        try:
            import pdfplumber
            
            with pdfplumber.open(path) as pdf:
                pages = []
                for i, page in enumerate(pdf.pages):
                    page_data = self._extract_page_with_pdfplumber(page, i + 1)
                    pages.append(page_data)
                
                return {
                    "document_id": path.stem,
                    "source_path": str(path),
                    "file_size": path.stat().st_size,
                    "page_count": len(pages),
                    "classification": self._infer_classification_from_path(path),
                    "metadata": self._extract_metadata_from_path(path),
                    "pages": pages,
                    "processing": {
                        "ocr_engine": "pdfplumber",
                        "layout_engine": "pdfplumber",
                        "timestamp": datetime.now().isoformat(),
                        "version": "1.0",
                    },
                }
        except Exception as e:
            logger.debug(f"pdfplumber extraction failed for {path}: {e}")
            return None

    def _extract_page_with_pdfplumber(self, page: Any, page_num: int) -> dict:
        """Extract a single page using pdfplumber."""
        try:
            text = page.extract_text() or ""
            
            # Extract tables
            tables = []
            for table in page.extract_tables():
                table_data = {
                    "bbox": [
                        float(table.bbox[0]) if table.bbox else 0,
                        float(table.bbox[1]) if table.bbox else 0,
                        float(table.bbox[2]) if table.bbox else 0,
                        float(table.bbox[3]) if table.bbox else 0,
                    ],
                    "markdown": self._table_to_markdown(table),
                    "csv": self._table_to_csv(table),
                }
                tables.append(table_data)
            
            # Extract headings (simple heuristic based on font size)
            headings = []
            if hasattr(page, 'chars'):
                # Group chars by line
                lines = []
                current_line = []
                for c in page.chars:
                    if current_line and abs(c['y0'] - current_line[-1]['y0']) > 5:
                        lines.append(current_line)
                        current_line = []
                    current_line.append(c)
                if current_line:
                    lines.append(current_line)
                
                for line in lines:
                    if line:
                        avg_size = sum(c['size'] for c in line) / len(line)
                        text = ''.join(c['char'] for c in line).strip()
                        if avg_size > 12 and text:
                            level = self._estimate_heading_level(avg_size)
                            headings.append({
                                "level": level,
                                "text": text,
                                "bbox": [
                                    min(c['x0'] for c in line),
                                    min(c['y0'] for c in line),
                                    max(c['x1'] for c in line),
                                    max(c['y1'] for c in line),
                                ],
                            })
            
            # Confidence based on text length
            confidence = min(1.0, len(text) / 500) if len(text) < 5000 else 1.0
            
            return {
                "page_number": page_num,
                "text": text,
                "markdown": self._text_to_markdown(text, headings),
                "tables": tables,
                "figures": [],
                "equations": [],
                "headings": headings,
                "qa_pairs": [],
                "confidence": round(confidence, 2),
            }
        except Exception as e:
            logger.debug(f"Failed to extract page {page_num}: {e}")
            return {
                "page_number": page_num,
                "text": "",
                "markdown": "",
                "tables": [],
                "figures": [],
                "equations": [],
                "headings": [],
                "qa_pairs": [],
                "confidence": 0.0,
            }

    def _extract_with_pymupdf(self, path: Path) -> Optional[dict]:
        """Extract text and images using PyMuPDF."""
        try:
            import fitz
            
            doc = fitz.open(path)
            pages = []
            
            for i, page in enumerate(doc):
                page_data = self._extract_page_with_pymupdf(page, i + 1)
                pages.append(page_data)
            
            return {
                "document_id": path.stem,
                "source_path": str(path),
                "file_size": path.stat().st_size,
                "page_count": len(pages),
                "classification": self._infer_classification_from_path(path),
                "metadata": self._extract_metadata_from_path(path),
                "pages": pages,
                "processing": {
                    "ocr_engine": "pymupdf",
                    "layout_engine": "pymupdf",
                    "timestamp": datetime.now().isoformat(),
                    "version": "1.0",
                },
            }
        except Exception as e:
            logger.debug(f"PyMuPDF extraction failed for {path}: {e}")
            return None

    def _extract_page_with_pymupdf(self, page: Any, page_num: int) -> dict:
        """Extract a single page using PyMuPDF."""
        try:
            text = page.get_text() or ""
            
            # Get blocks for structure
            blocks = page.get_text("dict")["blocks"]
            
            tables = []
            headings = []
            
            for block in blocks:
                if block["type"] == 0:  # Text block
                    # Check if it's a heading based on font size
                    if "lines" in block:
                        for line in block["lines"]:
                            if "spans" in line:
                                for span in line["spans"]:
                                    if span["size"] > 12:
                                        headings.append({
                                            "level": self._estimate_heading_level(span["size"]),
                                            "text": span["text"].strip(),
                                            "bbox": span["bbox"],
                                        })
                elif block["type"] == 1:  # Image block
                    # Could be a table or figure
                    pass
            
            confidence = min(1.0, len(text) / 500) if len(text) < 5000 else 1.0
            
            return {
                "page_number": page_num,
                "text": text,
                "markdown": self._text_to_markdown(text, headings),
                "tables": tables,
                "figures": [],
                "equations": [],
                "headings": headings,
                "qa_pairs": [],
                "confidence": round(confidence, 2),
            }
        except Exception as e:
            logger.debug(f"Failed to extract page {page_num} with PyMuPDF: {e}")
            return {
                "page_number": page_num,
                "text": "",
                "markdown": "",
                "tables": [],
                "figures": [],
                "equations": [],
                "headings": [],
                "qa_pairs": [],
                "confidence": 0.0,
            }

    def _extract_with_ocr(self, path: Path) -> Optional[dict]:
        """Extract text using OCR (PaddleOCR or Tesseract)."""
        # This is a placeholder - would need actual OCR implementation
        # For now, try to use Tesseract if available
        try:
            import pytesseract
            from PIL import Image
            import io
            import fitz
            
            doc = fitz.open(path)
            pages = []
            
            for i, page in enumerate(doc):
                # Get page as image
                pix = page.get_pixmap(dpi=300)
                img = Image.open(io.BytesIO(pix.tobytes()))
                
                # Run OCR
                text = pytesseract.image_to_string(img)
                
                pages.append({
                    "page_number": i + 1,
                    "text": text,
                    "markdown": text,
                    "tables": [],
                    "figures": [],
                    "equations": [],
                    "headings": [],
                    "qa_pairs": [],
                    "confidence": 0.8,  # OCR confidence
                })
            
            return {
                "document_id": path.stem,
                "source_path": str(path),
                "file_size": path.stat().st_size,
                "page_count": len(pages),
                "classification": self._infer_classification_from_path(path),
                "metadata": self._extract_metadata_from_path(path),
                "pages": pages,
                "processing": {
                    "ocr_engine": "tesseract",
                    "layout_engine": "none",
                    "timestamp": datetime.now().isoformat(),
                    "version": "1.0",
                },
            }
        except Exception as e:
            logger.debug(f"OCR extraction failed for {path}: {e}")
            return None

    def _table_to_markdown(self, table: list[list[str]]) -> str:
        """Convert a table to markdown format."""
        if not table:
            return ""
        
        lines = []
        for row in table:
            lines.append("|" + "|".join(str(cell).strip() for cell in row) + "|")
        
        if len(lines) > 1:
            # Add separator
            lines.insert(1, "|" + "|".join("-" for _ in lines[0].split("|")[1:-1]) + "|")
        
        return "\n".join(lines)

    def _table_to_csv(self, table: list[list[str]]) -> str:
        """Convert a table to CSV format."""
        if not table:
            return ""
        
        lines = []
        for row in table:
            lines.append(",".join(str(cell).strip() for cell in row))
        
        return "\n".join(lines)

    def _text_to_markdown(self, text: str, headings: list[dict]) -> str:
        """Convert text to markdown with headings."""
        # Simple implementation - just add heading markers
        markdown = text
        
        for heading in sorted(headings, key=lambda h: h["bbox"][1]):  # Sort by y position
            level = heading["level"]
            prefix = "#" * level + " "
            markdown = markdown.replace(heading["text"], f"\n{prefix}{heading['text']}\n")
        
        return markdown

    def _estimate_heading_level(self, font_size: float) -> int:
        """Estimate heading level from font size."""
        if font_size >= 20:
            return 1
        elif font_size >= 16:
            return 2
        elif font_size >= 14:
            return 3
        elif font_size >= 12:
            return 4
        return 6

    def _infer_classification_from_path(self, path: Path) -> str:
        """Infer document classification from file path."""
        path_str = str(path).lower()
        
        if any(word in path_str for word in ["textbook", "ncert"]):
            return "textbook"
        elif any(word in path_str for word in ["question", "qp", "paper"]):
            return "question_paper"
        elif any(word in path_str for word in ["marking", "ms", "scheme"]):
            return "marking_scheme"
        elif any(word in path_str for word in ["curriculum", "syllabus"]):
            return "curriculum"
        elif any(word in path_str for word in ["bylaw", "bye-law"]):
            return "bylaw"
        elif any(word in path_str for word in ["model", "answer", "ma"]):
            return "model_answer"
        return "unknown"

    def _extract_metadata_from_path(self, path: Path) -> dict:
        """Extract metadata from file path."""
        import re
        
        path_str = str(path)
        metadata = {"board": "CBSE", "language": "en"}
        
        # Extract grade
        grade_match = re.search(r'(?:class|grade|x|xi|xii|1[0-2])', path_str, re.IGNORECASE)
        if grade_match:
            grade = grade_match.group(0).upper()
            if grade in ["X", "XI", "XII"]:
                metadata["grade"] = grade
            elif grade.isdigit():
                metadata["grade"] = int(grade)
        
        # Extract subject
        subject_match = re.search(r'(?:math|science|english|hindi|physics|chemistry|biology|social)', path_str, re.IGNORECASE)
        if subject_match:
            metadata["subject"] = subject_match.group(0).title()
        
        # Extract year
        year_match = re.search(r'(?:202[0-9]|201[0-9])', path_str)
        if year_match:
            metadata["year"] = int(year_match.group(0))
        
        return metadata

    def run(self) -> None:
        """Run the ingestion pipeline."""
        # Setup signal handling
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)
        
        logger.info("Starting ingestion pipeline...")
        logger.info(f"Configuration: workers={self.config.workers}, output={self.config.output_dir}")
        
        # Discover documents if not resuming
        if not self.config.resume:
            self.discover_all_documents()
        
        # Get stats
        stats = self.state_db.get_stats()
        logger.info(f"Pipeline stats: {stats}")
        
        # Process documents
        if self.config.retry_failed:
            documents = self.state_db.get_failed_documents(self.config.batch_size * self.config.workers)
            logger.info(f"Retrying {len(documents)} failed documents")
        else:
            documents = self.state_db.get_pending_documents(self.config.batch_size * self.config.workers)
            logger.info(f"Processing {len(documents)} pending documents")
        
        if not documents:
            logger.info("No documents to process")
            return
        
        # Process in parallel
        self._process_batch(documents)
        
        logger.info("Ingestion pipeline completed")
        logger.info(f"Results: {self._stats}")

    def _process_batch(self, documents: list[DocumentState]) -> None:
        """Process a batch of documents."""
        # For now, process sequentially (parallel processing would need more work)
        # In production, we'd use ProcessPoolExecutor
        
        for i, doc in enumerate(documents):
            if not self._running:
                break
            
            logger.info(f"Processing [{i+1}/{len(documents)}] {doc.source_path}")
            
            result = self.process_document(doc)
            
            if result.success:
                logger.info(f"  ✓ Success: {result.pages_processed} pages")
            else:
                logger.error(f"  ✗ Failed: {result.error_message}")
            
            # Update progress
            self._stats["total"] += 1
            if result.success:
                self._stats["success"] += 1
            else:
                self._stats["failed"] += 1


def parse_args() -> IngestionConfig:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="AcademicOS PDF Ingestion Pipeline")
    
    parser.add_argument(
        "--source",
        type=Path,
        nargs="+",
        default=[],
        help="Source paths containing PDFs to ingest",
    )
    
    parser.add_argument(
        "--output",
        type=Path,
        default="output",
        help="Output directory for extracted data",
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=min(4, multiprocessing.cpu_count()),
        help="Number of worker processes",
    )
    
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from previous state",
    )
    
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Retry only failed documents",
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )
    
    parser.add_argument(
        "--db-path",
        type=Path,
        default="ingestion_state.db",
        help="Path to the state database",
    )
    
    parser.add_argument(
        "--temp-dir",
        type=Path,
        default="temp_ingest",
        help="Temporary directory for extraction",
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for processing",
    )
    
    args = parser.parse_args()
    
    # If no source paths provided, use defaults
    if not args.source:
        # Default source paths
        default_sources = [
            Path(r"C:\Users\varsh\OneDrive\Documents\Sarvam\ncert-dataset"),
            Path(r"C:\Users\varsh\OneDrive\Documents\Sarvam\cbse-dataset"),
            Path(r"C:\Users\varsh\OneDrive\Documents\Sarvam\cbse-model-answers"),
        ]
        args.source = [s for s in default_sources if s.exists()]
        if not args.source:
            logger.warning("No source paths provided and no default sources found")
    
    return IngestionConfig(
        source_paths=args.source,
        output_dir=args.output,
        workers=args.workers,
        resume=args.resume,
        retry_failed=args.retry_failed,
        debug=args.debug,
        batch_size=args.batch_size,
        db_path=args.db_path,
        temp_dir=args.temp_dir,
    )


def main() -> None:
    """Main entry point."""
    config = parse_args()
    
    if config.debug:
        logger.setLevel(logging.DEBUG)
    
    pipeline = IngestionPipeline(config)
    pipeline.run()


if __name__ == "__main__":
    main()
