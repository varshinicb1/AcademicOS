# AGENTS.md: rules for anyone changing AcademicOS

This file is the rulebook for every contributor: people, and AI coding agents (Claude Code, Codex,
GitHub Copilot, Cursor, Gemini and the rest). Tool-specific files (`CLAUDE.md`, `GEMINI.md`,
`.github/copilot-instructions.md`, `.cursor/rules/`) point here. **Where another document disagrees with
this file, this file wins. Report the disagreement in an issue so the other file can be fixed.**

Every rule below exists because breaking it once cost real work, data or trust. Apply the reason to cases
the rule does not name.

Last reconciled: 2026-10-13, live commit `2398635`.

---

## 0. Read before you change anything

1. **This file**, all of it.
2. [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md): what to build (v3, grades 1-10). Every requirement has
   an ID (`SCH-4`, `QB-5`, ...). Use these IDs in branches, commits, PRs and code comments.
3. [`docs/handover/2026-10-07-developer-handover.md`](docs/handover/2026-10-07-developer-handover.md): what
   already exists (so you do not rebuild it), the architecture, the current plan (R-A to R-E) and its
   acceptance criteria.
4. [`CONTRIBUTING.md`](CONTRIBUTING.md): how a change reaches `master`.
5. [`docs/agent-workflow.md`](docs/agent-workflow.md): the question-bank pipeline, parallel sessions, and
   the lessons behind these rules.
6. The latest audit in [`docs/audits/`](docs/audits/), which gives every requirement's measured score and
   what holds it back.

Then search the code before you build anything. Most of what a school needs already exists.

---

## 1. Process

1. **Every change is a pull request into `master`.** Docs included, one-line fixes included.
   - **Never push to `master`.** CI deploys every push to `master` to production. A direct push is an
     unreviewed release.
   - If you push to `master` by mistake, say so in an issue at once. Do not force-push to undo it.
   - Install the guard once per clone: `git config core.hooksPath .githooks`. Its `pre-push` hook refuses
     pushes to `master`.
2. **Never merge or approve your own PR, and never deploy**, unless you are the maintainer's session. The
   maintainer (@varshinicb1) reviews, merges and deploys. CI deploys each merge.
3. **Never deploy by hand while CI works.** A hand deploy races CI and can roll production back. Hand
   deploys (`docs/deploy-by-hand.md`) happen only when CI cannot run and the owner has asked for it.
4. **One task per branch, one branch per PR**, branched from current `origin/master`:
   `git switch -c <type>/<topic> origin/master`, with `type` one of `feat`, `fix`, `docs`, `test`, `data`
   or `chore`.
   - Claim the work first: assign yourself the issue, or open a draft PR as soon as there is a commit.
     Check `gh pr list` and `gh issue list` so two people never build the same thing.
5. **Open the PR as a draft and fill in the template.**
   - Mark it ready only when both test gates pass.
   - The reviewer reads the PR, not your chat, so put the evidence there.
6. **Stage by path** (`git add <files>`). Never use `git add -A` or `git commit -a`.
   - The Flutter `generated_plugin_registrant.*`, `generated_plugins.cmake` and
     `GeneratedPluginRegistrant.swift` always show as modified. They are build noise; never commit them.
7. **Never use a bare `git stash`** (the stash is shared across worktrees). Use a WIP commit.
   - If `master` moves, merge it into your branch. Do not rebase a branch you have pushed.
8. **`release/v1` is retired.** It stopped following `master` on 2026-10-01. Do not branch from it, merge
   into it or deploy it.
9. **Keep PRs reviewable:** a few hundred changed lines, excluding generated data. Split larger work into
   PRs that each leave `master` green. Say what you left undone.

## 2. Safety, secrets and the live system

1. **No secret ever goes in the repository, an issue, a PR, a chat, a log line or a test fixture.** Keys
   live in Secret Manager (production) or `config/secrets.env` (gitignored, local).
   - Refer to secrets by name only (`acos-cfg-cron-key`), never by value.
   - If you see a secret, do not repeat it. Tell the owner it needs rotating.
2. **Checks on the live system are unauthenticated and read-only:** `/health`, `/api/v1/auth/providers`,
   that a protected route answers 401, and that public pages load without console errors.
   - **Never create an account, sign in, or enter a credential on the live site.**
   - Schools and principals are registered by the owner through invite links.
   - Signed-in flows are verified locally, on the same commit, against a fresh data root.
3. **Never run a destructive command against production:** dropping tables, deleting GCS objects,
   resetting Cloud SQL, deleting a branch someone else owns, or `--force` anything.
4. **Owner-only decisions.** Raise them in an issue and do not decide them in code:
   - prices and any commercial term;
   - messages to schools or partners;
   - deleting a school's data;
   - infrastructure and deploy changes (`deploy/`, `Dockerfile`, `firebase.json`, `.github/workflows/`);
   - the timing of a migration cutover or write freeze;
   - anything in [`docs/PRD.md`](docs/PRD.md) §12 marked open.

## 3. Students' and schools' data

