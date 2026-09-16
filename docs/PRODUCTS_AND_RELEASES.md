# Products & Releases

**This file is the source of truth for "which thing are we talking about".**
Older documents — and several code comments — use "the deployment", "the app"
and "production" interchangeably for three genuinely separate deliverables.
Where they disagree with this file, this file wins.

Last reconciled: 2026-09-16.

---

## 1. There are two sub-products

They do not share a runtime, a data store, or a release cadence.

| | **AcademicOS Mobile** | **AcademicOS Web** |
|---|---|---|
| What it is | Standalone Android app | Flutter web client in a browser |
| Flutter target | Android (APK) | Web |
| Build flag | `--dart-define=ACADEMICOS_OFFLINE=true` | none (default) |
| Needs a backend? | **No.** Runs entirely on device | **Yes.** Every action is an HTTP call |
| Data lives in | On-device encrypted Hive + corpus bundled in the APK | Nowhere; it is a thin client |
| API clients wired | `LocalApiClient`, `LocalPillarApi` | `PillarApi`, `AuthApi`, `ConsentApi`, `CurriculumApi`, `ApiClient` |
| Ships as | `AcademicOS_Standalone.apk`, `AcademicOS-demo-offline.apk` | Static web bundle |
| Reachable in | `frontend/lib/core/local_engine/` | `frontend/lib/data/datasources/api/` |

The switch is one line in `frontend/lib/core/di/service_locator.dart`
(`offlineMode`), which swaps two objects in the service locator. Everything
above — repositories, use cases, all 24 screens — is identical between the two
builds. That is deliberate: one codebase, two products.

### Why this distinction matters operationally

- A bug reported against **Mobile** is a bug in the offline engine. The backend
  is not involved, cannot be blamed, and re-deploying it will not fix it.
- A bug reported against **Web** may be a backend bug, a client bug, or — most
  likely, per `docs/system-review.html` — a mismatch between a client call and
  a route that never existed.
- The offline engine **must be updated by hand** whenever the server contract
  changes. It is the largest unshared maintenance surface in the repository.

---

## 2. The backend has two deployment releases

Both deploy the *same* `src/academicos` backend. They are different production
releases with different infrastructure, different durability backends, and
different pipelines. Neither is an upgrade path of the other; they coexist.

| | **Render release** (current) | **GCP release** (pure GCP) |
|---|---|---|
| Compute | Render web service (image-backed) | Cloud Run, `asia-south1` |
| Image registry | Docker Hub | Artifact Registry |
| Public URL | `academicos-backend.onrender.com` | *(not yet provisioned)* |
| Structured data | **Supabase** (PostgREST) | **Cloud SQL** Postgres |
| Blob data | Supabase Storage | GCS *(wired for JSONB only so far — see gaps)* |
| Secrets | Render dashboard | Secret Manager |
| Pipeline | `.github/workflows/deploy-backend.yml` | `.github/workflows/deploy-gcp.yml` |
| Auth to deploy | `RENDER_API_KEY` + Docker Hub credentials | Workload Identity Federation (keyless) |
| Cold start | ~60 s, mitigated by a keep-warm ping | `min-instances=1` — no cold start |
| Status | **Live** | **Written and reviewed; never executed** |
| Runbook | `docs/deployment.md` | `docs/gcp-deployment.md`, `docs/gcp-bootstrap.md` |

### "Pure GCP" means what it says

The GCP release is not the Render release moved. It is GCP-native end to end:

- **Cloud SQL**, not Supabase — `deploy/gcp/schema.sql` defines all 11 durable
  tables; `src/academicos/assessment/postgres_kv.py` is the adapter.
- **GCS**, not Supabase Storage — `src/academicos/storage/gcs.py`.
- **Secret Manager**, not dashboard variables.
- **Keyless CI** via Workload Identity Federation — no service-account key
  exists anywhere, so there is nothing to rotate or leak.

### The one thing that is *not* yet GCP-native

