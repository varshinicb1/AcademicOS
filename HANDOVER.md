# AcademicOS — Handover (2026-09-27)

You are taking over AcademicOS from the original developer and the Claude Code sessions that built it.
Read in this order:

1. **This file**: what exists, access, set-up, where the work stands, what to build next.
2. **[`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md)**: what to build (v3, adopted 2026-09-27: grades 1-10,
   a web console, a teacher app and a student app). It supersedes the older scope in the PRD.
3. **[`docs/agent-workflow.md`](docs/agent-workflow.md)**: how work is done here (gates, the question-bank
   pipeline, releasing, evidence), plus the rules learned the hard way.
4. **[`CONTRIBUTING.md`](CONTRIBUTING.md)**: every change is a pull request into `master`, reviewed and
   merged by the maintainer (since 2026-09-28).
5. [`README.md`](README.md), then `CLAUDE.md` / `AGENTS.md` for architecture.

The previous handover (2026-09-21, answer-key linkage) is kept in `docs/history/`.

---

## 1. What is live

| Piece | Where | State |
|---|---|---|
| Web app (Flutter web) | https://vidyuthlabs.web.app (Firebase Hosting, project `vidyuthlabs`) | live, commit `c46681b` (2026-09-29): student Today and week grid, homework mix, emailed sign-in codes, marking reminders |
| Backend (FastAPI) | Cloud Run `academicos-backend`, `asia-south1`, https://academicos-backend-2eskom55ta-el.a.run.app | live, `/health` reports the commit |
| Database | Cloud SQL Postgres `academicos-pg` (durable tables) + SQLite snapshots | live |
| Blobs | GCS `vidyuthlabs-academicos-media` | live |
| Question-bank API | `/v1/*` on the same backend, API-key gated | live; the principal issues keys from School → API keys (D38 fixed); keys persist in GCS |
| Older Render release | `academicos-backend.onrender.com` | still answers on an old build; not the product; can be retired |

The live product is the **v2 scope**: a web console for classes 6-10 (paper generation, question bank,
calendar/lesson plan, principal dashboard). Under the v2 scorecard it measured **61.0 / 100**
(`docs/audits/2026-09-27-8db6636.md`); an incremental re-audit of the live `caf5e3d` (Task 125) also measured
**61.0** (`docs/audits/2026-09-28-caf5e3d.md`), and the full re-audit of M0 (`09649eb`) measured **60.5**
(`docs/audits/2026-09-28-09649eb.md`: M0's work +2.71; D115, the timetable stored per subject name, -3.13).
Since then the **v3 operations layer** has been built and merged (PRs #11-#30, 2026-09-28/29): sections,
allocations, rooms, bells, a solver-backed timetable, leave/substitution/compensation, teacher attendance,
notifications and scheduled automations, homework (with photos), learning progress and self-practice,
parents, delegated admin, CSV import/export, exam review/datesheet/invigilation/marks, a principal
dashboard and alerts, calendar feeds, the School tab on the web, and teacher/student app builds
(`docs/apps.md`). Backend and web through #38 are live (`c46681b`, 2026-09-29). None of it has been through a scored audit yet, so the score above has not moved. What is
still missing: section 6.

## 2. Access you need (ask the product owner)

- **GitHub** `varshinicb1/AcademicOS` (private): the owner invites collaborators, who get write access
  (@bahumanyarg11 was invited on 2026-09-28). `master` is what is live. Changes reach it only as pull
  requests (`CONTRIBUTING.md`). On a free plan GitHub cannot protect a private repository's branches, so
  that is a rule everyone keeps, not a lock.
- **Google Cloud** project `vidyuthlabs`: Cloud Run admin, Cloud Build editor, Artifact Registry writer,
  Cloud SQL client, Secret Manager accessor, Storage admin, **Firebase Hosting** admin.
- **Secrets** live in Secret Manager only, never in the repo: `principal-bootstrap-key`,
  `postgres-password`, `acos-llm-api-key` (bound as `ACOS_LLM_API_KEY` and `SARVAM_API_KEY`).
- **The first principal account** on live is created by the owner with the bootstrap key; there are no
  credentials in this repo and none should be added.
- **GitHub Actions is blocked since 2026-09-29** by the account's billing (failed payment or spending
  limit): every job is refused before it starts. Until the owner fixes it in GitHub → Billing & plans,
  deploy by hand ([`docs/deploy-by-hand.md`](docs/deploy-by-hand.md)) after both suites pass locally.
  Once fixed, a push to `master` deploys backend and web through `.github/workflows/deploy-gcp.yml` again.

### Owner actions that switch built features on

| Feature | What the owner does |
|---|---|
| CI deploys | Fix GitHub billing (above) |
| Push notifications (phones) | Set `ACOS_FCM_PROJECT` on Cloud Run, give the runtime service account FCM send rights, add the Firebase config files to the Android project |
| Email notifications and the weekly digest by email | Add SMTP secrets (see `assessment/mailer.py`) |
| Sign in with Google (INT-1) | In Google Cloud console, APIs & Services > Credentials: create an OAuth client ID of type *Web application* with authorised JavaScript origin `https://vidyuthlabs.web.app`, then set `ACOS_GOOGLE_CLIENT_ID=<client id>` on Cloud Run (a public value, not a secret). The button appears on the sign-in page once `/api/v1/auth/providers` reports it |
| Scheduled automations on a clock | Create secret `ACOS_CRON_KEY`, bind it to Cloud Run, and a Cloud Scheduler job POSTing `/api/v1/automations/run` with header `X-Cron-Key` every 5-15 minutes (until then they run on ordinary traffic) |
| Teacher and student apps on phones | Gradle flavors with `applicationIdSuffix`, signing keys, store listings (`docs/apps.md`) |
| Grades 1-5 question bank (M6) | Approve downloading the NCERT class 1-5 textbooks (none are in `ncert-dataset/`) |
| SMS and WhatsApp (INT-2) | WhatsApp: a WhatsApp Business account, an approved utility template `academicos_notice` with two body parameters (title, body) in English and Hindi, then `ACOS_WHATSAPP_TOKEN` (secret) and `ACOS_WHATSAPP_PHONE_NUMBER_ID` on Cloud Run. SMS: an MSG91 account with DLT sender and template registration, a flow template using `##title##` and `##body##`, then `ACOS_SMS_AUTHKEY` (secret) and `ACOS_SMS_TEMPLATE_ID`. A DPA with each provider (numbers are personal data). Until then consent is kept and nothing is sent |
| Alerts on new errors (NFR-7) | Cloud Console → Error Reporting: turn on notifications for new error groups. Optionally create secret `ACOS_OPS_KEY` and bind it to Cloud Run to read `GET /api/v1/ops/errors` |
| First principal of a school | Register with the bootstrap key (never in the repo) |

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
  - `pytest tests -q -p no:cacheprovider`: 3,804 pass, 113 skip and 3 xfail on `master` after PRs #1 and #2
    (2026-09-28, in a fresh clone without the gitignored data extras). It takes about 20 minutes.
  - `cd frontend && flutter analyze --no-fatal-infos`: 7 info notes are expected.
  - `flutter test --exclude-tags live-backend -j 1`: 468 pass, in about 3 minutes.
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
| **Question bank QB-1..13** | 5,319 served questions, every one with a marking scheme. Classes 6-10 Maths (265-852 per class) and Science (245-494). Sources: NCERT Exemplar 4,191, CBSE sample papers 743, CBSE competency items 366, board papers 19. The fidelity rebuild (2026-09-28, `corpus/fidelity.py`) repairs what the extraction broke where the repair is certain and refuses the rest. One serving gate; bank health report; chapter/topic tagging for about half of the bank. | **Grades 1-5: nothing.** English, Hindi and Social Science 6-10 are almost empty. No NCERT textbook exercises imported yet. No unofficial or AI-assisted source with a review queue. Difficulty and Bloom level are inferred, not judged (QB-11). Content fidelity: rebuilt 2026-09-28 against every example the audits named (D20, D21, D26, D31, D36, D45, D54, D74, D76, D77); not re-audited yet. Still open: about 2% of Exemplar keys misaligned (D37) and CBE keys that answer another part (Science8SB31c) -- neither has a rule that finds them. The CBE importer itself still doubles stacked fractions; the rebuild refuses those items rather than recovering them. |
| **Question bank API API-1..6** | `/v1` search/get/coverage/facets, an MCP server, API keys (`api_keys.py`). **The principal issues, lists and revokes keys on the live app** (`/api/v1/api-keys`, web: School → API keys), and the key store is snapshotted to GCS so keys survive restarts (D38 fixed, 2026-09-29) | Paging and error contract gaps (D52, D64, D65). No homework-generation endpoint on `/v1` (API-2); homework is set through `/api/v1/homework` instead. |
| **Exam automation EX-1..9** | Guided builder, quick paper, hand-pick, swap/pick/remove, sets, OR choices, PDF paper and key, **the paper as an editable Word file** (`/papers/{id}/export/docx`, the same header, instructions, sections, marks, options and OR choices as the PDF, a traceable-copy id in the footer, audited; EX-5), time saved per paper; the competency share shown before generating (Task 125). **Review workflow** (author → named reviewer/HOD → principal approval → locked; every export and download audited with who, EX-6). **Exam planning**: datesheet with clash checks, invigilation roster by matching (no own subject, no leave, no double booking), publish notifies students and invigilators (EX-7). **Marks entry** per question for a paper sat on paper, with analysis per question, chapter, topic and class and CBSE grade bands; marks feed progress (EX-8) | Real tiers need judged difficulty (QB-11). Science 6/7/8 cannot reach the 50% competency share. CBE garble in new Section E slots (D74). Half-yearly papers fall short of marks (D18). No report cards (EX-8 P2). School name/logo not printed by default (D41). |
| **Admin and dashboard ADM, ROLE** | Roles `principal`, `teacher`, `student`, **`parent`**; invite-only registration; a role policy on every route; audit log; admin console (roster, coverage and pace, reschedule, calendar setup, book editions, insights). **Delegated admin**: the principal grants a teacher any of users, calendar, timetable, leave, exams, qbank_review or reports, optionally scoped to classes/sections/subjects (`require_admin`, M1.4). **Bulk import** from CSV or an Excel workbook (its first sheet; dates typed as dates) with a dry run for sections, teachers, students, parents, allocations and holidays, and export as CSV or Excel in the same columns so an edited export imports back (M1.6, INT-3; `operations/xlsx.py`, no new dependency). **Parents** join through a student-bound invite and see only their linked children (M1.5). **Term report** (`/dashboard/term`, the School tab's Term report): one term, filtered by class, section or subject -- syllabus against plan, exams and papers set, time saved (estimated), homework, cover, the bank's gaps named, progress by chapter level -- as Excel (`xlsx.py`, no new dependency) or PDF, every download audited (ADM-2, ADM-4) | Scope is stored and returned but checked only where a route names a section. The term report names no student or teacher, by design (ADM-5). |
| **Scheduling SCH-1..9** | Sections, teacher allocations, rooms, bell schedules, a section × period × teacher × room timetable with clash checks and an OR-Tools solver (SCH-2/3); lesson plans per section (SCH-4); leave → substitution (proposed and accepted) → compensation with lost-period debt (SCH-5..7); **teacher attendance** that opens same-day cover (SCH-9); escalation of unaccepted cover (NTF-2); **labs, double periods and co-teaching** (an allocation needs a room kind, has double periods and a co-teacher; the solver books labs by clock time and a room's periods out of use stay free; a co-taught period needs cover only when both teachers are away); the **Timetable** page on the School tab (allocations, rooms, bell, generate with a preview, each section's week) | Section split/merge and electives across sections are not modelled. |
| **Teacher app TA-1..9** | The shared Flutter codebase: my schedule, daily planner, papers, question bank, mobile scan, an offline Android build. **Web workspace (School tab)**: my day with check-in and cover duties to accept, homework set from the lesson's chapters and marked per question, paper reviews. **Teacher and student app builds** (`--dart-define=ACADEMICOS_APP=teacher\|student`, docs/apps.md). **Offline (TA-8)**: every School read is kept per user and shown without signal; writes that mean the same later (lesson marked, marks saved, cover answered, homework and practice answers, notifications read) wait on the phone, are sent in order when the connection is back, and a change the school refuses is shown with its reason (`Ops.send`, the banner shows what waits) | No Gradle flavors or signing yet (owner action). Check-in and photo uploads do not queue: a check-in's time is the point, and photos need the connection. |
| **Student app SA-1..8** | **Today** as it runs, and the week as a grid with times (SA-1); **homework** answered in the app, MCQs marked at once, photos of written work, marks and model answers (SA-2); **learning progress** per subject, chapter and topic with what to revise and week by week (SA-3); self-practice (SA-4); exams datesheet and the evening-before reminder; notifications with quiet hours (SA-5). **Parent mode**: each child's week, day, homework, progress, and DPDP consent given or withdrawn by the parent (SA-6). **Profiles on a shared family phone**: every student and parent signed in on the device is one tap apart, each with its own session, offline copy and queued changes; staff accounts are not kept (SA-8). Student app build via `ACADEMICOS_APP=student`. **Young learners (SA-7)**: a class 1-5 student's home is four large pictures with one word each; a parent opens a class 1-5 child's homework and hands it in with them (`/children/{id}/homework/{hid}/submit`, audited as the parent's; from class 6 children hand in their own), with larger text | Grades 1-5 have no questions in the bank yet (M6 needs the NCERT class 1-5 books), and homework is built from bank questions, so until M6 no class 1-5 homework can be set; the young home, timetable, messages and the parent flow work, and are tested with a class 3 section. No read-aloud (TTS, P1). |
| **Notifications NTF, integrations INT** | One notification service: in-app inbox, FCM push, email, quiet hours, **a daily digest option** (one push and one email a day at the person's time; the inbox stays immediate; cover requests are never held; SA-5), English/Hindi templates, delivery tracking and retry (NTF-1). **Scheduled automations**: homework due and overdue, cover escalation, teacher daily digest, principal weekly digest and morning alerts, marking reminders, the evening-before exam reminder for students and invigilators, and the term report on a term's last day (NTF-2), from `POST /api/v1/automations/run` (Cloud Scheduler, `ACOS_CRON_KEY`) or ordinary traffic. Event notifications for leave, cover, timetables, homework, reviews and exams; **a holiday declared moves the lessons still to teach on it to the next teaching days and tells their teachers and students** (`moveLessons`, default on; everyone else hears of a holiday within 14 days) (NTF-3). CSV import/export (INT-3). **Sign in with Google** on the web for existing accounts: the ID token is checked against Google's keys, client id, issuer, expiry and a verified email (`/auth/google`, INT-1) | Push needs `ACOS_FCM_PROJECT` and FCM rights; email needs SMTP secrets; the cron route needs `ACOS_CRON_KEY` and a Cloud Scheduler job; Google sign-in needs `ACOS_GOOGLE_CLIENT_ID` (all owner actions). SMS and WhatsApp are built (`operations/messaging.py`: a person's own number, consent per channel, next-action kinds only) and wait on the owner's provider accounts. Google sign-in on Android not yet. |
| **NFR** | DPDP/CERT-In design in `docs/compliance.md` (5 of 22 ship boxes ticked), audit log, school scoping, security headers, cache-busting, hand-deploy runbook | Web first load 18-21 s on Slow 4G against a 10 s target (bundle breakdown below). Hindi UI missing. Error tracking (NFR-7) groups server and app errors as Cloud Error Reporting events (`api/error_tracking.py`); its alerts are an owner action. |

Web bundle, measured for the speed work: the CanvasKit renderer from Google's CDN is 1.6-2.2 MB brotli,
`main.dart.js` is 1.14 MB, and the four Inter TTFs are about 490 KB. Deferred imports, font subsetting,
and serving the content-hashed entry files as `immutable` (audit D29) are the levers.

## 7. Recommended roadmap

Milestones in dependency order. Each should be sized so one person with Claude Code can land it,
gate it and deploy it.

| # | Milestone | Why first | First tasks |
|---|---|---|---|
| **M0** | Stabilise what is live | Leaves a clean base | **Done, live as `09649eb`, re-audited at 60.5:** Task 125; D39; D29; D27; D22/D40; D78/D79; the content-fidelity rebuild. PRs #1-#3 followed it live as `e50d250`. |
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

Since 2026-09-28 open work is tracked as pull requests: `gh pr list`.

| Branch | State | What to do |
|---|---|---|
| `master` | live + these docs; every change arrives as a PR | branch from here |
| `release/v1` | follows `master` after each merge; the hand-deploy worktree's branch | never commit to it |
| `feat/task-125` | merged as `caf5e3d`, live | history only |
| `feat/term-insights`, `feat/question-bank-merge`, `feat/product-{calendar,exemplar,gcp,paperux,security}` | merged | history only |
| `feat/product-phone` | the offline engine's 8 fixes, merged through PR #1 (`merge/product-phone`) on 2026-09-28 | history only |
| `wip/product-calendar-2026-09-26` | the exporter and manifest fix, merged through PR #2 (`merge/calendar-exporter`); 5 of the 6 strict xfails it waited for now pass | history only; the Mathematics_6 template xfail remains |
| `wip/product-phone-2026-09-26` → `draft/phone-network-guard` | the offline network guard, finished and merged through PR #3 on 2026-09-28: the offline build makes no request until sync is on | history only; the opt-in sync switch (Task 405) is still to build |
| `docs/audit-0927` | merged | history only |

Planned in the last session but **not started** (the audit defect IDs are in `docs/audits/2026-09-27-8db6636.md`):
- **API surfaces:** D52, D64, D65, D10 (labels cleaned, matching fixed), D7, D62, D61, D38. D39 fixed in M0.
- **Dashboard honesty:** D43, D47, D48, D49, D42, D50, D51, D46, D55. D27 (terms on the web) fixed in M0.
- **Content fidelity:** rebuilt in M0 (D31, D26, D36, D20, D45, D21, D54, D74, D76, D77). Open: D37 and misaligned CBE part keys; an importer that recovers stacked fractions instead of refusing them. Floors were lowered to the measured counts under the owner's rule (tests/test_catalog_chapters.py has the per-record diff).
- **Speed:** 2.4 (D29 fixed in M0: the entry files are cached for a year under content-hashed names).

## 9. Things that will bite you

- **The served bank** (`academicos-data/syllabus/questions.json`) is rebuilt only in pipeline order
  (`docs/agent-workflow.md` §5: tag the SOURCE banks, then merge, then enrich). There is one serving gate in
  `corpus/bank_merge.py`, with the extraction repairs and refusals in `corpus/fidelity.py`. Add rules there,
  and measure false positives by reading every refused stem. The relink needs `answer_keys.db` and the
  683 MB parse trees, which live only in the main checkout.
- **Every new route** needs a row in `api/route_policy.py` and an entry in `tests/test_route_inventory.py`
  (307 routes today). If the schema changes, regenerate the OpenAPI contract and TS types.
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
