# PRD — AcademicOS

**Status:** draft v1, written 2026-09-17. This is the first product requirements
document for this repository; it did not previously exist.
**Author:** written autonomously by an agent, from the sources cited inline.

## How to read this document

Every claim below is one of three things, and they are marked:

| Marker | Meaning |
|---|---|
| *(cited)* | Stated somewhere in the repo. `file:line` follows. Verify it. |
| **PROPOSED** | My recommendation. Not established anywhere. Argue with it. |
| **OPEN** | A decision that cannot be made without the product owner. No default given. |

The honest summary: **the engineering intent is documented in depth and the
product intent mostly is not.** Six of the ten PRD categories are well covered
(problem, jobs, differentiation, scope, non-goals, constraints). Four are absent
— buyer, pricing, market size, and product-level success — and in those places
this document proposes rather than reports, so that there is something concrete
to accept or reject instead of a blank.

---

## 1. What this product is

> "AcademicOS is an evidence-grounded academic intelligence and school operating
> platform built on the official CBSE/NCERT corpus (textbooks, previous year
> question papers, marking schemes, curricula, circulars, and bye-laws). It
> bridges authoritative curriculum structures with day-to-day school operations:
> from scheduling and lesson planning to blueprint-based exam generation, mobile
> answer-sheet scanning, rubric grading, and personalized mastery tracking."
> — `README.md:3-5`

Shorter, and the version I would put on a website:

**AcademicOS runs the academic year of a CBSE school.** It takes the official
syllabus, works out what should be taught on which day, tells each teacher what
they are teaching today, records whether it happened, and shows the principal
where the year has fallen behind — in time to fix it.

The declared north star, which is a different and larger ambition:

> "**North star:** not an AI tutor — a library of validated learning algorithms
> backed by the world's best education knowledge graph. Most edtech products are
> collections of features; we build an architecture that evolves for years."
> — `docs/roadmap.md:3-5`

**OPEN — these two statements are not the same product.** The first is a school
operations tool with a defensible wedge and a reachable first customer. The
second is a multi-year research programme that would need funding before
revenue. Both are legitimate. Deciding which one this year is for determines
almost everything downstream, and the repo currently pursues both.

---

## 2. The problem

Stated in the user's terms, from the adoption research:

> A four-case study of secondary maths teachers found three time-related
> obstacles — lesson preparation, content-heavy syllabuses, assessment demands —
> that caused participants to abandon technology entirely. Teachers revert to
> "chalk and talk" because **"the 'chalk and talk' method is the quickest
> strategy to prepare lessons"** — `docs/research/ui-ux-principles.md:182-186`

Two consequences that shape design more than any feature list:

1. **Preparation time is the barrier, not capability.** A product that saves a
   principal time but costs a teacher time will not be used. Every teacher-facing
   surface is judged on whether it beats pen and paper *that morning*.
2. **A black box loses the teacher.** An intelligent tutoring system was
   abandoned because teachers could not predict what it would show students —
   *"I have no idea what kind of tasks they get. I experience a lack of control.
   I prefer control."* — `docs/research/ui-ux-principles.md:193-198`

The second is why review-and-approve is a hard requirement, not a feature.

---

## 3. Users

### 3.1 End users — three roles, plus one piggyback

| Role | Where | What they need | Source |
|---|---|---|---|
| **Principal / admin** | Web | Roster, coverage and pace, reschedule, approvals, consent, audit | `README.md:22-24`, `AGENTS.md` §5 |
| **Teacher** | Mobile | Today's lessons, mark complete, generate a paper, mark scripts | `docs/TRANSCRIPT_REQUIREMENTS_MATRIX.md:324-338` |
| **Student** | Mobile | What am I learning, what's done, what's next. Read-only | `README.md:32` |
| **Parent** | Mobile | Is my child on track. Piggybacks on the student view | `README.md:33`, matrix row: *"can initially piggyback on student"* |

The parent view is deliberately not a separate product yet. The research adds a
constraint: parents **do not share our vocabulary**, so that surface must be
scenario-driven rather than a filtered copy of the student screen
(`docs/research/interface-specification.md` §3.1).

### 3.2 The buyer — **OPEN**, and the biggest gap in the repo

