"""Hermetic end-to-end tests for the FastAPI app assembly in
`src/academicos/api/main.py` (installed with the `[api]` extra).

Two ordered groups:

1. Startup-free: a bare `TestClient(app)` — created WITHOUT the context
   manager, so the `@app.on_event("startup")` handler never runs — proves the
   app assembles, the three assessment routers are really mounted (openapi +
   real requests), and runtime-gated routes are mounted but return 503.
2. Full boot: `ACOS_DATA_ROOT` is pointed at a pytest `tmp_path` BEFORE
   entering `with TestClient(app)`, so the startup event builds every store
   (ChunkIndex, GraphStore, SourceRegistry, AssessmentStore, PaperStore,
   KnowledgeStore, TemplateStore, GradedStore, PracticeStore, scan workdir)
   under tmp. The only outbound call in the app (Composio calendar sync) is
   mocked to raise, proving a sync failure never blocks the assessment save.

Never starts uvicorn; never binds a port (TestClient is fully in-process).

Order matters: the startup-free 503 assertions must run before any test that
enters the startup context manager, because startup permanently sets module
globals (`assessment/routes.py` -> `_store`, `pillar_routes.py` -> `_cfg`,
`api/main.py` -> `_retriever`, ...).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
import requests
from fastapi.testclient import TestClient

from academicos.api.main import app
from academicos.assessment import routes as assessment_routes

from _auth_helpers import invite_code


# ---------------------------------------------------------------- helpers


def blueprint_body(total_marks: int = 80, duration_minutes: int = 180) -> dict:
    """A valid BlueprintRequest body — camelCase on the wire, all required
    fields present so FastAPI does not 422."""
    return {
        "totalMarks": total_marks,
        "durationMinutes": duration_minutes,
        "difficulty": {"easy": 0.3, "medium": 0.4, "hard": 0.3},
        "bloom": {
            "remember": 0.2,
            "understand": 0.2,
            "apply": 0.2,
            "analyze": 0.2,
            "evaluate": 0.1,
            "create": 0.1,
        },
        "chapterWeights": {"weights": {}},
        "competencyWeights": {"weights": {}},
    }


def create_assessment_body() -> dict:
    """A valid CreateAssessmentRequest body (camelCase). teacherId/schoolId
    are ignored by the real endpoint now (fixed 2026-09-15 -- they used to be
    trusted verbatim from the body, a full impersonation hole) in favor of
    the authenticated caller's own identity; kept here only so older callers
    of this helper that still pass the body through don't need to change."""
    return {
        "teacherId": "teacher_1",
        "schoolId": "school_1",
        "title": "Unit Test 1",
        "subject": "Mathematics",
        "grade": 10,
        "chapterIds": ["ch1"],
        "blueprint": blueprint_body(),
    }


def register_and_login(client: TestClient, school_id: str = "school_1",
                       email: str | None = None) -> tuple[dict, dict[str, str]]:
    """Registers a fresh teacher for `school_id` and returns (user_json,
    auth_headers) -- the standard way every full-boot test below gets a real
    identity now that most routes require Depends(get_current_user).

    The email defaults to a unique value rather than a fixed one: the
    UserStore is a process-wide singleton (see users.get_user_store), so it
    survives between tests even though each test gets its own tmp_path. A
    fixed default email made the second test to run collide with the first
    and get a 409 EmailAlreadyRegistered."""
    if email is None:
        email = f"teacher-{uuid.uuid4().hex[:10]}@example.com"
    r = client.post("/api/v1/auth/register", json={
        "inviteCode": invite_code(school_id), "name": "Test Teacher", "email": email,
        "password": "correct horse battery",
    })
    assert r.status_code == 200, r.text
    body = r.json()
    return body["user"], {"Authorization": f"Bearer {body['token']}"}


# =====================================================================
# Group 1: startup-free assertions (must run before any `with TestClient`).
# =====================================================================


def test_health_without_startup():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok" and set(r.json()) == {"status", "commit", "builtAt"}


