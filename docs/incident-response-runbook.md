# Incident Response Runbook — AcademicOS

**Status: a runbook to follow, not a statement of readiness.** This document does
**not** mean an incident response team, a 24/7 on-call roster, or CERT-In
registration currently exists. It exists so that when a real incident happens,
the 6-hour clock doesn't get eaten by people deciding who's in charge. Before it
can be used for real, every `[NAME]` bracket below must be filled with a real
person who has agreed to the role, and the contact numbers must be verified.

## The binding deadline (why this document has a clock)

Under the **CERT-In 2022 Directions** (issued under Section 70B of the IT Act
2000), any of the following must be reported to CERT-In **within 6 hours of the
moment someone on the team notices it** — the clock starts on *awareness*, not
on finishing an investigation:

- data breach
- data leak
- unauthorized access to IT systems
- identity theft
- phishing targeting the app or its users

For AcademicOS, every incident is also a DPDP Act 2023 child-data incident: all
data subjects are minors, so the downstream notification duties (Data Protection
Board, affected schools/parents) apply too — see "Downstream obligations" below.

**Working rule: if it touches a real student's data, or a credential that could
reach it, treat it as reportable until triage says otherwise.**

## Roles (fill in before use — small team, so a person can hold more than one)

| Role | Person | Backup | Phone |
|------|--------|--------|-------|
| Incident Commander (IC) — owns the clock, declares severity, coordinates, stops the 6-hour deadline from being missed | [NAME] | [NAME] | [PHONE] |
| CERT-In notifier — the *single* person with authority to send the 6-hour notification (and the DPB breach notice) | [NAME] | [NAME] | [PHONE] |
| Technical lead — runs containment, rotates credentials, preserves evidence | [NAME] | [NAME] | [PHONE] |

One person per role on a small team is fine; what is not fine is an incident
starting with the role unfilled. Decide now, in writing, and keep a copy of this
page somewhere a team member can reach at 2am (e.g. a pinned channel, an agreed
group chat).

## Detection sources (real mechanisms that already exist in this repo)

Do not wait for an alert system that doesn't exist yet. Detection starts with
the logging this codebase already produces:

1. **`src/academicos/assessment/audit_log.py`** — the `AuditLog` class. An
   append-only log (nothing in application code ever UPDATEs or DELETEs a row)
   that records **every grading write and every paper export** with
   `timestamp`, `action`, `assessment_id`, `student_id`, `actor`, and `details`
   (export records also carry the unique `watermarkId`). Persisted to local
   SQLite by default, or Supabase-backed when configured. This is the primary
   place to answer "what was written, by whom, when?" and to export evidence.
   The offline build has the same pattern via `LocalStore.appendAuditLog`
   (`frontend/lib/core/local_engine/local_store.dart`).
2. **Render / hosting logs** — the backend runs on Render. Note: Render's free
   tier **wipes local disk on every restart**, which is why every durable store
   (including the audit log) has a Supabase-when-configured path. If a
   production deployment is not Supabase-backed, the local-SQLite audit log
   lives on ephemeral disk — that is itself a gap against the 6-month retention
   rule and a reason to treat an un-Supabase deployment as risky.
3. **Supabase auth logs** — sign-in events, new devices, privilege changes.
   Anomalies here (a school admin account logging in from an unexpected
   location/IP) are a detection trigger on their own.
4. **Credential-exposure signals** — API keys appearing in logs, commit
   history, or a public repo; unexpected bursts of billable Sarvam API calls.
   Known pre-existing exposure to remediate: `config/config.toml` ships a live
   API key in plaintext (`llm_api_key`). This is a real, known risk to close,
   not hypothetical — treat any leak of that file as an incident.

## Severity classification (do this inside the first 30 minutes)

