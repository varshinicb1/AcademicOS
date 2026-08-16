# Roadmap — 5 Phases (revised per learning-first strategy)

**North star:** not an AI tutor — a library of validated learning algorithms
backed by the world's best education knowledge graph. Most edtech products are
collections of features; we build an architecture that evolves for years.

> **Research objective:** discover the algorithms governing how children learn,
> forget, stay motivated, lose confidence, regain confidence, choose careers,
> and achieve mastery. Every document — curriculum, research paper, textbook,
> assessment, or policy — becomes reusable knowledge contributing to one or
> more algorithms.

---

## Phase 1 — The Knowledge Base (in progress)

Output is NOT PDFs. Output is a knowledge graph where every concept knows:
prerequisites, difficulty, estimated learning time, common misconceptions,
Bloom taxonomy, visualization ideas, experiments, real-world examples.

Sources to structure:
- NCERT textbooks (Grades 1–12) + NCERT Exemplar
- CBSE Question Bank, Sample Papers, Marking Schemes
- Previous 15–20 years board papers
- Learning outcomes, NCF 2023, NEP 2020
- Teacher handbooks, lab manuals, DIKSHA resources

Status:
- [x] Ingest → parse → extract → graph → retrieval → agents (AcademicOS core)
- [x] Corpus pipeline validated on 43 real CBSE sources
- [x] OpenIE entity/triple extraction (Sarvam LLM) — graph densified
- [ ] Full CBSE corpus (800+ QP/MS, NCERT, model answers)
- [ ] Concept spine: misconceptions, difficulty, learning time per concept
- [ ] Question→concept mapping (LLM-assisted, verifier-checked)
- [ ] Unlimited-OCR for scanned artifacts (blocked on disk space)
- [ ] GCS mirror sync

## Phase 2 — The Student Brain Graph

Agent reads cognitive science, neuroscience, educational psychology,
motivation, executive function, memory, attention, developmental psychology,
AI tutoring. Output: the **Human Learning Graph** —

```
Sleep → Attention → Working Memory → Learning → Confidence → Motivation → Long-term Success
```

This phase turns `docs/research/learning-science.md` into validated,
parameterized model components (forgetting curves, spaced repetition,
self-efficacy, ICAP, etc.) that the algorithms consume.

## Phase 3 — The Indian Education Graph

Download and structure: ASER, UDISE+, NCERT, CBSE, state boards, DIKSHA,
UNESCO, World Bank, OECD, PISA, NIPUN Bharat, PARAKH, government circulars.
Understand the system graph:

```
Teacher → School → Parents → Village → District → Government → Child
```

## Phase 4 — The Algorithms Library

Instead of a chatbot: algorithms. Each is evidence-grounded, evaluated, and
versioned under `src/academicos/algorithms/`:

1. **Knowledge Mastery Score** — mastery % instead of marks (confidence +
   retention + application)
2. **Forgetting Prediction** — "when will this child forget?" (tomorrow /
   5 days / 2 weeks / 3 months) → auto-revision
3. **Motivation Prediction** — low motivation → reduce difficulty, insert
   game, short break, small success → confidence restored
4. **Career Discovery** — from observed behavior (questions asked, projects
   built, videos watched, reading habits, attention) → career graph
5. **Parent AI** — "don't teach. Just say this today: 'Great consistency
   this week.'"
6. **Teacher AI** — "today's priority: 12 students need fractions. Ignore
   chapter 8. Teach fractions."
7. Attention prediction, habit formation, emotional state, curiosity engine,
   revision scheduler, reward engine, study planner, confidence model,
   lifelong learner model.

Repository layout (each module is evidence-grounded, evaluated, versioned):

```
algorithms/
├── knowledge_mastery/
├── forgetting_prediction/
├── attention_prediction/
├── motivation_prediction/
├── habit_formation/
├── emotional_state/
├── curiosity_engine/
├── parent_guidance/
├── teacher_assistance/
├── career_discovery/
├── revision_scheduler/
├── reward_engine/
├── study_planner/
├── confidence_model/
└── lifelong_learner_model/
```

## Phase 5 — The Human Learning Engine

Every day it asks: What does this child know? What have they forgotten? Are
they tired? How motivated? How confident? What should they study? How long?
When to break? Solve questions / watch video / revise / rest? Parents
encourage? Teacher intervene? → **Update learner model.**

Every interaction updates the learner model. This is the loop no edtech
company has built.
