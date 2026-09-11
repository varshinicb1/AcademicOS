# P5.4 — Classroom Pilot Protocol

**Version:** 1.0 · **Status:** draft (P5.3 90-day offline simulation now
complete, 2026-09-11 — `scripts/simulate_daily_loop.py`, `docs/plan.md`;
this protocol has not yet been reconciled against those specific numbers)
**Owner:** AcademicOS research lead
**Reviewers:** algorithm leads, teacher-partner, data-governance officer
**Scope:** field-run plan for piloting the Phase-5 daily loop (P5.1) + calibrated learning algorithms on a real CBSE-aligned Indian classroom.
**Corpus context:** NCERT textbook layer, Classes 6–8 (`docs/ncert-corpus.md`), plus CBSE question papers/marking schemes already registered; question→concept mapping via P1.9.
**Document status:** documentation-only. No code ships with this protocol.

> **Purpose:** convert the algorithm library (FSRS-6 spacing, retrieval practice, confidence, motivation/attention/habit models) into a testable classroom experiment, decide its design, sample size, instrumentation, analysis, and running plan, and pre-commit the interpretation rules before data are collected.

---

## 1. Objective

**Primary question (P0).** Does the daily learning loop (P5.1) — *know / forgotten / tired / motivated / confident → plan* — improve **specific, measurable learning outcomes** versus an equal-time control in a real classroom?

**Primary endpoint (hypothesis H1).** Spaced-replay retention at ~90 days: the treatment arm retains measurably more of the practiced concept set than control:

> H1: `Δ retention 90d = (T − C) ≥ +0.30 SD` (d ≈ 0.30–0.40 expected from theory + simulation).

**Secondary objectives.**
- **TTrans accuracy** during the learning loop (per-concept % correct, first-answer).
- **Fewer right-intervention needs (H2):** the treatment loop keeps retrieval success above target with *fewer* lapse-flagged revisit events than a fixed-interval control (H2: lapse density lower in T).
- **Engagement (H3a):** session completion %, streak consistency, attentive behavior (attention/fatigue model).
- **Self-efficacy & calibration (H3b):** pre/post confidence on A13, calibration gap (efficacy − accuracy) narrows in T (Bandura, 1977/1997; Talsma et al., 2018).
- **Habit formation (H4):** study-day consistency → `habit` phase (forming→consolidating→automated, Lally et al. 2010).
- **Attitudinal (H5):** enjoyment, ownership, "again-tomorrow" share.

### 1.1 Non-goals
- Not a product-competition benchmark; not a study of content/curriculum quality; not a rewards-optimization test; no analysis of any personally-identifying trait.

---

## 2. Ethics & permissions

### 2.1 Minors & consent
- All participants are children (ages ~11–14). Obtain **informed consent from a parent/guardian** (template §8.2) plus **learner assent** in age-appropriate language, and school/headmaster permission.
- Consent explains: purpose; data captured; storage & confidentiality; voluntary participation; right to withdraw a request without penalty; the nature of the control arm (equal time, standard practice).
- **Teacher supervision required.** A classroom teacher is present during every session; the app never overrides teacher/parent guidance; the child can stop anytime.

### 2.2 Tailored-responsibility note (children)
Children in a classroom are **co-participants in guided problem-solving**, not passive data sources — learning happens in social participation (Rogoff, 1991). This protocol:
- keeps the teacher the responsible adult in the classroom for pacing and wellbeing;
- treats learner-generated affect/engagement as *conjectural* feedback that helps plan **for** the child (promoting agency), never as a label.
- no adaptive content that hides, tricks, or difficulties beyond stated practice.

### 2.3 Data minimalization
- Capture **only learning events**: `(learner_id, ts, kind, concept_id, outcome, affect, duration, bloom, difficulty)` and derived per-concept stats. No PII beyond grade/ID: **no name, phone, face, location, photo, audio** (by default).
- IDs are **classroom-local** (e.g., `c7-0421`), assigned by the school; no school cleartable links adversary to identity in the analysis server.
- Weekly exports are **aggregate/statistical**; no raw apprentice rows leave the school without the data-governance officer signing.
- Storage: local-first (student device + school local server); cloud only as anonymized, encrypted aggregate snapshots.

### 2.4 Data storage review & retention
- Event store is append-only SQLite (WAL), school-owned; retained max 24 months; then anonymized (ids salted & re-assigned) or deleted per agreement.
- A data-governance officer reviews the captured dictionary (§3.6) + weekly snapshot (any of: anomaly log deviates beyond threshold → halt & review).
- Opt-out:* delete all of that learner's raw rows before analysis; continue school/class practice unchanged.

