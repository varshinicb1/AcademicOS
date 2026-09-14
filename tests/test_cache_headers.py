"""Cache-Control headers for the cacheable pillar GET endpoints.

The four cacheable, rarely-changing endpoints get `public, max-age=300`:
`GET /api/v1/catalog`, `GET /api/v1/catalog/{subject}/{grade}/chapters`,
`GET /api/v1/syllabus/{subject}/{grade}`, and
`GET /api/v1/syllabus/{subject}/{grade}/timetable`.

Per-user / frequently-mutating endpoints must stay header-less, and a 404
must never carry the header (a 404 must not be cached).

Hermetic: `ACOS_DATA_ROOT` is pointed at a pytest `tmp_path` BEFORE entering
`with TestClient(app)`, so the startup event builds every store under tmp
(identical discipline to `tests/test_api_main.py`). All assertions run inside
the context; there are no startup-free assertions here.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from academicos.api.main import app

CACHEABLE_HEADER = "public, max-age=300"


def test_catalog_and_chapters_have_cache_control(tmp_path, monkeypatch):
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    with TestClient(app) as client:
        catalog = client.get("/api/v1/catalog")
        assert catalog.status_code == 200
        assert catalog.headers.get("Cache-Control") == CACHEABLE_HEADER

        # Science/10 genuinely returns 200 under tmp: load_syllabus("Science", 10)
        # yields a real doc (5 units / 80 marks), so the chapter breakdown is
        # built from the official syllabus even with an empty question pool.
        chapters = client.get("/api/v1/catalog/Science/10/chapters")
        assert chapters.status_code == 200
        assert chapters.headers.get("Cache-Control") == CACHEABLE_HEADER


def test_syllabus_and_timetable_have_cache_control(tmp_path, monkeypatch):
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    with TestClient(app) as client:
        syllabus = client.get("/api/v1/syllabus/Science/10")
        assert syllabus.status_code == 200
        assert syllabus.headers.get("Cache-Control") == CACHEABLE_HEADER

        timetable = client.get("/api/v1/syllabus/Science/10/timetable")
        assert timetable.status_code == 200
        assert timetable.headers.get("Cache-Control") == CACHEABLE_HEADER


def test_404_is_never_cached(tmp_path, monkeypatch):
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    with TestClient(app) as client:
        # load_syllabus("Physics", 10) is None -> handler raises 404 -> no header.
        missing = client.get("/api/v1/syllabus/Physics/10")
        assert missing.status_code == 404
        assert "Cache-Control" not in missing.headers


def test_mutable_and_per_user_endpoints_stay_header_less(tmp_path, monkeypatch):
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    with TestClient(app) as client:
        # Both endpoints now require a real caller (fixed 2026-09-15 -- see
        # test_api_main.py/test_route_inventory.py for the security fix these
        # auth headers are a side effect of); a registered student stands in
        # for a real student_id since require_school_owns_student 404s on an
        # id with no matching user.
        teacher = client.post("/api/v1/auth/register", json={
            "schoolId": "school_1", "name": "T", "email": "cache-teacher@example.com",
            "password": "correct horse battery",
        }).json()
        auth = {"Authorization": f"Bearer {teacher['token']}"}
        student = client.post("/api/v1/auth/register", json={
            "schoolId": "school_1", "name": "S", "email": "cache-student@example.com",
            "password": "correct horse battery", "role": "student",
        }).json()["user"]

        assessments = client.get("/api/v1/assessments", headers=auth)
        assert assessments.status_code == 200
        assert "Cache-Control" not in assessments.headers

        knowledge = client.get(f"/api/v1/knowledge/{student['id']}", headers=auth)
        assert knowledge.status_code == 200
        assert "Cache-Control" not in knowledge.headers