# NCERT Corpus — Download & Ingest Report (Phase 1, Roadmap)

**Date:** 2026-08-01 · **Corpus root:** `C:\Users\varsh\OneDrive\Documents\Sarvam\ncert-dataset`

## 1. Goal

Add the NCERT textbook layer (Phase 1 of `docs/roadmap.md`) to AcademicOS: official NCERT
textbooks for Mathematics, Science, and English, Classes 6–8 — a focused 9-book starter set,
ingested through the standard pipeline (`ingest → parse → extract`).

## 2. What was downloaded

All files were sourced from the official NCERT portal (`ncert.nic.in`). NCERT publishes each
book as a ZIP of chapter PDFs (`{code}{vol}dd.zip`); each ZIP was extracted and its chapter
PDFs merged (pypdf, page order: prelims first, then chapters) into one PDF per book. Class 7
Mathematics ships as two volumes (`gegp1`/`gegp2`); the two were merged into one book PDF.

| Class | Subject | Book (edition) | Chapters (PDFs merged) | Pages | Final PDF | Size |
|-------|---------|----------------|------------------------|-------|-----------|------|
| 6 | Maths | Ganita Prakash (First Ed. Aug 2024, Reprint 2026-27) | 11 (`fegp1dd.zip` → fegp1ps, fegp101–110) | 412 | `textbooks/maths/class6_ganita_prakash.pdf` | 26.4 MB |
| 7 | Maths | Ganita Prakash Part I + II (Apr 2025, Reprint 2026-27) | 17 (`gegp1dd.zip` → gegp1ps, gegp101–108; `gegp2dd.zip` → gegp2ps, gegp201–207) | 547 | `textbooks/maths/class7_ganita_prakash.pdf` | 44.3 MB |
| 8 | Maths | Ganita Prakash (2025-26) | 8 (`hegp1dd.zip` → hegp1ps, hegp101–107) | 263 | `textbooks/maths/class8_ganita_prakash.pdf` | 27.1 MB |
| 6 | Science | Curiosity (First Ed. Jul 2024, Reprint 2026-27) | 13 (`fecu1dd.zip` → fecu1ps, fecu101–112) | 272 | `textbooks/science/class6_curiosity.pdf` | 92.2 MB |
| 7 | Science | Curiosity (2025-26, Reprint 2026-27) | 13 (`gecu1dd.zip` → gecu1ps, gecu101–112) | 208 | `textbooks/science/class7_curiosity.pdf` | 51.1 MB |
| 8 | Science | Curiosity (2025-26) | 14 (`hecu1dd.zip` → hecu1ps, hecu101–113) | 248 | `textbooks/science/class8_curiosity.pdf` | 51.9 MB |
| 6 | English | Poorvi (First Ed. Jun 2024, Reprint 2026-27) | 6 (`fepr1dd.zip` → fepr1ps, fepr101–105) | 180 | `textbooks/english/class6_poorvi.pdf` | 54.9 MB |
| 7 | English | Poorvi (First Ed. Mar 2025, Reprint 2026-27) | 6 (`gepr1dd.zip` → gepr1ps, gepr101–105) | 240 | `textbooks/english/class7_poorvi.pdf` | 92.3 MB |
| 8 | English | Poorvi (2025-26) | 6 (`hepr1dd.zip` → hepr1ps, hepr101–105) | 268 | `textbooks/english/class8_poorvi.pdf` | 60.3 MB |

**Totals:** 9 book PDFs, 1,987 pages, ~460 MB on disk. Peak download footprint (ZIPs +
extracted chapters + merged finals) ≈ 852 MB — well under the 1.5 GB budget; C: free space
never dropped below 5.9 GB (stop threshold 2 GB). Book identities were verified from the
printed title pages (title/grade/edition) before ingest.

## 3. What was skipped / failed (and why)

- **Nothing failed at download time.** All 9 target books were available on `ncert.nic.in`
  with valid, non-HTML PDF content (`%PDF` magic verified on every extracted chapter).
- **Skipped by design:** NCERT "prelims-only" PDFs (`{code}1ps.pdf`) — these exist on the
  official site but contain only the front matter (title page, foreword, committees; 14–20
  pages). They were used to verify book identity, then discarded. The full book is the
  `dd` ZIP.
