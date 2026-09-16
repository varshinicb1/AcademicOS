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
      — `min_confidence` gating implemented 2026-09-11 (found decorative,
      then fixed on request): a parse whose `quality_score` falls below
      `cfg.min_confidence` is registered `status="low_confidence"` instead
      of `"parsed"` — excluded from `cmd_extract`/`cmd_build_graph`'s
      `"parsed"`/`"extracted"` consumption set, output still written to
      disk. `cli parse --force` accepts it anyway. `cli stats` now reports
      a `by_status` breakdown so the low-confidence backlog is visible, not
      silent. 5 new tests (`tests/test_cli_parse_min_confidence.py`), all
      pass.
- [x] P1.2 corpus pipeline validated on real CBSE sources (52 registered)
- [x] P1.3 OpenIE entity/triple extraction (Sarvam LLM)
- [x] P1.4 concept spine: Bloom + difficulty + learning hours (rule + llm
      methods) — audited 2026-09-11: `concept-profile --method rule` was
      silently crashing (missing spaCy model `en_core_web_md`, never
      declared as a setup step anywhere despite being a hard dependency of
      `extract/local_ie.py`); installed it, fixed. Also added
      skip-already-profiled-by-default + `--force` (previous runs
      re-selected the same top-occurrence concepts every time and made no
      forward progress). Real coverage: 1,031/1,153 (89%) of quality-eligible
      concepts (occurrences>=3) now profiled; the remaining 122 are
      structurally out of scope for the rule method — it needs the concept's
      phrase to occur in one of the corpus's 9 actual NCERT textbooks (most
      of the 3,350 registered sources are question papers/marking
      schemes/circulars, not textbooks), and most of the 122 are
      administrative terms (`examination fee`, `amanuensis`) or OCR noise,
      not learnable concepts with a cognitive-difficulty score. `--method
      llm` could reach them but costs real API calls — not run without
      asking first.
