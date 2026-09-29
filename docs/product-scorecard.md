# Product scorecard — the sellable product

> **v3 scope adopted 2026-09-27.** This file is the **v2** instrument (web-first, classes 6-10). The
> last v2 audit measured 61.0 (`docs/audits/2026-09-27-8db6636.md`). The three-app product under
> [`docs/REQUIREMENTS.md`](REQUIREMENTS.md) is measured by the **v3 scorecard**, adopted 2026-09-30:
> [`docs/product-scorecard-v3.md`](product-scorecard-v3.md), with its own audit log. v3 scores are not comparable with
> the v2 numbers below; the last v2 audit is 60.5 at `09649eb` (2026-09-28).


**Adopted 2026-09-21.** The product owner set the target: **90% of the sellable
product.** This file defines how that is measured. It was written and committed
*before* the first audit ran, so the instrument cannot be tuned to the result.

## Why a second number

`docs/roadmap.md` measures the 5-phase research vision (~32-37% on 2026-09-11).
By its own rule it does not count product work — its 2026-09-13 and 2026-09-14
entries say real, verified product features "don't move any phase's
percentage." It also cannot reach 90% from code: Phase 4's "evaluated" bar and
Phase 5's "running on real learners" need real students and a pilot.

So the product is scored here, separately, against `docs/PRD.md` §0 (decisions
of 2026-09-18), §5A (the question bank's rules), §6 (first sellable version),
§8 (what done and working mean) and §10 (hard constraints). **Both numbers are
reported, side by side. Neither replaces the other.** Swapping one for the
other to show a bigger figure would be relabelling, not progress.

## The rubric

Every item is scored on the same five-point scale. The scale is the PRD's own
evidence standard (§8.2): *"'Verified' means called with real data through the
actual running backend/app and the output was inspected — not 'the code looks
right.'"*

| Score | Meaning |
|---|---|
| **0** | Missing, or not started |
| **0.25** | Partial, or present but known-broken on its main path |
| **0.5** | Code exists and its tests pass; never exercised end to end with real data |
| **0.75** | Verified end to end with real data on at least one surface it ships on; only minor known defects |
| **1.0** | Verified on every surface it ships on; no known defect |

An area's score is the mean of its items. The product score is the
weight-weighted sum of the area scores. **When evidence is weak, score down.**

## Areas, weights and items

**Changed 2026-09-22 (v2, web-first).** The user decided the first sellable
product is the **web app** (the Flutter web build on GCP, vidyuthlabs.web.app);
the offline Android app is not in the first release. Area 1 took the phone
area's weight (10 → 20) and gained items 1.6-1.7; area 2 became *Web app
delivery* (20 → 10). The v1 phone items are kept at the end of area 2 for the
day the phone app returns. Every audit in the log below from 2026-09-22 on is
scored with these weights, so the totals are comparable with each other and
not with a v1 number.

| # | Area | Weight | Grounded in |
|---|---|---|---|
| 1 | Paper generation — web | 20 | §0 decision 3 |
| 2 | Web app delivery | 10 | §0 decision 3 (web-first, 2026-09-22) |
| 3 | Question bank coverage and quality | 20 | §0 decisions 4-5; §5A rules Q1-Q4 |
| 4 | Academic calendar automation | 15 | §0 decisions 1-2; §4 jobs 1-2; §12.7-8 |
| 5 | Principal dashboard | 10 | §12.6; §4 job 3 |
| 6 | Time-saved measurement | 5 | §0 decision 11; critical path item 2 |
| 7 | Question bank as an API product | 5 | §0 decision 7; §5A rule Q5 |
| 8 | Release readiness and hard constraints | 15 | §8.1; §10 |
| | **Total** | **100** | |

## Classes in scope

The first sellable release covers **classes 6-10**. The user decided this on
2026-09-23 ("skip 11 and 12 for now"), with the numbers in front of them:
correctness-first serves a board question only where its answer key was
verified, which left class 11 with no questions at all and class 12 unable to
build a Mathematics or Science paper. Classes 6-10 are carried by the NCERT
Exemplar import instead.

So items 1.5 and 3.1 are scored over 6-10. Two rules keep that honest:

- **Report, never hide.** An audit still states what 11 and 12 hold, as an
  out-of-scope line. A class dropped from the score is not a class dropped from
  the truth.
- **Never offer what we cannot serve.** The product must not present a class it
  cannot build a paper for -- the web builder offered 6-12 until 2026-09-23, so
  a teacher chose a class, a subject and a template and only then met "Unable to
  find sufficient questions". Offering 11 and 12 again is part of bringing them
  back into scope, not a separate nicety.

When 11 and 12 return, restore the 6-12 wording here and in the two items.

### 1. Paper generation — web (20)
1.1 Blueprint → selection → sectioned paper, quick and custom paths
1.2 PDF paper renders correctly: no crash, MCQ options shown, no dropped symbols, correct class in the header
1.3 PDF answer key carries the official scheme (share of rows that are "pending teacher entry")
1.4 Parallel sets, tiers, CBQ ≥ 50%
1.5 The requested class gets that class's questions, for every class **6-10**
    (the release's scope since 2026-09-23; see "Classes in scope" above)
1.6 Custom paper by hand: search the bank → select specific questions → generate a paper from exactly those
1.7 The paper and answer-key PDFs download from the browser and print correctly (A4, page breaks, fonts)

### 2. Web app delivery (10)
2.1 The live web app (vidyuthlabs.web.app) loads, and a new school goes from principal bootstrap → invite a teacher → teacher signs in → first paper, end to end
2.2 Usable in a phone browser: the teacher's main flows (sign in, make a paper, mark a lesson, download the PDF) work at 375 px width
2.3 No silent failures: every failed request on the main flows shows a clear message the user can act on
2.4 Speed: first load to interactive and paper generation, measured on the live URL (report the numbers; 0.75 needs < 10 s to interactive on a throttled 4G profile and < 20 s per paper)

*Not scored while the phone app is out of the release (v1 area 2, "Paper
generation — offline phone"; restore them, and the v1 weights, if it returns):*
the app starts and loads its bundled corpus with one bad row unable to stop it;
Quick Paper serves the requested grade and fills every section; custom paper;
phone PDF paper and key; the offline guarantee; an Android build compiles.

### 3. Question bank coverage and quality (20)
3.1 Classes served *by paper generation*: 6, 7, 8, 9, 10
    (11 and 12 are out of scope; report what they hold, score neither)
3.2 Subjects offered per class, against what CBSE offers at that class
3.3 Q1 — served questions carrying an official answer scheme; blank-scheme count
3.4 Q2 — served questions mapped to a curriculum chapter or topic
3.5 Q3/Q4 — marks range per topic reported including its gaps; coverage reported, never implied
3.6 Content fidelity — questions served that cannot be answered (missing figure, missing passage, missing options, garbled script)

### 4. Academic calendar automation (15)
4.1 Curriculum hierarchy, board to subtopic, set up for a school
4.2 Calendar: working days, holidays including multi-day blocks
4.3 Micro-scheduling: dated lessons from syllabus × timetable
4.4 Teacher daily loop: today's lessons (job 1) and mark complete in one tap with an honest save state (job 2) — scored on the web app
4.5 Reschedule on disruption (PUSH / ADJUST)
4.6 Book selection: one edition per subject per year, chosen by the school (§12.7 — listed Missing in §6)

### 5. Principal dashboard (10) — §12.6's four metrics
5.1 (a) Exam coverage — which classes and subjects have had a paper set this term
5.2 (b) Time saved this term, labelled *estimated*
5.3 (c) Syllabus coverage vs calendar, and where the year has fallen behind (job 3)
5.4 (d) Bank coverage per subject and grade

### 6. Time-saved measurement (5)
6.1 Time to produce each paper is recorded, on every web generation path
6.2 A baseline to compare against (manual time), per term
6.3 Surfaced to the principal

### 7. Question bank as an API product (5)
7.1 HTTP API — search, get, answer key, coverage
7.2 MCP server tools
7.3 Q5 — one corpus: the API, the MCP server and paper generation serve the same bank

### 8. Release readiness and hard constraints (15)
8.1 `pytest tests -q` green
8.2 `flutter analyze` clean and `flutter test` green
8.3 The live Web release is up and healthy
8.4 §10: every query scoped by `school_id`; role gates enforced; audit log immutable
8.5 `docs/compliance.md` "before you ship" boxes, for every shipped feature that touches student data
8.6 Web client ↔ backend contract: the real web screens send what the API accepts (no 422s on main flows); `ACADEMICOS_OFFLINE` never in the web build

## Not scored — gates code cannot close

These decide whether the product *sells*, and no amount of code produces them.
They are listed with every score, so a high number is never read as "ready to
sell" on its own.

- **A reference school** — §0 critical path item 1: *"nothing in the repo substitutes for it."*
- **Counsel's written position on redistributing CBSE content** — §12.11; gates selling the bank as an API.
- **A signed release APK, distributed** — and the `corpus-data` release that phones download republished. (Only when the phone app returns to the release.)
- **A signed data-processing agreement with a school** — `docs/dpa-template.md`.
- **The published price** — §0 decision 9 sets the band, not the number.

## How to re-score

Re-audit rather than trust a number written here; counts in prose rot (§11.5).
For each item: run the real code against real data, record the evidence
(command, output, file:line), and score it on the rubric. Record each audit in
the log below with its date, its scores, and what moved.

## Audit log

Each audit scored the commit `/health` reported live, item by item, with the
evidence in its own write-up: `docs/audits/<date>-<commit>.md`, one per row from
`cb16658` on. The `a153003` write-up was not kept; its scores survive as the
first column of the later tables. Paths in the write-ups that point at a
`scratchpad` are the auditor's working files and were not kept. v2 weights
throughout; the rows from `afadd6c` on also apply the classes 6-10 scope. A new
audit reads the previous write-up first, re-verifies every item rather than
copying its score, and adds its own file and row here.

| Date | Live commit | A1 (20) | A2 (10) | A3 (20) | A4 (15) | A5 (10) | A6 (5) | A7 (5) | A8 (15) | **Total** |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-21 | Render build | — | — | — | — | — | — | — | — | **26.3** provisional re-baseline, not an audit |
| 2026-09-22 | `a153003` (first GCP release) | 5.71 | 3.13 | 5.00 | 6.25 | 2.50 | 1.25 | 1.25 | 8.13 | **33.2** |
| 2026-09-22 | `cb16658` | 10.71 | 4.38 | 7.50 | 9.38 | 5.00 | 2.50 | 3.33 | 9.38 | **52.2** |
| 2026-09-23 | `6544c06` | 12.14 | 5.63 | 10.00 | 9.38 | 5.00 | 2.50 | 3.33 | 8.13 | **56.1** |
| 2026-09-23 | `00912e7` | 12.86 | 5.63 | 10.83 | 9.38 | 5.00 | 2.50 | 3.33 | 9.38 | **58.9** |
| 2026-09-23 | `afadd6c` (classes 6-10) | 14.29 | 6.25 | 12.50 | 9.38 | 5.00 | 2.50 | 3.33 | 10.63 | **63.9** |
| 2026-09-26 | `3197f4e` | 13.57 | 6.25 | 12.50 | 10.63 | 5.00 | 2.08 | 3.75 | 10.00 | **63.8** |
| 2026-09-27 | `8db6636` | 14.29 | 6.25 | 10.00 | 9.38 | 5.00 | 2.50 | 2.92 | 10.63 | **61.0** |
| 2026-09-28 | `caf5e3d` (incremental) | 14.29 | 6.25 | 10.00 | 9.38 | 5.00 | 2.50 | 2.92 | 10.63 | **61.0** |
| 2026-09-28 | `09649eb` (M0) | 14.29 | 6.25 | 10.83 | 6.88 | 5.00 | 3.33 | 3.33 | 10.63 | **60.5** |

What moved, briefly:

- **33.2 → 52.2**: shipping, not new code — real-school identity, authenticated
  PDF downloads, honest paper totals, no silent failures, the guided paper
  builder, and the calendar's Coverage & Pace plus year plan.
- **63.9**: +3.10 of the +5.0 is the scope change (items 1.5 and 3.1 scored over
  6-10), not new work; the rest is `flutter analyze` 61 issues → 7 info-only and
  the swallowed-errors guard going green.
- Areas 4-7 were flat for four audits running at 63.9.
- **63.8** hides two movements. Shipped work added +2.29: book editions (4.6),
  the principal's bank coverage card (5.4), and one serving gate (7.3). The
  full-suite log as evidence added +0.63 (8.1). Three defects that were already
  live at `afadd6c`, and that no earlier audit tested for, took back 3.01:
  - `main.dart.js` and `flutter_bootstrap.js` were served `immutable` for a
    year under names that never change, so a returning browser ran the
    2026-09-22 bundle (8.3);
  - the builder's chapter picker counts one chapter tag and filters on another,
    reaching 1,266 of the 2,297 questions it shows (1.1);
  - the time-saved report read only quick-generate papers, which the web app
    never makes (5.2, 6.1).

  Scored only as deep as the previous audit went, the same range reads 66.8.
- **61.0** (`8db6636`) is the first audit run as a workflow: one auditor per area,
  a skeptic per area that tried to refute every changed score, totals computed by
  the script. Shipped work earned +3.01 (D23, D24, D25 closed: returning browsers
  get new builds, a chosen chapter reaches what the picker counts, time saved
  counts web papers). Counting class 12 on the Question Bank tab against 3.1 took
  -0.83. One regression, D39, took -0.42: the builder files chapters with
  `chapter_filing` while `/v1` and MCP still match raw `chapterIds`. Old defects
  measured for the first time took -4.58. Scored only as deep as the previous
  audit went, this range reads 66.4.
- **61.0** (`caf5e3d`, incremental: every item Task 125 could move re-audited by two
  independent auditors, the rest carried after verifying their code and data unchanged). Task 125's
  gains -- a real competency share (7/10 quick papers and 46/56 builder presets reach 50%), 10
  presets now complete, set B/D keys fixed, 0 contradictions over 303 edits -- crossed no rubric step:
  1.4 stays 0.25 while no tier can print a different paper, and 3.6 stays 0.25 with D31 at 16/20 and
  newly filled Section E slots printing CBE garble (D74).
- **60.5** (`09649eb`, M0; a full re-audit by three independent auditors, `docs/audits/2026-09-28-09649eb.md`).
  M0's work held up and earned +2.71:
  - classes 6-10 only on the web (3.1);
  - per-term exam coverage and baseline on the web (5.1, 6.2);
  - the time-saved card rendered from real payloads (6.3);
  - one corpus on all five surfaces (7.3, D39 closed).

  It cost 3.13 on the calendar:
  - M0's setup seeds classes 6-10 under one year, which put D115 on the default path: the timetable and
    periods per week are stored per subject name, so every class's Science shares one timetable and plans
    inflate 1.8× (4.3, 4.5, 5.3);
  - the teacher's daily loop was scored on the web, as its text says. A school set up on the web cannot
    make a dated plan, so its day is empty (4.3, 4.4).

  3.6 stays 0.25: 12 of 20 papers still print an unanswerable item, all from items no rule catches (D83).