- **Dead-link safety net was exercised on probes only:** ~15 candidate URLs were HEAD-checked
  before downloading; 2 patterns returned 000/empty (e.g., a guess at a full-book `.pdf` URL
  that does not exist) and were abandoned after 1 attempt.
- **No classes/subjects were missing** for the 6–8 target set; no retries beyond the 2-attempt
  cap were needed.

## 4. Pipeline results

Run with `ACOS_CORPUS_ROOT=C:\Users\varsh\OneDrive\Documents\Sarvam\ncert-dataset`
(`config/config.toml` left untouched — env override only).

| Stage | Result |
|-------|--------|
| `ingest` | `accepted=9 rejected=0 duplicates=0` (9/9 registered) |
| `parse` | 9/9 parsed, quality **0.9**, winner provider **pdf_native** (all pages text-classified) |
| `extract` | 9/9 extracted into the index — **3,101 chunks** cumulative (index counter) |

`stats` output (final):

```
registered: 52   (43 existing CBSE + 9 NCERT)
by_type:    unknown 26, bye_law 14, notification 7, circular 3, question_paper 1, marking_scheme 1
chunks:     3101
graph_nodes 437 / graph_edges 438   (unchanged — build-graph not re-run in this task)
data_root:  ...\AcademicOS\academicos-data
corpus_root: ...\Sarvam\ncert-dataset
```

Registry rows for the NCERT layer (all `extracted`, quality 0.9):

```
src:cfd02e1c3628ca61d969c6a6 class6_ganita_prakash  src:40727e036384b2b238ff480f class6_curiosity
src:2ff44ea14cdcc39f5814794d class7_ganita_prakash  src:9f1391297088e4e6eab11f7e class7_curiosity
src:32612927f9b61b057de4d1d4 class8_ganita_prakash  src:d173a5ed6cdad473353a2e40 class8_curiosity
src:c9b120f84e2e57b31030fa86 class6_poorvi          src:738b0e2504e3925d53d56c3b class7_poorvi
src:aecad3ccc7f698dc03da7c20 class8_poorvi
```

## 5. Issues found

1. **Full-book "PDF" URLs are a trap.** `https://ncert.nic.in/textbook/pdf/{code}1ps.pdf`
   looks like the complete book but is **prelims only** (14–20 pages, 2.6–4.3 MB). The real
   full book ships as `{code}{vol}dd.zip` (chapter PDFs). Pipeline-safe approach used here:
   download ZIP → extract → verify each chapter (`%PDF`, > 2 KB) → merge into one PDF/book.
2. **doc_type classification:** NCERT textbooks land in `unknown` — the classifier only knows
   the CBSE artefact types (`question_paper`, `circular`, `bye_law`, `notification`,
   `marking_scheme`). A `textbook` type (subject/grade metadata already exists in the schema)
   would be the natural follow-up; no source changes were made per task constraints.
3. **Parse is slow on large books (~2.2–2.7 s/page, not a hang):** the ensemble always runs
   `unlimited_ocr` after `pdf_native`, rendering every page at 200 DPI and POSTing to the VLM
   service at `127.0.0.1:8910`. With no VLM (weights unavailable — disk-constrained), each
   page still pays the render cost + a Windows ~2 s connect-refusal delay. `pdf_native`
   itself costs ~1.5–1.8 s/page on these 200–550-page books. Mitigation used (no source
   changes): a throwaway local listener on 8910 that closes connections instantly, so the
   VLM call fails in ~0.01 s instead of 2 s — semantics identical to "VLM unavailable".
   First full run looked hung only because the CLI prints progress once at the end; each book
   was instead parsed individually with `parse --doc-id …` (6–22 min each).
4. **Pre-existing artifact, unrelated to this task:** `src:36d45506fad5d948fbd1d403.doc`
   (a legacy Word file in the CBSE corpus) still fails to parse ("no parser produced output")
   — not touched per task rules.
5. **Worked without issue:** all NCERT PDFs are machine-generated (typeset) text — `pdf_native`
   extracted clean text (e.g., 186,770 chars for `class6_poorvi`); no OCR was needed.

## 6. Next steps (suggested)

