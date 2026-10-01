# Product scorecard v3 — the three-app product

**Adopted 2026-09-30**, by the product owner ("do a fresh audit"; v3 chosen over re-running v2). This
file is committed before the first v3 audit runs, so the instrument cannot be tuned to the result. It
is `docs/REQUIREMENTS.md` §12 made operational. The areas, weights and items are exactly §12's, and
nothing was added or dropped.

v3 scores are **not comparable** with the v2 numbers in `docs/product-scorecard.md`, which measured
the web-first, classes 6-10 product: 61.0, then 60.5 at `09649eb`. That file stays as the record of
v2; its log ends there.

## What is measured

The product in `docs/REQUIREMENTS.md` has:
- **Classes:** grades 1-10;
- **Surfaces:** the web console, a teacher app, a student app with parent mode, and a question bank API;
- **Engine:** the scheduling engine;
- **Services:** notifications and integrations.

Every requirement ID is one item.

## The rubric

This is the same five-point scale as v2, and the PRD's evidence standard (§8.2): "verified" means called
with real data through the actual running backend or app, with the output inspected.

| Score | Meaning |
|---|---|
| **0** | Missing, or not started |
| **0.25** | Partial, or present but known-broken on its main path |
| **0.5** | Code exists and its tests pass; never exercised end to end with real data |
| **0.75** | Verified end to end with real data on at least one surface it ships on; only minor known defects |
| **1.0** | Verified on every surface it ships on; no known defect |

An area's score is the mean of its items; the product score is the weight-weighted sum.

**Rules:**
- **When evidence is weak, score down.**
- **Every item in the requirement counts.** An item scores against everything its requirement asks. A
  P1 item counts as much as a P0 item.
- **Scope in a requirement is scored:** "grades 1-10" means all ten classes.

## Areas, weights and items

| # | Area | Weight | Items (`docs/REQUIREMENTS.md`) |
|---|---|---|---|
| 1 | Question bank: coverage, schemes, quality, provenance | 20 | QB-1..13 (13) |
| 2 | Examination automation (web) | 15 | EX-1..9 (9) |
| 3 | Scheduling engine | 15 | SCH-1..9 (9) |
| 4 | Teacher app | 15 | TA-1..9 (9) |
| 5 | Student app (incl. parent mode) | 10 | SA-1..8 (8) |
| 6 | Principal dashboard and admin | 10 | ADM-1..5, ROLE-1..4 (9) |
| 7 | Question bank API | 5 | API-1..6 (6) |
| 8 | Notifications, automation, integrations | 5 | NTF-1..3, INT-1..5 (8) |
| 9 | Release readiness and compliance | 5 | NFR-1..8 (8) |
| | **Total** | **100** | 79 items |

### Where each surface is verified

- **Web console:** the live release, vidyuthlabs.web.app plus the Cloud Run backend.
  - Live checks are **unauthenticated only** (the owner's rule). Signed-in flows are verified locally, on
    the same commit's code and the served bank, through the real routes and the real web requests.
- **Teacher and student apps:** the one Flutter codebase built with `ACADEMICOS_APP=teacher|student`.
  - While no signed build is distributed (an owner action), 0.75 needs the flow exercised end to end
    against a running backend with real data, on the build's surface: its web build or a device.
  - Widget tests alone are 0.5.
- **API:** `/v1` and the MCP server, against the served bank.

## Not scored — gates code cannot close

These are listed with every score, so a high number is never read as "ready to sell":
- a reference school;
- counsel's written position on redistributing CBSE content;
- a signed data-processing agreement with a school;
- signed and distributed teacher and student app builds;
- the published price.

## How to re-score

Re-audit rather than trust a number written here. For each item:
1. run the real code against real data;
2. record the evidence (command, output, file:line);
3. score it on the rubric;
4. name what holds it below 1.0.

Record each audit under `docs/audits/` and log it below, with its date, commit, scores and what moved.

## Audit log

| Date | Commit | Total | File |
|---|---|---|---|
| 2026-09-30 | `e3a64de` | **40.0** (QB 6.15, EX 7.92, SCH 6.67, TA 5.00, SA 3.13, ADM 4.72, API 2.71, NTF/INT 1.88, NFR 1.88) | [`audits/2026-09-30-e3a64de-v3.md`](audits/2026-09-30-e3a64de-v3.md): the v3 baseline |
| 2026-10-01 | `9f5c41d` | **42.1** (QB 6.15, EX 8.75, SCH 6.67, TA 5.00, SA 3.13, ADM 5.83, API 2.71, NTF/INT 2.03, NFR 1.88) | [`audits/2026-10-01-9f5c41d-v3.md`](audits/2026-10-01-9f5c41d-v3.md): incremental; EX-6, EX-7, ROLE-1, ROLE-3, ADM-5, NTF-3 moved |