**No document in this repository names who pays.** Not in `README.md`, not in
`AGENTS.md`, not in `docs/roadmap.md`, not in `PRODUCTS_AND_RELEASES.md`. A
targeted search for buyer, payer, pricing, revenue, subscription, and contract
across ten product-level documents returned nothing. The closest references are
a pilot site (Deccan Springs Global School, `docs/status-2026-08-06.md:9`) and
"partner schools under agreement" (`docs/question-bank-api.md:56-57`), neither
of which states payment.

**PROPOSED — the buyer is the school, not the parent, and not the district.**

Reasoning from what *is* documented:

- The Indian market research shows schools are where the money already moves:
  incumbents charge ₹20,000–50,000/yr for schools under 500, ~₹35,000+/yr for
  large CBSE schools, or ₹100–500 per student per year
  (`docs/research/case-studies.md:77-86`).
- The competitive analysis explicitly names the trap: *"the ERP layer is where
  schools actually spend — so the product has to be credible on fees and
  attendance even though that is not where the value is"*
  (`docs/research/case-studies.md:113-114`).
- District and government appear in the repo only as nodes in a future
  knowledge graph, never as customers (`docs/roadmap.md:164`).

**OPEN — three sub-questions I will not decide:** who signs (principal, trustee,
or management trust); whether a school can buy without an ERP package; and
whether there is a second buyer for the question bank as a licensed asset.

### 3.3 Who this is explicitly *not* for

- **Coaching centres.** The corpus is CBSE/NCERT school curriculum. The research
  notes coaching is a different, larger market (`docs/research/case-studies.md:85`), and the
  product is not built for it.
- **Low-literacy users.** The HCI4D scaffolding principles apply; the
  picture-based interfaces for non-literate users do not. *"Teachers and
  principals are graduates. Do not design for illiteracy."*
  (`docs/research/ui-ux-principles.md:233`)
- **Multi-campus districts, for now.** Gradelink competes on the opposite:
  simplicity for small schools (`docs/research/case-studies.md:26`).

---

## 4. Jobs to be done

Three loops decide whether this product lives. Everything else is secondary.

| # | Job | Who | Frequency | Why it decides the outcome |
|---|---|---|---|---|
| **1** | *"What am I teaching today?"* | Teacher | Daily | It is already a daily ritual. Fogg's anchor: attach to the morning register, don't manufacture a new urge (`docs/research/ui-ux-principles.md:163-167`) |
| **2** | *"Did I mark that lesson?"* | Teacher | Daily | The highest-frequency write in the product. Must be one tap, and honest about save state |
| **3** | *"Where has the year fallen behind, and what do I do about it?"* | Principal | Weekly | The only job that a principal cannot do on paper without hours of work |

The declared ambition extends far beyond these — mastery scoring, forgetting
prediction, motivation prediction, career discovery, parent AI, teacher AI
(`docs/roadmap.md:178-191`, `docs/plan.md:92-106`). Those are Phase 4–5 and are
**not** part of the product sold today.

**PROPOSED — one more job belongs in the top three:** *"Is this paper the paper I
would have set?"* Paper generation is the most-built feature in the repo and the
one the competitive research identifies as the strongest asset
(`docs/research/case-studies.md:224`). If a principal cannot answer that question in the
review screen, the asset is wasted.

---

## 5. What is different — and the honest caveat

Four claims, in order of how defensible they are:

1. **Authentic questions carrying official marking schemes, bound to a canonical
   curriculum node.** *"A model can invent a plausible question; it cannot invent
   the one CBSE actually asked, or the official value points for it."* and
   *"anyone can scrape questions; almost nobody has the official value points
   mapped to each question"* — `docs/question-bank-api.md:19-23`
2. **Coverage and pace tied to a real dated schedule.** *"Atlas does curriculum
   mapping; Planbook does plans; not the operational 'planned vs actually taught,
   this week, this class'"* — `docs/research/case-studies.md:225`
3. **Fully offline Android.** Most Indian vendors are cloud-only.
   *"a genuine, hard-to-copy advantage"* — `docs/research/case-studies.md:226`
4. **Provenance as a trust signal.** *"'here is the page in the 2023 paper this
   came from' is a trust signal no competitor can fake"* —
   `docs/question-bank-api.md:72`

**The caveat, quoted so it cannot be quietly dropped later:**

