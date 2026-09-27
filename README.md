# AcademicOS

**AcademicOS automates two jobs in a CBSE school: setting examination papers and
running the academic calendar.** A teacher builds a board-style question paper,
with its answer key, from real questions that carry their official marking
schemes. The school's syllabus becomes a dated teaching plan. The principal sees
which classes are behind, what papers have been set, and how much time the
product saved.

- **Live:** [vidyuthlabs.web.app](https://vidyuthlabs.web.app) (web app) and a FastAPI backend on Google Cloud Run.
- **First release:** the web app, **classes 6-10**.
- **Status (2026-09-27):** **63.8 / 100** on the [product scorecard](docs/product-scorecard.md). The target is 80, then 90. [Where it stands](#where-it-stands) and [what has to be done](#what-has-to-be-done) are below.

---

## Vision

### The product being sold now

For a CBSE school, the product removes the two most time-consuming,
least-rewarded parts of the academic year:

1. **Examination automation, the wedge.** A teacher picks a class, subject,
   chapters and a paper template. The product assembles a balanced paper from
   real questions (CBSE, NCERT Exemplar, CBSE competency-based items and sample
   papers) and prints the paper and an answer key with the official value
   points. A paper that took an evening takes minutes.
2. **Academic calendar automation.** The syllabus, holidays and weekly timetable
   become dated lessons. Each teacher sees what to teach today and marks it done
   in one tap. When the year slips, the principal sees where, and can push or
   adjust the plan.

**Who pays:** the school, and the principal signs. The price is flat per school
per year and published: ₹75,000-1,50,000. **Renewal is earned by time saved per
paper**, which the product measures and shows the principal.

**What makes it defensible:** a model can invent a plausible question. It cannot
invent the one CBSE actually asked, or the official value points for it. The
question bank is also a product in its own right, sold as an HTTP API and an MCP
server.

### The longer ambition

[`docs/roadmap.md`](docs/roadmap.md) describes a five-phase research programme:
*"not an AI tutor — a library of validated learning algorithms backed by the
world's best education knowledge graph"*. It covers mastery, forgetting,
misconceptions, and learning paths. It stands at about **35%**, is measured
separately from the product score, and is **not** what is sold today.

### What it is not

These non-goals are binding ([`docs/PRD.md`](docs/PRD.md) §7):

- **Not an ERP.** No fees, attendance or admissions.
- **Not an AI tutor or chatbot.**
- **No gamification**, and **no per-teacher rankings**.
- **Student data is never sold or exposed.** The question-bank API is content only.
- **No unmeasured accuracy claims.** A number the product cannot measure is not shown as if it could.

---

## Requirements

### Decisions in force

The product owner made these decisions. Where an older document disagrees,
this table wins.

| Decision | Since | Replaces |
|---|---|---|
| Scope is examination automation plus academic calendar automation, nothing else | 2026-09-18 (PRD §0.1) | — |
| The product is paper generation: blueprint balancing, real questions with official schemes, PDF paper and answer key | 2026-09-18 (§0.3) | grading, scanning and analytics as the centre |
| **The first release is the web app** (Flutter web on GCP) | 2026-09-22 | §0.12, "primary surface: the offline Android phone" |
| **Classes 6-10** | 2026-09-23 | §0.4, "all grades 6-12" (11 and 12 return when their banks can serve a paper) |
| The question bank is also sold separately as an API | 2026-09-18 (§0.7) | — |
| Flat per-school annual price, ₹75k-1.5L; the principal signs; renewal is time saved per paper | 2026-09-18 (§0.8-0.11) | — |
| Rights: proceed, and revisit if challenged. This is an accepted commercial risk, not a legal position | 2026-09-18 (§0.6) | — |

### What the product must do

These are the scorecard's eight areas, with their weights out of 100
([`docs/product-scorecard.md`](docs/product-scorecard.md) has every item):

| Area | Weight | The requirement, in short |
|---|---|---|
| 1. Paper generation, web | 20 | Blueprint to sectioned paper, by the builder, quick or by hand. The PDF prints correctly. The key carries the official scheme. Parallel sets, tiers, and at least 50% competency-based questions (CBSE's rule). The requested class gets only its own questions. |
| 2. Web app delivery | 10 | A new school goes from principal sign-up to teacher invite to first paper. Usable at 375 px on a phone browser. No silent failures. Fast enough on 4G. |
| 3. Question bank | 20 | Every class 6-10 served, and the subjects CBSE offers. Rules Q1-Q5 below. No question a student cannot answer. |
| 4. Calendar automation | 15 | Board-to-subtopic hierarchy, terms and holidays, dated lessons, the teacher's daily loop, reschedule, and one book edition per subject per year. |
| 5. Principal dashboard | 10 | Exam coverage this term, time saved (labelled *estimated*), syllabus coverage against the calendar, and bank coverage per subject and class. |
| 6. Time-saved measurement | 5 | Generation time recorded on every path, a manual baseline per term, and both shown to the principal. |
| 7. Question bank API | 5 | HTTP API and MCP server, serving the same bank as paper generation. |
| 8. Release readiness | 15 | Both test suites green, the live release healthy, and every query scoped by school with role gates and an immutable audit log. The compliance boxes are ticked. |

### The question bank's rules

The bank is meant to work like an examination board ([PRD §5A](docs/PRD.md)):

| # | Rule |
|---|---|
| Q1 | **No answer key, no question.** A question without a marking scheme is not served. |
| Q2 | Every question is mapped to a curriculum chapter or topic. |
| Q3 | Every topic reports its full marks range, **including the gaps**. |
| Q4 | Coverage is reported, never implied. |
| Q5 | One corpus: the API, the MCP server and paper generation serve the same bank. |

A record that breaks a rule is left out with its reason in
`academicos-data/syllabus/_merge_excluded.json`, and the bank health report
([`docs/bank-health.md`](docs/bank-health.md)) counts it. A difficulty or Bloom
level the source did not print is flagged as inferred and never acted on.

### Hard constraints

These are non-negotiable ([PRD §10](docs/PRD.md)):

- **DPDP Act 2023:** verifiable parental consent for minors, no secondary use, breach notification.
- **CERT-In:** 6-hour breach reporting, 180-day log retention, an immutable audit trail.
- **Every query is scoped by `school_id`**, and every route has an explicit role policy.
- **No student data in the question-bank API, ever.**
- **Evidence-first:** no fact without provenance.
- **`ACADEMICOS_OFFLINE` never reaches the web build.**

---

## Where it stands

Measured 2026-09-26/27. The audit write-ups with full evidence are in [`docs/audits/`](docs/audits/).

### Score by area

Scores are from the last audit, of live commit `3197f4e`.

| Area | Score | Max |
|---|---|---|
| 1. Paper generation, web | 13.57 | 20 |
| 2. Web app delivery | 6.25 | 10 |
| 3. Question bank | 12.50 | 20 |
| 4. Calendar automation | 10.63 | 15 |
| 5. Principal dashboard | 5.00 | 10 |
| 6. Time-saved measurement | 2.08 | 5 |
| 7. Question bank API | 3.75 | 5 |
| 8. Release readiness | 10.00 | 15 |
| **Total** | **63.8** | **100** |

The score history is 33.2 → 52.2 → 56.1 → 58.9 → 63.9 → 63.8. Live now is
`3219702`, which fixes two of that audit's defects: the one-year cache on the app,
and a time-saved count that missed the web app's papers. It has not been audited
yet.

### What is done

**Paper generation**
- Three ways to make a paper:
  - the guided builder (class, subject, chapters, template);
  - a quick paper;
  - a paper from questions picked by hand.
- In the last audit, every class 6-10 built a paper on every path, with 0 wrong-class questions across 692 printed.
- The PDF paper and answer key download and print (A4, correct symbols).
- The answer key prints the source's own value points with their marks. All 4,575 in-scope Maths and Science schemes add up to the question's marks.
- Parallel sets work.

**Question bank**
- 5,429 questions served:
  - NCERT Exemplar: 4,192
  - CBSE sample papers with marking schemes: 783
  - CBSE competency-based items: 435
  - past board papers: 19 (most are withheld because their answer key cannot be verified)
- 4,675 records are refused, each with its reason, and one rule decides what can be served.
- Per class:

  | | 6 | 7 | 8 | 9 | 10 |
  |---|---|---|---|---|---|
  | Mathematics | 555 | 573 | 857 | 289 | 340 |
  | Science | 247 | 335 | 418 | 457 | 504 |

- A chapter view lists every served question. About half are still "not yet matched to a chapter".

**Calendar**
- Board → subtopic hierarchy, terms, holidays including multi-day blocks, and the weekly timetable.
- Dated lessons, the teacher's "today" view with one-tap completion, and reschedule (push or adjust).
- Book editions per subject per year, class setup, and a subtopic picker.

**Principal dashboard**
- Coverage and pace against the calendar.
- A bank coverage card for classes 6-10.
- A time-saved card that states its baseline is declared, not measured.

**Question bank API**
- `/v1` HTTP API with scoped API keys, and an MCP server with 7 tools.
- Both serve the same bank as the paper builder; a test holds them equal on every class 6-10 pair.

**Release and security**
- Deployed on GCP: Cloud Run, Cloud SQL, GCS and Firebase Hosting.
- Invite-only registration and a role policy on every one of 162 routes.
- An immutable audit log and school-scoped queries.
- **3,622 Python tests** and **373 Flutter tests** pass; `flutter analyze` shows 7 info-level notes and no warnings.

### What is built but not in the first release

- **The offline Android app** (branch `feat/product-phone`).
- Answer-sheet scanning and rubric grading.
- Spaced repetition and mastery models.
- The student and parent portals.

They stay in the codebase but are not scored or sold yet.

---

## What has to be done

### To reach 80 (16.2 points)

Points for items 1-4 are the last audit's estimates. For items 5-8, the figure is one
0.25 step on that item: the area's weight, divided by its number of items, times 0.25.
"How" is the approach that fits this codebase's rules.

| # | Work | Points | How |
|---|---|---|---|
| 1 | **Exam coverage and time saved, by class, subject and term** (items 5.1, 5.2, 6.1-6.3) | ~4.2 | Record subject, class and term on every generation path's audit entry. Aggregate per term. Let the principal set the manual baseline per term and show where the number came from. The web card shows the breakdown. |
| 2 | **The chapter picker filters on the tag it counts** (1.1, 3.4) | ~1.5 | Today the picker counts one chapter tag and the paper filters on another, so 1,266 of the 2,297 questions it shows are reachable. Filter on `taxonomyChapterId` as the chapter view does, then tag the unmatched half through the tagger's measured thresholds. `pillar_routes.py` and the chapter floors have an owner: coordinate, don't edit. |
| 3 | **Competency share and tiers** (1.4, Task 125) | ~1.4 | Read the competency signal the sources actually carry: the CBE bank is CBSE's competency-based item bank, and assertion-reason and case-study types count. Report the real share per class. Warn in the builder before a paper that cannot reach 50%. Say plainly when tiers are unavailable. **Never infer a Bloom level from marks or length.** |
| 4 | **Social Science, English and Hindi for classes 6-9** (3.2) | ~1.7 | **Needs source material from the product owner.** Import it through the same builder, tagger and merge gate; nothing bypasses Q1. |
| 5 | Faster first load (2.4) | ~1.25 | The first load is about 16 s on throttled 4G against a 10 s bar. Measure what loads, split or defer the non-sign-in code, and measure again on the live URL. |
| 6 | Garbled CBE maths (3.6) | ~0.8 | Stacked fractions print twice, and 221 of 379 CBE stems carry mark digits in the text. Fix in the importer, hand-check a sample against the PDF, and rebuild the bank in pipeline order. |
| 7 | Class setup for 7-9 (4.1) | ~0.6 | Seeded classes 7-9 have no approved subtopics, so they cannot be scheduled. Decompose from the textbooks, with principal approval. |
| 8 | Compliance boxes (8.5) | ~0.6 | 17 of 22 "before you ship" boxes in `docs/compliance.md` are open. Close each, or flag it to the product owner. |
| 9 | Signed-in evidence | — | Audits so far scored the signed-in flows from code and tests. A test account would let an audit exercise the live app end to end. |

### Needs the product owner

- Source material for Social Science, English and Hindi, classes 6-9.
- A signed-in test account for audits.
- A go-ahead for the pending bank rebuild. It removes three class 12 records, which the paper builder already refuses.

### Not scored, but decides whether it sells

- **A reference school.** Nothing in the repo substitutes for one.
- **Counsel's written position on redistributing CBSE content.** This gates selling the bank as an API.
- **A signed data-processing agreement** ([`docs/dpa-template.md`](docs/dpa-template.md)).
- **The published price** within the decided band.

---

## How the work is done

Several Claude agents work in this repo at once. **Read
[`docs/agent-workflow.md`](docs/agent-workflow.md) before changing anything.** In
short:

- **One worktree per stream**, branched off `release/v1`, and merged back with
  `--no-ff`. Only `release/v1` reaches `master`. Never touch another worktree,
  never `git stash`, and never sweep another session's uncommitted work.
- **Tests first.** Write the failing test, watch it fail, then fix.
- **Gates before every merge:**
  - `pytest tests -q`, run in the project venv;
  - `flutter analyze --no-fatal-infos`;
  - `flutter test --exclude-tags live-backend`.

  A new route needs a row in `api/route_policy.py`. The design system bans emoji and raw colours.
- **The question bank is rebuilt only in pipeline order**, as the docstring of
  `scripts/merge_question_banks.py` lists it. There is one gate for what can be
  served. Tell the bank owner before any rebuild.
- **Evidence, not claims.** Every number quotes the command that produced it.
  "Done" means verified on the live system, not "the code looks right".
- **Release:**
  1. Push `release/v1` to `master`; CI deploys.
  2. Until 2026-10-01 GitHub Actions has no minutes, so deploy by hand with [`docs/deploy-by-hand.md`](docs/deploy-by-hand.md) and run all of its live checks.
  3. Then re-audit the live commit, and record it in the scorecard and `docs/audits/`.
- **Commits** say what is now true, and why: `fix(area): …`, then a body with before-and-after measurements.

---

## Products and releases

| Deliverable | What it is | Status |
|---|---|---|
| **AcademicOS Web** | Flutter web client | **Live, first release:** [vidyuthlabs.web.app](https://vidyuthlabs.web.app) |
| **Backend, GCP release** | Cloud Run + Cloud SQL + GCS, Firebase Hosting for the web app | **Live since 2026-09-22.** Hand-deployed while Actions minutes are exhausted |
| **AcademicOS Mobile** | Offline Android app (`ACADEMICOS_OFFLINE=true`), on-device engine and bundled bank | Built; **not in the first release** |
| **Backend, Render release** | Render + Supabase | The older release. It still answers `/health`, on an old build (commit "unknown"), and is not the product |

[`docs/PRODUCTS_AND_RELEASES.md`](docs/PRODUCTS_AND_RELEASES.md) has the full
picture. It predates the GCP go-live, so where it calls GCP "not yet
provisioned", read "live".

---

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

## Documentation

**Start here**
- [docs/PRD.md](docs/PRD.md): what the product is for, who uses it, what is in and out of scope, and the decisions taken. The decisions table above records where two of them have since changed.
- [docs/agent-workflow.md](docs/agent-workflow.md): how work is done here. Worktrees, ownership, the rules that protect other sessions' work, gates, the bank pipeline, and releasing.
- [docs/product-scorecard.md](docs/product-scorecard.md): how the product is measured, and the audit log. The write-ups are in [docs/audits/](docs/audits/).

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
- [docs/research/](docs/research/): UI/UX principles, the interface specification, production AI principles, and case studies of about 50 competing platforms.

**Reference**
- [docs/PRODUCTS_AND_RELEASES.md](docs/PRODUCTS_AND_RELEASES.md): which product or release a document means. It predates the GCP go-live.
- [docs/REQUIREMENTS_BY_LAYER.md](docs/REQUIREMENTS_BY_LAYER.md): requirements split by backend and frontend.
- [docs/api.md](docs/api.md) and [docs/api-reference.md](docs/api-reference.md): the developer guide and endpoint inventory.
- [docs/roadmap.md](docs/roadmap.md): the five-phase research vision.
- [docs/ACADEMIC_DATA_MODEL.md](docs/ACADEMIC_DATA_MODEL.md): the curriculum data model.
- [docs/TRANSCRIPT_REQUIREMENTS_MATRIX.md](docs/TRANSCRIPT_REQUIREMENTS_MATRIX.md): requirements traced to the client transcript. It is a dated record, so read its header first.
- [AGENTS.md](AGENTS.md) and [CLAUDE.md](CLAUDE.md): architecture, invariants and commands.
