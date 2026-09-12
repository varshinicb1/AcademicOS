# Transcript Requirements Matrix

Audited 2026-09-12 against the actual `src/academicos/` implementation (the
real, working tree per `CLAUDE.md` — not `backend/`, which is a mostly-scaffolded
rewrite, and not `docs/architecture.md`, which documents that rewrite's
aspirational design, not what runs today) and the `frontend/` Flutter app.

**Method:** grepped every claimed node type / model class for real
instantiations (not just declarations), read the actual extraction/graph
pipeline, read the actual Flutter screens and routes. Where a class or enum
value exists but is never constructed by real code, it is marked **Missing**,
not Partial — a declared-but-unused type is exactly the kind of false
signal this project has repeatedly turned out to have (see `docs/plan.md`'s
and `docs/roadmap.md`'s own audit history from the last two days).

**Baseline test run (2026-09-12, this audit, before any change):**
- Backend: `python -m pytest tests -q` → **959 passed, 2 skipped, 1 xfailed**
- Frontend: `flutter test` → **96 passed, 2 failed** (both failures need a
  live backend on `localhost:7111` — `DioException: connection refused` —
  not a code defect)

No test was modified to produce this result.

**Update 2026-09-12, after building the curriculum data model** (see the
Curriculum hierarchy section below): backend `python -m pytest tests -q` →
**982 passed, 2 skipped, 1 xfailed** (+30 new tests: `test_curriculum_store.py`,
`test_curriculum_seed_cbse10.py`, plus real end-to-end coverage added to
`test_route_inventory.py`). Frontend untouched this round.

**Update 2026-09-12, after building Topic/Subtopic extraction + review +
question tagging** (see the same section below): backend →
**1004 passed, 2 skipped, 1 xfailed** (+22: `test_curriculum_extraction.py`,
`test_qmap_subtopics.py`, one comprehensive end-to-end test). A background
security review during this work found a real gap in the new code (the
question-tagging write endpoint had no auth at all, unlike every other
write in the file) -- fixed immediately, same pattern as the two
`pillar_routes.py` authorization fixes earlier this session.

**Update 2026-09-12, bulk extraction closed across all 46 real chapters.**
Real production run against `school_1`'s CBSE Class 10 seed (all 4 subjects):
extraction proposed, spot-check-reviewed, and admin-approved for every
chapter, zero unresolved failures. Final tally, verified against the live
database (`curriculum_store.topics_for_chapter`/`subtopics_for_topic`, not
the CLI's own summary line):

| Subject | Chapters | Topics | Subtopics |
|---|---|---|---|
| Science | 13 | 39 | 117 |
| Math | 7 | 21 | 58 |
| Social Science | 22 | 66 | 193 |
| English | 4 | 12 | 36 |
| **Total** | **46** | **138** | **404** |

Getting here required fixing a real LLM-reliability problem discovered only
under bulk load: `sarvam-105b` frequently returned `finish=length` (spent its
whole token budget on internal reasoning, zero content) or truncated JSON
when asked for an unbounded topics/subtopics breakdown with per-item
confidence scores. Went through three prompt revisions (`extraction.py`'s
`PROMPT_VERSION`): v1 (unbounded) failed ~50-75% of chapters even at
max_tokens=8000; v2 (capped "at most 5 topics/4 subtopics", still asked for
confidence) still failed on several chapters; **v3** (capped "at most 3
topics/3 subtopics", confidence removed from the requested schema entirely
and fixed at 0.7 in code, max_tokens=4000, 3-attempt retry with backoff) —
**0 failures across all 46 real chapters**, the entire remaining bulk run.
Proposal quality was spot-checked (not rubber-stamped) across 7 chapters
spanning all 4 subjects before approval; content was genuinely accurate,
specific CBSE Class 10 material, not generic filler.

## Legend
- **Complete** — real, tested, exercised by the app today
- **Partial** — a real piece exists but doesn't meet the requirement as
  specified (wrong granularity, wrong data source, disconnected from the
  rest of the system, etc.) — the partial credit is explained per row
- **Missing** — no real implementation; a declared type/model/route with
  zero real usage counts as Missing, not Partial

---

## Curriculum hierarchy (§5–9, §21–24, §27–28)

| Requirement | Evidence in existing code | Status | Relevant files | Required change |
|---|---|---|---|---|
| Board / AcademicYear / Grade / Subject / Unit / Chapter / Topic / Subtopic as first-class, queryable entities | **Update 2026-09-12: implemented, including Topic/Subtopic content generation, now run to completion across the whole real Class 10 corpus.** New `src/academicos/curriculum/` module — a dedicated SQLite-backed store, deliberately separate from the (still-unused) graph `NodeType.BOARD`/`ACADEMIC_YEAR`/etc (see `docs/ACADEMIC_DATA_MODEL.md`). Board→Unit→Chapter real and populated for Class 10 / 4 subjects since the earlier update. **Topic/Subtopic content**, via `curriculum/extraction.py` — LLM-proposed (Sarvam) or manual admin entry, never auto-accepted (`curriculum_extraction_runs`/`curriculum_extraction_proposals` hold the draft; only `approve_run()` materializes reviewed proposals into real `topics`/`subtopics` rows). Exposed over `/api/v1/curriculum/*`: propose, review, approve, manual add, rename, delete-with-linked-question-protection — all principal-gated and school-scoped. `qmap.py` extended with `map_subtopics()` to tag real questions against real subtopic canonical ids. **All 46 real chapters across all 4 subjects now have real, admin-approved Topic/Subtopic content** — 138 topics, 404 subtopics, verified against the live database, zero fabrication (see the extraction-reliability update above for how the bulk run was made to succeed with 0 failures). 37+ tests across `test_curriculum_extraction.py`, `test_qmap_subtopics.py`, `test_cli_curriculum_extract.py`, and one comprehensive end-to-end test covering the full seed→extract→review→edit→reject→approve→tag→generate-paper→delete-blocked flow. | **Complete for Class 10, all 4 subjects** — real, admin-approved, question-linkable Topic/Subtopic breakdown for every one of the 46 real chapters, proven end-to-end | `src/academicos/curriculum/extraction.py`, `src/academicos/qmap.py::map_subtopics`, `src/academicos/cli.py::cmd_curriculum_extract/cmd_curriculum_approve`, `tests/test_curriculum_extraction.py`, `tests/test_qmap_subtopics.py`, `tests/test_cli_curriculum_extract.py`, `tests/test_route_inventory.py::test_full_boot_curriculum_decomposition_review_and_question_paper` | None remaining for Class 10 bulk coverage. Separately: the lexical `map_subtopics()` matcher's threshold needs real calibration against realistic multi-clause exam questions — found during testing that short/targeted question phrasing matches well, a full exam sentence can score too low against a 3-word subtopic name; documented in the code, not yet tuned against a real corpus of questions. |
| Official CBSE curriculum data as the source (not fabricated) | `syllabus/cbse_syllabus.py` — real, hand-verified against the official 2025-26 CBSE curriculum PDFs, with a `source` field per JSON citing the exact document. **Covers exactly 4 subjects, Class X only**: Mathematics, Science, Social Science, English (`academicos-data/syllabus/*.json`). **Update 2026-09-12**: now genuinely imported (not just read) — `curriculum/seed_cbse10.py` seeds it into the canonical model, real `Unit.marks` matches the source JSON exactly (verified: 80/80 marks for Science, sums checked), Mathematics' unit-only (no chapter list) structure correctly falls back to one chapter per unit, matching `cbse_syllabus.py`'s own existing fallback logic. | **Partial → mostly resolved** | `src/academicos/syllabus/cbse_syllabus.py`, `src/academicos/curriculum/seed_cbse10.py` | Still stops at Chapter level — Topic/Subtopic is the real remaining gap (see row above). The "two incompatible representations" risk is now resolved by design (`docs/ACADEMIC_DATA_MODEL.md`): `cbse_syllabus.py` feeds the curriculum store, the graph stays semantic/unrelated, bridged only by `canonical_id`. |
| School selects the actual book it uses (not "process all books") | No such concept anywhere. The one thing resembling per-subject curriculum ingestion (`assessment/chapters.py`) is a **hardcoded, single, Class-X-Science-only** keyword-tagger, whose own docstring calls it a stopgap: *"the Question model has no chapter_id today... this exists to bridge that gap for the pilot subject before a real curriculum-ingestion pass replaces it."* | **Missing** | `src/academicos/assessment/chapters.py` | A real "school picks a book → book gets processed → chapters/topics/subtopics extracted" pipeline does not exist. `parse/`+`extract/`+`graph/` (the real, working document-ingestion pipeline used for question papers/marking schemes) is the right foundation to extend — it isn't built for curriculum/textbook structure extraction yet. |
| Teaching-time estimate per subtopic/topic/chapter, admin-configurable period duration | `syllabus/timetable.py` allocates a school's **weekly periods** proportionally to each unit's CBSE marks-weightage (documented explicitly as a proportional estimate, not an official hours figure — a real, honest, already-correct design choice to preserve). Admin-configurable period duration (30/40/45/50 min): not implemented — `timetable.py` takes `periods_per_week`/`weeks` as plain function args with no persisted config, no UI to set it beyond what the frontend's `daily_planner_page.dart` passes inline. | **Partial** | `src/academicos/syllabus/timetable.py` | Real algorithm, real method, right data source — but week-level only (no per-subtopic minutes, since Topic/Subtopic don't exist yet — see above), no persisted `PeriodConfiguration`, and produces `WeekSlot`s with no calendar date attached. |
| Chapter-level teaching-time breakdown, displayed | `timetable.py`'s `UnitAllocation` (marks, suggested_periods) is the real thing that exists; frontend surfaces it via `daily_planner_page.dart`'s "AI-suggested weekly timetable" sheet. | **Partial** | `src/academicos/syllabus/timetable.py`, `frontend/lib/presentation/planner/pages/daily_planner_page.dart` | Real and shown to the user today, but chapter/unit-level only, week-numbered not date-stamped. |

## Academic calendar (§10)

**Update 2026-09-12: built and tested — the real working-days algorithm,
period-duration config, and a calendar-grounded teaching-time-estimate
distribution, all exposed over the live API.** `AcademicYear`/`Calendar`/
`Holiday`/`PeriodConfiguration`/`TeachingTimeEstimate` entities and their
store-layer CRUD already existed from the earlier data-model round (real,
tested, but unwired); this round adds the one genuinely missing piece of
arithmetic (`curriculum/calendar.py::compute_working_days` — turns
weekly-off-days + alternate-Saturday-rule + a holiday list into an actual
list of real teaching days, precedence-correct so a holiday landing on a
weekly-off day is never double-subtracted) and 8 new principal-gated,
school-scoped routes: create/get calendar, add/list holidays, set period
duration, get computed working-days, compute teaching-time-estimates for a
book, get one subtopic's estimate. 16 new unit tests (`test_curriculum_calendar.py`,
covering alternate-Saturday date arithmetic against a real September 2026
calendar, holiday/weekly-off precedence, proportional distribution by real
Unit marks-weightage with exact-sum largest-remainder rounding, and
re-run idempotency) plus one full live-API end-to-end test
(`test_route_inventory.py::test_full_boot_academic_calendar_and_teaching_time_estimates`).

