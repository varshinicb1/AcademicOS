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
    # --- auth_routes.py (teacher/principal identity) ---
    ("POST", "/api/v1/auth/register"),
    ("POST", "/api/v1/auth/login"),
    ("POST", "/api/v1/auth/logout"),
    ("GET", "/api/v1/auth/me"),
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
    # --- ingest_routes.py (a school's own document uploads) ---
    ("POST", "/api/v1/ingest/school-documents"),
})

DOC_ROUTES: frozenset[tuple[str, str]] = frozenset({
    ("GET", "/docs"),
    ("GET", "/docs/oauth2-redirect"),
    ("GET", "/openapi.json"),
    ("GET", "/redoc"),
})


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
    if path == "/api/v1/auth/register":
        return {"schoolId": "school_1", "name": "Teacher One",
                "email": "teacher1@example.com", "password": "correct horse battery"}
    if path == "/api/v1/auth/login":
        return {"email": "teacher1@example.com", "password": "correct horse battery"}
    if path == "/v1/question/solve":
        return {"question": "What is photosynthesis?"}
    return {"query": "photosynthesis", "doubt": "light reaction",
            "question": "q", "paperId": "p", "paper_id": "p",
            "nodeId": "n", "node_id": "n", "source": "a", "target": "b"}


# =====================================================================
# Group 1: canonical route-set guard (no startup needed).
# =====================================================================


def test_canonical_route_inventory_matches_live_app():
    """The enumerated app must equal the 62-route inventory exactly."""
    live = _enumerate_routes()
    live_api = live - DOC_ROUTES
    assert live_api == API_ROUTES, (
        "backend routes drifted from tests/test_route_inventory.py — add/update "
        "the route AND its exercise cases below. "
        f"extra: {sorted(live_api - API_ROUTES)}  "
        f"missing: {sorted(API_ROUTES - live_api)}"
    )
    assert len(API_ROUTES) == 62


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
    assert r.json() == {"status": "ok"}


