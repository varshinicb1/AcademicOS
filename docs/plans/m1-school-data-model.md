# M1 — the school data model (plan)

Status: **draft, 2026-09-28.** Written after M0 went live (`09649eb`). Nothing here is built yet.

Every v3 product (the teacher app's timetable, leave and substitution; homework per section; the student
app; the dashboard filtered by section) needs the school modelled as it actually runs: sections, who
teaches what to whom, rooms, the bell, delegated admins, parents, and a way to load all of it at once.
Today the model stops short of that. This plan is the smallest set of changes that makes M2 (scheduling)
and M4/M5 (the apps) possible, in the order they depend on each other.

## What exists today (read from the code, 2026-09-28)

| Concept | Today | Where |
|---|---|---|
| Class and section | `Grade(number, section)` — the section is a **label on a grade row**; nothing is scheduled, enrolled or reported per section | `curriculum/models.py:57` |
| Who teaches what | `TeacherAssignment(teacher_id, book_id)` — a teacher teaches a **book**, with no section | `curriculum/models.py` (TeacherAssignment) |
| Periods per subject | `SubjectPeriodAllocation(subject, periods_per_week)` — **school-wide by subject name**, not per section | same |
| Timetable | `SubjectTimetableSlot(subject, day_of_week, period_number)` — school-wide, no section, teacher or room | same |
| The bell | `PeriodConfiguration(period_minutes)` — **one period length**; no breaks, assembly or zero period | same |
| Rooms | none | — |
| Roles | `teacher`, `principal`, `student` on the user row; routes gated `staff` / `principal` (`api/route_policy.py`, 37+ principal routes) | `assessment/users.py:148`, `auth_routes.py:176` |
| Delegated admin | none — a teacher either is the principal or is not | — |
| Parents | none (consent store exists: `ConsentStore`) | — |
| Bulk import | none; invites one at a time | — |

`CurriculumStore` holds the relational tables (SQLite, snapshot/restore to GCS on the GCP release);
`UserStore` holds users and invites (Cloud SQL through `postgres_kv.durable_table`).

## The changes, in dependency order

Each step is one pull request (`CONTRIBUTING.md`), gated on both suites, merged, deployed and verified
live before the next step that depends on it starts. Claim a step before starting it. M1.3 depends only on
M1.1, so it can run beside M1.2.

### M1.1 Sections as entities
- `Section(id, school_id, academic_year_id, grade_id, name, class_teacher_id?, home_room_id?)`,
  unique on (grade, name). A grade with no section gets one named "A" by migration, so every existing
  row keeps working; `Grade.section` values become `Section` rows.
- `StudentEnrollment` gains `section_id` (the grade is derived from it); the old `grade_id` stays for
  reads during the transition.
- Admin console: a Sections panel on Roster (add/rename/remove, class teacher). "Set up your school
  year" asks how many sections per class (default 1).
- Tests: migration on a copy of a seeded school; a student enrolled in 10-B is not in 10-A's reports.

### M1.2 Teaching allocations
- `TeachingAllocation(id, school_id, academic_year_id, section_id, subject_id, teacher_id,
  periods_per_week)` — the fact every later step reads: "Asha teaches Science to 10-B, 6 periods a week".
- Replaces `TeacherAssignment` (teacher × book) and `SubjectPeriodAllocation` (school-wide) for new
  flows; both stay readable, and a migration writes one allocation per existing assignment × section.
- The book a section studies stays the subject's chosen edition (`BookSelection`, PRD 12.7).
- Admin console: an allocation grid (sections × subjects, a teacher and a period count per cell), with
  the totals per teacher per week shown as the grid is filled (the first overload check M2 builds on).

### M1.3 Rooms and the bell
- `Room(id, school_id, name, kind: classroom|lab|hall|other, capacity?, subjects?)`.
- `BellSchedule(id, school_id, academic_year_id, name, days, slots[])`, each slot
  `(index, start, end, kind: teaching|break|assembly|zero)`; sections point at a schedule (default:
  the school's). Replaces `PeriodConfiguration.period_minutes`, which becomes the default slot length.
- Admin console: Calendar & Setup gains Bell schedule and Rooms cards.

### M1.4 Delegated admin (ROLE-1, ROLE-3)
- Capabilities: `users`, `calendar`, `timetable`, `leave`, `exams`, `qbank_review`, `reports`.
- `Grant(id, school_id, user_id, capability, scope{grades?, sections?, subjects?}, granted_by,
  granted_at, revoked_at?)` in `UserStore` (durable), every grant and revoke written to the audit log
  with before/after.
- `route_policy.py` gains a level per capability; each of today's principal routes is mapped to one
  (users: invites, `/auth/users`; calendar: calendar, holidays, terms, seeding; timetable: period
  configuration, slots, allocations, schedule, reschedule; exams: assessment approval, templates;
  reports: insights, coverage, paper timing, export). `require_capability(cap)` passes the principal
  and a teacher holding an active grant; `tests/test_role_gates.py` holds every route to its level.
- Scope checks (HOD/coordinator limited to grades/sections/subjects) apply on the routes that take a
  grade, section or subject.
- Admin console: a Staff permissions panel on Roster (grant/revoke per capability, with scope).

### M1.5 Parents
- Role `parent`; `Guardianship(parent_id, student_id, relation, verified_at?)` in `UserStore`.
- Parent invites (a student's guardian invite, single use); a parent reads their child's timetable,
  homework status and progress, never another child's (`authz` gains `require_guardian_of`).
- DPDP: the existing consent record (`docs/compliance.md`) is the parent's; the student app's parent
  mode (M5) reads through these routes.

### M1.6 Bulk import (INT-3, ROLE-2)
- `POST /admin/import/{kind}` for `sections`, `teachers` (creates invites), `students` (+ section),
  `parents` (+ link), `allocations`, `holidays`; CSV or XLSX; `?dryRun=true` returns every row with
  its outcome and errors before anything is written; the apply is all-or-nothing and audited.
- Templates downloadable from the console; an import screen that shows the dry run as a table.

## Measuring it

Adopt the v3 scorecard (`docs/REQUIREMENTS.md` §12) and run its baseline audit **before** M1.1, as
HANDOVER §7 says, so M1's effect is measured. M1 moves mainly v3's "Principal dashboard and admin"
(ADM-1, ROLE-1..4) and is the precondition for "Scheduling engine" (SCH-2/3).

## Open questions for the product owner

Each is marked with the step it blocks. Build nothing that depends on an answer until it is given.

1. **(M1.1, not blocking)** Sections per class: is "A, B, C…" enough, or do schools name them (e.g. "Rose",
   "Lotus")? The model takes any name; the default is letters.
2. **(M1.4)** Coordinators and HODs: one grant with a scope, or a separate role? Planned: a grant with a
   scope.
3. **(M1.5)** Parent accounts and linking in M1 with the parent screens in M5, or both in M5?
4. **(M1.6)** Bulk import: CSV only, or XLSX too from the start? XLSX adds `openpyxl`.
