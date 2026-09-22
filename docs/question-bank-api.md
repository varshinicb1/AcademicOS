# The question bank as a standalone API asset

**Status:** architecture proposal, 2026-09-17, with an implementation update
below. Sections 1-5 are the design; section 7 records what now exists and
section 8 what does not.
Companion to [`api.md`](api.md) and [`gcp-deployment.md`](gcp-deployment.md).

> ## Implementation update — 2026-09-17, later the same day
>
> Sections 3, 4 and 7 describe a design. Several parts of it are now built,
> tested, and verified against the real corpus. Read section 7 for the current
> state; the design sections above it are unchanged and still the intent.
>
> **The headline finding changed the plan.** This document's premise is that the
> official marking scheme "is the scarce half". Measured against the corpus, it
> is not scarce -- it is **unlinked**. Only 33.3% of questions carried a scheme,
> but a separate store (`answer_keys.db`) holds 4,483 official answers with real
> value points, and 88.6% of those rows sit under a filename carrying the CBSE
> paper code that the question's source document also carries. Nothing joined
> the two.
>
> A relink pass now walks `question -> parse tree -> paper code -> answer_keys`
> and attaches the official scheme where one exists. Coverage went from 33.3% to
> **40.1%**, and the index itself from 1,040 to **4,404 of 4,483 rows (98%)**
> after fixing the paper-code normaliser, which only accepted `[/-]` and so
> dropped every filename using `.` or `_` (real files carry `31.1.1`,
> `55_7_1`, `X_086_31_1-1`). The remaining gap is now a **question-number
> mismatch** between paper and scheme (1,150 questions), not a missing answer.

---

## 1. What the asset actually is

Not "an API over some questions". The claim worth productising is narrower and
stronger:

> **Authentic CBSE board questions, each carrying its provenance and the official
> marking-scheme answer, bound to a canonical curriculum node.**

Three properties do the work, and all three already exist in
`assessment/pool.py` and `qmap.py`:

| Property | Why it is the moat |
|---|---|
**Authenticity** | Extracted from real board papers, not generated. A model can invent a plausible question; it cannot invent the one CBSE actually asked, or the official value points for it. |
**Marking schemes** | The answer key is the scarce half. Anyone can scrape questions; almost nobody has the official value points mapped to each question. |
**Curriculum binding** | Tagged to Board → Grade → Subject → Chapter → Subtopic, so a consumer can ask "5-mark case-based questions, Class 10 Science, Chemical Reactions" and get a real answer. Tagging is what makes it a database rather than a pile of PDFs. |

Everything below is about exposing that, not about generating more of it.

---

## 2. The blocker to resolve first: licensing

**This is a legal question, not an engineering one, and it gates the whole
proposal. I am not qualified to answer it and this document does not try.**

The facts as they affect the design:

- CBSE question papers and marking schemes are **third-party content**. They are
  not owned by this project.
- CBSE publishes previous-year papers and marking schemes publicly for students,
  and a large number of Indian edtech products republish PYQs. That establishes
  a norm; it does **not** establish that a commercial API redistributing them to
  third parties is permitted.
- There is a meaningful difference in kind between **classroom/study use**
  (what the current product does — teachers generating papers for their own
  school) and **redistributing the corpus as a product to other organisations**.
  The second is the one that needs a rights position.
- The API surface itself can be designed now; the **distribution** cannot be
  launched until the rights position is settled.

**Recommendation:** before building a public API, get a written position from
counsel on (a) redistribution of CBSE papers and marking schemes, (b) attribution
requirements, and (c) whether the answer is "public subset only". Design for the
restrictive answer — keep a `rights` field on every question from day one (§3)
so that a compliance decision is a filter, not a migration.

If the answer is unfavourable, the asset still has a viable form: a **private**
question bank API for partner schools under agreement, which is most of the
commercial value at none of the legal exposure.

---

## 3. Data model

The current pool stores a question, a marking scheme and a chapter tag. A product
needs more, and the additions are cheap now and expensive later.

| Field | Status today | Why it is needed |
|---|---|---|
`id` | exists (canonical) | Stable public identifier |
`text`, `marks`, `answer_scheme` | exists | The payload |
`bloom`, `difficulty`, `type` | exists | Facets consumers filter on |
`chapter_id`, `subtopic_ids` | exists | Curriculum binding |
**`source_document_id`, `page_number`, `bounding_box`** | exists internally | **Provenance is the differentiator.** Expose it: "here is the page in the 2023 paper this came from" is a trust signal no competitor can fake |
**`rights`** | missing | `{origin: "CBSE", redistribution: "unknown" | "private-only" | "public", basis: "..."}`. Add before any distribution |
**`version`** | missing | Questions get corrected; consumers need to know a record changed, and pinning |
**`language`** | missing | Hindi and English at minimum. Multilingual CBSE papers exist and are unused today |
**`calibration`** | missing | Community or statistical difficulty once answer data exists. The current `difficulty` is assigned, not measured — say so, do not imply otherwise |
**`superseded_by`** | missing | Curriculum revisions retire questions without deleting them |

