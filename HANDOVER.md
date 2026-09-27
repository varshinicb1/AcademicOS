# AcademicOS — Handover (2026-09-27)

You are taking over AcademicOS from the original developer and the Claude Code sessions that built it.
Read in this order:

1. **This file**: what exists, access, set-up, where the work stands, what to build next.
2. **[`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md)**: what to build (v3, adopted 2026-09-27: grades 1-10,
   a web console, a teacher app and a student app). It supersedes the older scope in the PRD.
3. **[`docs/agent-workflow.md`](docs/agent-workflow.md)**: how work is done here (gates, the question-bank
   pipeline, releasing, evidence), plus the rules learned the hard way.
4. [`README.md`](README.md), then `CLAUDE.md` / `AGENTS.md` for architecture.

The previous handover (2026-09-21, answer-key linkage) is kept in `docs/history/`.

---

## 1. What is live

| Piece | Where | State |
|---|---|---|
| Web app (Flutter web) | https://vidyuthlabs.web.app (Firebase Hosting, project `vidyuthlabs`) | live, commit `caf5e3d` |
| Backend (FastAPI) | Cloud Run `academicos-backend`, `asia-south1`, https://academicos-backend-2eskom55ta-el.a.run.app | live, `/health` reports the commit |
| Database | Cloud SQL Postgres `academicos-pg` (durable tables) + SQLite snapshots | live |
| Blobs | GCS `vidyuthlabs-academicos-media` | live |
| Question-bank API | `/v1/*` on the same backend, API-key gated | live; no way yet to issue a key on live (audit D38) |
| Older Render release | `academicos-backend.onrender.com` | still answers on an old build; not the product; can be retired |

The live product is the **v2 scope**: a web console for classes 6-10 (paper generation, question bank,
calendar/lesson plan, principal dashboard). Under the v2 scorecard it measured **61.0 / 100**
(`docs/audits/2026-09-27-8db6636.md`). The **v3 requirements** (grades 1-10, teacher and student apps,
leave/substitution, homework, notifications) are mostly **not built yet**; see section 6.

## 2. Access you need (ask the product owner)

- **GitHub** `varshinicb1/AcademicOS` (private): write access. `master` is what is live.
- **Google Cloud** project `vidyuthlabs`: Cloud Run admin, Cloud Build editor, Artifact Registry writer,
  Cloud SQL client, Secret Manager accessor, Storage admin, **Firebase Hosting** admin.
- **Secrets** live in Secret Manager only, never in the repo: `principal-bootstrap-key`,
  `postgres-password`, `acos-llm-api-key` (bound as `ACOS_LLM_API_KEY` and `SARVAM_API_KEY`).
- **The first principal account** on live is created by the owner with the bootstrap key; there are no
  credentials in this repo and none should be added.
- **GitHub Actions** minutes ran out until **2026-10-01**. Until then deploy by hand:
  [`docs/deploy-by-hand.md`](docs/deploy-by-hand.md). After that, a push to `master` deploys through
  `.github/workflows/deploy-gcp.yml` (keyless, Workload Identity Federation).

## 3. Set up a machine

```bash
python -m venv .venv && . .venv/Scripts/activate      # Python 3.12
pip install -e ".[dev,api,ocr,retrieval,gcs,postgres,mcp]"
python -m pip install en_core_web_md@https://github.com/explosion/spacy-models/releases/download/en_core_web_md-3.8.0/en_core_web_md-3.8.0-py3-none-any.whl
cd frontend && flutter pub get                          # Flutter 3.44.9 stable
```

- Run locally: `python -m academicos.cli serve --port 8010`, then
  `flutter run -d chrome --dart-define=ACADEMICOS_API=http://localhost:8010/api/v1`.
- Gates (both must pass before any merge to `master`):
  - `pytest tests -q -p no:cacheprovider`: about 3,645 pass, 113 skip and 8 xfail. It takes about 20 minutes.
  - `cd frontend && flutter analyze --no-fatal-infos`: 7 info notes are expected.
  - `flutter test --exclude-tags live-backend -j 1`: 381 pass, in about 3 minutes.
- Tools used by the release: `gcloud`, Node (`npx firebase-tools@13`, `npx openapi-typescript@7.13.0`).

## 4. Machine load: read this first

The previous laptop **overloaded and shut down twice**. On a laptop, run **one heavy job at a time**:
a full pytest run, a Flutter test run, `flutter build web`, or a Cloud Build upload. Do not run swarms of
parallel agents. Two rules that also prevent false failures:

- **Never edit files in a checkout while its full suite runs.** Source-scan tests read files at run time.
- **Never rebuild `frontend/build/web` while pytest runs.** `api/main.py` mounts that directory at import.

## 5. Repository map

| Path | What |
|---|---|
| `src/academicos/assessment/` | papers (`paper*.py`), question pool and selection (`pool.py`, `selection.py`, `paper_templates.py`), chapter filing (`chapter_filing.py`), time saved (`paper_timing.py`), question-bank API (`qbank_routes.py`, `qbank_engine.py`), auth/users/invites, audit log, consent, scanning and grading |
| `src/academicos/curriculum/` | board → subtopic hierarchy, academic years, **terms**, holidays, subject timetable slots, teacher-book assignments, dated lesson plans (`scheduling.py`), book editions |
| `src/academicos/corpus/` | source importers (CBSE board/SQP/CBE, NCERT Exemplar) and **the one serving gate** (`bank_merge.py`) |
| `src/academicos/syllabus/` | syllabus and taxonomy, topic tagger, bank health report |
| `src/academicos/mcp/` | the question-bank MCP server |
| `src/academicos/api/` | FastAPI app (`main.py`) and **`route_policy.py`** (who may call each route) |
| `src/academicos/algorithms/` | FSRS spaced repetition, mastery and knowledge models (research; reusable for progress tracking) |
| `frontend/` | one Flutter codebase: the web console, and an offline Android build (`ACADEMICOS_OFFLINE=true`) |
| `academicos-data/` | the served question bank (`syllabus/questions.json`), refusals (`_merge_excluded.json`), syllabus and taxonomy JSON, bank health |
| `scripts/` | bank pipeline (`build_*_bank`, `apply_chapter_tags`, `tag_question_bank`, `merge_question_banks`), `bank_health.py`, `export_openapi.py`, `web_cache_bust.py` |
| `tests/`, `frontend/test/` | the two suites |
| `deploy/gcp/`, `firebase.json`, `Dockerfile` | the GCP release |
| `contract/` | the committed OpenAPI schema and TypeScript types (a test holds them current) |
| `docs/` | requirements, scorecard and audits, runbooks, compliance, design system, research |
| `backend/` | an abandoned rewrite; do not use |

## 6. Gap analysis: v3 requirements against the code (2026-09-27)

This section was measured by reading the code, not by running it. Requirement IDs are from `docs/REQUIREMENTS.md`.

| Area | What exists | Gap |
|---|---|---|
| **Question bank QB-1..13** | 5,429 served questions, every one with a marking scheme. Classes 6-10 Maths (289-857 per class) and Science (247-504). Sources: NCERT Exemplar 4,192, CBSE sample papers 783, CBSE competency items 435, board papers 19. One serving gate; bank health report; chapter/topic tagging for about half of the bank. | **Grades 1-5: nothing.** English, Hindi and Social Science 6-10 are almost empty. No NCERT textbook exercises imported yet. No unofficial or AI-assisted source with a review queue. Difficulty and Bloom level are inferred, not judged (QB-11). Content fidelity: 16 of 20 standard papers print an unanswerable question (audit D31, D26, D45; the bank rebuild for this is already authorised). |
| **Question bank API API-1..6** | `/v1` search/get/coverage/facets, an MCP server, API keys (`api_keys.py`) | No key issuance on live and no durable key store (D38). Chapter filter differs from the builder's (D39, a regression). Paging and error contract gaps (D52, D64, D65). **No homework-generation endpoint (API-2).** |
| **Exam automation EX-1..9** | Guided builder, quick paper, hand-pick, swap/pick/remove, sets, OR choices, PDF paper and key, time saved per paper; the competency share against CBSE's 50% and a tiers-unavailable sentence shown before generating (Task 125, live) | Real tiers need judged difficulty (QB-11); the competency share is 4-22% in Maths/Science 6-10, so most papers cannot reach 50% until the bank has more competency items. Half-yearly papers fall short of marks (D18). No review/approval workflow, datesheet, invigilation, marks entry or report cards. School name/logo not printed by default (D41). |
| **Admin and dashboard ADM, ROLE** | Roles `principal`, `teacher`, `student`; invite-only registration; a role policy on every route; audit log; admin console with roster, coverage and pace, reschedule, calendar setup, book editions; insights card (per-term exam coverage, time saved) | **No delegated admin or permission sets (ROLE-1).** No parent role. No bulk import. Terms cannot be declared on the web yet (D27). A section is only a label on a grade (`Grade.section`); nothing is scheduled per section. The dashboard lacks substitution, homework and progress data. |
| **Scheduling SCH-1..9** | Academic year, terms, holidays (multi-day), period configuration, **per-subject weekday slots** (`SubjectTimetableSlot`: subject, weekday, period), teacher → book assignments, dated lesson plans with PUSH/ADJUST reschedule and audit | **No real timetable model.** No section × period × teacher × room data, so no clash detection, no teacher timetable and no solver (SCH-2, SCH-3). **No leave, no substitution, no compensation or lost-period debt** (SCH-5..7). The edge cases (SCH-8) are unhandled. |
| **Teacher app TA-1..9** | The shared Flutter codebase has a teacher "my schedule" page, a daily planner, papers and question bank, mobile scan. An **offline Android build** exists; the old phone stream's branch `feat/product-phone` has 8 unmerged commits and a `wip/product-phone-2026-09-26` snapshot. | **No separate teacher app.** No leave or substitution UI, no homework creation, no push notifications, no offline sync of timetable and lessons (the offline build runs a local engine instead of syncing). |
| **Student app SA-1..8** | `student_schedule_page`, `parent_portal_page`, `practice_session_page` (practice sets from remediation) in the shared app | **No separate student app.** No assignments (homework) model at all; practice sets are student-generated, not teacher-set. No parent account or linking. No young-learner mode. |
| **Notifications NTF, integrations INT** | An email mailer (`mailer.py`), a notification policy doc (`docs/notifications.md`), a Sarvam LLM provider behind an interface | **No push (FCM), no in-app inbox, no reminders or scheduler jobs, no WhatsApp/SMS, no Google sign-in, no CSV import.** |
| **NFR** | DPDP/CERT-In design in `docs/compliance.md` (5 of 22 ship boxes ticked), audit log, school scoping, security headers, cache-busting, hand-deploy runbook | Web first load 18-21 s on Slow 4G against a 10 s target (bundle breakdown below). Hindi UI missing. No error tracking. |

Web bundle, measured for the speed work: the CanvasKit renderer from Google's CDN is 1.6-2.2 MB brotli,
`main.dart.js` is 1.14 MB, and the four Inter TTFs are about 490 KB. Deferred imports, font subsetting,
and serving the content-hashed entry files as `immutable` (audit D29) are the levers.

## 7. Recommended roadmap

Milestones in dependency order. Each should be sized so one person with Claude Code can land it,
gate it and deploy it.

| # | Milestone | Why first | First tasks |
|---|---|---|---|
| **M0** | Stabilise what is live | Leaves a clean base | ~~Finish Task 125~~ (done, live as `caf5e3d`). Fix D39 (use `chapter_filing` in `qbank_engine` and MCP). Serve hashed entry files immutable (D29). Declare terms on the web (D27). |
| **M1** | School data model | Everything in v3 needs it | Sections as entities; teacher ↔ subject ↔ section allocations; rooms; bell schedules; delegated-admin permission sets (ROLE-1); parent accounts and linking; bulk CSV import (INT-3). |
| **M2** | Scheduling engine | The teacher app's core | Timetable model and a constraint solver (OR-Tools CP-SAT) with clash detection (SCH-2/3). Leave → substitution → compensation with a lost-period debt (SCH-5..7). An edge-case test suite (SCH-8). Lesson plans per section. |
| **M3** | Notifications platform | Both apps need it | Device registry, FCM push, in-app inbox, preferences/quiet hours, templates, a scheduler (Cloud Scheduler + Cloud Run jobs) for reminders and digests (NTF-1..3). |
| **M4** | Teacher app | The first mobile product | Split the Flutter codebase into a workspace (`packages/core`, `apps/web`, `apps/teacher`, `apps/student`). Today, lessons, leave, substitution duties, offline sync, and homework from the bank (TA-1..9, API-2). |
| **M5** | Homework and student app | Closes the loop | Assignment model, submissions, auto-grading of objective items, progress per topic (reuse `algorithms/` mastery/FSRS), student today/assignments/progress, parent mode with DPDP consent (SA-1..8). |
| **M6** | Question bank to grades 1-10 | The biggest content job | Import NCERT textbook exercises for grades 1-10. Close the English/Hindi/Social Science gaps. Content fidelity with the authorised rebuild. A review queue for unofficial/AI-assisted items. Judged difficulty/Bloom (QB-1..13). |
| **M7** | Integrations and polish | Best in market | WhatsApp/SMS, Google Calendar/Classroom, Hindi UI, web speed, exam review workflow, marks entry and report cards. |

Third-party APIs worth evaluating for these milestones (sign-in, holidays, push, SMS/WhatsApp, calendar
sync) are reviewed in [`docs/integration-candidates.md`](docs/integration-candidates.md).

Adopt the **v3 scorecard** (`docs/REQUIREMENTS.md` §12) and run a baseline audit before M1, so progress is
measured from the start. Use `docs/audits/` for the write-ups and `docs/product-scorecard.md` for the log.

## 8. Open branches and unfinished work

| Branch | State | What to do |
|---|---|---|
| `master` / `release/v1` | live + these docs | work from here |
| `feat/task-125` | merged as `caf5e3d`, live | history only |
| `feat/term-insights`, `feat/question-bank-merge`, `feat/product-{calendar,exemplar,gcp,paperux,security}` | merged | history only |
| `feat/product-phone` | offline Android app, 8 commits never merged (the phone was dropped from v2) | read before building the teacher/student apps; reuse what fits |
| `wip/product-calendar-2026-09-26`, `wip/product-phone-2026-09-26` | snapshots of uncommitted work from stopped sessions | the calendar one is the exporter/manifest work the 6 strict xfails in `tests/test_curriculum_seed_grades.py` wait for; unreviewed and ungated |
| `docs/audit-0927` | merged | history only |

Planned in the last session but **not started** (the audit defect IDs are in `docs/audits/2026-09-27-8db6636.md`):
- **API surfaces:** D39, D52, D64, D65, D10, D7, D62, D61, D38.
- **Terms on the web and dashboard honesty:** D27, D43, D47, D48, D49, D42, D50, D51, D46, D55.
- **Content fidelity:** D31, D26, D36, D37, D20, D45, D21, D54. The owner authorised rebuilding the bank and lowering a chapter floor to the measured count when fewer-but-answerable questions make it fail.
- **Speed:** 2.4, D29.

## 9. Things that will bite you

- **The served bank** (`academicos-data/syllabus/questions.json`) is rebuilt only in pipeline order (the
  docstring of `scripts/merge_question_banks.py`). There is one serving gate in `corpus/bank_merge.py`.
  Add rules inside it, and measure false positives by reading refused stems.
- **Every new route** needs a row in `api/route_policy.py` and an entry in `tests/test_route_inventory.py`
  (163 routes today). If the schema changes, regenerate the OpenAPI contract and TS types.
- **Deploy traps:**
  - `firebase-tools` must be v13; v15 ignores the token.
  - Cloud Run env vars need the `^@^` delimiter.
  - Run `scripts/web_cache_bust.py` after every web build.
  - A 200 on a missing asset is the SPA rewrite, not the asset.
  - The Cloud Build client can look stuck while the server build succeeds; check `gcloud builds list`.
- **Use the project venv's PyMuPDF (1.28).** An older one fails a PDF-render fixture.
- **Evidence:** a number is quoted with the command that produced it, and "done" means verified on the
  live system.
- **Ownership notes** in `docs/agent-workflow.md` §3 name files owned by another Claude session (the chapter view).
  That session is gone. As of this handover you own everything, but keep the rule for any parallel work.
