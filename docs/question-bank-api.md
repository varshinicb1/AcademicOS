# The question bank as a standalone API asset

**Status:** architecture proposal, 2026-09-17, with an implementation update
below. Sections 1-5 are the design; section 7 records what now exists and
section 8 what does not. **Section 9 is how to call `/v1` as it is built**:
authentication, every filter, every error, and copy-paste snippets.
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

**`has_scheme` changed meaning in this pass, without a version bump, and that
is worth stating plainly.** It used to test the provenance label alone --
`provenance == "cbse_marking_scheme"` -- so `?has_scheme=true` meant "an
official CBSE scheme" and returned 1,235 records of the live bank. It now tests
the shared answer-key rule (a published provenance AND real content), so the
same request returns 5,427. Nothing errors and no field changes shape; a client
that used it as an official-schemes filter silently gets four times the set.
The official-schemes filter did not survive as `has_scheme`, so it is its own
parameter:

* `?key_provenance=cbse_marking_scheme` -- only questions whose key is the
  board's own marking scheme (the MCP's `answer_key_state="official"`).
* `?key_provenance=ncert_exemplar_answer` -- only questions keyed by NCERT's
  Exemplar answer.

It narrows **within** the answer-keyed set and never widens past Q1, so
`?key_provenance=cbse_marking_scheme` is exactly the `withOfficialCbseScheme`
count `/v1/coverage` reports. Any other value is a `400` naming the two
accepted ones rather than an empty page that reads like "the bank has none".
`has_scheme`, `include_unkeyed` and `key_provenance` are accepted by all three
routes.

`/v1/facets` takes the same default as the inline `?facets=true` counts, and
for the same reason: a facet count exists to size a query, so counting a wider
set than the query will serve misstates the page the consumer is about to ask
for. Paper generation (`assessment/pool.py`) applies the same rule to the same
bank, so a question the API will not list cannot be printed on a paper either.
All three callers -- HTTP, MCP and paper generation -- import the rule from
`assessment/qbank_engine.py`, which deliberately imports no web framework so
that the MCP server and the paper pool run on an install without `[api]`.

`GET /v1/coverage` reports the shortfall per subject and class, and returns the
same numbers as the MCP server's `coverage_report` tool because both call
`QuestionBank.coverage()` (rule Q5: one corpus, two surfaces). Per subject and
class it reports `markValues` -- the distinct mark denominations on offer,
`[8, 9]` for Assamese class 12 over two questions -- and `marksTotal`, what
those answer-keyed questions add up to. `markValues` was called
`marksAvailable`, which on a coverage endpoint reads as the total a buyer would
size a purchase on; it never was.

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
| Auth for third parties | **done** -- `ApiKeyStore`, SHA-256 at rest, scoped, revocable, per-key quota in SQLite; issued from the web console's API keys page; limited to classes and subjects when minted (2026-10-01, section 9) | usage shown on the web page |
| Rate limiting / quota | **done** -- per-key, counted in the database so N instances cannot each allow the full limit | — |
| QTI export | **done** -- QTI 2.1 package (manifest + items + test), value points carried in `rubricBlock` | QTI 1.2 for legacy LMS deployments |
| Grade by question | **done** -- `GET` one question across all students, `POST` one award to many | the Flutter review UI |
| SDKs, portal, changelog | **sandbox done** (`scripts/export_qbank_sandbox.py`, 60 fabricated questions); spec and reference docs generate already; copy-paste Python, JavaScript and curl snippets in section 9 | published Python and Dart SDKs, portal, changelog |
| Webhooks | **done** (API-6, 2026-10-01) -- `questions.added` per chapter, HMAC-signed, retried with backoff, public HTTPS only, scoped to the key; registered and logged on the web's API keys page (section 9, "Webhooks") | more event types |
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

---

## 9. Calling `/v1` (as built, 2026-10-01)

Everything here is what the code does, and `contract/openapi.json` declares
the same: the two key schemes, every parameter, and every error response with
its body. The rights position in section 2 still gates distribution to third
parties; this section is for the partner who has it.

### Base URL and the key

* **Base URL:** `https://academicos-backend-2eskom55ta-el.a.run.app`. The
  question-bank routes are at the root (`/v1/...`), not under `/api/v1`.
* **Getting a key:** a principal mints one on the web console's **API keys**
  page (or `POST /api/v1/api-keys`). The key (`acos_qb_...`) is shown **once**;
  only its SHA-256 is stored.