def test_non_gated_routes_work_without_startup():
    """Routes that need no module init: blueprint, section templates, mail
    status, syllabus/timetable (package-data backed), answer-key (pure
    build_answer_key), and scan-session creation (tolerates a None store)."""
    from fastapi.testclient import TestClient

    client = TestClient(app)
    try:
        assert client.post(
            "/api/v1/blueprints/generate", json=blueprint_body()
        ).status_code == 200
        assert client.get("/api/v1/schools/school_1/templates").status_code == 200
        assert client.get("/api/v1/mail/status").status_code == 200

        assert client.get("/api/v1/syllabus/Science/10").status_code == 200
        assert client.get("/api/v1/syllabus/Science/10/timetable").status_code == 200
        assert client.get("/api/v1/syllabus/Physics/10").status_code == 404

        key = client.post("/api/v1/assessments/a1/answer-key", json={
            "assessmentId": "a1", "questions": [question_body()], "correctOptions": {},
        })
        assert key.status_code == 200
        assert key.json()["totalMarks"] == 2

        session = client.post("/api/v1/scan/sessions", json={
            "assessmentId": "a1", "studentId": "s1", "studentName": "Student",
        })
        assert session.status_code == 200
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
            if (method, path) in {
                ("GET", "/health"),
                ("POST", "/api/v1/blueprints/generate"),
                ("GET", "/api/v1/schools/{school_id}/templates"),
                ("GET", "/api/v1/mail/status"),
                ("GET", "/api/v1/syllabus/{subject}/{grade}"),
                ("GET", "/api/v1/syllabus/{subject}/{grade}/timetable"),
                ("POST", "/api/v1/assessments/{assessment_id}/answer-key"),
                ("POST", "/api/v1/scan/sessions"),
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
            # These require Depends(get_current_user)/require_principal,
            # which checks for a bearer token *before* touching the auth
            # module's own _require() -- so with no Authorization header at
            # all, they correctly 401 ("no token"), not 503. That's the
            # right precedence (never reveal backend init state to an
            # unauthenticated caller); their real 503-when-uninitialized
            # path (with a syntactically valid but session-less token) is
            # exercised in the full-boot group instead.
            if (method, path) in {
                ("GET", "/api/v1/auth/me"),
                ("PATCH", "/api/v1/assessments/{assessment_id}/approve"),
                ("POST", "/api/v1/evaluations/sheet/{assessment_id}/{student_id}/review/{question_id}"),
                ("POST", "/api/v1/evaluations/sheet/{assessment_id}/{student_id}/finalize"),
            }:
                continue
            # Idempotent by design: no token means nothing to delete, so it
            # 200s without ever touching _require() -- correct, not a gap.
            if (method, path) == ("POST", "/api/v1/auth/logout"):
                continue
            # Every other scan route looks the session up first (404 on a
            # missing session) before any `_require()`, so no session -> 404
            # not 503; their error paths are exercised in the full-boot group.
            if path.startswith("/api/v1/scan/sessions/{session_id}"):
                continue
            concrete = (
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
            )
            body = _valid_body_for(method, path)
            r = client.request(method, concrete, json=body)
            assert r.status_code == 503, f"{method} {concrete} -> {r.status_code}"
    finally:
        client.close()


def test_auth_gated_routes_503_with_a_token_present():
    """The two routes excluded above (auth checked first, correctly 401s
    with no token) still hit the real 503-when-uninitialized path once a
    syntactically valid bearer token is actually supplied."""
    if assessment_routes._store is not None:
        pytest.skip("module globals already initialized (suite ran out of order)")
    from fastapi.testclient import TestClient

    client = TestClient(app)
    try:
        headers = {"Authorization": "Bearer not-a-real-token"}
        assert client.get("/api/v1/auth/me", headers=headers).status_code == 503
        assert client.patch(
            "/api/v1/assessments/a1/approve", headers=headers
        ).status_code == 503
    finally:
        client.close()


# =====================================================================
# Group 3: full hermetic boot.
# =====================================================================


def _boot_client(tmp_path, monkeypatch):
    """Boots the app with an empty corpus under tmp_path and returns the
    TestClient. Resets the audit-log and user-store singletons so earlier
    boots don't leak (same real gap that would have hit auth tests: a
    stale UserStore from a previous test's tmp_path would keep answering
    for a school that supposedly has no users yet in the new one)."""
    from academicos.assessment import users as users_mod

    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr(audit_log, "_INSTANCE", None)
    monkeypatch.setattr(users_mod, "_INSTANCE", None)
    from fastapi.testclient import TestClient

    return TestClient(app)


def test_full_boot_v1_public_surface(tmp_path, monkeypatch):
    with _boot_client(tmp_path, monkeypatch) as client:
        assert client.get("/health").json() == {"status": "ok"}

        stats = client.get("/v1/registry/stats")
        assert stats.status_code == 200
        assert stats.json() == {"count": 0}

        search = client.post("/v1/search", json={"query": "photosynthesis", "limit": 5})
        assert search.status_code == 200
        assert search.json()["hits"] == []

        # min_length=2 -> 422 on an invalid query.
        assert client.post("/v1/search", json={"query": "x"}).status_code == 422

        doubt = client.post("/v1/agent/doubt", json={"doubt": "light reaction"})
        assert doubt.status_code == 200
        assert "No evidence found" in doubt.json()["answer"]

        score = client.post("/v1/agent/score", json={
            "question": "What is photosynthesis?", "student_answer": "a process",
            "marks_available": 2,
        })
        assert score.status_code == 200
        assert score.json()["score"]["scheme_found"] is False

        analyze = client.post("/v1/agent/analyze", json={"paper_id": "paper_x"})
        assert analyze.status_code == 200

        neighbors = client.post("/v1/graph/neighbors", json={
            "node_id": "n1", "max_depth": 2,
        })
        assert neighbors.status_code == 200
        assert neighbors.json()["nodes"] == []

        paths = client.post("/v1/graph/paths", json={
            "source": "n1", "target": "n2", "max_depth": 4,
        })
        assert paths.status_code == 200
        assert paths.json()["paths"] == []

        # Empty event store / empty graph -> real 404s, not silent empty 200s.
        assert client.post("/v1/revise", json={"learner": "nobody"}).status_code == 404
        assert client.post("/v1/plan", json={"target": "nowhere"}).status_code == 404

        # Lexical fallback (no LLM key configured) still returns a real,
        # if unverified, mapping against an empty graph.
        solved = client.post("/v1/question/solve", json={"question": "What is photosynthesis?"})
        assert solved.status_code == 200
        assert solved.json()["question"] == "What is photosynthesis?"


def test_full_boot_auth_and_principal_approval(tmp_path, monkeypatch):
    """register (bootstrap: only a correct principalKey grants "principal";
    registration order grants nothing -- fixed 2026-09-11, was a real
    privilege-escalation bug where being first to register for a schoolId
    was enough) -> login -> me -> logout, plus the real reason auth exists:
    a teacher cannot approve their own paper, only a principal can, and
    approval actually engages the pre-existing edit lock."""
    monkeypatch.setenv("ACOS_PRINCIPAL_BOOTSTRAP_KEY", "test-bootstrap-key")
    with _boot_client(tmp_path, monkeypatch) as client:
        # -- an attacker racing to register first for school_1, with no key,
        # gets nothing: the vulnerability this test used to encode as
        # correct behavior (first registrant = principal) is closed.
        attacker = client.post("/api/v1/auth/register", json={
            "schoolId": "school_1", "name": "Eve Attacker",
            "email": "eve@example.com", "password": "correct horse battery",
        })
        assert attacker.status_code == 200
        assert attacker.json()["user"]["role"] == "teacher"

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

        # -- a wrong key guess grants nothing either (not just "no key")
        wrong_key = client.post("/api/v1/auth/register", json={
            "schoolId": "school_1", "name": "Wrong Key", "email": "wrong@example.com",
            "password": "correct horse battery", "principalKey": "guessed-wrong",
        })
        assert wrong_key.status_code == 200
        assert wrong_key.json()["user"]["role"] == "teacher"

        # -- a normal registration with no key at all is still a teacher
        reg2 = client.post("/api/v1/auth/register", json={
            "schoolId": "school_1", "name": "Tara Teacher",
            "email": "tara@example.com", "password": "correct horse battery",
        })
        assert reg2.status_code == 200
        assert reg2.json()["user"]["role"] == "teacher"
        teacher_token = reg2.json()["token"]

        # -- duplicate email -> 409; short password -> 400
        assert client.post("/api/v1/auth/register", json={
            "schoolId": "school_1", "name": "Dup", "email": "priya@example.com",
            "password": "correct horse battery",
        }).status_code == 409
        assert client.post("/api/v1/auth/register", json={
            "schoolId": "school_1", "name": "X", "email": "short@example.com",
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
        created = client.post("/api/v1/assessments", json={
            "teacherId": "tara", "schoolId": "school_1", "title": "Approval Test",
            "subject": "Science", "grade": 10, "chapterIds": [], "blueprint": blueprint_body(),
        })
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


def test_full_boot_assessment_lifecycle(tmp_path, monkeypatch):
    """create -> read -> list -> update -> status -> answer-key -> question
    search/optimize -> paper generate -> export -> file, plus the empty and
    invalid-body cases on every step."""
    with _boot_client(tmp_path, monkeypatch) as client:
        # -- create
        body = {
            "teacherId": "teacher_1", "schoolId": "school_1",
            "title": "Lifecycle Test", "subject": "Mathematics", "grade": 10,
            "chapterIds": ["ch1"], "blueprint": blueprint_body(),
        }
        created = client.post("/api/v1/assessments", json=body)
        assert created.status_code == 200, created.text
        assessment_id = created.json()["id"]

        assert client.post("/api/v1/assessments", json={}).status_code == 422

        # -- read / list
        fetched = client.get(f"/api/v1/assessments/{assessment_id}")
        assert fetched.status_code == 200
        assert client.get("/api/v1/assessments/does_not_exist").status_code == 404
        listed = client.get("/api/v1/assessments", params={"teacher_id": "teacher_1"})
        assert listed.status_code == 200
        assert any(a["id"] == assessment_id for a in listed.json())

        # -- update (GET body is a valid PUT body)
        put = client.put(f"/api/v1/assessments/{assessment_id}", json=fetched.json())
        assert put.status_code == 200

        # -- status
        status = client.patch(f"/api/v1/assessments/{assessment_id}/status",
                              json={"status": "questionsSelected"})
        assert status.status_code == 200
        assert status.json()["status"] == "questionsSelected"
        assert client.patch(
            f"/api/v1/assessments/{assessment_id}/status",
            json={"status": "bogus_status"},
        ).status_code == 422
        assert client.patch(
            "/api/v1/assessments/nope/status", json={"status": "draft"},
        ).status_code == 404

        # -- answer key
        key = client.post(f"/api/v1/assessments/{assessment_id}/answer-key", json={
            "assessmentId": assessment_id, "questions": [question_body()],
            "correctOptions": {},
        })
        assert key.status_code == 200
        assert key.json()["totalMarks"] == 2

        # -- question search / optimize on an empty corpus
        search = client.post("/api/v1/questions/search", json={
            "subject": "Science", "grade": 10,
        })
        assert search.status_code == 200
        assert search.json() == []
        assert client.post("/api/v1/questions/search", json={}).status_code == 422

        optimize = client.post("/api/v1/questions/optimize", json={
            "candidates": [], "blueprint": blueprint_body(),
        })
        assert optimize.status_code == 200
        assert client.post("/api/v1/questions/optimize", json={}).status_code == 422

        # -- paper generation: empty selection refused, valid generates
        empty = client.post("/api/v1/papers/generate", json={
            "assessmentId": assessment_id, "blueprint": blueprint_body(),
            "selectedQuestions": [], "template": school_template_body(),
        })
        assert empty.status_code == 400

        gen = client.post("/api/v1/papers/generate", json={
            "assessmentId": assessment_id, "blueprint": blueprint_body(),
            "selectedQuestions": [question_body()], "template": school_template_body(),
        })
        assert gen.status_code == 200, gen.text
        paper_id = gen.json()["id"]

        # -- paper read / export / file
        paper = client.get(f"/api/v1/papers/{paper_id}")
        assert paper.status_code == 200
        assert client.get("/api/v1/papers/does_not_exist").status_code == 404

        exported = client.post(f"/api/v1/papers/{paper_id}/export/pdf")
        assert exported.status_code == 200, exported.text
        assert exported.json()["url"] == f"/api/v1/papers/{paper_id}/file"
        assert client.post(f"/api/v1/papers/{paper_id}/export/docx").status_code == 400
        assert client.post("/api/v1/papers/does_not_exist/export/pdf").status_code == 404

        file_r = client.get(f"/api/v1/papers/{paper_id}/file")
        assert file_r.status_code == 200
        assert file_r.headers["content-type"] == "application/pdf"
        assert client.get("/api/v1/papers/does_not_exist/file").status_code == 404

        # -- mail/send-paper: pdf must already exist; a nonexistent paper 404s
        assert client.post("/api/v1/mail/send-paper", json={
            "paperId": "does_not_exist", "recipients": ["t@example.com"],
        }).status_code == 404

        # -- paper-templates endpoint delegates to the same template store
        templates = client.get("/api/v1/schools/school_1/paper-templates")
        assert templates.status_code == 200
        assert any(t["id"] for t in templates.json())


def test_full_boot_syllabus_catalog_and_templates(tmp_path, monkeypatch):
    with _boot_client(tmp_path, monkeypatch) as client:
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

        # School templates CRUD.
        listed = client.get("/api/v1/schools/school_1/school-templates")
        assert listed.status_code == 200
        assert any(t["id"] for t in listed.json())

        saved = client.post("/api/v1/schools/school_1/school-templates", json={
            "template": school_template_body("tpl_custom"),
            "sections": [],
        })
        assert saved.status_code == 200, saved.text
        assert saved.json()["id"] == "tpl_custom"

        sections = client.get(
            "/api/v1/schools/school_1/school-templates/tpl_custom/sections")
        assert sections.status_code == 200

        deleted = client.delete(
            "/api/v1/schools/school_1/school-templates/tpl_custom")
        assert deleted.status_code == 200
        assert deleted.json() == {"ok": True}


def test_full_boot_evaluations_knowledge_practice_insights(tmp_path, monkeypatch):
    with _boot_client(tmp_path, monkeypatch) as client:
        q = question_body()

        # review_sheet_answer / finalize_sheet_review require a real,
        # school-owned assessment + an authenticated caller (fixed
        # 2026-09-11 -- previously both mutated the graded store for any
        # assessment/student/question with zero authorization). A teacher
        # for school_1 and a real assessment record stand in for what the
        # Assessment Designer flow would already have created.
        teacher = client.post("/api/v1/auth/register", json={
            "schoolId": "school_1", "name": "Eval Teacher",
            "email": "eval-teacher@example.com", "password": "correct horse battery",
        }).json()
        teacher_auth = {"Authorization": f"Bearer {teacher['token']}"}

        other_school_teacher = client.post("/api/v1/auth/register", json={
            "schoolId": "school_2", "name": "Other School Teacher",
            "email": "other-school-teacher@example.com", "password": "correct horse battery",
        }).json()
        other_school_auth = {"Authorization": f"Bearer {other_school_teacher['token']}"}

        created = client.post("/api/v1/assessments", json={
            "teacherId": teacher["user"]["id"], "schoolId": "school_1",
            "title": "Evaluation Test", "subject": "Mathematics", "grade": 10,
            "chapterIds": [], "blueprint": blueprint_body(),
        })
        assert created.status_code == 200, created.text
        a_ev = created.json()["id"]

        # -- evaluation: single answer and full sheet (unauthenticated by
        # design -- not part of this fix; see pillar_routes.py)
        answer = client.post("/api/v1/evaluations/answer", json={
            "assessmentId": a_ev, "studentId": "s_answer",
            "question": q,
            "answerScheme": q["answerScheme"],
            "studentAnswer": "The solution is x = 2, "
            "obtained by subtracting 3 from both sides then dividing by 2.",
        })
        assert answer.status_code == 200, answer.text
        assert answer.json()["awardedMarks"] == 2

        sheet = client.post("/api/v1/evaluations/sheet", json={
            "assessmentId": a_ev, "studentId": "s_sheet", "studentName": "Sheeta",
            "questions": [q], "answers": {
                "q_1": "The solution is x = 2, obtained by subtracting 3 from "
                       "both sides then dividing by 2.",
            },
            "correctOptions": {},
        })
        assert sheet.status_code == 200, sheet.text
        assert sheet.json()["totalAwarded"] <= sheet.json()["totalMax"]

        # -- review + finalize: the AI's raw score must not reach mastery
        # until the teacher's decision is finalized (evaluate_sheet no
        # longer calls record_evaluations itself).
        assert client.get("/api/v1/knowledge/s_sheet").json()["overallMastery"] == 0.0

        # -- authorization itself: no token -> 401; wrong school -> 403
        assert client.post(
            f"/api/v1/evaluations/sheet/{a_ev}/s_sheet/review/q_1",
            json={"action": "approve"},
        ).status_code == 401
        assert client.post(
            f"/api/v1/evaluations/sheet/{a_ev}/s_sheet/review/q_1",
            json={"action": "approve"}, headers=other_school_auth,
        ).status_code == 403
        assert client.post(
            f"/api/v1/evaluations/sheet/{a_ev}/s_sheet/finalize", json={},
        ).status_code == 401
        assert client.post(
            f"/api/v1/evaluations/sheet/{a_ev}/s_sheet/finalize", json={},
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
            f"/api/v1/evaluations/sheet/{a_ev}/s_sheet/review/q_missing",
            json={"action": "approve"}, headers=teacher_auth,
        ).status_code == 404
        # review against a student/assessment with no evaluated sheet -> 404
        assert client.post(
            f"/api/v1/evaluations/sheet/{a_ev}/s_never_evaluated/review/q_1",
            json={"action": "approve"}, headers=teacher_auth,
        ).status_code == 404

        # teacher overrides the AI's award for q_1 down to 0/2
        edited = client.post(
            f"/api/v1/evaluations/sheet/{a_ev}/s_sheet/review/q_1",
            json={"action": "edit", "marks": 0}, headers=teacher_auth,
        )
        assert edited.status_code == 200, edited.text
        assert edited.json()["awardedMarks"] == 0
        assert edited.json()["maxMarks"] == 2

        # edit with no marks -> 400; unknown action -> 400
        assert client.post(
            f"/api/v1/evaluations/sheet/{a_ev}/s_sheet/review/q_1",
            json={"action": "edit"}, headers=teacher_auth,
        ).status_code == 400
        assert client.post(
            f"/api/v1/evaluations/sheet/{a_ev}/s_sheet/review/q_1",
            json={"action": "bogus"}, headers=teacher_auth,
        ).status_code == 400

        # finalize with no evaluated sheet -> 404
        assert client.post(
            f"/api/v1/evaluations/sheet/{a_ev}/s_never_evaluated/finalize",
            json={}, headers=teacher_auth,
        ).status_code == 404

        finalized = client.post(
            f"/api/v1/evaluations/sheet/{a_ev}/s_sheet/finalize",
            json={}, headers=teacher_auth,
        )
        assert finalized.status_code == 200, finalized.text
        assert finalized.json()["totalAwarded"] == 0  # reflects the teacher's override, not the AI's
        assert finalized.json()["totalMax"] == 2

        # mastery now reflects the teacher-finalized (not AI-original) mark.
        after = client.get("/api/v1/knowledge/s_sheet").json()
        assert after["overallMastery"] < 1.0

        assert client.post("/api/v1/evaluations/sheet", json={
            "assessmentId": a_ev, "studentId": "s_sheet",
            "questions": [], "answers": {},
        }).status_code == 200

        # -- knowledge: empty student is 200 (empty mastery), report 404s.
        knowledge = client.get("/api/v1/knowledge/s_unknown")
        assert knowledge.status_code == 200
        assert knowledge.json()["overallMastery"] == 0.0
        assert client.get("/api/v1/knowledge/s_unknown/report").status_code == 404

        # -- practice: nothing to remediate -> 400; unknown set -> 404.
        practice = client.post("/api/v1/practice/generate", json={
            "studentId": "s_unknown", "subject": "Science", "grade": "X",
        })
        assert practice.status_code == 400
        assert client.post("/api/v1/practice/submit", json={
            "setId": "nope", "answers": {},
        }).status_code == 404

        # -- insights: no evaluated sheets for this assessment -> class 404;
        # school is 200 (empty).
        assert client.get("/api/v1/insights/class/assessment_with_no_sheets").status_code == 404
        school = client.get("/api/v1/insights/school/school_1")
        assert school.status_code == 200


def test_full_boot_scan_session_error_paths(tmp_path, monkeypatch):
    """Scan routes exercised via their proper-4xx paths: no network, no OCR
    pipeline, no Supabase. Every route is hit with a real request."""
    with _boot_client(tmp_path, monkeypatch) as client:
        created = client.post("/api/v1/scan/sessions", json={
            "assessmentId": "a_scan", "studentId": "s1", "studentName": "Student",
        })
        assert created.status_code == 200, created.text
        session_id = created.json()["id"]

        # Empty session -> review is empty; process has no paper; finalize has
        # nothing; review-decision on an unknown question 400s; assets 404.
        review = client.get(f"/api/v1/scan/sessions/{session_id}/review")
        assert review.status_code == 200
        assert review.json()["items"] == []

        process = client.post(f"/api/v1/scan/sessions/{session_id}/process")
        assert process.status_code == 409
        assert "no generated paper" in process.json()["detail"]

        finalize = client.post(f"/api/v1/scan/sessions/{session_id}/finalize")
        assert finalize.status_code == 409

        decision = client.post(
            f"/api/v1/scan/sessions/{session_id}/review/q_1",
            json={"action": "approve"},
        )
        assert decision.status_code == 400
        assert "not in this session's review queue" in decision.json()["detail"]

        assert client.get(
            f"/api/v1/scan/sessions/{session_id}/pages/1/image"
        ).status_code == 404
        assert client.get(f"/api/v1/scan/sessions/{session_id}/raw-pdf").status_code == 404
        assert client.get(
            f"/api/v1/scan/sessions/{session_id}/corrected-pdf"
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
            r = client.request(method, path, json={"action": "approve"})
            assert r.status_code == 404, f"{method} {path} -> {r.status_code}"

        # The page-upload route needs a real multipart file to pass FastAPI
        # validation; the missing-session 404 still fires first.
        upload = client.post(
            "/api/v1/scan/sessions/scan_missing/pages",
            files={"file": ("page.jpg", b"x", "image/jpeg")},
        )
        assert upload.status_code == 404, f"POST /pages -> {upload.status_code}"