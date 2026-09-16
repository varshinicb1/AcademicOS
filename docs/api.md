# API & contributing guide

For a developer joining AcademicOS. Read
[`PRODUCTS_AND_RELEASES.md`](PRODUCTS_AND_RELEASES.md) first — it explains which
of the two sub-products and two releases you are looking at, which the rest of
this document assumes.

- **Generated endpoint inventory:** [`api-reference.md`](api-reference.md) — all
  122 operations, grouped by domain, with which require auth
- **Live schema:** `GET /openapi.json` · **Interactive docs:** `GET /docs`
- **Design system:** [`design-system.md`](design-system.md)

| Release | Base URL | Status |
|---|---|---|
Render | `https://academicos-backend.onrender.com` | live |
GCP | Cloud Run service URL (`gcp-deployment.md`) | written, not yet run |

Every operation lives under `/api/v1`. There is also a legacy `/v1/*` corpus
and agent surface — it is authenticated now, but nothing in the app calls it.

---

## 1. Quick start

```bash
# 1. register (the first principal of a school needs the bootstrap key)
curl -sX POST $BASE/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"schoolId":"school_1","name":"Priya","email":"priya@school.org",
       "password":"correct horse battery","principalKey":"<bootstrap-key>"}'
# -> {"user":{...},"token":"..."}

# 2. everything else carries the token
TOKEN=...
curl -s $BASE/api/v1/assessments -H "Authorization: Bearer $TOKEN"

# 3. who am I
curl -s $BASE/api/v1/auth/me -H "Authorization: Bearer $TOKEN"
```

Interactive docs at `/docs` let you authorise with that token and call any
endpoint from the browser.

---

## 2. Authentication & roles

- **Session token**, not JWT. `POST /api/v1/auth/login` returns an opaque
  `token`; send it as `Authorization: Bearer <token>` on every call.
  `POST /api/v1/auth/logout` invalidates it.
- **Roles** are `principal` (the Admin/Management tier), `teacher`, `student`.
- **`principal` can never be self-selected.** `POST /auth/register` accepts a
  `role` of `teacher` or `student`; the principal role is granted only by
  presenting a valid `principalKey`. This closed a real privilege-escalation
  bug, and `tests/test_users.py` pins it.
- **`401`** means no token, an expired token, or a token whose session no longer
  exists — the client should clear its session and route to login. **`403`**
  means authenticated but not permitted; the client should show the refusal, not
  log the user out. Getting this distinction wrong is what makes an app bounce
  users to login when they merely lack a permission.
- **School scoping is server-side, always.** `school_id` comes from the
  authenticated session, never from a path, query or body parameter. Several
  routes accept a `schoolId`/`teacherId` field for older clients and
  deliberately ignore it — see the ingest route, where trusting the body let an
  anonymous caller file a document against any school.

---

## 3. Conventions

| Concern | Convention |
|---|---|
| Casing | **camelCase on the wire** (every request/response model inherits a `Camel` base that aliases to snake_case internally) |
| Content type | `application/json`, except multipart on the upload routes (`/ingest/school-documents`, `/scan/sessions/{id}/pages`) |
| Timestamps | ISO 8601 with offset, e.g. `2026-09-16T09:14:00+05:30` |
| IDs | opaque strings, prefixed by kind: `asm_…`, `paper_…`, `user_…`, `src:…` |
| Listing | plain arrays; filtering is by query parameter, not a query language |
| Pagination | not implemented — the largest collections are scoped by school or assessment. A contributor adding one should use a `cursor` field rather than an offset. |
| Errors | FastAPI default: `{"detail": "..."}` |
| Status codes | `400` invalid input · `401` unauthenticated · `403` not permitted · `404` not found **or** not yours (deliberately not distinguished) · `422` schema validation · `503` a durability backend is unavailable |

**`404 vs 403` is deliberate.** Ownership checks return `404` when the object
does not exist and `403` when it exists but belongs to another school, so the
status never leaks whether an object exists. Follow that pattern in new routes.

---

## 4. Durability and the 503 contract

