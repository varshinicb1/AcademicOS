"""The GCP release refuses to run misconfigured, and says what build it is.

Why this exists (audit item 8.3, 2026-09-21): the live release served a build
at least 4 days older than its source -- missing 8 operations -- and reported
version `0.1.0` with no commit id, so nobody could tell. And
`deploy/gcp/bootstrap.sh` creates every Secret Manager entry holding the
placeholder `REPLACE_ME`: a service started on that placeholder, with CORS
open to `*`, or with the demo accounts (`principal@school.com` /
`password123`) seeded, must not come up looking healthy.

Each guard condition is asserted twice: it stops startup in production, and it
is ignored outside production (local, dev and the test suite are unaffected).
Everything here is hermetic -- no network, no cloud project.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from academicos import config as config_mod
from academicos.config import (
    Config,
    LLMNotEnabled,
    ProductionConfigError,
    enforce_production_config,
    is_production,
    production_config_problems,
)

REPO = Path(__file__).resolve().parents[1]
WORKFLOW = REPO / ".github" / "workflows" / "deploy-gcp.yml"
CHECK_SCRIPT = REPO / "deploy" / "gcp" / "check_served_commit.py"

# Every variable the guard reads. Cleared before each test so the developer's
# own shell (or config/secrets.env, which Config.load() copies into
# os.environ) cannot decide the outcome.
_GUARD_ENV = (
    "ACOS_ENV", "ACOS_POSTGRES_HOST", "ACOS_POSTGRES_DB", "ACOS_POSTGRES_USER",
    "ACOS_POSTGRES_PASSWORD", "ACOS_PRINCIPAL_BOOTSTRAP_KEY", "ACOS_CORS_ORIGINS",
    "ACOS_DEMO_ACCOUNTS", "SARVAM_API_KEY", "ACOS_LLM_API_KEY", "ACOS_LLM_BASE_URL",
    "ACOS_LLM_MODEL", "ACOS_BUILD_COMMIT", "ACOS_BUILT_AT",
)

GOOD_KEY = "k" * 40  # a bootstrap key comfortably over the 32-char floor


@pytest.fixture(autouse=True)
def clean_env(monkeypatch, tmp_path):
    for name in _GUARD_ENV:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path / "data"))


def _production(monkeypatch) -> None:
    """A correctly configured GCP release: what deploy-gcp.yml sets."""
    monkeypatch.setenv("ACOS_ENV", "production")
    monkeypatch.setenv("ACOS_POSTGRES_HOST", "/cloudsql/vidyuthlabs:asia-south1:academicos-pg")
    monkeypatch.setenv("ACOS_POSTGRES_DB", "academicos")
    monkeypatch.setenv("ACOS_POSTGRES_USER", "academicos")
    monkeypatch.setenv("ACOS_POSTGRES_PASSWORD", "a-real-database-password")
    monkeypatch.setenv("ACOS_PRINCIPAL_BOOTSTRAP_KEY", GOOD_KEY)
    monkeypatch.setenv("ACOS_CORS_ORIGINS",
                       "https://vidyuthlabs.web.app,https://vidyuthlabs.firebaseapp.com")


def _cfg(toml: dict | None = None) -> Config:
    return Config(toml=toml or {})


# --------------------------------------------------------------------------- #
# Production detection
# --------------------------------------------------------------------------- #

def test_explicit_acos_env_production_is_production(monkeypatch):
    monkeypatch.setenv("ACOS_ENV", "production")
    assert is_production()


def test_cloud_run_cloud_sql_socket_is_production(monkeypatch):
    """Cloud Run reaches Cloud SQL through the /cloudsql/ unix-socket mount --
    nothing else in this repo's environments does, so it identifies the GCP
    release even if ACOS_ENV were dropped from the deploy."""
    monkeypatch.setenv("ACOS_POSTGRES_HOST", "/cloudsql/p:asia-south1:academicos-pg")
    assert is_production()


def test_local_postgres_and_no_env_is_not_production(monkeypatch):
    monkeypatch.setenv("ACOS_POSTGRES_HOST", "localhost")
    assert not is_production()


def test_a_correct_production_config_has_no_problems(monkeypatch):
    _production(monkeypatch)
    assert production_config_problems(_cfg()) == []
    enforce_production_config(_cfg())  # does not raise


# --------------------------------------------------------------------------- #
# Each guard condition: fatal in production, ignored outside it
# --------------------------------------------------------------------------- #

def _break_secret_empty(mp):
    mp.setenv("ACOS_POSTGRES_PASSWORD", "")


def _break_secret_placeholder(mp):
    mp.setenv("ACOS_POSTGRES_PASSWORD", "REPLACE_ME")


def _break_bootstrap_placeholder(mp):
    mp.setenv("ACOS_PRINCIPAL_BOOTSTRAP_KEY", "REPLACE_ME")


def _break_bootstrap_short(mp):
    mp.setenv("ACOS_PRINCIPAL_BOOTSTRAP_KEY", "x" * 31)


def _break_cors_star(mp):
    mp.setenv("ACOS_CORS_ORIGINS", "*")


def _break_cors_unset(mp):
    # Falls back to the localhost dev list: plain http, and not the web app.
    mp.delenv("ACOS_CORS_ORIGINS", raising=False)


def _break_demo_accounts(mp):
    mp.setenv("ACOS_DEMO_ACCOUNTS", "1")


def _break_llm_vendor(mp):
    mp.setenv("ACOS_LLM_API_KEY", "a-real-looking-key")
    mp.setenv("ACOS_LLM_BASE_URL", "https://api.groq.com/openai")


BREAKS = {
    "secret-empty": (_break_secret_empty, "ACOS_POSTGRES_PASSWORD"),
    "secret-placeholder": (_break_secret_placeholder, "ACOS_POSTGRES_PASSWORD"),
    "bootstrap-placeholder": (_break_bootstrap_placeholder, "ACOS_PRINCIPAL_BOOTSTRAP_KEY"),
    "bootstrap-short": (_break_bootstrap_short, "32"),
    "cors-star": (_break_cors_star, "*"),
    "cors-unset": (_break_cors_unset, "CORS"),
    "demo-accounts": (_break_demo_accounts, "ACOS_DEMO_ACCOUNTS"),
    "llm-unlisted-vendor": (_break_llm_vendor, "api.groq.com"),
}


@pytest.mark.parametrize("name", sorted(BREAKS))
def test_each_condition_stops_startup_in_production(monkeypatch, name, caplog):
    breaker, needle = BREAKS[name]
    _production(monkeypatch)
    breaker(monkeypatch)
    problems = production_config_problems(_cfg())
    assert problems, f"{name}: production accepted a broken config"
    assert any(needle in p for p in problems), problems
    with caplog.at_level("ERROR"):
        with pytest.raises(ProductionConfigError):
            enforce_production_config(_cfg())
    # A clear log line, not just a traceback: it names the problem.
    assert any(needle in r.getMessage() for r in caplog.records), caplog.text


@pytest.mark.parametrize("name", sorted(BREAKS))
def test_each_condition_is_ignored_outside_production(monkeypatch, name):
    breaker, _ = BREAKS[name]
    _production(monkeypatch)
    breaker(monkeypatch)
    monkeypatch.delenv("ACOS_ENV")
    monkeypatch.setenv("ACOS_POSTGRES_HOST", "localhost")
    assert not is_production()
    enforce_production_config(_cfg())  # local/dev/test: never refuses


def test_config_toml_groq_default_is_refused_when_a_key_is_set(monkeypatch):
    """config/config.toml ships llm_base_url = api.groq.com. With a key set and
    no explicit ACOS_LLM_BASE_URL, POST /v1/agent/doubt would send student-typed
    text to a vendor no document lists. Production refuses that."""
    _production(monkeypatch)
    monkeypatch.setenv("ACOS_LLM_API_KEY", "a-real-looking-key")
    problems = production_config_problems(_cfg({"llm_base_url": "https://api.groq.com/openai"}))
    assert any("api.groq.com" in p for p in problems), problems


def test_no_llm_key_means_no_vendor_check(monkeypatch):
    """With no key, nothing is ever sent, so an unlisted base URL is inert --
    the school simply runs without AI features."""
    _production(monkeypatch)
    cfg = _cfg({"llm_base_url": "https://api.groq.com/openai"})
    assert production_config_problems(cfg) == []


def test_placeholder_llm_key_is_not_a_key(monkeypatch):
    """bootstrap.sh fills acos-llm-api-key with REPLACE_ME; that must read as
    'LLM not configured', not as a key the critic then sends to a provider."""
    monkeypatch.setenv("ACOS_LLM_API_KEY", "REPLACE_ME")
    assert _cfg().llm_api_key == ""


def test_approved_llm_hosts_are_exactly_compliance_vendor_table():
    """The code's allowlist and docs/compliance.md's LLM vendor table are one
    list kept in two places (docs/ is not in the image), so pin them equal."""
    text = (REPO / "docs" / "compliance.md").read_text(encoding="utf-8")
    section = text.split("### LLM providers", 1)[1].split("\n#", 1)[0]
    hosts = set(re.findall(r"^\|[^|]+\|\s*`([a-z0-9.-]+)`", section, flags=re.M))
    assert hosts, "no LLM provider rows found in docs/compliance.md"
    assert hosts == set(config_mod.APPROVED_LLM_HOSTS)


# --------------------------------------------------------------------------- #
# Startup wiring
# --------------------------------------------------------------------------- #

def test_startup_refuses_before_initialising_anything(monkeypatch):
    import academicos.api.main as main_mod

    calls = []
    monkeypatch.setattr(main_mod, "init_runtime", lambda *a, **k: calls.append(1))
    _production(monkeypatch)
    monkeypatch.setenv("ACOS_PRINCIPAL_BOOTSTRAP_KEY", "REPLACE_ME")
    with pytest.raises(ProductionConfigError):
        main_mod._startup()
    assert calls == []


def test_startup_proceeds_with_a_good_production_config(monkeypatch):
    import academicos.api.main as main_mod

    calls = []
    monkeypatch.setattr(main_mod, "init_runtime", lambda *a, **k: calls.append(1))
    _production(monkeypatch)
    main_mod._startup()
    assert calls == [1]


def _patch_serve(monkeypatch):
    """Stub the two things `cmd_serve` could do before the guard, recording
    the order they are reached in."""
    import argparse

    import uvicorn

    import academicos.api.main as main_mod

    calls = []
    monkeypatch.setattr(main_mod, "init_runtime", lambda *a, **k: calls.append("init_runtime"))
    monkeypatch.setattr(uvicorn, "run", lambda *a, **k: calls.append("uvicorn.run"))
    return calls, argparse.Namespace(host="127.0.0.1", port=0)


def test_serve_refuses_before_initialising_anything(monkeypatch):
    """The container's CMD is `python -m academicos.cli serve`, not `_startup`.
    cmd_serve used to call init_runtime() itself before uvicorn fired
    `_startup`, so every store opened on the unguarded config, and an
    init_runtime failure (a store choking on a placeholder credential) crashed
    the process before the named REFUSING TO START lines were logged."""
    from academicos import cli

    calls, args = _patch_serve(monkeypatch)
    _production(monkeypatch)
    monkeypatch.setenv("ACOS_PRINCIPAL_BOOTSTRAP_KEY", "REPLACE_ME")
    with pytest.raises(ProductionConfigError):
        cli.cmd_serve(args)
    assert calls == []


def test_serve_leaves_initialisation_to_startup(monkeypatch):
    """With a good config cmd_serve only starts uvicorn: `_startup` is the one
    init path, so the stores are not opened twice."""
    from academicos import cli

    calls, args = _patch_serve(monkeypatch)
    _production(monkeypatch)
    assert cli.cmd_serve(args) == 0
    assert calls == ["uvicorn.run"]


# --------------------------------------------------------------------------- #
# Demo accounts
# --------------------------------------------------------------------------- #

def test_demo_accounts_are_not_seeded_in_production(monkeypatch, tmp_path):
    """UserStore used to seed principal@school.com / password123 into SQLite
    on every empty store, and login falls back to SQLite when Cloud SQL has no
    row -- a known password for a principal on a school's service."""
    from academicos.assessment.users import UserStore

    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setenv("ACOS_ENV", "production")
    store = UserStore(tmp_path / "prod" / "users.db")
    assert store.conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0


