# The LLM Layer: Where It Is Necessary, Where It Is a Liability

**Status:** Decision document (research + recommendation)
**Scope:** AcademicOS backend (`src/academicos/`), CBSE/NCERT K-12
**Related:** `docs/provider-architecture.md`, `docs/compliance.md`, `docs/evaluation-plan.md`, `AGENTS.md`, `CLAUDE.md`
**Method:** 24 targeted web searches (benchmarks, security literature, framework comparisons, Indian regulation) plus direct inspection of this repository. Every externally sourced number is cited inline. Where a claim could not be verified, it is flagged in [Section 9](#9-verification-and-confidence).

---

## 0. Executive verdict

The team's instinct is correct and should be codified as a rule:

> **An LLM is only justified where the output is (a) open-ended natural language, (b) must be *judged* rather than *computed*, and (c) either a human reviews it before it affects a student, or a deterministic system validates it after. Everything else is a liability.**

Under that rule, of the four LLM-powered/candidate capabilities today:

| Capability | Verdict | Implementation to ship |
|---|---|---|
| Curriculum Topic/Subtopic extraction | **Keep LLM, keep human-in-the-loop** | LLM *proposes*, deterministic validator checks grounding against the page, principal approves; never auto-materialize |
| Doubt solving | **Keep LLM, bound tightly** | Retrieval-grounded (hybrid BM25+embedding) generation, citations mandatory, refusal on no-evidence, cached |
| Answer-script evaluation (subjective) | **Keep LLM for *signalling*, never for *scoring alone*** | LLM proposes marking-point outcomes; deterministic rubric scorer + teacher swipe-review is the gate; LLM score never commits without teacher |
| Question generation | **LLM for *drafting only*** | LLM drafts stems; deterministic blueprint/section/marks validator + parallel-set generator owns the paper; teacher approves |
| Everything already deterministic | **Freeze** | Do not introduce an LLM into working-day math, weightage allocation, lesson scheduling, blueprint balancing, parallel sets, FSRS, BM25/TF-IDF retrieval, chapter tagging, lexical subtopic matching, or rubric scoring |

The single most important finding from the literature: **an LLM's agreement with human graders is *below* the agreement between two human graders, on every benchmark we found** ([AIMECon 2025](https://aclanthology.org/2025.aimecon-wip.9.pdf), [CEUR Vol-3772](https://ceur-ws.org/Vol-3772/paper10short.pdf)). Human-human quadratic weighted kappa (QWK) on essay scoring is roughly **0.77-0.86**; the best LLM configuration reached **0.74**, and zero-shot holistic scoring sits near **0.60**. This is the quantitative reason the answer-script evaluator cannot be the final scorer in a system whose entire value proposition is defensible provenance.

---

## 1. Cost / latency / accuracy / reliability comparison by capability

### 1.1 The four implementation families

| Family | Determinism | Cost | Latency (typical) | Auditability | Failure mode |
|---|---|---|---|---|---|
| **Deterministic algorithm** | Bit-exact | ~0 | <1 ms - 10 ms | Full (code + inputs) | Only bugs |
| **Embedding model** (frozen, local) | Bit-exact for same weights/device | ~0 marginal (one-time embed) | 10-100 ms | Full | Silent semantic miss |
| **Open LLM API call** | Non-deterministic **even at temperature 0** | $0.15-$15 per 1M input tokens | 0.3 s (cache) - 90 s (reasoning) | Partial (provider logs, prompt+model version) | Empty/truncated/invalid output, hallucination |
| **Fine-tuned small model** (local, <4B) | Bit-exact with fixed seed/weights | one-time training + ~$0 marginal | 20-200 ms local | Full (weights are an artifact) | Task drift outside training distribution |

### 1.2 Non-determinism is not a tuning problem

This is the fact that kills "just set temperature 0":

- Under **exact repeats at temperature 0.0**, `gpt-4o-mini` produced distinct outputs in **~0.24 of runs**; `llama3.1-8b` in ~0.09; average Jaccard similarity across outputs 0.89 and 0.97 respectively ([Quantifying non-deterministic drift in LLMs](https://arxiv.org/pdf/2601.19934)).
- A 480-attempt reproducibility study across 6 models x 4 temperatures x 10 executions found that **"even at temperature zero some estimates lead to different conclusions about the same research question"** ([Same Prompt, Different Outcomes, arXiv 2602.14349](https://arxiv.org/pdf/2602.14349)).
- For LLM-as-judge specifically, **1-2 of 7 borderline items remain non-reproducible even under forced greedy decoding (top_k=1)** ([Necessary but Not Sufficient, arXiv 2606.26185](https://arxiv.org/html/2606.26185v1)). The cause is documented to be serving infrastructure, not sampling: floating-point non-associativity and batch-dependent kernels. vLLM's own docs state it "does not guarantee the reproducibility of the results by default" ([vLLM reproducibility docs](https://github.com/jxzhuge/vllm/blob/main/docs/usage/reproducibility.md)).

**Consequence for AcademicOS:** any pipeline that "re-runs the LLM" to reproduce a mark is not reproducible. Reproducibility must come from *logging the model+prompt version and the cached output*, not from re-invoking the model. This directly contradicts a naive audit story and must shape the architecture ([Section 4](#4-architecture-patterns-that-contain-llm-risk)).

### 1.3 Capability-by-capability

The table below is the core deliverable. "Evidence" links to the benchmark or repo component that justifies the row.

| Capability | Deterministic | Embedding | LLM | Fine-tuned SLM | Recommended | Why |
|---|---|---|---|---|---|---|
| Working-day calc | Yes | - | - | - | **Deterministic** | Arithmetic; LLM only adds variance |
| Marks-weightage period allocation (largest-remainder) | Yes | - | - | - | **Deterministic** | Provably fair apportionment; an LLM cannot beat a proven algorithm |
| Lesson schedule from curriculum order | Yes | - | - | - | **Deterministic** | Constraint satisfaction; auditable |
| Blueprint section balancing | Yes | - | - | - | **Deterministic** | Exact counts; LLM would be strictly worse |
| Parallel set generation | Yes | - | - | - | **Deterministic** | Hash/equivalence partitioning must be exact |
| FSRS spaced repetition | Yes | - | - | - | **Deterministic** | Published scheduler; changing it breaks learner state |
| BM25 / TF-IDF retrieval | Yes | optional | No | No | **Deterministic (+ neural reranker later)** | BM25 is the **3rd-best** method on BEIR overall, beaten only by neural rerankers; hybrid RRF + cross-encoder reached Recall@5 0.816 vs 0.644 (BM25) and 0.587 (dense) on a financial QA benchmark ([arXiv 2604.01733](https://arxiv.org/html/2604.01733v1), [BEIR NeurIPS 2021](https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/file/65b9eea6e1cc6bb9f0cd2a47751a186f-Paper-round2.pdf)) |
| Chapter tagging | - | **Yes** | No | optional | **Embedding (frozen)** | Classification against a fixed label set; embeddings are deterministic and cheap |
| Lexical question-to-subtopic matching | Yes | optional | No | optional | **Deterministic** | Exact term/ clause matching is what the task is |
| Rubric scoring vs marking-scheme value points | Yes | optional | guardrail | No | **Deterministic (+ embedding for paraphrase recall)** | Rubric scoring is a set-membership/coverage computation, not a judgement |
| **Curriculum Topic/Subtopic extraction** | partial | partial | **Yes** | plausible later | **LLM-propose + deterministic validate + human approve** | Source PDFs are messy; layout headers, tables, bilingual text. The step that *names* and *groups* topics needs judgement. Must inherit provenance from the page bbox |
| **Doubt solving** | No | retrieval | **Yes** | No | **Retrieval-grounded LLM** | Open-ended NL. Must cite chunks; refuse when evidence is absent |
| **Answer-script evaluation (subjective)** | partial (rubric) | partial | **Yes** | optional (see 1.5) | **LLM-propose + deterministic rubric + teacher gate** | LLM/human QWK tops out ≈0.74 vs human-human ≈0.77-0.86; it cannot be the sole scorer |
| **Question generation** | validation | - | **Yes (draft)** | plausible later (SFT) | **LLM-draft + deterministic validator + teacher approve** | Genuinely generative; the *constraints* must be deterministic |

### 1.4 Answer-script evaluation: the numbers that decide it

| Setting | Metric | Value | Source |
|---|---|---|---|
| Human-human | QWK (total score) | **0.77-0.86** | [AIMECon 2025](https://aclanthology.org/2025.aimecon-wip.9.pdf) |
| PEG (feature-based AES) | QWK | 0.61-0.74 | same |
| GPT-4o, context + few-shot CoT (best strategy) | QWK | **0.74** | same |
| GPT-4o, naive | QWK | 0.14 -> 0.20 exact agreement | same |
| Open-weight LLMs, zero-shot holistic | QWK | **~0.601**, bias -0.05 | [arXiv 2604.00259](https://arxiv.org/html/2604.00259) |
| Fine-tuned DeBERTa on Persuade 2.0 | QWK | **0.87** | [AES adversarial study](https://aclanthology.org/anthology-files/anthology-files/pdf/aimecon/2025.aimecon-sessions.10.pdf) |
| ChatGPT (GPT-3.5) vs human, short answer | weighted kappa vs human-human 0.395 | human-human 60.88% exact; ChatGPT "minimal agreement beyond chance" | [CEUR Vol-3772](https://ceur-ws.org/Vol-3772/paper10short.pdf) |
| Sentence-similarity + regression, few labelled examples | RMSE 0.717, beating fine-tuned transformers | [ERIC ED675666](https://files.eric.ed.gov/fulltext/ED675666.pdf) |

Two conclusions:

1. **A supervised SLM can beat an LLM on scoring agreement** (0.87 vs 0.74) *when you have labelled essays*. AcademicOS does not have labelled CBSE essays at scale, so the near-term answer is the LLM-propose + teacher-gate, not an in-house AUC model.
2. **Cheap non-LLM signals are competitive for short answers.** The sentence-similarity+regression result beats fine-tuned transformers, and the repo already owns sentence embeddings. For short-answer recall, a deterministic/embedding scorer should be tried *before* an LLM call.

### 1.5 Fine-tuned small models: when they beat an API

- A **1B Llama-3.2 QLoRA** fine-tune reached **99% exact-match accuracy, matching GPT-4.1** on structured intent recognition ([arXiv 2510.21970](https://arxiv.org/html/2510.21970v1)).
- Fine-tuned encoders match or beat zero-/few-shot LLM prompting on fixed-label classification **at 1-2 orders of magnitude lower cost and latency**; cost per 1M requests: fine-tuned encoder **$5-25** vs LLM prompting **$193-2,120** ([arXiv 2602.06370](https://arxiv.org/pdf/2602.06370)).
- Fine-tuned small LLMs "still significantly outperform" zero-shot GPT-3.5/4 and Claude on text classification ([arXiv 2406.08660](https://arxiv.org/html/2406.08660v1)).
- For Indic languages specifically, **Sarvam-1 (2B)** matches or exceeds much larger models on 10 Indic languages with 1.4-2.1 token fertility vs 4-8 for general multilingual tokenizers, and is **4-6x faster to infer** ([Sarvam-1 blog](https://www.sarvam.ai/blogs/sarvam-1)). Sarvam 30B/105B are **open-weight** as of March 2026 ([Sarvam open-source blog](https://www.sarvam.ai/blogs/sarvam-30b-105b)).

**Decision:** fine-tuning is the correct *later* move for exactly two jobs where the label set is stable and volume is high: (a) curriculum section classification, and (b) answer marking-point detection. **Do not fine-tune before there is a labelled dataset** — the first several hundred human-approved extraction proposals and graded answer sheets *are* that dataset. Capture them now with the model/prompt version attached.

### 1.6 Cost at scale, concretely

Token pricing, standard rates (verify before committing; providers move):

| Model | Input /1M | Output /1M | Cached input | Source |
|---|---|---|---|---|
| GPT-4o mini | $0.15 | $0.60 | $0.075 | [TECHSY 2026 table](https://techsy.io/en/resources/tools/openai-api-cost-calculator) |
| Gemini 3 Flash | $0.50 | $3.00 | - | [gentic.news](https://gentic.news/llm-api-pricing-2026) |
| Claude Haiku 4.5 | $1.00 | $5.00 | $0.10 | [costgoat](https://costgoat.com/pricing/claude-api) |
| Claude Sonnet 4.6 | $3.00 | $15.00 | $0.30 | same |

Levers that matter more than model choice: **prompt caching cuts cached input ~90%**, and **batch is 50% off** ([costgoat](https://costgoat.com/pricing/claude-api), [gentic.news](https://gentic.news/llm-api-pricing-2026)).

A worked estimate for a realistic pilot (flagged as arithmetic, not a benchmark):
- 1 school, 20 classes, 40 students/class = 800 students.
- Subjective grading: 30 LLM-graded answers/student/term. Prompt (question + scheme + OCR answer + system) ~1,800 input tokens; output ~700 tokens (repo's `MAX_TOKENS=4000`, reasoning model).
- Per term: 24,000 calls x (1,800 in + 700 out).
- On Haiku 4.5 with no caching: 43.2M in x $1 + 16.8M out x $5 = **$43.2 + $84 = ~$127/school/term**.
- With a well-designed cache on the (question + scheme) prefix — which is identical across a class — input collapses toward the cached rate; realistic **$60-90/school/term**.

Cross-check against the repo's own reality: the code comment in `llm/sarvam.py` notes sarvam-105b burns **past 1,800 tokens reasoning before writing**, and `llm_evaluate.py` sets `MAX_TOKENS = 4000` with a 90 s timeout. That is exactly the profile where a non-reasoning extraction model (or a fine-tuned 1-3B model) is 10-100x cheaper for the *same* structured task. **Reasoning models are the wrong tier for structured extraction.**

---

## 2. Specific failure modes of LLMs in production education software

### 2.1 Hallucinated curriculum content

- **Intrinsic hallucination** rates (contradicting the supplied source): GPT-4o **1.5%**, Llama-3.1-405B **3.9%**, Claude-3.5-Sonnet **4.6%** ([HalluLens, arXiv 2504.17550](https://arxiv.org/html/2504.17550v1)).
- **Extrinsic hallucination** (inventing facts not in training/source) is far worse: Llama-3.1-405B's best-case hallucination rate was **26.84%**, achieved only by refusing to answer **56.77%** of the time ([HalluLens](https://arxiv.org/html/2504.17550v1)).
- On a hard multi-turn benchmark, **even Claude-Opus-4.5 and GPT-5.2-thinking hallucinate in >30% of cases *with* web search, ~60% without** ([HalluHard, arXiv 2602.01031](https://arxiv.org/pdf/2602.01031)).
- Hallucination rate increases log-linearly with knowledge *obscurity* and *length* ([Law of Knowledge Overshadowing, ACL 2025](https://aclanthology.org/2025.findings-acl.1199.pdf)).

**Why this is existential for AcademicOS:** an invented definition in a syllabus node poisons the knowledge graph, every lesson plan derived from it, every generated question, and every progress report — silently, because the failure is fluent. The existing human-approval gate on Topics/Subtopics is not bureaucracy; it is the only control that works. It must extend to *any* content that can reach a student.

**Mitigation already latent in the repo:** `AGENTS.md:19` stages extraction proposals in `curriculum_extraction_runs`/`proposals` requiring principal approval. This is the correct pattern. Keep it.

### 2.2 Non-determinism breaking reproducibility and audit

See [1.2](#12-non-determinism-is-not-a-tuning-problem). The audit consequences:

- A mark cannot be reproduced by re-running. **The cached output + model version + prompt hash is the audit artifact.**
- `replay divergence` — a named failure mode where "LLM-based consumers of a deterministic event log produce different downstream outputs under model-version or prompt changes" ([Runtime Architecture Patterns, arXiv 2605.20173](https://arxiv.org/abs/2605.20173)).
- LLM-as-a-judge is **reliable but not valid**: high test-retest reliability (>=0.95) coexists with **severe position bias (>0.10) in the same model** ([arXiv 2606.19544](https://arxiv.org/html/2606.19544v1)). Reproducibility of a *wrong* judgement is still wrong.

### 2.3 Prompt injection via student-submitted text

This is the most under-appreciated risk for a system that OCRs free-text student answers.

- Research explicitly on LLM-based automatic grading: students can append crafted strings to answers (rubric overwriting, question substitution, fake-answer injection, instruction replacement, role-play) and **"current LLM-based AG systems remain highly vulnerable"** ([arXiv 2606.03090](https://arxiv.org/html/2606.03090v1)).
- Wharton ran **~40,000 grading trials**: frontier models largely resist simple injections, but **GPT-4o mini inflated scores by nearly 20 percentage points on average**, and Gemini 3 Pro was meaningfully vulnerable to verbose injections placed at the beginning or middle of longer documents. Crucially, models **"almost never explicitly acknowledged encountering a prompt injection"** — verbalized detection in only **1.4%** of frontier-model trials ([Wharton GAIL, Apr 2026](https://gail.wharton.upenn.edu/research-and-insights/hidden-prompt-injections)).
- A targeted educational framework showed attacks can be made **pedagogically plausible** — embedded in reflective reasoning rather than an obvious "ignore previous instructions" ([Nature Sci Rep, 2026](https://www.nature.com/articles/s41598-026-46563-1)).
- Indirect prompt injection is now operationally exploited in the wild, with a **32% relative increase** in malicious IPI content Nov 2025 -> Feb 2026 ([CSA research note](https://labs.cloudsecurityalliance.org/wp-content/uploads/2026/04/CSA_research_note_indirect_prompt_injection_in_the_wild_20260426-csa-styled.pdf)). OWASP ranks **LLM01: Prompt Injection** first in the [2025/2026 Top 10](https://genai.owasp.org/llmrisk/llm01-prompt-injection).

**Because the threat model is a student, not an outsider, the incentive is enormous.** A student who discovers "append this sentence and get full marks" has a rational incentive to spread it. Mitigations that actually hold: (a) deliver the answer text as *data* in a structured field, never concatenated into the instruction stream; (b) run a deterministic pre-filter (guard model / heuristics) and reject submissions that don't resemble answers; (c) require the teacher gate as the final commit; (d) log the raw submission so replay shows the injection. Google's own defence stack uses exactly this layering — deterministic configurable defences first, ML/LLM defences second ([Google Security Blog, Apr 2026](http://security.googleblog.com/2026/04/google-workspaces-continuous-approach.html)).

### 2.4 PII leakage to third-party APIs and DPDP Act 2023

Every CBSE student is a minor under Indian law, which triggers the child-data provisions of the **Digital Personal Data Protection Act, 2023** specifically:

- **Verifiable parental consent** is required before processing a child's personal data (s.9(1)); a generic admission-form clause or a student's own "I agree" does **not** satisfy this ([India Code, DPDP Act 2023](http://indiacode.nic.in/bitstream/123456789/22037/1/a2023-22.pdf), [DSCI FAQ](https://www.dsci.in/files/content/documents/2024/FAQs-on-DPDP-Act-2023-MiniBooklet.pdf)).
- **No tracking, behavioural monitoring, or targeted advertising directed at children** (s.9(3)).
- **Rule 12 exemption**: educational institutions are exempt from verifiable parental consent **only** where processing is solely for educational purposes and in the interest of child safety. It is **not** a blanket exemption ([DPDPA for EdTech](https://dpdp.lkslaw.com/sectors/edtech)).
- Penalties for child-data violations and breach-notification failures reach **₹200 crore** ([PIB DPDP Rules 2025](https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/nov/doc20251117695301.pdf)).
- The **DPDP Rules, 2025 were notified 14 Nov 2025**, with an **18-month phased compliance clock** (~mid-2027 full effect). The runway is for building, not deferring ([PIB](https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/nov/doc20251117695301.pdf)).

**AcademicOS-specific risk:** sending a scanned, OCR'd answer booklet to `api.sarvam.ai` transmits a minor's handwriting, name (if present), roll number, and academic performance. Two things follow:

1. **Data-minimisation is a legal control, not a nicety.** Strip roll number/name from the prompt; pass a per-request pseudonymous token. The system already has `assessment/consent.py` and `docs/dpa-template.md` — wire them to the LLM path.
2. **Reversible pseudonymisation is available and cheap.** Presidio + placeholders (`<PERSON_1>`, `<ROLL_1>`) let the model reason about entities without seeing real values, then restore locally ([Presidio/LiteLLM tutorial](https://github.com/BerriAI/litellm-docs/blob/main/docs/tutorials/presidio_pii_masking.md), [PrivAiTe](https://github.com/crp4222/PrivAiTe)). Note the residual-risk caveat: **Presidio is best-effort, not a guarantee** ([Presidio docs](https://pkg.go.dev/github.com/Microsoft/presidio)), and a 2026 evaluation of eight privacy techniques found **no single technique dominates**; the best combination (local-only + redact + rephrase) achieved **0.6% leak on PII and 31.3% on proprietary code** ([LLM-Redactor, arXiv 2604.12064](https://arxiv.org/html/2604.12064v1)).
3. **Prefer local self-hosted inference for anything that can identify a child.** Sarvam 30B/105B are open-weight as of March 2026, so a self-hosted deployment is *technically* possible. Whether it is *economically* possible for a school-scale deployment is unverified here — flag for a cost spike.

### 2.5 Cost at scale

Covered in [1.6](#16-cost-at-scale-concretely). The structural point: **an LLM in a per-student, per-answer, per-question loop makes the bill scale with the school's size and the teacher's grading frequency.** Deterministic code in the same loop costs nothing. Every capability you can move from "LLM" to "deterministic + occasional LLM," the better the unit economics.

---

## 3. Where LLMs are genuinely irreplaceable

Four tasks survive the "open-ended + must-be-judged + human/validator gate" test.

### 3.1 Open-ended subjective answer grading

A keyword matcher and a rubric scorer cannot award credit for "correct method with an arithmetic slip," recognise a valid alternate method, or read through OCR noise. The repo's `llm_evaluate.py` system prompt already encodes CBSE spot-evaluation conventions ("liberty of correction") precisely because a deterministic scorer cannot express them.

**But the evidence says it must be *advisory*.** Best LLM QWK ≈ 0.74 vs human-human ≈ 0.77-0.86; one study found ChatGPT's agreement with humans "minimal beyond chance" ([CEUR](https://ceur-ws.org/Vol-3772/paper10short.pdf)). Medical-education ASAG found **"verification by a human grader is still required"** and that LLMs give partial credit on answers humans marked fully wrong ([PMC11429088](https://pmc.ncbi.nlm.nih.gov/articles/PMC11429088)). The repo's `REVIEW_THRESHOLD` + swipe-review queue is therefore not a transitional concession; it is the permanent design.

### 3.2 Natural-language doubt solving

A student asking "why does a convex lens form a real image beyond 2F?" needs generated explanation, not retrieval of a paragraph. Prompting to answer *only* from retrieved chunks and to cite them is the standard grounded-generation pattern, and the repo's `agents/critic.py` (Self-RAG-style reflection) already implements the relevance/support check. **Irreplaceable, provided citations are mandatory and the system refuses when retrieval is empty.**

### 3.3 Rubric generation from free text

Turning a prose marking scheme into structured value-points is a real extraction problem with open-ended input. It is also the step whose errors are most dangerous, so the same approve-before-use gate applies.

### 3.4 Curriculum extraction from messy PDFs

NCERT/CBSE PDFs mix layout, tables, bilingual text, and equations; heuristic layout parsers produce plausible-looking but wrong section boundaries. The LLM's judgement over a page *is* the value here, bounded by a deterministic grounding validator (every proposed topic must be locatable in the page text / bounding box). This is why the repo's design — LLM proposes, provenance is recorded, principal approves — is the correct one.

### 3.5 Teacher-facing natural-language interfaces

A teacher asking "show me which chapters I haven't covered and what's most at risk" should get an answer, not a query builder. This is an LLM **router** over deterministic tools, which is the safest possible LLM role: the model selects a tool and formats the result; the numbers come from deterministic code.

---

## 4. Architecture patterns that contain LLM risk

The repo already implements several; this section names them and specifies the missing ones.

### 4.1 The stochastic-deterministic boundary (SDB) as a first-class object

The strongest framing from the literature: treat the boundary between stochastic model output and deterministic system action as a **four-part contract — proposer, verifier, commit, reject signal** ([Runtime Architecture Patterns, arXiv 2605.20173](https://arxiv.org/abs/2605.20173)). Every LLM call in AcademicOS should cross this boundary explicitly:

```
LLM (proposer)  ->  deterministic validator (verifier)  ->  commit (DB write)  or  reject (fallback)
```

Never `LLM -> DB`.

### 4.2 Human-in-the-loop approval (already present — extend it)

- Current: curriculum Topic/Subtopic proposals (`AGENTS.md:19`).
- Required: answer-script LLM evaluation (teacher swipe-review already exists — keep it mandatory for commit), generated question papers (teacher approval before publish), doubt-solving answers that are surfaced to students *as authority* (label as AI-generated + cite sources).

### 4.3 Deterministic validators around every LLM output

Each capability needs a *specific* validator, not a generic schema check:

| LLM output | Deterministic validator |
|---|---|
| Topic/Subtopic proposal | Every proposed string must be findable in the page text; page + bbox recorded; no proposal without provenance |
| Marking-point outcome | Point IDs must exist in the official scheme; sum of awarded marks must equal sum of point marks; awarded=true requires a cited span |
| Generated question | Marks/section/type must match the blueprint slot; parallel-set equivalence; nothing outside the syllabus node's subtopics |
| Doubt answer | Every cited chunk must exist in the retrieved set; refusal if retrieval empty; no numeric answer without cited source |

### 4.4 JSON-schema-constrained generation — use it, but do not trust it alone

- Structured output removes *parse* failures: schema validity for Llama-3.1-8B rose from **68.7% to 100%** with JSON-schema mode ([arXiv 2607.18261](https://arxiv.org/pdf/2607.18261v1)).
- **But schema-valid output can be semantically wrong.** Same study: semantic success stayed at **36.0%** for Llama-3.1-8B; Gemma-2-2B reached **100% schema validity with 2.0% semantic success and 41.7% unsafe acceptance**. The paper's own conclusion: *"structured output is a necessary interface layer, not a substitute for domain verification and fail-closed execution."*
- Constrained decoding carries a **3.6x-8.2x latency overhead** and can degrade task accuracy on complex schemas ([arXiv 2605.02363](https://arxiv.org/html/2605.02363v1)); a separate benchmark found it can *speed up* generation ~50% on simpler schemas ([arXiv 2501.10868](http://arxiv.org/html/2501.10868v1)). Framework choice matters — `guidance` had the highest compliance; `Outlines` lower due to timeouts.
- Also note: **schema-in-prompt is often enough.** A Claude Haiku 4.5 benchmark found plain prompting produced schema-correct output only **25%** of the time, while **pasting the schema into the prompt hit 100%** — no constrained decoding needed ([structured-output-eval](https://github.com/tkarim45/structured-output-eval)).

**Applied to the repo:** `llm/sarvam.py`'s `chat_json` is an *extraction heuristic*, not a contract. Replace it at the call site with a Pydantic model (`response_model`), validate, and on failure fall back to the deterministic engine rather than shipping a salvaged partial. The existing truncated-JSON salvage logic hides failures — keep it as a *diagnostic*, not a *recovery path*.

### 4.5 Caching and idempotency

- Semantic caching cuts API calls **up to 68.8%** with hit rates 61.6-68.8% and **>97% positive hit rate** on the cached answers ([GPT Semantic Cache, arXiv 2411.05276](https://arxiv.org/html/2411.05276v3)); GPTCache reports 2-10x speedup on hits ([ACL NLP-OSS](https://aclanthology.org/2023.nlposs.1.24.pdf)).
- For AcademicOS the highest-value cache key is **(question_id + scheme_version + model + prompt_hash + normalized_answer)** for grading, and **(document_id + page + model + prompt_hash)** for extraction. Because the question+scheme prefix is shared across a whole class, **provider prompt caching** (up to ~90% off cached input) compounds with application-level caching.
- **Idempotency:** the same answer graded twice must return the cached result. This is also what makes the audit story true — the artifact is the cached output.

### 4.6 Provenance recording of model + prompt version

Every LLM-authored row must store: `provider`, `model_id`, `model_version` (if exposed), `prompt_hash`, `temperature`, `max_tokens`, `created_at`, `output_sha256`, and `cache_key`. Without the prompt hash, a prompt change silently invalidates every prior audit. This is cheap and must be mandatory.

### 4.7 Graceful degradation to a deterministic fallback

This is already the repo's pattern and it is correct:
- `SarvamCritic` returns a neutral score when unavailable (`provider-architecture.md`).
- `evaluate.py` keyword matcher remains the default; `llm_evaluate.py` is the enhancement.
- `mobile_scan.py` falls back to the deterministic path.

**Rule to codify:** *every* LLM call site must have a named deterministic fallback, and the API response must carry `engine: "llm" | "deterministic"` so downstream code (and the teacher UI) knows which one produced the result. The repo's `Evaluation` shape already lets both engines drop into the same pipeline — expose the discriminator.

### 4.8 Per-school / per-tenant cost controls

Missing today and required before multi-school pilots:

- A per-tenant token budget with hard cut-off, degrading to the deterministic engine when exhausted.
- Per-tenant rate limits and a kill switch.
- Cost attribution per call (tokens x price) written to the audit row, so a single school's spend is visible before the invoice.
- A cache hit-rate dashboard; a low hit rate on grading is a design smell (means prompt prefixes aren't being reused).

### 4.9 PII redaction / pseudonymisation layer

Insert a Presidio-style pre-call redactor and post-call restorer before any LLM path that touches a scanned answer, and log redaction counts. Follow Google's layered model: **deterministic pattern defences first, then ML**. Treat residual leakage as real ([LLM-Redactor](https://arxiv.org/html/2604.12064v1)) and reflect it in the DPA.

---

## 5. The agentic framework question

### 5.1 Comparison

| Framework | Maturity | Production readiness | Determinism / testability | Observability | Self-hosting | Python/FastAPI fit |
|---|---|---|---|---|---|---|
| **LangGraph** | Highest; 1.0 GA Oct 2025; ~40.6k stars, MIT ([promptquorum](https://www.promptquorum.com/local-llms/best-ai-agent-framework-2026)) | Best-in-class for stateful/branching/HITL; checkpointers (Postgres/SQLite), interrupt/resume ([Alice Labs](https://alicelabs.ai/en/insights/langgraph-vs-crewai-2026)) | Explicit typed state; node-level checkpoints make tests possible, but each node is still an LLM call | LangSmith (paid) or OTel via `LANGSMITH_OTEL_ENABLED` -> Logfire/any OTel backend ([Pydantic docs](https://pydantic.dev/docs/logfire/integrations/llms/langgraph/)) | Free/self-host; `langgraph-platform` and LangSmith are the paid layer | Good; adds a graph abstraction and `langchain-core` dependency |
| **CrewAI** | High stars (~57.7k), MIT; fastest to prototype | Fast to a first build; **requires the most hardening**; "execution is non-deterministic"; no native persistence ([N-iX](https://www.n-ix.com/langgraph-vs-crewai-vs-autogen), [Ailog](https://app.ailog.fr/en/blog/guides/agent-frameworks-comparison-2026)) | Weakest determinism — role/collaboration loops are hard to pin down | CrewAI Enterprise console, logs | Self-host free | Python-only; good DX but poor fit for a culture that wants testability |
| **AutoGen** | **Maintenance mode in 2026**; README points new users to Microsoft Agent Framework ([promptquorum](https://www.promptquorum.com/local-llms/best-ai-agent-framework-2026)) | Do not start new work here | Conversation-driven, least predictable | AutoGen Studio / Agent Framework | Self-host, but no roadmap | Microsoft-stack leaning |
| **LlamaIndex** | Mature; strongest at RAG/data; ~6 ms framework overhead, ~1.6K tokens/query vs LangChain ~2.4K ([MLM](https://machinelearningmastery.com/llm-orchestration-frameworks-compared-langchain-vs-llamaindex-vs-raw-api-calls)) | Good for retrieval; agent layer still evolving | Moderate | OTel / integrations | Self-host free | Good, but overlaps heavily with the repo's existing retriever |
| **Pydantic AI** | **1.0 since Sep 4 2025**; ThoughtWorks radar: "stable, well-supported ... reliable and widely adopted" ([ThoughtWorks](https://www.thoughtworks.com/en-us/radar/languages-and-frameworks/pydantic-ai)) | Production-grade by design: typed outputs, validation, retries, DI, MCP/A2A/AG-UI | **Strongest**: agents are typed Python objects; output validated against a Pydantic model; retries on validation failure; `pydantic-graph` for typed state machines ([ZenML](https://www.zenml.io/blog/pydantic-ai-vs-langgraph)) | 100% OpenTelemetry GenAI semantics; works with Logfire or *any* OTel backend ([Pydantic docs](https://pydantic.dev/docs/logfire/get-started/comparisons/langsmith)) | Self-host free; Logfire free tier, no lock-in (OTel) | **Best fit** — same team as Pydantic, which FastAPI already uses; `Agent` feels like a FastAPI object |
| **OpenAI Agents SDK** | Young; provider-leaning | Viable | Moderate | Vendor OTel | Self-host the SDK, not the model | Good but couples to OpenAI models |
| **Semantic Kernel** | Mature for .NET; Python less mature | Microsoft-stack oriented | Moderate | Azure Monitor | Self-host | Weaker fit for a pure-Python FastAPI backend |
| **DSPy** | Mature optimizer; **not an orchestrator** | In production at Shopify, Databricks, Dropbox, JetBlue, Replit ([DSPy](https://dspy.ai/production)) | Deterministic *after* compile; the optimizer is offline | OTel/MLflow tracing | Self-host free | Excellent as a **prompt-optimization step**, not as the runtime agent layer |
| **Plain Python** | Trivially "mature" | Highest — you own it | **Fully deterministic**; unit-testable | Whatever you choose | n/a | Perfect; zero framework overhead; raw API is consistently fastest ([MLM](https://machinelearningmastery.com/llm-orchestration-frameworks-compared-langchain-vs-llamaindex-vs-raw-api-calls)) |

### 5.2 Recommendation: **Pydantic AI**, with plain-Python orchestration retained

Adopt **Pydantic AI** as the LLM-call layer. **Do not adopt a graph framework today.**

Reasoning, in order of weight:

1. **It gives the exact thing the team is missing: typed, validated LLM output with automatic retry-or-fail-closed.** The whole risk posture of this codebase is "no unverified claim may enter." Pydantic AI makes `response_model` the interface — an LLM that returns the wrong shape or semantics *cannot* be silently consumed. This is the single highest-leverage fix available given the observed 50-75% truncated/empty rate on bulk extraction.
2. **FastAPI fit is native.** The repo is Python + FastAPI + Pydantic; Pydantic AI is built by the Pydantic team and is described as bringing "the same type-safety ... found in FastAPI" ([ZenML](https://www.zenml.io/blog/pydantic-ai-vs-langgraph)). No `langchain-core` dependency, no graph ceremony.
3. **Observability without lock-in.** 100% OpenTelemetry GenAI semantics means the existing stack (or Logfire, or Langfuse) works, and there is no LangSmith-style proprietary trace format ([Pydantic docs](https://pydantic.dev/docs/logfire/get-started/comparisons/langsmith)).
4. **It is production-validated.** ThoughtWorks moved it to a stable, adoptable position; independent comparisons place it among the frameworks production teams actually ship ([ThoughtWorks](https://www.thoughtworks.com/en-us/radar/languages-and-frameworks/pydantic-ai), [Alice Labs](https://alicelabs.ai/en/insights/open-source-ai-agent-frameworks-comparison-2026)).
5. **Incremental adoption is trivial.** A single `SarvamLLM` wrapper becomes a Pydantic AI model + a typed agent per capability, without touching the Academic Brain (`retrieval/`, `graph/`, `algorithms/`, `assessment/`) — consistent with `provider-architecture.md`'s "providers are tools, not the brain."

**Keep the existing `agents/orchestrator.py` + `agents/base.py` Tool ABC as the control plane.** It is deterministic, already tested, and orchestrating typed tool calls is not a problem an agent framework solves better. Pydantic AI agents are themselves callable tools, so they slot in underneath the existing orchestrator.

**When to reconsider LangGraph:** the moment a workflow needs **durable, resumable, multi-step state with an approval interrupt that survives a process restart** — e.g., a paper-generation run that pauses for principal approval, resumes days later, and must not lose partial work. LangGraph's checkpointers + `interrupt()` are purpose-built for that ([Alice Labs](https://alicelabs.ai/en/insights/langgraph-vs-crewai-2026)). Pydantic AI's `pydantic-graph` can do typed state machines but its durable-execution story is less battle-tested. **Trigger, not default.**

**Do not adopt CrewAI** for anything on the critical grading or curriculum path — non-deterministic execution and no native persistence are direct contradictions of this codebase's invariants. **Do not start AutoGen** — maintenance mode. **Use DSPy offline**, if at all, to compile/optimize the prompts for the few LLM tasks once labelled data exists; Shopify reportedly cut cost ~75x and doubled reliability by moving to a smaller model plus GEPA ([DSPy](https://dspy.ai/getting-started/gepa-optimization)). That is a *training-time* tool, not a runtime framework.

### 5.3 When NOT to use an agent framework at all

- **For the deterministic capabilities.** An agent framework cannot help a largest-remainder allocation or an FSRS scheduler, and wrapping them in an agent adds latency and non-determinism for zero benefit.
- **For a single LLM call with one schema.** If the job is "text in, typed object out," a plain typed function is easier to test and debug. "Skip all of them if you have one agent making one or two tool calls: a plain function-calling loop is easier to debug" ([promptquorum](https://www.promptquorum.com/local-llms/best-ai-agent-framework-2026)).
- **When the "agent" would be a router over deterministic tools.** A teacher-facing NL interface should be a typed intent classifier + deterministic dispatch, not an autonomous loop. Frameworks add 100-500 ms of Python overhead per agent step ([MLM](https://machinelearningmastery.com/llm-orchestration-frameworks-compared-langchain-vs-llamaindex-vs-raw-api-calls)); on a synchronous teacher action that is pure waste.

---

## 6. Document generation

The repo already chose **ReportLab** for the CBSE question paper renderer — `assessment/pdf.py` states the reason explicitly: "no native GTK dependency, and the layout is deterministic across machines." That decision is correct and should be extended, not revisited.

### 6.1 Engine comparison

| Engine | Fidelity for Indian exam formatting | Determinism | Speed | Testability (golden-file) | Best for |
|---|---|---|---|---|---|
| **ReportLab (Platypus)** | Excellent for *programmatic* layout: gutters for question numbers, right-aligned marks, section banners, tables, the roll-no grid. Math must be composed (images/`matplotlib`/`MathML`) since open-source ReportLab has no LaTeX engine | **High** — pure Python, no browser/GTK, byte-stable across machines (repo's stated reason) | Very fast; much faster than HTML pipelines on repeated content ([pdf4.dev](https://pdf4.dev/blog/reportlab-vs-weasyprint)) | **Ideal** — deterministic text layer, easy to extract and diff | **Question papers, marking schemes, coverage/progress reports** — anything with structured, repeating, exam-style layout |
| **WeasyPrint (HTML+CSS)** | Good for CSS-styled documents; **known fidelity gaps**: the Lambda benchmark found it "dropped ... zoom, fit-content, margin-inline: auto, rendering is visibly broken"; poor flexbox and custom-font support ([gist](https://gist.github.com/LordHarsh/d17767932e9317f3c6d26e8b28262074), [HN](https://news.ycombinator.com/item?id=39028644)). Produces 50-80% smaller PDFs | High *if* versions and fonts are pinned; pure Python engine, no JS | Slower than Chromium on complex docs; degrades with document size ([verityengine benchmark](https://github.com/verityengine/pdf-engine-benchmarks)) | Good — text layer is extractable | **HTML-template reports** where the template is simple and the team wants CSS rather than flowable code |
| **Playwright + Chromium (HTML->PDF)** | **Highest CSS fidelity** — it is the browser. Handles JS, modern CSS, charts. The reference for "looks like the web preview" | **Not guaranteed bit-deterministic.** Playwright maintainers state Chromium rendering "is not guaranteed to be deterministic"; different hardware/OS/fonts produce different pixels ([Playwright issue #23654](https://github.com/microsoft/playwright/issues/23654)). Reproducible only with pinned browser version + fonts + environment | Warm Playwright renders a simple doc in ~3 ms vs WeasyPrint ~227 ms (75x); complex 13 ms vs 629 ms (48x) ([pdf4.dev](https://pdf4.dev/blog/playwright-vs-weasyprint)); ~200 ms for a 40-page PDF with headless Chromium ([GrumpTech](https://github.com/GrumpTech/pdf-benchmarks/blob/main/README.md)) | Hardest — pixel diffs are non-deterministic; use *rasterized* goldens with a tolerance, or extract-and-diff text only | **Only** where pixel fidelity to a web preview is a product requirement, with strict version pinning |
| **LaTeX (TeX Live / `exam.cls`)** | **Best-in-class for math-heavy exam typography.** `exam.cls` is purpose-built for exam papers: `\question`, graded tables, points, answer-space ([Overleaf](https://www.overleaf.com/learn/latex/Typesetting_exams_in_LaTeX)). Indian board papers (maths/physics) are dominated by equations | Compile is deterministic for fixed TeX version + packages, but TeX is a huge moving dependency and "deals with syntax and other errors very poorly" ([John D. Cook](https://www.johndcook.com/blog/2010/05/12/complexity-of-html-and-latex)) | Slower (discrete compile); deployment heavy (GB-scale toolchain) | Good text layer, but brittleness makes CI painful | **Only if** equation fidelity becomes the dominant constraint. Adds an entire toolchain to ship and secure |
| **DOCX templating (`docxtpl`)** | Faithful to Word conventions; teachers can edit | **Low for archival** — DOCX reflows differ across Word/LibreOffice versions and platforms | Fast | Hard (binary, reflowing) | **Teacher-editable drafts only** — never the archival/graded artifact |

### 6.2 Recommendation per document class

| Document | Engine | Why |
|---|---|---|
| CBSE question paper | **ReportLab** (keep) | Deterministic, exam-format-native (repo already implements the header band, roll-no grid, section banners, marks gutter, MCQ (A)-(D) layout), fast, golden-file testable. For equations, embed rendered math (matplotlib/SVG) rather than adding a TeX toolchain |
| Marking scheme | **ReportLab** | Structured value-points table; same pipeline as question paper |
| Coverage report | **ReportLab** for the canonical artifact; **WeasyPrint** for the HTML-templated version if the frontend already renders the same view | Deterministic canonical output; the HTML path is a convenience, not the source of truth |
| Progress report | **ReportLab** canonical; optional **WeasyPrint**/Chromium for a web share link | Same logic. If the frontend must be pixel-identical, generate the PDF from the *same* HTML with Chromium, accept the determinism cost, and pin versions |

**Golden-file testing recipe (works today with ReportLab):**
1. Fix the timestamp/random seed in templates.
2. Generate to bytes; assert `sha256` is stable for identical inputs (this is the real determinism test).
3. Extract the text layer and diff against a committed `.txt` golden — this catches *content* regressions without brittle pixel comparison.
4. For pixel-level checks (only if needed), rasterize and compare with a perceptual tolerance; never require byte identity from Chromium.
5. Commit one golden per document template per marking scheme version, and store the generator version alongside it ([snapshot/golden practice](https://cran.r-project.org/web/packages/testthat/vignettes/snapshotting.html), [ByteLedger](https://byteledger.vizleo.com/blog/golden-file-testing-2026)).

---

## 7. Reference architecture (target state)

```
                       ACADEMIC BRAIN (deterministic, offline, tested)
   working-days | weightage | scheduling | blueprint | parallel sets | FSRS
   BM25/TF-IDF  | chapter tagging (frozen embeddings) | lexical subtopic match
   rubric scoring | reportlab document generation | provenance store
                                        ^
                                        | typed tool calls only
              +-------------------------+-------------------------+
              |        ORCHESTRATOR (plain Python, deterministic)  |
              |  agents/base.py Tool ABC + agents/orchestrator.py  |
              +-------------------------+-------------------------+
                                        |
              +-------------------------v-------------------------+
              |            PYDANTIC AI  (LLM call layer)           |
              |  typed response_model | validation | retry | fail  |
              +-------------------------+-------------------------+
                                        |
        +-----------------+-------------+-------------+-----------------+
        |                 |                           |                 |
  [pre-call PII]   [prompt cache key]          [model+prompt ver]  [per-tenant budget]
   Presidio redact   (tenant, q, scheme,         written to row      hard stop -> fallback
   -> restore          model, prompt_hash)
                                        |
                       +----------------v----------------+
                       |  provider: Sarvam 105B / local  |
                       |  SARVAM_API_KEY or self-host    |
                       +----------------+----------------+
                                        |
                       +----------------v----------------+
                       |  post-call deterministic gate   |
                       |  validator -> commit  OR        |
                       |  reject  -> deterministic path  |
                       +----------------+----------------+
                                        |
                       +----------------v----------------+
                       |  HUMAN APPROVAL (principal /    |
                       |  teacher) where student-facing  |
                       +--------------------------------+
```

---

## 8. Migration plan (incremental, low-risk)

1. **Wrap the existing `SarvamLLM` behind a Pydantic AI model** with typed `response_model` per capability. No behaviour change; only the output contract tightens.
2. **Add the model/prompt-version + cache-key columns** to every table written by an LLM path and to the grading/audit records. Backfill nothing; enforce going forward.
3. **Move `llm_evaluate.py` from "returns an `Evaluation`" to "returns a *proposal* + `engine` discriminator"**, requiring the teacher gate for commit. (The swipe-review UI likely already implies this — make it explicit in the type.)
4. **Add the pre-call PII redactor** on the mobile scan -> LLM path; log redaction counts; wire to `assessment/consent.py` and the DPA.
5. **Add per-tenant token budgets + cost attribution.** Degrade to the deterministic engine on exhaustion.
6. **Add deterministic validators** per [4.3](#43-deterministic-validators-around-every-llm-output), and a refusal path for each.
7. **Only after ~300-500 human-approved examples exist**, evaluate a fine-tuned small model (PEFT on Sarvam-1 / Sarvam 30B or a small encoder) for extraction and marking-point detection, against the LLM baseline, on the repo's own eval harness (`docs/evaluation-plan.md`).
8. **Reconsider LangGraph only if** a durable multi-day approval workflow appears.

---

## 9. Verification and confidence

**Verified via web search (high confidence):**
- AES/ASAG QWK and human-agreement ranges; fine-tuned vs LLM scoring agreement.
- Constrained-decoding schema-vs-semantic gap; latency overhead; prompt-schema-in-prompt result.
- Non-determinism at temperature 0; LLM-as-judge position/self-preference/style biases.
- Prompt-injection vulnerability of LLM-based grading; Wharton ~40k-trial result; OWASP LLM01.
- DPDP Act 2023 child-data provisions, Rule 12 exemption, ₹200 crore penalty, Rules notified 14 Nov 2025 with 18-month clock.
- Token pricing table (2026), caching/batch discounts; fine-tuned-encoder vs LLM cost per 1M requests.
- BEIR/BM25/hybrid retrieval results.
- PDF-engine fidelity/determinism/speed comparisons; Playwright determinism caveat.
- Agent-framework maturity, AutoGen maintenance mode, Pydantic AI 1.0 + ThoughtWorks position, framework overhead figures.
- Sarvam model line (Sarvam-1 2B, 30B/105B open-weight, token fertility, inference speed).

**Repo-grounded (high confidence):** existing deterministic components; existing LLM call sites (`llm/sarvam.py`, `assessment/llm_evaluate.py`, `curriculum/extraction.py`, `agents/critic.py`, `qmap.py`, `extract/openie.py`); ReportLab choice and stated rationale in `assessment/pdf.py`; human-approval staging in `AGENTS.md`; consent/DPA docs.

**Arithmetic, not benchmark (medium confidence):** the per-school cost estimate in [1.6](#16-cost-at-scale-concretely). It depends on the answer/token-length assumptions stated; treat as an order-of-magnitude, rerun with real pilot telemetry.

**Could not verify — flag before relying on it:**
- The *actual* comparable cost of running **Sarvam 30B/105B self-hosted** vs the Sarvam API for a pilot-scale workload. This determines whether "process minor data fully on-premises" is affordable; it needs a GPU-cost spike, not an assumption.
- Sarvam's **published uptime, retry semantics, and any structured-output / JSON-schema-constrained mode** on `/v1/chat/completions`. The observed 50-75% truncation problem is consistent with a reasoning model and a token cap, not necessarily a platform defect — but whether the API *supports* schema-constrained decoding (and what its context/rate limits are) is unverified and materially affects the Pydantic AI design.
- **Prompt-cache support on Sarvam's API.** The cost model in [1.6](#16-cost-at-scale-concretely) assumes a cache mechanism; if Sarvam does not support prompt caching, cache only at the application layer and re-run the estimate.
- Whether **DPDP Rule 12** covers AcademicOS's specific posture. AcademicOS is a private EdTech system *used by* schools, not necessarily itself an "educational institution." This distinction changes whether verifiable parental consent is required. **This is a legal question — get counsel, do not infer it.**
- The exact current **CBSE blueprint** percentages by subject/class. The sources found (e.g., competency-based ~50%, objective ~20%) vary by year and subject ([PW](https://www.pw.live/school-prep/exams/cbse-class-10-syllabus), [Vidya Mandir](https://vidyamandir.com/studyhub/cbse-class-10-exam-pattern)). The repo's blueprint engine should be driven by the *official CBSE circular PDF* (cbseacademic.nic.in), not by secondary summaries.

---

## 10. One-paragraph answer

Keep the deterministic core exactly as it is — it is the product's moat and its audit story. Use LLMs at precisely four seams (curriculum extraction, doubt solving, subjective answer evaluation, question drafting), each behind a **typed output contract (Pydantic AI), a deterministic validator, a cached/idempotent artifact, recorded model+prompt provenance, a PII redactor, a per-tenant budget, and a named deterministic fallback**. Make the human-approval gate permanent for anything student-facing, because LLM/human grading agreement is provably below human/human agreement. Build the agent layer on **Pydantic AI with the existing plain-Python orchestrator retained** — and revisit LangGraph only when durable, resumable, multi-day approval workflows actually exist. Keep **ReportLab** for question papers and marking schemes (deterministic, golden-file testable, exam-format-native); add WeasyPrint only for HTML-template reports. Fine-tune a small Indic model only after a few hundred human-approved examples exist to train on.
