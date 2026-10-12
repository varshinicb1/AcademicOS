# AcademicOS: developer handover and requirements

| | |
|---|---|
| Prepared for | Shubham Pitekar (GitHub: shuence) |
| Prepared by | VidyuthLabs, product owner of AcademicOS |
| Date | 6 October 2026 |
| Engagement | Freelance, from 7 October 2026, 20 days in five phases (section 8) |
| Confidentiality | Covered by the NDA already signed. Everything in this repository is confidential: code, data, documents, school names and figures. |
| Commercial terms | Commission on revenue from sales of AcademicOS, as set out in the separate agreement. This document does not change those terms. |
| Live state at handover | Backend and web at commit `784b42b`, sellable-product score 55.4 / 100 (section 3) |

This document is the starting point. It tells you what AcademicOS is, what already works (so you do not build it twice), how the system is put together, the rules every change follows, what you are asked to deliver in the next 20 days, and how each delivery will be accepted.

Read it once fully before touching code. Where it disagrees with an older file in the repository, this document is newer; tell me about the disagreement so the older file can be fixed.

---

## 1. Reading order

1. This document.
2. `docs/REQUIREMENTS.md`: the full product requirements (v3, adopted 27 September 2026). Every requirement has an ID such as `SCH-4` or `QB-5`. Those IDs are used in code comments, tests, audits and in this document.
3. `docs/product-scorecard-v3.md` and the latest audit, `docs/audits/2026-10-05-784b42b-v3.md`: how the product is measured, and the measured state of every requirement with what still holds it back.
4. `CONTRIBUTING.md`: how changes reach `master`.
5. `docs/agent-workflow.md` sections 3 to 5: the question-bank pipeline and release rules.
6. `README.md`, `CLAUDE.md` and `AGENTS.md`: architecture notes kept for coding assistants. They are accurate and short; use them.

`HANDOVER.md` at the root is the previous handover (27 September). It is history now. Parts of it are out of date: CI is no longer blocked, email works through Composio, the scheduler runs and Google sign-in is configured.

---

## 2. The product

AcademicOS is a school operating system for CBSE schools, classes 1 to 10. It is sold to schools; the principal is the buyer, teachers and students are the daily users. It is deliberately not an ERP: no fees, admissions or transport.

There are four products on one backend:

| Product | Who | Where it runs |
|---|---|---|
| Web console | Principal, delegated admins, teachers | https://vidyuthlabs.web.app (Firebase Hosting) |
| Teacher app | Teachers | Android, built from the same Flutter code with `--dart-define=ACADEMICOS_APP=teacher` |
| Student app, with parent mode | Students and parents | Android, `--dart-define=ACADEMICOS_APP=student` |
| Question bank API | Partners and the school's own tools | `/v1/*` on the backend, API-key gated, plus an MCP server |

Backend: FastAPI on Cloud Run, https://academicos-backend-2eskom55ta-el.a.run.app (`/health` reports the deployed commit).

What the product does, in one paragraph: a principal sets up the school (classes, sections, subjects from the NCERT books, teachers, allocations, calendar, bell). The engine builds a clash-free timetable and a dated lesson plan for every section and subject. Teachers mark lessons taught, apply for leave, take cover, set homework from the question bank and build exam papers with marking schemes. The engine absorbs leave, holidays and lost periods and keeps the plan honest. Students see their day, homework, exams and progress; parents see their children. The principal sees the term: coverage against plan, papers set, cover filled, gaps, alerts.

The first school, a CBSE school in Hyderabad, is being onboarded now as a Phase 1 pilot. The pilot agreement is accepted inside the app (`/settings/pilot-agreement`). Treat the pilot school's data as production data from day one.

---

## 3. Where the product stands (6 October 2026)

The product is measured, not estimated. `docs/product-scorecard-v3.md` scores 79 requirements on a five-point rubric:

- **0**: missing.
- **0.25**: partial, or broken on its main path.
- **0.5**: code and tests exist, but it was never run end to end with real data.
- **0.75**: verified end to end with real data on one surface.
- **1.0**: verified on every surface it ships on, with no known defect.

The latest audit (5 October, commit `784b42b`) measured **55.4 / 100**:

