# Academic Data Model — the canonical curriculum hierarchy

**Status: Implemented, tested, and active in production (`src/academicos/curriculum/`).**
This resolves the single highest-leverage risk originally flagged in
`docs/TRANSCRIPT_REQUIREMENTS_MATRIX.md` (§24 of the master build prompt):
two incompatible curriculum representations previously existed in miniature
(`cbse_syllabus.py`'s chapter-level dataclasses vs. `qmap.py`/the graph's `Concept`
nodes). They are now unified via stable `canonical_id` bridges across
an authoritative, dedicated SQLite store (`CurriculumStore`).

All 46 Class 10 chapters across Science, Mathematics, Social Science, and
English have real, admin-approved Topic (138) and Subtopic (404) decompositions.
Recent operational extensions include multi-day block holidays (`Holiday.end_date`),
delivery sequence reordering (`PATCH .../sequence`), subject period allocations
(`SubjectPeriodAllocation`), and weekly timetable slots (`SubjectTimetableSlot`).

## 1. The core decision: two systems, one shared vocabulary

AcademicOS has two fundamentally different kinds of "what is this document
about" data, and they should **stay separate systems that share IDs**,
not merge into one:

**The knowledge graph** (`graph/store.py`, `NodeType`/`EdgeType`) — a
*semantic* model: `Concept` nodes extracted probabilistically from real
documents (OpenIE, confidence-scored), with prerequisites, misconceptions,
Bloom levels, difficulty. It's corpus-wide, cross-document, and inherently
fuzzy — the same concept can be phrased three different ways across three
documents and the graph's job is to notice that. This is the right engine
for retrieval, prerequisite mining, and "what does this question test."

**The curriculum/schedule model** (proposed here) — an *operational* model:
a specific school follows a specific book for a specific grade in a
specific year; that book has an authoritative, ordered
Chapter→Topic→Subtopic structure; each subtopic gets a time estimate;
subtopics get scheduled on specific calendar dates; a teacher either taught
one or didn't. This is administrative record-keeping with a single source
of truth per school-year, not a probabilistic extraction target. It needs
stable, admin-approved IDs that never silently change meaning — the exact
opposite property the knowledge graph optimizes for.

Forcing curriculum/scheduling data into `NodeType.SUBTOPIC` graph nodes
would inherit the graph's semantics (confidence scores, evidence chains,
document provenance) for data that has none of those things — a subtopic
in a school's teaching schedule isn't "extracted with 0.73 confidence," an
admin picked it. Forcing the knowledge graph's `Concept` model to also
carry this book's precise, authoritative sequencing would break every
existing prerequisite/retrieval consumer that already depends on `Concept`
meaning "a fuzzy semantic cluster," not "curriculum item #14."

**The bridge**: every `Subtopic` (and `Topic`, `Chapter`) in the new model
gets a stable `canonical_id`. `qmap.py` (question→concept mapping) is
extended to *also* resolve a `subtopic_id` alongside its existing graph
`Concept` match — same question, two independent tags, one from each
system, joined only by that id. Nothing about the existing graph/retrieval
pipeline changes. This is the "same canonical IDs" §24 asks for, achieved
without collapsing two systems that have genuinely different correctness
properties.

## 2. New module: `src/academicos/curriculum/`

