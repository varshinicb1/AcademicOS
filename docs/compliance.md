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

## Before you ship — per-feature checklist

Check every box that applies to the feature being built. Anything checked "no"
gets flagged to the user, not silently shipped.

- [ ] **New data store or new field holding student data?** → Is it encrypted at
      rest? (Android/offline: `SecureBox` + `HiveAesCipher` — done for the
      Hive-backed `LocalStore`. Key is held in a file in the app's own private
      data directory, OS-sandboxed but *not* hardware-Keystore-backed:
      `flutter_secure_storage` was tried first but its Windows plugin has a
      broken CMake/ATL packaging that blocks the desktop build entirely —
      swap back in once that's fixed upstream. Any *new* store, including
      server-side SQLite/Postgres tables, needs its own answer to this, not an
      assumption it inherits one.)
- [ ] **New endpoint or screen that reads/writes real student PII (name, roll
      number, answer images, scores)?** → Is access logged with who/when/what?
      (Built and verified end-to-end on both platforms: Android's `LocalStore.
      appendAuditLog` on `evaluateSheet`/`evaluateQuestion`, and the server-side
      `audit_log.py` — SQLite-local or Supabase, same pattern as every other
      store — wired into `/evaluations/sheet` and `/papers/{id}/export/{fmt}`.
      Any *new* write path to student data still needs its own call to this,
      it doesn't happen automatically.)
- [x] **Anything that could change a finalized grade?** → Is the change logged
      with a reason and a reviewer identity, not a silent overwrite? Every grading
      write is now logged (see above) and the scan-review flow has a real
      regrade path: `mobile_scan.review_decision`'s `regrade` action (and `edit`
      when it changes marks on an already-approved/edited item) requires a
      non-empty `reason` and `reviewer_id`, and every correction is appended to
      the server-side `audit_log` as a distinct `grade_regraded` action carrying
      `questionId`, `oldMarks`, `newMarks`, `reason`, `reviewerId`, and the
      automatic timestamp — wired through
      `POST /scan/sessions/{id}/review/{question_id}`. A first-time `edit` on a
      still-pending item stays reason-free (historical behavior, unchanged).
- [ ] **New third-party integration or vendor** (any API call leaving the
      device/server)? → Is there a DPA-equivalent understanding of what data
      crosses that boundary, and is it in the security notes for that platform's
      README?
- [ ] **New ingestion source** (a school's own uploaded papers/marking schemes)?
      → Copyright/license confirmation captured at upload time (see
      `docs/ingestion-plan.md` if/when that's written), file-type allowlist
      enforced, macros stripped from any Office document before parsing.
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
- [ ] **Touches real answer sheets or scores for the first time in a new
      context** (e.g. a new export format, a new analytics rollup)? → Re-run the
      evaluation-precision calibration, don't assume the last measured number
      still applies.

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
append-only audit logging on every grading write and every paper export on
both platforms, watermarked/traceable PDF exports, and one real calibration
run against a real teacher-graded dataset (not just cited literature). A
written incident-response runbook (`docs/incident-response-runbook.md`) and a
fillable DPA template for onboarding a real school (`docs/dpa-template.md`)
now also exist — as templates/runbooks requiring a human to fill in the
brackets and, for the DPA, legal review before adoption. They are **not**
evidence that an incident-response team, CERT-In registration, or a signed DPA
exists today.

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


Researched and documented, **not yet built**: the document-ingestion agent for
a real school's own content (blocked on actually getting documents from a
school). Investigation outcome (2026-08-16) on the two items that used to be
on this list: (1) the edit-existing-grade gap is **built** — see the regrade
checklist item above; (2) the principal-approval *lock* is **built** — see the
paper-release checklist item above. What is still genuinely absent is the
approval *workflow* itself: a principal user role, an explicit
"approve paper" action, and any notifications — no such workflow exists
anywhere in the product today (`principalApproved` was already a valid value of
`Assessment.status` but nothing ever set it or consumed it before this lock),
and no minimal real version of it can be built without deciding who the
principal is and how they authenticate, which is a product decision, not a
plumbing one. Recommended minimal version if it's ever pursued: a
`PATCH /assessments/{id}/approve` action gated on an authenticated principal
role that sets `status = principalApproved` (the lock then engages via the
existing `_require_editable` guard in `src/academicos/assessment/routes.py`)
and appends an `assessment_approved` entry to the same append-only `audit_log`
with the principal's identity — reusing the exact mechanisms this repo already
has rather than inventing new tables or a new workflow UI.

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

