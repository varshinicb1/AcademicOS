# AcademicOS — Product Requirements v3

**Adopted 2026-09-27 by the product owner.** This file is the source of truth for *what* to build.
Where `docs/PRD.md`, `docs/PRODUCTS_AND_RELEASES.md`, `docs/product-scorecard.md` or an older decision
disagrees, this file wins. `docs/HANDOVER.md` says what exists today and what to build first.

## 0. Decision record

The product owner's baseline, as stated on 2026-09-27:

> Web app with examination automation, including paper generation with the best question bank from
> grade 1 to grade 10, all main subjects, from any source (CBSE, NCERT textbooks, NCERT material,
> unofficial sources), with a marking scheme for every chapter, topic-wise and marks-wise. The question
> bank is also available as an API. A principal dashboard with everything and full admin access; some
> teachers can also have admin access. Teachers get a mobile app where class scheduling happens
> automatically, handling every edge case: academic calendar creation, teacher timetables, a teacher on
> leave and how those classes are compensated, and day-to-day assignments (homework) created from the
> question bank API. Students get an app showing that day's timetable and schedule, and their
> assignments. For both mobile apps, UI/UX is the top priority: very user friendly, with notifications,
> reminders and learning-progress tracking, and every integration and automation that can be done.
> This is the baseline; define the requirements needed to be the best in the market.

What this supersedes:

| Earlier decision | Now |
|---|---|
| PRD §0.4 "all grades 6-12", then 2026-09-23 "classes 6-10" | **Grades 1-10.** 11-12 are out of scope until a later decision |
| PRD §0.12 "primary surface: the teacher's offline Android phone", then 2026-09-22 "web-first; phone app out" | **Three products:** the web console, a **teacher app** and a **student app** (plus a parent view inside the student app) |
| PRD §0.1 "exam automation and calendar automation, nothing else" | Unchanged in spirit, but extended: **homework/assignments, leave and substitution, student-facing schedule and progress** are now in scope. Fees, admissions and transport stay out (not an ERP) |
| PRD §5A Q1 "without an answer key, no question" | Kept, and strengthened: **every served question has a marking scheme with value points**, from any source |
| Sources: CBSE/NCERT only | **Any source**, including unofficial ones, but every question carries its provenance and rights status, and unofficial or AI-assisted items are served only after review |

Still binding from `docs/PRD.md` §7 and §10: not an ERP, not a chatbot, no student data in the question-bank
API, DPDP Act 2023 and CERT-In, every query scoped by school, evidence-first (no number shown that is not
measured), no per-teacher rankings shown to staff, no leaderboards or streak mechanics aimed at children.

Priorities: **P0** = needed for the first sale of the three-app product; **P1** = needed to be best in
market within two releases; **P2** = later. Each requirement has an ID so code, tests and audits can
reference it.

## 1. Users and roles

| Role | Where | Can |
|---|---|---|
| Vendor super-admin | internal | onboard schools, manage content pipeline, issue API keys to partners |
| Principal / school owner | web (+ teacher app) | everything in their school |
| Delegated admin (a teacher granted admin) | web + teacher app | the admin permissions the principal grants: any of *users, calendar, timetable, leave & substitution, exams, question-bank review, reports* |
| Coordinator / HOD | web + teacher app | the same, limited to their grades/sections/subjects |
| Teacher | teacher app (+ web) | their timetable, lessons, homework, papers, leave |
| Student | student app | their timetable, homework, progress, practice |
| Parent / guardian | student app, parent mode | their child's timetable, homework status, progress, notices (read-only) |

- **ROLE-1 (P0)** Role-based access with **scopes** (school, grade, section, subject). Delegated admin is a
  permission set on a teacher account, granted and revoked by the principal, audited.
- **ROLE-2 (P0)** Invite-based onboarding: bulk CSV/Excel import of teachers, students, parents,
  sections and subjects; invite links/codes; Google sign-in (optional) and OTP sign-in for students/parents.
- **ROLE-3 (P0)** Every admin action is written to the immutable audit log (who, what, when, before/after).
- **ROLE-4 (P1)** Multi-campus: one owner, several schools, separate data per school.

## 2. Question bank (the core asset)

### 2.1 Coverage
- **QB-1 (P0)** Grades **1-10**, main subjects: English, Hindi, Mathematics, EVS (grades 1-5), Science
  (6-10), Social Science (6-10); third language and Computer Science **P1**.
