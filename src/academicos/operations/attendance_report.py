"""The principal's view of student attendance (ATT-1 oversight, ADM-2,
ADM-3): for one day, which sections have taken the register and how many
are away; for the year so far, each section's attendance and the students
below the attendance floor. Built on the register's own table
(attendance.py); it adds no table.

A reports admin sees only the classes their grant covers. Reading names
with a percentage is a read of student data, so it is logged like the
register's own reads.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..assessment.auth_routes import holds, require_admin
from ..assessment.users import User
from ..curriculum import routes as cr
from ..curriculum.schemas import Camel
from .attendance import STATUSES, summarise
from .routes import store

router = APIRouter(prefix="/api/v1/admin")

# CBSE's bye-laws ask 75% attendance of a student sitting the board
# examination; the school's own floor for every class until a school sets
# another. A share over fewer days than MIN_DAYS says little, so no student
# is named below the floor before then.
ATTENDANCE_FLOOR = 75.0
MIN_DAYS = 10
SHOWN = 50


def rows_between(ops, school_id: str, start: str, end: str) -> list[dict]:
    """Every register row of the school in [start, end]."""
    return ops._fetchall(
        "SELECT student_id, section_id, date, status FROM student_attendance "
        "WHERE school_id=? AND date>=? AND date<=?", (school_id, start, end))


def below_floor(ops, cs, school_id: str, start: str, end: str,
                section_ids: Optional[set[str]] = None) -> list[dict]:
    """Students enrolled now whose share of taken days attended is under
    the floor, lowest first: {student_id, section_id, percent, days_taken}."""
    by_student: dict[str, list[dict]] = {}
    for r in rows_between(ops, school_id, start, end):
        by_student.setdefault(r["student_id"], []).append(r)
    out = []
    for sid, rows in by_student.items():
        e = cs.enrollment_for_student(sid)
        if e is None or not e.section_id or (section_ids is not None and e.section_id not in section_ids):
            continue
        s = summarise(rows)
        if s["percent"] is not None and s["days_taken"] >= MIN_DAYS and s["percent"] < ATTENDANCE_FLOOR:
            out.append({"student_id": sid, "section_id": e.section_id, "percent": s["percent"],
                        "days_taken": s["days_taken"]})
    return sorted(out, key=lambda x: (x["percent"], x["student_id"]))


class SectionDay(Camel):
    section_id: str
    section_name: str
    enrolled: int
    taken: bool
    counts: dict[str, int]                  # that day
    year_percent: Optional[float] = None    # the year so far, over taken days


class BelowFloor(Camel):
    student_id: str
    name: str
    section_name: str
    percent: float
    days_taken: int


class AttendanceOverview(Camel):
    date: str
    year_start: str
    floor: float
    sections: list[SectionDay]
    not_taken: int
    away_today: int
    below_floor: list[BelowFloor]
    below_floor_total: int


def _year_on(cs, school_id: str, on: str):
    return next((y for y in cs.academic_years_for_school(school_id) if y.start_date <= on <= y.end_date), None)


@router.get("/attendance/overview", response_model=AttendanceOverview)
def attendance_overview(on: Optional[str] = Query(default=None, alias="date"),
                        principal: User = Depends(require_admin("reports", scoped=True))) -> AttendanceOverview:
    """One day's registers across the school, each section's attendance for
    the year so far, and the students below the floor."""
    today = cr._school_today().isoformat()
    if on is None:
        on = today
    try:
        on = date.fromisoformat(on).isoformat()
    except ValueError:
        raise HTTPException(422, "the date must look like 2026-06-01")
    cs, users, ops = cr._require(), cr._require_users(), store()
    year = _year_on(cs, principal.school_id, on)
    if year is None:
        raise HTTPException(404, "no academic year covers that day; set up the year's classes first")
    grades = {g.id: g.number for g in cs.grades_for_year(year.id)}
    sections = [s for s in cs.sections_for_year(year.id)
                if holds(principal, "reports", grade=grades.get(s.grade_id), section_id=s.id)]
    rows = rows_between(ops, principal.school_id, year.start_date, on)
    by_section: dict[str, list[dict]] = {}
    for r in rows:
        by_section.setdefault(r["section_id"], []).append(r)
    out, not_taken, away = [], 0, 0
    for s in sections:
        enrolled = len(cs.enrollments_for_section(s.id))
        mine = by_section.get(s.id, [])
        that_day = [r for r in mine if r["date"] == on]
        counts = {st: sum(1 for r in that_day if r["status"] == st) for st in STATUSES}
        taken = bool(that_day)
        if enrolled and not taken:
            not_taken += 1
        away += counts["absent"]
        out.append(SectionDay(section_id=s.id, section_name=cs._section_label(s), enrolled=enrolled, taken=taken,
                              counts=counts, year_percent=summarise(mine)["percent"] if mine else None))
    labels = {s.id: cs._section_label(s) for s in sections}
    low = below_floor(ops, cs, principal.school_id, year.start_date, on, set(labels))
    shown = []
    for x in low[:SHOWN]:
        u = users.get(x["student_id"])
        shown.append(BelowFloor(student_id=x["student_id"], name=u.name if u else "", section_name=labels[x["section_id"]],
                                percent=x["percent"], days_taken=x["days_taken"]))
    if shown:
        from ..assessment.audit_log import get_audit_log, record_pii_read
        record_pii_read(get_audit_log(cr._cfg.data_root), actor=principal.id, what="attendance_below_floor",
                        student_ids=[x.student_id for x in shown])
    return AttendanceOverview(date=on, year_start=year.start_date, floor=ATTENDANCE_FLOOR, sections=out,
                              not_taken=not_taken, away_today=away, below_floor=shown, below_floor_total=len(low))
