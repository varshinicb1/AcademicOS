# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Before you change anything, read [`docs/agent-workflow.md`](docs/agent-workflow.md).**
Several Claude sessions work here at once, each in its own worktree, and ship to a
live product. That file covers the worktrees and who owns what, the rules for not
destroying each other's work, the gates, the question-bank pipeline order, and how
to release — including the hand deploy (`docs/deploy-by-hand.md`) while CI cannot run.

## Project

**Start with [`docs/PRD.md`](docs/PRD.md)** — what the product is for, who uses it,
what is in scope, what is explicitly out of scope, and which decisions are still
open. It is the entry point this repo was missing; the sections below assume you
have read it.

AcademicOS — an evidence-grounded knowledge graph + retrieval + reasoning substrate over the
CBSE/NCERT corpus (question papers, marking schemes, model answers, curricula, circulars,
bye-laws). The active platform comprises a FastAPI backend (`src/academicos/`) and one Flutter
codebase (`frontend/`) that ships as two sub-products — a cloud **Web** client and a standalone
offline **Android** app. **The first sellable release is the Web app, classes 6-10**; the
Android app and classes 11-12 are out of it (user decisions, 2026-09-22 and 2026-09-23). The
Web release runs on **GCP** (Cloud Run backend, Firebase Hosting at vidyuthlabs.web.app), live
since 2026-09-22; the older **Render** release is described in `docs/deployment.md`. See
`docs/PRODUCTS_AND_RELEASES.md`, which predates the GCP go-live, and `docs/product-scorecard.md`
for how the product is measured.

**There are two parallel Python implementations — know which one you're in:**

- `src/academicos/` — the actual, working implementation, by far the larger of the two trees.
  Installed as the `academicos` package (`pyproject.toml` at repo root, `pip install -e .`). Has
  a CLI (`python -m academicos.cli`) and a large, passing test suite, and is what `README.md`
  documents. **Treat this as the source of truth unless told otherwise.**
- `backend/academicos/` + `backend/ingestion/` — a newer, mostly-scaffolded rewrite (see
  `backend/README.md`) following the target architecture in `docs/architecture.md` (separate
  `backend/pyproject.toml`, different dependency set — Qdrant, MinIO, SQLAlchemy/Alembic,
  LayoutLMv3, etc.). Many modules here are stubs/interfaces, not finished logic. Only work here
  if the task is explicitly about the `backend/` rewrite or `docs/architecture.md`.

**On LOC and test counts in this file:** deliberately not pinned to a number. This repo is
active enough that a specific count (LOC, tests passing) goes stale within days — the PRD's own
§11 records one that was wrong within the same working session it was written in. Run
`pytest tests -q` or `find src/academicos -name "*.py" | xargs wc -l` for the real current
number rather than trusting a figure written down in prose.

Don't casually port fixes between the two trees — they have diverging schemas and package layouts.

`frontend/` is one Flutter codebase (clean-architecture layout: `data/`, `domain/`,
`presentation/`, `core/local_engine/`) that ships as **two sub-products**:

- **Web** (default build) — a thin client; every action is an HTTP call to a backend release.
- **Mobile** (`--dart-define=ACADEMICOS_OFFLINE=true`) — a standalone Android app that runs the
  paper-generation and evaluation logic on device and **never contacts a backend**. Uses
  `LocalApiClient`/`LocalPillarApi` plus a corpus bundled into the APK.

The swap happens in `core/di/service_locator.dart`; every repository, use case and screen above
it is shared. Two rules follow: any change to an API route must be mirrored by hand into the local
clients (nothing detects that drift), and `ACADEMICOS_OFFLINE` must never leak into a Web build.
Windows desktop is a development/packaging target, not a deployed release.

## Compliance — read before touching student data

**Before adding or changing anything that touches student PII, assessment content, grading, or
a new data store: read `docs/compliance.md` and check its "before you ship" boxes.** This covers
DPDP Act 2023 (verifiable parental consent for minors, no secondary use of data, breach
notification), CERT-In's 6-hour breach-reporting rule and 6-month log-retention requirement.
Audit logging (`src/academicos/assessment/audit_log.py`) is implemented with immutable entries
and grade change tracking. Always scope operations by `school_id` and enforce role gates
(`principal`, `teacher`, `student`).

## Commands

### `src/academicos` (primary implementation)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .            # core (pymupdf, pydantic, numpy, spacy)
pip install -e ".[api]"     # + FastAPI server
pip install -e ".[dev]"     # + pytest / httpx (needed to run the test suite)
pip install -e ".[gcs]"     # + GCS mirror
pip install -e ".[retrieval]"  # + sentence-transformers/numpy
python -m pip install en_core_web_md@https://github.com/explosion/spacy-models/releases/download/en_core_web_md-3.8.0/en_core_web_md-3.8.0-py3-none-any.whl
    # required by extract/local_ie.py / graph/curriculum.py (concept-profile
    # --method rule, OpenIE). `pip install -e .` pulls in spacy itself but
    # NOT a model — spacy.load() fails at runtime, not import time, so this
    # is easy to miss until you actually run `concept-profile` or `openie`.
