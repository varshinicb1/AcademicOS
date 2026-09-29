"""Error tracking (REQUIREMENTS NFR-7).

An unhandled exception was a bare 500 and a log line nobody grouped, and an
error in the web or phone app was seen only by the person holding it. Now
both are grouped by fingerprint, counted, and written as Cloud Error
Reporting events (which group and alert on Cloud Run), with nothing personal
kept: no body, no query, the route's template instead of its path, no user
id, and emails and long numbers masked.

The server side is tested on a small app of its own, so no test route leaks
into the real app's route inventory.
"""
from __future__ import annotations

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from academicos.api import error_tracking as et


@pytest.fixture(autouse=True)
def _fresh():
    et.ERRORS.reset()
    yield
    et.ERRORS.reset()


def _events(captured: str) -> list[dict]:
    out = []
    for line in captured.splitlines():
        try:
            doc = json.loads(line)
        except ValueError:
            continue
        if isinstance(doc, dict) and doc.get("@type", "").endswith("ReportedErrorEvent"):
            out.append(doc)
    return out


def _app() -> TestClient:
    app = FastAPI()
    et.install(app)

    @app.get("/api/v1/students/{student_id}/marks")
    def boom(student_id: str):
        raise RuntimeError(f"no marks row for student {student_id} (asha@example.com, roll 20260042)")

    return TestClient(app, raise_server_exceptions=False)


def test_scrub_masks_what_could_name_a_person():
    assert et.scrub("mail asha.k@example.com or call 9876543210, class 10", 200) == \
        "mail [email] or call [number], class 10"
    assert len(et.scrub("x" * 500, 40)) == 40


def test_an_unhandled_exception_is_a_500_with_a_reference_grouped_and_reported(capsys):
    client = _app()
    first = client.get("/api/v1/students/stu_123456789/marks?token=secret")
    assert first.status_code == 500
    body = first.json()
    assert "asha" not in json.dumps(body) and "RuntimeError" not in json.dumps(body), \
        "the exception's text never reaches the caller"
    assert len(body["errorRef"]) == 12
    client.get("/api/v1/students/stu_2/marks")

    [group] = et.ERRORS.groups()
    assert (group.count, group.source, group.kind) == (2, "server", "RuntimeError")
    assert group.fingerprint == body["errorRef"], "one place in the code, one group"
    assert group.route == "GET /api/v1/students/{student_id}/marks", "the template, never an id"
    assert "asha@example.com" not in group.message and "20260042" not in group.message

    events = _events(capsys.readouterr().err)
    assert len(events) == 2
    ev = events[0]
    assert ev["severity"] == "ERROR" and ev["serviceContext"]["service"] == "academicos-backend"
    assert ev["context"]["httpRequest"] == {"method": "GET", "url": "/api/v1/students/{student_id}/marks",
                                           "responseStatusCode": 500}
    assert "Traceback" in ev["message"] and "boom" in ev["message"]
    assert "secret" not in json.dumps(ev) and "asha@example.com" not in json.dumps(ev)


def test_the_apps_report_what_they_caught_scrubbed_and_limited(capsys):
    client = _app()
    report = {"source": "web", "message": "Null check operator used on a null value for asha@example.com",
              "stack": "#0 _HomeworkPageState.build (package:academicos/presentation/x.dart:12)\n#1 ...",
              "route": "/school/my-homework", "appVersion": "c46681b"}
    r = client.post("/api/v1/client-errors", json=report)
    assert r.status_code == 200 and r.json()["recorded"] is True
    again = client.post("/api/v1/client-errors", json=report)
    assert again.json()["errorRef"] == r.json()["errorRef"]
    [group] = et.ERRORS.groups()
    assert (group.source, group.count, group.route) == ("web", 2, "/school/my-homework")
    assert "[email]" in group.message
    [ev, _] = _events(capsys.readouterr().err)
    assert ev["serviceContext"] == {"service": "academicos-web", "version": "c46681b"}

    assert client.post("/api/v1/client-errors", json={**report, "userId": "u1"}).status_code == 422
    assert client.post("/api/v1/client-errors", json={**report, "source": "desktop"}).status_code == 422
    for _ in range(et.CLIENT_PER_MINUTE):
        client.post("/api/v1/client-errors", json=report)
    assert client.post("/api/v1/client-errors", json=report).json()["recorded"] is False
    assert et.ERRORS.dropped_client >= 1


def test_the_operators_list_needs_the_key_and_health_gives_counts_only(monkeypatch):
    client = _app()
    client.get("/api/v1/students/stu_1/marks")
    monkeypatch.delenv("ACOS_OPS_KEY", raising=False)
    assert client.get("/api/v1/ops/errors").status_code == 404, "no key configured: no route"
    monkeypatch.setenv("ACOS_OPS_KEY", "k" * 32)
    assert client.get("/api/v1/ops/errors", headers={"X-Ops-Key": "wrong"}).status_code == 401
    [row] = client.get("/api/v1/ops/errors", headers={"X-Ops-Key": "k" * 32}).json()
    assert (row["count"], row["route"], row["schools"]) == (1, "GET /api/v1/students/{student_id}/marks", 0)
    health = client.get("/health/errors").json()
    assert (health["serverErrors"], health["clientErrors"], health["groups"]) == (1, 0, 1)
    assert "message" not in json.dumps(health)


def test_the_real_app_has_the_last_handler_installed():
    from academicos.api.main import app
    assert app.exception_handlers.get(Exception) is et._on_unhandled