* **Sending it:** either header works.
  * `X-API-Key: acos_qb_...`
  * `Authorization: Bearer acos_qb_...`. This is the API key, not a user's
    session token; a session token is refused here.
* **Scopes:**
  * `questions:read` opens the question, scheme, subtopic and homework-set
    routes.
  * `facets:read` opens `/v1/facets` and `/v1/coverage`.
  * `papers:create` and `curriculum:read` are refused at mint, `422 ... not
    available yet`, because no route checks them.
  * Any scope that would reach student data is refused permanently.
* **Classes and subjects:** a key may be limited when it is minted (`"grades":
  [9, 10]`, `"subjects": ["Science"]`). Then:
  * Every route serves only records inside the limits, and `/v1/facets` and
    `/v1/coverage` count only those.
  * A request that names a class or subject outside them is a `403`, and so is
    asking for a question outside them by id.
  * A subject the bank does not carry is refused at mint, `422`, with the
    bank's subjects listed.
  * The MCP server's network transports refuse a limited key, `403`. Its tools
    cannot apply the limits yet, and serving the whole bank would undo them.
* **Quota:** per key, per minute, counted in the database.
  * Every `200` carries `RateLimit-Limit` and `RateLimit-Policy`.
  * A spent key gets `429` with `Retry-After`: the seconds left in the current
    one-minute window, not a fixed 60.

### The routes

| Route | Scope | What it returns |
|---|---|---|
| `GET /v1/questions` | `questions:read` | A page of questions matching the filters below, `{items, count, totalMatching, nextCursor}`; `facets=true` adds the counts |
| `GET /v1/questions/{id}` | `questions:read` | One record, with provenance, rights and scheme |
| `GET /v1/questions/{id}/scheme` | `questions:read` | Just the marking scheme: value points, model answer, provenance, `hasAnswerKey` |
| `GET /v1/subtopics/{id}/questions` | `questions:read` | The same page as `?subtopic_id={id}`. Subtopic ids contain `/` (`science-10/life-processes/nutrition/nutrition-in-human-beings`); send them as they are or percent-encoded, both work |
| `GET /v1/facets` | `facets:read` | Counts per subject, grade, marks, type, difficulty, Bloom level, review state, source, book and key tier |
| `GET /v1/coverage` | `facets:read` | Answer-key coverage per subject and class |
| `POST /v1/homework-sets` | `questions:read` | A homework set, below |

Question ids can contain spaces and colons (`cbse:sqp:ClassX_2022_23:Carnatic
Music (Percussion):1`): percent-encode them in a path, as the snippets do.

### Filters on `GET /v1/questions`

Every filter narrows; they combine with AND. **A query parameter a route does
not take is a `422` naming it**: `?subjct=Science` used to answer with the
whole bank (audit D7). An unknown *value* of an open filter (`?book=zzz`) is an
empty page, because that is the true answer.

