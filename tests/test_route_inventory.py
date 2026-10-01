"""Hermetic route-inventory tests: every backend route the Flutter clients
(`api_client.dart`, `pillar_api.dart`) could hit, exercised end-to-end.

Three groups, in file order (order matters):

1. **Canonical-set guard** — enumerates the live FastAPI app programmatically
   and asserts it equals the 59-route inventory below. Adding/removing/renaming
   any backend route fails this test loudly until the inventory and its
   exercise table are updated too.

2. **Startup-free** — a bare `TestClient(app)` (no context manager, so the
   startup event never runs). Proves non-gated routes work before init and
   runtime-gated routes return 503, never 404. Runs before any `with
   TestClient(app)` below (startup permanently sets module globals); skips
   when a previously-ordered test file already booted the app.

3. **Full boot** — `ACOS_DATA_ROOT` points at a pytest `tmp_path` before
   entering `with TestClient(app)`. Walks every route in the inventory with a
   valid request (200) and a proper-4xx case (missing id / invalid body),
   including the full assessment → paper → export lifecycle and the mobile
   scan-session error paths.

Never starts uvicorn; never binds a port; never calls out to the network.
"""
from __future__ import annotations

import pytest

from academicos.assessment import audit_log
from academicos.assessment import mobile_scan, routes as assessment_routes
from academicos.api.main import app

from _auth_helpers import grant_consent, invite_code

# Canonical backend route inventory. Keeping it explicit (not derived from
# openapi at runtime) is the point: it is the contract every Dart call is
# judged against, and it fails loudly when the backend drifts.
API_ROUTES: frozenset[tuple[str, str]] = frozenset({
    # --- routes.py (assessment designer) ---
    ("POST", "/api/v1/blueprints/generate"),
    ("GET", "/api/v1/schools/{school_id}/templates"),
    ("GET", "/api/v1/schools/{school_id}/paper-templates"),
    ("POST", "/api/v1/questions/search"),
    ("POST", "/api/v1/questions/optimize"),
    ("POST", "/api/v1/papers/generate"),
    ("POST", "/api/v1/papers/quick-generate"),
    ("POST", "/api/v1/papers/generate-from-ids"),
    ("GET", "/api/v1/paper-timing"),
    ("GET", "/api/v1/papers/{paper_id}"),
    ("POST", "/api/v1/papers/{paper_id}/export/{fmt}"),
    ("GET", "/api/v1/papers/{paper_id}/file"),
    ("POST", "/api/v1/assessments"),
    ("GET", "/api/v1/assessments"),
    ("GET", "/api/v1/assessments/{assessment_id}"),
    ("PUT", "/api/v1/assessments/{assessment_id}"),
    ("DELETE", "/api/v1/assessments/{assessment_id}"),
    ("PATCH", "/api/v1/assessments/{assessment_id}/status"),
    ("PATCH", "/api/v1/assessments/{assessment_id}/approve"),
    # --- paper_template_routes.py (teacher paper templates, Task 901) ---
    ("GET", "/api/v1/schools/{school_id}/teacher-templates"),
    ("POST", "/api/v1/schools/{school_id}/teacher-templates"),
    ("GET", "/api/v1/schools/{school_id}/teacher-templates/{template_id}"),
    ("PUT", "/api/v1/schools/{school_id}/teacher-templates/{template_id}"),
    ("DELETE", "/api/v1/schools/{school_id}/teacher-templates/{template_id}"),
    ("POST", "/api/v1/schools/{school_id}/teacher-templates/{template_id}/share"),
    ("POST", "/api/v1/schools/{school_id}/teacher-templates/{template_id}/duplicate"),
    ("POST", "/api/v1/schools/{school_id}/teacher-templates/{template_id}/availability"),
    ("POST", "/api/v1/papers/generate-from-template"),
    ("POST", "/api/v1/papers/{paper_id}/questions/{slot}/swap"),
    ("POST", "/api/v1/papers/{paper_id}/questions/{slot}"),
    ("DELETE", "/api/v1/papers/{paper_id}/questions/{slot}"),
    # --- auth_routes.py (teacher/principal identity) ---
    ("POST", "/api/v1/auth/register"),
    ("POST", "/api/v1/auth/login"),
    ("POST", "/api/v1/auth/logout"),
    ("GET", "/api/v1/auth/me"),
    ("GET", "/api/v1/auth/users"),
    ("POST", "/api/v1/auth/users/{user_id}/close"),
    ("POST", "/api/v1/auth/users/{user_id}/reopen"),
    ("POST", "/api/v1/auth/invites"),
    ("GET", "/api/v1/auth/invites"),
    ("DELETE", "/api/v1/auth/invites/{code}"),
    # --- pillar_routes.py (syllabus, grading, insights) ---
    ("GET", "/api/v1/schools/{school_id}/school-templates"),
    ("POST", "/api/v1/schools/{school_id}/school-templates"),
    ("GET", "/api/v1/schools/{school_id}/school-templates/{template_id}/sections"),
    ("DELETE", "/api/v1/schools/{school_id}/school-templates/{template_id}"),
    ("POST", "/api/v1/assessments/{assessment_id}/answer-key"),
    ("GET", "/api/v1/catalog"),
    ("GET", "/api/v1/catalog/{subject}/{grade}/chapters"),
    ("GET", "/api/v1/syllabus/{subject}/{grade}"),
    ("GET", "/api/v1/syllabus/{subject}/{grade}/timetable"),
    ("GET", "/api/v1/mail/status"),
    ("POST", "/api/v1/mail/send-paper"),
    ("POST", "/api/v1/evaluations/answer"),
    ("POST", "/api/v1/evaluations/sheet"),
    ("POST", "/api/v1/evaluations/sheet/{assessment_id}/{student_id}/review/{question_id}"),
    ("POST", "/api/v1/evaluations/sheet/{assessment_id}/{student_id}/finalize"),
    ("GET", "/api/v1/evaluations/assessment/{assessment_id}/question/{question_id}"),
    ("POST", "/api/v1/evaluations/assessment/{assessment_id}/question/{question_id}/award"),
    ("GET", "/api/v1/knowledge/{student_id}"),
    ("GET", "/api/v1/knowledge/{student_id}/report"),
    ("POST", "/api/v1/practice/generate"),
    ("POST", "/api/v1/practice/submit"),
    ("GET", "/api/v1/insights/class/{assessment_id}"),
    ("GET", "/api/v1/insights/school/{school_id}"),
    # --- mobile_routes.py (scan-and-grade) ---
    ("POST", "/api/v1/scan/sessions"),
    ("POST", "/api/v1/scan/sessions/{session_id}/pages"),
    ("POST", "/api/v1/scan/sessions/{session_id}/process"),
    ("GET", "/api/v1/scan/sessions/{session_id}/review"),
    ("POST", "/api/v1/scan/sessions/{session_id}/review/{question_id}"),
    ("POST", "/api/v1/scan/sessions/{session_id}/finalize"),
    ("GET", "/api/v1/scan/sessions/{session_id}/pages/{page_no}/image"),
    ("GET", "/api/v1/scan/sessions/{session_id}/raw-pdf"),
    ("GET", "/api/v1/scan/sessions/{session_id}/corrected-pdf"),
    # --- api/main.py (v1 public surface) ---
    ("GET", "/health"),
    ("GET", "/health/llm"),
    ("GET", "/v1/registry/stats"),
    # --- the question-bank API (assessment/qbank_routes.py) ---
    # Separate auth from everything above: these take a scoped API key, not a
    # user bearer token. Their paths are part of a published contract third
    # parties build against, so they are fixed as `GET /v1/questions` and
    # friends per docs/question-bank-api.md.
    ("GET", "/v1/questions"),
    ("GET", "/v1/questions/{question_id}"),
    ("GET", "/v1/questions/{question_id}/scheme"),
    ("GET", "/v1/subtopics/{subtopic_id:path}/questions"),
    ("GET", "/v1/facets"),
    # Answer-key coverage per subject x class. The same numbers the MCP
    # server's coverage_report returns, from the same function (rule Q5).
    ("GET", "/v1/coverage"),
    ("POST", "/v1/search"),
    ("POST", "/v1/agent/doubt"),
    ("POST", "/v1/agent/score"),
    ("POST", "/v1/agent/analyze"),
    ("POST", "/v1/graph/neighbors"),
    ("POST", "/v1/graph/paths"),
    ("POST", "/v1/revise"),
    ("POST", "/v1/plan"),
    ("POST", "/v1/question/solve"),
    # --- ingest_routes.py (a school's own document uploads) ---
    ("POST", "/api/v1/ingest/school-documents"),
    # --- curriculum/routes.py (docs/ACADEMIC_DATA_MODEL.md) ---
    ("GET", "/api/v1/curriculum/boards"),
    ("GET", "/api/v1/curriculum/academic-years"),
    ("GET", "/api/v1/curriculum/academic-years/{academic_year_id}/grades"),
    ("GET", "/api/v1/curriculum/grades/{grade_id}/subjects"),
    ("GET", "/api/v1/curriculum/academic-years/{academic_year_id}/sections"),
    ("POST", "/api/v1/curriculum/grades/{grade_id}/sections"),
    ("PATCH", "/api/v1/curriculum/sections/{section_id}"),
    ("DELETE", "/api/v1/curriculum/sections/{section_id}"),
    ("GET", "/api/v1/curriculum/sections/{section_id}/students"),
    ("GET", "/api/v1/curriculum/academic-years/{academic_year_id}/allocations"),
    ("PUT", "/api/v1/curriculum/sections/{section_id}/allocations/{subject_id}"),
    ("DELETE", "/api/v1/curriculum/sections/{section_id}/allocations/{subject_id}"),
    ("GET", "/api/v1/curriculum/academic-years/{academic_year_id}/teacher-load"),
    ("GET", "/api/v1/curriculum/rooms"),
    ("POST", "/api/v1/curriculum/rooms"),
    ("PATCH", "/api/v1/curriculum/rooms/{room_id}"),
    ("DELETE", "/api/v1/curriculum/rooms/{room_id}"),
    ("GET", "/api/v1/curriculum/academic-years/{academic_year_id}/bell-schedules"),
    ("POST", "/api/v1/curriculum/academic-years/{academic_year_id}/bell-schedules"),
    ("PUT", "/api/v1/curriculum/bell-schedules/{bell_schedule_id}"),
    ("DELETE", "/api/v1/curriculum/bell-schedules/{bell_schedule_id}"),
    ("PUT", "/api/v1/curriculum/sections/{section_id}/bell-schedule"),
    ("GET", "/api/v1/curriculum/academic-years/{academic_year_id}/timetable"),
    ("GET", "/api/v1/curriculum/sections/{section_id}/timetable"),
    ("PUT", "/api/v1/curriculum/sections/{section_id}/timetable"),
    ("GET", "/api/v1/curriculum/my-timetable"),
    ("POST", "/api/v1/curriculum/academic-years/{academic_year_id}/timetable/solve"),
    ("GET", "/api/v1/curriculum/academic-years/{academic_year_id}/teacher-unavailability"),
    ("PUT", "/api/v1/curriculum/academic-years/{academic_year_id}/teacher-unavailability/{teacher_id}"),
    ("GET", "/api/v1/curriculum/academic-years/{academic_year_id}/room-unavailability"),
    ("PUT", "/api/v1/curriculum/academic-years/{academic_year_id}/room-unavailability/{room_id}"),
    ("GET", "/api/v1/curriculum/school-profile"),
    ("PUT", "/api/v1/curriculum/school-profile"),
    ("GET", "/api/v1/curriculum/school-profile/logo"),
    ("POST", "/api/v1/curriculum/school-profile/logo"),
    ("DELETE", "/api/v1/curriculum/school-profile/logo"),
    ("POST", "/api/v1/curriculum/leave-requests"),
    ("GET", "/api/v1/curriculum/leave-requests"),
    ("POST", "/api/v1/curriculum/leave-requests/{leave_id}/decision"),
    ("POST", "/api/v1/curriculum/leave-requests/{leave_id}/cancel"),
    ("POST", "/api/v1/curriculum/leave-requests/{leave_id}/document"),
    ("GET", "/api/v1/curriculum/leave-requests/{leave_id}/document"),
    ("GET", "/api/v1/curriculum/substitutions"),
    ("GET", "/api/v1/curriculum/substitutions/{sub_id}/candidates"),
    ("POST", "/api/v1/curriculum/substitutions/{sub_id}/assign"),
    ("POST", "/api/v1/curriculum/substitutions/{sub_id}/respond"),
    ("GET", "/api/v1/curriculum/academic-years/{academic_year_id}/lost-periods"),
    ("GET", "/api/v1/curriculum/lost-periods/{lost_id}/compensation-options"),
    ("POST", "/api/v1/curriculum/lost-periods/{lost_id}/compensate"),
    ("POST", "/api/v1/curriculum/lost-periods/{lost_id}/waive"),
    ("POST", "/api/v1/curriculum/academic-years/{academic_year_id}/closures"),
    ("GET", "/api/v1/curriculum/day"),
    ("GET", "/api/v1/curriculum/my-day"),
    ("GET", "/api/v1/curriculum/academic-years/{academic_year_id}/cover-summary"),
    ("GET", "/api/v1/curriculum/teacher-attendance"),
    ("PUT", "/api/v1/curriculum/teacher-attendance"),
    ("POST", "/api/v1/curriculum/my-attendance"),
    ("GET", "/api/v1/notifications"),
    ("POST", "/api/v1/notifications/{notification_id}/read"),
    ("POST", "/api/v1/notifications/read-all"),
    ("GET", "/api/v1/notification-preferences"),
    ("PUT", "/api/v1/notification-preferences"),
    ("POST", "/api/v1/devices"),
    ("DELETE", "/api/v1/devices/{token}"),
    ("POST", "/api/v1/automations/run"),
    ("GET", "/api/v1/automations/status"),
    ("GET", "/api/v1/admin/grants"),
    ("POST", "/api/v1/admin/grants"),
    ("DELETE", "/api/v1/admin/grants/{grant_id}"),
    ("GET", "/api/v1/my-grants"),
    ("GET", "/api/v1/staff"),
    ("GET", "/api/v1/dashboard/summary"),
    ("GET", "/api/v1/dashboard/term"),
    ("GET", "/api/v1/dashboard/term/export"),
    ("GET", "/api/v1/calendar-feed"),
    ("POST", "/api/v1/calendar-feed/reset"),
    ("GET", "/api/v1/my-calendar"),
    ("GET", "/api/v1/my-load"),
    ("POST", "/api/v1/curriculum/academic-years/{academic_year_id}/lesson-plans"),
    ("GET", "/api/v1/ics/{token}.ics"),
    ("POST", "/v1/homework-sets"),
    ("POST", "/api/v1/my-homework/{homework_id}/photos"),
    ("GET", "/api/v1/my-homework/{homework_id}/photos"),
    ("GET", "/api/v1/my-homework/{homework_id}/photos/{photo_id}"),
    ("DELETE", "/api/v1/my-homework/{homework_id}/photos/{photo_id}"),
    ("GET", "/api/v1/homework/{homework_id}/submissions/{student_id}/photos/{photo_id}"),
    ("POST", "/api/v1/my-practice"),
    ("GET", "/api/v1/my-practice"),
    ("GET", "/api/v1/my-practice/{practice_id}"),
    ("POST", "/api/v1/my-practice/{practice_id}/submit"),
    ("GET", "/api/v1/sections/{section_id}/progress"),
    ("POST", "/api/v1/auth/code/request"),
    ("POST", "/api/v1/auth/code/verify"),
    ("GET", "/api/v1/auth/providers"),
    ("GET", "/api/v1/qbank/coverage-map"),
    ("GET", "/api/v1/qbank/review-queue"),
    ("POST", "/api/v1/qbank/review/{question_id}"),
    ("POST", "/api/v1/auth/google"),
    ("GET", "/api/v1/homework/suggestion"),
    ("POST", "/api/v1/homework"),
    ("GET", "/api/v1/homework"),
    ("GET", "/api/v1/homework/{homework_id}"),
    ("POST", "/api/v1/homework/{homework_id}/publish"),
    ("POST", "/api/v1/homework/{homework_id}/close"),
    ("GET", "/api/v1/homework/{homework_id}/submissions"),
    ("POST", "/api/v1/homework/{homework_id}/submissions/{student_id}/grade"),
    ("POST", "/api/v1/homework/{homework_id}/remind"),
    ("GET", "/api/v1/my-homework"),
    ("GET", "/api/v1/my-homework/{homework_id}"),
    ("POST", "/api/v1/my-homework/{homework_id}/submit"),
    ("GET", "/api/v1/my-learning"),
    ("GET", "/api/v1/students/{student_id}/learning"),
    ("POST", "/api/v1/students/{student_id}/guardian-invites"),
    ("GET", "/api/v1/students/{student_id}/guardians"),
    ("POST", "/api/v1/guardianships"),
    ("DELETE", "/api/v1/guardianships/{parent_id}/{student_id}"),
    ("GET", "/api/v1/my-children"),
    ("GET", "/api/v1/children/{student_id}/timetable"),
    ("GET", "/api/v1/children/{student_id}/day"),
    ("GET", "/api/v1/children/{student_id}/homework"),
    ("GET", "/api/v1/children/{student_id}/homework/{homework_id}"),
    ("POST", "/api/v1/children/{student_id}/homework/{homework_id}/submit"),
    ("GET", "/api/v1/children/{student_id}/learning"),
    ("GET", "/api/v1/children/{student_id}/consent"),
    ("POST", "/api/v1/children/{student_id}/consent"),
    ("DELETE", "/api/v1/children/{student_id}/consent"),
    ("POST", "/api/v1/admin/import/{kind}"),
    ("GET", "/api/v1/admin/import/{kind}/template"),
    ("GET", "/api/v1/admin/export/{kind}"),
    ("POST", "/api/v1/api-keys"),
    ("GET", "/api/v1/api-keys"),
    ("DELETE", "/api/v1/api-keys/{key_id}"),
    ("GET", "/api/v1/api-keys/{key_id}/usage"),
    ("POST", "/api/v1/assessments/{assessment_id}/review-request"),
    ("POST", "/api/v1/assessments/{assessment_id}/review-decision"),
    ("GET", "/api/v1/assessments/{assessment_id}/reviews"),
    ("GET", "/api/v1/paper-reviews"),
    ("PUT", "/api/v1/papers/{paper_id}/marks"),
    ("GET", "/api/v1/papers/{paper_id}/marks"),
    ("GET", "/api/v1/papers/{paper_id}/analysis"),
    ("POST", "/api/v1/exams"),
    ("GET", "/api/v1/exams"),
    ("GET", "/api/v1/exams/{exam_id}"),
    ("PUT", "/api/v1/exams/{exam_id}/datesheet"),
    ("POST", "/api/v1/exams/{exam_id}/invigilation/auto"),
    ("PUT", "/api/v1/exams/{exam_id}/invigilation"),
    ("POST", "/api/v1/exams/{exam_id}/publish"),
    ("GET", "/api/v1/my-exams"),
    ("GET", "/api/v1/curriculum/subjects/{subject_id}/books"),
    ("POST", "/api/v1/curriculum/subjects/{subject_id}/books"),
    ("GET", "/api/v1/curriculum/subjects/{subject_id}/selected-book"),
    ("PUT", "/api/v1/curriculum/subjects/{subject_id}/selected-book"),
    ("GET", "/api/v1/curriculum/books/{book_id}/units"),
    ("GET", "/api/v1/curriculum/books/{book_id}/chapters"),
    ("POST", "/api/v1/curriculum/books/{book_id}/toc/ingest"),
    ("POST", "/api/v1/curriculum/seed/cbse10"),
    ("POST", "/api/v1/curriculum/seed/cbse"),
    ("GET", "/api/v1/curriculum/chapters/{chapter_id}/topics"),
    # The same read keyed by the SYLLABUS slug the Assessment Designer holds
    # (/catalog's chapterId), which is the only chapter id that screen has.
    ("GET", "/api/v1/curriculum/chapters/by-slug/{subject}/{grade}/{slug}/topics"),
    ("GET", "/api/v1/curriculum/chapters/{chapter_id}/proposed-topics"),
    ("POST", "/api/v1/curriculum/chapters/{chapter_id}/topics/approve-all"),
    ("POST", "/api/v1/curriculum/chapters/{chapter_id}/extract"),
    ("GET", "/api/v1/curriculum/extraction-runs/{run_id}"),
    ("POST", "/api/v1/curriculum/extraction-runs/{run_id}/approve"),
    ("POST", "/api/v1/curriculum/chapters/{chapter_id}/topics"),
    ("POST", "/api/v1/curriculum/topics/{topic_id}/subtopics"),
    ("PATCH", "/api/v1/curriculum/topics/{topic_id}"),
    ("PATCH", "/api/v1/curriculum/subtopics/{subtopic_id}"),
    ("DELETE", "/api/v1/curriculum/subtopics/{subtopic_id}"),
    ("PATCH", "/api/v1/curriculum/units/{unit_id}/sequence"),
    ("PATCH", "/api/v1/curriculum/chapters/{chapter_id}/sequence"),
    ("PATCH", "/api/v1/curriculum/topics/{topic_id}/sequence"),
    ("PATCH", "/api/v1/curriculum/subtopics/{subtopic_id}/sequence"),
    ("POST", "/api/v1/curriculum/chapters/{chapter_id}/questions/tag"),
    ("POST", "/api/v1/curriculum/questions/by-subtopics"),
    ("POST", "/api/v1/curriculum/academic-years/{academic_year_id}/calendar"),
    ("PUT", "/api/v1/curriculum/academic-years/{academic_year_id}/calendar"),
    ("GET", "/api/v1/curriculum/academic-years/{academic_year_id}/calendar"),
    ("POST", "/api/v1/curriculum/academic-years/{academic_year_id}/holidays"),
    ("GET", "/api/v1/curriculum/academic-years/{academic_year_id}/holidays"),
    ("DELETE", "/api/v1/curriculum/academic-years/{academic_year_id}/holidays/{holiday_id}"),
    ("POST", "/api/v1/curriculum/academic-years/{academic_year_id}/terms"),
    ("GET", "/api/v1/curriculum/academic-years/{academic_year_id}/terms"),
    ("GET", "/api/v1/curriculum/terms/current"),
    ("PUT", "/api/v1/curriculum/terms/{term_id}"),
    ("DELETE", "/api/v1/curriculum/terms/{term_id}"),
    ("PUT", "/api/v1/curriculum/terms/{term_id}/baseline"),
    ("POST", "/api/v1/curriculum/academic-years/{academic_year_id}/period-configuration"),
    ("POST", "/api/v1/curriculum/academic-years/{academic_year_id}/subject-period-allocations"),
    ("GET", "/api/v1/curriculum/academic-years/{academic_year_id}/subject-period-allocations"),
    ("POST", "/api/v1/curriculum/academic-years/{academic_year_id}/timetable-slots"),
    ("GET", "/api/v1/curriculum/academic-years/{academic_year_id}/timetable-slots"),
    ("DELETE", "/api/v1/curriculum/timetable-slots/{slot_id}"),
    ("GET", "/api/v1/curriculum/academic-years/{academic_year_id}/working-days"),
    ("POST", "/api/v1/curriculum/books/{book_id}/teaching-time-estimates"),
    ("GET", "/api/v1/curriculum/subtopics/{subtopic_id}/teaching-time-estimate"),
    ("POST", "/api/v1/curriculum/books/{book_id}/schedule"),
    ("GET", "/api/v1/curriculum/books/{book_id}/schedule"),
    ("GET", "/api/v1/curriculum/schedule"),
    ("POST", "/api/v1/curriculum/teacher-assignments"),
    ("GET", "/api/v1/curriculum/my-schedule"),
    ("PATCH", "/api/v1/curriculum/scheduled-lessons/{lesson_id}"),
    ("POST", "/api/v1/curriculum/scheduled-lessons/{lesson_id}/reschedule"),
    ("POST", "/api/v1/curriculum/books/{book_id}/schedule/push"),
    ("GET", "/api/v1/curriculum/scheduled-lessons/{lesson_id}/history"),
    ("POST", "/api/v1/curriculum/student-enrollments"),
    ("GET", "/api/v1/curriculum/my-class-schedule"),
    ("GET", "/api/v1/curriculum/my-progress"),
    ("GET", "/api/v1/curriculum/reporting/coverage"),
    ("GET", "/api/v1/curriculum/reporting/delayed-topics"),
    ("GET", "/api/v1/curriculum/export"),
    # --- api/main.py ---
    ("GET", "/health/storage"),
    # --- api/error_tracking.py (NFR-7) ---
    ("GET", "/health/errors"),
    ("POST", "/api/v1/client-errors"),
    ("GET", "/api/v1/ops/errors"),
    # --- operations/messaging_routes.py (INT-2) ---
    ("GET", "/api/v1/me/contact"),
    ("PUT", "/api/v1/me/contact"),
    # --- operations/report_cards.py (EX-8) ---
    ("GET", "/api/v1/report-cards/students/{student_id}"),
    ("GET", "/api/v1/report-cards/students/{student_id}/pdf"),
    ("GET", "/api/v1/report-cards/sections/{section_id}/pdf"),
    # --- consent_routes.py (DPDP Act 2023 parental consent) ---
    ("GET", "/api/v1/consent"),
    ("POST", "/api/v1/consent"),
    ("GET", "/api/v1/consent/missing"),
    ("GET", "/api/v1/consent/students/{student_id}"),
    ("DELETE", "/api/v1/consent/students/{student_id}"),
})

