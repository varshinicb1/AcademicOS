# AcademicOS — CBSE/NCERT Academic Operating System

AcademicOS is an evidence-grounded academic intelligence and school operating platform built on the official CBSE/NCERT corpus (textbooks, previous year question papers, marking schemes, curricula, circulars, and bye-laws).

It bridges authoritative curriculum structures with day-to-day school operations: from scheduling and lesson planning to blueprint-based exam generation, mobile answer-sheet scanning, rubric grading, and personalized mastery tracking.

---

## Key Pillars

### 1. Curriculum & Timetable Substrate
- **Canonical Hierarchy**: Board &rarr; Academic Year &rarr; Grade &rarr; Subject &rarr; Unit &rarr; Chapter &rarr; Topic &rarr; Subtopic.
- **Operational Planning**: Multi-day block holiday scheduling, term definitions, weekly timetable slot allocations (`SubjectTimetableSlot`), subject period duration configuration, and teaching days calculation.
- **Verified Decomposition**: Complete, admin-approved Topic and Subtopic decomposition for all 5 core CBSE Class 10 subjects (Science, Mathematics, Social Science, English, and Hindi Course A) with zero unverified fabrication.
- **Textbook Ingestion Pipeline**: Deterministic Table of Contents (TOC) extraction and automatic Unit/Chapter materialization for custom/uploaded textbooks (`POST /api/v1/curriculum/books/{book_id}/toc/ingest`).

### 2. Assessment Designer & Authentic Question Bank
- **Real CBSE Question Pool**: Hundreds of authentic question papers parsed, deduplicated, and paired with official marking scheme model answers.
- **Granular Question Tagging**: Every question tagged with Bloom taxonomy levels, difficulty, type (MCQ, VSA, SA, LA, Case-based), and canonical curriculum subtopics with calibrated multi-clause recall.
- **Blueprint-Driven Paper Generator**: Instant generation of balanced question papers and teacher answer keys conforming to CBSE marks distributions and section requirements, exportable to print-ready PDFs.

### 3. School Admin Console & Management Tracking
- **Unified 6-Tab Console** (`/admin`):
  1. *Roster*: Teacher book assignments and student grade enrollments.
  2. *School-Wide Master Calendar*: Cross-subject schedule tracking with date filtering and period numbers.
  3. *Coverage & Pace*: Planned vs. actually-taught lessons, pace %, period variance, and overdue delayed topics.
  4. *Sequence Reorder*: Interactive drag-and-drop delivery reordering for Units and Chapters (`ReorderableListView`).
  5. *Reschedule*: Disruption handling via PUSH (shifting subsequent lessons forward) and ADJUST (single lesson rescheduling).
  6. *Calendar & Setup*: Working days calculation, period duration configuration, and holiday blocks.

### 4. Student & Parent Portals
- **Student Schedule & Progress** (`/student/schedule`): Real-time syllabus completion progress with Day, Week, Month (`table_calendar`), and 4-week Overview schedule views.
- **Dedicated Parent Portal** (`/parent`): Student syllabus completion metrics, daily classroom attendance/lesson tracking, and Carol Dweck growth mindset parent guidance & concept scaffolding (§A8).

### 5. Evaluation, Scanning & Learner Analytics
- **Mobile Answer-Sheet Scanning**: Multi-page camera capture with perspective correction and vision OCR.
- **Rubric-Based Evaluation**: Itemized marking against official CBSE marking schemes with teacher overrides.
- **Auditing & Compliance**: Immutable audit log (`audit_log.py`) tracking grade modifications, adhering to DPDP Act 2023 and CERT-In requirements.
- **Spaced Repetition & Mastery**: FSRS (Free Spaced Repetition Scheduler) and knowledge state estimation with personalized remediation.

---

## Products & Releases

AcademicOS ships as **two sub-products** and the backend runs as **two
independent releases**. They are not the same thing and are not deployed
together. Full detail: [docs/PRODUCTS_AND_RELEASES.md](docs/PRODUCTS_AND_RELEASES.md).

| Deliverable | What it is | Backend required? | Status |
|---|---|---|---|
| **AcademicOS Mobile** | Standalone Android app, fully offline (`ACADEMICOS_OFFLINE=true`) | No — on-device engine + bundled corpus | Shipped as APK |
| **AcademicOS Web** | Flutter web client in a browser | Yes — every action is an HTTP call | Cloud-hosted |
| **Backend — Render release** | Image-backed Render service + Supabase | — | **Live** (`academicos-backend.onrender.com`) |
| **Backend — GCP release** | Cloud Run + Cloud SQL + GCS, keyless CI | — | Written, **not yet run** |

These are easy to confuse, and older documents do. Two consequences worth
holding onto: a bug reported against **Mobile** cannot be fixed by redeploying
the backend, and the **GCP release is not an upgrade of the Render release** —
they coexist from one codebase and are switched by environment variables.

---

## Architecture & Tech Stack

