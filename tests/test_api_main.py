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

from datetime import datetime, timedelta, timezone

import pytest
import requests
from fastapi.testclient import TestClient

from academicos.api.main import app
from academicos.assessment import routes as assessment_routes


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
    """A valid CreateAssessmentRequest body (camelCase)."""
    return {
        "teacherId": "teacher_1",
        "schoolId": "school_1",
        "title": "Unit Test 1",
        "subject": "Mathematics",
        "grade": 10,
        "chapterIds": ["ch1"],
        "blueprint": blueprint_body(),
    }


# =====================================================================
# Group 1: startup-free assertions (must run before any `with TestClient`).
# =====================================================================


def test_health_without_startup():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


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


def test_blueprint_generate_without_startup():
    client = TestClient(app)
    body = blueprint_body(total_marks=60, duration_minutes=90)
    r = client.post("/api/v1/blueprints/generate", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["totalMarks"] == 60
    assert data["durationMinutes"] == 90
    assert data["difficulty"]["hard"] == 0.3
    assert data["bloom"]["create"] == 0.1
    assert data["sections"], "expected default sections to be generated"


def test_blueprint_generate_invalid_body_422():
    client = TestClient(app)
    bad = blueprint_body()
    del bad["bloom"]
    assert client.post("/api/v1/blueprints/generate", json=bad).status_code == 422


def test_school_templates_and_mail_status_without_startup():
    client = TestClient(app)
    templates = client.get("/api/v1/schools/school_1/templates")
    assert templates.status_code == 200
    sections = templates.json()
    assert isinstance(sections, list) and sections
    assert "label" in sections[0]

    mail = client.get("/api/v1/mail/status")
    assert mail.status_code == 200
    body = mail.json()
    assert "backends" in body
    assert "anyConfigured" in body


def test_runtime_gated_routes_return_503_before_startup():
    """Mounted but not initialized -> 503, never 404."""
    if assessment_routes._store is not None:
        pytest.skip("module globals already initialized (suite ran out of order)")
    client = TestClient(app)
    assert client.get("/api/v1/assessments").status_code == 503
    assert client.get("/api/v1/schools/school_1/school-templates").status_code == 503
    r = client.post("/v1/search", json={"query": "photosynthesis", "limit": 5})
    assert r.status_code == 503
    assert client.post("/v1/revise", json={"learner": "alice"}).status_code == 503
    assert client.post("/v1/plan", json={"target": "Photosynthesis"}).status_code == 503
    assert client.post("/v1/question/solve", json={"question": "What is photosynthesis?"}).status_code == 503


def test_unknown_route_404_without_startup():
    client = TestClient(app)
    r = client.get("/api/v1/definitely-not-a-route")
    assert r.status_code == 404


# =====================================================================
# Group 2: full hermetic boot (startup event runs, stores land in tmp).
# =====================================================================


def test_full_boot_health_registry_stats_and_empty_search(tmp_path, monkeypatch):
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}

        stats = client.get("/v1/registry/stats")
        assert stats.status_code == 200
        assert stats.json() == {"count": 0}

        # Empty index -> bm25/tfidf both return [] and the graph is empty, so
        # HybridRetriever.search yields no hits (verified in hybrid.py).
        search = client.post("/v1/search", json={"query": "photosynthesis", "limit": 5})
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
        created = client.post("/api/v1/assessments", json=create_assessment_body())
        assert created.status_code == 200
        assessment_id = created.json()["id"]
        assert created.json()["status"] == "blueprintReady"

        fetched = client.get(f"/api/v1/assessments/{assessment_id}")
        assert fetched.status_code == 200
        assert fetched.json()["id"] == assessment_id
        assert fetched.json()["scheduledAt"] is None

        # GET returns camelCase JSON that doubles as a valid PUT body.
        body = fetched.json()
        body["scheduledAt"] = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()

        updated = client.put(f"/api/v1/assessments/{assessment_id}", json=body)
        assert updated.status_code == 200
        assert updated.json()["scheduledAt"] is not None

        # The save must NOT have been blocked by the (raised) calendar sync.
        again = client.get(f"/api/v1/assessments/{assessment_id}")
        assert again.status_code == 200
        assert again.json()["scheduledAt"] is not None
        assert datetime.fromisoformat(again.json()["scheduledAt"]) == datetime.fromisoformat(
            body["scheduledAt"]
        )

        # Persisted through the AssessmentStore -> listable by teacher.
        listed = client.get("/api/v1/assessments", params={"teacher_id": "teacher_1"})
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

    # Seed a learner with a couple of answered interactions so revise() has
    # a non-empty ConceptState to schedule against.
    estore = EventStore(cfg.events_db)
    estore.append("alice", Interaction(concept_id=prereq.id, kind="answer", outcome=1.0))
    estore.append("alice", Interaction(concept_id=prereq.id, kind="answer", outcome=0.0))

    with TestClient(app) as client:
        # revise(): learner exists -> 200 with a real FSRS-backed plan.
        r = client.post("/v1/revise", json={"learner": "alice"})
        assert r.status_code == 200
        body = r.json()
        assert body["learner"] == "alice"
        assert "totals" in body and "confident" in body

        # revise(): unknown learner -> 404, not a silent empty plan.
        r404 = client.post("/v1/revise", json={"learner": "nobody"})
        assert r404.status_code == 404

        # plan(): walks the seeded prereq chain in order.
        p = client.post("/v1/plan", json={"target": "Photosynthesis", "capacity_minutes": 60})
        assert p.status_code == 200
        pbody = p.json()
        assert pbody["target"] == "Photosynthesis"
        assert [i["label"] for i in pbody["session"]] == ["Cell Structure", "Photosynthesis"]

        # plan(): unknown target -> 404, not an empty 200.
        p404 = client.post("/v1/plan", json={"target": "Not A Real Concept"})
        assert p404.status_code == 404

        # question/solve(): no LLM key configured in this hermetic test -> the
        # lexical fallback still returns a real (if unverified) mapping.
        q = client.post("/v1/question/solve",
                        json={"question": "Explain photosynthesis in plants"})
        assert q.status_code == 200
        qbody = q.json()
        assert qbody["question"] == "Explain photosynthesis in plants"
        assert "method" in qbody and "concepts" in qbody
