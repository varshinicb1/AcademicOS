# Production AI principles — research and conformance

**Status:** research complete; eight hardening changes implemented and verified;
one significant gap documented rather than half-built (idempotency, §5).
**Date:** 2026-09-17
**Scope:** full-stack web applications that combine agentic AI, personal data,
and a reliability obligation. Every claim about this codebase below was checked
against the source, and every "implemented" item has a test that fails without
it.

---

## 1. Why this document exists

A system that calls a language model on behalf of a user inherits a threat model
that ordinary web applications do not have. The failure modes are not exotic —
they are the ones the industry has already catalogued, measured, and written
down. What follows is the catalogue, mapped onto this codebase, with the
distance between the two stated honestly rather than aspirationally.

The rule applied throughout: **a principle that has not changed the code is a
paragraph, not a control.**

## 2. Sources

| Source | What it is authoritative for |
|---|---|
| OWASP Top 10 for LLM Applications 2026 (Aug 2026) | Risks where the model is a *component* inside your app |
| OWASP Top 10 for Agentic Applications 2026 (Dec 2025) | Risks where the model is an *actor* with tools and memory |
| AWS Builders' Library — *Timeouts, Retries, and Backoff with Jitter* | Retry/backoff/jitter; the "retries are selfish" framing |
| Google SRE Book — *Handling Overload*, error budgets | Retry budgets, load shedding, "slowed but stable" |
| Anthropic — *Building Effective Agents*, *Trustworthy agents in practice*, *How we contain Claude* | Agent architecture, least agency, containment, HITL calibration |
| PostgreSQL / AWS RDS documentation on Row-Level Security | Tenant isolation enforced at the database |
| NIST AI RMF (AI 100-1) and Generative AI Profile (NIST AI 600-1) | Governance vocabulary |
| IETF `Idempotency-Key` draft; Stripe's idempotency design | Retry-safe mutating endpoints |

Two boundary facts from the OWASP work shape everything below, and are worth
quoting because they decide which list applies:

> The LLM list owns the risk when the model is a component inside your
> application. The moment that model becomes an actor, with tools it can call,
> memory it carries between sessions, and consequences it sets in motion
> downstream, the risk moves to the Agentic list.

and, on the ranking itself:

> Excessive Agency climbed to third … and Unbounded Consumption rose four
> places, carried by practitioners who weigh resource and cost exhaustion higher
> than in its old rank.

## 3. The principles

**P1 — Least agency.** Give the model the smallest capability set that does the
job. Anthropic's containment work is blunt about why: defences should overlap,
but the deterministic boundary is what catches what the probabilistic layer
misses, and *"any probabilistic defence has a non-zero miss rate"*.

**P2 — Treat model output as untrusted input.** OWASP LLM10. Validate at every
destination: encode for HTML, parameterise for SQL, allowlist for tools. Never
Python truthiness on an external value.

**P3 — Bound consumption explicitly.** OWASP LLM06. Every AI surface needs
per-user quotas, size limits, timeouts, and loop limits *before* spend occurs.

**P4 — Retry only what can change, and never in lockstep.** Retry transient
failures with capped, fully-jittered exponential backoff; never retry
deterministic failures. AWS: *"A timeout or failure doesn't necessarily mean
that side effects haven't happened."*

**P5 — Every outbound call needs its own timeout.** A `requests` call with no
`timeout=` waits forever and holds a threadpool worker forever.

**P6 — Make mutating endpoints retry-safe.** Stripe's contract: the client picks
a key per logical operation, the server guarantees the same key produces the
same observable outcome. Claim first, execute second.

**P7 — Enforce tenant isolation in the database, not in application code.**
Application-level `WHERE tenant_id = ?` has no second line of defence, and one
forgotten clause is a cross-tenant breach. RLS with `FORCE`, plus `WITH CHECK`
on writes, is the last line.

**P8 — Human review is a gate with a calibration problem.** Anthropic measured
users approving ~93% of permission prompts. An approval dialog that is always
clicked is not a control; escalating everything is as broken as escalating
nothing.

**P9 — Observe the component, or you cannot evaluate the whole.** Agent
observability has three levels — outcome, trajectory, component — and the
regression flywheel runs *trace → label → dataset → CI gate*. Deterministic
checks on 100% of calls; LLM judges on a sample, because judges are expensive
and drift when the judge model updates.

**P10 — Fail closed on security defaults, and say which failures are
acceptable.** An unset tenant variable must return nothing, not everything. A
retrieval critic that is unreachable should retrieve, not answer unsourced.

## 4. Conformance: where this codebase stands

### Already sound before this work — and worth stating, because it is easy to
### erode

