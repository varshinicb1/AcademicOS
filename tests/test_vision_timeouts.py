"""Every outbound HTTP call must carry a socket timeout.

Why this is a static check rather than only a behavioural one
-------------------------------------------------------------
`requests` with no `timeout=` waits indefinitely. That is not a slow request,
it is a *lost* request: FastAPI runs synchronous endpoints on a bounded
threadpool (`min(40, cpu+4)` workers by default), and a call that never returns
never releases its worker. Enough of them and the process stops serving
anything, with no error logged anywhere -- because nothing ever timed out to
raise.

The behavioural case is hard to cover completely: `vision.py` makes seven calls
across four helper functions, and some only run on a specific provider response.
An AST walk sees all of them, including the paths a test does not reach. So this
file does both -- the static check proves the *property* holds everywhere, and
the behavioural test proves the value actually reaches the transport at runtime
(a `timeout=None` would satisfy the AST check, so the AST check alone would have
a hole).

Context: this was a real defect. All seven calls in `assessment/vision.py`
lacked a timeout, and the module's `timeout_sec` parameter -- which looks like it
covers them -- bounds only the *polling loop's* willingness to wait, not any
individual socket.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SRC_ROOT = ROOT / "src" / "academicos"
HTTP_VERBS = {"get", "post", "put", "patch", "delete", "head", "request"}


def _requests_calls(path: Path) -> list[ast.Call]:
    """Every `requests.<verb>(...)` call in a module."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: list[ast.Call] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr not in HTTP_VERBS:
            continue
        if isinstance(func.value, ast.Name) and func.value.id == "requests":
            found.append(node)
    return found


def _modules_using_requests() -> list[Path]:
    return sorted(p for p in SRC_ROOT.rglob("*.py") if _requests_calls(p))


def test_the_walk_finds_modules_at_all():
    """Guard the guard: an AST walk that silently matches nothing passes vacuously."""
    modules = _modules_using_requests()
    assert modules, "found no module calling requests.<verb>() -- the walk is broken"
    names = {p.name for p in modules}
    assert "vision.py" in names


def test_every_outbound_http_call_passes_a_timeout():
    offenders: list[str] = []
    total = 0
    for module in _modules_using_requests():
        for call in _requests_calls(module):
            total += 1
            if not any(kw.arg == "timeout" for kw in call.keywords):
                offenders.append(f"{module.relative_to(ROOT).as_posix()}:{call.lineno}")
    assert total > 0
    assert not offenders, (
        "these outbound HTTP calls have no `timeout=`, so a wedged connection "
        "holds a threadpool worker forever:\n  " + "\n  ".join(offenders)
    )


def test_timeout_is_not_literally_none():
    """`timeout=None` is requests' default and satisfies a keyword-presence check."""
    offenders: list[str] = []
    for module in _modules_using_requests():
        for call in _requests_calls(module):
            for kw in call.keywords:
                if kw.arg == "timeout" and isinstance(kw.value, ast.Constant) \
                        and kw.value.value is None:
                    offenders.append(f"{module.relative_to(ROOT).as_posix()}:{call.lineno}")
    assert not offenders, f"explicit timeout=None is the same as no timeout: {offenders}"


def test_vision_calls_the_expected_number_of_endpoints():
    """Pin the count so a new untimed call site cannot be added unnoticed.

    vision.py's job pipeline is create -> upload-urls -> PUT -> start -> poll ->
    download-urls -> download. Seven calls; if this number changes, the new call
    needs a timeout and a thought about which one it is.
    """
    calls = _requests_calls(SRC_ROOT / "assessment" / "vision.py")
    assert len(calls) == 7, (
        f"expected 7 HTTP calls in vision.py, found {len(calls)} -- "
        f"a new call must pass timeout= and this count must be updated"
    )


# --------------------------------------------------------------------------- #
# behavioural: the values actually reach the transport
# --------------------------------------------------------------------------- #

class _RecordingResponse:
    def __init__(self, payload=None):
        self._payload = payload or {}
        self.status_code = 200
        self.text = "{}"
        self.headers: dict[str, str] = {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        return None


def test_vision_passes_finite_timeouts_to_the_transport(monkeypatch):
    """The static check would pass on `timeout=0` or a nonsense expression."""
    import zipfile
    import io
    import requests

    from academicos.assessment import vision

    recorded: list[float] = []

    def fake_post(url, **kw):
        recorded.append(kw.get("timeout"))
        if url.endswith("/download-files"):
            return _RecordingResponse({"download_urls": {"a.md": {"file_url": "https://x/a.md"}}})
        if "/start" in url:
            return _RecordingResponse({})
        if url.endswith("/upload-files"):
            return _RecordingResponse({"upload_urls": {"page.png": {"file_url": "https://x/put"}}})
        if "/job/v1" in url and url.rstrip("/").endswith("/job/v1"):
            return _RecordingResponse({"job_id": "job-1"})
        return _RecordingResponse({"job_state": "completed"})

    def fake_put(url, **kw):
        recorded.append(kw.get("timeout"))
        return _RecordingResponse({})

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("out.md", "transcribed text")

    def fake_get(url, **kw):
        recorded.append(kw.get("timeout"))
        if url.endswith("/status"):
            return _RecordingResponse({"job_state": "completed"})
        resp = _RecordingResponse({})
        resp.content = buf.getvalue()
        return resp

    monkeypatch.setattr(requests, "post", fake_post)
    monkeypatch.setattr(requests, "put", fake_put)
    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr(vision, "_POLL_INTERVAL_SEC", 0, raising=False)
    monkeypatch.setattr(vision.time, "sleep", lambda s: None)
    monkeypatch.setattr(vision, "api_key", lambda: "test-key")

    page = Path(__file__).parent / "_vision_probe.png"
    page.write_bytes(b"\x89PNG\r\n\x1a\n")
    try:
        vision.extract(page)
    finally:
        page.unlink(missing_ok=True)

    assert recorded, "no HTTP calls were recorded -- the fake transport was not exercised"
    assert all(t is not None for t in recorded), f"a call had no timeout: {recorded}"
    assert all(isinstance(t, (int, float)) and t > 0 for t in recorded), (
        f"every timeout must be a positive number of seconds, got {recorded}"
    )


def test_vision_poll_loop_timeout_does_not_cover_the_socket():
    """Documents the distinction that made this a bug worth a test file.

    `extract(timeout_sec=...)` bounds how long we wait for the *job*. It says
    nothing about any individual socket, which is why the per-call timeouts are
    a separate, necessary thing rather than redundant with it.
    """
    vision_path = SRC_ROOT / "assessment" / "vision.py"
    source = vision_path.read_text(encoding="utf-8")
    assert "_API_TIMEOUT_SEC" in source
    assert "_UPLOAD_TIMEOUT_SEC" in source
    assert "_DOWNLOAD_TIMEOUT_SEC" in source
