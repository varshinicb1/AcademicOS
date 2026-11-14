"""FEE-1 oversight for the principal (ADM-2, ADM-3, ADM-4, NTF-2): the year's
fees across the school per class and in total, the overdue list (as JSON and
as CSV or Excel), parents reminded before a fee falls due and once it is
overdue, and Monday's alert counting what is overdue. Cover fixture: Asha
is the only student, in 10-B; 2026-06-01 is a Monday and the school's today."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from test_cover_routes import w  # noqa: F401 - `w` is a fixture
from test_fees import _head, _pay
from test_parent_notices import _h, _items, _parent

IST = timezone(timedelta(hours=5, minutes=30))


def _run(at):
    from academicos.curriculum import routes as cr
    from academicos.operations import automations, routes as ops_routes
    return automations.run_due(ops_routes.store(), cr._require(), cr._require_users(), ops_routes.notify_safely, at)


def test_the_principal_sees_the_years_fees_and_who_is_overdue(w):
    sid, _ = _parent(w)
    tuition = _head(w, "Tuition, term 1", 15_000_00, "2026-05-15")
    _head(w, "Science lab", 2_000_00, "2026-07-01")
    _head(w, "Class 9 trip", 1_000_00, "2026-07-01", grade=9)
    assert _pay(w, sid, tuition, 10_000_00).status_code == 200
    r = w.c.get("/api/v1/fees/overview", headers=w.p)
    assert r.status_code == 200, r.text
    o = r.json()
    assert (o["totalPaise"], o["paidPaise"], o["balancePaise"], o["overduePaise"]) == (
        17_000_00, 10_000_00, 7_000_00, 5_000_00)
    assert o["collectedPercent"] == 58.8
    classes = {c["sectionName"]: c for c in o["classes"]}
    assert classes["10-B"]["students"] == 1 and classes["10-B"]["studentsOverdue"] == 1
    assert "9-A" not in classes, "a class with no students bills nobody"
    [d] = o["defaulters"]
    assert (d["name"], d["sectionName"], d["overduePaise"], d["overdueHeads"]) == (
        "Asha", "10-B", 5_000_00, ["Tuition, term 1"])
    assert o["defaultersTotal"] == 1


def test_the_overdue_list_downloads_and_is_audited(w):
    sid, _ = _parent(w)
    _head(w, "Tuition, term 1", 15_000_00, "2026-05-15")
    csv = w.c.get("/api/v1/fees/defaulters/export", headers=w.p)
    assert csv.status_code == 200 and csv.headers["content-type"].startswith("text/csv")
    lines = csv.text.strip().splitlines()
    assert lines[0] == "name,email,class,overdue_rupees,balance_rupees,overdue_fees"
    assert lines[1].startswith("Asha,s1@example.com,10-B,15000") and lines[1].endswith("Tuition, term 1\"")
    xlsx = w.c.get("/api/v1/fees/defaulters/export", params={"format": "xlsx"}, headers=w.p)
    assert xlsx.status_code == 200 and xlsx.content[:2] == b"PK"
    from academicos.assessment.audit_log import get_audit_log
    from academicos.curriculum import routes as cr
    assert len(get_audit_log(cr._cfg.data_root).for_action("fee_defaulters_exported")) == 2


def test_only_the_fees_admin_sees_the_schools_fees(w):
    assert w.c.get("/api/v1/fees/overview", headers=w.t["ana"]).status_code == 403
    assert w.c.get("/api/v1/fees/defaulters/export", headers=w.stu).status_code == 403
    assert w.c.get("/api/v1/fees/overview", headers=w.p2).status_code == 404, "another school: its own (empty) year"
    g = w.c.post("/api/v1/admin/grants", json={"userId": w.uid["ana"], "capability": "fees"}, headers=w.p)
    assert g.status_code == 200, g.text
    assert w.c.get("/api/v1/fees/overview", headers=w.t["ana"]).status_code == 200


def test_parents_hear_before_a_fee_is_due_and_once_it_is_overdue(w):
    sid, mum = _parent(w)
    _head(w, "Science lab", 2_000_00, "2026-06-04")              # due in three days
    _head(w, "Tuition, term 1", 15_000_00, "2026-05-31")          # due yesterday
    paid = _head(w, "Sports", 500_00, "2026-06-04")
    assert _pay(w, sid, paid, 500_00).status_code == 200
    assert _run(datetime(2026, 6, 1, 9, 55, tzinfo=IST))["fee_reminders"] == "not yet"
    out = _run(datetime(2026, 6, 1, 10, 5, tzinfo=IST))
    assert out["fee_reminders"] == 2, out
    [soon] = _items(w, _h(mum), "fee_due_soon")
    assert soon["title"] == "Fee due 2026-06-04: Asha" and "Rs 2,000 for Science lab" in soon["body"]
    [late] = _items(w, _h(mum), "fee_overdue")
    assert "Rs 15,000 for Tuition, term 1" in late["body"]
    assert _items(w, w.stu, "fee_due_soon") == [], "the student is not chased"
    assert not any("Sports" in n["body"] for n in _items(w, _h(mum), "fee_due_soon")), "a paid fee is not chased"
    assert _run(datetime(2026, 6, 1, 11, 0, tzinfo=IST))["fee_reminders"] == "done"


def test_mondays_alert_counts_whats_overdue(w):
    _parent(w)
    _head(w, "Tuition, term 1", 15_000_00, "2026-05-15")
    out = _run(datetime(2026, 6, 1, 8, 5, tzinfo=IST))
    assert out["principal_alerts"] == 1, out
    [alert] = _items(w, w.p, "principal_alert")
    assert "Rs 15,000 in fees overdue from 1 students" in alert["body"]
