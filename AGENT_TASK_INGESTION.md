# Agent Task: Production PDF Ingestion Pipeline (Free/Local Only)

## Objective
Build a complete, production-grade PDF ingestion pipeline for 1,120+ CBSE/NCERT PDFs using **only free, local tools**. No external APIs, no paid services. Must support auto-resume, monitoring, and incremental runs.

## Input Data
```
Source roots:
- C:\Users\varsh\OneDrive\Documents\Sarvam\ncert-dataset\  (textbooks)
- C:\Users\varsh\OneDrive\Documents\Sarvam\cbse-dataset\  (question papers, curriculum, bylaws, model answers)

Total: ~1,120 PDFs
Types: textbooks, question papers, marking schemes, curriculum docs, bylaws, model answers
```

## Required Output
Structured JSONL per document:
```json
{
  "document_id": "sha256-of-file",
  "source_path": "relative/path.pdf",
  "file_size": 1234567,
  "page_count": 45,
  "classification": "textbook|question_paper|marking_scheme|curriculum|bylaw|model_answer",
  "metadata": {
    "board": "CBSE",
    "grade": 10,
    "subject": "Mathematics",
    "year": 2025,
    "language": "en|hi",
    "title": "Extracted from first page"
  },
  "pages": [
    {
      "page_number": 1,
      "text": "full extracted text",
      "markdown": "structured markdown with headings",
      "tables": [{"bbox": [x1,y1,x2,y2], "markdown": "|A|B|\n|1|2|", "csv": "A,B\n1,2"}],
      "figures": [{"bbox": [x1,y1,x2,y2], "caption": "Figure 1: ...", "type": "diagram|chart|photo"}],
      "equations": [{"bbox": [x1,y1,x2,y2], "latex": "\\frac{a}{b}", "omml": "..."}],
      "headings": [{"level": 1, "text": "Chapter 1", "bbox": [...]}],
      "qa_pairs": [{"question": "...", "answer": "...", "marks": 5, "bloom": "apply"}],
      "confidence": 0.92
    }
  ],
  "processing": {
    "ocr_engine": "paddleocr|tesseract|pdfplumber",
    "layout_engine": "pdfplumber|layoutparser",
    "duration_seconds": 45.2,
    "timestamp": "2026-01-15T10:30:00Z",
    "version": "1.0"
  }
}
```

---

## Technical Requirements

### 1. Free OCR Stack (pick ensemble)
| Engine | Strength | Install |
|--------|----------|---------|
| **PaddleOCR** | Best for Indic + tables | `pip install paddlepaddle paddleocr` |
| **Tesseract** | Fast fallback | `choco install tesseract` + `pip install pytesseract` |
| **pdfplumber** | Native PDF text + tables | `pip install pdfplumber` |
| **PyMuPDF (fitz)** | Fast text + images | `pip install pymupdf` |
| **pdfminer.six** | Layout analysis | `pip install pdfminer.six` |
| **LayoutParser** | Deep learning layout | `pip install layoutparser[pdfplumber]` + detectron2 |
| **table-transformer** | Table structure | `pip install transformers torch` |

**Strategy**: Try native text extraction first (pdfplumber/PyMuPDF). If page text < 50 chars OR has scanned regions → OCR with PaddleOCR. Use Tesseract as final fallback.

### 2. Auto-Resume Architecture
```python
# State tracking (SQLite)
CREATE TABLE ingestion_state (
    document_id TEXT PRIMARY KEY,
    source_path TEXT NOT NULL,
    file_hash TEXT NOT NULL,           -- SHA256 for change detection
    status TEXT NOT NULL,              -- pending | processing | completed | failed | skipped
    pages_total INTEGER,
    pages_done INTEGER,
    current_page INTEGER,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    retry_count INTEGER DEFAULT 0,
    output_path TEXT
);

-- On startup: SELECT * WHERE status IN ('pending','processing') ORDER BY started_at
-- Resume from current_page
```

### 3. Monitoring & Observability
- **Progress bar**: tqdm with pages/sec, ETA
- **Structured logging**: JSONL to `logs/ingestion_YYYYMMDD.jsonl`
- **Metrics**: Prometheus pushgateway or local SQLite metrics table
- **Health endpoint**: HTTP `/health` showing queue depth, workers, throughput
- **Dashboard**: Optional Streamlit/Gradio for real-time view

### 4. Parallel Processing
```python
# Worker pool (adjust for RAM/CPU)
MAX_WORKERS = min(4, cpu_count())  # OCR is memory-heavy
QUEUE = multiprocessing.JoinableQueue()
# Each worker: pull path -> process -> write JSONL -> update state
```

