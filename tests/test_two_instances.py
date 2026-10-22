"""R-A1 (#143, findings 1 and 4): two instances on one Postgres do every scheduled thing once.

Two real processes, each with its own OperationsStore on the same schema (as two Cloud Run instances
would be), start at the same moment. Counting rows would not show a job run twice or a message sent
twice, so the assertions count the side effects themselves. Needs a Postgres (ACOS_STORE_PG_HOST or
ACOS_TEST_PG_HOST).
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"


def _pg_env() -> dict[str, str] | None:
    pre = "ACOS_STORE_PG_" if os.environ.get("ACOS_STORE_PG_HOST") else (
        "ACOS_TEST_PG_" if os.environ.get("ACOS_TEST_PG_HOST") else None)
    if pre is None:
        return None
    return {f"ACOS_STORE_PG_{k}": os.environ.get(pre + k, d) for k, d in
            (("HOST", ""), ("PORT", "5432"), ("DB", "postgres"), ("USER", "postgres"), ("PASSWORD", ""))}


pytestmark = pytest.mark.skipif(_pg_env() is None, reason="set ACOS_STORE_PG_HOST or ACOS_TEST_PG_HOST")

_AUTOMATIONS = r"""
import sys, time
from datetime import datetime, timezone
from pathlib import Path
from academicos.operations import automations
from academicos.operations.store import OperationsStore
ops = OperationsStore(Path(sys.argv[1]))
ran = []
def job(ops, cs, users, notify, now):
    ran.append(1)
    time.sleep(1.5)
    return 0
automations.JOBS = [("test_day_job", 0, "day", None, job), ("test_tick_job", 0, "run", None, job)]
start = float(sys.argv[2])
while time.time() < start:
    time.sleep(0.005)
automations.run_due(ops, None, None, lambda **k: [], datetime(2026, 10, 19, 10, 0, tzinfo=timezone.utc))
print(len(ran))
"""

_DELIVERIES = r"""
import sys, time
from datetime import datetime, timezone
from pathlib import Path
from academicos.operations import notifications
from academicos.operations.store import OperationsStore
sent = []
def fake_push(tokens, title, body, data):
    sent.append(data["id"])
    time.sleep(0.2)
    return "sent", None
notifications.send_push = fake_push
OperationsStore.devices_for = lambda self, uid: ["token"]
ops = OperationsStore(Path(sys.argv[1]))
start = float(sys.argv[2])
while time.time() < start:
    time.sleep(0.005)
ops.deliver_due(datetime(2026, 10, 19, 6, 0, tzinfo=timezone.utc))
print(len(sent))
"""


@pytest.fixture
def schema_env(monkeypatch, tmp_path):
    tag = uuid.uuid4().hex[:10]
    schemas = {f"ACOS_PG_SCHEMA_{k}": f"two_{k.lower()}_{tag}" for k in ("OPERATIONS", "API_KEYS", "WEBHOOKS")}
    env = {**_pg_env(), "ACOS_STORE_BACKEND": "postgres", **schemas}
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    yield env
    import psycopg
    from academicos.storage import pg_sqlite
    pg_sqlite.close_idle()
    with psycopg.connect(**pg_sqlite._dsn(), autocommit=True) as c:
        for schema in schemas.values():
            c.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")


def _both(code: str, env: dict, db: Path, *extra: str) -> list[int]:
    child = {**os.environ, **env, "PYTHONPATH": str(SRC)}
    child.pop("PYTEST_CURRENT_TEST", None)
    start = time.time() + 5.0
    if start % 60 > 45:                     # the quota counts per clock minute: race inside one
        start += 61 - start % 60
    procs = [subprocess.Popen([sys.executable, "-c", code, str(db), str(start), *extra], env=child, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(2)]
    out = []
    for p in procs:
        stdout, stderr = p.communicate(timeout=120)
        assert p.returncode == 0, stderr[-2000:]
        out.append(int(stdout.strip().splitlines()[-1]))
    return out


def test_two_instances_run_each_scheduled_job_once(schema_env, tmp_path):
    from academicos.operations.store import OperationsStore
    db = tmp_path / "operations.sqlite"
    OperationsStore(db).conn.close()                    # the schema exists before they race
    ran = _both(_AUTOMATIONS, schema_env, db)
    assert sorted(ran) == [0, 2], f"one instance ran both jobs, the other none: {ran}"
    # The day's job is recorded as done; the next round runs only the every-tick job.
    assert _both(_AUTOMATIONS, schema_env, db) in ([1, 0], [0, 1])


def test_two_instances_send_each_message_once(schema_env, tmp_path):
    from academicos.operations.store import OperationsStore
    db = tmp_path / "operations.sqlite"
    ops = OperationsStore(db)
    for i in range(6):
        ops._exec("INSERT INTO notifications (id, school_id, user_id, kind, title, body, link, data_json, "
                  "created_at, push_status, email_status) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                  (f"n{i}", "school_1", f"u{i}", "holiday_declared", "Holiday", "Diwali", None, "{}",
                   "2026-10-19T05:00:00+00:00", "pending", "none"))
    ops._commit()
    ops.conn.close()
    sent = _both(_DELIVERIES, schema_env, db)
    assert sum(sent) == 6, f"each of the 6 messages sent once, not {sent}"


# ---- the question bank API's stores ---------------------------------------------------------------

_QUOTA = r"""
import sys, time
from pathlib import Path
from academicos.assessment.api_keys import ApiKeyStore, QuotaExceeded
keys = ApiKeyStore(Path(sys.argv[1]))
key = keys.authenticate(sys.argv[3])
start = float(sys.argv[2])
while time.time() < start:
    time.sleep(0.005)
