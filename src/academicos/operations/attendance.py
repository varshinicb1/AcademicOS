"""Daily student attendance (ATT-1): one row per student per school day,
taken by the class's teachers, read by the student and their parents.

Statuses: present, late (counted as attended), absent, and excused (away
with the school's leave; not counted against the student). A day with no
row for a student was not taken for them.

A write is an upsert on (school_id, date, student_id): two teachers saving
the same register, or two server instances, end with one row per student
and the later save wins (AGENTS.md 5.5, no check-then-act).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Optional

STATUSES = ("present", "late", "absent", "excused")
ATTENDED = frozenset({"present", "late"})

ATTENDANCE_SCHEMA = """
CREATE TABLE IF NOT EXISTS student_attendance (
  school_id   TEXT NOT NULL,
  date        TEXT NOT NULL,
  student_id  TEXT NOT NULL,
  section_id  TEXT NOT NULL,
  status      TEXT NOT NULL,
  note        TEXT NOT NULL DEFAULT '',
  marked_by   TEXT NOT NULL,
  marked_at   TEXT NOT NULL,
  PRIMARY KEY (school_id, date, student_id)
);
CREATE INDEX IF NOT EXISTS idx_student_attendance_section ON student_attendance(section_id, date);
CREATE INDEX IF NOT EXISTS idx_student_attendance_student ON student_attendance(student_id, date);
"""


class AttendanceMixin:
    """Added to OperationsStore."""

    def mark_attendance(self, *, school_id: str, section_id: str, on: str, entries: Iterable[tuple[str, str, str]],
                        marked_by: str) -> dict[str, Optional[str]]:
        """Save (student_id, status, note) rows for one section and day.
        Returns each student's status before this save (None when it was
        not taken), so the caller can tell who has just become absent."""
        entries = list(entries)
        now = datetime.now(timezone.utc).isoformat()
        with self._conn_lock:
            before = {r["student_id"]: r["status"] for r in self._fetchall(
                "SELECT student_id, status FROM student_attendance WHERE school_id=? AND date=? AND section_id=?",
                (school_id, on, section_id))}
            for student_id, status, note in entries:
                self.conn.execute(
                    "INSERT INTO student_attendance (school_id, date, student_id, section_id, status, note, marked_by,"
                    " marked_at) VALUES (?,?,?,?,?,?,?,?) ON CONFLICT (school_id, date, student_id) DO UPDATE SET"
                    " section_id=excluded.section_id, status=excluded.status, note=excluded.note,"
                    " marked_by=excluded.marked_by, marked_at=excluded.marked_at",
                    (school_id, on, student_id, section_id, status, note, marked_by, now))
            self._commit()
        return {sid: before.get(sid) for sid, _, _ in entries}

    def attendance_for_section(self, school_id: str, section_id: str, on: str) -> dict[str, dict]:
        return {r["student_id"]: r for r in self._fetchall(
            "SELECT * FROM student_attendance WHERE school_id=? AND section_id=? AND date=?",
            (school_id, section_id, on))}

    def attendance_of_student(self, school_id: str, student_id: str, *, start: str, end: str) -> list[dict]:
        return self._fetchall(
            "SELECT * FROM student_attendance WHERE school_id=? AND student_id=? AND date>=? AND date<=?"
            " ORDER BY date", (school_id, student_id, start, end))

    def sections_with_attendance(self, school_id: str, on: str) -> set[str]:
        return {r["section_id"] for r in self._fetchall(
            "SELECT DISTINCT section_id FROM student_attendance WHERE school_id=? AND date=?", (school_id, on))}


def summarise(rows: list[dict]) -> dict:
    """Counts per status and the share of taken days attended. Excused days
    are left out of the share: the school let the student be away."""
    counts = {s: 0 for s in STATUSES}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    counted = sum(counts.values()) - counts["excused"]
    attended = counts["present"] + counts["late"]
    return {"days_taken": len(rows), "counts": counts,
            "percent": round(100 * attended / counted, 1) if counted else None}
