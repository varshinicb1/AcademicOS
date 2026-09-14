# AGENTS.md — Autonomous Agent Operational Guide for AcademicOS

This document provides mandatory operational context, architectural rules, and engineering invariants for AI coding agents and human contributors working on **AcademicOS**.

---

## 1. System Vision & Architecture

AcademicOS is an evidence-grounded academic intelligence and operational operating system built over official educational corpora (CBSE curricula, NCERT textbooks, previous years' question papers, marking schemes, circulars, and bye-laws).

### Core Pillars
1. **Evidence-Grounded Ingestion & Knowledge Graph (`src/academicos/`)**:
   - Parse pipeline: Native PDF text extraction raced against OCR engines (`unlimited_ocr`, `tesseract`).
   - Provenance tracking: Every assertion, chunk, and graph node preserves provenance (`document_id`, `page_number`, `bounding_box`, `method`, `confidence`).
   - Gated acceptance: Documents with `quality_score < min_confidence` are held in `low_confidence` registry status; low-confidence material never silently enters the knowledge graph.
2. **Curriculum & Schedule Substrate (`src/academicos/curriculum/`)**:
   - Canonical hierarchy: `Board` &rarr; `AcademicYear` &rarr; `Grade` &rarr; `Subject` &rarr; `Unit` &rarr; `Chapter` &rarr; `Topic` &rarr; `Subtopic`. Complete coverage across all 5 core CBSE Class 10 subjects (Science, Mathematics, Social Science, English, Hindi Course A).
   - Operational calendar: Working days, term dates, multi-day block holidays (`Holiday.end_date`), period duration configuration, subject period allocations, and weekly timetable slots (`SubjectTimetableSlot`).
   - Human-in-the-loop content extraction: LLM extraction proposals for Topics/Subtopics are staged in `curriculum_extraction_runs`/`proposals` and require explicit principal review and approval before materialization.
   - Textbook Table-of-Contents pipeline: Deterministic TOC text parser and automated Unit/Chapter creation for custom/uploaded textbooks (`POST /books/{book_id}/toc/ingest`).
3. **Assessment Designer & Question Bank (`src/academicos/assessment/`)**:
   - Question pool (`pool.py`): Deduplicated, validated questions extracted from authentic CBSE papers with real marking scheme answers.
   - Semantic & lexical tagging: Questions mapped to canonical curriculum units, chapters, topics, and subtopics (`qmap.py`, `embedding_chapter_tagger.py`) with calibrated multi-clause recall.
   - Blueprint-driven generation: Section-by-section balance by Bloom level, question type (MCQ, VSA, SA, LA, Case-based), and difficulty, with PDF rendering.
4. **School Admin Console, Portals & Analytics**:
   - School Admin Console (`/admin`): 6 tabs — Roster, Master Calendar Grid, Coverage & Pace reporting, Drag-and-Drop Sequence Reordering, Reschedule (PUSH/ADJUST), and Calendar Setup.
   - Student Portal (`/student/schedule`): Day, Week, Month (`table_calendar`), and Overview syllabus tracking.
   - Dedicated Parent Portal (`/parent`): Child syllabus completion metrics, daily classroom attendance/lesson tracking, and Carol Dweck growth mindset parent guidance & concept scaffolding (§A8).
   - Evaluation & Mobile Scan: Multi-page student answer sheet capture, perspective rectification, Sarvam Vision OCR, itemized grading, and audit logging (`audit_log.py`).
   - Spaced repetition & mastery: FSRS (Free Spaced Repetition Scheduler) and knowledge state estimation.

---

## 2. CRITICAL: The Two Implementations Rule

**Always inspect your active working directory.** The repository contains two distinct backend trees:

| Path | Status | Guidelines |
|---|---|---|
| **`src/academicos/`** | **Active Source of Truth** (~11.5k LOC) | This is the live, tested implementation. All CLI commands, FastAPI endpoints (`api/main.py`), and Flutter client interactions bind here. Default all work here. |
| **`backend/`** | **Experimental Future Rewrite** (~4k LOC) | Scaffolded target architecture (SQLAlchemy, Alembic, MinIO, Qdrant). **Do NOT edit, refactor, or port code here** unless explicitly requested by the user. |

---

## 3. Storage, Concurrency & Persistence Invariants

### Concurrency Rules (SQLite WAL & Busy Timeout)
Under multi-threaded FastAPI execution or multi-teacher concurrent operations, raw SQLite connections can fail with `OperationalError: database is locked`. 

**Mandatory Connection Standard:**
Every SQLite connection across `src/academicos/` MUST execute the following pragmas immediately upon connecting:
```python
conn = sqlite3.connect(str(db_path), check_same_thread=False)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA busy_timeout=60000")
```

### Complete SQLite Store Inventory (17 Stores)

| Store Class | DB Path | Tables / Content | Supabase Remote Table |
|---|---|---|---|
| `SourceRegistry` | `cfg.registry_db` (`registry.db`) | `sources`, `ingestion_runs` | None (static / baked) |
| `CurriculumStore` | `cfg.data_dir / "curriculum_store.db"` | `boards`, `grades`, `subjects`, `units`, `chapters`, `topics`, `subtopics`, `holidays`, `timetable_slots`, `allocations`, `proposals` | Whole-file snapshot/restore via `SupabaseStorage` (2026-09-15 — too relational for per-table `SupabaseTable`; see `docs/deployment.md`), not per-table like the rows below |
| `UserStore` | `cfg.data_dir / "users.db"` | `users`, `sessions` | `users`, `sessions` |
| `AssessmentStore` | `cfg.data_dir / "assessments.db"` | `assessments` | `assessments` |
| `PaperStore` | `cfg.data_dir / "papers.db"` | `papers` | `papers` |
| `GradedStore` | `cfg.data_dir / "graded_evaluations.db"` | `graded_evaluations` | `graded_evaluations` |
| `PracticeStore` | `cfg.data_dir / "practice_sets.db"` | `practice_sets` | `practice_sets` |
| `AuditLogStore` | `cfg.data_dir / "audit_log.db"` | `audit_log` | `audit_log` |
| `ScanSessionStore` | `cfg.data_dir / "scan_sessions.db"` | `scan_sessions` | `scan_sessions` |
| `TemplateStore` | `cfg.data_dir / "school_templates.db"` | `school_templates` | `school_templates` |
| `KnowledgeStore` | `cfg.data_dir / "learner_models.db"` | `learner_models` | `learner_models` |
| `ChapterTagCache` | `cfg.data_dir / "chapter_tags.db"` | `chapter_tags` | None (deterministic cache) |
| `AnswerKeyStore` | `cfg.data_dir / "answer_keys.db"` | `answer_keys` | None (derived from MS) |
| `GraphStore` | `cfg.graph_db` (`graph.db`) | `nodes`, `edges` | None (corpus graph) |
| `ChunkIndex` | `cfg.index_db` (`index.db`) | `chunks`, `bm25_stats` | None (retrieval index) |
| `EventStore` | `cfg.data_dir / "events.db"` | `learner_events` | `learner_events` (2026-09-15 — was the last durability-critical store without one; also fixed a real `seq = MAX(seq)+1` race with a per-learner lock, plus a `_conn_lock` after a concurrency test reproduced `sqlite3.InterfaceError` under true concurrent access) |
| `pool.py` (read-only query) | `cfg.registry_db` | `sources` query | None (reads registry) |

### Persistence & Deployment Topologies
- **Ephemeral Deployments (Render Free Tier)**: Containers wipe local disk on spin-down or redeploy.
- **Supabase Hybrid Sync**:
  Stores managing state that must outlive restarts (`AssessmentStore`, `PaperStore`, `GradedStore`, `PracticeStore`, `AuditLogStore`, `UserStore`, `ScanSessionStore`, `TemplateStore`, `KnowledgeStore`) use `SupabaseTable` to persist JSONB payloads to Supabase PostgREST when `SUPABASE_KNOWLEDGE_URL` and `SUPABASE_KNOWLEDGE_ANON_KEY` are defined, falling back safely to local SQLite.
- **Static Assets & Corpus Databases**:
  `academicos-data/` contains pre-ingested indexes (`registry.db`, `index.db`, `graph.db`, `curriculum_store.db`, syllabus JSONs) and is copied into Docker deployment images.
- **Observability**: `GET /health/storage` reports whether Supabase is configured and (if so) currently reachable — check this instead of guessing from the Render dashboard or grepping env vars on the host.
- **School data export**: `GET /api/v1/curriculum/export` (principal-gated, school_id always from the authenticated caller) bundles the curriculum tree, assessments, paper templates, and users for one school — for backup or manual transfer to another instance. Does not yet cover `PaperStore`/`PracticeStore`/`ScanSessionStore` (no `school_id` column) or provide a restore/import path — see `docs/deployment.md`.

See `docs/deployment.md` for the full picture: the real Render CI/CD pipeline, required Supabase env vars and bucket setup, and honestly-documented known gaps (fallback-consistency across stores, remaining unguarded concurrent-access call sites).

---

## 4. Client & Offline-First Engine

The Flutter app (`frontend/`) targets Web, Windows desktop, and Android:
- **Local Engine (`frontend/lib/core/local_engine/`)**: Encrypted Hive boxes (`secure_box.dart`), local SQLite/Hive storage, on-device OCR, and client-side PDF export.
- **Synchronization (`frontend/lib/core/sync/sync_service.dart`)**: Local-first queueing with background reconciliation against the backend API with conflict resolution via `KeyedMutex`.
- **API Base Configuration**: Configured via `--dart-define=ACADEMICOS_API=https://academicos-backend.onrender.com/api/v1` or defaults to `http://localhost:8010/api/v1`.

---

## 5. Compliance & Security Standards

Before making changes touching student data, assessments, or authentication, adhere to `docs/compliance.md`:
1. **DPDP Act 2023**:
   - Verifiable consent required for minor accounts.
   - Purpose limitation: Student evaluation data must never be repurposed or leaked to external models without sanitization.
2. **CERT-In Compliance**:
   - Maintain immutable audit trails in `audit_log.py`.
   - Retain system interaction logs for at least 180 days.
3. **Authentication & Authorization**:
   - RBAC enforced across routes (`principal`, `teacher`, `student`).
   - Principal-gated endpoints: Curriculum edits, extraction approvals, user provisioning.
   - School-scoped isolation: Every query must filter strictly by `school_id`.

---

## 6. Development, Testing & Verification Protocol

### Virtual Environment Execution
Always execute commands within the dedicated virtual environment:
```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m pytest tests -q
```

### Verification Gates
1. **Never mock away live functionality** in integration tests.
2. **Run route inventory tests** (`tests/test_route_inventory.py`) to ensure API contract integrity.
3. **Check status transitions**: Never reset source or curriculum states unconditionally on conflict or re-discovery.
