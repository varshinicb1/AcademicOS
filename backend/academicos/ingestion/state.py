"""Ingestion State Management - Auto-resume with SQLite."""
from __future__ import annotations

import hashlib
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    NEEDS_REVIEW = "needs_review"


@dataclass
class DocumentState:
    document_id: str
    source_path: str
    file_hash: str
    status: DocumentStatus
    pages_total: int = 0
    pages_done: int = 0
    current_page: int = 0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    output_path: Optional[str] = None
    classification: Optional[str] = None


class IngestionStateDB:
    """Thread-safe SQLite state management for ingestion pipeline."""
    
    SCHEMA = """
    CREATE TABLE IF NOT EXISTS documents (
        document_id TEXT PRIMARY KEY,
        source_path TEXT NOT NULL,
        file_hash TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        pages_total INTEGER DEFAULT 0,
        pages_done INTEGER DEFAULT 0,
        current_page INTEGER DEFAULT 0,
        error_message TEXT,
        started_at TIMESTAMP,
        completed_at TIMESTAMP,
        retry_count INTEGER DEFAULT 0,
        output_path TEXT,
        classification TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_status ON documents(status);
    CREATE INDEX IF NOT EXISTS idx_source_path ON documents(source_path);
    CREATE INDEX IF NOT EXISTS idx_file_hash ON documents(file_hash);
    
    CREATE TABLE IF NOT EXISTS pages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id TEXT NOT NULL REFERENCES documents(document_id),
        page_number INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        confidence REAL,
        text_length INTEGER,
        has_tables INTEGER DEFAULT 0,
        has_figures INTEGER DEFAULT 0,
        has_equations INTEGER DEFAULT 0,
        ocr_engine TEXT,
        processing_time_ms INTEGER,
        error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(document_id, page_number)
    );
    
    CREATE INDEX IF NOT EXISTS idx_pages_doc ON pages(document_id);
    
    CREATE TABLE IF NOT EXISTS metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        metric_name TEXT NOT NULL,
        metric_value REAL NOT NULL,
        labels TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_metrics_name_time ON metrics(metric_name, timestamp);
    """
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_db()
    
    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            self._local.conn.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrency
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA busy_timeout=30000")
        return self._local.conn
    
    def _init_db(self):
        with self._get_conn() as conn:
            conn.executescript(self.SCHEMA)
            conn.commit()
    
    @contextmanager
    def transaction(self):
        conn = self._get_conn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    
    def compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file for change detection."""
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    
    def register_document(self, source_path: Path, relative_path: str) -> DocumentState:
        """Register a new document or return existing state."""
        file_hash = self.compute_file_hash(source_path)
        document_id = file_hash[:16]  # Short ID for readability
        
        with self.transaction() as conn:
            existing = conn.execute(
                "SELECT * FROM documents WHERE document_id = ?", (document_id,)
            ).fetchone()
            
            if existing:
                # Check if file changed
                if existing["file_hash"] != file_hash:
                    logger.info(f"File changed, re-processing: {relative_path}")
                    conn.execute(
                        """UPDATE documents SET 
                           file_hash = ?, status = 'pending', pages_done = 0, 
                           current_page = 0, error_message = NULL, retry_count = 0,
                           updated_at = CURRENT_TIMESTAMP
                           WHERE document_id = ?""",
                        (file_hash, document_id)
                    )
                return self._row_to_state(existing)
            
            # New document
            conn.execute(
                """INSERT INTO documents 
                   (document_id, source_path, file_hash, status)
                   VALUES (?, ?, ?, 'pending')""",
                (document_id, relative_path, file_hash)
            )
            return DocumentState(
                document_id=document_id,
                source_path=relative_path,
                file_hash=file_hash,
                status=DocumentStatus.PENDING
            )
    
    def get_document(self, document_id: str) -> Optional[DocumentState]:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE document_id = ?", (document_id,)
            ).fetchone()
            return self._row_to_state(row) if row else None
    
    def get_documents_by_status(self, *statuses: DocumentStatus) -> list[DocumentState]:
        placeholders = ",".join("?" * len(statuses))
        with self._get_conn() as conn:
            rows = conn.execute(
                f"SELECT * FROM documents WHERE status IN ({placeholders}) "
                "ORDER BY created_at",
                statuses
            ).fetchall()
            return [self._row_to_state(r) for r in rows]
    
    def start_processing(self, document_id: str, pages_total: int):
        with self.transaction() as conn:
            conn.execute(
                """UPDATE documents SET 
                   status = 'processing', pages_total = ?, current_page = 1,
                   started_at = COALESCE(started_at, CURRENT_TIMESTAMP),
                   updated_at = CURRENT_TIMESTAMP
                   WHERE document_id = ?""",
                (pages_total, document_id)
            )
    
    def update_page_progress(self, document_id: str, page_num: int, 
                             pages_done: int, confidence: float = 0.0):
        with self.transaction() as conn:
            conn.execute(
                """UPDATE documents SET 
                   pages_done = ?, current_page = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE document_id = ?""",
                (pages_done, page_num + 1, document_id)
            )
            conn.execute(
                """INSERT OR REPLACE INTO pages
                   (document_id, page_number, status, confidence, ocr_engine)
                   VALUES (?, ?, 'completed', ?, '')""",
                (document_id, page_num, confidence)
            )
    
    def complete_document(self, document_id: str, output_path: str, 
                          classification: str):
        with self.transaction() as conn:
            conn.execute(
                """UPDATE documents SET 
                   status = 'completed', pages_done = pages_total,
                   current_page = pages_total + 1, completed_at = CURRENT_TIMESTAMP,
                   output_path = ?, classification = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE document_id = ?""",
                (output_path, classification, document_id)
            )
    
    def fail_document(self, document_id: str, error: str, 
                      increment_retry: bool = True):
        with self.transaction() as conn:
            if increment_retry:
                conn.execute(
                    """UPDATE documents SET 
                       status = 'failed', error_message = ?, 
                       retry_count = retry_count + 1,
                       updated_at = CURRENT_TIMESTAMP
                       WHERE document_id = ?""",
                    (error, document_id)
                )
            else:
                conn.execute(
                    """UPDATE documents SET 
                       status = 'failed', error_message = ?,
                       updated_at = CURRENT_TIMESTAMP
                       WHERE document_id = ?""",
                    (error, document_id)
                )
    
    def skip_document(self, document_id: str, reason: str):
        with self.transaction() as conn:
            conn.execute(
                """UPDATE documents SET 
                   status = 'skipped', error_message = ?,
                   updated_at = CURRENT_TIMESTAMP
                   WHERE document_id = ?""",
                (reason, document_id)
            )
    
    def flag_for_review(self, document_id: str, reason: str):
        with self.transaction() as conn:
            conn.execute(
                """UPDATE documents SET 
                   status = 'needs_review', error_message = ?,
                   updated_at = CURRENT_TIMESTAMP
                   WHERE document_id = ?""",
                (reason, document_id)
            )
    
    def record_metric(self, name: str, value: float, labels: str = ""):
        with self.transaction() as conn:
            conn.execute(
                "INSERT INTO metrics (metric_name, metric_value, labels) VALUES (?, ?, ?)",
                (name, value, labels)
            )
    
    def get_stats(self) -> dict:
        with self._get_conn() as conn:
            stats = {}
            for status in DocumentStatus:
                count = conn.execute(
                    "SELECT COUNT(*) FROM documents WHERE status = ?", (status.value,)
                ).fetchone()[0]
                stats[status.value] = count
            
            total_pages = conn.execute(
                "SELECT SUM(pages_done) FROM documents"
            ).fetchone()[0] or 0
            stats["total_pages_processed"] = total_pages
            
            avg_conf = conn.execute(
                "SELECT AVG(confidence) FROM pages WHERE status = 'completed'"
            ).fetchone()[0]
            stats["avg_confidence"] = round(avg_conf, 3) if avg_conf else 0
            
            return stats
    
    def _row_to_state(self, row: sqlite3.Row) -> DocumentState:
        return DocumentState(
            document_id=row["document_id"],
            source_path=row["source_path"],
            file_hash=row["file_hash"],
            status=DocumentStatus(row["status"]),
            pages_total=row["pages_total"],
            pages_done=row["pages_done"],
            current_page=row["current_page"],
            error_message=row["error_message"],
            started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
            retry_count=row["retry_count"],
            output_path=row["output_path"],
            classification=row["classification"],
        )
    
    def close(self):
        if hasattr(self._local, 'conn') and self._local.conn:
            self._local.conn.close()
            self._local.conn = None


# Global instance (initialized by main)
_state_db: Optional[IngestionStateDB] = None


def get_state_db(db_path: Optional[Path] = None) -> IngestionStateDB:
    global _state_db
    if _state_db is None:
        if db_path is None:
            from ..config import settings
            db_path = settings.state_db
        _state_db = IngestionStateDB(db_path)
    return _state_db