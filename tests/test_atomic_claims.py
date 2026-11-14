"""NFR-4, R-A1 (#143 items 1 and 4): what two instances may both start is decided by one atomic
statement, not by a check and then an act.

Two OperationsStores (or CurriculumStores) over one SQLite file stand in for two Cloud Run instances:
each has its own connection and its own process locks, so nothing here relies on a lock in memory.
The second instance acts while the first is mid-way, which is the window a check-then-act loses.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from academicos.operations import automations
from academicos.operations.store import OperationsStore

NOW = datetime(2026, 10, 19, 10, 0, tzinfo=timezone.utc)


def _count(ops, sql, params=()):
    return ops._fetchone(sql, params)["n"]


def test_two_instances_run_a_days_job_once_and_notify_once(tmp_path, monkeypatch):
    db = tmp_path / "operations.sqlite"
    first, second = OperationsStore(db), OperationsStore(db)
    ran = []
    inner = {}

    def job(ops, cs, users, notify, now):
        ran.append(ops)
        ops.notify(school_id="school_1", user_ids=["u1"], kind="holiday_declared",
                   params={"label": "Diwali", "dates": "20 Oct", "moved": "", "moved_hi": ""}, dedupe_key="holiday:2026-10-20")
        if len(ran) == 1:
            # The other instance's tick arrives while this run is still going.
            inner["out"] = automations.run_due(second, None, None, lambda **k: [], NOW)
        return 1

    monkeypatch.setattr(automations, "JOBS", [("test_day_job", 0, "day", None, job)])
    out = automations.run_due(first, None, None, lambda **k: [], NOW)

    assert len(ran) == 1, "the second instance ran the job the first had claimed"
    # On SQLite the claim turns it away; on Postgres the run-wide advisory lock already does.
    assert inner["out"] in ({"test_day_job": "done"}, {"busy": True}) and out["test_day_job"] == 1
    assert _count(first, "SELECT COUNT(*) AS n FROM notifications WHERE user_id='u1'") == 1
    assert _count(first, "SELECT COUNT(*) AS n FROM automation_runs WHERE job='test_day_job'") == 1
    assert first._fetchone("SELECT notified FROM automation_runs WHERE job='test_day_job'")["notified"] == 1
    # The day is done for both: the next tick on either runs nothing.
    assert automations.run_due(second, None, None, lambda **k: [], NOW)["test_day_job"] == "done"
    assert len(ran) == 1


def test_a_failed_job_gives_its_claim_back_and_the_next_tick_retries(tmp_path, monkeypatch):
    ops = OperationsStore(tmp_path / "operations.sqlite")
    calls = []

    def flaky(ops, cs, users, notify, now):
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("mail server down")
        return 3

    monkeypatch.setattr(automations, "JOBS", [("test_flaky", 0, "day", None, flaky)])
    assert automations.run_due(ops, None, None, lambda **k: [], NOW)["test_flaky"].startswith("failed")
    assert _count(ops, "SELECT COUNT(*) AS n FROM automation_runs") == 0
    assert automations.run_due(ops, None, None, lambda **k: [], NOW)["test_flaky"] == 3
    assert automations.run_due(ops, None, None, lambda **k: [], NOW)["test_flaky"] == "done"
    assert len(calls) == 2


def test_a_claim_is_one_winner_and_a_stale_claim_can_be_taken_over(tmp_path):
    db = tmp_path / "operations.sqlite"
    first, second = OperationsStore(db), OperationsStore(db)
    stamp = first.claim_automation("j", "2026-10-19", now=NOW)
    assert stamp is not None
    assert second.claim_automation("j", "2026-10-19", now=NOW) is None
    # The first instance was stopped mid-run: half an hour on, its claim is taken over, once.
    later = NOW.replace(hour=11)
    taken = second.claim_automation("j", "2026-10-19", now=later)
    assert taken is not None and first.claim_automation("j", "2026-10-19", now=later) is None
    # The stopped run's release (were it to come) no longer touches the claim that replaced it.
    first.release_automation("j", "2026-10-19", stamp)
    assert _count(first, "SELECT COUNT(*) AS n FROM automation_runs") == 1
    second.record_automation("j", "2026-10-19", 4, {"school_1": 4})
    assert first.claim_automation("j", "2026-10-19", now=later.replace(hour=23)) is None, "a finished run is never stale"
    assert first.automation_history("school_1")[0]["notified"] == 4


# ---------------- cover and leave: two answers to one question ----------------

from test_cover_routes import BASE, _apply, w  # noqa: E402,F401 - `w` is a fixture


def _second_store(w):
    from academicos.curriculum.store import CurriculumStore
    return CurriculumStore(w.store.db_path)


def _between_read_and_write(monkeypatch, store, getter, act):
    """Run `act` once, right after `store` reads (via `getter`) what it is about to change: the other
    instance's request landing in the check-then-act window."""
    original = getattr(store, getter)
    done = []

    def read_then_race(*a, **k):
        got = original(*a, **k)
        if not done:
            done.append(1)
            act()
        return got
    monkeypatch.setattr(store, getter, read_then_race)


