"""The v3 audit's "fix first" defects (docs/audits/2026-09-30-e3a64de-v3.md),
each through the routes the web calls. Uses the cover fixture: school_1 with
Ana, Bala, Chitra and Dev, sections 10-A, 10-B and 9-A, and school_2's
principal."""
from __future__ import annotations

import threading
import time
from datetime import datetime, timezone

from test_cover_routes import BASE, w  # noqa: F401 - `w` is a fixture


def _assessment(w, who: str, subject: str = "Mathematics", grade: int = 10) -> dict:
    r = w.c.post("/api/v1/assessments", headers=w.t[who], json={
        "teacherId": "", "schoolId": "school_1", "title": f"{subject} test", "subject": subject,
        "grade": grade, "chapterIds": [],
        "blueprint": {"totalMarks": 10, "durationMinutes": 30,
                      "difficulty": {"easy": 0.3, "medium": 0.4, "hard": 0.3},
                      "bloom": {"remember": 0.2, "understand": 0.2, "apply": 0.2, "analyze": 0.2,
                                "evaluate": 0.1, "create": 0.1},
                      "chapterWeights": {"weights": {}}, "competencyWeights": {"weights": {}}},
    })
    assert r.status_code == 200, r.text
    return r.json()


def _grade_sheet(assessment_id: str, student_id: str, chapter: str, awarded: int) -> None:
    from academicos.assessment import pillar_routes as pr
    from academicos.assessment.evaluate import Evaluation
    from academicos.assessment.schemas import QuestionSchema
    q = QuestionSchema.model_validate({
        "id": f"q-{chapter}", "questionBankId": "b", "subject": "Mathematics", "grade": 10,
        "chapterIds": [chapter], "competencyIds": [], "bloomLevel": "apply", "difficulty": "medium",
        "type": "short_answer", "stem": "Solve it", "parts": [], "marks": 2, "language": "en",
        "source": "teacher_created", "qualityScore": 0.9, "tags": [], "metadata": {},
        "estimatedTimeMinutes": 2, "createdAt": "2026-01-01T00:00:00Z", "updatedAt": "2026-01-01T00:00:00Z",
        "answerScheme": {"totalMarks": 2, "markingPoints": [], "rubricLevels": [], "commonErrors": [],
                         "alternativeAnswers": [], "modelAnswer": "2", "hasPartialCredit": False,
                         "metadata": {}},
    })
    sheet = [(q, Evaluation(question_id=q.id, awarded_marks=awarded, max_marks=2, verdict="partialCredit",
                            confidence=1.0, reasoning=""))]
    pr._graded.save(assessment_id, student_id, sheet)
    pr._knowledge.record_sheet(student_id, sheet, f"sheet:{assessment_id}")


# ---------------- N-67-2: the principal's analytics are their own school's ----------------

def test_school_insights_count_only_the_schools_own_graded_papers(w):
    a = _assessment(w, "ana")
    _grade_sheet(a["id"], "stu_a1", "mathematics-10/real-numbers", 1)
    theirs = w.c.get("/api/v1/insights/school/school_2", headers=w.p2)
    assert theirs.status_code == 200, theirs.text
    assert (theirs.json()["students"], theirs.json()["assessments"], theirs.json()["subjects"]) == (0, 0, [])
    ours = w.c.get("/api/v1/insights/school/school_1", headers=w.p).json()
    assert (ours["students"], ours["assessments"]) == (1, 1)
    [row] = ours["subjects"]
    assert (row["subject"], row["grade"], row["students"]) == ("Mathematics", 10, 1)
    assert row["averageMastery"] == ours["averageMastery"] > 0
    assert not any("Science" in line for line in ours["interventions"])


# ---------------- N-2-3: review is entered and left through the review routes ----------------

def test_a_paper_under_review_is_frozen_until_the_reviewer_decides(w):
    a = _assessment(w, "ana")
    url = f"/api/v1/assessments/{a['id']}"
    assert w.c.patch(f"{url}/status", json={"status": "paperGenerated"}, headers=w.t["ana"]).status_code == 200
    asked = w.c.post(f"{url}/review-request", json={"reviewerId": w.uid["bala"]}, headers=w.t["ana"])
    assert asked.status_code == 200, asked.text
    assert w.c.patch(f"{url}/status", json={"status": "paperGenerated"}, headers=w.t["ana"]).status_code == 409
    body = w.c.get(url, headers=w.t["ana"]).json()
    body["title"] = "changed under review"
    assert w.c.put(url, json=body, headers=w.t["ana"]).status_code == 409
    assert w.c.delete(url, headers=w.t["ana"]).status_code == 409
    back = w.c.post(f"{url}/review-decision", json={"decision": "changes", "comment": "Q3 is ambiguous"},
                    headers=w.t["bala"])
    assert back.status_code == 200, back.text
    body = w.c.get(url, headers=w.t["ana"]).json()
    assert body["status"] == "paperGenerated"
    body["title"] = "fixed"
    assert w.c.put(url, json=body, headers=w.t["ana"]).status_code == 200


