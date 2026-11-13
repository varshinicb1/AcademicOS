"""Request ids, one access line per request, and JSON logs on Cloud Run
(R-A4, REQUIREMENTS NFR-7: "structured logs").

Before this, a log line could not be tied to the request that wrote it, nor
to the school it served, and uvicorn's access line carried the raw path and
query string. Now:

- **Request id.** Each request carries one id: the caller's `X-Request-ID`
  when it is short and of a safe charset, otherwise a fresh one. It is sent
  back in the `X-Request-ID` response header, so a teacher's "it failed"
  screenshot or a support ticket can name the exact log lines.
- **School id.** Once auth resolves the signed-in user
  (`auth_routes.get_current_user`), `bind_school` records that user's
  `school_id` -- never anything from the request body.
- **Access line.** One per request on the `academicos.access` logger:
  method, the route's template (`/api/v1/students/{sid}`, so no ids), status,
  duration in ms, request id and school id. No query string, header, token,
  email or body is ever logged.
- **Format.** On Cloud Run (`K_SERVICE` is set) or with
  `ACOS_LOG_FORMAT=json`, every log record is one JSON line with the fields
  Cloud Logging reads (`severity`, `message`, `time`,
  `logging.googleapis.com/trace` and `.../spanId` when the request came
  through Google's front end and the project is known). Locally it is plain
  text. `ACOS_LOG_FORMAT=text` forces text anywhere. Standard library only.

The context lives in a contextvar holding a small mutable dict. FastAPI runs
sync dependencies and handlers in worker threads, each with a *copy* of the
context; a copy shares the same dict, so a school id bound inside the auth
dependency is seen by the handler's log lines and by the access line.
"""
from __future__ import annotations

import contextvars
import json
import logging
import os
import re
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

access_logger = logging.getLogger("academicos.access")

HEADER = b"x-request-id"
_SAFE_ID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")
_TRACE = re.compile(r"^([0-9a-fA-F]{32})(?:/(\d{1,20}))?")

_context: contextvars.ContextVar[Optional[dict[str, Optional[str]]]] = contextvars.ContextVar(
    "acos_request_context", default=None)


def valid_request_id(value: Optional[str]) -> bool:
    """8-64 characters of letters, digits, '.', '_' or '-': enough for a UUID
    or a trace id, and nothing that could forge a log line or a header."""
    return bool(value) and bool(_SAFE_ID.match(value))


def current() -> dict[str, Optional[str]]:
    """The running request's context (empty outside a request)."""
    return _context.get() or {}


def current_request_id() -> Optional[str]:
    return current().get("request_id")


def bind_school(school_id: Optional[str]) -> None:
    """Called where auth resolves the signed-in user. A no-op outside a request."""
    ctx = _context.get()
    if ctx is not None:
        ctx["school_id"] = school_id or None


def _gcp_project() -> Optional[str]:
    return (os.environ.get("ACOS_GCP_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT")
            or os.environ.get("GCP_PROJECT") or None)


def _trace_from(header: str) -> tuple[Optional[str], Optional[str]]:
    """`X-Cloud-Trace-Context: TRACE_ID/SPAN_ID;o=1` -> (trace id, span id)."""
    m = _TRACE.match(header or "")
    if not m:
        return None, None
    return m.group(1).lower(), m.group(2)