def test_demo_accounts_still_seed_locally_when_requested(monkeypatch, tmp_path):
    # Two rules combine (security Task 301 + GCP Task 502): demo accounts seed
    # only on explicit request (ACOS_SEED_DEMO_USERS=1), and never in production.
    from academicos.assessment.users import UserStore

    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setenv("ACOS_SEED_DEMO_USERS", "1")
    store = UserStore(tmp_path / "dev" / "users.db")
    assert store.conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 2


def test_demo_accounts_do_not_seed_locally_unless_requested(monkeypatch, tmp_path):
    from academicos.assessment.users import UserStore

    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.delenv("ACOS_SEED_DEMO_USERS", raising=False)
    store = UserStore(tmp_path / "dev2" / "users.db")
    assert store.conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0


def test_the_guard_refuses_the_demo_seed_request_in_production(monkeypatch):
    from academicos import config as config_mod

    monkeypatch.setenv("ACOS_ENV", "production")
    monkeypatch.setenv("ACOS_SEED_DEMO_USERS", "1")
    problems = config_mod.production_config_problems(config_mod.get_config())
    assert any("ACOS_SEED_DEMO_USERS" in p for p in problems)


# --------------------------------------------------------------------------- #
# Build identity
# --------------------------------------------------------------------------- #

def test_health_reports_commit_and_build_time(monkeypatch):
    from fastapi.testclient import TestClient

    import academicos.api.main as main_mod

    monkeypatch.setenv("ACOS_BUILD_COMMIT", "0123456789abcdef0123456789abcdef01234567")
    monkeypatch.setenv("ACOS_BUILT_AT", "2026-09-22T10:00:00Z")
    body = TestClient(main_mod.app).get("/health").json()
    assert body == {"status": "ok",
                    "commit": "0123456789abcdef0123456789abcdef01234567",
                    "builtAt": "2026-09-22T10:00:00Z"}