# ---------------- N-67-1: a limited admin acts only inside their classes ----------------

def _grant(w, who, cap, scope):
    r = w.c.post("/api/v1/admin/grants", json={"userId": w.uid[who], "capability": cap, "scope": scope},
                 headers=w.p)
    assert r.status_code == 200, r.text


def test_a_class_9_timetable_admin_cannot_touch_class_10_or_the_whole_school(w):
    _grant(w, "dev", "timetable", {"grades": [9]})
    dev = w.t["dev"]
    assert w.c.patch(f"{BASE}/sections/{w.a9}", json={"name": "Lotus"}, headers=dev).status_code == 200
    assert w.c.patch(f"{BASE}/sections/{w.a10}", json={"name": "Rose"}, headers=dev).status_code == 403
    assert w.c.post(f"{BASE}/academic-years/{w.year}/timetable/solve", json={},
                    headers=dev).status_code == 403
    assert w.c.put(f"{BASE}/sections/{w.a10}/allocations/{w.sci10}",
                   json={"teacherId": w.uid["ana"], "periodsPerWeek": 5}, headers=dev).status_code == 403
    # the principal is unaffected
    assert w.c.patch(f"{BASE}/sections/{w.a10}", json={"name": "Rose"}, headers=w.p).status_code == 200


def test_a_subject_admin_sets_their_subject_but_not_the_whole_section(w):
    _grant(w, "bala", "timetable", {"subjectIds": [w.sci10]})
    bala = w.t["bala"]
    cell = w.c.put(f"{BASE}/sections/{w.a10}/allocations/{w.sci10}",
                   json={"teacherId": w.uid["ana"], "periodsPerWeek": 5}, headers=bala)
    assert cell.status_code == 200, cell.text
    assert w.c.patch(f"{BASE}/sections/{w.a10}", json={"name": "Rose"}, headers=bala).status_code == 403


def test_a_limited_reports_admin_sees_their_classes_and_no_school_wide_report(w):
    chitra = w.t["chitra"]           # teaches 9-A only
    assert w.c.get(f"/api/v1/sections/{w.a10}/progress", headers=chitra).status_code == 403
    _grant(w, "chitra", "reports", {"grades": [10]})
    assert w.c.get(f"/api/v1/sections/{w.a10}/progress", headers=chitra).status_code == 200
    assert w.c.get("/api/v1/dashboard/summary", headers=chitra).status_code == 403
    _grant(w, "chitra", "reports", {})
    assert w.c.get("/api/v1/dashboard/summary", headers=chitra).status_code == 200


def test_scope_admits_needs_every_limited_axis_named():
    from academicos.operations.grants import scope_admits
    assert scope_admits({}) is True
    assert scope_admits({"grades": [9]}) is False
    assert scope_admits({"grades": [9]}, grade=9) is True
    assert scope_admits({"grades": [9], "subjectIds": ["s"]}, grade=9) is False
    assert scope_admits({"grades": [9], "subjectIds": ["s"]}, grade=9, subject_id="s") is True


# ---------------- N-9-1: automation runs show only the caller's school's share ----------------

def test_automation_status_shows_each_school_only_its_own_counts(w):
    from academicos.operations import routes as ops
    ops.store().record_automation("exam_reminders", "2026-06-01", 5, {"school_1": 5})
    ours = w.c.get("/api/v1/automations/status", headers=w.p).json()
    theirs = w.c.get("/api/v1/automations/status", headers=w.p2).json()
    assert [(r["job"], r["notified"]) for r in ours] == [("exam_reminders", 5)]
    assert [(r["job"], r["notified"]) for r in theirs] == [("exam_reminders", 0)]


# ---------------- N-8-1 / N-8-2: one delivery pass at a time, and a scheduled one ----------------

def test_two_delivery_passes_at_once_send_each_notification_once(w, monkeypatch):
    from academicos.operations import notifications
    from academicos.operations import routes as ops
    store = ops.store()
    monkeypatch.setattr(type(store), "_deliver_quietly", lambda self: None)
    monkeypatch.setattr(store, "deliver_inline", False)
    noon = datetime(2026, 6, 1, 6, 30, tzinfo=timezone.utc)          # 12:00 IST
    store.register_device(w.uid["ana"], "tok-ana", "android")
    for i in range(3):
        store.notify(school_id="school_1", user_ids=[w.uid["ana"]], kind="homework_assigned",
                     params={"title": f"HW {i}", "subject": "Science", "due": "Friday"}, now=noon)
    sent: list[str] = []

    def slow_push(tokens, title, body, data):
        time.sleep(0.05)
        sent.append(data["id"])
        return "sent", None
    monkeypatch.setattr(notifications, "send_push", slow_push)
    passes = [threading.Thread(target=store.deliver_due, kwargs={"now": noon}) for _ in range(2)]
    for t in passes:
        t.start()
    for t in passes:
        t.join()
    assert len(sent) == 3 and len(set(sent)) == 3


