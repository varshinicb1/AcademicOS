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

## 2. UI dead ends and loopholes still open

1. **No role guard in the router.** `authRedirect` only redirects `/home` by role. A student or parent who types an
   admin URL reaches the screen and then meets 403s on every call, with no explanation. The API is correct
   (it refuses); the UI should send them home.
2. **Legacy routes still reachable.** The offline/unknown-role nav list in `shell.dart` still lists legacy routes that
   the role-based navigation no longer shows. They should redirect, as `legacyCreateRedirect` already does for one.
3. **Settings tiles that lead nowhere useful** for some roles (School branding, Classes, Notifications, Biometric).
   Show only what the signed-in role can use.
4. **Setup wizard has no completion state.** The checklist (`setup-status`) knows every step is done; the wizard
   does not say so or step aside.
5. **Duplicate requests.** Several screens fire the same GET twice on first load. Harmless, but it doubles load on a
   single-instance backend.
6. **Unconfirmed:** typing into the Flutter login after sign-out did not register until a page reload. Could be the
   test driver or a real focus bug; needs a human check.

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

41 PASS, 5 NOTE, 5 initial FAIL. Every FAIL was a mistake in the audit's own call, and each feature was re-checked with
the correct call and works:

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

1. Router role guard and legacy-route redirects (items 1 and 2): small, removes the most confusing screens.
2. Retention job and an accurate privacy policy, then legal review.
3. CSP with a real `script-src`, and decide whether the web local store should hold a key at all.
4. Settings tiles, wizard completion state, request de-dupe.
5. Move the SQLite-snapshot stores to Cloud SQL before raising `--max-instances`.