| Severity | Definition | Example | CERT-In report? |
|----------|-----------|---------|-----------------|
| **S1 — Critical** | Real student PII, answer images, or awarded marks known or reasonably believed to be exposed/leaked/altered | Answer-sheet images or a scan session left an S3/R2 bucket public; an API key with access to Supabase is in a public repo | Yes — report at T+6hr |
| **S2 — High** | Unauthorized access to systems, or identity-theft/phishing targeting users, even if no data is yet confirmed taken | A school admin account is compromised; a phishing page impersonates the app | Yes — report at T+6hr |
| **S3 — Medium** | Credential or configuration exposure with *no* evidence it reached student data | `config/config.toml` with the plaintext key is leaked internally, not publicly | Investigate; likely yes (unauthorized access/leak category) — report if any doubt |
| **S4 — Low** | Incident with no PII and no credential exposure | A grading bug produces wrong marks (goes to evaluation-precision review, not CERT-In) | No |

When in doubt between severities, classify up. The 6-hour duty is triggered by
*noticing* the event; "unclear" is not a reason to hold the clock.

## The checklist against the 6-hour CERT-In clock

Every step below is time-boxed. If a step slips, the 6-hour notification
deadline does **not** wait — the notifier files the report at T+6hr with
whatever is known, and appends the rest later.

### T+0 — Detection
- [ ] Anyone on the team becomes aware → **immediately** tell the Incident
      Commander. Recording awareness with a timestamp is the single most
      important action in this runbook — the CERT-In clock is 6 hours from
      *this* moment.
- [ ] IC starts a running incident log (plain text file or pinned channel
      message) with: time of awareness, who reported, what was seen, severity
      guess. Everything else in this runbook appends to it.
- [ ] IC pages/contacts the Technical lead and the CERT-In notifier. (Target:
      notified within 15 minutes of awareness.)

### T+30min — Triage and severity classification
- [ ] Technical lead checks the real detection sources: `AuditLog`
      `for_assessment()` / SQLite queries, Render logs, Supabase auth logs.
- [ ] Team confirms severity per the table above and writes one line in the
      incident log: severity, what data class is involved (PII / answer images /
      marks / credentials / none), and whether the 6-hour clock is running.
- [ ] IC declares: **"CERT-In report required"** or **"no report — S4,
      evaluation-precision issue"** — and records it. If required, the T+6hr
      filing is now on the notifier's calendar.

### T+1hr — Containment (assume the worst while you work)
- [ ] **Rotate credentials** that could reach student data, in this order:
      1. `SARVAM_API_KEY` (used by `vision.py`, `llm_evaluate.py`,
         `llm/sarvam.py`) — rotate at the Sarvam dashboard; the old key is dead
         immediately.
      2. Supabase keys (`SUPABASE_KNOWLEDGE_URL` / `SUPABASE_KNOWLEDGE_ANON_KEY`,
         and any service-role key if exposed) — rotate in the Supabase project,
         revoke the exposed key, then update env on Render.
      3. Any exposed Render or hosting secrets, and the plaintext `llm_api_key`
         in `config/config.toml` — rotate and **remove the key from the
         committed file** (move to an env var / secret store). Do not commit the
         rotated value.
- [ ] **Stop the bleeding**: if a credential is believed publicly exposed,
      revoke it first, then investigate. If an asset (bucket, endpoint) is
      believed public, restrict it now.
- [ ] Record every action taken (key rotated at HH:MM, etc.) in the incident log.

### T+2hr — Evidence preservation (do not wait for the investigation to finish)
- [ ] Export the relevant `audit_log` rows for the affected assessment(s) /
      time window to a read-only file. Local SQLite file lives at
      `<data_root>/audit/audit_log.sqlite`; in Supabase the rows are the
      `audit_log` table. Example (SQLite):
      ```sql
      .open <data_root>/audit/audit_log.sqlite
      .headers on
      .mode csv
      SELECT * FROM audit_log
      WHERE timestamp >= '<incident_start>'
        AND (assessment_id IN (...affected ids...) OR action LIKE '%export%');
      ```