def test_health_says_unknown_when_the_image_carries_no_identity():
    from fastapi.testclient import TestClient

    import academicos.api.main as main_mod

    body = TestClient(main_mod.app).get("/health").json()
    assert body["commit"] == "unknown" and body["builtAt"] == "unknown"


# --------------------------------------------------------------------------- #
# CORS: production answers only the configured origins
# --------------------------------------------------------------------------- #

# api/main.py decides the CORS policy once, at import time, from is_production()
# -- so it is checked in a fresh interpreter per environment rather than by
# reloading the module this suite (and others) already imported. The child
# sends real preflights through the app and prints what came back.
_CORS_PROBE = """
import json
from fastapi.testclient import TestClient
import academicos.api.main as m
client = TestClient(m.app)
out = {}
for origin in ("https://vidyuthlabs.web.app", "https://other.web.app",
               "https://other.onrender.com"):
    r = client.options("/health", headers={
        "Origin": origin, "Access-Control-Request-Method": "GET"})
    out[origin] = [r.status_code, r.headers.get("access-control-allow-origin")]
print(json.dumps(out))
"""


def _cors_preflights(tmp_path, **env: str) -> dict:
    import os

    child_env = {k: v for k, v in os.environ.items() if k not in _GUARD_ENV}
    child_env.update(
        PYTHONPATH=str(REPO / "src"), PYTHONIOENCODING="utf-8",
        ACOS_DATA_ROOT=str(tmp_path / "data"),
        ACOS_CORS_ORIGINS="https://vidyuthlabs.web.app,https://vidyuthlabs.firebaseapp.com",
        **env,
    )
    proc = subprocess.run([sys.executable, "-c", _CORS_PROBE], env=child_env, cwd=str(REPO),
                          capture_output=True, text=True, timeout=180)
    assert proc.returncode == 0, proc.stderr[-2000:]
    return json.loads(proc.stdout.strip().splitlines()[-1])


