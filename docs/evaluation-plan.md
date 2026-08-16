# Evaluation Plan

## 1. Retrieval quality (per subject × doc-type cohort)
Gold sets: 60 hand-verified (query → relevant chunks) triples from QP/MS/curriculum.
Metrics: P@5, R@5, MRR, nDCG@10. Baselines: BM25-only, TF-IDF-only, hybrid.
Target: hybrid ≥ +10% MRR over BM25-only on the cohort.

## 2. Extraction fidelity (QP → questions, MS → marking points)
Gold: 30 papers × 5 random questions (marks, section, type, bloom), 20 marking
schemes (point count, point marks). Metrics: extraction_accuracy (exact field
match), F1 on question boundaries. Compare heuristic vs VLM paths.

## 3. Table extraction (weightage / blueprint tables)
Gold: 25 tables transcribed manually. Metric: cell-level exact/partial match.
Ensemble rule from XLLM-2025 finding: TATR/structural parse + MLLM validation.

## 4. Answer groundedness (doubt-solver)
30 CBSE-style doubts → answer + citations. Metrics: answer_groundedness
(verbatim sentence support), citation precision (top-3 cited chunks actually
answer the doubt), human rating 1–5.

## 5. Graph QA
20 multi-hop questions requiring 2+ traversals (e.g. "which 2025 circular
changed the X class subject pattern, and which papers reflect it?").
Metric: % answered correctly with full evidence chain.

## 6. Continuous eval (Phase 6)
Pinned eval set runs on every ingest/pipeline release; scores recorded in
`artifacts/eval/*.json`; regressions gate merges.

## 7. Memory-characteristics harness (from "AI Hippocampus", arXiv 2601.09113)

### 7.1 Temporality (does the memory respect time?)
- 20 questions requiring the *latest* state of a rule ("per the 2025 circular, is X
  still required?") — answer must reflect valid_from/valid_until, not superseded docs.
- Metric: % answers citing a non-superseded source (supersession precision).

### 7.2 Needle-in-a-haystack (pinpoint recall)
- 30 facts planted across QP/MS corpus ("which 2023 paper asked for 4 marks on topic T?").
- Metric: top-5 hit rate with BM25-only vs hybrid vs hybrid+subgraph (ablation).

### 7.3 Multi-hop graph QA (reasoning paths)
- 20 questions needing 2+ traversals, e.g. "Which blueprint maps unit U to marks M,
  and which question in the 2025 paper assesses it?" — evaluated via
  `retriever.reasoning_paths` + answer correctness.

### 7.4 Consistency & variance
- Same query repeated after re-ingesting a circular → answer must stay stable unless the
  circular actually changed content (consistency), and must change *when* it did (variance).

### 7.5 Redundancy
- Registry dedupe check: re-ingesting an identical file must produce 0 new sources
  (sha256 content-addressing) — already enforced; test asserts it.

### 7.6 Self-RAG-style retrieval necessity (Phase 4)
- Eval whether the agent retrieves when needed and abstains when the answer is in-context
  or unanswerable from the corpus (refusal precision on unanswerable questions).