- Extend the classifier with a `textbook` type so future NCERT ingests carry subject/grade.
- Add NCERT Exemplar + Grades 9–12 (same `dd.zip` pattern) when disk allows.
- Re-run `build-graph` + `openie` to densify the graph with the NCERT layer.

## 7. Update 2026-09-13 — Grade 9 added, Grade 6-8 actually wired in

This whole report describes a run made with `ACOS_CORPUS_ROOT` as a one-off env
override — **`config/config.toml`'s `corpus_root` itself was never changed**,
which meant every ingest run since (including the one that produced the 6,971-node
graph `docs/roadmap.md` cites from 2026-09-11) only ever scanned `cbse-dataset`.
The 9 Grade 6-8 books above sat on disk, fully downloaded and even previously
`extracted` once under that old env-override run, but **absent from the live
registry** — confirmed directly (`SELECT ... WHERE file_key LIKE '%poorvi%'`
returned 0 rows) before this session's fix.

**What changed this session:**
- Downloaded all 5 real Class 9 NCERT textbooks from `ncert.nic.in`, same
  ZIP→extract→merge method as section 2 above: English (Kaveri), Hindi (Ganga,
  new subject for this corpus), Mathematics (Ganita Manjari), Science
  (Exploration), Social Science (*Understanding Society: India and Beyond*,
  **Part I only** — NCERT has not published Part II as of this date; do not
  treat its absence as a download failure).
- Re-ingested via the same `ACOS_CORPUS_ROOT` scoped-override technique (still
  a one-off, `config.toml` still untouched by design — see below for why that's
  safe) — matched all 14 books (9 old + 5 new) to existing registry rows by
  **sha256 content hash**, since the 9 old ones already existed as
  unclassified `unknown/src_<hash>.pdf` rows from a prior run, not fresh
  inserts.
- Fixed the doc_type gap this report's section 5.2 already predicted: used
  the existing `reference_material` enum value (not a new `textbook` type —
  none was added to `models/enums.py::DocType` this session, so the "extend
  the classifier" suggestion above is still open) plus direct subject/grade/
  title metadata patches, since NCERT filenames don't match the CBSE-specific
  classifier patterns `ingest/discovery.py` looks for.
- Ran `parse`/`extract`/`build-graph` for real on all 14 (scoped via
  `--doc-id`, not a full corpus reparse) — verified live via `cli search`,
  not just exit codes.

**Why the env-override approach is safe to repeat, not a workaround to fix
later:** `ingest/pipeline.py` copies file bytes into `cfg.documents_dir`
(`store.put`) at ingest time — every downstream stage (`parse`/`extract`/
`build-graph`/`index`) reads from that internal copy via the registry's
`file_key`, never from `corpus_root` again. So a scoped `ACOS_CORPUS_ROOT`
ingest run has zero lasting effect on `config.toml` or on any other corpus's
processing — confirmed by grepping every module besides `ingest/pipeline.py`
and `cli.py`'s `cmd_ingest` for `corpus_root`; nothing else references it.

**Current registry state for the NCERT layer** (`cli stats`, 2026-09-13):
14 `reference_material` sources, all `status=extracted`. Grade 9 sources:

```
src:54402fcb4f3bb4922245f297  English  / Kaveri            (Class 9)
src:ee5a100eb7f07710bafcdd75  Hindi    / Ganga             (Class 9)
src:f2a4e5061d166a618328b17e  Mathematics / Ganita Manjari (Class 9)
src:cf6e431418feee5abbfd15d6  Science  / Exploration       (Class 9)
src:497573259f1e493bf965aa78  Social Science / Understanding Society Part I (Class 9)
```

**Still open**, none attempted this round: extending the classifier with a
real `textbook` `DocType` (section 5.2's suggestion, still valid); NCERT
Exemplar; Grades 10-12 NCERT textbooks; re-running `openie` over the new
Grade 9 layer; a real Topic/Subtopic LLM-decomposition pass over these books
the way `curriculum/extraction.py` already did for the 46 Grade 10 chapters
(`TRANSCRIPT_REQUIREMENTS_MATRIX.md`) — these 14 NCERT books have zero
Topic/Subtopic content, only chapter-level chunks; sourcing an official CBSE
Hindi curriculum so `syllabus/cbse_syllabus.py` can cover Hindi (currently
Mathematics/Science/Social Science/English only, Class X only).
