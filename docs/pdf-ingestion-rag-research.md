# PDF Ingestion & Per-Chapter RAG — Research Findings

Date: 2026-10-01
Status: research complete for parser + retrieval; architecture gated on rights decision.

---

## 1. Sources reviewed

### 1.1 NCERT official download page (ncert.nic.in/textbook.php)

Authoritative source for book/chapter inventory, and the **governing terms of use**.
Also exposes the canonical URL scheme `textbook.php?<bookcode><n>=<first>-<last>`, e.g.
`?jhks1=12-17` = Kshitij-2 class 12, chapters 12–17. Each book page links
`Rationalised Content`, `Prelims`, `Guide for using QR Code`, per-chapter PDFs, and
`Download complete book`. Classes I–XII, Hindi / English / Urdu.

**Terms of use (verbatim excerpts, material to this project):**

- "the NCERT textbooks are copyrighted."
- "republication of NCERT textbooks by any other individual or agency is strictly prohibited."
- "No agency or individual may make electronic or print copies of these books and
  redistribute them in any form whatsoever. **Use of these online books as a part of
  digital content packages or software is also strictly prohibited. No website or online
  service is permitted to host these online textbooks.**"
- "Links may however be provided with written permission from the NCERT."
- "the online textbooks carry a watermark on all pages declaring the copyright of NCERT."
- "Please bring to our notice any infringement or violation of copyright and commercial
  exploitation of these textbooks."

Consequence: storing extracted chapter text in a hosted R2 bucket and returning
passages from a served RAG is, on the plain reading, both "hosting these online
textbooks" and "use as a part of ... software". See §5.

### 1.2 github.com/praj2408/RAG-Enhanced-NCERT-Tutor

Student project, 3 commits, 5 stars, MIT. Stack: pdfplumber → `RecursiveCharacterTextSplitter(1800, 200)` →
nomic-embed-text (Ollama) → ChromaDB → Groq `llama-3.1-70b-versatile` → FastAPI + Streamlit.
Corpus: Class 12 Physics Part 1/2 (+ Hornbill English, Science book). Per-**book** vector DBs
(`vector_db`, `vector_db_eng_hornbill`, `vector_db_science_book`) — not per-chapter.

Useful:
- `vector_db_maker.py` stores `metadata = {source, page}` per chunk → page citation is
  demonstrably feasible; confirms we should keep page numbers at chunk level.
- `evaluation_script.py` computes a real metrics suite: precision@k, recall@k, MRR, nDCG,
  ROUGE-L, BLEU, BERTScore, exact match, F1, response_time. The *idea* is right; we adopt
  the discipline but not the implementation (see below).

Why not reuse:
- Retrieval relevance is judged by `SequenceMatcher(...).ratio() > 0.5` — character
  similarity against a reference answer, not semantic relevance. Unsound as a retrieval label.
- `compute_recall_at_k(relevant_at_k, len(relevant_documents))` divides by the number of
  documents *retrieved*, not the number relevant → the "recall" is not recall.
- `compute_mrr` does `next((i for i,r in enumerate(hits,1))) + 1`, so a hit at position 1
  reports MRR 0.5 instead of 1.0. Off-by-one.
- Disables TLS verification: `ssl._create_unverified_context`, `verify_mode = ssl.CERT_NONE`.
- `requirements.txt` omits every package its own eval script imports (rouge_score, evaluate,
  bert_score, nltk, pandas, torch, numpy, langchain retriever deps).
- "Reranking" is `ContextualCompressionRetriever` + `LLMChainExtractor` (an extra LLM call),
  not a cross-encoder. No hybrid retrieval, no page citations in answers, no Hindi, no
  question generation, no question validation.

### 1.3 prezi.com/p/1onhfjm377ed (CSE315 project, Dhruvi Mahale et al.)

Corpus: Class 11–12 Science / Maths / Social Science. FAISS vs ChromaDB (IndexFlatL2, IVF,
HNSW, PQ; cosine / dot / L1 / L2). Chose Mistral 7B for commercial-friendly licence.
Compared 5 embedding models (all-MiniLM-L6-v2, all-mpnet-base-v2, intfloat/e5-large-v2,
msmarco-distilbert-base-v4, BAAI/bge-large-en) on accuracy + inference time; chose
all-mpnet-base-v2 (768-d).

Useful:
- Chunking ~10 sentences with 2-sentence overlap; reports before/after chunking quality delta.
- Batch 32–64 sentences per embedding call for throughput. We should batch too.
- Header/footer stripping is a real requirement (NCERT running feet carry class/book/chapter).
- Reports the genuine problem: "non-searchable PDFs and inconsistent formatting".

