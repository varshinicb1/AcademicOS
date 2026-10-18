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
    env = {**_pg_env(), "ACOS_STORE_BACKEND": "postgres",
           "ACOS_PG_SCHEMA_OPERATIONS": f"two_{uuid.uuid4().hex[:10]}"}
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    yield env
    import psycopg
    from academicos.storage import pg_sqlite
    pg_sqlite.close_idle()
    with psycopg.connect(**pg_sqlite._dsn(), autocommit=True) as c:
        c.execute(f"DROP SCHEMA IF EXISTS {env['ACOS_PG_SCHEMA_OPERATIONS']} CASCADE")


def _both(code: str, env: dict, db: Path) -> list[int]:
    child = {**os.environ, **env, "PYTHONPATH": str(SRC)}
    child.pop("PYTEST_CURRENT_TEST", None)
    start = time.time() + 5.0
    procs = [subprocess.Popen([sys.executable, "-c", code, str(db), str(start)], env=child, text=True,
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