| Area | Weight | Score | Plainly |
|---|---|---|---|
| Question bank | 20 | 6.15 | The weakest area. 6,035 served questions, all classes 6-10 Maths and Science heavy. Classes 1-5: 0 questions. Hindi: 0 served. |
| Examination automation (web) | 15 | 10.00 | Paper builder, quick paper, sets, PDF and DOCX, review workflow, datesheet, invigilation, marks entry, report cards. Works. |
| Scheduling engine | 15 | 11.67 | Calendar, timetable solver, lesson plans, leave, cover, compensation, edge cases. The strongest area. |
| Teacher app | 15 | 7.50 | Built and working in its web build. Never run on a phone, no signed build, no push. |
| Student app | 10 | 5.31 | Same: works in its web build, not on a device. Young-learner mode untested end to end. |
| Principal dashboard and admin | 10 | 6.94 | Setup wizard, term report, alerts, delegated admin, multi-campus owner. |
| Question bank API | 5 | 3.75 | `/v1`, MCP server, API keys, webhooks. |
| Notifications and integrations | 5 | 2.03 | In-app inbox works. Email works but is unverified for digests. Push not live. WhatsApp/SMS built, not configured. |
| Release readiness and compliance | 5 | 2.03 | Security headers and CSP done. Single instance, in-memory rate limiter, compliance checklist mostly open. |

The owner's target is 80 for a confident first sale and 90 for "best in market". The 20 days below are planned to move the score into the high 60s or above while making the system genuinely production grade. The score will rise only through measured delivery.

