"""Storage for the class teacher's remark on each report card (EX-8;
operations/report_cards.py). One remark per student per term: the text the
teacher saved, who saved it and when. The draft the card's marks suggest is
never stored -- it is computed afresh, so it always says what the marks say
now."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

REMARKS_SCHEMA = """
CREATE TABLE IF NOT EXISTS report_card_remarks (
    term_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    school_id TEXT NOT NULL,
    remark TEXT NOT NULL,
    written_by TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (term_id, student_id)
);
"""


class RemarksMixin:
    """Added to OperationsStore."""

    def remarks_for(self, term_id: str, student_ids: list[str]) -> dict[str, dict]:
        if not student_ids:
            return {}
        marks = ",".join("?" * len(student_ids))
        return {r["student_id"]: r for r in self._fetchall(
            f"SELECT * FROM report_card_remarks WHERE term_id=? AND student_id IN ({marks})",
            (term_id, *student_ids))}

    def remark_for(self, term_id: str, student_id: str) -> Optional[dict]:
        return self.remarks_for(term_id, [student_id]).get(student_id)

    def save_remarks(self, *, school_id: str, term_id: str, remarks: dict[str, str], written_by: str) -> None:
        """Set each student's remark; an empty text removes it. One
        transaction: a batch lands whole or not at all."""
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self._conn_lock:
            for student_id, text in remarks.items():
                if text:
                    self.conn.execute(
                        "INSERT INTO report_card_remarks (term_id, student_id, school_id, remark, written_by,"
                        " updated_at) VALUES (?,?,?,?,?,?) ON CONFLICT (term_id, student_id) DO UPDATE SET"
                        " remark=excluded.remark, written_by=excluded.written_by, updated_at=excluded.updated_at",
                        (term_id, student_id, school_id, text, written_by, now))
                else:
                    self.conn.execute("DELETE FROM report_card_remarks WHERE term_id=? AND student_id=?",
                                      (term_id, student_id))
            self._commit()