def test_production_cors_refuses_other_firebase_and_render_sites(tmp_path):
    """Any *.web.app is ANY Firebase site. With credentials allowed, echoing
    one back would let a stranger's page call this school's API as the
    logged-in teacher. Production answers only ACOS_CORS_ORIGINS."""
    res = _cors_preflights(tmp_path, ACOS_ENV="production")
    assert res["https://vidyuthlabs.web.app"] == [200, "https://vidyuthlabs.web.app"]
    for stranger in ("https://other.web.app", "https://other.onrender.com"):
        status, acao = res[stranger]
        assert acao is None, f"production echoed {stranger} back: {res}"
        assert status == 400


def test_dev_cors_still_answers_any_firebase_and_render_origin(tmp_path):
    """Outside production the wildcard stays, so Firebase preview channels and
    the old Render frontend keep working against a dev API."""
    res = _cors_preflights(tmp_path, ACOS_ENV="development")
    for origin in ("https://vidyuthlabs.web.app", "https://other.web.app",
                   "https://other.onrender.com"):
        assert res[origin] == [200, origin], res


def _check(body: str, expected: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(CHECK_SCRIPT), expected], input=body,
                          capture_output=True, text=True, timeout=60)


def test_served_commit_check_passes_on_a_match():
    sha = "a" * 40
    assert _check(json.dumps({"status": "ok", "commit": sha, "builtAt": "t"}), sha).returncode == 0