- **QB-2 (P0)** For every grade × subject × **chapter** of the book the school chose, questions at **every
  marks value the paper patterns use** (e.g. 1, 2, 3, 4/5 marks) and of every type (MCQ, very short, short,
  long, case/source-based, assertion-reason, fill-in, match, true/false, diagrams/maps). Target minimum per
  chapter is configurable (default: 10 per marks value); the shortfall is **reported per chapter and topic**,
  never hidden.
- **QB-3 (P0)** Every question maps to board → grade → subject → book/edition → chapter → topic
  (→ subtopic where known). A question with no chapter is not offered for chapter-scoped papers.

### 2.2 Sources and provenance
- **QB-4 (P0)** Sources, in order of trust: CBSE board papers and marking schemes; CBSE sample papers +
  marking schemes; CBSE competency-based item banks; NCERT textbooks (in-text, exercises, end-of-chapter);
  NCERT Exemplar; NCERT lab manuals and other NCERT material; state-board and other public material;
  licensed publisher content; teacher-contributed questions; AI-assisted drafts.
- **QB-5 (P0)** Every question carries its **source, document, page, extraction method, rights status**
  and a **trust label**. Unofficial, teacher-contributed and AI-assisted items are **served only after a
  reviewer approves them** (review queue on the web, with the source shown beside the item).
- **QB-6 (P0)** Deduplication across sources (the CBSE copy wins), versioning, and an edit history.

### 2.3 Marking schemes
- **QB-7 (P0)** Every served question has an **answer key and a marking scheme with value points and marks
  per point** that sum to the question's marks; "any N of" schemes supported; MCQs have a verified option.
  A question without one is not served (PRD rule Q1).
- **QB-8 (P0)** Schemes print in a board-style answer key: value points, marks, and model answer; no raw
  marking codes (M1/A1/B1) without explanation.
- **QB-9 (P1)** Partial-credit schemes for multi-mark questions everywhere the source shows steps.

### 2.4 Quality
- **QB-10 (P0)** Nothing is served that a student cannot answer as printed: figures, tables, graphs and
  passages travel with the question (image assets), mathematics prints correctly (fractions, exponents,
  symbols), no source mark columns or headers inside stems. One serving gate decides this, measured for
  false positives.
- **QB-11 (P0)** Difficulty, Bloom level and competency type are **judged** (source label, reviewer, or a
  measured model with a published accuracy), never inferred from marks; an inferred value is flagged and not
  used for tiers.
- **QB-12 (P1)** Hindi (and later regional) questions in proper script; bilingual display where the source
  is bilingual.
- **QB-13 (P1)** A bank health report per grade × subject × chapter × topic × marks, with gaps named.

### 2.5 Question bank API (a product in its own right)
- **API-1 (P0)** REST `/v1`: search/filter by grade, subject, book, chapter, topic, marks, type,
  difficulty, competency, source/trust; get one question with its marking scheme; coverage; facets;
  cursor paging; documented errors.
- **API-2 (P0)** A **homework/assignment generation** endpoint: "N questions for this grade/section's
  chapter/topic, this mix of marks and types, avoiding questions the section has already had".
- **API-3 (P0)** API keys per partner/school, scoped (read-only, which grades/subjects), rate-limited,
  metered, revocable; keys issued from the web console; usage visible to the key owner.
- **API-4 (P0)** The API, the MCP server and the in-app paper builder serve **the same bank with the same
  filters** (one engine), held equal by tests.
- **API-5 (P0)** Never exposes student data.
- **API-6 (P1)** Webhooks for partners (new questions in a chapter), OpenAPI + SDK snippets.

## 3. Web console — examination automation

- **EX-1 (P0)** Paper builder: choose grade, subject, exam type (unit test, periodic, half-yearly, annual,
  class test), book chapters/topics, and a blueprint (CBSE pattern per grade, or a school template); the
  paper fills every section to the **exact marks** asked for, or says precisely why not before printing.
- **EX-2 (P0)** Quick paper, hand-picked paper, swap/pick/remove a question, internal choice (OR), parallel
  sets A/B/C with no repeated question across sets where the bank allows.
- **EX-3 (P0)** Differentiated versions (foundation/standard/advanced) that really differ, using judged
  difficulty; hidden when the bank cannot support them, with a sentence saying why.
