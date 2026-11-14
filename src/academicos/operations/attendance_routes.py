"""HTTP routes for daily student attendance (ATT-1; operations/attendance.py).

- The section's teachers (its class teacher and every teacher allocated to
  it) and the principal take the register for a day, today or earlier. A
  student with no recorded parental consent is left out and named back, as
  marks are (compliance.md, "Parental consent is enforced on the server").
- A student marked absent today is told nothing (they were not there); their
  linked parents hear it once, the same day, so they can tell the school if
  it is wrong (`child_absent`).
- A student reads their own attendance, a parent their linked child's, and
  the section's teachers or a reports admin any student's of the school.
  Every read of a student's record is logged.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import ConfigDict, Field
from pydantic.alias_generators import to_camel

from ..assessment.auth_routes import get_current_user, holds, require_staff
from ..assessment.users import User
from ..curriculum import routes as cr
from ..curriculum.schemas import Camel
from .attendance import STATUSES, summarise
from .routes import notify_parents_safely, store

router = APIRouter(prefix="/api/v1")

Status = Literal["present", "late", "absent", "excused"]
SUMMARY_DAYS = 400          # a whole academic year and a little more
RECENT_SHOWN = 30           # the most recent days that were not plain "present"


class _Req(Camel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")


class AttendanceEntry(_Req):
    student_id: str
    status: Status
    note: str = Field(default="", max_length=200)


class MarkAttendanceRequest(_Req):
    entries: list[AttendanceEntry] = Field(max_length=200)


class RegisterRow(Camel):
    student_id: str
    name: str
    status: Optional[str] = None         # None: not taken yet
    note: str = ""
    marked_by: Optional[str] = None


class RegisterResponse(Camel):
    section_id: str
    section_name: str
    date: str
    taken: bool
    rows: list[RegisterRow]
    counts: dict[str, int]
    without_consent: list[str] = []      # names left out of this save


class AttendanceDay(Camel):
    date: str
    status: str
    note: str = ""


class StudentAttendanceResponse(Camel):
    student_id: str
    start: str
    end: str
    days_taken: int
    counts: dict[str, int]
    percent: Optional[float] = None
    recent: list[AttendanceDay]          # newest first: absent, late and excused days


# ---------------- helpers ----------------

def _today() -> str:
    return cr._school_today().isoformat()


def _valid_day(on: Optional[str]) -> str:
    if on is None:
        return _today()
    try:
        day = date.fromisoformat(on)
    except ValueError:
        raise HTTPException(422, "the date must look like 2026-06-01")
    if day.isoformat() > _today():
        raise HTTPException(422, "attendance can be taken for today or an earlier day, not a future one")
    return day.isoformat()


def _teaches(section, current: User) -> bool:
    if section.class_teacher_id == current.id:
        return True
    return any(a.teacher_id == current.id and a.section_id == section.id
               for a in cr._require().allocations_for_year(section.academic_year_id))


def _may_mark(section, current: User) -> bool:
    return current.role == "principal" or _teaches(section, current)


def _may_read(section, current: User) -> bool:
    if _may_mark(section, current):
        return True
    grade = cr._require().get_grade(section.grade_id)
    return holds(current, "reports", grade=grade.number if grade else None, section_id=section.id)


def _register(section, on: str, without_consent: list[str]) -> RegisterResponse:
    cs, users, ops = cr._require(), cr._require_users(), store()
    saved = ops.attendance_for_section(section.school_id, section.id, on)
    rows = []
    for e in cs.enrollments_for_section(section.id):
        u, r = users.get(e.student_id), saved.get(e.student_id)
        rows.append(RegisterRow(student_id=e.student_id, name=u.name if u else "", status=r["status"] if r else None,
                                note=r["note"] if r else "", marked_by=r["marked_by"] if r else None))
    rows.sort(key=lambda r: r.name.lower())
    counts = {s: sum(1 for r in rows if r.status == s) for s in STATUSES}
    return RegisterResponse(section_id=section.id, section_name=cs._section_label(section), date=on,
                            taken=bool(saved), rows=rows, counts=counts, without_consent=without_consent)


def _log_read(current: User, what: str, **kw) -> None:
    from ..assessment.audit_log import get_audit_log, record_pii_read
    record_pii_read(get_audit_log(cr._cfg.data_root), actor=current.id, what=what, **kw)


def student_attendance(student: User, *, days: int = SUMMARY_DAYS) -> StudentAttendanceResponse:
    end = _today()
    start = (date.fromisoformat(end) - timedelta(days=days)).isoformat()
    rows = store().attendance_of_student(student.school_id, student.id, start=start, end=end)
    s = summarise(rows)
    recent = [AttendanceDay(date=r["date"], status=r["status"], note=r["note"])
              for r in reversed(rows) if r["status"] != "present"][:RECENT_SHOWN]
    return StudentAttendanceResponse(student_id=student.id, start=start, end=end, days_taken=s["days_taken"],
                                     counts=s["counts"], percent=s["percent"], recent=recent)


# ---------------- the register ----------------

@router.get("/sections/{section_id}/attendance", response_model=RegisterResponse)
def get_register(section_id: str, on: Optional[str] = Query(default=None, alias="date"),
                 current: User = Depends(require_staff)) -> RegisterResponse:
    """The section's register for a day (today by default): every enrolled
    student, with their status, or none when not taken yet."""
    section = cr._require_school_owns_section(section_id, current)
    if not _may_read(section, current):
        raise HTTPException(403, "only the section's teachers or the principal see its register")
    day = _valid_day(on)
    out = _register(section, day, [])
    _log_read(current, "attendance_register", student_ids=[r.student_id for r in out.rows], section_id=section.id)
    return out


@router.put("/sections/{section_id}/attendance", response_model=RegisterResponse)
def put_register(section_id: str, req: MarkAttendanceRequest, on: Optional[str] = Query(default=None, alias="date"),
                 current: User = Depends(require_staff)) -> RegisterResponse:
    """Take or correct the register. Rows for students not in the section are
    refused; students without parental consent are left out and named."""
    from ..assessment.audit_log import get_audit_log
    from ..assessment.authz import students_without_consent
    from ..assessment.consent import get_consent_store
    section = cr._require_school_owns_section(section_id, current)
    if not _may_mark(section, current):
        raise HTTPException(403, "only the section's teachers or the principal take its register")
    day = _valid_day(on)
    cs, users = cr._require(), cr._require_users()
    enrolled = {e.student_id for e in cs.enrollments_for_section(section.id)}
    strangers = [e.student_id for e in req.entries if e.student_id not in enrolled]
    if strangers:
        raise HTTPException(422, f"{len(strangers)} of these students are not in {cs._section_label(section)}; "
                                 "reload the register and save again")
    ids = [e.student_id for e in req.entries]
    if len(set(ids)) != len(ids):
        raise HTTPException(422, "a student appears twice; give each student one status")
    missing = set(students_without_consent(get_consent_store(cr._cfg.data_root), section.school_id, ids))
    entries = [(e.student_id, e.status, e.note.strip()) for e in req.entries if e.student_id not in missing]
    before = store().mark_attendance(school_id=section.school_id, section_id=section.id, on=day, entries=entries,
                                     marked_by=current.id)
    counts = {s: sum(1 for _, st, _ in entries if st == s) for s in STATUSES}
    get_audit_log(cr._cfg.data_root).append("attendance_marked", actor=current.id, details={
        "schoolId": section.school_id, "sectionId": section.id, "date": day, "counts": counts,
        "leftOutWithoutConsent": len(missing)})
    if day == _today():
        label = cs._section_label(section)
        for sid, status, _ in entries:
            if status != "absent" or before.get(sid) == "absent":
                continue
            u = users.get(sid)
            notify_parents_safely(school_id=section.school_id, student_ids=[sid], kind="child_absent",
                                  params={"student": u.name if u else "", "section": label, "date": day},
                                  dedupe_key=f"absent:{sid}:{day}")
    names = sorted((users.get(s).name if users.get(s) else "") for s in missing)
    return _register(section, day, names)


# ---------------- a student's own, and a parent's child's ----------------

@router.get("/my-attendance-record", response_model=StudentAttendanceResponse)
def my_attendance_record(current: User = Depends(get_current_user)) -> StudentAttendanceResponse:
    """The signed-in student's attendance this year: counts, the share
    attended, and the recent days they were absent, late or excused."""
    if current.role != "student":
        raise HTTPException(403, "this is a student's own attendance; a parent opens their child's")
    _log_read(current, "own_attendance", student_id=current.id)
    return student_attendance(current)


@router.get("/children/{student_id}/attendance", response_model=StudentAttendanceResponse)
def child_attendance(student_id: str, current: User = Depends(get_current_user)) -> StudentAttendanceResponse:
    from .guardian_routes import _my_child
    child = _my_child(student_id, current)
    _log_read(current, "child_attendance", student_id=student_id)
    return student_attendance(child)


@router.get("/students/{student_id}/attendance", response_model=StudentAttendanceResponse)
def staff_student_attendance(student_id: str, current: User = Depends(require_staff)) -> StudentAttendanceResponse:
    """One student's attendance for the section's teachers or a reports admin."""
    from ..assessment.authz import require_school_owns_student
    student = require_school_owns_student(cr._require_users(), student_id, current)
    e = cr._require().enrollment_for_student(student_id)
    section = cr._require().get_section(e.section_id) if e and e.section_id else None
    if section is None or not _may_read(section, current):
        if current.role != "principal":
            raise HTTPException(403, "only the student's teachers or the principal see their attendance")
    _log_read(current, "student_attendance", student_id=student_id)
    return student_attendance(student)