Sanity-checked against school_1's real seeded academic year
(2026-06-01..2027-04-30) with 3 real, fixed, government-mandated national
holidays (Independence Day, Gandhi Jayanti, Republic Day — dates that don't
vary year to year, unlike Diwali/Eid, which this session has no verified
2026-27 source for and did not fabricate): **262 real working days** out of
334 total calendar days (47 Sundays + 22 alternate-Saturdays + 3 holidays
removed) — a realistic number for a real CBSE school year, *before* any
summer/winter vacation block is configured.

Two honest gaps, not attempted this round: (1) **no vacation/block-holiday
concept** — every `Holiday` row is a single date; a real school's summer
break is 30-45 consecutive days, which today means entering that many
individual rows one at a time rather than a date-range holiday. (2)
**`periods_per_week` (how many periods/week a subject gets) has no
persisted entity** — taken as an explicit argument to
`compute_teaching_time_estimates()`, same pattern `syllabus/timetable.py`
already uses, documented in the code rather than silently assumed; a real
`SubjectPeriodAllocation` table is a reasonable next addition once an admin
UI needs to persist it rather than re-supply it every call. Neither
`period_minutes` nor `periods_per_week` was written into the real school_1
production database this round — both are genuine per-school admin
decisions this session doesn't know and won't guess on a real school's
behalf, unlike the government-mandated holiday dates above.