def test_docs_and_openapi_without_startup():
    client = TestClient(app)
    assert client.get("/docs").status_code == 200

    spec = client.get("/openapi.json")
    assert spec.status_code == 200
    paths = spec.json()["paths"]
    # Proves all three routers are actually mounted under /api/v1.
    for expected in (
        "/api/v1/blueprints/generate",
        "/api/v1/mail/status",
        "/api/v1/assessments",
        "/api/v1/schools/{school_id}/school-templates",
        "/api/v1/scan/sessions",
    ):
        assert expected in paths, f"openapi missing expected path {expected}"


def test_blueprint_generate_requires_auth_without_startup():
    """POST /api/v1/blueprints/generate now requires an authenticated caller
    (2026-09-16): it is a pure-compute endpoint, so leaving it open let any
    anonymous visitor burn CPU. Auth resolves before module-init state, so
    with no token this is 401 even before startup -- asserted here instead of
    the previous unauthenticated 200. The 200 + field/422 checks moved to
    test_blueprint_generate_full_boot below, where a real token can be minted
    (registering needs the startup event, so it cannot live in this group)."""
    client = TestClient(app)
    body = blueprint_body(total_marks=60, duration_minutes=90)
    assert client.post("/api/v1/blueprints/generate", json=body).status_code == 401


def test_school_templates_and_mail_status_without_startup():
    """GET /schools/{school_id}/templates now requires a real caller (fixed
    2026-09-15 -- previously served to anyone, no auth at all); auth is
    checked before any module-init state, so this 401s with no token even
    before startup, same convention as every other auth-gated route.
    /mail/status describes the deployment, so it 401s without a token too
    (NFR-2, 2026-10-01)."""
    client = TestClient(app)
    templates = client.get("/api/v1/schools/school_1/templates")
    assert templates.status_code == 401

    assert client.get("/api/v1/mail/status").status_code == 401


def test_docs_are_off_in_production(monkeypatch):
    """NFR-2: /docs, /redoc and /openapi.json would hand anyone the whole
    route map on the live release. Off there; on everywhere else."""
    from academicos.api import main

    monkeypatch.delenv("ACOS_ENV", raising=False)
    monkeypatch.delenv("ACOS_POSTGRES_HOST", raising=False)
    assert main._doc_urls() == {}
    monkeypatch.setenv("ACOS_ENV", "production")
    assert main._doc_urls() == {"docs_url": None, "redoc_url": None, "openapi_url": None}
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    live = FastAPI(**main._doc_urls())
    with TestClient(live) as c:
        assert [c.get(p).status_code for p in ("/docs", "/redoc", "/openapi.json")] == [404, 404, 404]
    assert live.openapi()["info"], "the contract export still works with the routes off"


def test_runtime_gated_routes_return_503_before_startup():
    """Mounted but not initialized -> 503, never 404 -- for routes that
    aren't also auth-gated. GET /assessments and /schools/.../school-templates
    are Depends(get_current_user)-gated (fixed 2026-09-15), so with no token
    at all they correctly 401 before ever reaching the 503 init check.

    The /v1/* pillar surface joined them on 2026-09-16: corpus search, the
    agent endpoints, revise/plan/question-solve, and the graph reads were all
    reachable with no token -- compute- and LLM-backed endpoints open to the
    internet. They are now 401 without a token, so the "503 when uninitialized"
    path for those is asserted with a token in the full-boot tests below
    instead. /health and /health/storage remain genuinely open on purpose."""
    if assessment_routes._store is not None:
        pytest.skip("module globals already initialized (suite ran out of order)")
    client = TestClient(app)
    assert client.get("/api/v1/assessments").status_code == 401
    assert client.get("/api/v1/schools/school_1/school-templates").status_code == 401
    assert client.post("/v1/search", json={"query": "photosynthesis", "limit": 5}).status_code == 401
    assert client.post("/v1/revise", json={"learner": "alice"}).status_code == 401
    assert client.post("/v1/plan", json={"target": "Photosynthesis"}).status_code == 401
    assert client.post("/v1/question/solve", json={"question": "What is photosynthesis?"}).status_code == 401
    assert client.get("/v1/registry/stats").status_code == 401


