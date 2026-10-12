# CLAUDE.md

Guidance for Claude Code in this repository. **The rules are in [`AGENTS.md`](AGENTS.md), imported in
full below, and they bind every Claude session.** This file adds only what is specific to Claude Code, plus
a technical reference.

@AGENTS.md

---

## Claude Code specifics

- **You are not the maintainer's session unless the user says so.** Only the maintainer's session:
  - merges PRs (`/review-pr <n>`, [`.claude/commands/review-pr.md`](.claude/commands/review-pr.md));
  - posts as the owner (issues, PR reviews, comments on the owner's behalf), and then only when the user
    has asked;
  - watches deploys.
- **End every commit** with the co-author line your session's instructions give. Never skip hooks
  (`--no-verify`).
- **Run one heavy job at a time** (a full pytest run, a Flutter test run, a web build, an image build). Do
  not spawn parallel agent swarms on a laptop.
- **Never print or paste a secret** you come across, including one the user pastes. Refer to it by its
  Secret Manager name.
- **Work in your own worktree or clone.** Never edit, reset, clean or `checkout --` another session's
  files, and never sweep another session's uncommitted work.
- **Put evidence in the PR description**, not only in the chat.

## Technical reference

### Commands

```bash
python -m venv .venv && . .venv/Scripts/activate            # Python 3.12
pip install -e ".[dev,api,ocr,retrieval,gcs,postgres,mcp]"
python -m pip install en_core_web_md@https://github.com/explosion/spacy-models/releases/download/en_core_web_md-3.8.0/en_core_web_md-3.8.0-py3-none-any.whl
python -m academicos.cli serve --port 8010                   # local backend
cd frontend && flutter pub get && flutter run -d chrome --dart-define=ACADEMICOS_API=http://localhost:8010/api/v1
pytest tests/test_homework.py                                # one file
pytest tests/test_homework.py::test_name                     # one test
```

App builds:
- `flutter build web` is the console.
- `--dart-define=ACADEMICOS_APP=teacher|student` gives the phone apps.
- `--dart-define=ACADEMICOS_OFFLINE=true` gives the offline Android app (`docs/apps.md`).

Runtime config:
- `config/config.toml`, overridable by `ACOS_*` environment variables (`ACOS_DATA_ROOT`,
  `ACOS_GCS_BUCKET`, `ACOS_POSTGRES_*`, ...).
- `ACOS_ENV=production` arms a startup guard that refuses placeholder secrets, CORS `*`, demo accounts
  and unlisted LLM providers.
- The LLM key lives in `config/secrets.env` (gitignored) or Secret Manager, **never** in `config.toml`. A
  live key was once committed there and had to be rotated.

### Storage

- **Cloud SQL Postgres** holds the JSONB stores: users and sessions, invites, the audit log, consents,
  papers, assessments, marking, learner models and events, practice. They go through one factory,
  `assessment/postgres_kv.durable_table(name)`. Never construct a remote table directly in a store.
- **Two relational stores are SQLite files** synced to GCS as whole-file snapshots
  (`storage/snapshot_sync.py`):
  - `CurriculumStore` (`curriculum/store.py`): years, sections, timetable, plans, lessons, leave, cover,
    staff rules;
  - `OperationsStore` (`operations/store.py`): notifications, homework, exams, marks, reviews, grants,
    owners, pilot agreement and more.
  - This is why Cloud Run runs one instance. R-A1 (developer handover §7) moves them to Cloud SQL.
- **Blobs** (uploads, scans, API keys, snapshots) live in GCS when `ACOS_GCS_BUCKET` is set
  (`storage/blobs.py`).
- `GET /health/storage` reports which backend is active. Check it rather than guessing.

### The ingestion and knowledge-graph pipeline

The research layer under the product. It runs offline and its CLI stages run in order: `ingest`, `parse`,
`extract`, `build-graph`, `index`, then `search`, `serve` or `stats`. Each stage reads the previous stage's
output through the registry:

- `ingest/`: the source registry.
- `parse/`: an ensemble of native PDF text and OCR. A parse below `min_confidence` is held as
  `low_confidence` and never reaches the graph.
- `extract/`: academic objects and chunks.
- `graph/`: the knowledge graph, with provenance on every node.
- `retrieval/`: hybrid search.
- `agents/`: optional LLM extraction and critic.
- `algorithms/`: FSRS spaced repetition and mastery models, used by learning progress.

The full target ontology in `docs/architecture.md` is only partly built. Check the real `NodeType`/`EdgeType`
enums before assuming a type exists.

### Data outside the repository

- The raw NCERT and CBSE PDFs (`ncert-dataset/`, `cbse-dataset/`) and the chapter transcriptions sit on the
  owner's machine, not in git. Ask for them; never commit them.
- Derived data lands under `academicos-data/`.