### 5. Quality Gates (auto-skip/flag)
- Page confidence < 0.6 → flag for review
- Zero text extracted → mark `needs_manual_review`
- Table extraction failed → store raw image bbox for later
- File > 500MB → chunk by page ranges

---

## Deliverables

### File Structure
```
backend/
├── ingestion/
│   ├── __init__.py
│   ├── main.py                 # CLI entry: python -m ingestion --resume --workers 4
│   ├── state.py                # SQLite state management
│   ├── ocr/
│   │   ├── __init__.py
│   │   ├── paddleocr_engine.py
│   │   ├── tesseract_engine.py
│   │   ├── ensemble.py         # Auto-select best engine per page
│   │   └── preprocess.py       # Deskew, denoise, binarize
│   ├── layout/
│   │   ├── __init__.py
│   │   ├── pdfplumber_extractor.py
│   │   ├── layoutparser_engine.py
│   │   └── structure.py        # Headings, reading order, regions
│   ├── tables/
│   │   ├── __init__.py
│   │   ├── pdfplumber_tables.py
│   │   ├── camelot_engine.py
│   │   └── transformer_engine.py
│   ├── equations/
│   │   ├── __init__.py
│   │   ├── detect.py           # Find math regions
│   │   └── latex_ocr.py        # Pix2Struct/Unimernet if available
│   ├── classification/
│   │   ├── __init__.py
│   │   ├── rules.py            # Filename + content heuristics
│   │   └── llm_fallback.py     # Optional local LLM (Ollama)
│   ├── quality/
│   │   ├── __init__.py
│   │   ├── scorer.py           # Per-page confidence
│   │   └── validators.py       # Schema validation
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── metrics.py          # SQLite metrics + optional Prometheus
│   │   ├── logger.py           # JSONL structured logging
│   │   └── dashboard.py        # Optional Streamlit
│   └── output/
│       ├── __init__.py
│       ├── writer.py           # JSONL + Parquet
│       └── manifest.py         # Manifest file per batch
├── tests/
│   ├── test_ocr.py
│   ├── test_tables.py
│   └── test_resume.py
└── requirements.txt
```

### CLI Interface
```bash
# First run
python -m ingestion --source "C:\data\ncert-dataset" "C:\data\cbse-dataset" \
    --output "C:\data\processed" --workers 4

# Resume (auto-detects incomplete)
python -m ingestion --resume --workers 4

# Re-process failed only
python -m ingestion --retry-failed --workers 2

# Single file debug
python -m ingestion --file "path/to/pdf" --debug

# Monitor (separate terminal)
python -m ingestion.monitoring.dashboard --port 8501
```

---

## Acceptance Criteria

| Criterion | Target |
|-----------|--------|
| **Success rate** | > 95% pages extracted (text + structure) |
| **Table extraction** | > 80% tables recovered as markdown/CSV |
| **Equation detection** | > 70% math regions found |
| **Resume correctness** | Zero duplicate pages, zero skipped pages on resume |
| **Speed** | ~2-5 sec/page average (CPU only) |
| **Memory** | < 8GB RAM with 4 workers |
| **Idempotency** | Re-running produces identical output (deterministic) |
| **Monitoring** | Real-time progress visible via logs + optional dashboard |

---

## Handoff Notes for Next Agent

1. **Start with `pdfplumber` + `PyMuPDF`** for native text — covers 70% of NCERT textbooks (born-digital PDFs)
2. **PaddleOCR** for scanned pages — best open-source for Hindi/English mixed
3. **LayoutParser** (with `lp://PubLayNet` model) for region detection — headings, tables, figures
4. **State DB first** — build `ingestion/state.py` before any extraction logic
5. **Test on 10 PDFs first** — validate schema, resume, quality gates
6. **Output to JSONL + Parquet** — Parquet for analytics, JSONL for streaming
7. **No external deps** — everything runs offline after `pip install`

---

## Quick Start Commands (for the agent)

```bash
# 1. Create venv
python -m venv .venv && .venv\Scripts\activate

# 2. Core deps
pip install pdfplumber pymupdf paddleocr paddlepaddle pytesseract \
    layoutparser pdfminer.six camelot-py[cv2] \
    tqdm loguru sqlite-utils

# 3. System deps (Windows)
# choco install tesseract poppler

# 4. Verify
python -c "import pdfplumber, fitz, paddleocr; print('OK')"
```

**The agent should deliver: working `python -m ingestion --resume` that processes all 1,120 PDFs overnight with zero manual intervention.**