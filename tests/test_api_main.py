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