Reads and writes go through one factory, `postgres_kv.durable_table(name)`, which
selects **Cloud SQL → Supabase → local SQLite** by what is configured. Two
consequences for API consumers:

- A live backend failure raises `SupabaseUnavailable` / `PostgresUnavailable`,
  which an app-level handler in `api/main.py` converts to **`503` naming the
  table** that failed. It is never a bare `500`. A 503 here means "retry may
  help"; a 500 would mean a bug.
- `GET /health/storage` reports which backend is **actually active**:

```json
{"durability_backend":"supabase","durability_reachable":false,
 "supabase_configured":true,"supabase_reachable":false,
 "tables":{"users":"error: … PGRST205 …","assessments":"ok", …}}
```

**Check this endpoint rather than guessing from a dashboard.** On 2026-09-16 it
reported `users`, `sessions`, `audit_log` and `learner_events` missing in
production — auth sessions and the audit trail were not durable — while `/health`
happily returned `{"status":"ok"}`. Answers are cached for 30s and
single-flighted; allow one TTL before trusting a still-red result.

---

## 5. Contract discipline

This project has a real, measured contract bug: **46 frontend calls target
backend routes that have never existed**, all in `api_client.dart`, all
currently unreachable from any screen. Four rules prevent the next one.

1. **Never construct a URL from a string in the client.** The Flutter
   repositories wrap API clients; a new screen must call through those, and the
   path must match `api-reference.md`.
2. **A new route needs a docstring.** FastAPI publishes the first line as the
   OpenAPI summary, which is what generates `api-reference.md`'s "Purpose"
   column. An undocumented route produces a useless reference entry.
3. **Declare auth with `Depends`, never inline header parsing.** The OpenAPI
   `security` block — and therefore the `Auth` column in the reference — exists
   only because `get_current_user` declares `HTTPBearer`. Reading a raw
   `Header(...)` silently advertises the route as public; that is exactly how
   122 operations were once documented as having no auth at all.
4. **Run the guards before you push.** They are cheap and they are real:

```bash
python scripts/audit_frontend_backend_contract.py       # frontend vs backend paths
python scripts/audit_endpoint_test_coverage.py          # every route reached by a test
python scripts/generate_api_reference.py                # refresh the reference
```

`tests/test_frontend_backend_contract.py` fails the build on a new frontend call
with no backend route, **and** on an allowlisted gap that has since been fixed —
so the debt list can neither grow nor rot into a lie.

### The frozen contract

The API surface is also committed as a **frozen artifact** in `contract/`:

| File | What |
|---|---|
`contract/openapi.json` | The full OpenAPI schema — 109 paths, 122 operations, 104 authenticated |
`contract/api-types.ts` | TypeScript types generated from it |

Regenerate both after any route, model or auth change:

```bash
python scripts/export_openapi.py
npx --yes openapi-typescript@latest contract/openapi.json -o contract/api-types.ts
```

`tests/test_openapi_contract.py` regenerates the schema and compares it against
the committed copy, so **forgetting this step fails CI with the diff** rather
than letting a client be written against a schema that is no longer true. See
[`../contract/README.md`](../contract/README.md) for the rules.

This exists because the alternative has already been paid for once: 46 frontend
calls targeting routes that never existed, invisible until an audit was run by
hand. With a generated, typed client, that bug becomes a compile error.

---

## 6. Testing

```bash
# backend — the gate. A red suite deploys nothing.
.\.venv\Scripts\python.exe -m pytest tests -q

# frontend
cd frontend; flutter test; flutter analyze

# the Cloud SQL adapter tests need a real Postgres, otherwise they skip
# (CI provides one as a service container)
ACOS_TEST_PG_HOST=localhost ACOS_TEST_PG_DB=academicos_verify \
ACOS_TEST_PG_USER=postgres  ACOS_TEST_PG_PASSWORD=postgres \
  python -m pytest tests/test_postgres_kv.py -q
```

**Two norms that matter more than coverage numbers:**

- **Never mock away live functionality in an integration test.** The
  `test_full_boot_*` tests boot the real app in-process, register real users
  through the real auth routes, and exercise real cross-school rejection. They
  are the strongest tests in the project; protect them.