Two rules worth keeping: **never delete** (supersede), and **never rewrite a
question's text in place** — a version bump, so a consumer can reproduce what
they saw.

---

## 4. API design

### Shape

The current `/api/v1/questions/search` is a POST-with-body for internal use.
A public API should be a resource API, because that is what developers expect,
what caches well, and what generates usable SDKs.

```
GET  /v1/questions                 list + filter (the workhorse)
GET  /v1/questions/{id}            one, with full provenance and scheme
GET  /v1/questions/{id}/scheme     just the marking scheme
GET  /v1/subtopics/{id}/questions  curriculum-driven listing
GET  /v1/curriculum/...            reuse the existing tree, read-only
GET  /v1/facets                    filter vocabulary and counts
GET  /v1/coverage                  answer-key coverage per subject x class
POST /v1/papers                    blueprint-driven paper generation
```

**The list is answer-keyed by default (rule Q1).** `/v1/questions`,
`/v1/subtopics/{id}/questions` and `/v1/facets` serve and count only questions
that carry a published answer key -- CBSE's marking scheme or NCERT's Exemplar
answer, with real content in it. An examination board does not issue a question
it cannot mark, and the audit of the first release found the default path
serving 345 records with no answer content at all. Two explicit ways to see the
rest, accepted by all three routes:

