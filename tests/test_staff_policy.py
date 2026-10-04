"""Staff automation (2026-10-04): the school's leave rule approves a teacher's
own short leave with enough notice and allowance left, and opens cover as the
principal's approval does; anything else waits and the principal is told.
Balances count working days. A check-in after the bell and grace is late. At
09:00 the teachers who have not checked in are reminded and the principal
hears who they are."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from test_cover_routes import BASE, MON, _apply, w  # noqa: F401 - `w` is a fixture

from academicos.curriculum import staff_policy
from academicos.curriculum.staff_policy import StaffPolicy, auto_decision

IST = timezone(timedelta(hours=5, minutes=30))


def _policy(w, **over):
    body = {"autoApprove": True, "maxAutoDays": 2, "minNoticeDays": 0, "annualAllowanceDays": 12,
            "checkInGraceMinutes": 10, "checkInReminder": True, **over}
    r = w.c.put(f"{BASE}/staff-policy", json=body, headers=w.p)
    assert r.status_code == 200, r.text
    return r.json()


def _kinds(w, who):
    return [n["kind"] for n in w.c.get("/api/v1/notifications", headers=who).json()["items"]]


def test_the_rule_decides_in_order():
    on = StaffPolicy(auto_approve=True, max_auto_days=2, min_notice_days=1)
    assert auto_decision(StaffPolicy(), days=1, left_before=12, start_date="2026-06-02", today=MON)[0] is False
    assert auto_decision(on, days=3, left_before=12, start_date="2026-06-03", today=MON)[1].startswith("longer than 2")
    assert "less than 1 day ahead" in auto_decision(on, days=1, left_before=12, start_date=MON, today=MON)[1]
    assert "more than the 0.5 days" in auto_decision(on, days=1, left_before=.5, start_date="2026-06-02", today=MON)[1]
    assert auto_decision(on, days=1, left_before=12, start_date="2026-06-02", today=MON) == (
        True, "approved automatically under the school's leave rule")


def test_without_the_rule_leave_waits_and_the_principal_is_told(w):
    r = _apply(w, "ana")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "pending" and r.json()["decisionNote"] == "waits for the principal"
    assert "leave_requested" in _kinds(w, w.p)


def test_the_rule_approves_and_opens_cover_like_the_principal(w):
    _policy(w)
    r = _apply(w, "ana")
    assert r.status_code == 200, r.text
    leave = r.json()
    assert leave["status"] == "approved" and leave["decidedAutomatically"] is True
    subs = w.c.get(f"{BASE}/substitutions", params={"from": MON, "to": MON}, headers=w.p).json()
    assert subs and all(s["leaveId"] == leave["id"] for s in subs), "every period of the day has cover opened"
    assert "leave_auto_approved" in _kinds(w, w.p)
    assert "leave_decided" in _kinds(w, w.t["ana"])


def test_only_the_principal_sets_the_rule_and_staff_read_it(w):
    assert w.c.put(f"{BASE}/staff-policy", json={"autoApprove": True}, headers=w.t["ana"]).status_code == 403
    got = w.c.get(f"{BASE}/staff-policy", headers=w.t["ana"]).json()
    assert got["autoApprove"] is False and got["firstBell"] == "08:00"
    assert w.c.get(f"{BASE}/staff-policy", headers=w.stu).status_code == 403
    assert w.c.put(f"{BASE}/staff-policy", json={"maxAutoDays": 0}, headers=w.p).status_code == 422


def test_balances_count_working_days_and_cap_the_rule(w):
    _policy(w, annualAllowanceDays=1)
    # Saturday 6 June to Monday 8 June: Sunday is off, so it is 2 working days.
    long_ = _apply(w, "bala", startDate="2026-06-06", endDate="2026-06-08")
    assert long_.json()["status"] == "pending" and "more than the 1 days" in long_.json()["decisionNote"]
    mine = w.c.get(f"{BASE}/my-leave-balance", headers=w.t["bala"]).json()
    assert (mine["allowance"], mine["used"], mine["pending"], mine["left"]) == (1, 0, 2, 0)
    assert mine["autoApprove"] is True
    half = _apply(w, "ana", kind="first_half")
    assert half.json()["status"] == "approved"
    rows = {r["name"]: r for r in w.c.get(f"{BASE}/leave-balances", headers=w.p).json()}
    assert rows["Ana"]["used"] == 0.5 and rows["Ana"]["left"] == 0.5
    assert w.c.get(f"{BASE}/leave-balances", headers=w.t["ana"]).status_code == 403


def test_a_check_in_after_the_bell_and_grace_is_late(w, monkeypatch):
    from academicos.curriculum import cover_routes
    monkeypatch.setattr(cover_routes, "_late_now", lambda *a: True)
    r = w.c.post(f"{BASE}/my-attendance", headers=w.t["chitra"])
    assert r.status_code == 200 and r.json()["status"] == "late"
    monkeypatch.setattr(cover_routes, "_late_now", lambda *a: False)
    again = w.c.post(f"{BASE}/my-attendance", headers=w.t["chitra"])
    assert again.json()["status"] == "late", "the first check-in stands"
    assert w.c.post(f"{BASE}/my-attendance", headers=w.t["dev"]).json()["status"] == "present"


def test_at_nine_the_missing_are_reminded_and_the_principal_hears_once(w):
    from academicos.curriculum import routes as cr
    from academicos.operations import automations, routes as ops_routes
    w.c.post(f"{BASE}/my-attendance", headers=w.t["dev"])          # Dev is in
    _policy(w)
    _apply(w, "bala")                                               # Bala is on approved leave
    at_nine = datetime(2026, 6, 1, 9, 5, tzinfo=IST)
    out = automations.run_due(ops_routes.store(), cr._require(), cr._require_users(), ops_routes.notify_safely, at_nine)
    assert out["staff_check_in"] == 3, out                         # Ana, Chitra, and the principal
    assert "check_in_reminder" in _kinds(w, w.t["ana"]) and "check_in_reminder" in _kinds(w, w.t["chitra"])
    assert "check_in_reminder" not in _kinds(w, w.t["dev"]) and "check_in_reminder" not in _kinds(w, w.t["bala"])
    told = [n for n in w.c.get("/api/v1/notifications", headers=w.p).json()["items"] if n["kind"] == "staff_not_checked_in"]
    assert len(told) == 1 and "Ana" in told[0]["body"] and "Chitra" in told[0]["body"]
    again = automations.run_due(ops_routes.store(), cr._require(), cr._require_users(), ops_routes.notify_safely,
                                at_nine + timedelta(minutes=5))
    assert again["staff_check_in"] == "done"


def test_no_reminders_on_a_sunday(w):
    from academicos.curriculum import routes as cr
    from academicos.operations import automations, routes as ops_routes
    sunday = datetime(2026, 6, 7, 9, 5, tzinfo=IST)
    out = automations.run_due(ops_routes.store(), cr._require(), cr._require_users(), ops_routes.notify_safely, sunday)
    assert out["staff_check_in"] == 0