- **EX-4 (P0)** CBSE competency share (≥50% where the pattern requires it) shown before printing.
- **EX-5 (P0)** Outputs: print-ready A4 PDF question paper and answer key/marking scheme with the school's
  name, logo, exam name, class, subject, time, marks and instructions; DOCX export (P1).
- **EX-6 (P1)** Review workflow: draft → HOD review → principal approval → locked; paper security (no
  student access before the exam; watermark; audit of every download).
- **EX-7 (P1)** Exam planning: datesheet builder, invigilation duty roster (uses the timetable and leave
  data), seating plan (P2).
- **EX-8 (P1)** Marks entry per question, result analysis per question/topic/class, CBSE-format report
  cards (P2). Existing answer-sheet scanning and rubric grading stay available (P2).
- **EX-9 (P0)** Time saved per paper is measured and shown (renewal criterion).

## 4. Web console — principal dashboard and full admin

- **ADM-1 (P0)** Everything a school configures, in one console: users and roles (ROLE-1..3), grades,
  sections, subjects, teacher-subject-section allocations, rooms/labs, academic calendar, timetable,
  leave approvals and substitutions, exams, question-bank review queue, API keys, notification settings.
- **ADM-2 (P0)** Dashboard, all per term and filterable by grade/section/subject:
  syllabus coverage vs plan (and where the year is behind), exam coverage (which classes/subjects have
  had a paper set, which not), time saved (labelled estimated), homework issued and completed,
  substitutions (requested, filled, unfilled, lost periods and compensated periods), question-bank
  coverage for the school's classes with gaps named, student progress aggregates.
- **ADM-3 (P0)** Alerts: a section falling behind, an unfilled substitution, a lost period not yet
  compensated, an exam paper not set by its deadline, homework overdue in bulk.
- **ADM-4 (P1)** Weekly principal digest (email/WhatsApp) and exportable reports (PDF/Excel).
- **ADM-5 (P0)** No per-teacher leaderboards; teacher-level data is visible to the principal and the
  teacher only.

## 5. Scheduling engine (serves the teacher app, the student app and the dashboard)

- **SCH-1 (P0) Academic calendar:** academic year, terms, working days, weekly offs (incl. alternate
  Saturdays), holidays (national, state, school; multi-day), exam windows, events, half-days; import a
  holiday list; publish to apps; ICS export/Google Calendar sync (P1).
- **SCH-2 (P0) Timetable model:** sections × days × periods × subject × teacher × room, with bell
  schedules (period lengths, breaks, assembly, zero period), periods per subject per week, labs and double
  periods, electives/optional subjects, combined classes.
- **SCH-3 (P0) Timetable generation:** a constraint solver produces a clash-free timetable for the whole
  school: no teacher/room/section double-booking; per-teacher max periods per day/week and max
  consecutive; subject distribution across the week; lab/double periods; teacher unavailability and
  preferences; fair first/last-period load. Manual edits with live clash detection; publish with a diff;
  re-solve after a change touching the fewest periods.
- **SCH-4 (P0) Lesson planning:** syllabus × timetable × calendar → a dated lesson plan per section and
  subject, with revision and exam-prep buffers; one-tap "taught / partly / not taught (why)" reflows the
  plan.
- **SCH-5 (P0) Teacher leave:** apply (full day, half day, specific periods; planned or same-day sudden),
  attach reason/document, approval by principal or delegated admin, auto-approval rules (P1), leave
  balances (P1).
- **SCH-6 (P0) Substitution:** on approval (or on a same-day absence), the engine proposes a substitute for
  every affected period: free at that time, qualified for the subject/grade first, fair load (fewest
  substitutions this week/month), not over max periods, same-section familiarity; the admin confirms or
  it auto-assigns by rule; the substitute is notified and accepts; lesson notes are handed over; a
  substitution register is kept.
