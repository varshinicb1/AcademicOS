"""Every route declares who may call it, and a student cannot act as staff.

Audit item 8.4, reproduced by two auditors on 2026-09-21 with a student-role
token: 200 on every classmate's answers to a question, 200 on finalizing
another student's sheet and on bulk-awarding marks (updated=1), 200 on
reading an unreleased paper and exporting its answer key. And a school_B
teacher got 200 on POST /v1/revise for a school_A student's retention data.

The tests below hold the app to `academicos.api.route_policy.ROUTE_POLICY`:

1. the table names every served (method, path), and nothing that is gone;
2. each entry matches the route's real dependency chain, so the table cannot
   claim a gate that is not there;
3. every `staff`/`principal` route answers a same-school student with the
   gate's own 403 -- with made-up ids, so a 404 would mean the handler ran
   before the gate;
4. the audit's four attacks replayed (403 for the student, 200 for the
   teacher, and the marks unchanged in between);
5. /v1/revise and /v1/plan check that the learner is the caller's school's
   and, for a student, the caller.
"""
from __future__ import annotations

import re
import uuid

import pytest
from fastapi.testclient import TestClient

from academicos.algorithms.learner_model import Interaction
from academicos.api import main as api_main
from academicos.api.main import app
from academicos.api.route_policy import (
    ANY_USER, API_KEY, PRINCIPAL, PUBLIC, ROUTE_POLICY, SELF_OR_STAFF, STAFF,
    app_operations, iter_routes,
)
from academicos.assessment import auth_routes, qbank_routes

from _auth_helpers import register_invited

STAFF_DETAIL = "this action requires a teacher or principal account"
PRINCIPAL_DETAIL = "this action requires the principal role"
BOOTSTRAP_KEY = "role-gates-bootstrap-key"


# --------------------------------------------------------------- the table


def test_every_route_has_a_declared_policy():
    """The next route cannot forget to choose: an unclassified route fails
    here, and so does an entry for a route that no longer exists."""
    live = app_operations(app)
    declared = frozenset(ROUTE_POLICY)
    assert not (live - declared), (
        "routes with no entry in api/route_policy.py ROUTE_POLICY -- add one "
        f"(and its gate): {sorted(live - declared)}")
    assert not (declared - live), (
        f"ROUTE_POLICY entries for routes the app no longer serves: {sorted(declared - live)}")


def _dependency_calls(dependant) -> set:
    calls = set()
    stack = list(dependant.dependencies)
    while stack:
        d = stack.pop()
        if d.call is not None:
            calls.add(d.call)
        stack.extend(d.dependencies)
    return calls


def _level_from_code(route) -> str:
    dependant = getattr(route, "dependant", None)
    if dependant is None:  # the OpenAPI/docs routes are plain Starlette routes
        return PUBLIC
    calls = _dependency_calls(dependant)
    if auth_routes.require_principal in calls:
        return PRINCIPAL
    if auth_routes.require_staff in calls:
        return STAFF
    if auth_routes.get_current_user in calls:
        return ANY_USER  # self_or_staff is any_user plus a check in the handler
    if any(getattr(c, "__module__", "") == qbank_routes.__name__ for c in calls):
        return API_KEY
    return PUBLIC


def test_declared_policy_matches_each_routes_dependencies():
    mismatches = []
    for method, path, route in iter_routes(app):
        declared = ROUTE_POLICY[(method, path)].level
        actual = _level_from_code(route)
        expected = ANY_USER if declared == SELF_OR_STAFF else declared
        if actual != expected:
            mismatches.append(f"{method} {path}: table says {declared}, code enforces {actual}")
    assert not mismatches, "\n".join(mismatches)


# --------------------------------------------------------------- a booted app


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    """One booted app for the module: school_1 with a principal, a teacher
    and two students; school_2 with a teacher. Singletons are reset the same
    way test_route_inventory._boot_client does, so no earlier boot leaks."""
    from academicos.assessment import audit_log, consent as consent_mod
    from academicos.assessment import consent_routes as consent_routes_mod
    from academicos.assessment import users as users_mod
    from academicos.curriculum import store as curriculum_store_mod

    mp = pytest.MonkeyPatch()
    mp.setenv("ACOS_DATA_ROOT", str(tmp_path_factory.mktemp("role_gates")))
    mp.setenv("ACOS_PRINCIPAL_BOOTSTRAP_KEY", BOOTSTRAP_KEY)
    mp.setattr(audit_log, "_INSTANCE", None)
    mp.setattr(users_mod, "_INSTANCE", None)
    mp.setattr(curriculum_store_mod, "_INSTANCE", None)
    mp.setattr(consent_mod, "_INSTANCE", None)
    mp.setattr(consent_routes_mod, "_store", None)
    mp.setattr(consent_routes_mod, "_audit", None)
    try:
        with TestClient(app) as client:
            tag = uuid.uuid4().hex[:8]
            principal = client.post("/api/v1/auth/register", json={
                "schoolId": "school_1", "name": "Principal", "email": f"p-{tag}@example.com",
                "password": "correct horse battery", "principalKey": BOOTSTRAP_KEY,
            })
            assert principal.status_code == 200, principal.text
            people = {
                "principal": principal.json(),
                "teacher": register_invited(client, "school_1", f"t-{tag}@example.com"),
                "student": register_invited(client, "school_1", f"s-{tag}@example.com",
                                            name="Asha", role="student"),
                "classmate": register_invited(client, "school_1", f"c-{tag}@example.com",
                                              name="Bala", role="student"),
                "other_teacher": register_invited(client, "school_2", f"o-{tag}@example.com"),
            }
            yield client, people
    finally:
        mp.undo()