DOC_ROUTES: frozenset[tuple[str, str]] = frozenset({
    ("GET", "/docs"),
    ("GET", "/docs/oauth2-redirect"),
    ("GET", "/openapi.json"),
    ("GET", "/redoc"),
})

# Routes whose handler chain begins with Depends(get_current_user) or
# require_principal (looked up through auth_routes._require()). These check
# for a bearer token before they ever touch the auth module's own _require(),
# so with NO Authorization header they 401 ("no token"), never 503 -- and a
# syntactically valid but session-less token still 503s while the app is
# uninitialized. The startup-free tests below drive exactly that split; the
# full-boot group exercises the real 401/403/404 paths.
AUTH_FIRST_ROUTES: frozenset[tuple[str, str]] = frozenset({
    # NFR-2: which mail backends are set up is not public.
    ("GET", "/api/v1/mail/status"),
    # INT-2: the caller's own number (authenticates first).
    ("GET", "/api/v1/me/contact"),
    ("PUT", "/api/v1/me/contact"),
    # EX-8 report cards (authenticate first).
    ("GET", "/api/v1/report-cards/students/{student_id}"),
    ("GET", "/api/v1/report-cards/students/{student_id}/pdf"),
    ("GET", "/api/v1/report-cards/sections/{section_id}/pdf"),
    # paper-timing authenticates first, like the other paper routes.
    ("GET", "/api/v1/paper-timing"),
    # --- routes.py (assessment designer) ---
    ("GET", "/api/v1/schools/{school_id}/templates"),
    ("GET", "/api/v1/schools/{school_id}/paper-templates"),
    ("POST", "/api/v1/papers/generate"),
    ("POST", "/api/v1/papers/quick-generate"),
    ("POST", "/api/v1/papers/generate-from-ids"),
    ("GET", "/api/v1/papers/{paper_id}"),
    ("POST", "/api/v1/papers/{paper_id}/export/{fmt}"),
    ("GET", "/api/v1/papers/{paper_id}/file"),
    ("POST", "/api/v1/assessments"),
    ("GET", "/api/v1/assessments"),
    ("GET", "/api/v1/assessments/{assessment_id}"),
    ("PUT", "/api/v1/assessments/{assessment_id}"),
    ("DELETE", "/api/v1/assessments/{assessment_id}"),
    ("PATCH", "/api/v1/assessments/{assessment_id}/status"),
    ("PATCH", "/api/v1/assessments/{assessment_id}/approve"),
    # --- paper_template_routes.py (teacher paper templates) ---
    ("GET", "/api/v1/schools/{school_id}/teacher-templates"),
    ("POST", "/api/v1/schools/{school_id}/teacher-templates"),
    ("GET", "/api/v1/schools/{school_id}/teacher-templates/{template_id}"),
    ("PUT", "/api/v1/schools/{school_id}/teacher-templates/{template_id}"),
    ("DELETE", "/api/v1/schools/{school_id}/teacher-templates/{template_id}"),
    ("POST", "/api/v1/schools/{school_id}/teacher-templates/{template_id}/share"),
    ("POST", "/api/v1/schools/{school_id}/teacher-templates/{template_id}/duplicate"),
    ("POST", "/api/v1/schools/{school_id}/teacher-templates/{template_id}/availability"),
    ("POST", "/api/v1/papers/generate-from-template"),
    ("POST", "/api/v1/papers/{paper_id}/questions/{slot}/swap"),
    ("POST", "/api/v1/papers/{paper_id}/questions/{slot}"),
    ("DELETE", "/api/v1/papers/{paper_id}/questions/{slot}"),
    # --- auth_routes.py (identity reads + principal approval) ---
    ("GET", "/api/v1/auth/me"),
    ("GET", "/api/v1/auth/users"),
    ("POST", "/api/v1/auth/users/{user_id}/close"),
    ("POST", "/api/v1/auth/users/{user_id}/reopen"),
    # Invites are principal-only (require_principal -> get_current_user).
    ("POST", "/api/v1/auth/invites"),
    ("GET", "/api/v1/auth/invites"),
    ("DELETE", "/api/v1/auth/invites/{code}"),
    # --- pillar_routes.py (school templates, grading, knowledge) ---
    ("GET", "/api/v1/schools/{school_id}/school-templates"),
    ("POST", "/api/v1/schools/{school_id}/school-templates"),
    ("GET", "/api/v1/schools/{school_id}/school-templates/{template_id}/sections"),
    ("DELETE", "/api/v1/schools/{school_id}/school-templates/{template_id}"),
    ("POST", "/api/v1/assessments/{assessment_id}/answer-key"),
    ("POST", "/api/v1/mail/send-paper"),
    ("POST", "/api/v1/evaluations/answer"),
    ("POST", "/api/v1/evaluations/sheet"),
    ("POST", "/api/v1/evaluations/sheet/{assessment_id}/{student_id}/review/{question_id}"),
    ("POST", "/api/v1/evaluations/sheet/{assessment_id}/{student_id}/finalize"),
    ("GET", "/api/v1/evaluations/assessment/{assessment_id}/question/{question_id}"),
    ("POST", "/api/v1/evaluations/assessment/{assessment_id}/question/{question_id}/award"),
    ("GET", "/api/v1/knowledge/{student_id}"),
    ("GET", "/api/v1/knowledge/{student_id}/report"),
    ("POST", "/api/v1/practice/generate"),
    ("POST", "/api/v1/practice/submit"),
    ("GET", "/api/v1/insights/class/{assessment_id}"),
    ("GET", "/api/v1/insights/school/{school_id}"),
    # --- mobile_routes.py (scan-and-grade) ---
    ("POST", "/api/v1/scan/sessions"),
    ("POST", "/api/v1/scan/sessions/{session_id}/pages"),
    ("POST", "/api/v1/scan/sessions/{session_id}/process"),
    ("GET", "/api/v1/scan/sessions/{session_id}/review"),
    ("POST", "/api/v1/scan/sessions/{session_id}/review/{question_id}"),
    ("POST", "/api/v1/scan/sessions/{session_id}/finalize"),
    ("GET", "/api/v1/scan/sessions/{session_id}/pages/{page_no}/image"),
    ("GET", "/api/v1/scan/sessions/{session_id}/raw-pdf"),
    ("GET", "/api/v1/scan/sessions/{session_id}/corrected-pdf"),
    # --- curriculum/routes.py (principal-gated writes + reads) ---
    # The hierarchy reads were anonymous until 2026-09-21 (the product audit
    # read school_1's approved topics as school_2, and school_1's academic
    # years with no token). They now authenticate first and are scoped to the
    # caller's school; /boards authenticates but is global reference data.
    ("GET", "/api/v1/curriculum/boards"),
    ("GET", "/api/v1/curriculum/academic-years"),
    ("GET", "/api/v1/curriculum/academic-years/{academic_year_id}/grades"),
    ("GET", "/api/v1/curriculum/grades/{grade_id}/subjects"),
    ("GET", "/api/v1/curriculum/academic-years/{academic_year_id}/sections"),
    ("POST", "/api/v1/curriculum/grades/{grade_id}/sections"),
    ("PATCH", "/api/v1/curriculum/sections/{section_id}"),
    ("DELETE", "/api/v1/curriculum/sections/{section_id}"),
    ("GET", "/api/v1/curriculum/sections/{section_id}/students"),
    ("GET", "/api/v1/curriculum/academic-years/{academic_year_id}/allocations"),
    ("PUT", "/api/v1/curriculum/sections/{section_id}/allocations/{subject_id}"),
    ("DELETE", "/api/v1/curriculum/sections/{section_id}/allocations/{subject_id}"),
    ("GET", "/api/v1/curriculum/academic-years/{academic_year_id}/teacher-load"),
    ("GET", "/api/v1/curriculum/rooms"),
    ("POST", "/api/v1/curriculum/rooms"),
    ("PATCH", "/api/v1/curriculum/rooms/{room_id}"),
    ("DELETE", "/api/v1/curriculum/rooms/{room_id}"),
    ("GET", "/api/v1/curriculum/academic-years/{academic_year_id}/bell-schedules"),
    ("POST", "/api/v1/curriculum/academic-years/{academic_year_id}/bell-schedules"),
    ("PUT", "/api/v1/curriculum/bell-schedules/{bell_schedule_id}"),
    ("DELETE", "/api/v1/curriculum/bell-schedules/{bell_schedule_id}"),
    ("PUT", "/api/v1/curriculum/sections/{section_id}/bell-schedule"),
    ("GET", "/api/v1/curriculum/academic-years/{academic_year_id}/timetable"),
    ("GET", "/api/v1/curriculum/sections/{section_id}/timetable"),
    ("PUT", "/api/v1/curriculum/sections/{section_id}/timetable"),
    ("GET", "/api/v1/curriculum/my-timetable"),
    ("POST", "/api/v1/curriculum/academic-years/{academic_year_id}/timetable/solve"),
    ("GET", "/api/v1/curriculum/academic-years/{academic_year_id}/teacher-unavailability"),
    ("PUT", "/api/v1/curriculum/academic-years/{academic_year_id}/teacher-unavailability/{teacher_id}"),
    ("GET", "/api/v1/curriculum/academic-years/{academic_year_id}/room-unavailability"),
    ("PUT", "/api/v1/curriculum/academic-years/{academic_year_id}/room-unavailability/{room_id}"),
    ("GET", "/api/v1/curriculum/school-profile"),
    ("PUT", "/api/v1/curriculum/school-profile"),
    ("GET", "/api/v1/curriculum/school-profile/logo"),
    ("POST", "/api/v1/curriculum/school-profile/logo"),
    ("DELETE", "/api/v1/curriculum/school-profile/logo"),
    ("POST", "/api/v1/curriculum/leave-requests"),
    ("GET", "/api/v1/curriculum/leave-requests"),
    ("POST", "/api/v1/curriculum/leave-requests/{leave_id}/decision"),
    ("POST", "/api/v1/curriculum/leave-requests/{leave_id}/cancel"),
    ("POST", "/api/v1/curriculum/leave-requests/{leave_id}/document"),
    ("GET", "/api/v1/curriculum/leave-requests/{leave_id}/document"),
    ("GET", "/api/v1/curriculum/substitutions"),
    ("GET", "/api/v1/curriculum/substitutions/{sub_id}/candidates"),
    ("POST", "/api/v1/curriculum/substitutions/{sub_id}/assign"),
    ("POST", "/api/v1/curriculum/substitutions/{sub_id}/respond"),
    ("GET", "/api/v1/curriculum/academic-years/{academic_year_id}/lost-periods"),
    ("GET", "/api/v1/curriculum/lost-periods/{lost_id}/compensation-options"),
    ("POST", "/api/v1/curriculum/lost-periods/{lost_id}/compensate"),
    ("POST", "/api/v1/curriculum/lost-periods/{lost_id}/waive"),
    ("POST", "/api/v1/curriculum/academic-years/{academic_year_id}/closures"),
    ("GET", "/api/v1/curriculum/day"),
    ("GET", "/api/v1/curriculum/my-day"),
    ("GET", "/api/v1/curriculum/academic-years/{academic_year_id}/cover-summary"),
    ("GET", "/api/v1/curriculum/teacher-attendance"),
    ("PUT", "/api/v1/curriculum/teacher-attendance"),
    ("POST", "/api/v1/curriculum/my-attendance"),
    ("GET", "/api/v1/notifications"),
    ("POST", "/api/v1/notifications/{notification_id}/read"),
    ("POST", "/api/v1/notifications/read-all"),
    ("GET", "/api/v1/notification-preferences"),
    ("PUT", "/api/v1/notification-preferences"),
    ("POST", "/api/v1/devices"),
    ("DELETE", "/api/v1/devices/{token}"),
    ("GET", "/api/v1/automations/status"),
    ("GET", "/api/v1/admin/grants"),
    ("POST", "/api/v1/admin/grants"),
    ("DELETE", "/api/v1/admin/grants/{grant_id}"),
    ("GET", "/api/v1/my-grants"),
    ("GET", "/api/v1/staff"),
    ("GET", "/api/v1/dashboard/summary"),
    ("GET", "/api/v1/dashboard/term"),
    ("GET", "/api/v1/qbank/coverage-map"),
    ("GET", "/api/v1/qbank/review-queue"),
    ("POST", "/api/v1/qbank/review/{question_id}"),
    ("GET", "/api/v1/dashboard/term/export"),
    ("GET", "/api/v1/calendar-feed"),
    ("POST", "/api/v1/calendar-feed/reset"),
    ("GET", "/api/v1/my-calendar"),
    ("GET", "/api/v1/my-load"),
    ("POST", "/api/v1/curriculum/academic-years/{academic_year_id}/lesson-plans"),
    ("POST", "/api/v1/my-homework/{homework_id}/photos"),
    ("GET", "/api/v1/my-homework/{homework_id}/photos"),
    ("GET", "/api/v1/my-homework/{homework_id}/photos/{photo_id}"),
    ("DELETE", "/api/v1/my-homework/{homework_id}/photos/{photo_id}"),
    ("GET", "/api/v1/homework/{homework_id}/submissions/{student_id}/photos/{photo_id}"),
    ("POST", "/api/v1/my-practice"),
    ("GET", "/api/v1/my-practice"),
    ("GET", "/api/v1/my-practice/{practice_id}"),
    ("POST", "/api/v1/my-practice/{practice_id}/submit"),
    ("GET", "/api/v1/sections/{section_id}/progress"),
    ("GET", "/api/v1/homework/suggestion"),
    ("POST", "/api/v1/homework"),
    ("GET", "/api/v1/homework"),
    ("GET", "/api/v1/homework/{homework_id}"),
    ("POST", "/api/v1/homework/{homework_id}/publish"),
    ("POST", "/api/v1/homework/{homework_id}/close"),
    ("GET", "/api/v1/homework/{homework_id}/submissions"),
    ("POST", "/api/v1/homework/{homework_id}/submissions/{student_id}/grade"),
    ("POST", "/api/v1/homework/{homework_id}/remind"),
    ("GET", "/api/v1/my-homework"),
    ("GET", "/api/v1/my-homework/{homework_id}"),
    ("POST", "/api/v1/my-homework/{homework_id}/submit"),
    ("GET", "/api/v1/my-learning"),
    ("GET", "/api/v1/students/{student_id}/learning"),
    ("POST", "/api/v1/students/{student_id}/guardian-invites"),
    ("GET", "/api/v1/students/{student_id}/guardians"),
    ("POST", "/api/v1/guardianships"),
    ("DELETE", "/api/v1/guardianships/{parent_id}/{student_id}"),
    ("GET", "/api/v1/my-children"),
    ("GET", "/api/v1/children/{student_id}/timetable"),
    ("GET", "/api/v1/children/{student_id}/day"),
    ("GET", "/api/v1/children/{student_id}/homework"),
    ("GET", "/api/v1/children/{student_id}/homework/{homework_id}"),
    ("POST", "/api/v1/children/{student_id}/homework/{homework_id}/submit"),
    ("GET", "/api/v1/children/{student_id}/learning"),
    ("GET", "/api/v1/children/{student_id}/consent"),
    ("POST", "/api/v1/children/{student_id}/consent"),
    ("DELETE", "/api/v1/children/{student_id}/consent"),
    ("POST", "/api/v1/admin/import/{kind}"),
    ("GET", "/api/v1/admin/import/{kind}/template"),
    ("GET", "/api/v1/admin/export/{kind}"),
    ("POST", "/api/v1/api-keys"),
    ("GET", "/api/v1/api-keys"),
    ("DELETE", "/api/v1/api-keys/{key_id}"),
    ("GET", "/api/v1/api-keys/{key_id}/usage"),
    ("POST", "/api/v1/assessments/{assessment_id}/review-request"),
    ("POST", "/api/v1/assessments/{assessment_id}/review-decision"),
    ("GET", "/api/v1/assessments/{assessment_id}/reviews"),
    ("GET", "/api/v1/paper-reviews"),
    ("PUT", "/api/v1/papers/{paper_id}/marks"),
    ("GET", "/api/v1/papers/{paper_id}/marks"),
    ("GET", "/api/v1/papers/{paper_id}/analysis"),
    ("POST", "/api/v1/exams"),
    ("GET", "/api/v1/exams"),
    ("GET", "/api/v1/exams/{exam_id}"),
    ("PUT", "/api/v1/exams/{exam_id}/datesheet"),
    ("POST", "/api/v1/exams/{exam_id}/invigilation/auto"),
    ("PUT", "/api/v1/exams/{exam_id}/invigilation"),
    ("POST", "/api/v1/exams/{exam_id}/publish"),
    ("GET", "/api/v1/my-exams"),
    ("GET", "/api/v1/curriculum/subjects/{subject_id}/books"),
    ("POST", "/api/v1/curriculum/subjects/{subject_id}/books"),
    ("GET", "/api/v1/curriculum/subjects/{subject_id}/selected-book"),
    ("PUT", "/api/v1/curriculum/subjects/{subject_id}/selected-book"),
    ("GET", "/api/v1/curriculum/books/{book_id}/units"),
    ("GET", "/api/v1/curriculum/books/{book_id}/chapters"),
    ("GET", "/api/v1/curriculum/chapters/{chapter_id}/topics"),
    ("GET", "/api/v1/curriculum/chapters/by-slug/{subject}/{grade}/{slug}/topics"),
    ("GET", "/api/v1/curriculum/chapters/{chapter_id}/proposed-topics"),
    ("POST", "/api/v1/curriculum/chapters/{chapter_id}/topics/approve-all"),
    ("POST", "/api/v1/curriculum/books/{book_id}/toc/ingest"),
    ("POST", "/api/v1/curriculum/seed/cbse10"),
    ("POST", "/api/v1/curriculum/seed/cbse"),
    ("POST", "/api/v1/curriculum/chapters/{chapter_id}/extract"),
    ("GET", "/api/v1/curriculum/extraction-runs/{run_id}"),
    ("POST", "/api/v1/curriculum/extraction-runs/{run_id}/approve"),
    ("POST", "/api/v1/curriculum/chapters/{chapter_id}/topics"),
    ("POST", "/api/v1/curriculum/topics/{topic_id}/subtopics"),
    ("PATCH", "/api/v1/curriculum/topics/{topic_id}"),
    ("PATCH", "/api/v1/curriculum/subtopics/{subtopic_id}"),
    ("DELETE", "/api/v1/curriculum/subtopics/{subtopic_id}"),
    ("PATCH", "/api/v1/curriculum/units/{unit_id}/sequence"),
    ("PATCH", "/api/v1/curriculum/chapters/{chapter_id}/sequence"),
    ("PATCH", "/api/v1/curriculum/topics/{topic_id}/sequence"),
    ("PATCH", "/api/v1/curriculum/subtopics/{subtopic_id}/sequence"),
    ("POST", "/api/v1/curriculum/chapters/{chapter_id}/questions/tag"),
    ("POST", "/api/v1/curriculum/academic-years/{academic_year_id}/calendar"),
    ("PUT", "/api/v1/curriculum/academic-years/{academic_year_id}/calendar"),
    ("GET", "/api/v1/curriculum/academic-years/{academic_year_id}/calendar"),
    ("POST", "/api/v1/curriculum/academic-years/{academic_year_id}/holidays"),
    ("GET", "/api/v1/curriculum/academic-years/{academic_year_id}/holidays"),
    ("DELETE", "/api/v1/curriculum/academic-years/{academic_year_id}/holidays/{holiday_id}"),
    ("POST", "/api/v1/curriculum/academic-years/{academic_year_id}/terms"),
    ("GET", "/api/v1/curriculum/academic-years/{academic_year_id}/terms"),
    ("GET", "/api/v1/curriculum/terms/current"),
    ("PUT", "/api/v1/curriculum/terms/{term_id}"),
    ("DELETE", "/api/v1/curriculum/terms/{term_id}"),
    ("PUT", "/api/v1/curriculum/terms/{term_id}/baseline"),
    ("POST", "/api/v1/curriculum/academic-years/{academic_year_id}/period-configuration"),
    ("POST", "/api/v1/curriculum/academic-years/{academic_year_id}/subject-period-allocations"),
    ("GET", "/api/v1/curriculum/academic-years/{academic_year_id}/subject-period-allocations"),
    ("POST", "/api/v1/curriculum/academic-years/{academic_year_id}/timetable-slots"),
    ("GET", "/api/v1/curriculum/academic-years/{academic_year_id}/timetable-slots"),
    ("DELETE", "/api/v1/curriculum/timetable-slots/{slot_id}"),
    ("GET", "/api/v1/curriculum/academic-years/{academic_year_id}/working-days"),
    ("POST", "/api/v1/curriculum/books/{book_id}/teaching-time-estimates"),
    ("GET", "/api/v1/curriculum/subtopics/{subtopic_id}/teaching-time-estimate"),
    ("POST", "/api/v1/curriculum/books/{book_id}/schedule"),
    ("GET", "/api/v1/curriculum/books/{book_id}/schedule"),
    ("GET", "/api/v1/curriculum/schedule"),
    ("POST", "/api/v1/curriculum/teacher-assignments"),
    ("GET", "/api/v1/curriculum/my-schedule"),
    ("PATCH", "/api/v1/curriculum/scheduled-lessons/{lesson_id}"),
    ("POST", "/api/v1/curriculum/scheduled-lessons/{lesson_id}/reschedule"),
    ("POST", "/api/v1/curriculum/books/{book_id}/schedule/push"),
    ("GET", "/api/v1/curriculum/scheduled-lessons/{lesson_id}/history"),
    ("POST", "/api/v1/curriculum/student-enrollments"),
    ("GET", "/api/v1/curriculum/my-class-schedule"),
    ("GET", "/api/v1/curriculum/my-progress"),
    ("GET", "/api/v1/curriculum/reporting/coverage"),
    ("GET", "/api/v1/curriculum/reporting/delayed-topics"),
    ("GET", "/api/v1/curriculum/export"),
    # --- consent_routes.py (DPDP Act 2023 parental consent) ---
    ("GET", "/api/v1/consent"),
    ("POST", "/api/v1/consent"),
    ("GET", "/api/v1/consent/missing"),
    ("GET", "/api/v1/consent/students/{student_id}"),
    ("DELETE", "/api/v1/consent/students/{student_id}"),
    # --- api/main.py (the /v1/* pillar surface) ---
    # These were made auth-gated on 2026-09-16 (compute- and LLM-backed routes
    # had been anonymously reachable). They were added to API_ROUTES then but
    # NOT to this list, and that omission made
    # test_gated_routes_return_503_without_startup fail whenever it actually
    # ran: it asserts 503 for everything not listed here, and these answer 401
    # because auth resolves first. It only ever passed by being *skipped* -- in
    # a full-suite run an earlier test boots the app, the guard at the top of
    # that test sees initialised globals and skips. Run in isolation it failed.
    # A test that passes because it never executes is not coverage.
    ("GET", "/v1/registry/stats"),
    ("POST", "/v1/search"),
    ("POST", "/v1/agent/doubt"),
    ("POST", "/v1/agent/score"),
    ("POST", "/v1/agent/analyze"),
    ("POST", "/v1/graph/neighbors"),
    ("POST", "/v1/graph/paths"),
    ("POST", "/v1/revise"),
    ("POST", "/v1/plan"),
    ("POST", "/v1/question/solve"),
    # Four more that were auth-gated but never declared here, found by driving
    # every route without a token and recording which answer 401 (rather than
    # guessing one at a time). All four return 401 with no token and 503 with
    # a syntactically valid one, which is exactly this set's contract.
    ("POST", "/api/v1/blueprints/generate"),
    ("POST", "/api/v1/curriculum/questions/by-subtopics"),
    ("POST", "/api/v1/ingest/school-documents"),
    ("POST", "/api/v1/questions/optimize"),
    ("POST", "/api/v1/questions/search"),
})