def test_unknown_route_404_without_startup():
    client = TestClient(app)
    r = client.get("/api/v1/definitely-not-a-route")
    assert r.status_code == 404


# =====================================================================
# Group 2: full hermetic boot (startup event runs, stores land in tmp).
# =====================================================================


def test_blueprint_generate_full_boot(tmp_path, monkeypatch):
    """The authenticated happy path for /api/v1/blueprints/generate, plus the
    422 body-validation path -- both need a real token, so they live in the
    full-boot group (see test_blueprint_generate_requires_auth_without_startup
    for the 401 half)."""
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    with TestClient(app) as client:
        _, auth = register_and_login(client)

        r = client.post("/api/v1/blueprints/generate",
                        json=blueprint_body(total_marks=60, duration_minutes=90),
                        headers=auth)
        assert r.status_code == 200
        data = r.json()
        assert data["totalMarks"] == 60
        assert data["durationMinutes"] == 90
        assert data["difficulty"]["hard"] == 0.3
        assert data["bloom"]["create"] == 0.1
        assert data["sections"], "expected default sections to be generated"

        bad = blueprint_body()
        del bad["bloom"]
        assert client.post("/api/v1/blueprints/generate", json=bad,
                           headers=auth).status_code == 422


def test_full_boot_health_registry_stats_and_empty_search(tmp_path, monkeypatch):
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    with TestClient(app) as client:
        assert client.get("/health").json()["status"] == "ok"
        _, auth = register_and_login(client)

        stats = client.get("/v1/registry/stats", headers=auth)
        assert stats.status_code == 200
        assert stats.json() == {"count": 0}

        # Empty index -> bm25/tfidf both return [] and the graph is empty, so
        # HybridRetriever.search yields no hits (verified in hybrid.py).
        search = client.post("/v1/search", json={"query": "photosynthesis", "limit": 5},
                             headers=auth)
        assert search.status_code == 200
        assert search.json()["hits"] == []