> "Our differentiation is **not** the ERP. It is the curriculum and assessment
> engine… But we must be honest that the ERP layer is where schools actually
> spend — so the product has to be credible on fees and attendance even though
> that is not where the value is." — `docs/research/case-studies.md:109-114`

That is a real risk: fees and attendance are named as table stakes
(`docs/research/case-studies.md:36-37`) and are **not** built. See §11.

---

## 5A. The question bank as a board-grade asset

**Added 2026-09-17 on the requirement that the bank should "work just like an
examination board": complete curriculum coverage, every question mapped to a
topic, an answer key for every question, a full range of marks per topic, and an
MCP server so agents and the backend both work from it.**

This is not a nice-to-have. §5 names the bank as the strongest asset the product
has, and §12 question 11 names its licensing as the one thing gating revenue.

### The rules

| # | Rule | Why |
|---|---|---|
| **Q1** | **Without an answer key, no question.** A question with no marking scheme is excluded from the served bank. | An examination board does not issue a question it cannot mark. A bank mixing answerable and unanswerable items degrades every paper built from it, and one teacher discovers this holding a printed paper. |
| **Q2** | Every question is mapped to a curriculum topic. | "Tagged to Board → Grade → Subject → Chapter → Subtopic, so a consumer can ask for 5-mark case-based questions on Chemical Reactions and get a real answer." Tagging is what makes it a database rather than a pile of PDFs. |
| **Q3** | Every topic reports its full marks range, **including the gaps**. | A distribution listing only what exists hides that a topic has no 5-mark question, and a paper is discovered short at assembly time. |
| **Q4** | Coverage is reported, never implied. | The corpus is genuinely incomplete. Saying so is the difference between a bank and a claim. |
| **Q5** | One corpus, two surfaces. | The HTTP API and the MCP server query the same engine, so an agent and the backend cannot disagree about what the bank contains. |

### What exists today, measured

| | |
|---|---|
| Questions served | **4,000** (722 CBSE CBE items + 3,278 board-paper questions) |
| Answer-key coverage | CBE import: **45.9%** of parsed candidates, but **722 of the ~893 items the documents state** — see below. Board-paper corpus: **40.1%** |
| Topic mapping | CBE import: **312 distinct learning-ladder codes**, 87% of served items mapped |
| Grades covered | **6–10** (CBE, three subjects) + 10 and 12 (board papers, 22 subjects) |
| MCP tools | 7 — search, get, answer key, topics, marks distribution, coverage, build paper |
| Marks range | 1–17, with **1–10 fully populated** |

**On the 45.9% figure.** It is the percentage of parsed *candidates* that carry a
scheme, and it understates the coverage because the parser deliberately
over-produces: anchoring on either a content code or the `Item identity` header
finds every real item and also fragments (a sub-question id inside a long item,
an id inside a mark scheme). Fragments have no scheme, so they inflate the
denominator. Measured against what the documents say they contain, the
answer-bearing parse is close to complete:

| | stated items | served, with answers |
|---|---|---|
| Maths 6 | 58 | **58** |
| Science 6 | 42 | **41** |
| Science 8 | 36 | **36** |
| Science 9 | 59 | **58** |
| Science 7 | 47 | **46** |
| Maths 9 | 112 | **106** |

The fragments are harmless: the Q1 gate removes them, and they are written to
`_unanswerable.json` so a future parser iteration has them.

### The source that made this possible

CBSE publishes item banks at `cbseacademic.nic.in/cbe/assessment.html` —
15 documents, Classes 6–10 × Mathematics/Science/English. Each item carries a
learning-ladder content reference (`6A1a`, `9.1.13`), AO mark split, calculator
rule, marks, the question, **and the published mark scheme**.

That is the requirement in one file format, from the authority. Nothing
third-party came close: two of the datasets surveyed carry no licence at all, and
one "4.9M question-answer" dataset is model-generated rather than authentic.
Provenance beats volume for a board-grade asset.

### What is deliberately not claimed

- **Not all subjects, not all grades.** The CBE banks are three subjects. Social
  Science, Hindi and the Class 11–12 elective set are covered only by the
  board-paper corpus, which is where answer-key coverage drops to 40%.
- **English is the weak subject.** Class 7 (44 of 49) and Class 10 (18 of 31)
  are reasonable; **Class 6 yields 4 of 46 and Class 9 yields 20 of 103.** Those
  two documents are linked-passage items where the mark scheme sits far from the
  question, and the current anchors do not span that distance.
  `tests/test_cbse_cbe_parser.py::test_english_is_parsed_but_is_the_weak_subject`
  pins this so it cannot regress silently.
