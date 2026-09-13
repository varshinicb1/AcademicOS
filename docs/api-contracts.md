# API Contracts — AcademicOS

Base Path: `/api/v1` (with `/v1` backward-compatible aliases for legacy graph and search endpoints).  
Authentication: Bearer token in `Authorization: Bearer <token>` or session cookies for role-gated routes.  
Standard Error Format: `{"detail": "Error explanation"}`

---

## 1. Authentication & User Management (`/api/v1/auth`)

| Method | Path | Role Required | Description |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | Public | Register a new user (`teacher`, `student`, or `principal` with bootstrap key) |
| `POST` | `/api/v1/auth/login` | Public | Authenticate user, returns session token and role |
| `POST` | `/api/v1/auth/logout` | Authenticated | Terminate session |
| `GET` | `/api/v1/auth/me` | Authenticated | Get current authenticated user profile |
| `GET` | `/api/v1/auth/users` | Principal | List school users (filterable by `role`: teacher, student) |

---

## 2. Curriculum & Scheduling (`/api/v1/curriculum`)

### Hierarchy & Navigation
| Method | Path | Role Required | Description |
|---|---|---|---|
| `GET` | `/api/v1/curriculum/boards` | Authenticated | List educational boards (e.g. CBSE) |
| `GET` | `/api/v1/curriculum/grades` | Authenticated | List active grades for a board |
| `GET` | `/api/v1/curriculum/subjects` | Authenticated | List subjects for grade (Mathematics, Science, etc.) |
| `GET` | `/api/v1/curriculum/units` | Authenticated | List units for a subject |
| `GET` | `/api/v1/curriculum/chapters` | Authenticated | List chapters for a unit/subject |
| `GET` | `/api/v1/curriculum/topics` | Authenticated | List topics for a chapter |
| `GET` | `/api/v1/curriculum/subtopics` | Authenticated | List subtopics for a topic |
| `PATCH` | `/api/v1/curriculum/{entity_type}/{id}/sequence` | Principal | Reorder delivery sequence of Unit/Chapter/Topic/Subtopic |

### Calendars, Holidays & Timetables
| Method | Path | Role Required | Description |
|---|---|---|---|
| `GET` | `/api/v1/curriculum/calendars` | Authenticated | Get academic calendar (terms, working days) |
| `POST` | `/api/v1/curriculum/calendars` | Principal | Create or update academic year calendar |
| `GET` | `/api/v1/curriculum/holidays` | Authenticated | List holidays (single date & multi-day blocks) |
| `POST` | `/api/v1/curriculum/holidays` | Principal | Add holiday or block holiday (`start_date`, `end_date`) |
| `GET` | `/api/v1/curriculum/timetable-slots` | Authenticated | Get per-subject weekly timetable schedule |
| `POST` | `/api/v1/curriculum/timetable-slots` | Principal | Configure weekly subject timetable slots |
| `GET` | `/api/v1/curriculum/period-allocations` | Authenticated | Get subject period allocations |
| `POST` | `/api/v1/curriculum/period-allocations` | Principal | Set subject target periods |

### Micro-Scheduling & Teaching Execution
| Method | Path | Role Required | Description |
|---|---|---|---|
| `POST` | `/api/v1/curriculum/schedule-book` | Principal | Generate automated day-by-day lesson schedule |
| `GET` | `/api/v1/curriculum/my-schedule` | Teacher | Get logged-in teacher's scheduled lessons |
| `PATCH` | `/api/v1/curriculum/scheduled-lessons/{id}` | Teacher/Principal | Mark lesson completed (Yes/No) with optional note |
| `POST` | `/api/v1/curriculum/reschedule` | Principal | Execute PUSH or ADJUST schedule shifting |
| `POST` | `/api/v1/curriculum/teacher-assignments` | Principal | Assign a teacher to a grade/subject book |
| `POST` | `/api/v1/curriculum/student-enrollments` | Principal | Enroll a student in a grade/section |
| `GET` | `/api/v1/curriculum/my-class-schedule` | Student | Student's upcoming 4-week class schedule |
| `GET` | `/api/v1/curriculum/my-progress` | Student | Student's completion progress by subject |

### Extraction & Question Tagging
| Method | Path | Role Required | Description |
|---|---|---|---|
| `POST` | `/api/v1/curriculum/extract-proposals` | Principal | Trigger LLM decomposition of chapters into topics/subtopics |
| `GET` | `/api/v1/curriculum/extraction-runs/{id}` | Principal | View extraction proposal review diffs |
| `POST` | `/api/v1/curriculum/approve-run/{id}` | Principal | Approve and commit extraction run into live topics/subtopics |
| `POST` | `/api/v1/curriculum/chapters/{id}/questions/tag` | Principal/Teacher | Tag question to canonical subtopic IDs |
| `POST` | `/api/v1/curriculum/questions/by-subtopics` | Authenticated | Query question IDs linked to subtopic IDs |

---

## 3. Assessment Designer & Question Bank (`/api/v1`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/assessments` | Create a new assessment draft or scheduled exam |
| `GET` | `/api/v1/assessments` | List assessments for school/teacher |
| `GET` | `/api/v1/assessments/{id}` | Get assessment detail, blueprint, and question list |
| `POST` | `/api/v1/questions/search` | Search questions by subject, grade, bloom, difficulty, chapters, subtopic IDs |
| `POST` | `/api/v1/generate-paper` | Generate balanced question paper and marking scheme from blueprint |
| `GET` | `/api/v1/papers/{id}/pdf` | Download formatted question paper PDF |
| `GET` | `/api/v1/papers/{id}/answer-key` | Retrieve official answer key and scoring criteria |
| `GET` | `/api/v1/templates` | List school assessment templates (CBSE standard, unit test, etc.) |
| `POST` | `/api/v1/templates` | Save customized school question paper layout template |

---

## 4. Mobile Scanning, Evaluation & Grading (`/api/v1`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/scan-sessions` | Initialize a mobile answer sheet scanning session |
| `POST` | `/api/v1/scan-pages` | Upload multi-page scan for perspective correction and OCR |
| `POST` | `/api/v1/evaluate` | Run rubric-based grading against student answer text |
| `GET` | `/api/v1/graded-evaluations/{id}` | Retrieve itemized scores, teacher feedback, and breakdown |
| `POST` | `/api/v1/audit-log` | Log an administrative or grading action to append-only audit trail |
| `GET` | `/api/v1/audit-log` | Query audit trail entries for student or assessment |

---

## 5. Knowledge Graph & Search (`/v1`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/v1/search` | Hybrid vector/BM25 search over textbook & QP chunks |
| `POST` | `/v1/graph/neighbors` | Traverse graph edges from a concept/node ID |
| `POST` | `/v1/graph/paths` | Find dependency and prerequisite paths between two nodes |
| `POST` | `/v1/agent/doubt` | Solve student doubt grounded in textbook evidence |
| `POST` | `/v1/study-plan` | Generate personalized spaced-repetition study schedule (FSRS) |
| `GET` | `/health` | Health check endpoint (used by keep-alive pings) |