def test_assessment_roundtrip_calendar_sync_failure_does_not_block_save(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("COMPOSIO_API_KEY", "test-key-123")
    monkeypatch.setenv("COMPOSIO_CALENDAR_CONNECTED_ACCOUNT_ID", "ca_test_account")
    monkeypatch.setenv("COMPOSIO_CALENDAR_USER_ID", "user_42")

    def raising_post(*args, **kwargs):
        raise requests.exceptions.ConnectionError("no network in tests")

    # The real requests.post call lives in composio_provider.py (the
    # ActionProvider composio_calendar.py delegates to).
    monkeypatch.setattr(
        "academicos.integrations.composio_provider.requests.post", raising_post
    )

    with TestClient(app) as client:
        teacher, auth = register_and_login(client)
        created = client.post("/api/v1/assessments", json=create_assessment_body(), headers=auth)
        assert created.status_code == 200
        assessment_id = created.json()["id"]
        assert created.json()["status"] == "blueprintReady"
        # teacherId/schoolId in the body are ignored now -- the real owner is
        # whoever authenticated, not whatever the request claimed.
        assert created.json()["teacherId"] == teacher["id"]
        assert created.json()["schoolId"] == teacher["schoolId"]

        fetched = client.get(f"/api/v1/assessments/{assessment_id}", headers=auth)
        assert fetched.status_code == 200
        assert fetched.json()["id"] == assessment_id
        assert fetched.json()["scheduledAt"] is None

        # GET returns camelCase JSON that doubles as a valid PUT body.
        body = fetched.json()
        body["scheduledAt"] = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()

        updated = client.put(f"/api/v1/assessments/{assessment_id}", json=body, headers=auth)
        assert updated.status_code == 200
        assert updated.json()["scheduledAt"] is not None

        # The save must NOT have been blocked by the (raised) calendar sync.
        again = client.get(f"/api/v1/assessments/{assessment_id}", headers=auth)
        assert again.status_code == 200
        assert again.json()["scheduledAt"] is not None
        assert datetime.fromisoformat(again.json()["scheduledAt"]) == datetime.fromisoformat(
            body["scheduledAt"]
        )

        # Persisted through the AssessmentStore -> listable by teacher.
        listed = client.get("/api/v1/assessments", params={"teacher_id": teacher["id"]}, headers=auth)
        assert listed.status_code == 200
        assert any(a["id"] == assessment_id for a in listed.json())


def test_revise_plan_question_solve_endpoints(tmp_path, monkeypatch):
    """P5.2 — revise/plan/question-solve wrap the already-tested algorithm
    modules (forgetting.RevisionScheduler, study_planner.StudyPlanner,
    qmap.QuestionMapper) over real seeded graph + event stores."""
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))

    from academicos.algorithms.learner_model import Interaction
    from academicos.config import Config
    from academicos.graph.schema import new_edge, new_node
    from academicos.graph.store import GraphStore
    from academicos.models.enums import EdgeType, NodeType
    from academicos.storage.event_store import EventStore

    cfg = Config.load()

    # Seed a two-node prereq chain the study planner can walk.
    gstore = GraphStore(cfg.graph_db)
    prereq = new_node(NodeType.CONCEPT, "Cell Structure",
                      attributes={"difficulty": 2.0, "learning_hours": 1.0,
                                  "bloom": "understand"})
    target = new_node(NodeType.CONCEPT, "Photosynthesis",
                      attributes={"difficulty": 3.0, "learning_hours": 1.0,
                                  "bloom": "understand"})
    gstore.upsert_node(prereq)
    gstore.upsert_node(target)
    gstore.upsert_edge(new_edge(
        EdgeType.PREREQUISITE_OF, prereq.id, target.id,
        weight=0.9, attributes={"confidence": 0.9, "score": 0.7,
                                "recommended_spacing_days": 2}))

    with TestClient(app) as client:
        _, auth = register_and_login(client)
        # The learner must be a real student of the caller's school: since
        # 2026-09-21 /v1/revise and /v1/plan refuse a learner id the caller
        # has no claim to (tests/test_role_gates.py). Seed that student with
        # a couple of answered interactions so revise() has a non-empty
        # ConceptState to schedule against.
        alice = client.post("/api/v1/auth/register", json={
            "inviteCode": invite_code("school_1", "student"), "name": "Alice",
            "email": f"alice-{uuid.uuid4().hex[:8]}@example.com",
            "password": "correct horse battery",
        })
        assert alice.status_code == 200, alice.text
        alice_id = alice.json()["user"]["id"]
        estore = EventStore(cfg.events_db)
        estore.append(alice_id, Interaction(concept_id=prereq.id, kind="answer", outcome=1.0))
        estore.append(alice_id, Interaction(concept_id=prereq.id, kind="answer", outcome=0.0))

        # revise(): learner exists -> 200 with a real FSRS-backed plan.
        r = client.post("/v1/revise", json={"learner": alice_id}, headers=auth)
        assert r.status_code == 200
        body = r.json()
        assert body["learner"] == alice_id
        assert "totals" in body and "confident" in body

        # revise(): unknown learner -> 404, not a silent empty plan.
        r404 = client.post("/v1/revise", json={"learner": "nobody"}, headers=auth)
        assert r404.status_code == 404

        # plan(): walks the seeded prereq chain in order.
        p = client.post("/v1/plan", json={"target": "Photosynthesis", "capacity_minutes": 60},
                        headers=auth)
        assert p.status_code == 200
        pbody = p.json()
        assert pbody["target"] == "Photosynthesis"
        assert [i["label"] for i in pbody["session"]] == ["Cell Structure", "Photosynthesis"]

        # plan(): unknown target -> 404, not an empty 200.
        p404 = client.post("/v1/plan", json={"target": "Not A Real Concept"}, headers=auth)
        assert p404.status_code == 404

        # question/solve(): no LLM key configured in this hermetic test -> the
        # lexical fallback still returns a real (if unverified) mapping.
        q = client.post("/v1/question/solve",
                        json={"question": "Explain photosynthesis in plants"},
                        headers=auth)
        assert q.status_code == 200
        qbody = q.json()
        assert qbody["question"] == "Explain photosynthesis in plants"
        assert "method" in qbody and "concepts" in qbody