- **Rights are `unknown`.** These are CBSE documents with no written
  redistribution position. The bank is usable inside a school; it is not
  distributable as an API until counsel says otherwise.

### Open questions this raises

12. **Does the bank get extended to all subjects and grades from CBSE's own
    sources, or from elsewhere?** The CBE programme covers three subjects; the
    rest would need board papers with schemes, which is the 40% path.
13. **Is the question bank sold separately from the school product?** §9 assumes
    one product; `question-bank-api.md` proposes the bank as a standalone asset
    gated on the rights position.

---

## 6. Scope

### In scope for the first sellable version

| Area | State | Source |
|---|---|---|
| Curriculum hierarchy, Board → Subtopic | Built, 46 chapters / 138 topics / 404 subtopics approved | `docs/TRANSCRIPT_REQUIREMENTS_MATRIX.md:86-92` |
| Academic calendar, working days, holidays | Built | matrix, *Academic calendar* section |
| Micro-scheduling, dated lessons | Built | matrix, *Micro scheduling* section |
| Teacher daily loop, mark complete | Built | matrix, *Teacher execution* |
| Coverage and pace reporting | Built | matrix:349 |
| Assessment designer, blueprint papers, PDF export | Built | matrix:369-372 |
| PARAKH/CBSE: tiers, parallel sets, CBQ ≥ 50%, marking schemes | Built | matrix:372 |
| Question bank, 4,143 questions from real board papers | Built | `docs/status-2026-08-06.md:16-19` |
| Student portal | Built | matrix:355 |
| Parent portal | Piggybacks on student | matrix:356 |
| **Book selection (school picks its edition)** | **Missing** | matrix:147 |
| **Fees and attendance** | **Not built** | implied by `docs/research/case-studies.md:36-37, 113` |

### Explicitly deferred

- Phase 3, the Indian Education Graph — *"This phase has not been started"*
  (`docs/roadmap.md:170`)
- The Phase 5 classroom pilot — *"documentation-only. No code ships with this
  protocol"* (`docs/pilot-protocol.md:10`)
- GCS blob storage — until wired, *"the GCP release cannot drop its Supabase
  credentials"* (`docs/PRODUCTS_AND_RELEASES.md:76-82`)
- Hindi Class X — no official CBSE syllabus JSON in the corpus yet
- Full CBSE corpus — *"P1.13 … licensing/disk"* (`docs/plan.md:70`)

---

## 7. Non-goals

These are stated in the repo and are binding:

1. **Not an AI tutor. Not a chatbot.** *"Instead of a chatbot: algorithms."*
   (`docs/roadmap.md:174`)
2. **Output is not PDFs.** *"Output is a knowledge graph where every concept
   knows: prerequisites, difficulty, estimated learning time, common
   misconceptions…"* (`docs/roadmap.md:67-69`)
3. **Never sell or expose student data.** *"**Student-linked reads** … **Never**
   part of this API. The question bank is content; student data is DPDP-regulated
   and stays behind the existing authenticated app."* (`docs/question-bank-api.md:119`)
4. **No accuracy claims that are not measured.** *"nothing in this session
   supports a '100% accuracy' claim for handwriting OCR + AI grading, and none
   should be made to the school."* (`docs/status-2026-08-06.md:110-118`)
5. **No gamification.** No streaks, badges, points, or leaderboards — ruled out
   with reasoning in `docs/design-system.md` §12 and
   `docs/research/interface-specification.md` §8.1, specifically so it is not
   re-proposed.
6. **Do not market per-teacher rankings.** *"Any per-teacher ranking. It corrupts
   the data and the staffroom."* (`docs/research/ui-ux-principles.md:279`)

Five things the market says **not to copy**, from `docs/research/case-studies.md:233-253`:
per-student pricing, quote-only pricing, per-module gating, product pivots that
remove features, and administrator-only sales.

---

## 8. Success

### 8.1 What "done" means for a release

The repo's existing engineering gates, which are good and should stay:

- `pytest tests -q` green after every change (`docs/plan.md:145-148`)
- The 12-corpus prereq eval AUC unchanged for graph changes
- Every algorithm change bumps `version` and cites evidence
- Typecheck and lint clean

