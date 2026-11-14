"""The cover desk runs itself where the school's rule says so (SCH-6, SCH-7,
NTF-2): a substitution nobody answers in time passes to the next teacher,
and owed lost periods are booked into make-up periods each afternoon, each
audited with the rule as the actor. With the rules off (the default) the
machine does neither. 2026-06-01 is a Monday."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from test_cover_routes import BASE, MON, _apply, w  # noqa: F401 - `w` is a fixture

IST = timezone(timedelta(hours=5, minutes=30))


def _policy(w, **over):
    body = {"autoApprove": False, "maxAutoDays": 2, "minNoticeDays": 0, "annualAllowanceDays": 12,
            "checkInGraceMinutes": 10, "checkInReminder": False, **over}
    r = w.c.put(f"{BASE}/staff-policy", json=body, headers=w.p)
    assert r.status_code == 200, r.text
    return r.json()


def _run(at: datetime) -> dict:
    from academicos.curriculum import routes as cr
    from academicos.operations import automations, routes as ops_routes
    return automations.run_due(ops_routes.store(), cr._require(), cr._require_users(), ops_routes.notify_safely, at)


def _notes(w, who, kind):
    return [n for n in w.c.get("/api/v1/notifications", headers=who).json()["items"] if n["kind"] == kind]


def _audit(action):
    from academicos.assessment.audit_log import get_audit_log
    from academicos.curriculum import routes as cr
    return get_audit_log(cr._cfg.data_root).for_action(action)


def _proposed_to_chitra(w) -> dict:
    """Ana's approved leave: 10-B period 2 (Science) is proposed to Chitra,
    asked at 07:30 IST."""
    leave = _apply(w, "ana").json()
    subs = w.c.post(f"{BASE}/leave-requests/{leave['id']}/decision", json={"approve": True},
                    headers=w.p).json()["substitutions"]
    duty = next(s for s in subs if s["sectionId"] == w.b10 and s["period"] == 2)
    assert duty["substituteId"] == w.uid["chitra"] and duty["status"] == "proposed"
    w.store._exec("UPDATE substitutions SET updated_at=? WHERE id=?", ("2026-06-01T02:00:00+00:00", duty["id"]))
    w.store._commit()
    return duty


def _lost_period(w) -> str:
    leave = _apply(w, "ana").json()
    subs = w.c.post(f"{BASE}/leave-requests/{leave['id']}/decision", json={"approve": True},
                    headers=w.p).json()["substitutions"]
    s = next(x for x in subs if x["sectionId"] == w.a10)
    r = w.c.post(f"{BASE}/substitutions/{s['id']}/assign", json={"mode": "lost", "note": "no one free"},
                 headers=w.p)
    assert r.status_code == 200 and r.json()["lostPeriod"]["status"] == "owed"
    return r.json()["lostPeriod"]["id"]


def test_the_rules_are_off_by_default_and_only_the_principal_sets_them(w):
    got = w.c.get(f"{BASE}/staff-policy", headers=w.t["ana"]).json()
    assert got["autoCompensate"] is False and got["substituteAnswerMinutes"] == 0
    assert w.c.put(f"{BASE}/staff-policy", json={"autoCompensate": True}, headers=w.t["ana"]).status_code == 403
    assert w.c.put(f"{BASE}/staff-policy", json={"substituteAnswerMinutes": 500}, headers=w.p).status_code == 422
    set_ = _policy(w, autoCompensate=True, substituteAnswerMinutes=20)
    assert set_["autoCompensate"] is True and set_["substituteAnswerMinutes"] == 20
    [entry] = _audit("staff_policy_set")
    assert entry["details"]["after"]["auto_compensate"] is True
    assert entry["details"]["before"]["substitute_answer_minutes"] == 0


def test_an_unanswered_substitution_passes_to_the_next_teacher(w):
    _policy(w, substituteAnswerMinutes=30)
    duty = _proposed_to_chitra(w)
    early = _run(datetime(2026, 6, 1, 7, 50, tzinfo=IST))           # 20 minutes: still Chitra's to answer
    assert early["substitution_timeout"] == 0
    out = _run(datetime(2026, 6, 1, 8, 10, tzinfo=IST))             # 40 minutes: passed on
    assert out["substitution_timeout"] == 2, out                    # Chitra told, the next teacher asked
    subs = w.c.get(f"{BASE}/substitutions", params={"from": MON, "to": MON}, headers=w.p).json()
    after = next(s for s in subs if s["id"] == duty["id"])
    assert after["status"] == "proposed" and after["substituteId"] not in (None, w.uid["chitra"])
    assert _notes(w, w.t["chitra"], "substitution_passed")
    nxt = {v: k for k, v in w.uid.items()}[after["substituteId"]]
    assert any(n["link"].endswith(MON) for n in _notes(w, w.t[nxt], "substitution_proposed"))
    late = w.c.post(f"{BASE}/substitutions/{duty['id']}/respond", json={"accept": True}, headers=w.t["chitra"])
    assert late.status_code == 409, "a late accept does not take the period back"
    [entry] = _audit("substitution_passed")
    assert entry["actor"] == "auto:school-rule" and entry["details"]["from"] == w.uid["chitra"]


def test_without_the_rule_a_silent_substitute_keeps_the_proposal(w):
    duty = _proposed_to_chitra(w)
    out = _run(datetime(2026, 6, 1, 9, 30, tzinfo=IST))
    assert out["substitution_timeout"] == 0
    subs = w.c.get(f"{BASE}/substitutions", params={"from": MON, "to": MON}, headers=w.p).json()
    assert next(s for s in subs if s["id"] == duty["id"])["substituteId"] == w.uid["chitra"]


def test_an_answered_proposal_is_not_passed(w):
    _policy(w, substituteAnswerMinutes=30)
    duty = _proposed_to_chitra(w)
    ok = w.c.post(f"{BASE}/substitutions/{duty['id']}/respond", json={"accept": True}, headers=w.t["chitra"])
    assert ok.status_code == 200
    w.store._exec("UPDATE substitutions SET updated_at=? WHERE id=?", ("2026-06-01T02:00:00+00:00", duty["id"]))
    w.store._commit()
    assert w.store.pass_unanswered(duty["id"], answered_before="2026-06-01T03:00:00+00:00") is None
    assert _run(datetime(2026, 6, 1, 9, 30, tzinfo=IST))["substitution_timeout"] == 0


def test_owed_lost_periods_are_booked_each_afternoon(w):
    lost_id = _lost_period(w)
    _policy(w, autoCompensate=True)
    assert _run(datetime(2026, 6, 1, 15, 55, tzinfo=IST))["auto_compensate"] == "not yet"
    out = _run(datetime(2026, 6, 1, 16, 5, tzinfo=IST))
    assert out["auto_compensate"] == 2, out                         # Ana and the principal
    [lp] = w.c.get(f"{BASE}/academic-years/{w.year}/lost-periods", headers=w.p).json()
    assert lp["id"] == lost_id and lp["status"] == "compensated" and lp["compensationDate"] > MON
    makeup = w.c.get(f"{BASE}/day", params={"date": lp["compensationDate"], "sectionId": w.a10}, headers=w.p).json()
    assert any(r["kind"] == "makeup" and r["period"] == lp["compensationPeriod"] for r in makeup)
    [teacher] = _notes(w, w.t["ana"], "makeup_scheduled")
    assert lp["compensationDate"] in teacher["body"] and MON in teacher["body"]
    [principal] = _notes(w, w.p, "makeups_booked")
    assert principal["title"] == "Make-up periods: 1 booked" and "Science" in principal["body"]
    [entry] = _audit("lost_period_compensated")
    assert entry["actor"] == "auto:school-rule" and entry["details"]["lostPeriodId"] == lost_id
    assert _run(datetime(2026, 6, 1, 16, 30, tzinfo=IST))["auto_compensate"] == "done"


def test_without_the_rule_lost_periods_wait_for_the_principal(w):
    _lost_period(w)
    assert _run(datetime(2026, 6, 1, 16, 5, tzinfo=IST))["auto_compensate"] == 0
    [lp] = w.c.get(f"{BASE}/academic-years/{w.year}/lost-periods", headers=w.p).json()
    assert lp["status"] == "owed"


def test_a_lost_period_is_booked_once(w):
    """The status is the claim: a second booking of the same lost period
    (the principal after the rule, or a second instance) is refused."""
    from academicos.curriculum.cover import CoverError
    lost_id = _lost_period(w)
    [(on, period), (on2, period2), *_] = w.store.compensation_options(lost_id, today=MON)
    w.store.compensate(lost_id, on=on, period=period, today=MON)
    try:
        w.store.compensate(lost_id, on=on2, period=period2, today=MON)
    except CoverError:
        pass
    else:
        raise AssertionError("a settled lost period was booked twice")
