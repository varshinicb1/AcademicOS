# Deploying the web release by hand

Normally a push to `master` deploys through `.github/workflows/deploy-gcp.yml`.
**GitHub Actions minutes are exhausted until 2026-10-01**, so every run fails at
runner start and nothing deploys. The user authorised deploying from the
development machine on 2026-09-23. Delete this paragraph once CI runs again, and
go back to letting CI deploy.

CI is the gate normally. By hand, **you** are the gate: run both suites, and
verify the live commit afterwards. Do not skip the verification — `/health` alone
cannot see a stale web bundle, and this project has shipped one before.

Everything runs from the `AcademicOS-release` worktree (branch `release/v1`).
Nothing here needs a secret on your machine: the secrets are bound from Secret
Manager by name. Never paste a key into a command, a file or a commit.

## 1. Gate

    PYTHONPATH=$PWD/src PYTHONIOENCODING=utf-8 D:/AcademicOS-venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider
    cd frontend && flutter analyze --no-fatal-infos && flutter test --exclude-tags live-backend -j 1

Last green at `5375af1` (2026-09-24): 3,589 passed / 113 skipped / 8 xfailed;
373 Flutter tests passed; analyzer at 7 info-level notes. A number lower than
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
    cd .. && python scripts/web_cache_bust.py frontend/build/web   # content-hashed entry URLs

Flutter writes `main.dart.js` and `flutter_bootstrap.js` under the same names
every build. The last command makes `index.html` (never cached) load both through
`?v=<content hash>` URLs, so a browser that cached an older build fetches this
one. It fails loudly if Flutter's output changes shape; do not deploy past that.

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
    curl -s https://vidyuthlabs.web.app/main.dart.js | wc -c   # equals build/web/main.dart.js byte for byte
    curl -s "$BACKEND/api/v1/catalog"           # per class x subject counts equal the local served bank

A 200 on `/assets/assets/corpus/questions.json` is NOT the asset: the SPA
rewrite returns `index.html` for unknown paths. Check the Content-Type.

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

Update this table with every hand deploy.
