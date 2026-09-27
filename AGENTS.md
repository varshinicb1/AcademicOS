# AGENTS.md — Autonomous Agent Operational Guide for AcademicOS

This document provides mandatory operational context, architectural rules, and engineering invariants for AI coding agents and human contributors working on **AcademicOS**.

**Before writing code, read [`HANDOVER.md`](HANDOVER.md), then [`docs/PRD.md`](docs/PRD.md)** (whose scope is superseded by `docs/REQUIREMENTS.md`, but whose non-goals and constraints still bind). This file tells you *how*
the system is built; the PRD tells you *what it is for, who uses it, and what it is
not*. Several questions that look like engineering decisions here are product
decisions that are still **open** — the PRD §12 lists them, and §7 lists the
non-goals that are binding. Building the wrong thing correctly is the most
expensive failure mode in this repo.

**Then read [`HANDOVER.md`](HANDOVER.md) and [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md)** (v3,
2026-09-27: grades 1-10, web console, teacher app, student app, question bank API; it supersedes the
PRD's scope decisions), **and [`docs/agent-workflow.md`](docs/agent-workflow.md)** — how work gets done
here with several agents at once: the worktrees and who owns which files, the rules
that stop one session destroying another's work, the gates a commit must pass, the
question-bank pipeline order, and how to release and verify. What is live is the
v2 **Web app, classes 6-10**, on GCP (`docs/product-scorecard.md`); what to build next is v3.

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
| **`src/academicos/`** | **Active Source of Truth**, by far the larger tree | This is the live, tested implementation. All CLI commands, FastAPI endpoints (`api/main.py`), and Flutter client interactions bind here. Default all work here. |
| **`backend/`** | **Experimental Future Rewrite**, a fraction of the other tree's size | Scaffolded target architecture (SQLAlchemy, Alembic, MinIO, Qdrant). See `backend/README.md`. **Do NOT edit, refactor, or port code here** unless explicitly requested by the user. |

A LOC count here goes stale within days in a repo this active — check with `find src/academicos -name "*.py" | xargs wc -l` (or the equivalent for `backend/`) if you need a real number, rather than trusting a figure written down in prose.

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

### Complete SQLite Store Inventory (19 stores)

**Corrected 2026-09-18 against the code.** The table below used to say 17 and to
list flat `.db` filenames. Both were wrong, and the errors were the misleading
kind — an agent looking for `registry.db` finds nothing, because the real path is
`registry/registry.sqlite`, and two stores were missing entirely.

Four things to know before reading it:

- **The filename pattern is `<dir>/<name>.sqlite`**, not a flat `.db`. The
  exceptions are `answer_keys.db` and `assessment/consents.db`, which really do
  end in `.db`. Several paths are injected by the caller rather than built by the
  store, and those are marked *injected*.
- **`KnowledgeStore` is not a SQLite store** and its row is removed below: it
  writes per-student JSON files under `knowledge/` plus Supabase. It was listed
  here for years as though it were a table-backed store, which is why
  `learner_models` appears in the Supabase column with no local table.
- **`pool.py` is not a store** either; it is a read-only query against the
  registry, and it has its own comment in the code. It was a row in this table.
- **Two stores were missing**: `ApiKeyStore` and `ConsentStore`. Consent is
  DPDP-critical, so an inventory that omits it is worse than incomplete.

Paths below verified against the constructors; run
`grep -rn "sqlite3.connect" src/academicos` to re-check rather than trusting
this table, which will drift like every other list in prose.

| Store Class | DB Path | Tables / Content | Supabase Remote Table |
|---|---|---|---|
| `SourceRegistry` | `cfg.registry_db` (`registry/registry.sqlite`) | `sources`, `ingestion_runs` | None (static / baked) |
| `CurriculumStore` | `curriculum/curriculum.sqlite` | `boards`, `grades`, `subjects`, `units`, `chapters`, `topics`, `subtopics`, `holidays`, `timetable_slots`, `allocations`, `proposals` | Whole-file snapshot/restore via `SupabaseStorage` (2026-09-15 — too relational for per-table `SupabaseTable`; see `docs/deployment.md`), not per-table like the rows below |
| `UserStore` | `users/users.sqlite` | `users`, `sessions` | `users`, `sessions` |
| `AssessmentStore` | `assessments/assessments.sqlite` | `assessments` | `assessments` |
| `PaperStore` | `assessments/papers.sqlite` | `papers` | `papers` |
| `GradedStore` | `assessments/graded.sqlite` | `graded_evaluations` | `graded_evaluations` |
| `PracticeStore` | `assessments/practice.sqlite` | `practice_sets` | `practice_sets` |
| `AuditLogStore` | `audit/audit_log.sqlite` | `audit_log` | `audit_log` |
| `ScanSessionStore` | `sessions.sqlite` (data root) | `scan_sessions` | `scan_sessions` |
| `TemplateStore` | `templates/templates.sqlite` | `school_templates` | `school_templates` |
| `ChapterTagCache` | `assessment/chapter_tags.sqlite` | `chapter_tags` | None (deterministic cache) |
| `AnswerKeyStore` | `answer_keys.db` (data root) | `answer_keys` | None (derived from MS) |
| `GraphStore` | `cfg.graph_db` (`graph/graph.sqlite`) | `nodes`, `edges` | None (corpus graph) |
| `ChunkIndex` | `cfg.index_db` (`index/index.sqlite`) | `chunks`, `bm25_stats` | None (retrieval index) |
| `EventStore` | `events/events.sqlite` | `learner_events` | `learner_events` (2026-09-15 — was the last durability-critical store without one; also fixed a real `seq = MAX(seq)+1` race with a per-learner lock, plus a `_conn_lock` after a concurrency test reproduced `sqlite3.InterfaceError` under true concurrent access) |
| `ApiKeyStore` | *injected* (`assessment/api_keys.sqlite` in practice) | `api_keys`, `api_key_usage` | None (SHA-256 at rest) |
| `ConsentStore` | `assessment/consents.db` | `parental_consents` | `parental_consents` |
| `QuestionBankStore` | *injected* | `question_versions`, `question_audit` | None (append-only) |
| `AnswerKeyIndex` | `answer_keys.db` (read-only URI) | `answer_keys` read | None (derived from MS) |

### Persistence & Deployment Topologies
- **Ephemeral Deployments**: Containers wipe local disk on spin-down or redeploy. This is true of both Render (free tier) and Cloud Run.
- **Durable backend selection (2026-09-16)**: Every store's remote handle now comes from `postgres_kv.durable_table(name)` instead of constructing `SupabaseTable` directly. It prefers **Cloud SQL Postgres** when `ACOS_POSTGRES_HOST`/`ACOS_POSTGRES_DB`/`ACOS_POSTGRES_USER` are set, and otherwise falls back to Supabase, which itself disables cleanly when its env vars are absent. `PostgresUnavailable` subclasses `SupabaseUnavailable`, so every existing `except` clause and `api/main.py`'s 503 handler keep working unchanged. `GET /health/storage` reports `durability_backend`.
- **Cloud SQL**: `deploy/gcp/schema.sql` defines all 11 durable tables; connection is via Cloud Run's `/cloudsql/<conn>` Unix socket, pooled and bounded (`ACOS_POSTGRES_POOL_MAX`, default 10) because `--concurrency=40` would otherwise exhaust a small instance. Migration off Supabase: `scripts/migrate_supabase_to_cloudsql.py`.
- **Supabase Hybrid Sync**: `SupabaseTable` persists JSONB payloads to Supabase PostgREST when `SUPABASE_KNOWLEDGE_URL` and `SUPABASE_KNOWLEDGE_ANON_KEY` are defined. Still the backend for **blob** storage (`SupabaseStorage`: scan media, curriculum snapshots) — that path is not yet on GCS.
- **Static Assets & Corpus Databases**:
  `academicos-data/` contains pre-ingested indexes (`registry.db`, `index.db`, `graph.db`, `curriculum_store.db`, syllabus JSONs) and is copied into Docker deployment images.
- **Observability**: `GET /health/storage` reports whether Supabase is configured and (if so) currently reachable — check this instead of guessing from the Render dashboard or grepping env vars on the host.
- **School data export**: `GET /api/v1/curriculum/export` (principal-gated, school_id always from the authenticated caller) bundles the curriculum tree, assessments, paper templates, and users for one school — for backup or manual transfer to another instance. Does not yet cover `PaperStore`/`PracticeStore`/`ScanSessionStore` (no `school_id` column) or provide a restore/import path — see `docs/deployment.md`.

See **[`docs/PRODUCTS_AND_RELEASES.md`](docs/PRODUCTS_AND_RELEASES.md)** for
the full picture. It is the source of truth for "which thing are we talking
about": two client sub-products (offline **Mobile**, cloud **Web**) and two
backend releases (**Render**, and **GCP** — the live Web release since
2026-09-22; that file predates the go-live) that coexist from one codebase. Then:

- `docs/deployment.md` — the Render release: CI/CD pipeline, Supabase env vars
  and bucket setup, known gaps (fallback consistency across stores, remaining
  unguarded concurrent-access call sites).
- `docs/gcp-deployment.md` — the GCP release: Cloud Run/Cloud SQL/GCS,
  cutover, costs, and the blob-storage item that keeps it off pure GCP.
- **`docs/REQUIREMENTS_BY_LAYER.md`** — every requirement split into what the
  backend must deliver vs what the frontend must deliver, with a
  verification-depth table. Read it before assuming a feature works: "the code
  exists and its tests pass" is a different claim from "a user has walked
  through it", and today only one area has been.

---

## 4. Client & Offline-First Engine

`frontend/` is **one Flutter codebase serving two distinct sub-products** —
do not reason about "the app" as a single thing (see
`docs/PRODUCTS_AND_RELEASES.md`):

| Sub-product | Build | Talks to a backend? | Uses |
|---|---|---|---|
| **AcademicOS Web** | `flutter build web` (default) | Yes — every action | `PillarApi`, `AuthApi`, `ConsentApi`, `CurriculumApi`, `ApiClient` |
| **AcademicOS Mobile** | `flutter build apk --dart-define=ACADEMICOS_OFFLINE=true` | **No** — on-device only | `LocalPillarApi`, `LocalApiClient` |

`offlineMode` in `core/di/service_locator.dart` performs the swap; everything
above it (repositories, use cases, all 26 page widgets across 29 routes) is shared. Two rules follow:

1. A change to any API route must be mirrored by hand into `local_api_client.dart`
   / `local_pillar_api.dart`. The offline engine cannot detect drift itself, and
   its methods **throw** `OfflineUnsupportedException` rather than returning an
   empty result — never revert one to `=> []`; a silent empty answer was read by
   teachers as "nothing to show" (see `tests/test_frontend_backend_contract.py`).
2. `ACADEMICOS_OFFLINE` must not leak into the Web build. The Web client talks
   HTTP; pointing it at the local engine silently disables the backend.

- **Local Engine (`frontend/lib/core/local_engine/`)**: Encrypted Hive boxes (`secure_box.dart`), local SQLite/Hive storage, on-device OCR, and client-side PDF export. Mobile-only.
- **Synchronization (`frontend/lib/core/sync/sync_service.dart`)**: Local-first queueing with background reconciliation against the backend API with conflict resolution via `KeyedMutex`. Web-only.
- **API Base Configuration**: `--dart-define=ACADEMICOS_API=…`. Absolute for the
  Render release (`https://academicos-backend.onrender.com/api/v1`) and for the
  live GCP release, whose Web bundle is on Firebase Hosting and whose API is on
  Cloud Run (`https://academicos-backend-2eskom55ta-el.a.run.app/api/v1`; see
  `docs/deploy-by-hand.md`). Defaults to `http://localhost:8010/api/v1`.

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
