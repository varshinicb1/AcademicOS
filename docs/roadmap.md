# Roadmap — 5 Phases (revised per learning-first strategy)

**North star:** not an AI tutor — a library of validated learning algorithms
backed by the world's best education knowledge graph. Most edtech products are
collections of features; we build an architecture that evolves for years.

> **Research objective:** discover the algorithms governing how children learn,
> forget, stay motivated, lose confidence, regain confidence, choose careers,
> and achieve mastery. Every document — curriculum, research paper, textbook,
> assessment, or policy — becomes reusable knowledge contributing to one or
> more algorithms.

## Real status (audited 2026-09-11)

Each phase heading below carries a percentage — measured against real code,
real file counts, and real test coverage on this date, not a guess. Method:
counted actual registered sources vs. real files on disk
(`academicos.cli stats` + `find` over `cbse-dataset`/`ncert-dataset`/
`cbse-model-answers`), grepped the graph schema for the literal node/edge
types a phase's own description calls for, and checked which
`algorithms/*.py` modules have a real (non-trivial, tested) implementation
vs. don't exist. Re-run this audit rather than trust these numbers once
several sessions' worth of work has passed — they will go stale exactly like
the "43 real CBSE sources" and directory-layout claims below already had.

| Phase | Status |
|---|---|
| 1 — Knowledge Base | ~35-40% |
| 2 — Student Brain Graph | ~30-40% (see caveat below) |
| 3 — Indian Education Graph | **0%** |
| 4 — Algorithms Library | ~55-65% |
| 5 — Human Learning Engine | ~60-65% (updated 2026-09-11 — see below) |
| **Weighted overall** | **~32-37%** |

(This table previously said Phase 5 ~50-60% / weighted ~30-35% even after
the Phase 5 narrative below was updated same-day — a real instance of the
exact doc-drift this file keeps warning about. Fixed here.)

**Re-checked 2026-09-13:** re-ran `cli stats` and grepped for the changes
made this session (Class 9 NCERT corpus added + wired in, Assessment-
Designer chapter tagging extended beyond Science). Real, verified work —
see Phase 1's checklist below — but it doesn't move any phase's percentage:
no new graph artifact, no new algorithm, Phase 3 untouched. Weighted overall
stays ~32-37%; not bumping it just because effort was spent this session.

**Re-checked 2026-09-14:** four real, tested backend features shipped this
session, all in `src/academicos/curriculum/` (the §10-14 academic calendar
and micro-scheduling engine `docs/TRANSCRIPT_REQUIREMENTS_MATRIX.md`
already tracks in detail): multi-day block holidays (`Holiday.end_date`),
delivery-sequence reordering (`PATCH .../sequence`), persisted per-subject
period allocations (`SubjectPeriodAllocation`), and real per-subject
weekday timetable slots (`SubjectTimetableSlot`, replacing a heuristic).
Full backend suite: 1113 passed. Same posture as 2026-09-13's note — real,
verified, valuable work, but it's teaching-execution/scheduling product
surface, not one of this roadmap's 5 phases; weighted overall stays
~32-37% for the same reason as before. See the transcript matrix's own
2026-09-14 re-audit note for the full detail rather than duplicating it
here.

---

## Phase 1 — The Knowledge Base — ~35-40% (in progress)

Output is NOT PDFs. Output is a knowledge graph where every concept knows:
prerequisites, difficulty, estimated learning time, common misconceptions,
Bloom taxonomy, visualization ideas, experiments, real-world examples.

Sources to structure:
- NCERT textbooks (Grades 1–12) + NCERT Exemplar
- CBSE Question Bank, Sample Papers, Marking Schemes
- Previous 15–20 years board papers
- Learning outcomes, NCF 2023, NEP 2020
- Teacher handbooks, lab manuals, DIKSHA resources

Status (re-measured 2026-09-11 — the "43 real CBSE sources" line below is
now stale; see the real count that replaced it):
- [x] Ingest → parse → extract → graph → retrieval → agents (AcademicOS core)
- [x] Corpus pipeline real and working: `academicos.cli stats` shows 6,971
      graph nodes, 7,259 edges, 11,153 chunks from 418 registered sources
- [x] OpenIE entity/triple extraction (Sarvam LLM) — graph densified
- [ ] Full CBSE corpus (800+ QP/MS, NCERT, model answers) — re-measured
      2026-09-14: resolved the registry status discrepancy where only 14
      sources showed `status="extracted"` despite 403 distinct extracted
      documents existing in the chunk index. Root cause traced and fixed in
      `SourceRegistry.register()` (an `ON CONFLICT` clause was
      unconditionally resetting status to `'registered'` on re-discovery).
      Data backfilled and verified against disk: **422 sources are now
      correctly tracked as `status="extracted"`** (including 410 real question
      papers and the 14 NCERT textbooks). Total registered sources: 3,355
      (2,756 unclassified `unknown`, 2,439 parsed). All 17 SQLite database
      stores across `src/academicos/` hardened with WAL mode and 60s busy
      timeouts for concurrent multi-user execution. Still short of the full
      15-year board paper corpus once broken downloads are purged.