Gates code alone cannot close (they stay on the owner's list, but you will prepare for them): a reference school, counsel's position on redistributing CBSE content, a signed data-processing agreement per school, signed and distributed app builds, and a published price.

---

## 4. What already exists: do not rebuild

This is the most important section for saving time. Everything below is in `master`, deployed, and covered by tests. Before building anything, search the code for it. If you believe something here is wrong or worth rewriting, raise it first; do not rewrite on your own.

### 4.1 Backend (`src/academicos/`, Python 3.12, FastAPI)

| Area | What exists | Where |
|---|---|---|
| Auth and roles | Invite-only registration; roles principal, teacher, student, parent; delegated admin grants (users, calendar, timetable, leave, exams, qbank_review, reports) with class/section/subject scope; owner over several schools; sign-in by password, by emailed 6-digit code (principal, student, parent), and Google ID token. A route policy decides who may call each route. | `assessment/auth_routes.py`, `operations/sign_in_codes.py`, `api/route_policy.py` |
| Audit and privacy | Immutable audit log of admin actions; DPDP consent per student (parent-given); erasure of a student's or parent's data on request; security headers, CSP. | `assessment/audit*.py`, `assessment/erasure.py`, `assessment/authz.py` |
| School model | Academic years, terms, sections, subjects from NCERT books, allocations (teacher x section x subject, periods, co-teacher, room kind, doubles), rooms, bell schedules, setup in one call (classes 1-10). | `curriculum/school_model*.py`, `curriculum/school_setup.py` |
| Curriculum data | Board, book, unit, chapter, topic, subtopic. Classes 1-5 chapters come from each NCERT book's contents page (`academicos-data/syllabus/ncert_books.json`, 243 chapters, plus Hindi 6-9). Classes 6-9 seed the current 2026-27 books (Exploring Society, Poorvi, Malhar, Kaveri, Ganga). Topic proposals are reviewed by the principal before they count. | `curriculum/seed_cbse10.py`, `curriculum/decomposition_templates.py`, `syllabus/cbse_syllabus.py` |
| Calendar | Weekly offs, alternate Saturdays, holidays (multi-day), half days, exam windows, compensatory working days, events; ICS feed per person; holidays move lessons and notify the people affected. | `curriculum/calendar.py`, `curriculum/routes.py` |
| Timetable | OR-Tools CP-SAT solver: no teacher/room/section clash, max per day and consecutive, doubles, labs by clock time, unavailability, preview then publish, re-solve touching the fewest periods, live clash checks on manual edits. | `curriculum/timetable_solver.py`, `curriculum/school_model_routes.py` |
| Lesson plans | Dated plan per section and subject from syllabus x timetable x calendar; one action plans the whole school; fit to periods left for a mid-year start; taught / partly / not taught reflows the plan; term report flags plans that cannot finish. | `curriculum/scheduling.py`, `curriculum/routes.py` (`/lesson-plans`) |
| Leave, cover, compensation | Leave (full, half, periods; with a document), approval, school leave rules with automatic approval, balances, cover proposals with fair load, acceptance, escalation, lost-period debt and make-up, teacher check-in with late marking and a 9:00 check-in round. | `curriculum/cover*.py`, `curriculum/staff_policy*.py` |
| Homework and practice | Homework from the bank, set from the lesson's chapter, answered in the app or by photo, marked per question; adaptive practice and exam preparation from weak topics. | `operations/homework*.py`, `operations/practice_routes.py`, `algorithms/` |
| Exams | Paper builder and quick paper, sets, OR choices, tiers, competency share, PDF and DOCX, review and lock, datesheet with clash checks, invigilation roster, marks entry per question, analysis, CBSE grade-band report cards. | `assessment/paper*.py`, `operations/exams.py`, `operations/exam_routes.py`, `operations/marks_routes.py`, `operations/paper_review_routes.py`, `operations/report_cards.py` |
| Question bank | One serving gate, fidelity repairs and refusals, chapter and topic tagging, bank health report, the `/v1` API with keys, metering and webhooks, the MCP server. | `corpus/bank_merge.py`, `corpus/fidelity.py`, `assessment/qbank_*.py`, `mcp/` |
| Notifications | Inbox, push (FCM, needs config), email (Composio Gmail, live), SMS and WhatsApp (built, not configured), quiet hours, daily digest option, delivery tracking and retry, English and Hindi templates, next-action rule. | `operations/notifications.py`, `operations/messaging.py`, `assessment/mailer.py` |
| Automations | Scheduled jobs (homework due and overdue, cover escalation, digests, morning alerts, exam reminders, term report, staff check-in), run by Cloud Scheduler every 5 minutes. | `operations/automations.py` |
| Dashboard | Term report (web, Excel, PDF), alerts, owner overview, usage endpoint for operators. | `operations/term_report.py`, `operations/dashboard_routes.py`, `operations/usage_routes.py` |
| Pilot agreement | Versioned agreement text with SHA-256, accepted by the principal, audited; the console is gated until accepted. | `operations/pilot_agreement*.py` |

### 4.2 Frontend (`frontend/`, Flutter 3.44 stable)

One codebase builds the web console, the teacher app, the student app and an offline Android app (`docs/apps.md`). The phone apps reuse the web console's School pages (`lib/presentation/workspace/`) inside a phone shell with a bottom bar (`app_mode.dart`).

Already in place: the Emergera theme (the owner's brand, light and dark, with the aurora gradient), responsive layouts reviewed page by page at 390 px, the setup wizard, the pilot agreement gate, sign-in with password, emailed code and Google, Hindi strings for many screens (`workspace/strings.dart`), offline reads and a queue of writes (`Ops.send`), profiles on a shared family phone, the young learners' home for classes 1-5.

### 4.3 Data (`academicos-data/`)

The served question bank (`syllabus/questions.json`, 6,035 records), syllabus and taxonomy JSON for every class, `ncert_books.json`, decomposition templates, the bank health report. The bank is rebuilt only through the pipeline in `docs/agent-workflow.md` section 5; never edit `questions.json` by hand.

NCERT textbook PDFs for classes 1-10 (every chapter, plus each book's prelims with its contents page) and chapter transcriptions exist on the owner's machine (`ncert-dataset/`, `AcademicOS-academicos-data/corpus/ncert_chapters`). They are not in git. Ask for a copy when you start the question-bank phase.

### 4.4 Work done in the last week, so you know the latest decisions

| PR | What | Why it matters to you |
|---|---|---|
| #125 | Emailed sign-in codes, Phase 1 pilot agreement gate, scheduler set-up page | Sign-in and onboarding flows are settled |
| #126 | Holiday reflow fixes; term report flags plans that cannot finish | ADM-2 behaviour |
| #127 | Font subsetting and preloads; ops usage endpoint | Load speed work already done |
| #128-#131, #133 | Fixes from the customer guide shoot; light-theme gradients; phone layouts | UI is reviewed; do not restyle |
| #132 | Staff automation: leave rules, automatic approval, balances, late check-in | SCH-5 done |
| #134 | Classes 1-5 can be set up (book chapters from contents pages) | Primary classes exist |
| #135 | Classes 1-5 get dated plans | Primary planning works |
| #136 | Classes 6-9 seed the current books | Social Science and languages are correct |
| #137 | Audit: 55.4 | The baseline you start from |

---

## 5. Architecture and environments

```
 Browser / Android apps (Flutter)
          |  HTTPS, JSON, bearer token
          v
 Cloud Run: academicos-backend (FastAPI, 1 vCPU, 1 GiB, min 1, max 1 instance, asia-south1)
   |-- Cloud SQL Postgres "academicos-pg"   JSONB stores: users, sessions, invites, audit log, consents,
   |                                         papers, assessments, marking, learner models, practice
   |-- GCS "vidyuthlabs-academicos-media"   two SQLite snapshots (CurriculumStore, OperationsStore),
   |                                         uploads, scans, API keys
   |-- academicos-data/ (in the image)       served question bank, syllabus, books
   |-- Composio (Gmail)                      email: sign-in codes, notices, digests
   |-- Sarvam                                AI marking, OCR, translation (key in Secret Manager)
 Cloud Scheduler "acos-automations"  -> POST /api/v1/automations/run every 5 min (X-Cron-Key)
 Firebase Hosting "vidyuthlabs"      -> the web console
 Cloudflare Workers (workers/qbank, workers/question-gen) -> model-backed question generation, locked by token
```

**The one structural limit.** Two stores keep their tables in a local SQLite file and save the whole file to GCS as one object:
- `CurriculumStore` (`curriculum/store.py`): academic years, sections, timetable, plans, lessons, leave, cover and staff rules.
- `OperationsStore` (`operations/store.py`): notifications, homework, learning, guardians, exams, marks, reviews, grants, owners and the pilot agreement.

Between them they hold about 80 tables. Two instances would overwrite each other's saves, so Cloud Run is pinned to one instance (`--max-instances=1`, explained in `.github/workflows/deploy-gcp.yml`). This caps capacity and makes every restart a full snapshot reload. Moving both stores to Cloud SQL is the first production task (R-A1).

**Releases.** A merge to `master` runs `.github/workflows/deploy-gcp.yml`:

1. The full Python suite, about 13 minutes.
2. `flutter analyze` and `flutter test`.
3. The image is built and deployed to Cloud Run, then `/health` is checked for the commit.
4. The web is built against the new backend, the entry files are given content-hashed names, and it is deployed to Firebase Hosting.

A failing test stops the deploy. Allow 25 to 40 minutes from merge to live. Never deploy by hand while CI works; it races CI.

**Secrets** live in Secret Manager only and are wired by the workflow.
- Always wired: `principal-bootstrap-key`, `postgres-password` and `acos-llm-api-key`.
- Optional, wired when present, as listed in `deploy/gcp/optional-config.json`:
  - Composio: `acos-cfg-composio-*`;
  - SMTP: `acos-cfg-smtp-*`;
  - WhatsApp: `acos-cfg-whatsapp-*`;
  - SMS: `acos-cfg-sms-*`;
  - Google client id: `acos-cfg-google-client-id`;
  - FCM project: `acos-cfg-fcm-project`;
  - operator keys: `acos-cfg-ops-key`, `acos-cfg-cron-key` and `acos-cfg-web-origin`.
- A value never goes in git, a chat or a document. `ACOS_ENV=production` arms a startup guard that refuses placeholder secrets, CORS `*`, demo accounts and an unlisted LLM provider.

**Local set-up**

```bash
python -m venv .venv && . .venv/Scripts/activate        # Python 3.12, not 3.14
pip install -e ".[dev,api,ocr,retrieval,gcs,postgres,mcp]"
cd frontend && flutter pub get                            # Flutter 3.44 stable
python -m academicos.cli serve --port 8010
flutter run -d chrome --dart-define=ACADEMICOS_API=http://localhost:8010/api/v1
```

For a local school, set `ACOS_PRINCIPAL_BOOTSTRAP_KEY` to any local test value and register a principal with it. `D:/acos-wt/_int/run_backend_e2e.py` on the owner's machine is a working example: fresh data root, no real keys, a mail relay nothing listens on. Ask for it.

**Test commands**

- Backend: `pytest tests -q -p no:cacheprovider -p no:warnings`. 5,126 tests; 20 to 45 minutes on a laptop, about 13 in CI.
- Frontend: `cd frontend && flutter analyze && flutter test --exclude-tags live-backend`. 816 tests, about 3 minutes.
- During development run the test files you touched. Run the full suites once per PR head, before asking for review.

---

## 6. Rules every change follows

These came from real incidents. They are not negotiable.

1. **Every change is a pull request into `master`.** Small, one purpose each, with a description that says what changed, why, and how it was verified. The owner reviews and merges. Do not push to `master`, do not force-push shared branches, do not merge your own PRs.
2. **Both suites pass** before review. A PR that turns a test off, skips it or weakens an assertion to pass needs the owner's explicit agreement in the PR.
3. **Every new or changed route** needs:
   - a row in `api/route_policy.py`;
   - its entry in `tests/test_route_inventory.py` (356 routes today);
   - if the schema changed, a regenerated contract: `PYTHONPATH=src python scripts/export_openapi.py`, then `npx --yes openapi-typescript@latest contract/openapi.json -o contract/api-types.ts`.
4. **No swallowed errors in the app.** `frontend/test/no_swallowed_errors_test.dart` fails any `catch` that does not rethrow, throw or show `serverErrorMessage(e)`. Errors are shown to people in words that say what to do next.
5. **Caching.** Only the content-hashed entry files may be cached for long (`tests/test_production_guard.py`). A wrong cache rule once blocked three deploys.
6. **Evidence.** A number in a PR, a report or the product is measured, and the command that produced it is quoted. "Done" means verified on the running system; on live, checks are unauthenticated.
7. **Never create accounts or enter credentials on the live system.** The owner registers schools and principals through invite links. You work against a local backend with test values.
8. **Personal data.** Student and parent data never leaves the school's scope, never goes to the question-bank API, and never goes to a third party without a DPA. No real student data in tests, screenshots or logs.
9. **The served question bank** changes only through the pipeline (`docs/agent-workflow.md` section 5) and the one serving gate (`corpus/bank_merge.py`). Count false positives by reading refused items, not by trusting a rate.
10. **One heavy job at a time on a laptop**: a full test run, a web build or an image build. Do not edit files in a checkout while its full suite runs; some tests read source files at run time.
11. **Keep the existing UI language and brand.** The Emergera theme is the owner's exact brand. Plain words, no jargon, no internal ids on screen, every error says what to do.
12. **Do not use `backend/`**: it is an abandoned rewrite. Do not split the Flutter code into packages, change the scoring rubric, or re-derive the chapter lists without agreement.

---

## 7. Requirements for this engagement

"Production grade" means, concretely, the following. Each line is measurable and will be checked at acceptance.

| Concern | Bar |
|---|---|
| Availability | 99.5% monthly; an uptime check and an alert on failure; no single-instance data-loss path |
| Data safety | Daily automated backups of Cloud SQL and the media bucket; a restore drill performed and written up (time taken, data checked) |
| Scale | 40-section school, 100 concurrent users, p95 under 1 s on the main read routes, 0 errors (current baseline: 0 errors to 100 users, about 78 req/s, on one instance) |
| Security | Rate limiting that survives restarts and works across instances; OWASP ASVS level 2 checklist walked and written up; dependency audit clean of high/critical issues; no secret in git history going forward |
| Observability | Structured logs with request id and school id; error alerts; per-school usage visible to the operator |
| Performance | Web first load under 10 s on Chrome's Slow 4G and under 3 s repeat; app cold start under 3 s on a low-end Android; APK under 30 MB |
| Accessibility | WCAG 2.2 AA spot-checked on the web console's main flows; TalkBack and 130% font scale usable on both apps |
| Language | Every teacher-app and student-app screen in English and Hindi |
| Privacy | DPDP Act 2023: consent, purpose limitation, retention periods written and enforced, erasure, breach runbook (CERT-In 6 hours) |

The requirements below are grouped into five workstreams. IDs in brackets are the v3 requirement IDs they move. "Accepted when" is what will be checked.

### A. Platform and data

**R-A1 Move the two snapshot stores to Cloud SQL** [NFR-4, NFR-3]
- `CurriculumStore` and `OperationsStore` (about 80 tables between them) move to Postgres, alongside the JSONB stores that already live there.
- Write a migration script that copies a live snapshot into Postgres and is safe to re-run.
- Keep SQLite for local development and tests if that is simpler, behind the same interface.
- Then raise `--max-instances` to at least 2.

Accepted when:
- the full suite passes on both back-ends;
- a two-instance concurrency test (parallel writes to the same school) loses nothing;
- the migration has been rehearsed on a copy of production data, with row counts compared table by table;
- a rollback path is written down.

This is the largest single task. Start it in Phase 2 and do not let it slip.

If both stores cannot be moved within Phase 2, move `CurriculumStore` first: it carries the most writes from the most people. Keep `--max-instances=1` until both are on Cloud SQL. Then carry the rest into Phase 3, and tell the owner the day you know.

**R-A2 Backups and restore** [NFR-4]
- Turn on Cloud SQL automated backups with point-in-time recovery, and object versioning or a scheduled copy for the media bucket.

Accepted when: a restore into a scratch instance has been done, timed and written up in `docs/incident-response-runbook.md`.

**R-A3 Durable rate limiting** [NFR-2]
- Replace the in-memory limiter (`RateLimiter`) with one that works across instances and restarts. Postgres or Cloud Memorystore are both fine; choose the simpler one.
- Keep the current limits.

Accepted when: tests show limits hold across two app processes, and sign-in code verification keeps its daily limit.

**R-A4 Monitoring and alerting** [NFR-7]
- Set up an uptime check on `/health` and alerts on uptime, 5xx rate, latency and new error groups.
- Add structured JSON logs with request id and school id; per-school usage is already at `/api/v1/ops/usage`.

Accepted when: a deliberately failing check produces an alert to the owner's email.

**R-A5 Load and performance** [NFR-3]
- Re-run the load test against a staging service, or against live outside school hours with the owner's agreement, after R-A1.
- Measure web first load on Slow 4G with the current bundle.

Accepted when: the figures are in a committed report with the commands used, and they meet the bar above or the gaps are named with a plan.

**R-A6 Security pass** [NFR-2]
- Walk OWASP ASVS level 2 against the API and the web console.
- Run a dependency audit (`pip-audit`, `flutter pub outdated` and advisories).
- Fix what is high or critical.

Accepted when: `docs/security-review-2026-10.md` lists each check, its result and the fix or the reason it is acceptable.

**R-A7 Compliance closure** [NFR-1]
- Close the open boxes in `docs/compliance.md` that code and documents can close: retention periods enforced by a scheduled job, the breach runbook, the DPA template, data-flow records.
- Mark the ones that need counsel as such.

Accepted when: the checklist is updated and every closed box has evidence.

### B. Teacher and student apps on real phones

**R-B1 Two installable apps** [TA, SA, NFR gate]
- Gradle product flavors `teacher` and `student` with their own application ids (`applicationIdSuffix`), names and icons, so both install side by side.
- Release signing from a keystore the owner holds; never commit it.
- App bundles uploaded to Google Play internal testing; the owner holds the Play Console account.

Accepted when: both apps install from the internal testing track on two phones and sign in to live with accounts the owner provides.

**R-B2 Push notifications** [NTF-1, TA-7, SA-5]
- Wire FCM: Firebase config in the Android project, device registration (the backend already has the registry and sender; read `operations/notifications.py` first), and `ACOS_FCM_PROJECT` set by the owner.

Accepted when: a cover request, a leave decision, a homework assignment and an exam reminder each arrive as a push on a phone, and tapping one opens the right screen.

**R-B3 Device test pass** [TA-1..9, SA-1..8]
- Run every teacher and student flow listed in `docs/REQUIREMENTS.md` sections 6 and 7 on a low-end Android phone (₹8,000 class, 360-390 px wide) and on one mid-range phone.
- Record each flow in a test sheet: steps, result, screenshot.
- Fix what fails.
- Include TalkBack on the five main screens of each app and 130% font scale everywhere.

Accepted when: the test sheet is committed under `docs/device-tests/` and has no open P0 failure.

**R-B4 Offline and size** [TA-8, SA-8]
- Verify on a phone that today's and this week's data is readable with the network off, that queued actions send in order when it returns, and that the sync state is visible.
- Get the release APK under 30 MB (split per ABI if needed).

Accepted when: the result is recorded in the device test sheet with sizes.

**R-B5 Hindi in both apps** [NFR-6, TA-9]
- Every string on every teacher-app and student-app screen goes through the existing `tr()` mechanism (`frontend/lib/presentation/workspace/strings.dart`) with a Hindi entry. Settings already has the language choice.
- Use Sarvam for a first draft if you like, but a human reads every string before merge; the owner will arrange a reviewer.

Accepted when: a test fails on any untranslated string in the app screens, and the Hindi screens are in the device test sheet.

**R-B6 Young learners, classes 1-5** [SA-7]
- Drive the young learners' home and the parent-operated homework flow on a phone with a class 1-5 student.
- Read-aloud through Sarvam TTS is a stretch goal (P1).

Accepted when: the flow is in the device test sheet.

**R-B7 Homework suggestion by chapter id** [TA-4]
- "Suggest from the lesson" matches the bank by chapter name and misses where names differ (defect N-4-4, `operations/homework_routes.py`). Match by the chapter's canonical id or taxonomy id, falling back to name.

Accepted when: a test covers a chapter whose names differ between the plan and the bank.

### C. Question bank

**R-C1 Classes 1-5 questions** [QB-1, QB-2, QB-7]
- Today there are none, so no paper or homework can be made for classes 1-5. That is the most visible gap for a primary school.
- Build questions from the NCERT textbooks' own exercises for English, Hindi, Mathematics and EVS, classes 1-5, through the existing pipeline: transcriptions, `scripts/build_textbook_bank.py`, the merge and the serving gate.
- Every question needs its chapter, an answer key and a marking scheme with value points.

Accepted when:
- the bank health report shows questions in every class 1-5 subject;
- at least 60% of chapters have 5 or more questions;
- a class 3 paper and a class 3 homework can be made end to end.

**R-C2 Hindi served** [QB-12]
- Hindi questions exist in the pipeline, but 0 reach the served bank. Find where they are refused (gate, tagging or merge), fix the cause, and serve the ones that pass.

Accepted when: Hindi questions are served for classes 6-10, with a count per class and a sample of 30 read by a Hindi reader without a defect.

**R-C3 Review queue for unofficial and AI-written questions** [QB-5]
- 718 model-written class 9-10 questions are served without a reviewer's approval. The owner accepted that for now; the requirement is that such items are served only after review.
- Build the review queue on the web: the item beside its source quote, approve or reject with a reason, audited, under the existing `qbank_review` grant.
- Put the serving gate behind the review state for new AI-assisted and teacher-contributed items. Leave the existing 718 served until the owner decides; mark them clearly.

Accepted when: a new AI item cannot be served unapproved (test), and an approved one is served (test).

**R-C4 Difficulty that is judged, not guessed** [QB-11, EX-3] (stretch)
- The main paper builder sends no tier (`paper_builder_api.dart`); only the quick dialog does. Wire the tier into the builder.
- Show the tier only where measured or judged difficulty supports it, with the reason when it cannot.

### D. Notifications and integrations

**R-D1 Email verified end to end** [NTF-1, ADM-4]
- Email leaves the live backend through Composio. Verify on live, with an account the owner provides, that the weekly principal digest and a teacher's daily digest arrive, are readable on a phone, and are recorded as delivered.
- Fix what does not.

Accepted when: there are screenshots of received mails and the delivery records.

**R-D2 Principal alerts** [ADM-3]
- Run the automations on a planned school (local) and confirm each alert fires once with the right text: a section behind, an unfilled substitution, a lost period not made up, a paper not set by its deadline, homework overdue in bulk.
- Today the term report counts the current day's unmarked lessons as "behind"; alerts use a 5-lesson threshold. Decide with the owner whether the report should count up to yesterday.

Accepted when: a test per alert, plus a written run.

**R-D3 WhatsApp for parents** [INT-2] (stretch, only if the owner provides the WhatsApp Business account and an approved template)
- The sender exists in `operations/messaging.py`. Configure it and verify a notice on a phone.

**R-D4 Google sign-in on Android** [INT-1] (stretch)
- The web has it. Add it to the apps.

### E. Release and handback

**R-E1 Re-audit.** At the end, re-score every item you touched, following `docs/product-scorecard-v3.md` ("How to re-score"). Record it under `docs/audits/` and log it.

**R-E2 Runbooks.** Update `docs/deployment.md`, `docs/incident-response-runbook.md` and `docs/apps.md` for everything you changed: the new database, backups, monitoring and app releases.

**R-E3 Handback note.** A short `docs/handover/` note for whoever comes next: what changed, what is open, where the traps are.

---

## 8. Timeline: 20 days, five phases

Day 1 is Wednesday 7 October 2026 and day 20 is Monday 26 October 2026. These are calendar days; agree your rest days with the owner at the start and the dates shift with them. Each phase ends with a short demo to the owner (30 minutes, screen share) and the phase's PRs merged and live.

| Phase | Days | Dates | Work | Deliverables at the end of the phase |
|---|---|---|---|---|
| 1. Onboarding and baseline | 1-3 | 7-9 Oct | Access, local set-up, both suites green on your machine, read the docs, measure the baseline (load test, web first load, APK size, a device run of the teacher app's My day) | Baseline report in `docs/handover/` with the figures and commands; one small merged PR that fixes an open defect from section 9, to prove the workflow end to end; a written plan for R-A1 (schema, migration, rollback) reviewed by the owner |
| 2. Platform | 4-8 | 10-14 Oct | R-A1 (both snapshot stores to Cloud SQL), R-A2 (backups and a restore drill), R-A3 (durable rate limiting), R-A4 (monitoring and alerts) | Live on Cloud SQL with at least 2 instances; the restore drill written up; alerts proven to fire; no regression in either suite |
| 3. Apps on phones | 9-13 | 15-19 Oct | R-B1 (flavors, signing, Play internal testing), R-B2 (push), R-B3 (device pass), R-B4 (offline and size), R-B5 (Hindi in the apps, started), R-B7 | Both apps on the internal testing track; push working; the device test sheet with no open P0 |
| 4. Question bank | 14-17 | 20-23 Oct | R-C1 (classes 1-5 questions), R-C2 (Hindi served), R-C3 (review queue); finish R-B5 | Bank health report showing classes 1-5 and Hindi; a class 3 paper and homework made end to end; review queue live |
| 5. Hardening and release | 18-20 | 24-26 Oct | R-A5 (load and performance), R-A6 (security pass), R-A7 (compliance closure), R-D1 and R-D2, R-B6, R-E1 to R-E3 | Re-audit with the new score; security review and compliance updates; runbooks; handback note; final demo |

If something must give, protect in this order: R-A1 to R-A4 (production safety), R-B1 to R-B3 (phones), R-C1 and R-C3 (the bank). Stretch items (R-C4, R-D3, R-D4) come last. Tell the owner the day you see a phase slipping, not at its end.

---

## 9. Open defects you will meet

Confirmed open on `784b42b`. File references are where to start, not a diagnosis.

| Defect | Where | Requirement |
|---|---|---|
| The two SQLite snapshot stores force a single instance | `.github/workflows/deploy-gcp.yml`, `curriculum/store.py`, `operations/store.py`, `storage/snapshot_sync.py` | NFR-4 (R-A1) |
| Rate limiter is in memory | `api/rate_limit.py` (`RateLimiter`) | NFR-2 (R-A3) |
| 0 class 1-5 questions; 0 Hindi questions served | `academicos-data/syllabus/questions.json`, `corpus/bank_merge.py` | QB-1, QB-12 (R-C1, R-C2) |
| 718 model-written questions served without review | `corpus/bank_merge.py`, records with source `ai_generated` / `textbook_grounded` | QB-5 (R-C3) |
| Homework suggestion for English and Social Science 6-9 finds no questions: the slug now decides (#141, #142), but the plan's chapter ids for these books (seeded from the current books, #136) are not in the catalog, which lists syllabus ids (0 Social Science matches, 3 of 18-19 English, measured 13 Oct) | `operations/homework_routes.py`, `assessment/pillar_routes.py` (`catalog_chapters`) | TA-4 (R-B7) |
| The main paper builder sends no difficulty tier | `frontend/lib/data/datasources/api/paper_builder_api.dart` | EX-3 (R-C4) |
| Term report counts today's unmarked lessons as behind | `operations/term_report.py` | ADM-2, ADM-3 (R-D2) |
| A school that set up classes 6-9 before #136 sees old and new chapters side by side after a re-seed (nothing is deleted, by design) | `curriculum/seed_cbse10.py` | SCH-4; needs an owner decision on a clean-up tool |
| Rooms are empty for ordinary classes when no rooms are allocated | `curriculum/timetable_solver.py` | TA-1, SA-1 |
| About 2% of Exemplar answer keys misaligned (D37); CBE stacked fractions refused instead of recovered | `corpus/` importers | QB-7, QB-10 |
| Social Science 7 has 202 book sections for about 130 periods left in a mid-year start; the plan says so, but the principal has no tool to choose what to drop | `curriculum/scheduling.py` | SCH-4 |

Closed since 7 October: a parent's calendar. A parent reads a child's calendar through
`GET /children/{student_id}/calendar`, which admits only that child's linked guardians
(`tests/test_my_calendar_load.py::test_a_parent_sees_their_childs_calendar_and_no_one_elses`). The 403 seen
on 4 October was a parent calling `/my-calendar`, which is for the caller's own events.

---

## 10. Access checklist

| Access | Status | Who |
|---|---|---|
| GitHub `varshinicb1/AcademicOS`, write | Invitation sent 6 October; accept it from your GitHub account | Owner (done) |
| Google Cloud project `vidyuthlabs`: Cloud Run admin, Cloud Build editor, Artifact Registry writer, Cloud SQL admin (Phase 2), Secret Manager accessor, Storage admin, Monitoring editor, Firebase Hosting admin | To be granted on day 1 | Owner |
| Google Play Console: internal testing for two apps | Phase 3 | Owner creates the apps; you get release manager |
| Firebase project (FCM) | Phase 3 | Owner |
| Cloudflare (Workers `qbank`, `question-gen`) | Only if R-C1 needs model generation | Owner |
| NCERT textbook files and chapter transcriptions | Phase 4, by secure transfer | Owner |
| Test accounts on live (principal, teacher, student, parent of a test school) | Phase 3 and 5, for device and email checks | Owner registers them; credentials are never shared in writing in the repository |

Secrets are read through IAM in Secret Manager. Nobody sends a secret value in chat or email.

---

## 11. Working together

- **Daily:** one short written update at the end of your day: done, next, blocked. Include links to PRs.
- **PRs:** small and frequent, at least one a day once past Phase 1. A PR that runs over 600 changed lines (generated files excepted) should be split unless it is R-A1's migration.
- **Review:** the owner reviews within one working day. Address comments in new commits, not force-pushes, so the review history stays readable.
- **Questions:** ask early. A question asked on day 2 is cheap; a wrong assumption found on day 15 is not.
- **Decisions:** anything that changes a requirement, the data model, the UI language or the brand is the owner's decision. Write the options and your recommendation in the PR or the daily update.

---

## 12. Acceptance of the engagement

The engagement is complete when:

1. every phase deliverable in section 8 is merged, deployed by CI and verified;
2. both suites pass on the final `master`;
3. the re-audit (R-E1) is committed;
4. the runbooks and the handback note (R-E2, R-E3) are committed;
5. the final demo has been given.

Work that is merged but not verified on the running system is not complete.