class RequestContextMiddleware:
    """Raw ASGI middleware, registered outermost in api/main.py, so its
    duration covers every other layer and every response carries the id."""

    def __init__(self, app_: Any) -> None:
        self.app = app_

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {k.lower(): v for k, v in scope.get("headers") or []}
        offered = headers.get(HEADER, b"").decode("latin-1")
        request_id = offered if valid_request_id(offered) else uuid.uuid4().hex
        trace, span = _trace_from(headers.get(b"x-cloud-trace-context", b"").decode("latin-1"))
        ctx: dict[str, Optional[str]] = {"request_id": request_id, "school_id": None,
                                         "trace": trace, "span": span}
        token = _context.set(ctx)
        started = time.perf_counter()
        status = {"code": 500}
        raw_id = request_id.encode("ascii")

        async def send_with_id(message: Any) -> None:
            if message["type"] == "http.response.start":
                status["code"] = message["status"]
                kept = [(k, v) for k, v in message.get("headers", []) if k.lower() != HEADER]
                message["headers"] = kept + [(HEADER, raw_id)]
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        finally:
            route = getattr(scope.get("route"), "path", None) or "(unmatched)"
            duration_ms = round((time.perf_counter() - started) * 1000, 1)
            code = status["code"]
            level = logging.ERROR if code >= 500 else logging.INFO
            access_logger.log(
                level, "%s %s %d %.1fms", scope.get("method"), route, code, duration_ms,
                extra={"http": {"method": scope.get("method"), "route": route, "status": code,
                                "duration_ms": duration_ms}})
            _context.reset(token)


# ------------------------------------------------------------------ formats

_SEVERITY = {logging.DEBUG: "DEBUG", logging.INFO: "INFO", logging.WARNING: "WARNING",
             logging.ERROR: "ERROR", logging.CRITICAL: "CRITICAL"}


class JsonFormatter(logging.Formatter):
    """One JSON object per record, in the shape Cloud Logging parses from a
    container's stdout/stderr (cloud.google.com/logging/docs/structured-logging)."""

    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        if record.exc_info:
            message = f"{message}\n{self.formatException(record.exc_info)}"
        entry: dict[str, Any] = {
            "severity": _SEVERITY.get(record.levelno, record.levelname),
            "message": message,
            "time": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "logger": record.name,
        }
        ctx = current()
        if ctx.get("request_id"):
            entry["request_id"] = ctx["request_id"]
        if ctx.get("school_id"):
            entry["school_id"] = ctx["school_id"]
        project = _gcp_project()
        if ctx.get("trace") and project:
            entry["logging.googleapis.com/trace"] = f"projects/{project}/traces/{ctx['trace']}"
            if ctx.get("span"):
                entry["logging.googleapis.com/spanId"] = ctx["span"]
        http = getattr(record, "http", None)
        if isinstance(http, dict):
            entry["httpRequest"] = {"requestMethod": http.get("method"), "status": http.get("status"),
                                    "latency": f"{http.get('duration_ms', 0) / 1000:.4f}s"}
            entry["route"] = http.get("route")
            entry["duration_ms"] = http.get("duration_ms")
        return json.dumps(entry, default=str, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """The local format, with the request id and school appended when there are any."""

    def __init__(self) -> None:
        super().__init__("%(asctime)s %(levelname)s %(name)s: %(message)s")

    def format(self, record: logging.LogRecord) -> str:
        line = super().format(record)
        ctx = current()
        if ctx.get("request_id"):
            line += f" [rid={ctx['request_id']} school={ctx.get('school_id') or '-'}]"
        return line


def use_json() -> bool:
    fmt = os.environ.get("ACOS_LOG_FORMAT", "").strip().lower()
    if fmt in ("json", "text"):
        return fmt == "json"
    return bool(os.environ.get("K_SERVICE"))


class _StderrHandler(logging.StreamHandler):
    """Writes to whatever `sys.stderr` is at the time of the write, so a
    stream swapped out and closed later (a test runner's capture) is never
    written to."""

    def __init__(self) -> None:
        super().__init__(sys.stderr)

    @property  # type: ignore[override]
    def stream(self):  # noqa: ANN201
        return sys.stderr

    @stream.setter
    def stream(self, _value) -> None:  # noqa: ANN001
        pass


def configure_logging(level: int = logging.INFO) -> None:
    """Install one root handler writing the chosen format to stderr. Called
    from `cli` before any command runs; calling it again replaces only the
    handler it installed, never another (a test runner's, say)."""
    handler = _StderrHandler()
    handler.setFormatter(JsonFormatter() if use_json() else TextFormatter())
    root = logging.getLogger()
    for old in list(root.handlers):
        if isinstance(old, _StderrHandler):
            root.removeHandler(old)
    root.addHandler(handler)
    root.setLevel(level)