- [x] Assessment-Designer chapter tagging beyond Science — added this
      session (`assessment/embedding_chapter_tagger.py`): sentence-embedding
      cosine-similarity match against `syllabus/cbse_syllabus.py`'s real
      CBSE chapter lists, replacing the Science-only keyword tagger
      (`chapters.py`) for Mathematics/Social Science/English at Class X.
      573/752 Mathematics, 322/403 Social Science, 61/134 English questions
      now carry a real chapter tag (none did before beyond Science). Hindi
      still has no syllabus JSON to tag against. Not one of this roadmap's
      headline phase deliverables, but real product-usable groundwork for
      the Assessment Designer across the subjects it's sold on.
- [x] Concept spine: misconceptions, difficulty, learning time per concept —
      correction to this audit (2026-09-11): `graph/curriculum.py` is a
      real, research-cited (Alatrash & Chatti 2025/26), tested
      (`test_graph_curriculum.py`) implementation the original pass missed
      entirely. Found and fixed why coverage looked stalled: the CLI's
      `--method rule` path was crashing on a missing spaCy model
      (`en_core_web_md`, now installed), and repeated runs re-profiled the
      same top-occurrence concepts instead of making progress (fixed with a
      skip-already-done default + `--force`). Real coverage: 1,031/1,153
      (89%) of quality-eligible concepts (occurrences>=3); the rest need
      `--method llm` (real API cost) or don't belong to a textbook at all.
- [x] Question→concept mapping (LLM-assisted, verifier-checked) — real,
      `src/academicos/qmap.py` + `storage/question_map.py` (261 lines), CLI
      `qmap`, 8/8 tests pass. Correction to this audit (2026-09-11): the
      original pass only grepped `graph/` and `extract/` and missed the
      module's actual top-level location — false negative, not a real gap.
- [ ] Unlimited-OCR for scanned artifacts (blocked on disk space)
- [~] GCS mirror sync — still disabled live (`sync_enabled=false` in
      `config/config.toml`, `academicos.cli stats` reports
      `"gcs": {"enabled": false}`), but the flag now actually means
      something: fixed 2026-09-11, `sync-gcs` previously ignored
      `sync_enabled` entirely and would sync regardless of it — a real
      correctness gap, now closed with a test-covered gate + `--force` +
      loop mode. Turning real syncing on requires installing the `gcs`
      extra (`google-cloud-storage`, not currently installed) and real
      service-account credentials — deliberately not done without your say

## Phase 2 — The Student Brain Graph — ~30-40%

Agent reads cognitive science, neuroscience, educational psychology,
motivation, executive function, memory, attention, developmental psychology,
AI tutoring. Output: the **Human Learning Graph** —

```
Sleep → Attention → Working Memory → Learning → Confidence → Motivation → Long-term Success
```

This phase turns `docs/research/learning-science.md` into validated,
parameterized model components (forgetting curves, spaced repetition,
self-efficacy, ICAP, etc.) that the algorithms consume.

**Real status (2026-09-11):** the parameterized model components genuinely
exist and are tested — `confidence_model.py`, `motivation_model.py`,
`attention_model.py`, `habit_model.py`, `forgetting.py` (FSRS-6). What does
**not** exist: the literal graph artifact this phase asks for. Grepped
`graph/store.py`'s actual `NodeType`/`EdgeType` enums for
Sleep/Attention/WorkingMemory-shaped types — none exist. The research has
been operationalized as standalone algorithm modules (which Phase 4 also
counts), not delivered as the Human Learning Graph structure itself.

## Phase 3 — The Indian Education Graph — 0%

Download and structure: ASER, UDISE+, NCERT, CBSE, state boards, DIKSHA,
UNESCO, World Bank, OECD, PISA, NIPUN Bharat, PARAKH, government circulars.
Understand the system graph:

```
Teacher → School → Parents → Village → District → Government → Child
```

**Real status (2026-09-11):** searched the entire source tree for ASER,
UDISE, DIKSHA, NIPUN, PARAKH, PISA — no real source file references any of
them. No file named anything like `aser`/`udise`/an India system graph
exists. This phase has not been started.

## Phase 4 — The Algorithms Library — ~55-65%

Instead of a chatbot: algorithms. Each is evidence-grounded, evaluated, and
versioned under `src/academicos/algorithms/`:

1. **Knowledge Mastery Score** — mastery % instead of marks (confidence +
   retention + application)
2. **Forgetting Prediction** — "when will this child forget?" (tomorrow /
   5 days / 2 weeks / 3 months) → auto-revision
