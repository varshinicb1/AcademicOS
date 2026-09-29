# Deploying the web release by hand

A push to `master` that touches a shipped path deploys through `.github/workflows/deploy-gcp.yml`.
**CI runs again since 2026-09-28**: the merge of #8 (`e0d7d63`) ran the Python suite, built the
image and deployed Cloud Run by itself, but skipped Hosting: its unpinned Flutter (3.47.5) failed the
analyzer. #10 pinned the workflow to 3.44.9, and its merge (`7e4b595`, run 36476002768) deployed both
halves by itself: tests, Cloud Run, the Flutter checks and Hosting, with a web bundle byte-identical to
the hand build of the same code (`main.dart.b24cfe4b829b.js`). **CI is the normal path again.** This
runbook is the fallback when a CI job cannot run; after a CI deploy, still do the checks in section 6.
The owner authorised hand deploys on 2026-09-23.

CI is the gate normally. By hand, **you** are the gate: run both suites, and
verify the live commit afterwards. Do not skip the verification — `/health` alone
cannot see a stale web bundle, and this project has shipped one before.

Only the maintainer deploys, and only a merged `master` (`CONTRIBUTING.md` §5). Everything runs from
the `AcademicOS-release` worktree (branch `release/v1`), after
`git fetch origin && git switch release/v1 && git merge --ff-only origin/master`, so the deployed tree
is exactly `master`.
Nothing here needs a secret on your machine: the secrets are bound from Secret
Manager by name. Never paste a key into a command, a file or a commit.

## 1. Gate

    PYTHONPATH=$PWD/src PYTHONIOENCODING=utf-8 D:/AcademicOS-venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider
    cd frontend && flutter analyze --no-fatal-infos && flutter test --exclude-tags live-backend -j 1

Last green at `e0d7d63` (2026-09-28): 3,832 passed / 112 skipped / 3 xfailed;
479 Flutter tests passed; analyzer at 7 info-level notes (Flutter 3.44.9). A number lower than
that is a regression until you can say which tests went and why.

Do not rebuild `frontend/build/web` while the Python suite runs. `api/main.py`
mounts that directory when it exists at import, so a rebuild's `rm -rf` mid-run
fails `test_unknown_route_404_without_startup` with "StaticFiles directory ...
does not exist" (2026-09-26). Build the web app before or after the suite.

If nothing under `frontend/` changed since the live commit
(`git diff --name-only <live-sha> HEAD -- frontend` is empty), the web bundle
does not need rebuilding: deploy the backend only and skip steps 4-5.

## 2. Backend image (Cloud Build)

    SHA=$(git rev-parse HEAD)
    gcloud builds submit --project vidyuthlabs --config deploy/gcp/cloudbuild.yaml \
      --substitutions=_IMAGE="asia-south1-docker.pkg.dev/vidyuthlabs/academicos/backend",_COMMIT_SHA=$SHA,_BUILT_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)" .

## 3. Cloud Run

    SECRETS="ACOS_PRINCIPAL_BOOTSTRAP_KEY=principal-bootstrap-key:latest,ACOS_POSTGRES_PASSWORD=postgres-password:latest,ACOS_LLM_API_KEY=acos-llm-api-key:latest,SARVAM_API_KEY=acos-llm-api-key:latest"
    ENV_VARS="ACOS_ENV=production@ACOS_POSTGRES_HOST=/cloudsql/vidyuthlabs:asia-south1:academicos-pg@ACOS_POSTGRES_DB=academicos@ACOS_POSTGRES_USER=academicos@ACOS_GCS_BUCKET=vidyuthlabs-academicos-media@ACOS_CORS_ORIGINS=https://vidyuthlabs.web.app,https://vidyuthlabs.firebaseapp.com@ACOS_LLM_BASE_URL=https://api.sarvam.ai"
    gcloud run deploy academicos-backend --project vidyuthlabs --region asia-south1 \
      --image "asia-south1-docker.pkg.dev/vidyuthlabs/academicos/backend:$SHA" \
      --platform=managed --allow-unauthenticated --port=8080 --cpu=1 --memory=1Gi \
      --concurrency=40 --timeout=300 --min-instances=1 --max-instances=1 --cpu-boost \
      --add-cloudsql-instances vidyuthlabs:asia-south1:academicos-pg \
      --service-account academicos-runtime@vidyuthlabs.iam.gserviceaccount.com \
      --set-secrets "$SECRETS" --set-env-vars "^@^$ENV_VARS" --quiet