Anti-pattern to avoid — explicitly:
- Their preprocessing step "**Eliminating Non-ASCII Characters**". NCERT Hindi is Devanagari
  (U+0900–U+097F). Stripping non-ASCII silently deletes all Hindi text. Normalise, never delete.
- Extraction is the naive `page.get_text("text")` per page, concatenated — same as ours today.

---

## 2. Corpus reality check (measured, not assumed)

`scripts/pdf_ingest/probe_textlayer.py` on the first 80 chapter PDFs:

| kind | count | chars/page | text coverage |
|---|---|---|---|
| digital | 80 | 518.3 | 0.974 |

So the corpus has a **real digital text layer**. Large file sizes (3.9–24.5 MB for single
grade-1 chapters) are high-resolution embedded *illustrations*, not scans. OCR is therefore a
targeted fallback for a minority of books, not the main ingestion path. This contradicts the
"non-searchable PDFs" premise in both reference projects and is the single most important
finding for cost and architecture: we do **not** need to OCR 629 PDFs.

Full-corpus probe over all chapter + full-book PDFs is still to be run to identify the exact
minority that needs OCR.

---

## 3. Parser benchmark (2026 evidence)

### 3.0 Chosen parser: custom PyMuPDF font heuristic

`scripts/pdf_ingest/ncert_extract.py`, used by both `extract_corpus.py` and
`benchmark_parsers.py`. Measured over 572 chapters / 9,610 pages: ~637 s total,
0.069 s/page, no OCR.

| metric (80-row scored sample) | value |
|---|---|
| anchor_exact | 0.806 |
| anchor_ng5 | 0.931 |
| head_rec | 0.771 |
| dup_rate | 0.064 |
| by language (en) | exact 0.985 / ng5 0.996 / head_rec 0.871 |
| by language (hi) | exact 0.234 / ng5 0.720 / head_rec 0.431 |

Hindi numbers are floor-limited by transcription noise in the anchor file
(`मेें` vs `में`), not only by the parser — hence `ng5` as the tracked metric.

Design decisions that were each forced by a measured defect, not by taste:

- **Char-weighted font size.** One 40pt page number must not define the profile.
- **Body size = char-weighted mode of sizes carrying >=3% of characters.** Scale-free,
  so it works for 9pt and 14pt body text without a per-book threshold table.
- **Heading levels assigned only after furniture removal.** Otherwise a page number
  claims level 1 and the real title is demoted to `##`.
- **Candidate heading sizes must carry real text** (`>=8` chars and `>=0.2%` of the
  chapter). Isolated glyphs (`'B'`, `'F'`, `'?'`) render at 30–125pt and were taking
  3 of the 4 level slots, leaving genuine 20pt/14pt section heads unranked. This one
  fix took `aemr1-ch01` from 1 detected heading to 20.
- **`normalize_lines()`: geometry repair before structure.** NCERT PDFs re-draw the
  same sidebar label 5× at overlapping coordinates, and emit justified headings as
  fragments on one baseline. De-duplicating by position and rejoining fragments fixed
  `Activity 1.1 Activity 1.1 Activity 1.1 Activity 1.1 Activity 1.1` and the
  cross-page over-merge `Chapter 1 Two Little Hands Let us sing`.
- **Merge only when stacked, same column, same page.** A wrapped heading has no
  reliable lexical signal that its first line is incomplete, so page/column geometry
  is the only trustworthy cut.
- **Second pass for same-size bold books.** `jesc1`/`jess1` expose no size step at
  all, so when the primary pass finds zero headings, short bold lines are promoted —
  as a *re-render in document order*, never an append (an append put every heading in
  a pile at the end of the chapter).
- **`is_corrupt_heading()` rejects broken assemblies** (repeated words). A heading
  made of overlapping re-draws is worse than no heading: it becomes a false chunk
  boundary and a junk retrieval key.

### 3.0.1 Legacy 8-bit Indic fonts

38 chapters are set in Type1 legacy Devanagari fonts with `/WinAnsiEncoding` and
**no `/ToUnicode` CMap**, so MuPDF returns ASCII standing in for Devanagari.
Detection is by observed font + observed script, not by language name, so it
generalises: the run found five families beyond the four originally suspected —
`Walkman-Chanakya905`, `KrutiDev010`, `Chanakya`, `ChanakyaThin`, `Mangal`.