- **SCH-7 (P0) Compensation of lost classes:** a period is "lost" when no qualified substitute takes the
  subject (a free period or another subject is run), when a holiday or closure is declared, or for events
  and exam days. The engine keeps a **per section-subject debt**, proposes make-up periods (the section's
  free periods, swaps with a colleague who agrees, extra periods within limits, or the next free slots
  before the unit's deadline), reflows the lesson plan, and reports debt and recovery on the dashboard.
- **SCH-8 (P0) Edge cases the engine must handle, each with a test:** a teacher joins or leaves mid-year
  (reallocate); long leave (temporary replacement teacher); two teachers absent for the same period;
  no free teacher at all (combine sections, supervised study, or mark lost); a substitute who is on leave
  later that day; a holiday declared retroactively or at short notice; an exam day or event that cancels
  teaching; half-days; section split or merge; a timetable change mid-term; electives across sections; a
  lab unavailable; a subject with multiple teachers or co-teaching; a teacher on exam duty; a day that
  becomes a working day (compensatory Saturday); time zones and DST are not an issue (IST), but dates are
  always the school's local date.
- **SCH-9 (P1)** Teacher attendance for the day (needed to trigger same-day substitution); student
  attendance is **not** in scope unless a school asks (not an ERP).

## 6. Teacher app (Android first, iOS P1) — UI/UX is the top priority

- **TA-1 (P0) Today:** my periods in order (time, section, subject, room, today's lesson topic), next-period
  countdown, substitution duties highlighted, changes since yesterday; one tap to mark a lesson taught,
  partly, or not taught with a reason (reflows the plan).
- **TA-2 (P0) Week and calendar views;** holidays, exams and events; my load.
- **TA-3 (P0) Leave:** apply in three taps, see status, write handover notes for the substitute; see my
  substitution duties and accept/decline.
- **TA-4 (P0) Homework and class tests from the question bank:** suggested automatically from today's
  lesson (chapter/topic), adjustable (count, marks, types, difficulty), due date, instructions, attach
  files; send to one or more sections; auto-graded objective items; manual or AI-assisted marking of
  written answers from photos (P1); submission status per student; reminders to students who have not
  submitted.
- **TA-5 (P0) Papers on the go:** open, review and share a paper/answer key built on the web; build a quick
  class test in the app.
- **TA-6 (P0) Class progress:** per section and topic, mastery from homework and tests; students who need
  help (visible to the teacher only).
- **TA-7 (P0) Notifications and reminders:** substitution assigned, leave decision, timetable change,
  period starting (optional), homework submissions, overdue marking, exam duty, digest at a chosen time.
- **TA-8 (P0) Offline-first:** today's and this week's timetable, lessons and homework cached; actions queue
  and sync; clear sync state.
- **TA-9 (P0) UX bar:** every main job in ≤3 taps; large touch targets; English and Hindi; light/dark;
  works on a ₹8,000 Android phone at 375 px; accessibility (TalkBack, font scaling); no dead ends — every
  error says what to do.

## 7. Student app (Android first, iOS P1) — UI/UX is the top priority

- **SA-1 (P0) Today:** that day's timetable (periods, subjects, teachers, rooms), substitutions and
  cancellations shown clearly; tomorrow's timetable after school hours; calendar of exams, holidays, events.
- **SA-2 (P0) Assignments:** list by due date; do objective work in the app, type short answers, or upload
  photos of written work; see marks and feedback; reminders before the due date.
- **SA-3 (P0) Learning progress:** per subject → chapter → topic mastery from homework, tests and practice;
  what to revise next; progress over the term. No leaderboards, no streak pressure.
- **SA-4 (P1) Practice:** adaptive practice from the bank for weak topics, with spaced revision; exam
  preparation mode before a scheduled exam.
- **SA-5 (P0) Notifications:** homework assigned and due, timetable changes, exam reminders, results;
  quiet hours (no notifications 21:00-07:00 by default) and a daily digest option.
- **SA-6 (P0) Parent mode:** a linked guardian sees the child's timetable, homework status, progress and
  school notices; receives notices by push/WhatsApp/SMS; gives verifiable parental consent (DPDP) before the
  student app collects a minor's data.
- **SA-7 (P0) Works for young children:** grades 1-5 get a simplified, picture-rich mode, read-aloud
  (TTS, P1), and a parent-operated default.
- **SA-8 (P0) Offline and low data;** under 30 MB install; works on shared family phones (profile switch).

## 8. Notifications, reminders and automation

- **NTF-1 (P0)** One notification service: in-app inbox, push (FCM), email; SMS and WhatsApp Business (P1);
  per-user channel preferences, quiet hours, digests, delivery tracking and retry; templates in English and
  Hindi. A notification is sent only when it is about the recipient's next action (docs/notifications.md).
- **NTF-2 (P0)** Scheduled automations: daily timetable/digest, homework due reminders, overdue alerts,
  substitution escalation if not accepted in N minutes, weekly principal digest, exam reminders,
  end-of-term reports.
- **NTF-3 (P0)** Event automations: leave approved → substitution proposal → notify; holiday declared →
  reflow plans → notify affected teachers/students; timetable published → notify; homework graded → notify
  student/parent.

## 9. Integrations

- **INT-1 (P0)** Firebase Cloud Messaging (push), email (existing mailer), Google sign-in.
- **INT-2 (P1)** WhatsApp Business API and SMS gateway (parents), Google Calendar/ICS, Google Classroom
  export of assignments, Microsoft Teams (P2).
- **INT-3 (P0)** Bulk import/export (CSV/Excel) for users, sections, timetables, holidays.
- **INT-4 (P1)** Indic language services (Sarvam: OCR of handwritten answers, translation of questions,
  TTS for young learners) behind the existing provider interface, never sending student PII without a
  DPA.
- **INT-5 (P2)** UDISE+ codes, CBSE portal exports, LMS (Moodle) and school ERPs via API.

## 10. Non-functional requirements

- **NFR-1 (P0) Privacy and compliance:** DPDP Act 2023 (verifiable parental consent for under-18s, purpose
  limitation, data minimisation, deletion on request, breach notification), CERT-In (6-hour reporting,
  180-day logs), per-school data isolation, encryption at rest and in transit, signed DPA per school.
- **NFR-2 (P0) Security:** RBAC with scopes on every route (the route policy table), invite-only
  registration, rate limiting, audit log, secrets in Secret Manager only.
- **NFR-3 (P0) Performance:** web first load < 10 s on Chrome's "Slow 4G" preset and < 3 s repeat; app cold
  start < 3 s on a low-end Android; timetable generation for a 40-section school < 60 s; paper generation
  < 5 s.
- **NFR-4 (P0) Reliability:** 99.5% monthly availability, daily backups, restore tested each term.
- **NFR-5 (P0) Accessibility:** WCAG 2.2 AA on web; TalkBack and font scaling on apps.
- **NFR-6 (P0) Localisation:** English and Hindi UI at launch; regional languages P1.
- **NFR-7 (P0) Observability:** error tracking, structured logs, per-school usage metrics, alerting.
- **NFR-8 (P0) Evidence:** every figure the product shows is measured or labelled estimated; releases are
  gated by both test suites and verified on the live system.

## 11. What makes it the best in the market

1. The question bank is **board-grade and honest**: every question keyed with value points, mapped to the
   school's book, gaps reported, provenance on every item. Competitors sell volume; we sell answerable,
   mapped, keyed questions.
2. **Scheduling that survives real school life**: leave, substitution and compensation handled
   automatically, with the debt of lost periods visible and recovered.
3. **Homework that writes itself** from today's lesson and the bank, and progress that follows from it.
4. **Principal sees the year**, not just reports: behind-schedule, unfilled, uncompensated, unset — as
   alerts with the next action.
5. **Mobile-first for teachers and students**, offline, Hindi, low-end phones, three taps.

## 12. Scorecard v3 (adopted 2026-09-30: `docs/product-scorecard-v3.md`)

The v2 scorecard (`docs/product-scorecard.md`, web-first, classes 6-10) measured the last release at 61.0.
It does not measure the three-app product. Proposed v3 areas and weights, each scored on the same
0/0.25/0.5/0.75/1.0 rubric; items are the requirement IDs above:

| # | Area | Weight | Items |
|---|---|---|---|
| 1 | Question bank: coverage, schemes, quality, provenance | 20 | QB-1..13 |
| 2 | Examination automation (web) | 15 | EX-1..9 |
| 3 | Scheduling engine | 15 | SCH-1..9 |
| 4 | Teacher app | 15 | TA-1..9 |
| 5 | Student app (incl. parent mode) | 10 | SA-1..8 |
| 6 | Principal dashboard and admin | 10 | ADM-1..5, ROLE-1..4 |
| 7 | Question bank API | 5 | API-1..6 |
| 8 | Notifications, automation, integrations | 5 | NTF-1..3, INT-1..5 |
| 9 | Release readiness and compliance | 5 | NFR-1..8 |

Scores under v3 are not comparable with v2 numbers; start a new audit log section.
