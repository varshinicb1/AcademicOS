"""The principal's view of fees across the school (FEE-1 oversight, ADM-2,
ADM-4): what was billed, collected and is still owed for the year, per class
and in total, and the students with an overdue balance, largest first, as a
list and as a CSV or Excel file. Built on fees.py's tables and statement;
it adds no table.

Each student's dues come from the same `fees.statement` a parent sees, so
the school's totals and a family's statement cannot disagree.
"""
from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from ..assessment.auth_routes import require_admin
from ..assessment.users import User
from ..curriculum import routes as cr
from ..curriculum.schemas import Camel
from .fees import statement
from .routes import store

router = APIRouter(prefix="/api/v1")

SHOWN = 50


def _year_on(cs, school_id: str, on: str):
    return next((y for y in cs.academic_years_for_school(school_id) if y.start_date <= on <= y.end_date), None)


def school_dues(ops, cs, school_id: str, today: str) -> tuple[Optional[object], list[dict]]:
    """(the year, one row per enrolled student): section, totals of their
    statement and how many of their heads are overdue."""
    year = _year_on(cs, school_id, today)
    if year is None:
        return None, []
    grades = {g.id: g.number for g in cs.grades_for_year(year.id)}
    heads: dict[int, list[dict]] = {}
    rows = []
    for s in cs.sections_for_year(year.id):
        grade = grades.get(s.grade_id)
        if grade not in heads:
            heads[grade] = ops.heads_for_grade(school_id, year.id, grade)
        for e in cs.enrollments_for_section(s.id):
            st = statement(heads[grade], ops.payments_of(school_id, e.student_id),
                           ops.concessions_of(school_id, e.student_id), today)
            rows.append({"student_id": e.student_id, "section_id": s.id, "section": cs._section_label(s),
                         "total": st["total_paise"], "concession": st["concession_paise"],
                         "paid": st["paid_paise"], "balance": st["balance_paise"],
                         "overdue": st["overdue_paise"],
                         "overdue_heads": [r["head"]["name"] for r in st["rows"] if r["status"] == "overdue"]})
    return year, rows


class ClassDues(Camel):
    section_id: str
    section_name: str
    students: int
    total_paise: int
    paid_paise: int
    balance_paise: int
    overdue_paise: int
    students_overdue: int


class Defaulter(Camel):
    student_id: str
    name: str
    section_name: str
    overdue_paise: int
    balance_paise: int
    overdue_heads: list[str]


class FeesOverview(Camel):
    date: str
    total_paise: int
    concession_paise: int
    paid_paise: int
    balance_paise: int
    overdue_paise: int
    collected_percent: Optional[float] = None    # paid over (billed less concessions)
    classes: list[ClassDues]
    defaulters: list[Defaulter]
    defaulters_total: int


def _defaulters(rows: list[dict]) -> list[dict]:
    return sorted((r for r in rows if r["overdue"] > 0), key=lambda r: (-r["overdue"], r["student_id"]))


def _log_read(current: User, student_ids: list[str]) -> None:
    if not student_ids:
        return
    from ..assessment.audit_log import get_audit_log, record_pii_read
    record_pii_read(get_audit_log(cr._cfg.data_root), actor=current.id, what="fee_defaulters",
                    student_ids=student_ids)


@router.get("/fees/overview", response_model=FeesOverview)
def fees_overview(current: User = Depends(require_admin("fees"))) -> FeesOverview:
    """The year's fees across the school: totals, each class, and the
    students with an overdue balance, largest first."""
    today = cr._school_today().isoformat()
    cs, users, ops = cr._require(), cr._require_users(), store()
    year, rows = school_dues(ops, cs, current.school_id, today)
    if year is None:
        raise HTTPException(404, "no academic year covers today; set up this year's classes first")
    classes: dict[str, ClassDues] = {}
    for r in rows:
        c = classes.setdefault(r["section_id"], ClassDues(
            section_id=r["section_id"], section_name=r["section"], students=0, total_paise=0, paid_paise=0,
            balance_paise=0, overdue_paise=0, students_overdue=0))
        c.students += 1
        c.total_paise += r["total"]
        c.paid_paise += r["paid"]
        c.balance_paise += r["balance"]
        c.overdue_paise += r["overdue"]
        c.students_overdue += 1 if r["overdue"] else 0
    late = _defaulters(rows)
    shown = []
    for r in late[:SHOWN]:
        u = users.get(r["student_id"])
        shown.append(Defaulter(student_id=r["student_id"], name=u.name if u else "", section_name=r["section"],
                               overdue_paise=r["overdue"], balance_paise=r["balance"],
                               overdue_heads=r["overdue_heads"]))
    _log_read(current, [d.student_id for d in shown])
    total = sum(r["total"] for r in rows)
    off = sum(r["concession"] for r in rows)
    paid = sum(r["paid"] for r in rows)
    return FeesOverview(date=today, total_paise=total, concession_paise=off, paid_paise=paid,
                        balance_paise=sum(r["balance"] for r in rows), overdue_paise=sum(r["overdue"] for r in rows),
                        collected_percent=round(100 * paid / (total - off), 1) if total - off > 0 else None,
                        classes=list(classes.values()), defaulters=shown, defaulters_total=len(late))


@router.get("/fees/defaulters/export")
def export_defaulters(format: Literal["csv", "xlsx"] = Query(default="csv"),
                      current: User = Depends(require_admin("fees"))) -> Response:
    """Every student with an overdue balance, as CSV or Excel, in rupees."""
    from .import_routes import _csv
    today = cr._school_today().isoformat()
    cs, users, ops = cr._require(), cr._require_users(), store()
    year, rows = school_dues(ops, cs, current.school_id, today)
    if year is None:
        raise HTTPException(404, "no academic year covers today; set up this year's classes first")
    late = _defaulters(rows)
    _log_read(current, [r["student_id"] for r in late])
    from ..assessment.audit_log import get_audit_log
    get_audit_log(cr._cfg.data_root).append("fee_defaulters_exported", actor=current.id,
                                            details={"schoolId": current.school_id, "rows": len(late),
                                                     "format": format})
    out = []
    for r in late:
        u = users.get(r["student_id"])
        out.append([u.name if u else "", u.email if u else "", r["section"], r["overdue"] / 100, r["balance"] / 100,
                    "; ".join(r["overdue_heads"])])
    return _csv(["name", "email", "class", "overdue_rupees", "balance_rupees", "overdue_fees"], out,
                f"fee-defaulters-{today}.csv", format)
