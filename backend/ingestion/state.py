"""State tracking for PDF ingestion pipeline with auto-resume support."""
from __future__ import annotations

import hashlib
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Iterator, Optional


class IngestionStatus(Enum):
    """Status of a document in the ingestion pipeline."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class DocumentState:
    """Represents the state of a document being ingested."""
    document_id: str
    source_path: str
    file_hash: str
    status: IngestionStatus
    pages_total: int
    pages_done: int
    current_page: int
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    retry_count: int
    output_path: Optional[str]
    classification: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> DocumentState:
        return cls(
            document_id=row["document_id"],
            source_path=row["source_path"],
            file_hash=row["file_hash"],
            status=IngestionStatus(row["status"]),
            pages_total=row["pages_total"],
            pages_done=row["pages_done"],
            current_page=row["current_page"],
            error_message=row["error_message"],
            started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
            retry_count=row["retry_count"],
            output_path=row["output_path"],
        )


@dataclass
class PipelineStats:
    """Aggregated statistics for the ingestion pipeline."""
    total_documents: int
    pending: int
    processing: int
    completed: int
    failed: int
    skipped: int
    total_pages: int
    processed_pages: int


class IngestionStateDB:
    """SQLite-based state tracking for the ingestion pipeline."""

    def __init__(self, db_path: str | Path = "ingestion_state.db"):
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the database with required tables."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ingestion_state (
                    document_id TEXT PRIMARY KEY,
                    source_path TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    status TEXT NOT NULL,
                    pages_total INTEGER DEFAULT 0,
                    pages_done INTEGER DEFAULT 0,
                    current_page INTEGER DEFAULT 0,
                    error_message TEXT,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    retry_count INTEGER DEFAULT 0,
                    output_path TEXT,
                    classification TEXT,
                    metadata_json TEXT
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_status ON ingestion_state(status)
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ingestion_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    document_id TEXT,
                    page_number INTEGER
                )
            """)
            
            conn.commit()

    @contextmanager
    def _get_connection(self) -> Iterator[sqlite3.Connection]:
        """Get a database connection with proper context management."""
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def add_document(
        self,
        source_path: str | Path,
        classification: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> DocumentState:
        """Add a new document to the ingestion queue."""
        source_path = Path(source_path)
        
        # Calculate file hash
        file_hash = self._calculate_file_hash(source_path)
        document_id = hashlib.sha256(file_hash.encode()).hexdigest()
        
        # Get page count
        pages_total = self._get_page_count(source_path)
        
        now = datetime.now()
        
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO ingestion_state (
                    document_id, source_path, file_hash, status,
                    pages_total, pages_done, current_page, started_at,
                    retry_count, classification, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                document_id,
                str(source_path),
                file_hash,
                IngestionStatus.PENDING.value,
                pages_total,
                0,
                0,
                now.isoformat(),
                0,
                classification,
                self._serialize_metadata(metadata),
            ))
            
            state = DocumentState(
                document_id=document_id,
                source_path=str(source_path),
                file_hash=file_hash,
                status=IngestionStatus.PENDING,
                pages_total=pages_total,
                pages_done=0,
                current_page=0,
                error_message=None,
                started_at=now,
                completed_at=None,
                retry_count=0,
                output_path=None,
                classification=classification,
                metadata=metadata or {},
            )
            return state

    def get_document(self, document_id: str) -> Optional[DocumentState]:
        """Get the state of a specific document."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM ingestion_state WHERE document_id = ?",
                (document_id,)
            ).fetchone()
            
            if row is None:
                return None
            
            metadata = self._deserialize_metadata(row["metadata_json"])
            state = DocumentState.from_row(row)
            state.metadata = metadata
            return state

    def update_document(
        self,
        document_id: str,
        **kwargs: Any,
    ) -> None:
        """Update the state of a document."""
        if not kwargs:
            return
            
        # Build update query
        updates = []
        values = []
        
        for key, value in kwargs.items():
            if hasattr(DocumentState, key):
                if key == "metadata":
                    updates.append(f"metadata_json = ?")
                    values.append(self._serialize_metadata(value))
                elif key == "status" and isinstance(value, IngestionStatus):
                    updates.append(f"status = ?")
                    values.append(value.value)
                else:
                    updates.append(f"{key} = ?")
                    values.append(value)
            elif key == "completed_at" and value is not None:
                updates.append(f"completed_at = ?")
                values.append(value.isoformat() if isinstance(value, datetime) else value)
        
        if not updates:
            return
        
        values.append(document_id)
        
        with self._get_connection() as conn:
            conn.execute(
                f"UPDATE ingestion_state SET {', '.join(updates)} WHERE document_id = ?",
                values,
            )

    def get_pending_documents(self, limit: int = 100) -> list[DocumentState]:
        """Get documents that are pending processing."""
        return self._get_documents_by_status(IngestionStatus.PENDING, limit)

    def get_processing_documents(self, limit: int = 100) -> list[DocumentState]:
        """Get documents that are currently being processed."""
        return self._get_documents_by_status(IngestionStatus.PROCESSING, limit)

    def get_failed_documents(self, limit: int = 100) -> list[DocumentState]:
        """Get documents that failed processing."""
        return self._get_documents_by_status(IngestionStatus.FAILED, limit)

    def _get_documents_by_status(
        self, status: IngestionStatus, limit: int
    ) -> list[DocumentState]:
        """Get documents by their status."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM ingestion_state WHERE status = ? ORDER BY started_at ASC LIMIT ?",
                (status.value, limit),
            ).fetchall()
            
            documents = []
            for row in rows:
                state = DocumentState.from_row(row)
                state.metadata = self._deserialize_metadata(row["metadata_json"])
                documents.append(state)
            
            return documents

    def get_stats(self) -> PipelineStats:
        """Get aggregated statistics for the pipeline."""
        with self._get_connection() as conn:
            # Count by status
            row = conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'processing' THEN 1 ELSE 0 END) as processing,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END) as skipped,
                    SUM(pages_total) as total_pages,
                    SUM(pages_done) as processed_pages
                FROM ingestion_state
            """).fetchone()
            
            return PipelineStats(
                total_documents=row["total"],
                pending=row["pending"],
                processing=row["processing"],
                completed=row["completed"],
                failed=row["failed"],
                skipped=row["skipped"],
                total_pages=row["total_pages"] or 0,
                processed_pages=row["processed_pages"] or 0,
            )

    def mark_completed(self, document_id: str, output_path: Optional[str] = None) -> None:
        """Mark a document as completed."""
        self.update_document(
            document_id,
            status=IngestionStatus.COMPLETED,
            current_page=0,
            pages_done=0,  # Will be updated properly
            completed_at=datetime.now(),
            output_path=output_path,
        )

    def mark_failed(self, document_id: str, error_message: str) -> None:
        """Mark a document as failed."""
        with self._get_connection() as conn:
            # Increment retry count
            row = conn.execute(
                "SELECT retry_count FROM ingestion_state WHERE document_id = ?",
                (document_id,)
            ).fetchone()
            
            retry_count = row["retry_count"] + 1 if row else 1
            
            conn.execute(
                """
                UPDATE ingestion_state 
                SET status = ?, error_message = ?, retry_count = ?, started_at = NULL
                WHERE document_id = ?
                """,
                (IngestionStatus.FAILED.value, error_message, retry_count, document_id),
            )

    def reset_failed(self, document_id: Optional[str] = None) -> int:
        """Reset failed documents to pending. Returns number of documents reset."""
        with self._get_connection() as conn:
            if document_id:
                conn.execute(
                    "UPDATE ingestion_state SET status = ?, error_message = NULL, retry_count = 0 WHERE document_id = ?",
                    (IngestionStatus.PENDING.value, document_id),
                )
                return conn.total_changes
            else:
                conn.execute(
                    "UPDATE ingestion_state SET status = ?, error_message = NULL, retry_count = 0 WHERE status = ?",
                    (IngestionStatus.PENDING.value, IngestionStatus.FAILED.value),
                )
                return conn.total_changes

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096 * 1024), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _get_page_count(self, file_path: Path) -> int:
        """Get the number of pages in a PDF file."""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            return len(doc)
        except Exception:
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    return len(pdf.pages)
            except Exception:
                return 0

    def _serialize_metadata(self, metadata: Optional[dict]) -> str:
        """Serialize metadata dict to JSON string."""
        if metadata is None:
            return "{}"
        import json
        return json.dumps(metadata, default=str)

    def _deserialize_metadata(self, metadata_json: Optional[str]) -> dict:
        """Deserialize metadata JSON string to dict."""
        if metadata_json is None:
            return {}
        import json
        try:
            return json.loads(metadata_json)
        except json.JSONDecodeError:
            return {}

    def document_exists(self, source_path: str | Path) -> Optional[str]:
        """Check if a document already exists in the database. Returns document_id if found."""
        source_path = Path(source_path)
        file_hash = self._calculate_file_hash(source_path)
        document_id = hashlib.sha256(file_hash.encode()).hexdigest()
        
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT document_id FROM ingestion_state WHERE file_hash = ?",
                (file_hash,)
            ).fetchone()
            
            if row:
                return row["document_id"]
            return None

    def add_existing_document(self, source_path: str | Path) -> Optional[DocumentState]:
        """Add a document if it doesn't exist, or return existing state."""
        existing_id = self.document_exists(source_path)
        if existing_id:
            return self.get_document(existing_id)
        
        source_path = Path(source_path)
        # Try to infer classification from path
        classification = self._infer_classification(source_path)
        return self.add_document(source_path, classification=classification)

    def _infer_classification(self, path: Path) -> Optional[str]:
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
        return None

    def discover_documents(
        self,
        source_paths: list[str | Path],
        recursive: bool = True,
        patterns: list[str] = ["*.pdf"],
    ) -> list[DocumentState]:
        """Discover and add all PDF documents from source paths."""
        from pathlib import Path
        
        documents = []
        for source_path in source_paths:
            source_path = Path(source_path)
            
            if source_path.is_file() and any(source_path.match(p) for p in ["*.pdf"]):
                doc = self.add_existing_document(source_path)
                if doc:
                    documents.append(doc)
            elif source_path.is_dir():
                if recursive:
                    for pdf_file in source_path.rglob("*.pdf"):
                        doc = self.add_existing_document(pdf_file)
                        if doc:
                            documents.append(doc)
                else:
                    for pdf_file in source_path.glob("*.pdf"):
                        doc = self.add_existing_document(pdf_file)
                        if doc:
                            documents.append(doc)
        
        return documents

    def discover_from_zips(
        self,
        source_paths: list[str | Path],
        extract_to: Optional[str | Path] = None,
    ) -> list[DocumentState]:
        """Discover PDFs inside ZIP files and add them to the queue."""
        import zipfile
        import tempfile
        from pathlib import Path
        
        documents = []
        extract_to = Path(extract_to) if extract_to else None
        
        for source_path in source_paths:
            source_path = Path(source_path)
            
            if source_path.is_file() and source_path.suffix.lower() == ".zip":
                self._process_zip_file(source_path, extract_to, documents)
            elif source_path.is_dir():
                for zip_file in source_path.rglob("*.zip"):
                    self._process_zip_file(zip_file, extract_to, documents)
        
        return documents

    def _process_zip_file(
        self,
        zip_path: Path,
        extract_to: Optional[Path],
        documents: list[DocumentState],
    ) -> None:
        """Process a single ZIP file and add its contents to the queue."""
        import zipfile
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                # First pass: just add to queue
                for file_info in z.infolist():
                    if file_info.filename.lower().endswith('.pdf'):
                        # Create a virtual path for the ZIP member
                        virtual_path = f"zip://{zip_path}#{file_info.filename}"
                        doc = self.add_existing_document(virtual_path)
                        if doc:
                            documents.append(doc)
        except Exception as e:
            print(f"Warning: Could not process {zip_path}: {e}")

    def cleanup(self) -> None:
        """Clean up database connections."""
        pass  # SQLite handles this automatically