| Principle | Evidence |
|---|---|
| **P1 least agency** | The agent layer is **read-only**. `agents/base.py` exposes `SearchTool` and `ConceptLookupTool`; the critic scores and writes nothing. A prompt injection through corpus text can reorder which passage is quoted; it cannot exfiltrate, delete, or call anything. This is the single most important architectural property in the repo and it should not be traded away casually. |
| **P7 tenant isolation** | `school_id` scoping is enforced across stores, with `tests/test_school_scoped_stores.py` as a ratchet. Remaining gap: RLS is not used (see §5). |
| **P8 human review** | Curriculum extraction proposals require explicit principal approval before materialisation — a real gate, not a dialog. |
| **P2 (partly)** | Idempotent-by-design choices are already made in places: `POST /auth/logout` 200s with no token because there is nothing to delete. |

### Implemented in this pass

| # | Principle | Change | Verification |
|---|---|---|---|
| 1 | P4 | `llm/resilience.py`: `RetryPolicy`, **full-jitter** capped exponential backoff, `Retry-After` in both RFC 9110 forms, retryable status classification `{408,425,429,500,502,503,504}`. Replaced a linear, unjittered `5*(attempt+1)` sleep that **did not retry 502/504 at all**. | `tests/test_llm_resilience.py` (44) |
| 2 | P2 | `llm/coerce.py`: `as_bool/as_int/as_float/as_choice/as_text`, each recording a coercion problem. Fixed a **live inversion bug**: `bool("false") is True`, so a model replying `{"retrieve": "false"}` had its decision flipped and retrieval ran anyway. | `tests/test_llm_coerce.py` |
| 3 | P3 | `llm/budget.py`: `LLMBudget` + contextvar + `LLMBudgetExceeded`, wired into every LLM-capable route. Deepest path was 4–5 calls, bounded only by a `hits[:3]` slice — an accident, not a control. | `tests/test_llm_budget.py`, `tests/test_api_llm_guardrails.py` (11) |
| 4 | P3 | Request bounds in `api/main.py`: `MAX_QUERY_CHARS=4000`, `MAX_ANSWER_CHARS=20000`, `MAX_ID_CHARS=128`, `MAX_CAPACITY_MINUTES=240`. `DoubtRequest.doubt` had **no upper bound** and `ScoreRequest.student_answer` had **no `Field` at all** — both fed straight into prompts. | same |
| 5 | P9 | `llm/telemetry.py`: per-call records (latency, attempt, status, prompt **size**), bounded ring buffer, `GET /health/llm`. Records shape, never content, so observability does not create a second store of student data. | `tests/test_llm_sarvam_hardening.py` (37) |
| 6 | P5 | `assessment/vision.py`: **seven** outbound calls given socket timeouts. The module's `timeout_sec` looked like it covered them and did not — it bounds the polling loop, not any socket. | `tests/test_vision_timeouts.py` (6), incl. a repo-wide AST guard |
| 7 | P2 | `llm/sarvam.py`: response-shape validation. `data["choices"][0]["message"]` raised `KeyError`/`IndexError` four frames up; it is now one error naming what arrived. `max_tokens` is always sent (it was previously omitted, leaving completion length to the provider). | `tests/test_llm_sarvam_hardening.py` |
| 8 | P2 | `agents/critic.py`: coercion replaces truthiness; a malformed field no longer discards two valid judgments; prompt text bounded; the untrusted-input boundary documented in the system prompt. | `tests/test_agents_critic.py` |

**Two tests were rewritten, and that is worth flagging.** `test_agents_critic.py`
contained `test_decide_retrieve_string_value_is_truthy`, which asserted
`bool("false") is True` and carried the comment *"a stringy non-empty value still
means retrieve"*. It documented the inversion bug as intended behaviour. A test
that pins a defect is worse than no test: it converts a bug into a requirement.
Both are now regression tests for the correct behaviour, with the reason
recorded in the docstring.

**One latent test failure was repaired.** `AUTH_FIRST_ROUTES` in
`tests/test_route_inventory.py` was missing 15 auth-gated routes, so
`test_gated_routes_return_503_without_startup` failed whenever it actually ran —
and passed in the full suite only because an earlier test boots the app and the
guard skips it. Found by driving every route without a token and recording which
returned 401, rather than guessing. The list was derived empirically, not
hand-written.

### Verified state

```
1400 passed, 15 skipped, 1 xfailed, 0 failures in 91.85s
```

The baseline before this work was `1194 passed, 14 skipped, 1 xfailed`; these
changes added 206 tests and changed no existing behavioural expectation except
the two assertions that had pinned defects (§4).

## 5. The gap: idempotency on mutating endpoints

**Principle P6. Not implemented, deliberately, and the reason is concrete.**

Every mutating generation endpoint is currently unsafe to retry:

```
POST /api/v1/papers/generate
POST /api/v1/papers/quick-generate
POST /api/v1/papers/generate-from-ids
POST /api/v1/practice/generate
POST /api/v1/scan/sessions
POST /api/v1/assessments
```

A client that times out has no way to distinguish "the request never arrived"
from "it succeeded and the response was lost", so it must choose between
duplicating a paper and losing one. Both are wrong.

**The design is settled** (Stripe/Brandur, with the concurrency corrections from
the production write-ups):

1. Scope the uniqueness key to `(user_id, idempotency_key, endpoint)`, not the
   key alone — a client reusing one UUID across two endpoints must not collide.