@pytest.mark.parametrize("body", [
    json.dumps({"status": "ok", "commit": "b" * 40, "builtAt": "t"}),  # stale build
    json.dumps({"status": "ok", "commit": "unknown", "builtAt": "unknown"}),
    json.dumps({"status": "ok"}),  # the old /health: no identity at all
    "<html>not json</html>",
])
def test_served_commit_check_fails_on_anything_else(body):
    result = _check(body, "a" * 40)
    assert result.returncode != 0
    assert "a" * 40 in result.stdout + result.stderr


# --------------------------------------------------------------------------- #
# The GCP deploy workflow, the image, and Hosting
# --------------------------------------------------------------------------- #

def _jobs() -> dict:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]


def _step(job: str, name_part: str) -> dict:
    steps = [s for s in _jobs()[job]["steps"] if name_part in s.get("name", "")]
    assert len(steps) == 1, f"expected one {job} step named like {name_part!r}"
    return steps[0]


def test_workflow_fails_when_the_served_commit_is_not_the_deployed_one():
    run = _step("backend", "/health")["run"]
    assert "deploy/gcp/check_served_commit.py" in run
    assert '"$GITHUB_SHA"' in run or "${GITHUB_SHA}" in run
    assert "exit 1" in run


def test_workflow_bakes_the_commit_into_the_image():
    run = _step("backend", "Build + push image")["run"]
    assert "_COMMIT_SHA=${GITHUB_SHA}" in run
    assert "_BUILT_AT=" in run
    cloudbuild = (REPO / "deploy" / "gcp" / "cloudbuild.yaml").read_text(encoding="utf-8")
    assert "--build-arg=BUILD_COMMIT=${_COMMIT_SHA}" in cloudbuild
    assert "--build-arg=BUILT_AT=${_BUILT_AT}" in cloudbuild
    dockerfile = (REPO / "Dockerfile").read_text(encoding="utf-8")
    assert "ACOS_BUILD_COMMIT=${BUILD_COMMIT}" in dockerfile
    assert "ACOS_BUILT_AT=${BUILT_AT}" in dockerfile


def test_workflow_deploy_is_production_single_instance_and_explicit_about_llm():
    run = _step("backend", "Deploy to Cloud Run")["run"]
    assert "--max-instances=1" in run  # Task 501: one snapshot writer
    assert "ACOS_ENV=production" in run
    # Both key names from ONE secret: vision.py/llm_evaluate.py read
    # SARVAM_API_KEY, the critic reads ACOS_LLM_API_KEY. Before this only the
    # latter was injected, so scan OCR saw no key on GCP.
    assert "SARVAM_API_KEY=acos-llm-api-key:latest" in run
    assert "ACOS_LLM_API_KEY=acos-llm-api-key:latest" in run
    assert "ACOS_LLM_BASE_URL" in run


def test_web_build_targets_the_cloud_run_api_and_never_offline():
    frontend = _jobs()["frontend"]
    text = yaml.safe_dump(frontend)
    assert "ACADEMICOS_OFFLINE" not in text
    build = _step("frontend", "Build Flutter web")["run"]
    assert '--dart-define=ACADEMICOS_API="${{ needs.backend.outputs.url }}/api/v1"' in build