def _auth(person: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {person['token']}"}


def _concrete(path: str, school_id: str) -> str:
    """Made-up ids everywhere except {school_id}, which is the caller's own:
    a 403 must come from the role gate, not from a school-ownership check."""
    def value(m: re.Match) -> str:
        name = m.group(1)
        if name == "school_id":
            return school_id
        if name in ("page_no", "grade"):
            return "1"
        return f"no_such_{name}"
    return re.sub(r"\{(\w+)\}", value, path)


def _call(client: TestClient, method: str, path: str, headers: dict):
    if method in ("GET", "DELETE"):
        return client.request(method, path, headers=headers)
    return client.request(method, path, json={}, headers=headers)


_GATED = sorted(k for k, p in ROUTE_POLICY.items() if p.level in (STAFF, PRINCIPAL))
_PRINCIPAL_ONLY = sorted(k for k, p in ROUTE_POLICY.items() if p.level == PRINCIPAL)


@pytest.mark.parametrize("method,path", _GATED, ids=[f"{m} {p}" for m, p in _GATED])
def test_a_student_is_refused_every_staff_and_principal_route(world, method, path):
    client, people = world
    student = people["student"]
    r = _call(client, method, _concrete(path, student["user"]["schoolId"]), _auth(student))
    assert r.status_code == 403, f"{method} {path} -> {r.status_code} {r.text[:200]}"
    expected = PRINCIPAL_DETAIL if ROUTE_POLICY[(method, path)].level == PRINCIPAL else STAFF_DETAIL
    assert r.json()["detail"] == expected


@pytest.mark.parametrize("method,path", _PRINCIPAL_ONLY, ids=[f"{m} {p}" for m, p in _PRINCIPAL_ONLY])
def test_a_teacher_is_refused_every_principal_route(world, method, path):
    client, people = world
    teacher = people["teacher"]
    r = _call(client, method, _concrete(path, teacher["user"]["schoolId"]), _auth(teacher))
    assert r.status_code == 403, f"{method} {path} -> {r.status_code} {r.text[:200]}"
    assert r.json()["detail"] == PRINCIPAL_DETAIL


# --------------------------------------------------------------- the audit's attacks


def _question(qid: str = "q_1", marks: int = 2) -> dict:
    return {
        "id": qid, "questionBankId": "bank_1", "subject": "Mathematics", "grade": 10,
        "chapterIds": ["ch1"], "competencyIds": [], "bloomLevel": "apply",
        "difficulty": "medium", "type": "short_answer", "stem": "Solve 2x + 3 = 7",
        "stemLatex": "", "parts": [],
        "answerScheme": {
            "totalMarks": marks,
            "markingPoints": [{"id": "mp1", "description": "correct answer", "marks": marks,
                               "keyword": "solution", "isRequired": False, "synonyms": []}],
            "rubricLevels": [], "commonErrors": [], "alternativeAnswers": [],
            "modelAnswer": "x = 2", "modelAnswerLatex": "", "hasPartialCredit": False,
            "metadata": {},
        },
        "estimatedTimeMinutes": 3, "marks": marks, "language": "en",
        "source": "teacher_created", "qualityScore": 0.9, "tags": [],
        "createdAt": "2026-01-01T00:00:00Z", "updatedAt": "2026-01-01T00:00:00Z",
        "metadata": {},
    }


def _blueprint() -> dict:
    return {
        "totalMarks": 80, "durationMinutes": 180,
        "difficulty": {"easy": 0.3, "medium": 0.4, "hard": 0.3},
        "bloom": {"remember": 0.2, "understand": 0.2, "apply": 0.2, "analyze": 0.2,
                  "evaluate": 0.1, "create": 0.1},
        "chapterWeights": {"weights": {}}, "competencyWeights": {"weights": {}},
    }


def test_the_audits_student_attacks_are_refused_and_teachers_still_work(world):
    client, people = world
    teacher, student, classmate = people["teacher"], people["student"], people["classmate"]
    t_auth, s_auth = _auth(teacher), _auth(student)
    classmate_id = classmate["user"]["id"]

    created = client.post("/api/v1/assessments", json={
        "teacherId": teacher["user"]["id"], "schoolId": "school_1", "title": "Unit test",
        "subject": "Mathematics", "grade": 10, "chapterIds": ["ch1"], "blueprint": _blueprint(),
    }, headers=t_auth)
    assert created.status_code == 200, created.text
    aid = created.json()["id"]
    sheet = client.post("/api/v1/evaluations/sheet", json={
        "assessmentId": aid, "studentId": classmate_id, "studentName": "Bala",
        "questions": [_question()], "answers": {"q_1": "no idea"}, "correctOptions": {},
    }, headers=t_auth)
    assert sheet.status_code == 200, sheet.text
    paper = client.post("/api/v1/papers/generate", json={
        "assessmentId": aid, "blueprint": _blueprint(), "selectedQuestions": [_question()],
        "template": {"id": "tpl_1", "schoolId": "school_1", "name": "Default"},
    }, headers=t_auth)
    assert paper.status_code == 200, paper.text
    pid = paper.json()["id"]

    question_view = f"/api/v1/evaluations/assessment/{aid}/question/q_1"
    before = client.get(question_view, headers=t_auth).json()["answers"]

    # 1. every classmate's answer to one question
    assert client.get(question_view, headers=s_auth).status_code == 403
    # 2. finalize another student's sheet
    finalize = f"/api/v1/evaluations/sheet/{aid}/{classmate_id}/finalize"
    assert client.post(finalize, json={}, headers=s_auth).status_code == 403
    # 3. award marks to another student
    award = f"{question_view}/award"
    assert client.post(award, json={"marks": 2, "studentIds": [classmate_id]},
                       headers=s_auth).status_code == 403
    # 4. export the answer key (and read the paper itself)
    assert client.post(f"/api/v1/papers/{pid}/export/answer_key", headers=s_auth).status_code == 403
    assert client.get(f"/api/v1/papers/{pid}", headers=s_auth).status_code == 403

    # Nothing the student sent changed a mark.
    assert client.get(question_view, headers=t_auth).json()["answers"] == before

    # The gate is not simply closed: the teacher does all of it.
    assert client.get(question_view, headers=t_auth).status_code == 200
    awarded = client.post(award, json={"marks": 1, "studentIds": [classmate_id]}, headers=t_auth)
    assert awarded.status_code == 200, awarded.text
    assert awarded.json()["updated"] == 1
    assert client.post(finalize, json={}, headers=t_auth).status_code == 200
    assert client.post(f"/api/v1/papers/{pid}/export/answer_key", headers=t_auth).status_code == 200
    assert client.get(f"/api/v1/papers/{pid}", headers=t_auth).status_code == 200


def test_a_student_keeps_their_own_routes(world):
    client, people = world
    student = people["student"]
    me = client.get("/api/v1/auth/me", headers=_auth(student))
    assert me.status_code == 200 and me.json()["role"] == "student"
    own = client.get(f"/api/v1/knowledge/{student['user']['id']}", headers=_auth(student))
    assert own.status_code == 200
    other = client.get(f"/api/v1/knowledge/{people['classmate']['user']['id']}", headers=_auth(student))
    assert other.status_code == 403


# --------------------------------------------------------------- /v1 learner ownership


def test_revise_and_plan_check_the_learner_belongs_to_the_caller(world):
    client, people = world
    student, classmate = people["student"], people["classmate"]
    sid = student["user"]["id"]
    api_main._events.append(sid, Interaction(concept_id="concept_x", kind="answer", outcome=1.0))

    # another school's teacher: the audit's exact repro
    assert client.post("/v1/revise", json={"learner": sid},
                       headers=_auth(people["other_teacher"])).status_code == 403
    # a classmate asking for someone else
    assert client.post("/v1/revise", json={"learner": sid},
                       headers=_auth(classmate)).status_code == 403
    # the student for themselves, and their own school's teacher
    mine = client.post("/v1/revise", json={"learner": sid}, headers=_auth(student))
    assert mine.status_code == 200, mine.text
    assert mine.json()["learner"] == sid
    assert client.post("/v1/revise", json={"learner": sid},
                       headers=_auth(people["teacher"])).status_code == 200
    # a learner id that is nobody's is 404, as it was
    assert client.post("/v1/revise", json={"learner": "nobody"},
                       headers=_auth(people["teacher"])).status_code == 404

    # /v1/plan runs the same check before it touches the graph
    assert client.post("/v1/plan", json={"target": "anything", "learner": sid},
                       headers=_auth(people["other_teacher"])).status_code == 403
    assert client.post("/v1/plan", json={"target": "anything", "learner": sid},
                       headers=_auth(classmate)).status_code == 403
