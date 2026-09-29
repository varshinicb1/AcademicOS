"""HTTP routes for exam planning (EX-7; operations/exams.py): the principal
builds the datesheet and the invigilation roster and publishes them;
students see their class's datesheet, teachers their duties."""
from __future__ import annotations

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ConfigDict, Field
from pydantic.alias_generators import to_camel

from ..assessment.auth_routes import get_current_user, require_principal
from ..assessment.users import User
from ..curriculum import routes as cr
from ..curriculum.schemas import Camel
from .exams import ExamError, auto_roster
from .routes import notify_safely, store

router = APIRouter(prefix="/api/v1")
_TIME = r"^([01]\d|2[0-3]):[0-5]\d$"


class _Req(Camel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")


class ExamCreate(_Req):
    name: str = Field(min_length=1, max_length=120)
    start_date: str
    end_date: str
    grades: list[int] = Field(min_length=1)
    academic_year_id: Optional[str] = None


class PaperSlot(_Req):
    grade: int
    subject_id: str
    date: str
    start_time: str = Field(default="09:30", pattern=_TIME)
    end_time: str = Field(default="12:30", pattern=_TIME)


class DatesheetRequest(_Req):
    papers: list[PaperSlot] = Field(max_length=500)


class DutyChange(_Req):
    exam_paper_id: str
    section_id: str
    teacher_id: Optional[str] = None


class RosterRequest(_Req):
    duties: list[DutyChange] = Field(min_length=1, max_length=2000)


class ExamPaper(Camel):
    id: str
    grade: int
    subject_id: str
    subject_name: str
    date: str
    start_time: str
    end_time: str


class Duty(Camel):
    exam_paper_id: str
    section_id: str
    section_name: str
    teacher_id: Optional[str] = None
    teacher_name: Optional[str] = None
    date: str
    start_time: str
    end_time: str
    grade: int
    subject_name: str


class ExamResponse(Camel):
    id: str
    name: str
    start_date: str
    end_date: str
    grades: list[int]
    status: str
    papers: list[ExamPaper] = []
    duties: list[Duty] = []
    unfilled: list[str] = []


def _audit(action: str, user: User, details: dict[str, Any]) -> None:
    from ..assessment.audit_log import get_audit_log
    get_audit_log(cr._cfg.data_root).append(action, actor=user.id, details={"schoolId": user.school_id, **details})


def _exam(exam_id: str, current: User) -> dict:
    e = store().get_exam(exam_id)
    if e is None:
        raise HTTPException(404, "exam not found")
    if e["school_id"] != current.school_id:
        raise HTTPException(403, "this exam belongs to a different school")
    return e


def _sections_by_grade(academic_year_id: str) -> dict[int, list]:
    cs = cr._require()
    return {g.number: cs.sections_for_grade(g.id) for g in cs.grades_for_year(academic_year_id)}


def _duty(r: dict, names: dict[str, str], labels: dict[str, str]) -> Duty:
    return Duty(exam_paper_id=r["exam_paper_id"], section_id=r["section_id"],
                section_name=labels.get(r["section_id"], r["section_id"]), teacher_id=r["teacher_id"],
                teacher_name=names.get(r["teacher_id"] or ""), date=r["date"], start_time=r["start_time"],
                end_time=r["end_time"], grade=r["grade"], subject_name=r["subject_name"])


def _response(e: dict, unfilled: Optional[list[str]] = None) -> ExamResponse:
    cs = cr._require()
    names = {u.id: u.name for u in cr._require_users().users_for_school(e["school_id"])}
    labels = {s.id: cs._section_label(s) for ss in _sections_by_grade(e["academic_year_id"]).values() for s in ss}
    return ExamResponse(id=e["id"], name=e["name"], start_date=e["start_date"], end_date=e["end_date"],
                        grades=e["grades"], status=e["status"],
                        papers=[ExamPaper(**{k: p[k] for k in ExamPaper.model_fields}) for p in store().exam_papers(e["id"])],
                        duties=[_duty(r, names, labels) for r in store().roster(e["id"])], unfilled=unfilled or [])


@router.post("/exams", response_model=ExamResponse)
def create_exam(req: ExamCreate, principal: User = Depends(require_principal)) -> ExamResponse:
    cs = cr._require()
    try:
        start, end = date.fromisoformat(req.start_date), date.fromisoformat(req.end_date)
    except ValueError:
        raise HTTPException(422, "dates are YYYY-MM-DD")
    if req.academic_year_id:
        year = cr._require_school_owns_academic_year(req.academic_year_id, principal)
    else:
        year = next((y for y in cs.academic_years_for_school(principal.school_id)
                     if y.start_date <= start.isoformat() <= y.end_date), None)
        if year is None:
            raise HTTPException(422, "no academic year contains the exam's start date")
    known = set(_sections_by_grade(year.id))
    missing = sorted(set(req.grades) - known)
    if missing:
        raise HTTPException(422, f"no class {', '.join(map(str, missing))} this year")
    try:
        e = store().create_exam(school_id=principal.school_id, academic_year_id=year.id, name=req.name.strip(),
                                start_date=start.isoformat(), end_date=end.isoformat(), grades=req.grades,
                                created_by=principal.id)
    except ExamError as err:
        raise HTTPException(422, str(err))
    _audit("exam_created", principal, {"examId": e["id"], "name": e["name"]})
    return _response(e)


@router.get("/exams", response_model=list[ExamResponse])
def list_exams(current: User = Depends(require_principal)) -> list[ExamResponse]:
    return [_response(e) for e in store().exams_for_school(current.school_id)]


@router.get("/exams/{exam_id}", response_model=ExamResponse)
def get_exam(exam_id: str, principal: User = Depends(require_principal)) -> ExamResponse:
    return _response(_exam(exam_id, principal))


@router.put("/exams/{exam_id}/datesheet", response_model=ExamResponse)
def set_datesheet(exam_id: str, req: DatesheetRequest, principal: User = Depends(require_principal)) -> ExamResponse:
    """Replace the whole datesheet. Every clash (two papers for a class on a
    day, a holiday, a date outside the exam) is reported at once; the old
    datesheet and its roster are kept on any problem, and dropped with it
    otherwise (the roster is per paper)."""
    e = _exam(exam_id, principal)
    cs = cr._require()
    subjects = {}
    by_grade = {g.number: g for g in cs.grades_for_year(e["academic_year_id"])}
    rows = []
    for p in req.papers:
        s = subjects.get(p.subject_id) or cs.get_subject(p.subject_id)
        g = by_grade.get(p.grade)
        if s is None or g is None or s.grade_id != g.id:
            raise HTTPException(422, f"that subject is not taught in class {p.grade}")
        subjects[p.subject_id] = s
        rows.append({"grade": p.grade, "subject_id": s.id, "subject_name": s.name, "date": p.date,
                     "start_time": p.start_time, "end_time": p.end_time})
    try:
        store().replace_datesheet(e, rows, working_dates=cs._working_dates(e["academic_year_id"]))
    except ExamError as err:
        raise HTTPException(409, str(err))
    _audit("exam_datesheet_set", principal, {"examId": e["id"], "papers": len(rows)})
    return _response(e)


@router.post("/exams/{exam_id}/invigilation/auto", response_model=ExamResponse)
def auto_invigilation(exam_id: str, principal: User = Depends(require_principal)) -> ExamResponse:
    """Fill every empty duty: no one on leave, no one who teaches that
    subject to that section, no one in two rooms at once, fewest duties
    first. Duties already set are kept; what cannot be filled is listed."""
    e = _exam(exam_id, principal)
    cs = cr._require()
    papers = store().exam_papers(e["id"])
    by_grade = {n: [s.id for s in ss] for n, ss in _sections_by_grade(e["academic_year_id"]).items()}
    teachers = sorted(u.id for u in cr._require_users().users_for_school(principal.school_id, role="teacher"))
    teaches = {(a.teacher_id, a.section_id, a.subject_id) for a in cs.allocations_for_year(e["academic_year_id"])
               if a.teacher_id}
    busy: dict[str, set[str]] = {}
    for p in papers:
        if p["date"] in busy:
            continue
        busy[p["date"]] = {t for t in teachers for l in cs.leave_for_teacher(t)
                           if l.status == "approved" and l.start_date <= p["date"] <= l.end_date}
    existing = {(r["exam_paper_id"], r["section_id"]): r["teacher_id"] for r in store().roster(e["id"])}
    rows, unfilled = auto_roster(papers, by_grade, teachers, teaches, busy, existing)
    store().set_invigilators(e["id"], rows, assigned_by=principal.id)
    _audit("exam_invigilation_auto", principal, {"examId": e["id"], "assigned": sum(1 for r in rows if r[2]),
                                                 "unfilled": len(unfilled)})
    return _response(e, unfilled)


@router.put("/exams/{exam_id}/invigilation", response_model=ExamResponse)
def set_invigilation(exam_id: str, req: RosterRequest, principal: User = Depends(require_principal)) -> ExamResponse:
    e = _exam(exam_id, principal)
    papers = {p["id"] for p in store().exam_papers(e["id"])}
    users = cr._require_users()
    for d in req.duties:
        if d.exam_paper_id not in papers:
            raise HTTPException(422, f"{d.exam_paper_id} is not a paper of this exam")
        if d.teacher_id:
            u = users.get(d.teacher_id)
            if u is None or u.school_id != principal.school_id or u.role not in ("teacher", "principal"):
                raise HTTPException(422, "an invigilator must be staff of this school")
    store().set_invigilators(e["id"], [(d.exam_paper_id, d.section_id, d.teacher_id) for d in req.duties],
                             assigned_by=principal.id)
    _audit("exam_invigilation_set", principal, {"examId": e["id"], "duties": len(req.duties)})
    return _response(e)


@router.post("/exams/{exam_id}/publish", response_model=ExamResponse)
def publish(exam_id: str, principal: User = Depends(require_principal)) -> ExamResponse:
    """Publish: students of the exam's classes get their datesheet, each
    invigilator their duties."""
    e = _exam(exam_id, principal)
    papers = store().exam_papers(e["id"])
    if not papers:
        raise HTTPException(409, "set the datesheet before publishing")
    e = store().publish_exam(e["id"])
    cs = cr._require()
    students = [en.student_id for g in e["grades"] for s in _sections_by_grade(e["academic_year_id"]).get(g, [])
                for en in cs.enrollments_for_section(s.id)]
    if students:
        notify_safely(school_id=e["school_id"], user_ids=students, kind="exam_scheduled",
                      params={"exam": e["name"], "start": e["start_date"]}, link="/my-exams",
                      dedupe_key=f"exam:{e['id']}")
    duties: dict[str, int] = {}
    for r in store().roster(e["id"]):
        if r["teacher_id"]:
            duties[r["teacher_id"]] = duties.get(r["teacher_id"], 0) + 1
    for t, n in duties.items():
        notify_safely(school_id=e["school_id"], user_ids=[t], kind="invigilation_duty",
                      params={"exam": e["name"], "count": n}, link="/my-exams", dedupe_key=f"duty:{e['id']}:{t}")
    _audit("exam_published", principal, {"examId": e["id"], "students": len(students), "invigilators": len(duties)})
    return _response(e)


class MyExams(Camel):
    exams: list[ExamResponse]


@router.get("/my-exams", response_model=MyExams)
def my_exams(current: User = Depends(get_current_user)) -> MyExams:
    """Published exams: a student's class's papers; a teacher's duties."""
    cs = cr._require()
    out = []
    for e in store().exams_for_school(current.school_id):
        if e["status"] != "published":
            continue
        full = _response(e)
        if current.role == "student":
            en = cs.enrollment_for_student(current.id)
            section = cs.get_section(en.section_id) if en and en.section_id else None
            grade = cs.get_grade(section.grade_id).number if section else None
            papers = [p for p in full.papers if p.grade == grade]
            if papers:
                out.append(full.model_copy(update={"papers": papers, "duties": []}))
        elif current.role in ("teacher", "principal"):
            mine = [d for d in full.duties if d.teacher_id == current.id]
            if mine or current.role == "principal":
                out.append(full.model_copy(update={"duties": mine if current.role == "teacher" else full.duties}))
    return MyExams(exams=out)