def _concrete_path(path: str) -> str:
    """Replaces every {path_param} with a value the route will accept."""
    return (
        path
        .replace("{school_id}", "school_1")
        .replace("{assessment_id}", "a1")
        .replace("{paper_id}", "paper_1")
        .replace("{fmt}", "pdf")
        .replace("{template_id}", "tpl_1")
        .replace("{subject}", "Science")
        .replace("{grade}", "10")
        .replace("{student_id}", "s1")
        .replace("{session_id}", "scan_1")
        .replace("{question_id}", "q_1")
        .replace("{page_no}", "1")
        .replace("{code}", "inv_1")
        .replace("{slot}", "1")
    )


def _enumerate_routes() -> frozenset[tuple[str, str]]:
    """Walks app.routes including `_IncludedRouter` wrappers (newer FastAPI
    nests included routers instead of flattening them)."""
    out: set[tuple[str, str]] = set()

    def walk(routes):
        for r in routes:
            if hasattr(r, "original_router"):
                walk(r.original_router.routes)
            elif hasattr(r, "methods"):
                for m in r.methods:
                    if m == "HEAD":
                        continue
                    out.add((m, r.path))

    walk(app.routes)
    return frozenset(out)


# ---------------------------------------------------------------- helpers


def blueprint_body(total_marks: int = 80, duration_minutes: int = 180) -> dict:
    return {
        "totalMarks": total_marks,
        "durationMinutes": duration_minutes,
        "difficulty": {"easy": 0.3, "medium": 0.4, "hard": 0.3},
        "bloom": {
            "remember": 0.2, "understand": 0.2, "apply": 0.2, "analyze": 0.2,
            "evaluate": 0.1, "create": 0.1,
        },
        "chapterWeights": {"weights": {}},
        "competencyWeights": {"weights": {}},
    }


def question_body(qid: str = "q_1", marks: int = 2) -> dict:
    return {
        "id": qid,
        "questionBankId": "bank_1",
        "subject": "Mathematics",
        "grade": 10,
        "chapterIds": ["ch1"],
        "competencyIds": [],
        "bloomLevel": "apply",
        "difficulty": "medium",
        "type": "short_answer",
        "stem": "Solve 2x + 3 = 7",
        "stemLatex": "",
        "parts": [],
        "answerScheme": {
            "totalMarks": marks,
            "markingPoints": [{
                "id": "mp1", "description": "correct answer", "marks": marks,
                "keyword": "solution", "isRequired": False, "synonyms": [],
            }],
            "rubricLevels": [],
            "commonErrors": [],
            "alternativeAnswers": [],
            "modelAnswer": "x = 2",
            "modelAnswerLatex": "",
            "hasPartialCredit": False,
            "metadata": {},
            # Rule Q1 (qbank_routes.QuestionBank.has_answer_key) takes a
            # published provenance AND real content; a fixture question that
            # stands in for a servable one carries the board's label, or no
            # paper path will print it.
            "provenance": "cbse_marking_scheme",
        },
        "estimatedTimeMinutes": 3,
        "marks": marks,
        "language": "en",
        "source": "teacher_created",
        "qualityScore": 0.9,
        "tags": [],
        "createdAt": "2026-01-01T00:00:00Z",
        "updatedAt": "2026-01-01T00:00:00Z",
        "metadata": {},
    }


def school_template_body(template_id: str = "tpl_1") -> dict:
    return {"id": template_id, "schoolId": "school_1", "name": "Default"}


def teacher_template_body(name: str = "Unit test") -> dict:
    return {
        "name": name, "grade": 10, "subject": "Science", "examType": "unit_test",
        "totalMarks": 5, "durationMinutes": 40,
        "sections": [{"title": "Section A", "questionCount": 5, "marksEach": 1}],
    }


def _valid_body_for(method: str, path: str) -> dict:
    """A body that passes FastAPI request validation for the route, so the
    handler's own `_require()` (503 before init) is what fires instead of a
    422. GET/DELETE routes take no body."""
    if method in ("GET", "DELETE"):
        return {}
    if path == "/api/v1/assessments":
        return {
            "teacherId": "t", "schoolId": "s", "title": "t", "subject": "Science",
            "grade": 10, "chapterIds": [], "blueprint": blueprint_body(),
        }
    if path == "/api/v1/assessments/{assessment_id}":  # PUT
        return {
            "id": "a1", "teacherId": "t", "schoolId": "s", "title": "t",
            "subject": "Science", "grade": 10, "chapterIds": [],
            "blueprint": blueprint_body(), "status": "draft",
            "createdAt": "2026-01-01T00:00:00Z",
            "updatedAt": "2026-01-01T00:00:00Z",
        }
    if path in ("/api/v1/curriculum/academic-years/{academic_year_id}/terms",
                "/api/v1/curriculum/terms/{term_id}"):  # POST / PUT
        return {"name": "Term 1", "startDate": "2026-04-01", "endDate": "2026-09-30"}
    if path == "/api/v1/auth/code/request":
        return {"email": "a@example.com"}
    if path == "/api/v1/auth/code/verify":
        return {"email": "a@example.com", "code": "123456"}
    if path == "/api/v1/auth/google":
        return {"credential": "x" * 40}
    if path == "/api/v1/curriculum/terms/{term_id}/baseline":  # PUT
        return {"minutes": 60}
    if path == "/api/v1/curriculum/subjects/{subject_id}/books":  # POST
        return {"title": "Mathematics Part I", "boardId": "board_1"}
    if path == "/api/v1/curriculum/subjects/{subject_id}/selected-book":  # PUT
        return {"bookId": "book_1"}
    if path == "/api/v1/assessments/{assessment_id}/status":  # PATCH
        return {"status": "draft"}
    if path == "/api/v1/questions/search":
        return {"subject": "Science", "grade": 10}
    if path == "/api/v1/questions/optimize":
        return {"candidates": [], "blueprint": blueprint_body()}
    if path == "/api/v1/papers/generate":
        return {
            "assessmentId": "a1", "blueprint": blueprint_body(),
            "selectedQuestions": [], "template": school_template_body(),
        }
    if path == "/api/v1/papers/{paper_id}/export/{fmt}":
        return {}
    if path == "/api/v1/mail/send-paper":
        return {"paperId": "p", "recipients": ["a@b.c"]}
    if path == "/api/v1/evaluations/answer":
        return {
            "assessmentId": "a", "studentId": "s", "question": question_body(),
            "studentAnswer": "x",
        }
    if path == "/api/v1/evaluations/sheet":
        return {"assessmentId": "a", "studentId": "s", "questions": [], "answers": {}}
    if path == "/api/v1/evaluations/sheet/{assessment_id}/{student_id}/review/{question_id}":
        return {"action": "approve"}
    if path == "/api/v1/practice/generate":
        return {"studentId": "s"}
    if path == "/api/v1/practice/submit":
        return {"setId": "s", "answers": {}}
    if path == "/api/v1/schools/{school_id}/school-templates":
        return {"template": school_template_body(), "sections": []}
    if path in ("/api/v1/schools/{school_id}/teacher-templates",
                "/api/v1/schools/{school_id}/teacher-templates/{template_id}"):
        return teacher_template_body()
    if path == "/api/v1/schools/{school_id}/teacher-templates/{template_id}/share":
        return {"shared": True}
    if path == "/api/v1/papers/generate-from-template":
        return {"templateId": "tpl_1"}
    if path == "/api/v1/papers/{paper_id}/questions/{slot}":
        return {"questionId": "q_1"}
    if path == "/api/v1/papers/{paper_id}/questions/{slot}/swap":
        return {}
    if path.startswith("/api/v1/schools/{school_id}/teacher-templates/"):
        return {}  # duplicate / availability: every field optional
    if path == "/api/v1/auth/register":
        return {"inviteCode": "inv_1", "name": "Teacher One",
                "email": "teacher1@example.com", "password": "correct horse battery"}
    if path == "/api/v1/auth/invites":
        return {"role": "teacher"}
    if path == "/api/v1/auth/login":
        return {"email": "teacher1@example.com", "password": "correct horse battery"}
    if path == "/v1/question/solve":
        return {"question": "What is photosynthesis?"}
    if path == "/api/v1/curriculum/chapters/{chapter_id}/questions/tag":
        return {"questionId": "q1", "questionText": "Balance the equation."}
    if path == "/api/v1/curriculum/questions/by-subtopics":
        return {"subtopicIds": ["st1"]}
    if path == "/api/v1/consent":
        return {
            "studentId": "s1",
            "guardianName": "Parent One",
            "guardianRelationship": "parent",
            "method": "Signed admission form",
        }
    return {"query": "photosynthesis", "doubt": "light reaction",
            "question": "q", "paperId": "p", "paper_id": "p",
            "nodeId": "n", "node_id": "n", "source": "a", "target": "b"}


# =====================================================================
# Group 1: canonical route-set guard (no startup needed).
# =====================================================================


def test_canonical_route_inventory_matches_live_app():
    """The enumerated app must equal the inventory above exactly."""
    live = _enumerate_routes()
    live_api = live - DOC_ROUTES
    assert live_api == API_ROUTES, (
        "backend routes drifted from tests/test_route_inventory.py — add/update "
        "the route AND its exercise cases below. "
        f"extra: {sorted(live_api - API_ROUTES)}  "
        f"missing: {sorted(API_ROUTES - live_api)}"
    )
    # 168: M1.1 added the five sections routes (list, create, update, delete, students).
    # 185: M1.2-M1.3 added 17 school-model routes (allocations, rooms, bell, timetable).
    # 188: SCH-3 added solve and teacher unavailability (list, set).
    # 204: SCH-5..7 added 16 leave, substitution and compensation routes.
    # 211: M3 added the inbox, preferences and devices (7).
    # 223: M5 added homework (12).
    # 225: SA-3 added learning progress (2).
    # 240: M1.5 added parents (12), M1.6 bulk import and export (3).
    # 244: D38 added API key issuance (4).
    # 247: SCH-9 added teacher attendance (3).
    # 249: NTF-2 added automations (2).
    # 253: EX-6 added paper review (4).
    # 256: EX-8 added marks entry and analysis (3).
    # 264: EX-7 added exam planning (8).
    # 268: M1.4 added delegated admin grants (4).
    # 269: the staff directory for pickers (1).
    # 279: dashboard, calendar feed (3), /v1 homework sets, homework photos (5).
    # 283: SA-4 self-practice (4).
    # 284: TA-6 class progress (1).
    # 286: sign-in by emailed code (2).
    # 288: ADM-2/4 the term report and its Excel/PDF export (2).
    # 290: INT-1 Google sign-in and the sign-in providers (2).
    # 292: SA-7 a parent opens and hands in a young child's homework (2).
    # 299: SCH-8 added a room's periods out of use (list, set); EX-5/D41 the school
    # profile (get, set) and its logo (get, upload, remove).
    # 302: NFR-7 error tracking (/health/errors, client reports, the operator's list).
    # 304: INT-2 a person's own number and SMS/WhatsApp consent (get, set).
    # 307: the question bank's coverage map and review queue (3).
    # 309: closing and reopening an account (N-67-8).
    # 311: TA-2 the caller's own calendar and teaching load in the apps.
    # 314: EX-8 report cards (a student's, as JSON and PDF; a section's PDF).
    # 315: N-67-5 every section's lesson plan in one action.
    # 317: N-3-17 a leave request's supporting document (attach, read).
    assert len(API_ROUTES) == 317


def test_docs_routes_present():
    assert DOC_ROUTES.issubset(_enumerate_routes())


# =====================================================================
# Group 2: startup-free (must precede any `with TestClient(app)`).
# =====================================================================


def test_health_without_startup():
    from fastapi.testclient import TestClient

    client = TestClient(app)
    try:
        r = client.get("/health")
    finally:
        client.close()
    assert r.status_code == 200
    assert r.json()["status"] == "ok" and set(r.json()) == {"status", "commit", "builtAt"}


def test_non_gated_routes_work_without_startup():
    """Routes that need no module init and no auth: mail status, and
    syllabus/timetable (package-data backed). The routes that used to be here
    (school templates, answer-key, scan-session creation, and -- as of
    2026-09-16 -- blueprint generation) now require
    Depends(get_current_user); they 401 without a token and are covered in the
    auth-gated startup-free tests below."""
    from fastapi.testclient import TestClient

    client = TestClient(app)
    try:
        # Pure-compute, so it is now auth-gated: 401 before module init.
        assert client.post(
            "/api/v1/blueprints/generate", json=blueprint_body()
        ).status_code == 401
        assert client.get("/api/v1/mail/status").status_code == 401
        assert client.get("/api/v1/auth/providers").status_code == 200

        assert client.get("/api/v1/syllabus/Science/10").status_code == 200
        assert client.get("/api/v1/syllabus/Science/10/timetable").status_code == 200
        assert client.get("/api/v1/syllabus/Physics/10").status_code == 404

        storage = client.get("/health/storage")
        assert storage.status_code == 200
        assert storage.json()["supabase_configured"] is False  # no env vars set in tests
    finally:
        client.close()


def test_gated_routes_return_503_without_startup():
    """Mounted but not initialized -> 503, never 404."""
    if assessment_routes._store is not None:
        pytest.skip("module globals already initialized (suite ran out of order)")
    from fastapi.testclient import TestClient

    client = TestClient(app)
    try:
        for method, path in sorted(API_ROUTES):
            # Auth-first routes 401 with no token (handled below by the
            # with-token variant) -- they never reach _require().
            if (method, path) in AUTH_FIRST_ROUTES:
                continue
            if (method, path) in {
                ("GET", "/health"),
                ("GET", "/health/llm"),
                ("GET", "/health/storage"),
                # NFR-7 error tracking: counts, the apps' reports and the
                # operator's list need no module but its own.
                ("GET", "/health/errors"),
                ("POST", "/api/v1/client-errors"),
                ("GET", "/api/v1/ops/errors"),
                ("POST", "/api/v1/blueprints/generate"),
                # Which ways in are set up: read from the environment, so it
                # answers before startup.
                ("GET", "/api/v1/auth/providers"),
                ("GET", "/api/v1/syllabus/{subject}/{grade}"),
                ("GET", "/api/v1/syllabus/{subject}/{grade}/timetable"),
            }:
                continue
            # The page-upload route cannot reach a 503 without a multipart
            # file; it is covered by the 404 test in the full-boot group.
            if (method, path) == ("POST", "/api/v1/scan/sessions/{session_id}/pages"):
                continue
            # Same reason: multipart form, not JSON. Covered in
            # test_document_ingestion.py instead.
            if (method, path) == ("POST", "/api/v1/ingest/school-documents"):
                continue
            # Idempotent by design: no token means nothing to delete, so it
            # 200s without ever touching _require() -- correct, not a gap.
            if (method, path) == ("POST", "/api/v1/auth/logout"):
                continue
            # API-key routes take a scoped key, not a user bearer token, and
            # their own module-init guard returns 503 before auth is consulted.
            # They are exercised in tests/test_qbank_api.py instead, where a
            # real key can be minted.
            if (method, path) in {
                ("GET", "/v1/questions"),
                ("GET", "/v1/questions/{question_id}"),
                ("GET", "/v1/questions/{question_id}/scheme"),
                ("GET", "/v1/subtopics/{subtopic_id:path}/questions"),
                ("GET", "/v1/facets"),
                ("GET", "/v1/coverage"),
                ("POST", "/v1/homework-sets"),
            }:
                continue
            concrete = _concrete_path(path)
            body = _valid_body_for(method, path)
            r = client.request(method, concrete, json=body)
            assert r.status_code == 503, f"{method} {concrete} -> {r.status_code}"
    finally:
        client.close()


def test_auth_gated_routes_503_with_a_token_present():
    """Every auth-first route (they 401 with no token, per the test above)
    still hits the real 503-when-uninitialized path once a syntactically
    valid but session-less bearer token is supplied -- get_current_user's
    token check passes, then auth_routes._require() finds the module not
    yet booted and raises 503, before any body/path validation."""
    if assessment_routes._store is not None:
        pytest.skip("module globals already initialized (suite ran out of order)")
    from fastapi.testclient import TestClient

    client = TestClient(app)
    try:
        headers = {"Authorization": "Bearer not-a-real-token"}
        for method, path in sorted(AUTH_FIRST_ROUTES):
            if (method, path) == ("POST", "/api/v1/scan/sessions/{session_id}/pages"):
                continue  # multipart body required (covered in full-boot 404 test)
            if path == "/api/v1/curriculum/academic-years":
                # Required query param, not a path param -- sent so the
                # request is otherwise valid and only the uninitialized auth
                # module can explain the answer. (Moved here from the
                # no-token test above when this route became auth-first.)
                concrete = path + "?school_id=school_1"
            else:
                concrete = _concrete_path(path)
            body = _valid_body_for(method, path)
            r = client.request(method, concrete, json=body, headers=headers)
            assert r.status_code == 503, f"{method} {concrete} -> {r.status_code}"
    finally:
        client.close()


# =====================================================================
# Group 3: full hermetic boot.
# =====================================================================


def _boot_client(tmp_path, monkeypatch):
    """Boots the app with an empty corpus under tmp_path and returns the
    TestClient. Resets the audit-log, user-store, and curriculum-store
    singletons so earlier boots don't leak (same real gap that would have
    hit auth tests: a stale UserStore from a previous test's tmp_path
    would keep answering for a school that supposedly has no users yet in
    the new one)."""
    from academicos.assessment import users as users_mod
    from academicos.assessment import consent as consent_mod, consent_routes as consent_routes_mod
    from academicos.curriculum import store as curriculum_store_mod

    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr(audit_log, "_INSTANCE", None)
    monkeypatch.setattr(users_mod, "_INSTANCE", None)
    monkeypatch.setattr(curriculum_store_mod, "_INSTANCE", None)
    monkeypatch.setattr(consent_mod, "_INSTANCE", None)
    monkeypatch.setattr(consent_routes_mod, "_store", None)
    monkeypatch.setattr(consent_routes_mod, "_audit", None)
    # The schedule route plans from the school's today and /my-progress
    # counts up to it. Every year these tests create starts 2026-06-01, so
    # pin today there: on the real date the tests would change as the year
    # passes (and stop scheduling anything once 2027-03-31 is behind us).
    from datetime import date
    from academicos.curriculum import routes as curriculum_routes
    monkeypatch.setattr(curriculum_routes, "_school_today", lambda: date(2026, 6, 1))
    from fastapi.testclient import TestClient

    return TestClient(app)


def test_full_boot_v1_surface_requires_auth(tmp_path, monkeypatch):
    """The /v1/* pillar surface used to be fully public (this test was named
    test_full_boot_v1_public_surface). As of 2026-09-16 it requires a real
    caller: corpus search, the agent endpoints, graph reads and
    revise/plan/question-solve are all compute- or LLM-backed, so anonymous
    access was an abuse and cost vector. Both halves are asserted -- 401
    without a token, and the original behaviour once authenticated, so the
    endpoint logic stays covered."""
    from test_assessment_routes_auth import _register

    with _boot_client(tmp_path, monkeypatch) as client:
        assert client.get("/health").json()["status"] == "ok"

        # No token -> 401 on every route in this surface, including the
        # cheapest read, so nothing here is anonymously reachable.
        for method, path, body in (
            ("get", "/v1/registry/stats", None),
            ("post", "/v1/search", {"query": "photosynthesis", "limit": 5}),
            ("post", "/v1/agent/doubt", {"doubt": "light reaction"}),
            ("post", "/v1/graph/neighbors", {"node_id": "n1", "max_depth": 2}),
            ("post", "/v1/revise", {"learner": "alice"}),
        ):
            r = getattr(client, method)(path, json=body) if body is not None \
                else getattr(client, method)(path)
            assert r.status_code == 401, f"{method.upper()} {path} -> {r.status_code}"

        user = _register(client, "school_1", "v1-surface@example.com")
        auth = {"Authorization": f"Bearer {user['token']}"}

        stats = client.get("/v1/registry/stats", headers=auth)
        assert stats.status_code == 200
        assert stats.json() == {"count": 0}

        search = client.post("/v1/search", json={"query": "photosynthesis", "limit": 5},
                             headers=auth)
        assert search.status_code == 200
        assert search.json()["hits"] == []

        # min_length=2 -> 422 on an invalid query (auth passes, validation fails).
        assert client.post("/v1/search", json={"query": "x"},
                           headers=auth).status_code == 422

        doubt = client.post("/v1/agent/doubt", json={"doubt": "light reaction"},
                            headers=auth)
        assert doubt.status_code == 200
        assert "No evidence found" in doubt.json()["answer"]

        score = client.post("/v1/agent/score", json={
            "question": "What is photosynthesis?", "student_answer": "a process",
            "marks_available": 2,
        }, headers=auth)
        assert score.status_code == 200
        assert score.json()["score"]["scheme_found"] is False

        analyze = client.post("/v1/agent/analyze", json={"paper_id": "paper_x"},
                              headers=auth)
        assert analyze.status_code == 200

        neighbors = client.post("/v1/graph/neighbors", json={
            "node_id": "n1", "max_depth": 2,
        }, headers=auth)
        assert neighbors.status_code == 200
        assert neighbors.json()["nodes"] == []

        paths = client.post("/v1/graph/paths", json={
            "source": "n1", "target": "n2", "max_depth": 4,
        }, headers=auth)
        assert paths.status_code == 200
        assert paths.json()["paths"] == []

        # Empty event store / empty graph -> real 404s, not silent empty 200s.
        assert client.post("/v1/revise", json={"learner": "nobody"},
                           headers=auth).status_code == 404
        assert client.post("/v1/plan", json={"target": "nowhere"},
                           headers=auth).status_code == 404

        # Lexical fallback (no LLM key configured) still returns a real,
        # if unverified, mapping against an empty graph.
        solved = client.post("/v1/question/solve",
                             json={"question": "What is photosynthesis?"}, headers=auth)
        assert solved.status_code == 200
        assert solved.json()["question"] == "What is photosynthesis?"