1. **Every query is scoped by `school_id`, taken from the signed-in user, never from the request body.** A
   principal of one school must get 403 on everything belonging to another.
2. **Read [`docs/compliance.md`](docs/compliance.md) before touching student data, consent, grading, the
   audit log or a new data store.** It covers the DPDP Act 2023 and CERT-In; tick its boxes in the PR.
3. **Nothing about a student leaves the school's scope:**
   - not to the question-bank API;
   - not to a third party, or to an LLM with the student identified, without a DPA;
   - never into tests, screenshots, logs or documents.
4. **Every admin action is audited** (`assessment/audit_log.py`). Every route has a row in
   `api/route_policy.py` naming who may call it.

## 4. Evidence and numbers

1. **A number is measured, with the command that produced it, or it is labelled "estimated".** "Modelled
   from asset sizes" is an estimate, not a measurement.
2. **"Done" means verified on the running system**:
   - locally against real data for signed-in flows;
   - on live (`/health` reports the commit) for what is public.
   - "The code exists and its tests pass" is a different, weaker claim; say which one you mean.
3. **Scores move only through an audit** (`docs/product-scorecard-v3.md`, "How to re-score"), recorded in
   `docs/audits/`. Never edit an audit to fit a result.
4. **Do not pin counts in prose** (tests, routes, lines): they go stale within days. Re-measure.
5. **Read the whole output of a command whose failure matters.** Piping through `grep` once hid a failure.

## 5. Code: backend (`src/academicos/`, Python 3.12, FastAPI)

1. **`src/academicos/` is the product. `backend/` is an abandoned rewrite: never edit it.**
2. **Every new or changed route** needs:
   - a row in `api/route_policy.py`;
   - an entry in `tests/test_route_inventory.py`, whose count bumps in the same commit with the reason;
   - if the schema changed, a regenerated contract:
     `PYTHONPATH=src python scripts/export_openapi.py`, then
     `npx --yes openapi-typescript@latest contract/openapi.json -o contract/api-types.ts`.
3. **Request models forbid unknown fields** (`extra="forbid"`, camelCase aliases), and every web-client
   shape is held by `tests/test_frontend_backend_contract.py`.
4. **Dates are the school's local date (IST).** Use `school_today()` / `_school_today()`, never
   `date.today()` or UTC.
5. **Two stores are SQLite files saved to GCS as one snapshot** (`CurriculumStore`, `OperationsStore`), so
   Cloud Run is pinned to one instance until R-A1 moves them to Cloud SQL. Write code that stays correct
   with two instances:
   - no check-then-act ("has this run?" then run): claim atomically with
     `INSERT ... ON CONFLICT DO NOTHING` and act only if the claim succeeded;
   - no reliance on a process lock or in-memory state for correctness;
   - unique constraints behind every dedupe.
6. **Keep SQL portable.** No new `INSERT OR IGNORE/REPLACE`, `rowid`, `AUTOINCREMENT`, `instr()` or
   PRAGMAs in feature code. Use standard `ON CONFLICT`, explicit order columns and standard functions.
   Every SQLite connection keeps `journal_mode=WAL` and `busy_timeout=60000`.
7. **A changed legal or agreement text is a new version** (e.g. `pilot_agreement.VERSION`).
   Acceptances are recorded per version with a SHA-256 of the text, so the old version's record stays and
   users are asked again.
8. **External providers sit behind interfaces** (`integrations/base.py`, `llm/base.py`). Never import a
   vendor SDK in product code, and keep the core runnable offline.

## 6. Code: frontend (`frontend/`, Flutter 3.44)

1. **One codebase, four products:**
   - the web console (default);
   - the teacher app (`--dart-define=ACADEMICOS_APP=teacher`);
   - the student app (`ACADEMICOS_APP=student`);
   - the offline Android app (`ACADEMICOS_OFFLINE=true`).
   - `ACADEMICOS_OFFLINE` must never reach a web build.
   - A route change must be mirrored by hand into `frontend/lib/core/local_engine/local_api_client.dart`
     and `local_pillar_api.dart`, which throw `OfflineUnsupportedException` rather than return an empty result.
2. **No swallowed errors.** Every `catch` rethrows, throws, or shows `serverErrorMessage(e)`
   (`test/no_swallowed_errors_test.dart`).
3. **Every error the user sees says what to do next.** No internal ids, enum values or stack traces on
   screen.
4. **The design system is enforced** (`tests/test_design_tokens.py`): no emoji or symbol glyphs in
   `frontend/lib` (use an `Icon`), no raw hex colours, no off-scale spacing. The Emergera theme is the
   owner's exact brand, so do not restyle it.
5. **Every user-facing string goes through `tr()`** (`presentation/workspace/strings.dart`), with its Hindi
   entry where the screen is translated.
6. **Check every screen you change at phone width (375-390 px) and at desktop width,** and attach both
   screenshots to the PR.
7. **Caching:** only the content-hashed entry files may be cached for long
   (`tests/test_production_guard.py`). A wrong cache rule once blocked three deploys.

## 7. Curriculum and question-bank content

