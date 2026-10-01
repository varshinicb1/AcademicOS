"""A lost period moves the lesson planned in it, and a make-up period
teaches one (v3 audit N-3-10). The cover engine never touched the lesson
plan: 10-A Science's period lost on 2026-10-05 left its lesson 'scheduled'
that day, and a make-up on 2026-10-08 still had 1 lesson that day.

test_cover_routes' world: 2026-06-01 (MON) is a Monday and "today". 10-A has
Science (Ana) in period 1 on Mondays only, so its Science plan has one
lesson each Monday. Approving Ana's leave puts Dev (Maths) on that period:
he only supervises, so it is a lost period (N-3-9).
"""
from __future__ import annotations

from academicos.curriculum import scheduling

from test_cover_exams import _dates, _decide, _science_book
from test_cover_routes import BASE, MON, _apply, w  # noqa: F401 - `w` is a fixture

MONDAYS = ["2026-06-01", "2026-06-08", "2026-06-15", "2026-06-22", "2026-06-29", "2026-07-06"]


def _plan(w, *sections) -> str:
    book = _science_book(w)
    for section in sections:
        scheduling.schedule_book(w.store, school_id="school_1", academic_year_id=w.year, book_id=book,
                                 periods_per_week=1, from_date=MON, section_id=section)
        assert _dates(w, book, section) == MONDAYS
    return book


def _monday_lessons(w, who: str) -> list[str]:
    r = w.c.get(f"{BASE}/my-schedule", params={"start_date": MON, "end_date": MON}, headers=w.t[who])
    assert r.status_code == 200, r.text
    return sorted(l["sectionId"] for l in r.json())


def test_a_lost_period_moves_its_lesson_on_and_a_make_up_period_teaches_one(w):
    book = _plan(w, w.a10, w.b10)
    assert _monday_lessons(w, "ana") == sorted([w.a10, w.b10])
    subs = _decide(w, _apply(w, "ana").json())
    assert subs[(w.a10, 1)]["mode"] == "supervised"
    assert _dates(w, book, w.a10) == MONDAYS[1:] + ["2026-07-13"], "the lost period's lesson is taught next Monday"
    assert _dates(w, book, w.b10) == MONDAYS, "Chitra teaches 10-B's Science: nothing was lost there"
    assert _monday_lessons(w, "ana") == [w.b10]

    [lost] = w.c.get(f"{BASE}/academic-years/{w.year}/lost-periods", headers=w.p).json()
    first = w.c.get(f"{BASE}/lost-periods/{lost['id']}/compensation-options", headers=w.p).json()[0]
    assert first == {"date": "2026-06-02", "period": 1}
    r = w.c.post(f"{BASE}/lost-periods/{lost['id']}/compensate", json=first, headers=w.p)
    assert r.status_code == 200, r.text
    assert _dates(w, book, w.a10) == ["2026-06-02"] + MONDAYS[1:], \
        "the make-up teaches the next lesson and the plan catches up"

    # Every move is on the lesson's record, with why.
    from academicos.assessment.audit_log import get_audit_log
    from academicos.curriculum import routes as cr
    reasons = {e["details"]["reason"] for e in get_audit_log(cr._cfg.data_root).for_action(
        scheduling.RESCHEDULE_ACTION)}
    assert any(x.startswith("period 1 on 2026-06-01 lost") for x in reasons)
    assert any(x.startswith("make-up period 1 on 2026-06-02") for x in reasons)


def test_a_period_taught_after_all_gives_the_lesson_back(w):
    book = _plan(w, w.a10)
    leave = _apply(w, "ana").json()
    _decide(w, leave)
    assert _dates(w, book, w.a10)[0] == "2026-06-08"
    r = w.c.post(f"{BASE}/leave-requests/{leave['id']}/cancel", headers=w.t["ana"])
    assert r.status_code == 200, r.text
    assert _dates(w, book, w.a10) == MONDAYS


def test_a_closure_moves_a_section_plan_one_teaching_day_not_two(w):
    """The closure adds the holiday, so the day is already off the plan's
    periods. PUSH then skipped the next Monday as well, for every section
    plan with a lesson that day."""
    book = _plan(w, w.a10)
    r = w.c.post(f"{BASE}/academic-years/{w.year}/closures", json={"date": MON, "reason": "heavy rain"},
                 headers=w.p)
    assert r.status_code == 200 and r.json()["plansReflowed"] == 1, r.text
    assert _dates(w, book, w.a10) == MONDAYS[1:] + ["2026-07-13"]


def test_a_closure_of_some_classes_moves_their_plans_one_teaching_day(w):
    book = _plan(w, w.a10, w.b10)
    r = w.c.post(f"{BASE}/academic-years/{w.year}/closures",
                 json={"date": MON, "reason": "class 10-A trip", "sectionIds": [w.a10]}, headers=w.p)
    assert r.status_code == 200 and r.json()["plansReflowed"] == 1, r.text
    assert _dates(w, book, w.a10) == MONDAYS[1:] + ["2026-07-13"]
    assert _dates(w, book, w.b10) == MONDAYS