def test_full_boot_auth_and_principal_approval(tmp_path, monkeypatch):
    """register -> login -> me -> logout, plus the real reason auth exists:
    a teacher cannot approve their own paper, only a principal can, and
    approval actually engages the pre-existing edit lock.

    The registration rules are pinned on the way (users.py has the history):
    naming a school gets no account without an invite (2026-09-21; before
    that the name alone made you a member). Only a correct principalKey
    creates a principal, and only the school's first: 2026-09-11 closed
    "first registrant is principal", and 2026-09-21 closed "the key mints
    another principal for a school that has one". Everyone else joins with
    an invite the principal issues."""
    monkeypatch.setenv("ACOS_PRINCIPAL_BOOTSTRAP_KEY", "test-bootstrap-key")
    with _boot_client(tmp_path, monkeypatch) as client:
        # -- an attacker racing to register first for school_1, with no key
        # and no invite, gets no account at all.
        attacker = client.post("/api/v1/auth/register", json={
            "schoolId": "school_1", "name": "Eve Attacker",
            "email": "eve@example.com", "password": "correct horse battery",
        })
        assert attacker.status_code == 403, attacker.text

        # -- the real principal, registering second, but with the correct
        # bootstrap key -- this is what actually grants the role now.
        reg1 = client.post("/api/v1/auth/register", json={
            "schoolId": "school_1", "name": "Priya Principal",
            "email": "priya@example.com", "password": "correct horse battery",
            "principalKey": "test-bootstrap-key",
        })
        assert reg1.status_code == 200, reg1.text
        assert reg1.json()["user"]["role"] == "principal"
        principal_token = reg1.json()["token"]
        principal_auth = {"Authorization": f"Bearer {principal_token}"}

        # -- a wrong key guess grants nothing either (not just "no key")
        wrong_key = client.post("/api/v1/auth/register", json={
            "schoolId": "school_1", "name": "Wrong Key", "email": "wrong@example.com",
            "password": "correct horse battery", "principalKey": "guessed-wrong",
        })
        assert wrong_key.status_code == 403, wrong_key.text

        # -- and the RIGHT key cannot mint a second principal for school_1
        second = client.post("/api/v1/auth/register", json={
            "schoolId": "school_1", "name": "Second Principal",
            "email": "second@example.com", "password": "correct horse battery",
            "principalKey": "test-bootstrap-key",
        })
        assert second.status_code == 403, second.text

        # -- the principal invites a teacher; the code alone is enough
        invite = client.post("/api/v1/auth/invites", json={"role": "teacher"},
                             headers=principal_auth)
        assert invite.status_code == 200, invite.text
        reg2 = client.post("/api/v1/auth/register", json={
            "inviteCode": invite.json()["code"], "name": "Tara Teacher",
            "email": "tara@example.com", "password": "correct horse battery",
        })
        assert reg2.status_code == 200, reg2.text
        assert reg2.json()["user"]["role"] == "teacher"
        assert reg2.json()["user"]["schoolId"] == "school_1"
        teacher_token = reg2.json()["token"]

        # -- the principal's invite list records the use; a teacher can't read it
        listed = client.get("/api/v1/auth/invites", headers=principal_auth)
        assert listed.status_code == 200
        assert [(i["status"], i["usedBy"]) for i in listed.json()] == [
            ("used", reg2.json()["user"]["id"])]
        assert client.get("/api/v1/auth/invites", headers={
            "Authorization": f"Bearer {teacher_token}"}).status_code == 403
        assert client.delete("/api/v1/auth/invites/no-such-code",
                             headers=principal_auth).status_code == 404

        # -- duplicate email -> 409; short password -> 400
        assert client.post("/api/v1/auth/register", json={
            "inviteCode": invite_code("school_1"), "name": "Dup", "email": "priya@example.com",
            "password": "correct horse battery",
        }).status_code == 409
        assert client.post("/api/v1/auth/register", json={
            "inviteCode": invite_code("school_1"), "name": "X", "email": "short@example.com",
            "password": "short",
        }).status_code == 400

        # -- login: right password 200, wrong password 401
        login_ok = client.post("/api/v1/auth/login", json={
            "email": "priya@example.com", "password": "correct horse battery",
        })
        assert login_ok.status_code == 200
        assert client.post("/api/v1/auth/login", json={
            "email": "priya@example.com", "password": "wrong password entirely",
        }).status_code == 401

        # -- me: valid token, no token, garbage token
        me = client.get("/api/v1/auth/me",
                        headers={"Authorization": f"Bearer {principal_token}"})
        assert me.status_code == 200
        assert me.json()["email"] == "priya@example.com"
        assert me.json()["role"] == "principal"
        assert client.get("/api/v1/auth/me").status_code == 401
        assert client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer garbage"}
        ).status_code == 401

        # -- the actual point: a teacher cannot approve; a principal can
        teacher_auth = {"Authorization": f"Bearer {teacher_token}"}
        created = client.post("/api/v1/assessments", json={
            "teacherId": "tara", "schoolId": "school_1", "title": "Approval Test",
            "subject": "Science", "grade": 10, "chapterIds": [], "blueprint": blueprint_body(),
        }, headers=teacher_auth)
        assert created.status_code == 200
        assessment_id = created.json()["id"]

        assert client.patch(
            f"/api/v1/assessments/{assessment_id}/approve",
            headers={"Authorization": f"Bearer {teacher_token}"},
        ).status_code == 403

        approved = client.patch(
            f"/api/v1/assessments/{assessment_id}/approve",
            headers={"Authorization": f"Bearer {principal_token}"},
        )
        assert approved.status_code == 200, approved.text
        assert approved.json()["status"] == "principalApproved"

        # -- the lock this workflow exists to engage actually engages
        assert client.put(
            f"/api/v1/assessments/{assessment_id}", json=approved.json(),
            headers=teacher_auth,
        ).status_code == 409

        # -- a principal from a different school cannot approve this one
        other_school = client.post("/api/v1/auth/register", json={
            "schoolId": "school_2", "name": "Other Principal",
            "email": "other@example.com", "password": "correct horse battery",
            "principalKey": "test-bootstrap-key",
        })
        assert other_school.json()["user"]["role"] == "principal"
        assert client.patch(
            f"/api/v1/assessments/{assessment_id}/approve",
            headers={"Authorization": f"Bearer {other_school.json()['token']}"},
        ).status_code == 403

        # -- logout invalidates the token
        assert client.post(
            "/api/v1/auth/logout", headers={"Authorization": f"Bearer {principal_token}"},
        ).status_code == 200
        assert client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {principal_token}"},
        ).status_code == 401
        # logout with no/garbage token is a safe no-op, not an error
        assert client.post("/api/v1/auth/logout").status_code == 200


def test_full_boot_school_roster(tmp_path, monkeypatch):
    """GET /auth/users -- the real roster an admin UI picks a teacher or
    student from. Principal-gated, school-scoped by the caller's own
    token, filterable by role."""
    monkeypatch.setenv("ACOS_PRINCIPAL_BOOTSTRAP_KEY", "test-bootstrap-key")
    with _boot_client(tmp_path, monkeypatch) as client:
        principal = client.post("/api/v1/auth/register", json={
            "schoolId": "school_1", "name": "Principal", "email": "principal@example.com",
            "password": "correct horse battery", "principalKey": "test-bootstrap-key",
        }).json()
        principal_auth = {"Authorization": f"Bearer {principal['token']}"}
        client.post("/api/v1/auth/register", json={
            "inviteCode": invite_code("school_1"), "name": "A Teacher", "email": "at@example.com",
            "password": "correct horse battery",
        })
        client.post("/api/v1/auth/register", json={
            "inviteCode": invite_code("school_1", "student"), "name": "A Student", "email": "as@example.com",
            "password": "correct horse battery",
        })
        client.post("/api/v1/auth/register", json={
            "inviteCode": invite_code("school_2"), "name": "Other School Teacher", "email": "ost@example.com",
            "password": "correct horse battery",
        })

        # -- a non-principal can't list the roster
        teacher_token = client.post("/api/v1/auth/login", json={
            "email": "at@example.com", "password": "correct horse battery",
        }).json()["token"]
        assert client.get("/api/v1/auth/users",
                          headers={"Authorization": f"Bearer {teacher_token}"}).status_code == 403

        # -- the principal's own roster, school-scoped -- never the other school's teacher
        all_users = client.get("/api/v1/auth/users", headers=principal_auth)
        assert all_users.status_code == 200
        names = {u["name"] for u in all_users.json()}
        assert names == {"Principal", "A Teacher", "A Student"}

        # -- role filter
        students = client.get("/api/v1/auth/users", params={"role": "student"}, headers=principal_auth)
        assert [u["name"] for u in students.json()] == ["A Student"]

        # -- an invalid role filter is a real 400, not a silent empty list
        assert client.get("/api/v1/auth/users", params={"role": "admin"},
                          headers=principal_auth).status_code == 400


def test_full_boot_parental_consent(tmp_path, monkeypatch):
    """Exercises the 5 parental consent compliance endpoints (DPDP Act 2023 §9):
    POST /api/v1/consent, GET /api/v1/consent, GET /api/v1/consent/missing,
    GET /api/v1/consent/students/{student_id}, and
    DELETE /api/v1/consent/students/{student_id}. Enforces school isolation."""
    with _boot_client(tmp_path, monkeypatch) as client:
        teacher1 = client.post("/api/v1/auth/register", json={
            "inviteCode": invite_code("school_1"), "name": "Teacher One", "email": "t1@example.com",
            "password": "correct horse battery",
        }).json()
        auth1 = {"Authorization": f"Bearer {teacher1['token']}"}

        teacher2 = client.post("/api/v1/auth/register", json={
            "inviteCode": invite_code("school_2"), "name": "Teacher Two", "email": "t2@example.com",
            "password": "correct horse battery",
        }).json()
        auth2 = {"Authorization": f"Bearer {teacher2['token']}"}

        # Initially no consent
        status = client.get("/api/v1/consent/students/s1", headers=auth1)
        assert status.status_code == 200
        assert status.json()["hasConsent"] is False

        # Record consent
        recorded = client.post("/api/v1/consent", json={
            "studentId": "s1",
            "guardianName": "Ramesh Kumar",
            "guardianRelationship": "father",
            "method": "Signed admission form",
            "notes": "Verified at admission desk",
        }, headers=auth1)
        assert recorded.status_code == 200
        assert recorded.json()["status"] == "granted"

        # Check status for s1
        status_after = client.get("/api/v1/consent/students/s1", headers=auth1)
        assert status_after.status_code == 200
        assert status_after.json()["hasConsent"] is True
        assert status_after.json()["record"]["guardianName"] == "Ramesh Kumar"

        # List consents for school_1
        consents = client.get("/api/v1/consent", headers=auth1)
        assert consents.status_code == 200
        assert len(consents.json()) == 1

        # School isolation: school_2 cannot see school_1's consent record
        school2_status = client.get("/api/v1/consent/students/s1", headers=auth2)
        assert school2_status.status_code == 200
        assert school2_status.json()["hasConsent"] is False
        assert len(client.get("/api/v1/consent", headers=auth2).json()) == 0

        # Who is missing consent: s1 is covered at school_1 only.
        missing = client.get("/api/v1/consent/missing",
                             params=[("studentIds", "s1"), ("studentIds", "s2")],
                             headers=auth1)
        assert missing.status_code == 200
        assert missing.json() == {"checked": 2, "missing": ["s2"]}
        assert client.get("/api/v1/consent/missing", params={"studentIds": "s1"},
                          headers=auth2).json()["missing"] == ["s1"]
        assert client.get("/api/v1/consent/missing",
                          params=[("studentIds", f"s{i}") for i in range(501)],
                          headers=auth1).status_code == 400

        # Revoke consent
        revoked = client.delete("/api/v1/consent/students/s1", headers=auth1)
        assert revoked.status_code == 200
        assert revoked.json()["hasConsent"] is False
        assert revoked.json()["record"]["status"] == "revoked"

        status_revoked = client.get("/api/v1/consent/students/s1", headers=auth1)
        assert status_revoked.status_code == 200
        assert status_revoked.json()["hasConsent"] is False
        # Withdrawn consent is missing consent.
        assert client.get("/api/v1/consent/missing", params={"studentIds": "s1"},
                          headers=auth1).json()["missing"] == ["s1"]


def test_full_boot_curriculum_seed_and_read(tmp_path, monkeypatch):
    """docs/ACADEMIC_DATA_MODEL.md: seed the real CBSE Class 10 curriculum
    through the live API (principal-gated, school-scoped -- not a
    caller-supplied school_id) and verify the read endpoints return the
    real seeded data, not just that the store layer works in isolation."""
    monkeypatch.setenv("ACOS_PRINCIPAL_BOOTSTRAP_KEY", "test-bootstrap-key")
    with _boot_client(tmp_path, monkeypatch) as client:
        # -- unauthenticated / non-principal callers can't seed
        assert client.post("/api/v1/curriculum/seed/cbse10", json={
            "academicYearLabel": "2026-27", "startDate": "2026-06-01", "endDate": "2027-04-30",
        }).status_code == 401

        teacher = client.post("/api/v1/auth/register", json={
            "inviteCode": invite_code("school_1"), "name": "Teacher", "email": "teacher@example.com",
            "password": "correct horse battery",
        }).json()
        assert client.post(
            "/api/v1/curriculum/seed/cbse10",
            json={"academicYearLabel": "2026-27", "startDate": "2026-06-01", "endDate": "2027-04-30"},
            headers={"Authorization": f"Bearer {teacher['token']}"},
        ).status_code == 403

        principal = client.post("/api/v1/auth/register", json={
            "schoolId": "school_1", "name": "Principal", "email": "principal@example.com",
            "password": "correct horse battery", "principalKey": "test-bootstrap-key",
        }).json()
        principal_auth = {"Authorization": f"Bearer {principal['token']}"}

        seeded = client.post(
            "/api/v1/curriculum/seed/cbse10",
            json={"academicYearLabel": "2026-27", "startDate": "2026-06-01", "endDate": "2027-04-30"},
            headers=principal_auth,
        )
        assert seeded.status_code == 200, seeded.text
        body = seeded.json()
        assert body["subjectsSeeded"] == 5
        assert body["subjectsSkipped"] == []
        academic_year_id = body["academicYearId"]
        grade_id = body["gradeId"]

        # -- idempotent through the live API too, not just the store layer
        seeded_again = client.post(
            "/api/v1/curriculum/seed/cbse10",
            json={"academicYearLabel": "2026-27", "startDate": "2026-06-01", "endDate": "2027-04-30"},
            headers=principal_auth,
        )
        assert seeded_again.json()["academicYearId"] == academic_year_id

        # -- reads need a signed-in caller (anonymous until 2026-09-21; the
        # cross-school half is pinned in tests/test_curriculum_read_scoping.py)
        assert client.get("/api/v1/curriculum/boards").status_code == 401
        assert client.get("/api/v1/curriculum/academic-years",
                          params={"school_id": "school_1"}).status_code == 401
        assert client.get(
            f"/api/v1/curriculum/academic-years/{academic_year_id}/grades").status_code == 401
        assert client.get(f"/api/v1/curriculum/grades/{grade_id}/subjects").status_code == 401

        # -- reads return the real seeded data
        boards = client.get("/api/v1/curriculum/boards", headers=principal_auth)
        assert any(b["code"] == "CBSE" for b in boards.json())

        years = client.get("/api/v1/curriculum/academic-years", params={"school_id": "school_1"},
                           headers=principal_auth)
        assert any(y["id"] == academic_year_id and y["label"] == "2026-27" for y in years.json())

        grades = client.get(f"/api/v1/curriculum/academic-years/{academic_year_id}/grades",
                            headers=principal_auth)
        assert any(g["id"] == grade_id and g["number"] == 10 for g in grades.json())

        subjects = client.get(f"/api/v1/curriculum/grades/{grade_id}/subjects",
                              headers=principal_auth)
        subject_names = {s["name"] for s in subjects.json()}
        assert subject_names == {"Mathematics", "Science", "Social Science", "English", "Hindi"}
        science = next(s for s in subjects.json() if s["name"] == "Science")

        assert client.get(f"/api/v1/curriculum/subjects/{science['id']}/books").status_code == 401
        books = client.get(f"/api/v1/curriculum/subjects/{science['id']}/books",
                           headers=principal_auth)
        assert books.json()[0]["status"] == "ready"
        book_id = books.json()[0]["id"]

        assert client.get(f"/api/v1/curriculum/books/{book_id}/chapters").status_code == 401
        assert client.get(f"/api/v1/curriculum/books/{book_id}/units").status_code == 401
        chapters = client.get(f"/api/v1/curriculum/books/{book_id}/chapters",
                              headers=principal_auth)
        chapter_names = {c["name"] for c in chapters.json()}
        assert "Chemical Reactions and Equations" in chapter_names
        assert "Our Environment" in chapter_names

        units = client.get(f"/api/v1/curriculum/books/{book_id}/units", headers=principal_auth)
        assert sum(u["marks"] for u in units.json()) == 80  # real CBSE Science X total

        # -- a same-school teacher reads the same hierarchy, not just the principal
        teacher_auth = {"Authorization": f"Bearer {teacher['token']}"}
        assert client.get(f"/api/v1/curriculum/books/{book_id}/chapters",
                          headers=teacher_auth).json() == chapters.json()

        # -- §5-9: TOC ingestion
        toc_res = client.post(
            f"/api/v1/curriculum/books/{book_id}/toc/ingest",
            json={"tocText": "Unit 1: Test Unit\nChapter 1: Test Chapter"},
            headers=principal_auth,
        )
        assert toc_res.status_code == 200
        assert toc_res.json()["unitsCreated"] >= 1

        # -- any grade 6-12, not only 10 (PRD section 0 decision 4). The
        # detailed behaviour lives in tests/test_curriculum_seed_grades.py;
        # this pins the live route and its bound.
        assert client.post("/api/v1/curriculum/seed/cbse", json={
            "academicYearLabel": "2026-27", "startDate": "2026-06-01",
            "endDate": "2027-04-30", "grade": 7,
        }).status_code == 401
        grade_7 = client.post(
            "/api/v1/curriculum/seed/cbse",
            json={"academicYearLabel": "2026-27", "startDate": "2026-06-01",
                  "endDate": "2027-04-30", "grade": 7},
            headers=principal_auth,
        )
        assert grade_7.status_code == 200, grade_7.text
        assert grade_7.json()["grade"] == 7
        assert grade_7.json()["chaptersSeeded"] > 0
        assert client.post(
            "/api/v1/curriculum/seed/cbse",
            json={"academicYearLabel": "2026-27", "startDate": "2026-06-01",
                  "endDate": "2027-04-30", "grade": 13},
            headers=principal_auth,
        ).status_code == 422

        # -- seed -> pending template topics -> approved topics for one chapter
        chapter_id = next(c["id"] for c in chapters.json()
                          if c["name"] == "Chemical Reactions and Equations")
        assert client.get(
            f"/api/v1/curriculum/chapters/{chapter_id}/proposed-topics").status_code == 401
        proposed = client.get(f"/api/v1/curriculum/chapters/{chapter_id}/proposed-topics",
                              headers=principal_auth)
        assert proposed.status_code == 200, proposed.text
        assert proposed.json()[0]["run"]["status"] == "pending"

        assert client.post(
            f"/api/v1/curriculum/chapters/{chapter_id}/topics/approve-all",
            json={}).status_code == 401
        assert client.post(
            f"/api/v1/curriculum/chapters/{chapter_id}/topics/approve-all",
            json={}, headers=teacher_auth).status_code == 403
        approved = client.post(f"/api/v1/curriculum/chapters/{chapter_id}/topics/approve-all",
                               json={}, headers=principal_auth)
        assert approved.status_code == 200, approved.text
        assert approved.json()["topicsCreated"] > 0
        real_topics = client.get(f"/api/v1/curriculum/chapters/{chapter_id}/topics",
                                 headers=principal_auth)
        assert len(real_topics.json()) == approved.json()["topicsCreated"]

        # The same chapter reached the way the Assessment Designer reaches
        # it: by the syllabus slug /catalog gave the page, not by chap_ id.
        by_slug = ("/api/v1/curriculum/chapters/by-slug/Science/10/"
                   "chemical-reactions-equations/topics")
        assert client.get(by_slug).status_code == 401
        slug_topics = client.get(by_slug, headers=principal_auth)
        assert slug_topics.status_code == 200, slug_topics.text
        assert [t["id"] for t in slug_topics.json()] == [t["id"] for t in real_topics.json()]

        # A class this school never seeded says what to do about it -- the
        # picker renders this text instead of looking empty.
        unset = client.get("/api/v1/curriculum/chapters/by-slug/Science/9/"
                           "chemical-reactions-equations/topics", headers=principal_auth)
        assert unset.status_code == 404, unset.text
        assert unset.json()["detail"] == (
            "Class 9 Science has not been set up for your school yet, so there are "
            "no subtopics to filter by. Setting a class up is not something the app "
            "can do yet -- it needs support.")