- **Backend**: Python 3.12 + FastAPI (`src/academicos/`), SQLite with Write-Ahead Logging (WAL) and busy timeout for high-concurrency multi-user access. Durable state is resolved through one factory that prefers **Cloud SQL** (GCP release), falls back to **Supabase PostgREST** (Render release), and finally to local SQLite.
- **Frontend**: Flutter multi-platform client (`frontend/`) — one codebase, two products: the cloud **Web** client and the standalone **Android** app.
- **Offline-First Engine**: Local-first encrypted Hive storage (`frontend/lib/core/local_engine/`), offline OCR, local PDF generation. This is what makes the Mobile sub-product possible; it is unused by the Web client.
- **Live Deployment**: the **Render release** (`academicos-backend.onrender.com`), with keep-warm monitoring and a Docker Hub CI/CD pipeline. The **GCP release** (Cloud Run, `asia-south1`) is written and reviewed but has not been executed.

---

## Getting Started

### 1. Backend Setup

```powershell
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install core and optional dependencies
pip install -e ".[api,mobile-scan,dev]"

# The question-bank MCP server (python -m academicos.mcp.qbank_server) needs
# the MCP SDK as well; [api] already covers uvicorn for its network transports.
pip install -e ".[api,mcp]"

# Download required spaCy NLP model
python -m pip install en_core_web_md@https://github.com/explosion/spacy-models/releases/download/en_core_web_md-3.8.0/en_core_web_md-3.8.0-py3-none-any.whl

# Start the API server
python -m academicos.cli serve --host 127.0.0.1 --port 8010
```

API documentation will be available at `http://127.0.0.1:8010/docs`.

### 2. Frontend Setup (Flutter)

```powershell
cd frontend
flutter pub get

# Run on Chrome/Web
flutter run -d chrome --dart-define=ACADEMICOS_API=http://localhost:8010/api/v1

# Run tests
flutter test
```

### 3. Running the Test Suite

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

---

## Documentation

- [docs/PRD.md](docs/PRD.md) — **Start here.** What the product is for, who uses it, what is in scope, what is explicitly out of scope, which decisions are still open, and where every other document lives. Every claim is marked as cited, proposed, or open — it does not pretend to know what has not been decided
- [docs/PRODUCTS_AND_RELEASES.md](docs/PRODUCTS_AND_RELEASES.md) — Which product/release you are looking at: two clients (offline Mobile, cloud Web) and two backends (Render live, GCP written)
- [docs/REQUIREMENTS_BY_LAYER.md](docs/REQUIREMENTS_BY_LAYER.md) — Every requirement split into what the **backend** must deliver vs what the **frontend** must deliver, with verification depth
- [docs/design-system.md](docs/design-system.md) — The design system: white-first, emoji-free, token-driven. Machine-readable source at `design/tokens.json`
- [docs/research/ui-ux-principles.md](docs/research/ui-ux-principles.md) — Research: dashboard UX, habit formation, teacher adoption, and the Indian context. Cited, including where the evidence is weak
- [docs/research/interface-specification.md](docs/research/interface-specification.md) — **The interface spec.** Every requirement in the matrix mapped to a screen, the craft contract, command palette, WCAG 2.2 AA obligations, offline truth, and build order
- [docs/research/production-ai-principles.md](docs/research/production-ai-principles.md) — Production AI principles (OWASP LLM/Agentic Top 10, SRE, containment) and this codebase's conformance, including the open idempotency gap
- [docs/research/case-studies.md](docs/research/case-studies.md) — ~50 competing platforms: what is table stakes, where every incumbent is weak, what not to copy, and the Indian edtech financial case studies
- [docs/notifications.md](docs/notifications.md) — Notification policy: a notification is about the recipient's next action, or it is not sent
- [docs/api.md](docs/api.md) — Developer and contributing guide; [docs/api-reference.md](docs/api-reference.md) is the generated endpoint inventory
- [docs/question-bank-api.md](docs/question-bank-api.md) — Proposal for exposing the question bank as a standalone API asset (licensing gate first)
- [docs/TRANSCRIPT_REQUIREMENTS_MATRIX.md](docs/TRANSCRIPT_REQUIREMENTS_MATRIX.md) — Requirements traced to the client transcript, by section (a dated audit record; read its status-correction header first)
- [AGENTS.md](AGENTS.md) — Autonomous agent operational protocol and codebase invariants
- [CLAUDE.md](CLAUDE.md) — Developer guidelines, commands, and architecture overview
- [docs/deployment.md](docs/deployment.md) — The **Render release**: CI/CD, Supabase durability, known gaps
- [docs/gcp-deployment.md](docs/gcp-deployment.md) — The **GCP release**: architecture, cutover, costs
- [docs/gcp-bootstrap.md](docs/gcp-bootstrap.md) — The **GCP release**: one-time owner runbook
- [docs/system-review.html](docs/system-review.html) — CTO-facing review of both sub-products and both releases
- [docs/roadmap.md](docs/roadmap.md) — 5-phase product vision and implementation status
- [docs/compliance.md](docs/compliance.md) — DPDP Act 2023 and CERT-In compliance specifications
- [docs/ACADEMIC_DATA_MODEL.md](docs/ACADEMIC_DATA_MODEL.md) — Canonical curriculum data model
- [docs/TRANSCRIPT_REQUIREMENTS_MATRIX.md](docs/TRANSCRIPT_REQUIREMENTS_MATRIX.md) — Detailed requirements traceability matrix
