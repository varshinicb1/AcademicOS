"""Output Writer - JSONL and Parquet output with manifest."""
from __future__ import annotations

import orjson
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import asdict

from ..classification import ClassificationResult, DocumentType
from ..quality import DocumentQuality
from ..ocr import OCREngineType

logger = logging.getLogger(__name__)


class OutputWriter:
    """Write processed documents to JSONL and maintain manifest."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # JSONL file for streaming
        self.jsonl_path = self.output_dir / "documents.jsonl"
        self.manifest_path = self.output_dir / "manifest.json"
        
        # Initialize manifest
        self.manifest = self._load_manifest()
    
    def _load_manifest(self) -> dict:
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, "rb") as f:
                    return orjson.loads(f.read())
            except Exception:
                pass
        return {
            "created_at": datetime.now().isoformat(),
            "version": "1.0",
            "documents": [],
            "stats": {
                "total_documents": 0,
                "total_pages": 0,
                "by_type": {},
                "by_quality": {}
            }
        }
    
    def _save_manifest(self):
        self.manifest["updated_at"] = datetime.now().isoformat()
        with open(self.manifest_path, "wb") as f:
            f.write(orjson.dumps(self.manifest, option=orjson.OPT_INDENT_2))
    
    def write_document(self, 
                       document_id: str,
                       source_path: str,
                       file_size: int,
                       page_count: int,
                       classification: ClassificationResult,
                       pages: list,
                       quality: DocumentQuality) -> str:
        """Write a single document to JSONL and update manifest."""
        
        # Build document record
        doc_record = {
            "document_id": document_id,
            "source_path": source_path,
            "file_size": file_size,
            "page_count": page_count,
            "classification": {
                "type": classification.doc_type.value,
                "confidence": classification.confidence,
                "metadata": classification.metadata,
                "matched_rules": classification.matched_rules
            },
            "quality": {
                "overall_score": quality.overall_score,
                "level": quality.level.value,
                "page_count": quality.page_count,
                "pages_scored": quality.pages_scored,
                "summary": quality.summary
            },
            "pages": [
                {
                    "page_number": p.page_number,
                    "text": p.text,
                    "markdown": p.markdown,
                    "ocr_confidence": p.ocr_confidence,
                    "ocr_engine": p.ocr_engine.value,
                    "tables": [
                        {
                            "engine": t.engine.value,
                            "bbox": t.bbox,
                            "rows": t.rows,
                            "cols": t.cols,
                            "markdown": t.markdown,
                            "csv": t.csv,
                            "confidence": t.confidence
                        }
                        for t in p.tables
                    ],
                    "figures": p.figures,
                    "equations": p.equations,
                    "headings": p.headings,
                    "qa_pairs": p.qa_pairs,
                    "processing_time_ms": p.processing_time_ms,
                    "confidence": p.confidence
                }
                for p in pages
            ],
            "processed_at": datetime.now().isoformat(),
            "version": "1.0"
        }
        
        # Append to JSONL
        with open(self.jsonl_path, "ab") as f:
            f.write(orjson.dumps(doc_record) + b"\n")
        
        # Update manifest
        self.manifest["documents"].append({
            "document_id": document_id,
            "source_path": source_path,
            "page_count": page_count,
            "type": classification.doc_type.value,
            "quality_score": quality.overall_score,
            "quality_level": quality.level.value,
            "processed_at": datetime.now().isoformat()
        })
        
        # Update stats
        self.manifest["stats"]["total_documents"] += 1
        self.manifest["stats"]["total_pages"] += page_count
        self.manifest["stats"]["by_type"][classification.doc_type.value] = \
            self.manifest["stats"]["by_type"].get(classification.doc_type.value, 0) + 1
        self.manifest["stats"]["by_quality"][quality.level.value] = \
            self.manifest["stats"]["by_quality"].get(quality.level.value, 0) + 1
        
        self._save_manifest()
        
        logger.info(f"Written document {document_id} ({page_count} pages, "
                   f"quality: {quality.overall_score:.2f})")
        
        return str(self.jsonl_path)
    
    def get_manifest(self) -> dict:
        return self.manifest


def get_output_writer(output_dir: Path) -> OutputWriter:
    """Factory for output writer."""
    return OutputWriter(output_dir)