"""Leave -> substitution -> compensation (SCH-5..7), with the SCH-8 edge cases
each as a test. Store level, on a small school:

  10-A, 10-B, 9-A on one bell (8 periods, Monday to Saturday).
  Ana teaches Science to 10-A and 10-B; Bala teaches Maths to 10-A and 10-B;
  Chitra teaches Science to 9-A; Dev teaches Maths to 9-A.

2026-06-01 is a Monday.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from academicos.curriculum.cover import CoverError
from academicos.curriculum.store import CurriculumStore

MON, TUE = "2026-06-01", "2026-06-02"
BELL = [{"start": f"{8 + i}:00".zfill(5), "end": f"{8 + i}:45".zfill(5)} for i in range(8)]


@pytest.fixture
def s(tmp_path):
    store = CurriculumStore(tmp_path / "curriculum.sqlite")
    yield store
    store.close()


def _school(store):
    year = store.create_academic_year(school_id="s1", label="2026-27", start_date="2026-04-01",
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
    for sec, subj, t in ((a10, sci10, "ana"), (b10, sci10, "ana"), (a10, mat10, "bala"), (b10, mat10, "bala"),
                         (a9, sci9, "chitra"), (a9, mat9, "dev")):
        store.set_allocation(section_id=sec.id, subject_id=subj.id, teacher_id=t, periods_per_week=6)
    # Monday: Ana 10-A p1, 10-B p2; Bala 10-A p2, 10-B p1; Chitra 9-A p1; Dev 9-A p3.
    week = {a10.id: [(0, 1, sci10), (0, 2, mat10)], b10.id: [(0, 1, mat10), (0, 2, sci10)],
            a9.id: [(0, 1, sci9), (0, 3, mat9)]}
    for sid, rows in week.items():
        store.replace_section_timetable(sid, [{"day_of_week": d, "period": p, "subject_id": subj.id}
                                              for d, p, subj in rows])
    return SimpleNamespace(year=year.id, a10=a10.id, b10=b10.id, a9=a9.id, sci10=sci10.id, mat10=mat10.id,
                           sci9=sci9.id, mat9=mat9.id)


def _leave(store, w, teacher, start=MON, end=MON, kind="full_day", **kw):
    return store.apply_for_leave(school_id="s1", academic_year_id=w.year, teacher_id=teacher, start_date=start,
                                 end_date=end, kind=kind, reason="unwell", created_by=teacher, **kw)


def _by_slot(subs):
    return {(x.section_id, x.period): x for x in subs}


def test_approving_leave_opens_a_substitution_for_every_missed_period(s):
    w = _school(s)
    leave = _leave(s, w, "ana")
    assert leave.status == "pending"
    leave, subs = s.decide_leave(leave.id, approve=True, decided_by="p1")
    assert leave.status == "approved"
    slots = _by_slot(subs)
    assert set(slots) == {(w.a10, 1), (w.b10, 2)}
    # 10-A period 1: Chitra teaches Science but is in 9-A then; Dev is free but
    # does not teach Science; Bala is in 10-B. So Dev, supervising.
    assert slots[(w.a10, 1)].substitute_id == "dev"
    # 10-B period 2: Chitra is free and teaches Science (another class): she ranks first.
    assert slots[(w.b10, 2)].substitute_id == "chitra"
    cands = s.substitute_candidates(slots[(w.b10, 2)].id)
    assert cands[0].teacher_id == "chitra" and cands[0].qualified
    assert "teaches Science" in cands[0].reasons


def test_a_subject_run_by_someone_who_does_not_teach_it_is_a_lost_period(s):
    w = _school(s)
    _, subs = s.decide_leave(_leave(s, w, "ana").id, approve=True, decided_by="p1")
    first = _by_slot(subs)[(w.a10, 1)]
    sub, lost = s.assign_substitute(first.id, substitute_id="dev")      # Dev teaches Maths
    assert sub.mode == "supervised" and lost is not None and lost.subject_id == w.sci10
    assert s.lost_periods_for_year(w.year, "owed")[0].id == lost.id


def test_two_teachers_absent_in_the_same_period_get_two_different_people(s):
    w = _school(s)
    _, ana_subs = s.decide_leave(_leave(s, w, "ana").id, approve=True, decided_by="p1")
    _, bala_subs = s.decide_leave(_leave(s, w, "bala").id, approve=True, decided_by="p1")
    period1 = [x for x in ana_subs + bala_subs if x.period == 1]
    assert len(period1) == 2
    takers = [x.substitute_id for x in period1]
    assert len(set(t for t in takers if t)) == len([t for t in takers if t]), takers


def test_no_free_teacher_leaves_it_open_and_a_passed_day_makes_it_lost(s):
    w = _school(s)
    for t in ("chitra", "dev", "bala"):
        s.decide_leave(_leave(s, w, t).id, approve=True, decided_by="p1")
    _, subs = s.decide_leave(_leave(s, w, "ana").id, approve=True, decided_by="p1")
    assert all(x.status == "open" and x.substitute_id is None for x in subs), [(x.status, x.substitute_id) for x in subs]
    assert s.settle_past_uncovered(w.year, today=TUE) >= 2
    reasons = {l.reason for l in s.lost_periods_for_year(w.year)}
    assert "no substitute" in reasons


def test_a_substitute_who_goes_on_leave_later_hands_the_duty_on(s):
    w = _school(s)
    _, subs = s.decide_leave(_leave(s, w, "ana").id, approve=True, decided_by="p1")
    duty = _by_slot(subs)[(w.b10, 2)]
    assert duty.substitute_id == "chitra"
    s.respond_to_substitution(duty.id, teacher_id="chitra", accept=True)
    # Chitra is called away for period 2 only.
    _, reopened = s.decide_leave(_leave(s, w, "chitra", kind="periods", periods=[2]).id, approve=True,
                                 decided_by="p1")
    [again] = [x for x in reopened if x.id == duty.id]
    assert again.substitute_id not in (None, "chitra")


def test_a_decline_passes_the_period_to_the_next_candidate(s):
    w = _school(s)
    _, subs = s.decide_leave(_leave(s, w, "ana").id, approve=True, decided_by="p1")
    duty = _by_slot(subs)[(w.b10, 2)]
    after = s.respond_to_substitution(duty.id, teacher_id="chitra", accept=False)
    assert after.substitute_id not in (None, "chitra") and after.status == "proposed"
    with pytest.raises(CoverError):
        s.respond_to_substitution(duty.id, teacher_id="chitra", accept=True)


def test_a_half_day_leave_covers_only_its_half(s):
    w = _school(s)
    leave = _leave(s, w, "dev", kind="second_half")        # Dev teaches 9-A p3: first half
    _, subs = s.decide_leave(leave.id, approve=True, decided_by="p1")
    assert subs == []
    leave = _leave(s, w, "chitra", kind="first_half")      # Chitra 9-A p1: first half
    _, subs = s.decide_leave(leave.id, approve=True, decided_by="p1")
    assert [(x.section_id, x.period) for x in subs] == [(w.a9, 1)]


def test_a_closure_at_short_notice_makes_every_periods_debt_and_cancels_the_days_cover(s):
    w = _school(s)
    s.decide_leave(_leave(s, w, "ana").id, approve=True, decided_by="p1")
    lost = s.declare_closure(w.year, MON, reason="rain")
    assert len(lost) == 6                                  # every Monday entry of the three sections
    assert all(x.status == "cancelled" for x in s.substitutions_between(w.year, MON, MON))


def test_a_lost_period_is_made_up_in_a_free_period_and_the_debt_clears(s):
    w = _school(s)
    [lp, *_] = s.declare_closure(w.year, MON, reason="rain")
    options = s.compensation_options(lp.id, today=MON)
    assert options and all(d > MON for d, _ in options)
    day, period = options[0]
    # 10-A's own periods that weekday are not offered.
    taken = {e.period for e in s.timetable_for_section(lp.section_id)
             if e.day_of_week == __import__("datetime").date.fromisoformat(day).weekday()}
    assert period not in taken
    done = s.compensate(lp.id, on=day, period=period, today=MON)
    assert done.status == "compensated"
    view = s.day_view(w.year, day, section_id=lp.section_id)
    assert any(r["kind"] == "makeup" and r["period"] == period for r in view)
    summary = s.cover_summary(w.year, MON, "2026-06-30")
    assert summary["compensated"] == 1 and summary["owed"] == len(s.lost_periods_for_year(w.year)) - 1
    with pytest.raises(CoverError):
        s.compensate(lp.id, on=day, period=period, today=MON)


def test_the_day_view_shows_the_absent_teacher_away_and_the_substitute_on_duty(s):
    w = _school(s)
    _, subs = s.decide_leave(_leave(s, w, "ana").id, approve=True, decided_by="p1")
    ana = s.day_view(w.year, MON, teacher_id="ana")
    assert ana and all(r["kind"] == "away" for r in ana)
    chitra = s.day_view(w.year, MON, teacher_id="chitra")
    assert {(r["sectionId"], r["period"], r["kind"]) for r in chitra} == {
        (w.a9, 1, "regular"), (w.b10, 2, "substitute")}
    section = s.day_view(w.year, MON, section_id=w.b10)
    assert [r["kind"] for r in section] == ["regular", "substitute"]
    assert s.day_view(w.year, "2026-06-07", section_id=w.b10) == [], "a Sunday is not a working day"


def test_leave_is_checked(s):
    w = _school(s)
    with pytest.raises(CoverError, match="ends before"):
        _leave(s, w, "ana", start=TUE, end=MON)
    with pytest.raises(CoverError, match="outside this academic year"):
        _leave(s, w, "ana", start="2027-05-01", end="2027-05-01")
    with pytest.raises(CoverError, match="name the periods"):
        _leave(s, w, "ana", kind="periods")
    _leave(s, w, "ana")
    with pytest.raises(CoverError, match="overlaps"):
        _leave(s, w, "ana")


# ---- v3 audit N-3-9: the engine's own pick who does not teach the subject ----

def test_the_engines_pick_who_does_not_teach_the_subject_supervises_and_the_period_is_owed(s):
    """Approving Ana's leave puts Dev (Maths) on 10-A's Science period, the
    only one free. He supervises: Science is not taught, so the period is
    owed, and the summary does not call it filled. Until N-3-9 the engine's
    pick was filed 'substitute' whoever it was, counted as filled, and
    never owed (8 of 24 in the audit's school)."""
    w = _school(s)
    _, subs = s.decide_leave(_leave(s, w, "ana").id, approve=True, decided_by="p1")
    by = _by_slot(subs)
    dev = by[(w.a10, 1)]
    assert (dev.substitute_id, dev.status, dev.mode) == ("dev", "proposed", "supervised")
    assert by[(w.b10, 2)].mode == "substitute", "Chitra teaches Science"
    [owed] = s.lost_periods_for_year(w.year, "owed")
    assert (owed.section_id, owed.subject_id, owed.period, owed.source_id) == (w.a10, w.sci10, 1, dev.id)
    summary = s.cover_summary(w.year, MON, MON)
    assert (summary["substitutionsRequested"], summary["filled"], summary["supervised"],
            summary["lost"], summary["owed"]) == (2, 1, 1, 1, 1)
    assert summary["debt"] == [{"sectionId": w.a10, "subjectId": w.sci10, "owed": 1, "compensated": 0,
                                "waived": 0}]


def test_a_decline_judges_the_next_candidate_the_same_way(s):
    """Chitra declines 10-B's Science period: it passes to Dev, who only
    supervises, so it is owed. Dev declines in turn: it goes back to
    Chitra, a teacher of the subject, and the debt goes."""
    w = _school(s)
    _, subs = s.decide_leave(_leave(s, w, "ana").id, approve=True, decided_by="p1")
    duty = _by_slot(subs)[(w.b10, 2)]

    def owed():
        return [(l.section_id, l.period) for l in s.lost_periods_for_year(w.year, "owed")]

    after = s.respond_to_substitution(duty.id, teacher_id="chitra", accept=False)
    assert (after.substitute_id, after.mode) == ("dev", "supervised")
    assert owed() == [(w.a10, 1), (w.b10, 2)]
    back = s.respond_to_substitution(duty.id, teacher_id="dev", accept=False)
    assert (back.substitute_id, back.mode) == ("chitra", "substitute")
    assert owed() == [(w.a10, 1)]


def test_a_leave_withdrawn_takes_back_what_its_supervised_periods_owed(s):
    w = _school(s)
    leave = _leave(s, w, "ana")
    s.decide_leave(leave.id, approve=True, decided_by="p1")
    assert len(s.lost_periods_for_year(w.year, "owed")) == 1
    s.cancel_leave(leave.id, today=MON)
    assert s.lost_periods_for_year(w.year) == []
    assert s.cover_summary(w.year, MON, MON)["owed"] == 0


# ---- v3 audit N-3-16: staff with no class of their own ----

def test_staff_with_no_class_of_their_own_cover_last(s):
    """Lata the librarian teaches no class. She is offered, but after every
    teacher of the school: Dev, who also only supervises Science, still
    comes first although his day is busier."""
    w = _school(s)
    s.staff_source = lambda school_id: ["ana", "bala", "chitra", "dev", "lata"]
    _, subs = s.decide_leave(_leave(s, w, "ana").id, approve=True, decided_by="p1")
    first = _by_slot(subs)[(w.a10, 1)]
    cands = s.substitute_candidates(first.id)
    assert [c.teacher_id for c in cands] == ["dev", "lata"]
    assert cands[1].score > cands[0].score, "a lighter day does not lift her above a teacher"
    assert not cands[1].qualified and "no class of their own" in cands[1].reasons[0]
    assert first.substitute_id == "dev"


def test_when_no_teacher_is_free_someone_with_no_class_sits_with_it(s):
    w = _school(s)
    for t in ("chitra", "dev", "bala"):
        s.decide_leave(_leave(s, w, t).id, approve=True, decided_by="p1")
    s.staff_source = lambda school_id: ["lata"]
    _, subs = s.decide_leave(_leave(s, w, "ana").id, approve=True, decided_by="p1")
    got = {(x.section_id, x.period): (x.substitute_id, x.mode) for x in subs}
    assert got[(w.a10, 1)] == got[(w.b10, 2)] == ("lata", "supervised")
    owed = {(l.section_id, l.subject_id) for l in s.lost_periods_for_year(w.year, "owed")}
    assert {(w.a10, w.sci10), (w.b10, w.sci10)} <= owed, "Science was not taught: both periods are owed"


def test_marking_a_teacher_present_again_takes_back_a_made_up_period_and_its_make_up(s):
    """QA S-02: Suresh was marked absent by mistake, his supervised 10-A
    period was made up on Monday, then he was marked present. The period
    stayed "lost" for the class and parents, and the Monday make-up stayed
    booked: only a period still owed was cleared."""
    w = _school(s)
    s.mark_attendance(school_id="s1", academic_year_id=w.year, on=MON, teacher_id="ana",
                      status="absent", marked_by="p1")
    [owed] = s.lost_periods_for_year(w.year, "owed")
    day, period = s.compensation_options(owed.id, today=MON)[0]
    assert s.compensate(owed.id, on=day, period=period, today=MON).status == "compensated"
    assert any(r["kind"] == "makeup" for r in s.day_view(w.year, day, section_id=owed.section_id))

    s.mark_attendance(school_id="s1", academic_year_id=w.year, on=MON, teacher_id="ana",
                      status="present", marked_by="p1")
    assert s.lost_periods_for_year(w.year) == []
    assert not any(r["kind"] == "makeup" for r in s.day_view(w.year, day, section_id=owed.section_id))
    summary = s.cover_summary(w.year, MON, "2026-06-30")
    assert (summary["lost"], summary["compensated"], summary["owed"]) == (0, 0, 0)


def test_a_closure_keeps_a_make_up_already_booked(s):
    """The other way round: a day closed after a supervised period was made
    up still owes the period, so its booked make-up stands."""
    w = _school(s)
    s.decide_leave(_leave(s, w, "ana").id, approve=True, decided_by="p1")
    [owed] = s.lost_periods_for_year(w.year, "owed")
    day, period = s.compensation_options(owed.id, today=MON)[0]
    s.compensate(owed.id, on=day, period=period, today=MON)
    s.declare_closure(w.year, MON, reason="rain")
    made_up = s.lost_periods_for_year(w.year, "compensated")
    assert [(l.section_id, l.period, l.compensation_date) for l in made_up] == [(owed.section_id, owed.period, day)]


def test_leave_applied_again_after_a_cancelled_one_is_its_own(s):
    """Re-measure 2026-10-04: a second leave on a day whose first leave was cancelled reused the
    cancelled cover rows with the old leave id. Cancelling it then left its duties live, and naming a
    replacement for it found no periods."""
    w = _school(s)
    first, _ = s.decide_leave(_leave(s, w, "ana").id, approve=True, decided_by="p1")
    s.cancel_leave(first.id, today=MON)
    second, subs = s.decide_leave(_leave(s, w, "ana").id, approve=True, decided_by="p1")
    assert set(_by_slot(subs)) == {(w.a10, 1), (w.b10, 2)}
    assert all(x.leave_id == second.id and x.status != "cancelled" for x in subs)
    # A replacement takes over this leave's periods.
    s.set_leave_replacement(second.id, "dev", today=MON)
    taken = [x for x in s._subs_where("leave_id=?", (second.id,)) if x.substitute_id == "dev"]
    assert taken, "the replacement found the second leave's periods"
    # Cancelling the second leave cancels all of its cover.
    s.cancel_leave(second.id, today=MON)
    live = s._subs_where("date=? AND status NOT IN ('cancelled','resolved')", (MON,))
    assert live == [], [(x.section_id, x.period, x.status, x.leave_id) for x in live]
