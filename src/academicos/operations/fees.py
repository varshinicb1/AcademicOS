"""Fees (FEE-1): what a school charges per class, what each student has paid,
and the concessions it grants. Amounts are whole paise (integers), never
floats.

- A fee head is one charge for one academic year: a name, an amount, a due
  date, and the class it applies to (`grade`), or every class when none.
- A payment is recorded by the school (cash, cheque, bank transfer, UPI, or
  other) against one head for one student, with a receipt number counted per
  school. No money moves through AcademicOS: online payment waits for a
  gateway the owner chooses.
- A concession lowers what one student owes on one head.

Receipt numbers come from a per-school counter claimed with one atomic
upsert, so two payments at once (or two server instances) never share a
number (AGENTS.md 5.5).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

METHODS = ("cash", "cheque", "bank", "upi", "other")

FEES_SCHEMA = """
CREATE TABLE IF NOT EXISTS fee_heads (
  id                TEXT PRIMARY KEY,
  school_id         TEXT NOT NULL,
  academic_year_id  TEXT NOT NULL,
  grade             INTEGER,
  name              TEXT NOT NULL,
  amount_paise      INTEGER NOT NULL,
  due_date          TEXT NOT NULL,
  created_by        TEXT NOT NULL,
  created_at        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_fee_heads_school ON fee_heads(school_id, academic_year_id);
CREATE TABLE IF NOT EXISTS fee_payments (
  id                TEXT PRIMARY KEY,
  school_id         TEXT NOT NULL,
  student_id        TEXT NOT NULL,
  fee_head_id       TEXT NOT NULL,
  amount_paise      INTEGER NOT NULL,
  paid_on           TEXT NOT NULL,
  method            TEXT NOT NULL,
  reference         TEXT NOT NULL DEFAULT '',
  receipt_no        INTEGER NOT NULL,
  recorded_by       TEXT NOT NULL,
  recorded_at       TEXT NOT NULL,
  UNIQUE (school_id, receipt_no)
);
CREATE INDEX IF NOT EXISTS idx_fee_payments_student ON fee_payments(student_id);
CREATE TABLE IF NOT EXISTS fee_concessions (
  id                TEXT PRIMARY KEY,
  school_id         TEXT NOT NULL,
  student_id        TEXT NOT NULL,
  fee_head_id       TEXT NOT NULL,
  amount_paise      INTEGER NOT NULL,
  reason            TEXT NOT NULL,
  created_by        TEXT NOT NULL,
  created_at        TEXT NOT NULL,
  UNIQUE (school_id, student_id, fee_head_id)
);
CREATE TABLE IF NOT EXISTS fee_receipt_counters (
  school_id         TEXT PRIMARY KEY,
  last_no           INTEGER NOT NULL
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class FeesMixin:
    """Added to OperationsStore."""

    # ---- heads ----
    def create_fee_head(self, *, school_id: str, academic_year_id: str, grade: Optional[int], name: str,
                        amount_paise: int, due_date: str, created_by: str) -> dict:
        hid = uuid.uuid4().hex
        with self._conn_lock:
            self.conn.execute(
                "INSERT INTO fee_heads (id, school_id, academic_year_id, grade, name, amount_paise, due_date, created_by,"
                " created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (hid, school_id, academic_year_id, grade, name, amount_paise, due_date, created_by, _now()))
            self._commit()
        return self.get_fee_head(hid)

    def get_fee_head(self, head_id: str) -> Optional[dict]:
        return self._fetchone("SELECT * FROM fee_heads WHERE id=?", (head_id,))

    def fee_heads(self, school_id: str, academic_year_id: str) -> list[dict]:
        return self._fetchall(
            "SELECT * FROM fee_heads WHERE school_id=? AND academic_year_id=? ORDER BY due_date, name",
            (school_id, academic_year_id))

    def heads_for_grade(self, school_id: str, academic_year_id: str, grade: Optional[int]) -> list[dict]:
        return [h for h in self.fee_heads(school_id, academic_year_id) if h["grade"] is None or h["grade"] == grade]

    def delete_fee_head(self, head_id: str) -> bool:
        """Only a head nobody has paid against: a receipt must keep its head."""
        with self._conn_lock:
            if self._fetchone("SELECT 1 AS x FROM fee_payments WHERE fee_head_id=? LIMIT 1", (head_id,)):
                return False
            self.conn.execute("DELETE FROM fee_concessions WHERE fee_head_id=?", (head_id,))
            self.conn.execute("DELETE FROM fee_heads WHERE id=?", (head_id,))
            self._commit()
        return True

    # ---- payments ----
    def record_fee_payment(self, *, school_id: str, student_id: str, fee_head_id: str, amount_paise: int,
                           paid_on: str, method: str, reference: str, recorded_by: str) -> dict:
        pid = uuid.uuid4().hex
        with self._conn_lock:
            row = self.conn.execute(
                "INSERT INTO fee_receipt_counters (school_id, last_no) VALUES (?, 1) ON CONFLICT (school_id)"
                " DO UPDATE SET last_no = fee_receipt_counters.last_no + 1 RETURNING last_no", (school_id,)).fetchone()
            receipt_no = int(row[0])
            self.conn.execute(
                "INSERT INTO fee_payments (id, school_id, student_id, fee_head_id, amount_paise, paid_on, method,"
                " reference, receipt_no, recorded_by, recorded_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (pid, school_id, student_id, fee_head_id, amount_paise, paid_on, method, reference, receipt_no,
                 recorded_by, _now()))
            self._commit()
        return self._fetchone("SELECT * FROM fee_payments WHERE id=?", (pid,))

    def payments_of(self, school_id: str, student_id: str) -> list[dict]:
        return self._fetchall(
            "SELECT * FROM fee_payments WHERE school_id=? AND student_id=? ORDER BY paid_on, receipt_no",
            (school_id, student_id))

    # ---- concessions ----
    def set_fee_concession(self, *, school_id: str, student_id: str, fee_head_id: str, amount_paise: int, reason: str,
                           created_by: str) -> dict:
        with self._conn_lock:
            self.conn.execute(
                "INSERT INTO fee_concessions (id, school_id, student_id, fee_head_id, amount_paise, reason, created_by,"
                " created_at) VALUES (?,?,?,?,?,?,?,?) ON CONFLICT (school_id, student_id, fee_head_id) DO UPDATE SET"
                " amount_paise=excluded.amount_paise, reason=excluded.reason, created_by=excluded.created_by,"
                " created_at=excluded.created_at",
                (uuid.uuid4().hex, school_id, student_id, fee_head_id, amount_paise, reason, created_by, _now()))
            self._commit()
        return self._fetchone(
            "SELECT * FROM fee_concessions WHERE school_id=? AND student_id=? AND fee_head_id=?",
            (school_id, student_id, fee_head_id))

    def concessions_of(self, school_id: str, student_id: str) -> list[dict]:
        return self._fetchall("SELECT * FROM fee_concessions WHERE school_id=? AND student_id=?", (school_id, student_id))


def statement(heads: list[dict], payments: list[dict], concessions: list[dict], today: str) -> dict:
    """Per head: the amount, any concession, what was paid, the balance and a
    status (paid, part paid, due, overdue). Totals in paise."""
    paid: dict[str, int] = {}
    for p in payments:
        paid[p["fee_head_id"]] = paid.get(p["fee_head_id"], 0) + p["amount_paise"]
    off = {c["fee_head_id"]: c["amount_paise"] for c in concessions}
    rows = []
    for h in heads:
        owed = max(0, h["amount_paise"] - off.get(h["id"], 0))
        got = paid.get(h["id"], 0)
        balance = max(0, owed - got)
        status = ("paid" if balance == 0 else "part_paid" if got > 0 and h["due_date"] >= today
                  else "overdue" if h["due_date"] < today else "due")
        rows.append({"head": h, "concession_paise": off.get(h["id"], 0), "paid_paise": got,
                     "balance_paise": balance, "status": status})
    return {"rows": rows,
            "total_paise": sum(r["head"]["amount_paise"] for r in rows),
            "concession_paise": sum(r["concession_paise"] for r in rows),
            "paid_paise": sum(r["paid_paise"] for r in rows),
            "balance_paise": sum(r["balance_paise"] for r in rows),
            "overdue_paise": sum(r["balance_paise"] for r in rows if r["status"] == "overdue")}