def test_a_leave_decided_on_two_instances_at_once_is_decided_once(w, monkeypatch):
    from academicos.curriculum.cover import CoverError
    leave = _apply(w, "ana").json()
    other = _second_store(w)
    _between_read_and_write(monkeypatch, w.store, "get_leave",
                            lambda: other.decide_leave(leave["id"], approve=False, decided_by="principal-b"))
    with pytest.raises(CoverError, match="decided a moment ago"):
        w.store.decide_leave(leave["id"], approve=True, decided_by="principal-a")
    monkeypatch.undo()
    after = w.store.get_leave(leave["id"])
    assert (after.status, after.decided_by) == ("rejected", "principal-b")
    assert w.store._fetchall("SELECT id FROM substitutions") == [], "a rejected leave opened no cover"


def test_a_cover_reassigned_while_its_teacher_accepts_is_not_accepted_for_the_new_teacher(w, monkeypatch):
    from academicos.curriculum.cover import CoverError
    leave = _apply(w, "ana").json()
    subs = w.c.post(f"{BASE}/leave-requests/{leave['id']}/decision", json={"approve": True},
                    headers=w.p).json()["substitutions"]
    duty = next(s for s in subs if s["sectionId"] == w.b10 and s["period"] == 2)
    assert duty["substituteId"] == w.uid["chitra"] and duty["status"] == "proposed"
    other = _second_store(w)
    # The principal gives the period to Dev on the other instance while Chitra's accept is in flight.
    _between_read_and_write(monkeypatch, w.store, "get_substitution",
                            lambda: other._exec("UPDATE substitutions SET substitute_id=?, status='proposed' "
                                                "WHERE id=?", (w.uid["dev"], duty["id"])) or other._commit())
    with pytest.raises(CoverError):
        w.store.respond_to_substitution(duty["id"], teacher_id=w.uid["chitra"], accept=True)
    monkeypatch.undo()
    after = w.store.get_substitution(duty["id"])
    assert (after.substitute_id, after.status) == (w.uid["dev"], "proposed"), "Dev's duty was marked accepted"


def test_a_cover_declined_twice_at_once_is_declined_once(w, monkeypatch):
    from academicos.curriculum.cover import CoverError
    leave = _apply(w, "ana").json()
    subs = w.c.post(f"{BASE}/leave-requests/{leave['id']}/decision", json={"approve": True},
                    headers=w.p).json()["substitutions"]
    duty = next(s for s in subs if s["sectionId"] == w.b10 and s["period"] == 2)
    other = _second_store(w)
    _between_read_and_write(monkeypatch, w.store, "get_substitution",
                            lambda: other.respond_to_substitution(duty["id"], teacher_id=w.uid["chitra"],
                                                                  accept=False))
    with pytest.raises(CoverError):
        w.store.respond_to_substitution(duty["id"], teacher_id=w.uid["chitra"], accept=False)
    monkeypatch.undo()
    # One decline, so the duty moved on once: to the next candidate, not past them too.
    after = w.store.get_substitution(duty["id"])
    assert after.substitute_id != w.uid["chitra"]
    nxt = [c.teacher_id for c in w.store.substitute_candidates(duty["id"]) if c.teacher_id != w.uid["chitra"]]
    assert after.substitute_id == (nxt[0] if nxt else None)


def test_a_plan_made_twice_at_once_has_each_lesson_once(w, monkeypatch):
    """Both callers find no plan; before the fix both then wrote one, and every lesson was there twice."""
    from academicos.curriculum import scheduling
    from test_cover_exams import _science_book
    book = _science_book(w)
    make = dict(school_id="school_1", academic_year_id=w.year, book_id=book, periods_per_week=1,
                from_date="2026-06-01", section_id=w.a10)
    refused = []

    def other_request():
        try:
            scheduling.schedule_book(w.store, **make)
        except ValueError as e:
            refused.append(str(e))
    _between_read_and_write(monkeypatch, w.store, "scheduled_lessons_for_book", other_request)
    scheduling.schedule_book(w.store, **make)
    monkeypatch.undo()
    lessons = w.store.scheduled_lessons_for_book(w.year, book, w.a10)
    assert lessons and len({(l.date, l.subtopic_id) for l in lessons}) == len(lessons), "lessons doubled"
    assert refused and "being made right now" in refused[0]