1. **Nothing is invented.** Chapter names come from the book's printed contents. Difficulty, Bloom level
   and marks splits come only from the source; inferred values are flagged and not used.
2. **The served bank** (`academicos-data/syllabus/questions.json`) changes only through the pipeline in
   `docs/agent-workflow.md` §5, in its own PR, with the per-record diff. **One serving gate** decides what
   is served (`corpus/bank_merge.py`): add rules inside it, never beside it.
3. **Chapter ids come from three vocabularies:**
   - the syllabus files (`academicos-data/syllabus/<Subject>_<grade>.json`);
   - the contents trees (`academicos-data/syllabus/taxonomy/`);
   - the whole-book lists (`academicos-data/syllabus/ncert_books.json`: classes 1-5 and Hindi 6-9, read
     from each book's contents page).

   Before matching chapters across them, check which one each side uses. Names differ between book
   editions.
4. **`ncert_books.json` is never regenerated from partial transcriptions.**
   `scripts/build_textbook_bank.py` merges into it and never drops a listed chapter.
5. **Lower a test floor only when the bank serves fewer questions that are all answerable,** with the
   per-record reason in the commit. Never lower one to make a test pass.
6. **CBSE owns its papers.** Every question carries its source and rights status, and AI-written items
   are served only after review (QB-5).

## 7a. Tests

1. **A bug fix starts with a test that fails without the fix.** A behaviour change comes with its test.
2. **Never skip, delete or weaken a test to get green.**
   - An `xfail` is `strict=True` and says how to un-xfail it.
   - A test whose expectation was wrong is corrected in its own commit, which says why.
3. **The gates, run one at a time on a laptop** (each is heavy; laptops have shut down under load):

   ```bash
   PYTHONPATH=$PWD/src PYTHONIOENCODING=utf-8 python -m pytest tests -q -p no:cacheprovider -p no:warnings
   cd frontend && flutter analyze && flutter test --exclude-tags live-backend
   ```

   - Use a Python 3.12 venv. Python 3.14 fails the OpenAPI contract test.
   - The bar is 0 failed and an analyzer with no issues.
   - Never edit files in a checkout while its full suite runs, and never rebuild `frontend/build/web`
     while pytest runs.
   - Paste the counts into the PR.

## 8. Brand, names and confidential material

1. **The company is VidyuthLabs, one word** (legal name: VidyuthLabs Technologies Private Limited). The
   product is AcademicOS.
2. **Confidential material never goes in this repository:**
   - contracts, MoUs, NDAs, pay or commission terms;
   - signatures;
   - school agreements;
   - anything with a personal ID number.

   Other collaborators can read the repository. Those documents stay with the owner.
3. **The letterhead and logo are the owner's locked assets.** Use them as provided; never redraw them.

## 9. Definition of done

A change is done when all of these hold:

- [ ] It does what the PR says, with the requirement ID or defect it serves.
- [ ] A test proves it, and both gates pass with the counts in the PR.
- [ ] Routes, policy, inventory and contract are updated where touched.
- [ ] Screens are checked at phone and desktop width, with screenshots.
- [ ] No secret, no student data, no confidential document and no build noise in the diff.
- [ ] Docs are updated where a rule, a route or a behaviour changed.
- [ ] Undone parts are named.
- [ ] After merge, CI deployed it and `/health` reports the commit. Only then is it live.

---

## 10. Orientation

- **Live:**
  - web console at https://vidyuthlabs.web.app (Firebase Hosting);
  - backend on Cloud Run, https://academicos-backend-2eskom55ta-el.a.run.app (`/health` gives the
    commit);
  - Cloud SQL Postgres `academicos-pg`;
  - GCS `vidyuthlabs-academicos-media`;
  - Cloud Scheduler job `acos-automations`, every 5 minutes.
- **Backend:** `src/academicos/`:
  - `api/` (app, route policy);
  - `assessment/` (papers, bank, auth, users, audit);
  - `curriculum/` (school model, calendar, timetable, plans, leave and cover, staff rules);
  - `operations/` (notifications, homework, exams, marks, automations, dashboards, pilot agreement);
  - `corpus/` and `syllabus/` (bank pipeline, syllabus, taxonomy);
  - `storage/` (blobs, snapshots, Postgres).
- **Frontend:** `frontend/lib/`: `data/` (API clients), `presentation/` (pages; the school workspace
  shared by the apps is `presentation/workspace/`), `core/` (theme, DI, offline engine).
- **Tests:** `tests/` (backend), `frontend/test/`.
- **Data:** `academicos-data/` (served bank, syllabus, taxonomy, books). Raw NCERT/CBSE PDFs are not in
  git.
- **Run locally:** `python -m academicos.cli serve --port 8010`, then
  `flutter run -d chrome --dart-define=ACADEMICOS_API=http://localhost:8010/api/v1`. Register a local
  principal with a local `ACOS_PRINCIPAL_BOOTSTRAP_KEY`.
- **Measure, don't trust prose:** `pytest --collect-only -q`, `gh run list`, `curl .../health`.
