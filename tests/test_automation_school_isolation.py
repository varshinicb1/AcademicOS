"""NTF-2, ADM-3: one school's broken data must not stop another school's reminders.

Every scheduled job looped over all schools inside one try, so an exception while handling school B
(a deleted section, a half-made exam) ended the job for every school after it, and every school
before it went unrecorded too. With dozens of schools on one service, one bad record anywhere would
silence the day's homework reminders, alerts and digests everywhere, and only a log line said so.

Now a per-school job runs once per school: a school that fails is recorded as an error group
(GET /api/v1/ops/errors, Cloud Error Reporting) and the job's claim is given back, so the next tick
retries; the other schools' notices go out now, and their dedupe keys stop the retry repeating them.
"""
from __future__ import annotations

import inspect
from datetime import datetime, timezone

from academicos.api import error_tracking as et
from academicos.operations import automations
from academicos.operations.store import OperationsStore

NOW = datetime(2026, 10, 19, 10, 0, tzinfo=timezone.utc)


def _job(fail_for: set[str], seen: list[str]):
    def job(ops, cs, users, notify, now):
        n = 0
        for school in automations._schools(cs):
            seen.append(school)
            if school in fail_for:
                raise ValueError(f"section sec_9 of {school} has no class teacher")
            notify(school_id=school, user_ids=[f"t_{school}"], kind="holiday_declared",
                   params={"label": "Diwali", "dates": "20 Oct", "moved": "", "moved_hi": ""},
                   dedupe_key=f"t:{school}:2026-10-19")
            n += 1
        return n
    return job


def _setup(tmp_path, monkeypatch, job):
    ops = OperationsStore(tmp_path / "operations.sqlite")
    monkeypatch.setattr(automations, "_all_schools", lambda cs: ["school_a", "school_b", "school_c"])
    monkeypatch.setattr(automations, "JOBS", [("test_per_school", 0, "day", None, job)])
    monkeypatch.setattr(automations, "PER_SCHOOL_JOBS", frozenset({"test_per_school"}))
    et.ERRORS.reset()
    return ops


def _notified(ops) -> set[str]:
    return {r["user_id"] for r in ops._fetchall("SELECT user_id FROM notifications")}


def test_one_schools_failure_does_not_stop_the_others(tmp_path, monkeypatch):
    seen: list[str] = []
    ops = _setup(tmp_path, monkeypatch, _job({"school_b"}, seen))

    out = automations.run_due(ops, None, None, ops.notify, NOW)

    assert seen == ["school_a", "school_b", "school_c"], "each school ran on its own"
    assert _notified(ops) == {"t_school_a", "t_school_c"}, "school_c still got its notice after school_b failed"
    assert out["test_per_school"].startswith("failed"), out
    assert "1 of 3 schools" in out["test_per_school"]
    # Not marked done, so the next tick retries the school that failed.
    assert ops._fetchone("SELECT COUNT(*) AS n FROM automation_runs")["n"] == 0


def test_a_school_failure_is_an_error_group_the_operator_can_see(tmp_path, monkeypatch):
    ops = _setup(tmp_path, monkeypatch, _job({"school_b"}, []))
    automations.run_due(ops, None, None, ops.notify, NOW)
    automations.run_due(ops, None, None, ops.notify, NOW)

    groups = [g for g in et.ERRORS.groups() if g.route == "automation test_per_school"]
    assert len(groups) == 1, "the same failure twice is one group"
    g = groups[0]
    assert g.count == 2 and g.kind == "ValueError" and g.schools == {"school_b"}
    assert et.ERRORS.server_total == 2


def test_the_retry_does_not_repeat_what_the_healthy_schools_already_got(tmp_path, monkeypatch):
    failing = {"school_b"}
    seen: list[str] = []
    ops = _setup(tmp_path, monkeypatch, _job(failing, seen))
    automations.run_due(ops, None, None, ops.notify, NOW)
    failing.clear()                                   # the school's data is fixed

    out = automations.run_due(ops, None, None, ops.notify, NOW)

    assert out["test_per_school"] == 3
    rows = ops._fetchall("SELECT user_id FROM notifications ORDER BY user_id")
    assert [r["user_id"] for r in rows] == ["t_school_a", "t_school_b", "t_school_c"], "one notice each"
    assert automations.run_due(ops, None, None, ops.notify, NOW)["test_per_school"] == "done"


def test_a_job_that_cannot_list_schools_still_fails_as_a_whole(tmp_path, monkeypatch):
    ops = _setup(tmp_path, monkeypatch, _job(set(), []))

    def broken(cs):
        raise RuntimeError("curriculum store unavailable")
    monkeypatch.setattr(automations, "_all_schools", broken)

    out = automations.run_due(ops, None, None, ops.notify, NOW)
    assert out["test_per_school"].startswith("failed: curriculum store unavailable")
    assert any(g.route == "automation test_per_school" for g in et.ERRORS.groups())


def test_every_job_that_loops_over_schools_is_run_per_school():
    """A new job that walks _schools(cs) is isolated per school without anyone remembering to."""
    loops = {name for name, *_rest, fn in automations.JOBS if "_schools(cs)" in inspect.getsource(fn)}
    assert loops, "the real jobs loop over schools"
    assert loops <= automations.PER_SCHOOL_JOBS, loops - automations.PER_SCHOOL_JOBS
    # And the run-wide jobs, which do not, stay out (they have no school to scope to).
    assert {"user_digests", "deliveries"}.isdisjoint(automations.PER_SCHOOL_JOBS)
