# AcademicOS — CBSE/NCERT Academic Operating System

AcademicOS is an evidence-grounded academic intelligence and school operating platform built on the official CBSE/NCERT corpus (textbooks, previous year question papers, marking schemes, curricula, circulars, and bye-laws).

It bridges authoritative curriculum structures with day-to-day school operations: from scheduling and lesson planning to blueprint-based exam generation, mobile answer-sheet scanning, rubric grading, and personalized mastery tracking.

---

## Key Pillars

### 1. Curriculum & Timetable Substrate
- **Canonical Hierarchy**: Board &rarr; Academic Year &rarr; Grade &rarr; Subject &rarr; Unit &rarr; Chapter &rarr; Topic &rarr; Subtopic.
- **Operational Planning**: Multi-day block holiday scheduling, term definitions, weekly timetable slot allocations (`SubjectTimetableSlot`), and subject period allocations.
- **Verified Decomposition**: Complete, admin-approved Topic and Subtopic decomposition for Class 10 (Science, Mathematics, Social Science, English) with zero unverified fabrication.

### 2. Assessment Designer & Authentic Question Bank
- **Real CBSE Question Pool**: Hundreds of authentic question papers parsed, deduplicated, and paired with official marking scheme model answers.
- **Granular Question Tagging**: Every question tagged with Bloom taxonomy levels, difficulty, type (MCQ, VSA, SA, LA, Case-based), and canonical curriculum subtopics.
- **Blueprint-Driven Paper Generator**: Instant generation of balanced question papers and teacher answer keys conforming to CBSE marks distributions and section requirements, exportable to print-ready PDFs.

### 3. Evaluation, Scanning & Feedback Loop
- **Mobile Answer-Sheet Scanning**: Multi-page camera capture with perspective correction and vision OCR.
- **Rubric-Based Evaluation**: Itemized marking against official CBSE marking schemes with teacher overrides.
- **Auditing & Compliance**: Immutable audit log (`audit_log.py`) tracking grade modifications, adhering to DPDP Act 2023 and CERT-In requirements.

### 4. Learner Mastery & Spaced Repetition
- **Cognitive Modeling**: Implementation of FSRS (Free Spaced Repetition Scheduler) and knowledge state estimation.
- **Personalized Remediation**: Automated generation of targeted practice sets based on identified misconceptions.

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
- [docs/roadmap.md](docs/roadmap.md) — 5-phase product vision and implementation status
- [docs/compliance.md](docs/compliance.md) — DPDP Act 2023 and CERT-In compliance specifications
- [docs/ACADEMIC_DATA_MODEL.md](docs/ACADEMIC_DATA_MODEL.md) — Canonical curriculum data model
- [docs/TRANSCRIPT_REQUIREMENTS_MATRIX.md](docs/TRANSCRIPT_REQUIREMENTS_MATRIX.md) — Detailed requirements traceability matrix
