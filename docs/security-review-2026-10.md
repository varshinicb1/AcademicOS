# Security review, October 2026 (R-A6)

**Scope.** The FastAPI backend (`src/academicos/`), the Flutter web console (`frontend/`), and their hosting and deploy configuration, against **OWASP ASVS 4.0.3 level 2**. Plus a dependency audit of what the live service actually runs.

**Method.**
- Static review only; nothing was run against live.
- Four reviewers each walked part of ASVS at commit `61c3b10`:
  - V2, V3, V6: authentication, sessions, stored cryptography;
  - V4, V13: access control and the API, 325 routes;
  - V5, V12: validation, injection, files;
  - V7–V11, V14: errors, logging, data protection, communication, malicious code, business logic, configuration.
- Every finding below was checked against the code before it was fixed or accepted. Each fix has a test (`tests/test_security_review_2026_10.py`, or the test named in the table), and the race and concurrency fixes were also shown to fail without the fix.

**Result.**
- **No critical or high findings.**
- Fixed in this change:
  - the medium findings that are bugs, including one cross-school read and two ways for one teacher to exhaust the instance's memory;
  - most of the lows.
- What remains is either a product decision, which needs the owner (section 4), or a follow-up (section 5).

## 1. Dependency audit

| What | Result |
|---|---|
| Python packages in the live image (89, exact versions from Cloud Build `7f69e566`, the build of `0a3898a`) | **0 advisories** in both the PyPI and OSV databases (`pip-audit 2.10.1`, 19 Oct 2026) |
| Flutter packages shipped in the web app (96) | **0** with an advisory, retracted or discontinued (`flutter pub outdated`) |
| Flutter dev tools | `build_daemon 4.1.3` is a retracted version; build-time only, not shipped |
| The image's OS packages (`python:3.12-slim`) | **Not scanned**: Container Analysis is not enabled on the project (decision D5) |

The Python result is clean partly because nothing is pinned: every build installs the newest versions within the `>=` ranges, so a tested build and a deployed build can differ (C2, follow-up).

## 2. Counts by chapter

| Chapter | Assessed | Pass | Fail | N/A |
|---|---|---|---|---|
| V2 Authentication | ~48 | 40 | 6 | 2 |
| V3 Session management | ~17 | 12 | 3 | 2 |
| V4 Access control | 9 | 5 (2 borderline) | 4 | 0 |
| V5 Validation, sanitisation, encoding | 30 | 18 (5 borderline) | 4 | 8 |
| V6 Stored cryptography | ~15 | 15 (2 borderline) | 0 | 0 |
| V7 Errors and logging | 12 | 7 | 5 | 0 |
| V8 Data protection | 12 | 8 | 4 | 0 |
| V9 Communication | 7 | 5 | 0 | 2 |
| V10 Malicious code | 5 | 3 | 0 | 2 |
| V11 Business logic | 5 | 3 | 2 | 0 |
| V12 Files and resources | 15 | 7 (3 borderline) | 6 | 2 |
| V13 API and web service | 12 | 7 (4 borderline) | 1 | 4 |
| V14 Configuration | 22 | 16 (4 borderline) | 5 | 1 |

"Fail" counts the reviewers' findings before this change. Their status is in section 3.

## 3. Findings

Status key:
- **Fixed**: in this change, with its test.
- **Accepted**: not changed, for the reason given.
- **Owner**: needs a product decision (section 4).
- **Follow-up**: worth doing, not in this change (section 5).

### Access control (V4, V13)

