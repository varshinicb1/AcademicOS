# Product scorecard — the sellable product

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

| # | Area | Weight | Grounded in |
|---|---|---|---|
| 1 | Paper generation — web | 10 | §0 decision 3 |
| 2 | Paper generation — offline phone | 20 | §0 decisions 3, 12 (the primary surface) |
| 3 | Question bank coverage and quality | 20 | §0 decisions 4-5; §5A rules Q1-Q4 |
| 4 | Academic calendar automation | 15 | §0 decisions 1-2; §4 jobs 1-2; §12.7-8 |
| 5 | Principal dashboard | 10 | §12.6; §4 job 3 |
| 6 | Time-saved measurement | 5 | §0 decision 11; critical path item 2 |
| 7 | Question bank as an API product | 5 | §0 decision 7; §5A rule Q5 |
| 8 | Release readiness and hard constraints | 15 | §8.1; §10 |
| | **Total** | **100** | |

### 1. Paper generation — web (10)
1.1 Blueprint → selection → sectioned paper, quick and custom paths
1.2 PDF paper renders correctly: no crash, MCQ options shown, no dropped symbols, correct class in the header
1.3 PDF answer key carries the official scheme (share of rows that are "pending teacher entry")
1.4 Parallel sets, tiers, CBQ ≥ 50%
1.5 The requested class gets that class's questions, for every class 6-12

### 2. Paper generation — offline phone (20)
2.1 The app starts and loads its bundled corpus; one bad row cannot stop it
2.2 Quick Paper: the requested grade only, every section filled, grade printed correctly
2.3 Custom paper: search → select → generate
2.4 Phone PDF paper and answer key: options shown, text renders
2.5 Offline guarantee: never contacts a backend; `ACADEMICOS_OFFLINE` never leaks into the Web build
2.6 An Android build compiles

### 3. Question bank coverage and quality (20)
3.1 Classes served *by paper generation*: 6, 7, 8, 9, 10, 11, 12
3.2 Subjects offered per class, against what CBSE offers at that class
3.3 Q1 — served questions carrying an official answer scheme; blank-scheme count
3.4 Q2 — served questions mapped to a curriculum chapter or topic
3.5 Q3/Q4 — marks range per topic reported including its gaps; coverage reported, never implied
3.6 Content fidelity — questions served that cannot be answered (missing figure, missing passage, missing options, garbled script)

### 4. Academic calendar automation (15)
4.1 Curriculum hierarchy, board to subtopic, set up for a school
4.2 Calendar: working days, holidays including multi-day blocks
4.3 Micro-scheduling: dated lessons from syllabus × timetable
4.4 Teacher daily loop: today's lessons (job 1) and mark complete in one tap with an honest save state (job 2)
4.5 Reschedule on disruption (PUSH / ADJUST)
4.6 Book selection: one edition per subject per year, chosen by the school (§12.7 — listed Missing in §6)

### 5. Principal dashboard (10) — §12.6's four metrics
5.1 (a) Exam coverage — which classes and subjects have had a paper set this term
5.2 (b) Time saved this term, labelled *estimated*
5.3 (c) Syllabus coverage vs calendar, and where the year has fallen behind (job 3)
5.4 (d) Bank coverage per subject and grade

### 6. Time-saved measurement (5)
6.1 Time to produce each paper is recorded
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
8.6 Frontend ↔ backend contract: no drift between the API and the offline local clients

## Not scored — gates code cannot close

These decide whether the product *sells*, and no amount of code produces them.
They are listed with every score, so a high number is never read as "ready to
sell" on its own.

- **A reference school** — §0 critical path item 1: *"nothing in the repo substitutes for it."*
- **Counsel's written position on redistributing CBSE content** — §12.11; gates selling the bank as an API.
- **A signed release APK, distributed** — and the `corpus-data` release that phones download republished.
- **A signed data-processing agreement with a school** — `docs/dpa-template.md`.
- **The published price** — §0 decision 9 sets the band, not the number.

## How to re-score

Re-audit rather than trust a number written here; counts in prose rot (§11.5).
For each item: run the real code against real data, record the evidence
(command, output, file:line), and score it on the rubric. Record each audit in
the log below with its date, its scores, and what moved.

## Audit log

*(First audit pending.)*