def test_firebase_hosting_is_an_spa_with_security_headers():
    fb = json.loads((REPO / "firebase.json").read_text(encoding="utf-8"))["hosting"]
    assert fb["public"] == "frontend/build/web"
    assert {"source": "**", "destination": "/index.html"} in fb["rewrites"]
    everywhere = {h["key"]: h["value"]
                  for rule in fb["headers"] if rule.get("source") == "**"
                  for h in rule["headers"]}
    assert everywhere["Strict-Transport-Security"].startswith("max-age=")
    assert everywhere["X-Content-Type-Options"] == "nosniff"
    assert everywhere["Referrer-Policy"] == "strict-origin-when-cross-origin"
    csp = everywhere["Content-Security-Policy"]
    assert "frame-ancestors 'none'" in csp
    # The rest of the policy (script-src, connect-src ...) is held by tests/test_hosting_csp.py. Until
    # 2026-10-04 this header restricted framing only, because a wrong script-src blanks the app; the
    # policy now there was tried against the built app in a browser first.
    assert "script-src" in csp


def test_bootstrap_creates_cloud_sql_on_the_enterprise_edition():
    """2026-09-22 real run: 'Invalid Tier (db-g1-small) for (ENTERPRISE_PLUS)
    Edition' -- new Postgres instances default to Enterprise Plus, which has no
    shared-core tiers."""
    script = (REPO / "deploy" / "gcp" / "bootstrap.sh").read_text(encoding="utf-8")
    flags = script.split("SQL_FLAGS=(", 1)[1].split(")", 1)[0]
    assert "--edition=ENTERPRISE" in flags


# --------------------------------------------------------------------------- #
# Unicode font in the image (audit 1.2)
# --------------------------------------------------------------------------- #

def test_font_lookup_finds_the_font_the_dockerfile_installs(tmp_path):
    """Simulates the image: the Windows fonts are absent and DejaVu is at the
    path fonts-dejavu-core installs to, re-rooted under a temp dir."""
    from academicos.assessment import pdf

    linux = [c for c in pdf._FONT_CANDIDATES if c[1].startswith("/usr/share/fonts/")]
    assert linux, "pdf.py has no candidate at a Debian font path"
    name, regular, bold = linux[0]
    rerooted = []
    for path in (regular, bold):
        p = tmp_path / path.lstrip("/")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"not parsed by the lookup")
        rerooted.append(str(p))
    candidates = [(n, str(tmp_path / "absent" / Path(r).name), str(tmp_path / "absent" / Path(b).name))
                  for n, r, b in pdf._FONT_CANDIDATES if not r.startswith("/usr/share/")]
    candidates.append((name, *rerooted))
    assert pdf.find_unicode_font(candidates) == (name, rerooted[0], rerooted[1])
    assert pdf.find_unicode_font(candidates[:-1]) is None

    dockerfile = (REPO / "Dockerfile").read_text(encoding="utf-8")
    assert "fonts-dejavu-core" in dockerfile  # the package that ships that path
    assert regular == "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def test_startup_logs_the_registered_font(monkeypatch, caplog):
    import academicos.api.main as main_mod

    monkeypatch.setattr(main_mod, "init_runtime", lambda *a, **k: None)
    with caplog.at_level("INFO"):
        main_mod._startup()
    assert any("PDF body font" in r.getMessage() for r in caplog.records), caplog.text


# --------------------------------------------------------------------------- #
# LLM features without a key: a clear "not enabled", not a mid-request failure
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("value", [None, "", "REPLACE_ME"])
def test_scan_ocr_without_a_key_is_not_enabled(monkeypatch, value):
    from academicos.assessment import vision

    if value is not None:
        monkeypatch.setenv("SARVAM_API_KEY", value)
    with pytest.raises(LLMNotEnabled):
        vision.api_key()