The `^@^` delimiter matters: `ACOS_CORS_ORIGINS` contains a comma, and the
default split turns it into a bad dict entry, which stops the revision starting.

## 4. Web app — rebuild it, never ship `build/web` as found

    cd frontend
    rm -rf build/web        # a local http.server serving it holds the directory; stop that first
    flutter build web --release --dart-define=ACADEMICOS_API="https://academicos-backend-2eskom55ta-el.a.run.app/api/v1"
    rm -f build/web/assets/assets/corpus/questions.json    # 15 MB offline-only bank; the web never reads it
    cd .. && python scripts/web_cache_bust.py frontend/build/web   # content-hashed entry names

Flutter writes `main.dart.js` and `flutter_bootstrap.js` under the same names
every build. The last command renames them `main.dart.<hash>.js` and
`flutter_bootstrap.<hash>.js` and points `index.html` (never cached) at them.
firebase.json caches exactly that name shape `immutable` for a year and
revalidates everything else, so a returning browser downloads the app only
after a deploy (D29), and a new build is a new name it has never cached. If you
skip the script the plain names ship `no-cache`: slow, never stale. It fails
loudly if Flutter's output changes shape; do not deploy past that.

## 5. Firebase Hosting

    FIREBASE_TOKEN="$(gcloud auth print-access-token)" GOOGLE_CLOUD_QUOTA_PROJECT=vidyuthlabs \
      npx --yes firebase-tools@13 deploy --only hosting --project vidyuthlabs --non-interactive

Pin **firebase-tools@13**. v15 ignores `FIREBASE_TOKEN`, falls back to
Application Default Credentials (which the dev machine does not have), and fails
with "Failed to get Firebase project" — which reads like a permission problem and
is not. The deploy writes a `.firebase/` cache; it is gitignored.

## 6. Verify — all four, every time

    BACKEND=https://academicos-backend-2eskom55ta-el.a.run.app
    curl -s $BACKEND/health                     # "commit" must equal the SHA you built
    curl -s $BACKEND/health/storage             # ok / cloudsql / gcs
    MAIN=$(ls frontend/build/web | grep -E '^main\.dart\.[0-9a-f]{12}\.js$')
    curl -s https://vidyuthlabs.web.app/$MAIN | wc -c          # equals frontend/build/web/$MAIN byte for byte
    curl -sI https://vidyuthlabs.web.app/$MAIN | grep -i cache-control   # public, max-age=31536000, immutable
    curl -s "$BACKEND/api/v1/catalog"           # per class x subject counts equal the local served bank

A 200 on `/assets/assets/corpus/questions.json` is NOT the asset: the SPA
rewrite returns `index.html` for unknown paths. Check the Content-Type. The same
goes for `/main.dart.js` since D29: the plain name is no longer uploaded, so it
answers with `index.html`.

Under CanvasKit, `document.fonts` is always empty, so it proves nothing about
whether a font loaded. Check the network log for the font request instead.

## Live history

