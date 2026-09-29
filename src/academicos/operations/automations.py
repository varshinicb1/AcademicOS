"""Scheduled automations (NTF-2): the reminders and digests nobody has to
remember to send.

Each job has a window on the school's clock (IST) and a period (a day or a
week). A run does every job whose window has opened and whose period has not
been done, and records it, so running every five minutes -- or on every
inbox poll -- sends each thing once. Notifications carry dedupe keys too, so
even two overlapping runs cannot double a message.

- homework_due_tomorrow (from 16:00): students who have not submitted
  homework due tomorrow.
- homework_overdue (from 09:00): the teacher of each homework that closed
  yesterday with students missing, once per homework.
- substitution_escalation (every run): the principal, when a substitution
  for today or tomorrow has no substitute, or its proposed substitute has not
  accepted within ESCALATE_AFTER_MINUTES.
- teacher_daily_digest (from 18:00): each teacher's periods and duties for
  tomorrow, when they have any.
- principal_weekly_digest (Monday from 07:00): last week's cover and homework.
- marking_due (from 15:00): teachers with submissions waiting over two days
  for their marks (TA-7).
- principal_alerts (from 08:00): sections behind plan, lost periods owed over a
  week, homework overdue in bulk, exams within a week without a full roster (ADM-3).

Triggered by POST /api/v1/automations/run (Cloud Scheduler, with the
operator's cron key) and, throttled, by ordinary traffic.
"""
from __future__ import annotations

import logging
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable, Optional

log = logging.getLogger(__name__)
IST = timezone(timedelta(hours=5, minutes=30))
ESCALATE_AFTER_MINUTES = 30

AUTOMATIONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS automation_runs (
    job TEXT NOT NULL,
    period_key TEXT NOT NULL,
    ran_at TEXT NOT NULL,
    notified INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (job, period_key)
);
"""


class AutomationsMixin:
    """Added to OperationsStore."""

    def automation_done(self, job: str, period_key: str) -> bool:
        return self._fetchone("SELECT 1 AS x FROM automation_runs WHERE job=? AND period_key=?",
                              (job, period_key)) is not None

    def record_automation(self, job: str, period_key: str, notified: int) -> None:
        with self._conn_lock:
            self.conn.execute("INSERT OR REPLACE INTO automation_runs (job, period_key, ran_at, notified)"
                              " VALUES (?,?,?,?)",
                              (job, period_key, datetime.now(timezone.utc).isoformat(timespec="seconds"), notified))
            self._commit()

    def automation_history(self, limit: int = 50) -> list[dict]:
        return self._fetchall("SELECT * FROM automation_runs ORDER BY ran_at DESC LIMIT ?", (limit,))


def _schools(cs) -> list[str]:
    return [r["school_id"] for r in cs._fetchall("SELECT DISTINCT school_id FROM academic_years")]


def _year_on(cs, school_id: str, on: str):
    return next((y for y in cs.academic_years_for_school(school_id) if y.start_date <= on <= y.end_date), None)


def _label(cs, section_id: str) -> str:
    s = cs.get_section(section_id)
    return cs._section_label(s) if s else section_id


def _subject(cs, subject_id: str) -> str:
    s = cs.get_subject(subject_id)
    return s.name if s else subject_id


# ---------------- jobs: each returns how many were notified ----------------

def homework_due_tomorrow(ops, cs, users, notify, now: datetime) -> int:
    tomorrow = (now.astimezone(IST).date() + timedelta(days=1)).isoformat()
    n = 0
    for school in _schools(cs):
        for hw in ops.homework_for_school(school, status="published"):
            if hw.due_date != tomorrow:
                continue
            done = {s.student_id for s in ops.submissions_for(hw.id)}
            for sid in hw.section_ids:
                for e in cs.enrollments_for_section(sid):
                    if e.student_id in done:
                        continue
                    notify(school_id=school, user_ids=[e.student_id], kind="homework_due",
                           params={"title": hw.title, "due": "tomorrow"}, link=f"/my-homework/{hw.id}",
                           dedupe_key=f"hwdue:{hw.id}:{e.student_id}:{tomorrow}")
                    n += 1
    return n


def homework_overdue(ops, cs, users, notify, now: datetime) -> int:
    today = now.astimezone(IST).date().isoformat()
    n = 0
    for school in _schools(cs):
        for hw in ops.homework_for_school(school, status="published"):
            if hw.due_date >= today:
                continue
            done = {s.student_id for s in ops.submissions_for(hw.id)}
            missing = sum(1 for sid in hw.section_ids for e in cs.enrollments_for_section(sid)
                          if e.student_id not in done)
            if not missing:
                continue
            notify(school_id=school, user_ids=[hw.teacher_id], kind="homework_overdue",
                   params={"title": hw.title, "count": missing, "due": hw.due_date},
                   link=f"/homework/{hw.id}", dedupe_key=f"hwoverdue:{hw.id}")
            n += 1
    return n


def substitution_escalation(ops, cs, users, notify, now: datetime) -> int:
    today = now.astimezone(IST).date()
    horizon = (today + timedelta(days=1)).isoformat()
    cutoff = (now - timedelta(minutes=ESCALATE_AFTER_MINUTES)).isoformat()
    n = 0
    for school in _schools(cs):
        principals = [u.id for u in users.users_for_school(school, role="principal")]
        year = _year_on(cs, school, today.isoformat())
        if not principals or year is None:
            continue
        for s in cs.substitutions_between(year.id, today.isoformat(), horizon):
            stuck = s.status == "open" or (s.status in ("proposed", "declined") and s.updated_at <= cutoff)
            if not stuck:
                continue
            what = "has no substitute" if s.status in ("open", "declined") else "is not accepted yet"
            notify(school_id=school, user_ids=principals, kind="principal_alert",
                   params={"title": f"Cover needed: {_label(cs, s.section_id)} period {s.period}",
                           "body": f"{_subject(cs, s.subject_id)} on {s.date} {what}."},
                   link=f"/cover?date={s.date}", dedupe_key=f"subesc:{s.id}:{s.status}")
            n += 1
    return n


def teacher_daily_digest(ops, cs, users, notify, now: datetime) -> int:
    tomorrow = (now.astimezone(IST).date() + timedelta(days=1)).isoformat()
    n = 0
    for school in _schools(cs):
        year = _year_on(cs, school, tomorrow)
        if year is None:
            continue
        for u in users.users_for_school(school, role="teacher"):
            rows = [r for r in cs.day_view(year.id, tomorrow, teacher_id=u.id) if r["kind"] != "away"]
            if not rows:
                continue
            kinds = Counter(r["kind"] for r in rows)
            duties = kinds["substitute"] + kinds["supervised"] + kinds["combined"]
            first = min(rows, key=lambda r: r["period"])
            notify(school_id=school, user_ids=[u.id], kind="daily_digest",
                   params={"periods": len(rows) - duties, "duties": duties,
                           "first": f"period {first['period']}, {_label(cs, first['sectionId'])} "
                                    f"{_subject(cs, first['subjectId'])}"},
                   link=f"/my-day?date={tomorrow}", dedupe_key=f"digest:{u.id}:{tomorrow}")
            n += 1
    return n


def principal_weekly_digest(ops, cs, users, notify, now: datetime) -> int:
    today = now.astimezone(IST).date()
    last_monday = today - timedelta(days=today.weekday() + 7)
    last_sunday = last_monday + timedelta(days=6)
    n = 0
    for school in _schools(cs):
        principals = [u.id for u in users.users_for_school(school, role="principal")]
        year = _year_on(cs, school, last_sunday.isoformat()) or _year_on(cs, school, today.isoformat())
        if not principals or year is None:
            continue
        cover = cs.cover_summary(year.id, last_monday.isoformat(), last_sunday.isoformat())
        set_ = [hw for hw in ops.homework_for_school(school)
                if hw.published_at and last_monday.isoformat() <= hw.published_at[:10] <= last_sunday.isoformat()]
        notify(school_id=school, user_ids=principals, kind="weekly_digest",
               params={"week": last_monday.isoformat(), "substitutions": cover["substitutionsRequested"],
                       "unfilled": cover["unfilled"], "lost": cover["lost"], "homework": len(set_)},
               link="/dashboard", dedupe_key=f"weekly:{school}:{last_monday.isoformat()}")
        n += 1
    return n


MARKING_AFTER_DAYS = 2      # submissions waiting this long remind their teacher


def marking_due(ops, cs, users, notify, now: datetime) -> int:
    """TA-7, once an afternoon: each teacher with homework submissions
    waiting over MARKING_AFTER_DAYS days for their marks hears how many."""
    cutoff = (now - timedelta(days=MARKING_AFTER_DAYS)).isoformat()
    today = now.astimezone(IST).date().isoformat()
    n = 0
    for school in _schools(cs):
        waiting: dict[str, list[tuple[str, str]]] = {}
        for hw in ops.homework_for_school(school):
            if hw.status == "draft":
                continue
            for sub in ops.submissions_for(hw.id):
                if sub.status == "submitted" and sub.submitted_at <= cutoff:
                    waiting.setdefault(hw.teacher_id, []).append((sub.submitted_at, hw.title))
        for teacher, items in waiting.items():
            items.sort()
            notify(school_id=school, user_ids=[teacher], kind="marking_due",
                   params={"count": len(items), "days": MARKING_AFTER_DAYS, "title": items[0][1]},
                   link="/homework", dedupe_key=f"marking:{teacher}:{today}")
            n += 1
    return n


BEHIND_LESSONS = 5          # a section this many lessons behind its plan is "falling behind"
OWED_AFTER_DAYS = 7         # a lost period owed this long is flagged


def principal_alerts(ops, cs, users, notify, now: datetime) -> int:
    """ADM-3, once a morning: what needs the principal today, in one
    message -- sections falling behind their plan, lost periods not made up,
    homework overdue in bulk, exams within a week without a full roster.
    Nothing to report sends nothing."""
    today = now.astimezone(IST).date()
    n = 0
    for school in _schools(cs):
        principals = [u.id for u in users.users_for_school(school, role="principal")]
        year = _year_on(cs, school, today.isoformat())
        if not principals or year is None:
            continue
        lines = []
        delayed = cs.get_delayed_topics(school_id=school, academic_year_id=year.id, as_of_date=today.isoformat())
        behind: dict[str, int] = {}
        for lesson in delayed["delayed_lessons"]:
            if lesson.get("section_id"):
                behind[lesson["section_id"]] = behind.get(lesson["section_id"], 0) + 1
        for sid, count in sorted(behind.items(), key=lambda kv: -kv[1]):
            if count >= BEHIND_LESSONS:
                lines.append(f"{_label(cs, sid)} is {count} lessons behind its plan")
        cutoff = (today - timedelta(days=OWED_AFTER_DAYS)).isoformat()
        owed = [l for l in cs.lost_periods_for_year(year.id, "owed") if l.date <= cutoff]
        if owed:
            lines.append(f"{len(owed)} lost periods not made up for over a week")
        bulk = 0
        for hw in ops.homework_for_school(school, status="published"):
            if hw.due_date >= today.isoformat():
                continue
            roster = sum(len(cs.enrollments_for_section(sid)) for sid in hw.section_ids)
            handed = len(ops.submissions_for(hw.id))
            if roster and handed < roster / 2:
                bulk += 1
        if bulk:
            lines.append(f"{bulk} homework past due with fewer than half handed in")
        soon = (today + timedelta(days=7)).isoformat()
        for ex in ops.exams_for_school(school):
            if not (today.isoformat() <= ex["start_date"] <= soon):
                continue
            papers = ops.exam_papers(ex["id"])
            empty = sum(1 for r in ops.roster(ex["id"]) if not r["teacher_id"])
            if not papers:
                lines.append(f"{ex['name']} starts {ex['start_date']} with no datesheet")
            elif empty or ex["status"] != "published":
                lines.append(f"{ex['name']} starts {ex['start_date']}: "
                             + (f"{empty} rooms without an invigilator" if empty else "not published yet"))
        if not lines:
            continue
        notify(school_id=school, user_ids=principals, kind="principal_alert",
               params={"title": f"Needs attention today ({len(lines)})", "body": "; ".join(lines) + "."},
               link="/dashboard", dedupe_key=f"alerts:{school}:{today.isoformat()}")
        n += 1
    return n


# (job, opens at IST hour, period: "day" | "week" | "run", weekday or None, function)
JOBS: list[tuple[str, int, str, Optional[int], Callable[..., int]]] = [
    ("homework_due_tomorrow", 16, "day", None, homework_due_tomorrow),
    ("homework_overdue", 9, "day", None, homework_overdue),
    ("substitution_escalation", 7, "run", None, substitution_escalation),
    ("teacher_daily_digest", 18, "day", None, teacher_daily_digest),
    ("principal_weekly_digest", 7, "week", 0, principal_weekly_digest),
    ("principal_alerts", 8, "day", None, principal_alerts),
    ("marking_due", 15, "day", None, marking_due),
]


def run_due(ops, cs, users, notify, now: Optional[datetime] = None) -> dict[str, Any]:
    """Run every job whose window is open and whose period is not done.
    A failing job is logged and reported, and does not stop the others."""
    now = now or datetime.now(timezone.utc)
    local = now.astimezone(IST)
    out: dict[str, Any] = {}
    for job, hour, period, weekday, fn in JOBS:
        if local.hour < hour or (weekday is not None and local.weekday() != weekday):
            out[job] = "not yet"
            continue
        key = (local.date().isoformat() if period == "day"
               else f"{local.isocalendar().year}-W{local.isocalendar().week:02d}" if period == "week" else None)
        if key is not None and ops.automation_done(job, key):
            out[job] = "done"
            continue
        try:
            n = fn(ops, cs, users, notify, now)
        except Exception as e:  # noqa: BLE001
            log.warning("automation %s failed", job, exc_info=True)
            out[job] = f"failed: {e}"
            continue
        if key is not None:
            ops.record_automation(job, key, n)
        out[job] = n
    return out