def test_add_page_without_a_key_refuses_instead_of_storing_a_blank_page(monkeypatch, tmp_path):
    """mobile_scan.add_page catches every OCR exception and records the page as
    blank; with no key that turned a whole booklet into zeros-for-review."""
    from academicos.assessment import mobile_scan

    monkeypatch.setattr(mobile_scan, "_WORKDIR_ROOT", tmp_path / "scan-sessions")
    session = mobile_scan.ScanSession(id="scan_t", assessment_id="a", student_id="s",
                                      student_name="S")
    with pytest.raises(LLMNotEnabled):
        mobile_scan.add_page(session, b"\xff\xd8 not really a jpeg")
    assert session.pages == []


def test_ai_marking_without_a_key_is_not_enabled(monkeypatch):
    from datetime import datetime, timezone

    from academicos.assessment import llm_evaluate
    from academicos.assessment.schemas import AnswerSchemeSchema, MarkingPointSchema, QuestionSchema

    now = datetime.now(timezone.utc)
    scheme = AnswerSchemeSchema(total_marks=1, metadata={}, marking_points=[
        MarkingPointSchema(id="m1", description="push or pull", marks=1, keyword="push")])
    q = QuestionSchema(
        id="q1", question_bank_id="bank1", subject="science", grade=10, chapter_ids=["c1"],
        competency_ids=[], bloom_level="remember", difficulty="easy", type="short_answer",
        stem="Define force.", parts=[], answer_scheme=scheme, estimated_time_minutes=1,
        marks=1, language="en", source="teacher_created", quality_score=0.7, tags=[],
        created_at=now, updated_at=now,
    )
    with pytest.raises(LLMNotEnabled):
        llm_evaluate.evaluate_answer_llm(q, scheme, "a push or a pull")


def test_not_enabled_reaches_the_client_as_a_clear_answer():
    import academicos.api.main as main_mod

    assert main_mod.app.exception_handlers[LLMNotEnabled] is main_mod._on_llm_not_enabled
    response = main_mod._on_llm_not_enabled(None, LLMNotEnabled())
    body = json.loads(bytes(response.body).decode("utf-8"))
    assert response.status_code == 501
    assert "not enabled for this school" in body["detail"]
    assert body["code"] == "llm_not_enabled"


def _cache_controls(fb):
    return [(rule.get("source") or rule["regex"], h["value"]) for rule in fb["headers"]
            for h in rule["headers"] if h["key"].lower() == "cache-control"]


def test_no_app_file_is_cached_as_if_its_name_changed_with_its_content():
    """Audit 2026-09-26 (item 8.3): `main.dart.js` and `flutter_bootstrap.js`
    were served `public, max-age=31536000, immutable`. Flutter web does not
    content-hash its file names -- every build writes `main.dart.js` again --
    so a browser that had loaded the app once kept running that bundle and
    never asked again: the auditor's browser ran the 2026-09-22 build four
    deploys later, with the old class 11-12 picker and none of the builder.
    A long or immutable cache is only safe on a name that changes when the
    content does. Since D29 (2026-09-28) the two entry files have one:
    scripts/web_cache_bust.py renames them `<name>.<content hash>.js`, and that
    exact shape -- its `HASHED_ENTRY` -- is the one rule allowed a long cache
    (tests/test_web_cache_bust.py holds the rule to the script)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "web_cache_bust", REPO / "scripts" / "web_cache_bust.py")
    wcb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wcb)
    fb = json.loads((REPO / "firebase.json").read_text(encoding="utf-8"))["hosting"]
    for source, value in _cache_controls(fb):
        v = value.lower()
        if source == wcb.HASHED_ENTRY:
            continue
        assert "immutable" not in v, (source, value)
        ages = [int(p.split("=", 1)[1]) for p in v.replace(" ", "").split(",")
                if p.startswith("max-age=")]
        assert all(a == 0 for a in ages), (source, value)


def test_every_app_file_revalidates_on_load():
    """Revalidation, not no-store: the ETag makes an unchanged file a 304, so a
    returning teacher re-downloads the 5 MB bundle only after a deploy."""
    fb = json.loads((REPO / "firebase.json").read_text(encoding="utf-8"))["hosting"]
    everywhere = [v for s, v in _cache_controls(fb) if s == "**"]
    assert everywhere and "no-cache" in everywhere[0].lower()
