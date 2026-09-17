# Requirements by layer — Frontend vs Backend

Companion to [`TRANSCRIPT_REQUIREMENTS_MATRIX.md`](TRANSCRIPT_REQUIREMENTS_MATRIX.md),
which tracks requirements against the client transcript. **That document's tables
are organised by transcript section; this one is organised by which layer has to
deliver the work**, so a frontend owner and a backend owner can each read their
own column.

Reconciled 2026-09-17. Status reflects what was verified on that date, not what
was intended when a feature was written.

**Legend:** ✅ done · ◐ partial · ✗ missing/absent · ⚠️ works in code but
verified-broken in one of the two releases

> **Read this first.** "Done" below means *the code exists and its tests pass*.
> It does **not** mean a user has walked through it. Only one area — the teacher
> schedule views — has ever been exercised interactively against a live backend
> (2026-09-14, partially blocked by CanvasKit having no DOM to automate). See
> "Verification depth" at the end.

---

## Part 1 — Backend requirements

### 1.1 Data model & persistence
| Requirement | Status |
|---|---|
Canonical hierarchy as first-class queryable entities: Board → AcademicYear → Grade → Subject → Unit → Chapter → Topic → Subtopic | ✅ |
Stable `canonical_id` bridge so scheduling and assessment share one curriculum model (§24) | ✅ |
Official CBSE curriculum as the source, hand-verified against the 2025-26 CBSE PDFs — Class 10, 4 subjects only | ◐ |
Durable remote store for the 10 flat tables (assessments, papers, practice sets, graded evaluations, scan sessions, school templates, users, sessions, audit log, learner events) | ✅ code / ⚠️ 4 tables missing in production |
WAL + `busy_timeout` on all 17 SQLite stores | ✅ |
Provenance tracking for ingested corpus (`SourceRegistry`) | ✅ |
Immutable audit log (CERT-In, 180-day retention) | ✅ code / ⚠️ not durable in production |

### 1.2 Curriculum & calendar
| Requirement | Status |
|---|---|
`AcademicYear` with real ISO start/end dates | ✅ |
Working-day computation: weekly-offs + alternate-Saturday rule + holidays, with correct precedence | ✅ |
Multi-day block holidays (`Holiday.end_date`) | ✅ |
Admin-configurable period duration (`PeriodConfiguration`) | ✅ |
Persisted `SubjectPeriodAllocation` (periods/week per subject) | ✅ |
`SubjectTimetableSlot` — real per-subject weekday slots | ✅ |
Textbook TOC ingestion → Unit/Chapter materialization | ✅ |
LLM Topic/Subtopic extraction with proposal → review → approve (never auto-accepted) | ✅ |
**School selects which book edition it uses** | ✗ |
**Period-by-period school timetable** ("Science meets 2nd period Monday") | ✗ |
Official CBSE **Hindi** Class X syllabus (needed before Hindi can be tagged) | ✗ |

### 1.3 Scheduling & reporting
| Requirement | Status |
|---|---|
`ScheduledLesson[]` — real dated lessons from curriculum order × time estimate × working days | ✅ |
Teaching-time estimate per subtopic, grounded in the real calendar | ✅ |
Delivery-sequence reordering, per level (Unit/Chapter/Topic/Subtopic) | ✅ |
Reschedule on disruption: PUSH (shift forward) / ADJUST (single lesson) | ✅ |
Coverage report: planned vs. taught, coverage %, pace %, period variance | ✅ |
Delayed-topics report with days overdue | ✅ |
`TeacherAssignment` (teacher ↔ book) | ✅ |
`StudentEnrollment` (student ↔ grade) | ✅ |

