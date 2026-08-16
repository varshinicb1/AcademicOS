# AcademicOS Master Plan

> North star: a library of validated learning algorithms backed by the
> world's best education knowledge graph (see `docs/roadmap.md` for the
> vision). This file is the working plan: task IDs, status, and acceptance
> criteria. Research-first: when a component touches cognitive science, the
> parameters/formulas must cite evidence (Ebbinghaus, ACT-R, FSRS, Bloom,
> ICAP, SDT...) before they ship.

## Status legend
- [ ] backlog · [~] in progress · [x] done · [!] blocked

## Phase 1 — Knowledge Base (base ~70%)
- [x] P1.1 ingest / parse / extract / graph / retrieval / agents (AcademicOS core)
- [x] P1.2 corpus pipeline validated on real CBSE sources (52 registered)
- [x] P1.3 OpenIE entity/triple extraction (Sarvam LLM)
- [x] P1.4 concept spine: Bloom + difficulty + learning hours (rule + llm methods)
- [x] P1.5 prerequisite mining: 5 criteria (TemO/CMH/IOLR/BERTropy/Text), confidence, transitive closure
- [x] P1.6 PREREQUISITE_OF edge materialization (score/confidence/difficulty_jump/spacing) + 12-corpus eval
- [x] P1.7 LO ontology layer (Bloom-template statements, MAPS_TO, inherited prereqs)
- [x] P1.8 learner-aware planning (`prereq_plan` mastery gate)
- [x] P1.9 question → concept mapping (LLM-assisted, verifier-checked) — `algorithms/../qmap.py`, `storage/question_map.py`, CLI `qmap`, 8 tests () — unlocks per-question tracing
- [x] P1.10 misconceptions per concept (research-shaped templates + answer diagnosis) — `algorithms/misconceptions.py`, CLI `misconceptions`, 10 tests
- [ ] P1.11 unlimited-OCR for scanned artifacts [!] disk space
- [ ] P1.12 GCS mirror sync (config exists, needs a scheduled run)
- [ ] P1.13 full CBSE corpus acquisition (800+ QP/MS, model answers) [!] licensing/disk
- [x] P1.14 end-to-end RAG eval harness (`scripts/eval_rag.py`, answer metrics ported from RAG-Enhanced-NCERT-Tutor MIT)

## Phase 2 — Student Brain Graph (base ~25%)
- [x] P2.1 `docs/research/learning-science.md` reading map (research → algorithm table)
- [x] P2.2 learner model schema + event store (event sourcing, replay)
- [x] P2.3 forgetting model v2: FSRS-6 (DSR) port — implemented (`algorithms/fsrs.py`, MIT; `ForgettingParams.model="fsrs"` default, exponential kept)
- [~] P2.4 spaced-repetition simulator + parameter calibration (simulator done: 89% fewer reviews vs naive; per-learner weight fitting pending)
- [x] P2.5 sleep-consolidation component (Walker): overnight stability boost — `ForgettingParams.sleep_boost`, capped, first-night-weighted
- [x] P2.6 retrieval-practice effect (Karpicke & Roediger): testing boost on stability gain — `answer`=retrieval vs `watch`=restudy (`restudy_gain`), scheduler defaults to retrieval mode
- [ ] P2.7 motivation/self-efficacy model (Bandura/SDT) — v1 from affect + outcome signals
- [ ] P2.8 attention/fatigue model (Baker, D'Mello): session-length + affect dynamics
- [ ] P2.9 habit formation (Lally 66-day): streaks, consistency signals
- [ ] P2.10 curiosity engine (Bjork desirable difficulty + novelty): next-concept routing

## Phase 3 — Indian Education Graph (base ~5%)
- [ ] P3.1 data catalog: ASER / UDISE+ / NCERT / CBSE / DIKSHA / PARAKH / NIPUN sources
- [ ] P3.2 system graph schema: Teacher→School→Parents→Village→District→Govt→Child
- [ ] P3.3 EKG-class gold datasets: keep 12-corpus prereq eval as the standing regression gate
- [ ] P3.4 dashboards/eval of learning-outcome attainment vs systemic factors

## Phase 4 — Algorithms Library (base ~15%)
Each module: evidence-grounded params, `version`, metrics entry point.
- [x] A1 knowledge_mastery (weights: accuracy/confidence/retention/application)
- [x] A2 forgetting_prediction → FSRS-6 (P2.3) + revision_scheduler (CLI `revise`)
- [ ] A3 motivation_prediction (P2.7)
- [ ] A4 attention_prediction (P2.8)
- [ ] A5 habit_formation (P2.9)
- [ ] A6 emotional_state
- [ ] A7 curiosity_engine (P2.10)
- [ ] A8 parent_guidance ("say this today" — template + behavior signals)
- [ ] A9 teacher_assistance (class-level priority aggregation)
- [ ] A10 career_discovery (Holland RIASEC mapping from behavior)
- [ ] A11 reward_engine (celebration policy; SDT: autonomy/competence/relatedness)
- [x] A12 study_planner v2 (prereq plan + FSRS spacing + session capacity) — `algorithms/study_planner.py`, CLI `study-plan`
- [x] A13 confidence_model (self-efficacy dynamics per concept) — `algorithms/confidence_model.py`, CLI `confidence`, 6 tests
- [x] A14 lifelong_learner_model (cross-year, cross-subject) — `algorithms/lifelong_model.py`, CLI `lifelong`, 7 tests

## Phase 5 — Human Learning Engine (base ~10%)
- [ ] P5.1 daily loop: know / forgotten / tired / motivated / confident → plan
- [ ] P5.2 API surface: revise, plan, stats, question-solve with evidence
- [ ] P5.3 offline eval: 90-day simulation of the loop on synthetic learners
- [ ] P5.4 (later) classroom pilot protocol

## Immediate execution order (this sprint)
1. P2.3/A2 — FSRS-6 engine + scheduler integration (researched: OSR benchmark, Anki default since 2023; 30–50% fewer reviews than SM-2 at same retention) — done
2. P2.4 — simulator proving the claim on our own data — done
3. CLI `revise`, tests, docs — done
4. P2.5/P2.6 (sleep boost, retrieval-practice gain) as FSRS extensions — done
5. P1.9 (question→concept) done; A12 study_planner v2 done; P1.10 misconceptions done; A13 confidence_model done; A14 lifelong_learner done; next P2.7 / A15

## Standing gates
- `python -m pytest tests -q` green after every change
- 12-corpus prereq eval AUC unchanged for graph changes
- every algorithm change bumps `version`; parameters documented with evidence
