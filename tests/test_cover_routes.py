"""Leave, substitution and compensation through the HTTP routes, as the
principal, the teachers and a student of one school (and a second school's
principal for the scoping checks). 2026-06-01 is a Monday."""
from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest

from _auth_helpers import register_invited
from test_assessment_routes_auth import _boot_client, _register

BASE = "/api/v1/curriculum"
MON = "2026-06-01"
BELL = [{"start": f"{8 + i}:00".zfill(5), "end": f"{8 + i}:45".zfill(5)} for i in range(8)]


def _h(u):
    return {"Authorization": f"Bearer {u['token']}"}


@pytest.fixture
def w(tmp_path, monkeypatch):
    from academicos.curriculum import routes as cr
    with _boot_client(tmp_path, monkeypatch) as c:
        p = _register(c, "school_1", "p1@example.com", "Priya", principal_key="test-bootstrap-key")
        p2 = _register(c, "school_2", "p2@example.com", "Ravi", principal_key="test-bootstrap-key")
        users = {n: _register(c, "school_1", f"{n}@example.com", n.title()) for n in ("ana", "bala", "chitra", "dev")}
        stu = register_invited(c, "school_1", "s1@example.com", name="Asha", role="student")
        monkeypatch.setattr(cr, "_school_today", lambda: date(2026, 6, 1))
        store = cr._require()
        year = store.create_academic_year(school_id="school_1", label="2026-27", start_date="2026-04-01",
                                          end_date="2027-03-31")
        store.create_calendar(academic_year_id=year.id, weekly_off_days=["sunday"], alternate_saturday_rule="none")
        store.create_bell_schedule(academic_year_id=year.id, name="Main", slots=BELL)
        g10 = store.create_grade(academic_year_id=year.id, number=10)
        g9 = store.create_grade(academic_year_id=year.id, number=9)
        [a10] = store.sections_for_grade(g10.id)
        b10 = store.create_section(grade_id=g10.id, name="B")
        [a9] = store.sections_for_grade(g9.id)
        sci10 = store.create_subject(grade_id=g10.id, name="Science")
        mat10 = store.create_subject(grade_id=g10.id, name="Maths")
        sci9 = store.create_subject(grade_id=g9.id, name="Science")
        mat9 = store.create_subject(grade_id=g9.id, name="Maths")
        uid = {n: u["user"]["id"] for n, u in users.items()}
        for sec, subj, t in ((a10, sci10, "ana"), (b10, sci10, "ana"), (a10, mat10, "bala"), (b10, mat10, "bala"),
                             (a9, sci9, "chitra"), (a9, mat9, "dev")):
            store.set_allocation(section_id=sec.id, subject_id=subj.id, teacher_id=uid[t], periods_per_week=6)
        for sid, rows in {a10.id: [(1, sci10), (2, mat10)], b10.id: [(1, mat10), (2, sci10)],
                          a9.id: [(1, sci9), (3, mat9)]}.items():
            store.replace_section_timetable(sid, [{"day_of_week": 0, "period": p, "subject_id": s.id}
                                                  for p, s in rows])
        store.enroll_student(school_id="school_1", student_id=stu["user"]["id"], section_id=b10.id)
        yield SimpleNamespace(c=c, p=_h(p), p2=_h(p2), stu=_h(stu), year=year.id, uid=uid,
                              t={n: _h(u) for n, u in users.items()}, a10=a10.id, b10=b10.id, a9=a9.id,
                              sci10=sci10.id, store=store)


def _apply(w, who, **body):
    body = {"startDate": MON, "endDate": MON, "reason": "unwell", **body}
    headers = who if isinstance(who, dict) else w.t[who]
    return w.c.post(f"{BASE}/leave-requests", json=body, headers=headers)