### 1.4 Auth, roles & tenancy
| Requirement | Status |
|---|---|
Three real roles: `principal` (= Admin/Management), `teacher`, `student` | ✅ |
Self-selected role can never escalate to `principal` | ✅ |
Bearer-token sessions + logout + 401 recovery path | ✅ code / ⚠️ sessions not durable in production |
School-scoped isolation on every query | ✅ where `school_id` exists |
Principal bootstrap key gating the first admin | ✅ |
**`school_id` on `PaperStore` / `PracticeStore` / `ScanSessionStore`** | ✗ |

### 1.5 Assessment engine
| Requirement | Status |
|---|---|
Question pool from real CBSE papers with official marking schemes | ✅ |
Every question carries a topic, so topic-wise selection works | ◐ **CBE corpus only.** 3,382 questions across 37 subject × grade pairs carry no topic; 27 of those pairs have no labeled reference at all. 496 Mathematics class 10 questions are mapped to strand level in `syllabus/inferred_topics.json` (`cbe_strand_centroid_v1`, 95% cross-validated precision, distribution-shift caveat recorded there) |
Figure-dependent items served whole | ◐ 95 of 124. Items referring to a figure that could not be attributed are served without one and flagged `metadata.figureState`; a wrong figure is worse than none |
Blueprint-driven section balancing (Bloom, type, difficulty) | ✅ |
Subtopic-level question selection (`map_subtopics`, `subtopic_ids`) | ✅ |
Chapter tagging across subjects (`embedding_chapter_tagger`) | ✅ |
PARAKH/CBSE standardization: differentiation tiers, parallel sets A/B/C, CBQ ≥50%, internal choice, value-point marking schemes | ✅ |
1-click prompt-to-paper generation | ✅ |
PDF question-paper + answer-key export | ✅ |
Paper delivery by email | ✅ |

### 1.6 Platform & ops
| Requirement | Status |
|---|---|
Authenticated API surface | ✅ 130 operations, 104 secured |
Durability selection: Cloud SQL ▸ Supabase ▸ local SQLite | ✅ |
Health + storage diagnostics (`/health`, `/health/storage`) | ✅ |
School data export | ✅ (no restore path yet) |
Blob storage for scan media + curriculum snapshots | ✅ on Supabase / not yet GCS |

---

## Part 2 — Frontend requirements

Surfaces are Flutter, one codebase, two sub-products — see
[`PRODUCTS_AND_RELEASES.md`](PRODUCTS_AND_RELEASES.md). Which sub-product each
surface ships in matters: the **Mobile** build has no backend at all.

### 2.1 Teacher surfaces
| Requirement | Ships in | Status |
|---|---|---|
"What do I teach today" — `/my-schedule` | both | ✅ |
Day / Week / Month / Year views over one data source (§38–41) | both | ✅ |
Mark a lesson Completed Yes/No + optional note | both | ✅ |
Daily planner with AI-suggested weekly timetable | both | ✅ |
Syllabus browser + chapter detail | both | ✅ |
Question bank browse/search | both | ✅ |
Practice session screen | both | ✅ |
Class management | both | ✅ |
Profile + settings (theme, language, notifications) | both | ✅ |

### 2.2 Principal / Admin surface — `/admin`
| Requirement | Status |
|---|---|
**Roster** tab — assign teacher to book, enroll student to grade | ✅ |
**Master Calendar Grid** tab | ✅ |
**Coverage & Pace** tab — KPI cards, variance breakdowns, overdue list | ✅ |
**Sequence Reorder** tab — drag-and-drop for all four levels | ✅ |
**Reschedule** tab — PUSH / ADJUST controls | ✅ |
**Calendar & Setup** tab — working days, period duration, holidays | ✅ |

### 2.3 Student & parent surfaces
| Requirement | Status |
|---|---|
Student `/student/schedule` — Overview + Day/Week/Month, strictly read-only (notes and `completedBy` scrubbed server-side) | ✅ |
Parent `/parent` — child syllabus completion, daily attendance/lesson tracking, growth-mindset guidance (§A8) | ✅ |