def test_full_boot_academic_calendar_and_teaching_time_estimates(tmp_path, monkeypatch):
    """§10, §27-29 through the live API: seed -> create calendar -> add
    holidays -> real working-days computation -> set period duration ->
    compute real, calendar-grounded teaching-time estimates across real
    (manually-added, no LLM needed) subtopics -> read one back. Also
    exercises the auth/school-scoping posture: unauthenticated and
    cross-school callers are rejected, same as every other curriculum
    write in this file."""
    monkeypatch.setenv("ACOS_PRINCIPAL_BOOTSTRAP_KEY", "test-bootstrap-key")
    with _boot_client(tmp_path, monkeypatch) as client:
        principal = client.post("/api/v1/auth/register", json={
            "schoolId": "school_1", "name": "Principal", "email": "principal@example.com",
            "password": "correct horse battery", "principalKey": "test-bootstrap-key",
        }).json()
        auth = {"Authorization": f"Bearer {principal['token']}"}

        seeded = client.post(
            "/api/v1/curriculum/seed/cbse10",
            json={"academicYearLabel": "2026-27", "startDate": "2026-06-01", "endDate": "2027-03-31"},
            headers=auth,
        ).json()
        academic_year_id = seeded["academicYearId"]
        grade_id = seeded["gradeId"]
        science = next(s for s in client.get(f"/api/v1/curriculum/grades/{grade_id}/subjects",
                                             headers=auth).json()
                       if s["name"] == "Science")
        book_id = client.get(f"/api/v1/curriculum/subjects/{science['id']}/books",
                             headers=auth).json()[0]["id"]
        chapter_id = client.get(f"/api/v1/curriculum/books/{book_id}/chapters",
                                headers=auth).json()[0]["id"]

        # -- unauthenticated caller can't create a calendar
        assert client.post(
            f"/api/v1/curriculum/academic-years/{academic_year_id}/calendar", json={},
        ).status_code == 401

        # -- create calendar (principal-gated)
        cal = client.post(
            f"/api/v1/curriculum/academic-years/{academic_year_id}/calendar",
            json={"weeklyOffDays": ["sunday"], "alternateSaturdayRule": "2nd,4th"},
            headers=auth,
        )
        assert cal.status_code == 200, cal.text
        assert cal.json()["weeklyOffDays"] == ["sunday"]

        # -- can't create a second calendar for the same year
        assert client.post(
            f"/api/v1/curriculum/academic-years/{academic_year_id}/calendar", json={}, headers=auth,
        ).status_code == 409

        # -- a different school's principal can't read/write this year's calendar
        other_principal = client.post("/api/v1/auth/register", json={
            "schoolId": "school_2", "name": "Other Principal", "email": "other@example.com",
            "password": "correct horse battery", "principalKey": "test-bootstrap-key",
        }).json()
        other_auth = {"Authorization": f"Bearer {other_principal['token']}"}
        assert client.get(
            f"/api/v1/curriculum/academic-years/{academic_year_id}/calendar", headers=other_auth,
        ).status_code == 403
        assert client.post(
            f"/api/v1/curriculum/academic-years/{academic_year_id}/holidays",
            json={"date": "2026-08-15", "label": "Independence Day"}, headers=other_auth,
        ).status_code == 403

        # -- add real holidays
        h1 = client.post(
            f"/api/v1/curriculum/academic-years/{academic_year_id}/holidays",
            json={"date": "2026-08-15", "label": "Independence Day"}, headers=auth,
        )
        assert h1.status_code == 200, h1.text
        client.post(
            f"/api/v1/curriculum/academic-years/{academic_year_id}/holidays",
            json={"date": "2026-10-02", "label": "Gandhi Jayanti"}, headers=auth,
        )
        holidays = client.get(
            f"/api/v1/curriculum/academic-years/{academic_year_id}/holidays", headers=auth,
        ).json()
        assert {h["label"] for h in holidays} == {"Independence Day", "Gandhi Jayanti"}

        # -- a holiday entered by mistake can be removed; an unknown kind or a
        # date outside the year is a 422, never a silent no-op row
        typo = client.post(
            f"/api/v1/curriculum/academic-years/{academic_year_id}/holidays",
            json={"date": "2026-11-11", "label": "Typo", "kind": "public"}, headers=auth,
        ).json()
        typo_url = f"/api/v1/curriculum/academic-years/{academic_year_id}/holidays/{typo['id']}"
        assert client.delete(typo_url, headers=other_auth).status_code == 403
        assert client.delete(typo_url, headers=auth).status_code == 200
        assert client.delete(typo_url, headers=auth).status_code == 404
        assert client.post(
            f"/api/v1/curriculum/academic-years/{academic_year_id}/holidays",
            json={"date": "2030-01-01", "label": "x", "kind": "festival"}, headers=auth,
        ).status_code == 422

        # -- real, computed working days for the year
        wd = client.get(
            f"/api/v1/curriculum/academic-years/{academic_year_id}/working-days", headers=auth,
        )
        assert wd.status_code == 200, wd.text
        wd_body = wd.json()
        assert wd_body["holidayCount"] == 2
        assert "2026-08-15" not in wd_body["dates"]

        # -- the calendar can be corrected in place (a second POST is a 409)
        assert client.put(
            f"/api/v1/curriculum/academic-years/{academic_year_id}/calendar",
            json={"weeklyOffDays": ["Sun"]}, headers=auth,
        ).status_code == 422
        assert client.put(
            f"/api/v1/curriculum/academic-years/{academic_year_id}/calendar",
            json={"weeklyOffDays": ["sunday"], "alternateSaturdayRule": "all"}, headers=other_auth,
        ).status_code == 403
        fixed = client.put(
            f"/api/v1/curriculum/academic-years/{academic_year_id}/calendar",
            json={"weeklyOffDays": ["sunday"], "alternateSaturdayRule": "all"}, headers=auth,
        )
        assert fixed.status_code == 200, fixed.text
        all_sat = client.get(
            f"/api/v1/curriculum/academic-years/{academic_year_id}/working-days", headers=auth,
        ).json()
        assert all_sat["alternateSaturdayOffCount"] > wd_body["alternateSaturdayOffCount"]
        assert client.put(
            f"/api/v1/curriculum/academic-years/{academic_year_id}/calendar",
            json={"weeklyOffDays": ["sunday"], "alternateSaturdayRule": "2nd,4th"}, headers=auth,
        ).status_code == 200
        assert wd_body["workingDays"] == (
            wd_body["totalDays"] - wd_body["weeklyOffCount"]
            - wd_body["alternateSaturdayOffCount"] - wd_body["holidayCount"]
        )

        # -- a real multi-day holiday block (summer-break style range), added
        # as one row with endDate rather than one row per date -- 2026-07-06
        # through 2026-07-08 is a clean Mon-Wed run inside the academic year
        # (2026-06-01..2027-03-31) with no weekly-off/alternate-Saturday day
        # inside it, so every one of the 3 dates counts as a fresh holiday.
        block = client.post(
            f"/api/v1/curriculum/academic-years/{academic_year_id}/holidays",
            json={"date": "2026-07-06", "endDate": "2026-07-08", "label": "Local closure block"},
            headers=auth,
        )
        assert block.status_code == 200, block.text
        assert block.json()["endDate"] == "2026-07-08"

        wd2 = client.get(
            f"/api/v1/curriculum/academic-years/{academic_year_id}/working-days", headers=auth,
        ).json()
        assert wd2["holidayCount"] == wd_body["holidayCount"] + 3
        for d in ("2026-07-06", "2026-07-07", "2026-07-08"):
            assert d not in wd2["dates"]

        # -- set period duration (principal-gated, real, admin-set minutes)
        cfg = client.post(
            f"/api/v1/curriculum/academic-years/{academic_year_id}/period-configuration",
            json={"periodMinutes": 40}, headers=auth,
        )
        assert cfg.status_code == 200, cfg.text
        assert cfg.json()["periodMinutes"] == 40
        assert client.post(
            f"/api/v1/curriculum/academic-years/{academic_year_id}/period-configuration",
            json={"periodMinutes": 45}, headers=auth,
        ).status_code == 409

        # -- real approved Topic/Subtopic content to distribute minutes across
        # (manual add -- no LLM dependency for this test)
        topic = client.post(
            f"/api/v1/curriculum/chapters/{chapter_id}/topics",
            json={"name": "Real Topic"}, headers=auth,
        ).json()
        subtopic = client.post(
            f"/api/v1/curriculum/topics/{topic['id']}/subtopics",
            json={"name": "Real Subtopic"}, headers=auth,
        ).json()

        # -- compute real, calendar-grounded teaching-time estimates
        tte = client.post(
            f"/api/v1/curriculum/books/{book_id}/teaching-time-estimates",
            params={"academic_year_id": academic_year_id},
            json={"periodsPerWeek": 6}, headers=auth,
        )
        assert tte.status_code == 200, tte.text
        tte_body = tte.json()
        assert tte_body["periodMinutes"] == 40
        assert tte_body["estimatesCreated"] >= 1
        # The budget is the year's real teaching periods (Task 105): with no
        # Science timetable, the first 6 working days of each ISO week, after
        # the 2nd/4th-Saturday rule and the holidays above -- not
        # periodsPerWeek x calendarWeeks, which ignored every holiday.
        from collections import defaultdict as _defaultdict
        from datetime import date as _date
        weeks = _defaultdict(list)
        for d in wd2["dates"]:
            weeks[_date.fromisoformat(d).isocalendar()[:2]].append(d)
        real_periods = sum(min(6, len(days)) for days in weeks.values())
        assert tte_body["totalSubjectPeriods"] == real_periods
        assert real_periods < tte_body["periodsPerWeek"] * tte_body["calendarWeeks"]
        assert tte_body["totalInstructionalMinutes"] == real_periods * tte_body["periodMinutes"]
        assert tte_body["fitsInYear"] is True

        # -- read one real estimate back
        est = client.get(
            f"/api/v1/curriculum/subtopics/{subtopic['id']}/teaching-time-estimate",
            params={"academic_year_id": academic_year_id}, headers=auth,
        )
        assert est.status_code == 200, est.text
        assert est.json()["estimatedMinutes"] > 0
        assert est.json()["method"] == "marks_weightage_proportional"

        # -- re-running is idempotent through the live API too
        tte_again = client.post(
            f"/api/v1/curriculum/books/{book_id}/teaching-time-estimates",
            params={"academic_year_id": academic_year_id},
            json={"periodsPerWeek": 6}, headers=auth,
        )
        assert tte_again.json()["estimatesCreated"] == 0


def test_full_boot_subject_period_allocation(tmp_path, monkeypatch):
    """Persisted periods/week through the live API: without one set, omitting
    periodsPerWeek from teaching-time-estimates is a real 400, not a guessed
    default; setting one (an upsert, not one-time-set) makes the omitted
    call resolve it automatically; an explicit value in the same call still
    always wins over the persisted one."""
    monkeypatch.setenv("ACOS_PRINCIPAL_BOOTSTRAP_KEY", "test-bootstrap-key")
    with _boot_client(tmp_path, monkeypatch) as client:
        principal = client.post("/api/v1/auth/register", json={
            "schoolId": "school_1", "name": "Principal", "email": "principal@example.com",
            "password": "correct horse battery", "principalKey": "test-bootstrap-key",
        }).json()
        auth = {"Authorization": f"Bearer {principal['token']}"}
        other_principal = client.post("/api/v1/auth/register", json={
            "schoolId": "school_2", "name": "Other Principal", "email": "other@example.com",
            "password": "correct horse battery", "principalKey": "test-bootstrap-key",
        }).json()
        other_auth = {"Authorization": f"Bearer {other_principal['token']}"}

        seeded = client.post(
            "/api/v1/curriculum/seed/cbse10",
            json={"academicYearLabel": "2026-27", "startDate": "2026-06-01", "endDate": "2027-03-31"},
            headers=auth,
        ).json()
        academic_year_id = seeded["academicYearId"]
        grade_id = seeded["gradeId"]
        science = next(s for s in client.get(f"/api/v1/curriculum/grades/{grade_id}/subjects",
                                             headers=auth).json()
                       if s["name"] == "Science")
        book_id = client.get(f"/api/v1/curriculum/subjects/{science['id']}/books",
                             headers=auth).json()[0]["id"]
        chapter_id = client.get(f"/api/v1/curriculum/books/{book_id}/chapters",
                                headers=auth).json()[0]["id"]

        client.post(f"/api/v1/curriculum/academic-years/{academic_year_id}/period-configuration",
                   json={"periodMinutes": 40}, headers=auth)
        # The estimate is budgeted against the calendar's real teaching days.
        client.post(f"/api/v1/curriculum/academic-years/{academic_year_id}/calendar",
                   json={"weeklyOffDays": ["sunday"]}, headers=auth)
        topic = client.post(f"/api/v1/curriculum/chapters/{chapter_id}/topics",
                            json={"name": "Real Topic"}, headers=auth).json()
        client.post(f"/api/v1/curriculum/topics/{topic['id']}/subtopics",
                   json={"name": "Real Subtopic"}, headers=auth)

        # -- no persisted allocation yet, no explicit value: honest 400
        no_alloc = client.post(
            f"/api/v1/curriculum/books/{book_id}/teaching-time-estimates",
            params={"academic_year_id": academic_year_id}, json={}, headers=auth,
        )
        assert no_alloc.status_code == 400, no_alloc.text

        # -- unauthenticated / cross-school can't set the allocation
        assert client.post(
            f"/api/v1/curriculum/academic-years/{academic_year_id}/subject-period-allocations",
            json={"subject": "Science", "periodsPerWeek": 6},
        ).status_code == 401
        assert client.post(
            f"/api/v1/curriculum/academic-years/{academic_year_id}/subject-period-allocations",
            json={"subject": "Science", "periodsPerWeek": 6}, headers=other_auth,
        ).status_code == 403

        # -- persist Science at 6 periods/week
        set1 = client.post(
            f"/api/v1/curriculum/academic-years/{academic_year_id}/subject-period-allocations",
            json={"subject": "Science", "periodsPerWeek": 6}, headers=auth,
        )
        assert set1.status_code == 200, set1.text
        assert set1.json()["periodsPerWeek"] == 6

        # -- an upsert: setting it again updates the same row, doesn't duplicate
        set2 = client.post(
            f"/api/v1/curriculum/academic-years/{academic_year_id}/subject-period-allocations",
            json={"subject": "Science", "periodsPerWeek": 7}, headers=auth,
        ).json()
        assert set2["id"] == set1.json()["id"]
        assert set2["periodsPerWeek"] == 7
        listed = client.get(
            f"/api/v1/curriculum/academic-years/{academic_year_id}/subject-period-allocations",
            headers=auth,
        ).json()
        assert len(listed) == 1 and listed[0]["periodsPerWeek"] == 7

        # -- omitting periodsPerWeek now resolves the persisted value (7)
        resolved = client.post(
            f"/api/v1/curriculum/books/{book_id}/teaching-time-estimates",
            params={"academic_year_id": academic_year_id}, json={}, headers=auth,
        )
        assert resolved.status_code == 200, resolved.text
        assert resolved.json()["periodsPerWeek"] == 7

        # -- an explicit value in the same call still overrides the persisted one
        overridden = client.post(
            f"/api/v1/curriculum/books/{book_id}/teaching-time-estimates",
            params={"academic_year_id": academic_year_id}, json={"periodsPerWeek": 10}, headers=auth,
        )
        assert overridden.json()["periodsPerWeek"] == 10


def test_full_boot_timetable_slots(tmp_path, monkeypatch):
    """Real weekday timetable entries through the live API: add slots for
    two subjects, list scoped by subject, cross-school rejected on both add
    and delete, delete works and is idempotently absent afterward."""
    monkeypatch.setenv("ACOS_PRINCIPAL_BOOTSTRAP_KEY", "test-bootstrap-key")
    with _boot_client(tmp_path, monkeypatch) as client:
        principal = client.post("/api/v1/auth/register", json={
            "schoolId": "school_1", "name": "Principal", "email": "principal@example.com",
            "password": "correct horse battery", "principalKey": "test-bootstrap-key",
        }).json()
        auth = {"Authorization": f"Bearer {principal['token']}"}
        other_principal = client.post("/api/v1/auth/register", json={
            "schoolId": "school_2", "name": "Other Principal", "email": "other@example.com",
            "password": "correct horse battery", "principalKey": "test-bootstrap-key",
        }).json()
        other_auth = {"Authorization": f"Bearer {other_principal['token']}"}

        seeded = client.post(
            "/api/v1/curriculum/seed/cbse10",
            json={"academicYearLabel": "2026-27", "startDate": "2026-06-01", "endDate": "2027-03-31"},
            headers=auth,
        ).json()
        academic_year_id = seeded["academicYearId"]

        assert client.post(
            f"/api/v1/curriculum/academic-years/{academic_year_id}/timetable-slots",
            json={"subject": "Science", "dayOfWeek": 1, "periodNumber": 1},
        ).status_code == 401
        assert client.post(
            f"/api/v1/curriculum/academic-years/{academic_year_id}/timetable-slots",
            json={"subject": "Science", "dayOfWeek": 1, "periodNumber": 1}, headers=other_auth,
        ).status_code == 403

        s1 = client.post(
            f"/api/v1/curriculum/academic-years/{academic_year_id}/timetable-slots",
            json={"subject": "Science", "dayOfWeek": 1, "periodNumber": 1}, headers=auth,
        )
        assert s1.status_code == 200, s1.text
        client.post(
            f"/api/v1/curriculum/academic-years/{academic_year_id}/timetable-slots",
            json={"subject": "Science", "dayOfWeek": 3, "periodNumber": 1}, headers=auth,
        )
        client.post(
            f"/api/v1/curriculum/academic-years/{academic_year_id}/timetable-slots",
            json={"subject": "Mathematics", "dayOfWeek": 0, "periodNumber": 2}, headers=auth,
        )

        science_slots = client.get(
            f"/api/v1/curriculum/academic-years/{academic_year_id}/timetable-slots",
            params={"subject": "Science"}, headers=auth,
        ).json()
        assert len(science_slots) == 2
        assert {s["dayOfWeek"] for s in science_slots} == {1, 3}

        # -- cross-school can't delete
        assert client.delete(
            f"/api/v1/curriculum/timetable-slots/{s1.json()['id']}", headers=other_auth,
        ).status_code == 403

        deleted = client.delete(f"/api/v1/curriculum/timetable-slots/{s1.json()['id']}", headers=auth)
        assert deleted.status_code == 200, deleted.text
        remaining = client.get(
            f"/api/v1/curriculum/academic-years/{academic_year_id}/timetable-slots",
            params={"subject": "Science"}, headers=auth,
        ).json()
        assert len(remaining) == 1 and remaining[0]["dayOfWeek"] == 3

        assert client.delete(
            f"/api/v1/curriculum/timetable-slots/not_a_real_slot", headers=auth,
        ).status_code == 404


def test_full_boot_micro_scheduling(tmp_path, monkeypatch):
    """§11-14 through the live API: seed -> calendar -> period duration ->
    real Topic/Subtopic content -> teaching-time estimates -> generate the
    real, dated schedule -> read it back both per-book and by date range.
    Also proves the refuse-to-silently-reschedule / force-regenerate and
    school-scoping postures at the HTTP layer, not just the store layer."""
    monkeypatch.setenv("ACOS_PRINCIPAL_BOOTSTRAP_KEY", "test-bootstrap-key")
    with _boot_client(tmp_path, monkeypatch) as client:
        principal = client.post("/api/v1/auth/register", json={
            "schoolId": "school_1", "name": "Principal", "email": "principal@example.com",
            "password": "correct horse battery", "principalKey": "test-bootstrap-key",
        }).json()
        auth = {"Authorization": f"Bearer {principal['token']}"}

        seeded = client.post(
            "/api/v1/curriculum/seed/cbse10",
            json={"academicYearLabel": "2026-27", "startDate": "2026-06-01", "endDate": "2027-03-31"},
            headers=auth,
        ).json()
        academic_year_id = seeded["academicYearId"]
        grade_id = seeded["gradeId"]
        science = next(s for s in client.get(f"/api/v1/curriculum/grades/{grade_id}/subjects",
                                             headers=auth).json()
                       if s["name"] == "Science")
        book_id = client.get(f"/api/v1/curriculum/subjects/{science['id']}/books",
                             headers=auth).json()[0]["id"]
        chapter_id = client.get(f"/api/v1/curriculum/books/{book_id}/chapters",
                                headers=auth).json()[0]["id"]

        client.post(f"/api/v1/curriculum/academic-years/{academic_year_id}/calendar",
                   json={"weeklyOffDays": ["sunday"], "alternateSaturdayRule": "2nd,4th"}, headers=auth)
        client.post(f"/api/v1/curriculum/academic-years/{academic_year_id}/period-configuration",
                   json={"periodMinutes": 40}, headers=auth)

        topic = client.post(f"/api/v1/curriculum/chapters/{chapter_id}/topics",
                            json={"name": "Real Topic"}, headers=auth).json()
        subtopic = client.post(f"/api/v1/curriculum/topics/{topic['id']}/subtopics",
                               json={"name": "Real Subtopic"}, headers=auth).json()

        # -- scheduling before teaching-time estimates exist: the subtopic
        # is honestly reported as skipped, not guessed.
        early = client.post(
            f"/api/v1/curriculum/books/{book_id}/schedule",
            params={"academic_year_id": academic_year_id}, json={"periodsPerWeek": 6}, headers=auth,
        )
        assert early.status_code == 200, early.text
        assert subtopic["id"] in early.json()["subtopicsWithoutEstimate"]
        assert early.json()["lessonsCreated"] == 0

        client.post(f"/api/v1/curriculum/books/{book_id}/teaching-time-estimates",
                   params={"academic_year_id": academic_year_id}, json={"periodsPerWeek": 6}, headers=auth)

        # -- unauthenticated caller can't generate a schedule
        assert client.post(
            f"/api/v1/curriculum/books/{book_id}/schedule",
            params={"academic_year_id": academic_year_id}, json={"periodsPerWeek": 6},
        ).status_code == 401

        sched = client.post(
            f"/api/v1/curriculum/books/{book_id}/schedule",
            params={"academic_year_id": academic_year_id}, json={"periodsPerWeek": 6}, headers=auth,
        )
        assert sched.status_code == 200, sched.text
        sched_body = sched.json()
        assert sched_body["lessonsCreated"] > 0
        assert sched_body["subtopicsScheduled"] >= 1
        assert sched_body["firstScheduledDate"] <= sched_body["lastScheduledDate"]

        # -- re-scheduling without force is refused (409), not silently redone
        assert client.post(
            f"/api/v1/curriculum/books/{book_id}/schedule",
            params={"academic_year_id": academic_year_id}, json={"periodsPerWeek": 6}, headers=auth,
        ).status_code == 409

        # -- force regenerates cleanly
        forced = client.post(
            f"/api/v1/curriculum/books/{book_id}/schedule",
            params={"academic_year_id": academic_year_id},
            json={"periodsPerWeek": 6, "force": True}, headers=auth,
        )
        assert forced.status_code == 200
        assert forced.json()["lessonsCreated"] == sched_body["lessonsCreated"]

        # -- read the real schedule back, per book
        book_schedule = client.get(
            f"/api/v1/curriculum/books/{book_id}/schedule",
            params={"academic_year_id": academic_year_id}, headers=auth,
        )
        assert book_schedule.status_code == 200
        lessons = book_schedule.json()
        assert len(lessons) == sched_body["lessonsCreated"]
        assert all(l["status"] == "scheduled" for l in lessons)

        # -- and by date range (the future daily/weekly/monthly view's real
        # access pattern), school-scoped by the caller's own token
        first_date = sched_body["firstScheduledDate"]
        by_range = client.get(
            "/api/v1/curriculum/schedule",
            params={"start_date": first_date, "end_date": first_date}, headers=auth,
        )
        assert by_range.status_code == 200
        assert len(by_range.json()) >= 1
        assert all(l["date"] == first_date for l in by_range.json())

        # -- a different school's principal reading this book's schedule is refused
        other_principal = client.post("/api/v1/auth/register", json={
            "schoolId": "school_2", "name": "Other Principal", "email": "other2@example.com",
            "password": "correct horse battery", "principalKey": "test-bootstrap-key",
        }).json()
        other_auth = {"Authorization": f"Bearer {other_principal['token']}"}
        assert client.get(
            f"/api/v1/curriculum/books/{book_id}/schedule",
            params={"academic_year_id": academic_year_id}, headers=other_auth,
        ).status_code == 403
        # -- but the date-range endpoint scopes to *their own* school, so it
        # correctly returns empty rather than leaking school_1's lessons
        other_range = client.get(
            "/api/v1/curriculum/schedule",
            params={"start_date": first_date, "end_date": first_date}, headers=other_auth,
        )
        assert other_range.status_code == 200
        assert other_range.json() == []