`lipi-aparsoft` 1.0.9 supplies the ASCII→Unicode tables. Its **full pipeline
(`lipi.extractor.extract_unicode_text`) returns empty text on these PDFs**, so only
the character-level mapping is usable.

Result: **Hindi chapters with zero Devanagari went 32 → 0.**

Honest limitation, flagged in every affected file's front matter
(`text_quality: decoded-legacy-font`, `quote_exact: false`): the mapping is
character-level and context-free, so the pre-base i-matra lands on the wrong side
(`ितलक` for `तिलक`, `िपता` for `पिता`) and word-level errors remain
(`दूद् पीने` for `दूध पीने`). Fixing this needs real Devanagari shaping, not a lookup
table. Usable for retrieval and topic extraction; **not quote-exact**. 9 of the 38
also yield no heading hierarchy because the legacy fonts carry no size contrast.
OCR is the escalation path if quote fidelity is ever required.

### 3.0.2 Known residual defects

- Decorative sidebar labels in `jesc1`/`jess1` remain split in the *body* text
  (`1.1 CHEMICAL EQUAAL EQUATIONSTIONS`); they are partial re-draws at differing
  offsets and are not reliably repairable by heuristics. They are now excluded from
  the heading tree.
- 3 native chapters have no detectable heading size step: `jeff1-ch02/ch06/ch07`.
- No Telugu exists in the corpus (0 codepoints across all 572 files), so Telugu
  decoding is implemented-but-unexercised.

OpenDataLoader PDF→Markdown benchmark, overall score:

| engine | overall | reading order | table | heading | s/page | licence |
|---|---|---|---|---|---|---|
| opendataloader [hybrid] | 0.907 | 0.934 | 0.928 | 0.821 | 0.463 | Apache-2.0 |
| nutrient | 0.885 | 0.925 | 0.708 | 0.819 | 0.008 | Commercial |
| docling | 0.882 | 0.898 | 0.887 | 0.824 | 0.762 | MIT |
| marker | 0.861 | 0.890 | 0.808 | 0.796 | 53.932 | GPL-3.0 |
| unstructured [hi_res] | 0.841 | 0.904 | 0.588 | 0.749 | 3.008 | Apache-2.0 |
| edgeparse | 0.837 | 0.894 | 0.717 | 0.706 | 0.036 | Apache-2.0 |
| mineru | 0.831 | 0.857 | 0.873 | 0.743 | 5.962 | AGPL-3.0 → custom Apache-based |
| pymupdf4llm | 0.732 | 0.885 | 0.401 | **0.412** | 0.091 | AGPL-3.0 |
| unstructured | 0.686 | 0.882 | 0.000 | 0.388 | 0.077 | Apache-2.0 |
| markitdown | 0.589 | 0.844 | 0.273 | 0.000 | 0.114 | MIT |

Two things follow:

1. **`pymupdf4llm` heading preservation is 0.412** — near the bottom. Our current wrapped-heading
   bug ("Chemical Reactions" / "and Equations" on separate lines) is a direct, predicted
   consequence. We are not even using pymupdf4llm today (`pymupdf4llm` is not installed;
   raw `fitz` is in use), which is worse still — raw `get_text` does no heading detection at all.
2. Docling has **HybridChunker**: chunks on *structural nodes* rather than characters, preserving
   header hierarchy, tables and bounding boxes. That is the primitive we want for chapter RAG.

MinerU 3.1+ relicensed from AGPLv3 to a custom Apache-2.0-based licence, so it is now
commercially usable. Marker remains GPL-3.0 — a viral licence to avoid in a product.

## 4. Retrieval research — what to build, and what to skip

From *From BM25 to Corrective RAG* (arXiv 2604.01733), 7,318 text+table docs:

| method | Recall@5 |
|---|---|
| dense only (text-embedding-3-large) | 0.587 |
| BM25 only | 0.644 |
| Hybrid RRF | 0.695 |
| **Hybrid RRF + cross-encoder rerank** | **0.816** |

- Hybrid RRF + cross-encoder reranking beats hybrid alone by +17.4% Recall@5. **Build this.**
- BM25 ≥ dense on precise terminology. NCERT is full of exact terms, symbols, "Rationalised
  Content", class codes → lexical retrieval is unusually well suited.
- **Contextual Hybrid > vanilla Hybrid RRF.** Prepend a short LLM-generated document-context
  summary (50–100 tokens) per chunk. Adopt.