### 8.2 What "working" means — the evidence standard

This is stated and worth elevating, because it is unusually rigorous:

> "'Verified' means: called with real data through the actual running
> backend/app and the output was inspected — not 'the code looks right.'"
> — `docs/status-2026-08-06.md:9-11`

**The honest current position against that standard:** of the whole product, only
the teacher schedule views have ever been exercised interactively against a live
backend (`docs/TRANSCRIPT_REQUIREMENTS_MATRIX.md:22-24`). "Complete" elsewhere means
"the code exists and its tests pass."

### 8.3 Product metrics — **PROPOSED**

No product-level success metric exists in the repo. The pilot has endpoints
(`docs/pilot-protocol.md:20-22`) and the eval sets have targets
(`docs/evaluation-plan.md:6`), but nothing defines success for the *shipped product*.

Proposed, drawing on `docs/research/ui-ux-principles.md:261-279`:

| Metric | Why |
|---|---|
| **Time to first value** — login to today's lesson visible | The single most predictive adoption number. Target: under 3 seconds |
| **Completion rate of the three core loops** (§4) | These *are* the product |
| **Weekly active teachers as a share of the school roster** | Not a raw count. 20 active in a 15-teacher school is meaningless |
| **Coverage-report views per principal per month** | Evidence the reporting drives decisions rather than being admired |
| **Empty/error state hit rate** | A high rate is an onboarding failure, not a data problem |

Anti-metrics, named so they cannot be used to look good: raw daily active users,
notifications sent or opened, assessments generated with no evidence they were
taught, and time in app — *"A longer session is usually a worse product"*
(`docs/research/ui-ux-principles.md:271-279`).

**OPEN — the number that matters most is not set.** What retention, or what
learning gain, would make a school renew? The pilot is designed to answer a
learning question at ±0.30 SD (`docs/pilot-protocol.md:20-22`); nothing addresses
whether a school pays again.

---

## 9. Business model — **OPEN**, with a proposal

**No pricing, revenue, or monetisation statement exists for the core product.**
The only commercial content in the repo concerns licensing the question bank as
a separate API, and its gate is legal:

> "**This is a legal question, not an engineering one, and it gates the whole
> proposal.** … get a written position from counsel on (a) redistribution of CBSE
> papers and marking schemes, (b) attribution requirements, and (c) whether the
> answer is 'public subset only'." — `docs/question-bank-api.md:31-53`

If that position is unfavourable, the documented fallback is *"a private question
bank API for partner schools under agreement, which is most of the commercial
value at none of the legal exposure"* (`docs/question-bank-api.md:55-57`).

**PROPOSED — flat, published, per-school, annual pricing.**

The market evidence is unambiguous that this is the wedge:

- Per-student pricing *"punishes a school that succeeds"* and the flat-rate
  challengers are winning explicitly on it (`docs/research/case-studies.md:90-92, 235`)
- EduGradUP charges a flat ₹9,000–23,000/yr by size band with no per-student
  metering; Schoolites flat ₹10/student/month; both are positioned as the
  alternative to opaque enterprise pricing (`docs/research/case-studies.md:81-83`)
- Every global SIS uses "contact us", which *"makes comparison impossible"*
  (`docs/research/case-studies.md:32-35`)

**OPEN — four things only you can set:** the actual number; whether a free tier
exists; whether the question bank is licensed separately; and whether offline
Mobile is priced the same as cloud Web.

---

## 10. Hard constraints

Non-negotiable, and all cited:

| Constraint | Source |
|---|---|
| **DPDP Act 2023** — verifiable parental consent for minors, no secondary use, breach notification | `CLAUDE.md:51-52` |
| **CERT-In** — 6-hour breach reporting, 6-month log retention, immutable audit trail | `README.md:38`, `CLAUDE.md:51-52` |
| **Every query scoped by `school_id`**; role gates enforced | `CLAUDE.md:49-50` |
| **No student data in the question-bank API, ever** | `docs/question-bank-api.md:119` |
| **Offline must never leak into the Web build** — `ACADEMICOS_OFFLINE` | `CLAUDE.md:44` |
| **Evidence-first** — no fact without provenance | `CLAUDE.md:207` |
| **Cognitive-science parameters must cite evidence before they ship** | `docs/plan.md:7-8` |
| **Pilot data**: learning events only, no name/phone/face/location/photo/audio; append-only; retained ≤ 24 months | `docs/pilot-protocol.md:51-57` |

