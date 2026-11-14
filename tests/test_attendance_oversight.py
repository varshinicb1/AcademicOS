"""ATT-1 oversight for the principal (ADM-2, ADM-3, NTF-2): one view of the
day's registers across the school and of who is below the attendance floor
this year; a reports admin sees only their classes; at 11:00 a class with no
register reminds its class teacher and the principal hears once; on Monday
the morning alert counts the students below the floor. Uses the cover
fixture: Asha is the only student, in 10-B; 2026-06-01 is a Monday and the
school's today."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from test_cover_routes import w  # noqa: F401 - `w` is a fixture

IST = timezone(timedelta(hours=5, minutes=30))
URL = "/api/v1/admin/attendance/overview"
TODAY = "2026-06-01"


def _asha(w):
    return w.c.get("/api/v1/auth/me", headers=w.stu).json()["id"]


def _past_register(w, sid, absent: int, present: int):
    """Asha's register on the school days before today, absent first."""
    from academicos.operations import routes as ops_routes
    ops = ops_routes.store()
    day, done = date(2026, 5, 30), 0
    while done < absent + present:
        if day.weekday() != 6:                                  # Sunday is the weekly off
            status = "absent" if done < absent else "present"
            ops.mark_attendance(school_id="school_1", section_id=w.b10, on=day.isoformat(),
                                entries=[(sid, status, "")], marked_by=w.uid["ana"])
            done += 1
        day -= timedelta(days=1)


def _run(at):
    from academicos.curriculum import routes as cr
    from academicos.operations import automations, routes as ops_routes
    return automations.run_due(ops_routes.store(), cr._require(), cr._require_users(), ops_routes.notify_safely, at)


def _items(w, headers, kind):
    return [i for i in w.c.get("/api/v1/notifications", headers=headers).json()["items"] if i["kind"] == kind]


def test_the_principal_sees_the_days_registers_and_who_is_below_the_floor(w):
    sid = _asha(w)
    _past_register(w, sid, absent=4, present=6)                 # 60% over 10 days
    r = w.c.get(URL, headers=w.p)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["date"] == TODAY and body["floor"] == 75 and body["yearStart"] == "2026-04-01"
    rows = {s["sectionName"]: s for s in body["sections"]}
    assert set(rows) == {"10-A", "10-B", "9-A"}
    assert rows["10-B"]["enrolled"] == 1 and rows["10-B"]["taken"] is False and rows["10-B"]["yearPercent"] == 60.0
    assert rows["10-A"]["enrolled"] == 0 and rows["10-A"]["yearPercent"] is None
    assert body["notTaken"] == 1, "a class with no students needs no register"
    [low] = body["belowFloor"]
    assert (low["name"], low["sectionName"], low["percent"], low["daysTaken"]) == ("Asha", "10-B", 60.0, 10)
    assert body["belowFloorTotal"] == 1
    # an earlier day reads that day's register
    past = w.c.get(URL, params={"date": "2026-05-30"}, headers=w.p).json()
    assert {s["sectionName"]: s for s in past["sections"]}["10-B"]["counts"]["absent"] == 1
    assert past["awayToday"] == 1
    from academicos.assessment.audit_log import PII_READ_ACTION, get_audit_log
    from academicos.curriculum import routes as cr
    reads = [e for e in get_audit_log(cr._cfg.data_root).for_action(PII_READ_ACTION)
             if e["details"].get("what") == "attendance_below_floor"]
    assert reads and reads[0]["actor"] == w.uid.get("p1", reads[0]["actor"]), "naming students is a logged read"


def test_too_few_days_names_nobody_and_good_attendance_is_not_named(w):
    sid = _asha(w)
    _past_register(w, sid, absent=3, present=2)                 # 40%, but only 5 days
    assert w.c.get(URL, headers=w.p).json()["belowFloor"] == []
    _past_register(w, sid, absent=0, present=10)                # the same days and more, now 80%
    assert w.c.get(URL, headers=w.p).json()["belowFloor"] == []


def test_a_reports_admin_sees_only_their_classes_and_others_none(w):
    sid = _asha(w)
    _past_register(w, sid, absent=4, present=6)
    assert w.c.get(URL, headers=w.t["chitra"]).status_code == 403
    assert w.c.get(URL, headers=w.stu).status_code == 403
    g = w.c.post("/api/v1/admin/grants", json={"userId": w.uid["chitra"], "capability": "reports",
                                               "scope": {"grades": [9]}}, headers=w.p)
    assert g.status_code == 200, g.text
    mine = w.c.get(URL, headers=w.t["chitra"]).json()
    assert [s["sectionName"] for s in mine["sections"]] == ["9-A"]
    assert mine["belowFloor"] == [] and mine["belowFloorTotal"] == 0, "Asha is in 10-B, outside the grant"
    assert w.c.get(URL, headers=w.p2).status_code == 404, "another school has no year here, and sees nothing"
    assert w.c.get(URL, params={"date": "June"}, headers=w.p).status_code == 422


def test_at_eleven_a_class_with_no_register_is_chased_once(w):
    sid = _asha(w)
    w.store.update_section(w.b10, class_teacher_id=w.uid["bala"])
    assert _run(datetime(2026, 6, 1, 10, 55, tzinfo=IST))["attendance_not_taken"] == "not yet"
    out = _run(datetime(2026, 6, 1, 11, 5, tzinfo=IST))
    assert out["attendance_not_taken"] == 2, out                # Bala, and the principal
    [mine] = _items(w, w.t["bala"], "register_not_taken")
    assert "10-B" in mine["title"] and mine["link"] == "/school/attendance"
    [boss] = _items(w, w.p, "registers_missing")
    assert boss["title"] == "No register yet: 1 classes" and "10-B" in boss["body"] and "reminded" in boss["body"]
    assert _run(datetime(2026, 6, 1, 11, 30, tzinfo=IST))["attendance_not_taken"] == "done"
    # a register taken before 11:00 the next school day means nobody is chased
    from academicos.operations import routes as ops_routes
    ops_routes.store().mark_attendance(school_id="school_1", section_id=w.b10, on="2026-06-02",
                                       entries=[(sid, "present", "")], marked_by=w.uid["bala"])
    assert _run(datetime(2026, 6, 2, 11, 5, tzinfo=IST))["attendance_not_taken"] == 0


def test_without_a_class_teacher_the_principal_is_told_nobody_was_reminded(w):
    _asha(w)
    out = _run(datetime(2026, 6, 1, 11, 5, tzinfo=IST))
    assert out["attendance_not_taken"] == 1, out
    [boss] = _items(w, w.p, "registers_missing")
    assert "no class teacher" in boss["body"]


def test_no_chasing_on_a_sunday(w):
    _asha(w)
    assert _run(datetime(2026, 6, 7, 11, 5, tzinfo=IST))["attendance_not_taken"] == 0


def test_mondays_alert_counts_students_below_the_floor(w):
    sid = _asha(w)
    _past_register(w, sid, absent=4, present=6)
    out = _run(datetime(2026, 6, 1, 8, 5, tzinfo=IST))
    assert out["principal_alerts"] == 1, out
    [alert] = _items(w, w.p, "principal_alert")
    assert "1 students below 75% attendance this year" in alert["body"]