| Date | Commit | What |
|---|---|---|
| 2026-09-23 | `e025bb7` | value points, chapter view, tagger fix, principal insights card |
| 2026-09-24 | `86f8711` | calendar terms, book editions, class setup, subtopic picker |
| 2026-09-24 | `5375af1` | one serving gate for the bank; catalog 5,429 |
| 2026-09-26 | `3197f4e` | Task 126 review fixes, bank health report fixes, these docs. Backend only (frontend unchanged; bundle 5,539,687 bytes both sides). Gate 3,611 passed / 113 skipped / 8 xfailed. Catalog 5,426: Informatics Practices 12 is 29 against the file's 32 -- the three `PENDING_REBUILD` records the gate now refuses; every class 6-10 pair equals the file |
| 2026-09-27 | `3219702` | time saved counts every generation path; the app is no longer cached `immutable`; entry URLs carry a content hash (`flutter_bootstrap.js?v=7b1ce8b13f27`, `main.dart.js?v=55ed9c781cee`). Backend and web. Gate 3,622 passed / 113 skipped / 8 xfailed. Live: `Cache-Control: no-cache` on the entry files, bundle 5,539,687 bytes both sides, catalog unchanged (5,426), `/paper-timing` 401 unauthenticated, and a fresh browser loaded `main.dart.js?v=55ed9c781cee` with no console errors |
| 2026-09-27 | `8db6636` | exam coverage and time saved per term with the principal's baseline (route 163); a chosen chapter reaches what the picker counts (2,297 of 2,297). Backend and web. Gate 3,645 passed / 113 skipped / 8 xfailed; Flutter 381. Live: `/health` 8db6636, storage ok, bundle 5,546,482 bytes both sides, `/paper-timing` and the baseline route 401 unauthenticated, catalog 5,426 unchanged. A browser that had loaded the previous build fetched `main.dart.js?v=0a164747aba1` on its next visit with no console errors -- the cache-bust working on a returning browser |
| 2026-09-27 | `caf5e3d` | Task 125: one competency rule, the share and the tier sentence on the builder's chapters step, edited papers recount their sentences, bank health competency section, /assessment/create -> builder on the web. Backend and web. Gate 3,736 passed / 113 skipped / 8 xfailed; Flutter 386; analyze 7 info. Live: `/health` caf5e3d, storage ok, bundle 5,548,646 bytes both sides, hashed entry URLs match, catalog 5,426 unchanged, the availability route 401 unauthenticated, and a fresh browser loaded `main.dart.js?v=a02995a0915f` with no console errors |
| 2026-09-28 | `09649eb` | M0: /v1 and MCP file chapters like the builder (D39); entry files cached a year under content-hashed names (D29); classes 6-10 and stocked subjects only (D22, D40); a paper keeps its competency sentences, one share format (D78, D79); terms and class setup on the web (D27); the fidelity rebuild, 5,429 -> 5,319 served (D20, D21, D26, D31, D36, D45, D54, D74, D76, D77). Backend and web. Gate 3,795 passed / 112 skipped / 8 xfailed; Flutter 403 passed; analyze 7 info. Live: `/health` 09649eb, storage ok (cloudsql, gcs), bundle `main.dart.aa6fb69bb2f8.js` 5,572,517 bytes both sides and cached `public, max-age=31536000, immutable`, `index.html` no-cache naming `flutter_bootstrap.b25987820cdf.js`, plain `/main.dart.js` now the SPA page, catalog 5,319 equal to the local bank on all 68 pairs (classes 6-10: 33 pairs, 4,826), terms and `/v1` routes 401 unauthenticated; in a browser the first visit transferred 1,145,574 B for the app and the second 0 B, no console errors |
| 2026-09-28 | `e50d250` | PRs #1-#6, the first release through pull requests: unscorable answers (a scheme with no keyword or no marking point) go to teacher review instead of a confident 0, in the backend's evaluator and the offline engine (#1); the decomposition exporter says why a chapter has no template (#2); the offline build makes no request until sync is on, and Settings loses the unused Server URL field and its `localhost:8000` default (#3, D15). Backend and web. Gate in this worktree: 3,805 passed / 112 skipped / 3 xfailed; Flutter 468 passed; analyze 7 info. Cloud Build `024a3080` SUCCESS; Cloud Run revision `academicos-backend-00018-k45` at 100%. Live: `/health` e50d250 (built 2026-09-28T16:19:44Z), storage ok (13/13 tables, cloudsql), bundle `main.dart.81ffd976c2d7.js` 5,570,739 bytes both sides and byte-identical, cached `public, max-age=31536000, immutable`; `flutter_bootstrap.57764beda079.js` byte-identical and named by `index.html` (`no-cache, no-store, must-revalidate`); the bundle holds `ACADEMICOS_OFFLINE` and `localhost:8000` 0 times; catalog 5,319 equal to the local bank on all 68 pairs (classes 6-10: 33 pairs, 4,826). A fresh browser loaded `main.dart.81ffd976c2d7.js` (1,144,906 B transferred) and reached sign-in with 0 console errors |
| 2026-09-28 | `e0d7d63` | M1.1 sections (#8, by @bahumanyarg11): Section rows, enrollment by section, 5 routes (163 -> 168), the Sections card and sections per class in setup. Backend by CI (run 36460457019: tests passed, Cloud Build `43977a0a`, revision `00019-xnt`, /health verified; its Flutter analyze failed on 3.47.5, so Hosting was skipped), then by hand (revision `00020-9g2`, the same image digest) and the web by hand. Gate in this worktree: 3,832 passed / 112 skipped / 3 xfailed; Flutter 479 passed; analyze 7 info. **Migration:** a dry run on a copy of the live curriculum snapshot (0 years, 0 grades, 0 enrollments) added the empty `sections` table and `section_id` column only; after the deploy the snapshot's GCS generation is unchanged (1790099962376437), so starting did not upload it. Live: `/health` e0d7d63, storage ok (13/13, cloudsql + gcs), bundle `main.dart.b24cfe4b829b.js` 5,620,231 bytes byte-identical and `immutable`, `flutter_bootstrap.a71df9a948ff.js` byte-identical and named by `index.html`, catalog 5,319 equal to the local bank on 68/68 pairs, the sections routes 401 unauthenticated and in the live OpenAPI; a fresh browser loaded the new bundle (1,153,477 B) and reached sign-in with 0 console errors |
| 2026-09-29 | `aa85cae` | PRs #16-#25: notifications (inbox, push, email, quiet hours), homework, learning progress, parents and guardians, CSV import/export, question-bank API key issuance with a durable key store (D38), teacher attendance, scheduled automations, paper review, marks entry and analysis, exam datesheet and invigilation. **Backend only** (no `frontend/` change since the live bundle). GitHub Actions refused every job for account billing, so by hand. Gate: 4,049 passed / 113 skipped / 3 xfailed on the stack head `83a2c25`, whose tree equals `aa85cae`. Cloud Build `72f61c55` SUCCESS; revision `academicos-backend-00025-v6f` at 100%. Live: `/health` aa85cae (built 2026-09-29T04:50:04Z), storage ok, catalog 5,319 unchanged, the new routes 401 unauthenticated, live OpenAPI 264 operations. The operations and API-key stores start empty on first boot (`allow_empty_boot`) |
| 2026-09-29 | `2fc1771` | PRs #26-#32: delegated admin (78 principal routes behind capability grants), the web **School** tab for every role (homework, progress, parents, cover and attendance, exams, reviews, marks entry, import/export, API keys, staff permissions, notifications) and the teacher/student app builds, the principal dashboard, calendar feeds, `/v1/homework-sets`, photos of written homework, self-practice, class progress, principal alerts, leave and lessons on My day, Hindi for the School pages, offline reads. **Backend and web**, by hand (Actions blocked by billing). Gate: Python 4,073 passed / 113 skipped / 3 xfailed at `d7eb17f` (the Python tree of `2fc1771`); Flutter 491 passed and analyze 7 info at `a596c32` (`2fc1771`'s tree). Cloud Build `f19d6bd4` SUCCESS; revision `academicos-backend-00026-jbw` at 100%. Live: `/health` 2fc1771 (built 2026-09-29T06:25:31Z), storage ok (cloudsql), bundle `main.dart.8c85fbd046d9.js` 5,942,537 bytes byte-identical and `immutable`, `index.html` `no-cache` naming `flutter_bootstrap.e9a11f3e1943.js`, the bundle holds `ACADEMICOS_OFFLINE` and `localhost:8000` 0 times, catalog 5,319 unchanged, live OpenAPI 284 operations, the new routes 401 unauthenticated; a fresh browser loaded the new bundle and reached sign-in with 0 console errors |

Update this table with every hand deploy.