3. **Motivation Prediction** — low motivation → reduce difficulty, insert
   game, short break, small success → confidence restored
4. **Career Discovery** — from observed behavior (questions asked, projects
   built, videos watched, reading habits, attention) → career graph
5. **Parent AI** — "don't teach. Just say this today: 'Great consistency
   this week.'"
6. **Teacher AI** — "today's priority: 12 students need fractions. Ignore
   chapter 8. Teach fractions."
7. Attention prediction, habit formation, emotional state, curiosity engine,
   revision scheduler, reward engine, study planner, confidence model,
   lifelong learner model.

**Real status (2026-09-11):** every one of the 15 concepts above has a real,
substantial, tested implementation — not stubs. 4,933 lines across 19 files
in `src/academicos/algorithms/`, every module has a dedicated test file
under `tests/`, all pass (925 tests green project-wide as of this audit).
Held to ~55-65% rather than higher because "evaluated" is a real bar this
doc sets, not decoration: `docs/compliance.md` has direct proof of
calibration-against-real-data for the *grading* engine specifically (a
measured 26% exact-match rate against real teacher marks), but no equivalent
calibration evidence exists yet for these *learning* algorithms
(forgetting/motivation/attention/etc.) against real longitudinal student
data — there may not be a real user base generating that data yet.

Actual repository layout (the directory-per-module structure below was the
original plan; real implementation consolidated related concepts into
fewer, flatter files — e.g. `forgetting.py` contains both forgetting
prediction and the revision scheduler, and `mastery.py` covers knowledge
mastery — rather than one directory per bullet above):

```
algorithms/
├── mastery.py            (Knowledge Mastery Score)
├── forgetting.py          (Forgetting Prediction + revision scheduler)
├── motivation_model.py
├── career_discovery.py
├── parent_guidance.py
├── teacher_assistance.py
├── attention_model.py
├── habit_model.py
├── emotion_model.py
├── curiosity_engine.py
├── reward_engine.py
├── study_planner.py
├── confidence_model.py
├── lifelong_model.py
├── misconceptions.py
├── learner_model.py       (shared base data structures)
├── fsrs.py, fsrs_fit.py    (spaced-repetition core)
└── daily_loop.py           (Phase 5's orchestrator — see below)
```

## Phase 5 — The Human Learning Engine — ~50-60%

Every day it asks: What does this child know? What have they forgotten? Are
they tired? How motivated? How confident? What should they study? How long?
When to break? Solve questions / watch video / revise / rest? Parents
encourage? Teacher intervene? → **Update learner model.**

Every interaction updates the learner model. This is the loop no edtech
company has built.

**Real status (2026-09-11):** `algorithms/daily_loop.py` (597 lines) is
explicitly labeled "P5.1 — The daily loop (phase-5 orchestrator)" in its own
docstring and genuinely does what this phase describes — it orchestrates
`forgetting.ForgettingModel`, `study_planner.StudyPlanner`,
`confidence_model.ConfidenceModel`, `attention_model.AttentionModel`,
`habit_model.HabitModel`, and `motivation_model.MotivationModel` into one
deterministic daily plan, tested (`tests/test_daily_loop.py`). What's
unverified: whether this runs as an actual live, continuously-updating loop
against real users, versus being a correct, callable function nobody is
invoking on a real schedule yet. Held at ~50-60% for that reason — the
mechanism is real, the *engine actually running* is not confirmed.

**Update (2026-09-11, second pass):** P5.1 was also a stale checklist entry
in `docs/plan.md` (marked backlog; this roadmap already had it right) —
corrected there too. P5.3 (90-day offline simulation) existed as
`scripts/simulate_daily_loop.py`, self-labeled "P5.3", but had never
actually run — 5 real bugs (`NameError`s from typos/undefined names at
import time). Fixed all five; it now runs and every headline claim in its
own docstring holds, with 7 new tests. Nudged to ~60-65%: a second real,
working offline-eval capability now exists where before there was silent
breakage nobody had caught.

**Update (2026-09-11, same audit):** P5.2's API surface gap is now closed —
`POST /v1/revise`, `/v1/plan`, `/v1/question/solve` added to `api/main.py`,
wrapping the already-tested algorithm modules rather than reimplementing
them; 10/10 tests including a real seeded-graph/event-store round trip
through the live FastAPI app. Wiring `EventStore` into a real server also
surfaced and fixed a genuine latent bug (`sqlite3.ProgrammingError` — the
store's connection was missing `check_same_thread=False`, unlike
`GraphStore`/`SourceRegistry`, so it worked in single-threaded CLI/test use
but broke the moment FastAPI called it from a worker thread). Nudged to
~55-60%: a real HTTP surface now exists for a client to call, but nothing
calls `daily_loop.py` on a schedule yet and no real user traffic has
exercised it — P5.3 (offline eval) and P5.4 (pilot) are still backlog.