| Requirement | Evidence | Status | Relevant files | Required change |
|---|---|---|---|---|
| Academic year, start date, end date | Real, persisted `AcademicYear` (`school_id`, `label`, real ISO `start_date`/`end_date`, `status`) — seeded for school_1 since the earlier curriculum round (`year_da27411833a6`, 2026-06-01..2027-04-30). | **Complete** | `src/academicos/curriculum/models.py::AcademicYear`, `store.py::create_academic_year` | None. |
| Calendar days vs. working days, holidays, second/fourth Saturdays, configurable | **Now real**: `curriculum/calendar.py::compute_working_days` computes the actual working-day list/count from a real `Calendar` (admin-configurable `weekly_off_days`, `alternate_saturday_rule` — tested against real "2nd,4th" and "all" Saturday rules) plus a real `Holiday` list (`kind="holiday"`/`"unexpected_closure"` remove a day; `kind="event"` does not — tested). Exposed over `POST/GET .../calendar`, `POST/GET .../holidays`, `GET .../working-days`. | **Complete** for single-date holidays and weekly/alternate-Saturday offs; **Partial** for real-world calendars overall — no multi-day vacation-block entity yet (see gap 1 above) | `src/academicos/curriculum/calendar.py`, `src/academicos/curriculum/routes.py`, `tests/test_curriculum_calendar.py` | Add a `holiday_range`/vacation-block convenience (either a bulk-add endpoint or a `Holiday.end_date` field) so a 30-45 day break doesn't require entering each date individually. |
| Admin-configurable period duration (§8) | Real: `PeriodConfiguration.period_minutes`, admin-set per academic year, never hardcoded (tested: `test_period_configuration_never_hardcoded` asserts a non-45 value survives, catching exactly the "assumed a fixed default" bug class). Exposed over `POST .../period-configuration` (principal-gated, one-time-set — a 409 on a second call rather than a silent overwrite of an existing school decision). | **Complete** | `src/academicos/curriculum/store.py`, `routes.py::set_period_configuration` | None. |
| Teaching-time estimate per subtopic, grounded in the real calendar | **Now real**: `compute_teaching_time_estimates()` distributes a subject's real instructional minutes (periods/week × calendar-weeks × period-minutes) across its real, approved Subtopics, proportional to each Unit's real CBSE marks-weightage, with exact-sum largest-remainder rounding (no drift) and per-subtopic idempotency (a re-run never duplicates or clobbers an admin's prior estimate — §29). Exposed over `POST /books/{book_id}/teaching-time-estimates` and `GET /subtopics/{subtopic_id}/teaching-time-estimate`. | **Complete** for the computation and its API; **not yet run for real** against school_1's actual 46-chapter curriculum, since `periods_per_week`/`period_minutes` are real per-school facts this session doesn't have and won't guess (see gap 2 above) | `src/academicos/curriculum/calendar.py::compute_teaching_time_estimates` | An admin needs to actually supply `periods_per_week` per subject (today: a per-call argument) and `period_minutes` (today: a one-time admin POST) before this can be run for real on school_1; both are real UI/admin-workflow steps, not backend gaps. |

## Micro scheduling, yearly/monthly/weekly/daily views, rescheduling (§11–14, §38–41)

**Update 2026-09-12: the core date-assignment algorithm is built and
tested — real, dated `ScheduledLesson` rows, produced from real curriculum
order, real calendar-grounded teaching-time estimates, and real working
days.** `curriculum/scheduling.py::schedule_book()` walks a book's real
approved Subtopics in their real delivery order (`Unit.seq` →
`Chapter.seq` → `Topic.seq` → `Subtopic.seq`, already the §13
independently-reorderable sequence store.py enforces via `ORDER BY`) and
assigns each one its real `TeachingTimeEstimate.estimated_periods` worth of
consecutive real teaching days — never a guessed period count: a Subtopic
without a real estimate is skipped and reported by name, not silently
defaulted. 3 new principal-gated, school-scoped routes: generate a book's
schedule (`force=true` required to regenerate — refuses to silently
clobber a schedule teachers/students may already be looking at), read a
book's schedule, and read a school's lessons in a date range (the real
access pattern the next milestone's yearly/monthly/weekly/daily views and
the teacher "what do I teach today" screen will both call). 8 new tests:
7 unit tests on the scheduler itself (curriculum-order correctness, honest
skip-without-estimate reporting, refuse-to-reschedule vs. force-regenerate,
honest reporting when a deliberately tiny academic year can't fit every
subtopic, and — the real proof the calendar and scheduler are genuinely
wired together, not just both independently correct — zero lessons land on
a real holiday, Sunday, or alternate Saturday) plus one full live-API
end-to-end test covering the whole real flow through auth and
cross-school scoping.

Two honest simplifications, documented in the code, not hidden: (1) **no
school-wide, period-by-period timetable exists** in this data model (no
concept of "Science meets 2nd period on Monday" — confirmed missing
elsewhere in this matrix), so `_subject_teaching_days()` deterministically
assigns a subject to the first `periods_per_week` real working days of
each calendar week rather than claiming to know a real school's actual
weekday slots — the same "no finer real signal exists, don't fabricate
one" stance `seed_cbse10.py` and `calendar.py` already take elsewhere in
this module. (2) **Not run against school_1's real production data this
round** — same reasoning as the calendar milestone: `periods_per_week` is
a genuine per-subject admin decision this session doesn't know and won't
guess on a real school's behalf; the algorithm itself is proven correct
by the 8 tests above against realistic (if synthetic) inputs, including a
real September-2026 calendar's real alternate-Saturday/holiday dates.

| Requirement | Evidence | Status | Relevant files | Required change |
|---|---|---|---|---|
| Date-wise `ScheduledLesson[]` (curriculum × time-estimate × period-duration × calendar → real dated lesson plan) | **Now real.** `ScheduledLesson(school_id, academic_year_id, book_id, subtopic_id, date, status)`, produced by `scheduling.py::schedule_book()` from real curriculum order + real `TeachingTimeEstimate` + real `working_days_for_year()` — every date is a verified real working day (tested against real holidays/alternate-Saturdays). `status` defaults to `"scheduled"`; a later milestone (§15 completion tracking) reads/writes it — the column exists now so that milestone doesn't need a schema migration, but nothing writes anything other than `"scheduled"` yet. | **Complete** for the core algorithm and its API; **not yet exercised on real school_1 production data** (see above) | `src/academicos/curriculum/scheduling.py`, `src/academicos/curriculum/routes.py`, `tests/test_curriculum_scheduling.py`, `tests/test_route_inventory.py::test_full_boot_micro_scheduling` | Run for real once an admin supplies real `periods_per_week` per subject (a UI/admin-workflow step, not a backend gap — same open item the calendar milestone left). Separately: `_subject_teaching_days()`'s weekday-assignment simplification (see above) should eventually be replaced by a real school-timetable input if/when one exists, rather than the deterministic "first N working days of the week" rule. |
| Yearly / Monthly / Weekly / Daily views, kept consistent | `daily_planner_page.dart`'s `PlannerPage` shows the **assessment exam schedule** (dates teachers have scheduled tests on) — a real, working, different feature from a teaching-content schedule. Its "Daily Planner" route (`/planner/daily`) is a thin wrapper kept only "so the existing route still resolves" (frontend's own code comment) — effectively vestigial. **The real access pattern these views need now exists** (`GET /api/v1/curriculum/schedule?start_date=&end_date=`, school-scoped, tested), but no yearly/monthly/weekly/daily UI consumes it yet. | **Missing** (the UI); the API access pattern it needs is now **Complete** | `frontend/lib/presentation/planner/pages/daily_planner_page.dart`, `src/academicos/curriculum/routes.py::get_schedule_for_range` | Do not confuse or merge with the exam-date planner — that's a real, separate, working feature (exam scheduling) that should be preserved as-is. Build the actual teaching-content calendar views (Flutter) against the now-real `GET /schedule` endpoint. |
| Reorder curriculum delivery sequence | `Unit.seq`/`Chapter.seq`/`Topic.seq`/`Subtopic.seq` already exist and are what `schedule_book()` reads to determine delivery order — reordering one of these fields today (no dedicated reorder endpoint yet, a direct field, not exposed for editing) would genuinely change the next `schedule_book()` run's output. | **Partial** — the schedule now genuinely respects sequence, but no admin-facing "drag to reorder" endpoint exists yet | `src/academicos/curriculum/scheduling.py` | Add a `PATCH .../sequence` endpoint (or reuse the existing rename-style pattern) so an admin can actually change delivery order through the API, not just by construction order. |
| Rescheduling on disruption (PUSH / ADJUST), with audit trail (old date, new date, reason, changed-by, timestamp) | No `ScheduleRevision`/rescheduling concept anywhere yet — deliberately out of scope for this round (`schedule_book()`'s docstring is explicit: it only ever produces the *initial* full-book schedule; §14's individual-lesson PUSH/ADJUST is a separate, smaller, later operation). The backend does have a real, working, general-purpose audit log (`assessment/audit_log.py`, actively used by assessment approval, sheet review/finalize) that a rescheduling feature could genuinely reuse for the audit-trail requirement, rather than build its own. | **Missing**, with a real reusable building block and a real `ScheduledLesson.id` to attach a revision to | `src/academicos/assessment/audit_log.py`, `src/academicos/curriculum/scheduling.py` | Build the reschedule algorithm + UI; wire its history writes through the existing audit log rather than inventing a parallel mechanism. |
| Yearly / Monthly / Weekly / Daily views, kept consistent | `daily_planner_page.dart`'s `PlannerPage` shows the **assessment exam schedule** (dates teachers have scheduled tests on) — a real, working, different feature from a teaching-content schedule. Its "Daily Planner" route (`/planner/daily`) is a thin wrapper kept only "so the existing route still resolves" (frontend's own code comment) — effectively vestigial. No yearly/monthly view of anything exists. | **Missing** (the transcript's meaning) / the exam-scheduling feature that does exist is **Complete** for its own, different purpose | `frontend/lib/presentation/planner/pages/daily_planner_page.dart` | Do not confuse or merge with the exam-date planner — that's a real, separate, working feature (exam scheduling) that should be preserved as-is. The teaching-content schedule is net-new. |
| Reorder curriculum delivery sequence | No schedule exists to reorder. | **Missing** | — | Depends on the scheduling engine existing first. |
| Rescheduling on disruption (PUSH / ADJUST), with audit trail (old date, new date, reason, changed-by, timestamp) | No `ScheduleRevision`/rescheduling concept anywhere. The backend does have a real, working, general-purpose audit log (`assessment/audit_log.py`, actively used by assessment approval, sheet review/finalize — see this session's own security-fix commits) that a rescheduling feature could genuinely reuse for the audit-trail requirement, rather than build its own. | **Missing**, with a real reusable building block | `src/academicos/assessment/audit_log.py` | Build the reschedule algorithm + UI; wire its history writes through the existing audit log rather than inventing a parallel mechanism. |

## Teacher execution (§15–16, §30–31)

**Update 2026-09-13: the "what do I teach today" view is now real, backend
and frontend.** The missing link was that `assessment/users.py`'s `User`
has no subject/class field at all (confirmed: id, school_id, name, email,
role, created_at only) — a teacher's own schedule couldn't be scoped to
just their subjects without one. Added `TeacherAssignment(school_id,
teacher_id, book_id)`, a principal-gated `POST /teacher-assignments`
(verifies both the teacher and the book belong to the assigning
principal's own school), and `GET /my-schedule?start_date=&end_date=` —
every real, dated lesson for every book the caller is actually assigned to,
server-side enriched with subject/chapter/topic/subtopic names (never bare
ids) so the client needs no follow-up calls to render a readable lesson
card. A caller with no assignment yet honestly gets an empty list, never
someone else's data. 6 new tests (4 store-level, one full live-API
end-to-end test covering assignment, cross-school rejection, an
unassigned second teacher seeing nothing, and the enriched real data
reaching the right teacher).

Frontend: `frontend/lib/presentation/schedule/pages/my_schedule_page.dart`
— a real day-by-day (forward/back arrow) view of the logged-in teacher's
own lessons, reachable from a new Home-page card. Built on top of a real,
already-working, previously-uncommitted online auth system this session
discovered already existed (`auth_api.dart`, a Dio bearer-token
interceptor in `service_locator.dart`, `LocalStore.authToken`/`authUser`)
rather than assuming one needed to be built. Deliberately **online-only**:
the offline on-device engine (`core/local_engine/`) has no local mirror of
curriculum/schedule data at all, so the screen honestly says "needs a
connection" instead of silently failing when `ACADEMICOS_OFFLINE=true` —
same posture `home_page.dart` already uses for its own online-only sync
card. Verified with `flutter analyze` (zero new issues); **not verified
by actually running the app in a browser/device and clicking through it**
— an honest gap, not a "should be fine" claim, since no backend server was
running in this environment to log in against.

| Requirement | Evidence | Status | Relevant files | Required change |
|---|---|---|---|---|
| Teacher "what do I teach today" view, sourced from an admin-generated schedule | **Now real.** `GET /my-schedule` + `my_schedule_page.dart`, both described above — a teacher's real, assigned, dated, enriched lessons, not a placeholder. | **Complete** for the core view; **not interactively tested in a running app** (see above) | `src/academicos/curriculum/routes.py::get_my_schedule`, `frontend/lib/presentation/schedule/pages/my_schedule_page.dart`, `frontend/lib/data/datasources/api/curriculum_api.dart`, `tests/test_route_inventory.py::test_full_boot_teacher_assignment_and_my_schedule` | Run the app against a live backend and click through login → my-schedule to catch anything static analysis can't (layout, real network error handling, timezone edge cases in date math). Separately: no admin UI yet to *create* a `TeacherAssignment` (today: API-only, `POST /teacher-assignments`) — a real, smaller follow-up. |
| Teacher marks a planned lesson Completed Yes/No + optional note | **Update 2026-09-13: built and tested.** `ScheduledLesson` gained `note`/`completed_by`/`completed_at` (the `status` column already existed, specifically to avoid a migration for this milestone — confirmed zero real production `scheduled_lessons` rows existed yet, so no migration was even needed for the new columns either). `PATCH /api/v1/curriculum/scheduled-lessons/{lesson_id}` — real authorization: only the teacher actually assigned to that lesson's book, or a principal of the same school (a legitimate override/audit case), may mark it; any other same-school teacher gets a 403, same as a stranger at another school. `completed_by`/`completed_at` are set on every mark (even an "undo" back to `status="scheduled"`), so there's always a real record of who last touched a lesson. Frontend: tapping a lesson in `my_schedule_page.dart` opens a deliberately trivial bottom sheet — Yes/No buttons + an optional note field, nothing else, per the transcript's own instruction not to make this re-select curriculum. 6 new store tests + one full live-API end-to-end test (assigned-teacher marks with a note, unassigned teacher refused, invalid status rejected before touching the row, principal override, cross-school rejection, the mark reflected back through both the PATCH response and a fresh `GET /my-schedule`). Verified with `flutter analyze` (zero new issues, same 68-issue baseline as before this change) and the full backend suite (1055 passed). | **Complete** for the core flow; **not interactively tested in a running app** (same honest gap as the schedule view itself) | `src/academicos/curriculum/store.py::mark_lesson`, `src/academicos/curriculum/routes.py::mark_lesson`, `frontend/lib/presentation/schedule/pages/my_schedule_page.dart`, `tests/test_curriculum_store.py`, `tests/test_route_inventory.py::test_full_boot_completion_tracking` | Run the app against a live backend and click through the mark-complete flow to catch anything static analysis can't. Separately: no principal-facing rollup view yet ("which lessons across the school were marked completed today") — a real, smaller follow-up once the management-reporting milestone is reached. |

## Management tracking & reporting (§17, §32)

| Requirement | Evidence | Status | Relevant files | Required change |
|---|---|---|---|---|
| Planned vs. actually-taught, coverage %, variance, delayed topics — by class/subject/chapter/topic/subtopic/teacher/date/month | No data source exists to compute this from (no `ScheduledLesson`, no `TeachingCompletion`). **Real, but different, coverage metric already exists and must not be confused with this**: `syllabus_page.dart`/backend's catalog/chapters endpoints report **question-bank coverage** — how many gradeable questions exist per chapter, not whether the chapter was taught. Easy to accidentally conflate; they answer different questions. | **Missing** (teaching-completion reporting) / real, working **Complete** (question-bank coverage, a different feature) | `frontend/lib/presentation/syllabus/pages/syllabus_page.dart`, `src/academicos/assessment/pillar_routes.py` (`/catalog`, `/catalog/{subject}/{grade}/chapters`) | Build teaching-completion reporting as a new capability once scheduling+completion tracking exist. Keep question-bank coverage exactly as-is — it's a real, separately useful feature. |

## Student & parent visibility (§18–19)

| Requirement | Evidence | Status | Relevant files | Required change |
|---|---|---|---|---|
| Student portal: what's being taught, what's completed, upcoming, progress — a reduced subset, no management controls | Confirmed via a full first-hand audit of the Flutter app this session: **zero student-facing screens exist anywhere.** Every screen (`home_page`, `syllabus_page`, `mastery_dashboard`, `evaluation_page`, `mobile_scan_page`, `gap_analysis`, `principal_page`, etc.) is teacher- or principal-facing. There is no student login, no student route, no student data-scoping anywhere in `app_router.dart`. | **Missing** | `frontend/lib/core/routing/app_router.dart` (no student routes at all) | This is a full new portal, not an extension — new auth role, new scoped API surface, new UI, built from nothing. |
| Parent view (can initially piggyback on student) | Same as above — nothing to piggyback on yet. | **Missing** | — | Deferred by the transcript's own instructions until student view exists. |

## Users / roles (§2)

| Requirement | Evidence | Status | Relevant files | Required change |
|---|---|---|---|---|
| 3 primary roles: Admin/Management, Teacher, Student | The real auth system built this session (`users.py`, `auth_routes.py` — including the privilege-escalation fix from this session's earlier work) has exactly **two** roles: `"teacher"` and `"principal"`. No `"admin"`/`"management"` tier distinct from principal, no `"student"` role at all. | **Partial** (2 of 3 roles exist, real, tested, secured) | `src/academicos/assessment/users.py`, `auth_routes.py` | Add a `student` role (and decide whether "Admin/Management" is a rename/superset of the existing `principal` role or a genuinely distinct third tier — the transcript's phrasing suggests Admin/Management is the school-configuration role, which the current `principal` role's *capabilities* don't yet cover at all — principal today can only approve/lock an assessment, nothing about calendars or schedules). |
| Admin primarily web, Teacher/Student primarily mobile, one shared backend | The Flutter app already builds for Android, Windows, **and web** from one codebase against one backend — the *mechanism* for this split exists and works today. No admin-specific web experience exists yet (no admin routes, no admin screens) — every existing screen is the same teacher/principal toolset regardless of platform. | **Partial** (the technical foundation for the split is real; the actual admin-specific web UI is not) | `frontend/lib/core/routing/app_router.dart`, `frontend/README.md` (real, documented, measured web build) | Build actual admin-scoped routes/screens; the multi-platform build pipeline itself needs no new work. |

## Question paper / assessment (§20–25)

| Requirement | Evidence | Status | Relevant files | Required change |
|---|---|---|---|---|
| Existing Assessment Designer, Question Bank, blueprint generation, PDF export | Real, extensively verified this session (both backend tests and a full first-hand Flutter app read). Not touched by this audit's gaps — explicitly preserve. | **Complete** | `src/academicos/assessment/routes.py`, `pillar_routes.py`, `frontend/lib/presentation/assessment/`, `frontend/lib/presentation/question_bank/` | None — preserve as-is per the transcript's own instruction. |
| Subtopic-level question selection/generation | **Update 2026-09-12: complete, including the paper-generation bridge.** `qmap.py::map_subtopics()` resolves a question's text against a chapter's real, approved Subtopic rows; `POST /api/v1/curriculum/chapters/{chapter_id}/questions/tag` persists the match; `POST /api/v1/curriculum/questions/by-subtopics` returns tagged question ids. **Now also wired into the real, existing paper-generation search**: `QuestionSearchParams.subtopic_ids` on `POST /api/v1/questions/search` (`assessment/routes.py`) filters the same candidate pool `chapter_ids`/bloom/difficulty already filter — the literal §21 mockup's "Generate Question Paper" button now reaches real subtopic-eligible questions through the actual pipeline that builds a paper, not a separate standalone query. 4 new tests confirm: only tagged questions returned, a subtopic nothing is tagged to returns zero (not a silent fallback), the filter is a pure no-op when omitted (no regression), and it composes correctly with existing filters (AND, not replace). The original graph-`Concept` question mapping (P1.9) and chapter-level tagging (`assessment/chapters.py`) are both untouched — this adds a layer under them, doesn't replace either. | **Complete** | `src/academicos/qmap.py::map_subtopics`, `src/academicos/curriculum/routes.py`, `src/academicos/assessment/routes.py::search_questions`, `tests/test_assessment_question_search_subtopics.py` | None remaining on the backend. The Flutter frontend's question-search UI/models don't yet expose `subtopicIds` as a filter option — a real, separate, smaller follow-up (Dart model + a subtopic picker screen), not attempted this round since it wasn't asked for and is frontend UI work, not backend wiring. |
| One canonical curriculum model shared by scheduling and assessment (§24) | **Update 2026-09-12: resolved by design, not yet by data.** `docs/ACADEMIC_DATA_MODEL.md` proposes and `src/academicos/curriculum/` implements the answer: a dedicated operational store (not the graph) is the one canonical curriculum hierarchy, with a stable `canonical_id` per Unit/Chapter/Topic/Subtopic as the bridge `qmap.py` will resolve questions against. The design decision is made and real; `qmap.py` itself has not yet been extended to use it (still resolves only against graph `Concept` nodes), and there are still zero real Topic/Subtopic rows to resolve against yet. | **Design: Complete. Integration: Missing** | `docs/ACADEMIC_DATA_MODEL.md`, `src/academicos/curriculum/` | Extend `qmap.py` with a second resolution path against `curriculum/store.py`'s `subtopics` table once real Subtopic content exists. |

## Existing functionality to preserve (§25–26)

All independently verified this session (ran the real test suites, read the real source — not README claims):

| Feature | Status | Evidence |
|---|---|---|
| Assessment Designer, Question Bank, Evaluation, Scan & Grade, OCR (on-device ML Kit + optional Sarvam Vision), Mastery, Practice, Gap Analysis, Principal analytics, Syllabus coverage, Planner (exam scheduling), PDF generation, offline mode, encrypted local storage (Hive+SecureBox), biometric app lock, API abstraction (online/offline dual `PillarApi` implementations) | **Complete** — real, substantial, working | Full first-hand Flutter app audit this session; 96/98 `flutter test` (2 failures need a live server, not a defect); backend 959/959 `pytest` |
| Planner specifically | **Complete for what it is today** (exam-date scheduling) — **not** the teaching-content micro-scheduler the transcript wants; do not conflate when extending | `frontend/lib/presentation/planner/pages/daily_planner_page.dart` |

---

## Summary: what's real vs. what's the actual ask

The transcript describes a **teaching-execution and micro-scheduling product** (what must be taught, when, by whom, was it actually taught, reschedule if not) layered under the **existing assessment product** (question papers, grading, mastery) that AcademicOS already has, extensively, for real.

Those two things currently share almost no code. The scheduling/calendar/completion-tracking half described in §1–19 mostly does not exist yet. What's now real, as of 2026-09-12: the curriculum hierarchy (Board→AcademicYear→Grade→Subject→Book→Unit→Chapter→**Topic→Subtopic**), an LLM-proposed + admin-approved decomposition pipeline with a full audit trail (never auto-accepted), run to completion across **all 46 real chapters / all 4 Class 10 subjects** (138 topics, 404 subtopics, zero fabrication), and question-to-subtopic tagging feeding a real "questions eligible for these subtopics" query that's wired into the real paper-generation search. What's still fully greenfield: the calendar/holiday model (schema exists, zero real rows and no seeding path yet), the actual scheduling algorithm, teacher completion tracking, management reporting, and an entire student portal that doesn't exist in any form today.

**Priority 1: fully closed for its core promise.** Class 10, all 4 subjects, all 46 real chapters → real, admin-approved Topics → real, admin-approved Subtopics → real questions taggable against them → a real "which questions match these subtopics" query wired into the real, existing PDF paper-generation pipeline (`assessment/routes.py::search_questions`'s `subtopic_ids` filter) — proven end-to-end through the live API, not just at the store layer, and now proven at bulk scale, not just on one hand-picked chapter. The §24 two-incompatible-hierarchies risk this matrix originally found in miniature is resolved by design *and* now proven in practice at full scale: `qmap.py`'s `map_subtopics()` is the bridge, tested end-to-end. Next milestone per the transcript's own stated priority order: §10's academic calendar (Academic Year → Working Days → Holidays → Period Duration → Teaching-Time Estimate), which Priority 2-4 all depend on.