def test_full_boot_teacher_assignment_and_my_schedule(tmp_path, monkeypatch):
    """§15 through the live API: a principal assigns a real teacher to a
    real book, a real schedule is generated, and the teacher's own
    /my-schedule query returns only their assigned book's real, enriched
    lessons -- never the whole school's schedule, never another teacher's
    or another school's data."""
    monkeypatch.setenv("ACOS_PRINCIPAL_BOOTSTRAP_KEY", "test-bootstrap-key")
    with _boot_client(tmp_path, monkeypatch) as client:
        principal = client.post("/api/v1/auth/register", json={
            "schoolId": "school_1", "name": "Principal", "email": "principal@example.com",
            "password": "correct horse battery", "principalKey": "test-bootstrap-key",
        }).json()
        principal_auth = {"Authorization": f"Bearer {principal['token']}"}

        teacher = client.post("/api/v1/auth/register", json={
            "inviteCode": invite_code("school_1"), "name": "Teacher", "email": "teacher@example.com",
            "password": "correct horse battery",
        }).json()
        teacher_auth = {"Authorization": f"Bearer {teacher['token']}"}

        seeded = client.post(
            "/api/v1/curriculum/seed/cbse10",
            json={"academicYearLabel": "2026-27", "startDate": "2026-06-01", "endDate": "2027-03-31"},
            headers=principal_auth,
        ).json()
        academic_year_id = seeded["academicYearId"]
        grade_id = seeded["gradeId"]
        science = next(s for s in client.get(f"/api/v1/curriculum/grades/{grade_id}/subjects",
                                             headers=principal_auth).json()
                       if s["name"] == "Science")
        book_id = client.get(f"/api/v1/curriculum/subjects/{science['id']}/books",
                             headers=principal_auth).json()[0]["id"]
        chapter_id = client.get(f"/api/v1/curriculum/books/{book_id}/chapters",
                                headers=principal_auth).json()[0]["id"]

        # -- a teacher can't assign themselves (principal-gated)
        assert client.post(
            "/api/v1/curriculum/teacher-assignments",
            json={"teacherId": teacher["user"]["id"], "bookId": book_id}, headers=teacher_auth,
        ).status_code == 403

        # -- a different school's principal can't assign one of school_1's
        # teachers to a school_1 book (school ownership on the book) --
        other_principal = client.post("/api/v1/auth/register", json={
            "schoolId": "school_2", "name": "Other Principal", "email": "other3@example.com",
            "password": "correct horse battery", "principalKey": "test-bootstrap-key",
        }).json()
        assert client.post(
            "/api/v1/curriculum/teacher-assignments",
            json={"teacherId": teacher["user"]["id"], "bookId": book_id},
            headers={"Authorization": f"Bearer {other_principal['token']}"},
        ).status_code == 403

        # -- before any assignment, the teacher's schedule is honestly empty
        empty = client.get("/api/v1/curriculum/my-schedule",
                           params={"start_date": "2026-06-01", "end_date": "2027-03-31"},
                           headers=teacher_auth)
        assert empty.status_code == 200
        assert empty.json() == []

        # -- real assignment
        assign = client.post(
            "/api/v1/curriculum/teacher-assignments",
            json={"teacherId": teacher["user"]["id"], "bookId": book_id}, headers=principal_auth,
        )
        assert assign.status_code == 200, assign.text

        # -- build a real, dated schedule to read back
        client.post(f"/api/v1/curriculum/academic-years/{academic_year_id}/calendar",
                   json={"weeklyOffDays": ["sunday"]}, headers=principal_auth)
        client.post(f"/api/v1/curriculum/academic-years/{academic_year_id}/period-configuration",
                   json={"periodMinutes": 40}, headers=principal_auth)
        topic = client.post(f"/api/v1/curriculum/chapters/{chapter_id}/topics",
                            json={"name": "Real Topic"}, headers=principal_auth).json()
        client.post(f"/api/v1/curriculum/topics/{topic['id']}/subtopics",
                   json={"name": "Real Subtopic"}, headers=principal_auth)
        client.post(f"/api/v1/curriculum/books/{book_id}/teaching-time-estimates",
                   params={"academic_year_id": academic_year_id},
                   json={"periodsPerWeek": 6}, headers=principal_auth)
        sched = client.post(
            f"/api/v1/curriculum/books/{book_id}/schedule",
            params={"academic_year_id": academic_year_id}, json={"periodsPerWeek": 6},
            headers=principal_auth,
        ).json()

        # -- unauthenticated caller can't read anyone's schedule
        assert client.get("/api/v1/curriculum/my-schedule",
                          params={"start_date": "2026-06-01", "end_date": "2027-03-31"}).status_code == 401

        # -- the assigned teacher's own schedule now shows the real,
        # enriched lesson -- subject/chapter/topic/subtopic names resolved,
        # not bare ids
        mine = client.get("/api/v1/curriculum/my-schedule",
                          params={"start_date": "2026-06-01", "end_date": "2027-03-31"},
                          headers=teacher_auth)
        assert mine.status_code == 200, mine.text
        entries = mine.json()
        assert len(entries) == sched["lessonsCreated"]
        assert all(e["bookId"] == book_id for e in entries)
        assert all(e["subjectName"] == "Science" for e in entries)
        assert any(e["subtopicName"] == "Real Subtopic" for e in entries)

        # -- a second, unassigned teacher at the same school sees nothing
        other_teacher = client.post("/api/v1/auth/register", json={
            "inviteCode": invite_code("school_1"), "name": "Teacher Two", "email": "teacher2@example.com",
            "password": "correct horse battery",
        }).json()
        theirs = client.get("/api/v1/curriculum/my-schedule",
                            params={"start_date": "2026-06-01", "end_date": "2027-03-31"},
                            headers={"Authorization": f"Bearer {other_teacher['token']}"})
        assert theirs.status_code == 200
        assert theirs.json() == []


def test_full_boot_completion_tracking(tmp_path, monkeypatch):
    """§15 through the live API: an assigned teacher marks a real lesson
    completed with a note, an unassigned same-school teacher is refused,
    a principal can override, and the mark is honestly reflected back
    through both GET /my-schedule and the PATCH response itself."""
    monkeypatch.setenv("ACOS_PRINCIPAL_BOOTSTRAP_KEY", "test-bootstrap-key")
    with _boot_client(tmp_path, monkeypatch) as client:
        principal = client.post("/api/v1/auth/register", json={
            "schoolId": "school_1", "name": "Principal", "email": "principal@example.com",
            "password": "correct horse battery", "principalKey": "test-bootstrap-key",
        }).json()
        principal_auth = {"Authorization": f"Bearer {principal['token']}"}

        teacher = client.post("/api/v1/auth/register", json={
            "inviteCode": invite_code("school_1"), "name": "Teacher", "email": "teacher@example.com",
            "password": "correct horse battery",
        }).json()
        teacher_auth = {"Authorization": f"Bearer {teacher['token']}"}

        other_teacher = client.post("/api/v1/auth/register", json={
            "inviteCode": invite_code("school_1"), "name": "Other Teacher", "email": "other-teacher@example.com",
            "password": "correct horse battery",
        }).json()
        other_teacher_auth = {"Authorization": f"Bearer {other_teacher['token']}"}

        seeded = client.post(
            "/api/v1/curriculum/seed/cbse10",
            json={"academicYearLabel": "2026-27", "startDate": "2026-06-01", "endDate": "2027-03-31"},
            headers=principal_auth,
        ).json()
        academic_year_id = seeded["academicYearId"]
        grade_id = seeded["gradeId"]
        science = next(s for s in client.get(f"/api/v1/curriculum/grades/{grade_id}/subjects",
                                             headers=principal_auth).json()
                       if s["name"] == "Science")
        book_id = client.get(f"/api/v1/curriculum/subjects/{science['id']}/books",
                             headers=principal_auth).json()[0]["id"]
        chapter_id = client.get(f"/api/v1/curriculum/books/{book_id}/chapters",
                                headers=principal_auth).json()[0]["id"]

        client.post("/api/v1/curriculum/teacher-assignments",
                   json={"teacherId": teacher["user"]["id"], "bookId": book_id}, headers=principal_auth)
        client.post(f"/api/v1/curriculum/academic-years/{academic_year_id}/calendar",
                   json={"weeklyOffDays": ["sunday"]}, headers=principal_auth)
        client.post(f"/api/v1/curriculum/academic-years/{academic_year_id}/period-configuration",
                   json={"periodMinutes": 40}, headers=principal_auth)
        topic = client.post(f"/api/v1/curriculum/chapters/{chapter_id}/topics",
                            json={"name": "Real Topic"}, headers=principal_auth).json()
        client.post(f"/api/v1/curriculum/topics/{topic['id']}/subtopics",
                   json={"name": "Real Subtopic"}, headers=principal_auth)
        client.post(f"/api/v1/curriculum/books/{book_id}/teaching-time-estimates",
                   params={"academic_year_id": academic_year_id},
                   json={"periodsPerWeek": 6}, headers=principal_auth)
        client.post(f"/api/v1/curriculum/books/{book_id}/schedule",
                   params={"academic_year_id": academic_year_id}, json={"periodsPerWeek": 6},
                   headers=principal_auth)

        mine = client.get("/api/v1/curriculum/my-schedule",
                          params={"start_date": "2026-06-01", "end_date": "2027-03-31"},
                          headers=teacher_auth).json()
        lesson_id = mine[0]["lessonId"]
        assert mine[0]["status"] == "scheduled"
        assert mine[0]["note"] is None

        # -- unauthenticated caller can't mark anything
        assert client.patch(f"/api/v1/curriculum/scheduled-lessons/{lesson_id}",
                            json={"status": "completed"}).status_code == 401

        # -- an unassigned same-school teacher can't mark someone else's lesson
        assert client.patch(
            f"/api/v1/curriculum/scheduled-lessons/{lesson_id}",
            json={"status": "completed"}, headers=other_teacher_auth,
        ).status_code == 403

        # -- an invalid status value is rejected before it ever touches the row
        assert client.patch(
            f"/api/v1/curriculum/scheduled-lessons/{lesson_id}",
            json={"status": "done"}, headers=teacher_auth,
        ).status_code == 422

        # -- the assigned teacher marks it completed with a real note
        marked = client.patch(
            f"/api/v1/curriculum/scheduled-lessons/{lesson_id}",
            json={"status": "completed", "note": "Covered fully, good engagement"}, headers=teacher_auth,
        )
        assert marked.status_code == 200, marked.text
        body = marked.json()
        assert body["status"] == "completed"
        assert body["note"] == "Covered fully, good engagement"
        assert body["completedBy"] == teacher["user"]["id"]
        assert body["completedAt"] is not None

        # -- reflected back through my-schedule too, not just the PATCH response
        mine_after = client.get("/api/v1/curriculum/my-schedule",
                                params={"start_date": "2026-06-01", "end_date": "2027-03-31"},
                                headers=teacher_auth).json()
        assert mine_after[0]["status"] == "completed"
        assert mine_after[0]["note"] == "Covered fully, good engagement"

        # -- a principal of the same school can override/mark it too (skipped, no note)
        overridden = client.patch(
            f"/api/v1/curriculum/scheduled-lessons/{lesson_id}",
            json={"status": "skipped"}, headers=principal_auth,
        )
        assert overridden.status_code == 200
        assert overridden.json()["status"] == "skipped"
        assert overridden.json()["note"] is None

        # -- a different school's principal can't touch it at all
        other_principal = client.post("/api/v1/auth/register", json={
            "schoolId": "school_2", "name": "Other Principal", "email": "other-principal@example.com",
            "password": "correct horse battery", "principalKey": "test-bootstrap-key",
        }).json()
        assert client.patch(
            f"/api/v1/curriculum/scheduled-lessons/{lesson_id}",
            json={"status": "completed"},
            headers={"Authorization": f"Bearer {other_principal['token']}"},
        ).status_code == 403


def test_full_boot_rescheduling(tmp_path, monkeypatch):
    """§14 through the live API: a principal ADJUSTs one lesson to a new
    real working day, then PUSHes a whole tail of the schedule for a
    disruption -- both write a real audit trail readable back through
    GET .../history, and both are refused to a non-principal or a
    different school."""
    monkeypatch.setenv("ACOS_PRINCIPAL_BOOTSTRAP_KEY", "test-bootstrap-key")
    with _boot_client(tmp_path, monkeypatch) as client:
        principal = client.post("/api/v1/auth/register", json={
            "schoolId": "school_1", "name": "Principal", "email": "principal@example.com",
            "password": "correct horse battery", "principalKey": "test-bootstrap-key",
        }).json()
        principal_auth = {"Authorization": f"Bearer {principal['token']}"}

        teacher = client.post("/api/v1/auth/register", json={
            "inviteCode": invite_code("school_1"), "name": "Teacher", "email": "teacher@example.com",
            "password": "correct horse battery",
        }).json()
        teacher_auth = {"Authorization": f"Bearer {teacher['token']}"}

        seeded = client.post(
            "/api/v1/curriculum/seed/cbse10",
            json={"academicYearLabel": "2026-27", "startDate": "2026-06-01", "endDate": "2027-03-31"},
            headers=principal_auth,
        ).json()
        academic_year_id = seeded["academicYearId"]
        grade_id = seeded["gradeId"]
        science = next(s for s in client.get(f"/api/v1/curriculum/grades/{grade_id}/subjects",
                                             headers=principal_auth).json()
                       if s["name"] == "Science")
        book_id = client.get(f"/api/v1/curriculum/subjects/{science['id']}/books",
                             headers=principal_auth).json()[0]["id"]
        chapter_id = client.get(f"/api/v1/curriculum/books/{book_id}/chapters",
                                headers=principal_auth).json()[0]["id"]

        client.post("/api/v1/curriculum/teacher-assignments",
                   json={"teacherId": teacher["user"]["id"], "bookId": book_id}, headers=principal_auth)
        client.post(f"/api/v1/curriculum/academic-years/{academic_year_id}/calendar",
                   json={"weeklyOffDays": ["sunday"]}, headers=principal_auth)
        client.post(f"/api/v1/curriculum/academic-years/{academic_year_id}/period-configuration",
                   json={"periodMinutes": 40}, headers=principal_auth)
        for i in range(3):
            topic = client.post(f"/api/v1/curriculum/chapters/{chapter_id}/topics",
                                json={"name": f"Topic {i}"}, headers=principal_auth).json()
            client.post(f"/api/v1/curriculum/topics/{topic['id']}/subtopics",
                       json={"name": f"Subtopic {i}"}, headers=principal_auth)
        # 5 periods a week: the first-N-days fallback uses Mon-Fri and leaves
        # Saturdays free. (At 6 the plan now fills every working day of the
        # year, since the estimate is budgeted against the real periods.)
        client.post(f"/api/v1/curriculum/books/{book_id}/teaching-time-estimates",
                   params={"academic_year_id": academic_year_id},
                   json={"periodsPerWeek": 5}, headers=principal_auth)
        client.post(f"/api/v1/curriculum/books/{book_id}/schedule",
                   params={"academic_year_id": academic_year_id}, json={"periodsPerWeek": 5},
                   headers=principal_auth)

        mine = client.get("/api/v1/curriculum/my-schedule",
                          params={"start_date": "2026-06-01", "end_date": "2027-03-31"},
                          headers=teacher_auth).json()
        assert len(mine) >= 2
        lesson_id = mine[0]["lessonId"]
        old_date = mine[0]["date"]
        # ADJUST refuses a day that already holds this book's lesson (409),
        # so move onto the first real working day (Sunday is the only off
        # day, no holidays) the schedule left free. Until 2026-09-21 this
        # used Monday 2026-06-08, which already held a lesson -- it passed
        # only because ADJUST double-booked the day.
        from datetime import date as _date, timedelta as _timedelta
        occupied = {l["date"] for l in mine}
        d = _date(2026, 6, 2)
        while d.weekday() == 6 or d.isoformat() in occupied:
            d += _timedelta(days=1)
        assert d <= _date(2027, 3, 31), "schedule left no free working day to ADJUST onto"
        free_day = d.isoformat()

        # -- a teacher (non-principal) can't ADJUST
        assert client.post(
            f"/api/v1/curriculum/scheduled-lessons/{lesson_id}/reschedule",
            json={"newDate": free_day, "reason": "swap"}, headers=teacher_auth,
        ).status_code == 403

        # -- rejecting a non-working day (a Sunday) with a real 422, not a 500
        assert client.post(
            f"/api/v1/curriculum/scheduled-lessons/{lesson_id}/reschedule",
            json={"newDate": "2026-06-07", "reason": "oops"}, headers=principal_auth,
        ).status_code == 422

        # -- a real ADJUST
        adjusted = client.post(
            f"/api/v1/curriculum/scheduled-lessons/{lesson_id}/reschedule",
            json={"newDate": free_day, "reason": "Assembly conflict"}, headers=principal_auth,
        )
        assert adjusted.status_code == 200, adjusted.text
        assert adjusted.json()["date"] == free_day

        # -- the real audit trail is readable back -- old date, new date,
        # reason, who, when -- through the live API, not just the store
        history = client.get(f"/api/v1/curriculum/scheduled-lessons/{lesson_id}/history",
                             headers=teacher_auth)
        assert history.status_code == 200
        h = history.json()
        assert len(h) == 1
        assert h[0]["oldDate"] == old_date
        assert h[0]["newDate"] == free_day
        assert h[0]["reason"] == "Assembly conflict"
        assert h[0]["mode"] == "adjust"
        assert h[0]["actor"] == principal["user"]["id"]
        assert h[0]["timestamp"]

        # -- a different school can't read this lesson's history either
        other_principal = client.post("/api/v1/auth/register", json={
            "schoolId": "school_2", "name": "Other Principal", "email": "other-p@example.com",
            "password": "correct horse battery", "principalKey": "test-bootstrap-key",
        }).json()
        other_auth = {"Authorization": f"Bearer {other_principal['token']}"}
        assert client.get(f"/api/v1/curriculum/scheduled-lessons/{lesson_id}/history",
                          headers=other_auth).status_code == 403
        assert client.post(
            f"/api/v1/curriculum/books/{book_id}/schedule/push",
            params={"academic_year_id": academic_year_id},
            json={"fromDate": "2026-06-01", "periodsPerWeek": 6, "reason": "x"}, headers=other_auth,
        ).status_code == 403

        # -- a real PUSH: disruption from the earliest remaining lesson's date
        remaining = client.get(
            f"/api/v1/curriculum/books/{book_id}/schedule",
            params={"academic_year_id": academic_year_id}, headers=principal_auth,
        ).json()
        from_date = min(l["date"] for l in remaining)
        pushed = client.post(
            f"/api/v1/curriculum/books/{book_id}/schedule/push",
            params={"academic_year_id": academic_year_id},
            json={"fromDate": from_date, "periodsPerWeek": 5, "reason": "Unplanned closure"},
            headers=principal_auth,
        )
        assert pushed.status_code == 200, pushed.text
        push_body = pushed.json()
        assert push_body["lessonsPushed"] > 0
        for r in push_body["reschedules"]:
            assert r["mode"] == "push"
            assert r["newDate"] > r["oldDate"]

        # -- each pushed lesson's own history reflects the push, with the
        # right actor and reason, readable through the live API
        one_pushed = push_body["reschedules"][0]
        pushed_history = client.get(
            f"/api/v1/curriculum/scheduled-lessons/{one_pushed['lessonId']}/history",
            headers=principal_auth,
        ).json()
        assert any(e["mode"] == "push" and e["reason"] == "Unplanned closure" for e in pushed_history)


def test_full_boot_student_visibility(tmp_path, monkeypatch):
    """§18 through the live API: a student self-registers (role="student"),
    a principal enrolls them into a real grade, and the student's own
    read-only /my-class-schedule and /my-progress reflect the real class
    schedule -- with a reduced, no-note, no-management-controls subset.
    Also proves a student cannot write anything (mark completion, seed,
    etc.) and cross-school/unenrolled honesty."""
    monkeypatch.setenv("ACOS_PRINCIPAL_BOOTSTRAP_KEY", "test-bootstrap-key")
    with _boot_client(tmp_path, monkeypatch) as client:
        principal = client.post("/api/v1/auth/register", json={
            "schoolId": "school_1", "name": "Principal", "email": "principal@example.com",
            "password": "correct horse battery", "principalKey": "test-bootstrap-key",
        }).json()
        principal_auth = {"Authorization": f"Bearer {principal['token']}"}

        teacher = client.post("/api/v1/auth/register", json={
            "inviteCode": invite_code("school_1"), "name": "Teacher", "email": "teacher@example.com",
            "password": "correct horse battery",
        }).json()
        teacher_auth = {"Authorization": f"Bearer {teacher['token']}"}

        # -- real student self-registration (role="student")
        student = client.post("/api/v1/auth/register", json={
            "inviteCode": invite_code("school_1", "student"), "name": "Student", "email": "student@example.com",
            "password": "correct horse battery",
        }).json()
        assert student["user"]["role"] == "student"
        student_auth = {"Authorization": f"Bearer {student['token']}"}

        seeded = client.post(
            "/api/v1/curriculum/seed/cbse10",
            json={"academicYearLabel": "2026-27", "startDate": "2026-06-01", "endDate": "2027-03-31"},
            headers=principal_auth,
        ).json()
        academic_year_id = seeded["academicYearId"]
        grade_id = seeded["gradeId"]
        science = next(s for s in client.get(f"/api/v1/curriculum/grades/{grade_id}/subjects",
                                             headers=principal_auth).json()
                       if s["name"] == "Science")
        book_id = client.get(f"/api/v1/curriculum/subjects/{science['id']}/books",
                             headers=principal_auth).json()[0]["id"]
        chapter_id = client.get(f"/api/v1/curriculum/books/{book_id}/chapters",
                                headers=principal_auth).json()[0]["id"]

        # -- before enrollment: honestly empty/404, not someone else's data
        assert client.get("/api/v1/curriculum/my-class-schedule",
                          params={"start_date": "2026-06-01", "end_date": "2027-03-31"},
                          headers=student_auth).status_code == 404

        # -- a teacher can't enroll a student (principal-gated)
        assert client.post("/api/v1/curriculum/student-enrollments",
                           json={"studentId": student["user"]["id"], "gradeId": grade_id},
                           headers=teacher_auth).status_code == 403

        # -- real enrollment
        enroll = client.post("/api/v1/curriculum/student-enrollments",
                             json={"studentId": student["user"]["id"], "gradeId": grade_id},
                             headers=principal_auth)
        assert enroll.status_code == 200, enroll.text

        # -- build a real, dated, partially-completed schedule
        client.post("/api/v1/curriculum/teacher-assignments",
                   json={"teacherId": teacher["user"]["id"], "bookId": book_id}, headers=principal_auth)
        client.post(f"/api/v1/curriculum/academic-years/{academic_year_id}/calendar",
                   json={"weeklyOffDays": ["sunday"]}, headers=principal_auth)
        client.post(f"/api/v1/curriculum/academic-years/{academic_year_id}/period-configuration",
                   json={"periodMinutes": 40}, headers=principal_auth)
        topic = client.post(f"/api/v1/curriculum/chapters/{chapter_id}/topics",
                            json={"name": "Real Topic"}, headers=principal_auth).json()
        client.post(f"/api/v1/curriculum/topics/{topic['id']}/subtopics",
                   json={"name": "Real Subtopic"}, headers=principal_auth)
        client.post(f"/api/v1/curriculum/books/{book_id}/teaching-time-estimates",
                   params={"academic_year_id": academic_year_id},
                   json={"periodsPerWeek": 6}, headers=principal_auth)
        client.post(f"/api/v1/curriculum/books/{book_id}/schedule",
                   params={"academic_year_id": academic_year_id}, json={"periodsPerWeek": 6},
                   headers=principal_auth)
        first_lesson = client.get(
            "/api/v1/curriculum/my-schedule", params={"start_date": "2026-06-01", "end_date": "2027-03-31"},
            headers=teacher_auth,
        ).json()[0]
        client.patch(f"/api/v1/curriculum/scheduled-lessons/{first_lesson['lessonId']}",
                     json={"status": "completed", "note": "private teacher note"}, headers=teacher_auth)

        # -- unauthenticated caller can't read anything
        assert client.get("/api/v1/curriculum/my-class-schedule",
                          params={"start_date": "2026-06-01", "end_date": "2027-03-31"}).status_code == 401

        # -- the enrolled student's real, reduced-subset class schedule
        mine = client.get("/api/v1/curriculum/my-class-schedule",
                          params={"start_date": "2026-06-01", "end_date": "2027-03-31"},
                          headers=student_auth)
        assert mine.status_code == 200, mine.text
        entries = mine.json()
        assert len(entries) >= 1
        assert any(e["status"] == "completed" for e in entries)
        # reduced subset: no note, no completedBy field leaks the teacher's
        # private remark to the student
        for e in entries:
            assert "note" not in e
            assert "completedBy" not in e
            assert e["subjectName"] == "Science"

        # -- real progress rollup
        progress = client.get("/api/v1/curriculum/my-progress",
                              params={"academic_year_id": academic_year_id}, headers=student_auth)
        assert progress.status_code == 200, progress.text
        science_progress = next(s for s in progress.json()["subjects"] if s["subjectName"] == "Science")
        assert science_progress["completedCount"] >= 1
        assert science_progress["totalCount"] >= science_progress["completedCount"]

        # -- a student cannot mark lesson completion (no management controls)
        assert client.patch(
            f"/api/v1/curriculum/scheduled-lessons/{first_lesson['lessonId']}",
            json={"status": "skipped"}, headers=student_auth,
        ).status_code == 403

        # -- a different school's student sees nothing (school-scoped) and
        # an unenrolled student gets an honest 404, not another class's data
        other_student = client.post("/api/v1/auth/register", json={
            "inviteCode": invite_code("school_2", "student"), "name": "Other Student", "email": "other-student@example.com",
            "password": "correct horse battery",
        }).json()
        other_student_auth = {"Authorization": f"Bearer {other_student['token']}"}
        assert client.get("/api/v1/curriculum/my-class-schedule",
                          params={"start_date": "2026-06-01", "end_date": "2027-03-31"},
                          headers=other_student_auth).status_code == 404