### 2.4 Assessment surfaces
| Requirement | Status |
|---|---|
Assessment list / create / review pages | ✅ |
Quick-generate modal (1-click from the AppBar) | ✅ |
Subtopic filter chips feeding paper generation | ✅ |
Blueprint review & edit | ✅ |
Paper export + school template maker | ✅ |
Evaluation screen with itemized marking + teacher override | ✅ |
Mobile scan capture (`/scan`) + scan history | ✅ |
Analytics: mastery dashboard, gap analysis, principal insights | ✅ |

### 2.5 Client platform
Everything here is client-only — no backend counterpart.

| Requirement | Ships in | Status |
|---|---|---|
Offline engine (`LocalApiClient` / `LocalPillarApi`, bundled corpus) | Mobile only | ✅ |
Encrypted Hive local storage | both | ✅ |
Biometric app lock | Mobile only | ✅ |
On-device OCR (ML Kit) | Mobile only | ✅ |
Client-side PDF generation | Mobile only | ✅ |
Repository + service-locator API abstraction | both | ✅ |
`go_router`, 24 routes, role-based access | both | ✅ |
401 → clear session → route to `/login` | Web only | ✅ |

---

## Part 3 — Full-stack features (both halves required)

The third column is where the gap is today, not whether the halves exist.

| Feature | Backend half | Frontend half | Where it stands |
|---|---|---|---|
Lesson schedule | `scheduling.py` + `/schedule` routes | `my_schedule_page.dart` | ✅ both; verified live once |
Mark lesson complete | `PATCH /scheduled-lessons/{id}` + authorization | bottom sheet in the schedule page | ✅ both; Yes/No tap not automation-verified |
Coverage reporting | `get_coverage_report` + routes | "Coverage & Pace" tab | ✅ both |
Reschedule | `adjust_lesson` / `push_lessons_after` + audit | PUSH / ADJUST controls | ✅ both / ⚠️ audit not durable in prod |
Sequence reorder | `PATCH .../sequence` × 4 levels | drag-and-drop | ✅ both |
Roster assignment | `POST /teacher-assignments`, `/student-enrollments` | Roster tab | ✅ both |
Student portal | `/my-class-schedule`, `/my-progress` | `student_schedule_page.dart` | ✅ both |
Subtopic selection | `map_subtopics` + `subtopic_ids` | filter chips in the create page | ✅ both |
Auth + roles | users/sessions/roles/bootstrap key | login page + token interceptor | ✅ both / ⚠️ sessions not durable in prod |
Curriculum extraction | LLM propose → approve pipeline | review/approve UI | ✅ both |

---

## Part 4 — Verification depth

Status labels above say nothing about *how far* something was verified. Measured
2026-09-16:

| Layer | Coverage | Evidence |
|---|---|---|
1. Backend logic | ~all | `pytest` — **1,716 passing, 15 skipped, 1 xfailed** (2026-09-17) |
2. Backend **end-to-end** (live API, real auth, cross-school scoping) | most backend rows | `tests/test_route_inventory.py::test_full_boot_*` |
3. Frontend compiles | all | `flutter analyze` against a **68-issue baseline** — zero *new* issues, not a clean run |
4. Frontend widget/unit | some | 117 tests, **3 currently failing** (2 need a live server on :8000, 1 pre-existing arithmetic mismatch) |
5. **Interactive UI → live backend** | **1 area, one pass** | 2026-09-14 — teacher Day/Week/Month/Year views, blocked elsewhere by CanvasKit rendering to a single `<canvas>` |
6. **Production (Render release)** | degraded | `users`, `sessions`, `audit_log`, `learner_events` return `PGRST205` — not durable |

**Summary of the summary:** backend is the more complete and better-verified
half, and its genuine gaps are narrow and named. The frontend is broad but
shallowly verified — almost every surface exists and compiles, and almost none
has been proven by a human using it. The two problems that break users *today*
are neither a frontend nor a backend gap; they are deployment and contract
problems, recorded in [`system-review.html`](system-review.html).