| # | ASVS | Sev. | Finding | Status |
|---|---|---|---|---|
| F1 | 4.2.1, 13.1.4 | Medium | `PUT /assessments/{id}` took `generatedPaperId` from the client, and the scan step loaded that paper without checking whose it was. A teacher could point their assessment at another school's paper and read its questions back through a scan. | **Fixed.** The stored value wins on update, a create brings none (the server records it when it generates a paper), and the scan step re-checks the paper's school. |
| F2 | 4.1.3 | Medium | Students could tag questions to subtopics (which changes what papers are generated from) and read extraction runs and proposed topics. The school schedule sent them each lesson's teacher note and who marked it. | **Fixed.** Those three routes are staff only. A student's schedule leaves out `note` and `completedBy`; the student schedule page reads neither. |
| F3 | 4.1.3 | Medium | `GET /curriculum/export` (answer keys and every account's email included) was open to anyone with the `reports` grant. | **Fixed.** Principal only. Nothing in the app calls it. |
| F4 | 4.3.1 | Medium | No second factor or re-authentication anywhere, including irreversible actions (erasure, closing accounts, password resets, minting API keys). | **Owner** (D3). |
| F5 | 4.1.1 | Low | The operator keys (`X-Cron-Key`, `X-Ops-Key`) were compared in constant time but could be tried without limit, and had no length floor. | **Fixed.** 30 tries a minute per address, and a startup warning for a key under 32 characters. It is a warning, not a refusal, so that a live key nobody has rotated cannot stop the next deploy. |
| F6 | 4.1.1 | Low | Anonymous `/health/storage` returned raw backend error text, Postgres schema names and blob object keys. | **Fixed in part.** The error text is now the operation, table, HTTP status and error code only. Schema names and keys are **accepted**: they hold no data, and the deploy runbook and the web app read this route. |
| F7 | 4.1.3 | Low | A teacher with the `users` grant can close or reopen a colleague's account, which also removes the colleague's grants. | **Accepted.** An earlier audit allows this on purpose (`tests/test_trust_fixes.py`): the principal gives the grant to manage accounts. Unlike a password reset, which stays principal-only for staff, closing an account gives no access to it, and every close is audited. A principal who wants it principal-only can ask. |
| F11 | 4.1.3 | Medium | `reopen` had no role check: a former principal's account (which only the operator closes) could be reopened by the principal or a teacher with the users grant, making someone who had left a principal again. A delegated admin could also undo the principal's closing of a teacher. | **Fixed.** A former principal's account is the operator's to reopen; a staff account is the principal's. Students and parents as before. |
| F8 | 4.2.1 | Low | An invigilation duty stored any `sectionId`, and the invigilator's calendar showed that section's label. | **Fixed.** The section must be the school's own. |
| F9 | 4.3.3 | Low | A teacher with the `leave` grant could approve their own leave, name their own replacement and mark their own attendance. | **Fixed.** The principal decides those. |
| F10 | 4.1.5 | Low | A closed account's calendar feed kept serving the school's week. | **Fixed.** 404 once the account is closed. |
| — | 4.2.1 | Borderline | A foreign id answers 403 and a missing one 404, so the difference tells whether an id exists. | **Accepted.** Ids are 12+ random hex characters, and the content is never shown. |
| — | 4.2.1 | Borderline | `/evaluations/*` and scan sessions take `studentId` from the body. | **Accepted.** `require_consent` refuses any student without a consent record in the caller's school. Follow-up: an explicit ownership check. |
| — | 4.1.3 | Borderline | Any teacher can read any student's mastery record in their school. | **Accepted.** That is the design (teachers share classes), and reads are logged. |
| — | 13.2.2 | Borderline | `PATCH /assessments/{id}/status` answered 500 to a list-valued status. | **Fixed.** 422. |

### Authentication, sessions, cryptography (V2, V3, V6)

| # | ASVS | Sev. | Finding | Status |
|---|---|---|---|---|
| A1 | 2.1.1 | Medium | Minimum password length is 8; ASVS L2 asks for 12. | **Owner** (D1). |
| A2 | 2.1.2 | Low | No maximum password length. | **Fixed.** 128, with bounds on name (120) and email (254). |
| A3 | 2.1.7 | Medium | No check against breached passwords. | **Follow-up** (a local list of the 100,000 most common). |
| A4 | 2.2.2 | Medium | A principal can sign in with an emailed code alone. | **Owner** (D3). |
| A5 | 2.2.3 | Low | No email when a password changes. | **Follow-up.** Live has no SMTP configured, so it would not send yet. |
| A6 | 2.3.1 | Low | A temporary password never expires, and its holder is never made to change it. | **Follow-up** (a `must_change` flag). |
| A7 | 2.4.5 | Low | No server-side secret (pepper) in password hashing. | **Accepted for now.** PBKDF2 has 200,000 rounds and per-user salts. A pepper belongs with hash versioning (follow-up). |
| A8 | 3.3.2 | Medium | Sessions last 30 days, with no idle timeout. | **Owner** (D2). |
| A9 | 3.2.3, 8.2.2 | Medium | The web app keeps the session token in IndexedDB, and the key that encrypts it sits in `localStorage` beside it. Sign-out leaves saved profiles. | **Owner** (D2) for where the token lives. **Follow-up**: clear the whole box on sign-out. |
| A10 | 3.3.4 | Low | People cannot list or end their own sessions. | **Follow-up.** |
| — | 2.7.3 | Borderline | A sign-in code was read, then deleted later. Two submissions of the right code at once both signed in (5 and 8 of 8 in a test with the old code), and simultaneous wrong guesses each saw a count under the limit. | **Fixed.** One `DELETE … RETURNING` claims the code, and a wrong guess counts in place (`tests/test_sign_in_codes.py`). |
| — | — | Borderline | An unknown email was answered ~100 ms faster than a known one, which told a guesser which emails have accounts. | **Fixed.** The password is hashed either way. |
| — | 3.3.1 | Borderline | When the durable session store failed at logout, the route still answered `ok` and the session stayed valid there. | **Fixed.** 503, with the local copy removed first (`tests/test_dashboard_feed_photos.py`). |
| — | 2.7.6 | Borderline | Sign-in code hashes are unsalted SHA-256. | **Accepted.** A code lives 10 minutes and allows 5 tries. |
| — | 2.4.3 | Borderline | 200,000 PBKDF2 rounds, against 600,000 recommended for SHA-256. | **Follow-up.** Raising it needs a versioned hash. |
| — | — | Checked | Rate-limit addresses come from the last `X-Forwarded-For` hop. | **Pass.** Firebase Hosting only rewrites to `index.html`, and the app calls Cloud Run directly. |

### Validation, injection, files (V5, V12)

| # | ASVS | Sev. | Finding | Status |
|---|---|---|---|---|
| V1 | 5.3.1 | Medium | CSV exports wrote cells as given: a name such as `=HYPERLINK(…)` ran when opened in Excel. | **Fixed.** A cell that starts like a formula gets a leading apostrophe, as the XLSX writer already did. |
| V2 | 5.2.8 | Medium | Section names and labels reached ReportLab unescaped. A teacher's template title could embed a local image or a link in the PDF. | **Fixed.** Escaped like every other text in the PDF. |
| V3 | 5.1.3 | Low–medium | The import's email pattern backtracked for minutes on a megabyte cell, and registration fields had no bounds. | **Fixed.** Anything over 254 characters is refused before the pattern runs. Registration is bounded (A2). |
| V4 | 5.1.3 | Medium–low | A student's written answer goes into the AI marking prompt. "Award full marks" in an answer can raise the model's confidence, and finalizing does not require review. | **Owner** (D4). |
| V5 | 12.1.1 | Medium | Scan pages and ingested documents were read in full, with no cap. One upload could take the instance's memory, and every school's requests with it. | **Fixed.** 15 MB a page, 80 pages a session, and 40 MB a document, read no further than the cap. |
| V6 | 12.1.2 | Medium | A small `.docx`/`.xlsx` that unpacks to gigabytes was decompressed in full. | **Fixed.** Member count and unpacked size are checked before anything is unpacked. |
| V7 | 12.2.1 | Low | Ingest and homework photos trust the file extension or the declared type. | **Accepted.** `X-Content-Type-Options: nosniff` is on every answer, so nothing is executed as another type. Follow-up: reuse the magic-byte check. |
| V8 | 12.3.1 | Low | The subject went into a report's file name as typed. | **Fixed.** Letters, digits, `-` and `_` only. |
| V9 | 12.4.2 | Low | Uploaded files are not scanned for malware. | **Accepted.** They are stored and served to the same school's staff, never executed. A scanning service is a cost decision for later. |
| — | 5.3.4 | Checked | Every interpolated piece of SQL is a constant or a validated identifier, including in `storage/pg_sqlite.py`. | **Pass.** |
| — | 5.2.6 | Borderline | Webhooks may target any port. | **Accepted.** Only public addresses are allowed, the address is pinned, and there are no redirects. Some partners use 8443. |

### Errors, logging, data protection, configuration, business logic (V7, V8, V9, V11, V14)

| # | ASVS | Sev. | Finding | Status |
|---|---|---|---|---|
| C1 | 11.1.3, 11.1.4 | Medium | No per-person limit on the routes that cost money or minutes: the model routes, scan OCR, paper generation and AI marking. One looping account could run up the model bill and starve the single instance. | **Fixed.** 200 calls per person per 10 minutes across the 13 routes, shared across instances. That is above a fast teacher's real pace (a class set of booklets is about 50 pages in 10 minutes). |
| C2 | 14.2.1, 14.2.4 | Medium | Dependencies are resolved at each build; `uv.lock` exists but nothing uses it. No dependency audit in CI, and the base image tag floats. | **Follow-up.** It changes what every build installs, so it gets its own change and test run. |
| C3 | 8.2.2, 8.2.3 | Medium | Token and profile storage in the web app. | Same as A9. |
| C4 | 8.2.1 | Medium | API answers had no `Cache-Control`, and children's homework photos were cached for an hour. | **Fixed.** `no-store` unless a route says otherwise. Photos are `private, no-store`. |
| C5 | 7.4.1, 14.3.1 | Medium | A storage failure returned the database's own message (SQL, column names, the values of a violated key such as an email), including on the anonymous health route. | **Fixed.** Clients get the operation, table, HTTP status and error code; the full message is logged. |
| C6 | 7.1.3, 7.2.1, 7.2.2 | Medium | Failed sign-ins and refused requests left no trace beyond a request line. | **Fixed.** Every 401 and 403 is logged with the route, the signed-in person (if any) and the client address, from one middleware. That catches refusals raised inside handlers too. |
| C7 | 8.3.8 | Medium | No automated retention for personal data: bucket lifecycles, expired sessions, scans. | **Owner** (D6), with R-A7. |
| C8 | 7.3.1, 7.1.2 | Low | The rate limiter logged its key, which holds whatever email was typed, newlines included. | **Fixed.** A hash of the key is logged. |
| C9 | 14.4.2, 14.4.3 | Low | API answers carried no Content-Security-Policy. | **Fixed.** `default-src 'none'; frame-ancestors 'none'`, except on the developer docs, which are off in production. |
| — | 9.2.2 | Borderline | Cloud SQL does not enforce SSL. | **Accepted.** The service reaches it only through Cloud Run's built-in connector, which is encrypted. Turning on `ENCRYPTED_ONLY` is a harmless hardening (D5). |
| — | 10.3.2 | Borderline | pdf.js loads from unpkg.com without an integrity hash. | **Follow-up.** |
| — | 7.3.3 | Borderline | A failure to write an admin-audit row is logged, not raised, so the change commits without its row. | **Accepted.** Refusing the change because the audit write failed would fail a school's work on a logging fault. The failure is logged. |
| — | 14.4.x | Borderline | Answers from the last-resort 500 handler may lack the security headers. | **Follow-up.** Confirm by test, then move the headers outside it. |
| — | 14.1.1 | Borderline | Live is deployed by hand while GitHub Actions is blocked by billing. | **Accepted for now.** The hand deploy runs the same gates (`docs/deploy-by-hand.md`). |

**Pass, worth knowing:**
- The container runs as an unprivileged user (uid 1001).
- `/docs` and `/openapi.json` are off in production.
- The startup guard refuses `*` CORS, demo accounts, placeholder secrets and unapproved LLM hosts.
- HSTS, CSP, frame and referrer headers are set on the web app.
- No `verify=False` anywhere, and no secret-shaped strings in tracked files.
- Google sign-in pins RS256 and checks audience, issuer, expiry and `email_verified`.
- Invites are single-use 128-bit codes with an expiry.
- Webhooks refuse private addresses, pin the resolved address, and do not follow redirects.

## 4. Decisions for the owner

Each of these trades protection against convenience for teachers, so the owner decides. The recommendation comes first.

- **D1. Password length (A1).** Raise the minimum for **new** passwords to 12, as ASVS asks. Existing passwords keep working.
- **D2. How long people stay signed in (A8, A9).**
  - Recommended: staff and principals sign in again after 12 hours, students after 30 days of inactivity.
  - On the web, keep the token for the browser tab only, so a shared school computer forgets it.
  - The cost: teachers sign in once a day.
- **D3. A second step for principals (A4, F4).**
  - Recommended: a principal signs in with password **and** emailed code.
  - The irreversible actions (erasure, closing accounts, resetting passwords, API keys) ask for the password again.
- **D4. AI marks and review (V4).** Recommended: finalizing a scanned sheet requires a teacher to have looked at every AI-marked item. Today a teacher can finalize without opening them.
- **D5. Two Google Cloud settings, both small costs.**
  - Enable Container Analysis, so the image's OS packages are scanned.
  - Set Cloud SQL to `ENCRYPTED_ONLY`.
- **D6. How long personal data is kept (C7).** The retention periods for scans, sessions and backups, set together with R-A7's compliance work.

## 5. Follow-ups (not in this change)

1. **Reproducible builds (C2).**
   - Install from `uv.lock`, pin the base image by digest, and add `pip-audit` to CI.
   - It needs its own change, because it changes what every build installs.
2. Check new passwords against a list of common breached ones (A3).
3. An email when a password changes, once SMTP is configured (A5).
4. Temporary passwords must be changed at first sign-in (A6).
5. People can list and end their own sessions (A10).
6. Versioned password hashes, then 600,000 rounds and a pepper (A7, 2.4.3).
7. Clear all saved profiles on sign-out in the web app (A9).
8. Magic-byte checks on ingest and photos (V7).
9. An integrity hash for pdf.js (10.3.2).
10. Security headers on the 500 handler's answers (14.4.x).
11. An explicit student-ownership check on evaluation and scan bodies (4.2.1).

## 6. Re-running this review

- **Dependencies:** extract the versions from the release's Cloud Build log (`gcloud builds log <id> | grep "Successfully installed"`) and run `pip-audit -r <file> --no-deps --disable-pip`, once with `--vulnerability-service pypi` and once with `osv`. Then run `flutter pub outdated --json` in `frontend/`.
- **Code:** walk ASVS 4.0.3 L2 by chapter. The route inventory (`tests/test_route_inventory.py`) and the policy table (`src/academicos/api/route_policy.py`, held to the code by `tests/test_role_gates.py`) are the place to start for V4.