| Parameter | Matches |
|---|---|
| `subject`, `grade` | the record's subject (case ignored) and class |
| `marks`, `type`, `difficulty`, `bloom`, `review_state` | the record's field, exactly |
| `chapter_id` | the chapter the paper builder files the question under (a pre-2024 slug still works) |
| `subtopic_id`, `topic_id` | one of the record's `subtopicIds` / `topicIds`, exactly |
| `competency` | one of the record's `competencyIds`, exactly. **No record in the served bank carries one yet** (0 of 5,319 at this commit), so this answers an empty page until the bank is tagged |
| `source` | the record's `source` (case ignored): `cbse_board_paper`, `cbse_sample_paper`, `cbse_question_bank`, `ncert_exemplar`, ... The `source` facet lists what the bank holds |
| `book` | the publication the question was printed in, as its `rights.attribution` names it (`NCERT, Exemplar Problems, Class X Science`). Case and spacing are ignored; the `book` facet lists the exact names. To select the textbook chapter a question is filed under, use `chapter_id` |
| `trust` | the key's trust label, the list's `keyTier`: `published` (CBSE's or NCERT's own key) or `checked` (grounded in the textbook, two agreeing solves, or a teacher's approval). Anything else is a `400` |
| `key_provenance` | one kind of key, e.g. `cbse_marking_scheme` for the board's own schemes |
| `has_scheme`, `include_unkeyed` | rule Q1's two opt-ins (section 4): `has_scheme=false` for only the unanswerable set, `include_unkeyed=true` for everything |
| `keyword` | a substring of the stem or tags |
| `limit` (1-200, default 25), `cursor`, `facets` | paging and inline counts. `Link: <...>; rel="next"` repeats the whole query with the next cursor |

### Homework sets

`POST /v1/homework-sets` with a JSON body. Every question in a set has an
answer key, and the same body with the same `seed` returns the same set.

| Field | Meaning |
|---|---|
| `subject`, `grade` | required |
| `chapterIds`, `topicIds`, `subtopicIds` | optional; a question must carry one of each list given |
| `count` (1-50, default 10) | how many, when no mix is given |
| `marks` | a mix of marks: `{"1": 4, "3": 2}` is four 1-mark and two 3-mark questions |
| `types` | a mix of types, `{"mcq": 5, "short_answer": 3}`; or a list, `["mcq", "short_answer"]`, meaning `count` questions of those types, spread across them. A list also chooses the types inside a `marks` mix |
| `excludeIds` | ids the class has already had; the API keeps no class history (API-5) |
| `seed` | any string; the default is fixed per subject, class and chapters |

The rules:

* A `marks` mix and a `types` mix together are a `422`. Satisfying both at once
  is an allocation problem a greedy pick gets wrong without saying so. To
  combine them, send `types` as a list.
* `count` sent beside a mix must equal the mix's total, or it is a `422`. It
  used to be ignored.
* The response is `{items, count, requested, available, shortfall}`.
  `shortfall` names every bucket the bank could not fill, and by how many:
  `{"4": 2}` (marks), `{"mcq": 3}` (types), or `{"any": 8}` with no mix.

### Errors

Every error body is JSON with a `detail`. The bodies are served as
`application/json`, not yet `application/problem+json`; a `400` carries RFC
9457's fields **under** `detail`.

| Status | When | Body |
|---|---|---|
| `400` | A cursor that does not decode; a `key_provenance` or `trust` outside its vocabulary; `has_scheme=false` with `key_provenance` or `trust` (no record can satisfy both) | `{"detail": {"type": "about:blank", "title": "unknown trust label", "status": 400, "detail": "trust must be one of checked, published"}}` |
| `401` | No key, an unknown key, or a revoked one. Carries `WWW-Authenticate: Bearer` | `{"detail": "a valid API key is required"}` |
| `403` | The key lacks the route's scope; or the request, or the question asked for, is outside the key's classes or subjects | `{"detail": "this key does not hold the 'questions:read' scope"}`, `{"detail": "this key is limited to classes [10]; class 9 is outside it"}` |
| `404` | No question with that id (and any path that is not a route) | `{"detail": "no question 'cbse:q:x:1'"}` |
| `422` | A query parameter the route does not take; a value of the wrong type or out of range (`limit=500`); a homework-set body that does not validate | `{"detail": [{"type": "extra_forbidden", "loc": ["query", "subjct"], "msg": "unknown query parameter 'subjct'; this route takes ...", "input": "Science"}]}` |
| `429` | The key spent its requests for this minute. Carries `Retry-After` | `{"detail": "quota exceeded for Partner LMS: 120/min"}` |
| `503` | The question bank is not loaded on this server | `{"detail": "question-bank API not initialised"}` |

Known gaps, from the audit and not fixed here:

* Error responses carry no `RateLimit-*` headers (D65).
* A few malformed cursors (`%%%`, `....`) decode to something and restart at
  page one rather than answering `400` (D64).
* Webhooks (API-6) carry one event, `questions.added`; see "Webhooks" below.

### Snippets

Set the key once: `export ACOS_QB_KEY=acos_qb_...`.

**curl**

```bash
BASE=https://academicos-backend-2eskom55ta-el.a.run.app

# List: 3-mark Science 10 questions from the NCERT Exemplar, with counts.
curl -s -G "$BASE/v1/questions" -H "X-API-Key: $ACOS_QB_KEY" \
  --data-urlencode subject=Science --data-urlencode grade=10 \
  --data-urlencode marks=3 --data-urlencode source=ncert_exemplar \
  --data-urlencode limit=50 --data-urlencode facets=true

# Next page: pass nextCursor back as cursor (or follow the Link header).
curl -s -G "$BASE/v1/questions" -H "X-API-Key: $ACOS_QB_KEY" \
  --data-urlencode subject=Science --data-urlencode grade=10 \
  --data-urlencode cursor="<nextCursor>"

# One question's marking scheme. Percent-encode the id: ids hold spaces.
QID=$(python3 -c 'import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1], safe=""))' "exemplar:q:10:science:6:-:1")
curl -s "$BASE/v1/questions/$QID/scheme" -H "Authorization: Bearer $ACOS_QB_KEY"

# A homework set: four 1-mark and two 3-mark questions from one chapter.
curl -s "$BASE/v1/homework-sets" -H "X-API-Key: $ACOS_QB_KEY" \
  -H "Content-Type: application/json" \
  -d '{"subject": "Science", "grade": 10, "chapterIds": ["life-processes"],
       "marks": {"1": 4, "3": 2}, "excludeIds": [], "seed": "10A-week-14"}'
```

**Python (`requests`)**

```python
import os
import time
from urllib.parse import quote

import requests

BASE = "https://academicos-backend-2eskom55ta-el.a.run.app"
session = requests.Session()
session.headers["X-API-Key"] = os.environ["ACOS_QB_KEY"]


def call(method: str, path: str, **kwargs) -> dict:
    """One request; waits out a 429 and raises on any other error."""
    while True:
        r = session.request(method, BASE + path, timeout=30, **kwargs)
        if r.status_code == 429:
            time.sleep(int(r.headers["Retry-After"]))
            continue
        if not r.ok:
            raise RuntimeError(f"{r.status_code}: {r.json()['detail']}")
        return r.json()


# List: every 3-mark Science 10 Exemplar question, all pages.
params = {"subject": "Science", "grade": 10, "marks": 3,
          "source": "ncert_exemplar", "limit": 200}
questions = []
while True:
    page = call("GET", "/v1/questions", params=params)
    questions += page["items"]
    if not page["nextCursor"]:
        break
    params["cursor"] = page["nextCursor"]

# One question's marking scheme.
scheme = call("GET", f"/v1/questions/{quote(questions[0]['id'], safe='')}/scheme")
for point in scheme["markingPoints"]:
    print(point["marks"], point["description"])

# A homework set: two MCQs and one short answer, avoiding last week's set.
homework = call("POST", "/v1/homework-sets", json={
    "subject": "Science", "grade": 10, "chapterIds": ["life-processes"],
    "types": {"mcq": 2, "short_answer": 1},
    "excludeIds": [q["id"] for q in questions[:5]],
})
print(homework["count"], "of", homework["requested"], "shortfall:", homework["shortfall"])
```

**JavaScript (`fetch`)**

```js
const BASE = "https://academicos-backend-2eskom55ta-el.a.run.app";
const KEY = process.env.ACOS_QB_KEY;

async function call(path, init = {}) {
  for (;;) {
    const r = await fetch(BASE + path, {
      ...init,
      headers: { "X-API-Key": KEY, "Content-Type": "application/json", ...init.headers },
    });
    if (r.status === 429) {
      await new Promise((ok) => setTimeout(ok, Number(r.headers.get("Retry-After")) * 1000));
      continue;
    }
    const body = await r.json();
    if (!r.ok) throw new Error(`${r.status}: ${JSON.stringify(body.detail)}`);
    return body;
  }
}

// List: Science 10 questions whose key CBSE or NCERT published.
const params = new URLSearchParams({ subject: "Science", grade: "10", trust: "published", limit: "50" });
const page = await call(`/v1/questions?${params}`);

// One question's marking scheme.
const scheme = await call(`/v1/questions/${encodeURIComponent(page.items[0].id)}/scheme`);

// A homework set: 6 questions, MCQs and short answers, from one topic.
const homework = await call("/v1/homework-sets", {
  method: "POST",
  body: JSON.stringify({
    subject: "Science", grade: 10, count: 6, types: ["mcq", "short_answer"],
    topicIds: ["science-10/life-processes/nutrition"],
  }),
});
console.log(homework.count, homework.shortfall);
```

### Webhooks: `questions.added` (API-6)

Instead of polling `/v1/questions`, a partner can be told when there is
something new to fetch. A webhook belongs to one API key: the school's
principal registers the partner's URL for that key on the web console's
**API keys** page (or `POST /api/v1/api-keys/{key_id}/webhooks` with
`{"url": "https://...", "events": ["questions.added"]}`), copies the secret it
shows once, and hands both to the partner. The same page lists each webhook's
deliveries: status, attempts, and the receiver's last answer or the error.

**When an event is sent.** Whenever the questions the key may read grow: a
bank load or reload that serves new answer-keyed questions, or the school's
reviewer taking back a rejection in the review queue. Each chapter of new
questions is one event (at most 500 ids; more are split). A webhook hears only
of changes after it was registered.

**What it carries.** Question ids and where they sit, nothing else: no
question text (fetch it with `GET /v1/questions/{id}` and the same key, which
re-checks the key's scope), and no student, teacher or school record of any
kind. Only questions the key may read are announced: its classes and subjects,
the `questions:read` scope (a webhook cannot be registered on a key without
it), and not a question the school's reviewer rejected.

A worked example you can check your verifier against: with the secret
`whsec_test_only`, this request verifies (its body is one line; the server
sends compact JSON with sorted keys, and you must verify the bytes as sent):

```http
POST /your/endpoint HTTP/1.1
Content-Type: application/json
X-AcademicOS-Event: questions.added
X-AcademicOS-Delivery: whd_0123456789abcdef
X-AcademicOS-Signature: t=1790848800,v1=e190c4313f69d011767b929235732045438a3b8c3701910229272cfb3975fd8d

{"createdAt":"2026-10-01T10:00:00+00:00","data":{"chapterId":"life-processes","count":2,"grade":10,"questionIds":["q-101","q-107"],"reason":"bank_updated","subject":"Science"},"id":"evt_0123456789abcdef0123","type":"questions.added"}
```

(`t` there is in the past, so a five-minute tolerance refuses it; check the
HMAC with the tolerance switched off.)

`reason` is `bank_updated` (a bank load served new questions) or
`review_approved` (the school's reviewer took back a rejection).

**Answer quickly with any 2xx.** Anything else, a timeout (5 s to connect,
10 s to answer) or a refused connection is retried after 1 minute, 5 minutes,
30 minutes, 2 hours and 6 hours, six attempts in all, then the delivery is
marked `failed`. A retry sends the same body with the same
`X-AcademicOS-Delivery`, so de-duplicate on that header (or on `id`).
Redirects are not followed.

**Where it may point.** `https://` only, with no user name or password in the
URL, and only to a public address. A host that is, or resolves to, a private,
loopback, link-local, carrier-grade NAT, multicast, reserved or cloud-metadata
address is refused when the webhook is registered (422) and again before every
send; the send connects to the address it has just checked, with TLS verified
against your host name.

**Stopping it.** Revoking the webhook or its API key stops it at once, and
anything not yet delivered is cancelled: nothing is sent for a revoked key.

#### Verifying the signature

`X-AcademicOS-Signature` is `t=<unix seconds>,v1=<hex>`, where `<hex>` is
HMAC-SHA256 under the webhook's secret over `<t>.` followed by the raw request
body, byte for byte. Compute it over the body exactly as received (before any
JSON parsing), compare in constant time, and refuse a `t` more than five
minutes from your clock, which stops a captured request being replayed.

**Python**

```python
import hashlib
import hmac
import time


def verify(secret: str, header: str, body: bytes, tolerance: int = 300) -> bool:
    fields = dict(p.split("=", 1) for p in header.split(",") if "=" in p)
    try:
        t = int(fields["t"])
    except (KeyError, ValueError):
        return False
    if abs(time.time() - t) > tolerance:
        return False
    expected = hmac.new(secret.encode(), f"{t}.".encode() + body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, fields.get("v1", ""))


# Flask, for example:
# if not verify(SECRET, request.headers["X-AcademicOS-Signature"], request.get_data()):
#     abort(400)
```

**JavaScript (Node.js)**

```javascript
const crypto = require("node:crypto");

function verify(secret, header, rawBody, toleranceSeconds = 300) {
  const fields = Object.fromEntries(
    header.split(",").map((p) => p.split("=")).filter((kv) => kv.length === 2));
  const t = Number.parseInt(fields.t, 10);
  if (!Number.isFinite(t) || Math.abs(Date.now() / 1000 - t) > toleranceSeconds) return false;
  const expected = crypto.createHmac("sha256", secret)
    .update(`${t}.`).update(rawBody).digest("hex");
  const given = Buffer.from(fields.v1 || "", "utf8");
  const want = Buffer.from(expected, "utf8");
  return given.length === want.length && crypto.timingSafeEqual(given, want);
}

// Express: keep the raw body, e.g. app.post("/hook", express.raw({ type: "application/json" }), ...)
// and call verify(SECRET, req.get("X-AcademicOS-Signature"), req.body).
```

The routes, all for the key's own school's principal:

| Route | Does |
|---|---|
| `POST /api/v1/api-keys/{key_id}/webhooks` | register a URL; the answer carries `secret`, shown once |
| `GET /api/v1/api-keys/{key_id}/webhooks` | the key's webhooks (the secret is never listed) |
| `DELETE /api/v1/api-keys/{key_id}/webhooks/{webhook_id}` | revoke; undelivered events are cancelled |
| `GET /api/v1/api-keys/{key_id}/webhooks/{webhook_id}/deliveries` | the last 50 deliveries: status, attempts, last answer |
