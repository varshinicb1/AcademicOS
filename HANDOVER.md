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
| Web app (Flutter web) | https://vidyuthlabs.web.app (Firebase Hosting, project `vidyuthlabs`) | live, commit `e0d7d63` (2026-09-28) |
| Backend (FastAPI) | Cloud Run `academicos-backend`, `asia-south1`, https://academicos-backend-2eskom55ta-el.a.run.app | live, `/health` reports the commit |
| Database | Cloud SQL Postgres `academicos-pg` (durable tables) + SQLite snapshots | live |
| Blobs | GCS `vidyuthlabs-academicos-media` | live |
| Question-bank API | `/v1/*` on the same backend, API-key gated | live; no way yet to issue a key on live (audit D38) |
| Older Render release | `academicos-backend.onrender.com` | still answers on an old build; not the product; can be retired |

The live product is the **v2 scope**: a web console for classes 6-10 (paper generation, question bank,
calendar/lesson plan, principal dashboard). Under the v2 scorecard it measured **61.0 / 100**
(`docs/audits/2026-09-27-8db6636.md`); an incremental re-audit of the live `caf5e3d` (Task 125) also measured
**61.0** (`docs/audits/2026-09-28-caf5e3d.md`), and the full re-audit of M0 (`09649eb`) measured **60.5**
(`docs/audits/2026-09-28-09649eb.md`: M0's work +2.71; D115, the timetable stored per subject name, -3.13).
The **v3 requirements** (grades 1-10, teacher and student apps,
leave/substitution, homework, notifications) are mostly **not built yet**; see section 6.

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
- **GitHub Actions** runs again since 2026-09-28: a push to `master` that touches a shipped path deploys
  through `.github/workflows/deploy-gcp.yml` (keyless, Workload Identity Federation): backend and web, with
  Flutter pinned to 3.44.9. The hand runbook ([`docs/deploy-by-hand.md`](docs/deploy-by-hand.md)) is the
  fallback, and its checks follow every deploy.

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
| **Question bank API API-1..6** | `/v1` search/get/coverage/facets, an MCP server, API keys (`api_keys.py`) | No key issuance on live and no durable key store (D38). The chapter filter and MCP topics file chapters as the builder does (D39 fixed, M0). Paging and error contract gaps (D52, D64, D65). **No homework-generation endpoint (API-2).** |
| **Exam automation EX-1..9** | Guided builder, quick paper, hand-pick, swap/pick/remove, sets, OR choices, PDF paper and key, time saved per paper; the competency share against CBSE's 50% and a tiers-unavailable sentence shown before generating (Task 125, live) | Real tiers need judged difficulty (QB-11). The bank's competency share is 4-22% in Maths/Science 6-10, but the builder fills competency sections first: 46 of 56 whole-syllabus presets and 7 of 10 quick papers reach 50%; Science 6/7/8 cannot, and say so. Newly filled Section E slots print CBE garble (audit D74), which makes content fidelity (M6) more urgent. Half-yearly papers fall short of marks (D18). No review/approval workflow, datesheet, invigilation, marks entry or report cards. School name/logo not printed by default (D41). |
| **Admin and dashboard ADM, ROLE** | Roles `principal`, `teacher`, `student`; invite-only registration; a role policy on every route; audit log; admin console with roster, coverage and pace, reschedule, calendar setup, book editions; insights card (per-term exam coverage, time saved) | **No delegated admin or permission sets (ROLE-1).** No parent role. No bulk import. Terms and a new school's classes 6-10 are set up on the web (D27, M0); a dated year plan still needs the API. Sections are rows of their own since M1.1 (every class has at least one; students are enrolled in a section; the principal adds, renames and removes them and names a class teacher on Roster), but nothing is scheduled per section yet (M1.2+). The dashboard lacks substitution, homework and progress data. |
| **Scheduling SCH-1..9** | Academic year, terms, holidays (multi-day), period configuration, **per-subject weekday slots** (`SubjectTimetableSlot`: subject, weekday, period), teacher → book assignments, dated lesson plans with PUSH/ADJUST reschedule and audit | **No real timetable model.** No section × period × teacher × room data, so no clash detection, no teacher timetable and no solver (SCH-2, SCH-3). **No leave, no substitution, no compensation or lost-period debt** (SCH-5..7). The edge cases (SCH-8) are unhandled. |
| **Teacher app TA-1..9** | The shared Flutter codebase has a teacher "my schedule" page, a daily planner, papers and question bank, mobile scan. An **offline Android build** exists. The old phone stream's fixes (PR #1) and its network guard (PR #3: no request until sync is on) were merged on 2026-09-28. | **No separate teacher app.** No leave or substitution UI, no homework creation, no push notifications, no offline sync of timetable and lessons (the offline build runs a local engine instead of syncing). |
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
  (244 routes today). If the schema changes, regenerate the OpenAPI contract and TS types.
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