2. **Claim before executing**: `INSERT ... ON CONFLICT DO NOTHING RETURNING`,
   never `SELECT` then `INSERT`. The check-then-act race lets two concurrent
   retries both pass the check and both execute.
3. Model the key as a three-state machine — `pending` / `succeeded` / `failed` —
   and return **409 with `Retry-After`** for an in-flight key rather than
   re-executing or hanging.
4. Store a SHA-256 of the request body; the same key with a different body is a
   client bug and returns **422**, before acquiring anything.
5. TTL the pending state and sweep it, or a worker that dies between `INSERT`
   and `UPDATE` leaves the key stuck in `pending` forever and every retry 409s
   permanently.
6. Fail **closed** if the claim cannot be made atomically.

**The blocker, precisely.** Step 2 needs an atomic conditional insert.
`durable_table(...)` exposes `select`, `upsert(row, on_conflict)`, `update`,
`delete` — and `upsert` returns `None`, with no indication of whether it
inserted or updated. So the durable path cannot currently express "insert only
if absent, and tell me which happened".

The local SQLite path can (`INSERT … ON CONFLICT DO NOTHING RETURNING` is
native and genuinely atomic), but a SQLite-backed idempotency store is close to
useless in production: both Render and Cloud Run wipe local disk on restart, so
the key would evaporate exactly when a retry is most likely — right after an
instance died. Implementing only that would produce a control that passes its
tests and does nothing where it matters.

`PostgresTable` (Cloud SQL) can do this natively; the Supabase PostgREST path
needs `Prefer: resolution=ignore-duplicates` plus a check of the returned
representation. Both are extensions to `supabase_kv.py`/`postgres_kv.py` before
the store can be written.

**Recommendation:** add `durable_table(...).insert_if_absent(row, on_conflict) ->
bool` to both backends, then build the store on top. Until then this is a stated
gap, not a silent one. `docs/supabase-setup.sql` remains unrun, so the durable
paths are already degraded — sequence the two.

## 6. Other accepted gaps, with reasons

| Gap | Principle | Why it is not fixed here |
|---|---|---|
| No row-level security | P7 | Isolation is enforced in application code with a test ratchet, which is the *first* line of defence, not the last. RLS needs `ALTER TABLE … ENABLE`+`FORCE` and a per-transaction `SET LOCAL app.school_id`; without a connection-pooler review (PgBouncer transaction mode resets session state) it risks a cross-tenant leak. The migration order is documented in the RLS literature for good reason: set the variable everywhere *first*, then enable the policy, or every query returns zero rows. |
| In-memory rate limiting | P3 | `RateLimiter` uses a per-process `deque`, so it does not span Cloud Run instances and resets on redeploy. Adequate for single-instance auth brute-force; not a quota system. |
| No retry budget | P4 | Google SRE's ~10% retry budget matters when many clients retry into one backend. Here one process calls one provider, so per-request attempt caps bound the amplification and a budget would add state without changing an outcome. Stated in `resilience.py`. |
| No trajectory or outcome evals | P9 | Only the component level exists. Trajectory and outcome evaluation need a versioned golden dataset built from real production traces — the trace→eval flywheel. Inventing a half-version would be worse than leaving a clean seam. |
| No cost/token accounting | P3, P9 | Telemetry records prompt and completion *character counts*, not tokens or cost, because the provider's usage block is not parsed. Enough to see a regression in shape; not enough to bill. |

## 7. What this work does not claim

- **No user has walked any of these paths in production.** The tests drive the
  real ASGI stack via `TestClient`, which is stronger than calling handlers
  directly — it is what proves the budget contextvar survives FastAPI's
  threadpool hop — but it is not a deployed instance.
- **The retry/backoff behaviour has not been exercised against a degrading
  provider.** Timing is asserted against an injected sleeper, not observed.
- **`/health/llm` describes one process.** On a multi-instance deployment that
  is a stated limitation, not a global view.
- **The idempotency gap is open.** §5.

## 8. Rules for the next agent

Derived from the above, ordered by how likely they are to be violated by
someone moving fast:

1. Do not add a tool to the agent layer without revisiting §4's least-agency
   argument. Read-only is the property that makes prompt injection survivable
   here.
2. Never read a model output with Python truthiness. Use `llm/coerce.py`.
3. Every outbound HTTP call passes a finite `timeout=`. There is a repo-wide AST
   test; do not weaken it.
4. Every LLM-capable route enters `with llm_budget(...)` **inside the endpoint
   body**, not in a dependency — the contextvar does not survive the
   dependency-to-endpoint threadpool hop.
5. Bound every request field that reaches a prompt. An unbounded `str` field on
   an LLM route is a denial-of-wallet path.
6. Do not add prompt or completion text to telemetry. This system holds
   children's data under DPDP; observability must not become a second store of
   it.
7. A test that asserts existing behaviour is not evidence the behaviour is
   correct. Two tests in this repo had pinned real defects.