def test_leave_to_accepted_substitution_end_to_end(w):
    r = _apply(w, "ana", handoverNote="Chapter 3 worksheet on my desk")
    assert r.status_code == 200, r.text
    leave = r.json()
    assert leave["status"] == "pending" and leave["teacherId"] == w.uid["ana"]
    mine = w.c.get(f"{BASE}/leave-requests", headers=w.t["ana"]).json()
    assert [l["id"] for l in mine] == [leave["id"]]
    assert w.c.post(f"{BASE}/leave-requests/{leave['id']}/decision", json={"approve": True},
                    headers=w.t["bala"]).status_code == 403
    d = w.c.post(f"{BASE}/leave-requests/{leave['id']}/decision", json={"approve": True}, headers=w.p).json()
    assert d["leave"]["status"] == "approved"
    subs = {(s["sectionId"], s["period"]): s for s in d["substitutions"]}
    duty = subs[(w.b10, 2)]
    assert duty["substituteId"] == w.uid["chitra"] and duty["status"] == "proposed"
    cands = w.c.get(f"{BASE}/substitutions/{duty['id']}/candidates", headers=w.p).json()
    assert cands[0]["teacherId"] == w.uid["chitra"] and cands[0]["qualified"] is True
    # Chitra sees the duty in her list and in her day; she accepts.
    chitra_duties = w.c.get(f"{BASE}/substitutions", params={"from": MON, "to": MON},
                            headers=w.t["chitra"]).json()
    assert [s["id"] for s in chitra_duties] == [duty["id"]]
    day = w.c.get(f"{BASE}/my-day", params={"date": MON}, headers=w.t["chitra"]).json()
    assert {(r["sectionId"], r["kind"]) for r in day} == {(w.a9, "regular"), (w.b10, "substitute")}
    assert w.c.post(f"{BASE}/substitutions/{duty['id']}/respond", json={"accept": True},
                    headers=w.t["dev"]).status_code == 409
    ok = w.c.post(f"{BASE}/substitutions/{duty['id']}/respond", json={"accept": True}, headers=w.t["chitra"])
    assert ok.status_code == 200 and ok.json()["status"] == "accepted"
    # Ana's day shows her periods away; the class sees who is taking them.
    assert {r["kind"] for r in w.c.get(f"{BASE}/my-day", params={"date": MON}, headers=w.t["ana"]).json()} == {"away"}
    student = w.c.get(f"{BASE}/my-day", params={"date": MON}, headers=w.stu).json()
    assert [(r["period"], r["kind"]) for r in student] == [(1, "regular"), (2, "substitute")]


def test_a_teacher_with_no_class_is_offered_for_cover_last(w):
    """v3 audit N-3-16: the librarian, registered as a teacher with no
    allocation, was in no candidate list."""
    lata = _register(w.c, "school_1", "lata@example.com", "Lata")["user"]["id"]
    leave = _apply(w, "ana").json()
    subs = w.c.post(f"{BASE}/leave-requests/{leave['id']}/decision", json={"approve": True},
                    headers=w.p).json()["substitutions"]
    s = next(x for x in subs if x["sectionId"] == w.a10)
    cands = w.c.get(f"{BASE}/substitutions/{s['id']}/candidates", headers=w.p).json()
    assert [c["teacherId"] for c in cands] == [w.uid["dev"], lata]
    r = w.c.post(f"{BASE}/substitutions/{s['id']}/assign", json={"substituteId": lata}, headers=w.p)
    assert r.status_code == 200, r.text
    assert r.json()["substitution"]["mode"] == "supervised" and r.json()["lostPeriod"]["status"] == "owed"


def test_only_the_principal_applies_for_someone_else(w):
    assert _apply(w, "bala", teacherId=w.uid["ana"]).status_code == 403
    r = _apply(w, w.p, teacherId=w.uid["ana"], reason="called in sick at 7am")
    assert r.status_code == 200 and r.json()["teacherId"] == w.uid["ana"]
    assert r.json()["createdBy"] != w.uid["ana"]


def test_a_period_run_without_a_substitute_is_owed_and_made_up(w):
    leave = _apply(w, "ana").json()
    subs = w.c.post(f"{BASE}/leave-requests/{leave['id']}/decision", json={"approve": True},
                    headers=w.p).json()["substitutions"]
    s = next(x for x in subs if x["sectionId"] == w.a10)
    r = w.c.post(f"{BASE}/substitutions/{s['id']}/assign", json={"mode": "lost", "note": "no one free"},
                 headers=w.p)
    assert r.status_code == 200 and r.json()["lostPeriod"]["status"] == "owed"
    lost_id = r.json()["lostPeriod"]["id"]
    owed = w.c.get(f"{BASE}/academic-years/{w.year}/lost-periods", params={"status": "owed"}, headers=w.p).json()
    assert [l["id"] for l in owed] == [lost_id]
    options = w.c.get(f"{BASE}/lost-periods/{lost_id}/compensation-options", headers=w.p).json()
    assert options
    first = options[0]
    done = w.c.post(f"{BASE}/lost-periods/{lost_id}/compensate", json=first, headers=w.p)
    assert done.status_code == 200 and done.json()["status"] == "compensated"
    makeup = w.c.get(f"{BASE}/day", params={"date": first["date"], "sectionId": w.a10}, headers=w.p).json()
    assert any(r["kind"] == "makeup" for r in makeup)
    summary = w.c.get(f"{BASE}/academic-years/{w.year}/cover-summary", params={"from": MON, "to": "2026-06-30"},
                      headers=w.p).json()
    assert summary["lost"] == 1 and summary["compensated"] == 1 and summary["owed"] == 0