- [ ] Export the same rows from the Dart offline log if the incident is
      client-side (`LocalStore.auditLog(assessmentId: ...)`).
- [ ] Preserve the Supabase auth log window and the relevant Render log window.
- [ ] Hash the exported evidence files (e.g. `Get-FileHash`/`sha256sum`) and
      record the hashes in the incident log — tamper-evident copies for the
      post-incident review and any regulator.
- [ ] The audit log is append-only by design; do not "clean up" rows during an
      incident.

### T+6hr — CERT-In notification deadline (the notifier files this, no exceptions)
- [ ] Notifier submits the report via the real channels:
      - Email: **incident@cert-in.org.in**
      - Portal: **https://www.cert-in.org.in/**
      - Helpline: **1800-11-4949**
- [ ] Include (even if partial — complete in a follow-up): who is reporting
      (the [COMPANY / CONTACT] acting on behalf of AcademicOS), what happened,
      when noticed, systems/data affected, severity, steps already taken, and a
      timeline. Being incomplete is acceptable; being late is not.
- [ ] Record the submission (time, reference/ack number) in the incident log.
- [ ] **Do not overstate readiness** in the filing: AcademicOS is not a
      registered/notified entity with a standing IR team unless that is actually
      true on the day; file as the operating party under the Directions.

## Downstream obligations (after the T+6hr filing)

- **DPDP Act 2023 — breach notification to the Data Protection Board and to
  affected users/parents.** Every affected data subject is a minor, so the
  school(s) must be told, and the school/processor must notify the affected
  guardians. The Act's "without undue delay" runs on top of CERT-In's 6-hour
  rule — do not treat the CERT-In filing as the end of notification duty.
- **Schools first, then guardians.** The school is the data controller (see
  `docs/dpa-template.md`); notify the school's named contact without undue
  delay and work with them on the parent-facing notice.
- **6-month minimum ICT log retention.** CERT-In requires logs be retained for
  at least 6 months. `audit_log.py` satisfies the *persistence* half by writing
  to SQLite/Supabase (not memory), but only if the deployment is actually
  Supabase-backed in production — on Render's ephemeral free-tier disk the local
  SQLite copy dies on restart. Confirm the production audit log is durable, and
  keep the exported incident evidence for at least 6 months as well.

## Post-incident review (run within 5 working days, however small the incident)

Fill this out and file it in the incident log. The point is the control gap, not
the blame.

- **Timeline**: noticed → contained → notified → closed (reconstruct from the
  incident log).
- **Root cause**: what actually happened, in one or two sentences.
- **What the audit log showed**: which `audit_log` rows (or their absence)
  told the story — e.g. "the grading write at 14:03 had `actor=null`" or "an
  export row carries `watermarkId exp_…` that matches the leaked copy."
- **What control gap allowed it**: name the missing control explicitly (e.g.
  "plaintext key committed in `config/config.toml`", "no Supabase-backed audit
  trail in production", "no MFA on the school-admin login").
- **Follow-up action items**: concrete, owned, dated items — e.g. remove the
  key from `config/config.toml` and move to env/secrets; enable Supabase-backed
  `AuditLog` in production; add a runbook drill; review the incident-response
  roster. Track them to done, not just to "discussed."
- **Runbook improvement**: anything this incident proved the runbook got wrong
  (unreachable phone numbers, a role that wasn't filled) gets fixed in this
  file.

## Before this runbook is used for real

- [ ] All `[NAME]` / `[PHONE]` brackets filled with people who have confirmed
      the role.
- [ ] The notifier has access to incident@cert-in.org.in from their mail client
      and has read https://www.cert-in.org.in/ once.
- [ ] A dry run of the T+0 → T+30min → T+1hr steps done at least once on a
      harmless simulated event (e.g. "a teammate finds an old key in a public
      gist").
- [ ] The plaintext `llm_api_key` in `config/config.toml` is rotated and moved
      to an env var / secret store.
- [ ] Production audit log confirmed Supabase-backed (durable past a Render
      restart).