- [x] P1.5 prerequisite mining: 5 criteria (TemO/CMH/IOLR/BERTropy/Text), confidence, transitive closure
- [x] P1.6 PREREQUISITE_OF edge materialization (score/confidence/difficulty_jump/spacing)
      — [!] the "+ 12-corpus eval" half is currently **not re-runnable**:
      `scripts/eval_prereqs.py` hardcoded its gold-standard dataset path to
      a different tool's (`opencode`) temp directory, which has since been
      cleaned — the EKG-Dataset (ACE paper MEKG files) is not vendored
      anywhere in this repo or found elsewhere on this machine. Made the
      path configurable (`EVAL_EKG_DATASET` env var, clear error instead of
      a foreign-path traceback) so it's portable once the data exists again,
      but re-acquiring that dataset is external work I did not do
      unprompted. Until then, the Standing Gate below ("12-corpus prereq
      eval AUC unchanged") cannot actually be checked by anyone.
- [x] P1.7 LO ontology layer (Bloom-template statements, MAPS_TO, inherited prereqs)
- [x] P1.8 learner-aware planning (`prereq_plan` mastery gate)
- [x] P1.9 question → concept mapping (LLM-assisted, verifier-checked) — `algorithms/../qmap.py`, `storage/question_map.py`, CLI `qmap`, 8 tests () — unlocks per-question tracing
- [x] P1.10 misconceptions per concept (research-shaped templates + answer diagnosis) — `algorithms/misconceptions.py`, CLI `misconceptions`, 10 tests
- [ ] P1.11 unlimited-OCR for scanned artifacts [!] disk space
- [~] P1.12 GCS mirror sync — fixed a real gap: `sync_enabled` was defined in
      config but never actually gated the `sync-gcs` CLI command (dead
      config; sync would run regardless of the flag). Now gated, with
      `--force` override and `--interval-minutes`/`--max-cycles` for a
      supervised loop; 6 new tests (`tests/test_cli_sync_gcs.py`), all pass.
      Still `[~]` not `[x]`: nothing registers this with an external
      scheduler (cron/Task Scheduler) — that's a system-level change needing
      explicit user action — and `google-cloud-storage` isn't installed in
      this venv, so no real sync has actually been run against the live
      `varsh-dev-storage` bucket
- [ ] P1.13 full CBSE corpus acquisition (800+ QP/MS, model answers) [!] licensing/disk
- [x] P1.14 end-to-end RAG eval harness (`scripts/eval_rag.py`, answer metrics ported from RAG-Enhanced-NCERT-Tutor MIT)

## Phase 2 — Student Brain Graph (base ~25%)
- [x] P2.1 `docs/research/learning-science.md` reading map (research → algorithm table)
- [x] P2.2 learner model schema + event store (event sourcing, replay)
- [x] P2.3 forgetting model v2: FSRS-6 (DSR) port — implemented (`algorithms/fsrs.py`, MIT; `ForgettingParams.model="fsrs"` default, exponential kept)
- [x] P2.4 spaced-repetition simulator + parameter calibration (simulator: 89% fewer reviews vs naive; per-learner weight fitting: `algorithms/fsrs_fit.py`, `FSRSFit` grid-search class, 15/15 tests pass — checklist was stale, module already real)
- [x] P2.5 sleep-consolidation component (Walker): overnight stability boost — `ForgettingParams.sleep_boost`, capped, first-night-weighted
- [x] P2.6 retrieval-practice effect (Karpicke & Roediger): testing boost on stability gain — `answer`=retrieval vs `watch`=restudy (`restudy_gain`), scheduler defaults to retrieval mode
- [x] P2.7 motivation/self-efficacy model (Bandura/SDT) — `algorithms/motivation_model.py`, tested
- [x] P2.8 attention/fatigue model (Baker, D'Mello) — `algorithms/attention_model.py`, tested
- [x] P2.9 habit formation (Lally 66-day) — `algorithms/habit_model.py`, tested
- [x] P2.10 curiosity engine (Bjork desirable difficulty + novelty) — `algorithms/curiosity_engine.py`, tested

## Phase 3 — Indian Education Graph (base ~5%)
- [ ] P3.1 data catalog: ASER / UDISE+ / NCERT / CBSE / DIKSHA / PARAKH / NIPUN sources
- [ ] P3.2 system graph schema: Teacher→School→Parents→Village→District→Govt→Child
- [ ] P3.3 EKG-class gold datasets: keep 12-corpus prereq eval as the standing regression gate
- [ ] P3.4 dashboards/eval of learning-outcome attainment vs systemic factors

## Phase 4 — Algorithms Library (base ~15%)
Each module: evidence-grounded params, `version`, metrics entry point.
- [x] A1 knowledge_mastery (weights: accuracy/confidence/retention/application)
- [x] A2 forgetting_prediction → FSRS-6 (P2.3) + revision_scheduler (CLI `revise`)
- [x] A3 motivation_prediction (P2.7) — `algorithms/motivation_model.py`, tested
- [x] A4 attention_prediction (P2.8) — `algorithms/attention_model.py`, tested
- [x] A5 habit_formation (P2.9) — `algorithms/habit_model.py`, tested
- [x] A6 emotional_state — `algorithms/emotion_model.py`, tested
- [x] A7 curiosity_engine (P2.10) — `algorithms/curiosity_engine.py`, tested
- [x] A8 parent_guidance ("say this today") — `algorithms/parent_guidance.py`, tested
- [x] A9 teacher_assistance (class-level priority aggregation) — `algorithms/teacher_assistance.py`, tested
- [x] A10 career_discovery (Holland RIASEC mapping from behavior) — `algorithms/career_discovery.py`, tested
- [x] A11 reward_engine (celebration policy; SDT) — `algorithms/reward_engine.py`, tested
- [x] A12 study_planner v2 (prereq plan + FSRS spacing + session capacity) — `algorithms/study_planner.py`, CLI `study-plan`
- [x] A13 confidence_model (self-efficacy dynamics per concept) — `algorithms/confidence_model.py`, CLI `confidence`, 6 tests
- [x] A14 lifelong_learner_model (cross-year, cross-subject) — `algorithms/lifelong_model.py`, CLI `lifelong`, 7 tests

## Phase 5 — Human Learning Engine (base ~10%)
- [x] P5.1 daily loop: know / forgotten / tired / motivated / confident →
      plan — `algorithms/daily_loop.py` (597 lines), self-labeled "P5.1"
      in its own docstring, orchestrates forgetting/study_planner/
      confidence/attention/habit/motivation into one deterministic daily
      plan; 15 tests pass + 1 intentional xfail (`tests/test_daily_loop.py`)
      — checklist was stale, module already real
- [x] P5.2 API surface: revise, plan, stats, question-solve with evidence —
      `POST /v1/revise`, `/v1/plan`, `/v1/question/solve` in `api/main.py`
      (wrap `forgetting.RevisionScheduler`, `study_planner.StudyPlanner`,
      `qmap.QuestionMapper`), 10/10 tests incl. real seeded-graph/event-store
      round trip; fixed a latent `EventStore` sqlite thread-safety bug this
      surfaced (missing `check_same_thread=False`, same as `GraphStore`/
      `SourceRegistry` already had)
- [x] P5.3 offline eval: 90-day simulation of the loop on synthetic learners
      — `scripts/simulate_daily_loop.py` already existed, self-labeled
      "P5.3" in its own docstring, but had never actually run: `DEFAULT_DAYS`
      referenced but never defined (`NameError` at import time before
      `main()` could start), plus a typo'd constant, a misnamed local
      variable, and an undefined formatter function. Fixed all five bugs;
      it now runs and every headline claim in its own docstring is real
      (consistent > erratic retention, fatigue-prone respects its budget,
      "new" control has max exposure + lowest retention). 7 new tests
      (`tests/test_simulate_daily_loop.py`), all pass.
- [ ] P5.4 (later) classroom pilot protocol

## Immediate execution order (this sprint)
1. P2.3/A2 — FSRS-6 engine + scheduler integration (researched: OSR benchmark, Anki default since 2023; 30–50% fewer reviews than SM-2 at same retention) — done
2. P2.4 — simulator proving the claim on our own data — done
3. CLI `revise`, tests, docs — done
4. P2.5/P2.6 (sleep boost, retrieval-practice gain) as FSRS extensions — done
5. P1.9 (question→concept) done; A12 study_planner v2 done; P1.10 misconceptions done; A13 confidence_model done; A14 lifelong_learner done
6. P2.7–P2.10 / A3–A11 (motivation, attention, habit, curiosity, emotion, parent, teacher, career, reward) — found already implemented + tested 2026-09-11, checklist was stale; corrected, no rebuild needed
7. Curriculum & Micro-Scheduling (§10-14, §21-24) — `src/academicos/curriculum/` operational store, CBSE 10 bulk decomposition (138 topics, 404 subtopics), multi-day holidays, weekly timetable slots, period allocations, and delivery sequence reordering — done
8. Registry Status Discrepancy (`rg`) — Traced and fixed root cause in `SourceRegistry.register()` `ON CONFLICT` clause, corrected 3 tests, backfilled 408 rows (422 extracted sources now accurately tracked) — done
9. Storage & Concurrency Hardening — Applied `PRAGMA journal_mode=WAL` and `PRAGMA busy_timeout=60000` across all 17 SQLite stores, audited Render deployment & persistence pathways, verified Flutter local-engine offline sync — done

## Standing gates
- `python -m pytest tests -q` green after every change (1,184 passing as of 2026-09-16)
- 12-corpus prereq eval AUC unchanged for graph changes
- every algorithm change bumps `version`; parameters documented with evidence
