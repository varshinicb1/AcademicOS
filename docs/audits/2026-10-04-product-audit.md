# Product audit, 2026-10-04

Scope: UI dead ends and logical loopholes screen by screen; then database, caching, security, compliance;
then whether each feature works. Method: a local backend (single core, like Cloud Run) seeded with an audit
school (principal, teacher, student, parent), driven through the real API as each persona, plus the Flutter web
build driven through its semantics tree. Nothing was run against production accounts.

## 1. Fixed during the audit (merged to master)

| Finding | Evidence | PR |
|---|---|---|
| Lesson plans page: every chapter red "no approved subtopics", "Make the plan" greyed, the only way out was a tab on another console | Production screenshot | #105 |
| API-key fields in the UI (workspace card, Settings, Admin, webhooks page, legal text) | Code scan; guard test `no_api_keys_for_schools_test.dart` | #104 |
| `GET /qbank/review-queue` returned 500 whenever a model-written question carried string evidence | `api_smoke.py`, principal persona | #106 |
| A parent could not change their own password or save Guide progress (403 "can see only their children's pages") | Test fails before the fix, passes after | #107 |

## 2. UI dead ends and loopholes (fixed in the follow-up PR, 2026-10-04)

1. **Role guard.** `pageForRole` in `app_router.dart` sends a student or parent away from pages the server refuses
   them, a teacher away from `/admin`, `/owner` and `/school/grants`, and a principal away from `/owner`, to the
   role's own home. Allow-lists are pinned by `test/routing/page_for_role_test.dart`.
2. **Legacy routes.** `/syllabus`, `/planner`, `/planner/daily`, `/analytics`, `/analytics/gaps`, `/student/schedule`
   and `/parent` redirect to their v3 replacements. Pages other roles still link to (mastery, scan, evaluation,
   questions, my-schedule) are left alone.
3. **Settings.** Students and parents no longer see School branding, Classes or Manual Sync. Removed: the Notifications
   and Auto Sync toggles (nothing read either), Rate App, the dead Sync History tap, and the biometric tile on web.
4. **Setup wizard.** A school whose checklist is complete reopens on "Your school is ready", with "Change something".
5. **Duplicate requests.** `Ops.get` shares one in-flight request between identical reads; any write ends the sharing.
6. **Still unconfirmed:** typing into the Flutter login after sign-out did not register until a reload. Not reproduced
   outside the test driver; needs a human check.

## 3. Database, caching, security, compliance

Database and caching
- Cloud SQL holds 12 tables. The curriculum and operations stores are SQLite files snapshotted to one GCS object each,
  on a 30 s debounce, with `--max-instances=1`. Consequence: an instance killed inside the debounce window loses up to
  30 s of writes, and the service cannot scale out. Measured earlier: about 95 req/s at 5 users falling to 61 req/s at 60.
- The served question bank is not reproducible from committed inputs (merge and enrichment drift), so data PRs only
  append records.

Security
- Authentication: PBKDF2-SHA256 at 200k iterations, 30-day sessions. Route access is an allow-list
  (`route_policy.py`) and the route inventory test fails on an unlisted route. Good.
- **Web local-store key sits beside the data.** `secure_box_web.dart` keeps the Hive encryption key in `localStorage`,
  next to the encrypted box, so on web it is obfuscation, not protection against script running on the page.
- **CSP is `frame-ancestors 'none'` only** (`firebase.json`). There is no `script-src`, so it does not limit injected script.
  Pair this with the previous item.
- Verified present: HSTS, `nosniff`, referrer policy, `X-Frame-Options: DENY`.

Compliance (DPDP)
- Parental consent is enforced server-side, and the erasure registry (`operations/forget.py`) previews and erases a
  student across stores.
- **No automated retention.** Nothing deletes data after a period; the privacy text must not promise that it does.
- **The privacy policy text needs legal review** before it is relied on with schools.

## 4. Feature status (51 checks, local audit school)

41 PASS, 4 NOTE, 6 initial FAIL. Every FAIL was a mistake in the audit's own call, and each feature was re-checked with
the correct call and works (five in the table, homework below):

| Initial FAIL | Cause | Re-check |
|---|---|---|
| Student class schedule 422 | call omitted `start_date`/`end_date` | 200, 70 entries |
| Teacher dated lessons 422 | same | 200, 140 lessons |
| Cover substitutions "-1" | call omitted `from`/`to` | 200, 4 substitutions |
| Leave-decision notification | script expected a list; the API returns `{unreadCount, items}` | `leave_decided` present |
| Import template "people" 404 | import kinds are teachers/students/parents; export has a combined "people" | teachers template 200 |

The homework 422 was a wrong request body in the first run; homework was set, handed in, and the teacher was notified
(`homework_submitted`).

Working end to end: setup, timetable (36 cells, 0 teacher clashes, placed periods match allocation), lesson plans for
all 6 sections (153 lessons each, 3.0 s), papers from a CBSE preset and a quick paper, PDF/DOCX/answer-key/marks-sheet
export, practice set, exams, leave and cover, attendance, dashboard, term report (XLSX and PDF), report cards, import
and export templates, whole-school export, consent and erasure preview, calendar feed, notification preferences,
saved progress, and the question-bank API (401 without a key, 200 with).

Notes, not defects: e-mail delivery is not configured here (no SMTP or Composio keys), so the UI says "coming soon";
Google sign-in rejects a malformed credential with 422; a datesheet cannot be published empty (409, by design).

## 5. Suggested order

1. Retention job and an accurate privacy policy, then legal review.
2. CSP with a real `script-src`, and decide whether the web local store should hold a key at all.
3. Move the SQLite-snapshot stores to Cloud SQL before raising `--max-instances`.