allowed = 0
for _ in range(40):
    try:
        keys.check_quota(key)
        allowed += 1
    except QuotaExceeded:
        pass
print(allowed)
"""

_WEBHOOK_DELIVERIES = r"""
import sys, time
from pathlib import Path
from academicos.assessment.api_keys import ApiKeyStore
from academicos.assessment.webhooks import WebhookService, WebhookStore
sent = []
def sender(url, address, body, headers, timeouts):
    sent.append(headers)
    time.sleep(0.2)
    return 200
db = Path(sys.argv[1])
service = WebhookService(WebhookStore(db.with_name("webhooks.sqlite")), ApiKeyStore(db),
                         sender=sender, resolver=lambda host, port: ["93.184.216.34"], background=False)
start = float(sys.argv[2])
while time.time() < start:
    time.sleep(0.005)
service.deliver_due()
print(len(sent))
"""


def test_two_instances_hold_an_api_keys_quota_together(schema_env, tmp_path):
    """A partner's key allows 25 requests a minute however many instances serve it: two instances
    taking 40 each at the same moment let 25 through between them, not 25 each, and not 26."""
    from academicos.assessment.api_keys import ApiKeyStore
    db = tmp_path / "api_keys.sqlite"
    keys = ApiKeyStore(db)
    plaintext, _ = keys.create(school_id="school_1", scopes=["questions:read"], label="partner",
                               quota_per_minute=25)
    keys.close()
    allowed = _both(_QUOTA, schema_env, db, plaintext)
    assert sum(allowed) == 25, f"25 allowed between the two instances, not {allowed}"


def test_two_instances_deliver_each_webhook_once(schema_env, tmp_path):
    from datetime import datetime, timezone

    from academicos.assessment.api_keys import ApiKeyStore
    from academicos.assessment.webhooks import WebhookStore, _event
    db = tmp_path / "api_keys.sqlite"
    keys = ApiKeyStore(db)
    _, key = keys.create(school_id="school_1", scopes=["questions:read"], label="partner")
    hooks = WebhookStore(db.with_name("webhooks.sqlite"))
    _, hook = hooks.create(key_id=key.id, school_id="school_1", url="https://partner.example/hook",
                           events=["questions.added"], created_by="t")
    for i in range(6):
        hooks.enqueue(hook["id"], _event(subject="Science", grade=10, chapter_id=f"c{i}", question_ids=[f"q{i}"],
                                         reason="test"), due_at=datetime(2026, 10, 19, tzinfo=timezone.utc))
    hooks.close()
    keys.close()
    sent = _both(_WEBHOOK_DELIVERIES, schema_env, db)
    assert sum(sent) == 6, f"each of the 6 events delivered once, not {sent}"