- **HyDE underperforms** vanilla dense (0.544 vs 0.587). Skip.
- **RAG-Fusion multi-query gives negligible gain** over BM25. Skip.
- **CRAG (adaptive query correction) underperforms plain hybrid fusion.** Skip.
- Anthropic-style weighted fusion, dense 1.0 : BM25 0.25.
- **Semantic chunking is not worth it.** NAACL 2025 findings: on real-world (non-synthetic)
  data, fixed-size chunking often *beat* semantic chunking; cost not justified. Skip.
- **GraphRAG underperformed plain RAG** on a well-produced corpus (82% vs 94.1%). Do not
  build a knowledge graph.
- **Hand-made Markdown beat every automated pipeline** in the Docling benchmark → our curated
  chapter boundaries and `transcriptions/textbook/*.json` ground truth are an asset, not a
  liability. Never discard them in favour of blind automated parsing.
- Late chunking helps but needs long-context embedding models; treat as a later option.

## 5. Cloudflare feasibility (this constrains the design)

Vectorize current limits:

| feature | Workers Paid | Workers Free |
|---|---|---|
| indexes per account | 50,000 | 100 |
| **namespaces per index** | 50,000 | **1,000** |
| vectors per index | 20,000,000 | same |
| dimensions | 1536 | same |
| metadata per vector | 10 KiB | same |
| max topK (with values/metadata) | 50 | same |
| upsert batch | 1,000 Workers / 5,000 HTTP | same |
| metadata indexes per index | 10 | same |
| indexed string per metadata index | first 64 bytes | same |

**Decisive constraint:** 572 chapters. Per-chapter *indexes* would need 572 indexes — infeasible
on the Free plan (100). Per-chapter *namespaces* need 572 — **fits even the Free plan (1,000)**.

→ **Architecture: one Vectorize index, one namespace per chapter.** A query names the chapter's
namespace, so retrieval is hard-partitioned to that chapter. This is per-chapter isolation
without per-chapter indexes, and it costs nothing to add chapters.

Available Workers AI models that make the §4 recipe executable on Cloudflare:
- `@cf/baai/bge-m3` — multilingual (100+ languages) embeddings, so Hindi and English share
  one index. Dense + sparse + multi-vector capable.
- `@cf/baai/bge-reranker-base` — cross-encoder reranker, exactly the +17.4% step.

Cloudflare Workers cannot run PyMuPDF/Docling. So parsing must happen **locally or in
CI**, and the Worker only does retrieval + generation. That fits the batch-worker pattern
already in place.

## 6. Open decision — rights (blocks §7)

NCERT's published terms prohibit using the books as part of software and prohibit any website
or online service hosting the textbooks. Archiving 629 chapter PDFs plus extracted text into R2
and serving retrieval passages sits inside that prohibition on the plain reading.

Options, in descending order of exposure:

A. **Written permission on file.** Keep the current architecture, record the permission
   reference in the source manifest. Only option that supports verbatim passage retrieval.
B. **Derived facts, no NCERT text served.** Store per-chapter *topic/section metadata and
   question anchors*, generate original questions, cite "Class 10 Science, Ch. 1 (NCERT)",
   link to ncert.nic.in, never return NCERT prose. Original questions are ours; NCERT is a
   citation, not redistributed content. Much lower exposure, still fully supports the product.
C. **Local-only corpus, no hosted copy.** Keep PDFs and extracted text on the machine; nothing
   in R2. Prevents hosting, but loses reproducible CI and shared access.

Recommended: **B**, with A pursued in parallel. B loses nothing the product actually needs —
question generation needs structure and grounding, not verbatim republication.

## 7. Proposed pipeline (pending §6)

Local/CI, not in the Worker:

1. Inventory all PDFs; record sha256, pages, class, subject, language, book code.
2. Extract with Docling (structural, HybridChunker) for headings/tables; fall back to
   pdfplumber for simple pages; fall back to OCR only for PDFs the probe flags as
   image-only. Normalise Unicode, **never strip non-ASCII**.
3. Strip running headers/footers by position, not by regex over the whole page.
4. Snap to the curated `transcriptions/textbook/*.json` chapter + topic boundaries. Reject
   boundaries that contradict the PDF rather than silently accepting them.
5. Emit per chapter: structured markdown + per-chunk `{text, page, section, char_range}`.
6. Batch-embed 32–64 chunks per call; namespace = chapter id.
7. Evaluate before shipping: heading recall, anchor recall (`startsWith` strings), page
   fidelity, against the transcription ground truth. No LLM judge.

Retrieval at query time: dense (`bge-m3`) + BM25, RRF weighted 1 : 0.25, top 50,
`bge-reranker-base`, top 5–8 passages, then generation.