Blob storage. Scan-session media and `CurriculumStore` snapshots still go
through `SupabaseStorage`. Until that is wired to GCS, **the GCP release cannot
drop its Supabase credentials** — the JSONB tables would move to Cloud SQL and
blob writes would fall back to container-local disk and be lost. This is the
blocking item before "pure GCP" is literally true, and it is recorded in
`docs/gcp-deployment.md` §8.

### They deliberately share one codebase

Store construction goes through a single factory
(`postgres_kv.durable_table`) that prefers **Cloud SQL when configured, else
Supabase, else local SQLite**. So:

- On Render, `ACOS_POSTGRES_*` is unset → behaviour is exactly as before.
- On GCP, `ACOS_POSTGRES_*` is set → Cloud SQL is used.
- Cutover and rollback are both an environment-variable change.

`GET /health/storage` reports which one is actually active
(`durability_backend`), because guessing from a dashboard is how the
2026-09-15 outage stayed invisible.

---

## 3. Build matrix (use this, not memory)

```bash
# Mobile sub-product (offline, no backend)
cd frontend && flutter build apk --release --dart-define=ACADEMICOS_OFFLINE=true

# Web sub-product against the Render release
flutter build web --release --dart-define=ACADEMICOS_API=https://academicos-backend.onrender.com/api/v1

# Web sub-product against the GCP release (same-origin: served BY Cloud Run)
flutter build web --release --dart-define=ACADEMICOS_API=/api/v1
```

A relative `ACADEMICOS_API` is only valid on Web (Dio throws on other targets),
which is what makes the same-origin Cloud Run serving work. See
`PillarApi.serverOrigin` for the matching origin fallback.

**After any `flutter build web`, before deploying it**, delete
`build/web/assets/assets/corpus/questions.json` (~6.8 MB). `pubspec.yaml`
declares it unconditionally — Flutter has no per-target conditional asset
mechanism, so every `flutter build web` bundles it even though Web never reads
it (it uses `POST /questions/search` instead; only the offline APK build's
bundled `CorpusRepository` needs the file locally). `.github/workflows/
deploy-gcp.yml` does this automatically; a manual build (e.g. for GitHub
Pages) needs the same `rm` by hand.

---

## 4. Documentation map

| Document | Scope |
|---|---|
| **This file** | Which product/release you are looking at |
| `docs/REQUIREMENTS_BY_LAYER.md` | Every requirement, split by frontend vs backend, with verification depth |
| `docs/design-system.md` + `design/tokens.json` | The design system and its machine-readable token source |
| `docs/research/ui-ux-principles.md` | The UX, habit-formation and adoption research behind it |
| `docs/research/interface-specification.md` | The interface spec: matrix row → screen, craft contract, WCAG 2.2 AA, offline truth, build order |
| `docs/research/production-ai-principles.md` | Production AI principles and this codebase's conformance, with the open gaps stated |
| `docs/notifications.md` | What may and may not be pushed to a teacher |
| `docs/research/llm-layer.md` | Where an LLM is justified in the backend, and where it is a liability |
| `docs/api.md` + `docs/api-reference.md` | Developer/contributing guide and the generated endpoint inventory |
| `contract/openapi.json` + `api-types.ts` | The frozen API contract and its generated TypeScript types |
| `docs/question-bank-api.md` | Proposal: the question bank as a standalone API asset |
| `docs/TRANSCRIPT_REQUIREMENTS_MATRIX.md` | The same requirements traced to the client transcript, by section (dated audit record) |
| `docs/deployment.md` | The **Render release**, live — pipeline, Supabase, known gaps |
| `docs/gcp-deployment.md` | The **GCP release** — architecture, cutover, costs |
| `docs/gcp-bootstrap.md` | The **GCP release** — one-time owner runbook |
| `docs/system-review.html` | Both sub-products and both releases, reviewed for a CTO |
| `AGENTS.md` | Codebase invariants; §3 covers storage/durability, §4 the two client sub-products |

If you are reading any other document and it says "the deployment" without
qualification, treat it as referring to the **Render release**, which was the
only one that existed when it was written.
