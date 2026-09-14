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

## Architecture & Tech Stack

- **Backend**: Python 3.12 + FastAPI (`src/academicos/`), SQLite with Write-Ahead Logging (WAL) and busy timeout for high-concurrency multi-user access, optional Supabase PostgREST sync for persistent deployments.
- **Frontend**: Flutter multi-platform client (`frontend/`) supporting Web, Android, and Windows desktop.
- **Offline-First Engine**: Local-first encrypted Hive storage (`frontend/lib/core/local_engine/`), offline OCR, local PDF generation, and background sync reconciliation (`SyncService`).
- **Live Deployment**: Hosted on Render (`academicos-backend.onrender.com`) with automated keep-warm monitoring and Docker Hub CI/CD pipeline.

---

## Getting Started

### 1. Backend Setup

```powershell
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install core and optional dependencies
pip install -e ".[api,mobile-scan,dev]"

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

- [AGENTS.md](AGENTS.md) — Autonomous agent operational protocol and codebase invariants
- [CLAUDE.md](CLAUDE.md) — Developer guidelines, commands, and architecture overview
- [docs/deployment.md](docs/deployment.md) — Real Render CI/CD pipeline, Supabase durability setup, and honestly-documented known gaps
- [docs/roadmap.md](docs/roadmap.md) — 5-phase product vision and implementation status
- [docs/compliance.md](docs/compliance.md) — DPDP Act 2023 and CERT-In compliance specifications
- [docs/ACADEMIC_DATA_MODEL.md](docs/ACADEMIC_DATA_MODEL.md) — Canonical curriculum data model
- [docs/TRANSCRIPT_REQUIREMENTS_MATRIX.md](docs/TRANSCRIPT_REQUIREMENTS_MATRIX.md) — Detailed requirements traceability matrix