Mirrors the existing `assessment/` package's pattern exactly — plain
SQLite-backed stores (`assessment/store.py`, `users.py`, `audit_log.py`),
Postgres-via-Supabase when configured (same `SupabaseTable` pattern
`users.py` already uses, for the same reason: Render's disk doesn't
survive a restart, and a school's entire curriculum/schedule disappearing
on a cold start would be a much worse version of the exact bug
`store.py`'s own docstring warns about for assessments).

```
src/academicos/curriculum/
├── models.py       # dataclasses: Board, AcademicYear, Grade, Subject, Book,
│                   #   Chapter, Topic, Subtopic, Calendar, WorkingDay, Holiday,
│                   #   PeriodConfiguration, TeachingTimeEstimate
├── store.py        # CurriculumStore: SQLite CRUD for all of the above
├── seed_cbse10.py  # imports cbse_syllabus.py's real Class X data as the
│                   #   starting Book/Chapter rows for the 4 already-covered
│                   #   subjects -- the one real asset this whole model can
│                   #   build on immediately, not from zero
└── routes.py       # /api/v1/curriculum/* -- admin CRUD + review/approve flow
```

## 3. Entities and fields

Every id is a short opaque string (`{prefix}_{uuid4 hex[:12]}`), matching
`users.py`'s `user_{...}` convention — not the graph's descriptive
`board:grade:subject:...` style, because these rows are meant to be
edited/reordered/renamed by an admin (§13's explicit "teach last chapter
first" requirement), and a human-readable-but-positional id would break
the moment something gets reordered. A separate `canonical_id` field
(assigned once, never recomputed) is what `qmap.py` and any future graph
cross-reference key against — stable identity, independent of display
order.

```sql
-- Board is a property of a school's curriculum config, not hardcoded
-- anywhere in application logic (per §4).
CREATE TABLE boards (
  id           TEXT PRIMARY KEY,
  name         TEXT NOT NULL,          -- "CBSE" | "ICSE" | "State Board: <name>"
  code         TEXT NOT NULL
);

CREATE TABLE academic_years (
  id           TEXT PRIMARY KEY,
  school_id    TEXT NOT NULL,
  label        TEXT NOT NULL,          -- "2026-27"
  start_date   TEXT NOT NULL,          -- ISO date
  end_date     TEXT NOT NULL,
  status       TEXT NOT NULL DEFAULT 'draft'  -- draft | active | closed
);
CREATE INDEX idx_years_school ON academic_years(school_id);

CREATE TABLE grades (
  id           TEXT PRIMARY KEY,
  academic_year_id TEXT NOT NULL,
  number       INTEGER NOT NULL,       -- 1-12
  section      TEXT                    -- "A", "B", null if ungraded/whole-cohort
);

CREATE TABLE subjects (
  id           TEXT PRIMARY KEY,
  grade_id     TEXT NOT NULL,
  name         TEXT NOT NULL,
  code         TEXT
);

-- The school's actual choice of book for a subject -- §6/§16. Not every
-- available CBSE/NCERT book, one deliberate selection per subject.
CREATE TABLE books (
  id           TEXT PRIMARY KEY,
  subject_id   TEXT NOT NULL,
  board_id     TEXT NOT NULL,
  title        TEXT NOT NULL,
  publisher    TEXT,
  source_doc_ids TEXT,                 -- json list of registry source_ids
                                        --   (bridges to the real, working
                                        --   ingest/parse/extract pipeline
                                        --   already in src/academicos/ingest/)
  status       TEXT NOT NULL DEFAULT 'selected'  -- selected | processing | ready
);

CREATE TABLE chapters (
  id           TEXT PRIMARY KEY,
  canonical_id TEXT NOT NULL UNIQUE,   -- e.g. cbse:x:science:chemical-reactions
  book_id      TEXT NOT NULL,
  name         TEXT NOT NULL,
  seq          INTEGER NOT NULL,       -- delivery order, independently
                                        --   reorderable from textbook order (§13)
  source_weightage_marks INTEGER       -- from cbse_syllabus.py where known;
                                        --   null for chapters with no official figure
);
CREATE INDEX idx_chapters_book ON chapters(book_id);

CREATE TABLE topics (
  id           TEXT PRIMARY KEY,
  canonical_id TEXT NOT NULL UNIQUE,
  chapter_id   TEXT NOT NULL,
  name         TEXT NOT NULL,
  seq          INTEGER NOT NULL
);
CREATE INDEX idx_topics_chapter ON topics(chapter_id);

CREATE TABLE subtopics (
  id           TEXT PRIMARY KEY,
  canonical_id TEXT NOT NULL UNIQUE,   -- what qmap.py resolves against
  topic_id     TEXT NOT NULL,
  name         TEXT NOT NULL,
  seq          INTEGER NOT NULL
);
CREATE INDEX idx_subtopics_topic ON subtopics(topic_id);

-- Separate from the entity itself (§27 lists it standalone) because the
-- same subtopic takes different real time at different schools/paces --
-- this is a school's estimate for a subtopic, not an intrinsic property
-- of the subtopic.
CREATE TABLE teaching_time_estimates (
  id           TEXT PRIMARY KEY,
  subtopic_id  TEXT NOT NULL,
  academic_year_id TEXT NOT NULL,
  estimated_minutes INTEGER NOT NULL,
  estimated_periods INTEGER,           -- derived from period_configuration below,
                                        --   stored too so a later period-length
                                        --   change doesn't silently reinterpret history
  method       TEXT NOT NULL,          -- 'marks_weightage_proportional' | 'admin_override' | 'llm_estimate'
  approved_by  TEXT                    -- admin user id, null until reviewed (§29's
                                        --   explicit "assign / approve teaching times" step)
);

CREATE TABLE period_configurations (
  id           TEXT PRIMARY KEY,
  school_id    TEXT NOT NULL,
  academic_year_id TEXT NOT NULL,
  period_minutes INTEGER NOT NULL      -- 30 | 40 | 45 | 50 | admin-set, never hardcoded (§8)
);

CREATE TABLE calendars (
  id           TEXT PRIMARY KEY,
  academic_year_id TEXT NOT NULL UNIQUE,
  weekly_off_days TEXT NOT NULL,       -- json list, e.g. ["sunday"]
  alternate_saturday_rule TEXT         -- e.g. "2nd,4th" | "all" | "none", admin-configurable (§10)
);

CREATE TABLE holidays (
  id           TEXT PRIMARY KEY,
  calendar_id  TEXT NOT NULL,
  date         TEXT NOT NULL,
  label        TEXT NOT NULL,
  kind         TEXT NOT NULL          -- 'holiday' | 'event' | 'unexpected_closure'
);
CREATE INDEX idx_holidays_calendar ON holidays(calendar_id);
-- working_days are computed (calendar_days - weekly_off - holidays), not
-- stored as their own rows -- §10 draws the distinction conceptually but
-- nothing needs the derived set persisted; it's a query, not a fact.
```

`ScheduledLesson`, `TeachingCompletion`, and `ScheduleRevision` (the actual
scheduling-engine output) belong in `MICRO_SCHEDULING_ARCHITECTURE.md`, not
here — this document is the curriculum *hierarchy* those tables will
reference (`scheduled_lessons.subtopic_id → subtopics.id`), kept separate
because the scheduling algorithm itself is a distinct design decision this
review round didn't ask for yet.

## 4. Relationship diagram (matches §28)

```
Board
  └─ AcademicYear (school + year, start/end dates)
       └─ Grade
            └─ Subject
                 └─ Book  (the school's actual chosen book)
                      └─ Chapter (seq = delivery order, reorderable)
                           └─ Topic
                                └─ Subtopic
                                     └─ TeachingTimeEstimate (per academic_year)
                                     └─ canonical_id ──┐
                                                        │ same id, two consumers
Question (existing, models/academic.py) ── qmap.py ────┘
                                     resolves subtopic_id alongside its
                                     existing graph Concept match
```

## 5. What already exists vs. what's genuinely new

| Piece | Status | This design's role |
|---|---|---|
| `syllabus/cbse_syllabus.py` — real, official, cited Class X data for 4 subjects, Unit→Chapter | Real, keep | `curriculum/seed_cbse10.py` imports it as the first `Book`/`Chapter` rows — the actual bridge from "real data that exists" to "the canonical model," not a rewrite |
| `syllabus/timetable.py` — proportional period allocation from marks-weightage | Real, keep | Becomes the `method='marks_weightage_proportional'` case for seeding `TeachingTimeEstimate` rows, pending admin approval — same real algorithm, now feeding a persisted, admin-reviewable record instead of an ephemeral API response |
| `qmap.py` — question→graph-Concept mapping | Real, keep unchanged | Gets one new method: resolve a question against real `subtopics` rows too (lexical fallback first, matching its existing offline-capable design; LLM-assisted later) |
| Topic/Subtopic content below chapter level | **Does not exist for any subject yet** | Needs real population — see open decision below |
| `NodeType.BOARD`/`ACADEMIC_YEAR`/`GRADE`/`UNIT` (declared, unused) | Dead enum values | Left alone. Not deleted (matches this session's practice of not breaking a documented-if-unused public type without being asked), but the curriculum module does not use them — this new SQLite-backed model is the real implementation, not the graph enum |

## 6. Open decision that needs your call before implementation

**How do Topic/Subtopic rows for real content get populated?** Three honest
options, not mutually exclusive:

1. **LLM-assisted extraction from the real NCERT textbook PDFs already in
   the corpus** (the same textbooks `curriculum.py`'s concept-profiling
   already reads for Bloom/difficulty) — propose Topic/Subtopic breakdown
   per chapter, admin reviews and approves before it's live (mirrors the
   existing `concept-profile --method rule|llm` pattern and this session's
   `--force`/approval conventions).
2. **Manual admin entry** — slower, but zero risk of a hallucinated
   subtopic reaching a real schedule before anyone looks at it.
3. **A hybrid**: LLM-proposed, `approved_by` stays null (and the row
   stays out of scheduling) until an admin explicitly approves it — the
   same "propose → verify" shape `qmap.py` already uses successfully for
   question→concept mapping.

I'd recommend (3) for consistency with how this codebase already handles
every other LLM-assisted-but-consequential step, but this is a real
product decision about how much you trust automated extraction for
content that will end up on a teacher's daily schedule — not mine to pick
unilaterally.

## 7. What this document does not cover

- The scheduling algorithm itself (date assignment, PUSH/ADJUST
  rescheduling) → `MICRO_SCHEDULING_ARCHITECTURE.md` / `RESCHEDULING_LOGIC.md`
- Teacher/student/admin role and portal design → out of scope for this
  round per your answer ("design the canonical model first"); `users.py`
  already has `teacher`/`principal` roles real and secured, a `student`
  role is a separate, smaller decision once there's a student-facing
  surface to grant it access to
- Class 10 Topic/Subtopic *content itself* — this document defines where
  it would live and how, not what the actual topics/subtopics for Science/
  Math/Social Science/English are
