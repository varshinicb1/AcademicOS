# AcademicOS

**AcademicOS runs the academic side of a CBSE school, grades 1-10.** It sets examination papers from a
board-grade question bank with a marking scheme for every question. It builds the school's calendar and
timetable, and keeps them working through leave, substitutions and holidays. It sends teachers and students
their day, their homework and their progress, on their phones.

> **New here? Read [`HANDOVER.md`](HANDOVER.md) first**, then
> [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md) (what to build),
> [`docs/agent-workflow.md`](docs/agent-workflow.md) (how work is done) and
> [`CONTRIBUTING.md`](CONTRIBUTING.md) (how a change reaches `master`: always a pull request).

- **Live:** [vidyuthlabs.web.app](https://vidyuthlabs.web.app) (the web console) and a FastAPI backend on
  Google Cloud Run.
- **Requirements:** v3, adopted 2026-09-27 ([`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md)).
- **Status (2026-09-28):**
  - The web console for classes 6-10 is live as `e50d250`: milestone M0 (`09649eb`) plus PRs #1-#3. M0's re-audit measured
    **60.5 / 100** on the v2 scorecard ([`docs/audits/2026-09-28-09649eb.md`](docs/audits/2026-09-28-09649eb.md)).
    M0's work gained 2.71, and the calendar lost 3.13 to a timetable stored per subject name rather than per
    class (D115), which M1 fixes.
  - The v3 teacher and student apps, the scheduling engine (timetable, leave, substitution, compensation),
    homework and notifications are **not built yet**. M1 (the school data model) is next:
    [`docs/plans/m1-school-data-model.md`](docs/plans/m1-school-data-model.md).
  - The gap analysis and roadmap are in [`HANDOVER.md`](HANDOVER.md) sections 6-7.

---

## Vision

Four products on one backend, for the people who run a school's academic year:

| Product | For | Core jobs |
|---|---|---|
| **Web console** | principal, delegated admins, coordinators, teachers | examination automation (paper builder, answer keys, exam planning); the principal dashboard with full admin: users and roles, calendar, timetable, leave and substitution, question-bank review, reports and alerts |
| **Teacher app** (Android first) | teachers | today's periods and lessons; one-tap "taught"; leave in three taps; substitution duties; homework and class tests from the question bank; class progress; reminders; works offline |
| **Student app** (Android first), with parent mode | students (grades 1-10), parents | today's timetable and changes; assignments with reminders and submission; learning progress per topic; practice; parents see status and notices |
| **Question bank + API** | the products above, partners | grades 1-10 and all main subjects; from CBSE, NCERT and reviewed unofficial sources; every question mapped to chapter/topic/marks with a marking scheme; REST `/v1` and an MCP server |

**What makes it the best in the market:**
- An honest, board-grade question bank: keyed, mapped to the book, gaps reported, provenance on every item.
- Scheduling that survives real school life: leave, substitution and lost-period compensation, handled
  automatically.
- Homework that writes itself from today's lesson.
- A principal who sees where the year is slipping, with the next action attached.
- Apps built for low-end phones, Hindi and English, offline, three taps.

**Not:** an ERP (no fees, admissions or transport), a chatbot, or a seller of student data. No
leaderboards or streak pressure aimed at children. Every number shown is measured or labelled estimated.
The longer research ambition (a knowledge graph of validated learning algorithms, `docs/roadmap.md`, about
35%) is separate from the product.

## Requirements

The full set, with IDs, priorities and acceptance checks, is [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md).
The headlines:

- **Question bank (QB):** grades 1-10; English, Hindi, Maths, EVS/Science, Social Science; every chapter
  covered at every marks value the paper patterns use; a marking scheme with value points for every
  question; any source, with provenance and review; nothing served that cannot be answered as printed.
- **API:** search/get/coverage and **homework generation**; per-partner keys issued from the console; the
  same engine as the paper builder; never student data.
- **Exams (EX):** blueprint papers to the exact marks; sets; real tiers; the CBSE competency share; PDF and
  answer key with the school's branding; review workflow; datesheet and invigilation; marks entry and
  analysis.
- **Admin (ADM, ROLE):** full admin for the principal; delegated admin permission sets for chosen teachers;
  scoped coordinators; bulk import; a dashboard of coverage, exams, time saved, homework, substitutions and
  progress, with alerts.
- **Scheduling (SCH):** academic calendar; a clash-free timetable from a constraint solver; dated lesson
  plans; leave -> substitution -> compensation with a lost-period debt; a named list of edge cases, each
  tested.
- **Teacher app (TA) and student app (SA):** UI/UX first; notifications and reminders; progress
  tracking; offline; Hindi; accessibility; parent mode with DPDP consent.
- **Notifications and integrations (NTF, INT):** push, in-app inbox, email; WhatsApp/SMS; Google
  sign-in/Calendar/Classroom; CSV import; scheduled and event-driven automations.
- **Non-functional (NFR):** DPDP and CERT-In; RBAC on every route; web < 10 s first load on Slow 4G; 99.5%
  availability; WCAG 2.2 AA.

## Where it stands

| Area | State |
|---|---|
| Web console (classes 6-10) | Live. Paper builder, quick and hand-picked papers, sets, PDF paper and key with value points, a chapter picker that reaches every question, the question bank browser, calendar and terms, dated lesson plans with reschedule, book editions, the principal's coverage/pace, bank and per-term time-saved cards. v2 audit of `09649eb`: **60.5 / 100** ([`docs/audits/2026-09-28-09649eb.md`](docs/audits/2026-09-28-09649eb.md)). |
| Question bank | 5,319 served questions, all keyed: NCERT Exemplar 4,191, CBSE sample papers 743, CBSE competency items 366, board papers 19; rebuilt 2026-09-28 without the questions that cannot be answered as printed. Strong for Maths and Science 6-10. **Grades 1-5: none; English, Hindi and Social Science: nearly none.** |
| Question bank API | `/v1` and MCP live, and they file chapters exactly as the paper builder does (D39, fixed in M0). There is still no way to issue an API key on live (D38). |
| Scheduling engine | Calendar, terms, holidays, per-subject weekday slots, lesson plans. **No section x teacher x room timetable, no solver, no leave, substitution or compensation.** |
| Teacher and student apps | A shared Flutter codebase with teacher, student and parent pages and an offline Android build. **No separate apps, no homework model, no push notifications.** |
| Engineering | 3,804 Python and 468 Flutter tests pass on `master` (2026-09-28); 244 routes, each with a role policy; audit log; school scoping; CI deploys the backend and the web on merge (since 2026-09-28; Flutter pinned to 3.44.9). |

## What has to be done

The milestones, their order and the first tasks are in [`HANDOVER.md`](HANDOVER.md) section 7.

1. **M0, stabilise:** done, live since `09649eb` (Task 125, D39, D29, D27, D22/D40, D78/D79, the fidelity rebuild). Re-audited at 60.5.
2. **M1, school data model:** sections, teacher allocations, rooms, bell schedules, delegated admin,
   parents, bulk import.
3. **M2, scheduling engine:** timetable solver, leave -> substitution -> compensation, the edge-case tests.
4. **M3, notifications platform:** push, inbox, preferences, scheduled jobs.
5. **M4, teacher app.**
6. **M5, homework and the student app, with parent mode.**
7. **M6, question bank to grades 1-10:** NCERT textbooks, the language subjects, content fidelity, a
   review queue.
8. **M7, integrations and polish.**

Adopt the v3 scorecard ([`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md) section 12) and take a baseline
audit before M1.

## How the work is done

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`docs/agent-workflow.md`](docs/agent-workflow.md). In short:
- **Pull requests only.** Every change reaches `master` as a PR. The maintainer reviews it, runs the gates
  on the merge result and merges it; nobody pushes to `master`.
