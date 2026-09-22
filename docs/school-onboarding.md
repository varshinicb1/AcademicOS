# School onboarding — from an empty project to a principal logged in

The operator's runbook for putting one school on the GCP release (Cloud Run +
Cloud SQL + GCS + Firebase Hosting, region `asia-south1`). For vidyuthlabs
the web app is <https://vidyuthlabs.web.app>. Written against the code on
`feat/product-gcp` as of 2026-09-22.

Steps that depend on work in another stream carry that stream's task number,
e.g. **[Task 301]**. Until that task is merged, the step as written does not
work yet; the "today" note under it says what does.

Related: `docs/gcp-bootstrap.md` (the account owner's one-time job),
`docs/gcp-deployment.md` (the release in depth), `docs/compliance.md` (read
before touching student data), `docs/dpa-template.md` (the agreement the
school signs).

---

## 0. Before anything: the agreement

The school signs the DPA (`docs/dpa-template.md`) before any student data is
entered. It names the sub-processors: Google Cloud (hosting, `asia-south1`)
and, only if the school turns AI features on, the LLM provider in
`docs/compliance.md`'s LLM provider table (today: Sarvam AI).

## 1. The project (once per GCP project)

1. The account owner runs `deploy/gcp/bootstrap.sh` (`docs/gcp-bootstrap.md`).
   It creates Cloud SQL (Postgres 16, Enterprise edition, daily backups +
   PITR), the GCS buckets, Secret Manager entries (holding `REPLACE_ME`),
   Workload Identity Federation and the budget alert.
2. The team sets the repo variables it prints. `CORS_ORIGINS` is the Hosting
   origins, both of them:
   `https://<project>.web.app,https://<project>.firebaseapp.com`.
3. Real secret values (Cloud Shell, never into git):

   ```bash
   openssl rand -hex 32 | tr -d '\n' | gcloud secrets versions add principal-bootstrap-key --data-file=-
   ```

   `postgres-password` was set by the bootstrap. `acos-llm-api-key` stays
   `REPLACE_ME` unless the school has chosen an AI provider (§6).

   **The service will not start** while `principal-bootstrap-key` or
   `postgres-password` is `REPLACE_ME` or empty, the bootstrap key is under 32
   characters, `CORS_ORIGINS` is `*` or not https, or demo accounts are on.
   That is deliberate (`docs/gcp-deployment.md` §4, "Production guard"): a
   misconfigured revision never goes ready, the old one keeps serving, and CI
   goes red. Cloud Run's logs name each problem on a line starting
   `REFUSING TO START (production config)`.

## 2. The database schema

**Check for duplicate emails first** **[Task 301]**. Task 301 makes
`users.email` unique; on a database that already has two accounts with one
email that statement fails and, because the apply script stops on the first
error, the invites table after it is never created. In `gcloud sql connect
academicos-pg --user=academicos --database=academicos`:

```sql
SELECT lower(email), count(*) FROM users GROUP BY 1 HAVING count(*) > 1;
```

No rows: continue. Rows: stop. For each email, list the accounts
(`SELECT id, school_id, name, role, created_at FROM users WHERE lower(email) =
'<email>';`), agree with the school which is the real one, and move or delete
the others until the query is empty. A new school's database is empty and
returns nothing.

Then apply the schema (idempotent, required before the first deploy and after
any change to `deploy/gcp/schema.sql`):

```bash
PROJECT_ID=<project> bash scripts/apply_cloudsql_schema.sh
```

## 3. The first deploy

A new school has no Supabase history to migrate. Set the repo variable
`FRESH_INSTALL=1` for the first deploy only (it lets an empty curriculum
snapshot and an empty mastery table boot), push to `master`, and delete the
variable afterwards. (A school moving off Supabase runs the two migration
scripts instead; `docs/gcp-deployment.md` §8.)

The deploy is done when the workflow is green. It checks for you that:

- `GET <cloud-run-url>/health` answers
  `{"status":"ok","commit":"<the sha you pushed>","builtAt":"..."}` — a
  different commit fails the job;
- the web app was built against `<cloud-run-url>/api/v1` and deployed to
  Hosting.

Check yourself: `GET <cloud-run-url>/health/storage` shows `"status": "ok"`,
`durability_backend` Cloud SQL, `blob_backend: "gcs"`, every table `"ok"`.

## 4. The school's first principal

The principal bootstrap key turns one registration into a principal account.

1. Agree a `school_id` with the school: short, lowercase, permanent
   (e.g. `dps-bangalore-east`). Every record the school creates is scoped to
   it.
2. Send the principal the web app URL and, **through a separate channel**
   (phone, in person), the bootstrap key.
3. The principal opens the web app → Sign up, enters the `school_id`, their
   name, email and a password (8+ characters), and pastes the key into the
   principal-key field. (API: `POST /api/v1/auth/register` with
   `{"schoolId", "name", "email", "password", "principalKey"}`.)
4. Confirm: `GET /api/v1/auth/me` with their token answers `"role":
   "principal"`.

**[Task 301]** restricts the key to a school's **first** principal: once a
school has one, the key no longer grants the role for that school. Today, on
this branch, the key grants principal to *any* registration that supplies it,
for any `school_id` — so after step 4, **rotate the key** (add a new
Secret Manager version with `openssl rand -hex 32` and push a deploy, or
`gcloud run services update academicos-backend --region asia-south1
--update-secrets ...`) and never reuse one key across schools.

There are no demo accounts on the GCP release: `principal@school.com` /
`password123` are seeded only in local development, and `ACOS_DEMO_ACCOUNTS`
on the service stops it starting.

## 5. Teachers, students, consent, calendar, classes

### Teachers and students

**[Task 301]**: the principal invites teachers and students from the web app
(an invite per email, accepted by setting a password), so no one else ever
chooses a school or a role for themselves.

Today: teachers and students self-register at Sign up with the school's
`school_id` and pick "teacher" or "student" (`POST /api/v1/auth/register`,
`"role": "teacher" | "student"`; principal is never selectable). The principal
checks the roster — `GET /api/v1/auth/users` — and reports anyone who should
not be there to the operator.

### Parental consent (DPDP Act 2023) — before any student data

For every student, record the guardian's verifiable consent **before** that
student's marks, scans or answers are entered:

`POST /api/v1/consent` with `{"studentId", "guardianName",
"guardianRelationship", "method"}` — `method` is how it was obtained
("Signed admission form", "Physical consent slip"). Check a student with
`GET /api/v1/consent/students/{student_id}`; list the school's with
`GET /api/v1/consent`. Withdrawal: `DELETE /api/v1/consent/students/{id}`.
Keep the paper originals; the record says where they are. (On this branch any
signed-in member of the school can record consent; the school should have the
principal or office do it.)

### Calendar and classes

All principal actions, in the web app's admin screens or via
`/api/v1/curriculum/...`:

1. **Curriculum.** `POST /seed/cbse10` with `{"academicYearLabel": "2026-27",
   "startDate": "2026-06-01", "endDate": "2027-04-30"}` seeds the official
   CBSE Class X syllabus as the school's academic year → grade 10 → subjects →
   books → chapters. Idempotent.
2. **Calendar.** `POST /academic-years/{id}/calendar`, holidays with
   `POST /academic-years/{id}/holidays` (multi-day blocks allowed), then the
   period configuration, subject period allocations and weekly timetable
   slots (`/period-configuration`, `/subject-period-allocations`,
   `/timetable-slots`). `GET /academic-years/{id}/working-days` checks it.
3. **Classes.** Assign each teacher their book(s):
   `POST /teacher-assignments` `{"teacherId", "bookId"}`. Enrol each student
   in their grade: `POST /student-enrollments` `{"studentId", "gradeId"}`.
   Both refuse a user or book from another school.
4. **Schedule.** `POST /books/{book_id}/schedule` lays the syllabus over the
   working days; teachers see theirs at `GET /my-schedule`.

## 6. The first paper

A teacher signs in → Create paper (quick generate: subject, grade, chapters,
marks) → reviews the questions → exports the PDF (`POST
/api/v1/papers/quick-generate`, then `POST /api/v1/papers/{id}/export/pdf`).
The PDF uses the Unicode body font the image ships (DejaVu Sans); the service
logs `PDF body font: AcademicSans (/usr/share/fonts/truetype/dejavu/...)` at
startup. A line saying `Helvetica (built-in, Latin-1 only ...)` means the font
is missing and symbols will print as boxes.

**AI features** (scan reading, AI marking) are off until the school chooses a
provider. Without a key they answer 501 `"not enabled for this school"`;
paper generation, manual marking and everything above work without one. To
turn them on: the provider must be in `docs/compliance.md`'s LLM provider
table and the DPA; add the key as a new version of `acos-llm-api-key`; set
the `LLM_BASE_URL` / `LLM_MODEL` repo variables to that provider; deploy. A
key with a base URL outside the table stops the service starting.

## 7. Where the data lives

Everything is in the GCP project, region `asia-south1` (Mumbai):

| What | Where |
|---|---|
| Users, sessions, assessments, papers, marks, scan sessions, templates, audit log, learner events, parental consent, mastery history | Cloud SQL Postgres `academicos-pg`, database `academicos` |
| Calendar, curriculum sequence, timetable, teacher assignments, enrolments | One SQLite snapshot in GCS: `gs://<project>-academicos-media/academicos/curriculum-snapshots/curriculum.sqlite` (single writer; `--max-instances=1`) |
| Scan photos and PDFs | GCS `gs://<project>-academicos-media/academicos/scan-media/` |
| A school's own uploaded papers, partner API keys | **Container disk only — lost on redeploy.** Open gap (`docs/gcp-deployment.md` store census); do not rely on them yet |
| Answer sheets / typed text sent for AI features | The LLM provider, only when AI features are on |

## 8. Backups and restore

**Cloud SQL** (every table in the first row above): automated daily backup
(started 19:00 UTC, 00:30 IST; Cloud SQL keeps the last 7 by default) and
point-in-time recovery (transaction logs, 7 days by default). Restore into a
**new** instance, check it, then point the service at it — never restore over
the live instance first.

```bash
# to a point in time (e.g. just before a bad import)
gcloud sql instances clone academicos-pg academicos-pg-restore \
  --point-in-time '2026-10-01T04:30:00Z' --project <project>

# or from a daily backup
gcloud sql backups list --instance academicos-pg --project <project>
gcloud sql backups restore <BACKUP_ID> --restore-instance academicos-pg-restore \
  --backup-instance academicos-pg --project <project>
```

(`backups restore` needs the target instance to exist; create it with the same
tier and edition first.) Then set the `SQL_CONNECTION` repo variable to
`<project>:asia-south1:academicos-pg-restore`, apply the schema to it (§2),
and deploy. Keep the old instance until the school has checked its data.

**GCS objects** (the curriculum snapshot and scan media) are **not** covered
by the Cloud SQL backups, and the bootstrap does not turn on object
versioning. Until it does, the only copy of the calendar and classes is the
live snapshot object. Recommended once per project (the account owner):

```bash
gcloud storage buckets update gs://<project>-academicos-media --versioning
```

With versioning on, a bad snapshot is rolled back by copying the previous
generation over it while the service is stopped
(`gcloud storage ls -a gs://.../curriculum.sqlite`, then
`gcloud storage cp gs://...#<generation> gs://.../curriculum.sqlite`), and
redeploying.

## 9. Checklist

- [ ] DPA signed; LLM provider decision recorded (or "none")
- [ ] Secrets real; bootstrap key 32+ characters, sent separately
- [ ] Duplicate-email check empty; schema applied
- [ ] Workflow green; `/health` commit matches; `/health/storage` ok
- [ ] Principal registered, role confirmed; bootstrap key rotated (until Task 301)
- [ ] Consent recorded for every student before their data
- [ ] Curriculum seeded, calendar and timetable set, teachers assigned, students enrolled
- [ ] First paper generated and the PDF's symbols checked
- [ ] Media bucket versioning on