def test_a_closure_owes_the_days_periods_and_takes_the_day_off_the_calendar(w):
    r = w.c.post(f"{BASE}/academic-years/{w.year}/closures", json={"date": MON, "reason": "heavy rain"}, headers=w.p)
    assert r.status_code == 200, r.text
    assert r.json()["lostPeriods"] == 6 and r.json()["holidayAdded"] is True
    assert w.c.get(f"{BASE}/day", params={"date": MON}, headers=w.p).json() == [], "no longer a working day"
    assert len(w.c.get(f"{BASE}/academic-years/{w.year}/lost-periods", headers=w.p).json()) == 6


def test_a_closure_of_some_classes_owes_only_their_periods_and_keeps_the_calendar(w):
    r = w.c.post(f"{BASE}/academic-years/{w.year}/closures",
                 json={"date": MON, "reason": "class 10 trip", "sectionIds": [w.a10, w.b10]}, headers=w.p)
    assert r.status_code == 200, r.text
    assert r.json()["lostPeriods"] == 4 and r.json()["holidayAdded"] is False
    lost = w.c.get(f"{BASE}/academic-years/{w.year}/lost-periods", headers=w.p).json()
    assert {l["sectionId"] for l in lost} == {w.a10, w.b10}
    day = w.c.get(f"{BASE}/day", params={"date": MON, "sectionId": w.a9}, headers=w.p).json()
    assert {r["kind"] for r in day} == {"regular"}, "class 9 still teaches that day"
    other_year = w.store.create_academic_year(school_id="school_2", label="x", start_date="2026-04-01",
                                              end_date="2027-03-31")
    [foreign] = w.store.sections_for_grade(w.store.create_grade(academic_year_id=other_year.id, number=10).id)
    assert w.c.post(f"{BASE}/academic-years/{w.year}/closures",
                    json={"date": MON, "reason": "x", "sectionIds": [foreign.id]}, headers=w.p).status_code == 403
    assert w.c.post(f"{BASE}/academic-years/{w.year}/closures",
                    json={"date": MON, "reason": "x", "sectionIds": []}, headers=w.p).status_code == 422


def test_a_waived_period_keeps_its_reason_in_the_audit_log(w):
    from academicos.assessment.audit_log import get_audit_log
    from academicos.curriculum import routes as cr
    lost = w.store.declare_closure(w.year, MON, reason="rain", section_ids={w.a10})
    assert len(lost) == 2
    r = w.c.post(f"{BASE}/lost-periods/{lost[0].id}/waive", json={"reason": "covered in the revision week"},
                 headers=w.p)
    assert r.status_code == 200 and r.json()["status"] == "waived"
    [entry, *_] = get_audit_log(cr._cfg.data_root).for_action("lost_period_waived")
    assert entry["details"]["reason"] == "covered in the revision week"
    assert w.c.post(f"{BASE}/lost-periods/{lost[1].id}/waive", json={"reason": ""},
                    headers=w.p).status_code == 422
    assert w.c.post(f"{BASE}/lost-periods/{lost[1].id}/waive", headers=w.p).status_code == 200, \
        "the reason is optional for callers that send none"


def test_gates_and_scoping(w):
    leave = _apply(w, "ana").json()
    assert w.c.post(f"{BASE}/leave-requests/{leave['id']}/decision", json={"approve": True},
                    headers=w.p2).status_code == 403
    assert w.c.get(f"{BASE}/academic-years/{w.year}/cover-summary", params={"from": MON, "to": MON},
                   headers=w.t["ana"]).status_code == 403
    assert w.c.get(f"{BASE}/day", params={"date": MON, "sectionId": w.a10}, headers=w.stu).status_code == 403
    assert w.c.get(f"{BASE}/leave-requests", headers=w.stu).status_code == 403
    assert w.c.post(f"{BASE}/academic-years/{w.year}/closures", json={"date": MON, "reason": "x"},
                    headers=w.t["ana"]).status_code == 403
    # A teacher cancels her own leave; not somebody else's.
    assert w.c.post(f"{BASE}/leave-requests/{leave['id']}/cancel", headers=w.t["bala"]).status_code == 403
    assert w.c.post(f"{BASE}/leave-requests/{leave['id']}/cancel", headers=w.t["ana"]).json()["status"] == "cancelled"