```

Pipeline stages, run in order:

```powershell
python -m academicos.cli ingest        # discover + validate + register corpus files
python -m academicos.cli parse         # ensemble parse over registered sources
python -m academicos.cli extract       # extract academic objects + chunk
python -m academicos.cli build-graph   # build knowledge graph from extracted objects
python -m academicos.cli index         # (re)build retrieval index
python -m academicos.cli search "photosynthesis light reaction"
python -m academicos.cli serve --port 8000
python -m academicos.cli stats
python -m academicos.cli sync-gcs      # push artifacts to GCS (if config.sync_enabled)
```

Tests (smoke test builds a tiny corpus in a temp dir and runs the whole pipeline):

```powershell
pytest tests/
pytest tests/test_fsrs.py             # single file
pytest tests/test_fsrs.py::test_name  # single test
```

Runtime config lives in `config/config.toml` (corpus_root, gcs_bucket, parse_priority, LLM
provider/model, retrieval thresholds). Overridable via `ACOS_DATA_ROOT`, `ACOS_CORPUS_ROOT`,
`ACOS_GCS_BUCKET`, `ACOS_GCS_PREFIX`, `ACOS_SYNC_ENABLED`, `ACOS_VLM_DEVICE`.

**The LLM key is not stored in `config/config.toml`.** An earlier version of this file had
a live Groq key committed in plaintext; it was rotated after being caught in git history, and
the key now lives in `config/secrets.env` (gitignored) as `ACOS_LLM_API_KEY`, or as a real env
var in deployment. Never put a real key back in `config.toml` — it's a committed file.

### `backend/` (in-progress rewrite)

```powershell
cd backend
pip install -e .
pip install -e ".[dev]"     # pytest, ruff, mypy, pre-commit
pytest tests/               # testpaths = tests/, files test_*.py
ruff check .                # line-length 100, target py311
mypy .
```

The standalone ingestion CLI described in `AGENT_TASK_INGESTION.md` targets `backend/ingestion/`
(`python -m ingestion --resume --workers 4`, state tracked in a SQLite `ingestion_state` table
for auto-resume).

### `frontend/` (Flutter)

```powershell
cd frontend
flutter pub get
flutter analyze
flutter test
flutter build windows --release
flutter build appbundle --release
```

## Architecture (`src/academicos`)

Pipeline stages are separate CLI subcommands, each reading the previous stage's output via the
registry/store rather than being called as library functions in sequence:

1. **`ingest/`** — discovers PDFs under `corpus_root`, computes checksums, registers them in
   `SourceRegistry` (SQLite-backed, at `cfg.registry_db`).
2. **`parse/`** — ensemble parsing per `config.toml`'s `parse_priority` (`pdf_native` →
   `unlimited_ocr` → `tesseract`), gated by `min_confidence` (fixed 2026-09-11: previously
   loaded from config but never read anywhere — every parse was accepted regardless of
   `quality_score`). The ensemble already races every configured provider and picks the best
   result per page, so there's no "next method" to retry — a result whose `quality_score` falls
   below `min_confidence` is registered `status="low_confidence"` instead of `"parsed"` (the
   parse output is still written to disk, nothing is lost). `cmd_extract`/`cmd_build_graph` only
   ever consume `"parsed"`/`"extracted"` sources, so a bad OCR result no longer silently reaches
   the knowledge graph. `python -m academicos.cli parse --force` accepts every parse regardless
   of score, e.g. once a human has reviewed the `low_confidence` backlog
   (`registry.by_status("low_confidence")`, or `cli stats`'s `by_status` breakdown) and decided a
   given document is fine as-is.
3. **`extract/`** — pulls academic objects (chapters, topics, questions, answer schemes, etc.)
   out of parsed documents and chunks them for retrieval.
4. **`graph/`** — `GraphBuilder` constructs the knowledge graph from extracted objects into
   `GraphStore`; nodes/edges carry provenance (source doc/page/bbox/confidence).
5. **`retrieval/`** — `ChunkIndex` + `HybridRetriever` combine vector/keyword search over the
   chunk index for `search`/`serve`.
6. **`agents/`** — LLM-driven agents (OpenIE extraction, Self-RAG-style critic) that call out to
   the LLM provider configured in `config.toml` (`llm_base_url`/`llm_model`).
7. **`curriculum/`** — `CurriculumStore` manages the operational hierarchy (`Board` → `AcademicYear`
   → `Grade` → `Subject` → `Unit` → `Chapter` → `Topic` → `Subtopic`), operational calendars (multi-day
   block holidays via `Holiday.end_date`), subject period allocations, and weekly timetable slots (`SubjectTimetableSlot`).
   Includes LLM decomposition proposals (`extraction.py`) requiring principal review/approval.
8. **`assessment/`** — `AssessmentStore`, question pool (`pool.py`), blueprinting, subtopic tagging (`qmap.py`),
   paper rendering (`paper_store.py`), answer keys (`answer_key.py`), mobile answer-sheet scanning (`mobile_scan.py`),
   and rubric evaluation (`graded_store.py`).
9. **`algorithms/`** — learner-facing models independent of the ingestion pipeline: FSRS spaced
   repetition (`fsrs.py`, `fsrs_fit.py`), mastery/confidence/misconception models, study planner,
   daily loop, motivation/attention/habit models. These operate on `EventStore`
   (`storage/event_store.py`) interaction records, not on the document graph directly.
10. **`api/main.py`** — FastAPI app exposing all modules via REST endpoints.

### Storage & Concurrency Invariant

All SQLite stores (17 total across `src/academicos/`) MUST enable WAL mode and a 60-second busy timeout:
```python
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA busy_timeout=60000")
```
Never remove these pragmas. They protect against `database is locked` under multi-threaded requests
*between separate connections/processes* — they do NOT make one `sqlite3.Connection` safe for two
threads to call `execute()` on it concurrently (`check_same_thread=False` only disables Python's own
check, not a real thread-safety guarantee). `EventStore` additionally guards every local-SQLite call
site with a `_conn_lock` after a concurrency test reproduced `sqlite3.InterfaceError` under genuine
concurrent access (2026-09-15) — most other stores don't have this yet, a known gap, see
`docs/deployment.md`.

The flat single-object stores (`AssessmentStore`, `PaperStore`, `PracticeStore`, `GradedStore`,
`ScanSessionStore`, `TemplateStore`, `UserStore`, `AuditLog`, `EventStore`) resolve their remote
handle through **one factory, `postgres_kv.durable_table(name)`** — do not construct
`SupabaseTable` directly in a store. It prefers **Cloud SQL Postgres** when `ACOS_POSTGRES_HOST`/
`_DB`/`_USER` are set (the GCP release), otherwise falls back to **Supabase** when
`SUPABASE_KNOWLEDGE_URL`/`SUPABASE_KNOWLEDGE_ANON_KEY` are set (the Render release), otherwise
local SQLite. `PostgresUnavailable` subclasses `SupabaseUnavailable`, so existing `except` clauses
and the app-level 503 handler keep working. Known inconsistency, unchanged: only `AssessmentStore`
and `EventStore` catch a live failure and fall back gracefully — the others let it propagate.
`CurriculumStore` (18 relational tables, `PRAGMA foreign_keys=ON`) still uses whole-file
snapshot/restore via `SupabaseStorage` rather than per-table wrapping, since per-table REST would
lose FK integrity across two storage layers.

**Blob storage is not yet on GCS** — scan media and curriculum snapshots still go through
`SupabaseStorage`, which is why the GCP release cannot yet drop its Supabase credentials.
Check `GET /health/storage` for which backend is actually active (`durability_backend`) rather than
guessing. Full picture: `docs/deployment.md` (Render) and `docs/gcp-deployment.md` (GCP).

External capability providers (Composio for app actions, Sarvam for LLM calls) sit behind
`integrations/base.py`/`llm/base.py` interfaces and the existing `agents/base.py` `Tool` ABC —
the Brain never imports their SDKs directly and must stay runnable offline. See
`docs/provider-architecture.md`.

Design principles carried over from `docs/architecture.md` and `README.md`:
- **Evidence-first**: no fact without provenance (doc/page/bbox/method/confidence) — this
  applies to both the `src/` and `backend/` trees.
- **Deterministic core, generative surface**: the v0.1 pipeline (`src/academicos`) runs fully
  offline without any LLM calls except the optional OpenIE/critic agents.
- Full target ontology (60+ node types, temporal versioning, board/school overlays) is
  documented in `docs/architecture.md` but only partially implemented in `src/academicos/graph/`;
  check the actual `NodeType`/`EdgeType` enums in code before assuming a doc'd type exists.

## Data layout

- `ncert-dataset/` and `cbse-dataset/` (siblings of `AcademicOS/`, at
  `C:\Users\varsh\OneDrive\Documents\Sarvam\`) hold the raw source PDFs — textbooks, question
  papers, marking schemes, curricula, circulars, bye-laws (~1,120 files total). These are data,
  not code — don't expect them to follow any particular internal structure beyond the top-level
  category folders.
- `cbse-model-answers/` holds model-answer PDFs, also raw data.
- Processed/derived artifacts land under `academicos-data/` and `config.documents_dir`, not in
  the dataset folders themselves.