---

## 11. Known contradictions in the current documentation

An agent reading this repo today will hit five conflicts. Naming them is part of
the PRD's job, because they cause real errors.

1. **The product has two names.** `AcademicOS` in `README.md` and `CLAUDE.md`;
   `AssessmentOS` in `docs/status-2026-08-06.md:1`.
2. **The only requirements doc tells you not to trust it.**
   `docs/TRANSCRIPT_REQUIREMENTS_MATRIX.md:5`: *"a dated audit record, not a live
   status board"* and *"the summary at the bottom is wrong."*
3. **Two backend trees, and only one is real.** `src/academicos/` is active;
   `backend/` is a scaffold, and `docs/architecture.md` (966 lines) documents
   that scaffold, **not** what runs. `CLAUDE.md:24-25` says so, but an agent
   following the architecture doc will be misled.
4. **Two clients, and which is the real product is undecided.** The research
   leans Mobile (*"Mobile is the strategically important sub-product"*,
   `docs/frontend-platform-decision.md:206-207`); the migration plan is porting Web to
   React. Both are being worked on.
5. **Stale test counts** appear in several docs (959, 982, 1004, 1113, 1184).
   The current figure is 1,416 passed, 15 skipped, 1 xfailed as of 2026-09-17.

---

## 12. Open questions

The decisions this document cannot make. Grouped by who can.

**Product owner — required before the next build phase:**

1. **Which product is this year's product** — the school operations tool, or the
   algorithms research programme? (§1)
2. **Who is the buyer, and what do they sign?** (§3.2)
3. **What is the price, and is it published?** (§9)
4. **What retention or learning number makes a school renew?** (§8.3)
5. **Does a school buy this without an ERP?** If not, fees and attendance are on
   the critical path and are not built. (§5, §6)

**Answerable from the school, and currently guessed at — these already block six
screens in `design/screens.html`:**

6. Which four metrics belong on the principal's dashboard?
7. Does a school choose one book edition per subject per year, or does each
   teacher choose their own?
8. Is the weekly timetable fixed, or does it vary week to week?
9. How do parents actually give consent — signed paper, SMS, link, in person?
10. Is the principal's console or the teacher's phone screen the primary surface?

**Legal, and blocking revenue:**

11. The question-bank rights position from counsel (`docs/question-bank-api.md:31-53`).

---

## 13. Where each detail lives

This index exists so that the PRD does not become a second, drifting copy of
everything. The PRD owns *intent*; these own their domains.

| Question | Document |
|---|---|
| Which product/release am I looking at? | `docs/PRODUCTS_AND_RELEASES.md` |
| What are the requirements, traced to the client? | `docs/TRANSCRIPT_REQUIREMENTS_MATRIX.md` (dated audit — read its header) |
| Backend vs frontend obligations, with verification depth | `docs/REQUIREMENTS_BY_LAYER.md` |
| What should each screen look like? | `docs/research/interface-specification.md` + `design/screens.html` |
| Colours, type, spacing, component states | `docs/design-system.md` + `design/tokens.json` |
| Why users do or do not adopt it | `docs/research/ui-ux-principles.md` |
| What competitors do and where they are weak | `docs/research/case-studies.md` |
| Where an LLM belongs, and where it is a liability | `docs/research/llm-layer.md` |
| Production AI risk and this codebase's conformance | `docs/research/production-ai-principles.md` |
| What may be pushed to a teacher | `docs/notifications.md` |
| Compliance obligations | `docs/compliance.md` |
| The frozen API contract | `contract/openapi.json` + `contract/api-types.ts` |
| What is next | `docs/roadmap.md`, `docs/plan.md` |

---

## 14. The one-paragraph version

AcademicOS runs a CBSE school's academic year: it turns the official syllabus
into a dated schedule, tells each teacher what they are teaching today, records
whether it happened, and shows the principal where the year is behind. Its
defensible asset is a question bank of real board questions carrying their
official marking schemes, bound to the curriculum. It is sold to schools, works
offline on a teacher's Android phone, and is credible on fees and attendance even
though that is not where its value is. The engineering is roughly 40% of the way
to a sellable product and the product definition was, until this document, not
written down.
