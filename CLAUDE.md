# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

AcademicOS — an evidence-grounded knowledge graph + retrieval + reasoning substrate over the
CBSE/NCERT corpus (question papers, marking schemes, model answers, curricula, circulars,
bye-laws). Long-term target is a FastAPI backend + Flutter frontend (Windows/Android); today
only the Python backend is real.

**There are two parallel Python implementations — know which one you're in:**

- `src/academicos/` — the actual, working implementation (~11.5k LOC). Installed as the
  `academicos` package (`pyproject.toml` at repo root, `pip install -e .`). Has a CLI
  (`python -m academicos.cli`), passing tests, and is what `README.md` documents. **Treat this
  as the source of truth unless told otherwise.**
- `backend/academicos/` + `backend/ingestion/` — a newer, mostly-scaffolded rewrite (~4k LOC)
  following the target architecture in `docs/architecture.md` (separate `backend/pyproject.toml`,
  different dependency set — Qdrant, MinIO, SQLAlchemy/Alembic, LayoutLMv3, etc.). Many modules
  here are stubs/interfaces, not finished logic. Only work here if the task is explicitly about
  the `backend/` rewrite or `docs/architecture.md`.

Don't casually port fixes between the two trees — they have diverging schemas and package layouts.

`frontend/` is a Flutter app (clean-architecture layout: `data/`, `domain/`, `presentation/`)
targeting Windows + Android; it is early-stage relative to the Python backend.

## Compliance — read before touching student data

**Before adding or changing anything that touches student PII, assessment content, grading, or
a new data store: read `docs/compliance.md` and check its "before you ship" boxes.** This covers
DPDP Act 2023 (verifiable parental consent for minors, no secondary use of data, breach
notification), CERT-In's 6-hour breach-reporting rule and 6-month log-retention requirement, and
what's actually built vs. only documented today. Several controls it calls for (audit logging,
grade-change history, paper-release locking) are **not implemented yet** — don't assume they
exist because the doc discusses them.

## Commands

### `src/academicos` (primary implementation)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .            # core (pymupdf, pydantic, numpy, spacy)
pip install -e ".[api]"     # + FastAPI server
pip install -e ".[dev]"     # + pytest / httpx2 (needed to run the test suite)
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

**⚠ `config/config.toml` currently has a live Groq API key committed in plaintext
(`llm_api_key`). Do not copy this value into new files, examples, or commits — flag it to the
user rather than propagating it further.**

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
   `unlimited_ocr` → `tesseract`). **`min_confidence` is currently decorative** (audited
   2026-09-11): `Config.min_confidence` is loaded from `config.toml` but nothing in
   `parse/ensemble.py` or `cmd_parse` reads it — every parse result is accepted and marked
   `status="parsed"` regardless of `quality_score`, there is no reject/fallback/flag path.
   Wiring it up is a real design decision (what should happen to a low-confidence parse:
   reject, retry the next `parse_priority` method, or just flag for review?) — not done here
   without deciding that first.
3. **`extract/`** — pulls academic objects (chapters, topics, questions, answer schemes, etc.)
   out of parsed documents and chunks them for retrieval.
4. **`graph/`** — `GraphBuilder` constructs the knowledge graph from extracted objects into
   `GraphStore`; nodes/edges carry provenance (source doc/page/bbox/confidence).
5. **`retrieval/`** — `ChunkIndex` + `HybridRetriever` combine vector/keyword search over the
   chunk index for `search`/`serve`.
6. **`agents/`** — LLM-driven agents (OpenIE extraction, Self-RAG-style critic) that call out to
   the LLM provider configured in `config.toml` (`llm_base_url`/`llm_model`).
7. **`algorithms/`** — learner-facing models independent of the ingestion pipeline: FSRS spaced
   repetition (`fsrs.py`, `fsrs_fit.py`), mastery/confidence/misconception models, study planner,
   daily loop, motivation/attention/habit models. These operate on `EventStore`
   (`storage/event_store.py`) interaction records, not on the document graph directly.
8. **`api/main.py`** — FastAPI app exposing the above (only installed with the `[api]` extra).

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
