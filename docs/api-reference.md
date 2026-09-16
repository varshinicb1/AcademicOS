# API reference (generated)

**Do not edit by hand.** Generated from the running application's OpenAPI
schema by `scripts/generate_api_reference.py`.

* **Base URL (Render release):** `https://academicos-backend.onrender.com`
* **Base URL (GCP release):** the Cloud Run service URL
* **Path prefix:** every operation is under `/api/v1` (the older `/v1/*`
  corpus/agent surface is also present and is now authenticated)
* **Live schema:** `GET /openapi.json` · **Interactive docs:** `GET /docs`

`Auth` is `bearer` when the operation requires an authenticated caller
(`Depends(get_current_user)` or `require_principal`), and `open` when it does
not. This column is derived from the schema's `security` field, which is only
populated because the auth dependency declares `HTTPBearer` — see
[`api.md`](api.md#contract-discipline).


**122 operations** across 19 domains — 104 require authentication, 18 are open.

## Contents

- [Assessments](#assessments) — 8 operations
- [Authentication](#authentication) — 5 operations
- [Blueprints](#blueprints) — 1 operations
- [Catalog](#catalog) — 2 operations
- [Curriculum, calendar, scheduling & reporting](#curriculum-calendar-scheduling--reporting) — 52 operations
- [Document ingestion](#document-ingestion) — 1 operations
- [Evaluations](#evaluations) — 4 operations
- [Health & diagnostics](#health--diagnostics) — 2 operations
- [Insights](#insights) — 2 operations
- [Learner knowledge & mastery](#learner-knowledge--mastery) — 2 operations
- [Legacy corpus & agent surface](#legacy-corpus--agent-surface) — 10 operations
- [Paper delivery](#paper-delivery) — 2 operations
- [Parental consent (DPDP)](#parental-consent-dpdp) — 4 operations
- [Practice](#practice) — 2 operations
- [Question bank](#question-bank) — 2 operations
- [Question papers](#question-papers) — 6 operations
- [Scan & capture](#scan--capture) — 9 operations
- [School templates](#school-templates) — 6 operations
- [Syllabus & pacing](#syllabus--pacing) — 2 operations


## Assessments

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `GET` | `/api/v1/assessments` | bearer | List Assessments |
| `POST` | `/api/v1/assessments` | bearer | Create Assessment |
| `DELETE` | `/api/v1/assessments/{assessment_id}` | bearer | Delete Assessment |
| `GET` | `/api/v1/assessments/{assessment_id}` | bearer | Get Assessment |
| `PUT` | `/api/v1/assessments/{assessment_id}` | bearer | Update Assessment |
| `POST` | `/api/v1/assessments/{assessment_id}/answer-key` | bearer | Make Answer Key |
| `PATCH` | `/api/v1/assessments/{assessment_id}/approve` | bearer | Approve Assessment |
| `PATCH` | `/api/v1/assessments/{assessment_id}/status` | bearer | Update Status |


## Authentication

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/v1/auth/login` | open | Login |
| `POST` | `/api/v1/auth/logout` | open | Logout |
| `GET` | `/api/v1/auth/me` | bearer | Me |
| `POST` | `/api/v1/auth/register` | open | Register |
| `GET` | `/api/v1/auth/users` | bearer | List School Users |


## Blueprints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/v1/blueprints/generate` | bearer | Generate Blueprint |


## Catalog

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `GET` | `/api/v1/catalog` | open | Catalog |
| `GET` | `/api/v1/catalog/{subject}/{grade}/chapters` | open | Catalog Chapters |


## Curriculum, calendar, scheduling & reporting

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `GET` | `/api/v1/curriculum/academic-years` | open | List Academic Years |
| `GET` | `/api/v1/curriculum/academic-years/{academic_year_id}/calendar` | bearer | Get Calendar |
| `POST` | `/api/v1/curriculum/academic-years/{academic_year_id}/calendar` | bearer | Create Calendar |
| `GET` | `/api/v1/curriculum/academic-years/{academic_year_id}/grades` | open | List Grades |
| `GET` | `/api/v1/curriculum/academic-years/{academic_year_id}/holidays` | bearer | List Holidays |
| `POST` | `/api/v1/curriculum/academic-years/{academic_year_id}/holidays` | bearer | Add Holiday |
| `POST` | `/api/v1/curriculum/academic-years/{academic_year_id}/period-configuration` | bearer | Set Period Configuration |
| `GET` | `/api/v1/curriculum/academic-years/{academic_year_id}/subject-period-allocations` | bearer | List Subject Period Allocations |
| `POST` | `/api/v1/curriculum/academic-years/{academic_year_id}/subject-period-allocations` | bearer | Set Subject Period Allocation |
| `GET` | `/api/v1/curriculum/academic-years/{academic_year_id}/timetable-slots` | bearer | List Timetable Slots |
| `POST` | `/api/v1/curriculum/academic-years/{academic_year_id}/timetable-slots` | bearer | Add Timetable Slot |
| `GET` | `/api/v1/curriculum/academic-years/{academic_year_id}/working-days` | bearer | Get Working Days |
| `GET` | `/api/v1/curriculum/boards` | open | List Boards |
| `GET` | `/api/v1/curriculum/books/{book_id}/chapters` | open | List Chapters |
| `GET` | `/api/v1/curriculum/books/{book_id}/schedule` | bearer | Get Book Schedule |
| `POST` | `/api/v1/curriculum/books/{book_id}/schedule` | bearer | Schedule Book |
| `POST` | `/api/v1/curriculum/books/{book_id}/schedule/push` | bearer | Push Schedule |
| `POST` | `/api/v1/curriculum/books/{book_id}/teaching-time-estimates` | bearer | Compute Teaching Time Estimates |
| `POST` | `/api/v1/curriculum/books/{book_id}/toc/ingest` | bearer | Ingest Textbook Toc |
| `GET` | `/api/v1/curriculum/books/{book_id}/units` | open | List Units |
| `POST` | `/api/v1/curriculum/chapters/{chapter_id}/extract` | bearer | Extract Chapter |
| `POST` | `/api/v1/curriculum/chapters/{chapter_id}/questions/tag` | bearer | Tag Question |
| `PATCH` | `/api/v1/curriculum/chapters/{chapter_id}/sequence` | bearer | Set Chapter Sequence |
| `GET` | `/api/v1/curriculum/chapters/{chapter_id}/topics` | open | List Topics |
| `POST` | `/api/v1/curriculum/chapters/{chapter_id}/topics` | bearer | Add Manual Topic |
| `GET` | `/api/v1/curriculum/export` | bearer | Export School Data |
| `GET` | `/api/v1/curriculum/extraction-runs/{run_id}` | bearer | Get Extraction Run |
| `POST` | `/api/v1/curriculum/extraction-runs/{run_id}/approve` | bearer | Approve Extraction Run |
| `GET` | `/api/v1/curriculum/grades/{grade_id}/subjects` | open | List Subjects |
| `GET` | `/api/v1/curriculum/my-class-schedule` | bearer | Get My Class Schedule |
| `GET` | `/api/v1/curriculum/my-progress` | bearer | Get My Progress |
| `GET` | `/api/v1/curriculum/my-schedule` | bearer | Get My Schedule |
| `POST` | `/api/v1/curriculum/questions/by-subtopics` | bearer | Questions By Subtopics |
| `GET` | `/api/v1/curriculum/reporting/coverage` | bearer | Get Coverage Report |
| `GET` | `/api/v1/curriculum/reporting/delayed-topics` | bearer | Get Delayed Topics |
| `GET` | `/api/v1/curriculum/schedule` | bearer | Get Schedule For Range |
| `PATCH` | `/api/v1/curriculum/scheduled-lessons/{lesson_id}` | bearer | Mark Lesson |
| `GET` | `/api/v1/curriculum/scheduled-lessons/{lesson_id}/history` | bearer | Get Lesson History |
| `POST` | `/api/v1/curriculum/scheduled-lessons/{lesson_id}/reschedule` | bearer | Adjust Lesson |
| `POST` | `/api/v1/curriculum/seed/cbse10` | bearer | Seed Cbse10 |
| `POST` | `/api/v1/curriculum/student-enrollments` | bearer | Enroll Student |
| `GET` | `/api/v1/curriculum/subjects/{subject_id}/books` | open | List Books |
| `DELETE` | `/api/v1/curriculum/subtopics/{subtopic_id}` | bearer | Delete Subtopic |
| `PATCH` | `/api/v1/curriculum/subtopics/{subtopic_id}` | bearer | Rename Subtopic |
| `PATCH` | `/api/v1/curriculum/subtopics/{subtopic_id}/sequence` | bearer | Set Subtopic Sequence |
| `GET` | `/api/v1/curriculum/subtopics/{subtopic_id}/teaching-time-estimate` | bearer | Get Teaching Time Estimate |
| `POST` | `/api/v1/curriculum/teacher-assignments` | bearer | Assign Teacher |
| `DELETE` | `/api/v1/curriculum/timetable-slots/{slot_id}` | bearer | Delete Timetable Slot |
| `PATCH` | `/api/v1/curriculum/topics/{topic_id}` | bearer | Rename Topic |
| `PATCH` | `/api/v1/curriculum/topics/{topic_id}/sequence` | bearer | Set Topic Sequence |
| `POST` | `/api/v1/curriculum/topics/{topic_id}/subtopics` | bearer | Add Manual Subtopic |
| `PATCH` | `/api/v1/curriculum/units/{unit_id}/sequence` | bearer | Set Unit Sequence |


## Document ingestion

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/v1/ingest/school-documents` | bearer | Ingest School Document |


## Evaluations

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/v1/evaluations/answer` | bearer | Evaluate One |
| `POST` | `/api/v1/evaluations/sheet` | bearer | Evaluate Sheet |
| `POST` | `/api/v1/evaluations/sheet/{assessment_id}/{student_id}/finalize` | bearer | Finalize Sheet Review |
| `POST` | `/api/v1/evaluations/sheet/{assessment_id}/{student_id}/review/{question_id}` | bearer | Review Sheet Answer |


## Health & diagnostics

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `GET` | `/health` | open | Health |
| `GET` | `/health/storage` | open | Health Storage |


## Insights

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `GET` | `/api/v1/insights/class/{assessment_id}` | bearer | Class Report |
| `GET` | `/api/v1/insights/school/{school_id}` | bearer | School Report |


## Learner knowledge & mastery

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `GET` | `/api/v1/knowledge/{student_id}` | bearer | Student Knowledge |
| `GET` | `/api/v1/knowledge/{student_id}/report` | bearer | Student Progress Report |


## Legacy corpus & agent surface

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `POST` | `/v1/agent/analyze` | bearer | Agent Analyze |
| `POST` | `/v1/agent/doubt` | bearer | Agent Doubt |
| `POST` | `/v1/agent/score` | bearer | Agent Score |
| `POST` | `/v1/graph/neighbors` | bearer | Graph Neighbors |
| `POST` | `/v1/graph/paths` | bearer | Graph Paths |
| `POST` | `/v1/plan` | bearer | Study Plan |
| `POST` | `/v1/question/solve` | bearer | Question Solve |
| `GET` | `/v1/registry/stats` | bearer | Registry Stats |
| `POST` | `/v1/revise` | bearer | Revise |
| `POST` | `/v1/search` | bearer | Search |


## Paper delivery

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/v1/mail/send-paper` | bearer | Send Paper |
| `GET` | `/api/v1/mail/status` | open | Mail Status |


## Parental consent (DPDP)

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `GET` | `/api/v1/consent` | bearer | List Consents |
| `POST` | `/api/v1/consent` | bearer | Record Consent |
| `DELETE` | `/api/v1/consent/students/{student_id}` | bearer | Revoke Consent |
| `GET` | `/api/v1/consent/students/{student_id}` | bearer | Get Student Consent |


## Practice

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/v1/practice/generate` | bearer | Generate Practice |
| `POST` | `/api/v1/practice/submit` | bearer | Submit Practice |


## Question bank

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/v1/questions/optimize` | bearer | Optimize Questions |
| `POST` | `/api/v1/questions/search` | bearer | Search Questions |


## Question papers

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/v1/papers/generate` | bearer | Generate Paper Endpoint |
| `POST` | `/api/v1/papers/generate-from-ids` | bearer | Generate From Ids |
| `POST` | `/api/v1/papers/quick-generate` | bearer | Quick Generate Paper |
| `GET` | `/api/v1/papers/{paper_id}` | bearer | Get Paper |
| `POST` | `/api/v1/papers/{paper_id}/export/{fmt}` | bearer | Export Paper |
| `GET` | `/api/v1/papers/{paper_id}/file` | bearer | Get Paper File |


## Scan & capture

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/v1/scan/sessions` | bearer | Create Scan Session |
| `GET` | `/api/v1/scan/sessions/{session_id}/corrected-pdf` | bearer | Get Corrected Pdf |
| `POST` | `/api/v1/scan/sessions/{session_id}/finalize` | bearer | Finalize Scan Session |
| `POST` | `/api/v1/scan/sessions/{session_id}/pages` | bearer | Upload Scan Page |
| `GET` | `/api/v1/scan/sessions/{session_id}/pages/{page_no}/image` | bearer | Get Page Image |
| `POST` | `/api/v1/scan/sessions/{session_id}/process` | bearer | Process Scan Session |
| `GET` | `/api/v1/scan/sessions/{session_id}/raw-pdf` | bearer | Get Raw Pdf |
| `GET` | `/api/v1/scan/sessions/{session_id}/review` | bearer | Get Scan Review |
| `POST` | `/api/v1/scan/sessions/{session_id}/review/{question_id}` | bearer | Submit Review Decision |


## School templates

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `GET` | `/api/v1/schools/{school_id}/paper-templates` | bearer | Get Paper Templates |
| `GET` | `/api/v1/schools/{school_id}/school-templates` | bearer | List Templates |
| `POST` | `/api/v1/schools/{school_id}/school-templates` | bearer | Save Template |
| `DELETE` | `/api/v1/schools/{school_id}/school-templates/{template_id}` | bearer | Delete Template |
| `GET` | `/api/v1/schools/{school_id}/school-templates/{template_id}/sections` | bearer | Template Sections |
| `GET` | `/api/v1/schools/{school_id}/templates` | bearer | Get Section Templates |


## Syllabus & pacing

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `GET` | `/api/v1/syllabus/{subject}/{grade}` | open | Get Syllabus |
| `GET` | `/api/v1/syllabus/{subject}/{grade}/timetable` | open | Get Timetable |