- **Tests first.**
- **Gates:** both suites before every merge.
- **Question bank:** one serving gate, and the bank is rebuilt only in pipeline order.
- **New routes:** a row in `route_policy.py` for every new route.
- **Evidence:** every number is quoted with its command, and "done" means verified on the live system.
- **Deploys:** a merge to `master` deploys the backend and the web through CI; the hand runbook is the fallback ([`docs/deploy-by-hand.md`](docs/deploy-by-hand.md)).
- **Machine load:** one heavy job at a time on a laptop.

## Architecture and tech stack

- **Backend:** Python 3.12 and FastAPI (`src/academicos/`).
  - Durable state goes through one factory that prefers **Cloud SQL**, then Supabase, then local SQLite (WAL mode with a busy timeout).
  - Blobs are on GCS.
  - The paper engine, bank merge, tagger and PDF renderer are all in this tree.
- **Frontend:** one Flutter codebase (`frontend/`) with two builds: the web client, and the offline Android app with its own local engine.
- **Data:** `academicos-data/` holds the served question bank, the syllabus and taxonomy trees, and the bank health report.
- **`backend/`** is an experimental rewrite. Do not work there unless asked.

The architecture detail is in [`CLAUDE.md`](CLAUDE.md) and [`AGENTS.md`](AGENTS.md).

---

## Getting started

### Backend

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[api,mobile-scan,dev]"
pip install -e ".[api,mcp]"          # the question-bank MCP server
python -m pip install en_core_web_md@https://github.com/explosion/spacy-models/releases/download/en_core_web_md-3.8.0/en_core_web_md-3.8.0-py3-none-any.whl
python -m academicos.cli serve --host 127.0.0.1 --port 8010
```

The API docs are at `http://127.0.0.1:8010/docs`. The LLM key goes in
`config/secrets.env` (gitignored), never in `config/config.toml`.