class _FakeLLMForRoutes:
    """Same shape as extraction.py's own test double -- used here to prove
    the HTTP-layer wiring (routes.py -> extraction.propose/approve_run)
    works end-to-end, not just the already-thoroughly-unit-tested
    extraction.py functions in isolation."""
    def __init__(self, response):
        self.response = response
        self.model = "fake-model"

    @property
    def available(self):
        return True

    def chat_json(self, messages, **kw):
        return self.response


def test_full_boot_sequence_reorder(tmp_path, monkeypatch):
    """PATCH .../sequence through the live API for Unit and Chapter (Topic/
    Subtopic's identical generic store.set_sequence() path is covered at
    the store level in test_curriculum_store.py -- this proves the route
    wiring + auth for a representative couple of the four entity types):
    unauthenticated rejected, cross-school rejected, a real reorder changes
    what units_for_book()/chapters_for_unit() (and so schedule_book(), see
    test_reordering_a_unit_changes_the_next_schedule_book_run) return next."""
    monkeypatch.setenv("ACOS_PRINCIPAL_BOOTSTRAP_KEY", "test-bootstrap-key")
    with _boot_client(tmp_path, monkeypatch) as client:
        principal = client.post("/api/v1/auth/register", json={
            "schoolId": "school_1", "name": "Principal", "email": "principal@example.com",
            "password": "correct horse battery", "principalKey": "test-bootstrap-key",
        }).json()
        auth = {"Authorization": f"Bearer {principal['token']}"}
        other_principal = client.post("/api/v1/auth/register", json={
            "schoolId": "school_2", "name": "Other Principal", "email": "other@example.com",
            "password": "correct horse battery", "principalKey": "test-bootstrap-key",
        }).json()
        other_auth = {"Authorization": f"Bearer {other_principal['token']}"}

        seeded = client.post(
            "/api/v1/curriculum/seed/cbse10",
            json={"academicYearLabel": "2026-27", "startDate": "2026-06-01", "endDate": "2027-04-30"},
            headers=auth,
        ).json()
        grade = client.get(f"/api/v1/curriculum/academic-years/{seeded['academicYearId']}/grades",
                           headers=auth).json()[0]
        science = next(s for s in client.get(f"/api/v1/curriculum/grades/{grade['id']}/subjects",
                                             headers=auth).json()
                       if s["name"] == "Science")
        book = client.get(f"/api/v1/curriculum/subjects/{science['id']}/books", headers=auth).json()[0]
        chapters = client.get(f"/api/v1/curriculum/books/{book['id']}/chapters", headers=auth).json()
        first, second = chapters[0], chapters[1]

        # -- unauthenticated caller can't reorder
        assert client.patch(
            f"/api/v1/curriculum/chapters/{first['id']}/sequence", json={"seq": 99},
        ).status_code == 401

        # -- a different school's principal can't reorder this chapter
        assert client.patch(
            f"/api/v1/curriculum/chapters/{first['id']}/sequence", json={"seq": 99}, headers=other_auth,
        ).status_code == 403

        # -- unknown chapter id: honest 404, not a silent no-op or 500
        assert client.patch(
            "/api/v1/curriculum/chapters/not_a_real_chapter/sequence", json={"seq": 1}, headers=auth,
        ).status_code == 404

        # -- swap the first two chapters' delivery order
        r1 = client.patch(f"/api/v1/curriculum/chapters/{first['id']}/sequence",
                          json={"seq": second["seq"]}, headers=auth)
        assert r1.status_code == 200, r1.text
        r2 = client.patch(f"/api/v1/curriculum/chapters/{second['id']}/sequence",
                          json={"seq": first["seq"]}, headers=auth)
        assert r2.status_code == 200, r2.text
        assert r1.json()["seq"] == second["seq"]
        assert r2.json()["seq"] == first["seq"]

        reordered = client.get(f"/api/v1/curriculum/books/{book['id']}/chapters", headers=auth).json()
        assert reordered[0]["id"] == second["id"]
        assert reordered[1]["id"] == first["id"]

        # -- same reorder proof one level up, for Unit
        units = client.get(f"/api/v1/curriculum/books/{book['id']}/units", headers=auth).json()
        u1, u2 = units[0], units[1]
        client.patch(f"/api/v1/curriculum/units/{u1['id']}/sequence",
                    json={"seq": u2["seq"]}, headers=auth)
        client.patch(f"/api/v1/curriculum/units/{u2['id']}/sequence",
                    json={"seq": u1["seq"]}, headers=auth)
        reordered_units = client.get(f"/api/v1/curriculum/books/{book['id']}/units", headers=auth).json()
        assert reordered_units[0]["id"] == u2["id"]
        assert reordered_units[1]["id"] == u1["id"]


def test_full_boot_curriculum_decomposition_review_and_question_paper(tmp_path, monkeypatch):
    """The transcript's literal acceptance-criteria workflow, end-to-end
    through the live API: seed -> extract -> review -> edit one item ->
    approve -> persist -> (simulated restart already covered at the store
    level in test_curriculum_extraction.py) -> question gets tagged to a
    subtopic -> generate paper using selected subtopics -> paper only
    contains eligible questions. Also: rejected proposals never appear,
    renaming doesn't break references, deleting a linked subtopic is
    blocked, cross-school access is denied.
    """
    monkeypatch.setenv("ACOS_PRINCIPAL_BOOTSTRAP_KEY", "test-bootstrap-key")
    with _boot_client(tmp_path, monkeypatch) as client:
        principal = client.post("/api/v1/auth/register", json={
            "schoolId": "school_1", "name": "Principal", "email": "principal@example.com",
            "password": "correct horse battery", "principalKey": "test-bootstrap-key",
        }).json()
        auth = {"Authorization": f"Bearer {principal['token']}"}

        other_school_principal = client.post("/api/v1/auth/register", json={
            "schoolId": "school_2", "name": "Other Principal", "email": "other-p@example.com",
            "password": "correct horse battery", "principalKey": "test-bootstrap-key",
        }).json()
        other_auth = {"Authorization": f"Bearer {other_school_principal['token']}"}

        seeded = client.post(
            "/api/v1/curriculum/seed/cbse10",
            json={"academicYearLabel": "2026-27", "startDate": "2026-06-01", "endDate": "2027-04-30"},
            headers=auth,
        ).json()
        grade = client.get(f"/api/v1/curriculum/academic-years/{seeded['academicYearId']}/grades",
                           headers=auth).json()[0]
        science = next(s for s in client.get(f"/api/v1/curriculum/grades/{grade['id']}/subjects",
                                             headers=auth).json()
                       if s["name"] == "Science")
        book = client.get(f"/api/v1/curriculum/subjects/{science['id']}/books", headers=auth).json()[0]
        chapter = next(c for c in client.get(f"/api/v1/curriculum/books/{book['id']}/chapters",
                                             headers=auth).json()
                       if c["name"] == "Chemical Reactions and Equations")

        # -- no LLM available: extraction reports manual_required, not a
        # fabrication. Explicitly forced via monkeypatch rather than relying
        # on this environment's real key state -- a real SARVAM_API_KEY can
        # be set here (found 2026-09-12 fixing _llm()'s config-field bug),
        # and this test suite must stay hermetic: no live network call, no
        # real API spend, on every `pytest` run.
        from academicos.curriculum import routes as curriculum_routes
        monkeypatch.setattr(curriculum_routes, "_llm", lambda: None)
        honest_run = client.post(f"/api/v1/curriculum/chapters/{chapter['id']}/extract",
                                 json={}, headers=auth)
        assert honest_run.status_code == 200
        assert honest_run.json()["status"] == "manual_required"

        # -- a real LLM configured: propose a real draft.
        fake_response = {
            "topics": [
                {"name": "Chemical Equations", "confidence": 0.9, "subtopics": [
                    {"name": "Writing chemical equations", "confidence": 0.8},
                    {"name": "Balancing chemical equations", "confidence": 0.8},
                ]},
                {"name": "Types of Chemical Reactions", "confidence": 0.9, "subtopics": [
                    {"name": "Combination reactions", "confidence": 0.8},
                    {"name": "Oxidation and reduction", "confidence": 0.8},
                ]},
            ]
        }
        monkeypatch.setattr(curriculum_routes, "_llm", lambda: _FakeLLMForRoutes(fake_response))

        # -- non-principal / cross-school callers can't extract
        assert client.post(f"/api/v1/curriculum/chapters/{chapter['id']}/extract",
                           json={}).status_code == 401
        assert client.post(f"/api/v1/curriculum/chapters/{chapter['id']}/extract",
                           json={}, headers=other_auth).status_code == 403

        run = client.post(f"/api/v1/curriculum/chapters/{chapter['id']}/extract",
                          json={}, headers=auth).json()
        assert run["status"] == "pending"

        # -- AI DRAFT, not DATABASE: nothing real yet.
        assert client.get(f"/api/v1/curriculum/chapters/{chapter['id']}/topics",
                          headers=auth).json() == []

        # -- cross-school cannot even read the draft
        assert client.get(f"/api/v1/curriculum/extraction-runs/{run['id']}",
                          headers=other_auth).status_code == 403

        run_detail = client.get(f"/api/v1/curriculum/extraction-runs/{run['id']}", headers=auth).json()
        proposals = run_detail["proposals"]
        edit_target = next(p for p in proposals if p["proposedName"] == "Chemical Equations")
        reject_target = next(p for p in proposals if p["proposedName"] == "Types of Chemical Reactions")

        # -- review: edit one, reject one, approve the rest
        approved = client.post(
            f"/api/v1/curriculum/extraction-runs/{run['id']}/approve",
            json={"edits": {edit_target["id"]: "Chemical Equations (Reviewed)"},
                 "rejectedProposalIds": [reject_target["id"]]},
            headers=auth,
        )
        assert approved.status_code == 200, approved.text
        assert approved.json()["topicsCreated"] == 1  # the rejected topic excluded
        assert approved.json()["subtopicsCreated"] == 2

        # -- persisted, real, edited name won -- rejected topic absent
        topics = client.get(f"/api/v1/curriculum/chapters/{chapter['id']}/topics", headers=auth).json()
        assert len(topics) == 1
        topic = topics[0]
        assert topic["name"] == "Chemical Equations (Reviewed)"
        assert {s["name"] for s in topic["subtopics"]} == \
            {"Writing chemical equations", "Balancing chemical equations"}

        # -- manual "+ Add Topic" / "+ Add Subtopic" (no LLM needed at all)
        manual_topic = client.post(
            f"/api/v1/curriculum/chapters/{chapter['id']}/topics",
            json={"name": "Rate of Reaction"}, headers=auth,
        ).json()
        assert manual_topic["sourceType"] == "manual"
        manual_sub = client.post(
            f"/api/v1/curriculum/topics/{manual_topic['id']}/subtopics",
            json={"name": "Factors affecting reaction rate"}, headers=auth,
        ).json()
        assert manual_sub["sourceType"] == "manual"

        subtopic_id = next(s["id"] for s in topic["subtopics"]
                           if s["name"] == "Balancing chemical equations")
        original_canonical_id = next(s["canonicalId"] for s in topic["subtopics"]
                                     if s["id"] == subtopic_id)

        # -- tag a real question against this chapter's real subtopics
        # (tagged while the subtopic still has its original name, matching
        # how a real question-bank tagging pass would run against the
        # curriculum as it existed when the paper was assembled)
        assert client.post(  # no token -> 401, real security-review fix
            f"/api/v1/curriculum/chapters/{chapter['id']}/questions/tag",
            json={"questionId": "q_balance_1", "questionText": "Balance the following chemical equation."},
        ).status_code == 401
        assert client.post(  # wrong school -> 403
            f"/api/v1/curriculum/chapters/{chapter['id']}/questions/tag",
            json={"questionId": "q_balance_1", "questionText": "Balance the following chemical equation."},
            headers=other_auth,
        ).status_code == 403
        tagged = client.post(
            f"/api/v1/curriculum/chapters/{chapter['id']}/questions/tag",
            json={"questionId": "q_balance_1", "questionText": "Balance the following chemical equation."},
            headers=auth,
        )
        assert tagged.status_code == 200
        assert any(t["subtopicId"] == subtopic_id for t in tagged.json()["tagged"])

        # -- rename: canonical_id (what the tag above keys against) is
        # untouched, so the question<->subtopic link survives the rename.
        renamed = client.patch(f"/api/v1/curriculum/subtopics/{subtopic_id}",
                               json={"name": "Balancing equations (renamed)"}, headers=auth)
        assert renamed.json()["name"] == "Balancing equations (renamed)"
        assert renamed.json()["canonicalId"] == original_canonical_id
        assert client.post("/api/v1/curriculum/questions/by-subtopics",
                           json={"subtopicIds": [subtopic_id]},
                           headers=auth).json()["questionIds"] == ["q_balance_1"]

        # -- generate paper using selected subtopics: only tagged questions
        by_subtopic = client.post("/api/v1/curriculum/questions/by-subtopics",
                                  json={"subtopicIds": [subtopic_id]}, headers=auth)
        assert by_subtopic.json()["questionIds"] == ["q_balance_1"]
        # A subtopic nothing was tagged to returns no questions -- not a
        # silent guess. Uses the unrelated manually-added subtopic
        # ("Factors affecting reaction rate" shares no real vocabulary with
        # the tagged "balance the equation" question) rather than a
        # same-topic sibling, since the lexical tagger legitimately can
        # (and, checked directly: does) match more than one subtopic when
        # their names genuinely share words -- a real property of the
        # matcher, not a bug this assertion should fight.
        assert client.post("/api/v1/curriculum/questions/by-subtopics",
                           json={"subtopicIds": [manual_sub["id"]]},
                           headers=auth).json()["questionIds"] == []

        # -- deleting a linked subtopic is blocked, not silent data loss
        blocked = client.delete(f"/api/v1/curriculum/subtopics/{subtopic_id}", headers=auth)
        assert blocked.status_code == 409
        # cross-school cannot delete it either (403 before the link check)
        assert client.delete(f"/api/v1/curriculum/subtopics/{subtopic_id}",
                             headers=other_auth).status_code == 403
        # explicit force=true migrates past the block
        forced = client.delete(f"/api/v1/curriculum/subtopics/{subtopic_id}?force=true", headers=auth)
        assert forced.status_code == 200
        assert client.post("/api/v1/curriculum/questions/by-subtopics",
                           json={"subtopicIds": [subtopic_id]},
                           headers=auth).json()["questionIds"] == []


def test_full_boot_assessment_lifecycle(tmp_path, monkeypatch):
    """create -> read -> list -> update -> status -> answer-key -> question
    search/optimize -> paper generate -> export -> file, plus the empty and
    invalid-body cases on every step."""
    with _boot_client(tmp_path, monkeypatch) as client:
        # Every assessment route is now behind Depends(get_current_user);
        # register a teacher and thread the token through every call.
        teacher = client.post("/api/v1/auth/register", json={
            "inviteCode": invite_code("school_1"), "name": "Lifecycle Teacher",
            "email": "lifecycle@example.com", "password": "correct horse battery",
        }).json()
        auth = {"Authorization": f"Bearer {teacher['token']}"}

        # -- create
        body = {
            "teacherId": "teacher_1", "schoolId": "school_1",
            "title": "Lifecycle Test", "subject": "Mathematics", "grade": 10,
            "chapterIds": ["ch1"], "blueprint": blueprint_body(),
        }
        created = client.post("/api/v1/assessments", json=body, headers=auth)
        assert created.status_code == 200, created.text
        assessment_id = created.json()["id"]

        assert client.post("/api/v1/assessments", json={}, headers=auth).status_code == 422

        # -- read / list
        fetched = client.get(f"/api/v1/assessments/{assessment_id}", headers=auth)
        assert fetched.status_code == 200
        assert client.get("/api/v1/assessments/does_not_exist", headers=auth).status_code == 404
        listed = client.get("/api/v1/assessments", headers=auth)
        assert listed.status_code == 200
        assert any(a["id"] == assessment_id for a in listed.json())
        # listing another teacher's assessments is refused (caller is not a principal)
        assert client.get(
            "/api/v1/assessments", params={"teacher_id": "someone_else"}, headers=auth,
        ).status_code == 403

        # -- update (GET body is a valid PUT body)
        put = client.put(f"/api/v1/assessments/{assessment_id}", json=fetched.json(), headers=auth)
        assert put.status_code == 200

        # -- status
        status = client.patch(f"/api/v1/assessments/{assessment_id}/status",
                              json={"status": "questionsSelected"}, headers=auth)
        assert status.status_code == 200
        assert status.json()["status"] == "questionsSelected"
        assert client.patch(
            f"/api/v1/assessments/{assessment_id}/status",
            json={"status": "bogus_status"}, headers=auth,
        ).status_code == 422
        assert client.patch(
            "/api/v1/assessments/nope/status", json={"status": "draft"}, headers=auth,
        ).status_code == 404

        # -- answer key
        key = client.post(f"/api/v1/assessments/{assessment_id}/answer-key", json={
            "assessmentId": assessment_id, "questions": [question_body()],
            "correctOptions": {},
        }, headers=auth)
        assert key.status_code == 200
        assert key.json()["totalMarks"] == 2

        # -- question search / optimize on an empty corpus. Both are
        # auth-gated as of 2026-09-16 (they were open, and both are
        # compute-backed).
        search = client.post("/api/v1/questions/search", json={
            "subject": "Science", "grade": 10,
        }, headers=auth)
        assert search.status_code == 200
        assert search.json() == []
        assert client.post("/api/v1/questions/search", json={},
                           headers=auth).status_code == 422
        assert client.post("/api/v1/questions/search", json={
            "subject": "Science", "grade": 10,
        }).status_code == 401

        optimize = client.post("/api/v1/questions/optimize", json={
            "candidates": [], "blueprint": blueprint_body(),
        }, headers=auth)
        assert optimize.status_code == 200
        assert client.post("/api/v1/questions/optimize", json={},
                           headers=auth).status_code == 422

        # -- paper generation: empty selection refused, valid generates
        empty = client.post("/api/v1/papers/generate", json={
            "assessmentId": assessment_id, "blueprint": blueprint_body(),
            "selectedQuestions": [], "template": school_template_body(),
        }, headers=auth)
        assert empty.status_code == 400

        gen = client.post("/api/v1/papers/generate", json={
            "assessmentId": assessment_id, "blueprint": blueprint_body(),
            "selectedQuestions": [question_body()], "template": school_template_body(),
        }, headers=auth)
        assert gen.status_code == 200, gen.text
        paper_id = gen.json()["id"]

        # -- paper read / export / file
        paper = client.get(f"/api/v1/papers/{paper_id}", headers=auth)
        assert paper.status_code == 200
        assert client.get("/api/v1/papers/does_not_exist", headers=auth).status_code == 404

        exported = client.post(f"/api/v1/papers/{paper_id}/export/pdf", headers=auth)
        assert exported.status_code == 200, exported.text
        assert exported.json()["url"] == f"/api/v1/papers/{paper_id}/file?export={exported.json()['watermarkId']}"
        # docx is an export since EX-5 (tests/test_paper_docx.py); an unknown format is still refused
        assert client.post(
            f"/api/v1/papers/{paper_id}/export/docx", headers=auth,
        ).status_code == 200
        assert client.post(
            f"/api/v1/papers/{paper_id}/export/odt", headers=auth,
        ).status_code == 400
        assert client.post(
            "/api/v1/papers/does_not_exist/export/pdf", headers=auth,
        ).status_code == 404

        file_r = client.get(f"/api/v1/papers/{paper_id}/file", headers=auth)
        assert file_r.status_code == 200
        assert file_r.headers["content-type"] == "application/pdf"
        assert client.get("/api/v1/papers/does_not_exist/file", headers=auth).status_code == 404

        # -- mail/send-paper: pdf must already exist; a nonexistent paper 404s
        assert client.post("/api/v1/mail/send-paper", json={
            "paperId": "does_not_exist", "recipients": ["t@example.com"],
        }, headers=auth).status_code == 404

        # -- paper-templates endpoint delegates to the same template store
        templates = client.get("/api/v1/schools/school_1/paper-templates", headers=auth)
        assert templates.status_code == 200
        assert any(t["id"] for t in templates.json())