### 2.5 Do no harm
- No punishing mechanics in any arm (the treatment loop is reward-aware but never penalizes a miss; repeated miss = gentle re-introduction).
- Breaks enforced by attention model (attention) — a child reading tired is offered a break, not pushed.
- A real-time escalation button for teacher if a child shows distress; the abort for the week is allowed.

---

## 3. Design

### 3.1 Study family
A **two-arm, parallel, randomized, matched-class pair trial** (treatment vs control), pre-registered (full analysis plan frozen before the press run, including hypotheses, DAG, and decision boundaries).

Within each school (≥1, up to 3), classes are **ranked/paired at block level**:
- **Level 1 block:** school/grade/subject (mixture differences in teacher, syllabus start point, enrollment).
- **Level 2 block:** class pair (two sections of the same grade+subject are matched by the teacher's grading baseline, % pass, and prior term mean). Within each class pair, the **section** is randomized to arm (C vs T) at school level; every learner in that section follows its arm.
- **Feasible level 3:** if a school has only one class available, the *matched pair* is at **student level** (students matched by baseline probe score k̶ → one arm each).

This is a **randomized-block design** with class/section as the unit of elimination; learners nested in sections. It keeps teacher & syllabus constant within the matched pair and preserves classroom ecology (you cannot randomize two versions of practice into the same room without contamination).

**Alternate (fallback) design:** if a single school can only supply *one* section, use **within-class AB/AB crossover** over halves of the term — first half class uses C, later half T (with neutral washout week). Crossover has leakage risk; it is a fallback, not plan A.

### 3.2 Sample size reasoning & power table

Assumptions:
- Primary comparison: T vs C on `Δ retention_90`, continuous outcome, equal variance;
- **Expected effect δ = 0.30–0.40 SD** on the normalized platform scale (from our own 90-day simulated retention delta *and* the meta-analytic retrieval-practice*large effects — Karpicke & Roediger 2008; Rowland 2014; Blackwell, 2014 mind, the literature says ~0.30–0.50 for spaced/retrieval of young learners on longer intervals);
- α = 0.05 (two-tailed), power (1−β) = 0.80; ICC within school ≈ 0.05–0.15; design effect F = 1 + (m−1)·ICC with class m ≈ 30.

Effective sample per arm needed (independent two-group):

```
n_arm = 2 · (z_α/2 + z_β)² / δ²          z_α/2 = 1.96, z_β = 0.842 → 2.802² = 7.85
   δ=0.20 → n_arm ≈ 393 (not feasible)
   δ=0.30 → n_arm ≈ 175
   δ=0.35 → n_arm ≈ 129
   δ=0.40 → n_arm ≈ 98
```

Inflated for clustering (ICC ≈ 0.10, m = 30): `n_eff = 1 + (30−1)·0.10 = 3.9`.

Applied → **required effective per arm ≈ 129–175**; with DE 3.9 divided → ~34–45 classrooms-wide; inflate for 10% attrition → **target ≈ 45–50 learners per arm per school** across 2 matched sections (≈ 2×25).

**Power table (design-approach set of deployed learners):**

| Design | At δ=0.30 | At δ=0.40 | Verdict |
|---|---|---|---|
| Independent t, n=175/arm | 0.80 | 0.99 | core model |
| Blocked class-pair, n=45/arm/school | 0.62 | 0.87 | minimum school |
| 2 schools × (2 matched sections) → n≈90/arm total | 0.82 | 0.96 | **chosen** |
| 1 school, 2 sections (n≈45/arm) | 0.62 | 0.87 | accept w/ caveat |

**Final target N ≈ 180 learners total (90 per arm) across 2–4 schools, 4–8 sections.** If a single school with two sections is all that is found, the pilot still runs (secondary statistics become descriptive).

### 3.3 Primary & secondary endpoints (pre-registered)

| Endpoint | Operation | Primary/Secondary |
|---|---|---|
| 90-day delayed ret-test score (concept-level 0–1) | probe at end washout; scored to marking-scheme | **Primary** |
| 7-day & 30-day intermediate retention | probes at +7/+30 per concept set | Secondary |
| accuracy on first attempt (% correct) | from log `outcome` | Secondary |
| distinct-concept coverage (count distinct) | log unique concept_id | Secondary |
| lapse/revisit rate (H2) | # of scheduled revisits when retention < target | Secondary |
| engagement adherence (sessions on-time), active minutes | log | Secondary |
| affect changes / curiosity index | affect tags | Secondary |
| self-efficacy (A13 at post vs pre) | confidence CLI + survey | Secondary |
| habit phase transition | `habit` model | Secondary |
| attrition balance | completion/se.pm | Secondary (fairness) |

### 3.4 Contrast / shunt
- Arm C = same syllabus/questions (same item bank), same total time, **paper-self-practice** (standard sheet / revision notes), reviewed weekly by teacher — no spacing algorithm.
- Arm T = the AcademicOS daily loop: `study-plan`, FSRS-space, `revise`, `confidence` feedback, affect logging.
- Both arms get the same *test* set at the same times (pre, +7, +30, +90).

### 3.5 Confounding & constraints
- **Order effects / familiarity:** both arms get equal exposures; the bank is the same but order differs (T: adaptive; C: fixed).
- **Teacher bias**: the teacher is not told the hypothesis arm-of-day; clear — both arms are "power practice".
- **Timing**: same daypart when possible.
- **Hacking/spacing leak**: the learner model (even in C) doesn't leak scheduling probability; C gets no algorithm signal (see § precedent).

---

## 4. Instrumentation & deployment

### 4.1 Available CLI & data path
Captures via `src/academicos/cli.py` (`learn`, `study-plan`, `revise`, `plan`, `confidence`, `stats`, `day-loop`-equivalent not yet default — the loop is assembled from `study-plan` + `revise` today):

| Capture | Command | Fields captured (`Interaction.style) |
|---|---|---|
| Study plan | `python -m academicos.cli study-plan "<LO>" --learner <id>` | plan session; concept set |
| Answer/interaction | `learn record --kind answer → outcome` | `ts, kind, concept_id, outcome, affect, duration_sec, bloom, difficulty` |
| Revision due | `revise --learner <id>` | predicted retention → due-today list |
| Confidence | `confidence --learner <id>` | efficacy, accuracy, affect, calibration |
| Habits | `habit --learner <id>` (future CLI; model exists) | consistency, phase, streak |
| Replay stats | `learn stats --learner <id>` | totals per concept, mastery, vs. |
| Q→concept map | `qmap` (per question) | adds concept mapping (P1.9) |

Interaction default (from learner model):
```
Interaction(concept_id, kind, outcome, bloom, difficulty, affect, duration_sec, ts)
   kind ∈ {answer, attempt, watch, session_end, affect}
   outcome ∈ [0,1]; affect ∈ valence set
   ts = UTC ISO
```

### 4.2 Offline-first
- Everything runs **offline** on school tablets/phones. The loop + scheduler + confidence run locally (SQLite event store).
- Sync (when internet is available) pulls corpus updates and pushes anonymized aggregate; the loop never *requires* connection.
- **Offline guarantee check** (deploy day): kill network → the app still serves a 15-min session & log in the event store.

### 4.3 Weekly extract & snapshot
- Every Friday: `learn stats --learner *` for all → weekly `snapshot_YYYYMMDD.json`.
- Keep two back-up copies (school server + lead off-line drive). Weekly snapshot includes per-learner events, derived state, and a QA (row counts vs. device totals).
- Anomaly during a session (invalid outcome, duplicate `seq`): the record is **left in place** (append-only invariant — never delete/modify an event); on read, the validator skips/marks it and reports in the QA column. **No crash** ourselves ⇒ no mutation (DML) of the store.

### 4.4 Anomaly rules
- If a device reports a crash/desync: move its rows to a `paused` flag, re-pair, and keep learner-in-analysis (ITT).
- If a learner consistently fails the day: action-interview teacher; but data keeps counting (ITT).
- If a learner drops out: **ITT** – full set retained/withdraw is their data unless child opts out (§2.4).

---

## 5. Timeline (16 weeks)

13 working school weeks + 90s hidden review:

| Window | Days | Focus |
|---|---|---|
| T0 (days 1–5) | onboarding | consent, IDs, baseline test, install app, pilots | hand-back |
| T1–T2 (days 6–15) | run-in | calibration, supervisor sign-off, QA |
| T3–T11 (days 16–50) | **intervention** | loop in place (T), equal-time practice (C) |
| T11+5 / T11+30 | hidden reviews | +7 / +30 recall probes |
| +60 | +90 probe | (intervention ended) final recall |
| +14 more | post-study | self-efficacy post, attitudes, parent/teacher debrief, data analysis |

Milestones:
- **M0 (day 0):** randomization seed frozen; consent docs stored; device QA.
- **M1 (day 5):** baseline done for 100% of known; any failed arm-fp in it: run test/control switch.
- **M2 (day 15):** 1 week of solid logs; any data / novelty design reviewed.
- **M3 (day 50):** end active intervention; freeze logs.
- **M4 (+90):** final probe; unblind results.

---

## 6. Analysis plan

Analy-s-is plan frozen before T0 (pre-registered; versioned). Statistical software = R (lme4) or equivalent; decisions deterministic.

### 6.1 Pre-registered hypotheses (directional)
- **H1 (primary):** mean predic.reten 90-day retention is higher in T. Confirmation if CI of mean difference excludes 0 and effect ≥ 0.30 SD.
- **H2:** lapse/revisit rate (per concept per week) lower in T.
- **H3a:** session adherence (sessions completed/present %) higher in T.
- **H3b:** confidence gain and post calibration better in T.
- **H4:** habit phase grade higher in T by end.
- Analytical checks: H3/H4 described; consensus if p<0.05 & effect reasonable.

### 6.2 Primary model — linear mixed-effects intent-to-treat
```
outcome_90 ~ arm + baseline_grade + school + class + confidentiality
            + (1 | learner)  + (1 | school) ?
```
- ITT: all randomized analysed by randomized arm (even dropout, unless opt-out).
- learner as **random effect** (repeated time per learner, since each seen at +7/+30/+90).
- Include baseline covariate (baseline score) for power.
- Handle school/class blocking in fixed/random part.
- Report **Cohen's d & 95% CI**; both per- nearest vs standard-error.

### 6.3 Missing data (MAR policy)
- Missing at random (device/internet day, absence) → handled by mixed-model REML (usable cases, no drop). Recorded reasons audited.
- If missingness is *informative* (e.g., T learners leaving — outside school move, not arm), report both — per-complete & worst-case (all-missing = pre-intervention score) sensitivity.
- Any deletion requires §2.4.

### 6.4 Effect-size & substantive judgement
- The P3 simulation (90-day, `scripts/simulate_spaced_repetition.py`) + FSRS (89% fewer reviews at equal retention) installed that the **expected effect at H1 is δ=0.30–0.40**; we power to that.
- The **same simulator output** used to build the *predictive prior* for δ (0.35) and a tolerance band. Results are reported against the prior, not scid.

### 6.5 Confidence & calibration measurement
- `confidence --learner` (A13) at week2, 6, 12: efficacy, accuracy, calibration (efficacy − accuracy); pre/post self-efficacy questionnaire (4 items).
- 5 express-probe "how confident do you feel you'll recall this?" vs later actual recall — builds the calibration curve.

### 6.6 SDK / report style
Deliverables:
1. `PILOT_REPORT.md` — design map, ITT table, effect table with d & CI, model propo, DMDA (data-model-data audit).
2. `XLSX/CSV` participant-level (anonymized) + code-file (code to reproduce every table).
3. **Dashboard-style "learning audit"** per class — per-concept retention curves, streak heatmap, calibration.
Everything deterministic; print given seed in regression.

---

## 7. Operations & risks

| Risk | L | I | Mitigation |
|---|---|---|---|
| Device availability/procurement | M | H | school-owned fleet; pre-promise check; paper fallback for 1 wk; sync offline |
| Intermittent internet | M/M | M | offline first (all run closed); week sync queued |
| Novelty effect (early H3 drop later) | H | M | measure engagement at 4 windows; report time-trend not last-only |
| Teacher/class imbalance | M | H | matched class blocks; baseline; analysis with class random effect |
| Contamination (arm cross-talk) | M | H | different sections in different rooms if possible; thread controls routinely; marked |
| Iteration/adaptado loyalty with product | — | — | product feedback log; freeze loop parameters during pilot run |
| Adaptation for larger rollout (r/ no-punish correctness) | M | M | capture "did you follow" + learning; separate *productization* follow-up, not analyzed in P0 |
| Rollback (a systemic bug in T) | M | H | feature flag; daily logs; revert to C-style in emergencies for ≤1 week; report (ITT keeps arm) |
| **Stop criteria** | — | — | (a) any reportable harm/harm suspicion → stop & review; (b) learner consent revoked → drop row(s) per §2; (c) app shows crashing >2 consecutive days for a learner → fix in <24h else move that learner to paper fallback (kept in ITT); (e) serious data leak → halt export, reset, reopen data governance |
| Wastetime / protocol draft avulsion | L | M | pilot leadership weekly; flag early |

---

## 7. Appendix

### 7.1 Data dictionary (as captured)

| Field | Type | Values / example | Source |
|---|---|---|---|
| `learner_id` | str | `C7-02`, `M2-11` | allocation |
| `ts` | ISO-8601 UTC | `2026-09-02T05:14:00Z` | autolog |
| `kind` | str | `answer`, `attempt`, `watch`, `session_end`, `affect` | CLI `learn` |
| `concept_id` | str | graph concept Id (e.g., `fractions:length`) | plan |
| `outcome` | float [0,1] | 1.0 = correct, 0 = wrong, mid = partial | CLI `learn | CLI |
| `bloom` | str | `remember`/`understand`/`apply`/… | graph |
| `difficulty` | float [0,1] | concept difficulty (spine) | graph |
| `affect` | str enum | valence set | CLI or buttons |
| `duration_sec` | float | seconds on item | autolog |
| `payload` | JSON | free extension (e.g., `{"flagged_lapse":true}`) | optional |
| `outcome_class` | derived | correct|wrong|partial/with-withholding | pipeline |
| `calib` | float derived | efficacy − accuracy | A13 |

Affect (valence/arousal cst. table):
- engaged .90, happy .85, curious .80, neutral .60, bored ..45, frustrated .25, tired .30, anxious .20, stressed .20, surprised .40, excited 1.0, confident .95, angry .15 (numeric fixed from `emotion_model.py`).

### 7.2 Consent template (outline)
1. Title & purpose (in child + parent language).
2. What will be captured (grammar: "answers you give and how you feel, no video/no name").
3. What will never be captured (PII).
4. Voluntary + opt-out language; contact of study lead & teacher.
5. Data storage, retention (24 mo), data officer.
6. Signatures: parent/guardian, learner (assent), teacher-in-charge, school stamp.

### 7.3 Assumptions checklist
- [ ] Loop P5.1 implemented (study-plan + revise + confidence wired)
- [ ] P5.3 90-day simulator green (gate)
- [ ] Bank/questions mapped to concept graph (question_map/p1.9)
- [ ] Devices + offline deploy validated for class tour
- [ ] Ethics/consent template staged with school head
- [ ] Analysis frozen & signing (power, priors, hypotheses H1–H4
- [ ] Block randomization (seeded) seal held, seen by 3rd party? Section)
- [ ] Control arm == same bank, same time, no algorithm

### 7.4 Sign-off checklist
- [ ] P/S approvals (school)
- [ ] data-governance assessment
- [ ] Seed lock & block roster
- [ ] baseline set
- [ ] device QA (each device, offline & online)
- [ ] 1-week pilot clearance (M1)
- [ ] end-run snapshot QA
- [ ] pre-analysis freeze version
- [ ] results review (with teacher)

### 7.5 References (books/papers; no URLs)
- Bloom, B. S. (1984). The 2-Sigma Problem: The Search for Methods of School Instruction that Work. *Educational Researcher*, 13(6).
  **(cross-arms: mastery learning ≈ 1σ raised performance, tutor 2σ; effect-size scale anchor for "what is educationally meaningfully large".)**
- Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences*, 2nd ed. L. Erlbaum. (the definitive effect-size convention applied in §§3,6.)
- Rogoff, B. (1993). *Apprenticeship in Thinking* (and notes care of cognitive development in social context) — Oxford University Press. (the child as integral participant, learning in social context — supports the ethical/framework; co-participation framing in §2.2.)
- Karpicke, J. D., & Roediger, H. L. (2009). Retrieval practices produce more learning and better long-term retention than elaborative studying. *Science* 319(5865), 966–968 (and the extended eval studies).
- Rowland, C. A. (2014). The effect of testing versus restudy on retention: A meta-analytic review of the testing effect. *Psychological Bulletin*, 140(6), 1432–1463.
- Lally, P., van Jaarsveld, C., Potts, H., & Wardle, J. (2010). How habits are formed. *European Journal of Social Psychology*, 40(6).
- Bandura, A. (1997.) *Self-Efficacy: The Exercise of Control.* W.H. Freeman.
- Talsma, K., Schüz, B., Schwarzer, R., & Norberg, A. (2018). A meta-analytic cross-lagged model of self-efficacy, achievement. *Learning and Individual Differences* (Talsma et al., 2018).
- Ein: "FSRS (Open Spaced Repetition 2023–2025) — published claims: same retention with fewer reviews than SM-2/SM-2; our port matches (89–92%% fewer reviews in our 365-day sim)". Redis: `docs/research/fsrs.md`.

---

*End P5.4 protocol v1.0. All decisions provisional until the design-freeze/gaited-gate reviews at (M0, M3, analysis); the protocol is a living document that can only change with a review-version bump.*