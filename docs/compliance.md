# Compliance Checklist

This is a working checklist, not a certification. AcademicOS is **not** ISO 27001
certified, **not** SOC 2 audited, and **not** DPDP-registered as of this writing —
those all require an accredited external body, real time, and real money. What
this document is: the concrete controls those certifications actually check for,
so the project is *ready* to pass one when it's pursued for real, and so no future
feature quietly regresses something a real school's data depends on.

**Any agent (human or AI) adding a feature that touches student data, assessment
content, or grading should check this file first.** If a change trips one of the
"before you ship" boxes below, either satisfy it or flag it explicitly to the user
— don't ship it silently unresolved.

## The binding law, right now: India's DPDP Act 2023

Every CBSE student is a minor. That triggers the Act's child-data provisions
specifically, not just its general ones.

- [ ] **Verifiable parental consent**, not a checkbox. A generic admission-form
      clause or an in-app "I agree" does not satisfy this. Consent needs to be a
      distinct, verifiable step tied to the parent/guardian, not the student.
      ([campusfeed.in](https://campusfeed.in/dpdp-act-schools-child-data-privacy/))
  - Since 2026-09-22 the web server **refuses to process a student's work
    without it** — see "Parental consent is enforced on the server" below for
    exactly which paths check it and which do not. What still makes this box
    unticked is the *verifiable* half: consent is recorded by staff from a
    signed form, and nothing in the product verifies the guardian.
- [ ] **No behavioral profiling, tracking, or targeted advertising** aimed at a
      student, ever, regardless of what else consent covers.
- [ ] **No secondary use of student data** (e.g. using real answer sheets to
      improve/train a model) without separate, specific, informed consent beyond
      whatever consent covers the primary use (grading their own paper).
- [ ] **A data processing agreement (DPA) with the school** before any real
      student data moves — purpose limitation, retention period, deletion rights,
      named data controller and processor spelled out in writing. Not verbal.
      ([ksandk.com](https://ksandk.com/data-protection-and-data-privacy/dpdp-compliance-for-schools-and-edtech/))
- [ ] **Breach notification duty to the Data Protection Board** and to affected
      users — the Act's own timeline, layered under the CERT-In 6-hour rule below.

Enforcement for child-data provisions phases in on an 18-month clock from the
rules' notification — that's a runway to build this properly, not a reason to
defer it.

## IT Act 2000 — SPDI Rules, 2011

Predates DPDP, still in force, still the operative "reasonable security
practices" standard for anything DPDP doesn't yet fully occupy.

- [ ] **A documented, comprehensive information security programme** — the Rules
      explicitly recognize **ISO/IEC 27001 certification** (or an equivalent
      documented ISMS) as satisfying "reasonable security practices." That's the
      concrete target if/when real certification is pursued, not an arbitrary
      choice. ([indicpacific.com](https://www.indicpacific.com/india-ai-regulation-101-landscape/information-technology-(reasonable-security-practices-and-procedures-and-sensitive-personal-data-or-information)-rules,-2011-(spdi-rules)))
- [ ] **Independent security audit at least annually**, or after any significant
      infrastructure change (a new hosting provider, a new data store, a new
      third-party integration all count).
- [ ] **Informed, explicit, freely-given consent** before collecting sensitive
      personal data — same bar as DPDP, predates it.

## CERT-In 2022 Directions (Section 70B, IT Act)

This is the one with teeth on timing.

- [ ] **Report any of these to CERT-In within 6 hours of noticing** (the clock
      starts on awareness, not on finishing an investigation): data breach, data
      leak, unauthorized access to IT systems, identity theft, phishing targeting
      the app or its users. ([upguard.com](https://www.upguard.com/blog/indias-6-hour-data-breach-reporting-rule))
  - This means an **incident response runbook needs to exist before it's needed**
    — who gets paged, who has authority to notify CERT-In, where the report
    template lives. Writing it during an actual incident is too late.
- [ ] **Retain ICT system logs for 6 months minimum**, securely. This directly
      implies: every store that doesn't currently have audit logging (which store,
      exactly, per the feature checklist below) is a gap against this rule, not
      just a nice-to-have.
- [ ] Maintain accurate **point-of-contact and system-inventory records** CERT-In
      can be handed on request.

## Certifications worth pursuing for real, once there's a paying pilot

- [ ] **ISO/IEC 27001** — the SPDI-recognized path; also carries ~60-70% control
      overlap with SOC 2, so doing this one first is efficient.
      ([strikegraph.com](https://www.strikegraph.com/blog/soc-2-vs.-iso-27001-security-standards-for-edtech-companies))
- [ ] **SOC 2 Type II** — increasingly the actual price of entry for any EdTech
      vendor selling above small-school scale; districts/school groups are now
      disqualifying vendors at procurement for compliance gaps.
      ([episki.com](https://episki.com/now/soc2-for-education))
- [ ] No India-specific EdTech data-privacy circular from CBSE was found during
      this research (checked cbse.gov.in's circular pages directly) — DPDP Act
      2023 + SPDI Rules are the operative law for a CBSE-affiliated school today,
      not a board-specific rule. Re-check periodically; CBSE has been actively
      piloting its own AI evaluation system and could issue vendor guidance.

## Evaluation-precision — the honest standard, not a marketing number

Published research gives real reference points, not this project's own claims:

- OCR-only accuracy on real student handwriting: **75-95%** depending on scan
  quality and handwriting legibility.
  ([aichanakya.in](https://aichanakya.in/blog/ocr-handwriting-technology))
- Semantic/NLP-assisted grading matching manual (human teacher) grading: one
  published study reports **92% agreement**.
  ([computersciencejournal.org](https://computersciencejournal.org/wp-content/uploads/8-JCS1581.pdf))
- CBSE itself is actively piloting AI digital evaluation, trained on real answer
  scripts across states/handwriting styles — this is the actual competitive/
  credibility bar, not a hypothetical.
  ([vidyamandir.com](https://vidyamandir.com/studyhub/cbse-ai-digital-evaluation-answer-sheets/))

**Rule for this project: never claim an accuracy number that hasn't been measured
against real, teacher-graded answer sheets from this system specifically.** The
`needsReview` confidence gate already in `evaluate.py` / its Dart port is the
right mechanism — low-confidence answers go to a human, they don't get silently
auto-scored. Before any real deployment, run the calibration harness (see
"Before you ship" below) against a real graded batch and publish the actual
agreement rate, high or low.

## Vendors that receive school data

### LLM providers

The only hosts an AI feature (scan OCR, AI marking, the doubt critic,
curriculum extraction) may send school data to. **This table is enforced:**
`APPROVED_LLM_HOSTS` in `src/academicos/config.py` must equal it
(`tests/test_production_guard.py` pins the two), and on the GCP release a
service with an LLM key set whose LLM base URL points anywhere else refuses to
start. Adding a provider means a row here, the host in `APPROVED_LLM_HOSTS`,
and the DPA's sub-processor list (`docs/dpa-template.md` §5) — in that order,
before any key for it is deployed.

| Provider | Host | Used for | Data it receives |
|---|---|---|---|
| Sarvam AI | `api.sarvam.ai` | Scan OCR (`assessment/vision.py`), AI marking (`assessment/llm_evaluate.py`), curriculum extraction (`llm/sarvam.py`); the doubt critic when `ACOS_LLM_BASE_URL` points here | Answer-sheet images, OCR'd answer text, student-typed doubts, textbook chapter text |

Not listed, so refused in production: Groq (`api.groq.com`), which
`config/config.toml`'s `llm_base_url` still names for local batch extraction.
Choosing the provider is the school's decision; with no key configured the AI
features answer 501 "not enabled for this school" and nothing leaves the
service.

## Before you ship — per-feature checklist

Check every box that applies to the feature being built. Anything checked "no"
gets flagged to the user, not silently shipped.

- [x] **New data store or new field holding student data?** → Is it encrypted at
      rest? **Ticked for the GCP release only (2026-09-22).** Audit item 8.5
      found no documented answer for the server stores (graded_evaluations,
      scan_sessions and their images, learner_events, parental_consents).
      - **GCP release (the web product).** Every durable server store is a
        Cloud SQL Postgres table (`postgres_kv.durable_table`), and scan
        photos/PDFs and the curriculum snapshot are GCS objects
        (`storage/blobs.py`, from Task 501; see Condition below), all in
        `asia-south1`. Per Google Cloud
        documentation, Cloud SQL and Cloud Storage encrypt all data at rest by
        default with Google-managed keys, and Cloud SQL backups are encrypted
        the same way as the instance. The pages to cite are "Default
        encryption at rest" (Google Cloud security documentation), "About
        customer-managed encryption keys (CMEK)" in the Cloud SQL
        documentation, and "Data encryption options" in the Cloud Storage
        documentation. These pages were not fetched while this was written,
        so the operator should open them and record the links here. No
        customer-managed key is configured: `deploy/gcp/bootstrap.sh` passes no
        `--disk-encryption-key` to Cloud SQL and no default KMS key to the
        buckets, so the keys are Google's. The daily Cloud SQL backups and the
        `pg_dump` exports in the `-academicos-backups` bucket are covered on
        the same terms.
      - **Condition.** The GCS routing for scan media and the removal of the
        Supabase credentials from `deploy-gcp.yml` come from Task 501
        (commit `eaa30f8` on `feat/product-gcp`). That commit is not on
        this branch yet. Until it is merged, a GCP deploy of this branch still
        injects `SUPABASE_KNOWLEDGE_URL`, so scan photos and PDFs go to
        Supabase Storage, and this tick does not describe that deploy.
      - **Not covered.** (1) Files a request writes to the container:
        `data_root/exports` (progress reports, corrected PDFs), the scan
        workdir, and any store `docs/gcp-deployment.md` lists as still
        container-local. Cloud Run's filesystem is in memory and is gone when
        the instance stops. Nothing in this repo claims it is encrypted at
        rest, and nothing should rely on it. (2) The Render release (Render +
        Supabase): not assessed here, and no claim is made for it. (3) The
        phone app is outside this release. For the record, its Hive-backed
        `LocalStore` is AES-encrypted (`SecureBox` + `HiveAesCipher`) with the
        key in a file in the app's private directory, not in the hardware
        Keystore. `flutter_secure_storage` was dropped because its Windows
        plugin's CMake/ATL packaging breaks the desktop build.
      Any *new* store needs its own answer to this. It does not inherit one.
- [ ] **New endpoint or screen that reads/writes real student PII (name, roll
      number, answer images, scores)?** → Is access logged with who/when/what?
      **Writes, yes. The reads the audit named, yes as of 2026-09-22. Three
      reads are still unlogged (listed below), so the box stays unticked.**
      Audit item 8.5 found that grading writes and paper exports were logged
      and reads were not. Nothing recorded who read a student's knowledge,
      answers, scan images or consent record.
      - **Writes:** every grading write is audited before it is saved (see
        the finalized-grade box below), and so are paper exports and consent
        changes.
      - **Reads (new):** each of these routes appends one `pii_read` entry to
        the append-only audit log after its access checks pass and before it
        returns anything. The entry records `actor` (the authenticated
        caller), `student_id`, `details.what`, and the timestamp. The call is
        `audit_log.record_pii_read`, made once per route. Routes and
        `what` values:
        `GET /knowledge/{id}` (`knowledge`; a student reading their own is
        logged too), `GET /knowledge/{id}/report` (`progress_report`),
        `GET /scan/sessions/{id}/review` (`scan_review`), `.../pages/{n}/image`
        (`scan_page_image`), `.../raw-pdf` and `.../corrected-pdf`, and
        `GET /consent/students/{id}` (`consent_record`). A read that covers
        many students writes **one** entry with the ids in
        `details.studentIds`: `GET /insights/class/{id}` (`class_insights`),
        `GET /evaluations/assessment/{a}/question/{q}`
        (`answers_to_question`), `GET /consent` (`consent_records`) and
        `GET /consent/missing` (`consent_status`). A request refused with
        403/404 served nothing and is not logged as a read. A read the log
        refuses (the table answered and refused the append) gets a 503 and no
        data: a read that cannot be logged is not served.
        `tests/test_pii_access_log.py` covers each route.
      - **Still unlogged:** `GET /auth/users` (the principal's roster, with
        student names and emails), and `POST /v1/revise` and `POST /v1/plan`
        (each replays one learner's event history). The school-wide
        `GET /insights/school/{id}` returns aggregates with no student named,
        and it is not logged. The Android `LocalStore` logs its grading
        writes (`appendAuditLog`), not its reads, and the phone app is
        outside this release anyway.
      Any *new* route that reads or writes student data needs its own call.
      Logging does not happen automatically.
- [x] **Anything that could change a finalized grade?** → Is the change logged
      with a reason and a reviewer identity, not a silent overwrite? **On the
      server, yes, as of 2026-09-22.** This box was ticked before that without
      being true. Audit item 8.5 finalized a sheet, changed its marks 0→2
      through `/award` and back through the sheet review, and the audit row
      count stayed at 2. What holds now (`assessment/grade_lock.py`,
      `tests/test_grade_integrity.py`):
      - A sheet is finalized once `finalize_sheet_review` (or a scan-session
        finalize) appends its `sheet_reviewed` entry. The log is append-only,
        so a sheet cannot be un-finalized.
      - Every server route that writes marks refuses a change to a finalized
        sheet without a non-empty `reason`, with **409 Conflict**: the sheet
        review, the grade-by-question award, `/evaluations/sheet` and
        `/evaluations/answer`. A bulk award with one finalized target is
        refused whole, before any write. A scan-session finalize takes no
        reason, so it is refused outright over a finalized sheet.
      - Every grading write is audited **before** it is saved, with the
        authenticated caller as `actor` (never None; `sheet_evaluated` used to
        be logged with actor=None), the marks `before` and `after`, `reason`,
        `finalized`, and the timestamp. The actions are `sheet_evaluated`,
        `answer_evaluated`, `sheet_answer_reviewed`, `grade_awarded` (one
        entry per student changed), and `sheet_reviewed` (finalize).
      - The scan-review regrade path is unchanged:
        `mobile_scan.review_decision`'s `regrade` action (and `edit` when it
        changes marks on an already-approved or edited item) requires a
        `reason` and a `reviewer_id` and logs `grade_regraded` with
        `oldMarks`/`newMarks`.
      **Not covered yet:** the Flutter clients do not send `reason`. After
      finalize, a web teacher's edit gets the 409 and its message, with no
      field to fill in. The offline Android engine (`local_pillar_api.dart`)
      has no finalized lock of its own.
- [x] **Is the audit log itself append-only, not just by convention?** →
      **Locally, yes; remotely, only once the SQL below is applied.** The
      local SQLite file has BEFORE UPDATE and BEFORE DELETE triggers that
      `RAISE(ABORT)`. They are created with the schema and added to existing
      files when opened. An append is a plain insert, so an existing id
      raises `DuplicateAuditEntry` locally and remotely; the remote append
      was an upsert until 2026-09-22. Each entry carries `seq`, `prev_hash`
      and `entry_hash` (a SHA-256 chain), and `AuditLog.verify_chain()`
      returns the first entry that does not fit. That catches an edit or a
      deletion made by someone who dropped the triggers, but not removal of
      the newest entries. Rows written before the chain existed are not
      hashed into it; the chain's first entry (`audit_chain_started`)
      records their ids and content hashes, so a later edit or deletion of
      one, or a raw INSERT of an unchained row at any time after the chain
      began (backdated or not), is reported too. A log that has no chained
      entry yet is not checked at all. The chain does not stop anyone who
      holds INSERT from appending a correctly chained entry: the hash is
      unkeyed, and the INSERT privilege is the control there. The remote
      read pages by id, because PostgREST silently caps one response at
      max-rows (1000 by default). Appends from one process take turns, so
      only two instances can race for a seq; a loser backs off with jitter
      and retries, and an append that loses 12 times in a row answers 503
      and saves no grade (or serves no read); it is not written to local
      disk. An append waits at most 5 s for its turn, then answers 503 the
      same way, so a slow database cannot tie up every request thread; if
      the append ahead of it found the database unreachable, the ones
      waiting fall back to local disk at once, as it did, instead of each
      waiting out the 10 s connection timeout in a queue.
      **Manual step, not yet applied to any live project:** the
      `audit_log` block of `docs/supabase-setup.sql` (chain columns, unique
      `seq`, RLS with INSERT/SELECT policies only, UPDATE/DELETE/TRUNCATE
      revoked, and the refuse-change trigger) must be run in the Supabase SQL
      editor **before** a build with this change is deployed; otherwise every
      grading write answers 503. A 4xx from the remote table (unknown column,
      RLS or permission refused) is a configuration error, not an outage, so
      it is not written to local disk, which Render wipes on restart; only a
      transport error or a 5xx falls back there. `deploy/gcp/schema.sql`
      carries the same columns and trigger for Cloud SQL. The real-Postgres
      tests for it run in CI, not locally.
- [ ] **New third-party integration or vendor** (any API call leaving the
      device/server)? → Is there a DPA-equivalent understanding of what data
      crosses that boundary, and is it in the security notes for that platform's
      README? **What crosses each boundary is now written down (below, read
      from the code on 2026-09-22). No signed agreement with any vendor is in
      hand, so the box stays unticked.** Before this, the vendors were listed
      only in the unsigned `docs/dpa-template.md`, which named Sarvam,
      Supabase and Render and missed the mail backends and the critic LLM.
      Code cannot produce the missing part. Someone has to accept Google
      Cloud's data processing terms for project `vidyuthlabs`, get Sarvam's
      terms (and those of whichever mail relay is configured), record both
      here, and have each school sign the DPA template.

      Every third party that receives school data in the **GCP release**, as
      `.github/workflows/deploy-gcp.yml` configures it:

      | Vendor | What it receives | When |
      |---|---|---|
      | **Google Cloud** (Cloud Run, Cloud SQL, Cloud Storage, Secret Manager, Cloud Build/Artifact Registry; `asia-south1`) | Everything the server stores or processes: accounts, consent records, graded sheets, scan photos/PDFs, mastery, the audit log | Always. This is the hosting |
      | **Firebase Hosting** (Google) | The static web app only. `firebase.json` has no rewrite to the API, so browsers call Cloud Run directly and no student data passes through Hosting | Always |
      | **Sarvam AI**, `api.sarvam.ai` Vision (`assessment/vision.py`) | Each captured answer-sheet page image, sent 3 times per page for the OCR vote. The handwriting itself, plus anything written on the page, such as a name or roll number | A scan page upload (`POST /scan/sessions/{id}/pages`), **only if `SARVAM_API_KEY` is set** |
      | **Sarvam AI**, `sarvam-105b` chat (`assessment/llm_evaluate.py`) | Per answer: subject, class, marks, the question, the marking scheme (or options and key) and model answer, the OCR'd answer text, and OCR risk flags. No student id or name is put in the prompt | Scan processing (`POST /scan/sessions/{id}/process`), **only if `SARVAM_API_KEY` is set** |
      | **Sarvam AI**, via `SarvamLLM` (`curriculum/routes.py`) | Syllabus/textbook text for chapter decomposition. No student data | A principal's extraction run, with `ACOS_LLM_API_KEY` |
      | **The critic LLM** at `llm_base_url` (`config/config.toml`: `https://api.groq.com/openai`, i.e. **Groq**, unless `ACOS_LLM_BASE_URL` overrides it) | The doubt text a logged-in user typed (students included) and retrieved corpus snippets. No student id | `POST /v1/agent/doubt`, whenever `ACOS_LLM_API_KEY` is set, which the GCP deploy does |
      | **SMTP relay**: none is named in code. It is whatever `SMTP_HOST` points at | Recipient addresses, the exported paper PDF, the answer key PDF if asked for, the school name and the teacher's note. No student data unless someone types it into the note | `POST /mail/send-paper`, **only if `SMTP_HOST/USER/PASSWORD` are set**. The GCP deploy sets none, so the route answers 400 there |
      | **Composio**, `backend.composio.dev`, which relays through the school's Gmail/Outlook | The same as SMTP for mail. For calendar sync, an assessment's title and date | **Only if `COMPOSIO_API_KEY` is set.** The GCP deploy does not set it, so Composio is not reachable in that release |
      | **Supabase** | Scan photos/PDFs and the curriculum snapshot (Supabase Storage) | **Not in the GCP release once Task 501 (`eaa30f8`, `feat/product-gcp`) is merged.** On this branch before that merge, `deploy-gcp.yml` still injects the Supabase credentials |
      | **Render** | Everything, as host | The Render release only. It is not the GCP release |
      | **A partner's webhook receiver** (API-6, 2026-10-01): an HTTPS URL a school's principal registers for one of the school's question-bank API keys (`assessment/webhooks.py`) | `questions.added` events: question ids with their class, subject and chapter, and why they were added. No question text and no student, teacher or school record: the event's fields are a closed list, and only questions the key may read are named | Only once a principal has registered a webhook, when the questions that key may read grow. Public HTTPS addresses only (private, loopback, link-local and metadata addresses are refused at registration and at every send), signed with HMAC-SHA256, and revoked with the webhook or the key |

      Two findings from reading the code. (1) `vision.py` and `llm_evaluate.py`
      read `SARVAM_API_KEY`, and the GCP deploy injects only
      `ACOS_LLM_API_KEY`. As deployed, scan OCR fails, each page is treated
      as blank with a warning, and every answer goes to a teacher. That is a
      functional gap, not a data leak. (2) The critic sends user-typed text to
      Groq by default. That is a vendor no document named before.
- [x] **New ingestion source** (a school's own uploaded papers/marking schemes)?
      → **Built (2026-08-20):** `POST /api/v1/ingest/school-documents`
      (`src/academicos/assessment/ingest_routes.py`). A file-type allowlist
      (pdf/docx/xlsx/jpg/jpeg/png; anything else is a 400, audited as
      `document_ingest_rejected`); a mandatory `copyrightConfirmed` flag —
      no confirmation, no ingest, also a 400 + audit entry; and real macro
      stripping for `.docx`/`.xlsx` — any `vbaProject.bin` member is removed
      from the OOXML zip and the `[Content_Types].xml` macro-enabled
      declaration is rewritten to the plain equivalent, verified in
      `tests/test_document_ingestion.py` against a real macro-bearing docx
      built with an actual `vbaProject.bin` payload (confirmed absent from
      the stored bytes after upload, and a macro-free docx is confirmed
      byte-for-byte untouched — the transform isn't just accepted, it's
      shown to leave clean files alone). Accepted files are registered in
      the same `SourceRegistry` the CBSE corpus crawl uses (`ingest/
      pipeline.py`), tagged with `schoolId`/`uploaderId`/`copyrightConfirmed`
      /`macrosStripped` in the row's `meta`, content-addressed so a repeat
      upload of the same bytes is recognized as a duplicate rather than
      re-registered, and every accept/reject is a distinct `audit_log` entry
      (`document_ingested` / `document_ingest_rejected`). What this does
      *not* do: parse/extract/index the uploaded document into the graph —
      it lands as a registered source, same stage a freshly-crawled CBSE PDF
      is in before `academicos.cli parse` runs; wiring that stage to also
      pick up school uploads is a straightforward follow-on, not done here.
- [x] **New feature that could leak an unpublished question paper early?** →
      Every PDF export now gets a unique, audit-logged watermark ID stamped in
      the footer (`pdf.py`'s `_page_furniture`, verified: a real generated paper
      was exported, the exact watermark ID was confirmed present in the PDF
      bytes via PyMuPDF, and confirmed logged). This is *traceability*
      (a leaked copy can be traced to the export that produced it), not a hard
      time-lock on export — a real school needs to print before the exam
      *starts*, so blocking export until a release timestamp isn't how real
      printing workflows work. A hard lock on *editing* an approved paper now
      exists: `principalApproved` (a real value of the existing
      `Assessment.status` field, reachable via `PATCH /assessments/{id}/status`)
      is terminal — once set, `POST /papers/generate` and
      `PUT /assessments/{id}` refuse with 409 (can't quietly re-run question
      selection or swap a question), and the status can't be PATCHed back to an
      editable state. Full principal-approval *workflow* (who approves, the
      approval action itself, notifications) still does not exist and was
      deliberately not invented — this is the lock half of the control only.
      **Correction and re-check (2026-09-22).** This box was ticked while
      audit item 8.5 could still get an unreleased paper and export its
      answer key from a student-role account. Watermarking traces a leak
      after the fact. It did not stop the student. The route policy table
      and staff gates from Task 302 (`api/route_policy.py`) do. A student now
      gets **403** on `GET /papers/{id}` and on
      `POST /papers/{id}/export/answer_key`, and a teacher at the school still
      gets 200 on both. This was re-verified by running
      `tests/test_role_gates.py::test_the_audits_student_attacks_are_refused_and_teachers_still_work`,
      which also covers the audit's other student attacks (every classmate's
      answer to a question, finalize, award). The tick now rests on that test.
- [ ] **Touches real answer sheets or scores for the first time in a new
      context** (e.g. a new export format, a new analytics rollup)? → Re-run the
      evaluation-precision calibration, don't assume the last measured number
      still applies. **Not done. Stated plainly (2026-09-22):** the only
      calibration that exists is MCQ, run on a university Data Science exam
      rather than CBSE (`scripts/calibrate_evaluation.py`; see "one real
      calibration run" below). There the engine's total matched the
      teacher's recorded mark for 26% of students exactly (13/50). The
      short-answer script (`scripts/calibrate_short_answer.py`) never
      completed a run, and its numbers must not be cited. **Short-answer and
      handwritten calibration needs real, anonymised student scripts graded
      by a teacher, which the code cannot produce, so this box stays
      unticked until a school provides such a batch and the run is
      published, whatever the result.** The scan-and-grade flow does not
      auto-trust a score in the meantime. Every low-confidence answer goes to
      a teacher (`needsReview`).

## Evaluation-precision — one real calibration run, not just cited literature

`scripts/calibrate_evaluation.py` runs the actual production `evaluate_answer()`
against a real, public, teacher-graded dataset (CC BY 4.0, Dinesh K P / Anna
University Chennai, DOI 10.17632/sf3kvjwknt.1 — 50 real students, real MCQ
selections, real teacher-recorded marks). Not CBSE Class X — a university Data
Science exam — so this calibrates the *scoring mechanism*, not CBSE-subject
accuracy specifically. Result, run 2026-08-16:

- Engine's option-matching agrees with the printed answer key: **100%**
  (993/993 question instances) — the mechanism itself is internally correct.
- Engine's summed MCQ total matches the **teacher's actual recorded mark**:
  only **26%** of students exactly (13/50), mean absolute difference 1.06/20,
  with a handful of large single-student gaps (checked one by hand against the
  raw CSV to rule out a parsing bug — confirmed real, not a bug).

Read this as: a strict answer key and a real human teacher's recorded marks
disagree more often than you'd hope, even on multiple-choice. That's the
actual argument for keeping the `needsReview` human-in-the-loop gate rather
than trusting any auto-score, MCQ included, as ground truth. Short-answer
(Q21-35) calibration is not done — needs OCR transcription of the raw scanned
PDFs first (the dataset has the PDFs and the final marks, but not transcribed
answer text); see the bottom of the script for exactly what that requires.

## Scan & Grade pipeline — bugs found running against real CBSE handwritten scripts

Ran the actual `/scan/sessions` → `/pages` → `/process` → `/finalize` flow (an
isolated local server, not production) against real handwritten CBSE Class X
2025 model-answer booklets for Science, Math Standard, Social Science, and
English (`cbse-model-answers/model-answer/2025/X/`), 2026-08-16. Findings:

- **Fixed — silent answer loss on table-formatted OCR.** Sarvam Vision
  sometimes renders a tabular MCQ answer block as an HTML table
  (`<td>Ans1.</td><td>(A) No Solution</td>`) instead of plain
  `"1. (A) No Solution"` lines. `_Q_MARKER` in `scan.py` only matches a
  question number at the *start of a line*; inside a table every line starts
  with a tag, so it matched nothing. Result: on the real Math Standard
  booklet, all 20 real, legible answers ("Ans1." through "Ans20.") were
  silently marked `blank` — not flagged, not low-confidence, just silently
  wrong. Fixed by stripping HTML tags before segmentation (`_HTML_TAG.sub("",
  ...)` in `segment_answers`); verified the same real page now recovers real
  answer text (`(D) 4/√(5) [check]`, `(A) x²+2x=0 [check]`, etc.) instead of
  blanks. **This was a real, reproducible, silent-failure grading bug, not a
  hypothetical — treat any other unusual Sarvam output shape (bullet lists,
  nested tables) as a similar risk until segmentation is made more robust to
  OCR formatting variance in general, not just this one shape.**
- **Not a bug — working as designed.** The page auto-crop
  (`imaging.py:crop_to_document`) reported "page edges not detected; used the
  full photo uncropped" on 3 of 8 real pages tested. Confirmed this is the
  correct, safe fallback for full-bleed pre-scanned/rendered pages that have
  no visible edge against a background to detect (the algorithm targets
  phone-camera photos of paper on a desk) — it kept the full frame rather
  than guessing a bad crop, exactly as designed. Real phone-captured photos
  (the actual target use case) weren't tested here.
- **Real, non-reproducible — transient Sarvam API failure. Fixed the silent
  part.** One page upload failed with `SSLEOFError` from `api.sarvam.ai` and
  was correctly treated as blank rather than crashing the session; an
  immediate retry of the same image succeeded, so the failure itself is
  transient, not a code bug. But the *consequence* was a real gap: a "blank"
  verdict caused by an OCR provider outage and a "blank" verdict because the
  student genuinely left the question empty were indistinguishable to a
  teacher reviewing results — both came back `needsReview: false`, a
  confident zero. Fixed in `mobile_scan.process_session`
  (`ocr_failed_pages`/`force_review`): any question with no matched answer
  segment, in a session where *any* page's OCR call failed, is now forced to
  `needsReview: true` with an explicit warning
  ("this 'blank' may be an OCR outage, not a genuinely blank answer; verify
  manually") instead of silently reading as a normal zero. Verified directly
  against `process_session()`: a question with a real matched answer stays
  unaffected (no spurious warning), only the genuinely-unmatched one gets
  flagged.
- **Follow-up: found the real matching question paper and re-ran properly.**
  The synthetic-paper limitation above was closed by identifying which real
  CBSE 2025 Science-086 question paper the model-answer booklet actually
  answers. Confirmed by cross-referencing the handwritten Section-A answers
  against every text-based variant in `cbse-dataset/question-papers/`:
  **Paper Code 31/1/3** (English medium) — verified on 7 independent
  questions before treating it as certain. Extracted the real, matching
  marking-scheme answer key for that exact paper code from
  `cbse-dataset/marking-schemes/`. Ground truth, read directly off the
  booklet (not via OCR): a perfect 20/20 on Section A — this corpus is
  *model/exemplar* answer scripts, not an average student's script, so any
  question that doesn't come back full marks is a genuine pipeline defect,
  not a content-mismatch artifact.

  Ran the real OCR → segmentation → Sarvam-105b scoring pipeline in-process
  against these real 20 questions + real answer key + the real handwritten
  page images. First real, honest result: **13/20 (65%)** — a large,
  genuine false-negative rate on a paper that should score 100%. Root-caused
  every miss against the raw OCR text and found one connected family of
  segmentation bugs, all in `_Q_MARKER`/`segment_answers` (`scan.py`):
  Sarvam sometimes misreads a handwritten "Q." as "9." (so "Q.5)" and "Q.7)"
  both matched as a bogus marker "9", concatenating both real answers into
  question 9's slot and leaving Q5/Q7 blank), sometimes prefixes a spurious
  digit before a real two-digit number ("8.14)" for "14)", dumping Q14's
  real answer into Q8's already-correct segment), and a stray leading
  period blocked the marker regex from matching at all ("`.13)`" for
  "13)"). Fixed by (1) tolerating a single leading stray period in
  `_Q_MARKER`, and (2) adding `_split_nested_marker`: when a captured
  answer body itself starts with its own clean, distinct marker pattern,
  trust the inner one — a genuine single-answer body never legitimately
  starts with "`<digit><separator>`" as its own first characters. Re-ran
  the identical real test after the fix: **18/20 (90%)**.

  The remaining 2 misses (Q9, Q10) are a distinct, harder, unresolved gap:
  Sarvam dropped the question-number digit entirely on those two ("9)"
  transcribed as bare ")", "10)" transcribed as "o)"), leaving no numeral
  in the text at all to recover from. Fixing that would require a riskier
  heuristic — inferring the missing number from its position between two
  confidently-matched neighbors — deliberately not attempted here given the
  risk of misattributing a real answer to the wrong question is worse than
  leaving it correctly flagged for human review. Flagged, not fixed.

## What's actually true today (2026-08-16), stated plainly

Built, verified, and (for the backend pieces) live on Render: no bundled API
keys in any distributable, release-build logging that would leak student PII
compiled out, local backend/server binds to localhost only, Android's local
student-data store (`LocalStore`, via Hive) is encrypted at rest (key in the
app's private storage — see the note below on why it's not Keystore-backed),
audit logging on every grading write and every paper export on both
platforms, watermarked/traceable PDF exports, and one real calibration
run against a real teacher-graded dataset (not just cited literature). A
written incident-response runbook (`docs/incident-response-runbook.md`) and a
fillable DPA template for onboarding a real school (`docs/dpa-template.md`)
now also exist — as templates/runbooks requiring a human to fill in the
brackets and, for the DPA, legal review before adoption. They are **not**
evidence that an incident-response team, CERT-In registration, or a signed DPA
exists today.

Correction (2026-09-22): the paragraph above called the server audit log
"append-only" and said every grading write was logged. Neither was true.
Audit item 8.5 found no audit entry and no finalized lock on the sheet review
or the grade-by-question award, `sheet_evaluated` logged with actor=None, raw
UPDATE and DELETE succeeding on the audit table, and the remote append being
an upsert. For the server, see "Anything that could change a finalized
grade?" and "Is the audit log itself append-only" in the checklist above for
what is true now, and what stays a manual step until the Supabase SQL is
applied. This correction does not cover the Android `LocalStore` log.

Encryption-key storage note: `flutter_secure_storage` (true OS-Keystore-backed
key storage) was tried first and dropped — its Windows plugin has a broken
CMake/ATL packaging that blocks the desktop build entirely (confirmed: the
required headers exist on disk after installing the VS ATL component, MSBuild
still doesn't find them — an upstream packaging bug, not a local config issue).
The key currently lives in a file in the app's own private data directory:
OS-sandboxed, but not hardware-Keystore-backed. Revisit if upstream fixes it.

## Correctness audit — stale-cache bug class + a real wrong-mark bug (2026-08-16)

The two `test_daily_loop.py` audits below kicked off a wider sweep once the
same defect shape turned up a second and third time. The stale-cache class
(a derived field the real write path never populates, read anyway, silently
degrading a feature to a constant) was found and fixed in three places
today:

1. `daily_loop.py`'s underconfident-advice gate (detailed below).
2. `forgetting.py`'s `RevisionScheduler.plan` — `importance = 0.5 + 0.5 *
   state.mastery` read the same stale `0.0`, pinning every concept's
   importance weight to exactly 0.5 and collapsing the revision-priority
   ranking to pure urgency. Reachable via `academicos.cli revise`.
   Demonstrated with two equally-stale concepts of real mastery 0.38 vs
   0.03: both got importance 0.5 before the fix; after, the better-known
   concept's priority is measurably higher.
3. `cli.py`'s `academicos.cli learn stats` (`cmd_learn`, `replay` action) —
   printed `ConceptState.mastery`/`.confidence` directly. A learner with
   22/22 correct answers across two concepts printed `mastery=0.000
   confidence=0.000` for both, while the real computed values are ~0.64–0.66
   mastery and ~1.0 recency-weighted accuracy. A teacher running this
   command would see a perfect student reported as having learned nothing.

All three fixed by computing the real value at point of use
(`KnowledgeMastery`/`ConfidenceModel`/`ForgettingModel`, all of which take an
explicit `now` for exactly this reason) instead of trusting the cached
field. `ConceptState`'s own docstring in `learner_model.py` now documents the
trap directly so it cannot recur a fourth time in this specific shape.

### A real, high-severity wrong-mark bug: MCQ option extraction (fixed)

Separate finding, different subsystem, same audit pass — this one changes
actual awarded marks, not just advice text.

`evaluate.py`'s `_evaluate_objective` (the deterministic MCQ scorer used by
the calibration harness and the Android offline engine) identified the
student's selected option with `_OPTION_ANSWER.search(answer.upper())` —
the **first** standalone letter A–D anywhere in the transcribed text.
Real CBSE OCR transcripts routinely contain a second, different letter that
is not the student's selection: Assertion/Reason boilerplate
("...Reason(R)...Assertion(A)..."), a "Section-A" heading, or a student's
own eliminative reasoning ("I first considered (A) but eliminated it, then
chose (D)"). Proven directly: a student who wrote the genuinely correct
final answer "(D)" after reasoning through option (A) first was scored
`0/1, noCredit, confidence=0.93, needsReview=False` — a **correct answer
marked wrong with false high confidence**, not flagged for any human to
catch.

Fix: detect when the transcript contains multiple *distinct* option letters
(a single letter repeated is not ambiguous) and cap confidence below
`REVIEW_THRESHOLD` so `needsReview` fires through the same mechanism as
every other uncertain read — instead of trusting the guess silently. The
letter picked is still the first-mentioned one: an earlier attempt at
picking the *last* letter was tried and measured **worse** against real
data — verified against all 17 scoreable real answers from today's CBSE
31/1/3 harness run (`docs/compliance.md`'s Scan & Grade section above), the
genuine selection is consistently first-mentioned and contamination is
trailing (boilerplate phrasing, neighboring-question OCR noise), so
"prefer last" flipped 5 of 17 previously-correct real answers to wrong.
Re-verified after correcting to first-match: zero regressions across all 17
real answers, and the genuinely ambiguous ones among them (4 of 17) are now
correctly flagged `needsReview` instead of silently trusted. This is not a
complete fix for option-letter ambiguity — no automatic method reliably
recovers the right letter from free text reasoning either direction — but a
wrong mark can no longer hide behind full confidence.

## Learner-advice correctness — two dead paths found by audit (2026-08-16)

Auditing the two long-standing `test_daily_loop.py` failures turned up a real
defect and a real design tension. Both matter here because this advice is
student-facing output derived from student data.

- **Fixed — mastery gate read a cache nothing fills.** `DailyLoop`'s
  "you know this" (underconfident) advice gated on `ConceptState.mastery`.
  That attribute is only ever assigned inside `forgetting.demo()`, a synthetic
  helper: the real ingestion path (`LearnerModel.observe` → `ConceptState.record`)
  updates attempts/correct/last_seen and leaves `mastery` at its `0.0` default
  permanently. Verified directly — a concept answered correctly 10/10 times
  reports a stored mastery of `0.0` while its real computed mastery is `0.66`.
  The gate therefore never opened for any real learner, silently disabling the
  advice. Fixed by computing mastery via `KnowledgeMastery` at use, matching
  how the same function already computes retention and confidence fresh rather
  than trusting stored fields. Proven by A/B: the regression test fails against
  the old gate and passes against the new one. Note the same stale-cache trap
  applies to `ConceptState.confidence`/`.retention` — anything reading those
  fields off a replayed learner is reading defaults, not measurements.
- **Corrected (2026-08-19) — "overconfident but drifting" is reachable; the
  earlier "proven unreachable" conclusion here was wrong.** That advice
  requires calibration ≥ +0.15 **and** ≥ 3 answers **and**
  `retention_now < min_retention` (0.35) at once. The original sweep evaluated
  every history at `now = last_answer`, which pins retention at ~1.0 by
  construction; production passes the *current* date, so decay applies. A
  corrected sweep (outcome patterns of length 3–5, spacings 1–60 days, ages to
  730 days, all affect valences) found **34 of 1008** histories satisfying all
  three conditions — e.g. outcomes `(1,0,0)` at 14-day spacing, 730 days
  stale, affect `excited` → calibration +0.1604, retention 0.3148. Verified
  end-to-end through `DailyLoop.plan()`: that learner receives *"c:
  overconfident but drifting — practice without hints to recalibrate the
  belief."* The advice branch is a live, intended feature. The
  `test_overconfident_but_forgotten_advice` test still legitimately xfails —
  its *specific* profile computes retention 0.554 > 0.35 and lands in the
  ordinary overconfident branch — so the `xfail(strict=True)` marker is kept;
  the marker's "reachable?" rationale is stale and should read "profile below
  min_retention" instead.


**Updated (2026-08-20):** the ingestion *endpoint and its compliance controls*
(file-type allowlist, macro stripping, copyright confirmation, audit logging)
are now built — see the "New ingestion source" checklist item above. What's
still not built is the part that was genuinely blocked on a real school
relationship rather than plumbing: nothing calls that endpoint yet (no
Flutter upload screen), and there's no real school-supplied corpus to test it
against beyond synthetic bytes in the test suite — it's ready to receive real
uploads the moment either exists.

Investigation outcome (2026-08-16) on the two items that used to be
on this list: (1) the edit-existing-grade gap is **built** — see the regrade
checklist item above; (2) the principal-approval *lock* is **built** — see the
paper-release checklist item above.

**Built (2026-09-11): teacher/principal identity and the approval workflow.**
The gap above (a principal role, an authenticated approve action, and
something to enforce that role) is now real, exactly along the lines this
document recommended — `PATCH /assessments/{id}/approve`
(`src/academicos/assessment/routes.py`), gated on
`auth_routes.require_principal`, sets `status = principalApproved` (engaging
the existing `_require_editable` lock unchanged) and appends an
`assessment_approved` entry to `audit_log` with the real principal's identity.
Identity itself: `src/academicos/assessment/users.py` + `auth_routes.py` —
register/login/logout/me, stdlib PBKDF2-HMAC-SHA256 password hashing (200,000
rounds; no new dependency added), opaque server-side session tokens (not a
JWT — no signing-key management, revocation is deleting a row), same
SQLite-local/Supabase-when-configured persistence every other store here
uses. Who becomes principal: the *first person to register for a given
schoolId* — a real product decision, not silently assumed (see users.py's
docstring for the reasoning and its limits). `reviewerId` on
`finalize_sheet_review`/`review_decision` — permanently blank before this,
since there was no authenticated actor to put there — now prefers the real
logged-in identity, falling back to the client-supplied value only for a
caller that has never logged in. Full Flutter wiring too: a real login/
register screen, a Dio interceptor carrying the session token, and the
Settings > Profile page's existing free-text "principal name" field (anyone
could type any name and approve) replaced by this real, role-gated action —
in both the online build (a real login) and the offline single-device build
(`LocalStore.teacherRole`, self-declared and gated the same way biometric
device-lock already is, an intentionally different and honestly weaker trust
model than the server's password-backed one, documented as such rather than
conflated with it). All 12 route-inventory tests plus a dedicated
register/login/approve/cross-school/logout test pass; full Python suite (925)
and Flutter suite (98, excluding the 2 unrelated pre-existing live-backend
integration tests) both green after this change.

Not built: the actual notifications half of "an explicit approve action, and
any notifications" — approving still doesn't notify anyone. A real
multi-teacher-per-school pilot will also want more than one principal-capable
account per school (today's bootstrap rule gives exactly one, automatically);
revisit before that's a real constraint.

**Superseded (2026-09-21): school membership is granted by invite, not
asserted.** Both the "first registrant is principal" rule above (already
replaced on 2026-09-11 by `ACOS_PRINCIPAL_BOOTSTRAP_KEY`) and the rest of
registration let the caller name its own school: `RegisterRequest` took
`schoolId` and `role` from the body and `UserStore.register` stored them
unchecked. Two auditors reproduced it with TestClient probes (scorecard item
8.4): `attacker@evil.example` registered into school_A as a teacher and then
read `/assessments/{id}`, `/knowledge/{studentId}`, `/insights/class/{aid}`,
every student's answers under `/evaluations/assessment/{aid}/question/q_1` and
`/consent/students/{sid}`. Every `school_id` check rested on that one claim.
Separately, the global bootstrap key made its holder principal of any school,
including one that already had a principal. Now (`users.py`,
`auth_routes.py`, `tests/test_auth_invites.py`):

- a principal issues invites for their OWN school (`POST/GET/DELETE
  /api/v1/auth/invites`; Admin console > Roster > Invite people): a 128-bit
  random code, role `teacher` or `student`, optionally bound to one email,
  14-day default expiry (90-day cap), single use (one conditional UPDATE, so
  a race on one code has exactly one winner), revocable, recording who
  created it and who used it when;
- `/auth/register` takes the school and role from the invite. A `schoolId` or
  `role` that disagrees with it is a 400; no invite, or an unknown, used,
  revoked, expired or wrong-email one, is a 403;
- the bootstrap key is an operator secret that creates a school's FIRST
  principal only; for a school with a principal it is a 403;
- the demo accounts (`principal@school.com` / `teacher@school.com`, published
  password, `demo_school`) are seeded only when `ACOS_SEED_DEMO_USERS=1`.
  Before this they were re-created on every Render cold start, because the
  local users table there is empty after each restart (the real rows live in
  Supabase).

**Operator action, not done by code:** accounts created before 2026-09-21
keep their stored school and role. An account that named its own school then
cannot be told apart from a real one, so review each school's roster
(`GET /api/v1/auth/users` as its principal) once and remove anyone who does
not belong. Also check the durable store for `principal@school.com` /
`teacher@school.com` and delete them if present.

## Parental consent is enforced on the server (2026-09-22)

Audit item 8.5 (2026-09-21): consent was recorded (`consent.py`,
`consent_routes.py`) but never read — a grep found no consent reference
anywhere else, so grading and scanning ran for a student with no consent on
file. Now one check, `authz.require_consent`, answers **409 "no recorded
parental consent for student X; record it under Classes before grading"**
unless the student has an active consent record at the caller's school.
Withdrawn consent (`status: "revoked"`) counts as none, and so does a record
whose status cannot be read (fail closed, as `ParentalConsentRecord.from_row`
already did). Consent recorded by another school does not count.

**Enforced — every web-server path that processes a named student's work**,
checked after the route's own 401/403/404 checks and before anything is
scored or written (`tests/test_consent_enforced.py`):

- `POST /evaluations/answer` and `POST /evaluations/sheet` — before the
  answers are scored, not only before they are saved;
- `POST /evaluations/sheet/{aid}/{sid}/review/{qid}` and `.../finalize` —
  finalize folds the sheet into mastery, which is new processing;
- `POST /evaluations/assessment/{aid}/question/{qid}/award` — every target
  student is checked before the first write; one without consent refuses the
  whole request and is named;
- `POST /scan/sessions`, and on an existing session `.../pages`,
  `.../process`, `.../review/{qid}`, `.../finalize` — checked on each call,
  so a withdrawal mid-session stops the rest of it;
- `POST /practice/generate` and `POST /practice/submit`.

**Not gated, deliberately:** reads of what is already stored — the question
grid, class and school insights, `/knowledge/{sid}` and its PDF report, a scan
session's review queue, page images and PDFs, `/v1/revise` and `/v1/plan`.
Reading stored marks is not processing new data, and withdrawal must not hide
what was graded while consent was in force. No web-server route writes the
learner event store (only the CLI does), so there is no event write to gate.

**Before a test:** `GET /api/v1/consent/missing?studentIds=a&studentIds=b`
(staff only) returns which of those students have no active consent. It takes
the roster as ids because the server holds none: an assessment records how
many students sit it, not which, and the class list lives in the web client's
Classes page, which is also where consent is recorded. The grading, scanning
and practice pages show the 409 sentence itself (`apiErrorMessage` in
`pillar_api.dart`) instead of Dio's generic error.

**Not covered here:**

- anything graded on-device by the Flutter local engine
  (`LocalPillarApi`): the offline phone app, and the demo seeder, which grades
  its sample class that way. None of it reaches these routes, so none of this
  check applies; the phone is Task 305's concern in another stream.
- Tests record consent in their setup (`grant_consent` in
  `tests/_auth_helpers.py`); nothing bypasses the rule.

## Owners over several schools (ROLE-4, 2026-10-01)

One owner account (a trust or management) may be linked to several schools.
This is a change to tenancy, so what holds is written down here.

- **Who grants it.** Only a school's own principal account issues an owner
  link (`POST /api/v1/owner-links`): a single-use code, shown once, kept only
  as its SHA-256, expiring in 14 days by default. The owner redeems it, and the
  link then is the membership. The principal can end it at any time
  (`DELETE /api/v1/owner-links/{id}`), and it ends on the owner's next request:
  the link is re-checked on every request, not cached in the session. An
  owner acting as the school's principal cannot issue or withdraw owner links,
  so a revoked owner cannot have left a second account linked behind it.
- **What it grants.** Principal-level rights in ONE school at a time. The
  owner's session chooses a linked school (`POST /api/v1/owner/active-school`),
  and every route then sees that school's principal and scopes by that school
  alone, so the existing `school_id` checks are what keep the schools apart.
  With no school chosen, an owner reaches only its own routes and `/auth/me`.
  No route returns two schools' records in one response; the one exception is
  `GET /api/v1/owner/overview`, which gives per-school counts (papers this
  term, syllabus taught against plan, cover filled) and names no student,
  teacher or record. `tests/test_owner_multi_campus.py` sweeps every
  parameterless GET as an owner acting in one school for the other school's
  records, and checks an unlinked school, switching, and a revoke.
- **Logged.** `owner_link_created`, `owner_registered`, `owner_link_redeemed`,
  `owner_link_revoked` and every `owner_school_switched` are audit entries.
  What an owner does inside a school is logged as that school's principal's
  actions are, with the owner as `actor`; a principal-level change
  (`admin_action`) also carries `viaOwner` and the `schoolId` it was made in,
  and a read of student data is a `pii_read` with the owner as `actor`.
- **Storage.** The links live in the operations store (SQLite, snapshotted to
  the blob store with the admin grants). They hold account and school ids,
  not student data.
- **Not settled by code.** Each school remains the data fiduciary for its own
  students. A school linking an owner is giving that owner access to its
  student data, so the school's DPA (`docs/dpa-template.md`) should name the
  owner before a link is issued. The web says what the link grants when the
  principal creates one; it cannot check the paperwork.

## Six-dimension audit (2026-08-19) — fixed bugs and open decisions

A six-subagent audit (D1 stale caches, D2 docs/behavior contradictions,
C1 capture-failure masking, D4 data-loss, D5 API-surface drift, D6
out-of-range robustness) confirmed mechanical bugs and shipped fixes + A/B
regression tests. Everything below the divider was deliberately left for a
human decision — it is behavior, not a defect, and changing it unilaterally
would alter what reaches real students/teachers.

**Fixed (mechanical, A/B regression-tested):**
- `graph/query.py` `_mastery()` and `curiosity_engine.py` `rank()` read the
  stale `ConceptState.mastery` cache (same defect class as the DailyLoop gate
  above); now compute via `KnowledgeMastery` at use. Tests in
  `tests/test_prereq_edges.py` / `tests/test_curiosity_engine.py` rewritten to
  real `observe()` evidence.
- `assessment/vision.py`: an OCR run where every Sarvam Vision pass raises
  now re-raises (blank page returned only when passes genuinely recover empty
  text) — callers already catch `Exception`, so the `ocr_failed_pages`
  detector now routes real capture failures to review. Tests in
  `tests/test_assessment_vision.py`.
- `assessment/knowledge.py`: `record_evaluations` outcome now derives from
  awarded/max marks, so a teacher correcting a "blank" verdict to full marks
  lands as outcome 1.0; `load()` restores `updated_at`; local `_path()`
  sanitization is now injective (`stu.dent` ≠ `student`). Tests in
  `tests/test_assessment_knowledge.py`.
- `assessment/store.py`: the upsert `ON CONFLICT` clause now refreshes
  `school_id`/`teacher_id`/`created_at`, not just working fields. Tests in
  `tests/test_assessment_store.py`.
- `assessment/routes.py`: `PATCH .../status` rejects unknown statuses with
  422; `DELETE` of a nonexistent assessment returns 404. Tests in
  `tests/test_assessment_governance.py`.
- `algorithms/{mastery,confidence_model,motivation_model}.py`: out-of-range
  outcomes and future-dated interactions are clamped (no >1.0 confidence, no
  `OverflowError` from `math.exp`); `forgetting.py` `RevisionScheduler.plan()`
  caps next-review dates at the maximum representable date instead of
  crashing. Tests in `tests/test_algorithms_robustness.py`.

---
**Left for human decision (flagged, not changed):**
- **C3 — `process_session` drops bank-missing questions silently.** A scanned
  answer whose question id is not in the session's question list is skipped
  with no per-question failure flag; the sheet still completes. Option to
  consider: emit a per-question `failed` review item so the teacher sees *why*
  a question is absent. Nothing in the shipped flow currently surfaces the
  drop. **Resolved (2026-08-20):** `process_session` now emits a review item
  for an unmatchable question instead of skipping it — `status="failed"`,
  `verdict="noMatch"`, low confidence, `needs_review=True`, reasoning naming
  the missing bank match, and any answer text the student actually wrote under
  that number preserved. Verified by
  `tests/test_assessment_mobile_scan.py::
  test_bank_missing_question_is_surfaced_not_silently_dropped` (fails against
  the old skip, passes against the new surface), which also asserts the real
  questions in the same session score untouched.
- **C4 — genuinely keyless questions score as confident noCredit.** When a
  question has no answer scheme at all, `evaluate_answer` hits the empty
  `marking_points` path: confidence computes at 0.8–0.9 and the verdict is
  "none of the expected marking points were found" rather than "cannot score".
  Checked the Flutter client (`pillar_api.dart` `evaluateSheet` + callers):
  it always sends full bank questions with `answerScheme` attached, and
  `build_answer_key` synthesizes a key otherwise, so this path is **not**
  reachable through the shipped app. It only matters if hand-imported bank
  questions can carry a scheme with zero marking points. If that becomes
  possible, the empty-points branch should route to review (low confidence)
  instead of scoring. **Resolved (2026-08-20):** a scoreable-length answer
  against a zero-marking-points scheme now returns `confidence=0.0`,
  `needs_review=True`, `verdict="partialCredit"`, with reasoning that names
  the missing scheme — distinct from a genuine zero-credit answer (which a
  real key still scores confidently). Verified A/B by
  `tests/test_assessment_evaluate.py::
  test_keyless_scheme_routes_to_review_not_confident_zero` (same answer:
  confident noCredit with a real key vs. low-confidence review with no key;
  the test fails against the old scorer).
- **D5 — ~40 Dart `ApiClient` routes have no Python handler.** (e.g.
  `teacherReview`, `finalizeEvaluation`, `/answer-sheets/{id}/evaluate`).
  These are feature gaps in `src/academicos/assessment/routes.py`, not bugs;
  the app targets the local backend and the missing endpoints are simply
  unimplemented surfaces. Triaged per-route in the audit; none is called by
  the shipped demo flow. `GET /schools/{id}/school-templates` auto-seeding a
  default template is intentional (per the code comment) and left as-is.
  **Updated (2026-08-20):** a complete, programmatically-verified route
  inventory now lives in `tests/test_route_inventory.py`. It enumerates all
  51 real backend routes (15 `routes.py` + 19 `pillar_routes.py` + 9
  `mobile_routes.py` + 8 `api/main.py`) and asserts the live app matches
  exactly, so any route added/removed/renamed fails loudly until the
  inventory and its exercise table are updated. Every one of those 51 routes
  is exercised end-to-end (valid 200s + proper-4xx error paths), and the
  Flutter side was re-audited: `pillar_api.dart` (25 method calls) is 100%
  matched; `api_client.dart` has 16 matched / 42 unmatched methods. **All 42
  unmatched Dart methods are dead code** — each is called only from
  repositories/blocs no live page consumes (the pages dispatch only
  AssessmentBloc events; Scanner/Evaluation/Mastery/Analytics/ReportsBlocs
  are registered in `main.dart` but unused; two AssessmentBloc methods return
  `NotFoundFailure('Not implemented')`). Consequently there is nothing to
  implement and nothing to stub: **implemented 0 / 501-stubbed 0 / dead-code
  42**. The per-route verdicts are itemized in the audit log of this work
  session.
- **D4 — PUT is an upsert.** `PUT /assessments/{id}` silently creates when the
  id doesn't exist (200, no 404), and the remote Postgres path replaces the
  whole payload row. For offline-first mobile sync an upsert may be exactly
  right; for strict REST semantics it should 404 on a missing id. **Resolved
  (2026-08-20): confirmed safe, upsert stays.** Grep'd every real call site in
  the Flutter client; none relies on (or even handles) a 404 for this method:
  - The only live caller is `frontend/lib/presentation/planner/pages/
    daily_planner_page.dart:212` —
    `GetIt.I<ApiClient>().updateAssessment(a.id, a.copyWith(scheduledAt: ...))`,
    where `a` came from `loadAssessments` → `getAssessmentsByTeacher` — a
    known-existing assessment the teacher just fetched. The surrounding
    try/catch treats every error identically ("Could not schedule: $e"); there
    is no not-found branch anywhere.
  - The repository path (`AssessmentRepository.updateAssessment`,
    `assessment_repository_impl.dart:63`) has **no** presentation-layer caller
    today (the blocs use create/get/updateStatus only), and even it folds
    every failure into a generic `ServerFailure` — no 404 semantics.
  - The offline-first engine (`local_api_client.dart:76`) implements this
    exact method as a literal `LocalStore.upsertAssessment` — create-if-missing
    is the product's own offline sync contract for it, and the server-side
    upsert matches that contract.
  - Upsert does not bypass the hard edit lock: PUT still calls
    `_require_editable` and 409s on `principalApproved`+ assessments
    (`routes.py`).
  So a 404 on a missing id would be dead code for every current caller, and
  riskier for the planner flow (an assessment that vanished mid-session would
  throw instead of being re-created for offline sync). Behavior left as-is.
  If a future caller genuinely needs strict create-vs-update semantics, add a
  distinct `POST /assessments/{id}` or a `?upsert=false` flag then — don't
  retrofit the 404 onto today's contract.
- **D5 — dev-file rename caveat.** Making the local `_path()` sanitizer
  injective (above) changes the on-disk file name only for ids containing
  characters outside `[A-Za-z0-9_-]`; existing clean ids keep the same files,
  and ids that previously collided would have been corrupted anyway. Safe to
  ship; a future remote migration should not depend on local file names.
- **E1 — Audit Logging & Grade Change Tracking (2026-09-14).**
  Implemented `src/academicos/assessment/audit_log.py` as an audit trail for
  grading overrides, assessment state transitions and administrative
  operations. As written on 2026-09-14 it was append-only only by convention.
  Database triggers, insert-not-upsert and the hash chain arrived on
  2026-09-22; see the checklist above. Each audit record captures `entry_id`, `action`,
  `assessment_id`, `student_id`, `actor`, `details` (JSON payload), and an ISO-8601
  UTC `timestamp`. Persisted locally in SQLite and synchronized to Supabase
  Postgres (`audit_log` table) when configured, fulfilling CERT-In log retention
  and DPDP Act accountability requirements.
- **E2 — Concurrency & Data Integrity (2026-09-14).**
  All 17 SQLite database connections across `src/academicos/` enforce `PRAGMA journal_mode=WAL`
  and `PRAGMA busy_timeout=60000`. This guarantees non-blocking concurrent reads and
  serialized writes under multi-user operational loads, eliminating `database is locked`
  failures during concurrent teacher grading and administrative scheduling.

