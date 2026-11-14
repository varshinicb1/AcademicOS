"""HTTP routes for fees (FEE-1; operations/fees.py).

- The principal, or a teacher given the "fees" admin grant, sets the year's
  fee heads, records payments (each gets the school's next receipt number)
  and grants concessions. Every change is audited.
- A parent sees each linked child's statement: every head, what was paid,
  the balance and what is overdue, with the receipts. A student sees their
  own. Each payment recorded tells the child's parents (`fee_receipt`).
- Amounts travel as whole paise. No money moves through AcademicOS.
"""
from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import ConfigDict, Field
from pydantic.alias_generators import to_camel

from ..assessment.auth_routes import get_current_user, require_admin
from ..assessment.users import User
from ..curriculum import routes as cr
from ..curriculum.schemas import Camel
from .fees import statement
from .routes import notify_parents_safely, store

router = APIRouter(prefix="/api/v1")

MAX_PAISE = 10_000_000_00          # ten lakh rupees: a typing slip, not a fee


class _Req(Camel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")


class FeeHeadRequest(_Req):
    academic_year_id: str
    grade: Optional[int] = Field(default=None, ge=1, le=12)
    name: str = Field(min_length=1, max_length=80)
    amount_paise: int = Field(gt=0, le=MAX_PAISE)
    due_date: str


class PaymentRequest(_Req):
    student_id: str
    fee_head_id: str
    amount_paise: int = Field(gt=0, le=MAX_PAISE)
    paid_on: Optional[str] = None
    method: Literal["cash", "cheque", "bank", "upi", "other"]
    reference: str = Field(default="", max_length=80)


class ConcessionRequest(_Req):
    student_id: str
    fee_head_id: str
    amount_paise: int = Field(ge=0, le=MAX_PAISE)
    reason: str = Field(min_length=1, max_length=200)


class FeeHead(Camel):
    id: str
    academic_year_id: str
    grade: Optional[int] = None
    name: str
    amount_paise: int
    due_date: str


class Receipt(Camel):
    id: str
    receipt_no: int
    fee_head_id: str
    fee_head_name: str
    amount_paise: int
    paid_on: str
    method: str
    reference: str = ""


class StatementRow(Camel):
    head: FeeHead
    concession_paise: int
    paid_paise: int
    balance_paise: int
    status: str                       # paid | part_paid | due | overdue


class FeeStatement(Camel):
    student_id: str
    student_name: str
    rows: list[StatementRow]
    total_paise: int
    concession_paise: int
    paid_paise: int
    balance_paise: int
    overdue_paise: int
    receipts: list[Receipt]


# ---------------- helpers ----------------

def _today() -> str:
    return cr._school_today().isoformat()


def _iso(value: str, what: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        raise HTTPException(422, f"the {what} must look like 2026-06-01")


def _head(h: dict) -> FeeHead:
    return FeeHead(id=h["id"], academic_year_id=h["academic_year_id"], grade=h["grade"], name=h["name"],
                   amount_paise=h["amount_paise"], due_date=h["due_date"])


def _audit(action: str, current: User, details: dict) -> None:
    from ..assessment.audit_log import get_audit_log
    get_audit_log(cr._cfg.data_root).append(action, actor=current.id,
                                            details={"schoolId": current.school_id, **details})


def _student(student_id: str, current: User) -> User:
    from ..assessment.authz import require_school_owns_student
    s = require_school_owns_student(cr._require_users(), student_id, current)
    if s.role != "student":
        raise HTTPException(422, "that account is not a student")
    return s


def _place(student_id: str) -> tuple[Optional[str], Optional[int]]:
    """The student's academic year and class, from their enrolment."""
    cs = cr._require()
    e = cs.enrollment_for_student(student_id)
    if e is None or not e.grade_id:
        return None, None
    g = cs.get_grade(e.grade_id)
    return (g.academic_year_id, g.number) if g else (None, None)


def _owned_head(head_id: str, current: User) -> dict:
    h = store().get_fee_head(head_id)
    if h is None or h["school_id"] != current.school_id:
        raise HTTPException(404, "no fee head of your school with that id")
    return h


def fee_statement(student: User) -> FeeStatement:
    year, grade = _place(student.id)
    s = store()
    heads = s.heads_for_grade(student.school_id, year, grade) if year else []
    payments = s.payments_of(student.school_id, student.id)
    st = statement(heads, payments, s.concessions_of(student.school_id, student.id), _today())
    names = {h["id"]: h["name"] for h in heads}
    for p in payments:
        if p["fee_head_id"] not in names:
            h = s.get_fee_head(p["fee_head_id"])
            names[p["fee_head_id"]] = h["name"] if h else ""
    return FeeStatement(
        student_id=student.id, student_name=student.name,
        rows=[StatementRow(head=_head(r["head"]), concession_paise=r["concession_paise"], paid_paise=r["paid_paise"],
                           balance_paise=r["balance_paise"], status=r["status"]) for r in st["rows"]],
        total_paise=st["total_paise"], concession_paise=st["concession_paise"], paid_paise=st["paid_paise"],
        balance_paise=st["balance_paise"], overdue_paise=st["overdue_paise"],
        receipts=[Receipt(id=p["id"], receipt_no=p["receipt_no"], fee_head_id=p["fee_head_id"],
                          fee_head_name=names.get(p["fee_head_id"], ""), amount_paise=p["amount_paise"],
                          paid_on=p["paid_on"], method=p["method"], reference=p["reference"]) for p in payments])


def rupees(paise: int) -> str:
    r, p = divmod(paise, 100)
    return f"Rs {r:,}" + (f".{p:02d}" if p else "")


# ---------------- the school's side ----------------

@router.get("/fees/heads", response_model=list[FeeHead])
def list_heads(academic_year_id: str = Query(alias="academicYearId"),
               current: User = Depends(require_admin("fees"))) -> list[FeeHead]:
    cr._require_school_owns_academic_year(academic_year_id, current)
    return [_head(h) for h in store().fee_heads(current.school_id, academic_year_id)]


@router.post("/fees/heads", response_model=FeeHead)
def create_head(req: FeeHeadRequest, current: User = Depends(require_admin("fees"))) -> FeeHead:
    cr._require_school_owns_academic_year(req.academic_year_id, current)
    h = store().create_fee_head(school_id=current.school_id, academic_year_id=req.academic_year_id, grade=req.grade,
                                name=req.name.strip(), amount_paise=req.amount_paise,
                                due_date=_iso(req.due_date, "due date"), created_by=current.id)
    _audit("fee_head_created", current, {"feeHeadId": h["id"], "grade": req.grade, "amountPaise": req.amount_paise})
    return _head(h)


@router.delete("/fees/heads/{head_id}", response_model=FeeHead)
def delete_head(head_id: str, current: User = Depends(require_admin("fees"))) -> FeeHead:
    h = _owned_head(head_id, current)
    if not store().delete_fee_head(head_id):
        raise HTTPException(409, "payments are recorded against this fee; it cannot be removed")
    _audit("fee_head_deleted", current, {"feeHeadId": head_id})
    return _head(h)


@router.post("/fees/payments", response_model=Receipt)
def record_payment(req: PaymentRequest, current: User = Depends(require_admin("fees"))) -> Receipt:
    """Record money the school received; the receipt number is the school's
    next. The child's parents hear of it."""
    student = _student(req.student_id, current)
    h = _owned_head(req.fee_head_id, current)
    year, grade = _place(student.id)
    if h["academic_year_id"] != year or (h["grade"] is not None and h["grade"] != grade):
        raise HTTPException(422, f"{h['name']} is not charged to {student.name}'s class")
    paid_on = _iso(req.paid_on, "payment date") if req.paid_on else _today()
    if paid_on > _today():
        raise HTTPException(422, "a payment cannot be dated in the future")
    p = store().record_fee_payment(school_id=current.school_id, student_id=student.id, fee_head_id=h["id"],
                                   amount_paise=req.amount_paise, paid_on=paid_on, method=req.method,
                                   reference=req.reference.strip(), recorded_by=current.id)
    _audit("fee_payment_recorded", current, {"studentId": student.id, "feeHeadId": h["id"],
                                             "amountPaise": req.amount_paise, "receiptNo": p["receipt_no"]})
    notify_parents_safely(school_id=current.school_id, student_ids=[student.id], kind="fee_receipt",
                          params={"student": student.name, "amount": rupees(req.amount_paise), "fee": h["name"],
                                  "receipt": str(p["receipt_no"])},
                          dedupe_key=f"feereceipt:{p['id']}:{student.id}")
    return Receipt(id=p["id"], receipt_no=p["receipt_no"], fee_head_id=h["id"], fee_head_name=h["name"],
                   amount_paise=p["amount_paise"], paid_on=p["paid_on"], method=p["method"], reference=p["reference"])


@router.put("/fees/concessions", response_model=FeeStatement)
def set_concession(req: ConcessionRequest, current: User = Depends(require_admin("fees"))) -> FeeStatement:
    """Lower what one student owes on one fee (0 removes the concession)."""
    student = _student(req.student_id, current)
    h = _owned_head(req.fee_head_id, current)
    if req.amount_paise > h["amount_paise"]:
        raise HTTPException(422, "a concession cannot be more than the fee")
    store().set_fee_concession(school_id=current.school_id, student_id=student.id, fee_head_id=h["id"],
                               amount_paise=req.amount_paise, reason=req.reason.strip(), created_by=current.id)
    _audit("fee_concession_set", current, {"studentId": student.id, "feeHeadId": h["id"],
                                           "amountPaise": req.amount_paise})
    return fee_statement(student)


@router.get("/fees/students/{student_id}", response_model=FeeStatement)
def student_statement(student_id: str, current: User = Depends(require_admin("fees"))) -> FeeStatement:
    return fee_statement(_student(student_id, current))


# ---------------- a family's side ----------------

@router.get("/children/{student_id}/fees", response_model=FeeStatement)
def child_fees(student_id: str, current: User = Depends(get_current_user)) -> FeeStatement:
    from .guardian_routes import _my_child
    return fee_statement(_my_child(student_id, current))


@router.get("/my-fees", response_model=FeeStatement)
def my_fees(current: User = Depends(get_current_user)) -> FeeStatement:
    if current.role != "student":
        raise HTTPException(403, "this is a student's own statement; a parent opens their child's")
    return fee_statement(current)


class SectionFeeRow(Camel):
    student_id: str
    name: str
    total_paise: int
    paid_paise: int
    balance_paise: int
    overdue_paise: int


@router.get("/fees/sections/{section_id}", response_model=list[SectionFeeRow])
def section_fees(section_id: str, current: User = Depends(require_admin("fees"))) -> list[SectionFeeRow]:
    """Each student of one class with what they owe: the school's way in to
    a student's statement, and its list of who is behind."""
    section = cr._require_school_owns_section(section_id, current)
    users = cr._require_users()
    out = []
    for e in cr._require().enrollments_for_section(section.id):
        u = users.get(e.student_id)
        if u is None:
            continue
        st = fee_statement(u)
        out.append(SectionFeeRow(student_id=u.id, name=u.name, total_paise=st.total_paise, paid_paise=st.paid_paise,
                                 balance_paise=st.balance_paise, overdue_paise=st.overdue_paise))
    return sorted(out, key=lambda r: r.name.lower())
