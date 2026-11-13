# Data-flow record (R-A7, NFR-1)

What personal data AcademicOS holds, where it is stored, which processors
receive it, and how long it is kept. It was read from the code on 2026-11-13,
not from other documents. Paths are under `src/academicos/`. When a store, a
field or a vendor changes, update this file in the same PR, together with
`docs/compliance.md` ("New third-party integration or vendor") and the DPA
sub-processor list (`docs/dpa-template.md` §5).

This is a record of the build, not legal advice. Retention marked **owner to
confirm** has no period written down anywhere: the job keeps that data until a
period is set. The school's DPA (§6.1, still `[FILL IN]`) and the owner's
decision D6 (`docs/security-review-2026-10.md`) are where those periods are
set.

## Where things are stored (GCP release)

- **Cloud SQL Postgres** (`asia-south1`): the tables made by
  `assessment/postgres_kv.durable_table`: `users`, `sessions`, `invites`,
  `audit_log`, `parental_consents`, `papers`, `assessments`,
  `graded_evaluations`, `scan_sessions`, `learner_models`, `learner_events`,
  `practice_sets`, `school_templates`.
- **SQLite files saved to GCS as whole-file snapshots**
  (`storage/snapshot_sync.py`): the operations store (`operations/store.py`) and
  the curriculum store (`curriculum/store.py`). With
  `ACOS_STORE_BACKEND=postgres` (R-A1, `storage/pg_sqlite.py`) the same tables
  live in Cloud SQL instead.
- **GCS blobs** (`storage/blobs.py`): `scan-media` (answer-sheet photos and
  PDFs), `homework-media` (photos of written homework), `leave-documents`, the
  school profile's files, and the store snapshots.
- **Container disk** (Cloud Run, in memory, gone at restart): progress-report
  PDFs and exports under `data_root/exports`, the scan workdir.

## Categories of personal data

| Category | Whose | Stored in | Processors that receive it | Retention |
|---|---|---|---|---|
| Account: name, email, role, school, password hash | Staff, students, parents | Cloud SQL `users` | Google Cloud (host) | Until erased (`assessment/erasure.py`) or the account is closed; no period. **Owner to confirm** |
| Sign-in session tokens | Everyone signed in | Cloud SQL `sessions` | Google Cloud | 30 days (`users._SESSION_LIFETIME`); expired rows deleted daily by `operations/retention.py` |
| Emailed sign-in codes (hashed) | Principals, students, parents | Operations store `sign_in_codes` | Google Cloud; the code itself goes out by email (see mail) | 10 minutes (`sign_in_codes.LIFETIME`); expired rows deleted daily |
| Invites: invitee email, role | People invited | Cloud SQL `invites` | Google Cloud; the code by email if sent | Expire after 14 days (90 at most). Unused, expired or withdrawn invites are deleted after `ACOS_RETENTION_INVITE_DAYS` days: **owner to confirm**, unset means kept. Used invites are kept |
| Parental consent: guardian name, method, status | Students, guardians | Cloud SQL `parental_consents` | Google Cloud | Kept while the student is on the roll; deleted by erasure. **Owner to confirm** |
| Answer-sheet photos, PDFs, OCR text | Students | GCS `scan-media`; Cloud SQL `scan_sessions` | Google Cloud; **Sarvam AI** (images and OCR text, only if `SARVAM_API_KEY` is set) | **Owner to confirm** (D6). Deleted by erasure |
| Marks, graded sheets, paper marks, absences | Students | Cloud SQL `graded_evaluations`; operations store `paper_marks`, `paper_absent` | Google Cloud | **Owner to confirm** (DPA §6.1 suggests the academic year plus one). Deleted by erasure |
| Homework answers, feedback, photos | Students | Operations store `homework_submissions`, `homework_photos`; GCS `homework-media` | Google Cloud | **Owner to confirm**. Deleted by erasure |
| Mastery model, learner events, practice | Students | Cloud SQL `learner_models`, `learner_events`, `practice_sets`; operations store `learning_evidence`, `practice_sets` | Google Cloud | **Owner to confirm**. `docs/pilot-protocol.md` §2.4 says pilot event data is kept 24 months at most, "per agreement"; not enforced in code |
| Doubt text a user types | Anyone, students included | Not stored by the server | The critic LLM at `llm_base_url` (Groq by default; refused in production unless listed in `APPROVED_LLM_HOSTS`) | Not kept by AcademicOS |
| Class enrollment | Students | Curriculum store `student_enrollments` | Google Cloud | While enrolled; deleted by erasure |
| Notifications, digests, settings | Everyone | Operations store `notifications` and related tables | Google Cloud; **Firebase Cloud Messaging** for push (device token, title, body) | **Owner to confirm**. Deleted by erasure |
| Mobile number and SMS/WhatsApp consent | Staff, parents (never students) | Operations store `contact_numbers`, `message_deliveries` | **MSG91** (SMS) and the **WhatsApp Business Platform** (Meta), each only if its keys are set (`operations/messaging.py`) | Until withdrawn or erased |
| Email sent by the app (papers, codes, notices) | Recipients | Not stored beyond the delivery record | The configured SMTP relay, or **Composio** (`backend.composio.dev`) relaying through the school's Gmail/Outlook, each only if configured (`assessment/mailer.py`) | Not kept by AcademicOS |
| Google sign-in (ID token) | Users who choose it | Not stored; the email is matched to an account | Google (`operations/google_sign_in.py` fetches Google's public certificates; no school data is sent) | Not kept |
| Leave documents | Staff | GCS `leave-documents` | Google Cloud | **Owner to confirm** |
| Audit log: actor ids, student ids, action details | Everyone | Cloud SQL `audit_log` (append-only) | Google Cloud | **Never deleted by the app.** CERT-In requires ICT logs be kept at least 180 days; `operations/retention.py` holds no rule over it (`tests/test_retention.py::test_the_audit_log_is_kept_at_every_age`). An upper limit **needs counsel** |
| Error reports | No person by design | Cloud Logging / Error Reporting | Google Cloud | Cloud Logging's own retention. Messages are scrubbed of emails and long numbers (`api/error_tracking.py`) |
| Backups | Everything above | Cloud SQL backups and point-in-time recovery; the backups bucket | Google Cloud | The backup settings' own expiry. **Owner to confirm** (D6) |

## Processors in one list

Google Cloud (Cloud Run, Cloud SQL, Cloud Storage, Secret Manager, Logging,
Firebase Hosting and Cloud Messaging); Sarvam AI; the critic LLM host;
MSG91; the WhatsApp Business Platform; an SMTP relay; Composio. Every one
except Google Cloud receives data only when its key is configured. No
agreement with any of them is recorded in this repository; see
`docs/compliance.md`.