- **`tests/test_route_inventory.py` is a contract test, not a smoke test.** It
  pins the route table and the auth boundary. If you add or remove a route,
  expect to update it — and treat that diff as the question "should this route
  exist?".

Current state: **1,184 backend tests passing**, 2 skipped, 1 xfailed; every one
of the 107 API paths is reached by at least one test call. Frontend: 117 tests.
That is *test* coverage, not *end-to-end* verification — see
[`REQUIREMENTS_BY_LAYER.md`](REQUIREMENTS_BY_LAYER.md) §Part 4 for the
difference, which is large.

---

## 7. Contributing workflow

```bash
git checkout -b feat/<scope>-<summary>
# ... make the change, with tests ...
.\.venv\Scripts\python.exe -m pytest tests -q     # must be green
git commit -m "feat(scope): imperative summary"
```

| | |
|---|---|
Working tree | `src/academicos/` is the live backend. `backend/` is a **scaffolded rewrite — do not edit it** unless the task is explicitly about it. |
Commit style | Conventional commits, multi-scope is used here: `feat(deploy,data): …`, `fix(auth): …`, `docs: …`. The body explains *why*, including what was ruled out. |
Invariants | [`AGENTS.md`](../AGENTS.md) and [`CLAUDE.md`](../CLAUDE.md) — WAL pragmas, the two client sub-products, the durable-store factory. Read them before touching storage or the client. |
Compliance | Student data touches DPDP Act 2023 and CERT-In. Read [`compliance.md`](compliance.md) before changing anything that reads, stores or exports student records. |
Docs | If you change a route, regenerate the reference. If you change behaviour a doc claims, correct the doc in the same commit — several docs here went stale for weeks precisely because that did not happen. |

### Adding a route, end to end

1. Put it in the right router under `src/academicos/` — `assessment/routes.py`,
   `pillar_routes.py`, `curriculum/routes.py`, `mobile_routes.py`.
2. Give it a **docstring** and `Depends(get_current_user)` or
   `Depends(require_principal)`.
3. Scope it to a school — take `school_id` from the authenticated user.
4. Add a `test_full_boot_*` test that calls it through the real app with a real
   token, plus a cross-school rejection assertion.
5. Wire the client through the existing repository/client layer, never a raw
   string URL.
6. Run the three guard scripts above and commit the regenerated reference.

---

## 8. Local setup

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -e ".[api,mobile-scan,dev]"     # add postgres,gcs for the GCP paths
python -m academicos.cli serve --host 127.0.0.1 --port 8010
# docs at http://127.0.0.1:8010/docs

cd frontend
flutter run -d chrome --dart-define=ACADEMICOS_API=http://localhost:8010/api/v1
```

Nothing else is required to work on the backend. `ACOS_DATA_ROOT` defaults to
`./academicos-data`, which carries the pre-ingested corpus; with no
`ACOS_POSTGRES_*` or `SUPABASE_*` set, every store transparently uses local
SQLite, which is exactly what you want for local development.

---

## 9. Where to look next

| Question | Document |
|---|---|
Which product/release am I in? | [`PRODUCTS_AND_RELEASES.md`](PRODUCTS_AND_RELEASES.md) |
What has each layer actually delivered? | [`REQUIREMENTS_BY_LAYER.md`](REQUIREMENTS_BY_LAYER.md) |
Every requirement vs the client transcript | [`TRANSCRIPT_REQUIREMENTS_MATRIX.md`](TRANSCRIPT_REQUIREMENTS_MATRIX.md) |
Storage, concurrency, base 2 invariants | [`AGENTS.md`](../AGENTS.md) |
Render release operations | [`deployment.md`](deployment.md) |
GCP release operations | [`gcp-deployment.md`](gcp-deployment.md) · [`gcp-bootstrap.md`](gcp-bootstrap.md) |
Why the web client may move off Flutter | [`frontend-platform-decision.md`](frontend-platform-decision.md) |
The honest current state | [`system-review.html`](system-review.html) |
