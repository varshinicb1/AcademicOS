"""Request ids and structured logs (R-A4, REQUIREMENTS NFR-7).

A log line could not be tied to the request that wrote it or to the school it
served, and uvicorn's access line carried the raw path and query string. These
hold:

  * a safe `X-Request-ID` from the caller comes back unchanged; a missing one
    is generated; a malicious one (a forged log line, an overlong value) is
    replaced, never echoed;
  * on Cloud Run each log record is one JSON line with Cloud Logging's fields,
    including the trace when Google's front end sent one;
  * the access line names the route's template, the status, the duration, the
    request id and the signed-in school, and carries no query string, token,
    email or id from the path.
"""
from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from academicos.api import request_logging as rl  # noqa: E402
from test_assessment_routes_auth import _boot_client, _register  # noqa: E402

PRINCIPAL_KEY = "test-bootstrap-key"
TRACE = "105445aa7843bc8bf206b12000100000"


class _Capture(logging.Handler):
    """Formats at emit time, as the real handler does, so the request's context is seen."""

    def __init__(self) -> None:
        super().__init__()
        self.setFormatter(rl.JsonFormatter())
        self.lines: list[dict] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.lines.append(json.loads(self.format(record)))


@pytest.fixture
def access():
    handler = _Capture()
    logger = rl.access_logger
    old = logger.level
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    yield handler.lines
    logger.removeHandler(handler)
    logger.setLevel(old)


@pytest.fixture
def client(tmp_path, monkeypatch):
    with _boot_client(tmp_path, monkeypatch) as c:
        yield c


def test_a_safe_request_id_comes_back_unchanged(client, access):
    r = client.get("/health", headers={"X-Request-ID": "web-7f3a9c1e.42_x"})
    assert r.headers["x-request-id"] == "web-7f3a9c1e.42_x"
    assert access[-1]["request_id"] == "web-7f3a9c1e.42_x"


def test_a_missing_request_id_is_generated(client, access):
    first = client.get("/health").headers["x-request-id"]
    second = client.get("/health").headers["x-request-id"]
    assert re.fullmatch(r"[0-9a-f]{32}", first) and first != second
    assert access[-1]["request_id"] == second


@pytest.mark.parametrize("bad", [
    "abc\r\nX-Injected: 1",            # header / log-line forgery
    "x" * 65,                           # overlong
    "<script>alert(1)</script>",        # unsafe charset
    "short",                            # too short to be unique
    "id with spaces 123",
])
def test_a_malicious_request_id_is_replaced_never_echoed(bad):
    assert not rl.valid_request_id(bad)


def test_a_malicious_request_id_over_http_is_replaced(client, access):
    r = client.get("/health", headers={"X-Request-ID": "<script>alert(1)</script>"})
    rid = r.headers["x-request-id"]
    assert "script" not in rid and re.fullmatch(r"[0-9a-f]{32}", rid)
    assert access[-1]["request_id"] == rid


def test_the_json_formatter_writes_cloud_loggings_fields(monkeypatch):
    monkeypatch.setenv("ACOS_GCP_PROJECT", "demo-project")
    token = rl._context.set({"request_id": "req-12345678", "school_id": "school_9",
                             "trace": TRACE, "span": "17"})
    try:
        record = logging.LogRecord("academicos.x", logging.WARNING, __file__, 1, "held %s", ("back",), None)
        doc = json.loads(rl.JsonFormatter().format(record))
    finally:
        rl._context.reset(token)
    assert doc["severity"] == "WARNING" and doc["message"] == "held back"
    assert doc["request_id"] == "req-12345678" and doc["school_id"] == "school_9"
    assert doc["logging.googleapis.com/trace"] == f"projects/demo-project/traces/{TRACE}"
    assert doc["logging.googleapis.com/spanId"] == "17"
    assert doc["time"].endswith("+00:00") and doc["logger"] == "academicos.x"


def test_json_on_cloud_run_text_locally(monkeypatch):
    monkeypatch.delenv("ACOS_LOG_FORMAT", raising=False)
    monkeypatch.delenv("K_SERVICE", raising=False)
    assert rl.use_json() is False
    monkeypatch.setenv("K_SERVICE", "academicos-backend")
    assert rl.use_json() is True
    monkeypatch.setenv("ACOS_LOG_FORMAT", "text")
    assert rl.use_json() is False
    monkeypatch.delenv("K_SERVICE")
    monkeypatch.setenv("ACOS_LOG_FORMAT", "json")
    assert rl.use_json() is True


def test_the_trace_header_reaches_the_access_line(client, access, monkeypatch):
    monkeypatch.setenv("ACOS_GCP_PROJECT", "demo-project")
    client.get("/health", headers={"X-Cloud-Trace-Context": f"{TRACE}/99;o=1"})
    assert access[-1]["logging.googleapis.com/trace"] == f"projects/demo-project/traces/{TRACE}"
    assert access[-1]["logging.googleapis.com/spanId"] == "99"


def test_a_signed_in_request_logs_its_school_and_nothing_personal(client, access):
    email = "head.asha@school1.test"
    body = _register(client, "school_1", email, "Asha Head", principal_key=PRINCIPAL_KEY)
    token = body["token"]
    access.clear()
    r = client.put("/api/v1/me/progress/guide.done.setup?note=asha@example.com",
                   headers={"Authorization": f"Bearer {token}"}, json={"value": True})
    assert r.status_code == 200, r.text
    [line] = access
    assert line["school_id"] == "school_1"
    assert line["route"] == "/api/v1/me/progress/{key}", "the template, never the raw path"
    assert line["httpRequest"]["status"] == 200 and line["httpRequest"]["requestMethod"] == "PUT"
    assert isinstance(line["duration_ms"], float)
    text = json.dumps(line)
    for leaked in (token, email, "asha", "Asha", "guide.done.setup", "note=", body["user"]["id"]):
        assert leaked not in text, f"{leaked!r} must not be logged"


def test_an_anonymous_request_has_no_school(client, access):
    r = client.get("/api/v1/me/progress")
    assert r.status_code == 401
    assert "school_id" not in access[-1] and access[-1]["httpRequest"]["status"] == 401


def test_the_web_client_may_read_the_request_id(client):
    r = client.get("/health", headers={"Origin": "http://localhost:5000"})
    exposed = r.headers.get("access-control-expose-headers", "")
    assert "x-request-id" in exposed.lower()


def test_an_unhandled_error_still_gets_one_access_line(access):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()
    app.add_middleware(rl.RequestContextMiddleware)

    @app.get("/boom/{sid}")
    def boom(sid: str):
        raise RuntimeError("no row")

    r = TestClient(app, raise_server_exceptions=False).get("/boom/stu_1", headers={"X-Request-ID": "req-abcdef12"})
    assert r.status_code == 500
    [line] = access
    assert line["severity"] == "ERROR" and line["httpRequest"]["status"] == 500
    assert line["route"] == "/boom/{sid}" and line["request_id"] == "req-abcdef12"