* `?has_scheme=false` -- ONLY the unanswerable set, for auditing what the
  relink has not reached (the MCP's `answer_key_state="none"`).
* `?include_unkeyed=true` -- the whole bank, for a client written against the
  old default.

`/v1/facets` takes the same default as the inline `?facets=true` counts, and
for the same reason: a facet count exists to size a query, so counting a wider
set than the query will serve misstates the page the consumer is about to ask
for. Paper generation (`assessment/pool.py`) applies the same rule to the same
bank, so a question the API will not list cannot be printed on a paper either.

`GET /v1/coverage` reports the shortfall per subject and class, and returns the
same numbers as the MCP server's `coverage_report` tool because both call
`QuestionBank.coverage()` (rule Q5: one corpus, two surfaces).

| Concern | Decision | Reasoning |
|---|---|---|
Versioning | Path-based (`/v1`) | Simplest to explain and to cache; matches Stripe's clarity without needing date headers |
Pagination | **Cursor**, not offset | The corpus is written once and read forever; offset paging over a large filtered set degrades and duplicates rows under concurrent edits |
Filtering | Query parameters, not a query DSL | `?subject=science&grade=10&marks=5&type=case_based&subtopic_id=...`. A DSL is a second language to document and to get wrong |
Search | Hybrid: lexical + semantic, with `mode=` | Lexical for exact syllabus terms ("Ohm's law"), semantic for intent ("questions about electricity for a weak student"). Expose which mode was used in the response |
Response | Include `facets` on list responses | One round trip instead of list-then-fetch-counts |
Errors | `application/problem+json` (RFC 9457) | Standard, machine-readable, survives an SDK generation |
Rate limits | Headers on every response (`RateLimit-*`) plus `429` with `Retry-After` | Consumers cannot behave well without them |

### Third-party authentication

| Consumer | Mechanism |
|---|---|
Partner schools, internal apps | API keys (hashed at rest, scoped per school, revocable) |
Third-party developers, public product | OAuth 2.0 client-credentials for server-to-server; no end-user OAuth needed, because there is no end-user data in the bank |
**Student-linked reads** (`/knowledge/*`, progress) | **Never** part of this API. The question bank is content; student data is DPDP-regulated and stays behind the existing authenticated app |

An API key must never grant access to anything a school's own users cannot see.
Scope keys to the curriculum and questions only.

---

## 5. Latency architecture on GCP

Read-heavy, write-never, which is the cheap and fast case.

```
                    Cloud CDN  (curriculum + facets, 1h TTL)
                         |
Client -> Global HTTPS LB -> Cloud Run (api, min 1, asia-south1)
                                   |
                                   +-- Memorystore Redis  (hot facets, 5m TTL)
                                   |
                                   +-- Cloud SQL read replica   (question reads)
                                        ^
                                        | nightly
                                   Cloud SQL primary  (ingest, admin)
```

| Layer | What it holds | TTL | Why |
|---|---|---|---|
Cloud CDN | Curriculum tree, facets, `catalog` | 1 hour | Immutable between ingests; serves from an Indian edge node |
Redis | Facet counts, popular filters | 5 minutes | The single most repeated query shape |
Read replica | All question reads | — | Keeps ingest and admin writes off the serving path |
Primary | Ingest, corrections | — | Never on the read path |

Expected shape at these volumes: **p99 dominated by network RTT, not by query
time.** Indian mobile RTT to `asia-south1` is typically 20–60 ms; a well-indexed
question read is single-digit milliseconds from cache. The p99 wins come from
caching, not from query tuning — so budget effort there first.

Indexes that matter: `(grade, subject, chapter_id)`, `(subtopic_id)`,
`(type, marks)`, and a GIN index on the tags array. A `pg_trgm` or tsvector
column for lexical search before considering anything heavier.

**What not to do yet:** no dedicated search engine (Elastic/Vertex AI Search) —
at this corpus size, Postgres full-text plus pgvector is faster to build, cheaper
to run, and one fewer system to operate. Revisit above roughly a million rows or
when relevance measurement actually exists.

---

## 6. Packaging it as a product

Configuration management is half of why developers adopt an API.

| Artifact | Mechanism |
|---|---|
OpenAPI spec | Already generated — `contract/openapi.json` ([`../contract/README.md`](../contract/README.md)) |
Reference docs | Already generated — [`api-reference.md`](api-reference.md) |
SDKs | Generate from the spec: `openapi-typescript` (done), plus Python and Dart for the audiences that matter here |
Developer portal | Rendered from the spec; every endpoint page needs a copy-pasteable example with a real sandbox key |
Sandbox | A fixed read-only subset with **fabricated** questions, so the sandbox is never the licensing problem and never leaks the corpus |
Changelog + deprecation | Required before any external consumer. Nothing in `/v1` changes without a dated entry |
Status page | Separate from the app's `/health`; consumers need to know about *your* incidents |

---

## 7. What exists vs what is needed

Updated 2026-09-17 with measured results. "exists" now means tested.

| Capability | Today | Needed |
|---|---|---|
| Question pool with provenance | **exists** | expose provenance fields |
| Marking schemes | **exists**, and now **attached** where a paper code matches (33.3% -> 40.1%) | narrow the question-number mismatch |
| Curriculum binding | **exists** (`qmap` subtopics) | 0% of the exported bank carries `subtopicIds`; chapter-level only |
| Lexical + semantic search | **exists** internally | wrap in a GET resource API |
| Facets | **done** -- `GET /v1/facets`, and `?facets=true` on the list | cdN caching |
| Blueprint paper generation | **exists** | expose with a documented schema |
| Pagination | **done** -- keyset cursor on `id`, verified to walk 3,286 rows with no duplicate or skip | — |
| Versioning | **done** -- `QuestionBankStore` appends `(id, version)`, and `at_version()` reconstructs what was served | backfill the existing bank into the store |
| Rights metadata | **done as a field** -- `rights` on every record, defaulting to `redistribution: "unknown"` so an unsettled position fails closed | **the counsel opinion itself, which still blocks distribution** |
| Item review states | **done** -- draft / in_review / published / superseded, with illegal transitions refused | editorial UI |
| Item-level audit trail | **done** -- every write appends a row with actor, note and both ends of a transition | an audit reader in the admin console |
| Auth for third parties | **done** -- `ApiKeyStore`, SHA-256 at rest, scoped, revocable, per-key quota in SQLite | key issuance UI |
| Rate limiting / quota | **done** -- per-key, counted in the database so N instances cannot each allow the full limit | — |
| QTI export | **done** -- QTI 2.1 package (manifest + items + test), value points carried in `rubricBlock` | QTI 1.2 for legacy LMS deployments |
| Grade by question | **done** -- `GET` one question across all students, `POST` one award to many | the Flutter review UI |
| SDKs, portal, changelog | **sandbox done** (`scripts/export_qbank_sandbox.py`, 60 fabricated questions); spec and reference docs generate already | published Python and Dart SDKs, portal, changelog |
| Multilingual | **absent** | Hindi-first. `language` exists on 100% of records but is `en` throughout |
| Calibration | **absent** | `calibration.measured` is `false` everywhere; difficulty is derived from marks and Bloom, and the payload says so |

Roughly: the corpus and the intelligence were ~80% there and the product surface
~10%. The product surface is now the larger half — but the one item that gates
everything, the rights position, is unchanged and still not an engineering
problem.

---

## 8. Phased plan

| Phase | Deliverable | Gate |
|---|---|---|
0 | **Rights position from counsel** | Blocks all distribution. Do this first, in parallel with phase 1 |
1 | `rights` + `version` + `language` fields on every question; supersede-don't-delete | No external surface needed; improves the internal bank immediately |
2 | Read-only resource API (`GET /v1/questions`, `/{id}`, `/{id}/scheme`, `/facets`) with cursor pagination and API keys | Internal consumers first — the Flutter client can migrate onto it and prove it |
3 | CDN + Redis + read replica; publish latency targets and measure | Needs real traffic, not a benchmark |
4 | Spec-generated SDKs, developer portal, sandbox, changelog | Only if phase 0 permits public distribution |
5 | Multilingual corpus (Hindi) and measured difficulty calibration | Depends on data, not code |

Phases 1 and 2 are worth doing **even if the public API never ships**, because
they make the internal bank better: versioned, properly attributed, and behind a
stable interface the two client sub-products can share.
