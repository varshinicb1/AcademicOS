# AcademicOS — CBSE Academic Brain Architecture

**Version:** 1.0  
**Target:** Windows Desktop + Android (Flutter)  
**Backend:** Python (FastAPI) + SQLite (WAL Mode + busy_timeout) + Supabase Dual-Mode + Local Chunk Index  
**Frontend:** Flutter (Windows, Android, Web) + Local-First Offline Engine (Hive AES-256)  
**Document Processing:** Sarvam Vision + Local OCR Ensemble + Native PDF  

> **Implementation Note for Contributors & Agents:**  
> This document details the architectural target and system design. The **active, working, tested implementation** lives in `src/academicos/` (~11.5k LOC, 1113+ passing tests). The `backend/` directory is a parallel scaffolded rewrite (~4k LOC). All production features, CLI commands, and Flutter API integrations run against `src/academicos/`. See `AGENTS.md` and `CLAUDE.md` for codebase invariants.

---

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            FLUTTER APP (Windows/Android)                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐             │
│  │  Syllabus   │ │  Planner    │ │ Question    │ │  Analytics  │             │
│  │  Explorer   │ │  (Daily/    │ │  Bank       │ │  (Mastery,  │             │
│  │             │ │   Yearly)   │ │             │ │   Gaps,     │             │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘             │
│         │               │               │               │                      │
│         └───────────────┼───────────────┼───────────────┘                      │
│                         ▼               ▼                                      │
│              ┌─────────────────────────────────────┐                           │
│              │         BFF Layer (Riverpod/Bloc)   │                           │
│              └─────────────────────┬───────────────┘                           │
└─────────────────────────────────────┼──────────────────────────────────────────┘
                                      │ HTTPS/gRPC
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FASTAPI BACKEND (AcademicOS Core)                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │   Ingestion  │ │  Extraction  │ │   Graph      │ │  Retrieval   │        │
│  │   Pipeline   │ │  Pipeline    │ │   Engine     │ │   Engine     │        │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘        │
│         │                │                │                │                  │
│         └────────────────┼────────────────┼────────────────┘                  │
│                          ▼                ▼                                   │
│                 ┌─────────────────────────────────────┐                       │
│                 │         Agent Orchestrator          │                       │
│                 │  (Ingestion|Syllabus|Blueprint|     │                       │
│                 │   QGen|Eval|Misconception|Calendar) │                       │
│                 └─────────────────────┬───────────────┘                       │
└────────────────────────────────────────┼──────────────────────────────────────┘
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        ▼                                ▼                                ▼
┌───────────────┐              ┌───────────────┐              ┌───────────────┐
│   SQLite      │              │   Vector DB   │              │  Object Store │
│   (Graph,     │              │   (Embeddings,│              │  (PDFs,       │
│   Events,     │              │   Hybrid      │              │   Images,     │
│   Provenance) │              │   Search)     │              │   OCR,        │
│               │              │               │              │   Exports)    │
└───────────────┘              └───────────────┘              └───────────────┘
```

---

## 2. Repository Structure

```
academicos/
├── backend/                          # Python FastAPI Backend
│   ├── academicos/
│   │   ├── __init__.py
│   │   ├── config.py                 # Unified config (env, YAML, secrets)
│   │   ├── main.py                   # FastAPI app factory
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   ├── sqlite.py             # SQLite async (aiosqlite)
│   │   │   ├── vector.py             # Vector DB client (Qdrant/Chroma)
│   │   │   ├── object_store.py       # S3/R2/local object storage
│   │   │   └── migrations/           # Schema migrations
│   │   ├── ingestion/
│   │   │   ├── __init__.py
│   │   │   ├── discover.py           # PDF discovery + checksums
│   │   │   ├── classifier.py         # Document type classification
│   │   │   ├── processor.py          # Batch processing orchestration
│   │   │   ├── ocr/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── sarvam_vision.py  # Sarvam Vision integration
│   │   │   │   ├── layoutlm.py       # LayoutLMv3 for structure
│   │   │   │   ├── ensemble.py       # Ensemble OCR + confidence
│   │   │   │   └── fallback.py       # Tesseract/PaddleOCR fallback
│   │   │   └── quality.py            # Quality scoring + corruption detection
│   │   ├── extraction/
│   │   │   ├── __init__.py
│   │   │   ├── layout.py             # Layout analysis (headings, regions)
│   │   │   ├── tables.py             # Table extraction (Camelot + PDFPlumber)
│   │   │   ├── figures.py            # Figure/chart detection + captioning
│   │   │   ├── equations.py          # Equation extraction (LaTeX/OMML)
│   │   │   ├── qa_sections.py        # Q/A section detection
│   │   │   ├── answer_schemes.py     # Marking scheme / rubric extraction
│   │   │   ├── chapters.py           # Chapter boundary detection
│   │   │   ├── topics.py             # Topic/subtopic extraction
│   │   │   ├── learning_outcomes.py  # LO extraction + Bloom tagging
│   │   │   ├── competencies.py       # Competency mapping
│   │   │   ├── time_estimates.py     # Period/time inference
│   │   │   └── schemas.py            # Extraction output schemas (Pydantic)
│   │   ├── graph/
│   │   │   ├── __init__.py
│   │   │   ├── ontology.py           # Full academic ontology (NodeType, EdgeType)
│   │   │   ├── schema.py             # Graph schema + versioning
│   │   │   ├── store.py              # Graph CRUD + transactions
│   │   │   ├── builder.py            # Graph construction from extractions
│   │   │   ├── query.py              # Graph queries (prereq, path, subgraph)
│   │   │   ├── versioning.py         # Temporal versioning (valid_from/valid_to)
│   │   │   ├── overlays.py           # Board/school overlays
│   │   │   └── provenance.py         # Provenance tracking per node/edge
│   │   ├── retrieval/
│   │   │   ├── __init__.py
│   │   │   ├── hybrid.py             # Hybrid search (vector + keyword + graph)
│   │   │   ├── chapter_aware.py      # Chapter-scoped retrieval
│   │   │   ├── page_aware.py         # Page-level retrieval with coordinates
│   │   │   ├── evidence.py           # Evidence-aware retrieval
│   │   │   ├── reranker.py           # Cross-encoder + graph-aware reranking
│   │   │   └── schemas.py            # Retrieval request/response
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # BaseAgent with tool registry
│   │   │   ├── ingestion_agent.py
│   │   │   ├── syllabus_agent.py
│   │   │   ├── blueprint_agent.py
│   │   │   ├── question_generator.py
│   │   │   ├── answer_scheme_agent.py
│   │   │   ├── evaluation_agent.py
│   │   │   ├── misconception_agent.py
│   │   │   ├── knowledge_gap_agent.py
│   │   │   ├── calendar_agent.py
│   │   │   ├── compliance_agent.py
│   │   │   ├── provenance_agent.py
│   │   │   ├── quality_agent.py
│   │   │   └── orchestrator.py       # Multi-agent workflow engine
│   │   ├── algorithms/               # Existing learning algorithms (keep)
│   │   │   ├── __init__.py
│   │   │   ├── forgetting.py
│   │   │   ├── fsrs.py
│   │   │   ├── fsrs_fit.py
│   │   │   ├── mastery.py
│   │   │   ├── learner_model.py
│   │   │   ├── study_planner.py
│   │   │   ├── confidence_model.py
│   │   │   ├── misconceptions.py
│   │   │   ├── lifelong_model.py
│   │   │   ├── motivation_model.py
│   │   │   ├── attention_model.py
│   │   │   ├── habit_model.py
│   │   │   ├── emotion_model.py
│   │   │   ├── curiosity_engine.py
│   │   │   ├── parent_guidance.py
│   │   │   ├── teacher_assistance.py
│   │   │   ├── career_discovery.py
│   │   │   ├── reward_engine.py
│   │   │   └── daily_loop.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── ingestion.py
│   │   │   │   ├── documents.py
│   │   │   │   ├── graph.py
│   │   │   │   ├── retrieval.py
│   │   │   │   ├── syllabus.py
│   │   │   │   ├── questions.py
│   │   │   │   ├── evaluation.py
│   │   │   │   ├── planner.py
│   │   │   │   ├── analytics.py
│   │   │   │   ├── agents.py
│   │   │   │   └── admin.py
│   │   │   ├── schemas/              # Pydantic request/response models
│   │   │   │   ├── __init__.py
│   │   │   │   ├── ingestion.py
│   │   │   │   ├── graph.py
│   │   │   │   ├── retrieval.py
│   │   │   │   ├── syllabus.py
│   │   │   │   └── ...
│   │   │   ├── deps.py               # FastAPI dependencies
│   │   │   └── middleware.py         # Auth, logging, rate limit
│   │   ├── eval/
│   │   │   ├── __init__.py
│   │   │   ├── ocr_eval.py
│   │   │   ├── layout_eval.py
│   │   │   ├── entity_eval.py
│   │   │   ├── relation_eval.py
│   │   │   ├── retrieval_eval.py
│   │   │   ├── faithfulness_eval.py
│   │   │   ├── citation_eval.py
│   │   │   └── coverage_eval.py
│   │   ├── governance/
│   │   │   ├── __init__.py
│   │   │   ├── audit.py              # Audit logging
│   │   │   ├── citations.py          # Citation enforcement
│   │   │   ├── hallucination.py      # Hallucination detection
│   │   │   ├── rbac.py               # Role-based access
│   │   │   └── versioning.py         # Rollback + change detection
│   │   └── cli.py                    # CLI for admin tasks
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── fixtures/
│   │   └── conftest.py
│   ├── pyproject.toml
│   ├── uv.lock / requirements.txt
│   └── Dockerfile
│
├── frontend/                         # Flutter App
│   ├── pubspec.yaml
│   ├── analysis_options.yaml
│   ├── lib/
│   │   ├── main.dart
│   │   ├── app.dart
│   │   ├── core/
│   │   │   ├── constants/
│   │   │   ├── theme/
│   │   │   ├── routing/
│   │   │   ├── di/                   # Dependency injection (get_it)
│   │   │   ├── errors/
│   │   │   ├── utils/
│   │   │   └── platform/             # Windows/Android specifics
│   │   ├── data/
│   │   │   ├── models/               # DTOs matching backend schemas
│   │   │   ├── repositories/         # Repository implementations
│   │   │   ├── datasources/
│   │   │   │   ├── api/              # Dio/Retrofit API client
│   │   │   │   ├── local/            # Local DB (Drift/SQLite)
│   │   │   │   └── cache/            # In-memory/cache
│   │   │   └── mappers/
│   │   ├── domain/
│   │   │   ├── entities/             # Pure domain entities
│   │   │   ├── repositories/         # Repository interfaces
│   │   │   ├── usecases/             # Business logic (clean architecture)
│   │   │   └── failures/
│   │   ├── presentation/
│   │   │   ├── syllabus/
│   │   │   ├── planner/
│   │   │   ├── question_bank/
│   │   │   ├── analytics/
│   │   │   ├── settings/
│   │   │   └── shared/
│   │   │       ├── widgets/
│   │   │       ├── blocs/            # Riverpod/Bloc providers
│   │   │       └── themes/
│   │   └── l10n/                     # Localization
│   ├── test/
│   │   ├── unit/
│   │   ├── widget/
│   │   └── integration/
│   ├── android/
│   ├── windows/
│   ├── web/
│   └── assets/
│
├── shared/                           # Shared schemas (auto-generated)
│   ├── python/                       # Pydantic models (from OpenAPI)
│   └── dart/                         # Dart models (from OpenAPI)
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── DATA_MODEL.md
│   ├── EXTRACTION_PIPELINE.md
│   ├── AGENT_ORCHESTRATION.md
│   ├── EVALUATION.md
│   ├── GOVERNANCE.md
│   ├── FLUTTER_INTEGRATION.md
│   └── DEPLOYMENT.md
│
├── scripts/
│   ├── generate_openapi.py
│   ├── generate_dart_models.py
│   ├── migrate_db.py
│   └── seed_data.py
│
├── docker-compose.yml
├── docker-compose.dev.yml
├── .env.example
├── Makefile
├── README.md
└── LICENSE
```

---

## 3. Data Model — Academic Ontology

### 3.1 Core Node Types

```python
# backend/academicos/graph/ontology.py
from enum import Enum

class NodeType(str, Enum):
    # Board & Policy
    BOARD = "Board"
    BOARD_POLICY = "BoardPolicy"
    ACADEMIC_YEAR = "AcademicYear"
    CIRCULAR = "Circular"
    
    # Structure
    SUBJECT = "Subject"
    GRADE = "Grade"
    UNIT = "Unit"
    CHAPTER = "Chapter"
    TOPIC = "Topic"
    SUBTOPIC = "Subtopic"
    
    # Pedagogical
    LEARNING_OUTCOME = "LearningOutcome"
    COMPETENCY = "Competency"
    CONCEPT = "Concept"
    PREREQUISITE = "Prerequisite"
    MISCONCEPTION = "Misconception"
    
    # Assessment
    ASSESSMENT_BLUEPRINT = "AssessmentBlueprint"
    QUESTION_PAPER = "QuestionPaper"
    QUESTION = "Question"
    QUESTION_PART = "QuestionPart"
    ANSWER_SCHEME = "AnswerScheme"
    MARKING_POINT = "MarkingPoint"
    RUBRIC = "Rubric"
    EXAM_PATTERN = "ExamPattern"
    SAMPLE_PAPER = "SamplePaper"
    SYLLABUS_ITEM = "SyllabusItem"
    
    # Content
    ACTIVITY = "Activity"
    EXPERIMENT = "Experiment"
    WORKSHEET = "Worksheet"
    RESOURCE = "Resource"
    DIAGRAM = "Diagram"
    TABLE = "Table"
    FIGURE = "Figure"
    FORMULA = "Formula"
    TERM = "Term"
    DEFINITION = "Definition"
    EXAMPLE = "Example"
    PASSAGE = "Passage"
    
    # Document & Provenance
    DOCUMENT = "Document"
    PAGE = "Page"
    DOCUMENT_VERSION = "DocumentVersion"
    EXTRACTION_JOB = "ExtractionJob"
    PROVENANCE_RECORD = "ProvenanceRecord"
    
    # School Context
    SCHOOL = "School"
    TEACHER = "Teacher"
    CLASSROOM = "Classroom"
    STUDENT = "Student"
    SCHOOL_PLAN = "SchoolPlan"
    REVISION_PLAN = "RevisionPlan"
    TEACHER_NOTE = "TeacherNote"
```

### 3.2 Edge Types

```python
class EdgeType(str, Enum):
    CONTAINS = "CONTAINS"
    PRECEDES = "PRECEDES"
    PREREQUISITE_OF = "PREREQUISITE_OF"
    MAPS_TO = "MAPS_TO"
    EVIDENCED_BY = "EVIDENCED_BY"
    DERIVED_FROM = "DERIVED_FROM"
    REPLACES = "REPLACES"
    SUPERSEDES = "SUPERSEDES"
    SUPPORTED_BY = "SUPPORTED_BY"
    ASSESSED_BY = "ASSESSED_BY"
    EXEMPLIFIED_BY = "EXEMPLIFIED_BY"
    RELATED_TO = "RELATED_TO"
    WEAKENS = "WEAKENS"
    STRENGTHENS = "STRENGTHENS"
    ALIGNS_WITH = "ALIGNS_WITH"
    PART_OF = "PART_OF"
    HAS_DIFFICULTY = "HAS_DIFFICULTY"
    HAS_TIME_ESTIMATE = "HAS_TIME_ESTIMATE"
    HAS_BLOOM_LEVEL = "HAS_BLOOM_LEVEL"
    HAS_COMPETENCY = "HAS_COMPETENCY"
    HAS_MARKING_POINT = "HAS_MARKING_POINT"
    HAS_SOURCE = "HAS_SOURCE"
    HAS_PROVENANCE = "HAS_PROVENANCE"
    VALID_FROM = "VALID_FROM"
    VALID_TO = "VALID_TO"
    OVERLAYS = "OVERLAYS"
```

### 3.3 Key Attributes (Per Node)

```python
# Every node has these base attributes
class BaseNodeAttributes(BaseModel):
    id: str                           # UUID v7 (time-ordered)
    type: NodeType
    created_at: datetime
    updated_at: datetime
    version: int                      # Optimistic locking
    valid_from: datetime | None       # Temporal validity
    valid_to: datetime | None
    board: str = "CBSE"               # Board context
    grade: int | None                 # Grade 1-12
    subject: str | None               # Subject code
    source_document_id: str | None    # Provenance
    page_number: int | None
    bbox: list[float] | None          # [x1, y1, x2, y2] normalized 0-1
    extraction_method: str            # "sarvam_vision", "layoutlm", "manual"
    extraction_confidence: float      # 0.0-1.0
    verified_by_human: bool = False
    human_verifier_id: str | None
    tags: list[str] = []
```

### 3.4 Temporal Versioning

```sql
-- Every node/edge has temporal validity
CREATE TABLE nodes (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    attributes JSONB NOT NULL,
    valid_from TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMP,
    version INTEGER NOT NULL DEFAULT 1,
    superseded_by TEXT REFERENCES nodes(id),
    board TEXT NOT NULL DEFAULT 'CBSE',
    grade INTEGER,
    subject TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE edges (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES nodes(id),
    target_id TEXT NOT NULL REFERENCES nodes(id),
    type TEXT NOT NULL,
    attributes JSONB NOT NULL DEFAULT '{}',
    valid_from TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMP,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL
);

-- Index for temporal queries
CREATE INDEX idx_nodes_temporal ON nodes(valid_from, valid_to);
CREATE INDEX idx_nodes_board_grade_subject ON nodes(board, grade, subject);
```

---

## 4. Ingestion Pipeline Design

### 4.1 Document Discovery & Classification

```python
# backend/academicos/ingestion/classifier.py
class DocumentClassifier:
    """Classify CBSE/NCERT documents by type."""
    
    DOCUMENT_TYPES = [
        "syllabus",
        "circular",
        "sample_paper",
        "question_paper",
        "marking_scheme",
        "textbook_chapter",
        "teacher_manual",
        "competency_framework",
        "blueprint",
        "exemplar",
        "worksheet",
        "activity_guide",
        "lab_manual",
        "revision_notes",
    ]
    
    async def classify(self, pdf_path: Path) -> ClassificationResult:
        # 1. Filename + metadata heuristics
        # 2. First N pages text analysis
        # 3. Layout signature (tables, diagrams, Q/A patterns)
        # 4. Sarvam Vision + LLM classification
        pass
```

### 4.2 Layout-Aware Extraction Pipeline

```python
# backend/academicos/extraction/layout.py
class LayoutAnalyzer:
    """LayoutLMv3-based document structure analysis."""
    
    async def analyze(self, pdf_path: Path, pages: list[PageImage]) -> LayoutResult:
        # Returns: reading_order, headings, regions, tables, figures, equations
        pass

# backend/academicos/extraction/tables.py
class TableExtractor:
    """Multi-engine table extraction with consensus."""
    
    ENGINES = ["pdfplumber", "camelot", "tabula", "sarvam_vision"]
    
    async def extract(self, page_image: PageImage, layout: LayoutResult) -> list[Table]:
        # Run all engines, merge with IoU-based consensus
        # Output: Table(bbox, rows, headers, confidence, latex, markdown)
        pass

# backend/academicos/extraction/equations.py
class EquationExtractor:
    """Equation detection + LaTeX/OMML conversion."""
    
    async def extract(self, page_image: PageImage) -> list[Equation]:
        # Detect math regions -> LaTeX via Nougat/MathPix/Unimernet
        pass
```

### 4.3 Structured Extraction Schemas

```python
# backend/academicos/extraction/schemas.py
class ChapterExtraction(BaseModel):
    chapter_number: int
    chapter_title: str
    subject: str
    grade: int
    start_page: int
    end_page: int
    topics: list[TopicExtraction]
    learning_outcomes: list[LearningOutcomeExtraction]
    competencies: list[CompetencyExtraction]
    time_estimate_periods: int
    bloom_distribution: dict[str, int]  # remember: 3, understand: 5, ...
    assessment_blueprint_ref: str | None
    prerequisites: list[str]  # concept IDs
    source_document_id: str
    confidence: float

class QuestionExtraction(BaseModel):
    question_number: str
    stem: str
    stem_latex: str | None
    parts: list[QuestionPartExtraction]
    marks: int
    bloom_level: str
    difficulty: float  # 0-1
    topic_tags: list[str]
    competency_tags: list[str]
    answer_scheme: AnswerSchemeExtraction | None
    source_document_id: str
    page_number: int
    bbox: list[float]
    confidence: float

class AnswerSchemeExtraction(BaseModel):
    marking_points: list[MarkingPointExtraction]
    total_marks: int
    alternative_answers: list[str]
    common_errors: list[str]
    rubric_levels: list[RubricLevel] | None
```

---

## 5. Retrieval Architecture

### 5.1 Hybrid Search

```python
# backend/academicos/retrieval/hybrid.py
class HybridRetriever:
    """Vector + Keyword + Graph retrieval with fusion."""
    
    def __init__(self, vector_db: VectorDB, graph_store: GraphStore, 
                 keyword_index: KeywordIndex):
        self.vector = vector_db
        self.graph = graph_store
        self.keyword = keyword_index
    
    async def search(self, query: RetrievalQuery) -> RetrievalResult:
        # 1. Expand query (synonyms, related concepts)
        # 2. Vector search (semantic)
        # 3. Keyword search (BM25)
        # 4. Graph traversal (prereq, contains, maps_to)
        # 5. Reciprocal Rank Fusion (RRF) with weights
        # 6. Graph-aware reranking (cross-encoder + structure)
        pass
```

### 5.2 Chapter/Page-Aware Retrieval

```python
class ChapterAwareRetriever:
    """Scope retrieval to chapter/subtopic boundaries."""
    
    async def search_in_chapter(self, chapter_id: str, query: str, 
                                 k: int = 10) -> list[Evidence]:
        # Filter vector results by chapter containment
        # Include page-level coordinates for citation
        pass

class PageAwareRetriever:
    """Retrieve with page coordinates for exact citation."""
    
    async def search_with_pages(self, query: str, k: int = 10) -> list[PageEvidence]:
        # Returns: text, page_num, bbox, document_id, confidence
        pass
```

---

## 6. Agent Orchestration

### 6.1 Base Agent Framework

```python
# backend/academicos/agents/base.py
class BaseAgent(ABC):
    def __init__(self, tools: dict[str, Tool], llm: LLMClient, 
                 memory: AgentMemory, tracer: Tracer):
        self.tools = tools
        self.llm = llm
        self.memory = memory
        self.tracer = tracer
    
    @abstractmethod
    async def execute(self, task: AgentTask) -> AgentResult:
        pass
    
    async def verify(self, result: AgentResult) -> VerificationResult:
        # Self-verification using evidence
        pass
```

### 6.2 Specialized Agents

| Agent | Responsibility | Tools |
|-------|---------------|-------|
| `IngestionAgent` | PDF → structured extraction | OCR, Layout, Tables, Equations, Classifier |
| `SyllabusAgent` | Generate syllabus plan from graph | GraphQuery, BlueprintRetriever, Calendar |
| `BlueprintAgent` | Create assessment blueprints | GraphQuery, LORetriever, BloomAnalyzer |
| `QuestionGenerator` | Generate questions from LOs | GraphQuery, LOContext, BloomMapper, AnswerSchemeGen |
| `AnswerSchemeAgent` | Create marking schemes | QuestionContext, RubricTemplates, MarkingPoints |
| `EvaluationAgent` | Evaluate student answers | AnswerScheme, RubricMatcher, MisconceptionChecker |
| `MisconceptionAgent` | Detect & map misconceptions | AnswerHistory, MisconceptionCatalog, GraphQuery |
| `KnowledgeGapAgent` | Identify gaps per learner | LearnerModel, PrereqGraph, MasteryThresholds |
| `CalendarAgent` | Yearly/term calendars | SyllabusGraph, HolidayCalendar, PeriodAllocator |
| `ComplianceAgent` | CBSE circular compliance | CircularGraph, PolicyMatcher, AlertEngine |
| `ProvenanceAgent` | Trace answers to source | GraphTraversal, EvidenceCollector, CitationBuilder |
| `QualityAgent` | Extraction QA | ConfidenceScorer, HumanReviewQueue, RegressionTester |

### 6.3 Orchestrator

```python
# backend/academicos/agents/orchestrator.py
class AgentOrchestrator:
    """Multi-agent workflow execution with DAG."""
    
    async def execute_workflow(self, workflow: WorkflowDefinition) -> WorkflowResult:
        # 1. Build DAG from workflow
        # 2. Topological execution with parallelism
        # 3. Checkpointing + retry
        # 4. Verification at each step
        # 5. Compile final result with full provenance
        pass
```

---

## 7. API Contracts (OpenAPI 3.1)

### 7.1 Core Endpoints

```yaml
# POST /api/v1/ingestion/documents
# Upload & queue PDF for processing
request:
  multipart/form-data:
    file: binary
    metadata: DocumentMetadata
response: IngestionJob

# GET /api/v1/ingestion/jobs/{job_id}
# Job status + results

# POST /api/v1/graph/query
# Graph traversal query
request:
  query: GraphQuery  # Cypher-like or DSL
response: GraphResult

# POST /api/v1/retrieval/search
# Hybrid search
request:
  query: str
  filters: RetrievalFilters
  k: int
  mode: "hybrid" | "vector" | "keyword" | "graph"
response: RetrievalResult

# POST /api/v1/syllabus/generate
# Generate syllabus plan
request:
  grade: int
  subject: str
  academic_year: str
  school_overlay_id: str | null
response: SyllabusPlan

# POST /api/v1/questions/generate
# Generate question paper
request:
  blueprint_id: str
  difficulty_distribution: dict
  bloom_distribution: dict
  count: int
response: QuestionPaper

# POST /api/v1/evaluation/evaluate
# Evaluate answer sheet
request:
  question_paper_id: str
  student_answers: list[StudentAnswer]
  learner_id: str | null
response: EvaluationResult

# POST /api/v1/planner/daily
# Get daily study plan
request:
  learner_id: str
  date: date | null
  capacity_minutes: int
response: DailyPlan

# GET /api/v1/analytics/learner/{learner_id}
# Mastery, gaps, confidence, habit
response: LearnerAnalytics

# POST /api/v1/agents/execute
# Execute agent workflow
request:
  agent_type: str
  task: AgentTask
response: AgentResult
```

---

## 8. Flutter Frontend Architecture

### 8.1 Clean Architecture Layers

```
lib/
├── core/
│   ├── constants/app_constants.dart
│   ├── theme/app_theme.dart
│   ├── routing/app_router.dart (go_router)
│   ├── di/service_locator.dart (get_it)
│   ├── errors/failures.dart
│   ├── utils/extensions.dart
│   └── platform/platform_service.dart
├── data/
│   ├── models/           # DTOs (from OpenAPI)
│   ├── repositories/
│   │   ├── syllabus_repository_impl.dart
│   │   ├── planner_repository_impl.dart
│   │   ├── question_repository_impl.dart
│   │   └── analytics_repository_impl.dart
│   ├── datasources/
│   │   ├── api/          # Dio + Retrofit
│   │   ├── local/        # Drift (SQLite)
│   │   └── cache/        # In-memory + Hive
│   └── mappers/
├── domain/
│   ├── entities/
│   │   ├── syllabus_plan.dart
│   │   ├── daily_plan.dart
│   │   ├── question_paper.dart
│   │   ├── learner_analytics.dart
│   │   └── chapter.dart
│   ├── repositories/
│   │   ├── syllabus_repository.dart
│   │   └── ...
│   └── usecases/
│       ├── get_syllabus_plan.dart
│       ├── get_daily_plan.dart
│       ├── generate_question_paper.dart
│       └── ...
├── presentation/
│   ├── syllabus/
│   │   ├── pages/syllabus_page.dart
│   │   ├── widgets/chapter_card.dart
│   │   └── bloc/syllabus_bloc.dart
│   ├── planner/
│   │   ├── pages/daily_planner_page.dart
│   │   ├── pages/yearly_planner_page.dart
│   │   └── bloc/planner_bloc.dart
│   ├── question_bank/
│   │   ├── pages/question_bank_page.dart
│   │   ├── widgets/question_card.dart
│   │   └── bloc/question_bloc.dart
│   ├── analytics/
│   │   ├── pages/mastery_dashboard.dart
│   │   ├── pages/gap_analysis.dart
│   │   ├── pages/confidence_calibration.dart
│   │   └── bloc/analytics_bloc.dart
│   ├── settings/
│   └── shared/
│       ├── widgets/
│       ├── blocs/
│       └── themes/
└── l10n/app_en.arb
```

### 8.2 Key Screens

| Screen | Purpose | Backend Endpoints |
|--------|---------|-------------------|
| **Syllabus Explorer** | Browse CBSE syllabus by grade/subject/chapter; see LOs, time estimates, blueprint | `/syllabus/generate`, `/graph/query` |
| **Daily Planner** | FSRS-powered daily session (know/forgot/tired/motivated/confident) | `/planner/daily`, `/planner/revise` |
| **Yearly Planner** | Term-wise chapter allocation, period mapping, revision calendar | `/syllabus/generate`, `/calendar/generate` |
| **Question Bank** | Search/generate questions; filter by bloom, difficulty, competency | `/questions/search`, `/questions/generate` |
| **Answer Scheme Viewer** | Marking scheme with rubric, common errors, alternative answers | `/questions/{id}/answer-scheme` |
| **Mastery Dashboard** | Per-concept mastery, retention, confidence calibration | `/analytics/learner/{id}` |
| **Gap Analysis** | Prerequisite gaps, misconception flags, recommended remediation | `/analytics/gaps/{learner_id}` |
| **Teacher Tools** | Class analytics, blueprint creation, paper generation, evaluation | `/agents/execute` (BlueprintAgent, EvalAgent) |

### 8.3 Offline-First Strategy

```dart
// Drift local database for offline access
@DriftDatabase(tables: [
  SyllabusPlans, Chapters, Topics, LearningOutcomes,
  DailyPlans, SessionBlocks, QuestionPapers, Questions,
  LearnerModels, ConceptStates, MasteryStates,
])
class AppDatabase extends _$AppDatabase {
  // Sync strategy: background sync when online
  // Conflict resolution: server-wins for curriculum, client-wins for learner data
}
```

---

## 9. Evaluation Plan

### 9.1 Metrics by Component

| Component | Metrics | Target |
|-----------|---------|--------|
| OCR | CER, WER, Table F1, Equation LaTeX accuracy | CER < 2%, Table F1 > 0.9 |
| Layout | Heading detection F1, Reading order accuracy | F1 > 0.95 |
| Entity Extraction | Concept/LO/Competency P/R/F1 | F1 > 0.85 |
| Relation Extraction | Prereq/MapsTo/AssessedBy P/R/F1 | F1 > 0.8 |
| Graph Correctness | Cycle detection, Orphan rate, Coverage | 0 cycles, <1% orphans |
| Retrieval | nDCG@10, MRR, Recall@k, Citation precision | nDCG@10 > 0.7 |
| Answer Faithfulness | Citation coverage, Hallucination rate | 100% cited, <1% hallucination |
| Planner | Schedule feasibility, Capacity adherence | 100% feasible |
| Algorithms | FSRS prediction MAE, Mastery calibration | MAE < 0.1 |

### 9.2 Evaluation Datasets

- **CBSE Eval Set**: 500 annotated documents (syllabus, Q-papers, marking schemes)
- **Prereq Gold**: 12-corpus prerequisite evaluation (existing)
- **Retrieval Bench**: 1000 query-document pairs with relevance judgments
- **Learner Sim**: 90-day synthetic learner trajectories (existing)

---

## 10. Implementation Phases

### Phase 1: Document Ingestion + Extraction (Weeks 1-4)
- [ ] PDF discovery + checksum + dedup
- [ ] Document classification (15 types)
- [ ] Sarvam Vision integration (OCR + markdown)
- [ ] LayoutLMv3 layout analysis
- [ ] Table extraction (ensemble)
- [ ] Figure/chart detection + captioning
- [ ] Equation extraction (LaTeX)
- [ ] Q/A section detection
- [ ] Answer scheme / rubric extraction
- [ ] Chapter boundary detection
- [ ] Topic/subtopic extraction
- [ ] LO extraction + Bloom tagging
- [ ] Competency mapping
- [ ] Time estimate inference
- [ ] Quality scoring + corruption detection

### Phase 2: Full Ontology + Graph + Versioning (Weeks 5-7)
- [ ] Complete NodeType/EdgeType enum (60+ types)
- [ ] Graph schema with temporal versioning
- [ ] Graph store (SQLite + async)
- [ ] Graph builder from extractions
- [ ] Provenance tracking per node/edge
- [ ] Board/school overlay system
- [ ] Supersession/replacement logic
- [ ] Migration framework

### Phase 3: Hybrid Retrieval (Weeks 8-10)
- [ ] Vector DB setup (Qdrant)
- [ ] Embedding pipeline (multilingual-e5-large)
- [ ] Keyword index (BM25 + Tantivy)
- [ ] Hybrid search with RRF
- [ ] Chapter-aware retrieval
- [ ] Page-aware retrieval with coordinates
- [ ] Evidence-aware retrieval
- [ ] Cross-encoder reranker
- [ ] Graph-aware reranking

### Phase 4: Agent Orchestration + APIs (Weeks 11-14)
- [ ] BaseAgent framework + tool registry
- [ ] 12 specialized agents
- [ ] Orchestrator (DAG execution)
- [ ] FastAPI app with all routes
- [ ] Pydantic schemas (request/response)
- [ ] Auth + RBAC middleware
- [ ] Rate limiting + audit logging
- [ ] OpenAPI spec generation
- [ ] Dart model generation from OpenAPI

### Phase 5: Evaluation + Human Loop (Weeks 15-17)
- [ ] OCR/Layout/Entity/Relation eval pipelines
- [ ] Retrieval eval (nDCG, MRR)
- [ ] Faithfulness + citation eval
- [ ] Human review UI (low-confidence queue)
- [ ] Active learning from corrections
- [ ] Regression test suite

### Phase 6: Overlays + School Config (Weeks 18-20)
- [ ] Board version overlays (CBSE 2023/2024/2025)
- [ ] State board overlays
- [ ] School-specific calendars/holidays
- [ ] Teacher customization layer
- [ ] Multi-tenancy support

### Phase 7: Flutter App + Hardening (Weeks 21-26)
- [ ] Flutter project setup (Windows + Android)
- [ ] Clean architecture implementation
- [ ] Dio/Retrofit API client
- [ ] Drift local DB + sync
- [ ] Syllabus Explorer screen
- [ ] Daily/Yearly Planner screens
- [ ] Question Bank screens
- [ ] Analytics Dashboard screens
- [ ] Teacher Tools screens
- [ ] Offline-first sync
- [ ] Windows packaging (MSIX)
- [ ] Android packaging (AAB)
- [ ] CI/CD pipelines
- [ ] Load testing + monitoring
- [ ] Documentation + runbooks

---

## 11. Deployment Architecture

```yaml
# docker-compose.yml (production)
services:
  api:
    build: ./backend
    replicas: 3
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///data/academicos.db
      - VECTOR_DB_URL=http://qdrant:6333
      - OBJECT_STORE_URL=http://minio:9000
      - SARVAM_API_KEY=${SARVAM_API_KEY}
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
  
  qdrant:
    image: qdrant/qdrant:v1.8
    volumes: [qdrant_data:/qdrant/storage]
  
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    volumes: [minio_data:/data]
  
  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
    volumes: [./nginx.conf:/etc/nginx/nginx.conf]

volumes:
  qdrant_data:
  minio_data:
```

---

## 12. Flutter Build Targets

```yaml
# frontend/pubspec.yaml key targets
flutter:
  assets:
    - assets/fonts/
    - assets/icons/
    - assets/lottie/

# Windows
# flutter build windows --release
# Output: build/windows/x64/runner/Release/
# Package: MSIX via msix-packaging tool

# Android
# flutter build appbundle --release
# Output: build/app/outputs/bundle/release/app.aab
# Play Console upload ready

# Web (optional)
# flutter build web --release
```

---

## 13. Migration Strategy for Future UI/App Screens

1. **Backend-First**: All academic logic lives in backend; Flutter is a thin client
2. **API Versioning**: `/api/v1/`, `/api/v2/` — never break existing clients
3. **Feature Flags**: LaunchDarkly-style flags for gradual rollout
4. **BFF Pattern**: If mobile needs different aggregation, add BFF layer
5. **GraphQL Gateway**: Future: GraphQL federation for flexible queries
6. **Widget Library**: Shared Flutter package for academic widgets (reusable across apps)

---

## 14. Roadmap Summary

| Quarter | Focus | Deliverable |
|---------|-------|-------------|
| Q1 | Phase 1-2 | Ingestion pipeline + Full ontology + Graph |
| Q2 | Phase 3-4 | Hybrid retrieval + Agents + APIs |
| Q3 | Phase 5-6 | Evaluation harness + Overlays + School config |
| Q4 | Phase 7 | Flutter app (Windows/Android) + Production hardening |

---

## 15. Next Steps (Immediate)

1. **Create ARCHITECTURE.md** ✓ (this document)
2. **Set up backend monorepo structure** with `uv`/`poetry`
3. **Set up Flutter project** with clean architecture
4. **Implement Phase 1.1**: PDF discovery + classification
5. **Implement Phase 1.2**: Sarvam Vision + LayoutLM integration
6. **Generate OpenAPI spec** → auto-generate Dart models
7. **Build first Flutter screen**: Syllabus Explorer (read-only from graph)

---

*This architecture is designed to be the stable "academic brain" that multiple UIs and agents can plug into without rewriting the core. The Flutter app is just the first consumer.*