def test_the_scheduler_delivers_what_quiet_hours_held(w, monkeypatch):
    from academicos.operations import automations
    names = [job for job, *_ in automations.JOBS]
    assert "deliveries" in names
    calls = []

    class Ops:
        def deliver_due(self, now=None):
            calls.append(now)
            return 2
    at = datetime(2026, 6, 1, 1, 35, tzinfo=timezone.utc)
    assert automations.deliveries(Ops(), None, None, None, at) == 2 and calls == [at]


# ---------------- N-67-13: a consent register names only this school's students ----------------

def test_consent_cannot_be_recorded_for_another_schools_student(w):
    stu = w.c.get("/api/v1/auth/me", headers=w.stu).json()["id"]
    body = {"studentId": stu, "guardianName": "Parent", "method": "Signed form"}
    assert w.c.post("/api/v1/consent", json=body, headers=w.p2).status_code == 403
    assert w.c.post("/api/v1/consent", json=body, headers=w.p).status_code == 200
    roll = {"studentId": "roll-17", "guardianName": "Parent", "method": "Signed form"}
    assert w.c.post("/api/v1/consent", json=roll, headers=w.p2).status_code == 200


# ---------------- N-9-3: the API's own responses carry security headers ----------------

def test_api_responses_carry_security_headers(w):
    r = w.c.get("/health")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert "max-age" in r.headers["strict-transport-security"]


# ---------------- N-67-8: a person who leaves can be closed out ----------------

def test_closing_an_account_ends_its_sessions_and_sign_in_and_reopening_restores_it(w):
    from academicos.assessment.audit_log import get_audit_log
    from academicos.assessment import auth_routes
    ana = w.uid["ana"]
    _grant(w, "ana", "exams", {})
    closed = w.c.post(f"/api/v1/auth/users/{ana}/close", headers=w.p)
    assert closed.status_code == 200, closed.text
    assert closed.json()["role"] == "left:teacher"
    assert w.c.get("/api/v1/auth/me", headers=w.t["ana"]).status_code == 401
    login = w.c.post("/api/v1/auth/login", json={"email": "ana@example.com", "password": "correct horse battery"})
    assert login.status_code == 403 and "closed" in login.json()["detail"]
    staff = [u["id"] for u in w.c.get("/api/v1/auth/users", headers=w.p).json()]
    left = [u["id"] for u in w.c.get("/api/v1/auth/users", params={"role": "left"}, headers=w.p).json()]
    assert ana not in staff and left == [ana]
    assert w.c.get("/api/v1/my-grants", headers=w.p).status_code == 200
    assert [g for g in w.c.get("/api/v1/admin/grants", headers=w.p).json() if g["userId"] == ana] == []
    rows = get_audit_log(auth_routes._cfg.data_root).for_action("account_closed")
    principal_id = w.c.get("/api/v1/auth/me", headers=w.p).json()["id"]
    assert (rows[0]["details"]["before"], rows[0]["actor"]) == ("teacher", principal_id)

    reopened = w.c.post(f"/api/v1/auth/users/{ana}/reopen", headers=w.p)
    assert reopened.json()["role"] == "teacher"
    again = w.c.post("/api/v1/auth/login", json={"email": "ana@example.com", "password": "correct horse battery"})
    assert again.status_code == 200, again.text


def test_only_the_schools_users_admin_closes_and_never_the_principal_or_themselves(w):
    ana = w.uid["ana"]
    assert w.c.post(f"/api/v1/auth/users/{ana}/close", headers=w.t["bala"]).status_code == 403
    assert w.c.post(f"/api/v1/auth/users/{ana}/close", headers=w.p2).status_code == 404
    me = w.c.get("/api/v1/auth/me", headers=w.p).json()["id"]
    assert w.c.post(f"/api/v1/auth/users/{me}/close", headers=w.p).status_code == 422
    _grant(w, "bala", "users", {})
    assert w.c.post(f"/api/v1/auth/users/{me}/close", headers=w.t["bala"]).status_code == 403
    assert w.c.post(f"/api/v1/auth/users/{ana}/close", headers=w.t["bala"]).status_code == 200