### Frontend

```powershell
cd frontend
flutter pub get
flutter run -d chrome --dart-define=ACADEMICOS_API=http://localhost:8010/api/v1
```

### Tests

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
cd frontend; flutter analyze --no-fatal-infos; flutter test --exclude-tags live-backend
```

On the development machine, run the Python suite with `D:/AcademicOS-venv`. Its
PyMuPDF version matches the render fixtures. Don't rebuild
`frontend/build/web` while the suite runs.

---

## Contributing

| Who | Role |
|---|---|
| [@varshinicb1](https://github.com/varshinicb1) | owner and maintainer: reviews and merges pull requests, deploys, runs the audits |
| [@bahumanyarg11](https://github.com/bahumanyarg11) | collaborator: builds on branches and opens pull requests |

People and Claude Code agents work the same way: pick a task, branch from `master`, run both gates, and
open a pull request from the template. The maintainer's Claude reviews it with `/review-pr <n>`
([`.claude/commands/review-pr.md`](.claude/commands/review-pr.md)), runs the gates on the merge result,
and merges it or requests changes. The whole process is in [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## Documentation

**Start here**
- [HANDOVER.md](HANDOVER.md): what exists, access, set-up, the gap analysis against v3, the roadmap, the traps.
- [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md): the v3 product requirements (grades 1-10, web console, teacher app, student app, API), with IDs and priorities, and the proposed v3 scorecard.
- [docs/agent-workflow.md](docs/agent-workflow.md): how work is done here: gates, the bank pipeline, releasing, evidence, and the rules learned the hard way.
- [CONTRIBUTING.md](CONTRIBUTING.md): the pull-request process for people and agents: claim, branch, gates, the PR template, review and merge.
- [docs/plans/](docs/plans/): plans for the next work (M1, the school data model) and past work (Task 125).
- [docs/integration-candidates.md](docs/integration-candidates.md): third-party APIs reviewed for v3 (sign-in and OTP, holidays, calendar sync, government data, push/SMS/WhatsApp), with liveness checked.

**Measuring the product**
- [docs/product-scorecard.md](docs/product-scorecard.md): the v2 instrument and its audit log. The write-ups are in [docs/audits/](docs/audits/).
- [docs/PRD.md](docs/PRD.md): the original product definition. Its scope decisions are superseded by docs/REQUIREMENTS.md; its non-goals and hard constraints still bind.

**Operating the release**
- [docs/deploy-by-hand.md](docs/deploy-by-hand.md): the deploy recipe and live checks, with the deploy history.
- [docs/gcp-deployment.md](docs/gcp-deployment.md) and [docs/gcp-bootstrap.md](docs/gcp-bootstrap.md): the GCP release, and the one-time owner runbook.
- [docs/deployment.md](docs/deployment.md): the older Render release.
- [docs/compliance.md](docs/compliance.md): DPDP Act 2023 and CERT-In, and the "before you ship" boxes.

**The question bank**
- [docs/bank-health.md](docs/bank-health.md): per class, subject, chapter and topic, including what the merge refused and why.
- [docs/question-bank-api.md](docs/question-bank-api.md): the bank as an API product, with the licensing gate first.
- [docs/ncert-corpus.md](docs/ncert-corpus.md): the source corpus.

**Design and research**
- [docs/design-system.md](docs/design-system.md): white-first, emoji-free, token-driven (`design/tokens.json`).
- [docs/notifications.md](docs/notifications.md): the notification policy: only about the recipient's next action.
- [docs/research/](docs/research/): UI/UX principles, the interface specification, production AI principles, and case studies of about 50 competing platforms.

**Reference**
- [docs/PRODUCTS_AND_RELEASES.md](docs/PRODUCTS_AND_RELEASES.md): a dated record of the older product/release split. Where it disagrees, HANDOVER.md and REQUIREMENTS.md win.
- [docs/REQUIREMENTS_BY_LAYER.md](docs/REQUIREMENTS_BY_LAYER.md): older requirements split by backend and frontend.
- [docs/api.md](docs/api.md) and [docs/api-reference.md](docs/api-reference.md): the developer guide and endpoint inventory.
- [docs/roadmap.md](docs/roadmap.md): the five-phase research vision.
- [docs/ACADEMIC_DATA_MODEL.md](docs/ACADEMIC_DATA_MODEL.md): the curriculum data model.
- [docs/TRANSCRIPT_REQUIREMENTS_MATRIX.md](docs/TRANSCRIPT_REQUIREMENTS_MATRIX.md): requirements traced to the client transcript. It is a dated record, so read its header first.
- [docs/history/](docs/history/): superseded handovers.
- [AGENTS.md](AGENTS.md) and [CLAUDE.md](CLAUDE.md): architecture, invariants and commands.