def test_full_boot_syllabus_catalog_and_templates(tmp_path, monkeypatch):
    with _boot_client(tmp_path, monkeypatch) as client:
        teacher = client.post("/api/v1/auth/register", json={
            "inviteCode": invite_code("school_1"), "name": "Template Teacher",
            "email": "template@example.com", "password": "correct horse battery",
        }).json()
        auth = {"Authorization": f"Bearer {teacher['token']}"}

        # Syllabus: Science/10 exists, Physics/10 does not.
        syl = client.get("/api/v1/syllabus/Science/10")
        assert syl.status_code == 200
        assert syl.json()["totalMarks"] > 0
        assert client.get("/api/v1/syllabus/Physics/10").status_code == 404

        tt = client.get("/api/v1/syllabus/Science/10/timetable")
        assert tt.status_code == 200
        assert tt.json()["allocations"]
        assert client.get("/api/v1/syllabus/Physics/10/timetable").status_code == 404

        # Catalog on an empty corpus: no entries, but Science/10 chapters come
        # from the packaged syllabus (shown even with zero questions).
        cat = client.get("/api/v1/catalog")
        assert cat.status_code == 200
        assert cat.json() == {"entries": [], "totalQuestions": 0}

        chapters = client.get("/api/v1/catalog/Science/10/chapters")
        assert chapters.status_code == 200
        assert chapters.json(), "Science/10 syllabus chapters should be listed"

        # School templates CRUD (auth-gated since 2026-09-15).
        listed = client.get("/api/v1/schools/school_1/school-templates", headers=auth)
        assert listed.status_code == 200
        assert any(t["id"] for t in listed.json())

        saved = client.post("/api/v1/schools/school_1/school-templates", json={
            "template": school_template_body("tpl_custom"),
            "sections": [],
        }, headers=auth)
        assert saved.status_code == 200, saved.text
        assert saved.json()["id"] == "tpl_custom"

        sections = client.get(
            "/api/v1/schools/school_1/school-templates/tpl_custom/sections", headers=auth)
        assert sections.status_code == 200

        deleted = client.delete(
            "/api/v1/schools/school_1/school-templates/tpl_custom", headers=auth)
        assert deleted.status_code == 200
        assert deleted.json() == {"ok": True}


def test_full_boot_evaluations_knowledge_practice_insights(tmp_path, monkeypatch):
    # The bootstrap key must be in place before the app boots: UserStore
    # captures it at construction, not per-request.
    monkeypatch.setenv("ACOS_PRINCIPAL_BOOTSTRAP_KEY", "test-bootstrap-key")
    with _boot_client(tmp_path, monkeypatch) as client:
        q = question_body()

        # review_sheet_answer / finalize_sheet_review require a real,
        # school-owned assessment + an authenticated caller (fixed
        # 2026-09-11 -- previously both mutated the graded store for any
        # assessment/student/question with zero authorization). A teacher
        # for school_1 and a real assessment record stand in for what the
        # Assessment Designer flow would already have created.
        teacher = client.post("/api/v1/auth/register", json={
            "inviteCode": invite_code("school_1"), "name": "Eval Teacher",
            "email": "eval-teacher@example.com", "password": "correct horse battery",
        }).json()
        teacher_auth = {"Authorization": f"Bearer {teacher['token']}"}

        other_school_teacher = client.post("/api/v1/auth/register", json={
            "inviteCode": invite_code("school_2"), "name": "Other School Teacher",
            "email": "other-school-teacher@example.com", "password": "correct horse battery",
        }).json()
        other_school_auth = {"Authorization": f"Bearer {other_school_teacher['token']}"}

        # A school_1 principal is required for /insights/school (require_principal).
        principal = client.post("/api/v1/auth/register", json={
            "schoolId": "school_1", "name": "Eval Principal",
            "email": "eval-principal@example.com", "password": "correct horse battery",
            "principalKey": "test-bootstrap-key",
        }).json()
        assert principal["user"]["role"] == "principal"
        principal_auth = {"Authorization": f"Bearer {principal['token']}"}

        # /knowledge and /practice are school-scoped to registered users
        # (require_school_owns_student 404s on any id that isn't a user), so
        # the two students these assertions lean on must be real school_1
        # users -- their generated ids thread through the whole flow.
        sheet_student = client.post("/api/v1/auth/register", json={
            "inviteCode": invite_code("school_1", "student"), "name": "Sheeta", "email": "sheeta@example.com",
            "password": "correct horse battery",
        }).json()
        sheet_id = sheet_student["user"]["id"]
        unknown_student = client.post("/api/v1/auth/register", json={
            "inviteCode": invite_code("school_1", "student"), "name": "Nobody", "email": "nobody@example.com",
            "password": "correct horse battery",
        }).json()
        unknown_id = unknown_student["user"]["id"]

        created = client.post("/api/v1/assessments", json={
            "teacherId": teacher["user"]["id"], "schoolId": "school_1",
            "title": "Evaluation Test", "subject": "Mathematics", "grade": 10,
            "chapterIds": [], "blueprint": blueprint_body(),
        }, headers=teacher_auth)
        assert created.status_code == 200, created.text
        a_ev = created.json()["id"]
        # Every student this test grades or practises has a parent's consent
        # on file (authz.require_consent refuses otherwise).
        grant_consent("school_1", "s_answer", sheet_id, unknown_id)

        # -- evaluation: single answer and full sheet (both now require the
        # authenticated caller from the assessment's own school).
        answer = client.post("/api/v1/evaluations/answer", json={
            "assessmentId": a_ev, "studentId": "s_answer",
            "question": q,
            "answerScheme": q["answerScheme"],
            "studentAnswer": "The solution is x = 2, "
            "obtained by subtracting 3 from both sides then dividing by 2.",
        }, headers=teacher_auth)
        assert answer.status_code == 200, answer.text
        assert answer.json()["awardedMarks"] == 2

        sheet = client.post("/api/v1/evaluations/sheet", json={
            "assessmentId": a_ev, "studentId": sheet_id, "studentName": "Sheeta",
            "questions": [q], "answers": {
                "q_1": "The solution is x = 2, obtained by subtracting 3 from "
                       "both sides then dividing by 2.",
            },
            "correctOptions": {},
        }, headers=teacher_auth)
        assert sheet.status_code == 200, sheet.text
        assert sheet.json()["totalAwarded"] <= sheet.json()["totalMax"]

        # -- review + finalize: the AI's raw score must not reach mastery
        # until the teacher's decision is finalized (evaluate_sheet no
        # longer calls record_evaluations itself).
        assert client.get(
            f"/api/v1/knowledge/{sheet_id}", headers=teacher_auth,
        ).json()["overallMastery"] == 0.0

        # -- authorization itself: no token -> 401; wrong school -> 403
        assert client.post(
            f"/api/v1/evaluations/sheet/{a_ev}/{sheet_id}/review/q_1",
            json={"action": "approve"},
        ).status_code == 401
        assert client.post(
            f"/api/v1/evaluations/sheet/{a_ev}/{sheet_id}/review/q_1",
            json={"action": "approve"}, headers=other_school_auth,
        ).status_code == 403
        assert client.post(
            f"/api/v1/evaluations/sheet/{a_ev}/{sheet_id}/finalize", json={},
        ).status_code == 401
        assert client.post(
            f"/api/v1/evaluations/sheet/{a_ev}/{sheet_id}/finalize", json={},
            headers=other_school_auth,
        ).status_code == 403
        # a real caller, but an assessment id that doesn't exist -> 404,
        # never a 403 that would leak whether the id is real
        assert client.post(
            "/api/v1/evaluations/sheet/not_a_real_assessment/s_sheet/review/q_1",
            json={"action": "approve"}, headers=teacher_auth,
        ).status_code == 404

        # unknown question in this sheet -> 404
        assert client.post(
            f"/api/v1/evaluations/sheet/{a_ev}/{sheet_id}/review/q_missing",
            json={"action": "approve"}, headers=teacher_auth,
        ).status_code == 404
        # review against a student/assessment with no evaluated sheet -> 404
        assert client.post(
            f"/api/v1/evaluations/sheet/{a_ev}/s_never_evaluated/review/q_1",
            json={"action": "approve"}, headers=teacher_auth,
        ).status_code == 404

        # teacher overrides the AI's award for q_1 down to 0/2
        edited = client.post(
            f"/api/v1/evaluations/sheet/{a_ev}/{sheet_id}/review/q_1",
            json={"action": "edit", "marks": 0}, headers=teacher_auth,
        )
        assert edited.status_code == 200, edited.text
        assert edited.json()["awardedMarks"] == 0
        assert edited.json()["maxMarks"] == 2

        # edit with no marks -> 400; unknown action -> 400
        assert client.post(
            f"/api/v1/evaluations/sheet/{a_ev}/{sheet_id}/review/q_1",
            json={"action": "edit"}, headers=teacher_auth,
        ).status_code == 400
        assert client.post(
            f"/api/v1/evaluations/sheet/{a_ev}/{sheet_id}/review/q_1",
            json={"action": "bogus"}, headers=teacher_auth,
        ).status_code == 400

        # finalize with no evaluated sheet -> 404
        assert client.post(
            f"/api/v1/evaluations/sheet/{a_ev}/s_never_evaluated/finalize",
            json={}, headers=teacher_auth,
        ).status_code == 404

        finalized = client.post(
            f"/api/v1/evaluations/sheet/{a_ev}/{sheet_id}/finalize",
            json={}, headers=teacher_auth,
        )
        assert finalized.status_code == 200, finalized.text
        assert finalized.json()["totalAwarded"] == 0  # reflects the teacher's override, not the AI's
        assert finalized.json()["totalMax"] == 2

        # mastery now reflects the teacher-finalized (not AI-original) mark.
        after = client.get(f"/api/v1/knowledge/{sheet_id}", headers=teacher_auth).json()
        assert after["overallMastery"] < 1.0

        # Re-evaluating the finalized sheet would replace every mark on it
        # (here with an empty sheet). Without a reason that is 409; with one
        # it goes through and is audited (grade_lock.py, audit item 8.5).
        assert client.post("/api/v1/evaluations/sheet", json={
            "assessmentId": a_ev, "studentId": sheet_id,
            "questions": [], "answers": {},
        }, headers=teacher_auth).status_code == 409
        assert client.post("/api/v1/evaluations/sheet", json={
            "assessmentId": a_ev, "studentId": sheet_id,
            "questions": [], "answers": {}, "reason": "re-marking after moderation",
        }, headers=teacher_auth).status_code == 200

        # -- knowledge: empty student is 200 (empty mastery), report 404s.
        knowledge = client.get(f"/api/v1/knowledge/{unknown_id}", headers=teacher_auth)
        assert knowledge.status_code == 200
        assert knowledge.json()["overallMastery"] == 0.0
        assert client.get(
            f"/api/v1/knowledge/{unknown_id}/report", headers=teacher_auth,
        ).status_code == 404

        # -- practice: nothing to remediate -> 400; unknown set -> 404.
        practice = client.post(
            "/api/v1/practice/generate",
            json={"studentId": unknown_id, "subject": "Science", "grade": "X"},
            headers=teacher_auth,
        )
        assert practice.status_code == 400
        assert client.post(
            "/api/v1/practice/submit", json={"setId": "nope", "answers": {}},
            headers=teacher_auth,
        ).status_code == 404

        # -- insights: no evaluated sheets for this assessment -> class 404;
        # school is principal-only and 200 (empty).
        assert client.get(
            "/api/v1/insights/class/assessment_with_no_sheets", headers=teacher_auth,
        ).status_code == 404
        school = client.get("/api/v1/insights/school/school_1", headers=principal_auth)
        assert school.status_code == 200


def test_full_boot_scan_session_error_paths(tmp_path, monkeypatch):
    """Scan routes exercised via their proper-4xx paths: no network, no OCR
    pipeline, no Supabase. Every route is hit with a real request."""
    with _boot_client(tmp_path, monkeypatch) as client:
        teacher = client.post("/api/v1/auth/register", json={
            "inviteCode": invite_code("school_1"), "name": "Scan Teacher",
            "email": "scan-teacher@example.com", "password": "correct horse battery",
        }).json()
        auth = {"Authorization": f"Bearer {teacher['token']}"}

        # Every session route verifies the session's assessment belongs to
        # the caller's school, so the session must reference a real owned
        # assessment rather than a made-up id.
        assessment = client.post("/api/v1/assessments", json={
            "teacherId": teacher["user"]["id"], "schoolId": "school_1",
            "title": "Scan Session Test", "subject": "Mathematics", "grade": 10,
            "chapterIds": [], "blueprint": blueprint_body(),
        }, headers=auth)
        assert assessment.status_code == 200, assessment.text
        a_scan = assessment.json()["id"]
        grant_consent("school_1", "s1")  # scanning needs it (authz.require_consent)

        created = client.post("/api/v1/scan/sessions", json={
            "assessmentId": a_scan, "studentId": "s1", "studentName": "Student",
        }, headers=auth)
        assert created.status_code == 200, created.text
        session_id = created.json()["id"]

        # Empty session -> review is empty; process has no paper; finalize has
        # nothing; review-decision on an unknown question 400s; assets 404.
        review = client.get(f"/api/v1/scan/sessions/{session_id}/review", headers=auth)
        assert review.status_code == 200
        assert review.json()["items"] == []

        process = client.post(f"/api/v1/scan/sessions/{session_id}/process", headers=auth)
        assert process.status_code == 409
        assert "no generated paper" in process.json()["detail"]

        finalize = client.post(f"/api/v1/scan/sessions/{session_id}/finalize", headers=auth)
        assert finalize.status_code == 409

        decision = client.post(
            f"/api/v1/scan/sessions/{session_id}/review/q_1",
            json={"action": "approve"}, headers=auth,
        )
        assert decision.status_code == 400
        assert "not in this session's review queue" in decision.json()["detail"]

        assert client.get(
            f"/api/v1/scan/sessions/{session_id}/pages/1/image", headers=auth
        ).status_code == 404
        assert client.get(
            f"/api/v1/scan/sessions/{session_id}/raw-pdf", headers=auth
        ).status_code == 404
        assert client.get(
            f"/api/v1/scan/sessions/{session_id}/corrected-pdf", headers=auth
        ).status_code == 404

        # Nonexistent session -> 404 on every route.
        for method, path in (
            ("POST", "/api/v1/scan/sessions/scan_missing/process"),
            ("GET", "/api/v1/scan/sessions/scan_missing/review"),
            ("POST", "/api/v1/scan/sessions/scan_missing/review/q_1"),
            ("POST", "/api/v1/scan/sessions/scan_missing/finalize"),
            ("GET", "/api/v1/scan/sessions/scan_missing/pages/1/image"),
            ("GET", "/api/v1/scan/sessions/scan_missing/raw-pdf"),
            ("GET", "/api/v1/scan/sessions/scan_missing/corrected-pdf"),
        ):
            r = client.request(method, path, json={"action": "approve"}, headers=auth)
            assert r.status_code == 404, f"{method} {path} -> {r.status_code}"

        # The page-upload route needs a real multipart file to pass FastAPI
        # validation; the missing-session 404 still fires first.
        upload = client.post(
            "/api/v1/scan/sessions/scan_missing/pages",
            files={"file": ("page.jpg", b"x", "image/jpeg")},
            headers=auth,
        )
        assert upload.status_code == 404, f"POST /pages -> {upload.status_code}"


def test_full_boot_topic_and_subtopic_sequence_routes(tmp_path, monkeypatch):
    """PATCH .../sequence for TOPIC and SUBTOPIC, through the live API.

    test_full_boot_sequence_reorder deliberately samples only Unit and Chapter
    and leaves the other two route bindings unexercised. The generic
    store.set_sequence() is covered for all four entity types in
    test_curriculum_store.py, so a wrong path or a wrong entity-type string in
    routes.py for these two would have gone unnoticed by the entire suite.
    This closes the two route bindings, including their authorization.
    """
    monkeypatch.setenv("ACOS_PRINCIPAL_BOOTSTRAP_KEY", "test-bootstrap-key")
    with _boot_client(tmp_path, monkeypatch) as client:
        principal = client.post("/api/v1/auth/register", json={
            "schoolId": "school_1", "name": "Principal", "email": "seq-p@example.com",
            "password": "correct horse battery", "principalKey": "test-bootstrap-key",
        }).json()
        auth = {"Authorization": f"Bearer {principal['token']}"}
        other = client.post("/api/v1/auth/register", json={
            "schoolId": "school_2", "name": "Other Principal", "email": "seq-o@example.com",
            "password": "correct horse battery", "principalKey": "test-bootstrap-key",
        }).json()
        other_auth = {"Authorization": f"Bearer {other['token']}"}

        seeded = client.post("/api/v1/curriculum/seed/cbse10", json={
            "academicYearLabel": "2026-27", "startDate": "2026-06-01", "endDate": "2027-04-30",
        }, headers=auth).json()
        grade = client.get(
            f"/api/v1/curriculum/academic-years/{seeded['academicYearId']}/grades", headers=auth).json()[0]
        science = next(s for s in client.get(
            f"/api/v1/curriculum/grades/{grade['id']}/subjects", headers=auth).json()
            if s["name"] == "Science")
        book = client.get(f"/api/v1/curriculum/subjects/{science['id']}/books", headers=auth).json()[0]
        chapter = client.get(f"/api/v1/curriculum/books/{book['id']}/chapters", headers=auth).json()[0]

        # -- two manual topics on a real chapter
        t1 = client.post(f"/api/v1/curriculum/chapters/{chapter['id']}/topics",
                         json={"name": "Chemical equations", "seq": 0}, headers=auth)
        t2 = client.post(f"/api/v1/curriculum/chapters/{chapter['id']}/topics",
                         json={"name": "Types of reactions", "seq": 1}, headers=auth)
        assert t1.status_code == 200, t1.text
        assert t2.status_code == 200, t2.text
        first = t1.json()

        # -- authorization on the topic route
        assert client.patch(f"/api/v1/curriculum/topics/{first['id']}/sequence",
                            json={"seq": 5}).status_code == 401
        assert client.patch(f"/api/v1/curriculum/topics/{first['id']}/sequence",
                            json={"seq": 5}, headers=other_auth).status_code == 403

        # -- the route actually reorders; that is the wiring being proved
        moved = client.patch(f"/api/v1/curriculum/topics/{first['id']}/sequence",
                             json={"seq": 9}, headers=auth)
        assert moved.status_code == 200, moved.text
        listed = client.get(f"/api/v1/curriculum/chapters/{chapter['id']}/topics", headers=auth).json()
        assert [t["name"] for t in listed] == ["Types of reactions", "Chemical equations"]

        # -- two subtopics under the first topic, same three assertions
        s1 = client.post(f"/api/v1/curriculum/topics/{first['id']}/subtopics",
                         json={"name": "Balancing equations", "seq": 0}, headers=auth)
        s2 = client.post(f"/api/v1/curriculum/topics/{first['id']}/subtopics",
                         json={"name": "Word equations", "seq": 1}, headers=auth)
        assert s1.status_code == 200, s1.text
        assert s2.status_code == 200, s2.text
        sa = s1.json()

        assert client.patch(f"/api/v1/curriculum/subtopics/{sa['id']}/sequence",
                            json={"seq": 5}).status_code == 401
        assert client.patch(f"/api/v1/curriculum/subtopics/{sa['id']}/sequence",
                            json={"seq": 5}, headers=other_auth).status_code == 403

        moved_s = client.patch(f"/api/v1/curriculum/subtopics/{sa['id']}/sequence",
                               json={"seq": 9}, headers=auth)
        assert moved_s.status_code == 200, moved_s.text
        topics = client.get(f"/api/v1/curriculum/chapters/{chapter['id']}/topics", headers=auth).json()
        topic = next(t for t in topics if t["id"] == first["id"])
        assert [st["name"] for st in topic["subtopics"]] == ["Word equations", "Balancing equations"]


def test_full_boot_teacher_paper_templates(tmp_path, monkeypatch):
    """Every paper_template_routes.py route once on the happy path and once
    on a proper 4xx. The behaviour in depth (sharing, presets, availability
    numbers, gap handling) is tests/test_paper_templates.py; this is the
    inventory's walk. Empty corpus, so generation is a 400 with the
    availability attached rather than a paper."""
    with _boot_client(tmp_path, monkeypatch) as client:
        teacher = client.post("/api/v1/auth/register", json={
            "inviteCode": invite_code("school_1"), "name": "Template Teacher",
            "email": "tpl-walk@example.com", "password": "correct horse battery",
        }).json()
        auth = {"Authorization": f"Bearer {teacher['token']}"}
        base = "/api/v1/schools/school_1/teacher-templates"

        listed = client.get(base, headers=auth)
        assert listed.status_code == 200 and listed.json()["presets"]
        assert client.get("/api/v1/schools/school_2/teacher-templates",
                          headers=auth).status_code == 403

        assert client.post(base, json={}, headers=auth).status_code == 422
        created = client.post(base, json=teacher_template_body(), headers=auth)
        assert created.status_code == 200, created.text
        tid = created.json()["id"]

        assert client.get(f"{base}/{tid}", headers=auth).status_code == 200
        assert client.get(f"{base}/missing", headers=auth).status_code == 404
        assert client.put(f"{base}/{tid}", json=teacher_template_body("Renamed"),
                          headers=auth).json()["name"] == "Renamed"
        assert client.put(f"{base}/missing", json=teacher_template_body(),
                          headers=auth).status_code == 404
        assert client.post(f"{base}/{tid}/share", json={"shared": True},
                           headers=auth).json()["shared"] is True
        assert client.post(f"{base}/{tid}/share", json={}, headers=auth).status_code == 422
        dup = client.post(f"{base}/{tid}/duplicate", json={}, headers=auth)
        assert dup.status_code == 200 and dup.json()["basedOn"] == tid
        assert client.post(f"{base}/missing/duplicate", json={},
                           headers=auth).status_code == 404

        avail = client.post(f"{base}/{tid}/availability", json={}, headers=auth)
        assert avail.status_code == 200
        assert avail.json()["sections"][0]["shortfall"] == 5
        assert client.post(f"{base}/missing/availability", json={},
                           headers=auth).status_code == 404

        gen = client.post("/api/v1/papers/generate-from-template",
                          json={"templateId": tid}, headers=auth)
        assert gen.status_code == 400
        assert gen.json()["detail"]["availability"]["complete"] is False
        assert client.post("/api/v1/papers/generate-from-template", json={},
                           headers=auth).status_code == 422

        assert client.delete(f"{base}/{tid}", headers=auth).json() == {"ok": True}
        assert client.delete(f"{base}/{tid}", headers=auth).status_code == 404

        # Swap / pick one question: a paper from a seeded 1-mark bank.
        from academicos.assessment import pool as pool_mod
        from academicos.models.academic import Question

        bank = pool_mod.QuestionPool()
        for i, word in enumerate(("magnet", "glacier", "enzyme", "turbine", "orbit",
                                  "pigment", "lantern")):
            rec = question_body(f"inv_q{i}", marks=1)
            rec.update({"subject": "Science", "stem": f"Explain how a {word} works."})
            bank.questions.append(pool_mod.PoolQuestion(
                question=Question(canonical_id=rec["id"], title=rec["stem"],
                                  source_text=rec["stem"], marks=1.0),
                subject="Science", grade="X", academic_year="2024", chapter_id="ch1",
                chapter_name=None, chapter_confidence=0.9, text_hash=rec["id"],
                record=rec))
        monkeypatch.setitem(pool_mod._CACHE, ("Science", "X"), bank)
        tid = client.post(base, json=teacher_template_body(), headers=auth).json()["id"]
        paper = client.post("/api/v1/papers/generate-from-template",
                            json={"templateId": tid}, headers=auth).json()["paper"]
        pid = paper["id"]
        swap = client.post(f"/api/v1/papers/{pid}/questions/1/swap", headers=auth)
        assert swap.status_code == 200, swap.text
        assert client.post("/api/v1/papers/missing/questions/1/swap",
                           headers=auth).status_code == 404
        pick = client.post(f"/api/v1/papers/{pid}/questions/1", headers=auth,
                           json={"questionId": swap.json()["replacedQuestionId"]})
        assert pick.status_code == 200, pick.text
        assert client.post(f"/api/v1/papers/{pid}/questions/1", json={},
                           headers=auth).status_code == 422
