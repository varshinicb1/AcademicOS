"""AI reading of homework photos (TA-4, P1: "AI-assisted marking of written
answers from photos").

A student photographs written answers and attaches them to their submission
(homework_photos.py). Until now the teacher read every photo and typed every
mark. Here the photos are read the way a scanned answer booklet is
(assessment/mobile_scan.py): each photo is cropped and its lighting evened
(imaging.py), transcribed by Sarvam Vision (vision.py), split into answers on
the question numbers the student wrote ("Q1", "2."), and each answer the
student did not type is scored against the question's marking scheme
(llm_evaluate.py). The result is a suggestion per question -- the text read,
the marks and the reason -- which the teacher's marking dialog fills in. The
teacher confirms or changes it and saves through the ordinary grade route: a
suggestion never becomes a mark on its own.

Who and what leaves the school: the photos (which may show anything the
student wrote, a name included) and, per answer, the question, its marking
scheme and the text read go to Sarvam AI, the sub-processor already listed for
answer-booklet scans (docs/compliance.md, docs/dpa-template.md §5). No
student identifier is added. It needs the student's parental consent, as
uploading the photo did, and nothing runs with no Sarvam key configured.

Reading happens by itself: the automation `homework_photo_reading` reads
submissions waiting for marks that have photos and no reading yet, a few per
run, and the teacher can ask for a reading at once (or again, after a re-take)
from the dialog. A submission is claimed atomically before it is read, so two
runs (or two instances) never read it twice.
"""
from __future__ import annotations

import json
import logging
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger(__name__)

READ_PER_RUN = 5            # submissions the automation reads in one run
STALE_CLAIM_MINUTES = 30    # a claim this old is a reader that died; it may be taken again

AI_SCHEMA = """
CREATE TABLE IF NOT EXISTS homework_photo_reads (
    homework_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    status TEXT NOT NULL,              -- reading | done | failed
    note TEXT,
    requested_by TEXT NOT NULL,        -- a teacher's id, or 'automation'
    started_at TEXT NOT NULL,
    finished_at TEXT,
    PRIMARY KEY (homework_id, student_id)
);
CREATE TABLE IF NOT EXISTS homework_photo_readings (
    homework_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    question_id TEXT NOT NULL,
    answer_text TEXT NOT NULL,
    awarded_marks REAL NOT NULL,
    max_marks INTEGER NOT NULL,
    verdict TEXT NOT NULL,
    confidence REAL NOT NULL,
    reasoning TEXT NOT NULL,
    warnings_json TEXT NOT NULL,
    PRIMARY KEY (homework_id, student_id, question_id)
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _stale_before() -> str:
    """A 'reading' claim started before this is a reader that died."""
    return (datetime.now(timezone.utc) - timedelta(minutes=STALE_CLAIM_MINUTES)).isoformat(timespec="seconds")


class HomeworkAIMixin:
    """Added to OperationsStore."""

    def claim_photo_read(self, homework_id: str, student_id: str, *, by: str, again: bool = False) -> bool:
        """Take the submission for reading. True only for the caller who took
        it: a new claim, or (with `again`, a teacher asking) one that is not
        being read now, or a claim left by a reader that died."""
        now = _now()
        with self._conn_lock:
            cur = self.conn.execute(
                "INSERT INTO homework_photo_reads (homework_id, student_id, status, requested_by, started_at)"
                " VALUES (?,?,?,?,?) ON CONFLICT (homework_id, student_id) DO NOTHING",
                (homework_id, student_id, "reading", by, now))
            took = cur.rowcount == 1
            if not took:
                stale = _stale_before()
                cond = "(status<>'reading' OR started_at<?)" if again else "(status='reading' AND started_at<?)"
                cur = self.conn.execute(
                    f"UPDATE homework_photo_reads SET status='reading', note=NULL, requested_by=?, started_at=?,"
                    f" finished_at=NULL WHERE homework_id=? AND student_id=? AND {cond}",
                    (by, now, homework_id, student_id, stale))
                took = cur.rowcount == 1
            self._commit()
        return took

    def finish_photo_read(self, homework_id: str, student_id: str, *, readings: list[dict],
                          failed: Optional[str] = None) -> None:
        with self._conn_lock:
            self.conn.execute("DELETE FROM homework_photo_readings WHERE homework_id=? AND student_id=?",
                              (homework_id, student_id))
            for r in readings:
                self.conn.execute(
                    "INSERT INTO homework_photo_readings (homework_id, student_id, question_id, answer_text,"
                    " awarded_marks, max_marks, verdict, confidence, reasoning, warnings_json)"
                    " VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (homework_id, student_id, r["questionId"], r["answerText"], r["awardedMarks"],
                     r["maxMarks"], r["verdict"], r["confidence"], r["reasoning"],
                     json.dumps(r["warnings"], ensure_ascii=False)))
            self.conn.execute(
                "UPDATE homework_photo_reads SET status=?, note=?, finished_at=? WHERE homework_id=? AND student_id=?",
                ("failed" if failed else "done", failed, _now(), homework_id, student_id))
            self._commit()

    def photo_read(self, homework_id: str, student_id: str) -> Optional[dict]:
        return self._fetchone("SELECT * FROM homework_photo_reads WHERE homework_id=? AND student_id=?",
                              (homework_id, student_id))

    def photo_readings(self, homework_id: str, student_id: str) -> list[dict]:
        rows = self._fetchall("SELECT * FROM homework_photo_readings WHERE homework_id=? AND student_id=?"
                              " ORDER BY question_id", (homework_id, student_id))
        return [{"questionId": r["question_id"], "answerText": r["answer_text"],
                 "awardedMarks": r["awarded_marks"], "maxMarks": r["max_marks"], "verdict": r["verdict"],
                 "confidence": r["confidence"], "reasoning": r["reasoning"],
                 "warnings": json.loads(r["warnings_json"])} for r in rows]

    def photo_reads_waiting(self, school_id: str, limit: int) -> list[tuple[Any, str]]:
        """(homework, student id) for submissions waiting for marks, with
        photos, and not read since their newest photo: never read, or a
        photo added after the last reading (a re-take). Oldest first."""
        rows = self._fetchall(
            "SELECT s.homework_id, s.student_id FROM homework_submissions s"
            " JOIN homework h ON h.id = s.homework_id"
            " WHERE h.school_id=? AND s.status='submitted'"
            " AND EXISTS (SELECT 1 FROM homework_photos p WHERE p.homework_id=s.homework_id"
            "             AND p.student_id=s.student_id)"
            " AND NOT EXISTS (SELECT 1 FROM homework_photo_reads r WHERE r.homework_id=s.homework_id"
            "                 AND r.student_id=s.student_id AND ("
            "                   (r.status='reading' AND r.started_at >= ?) OR (r.status<>'reading' AND NOT EXISTS ("
            "                     SELECT 1 FROM homework_photos q WHERE q.homework_id=s.homework_id"
            "                     AND q.student_id=s.student_id AND q.uploaded_at > r.started_at))))"
            " ORDER BY s.submitted_at LIMIT ?", (school_id, _stale_before(), limit))
        return [(self.get_homework(r["homework_id"]), r["student_id"]) for r in rows]


# ---------------------------------------------------------------- reading


def enabled() -> bool:
    """A Sarvam key is configured: without one nothing is sent anywhere."""
    from ..assessment import vision
    from ..config import LLMNotEnabled
    try:
        vision.api_key()
        return True
    except LLMNotEnabled:
        return False


def _ocr_photos(photos: list[dict], workdir: Path) -> list:
    """One PageOCR per photo, in upload order. A photo whose OCR fails is a
    blank page with a warning, not an end to the reading."""
    from ..assessment import imaging, vision
    from .homework_photos import TYPES, _bytes
    pages = []
    for i, p in enumerate(photos, start=1):
        raw = workdir / f"photo_{i}.{TYPES[p['content_type']]}"
        raw.write_bytes(_bytes(p))
        warnings: list[str] = []
        source = raw
        try:
            result = imaging.preprocess_page(raw, workdir / "processed", i)
            source = result.path
            warnings.extend(result.warnings)
        except Exception as exc:  # noqa: BLE001 - the original photo is still readable
            log.warning("preprocessing failed for homework photo %s: %s", p["id"], exc)
            warnings.append("the photo could not be straightened; it was read as taken")
        try:
            page = vision.ocr_page(source, i, workdir=workdir / "ocr", crop_furniture=False)
            page.warnings = warnings + page.warnings
        except Exception as exc:  # noqa: BLE001 - recorded on the page, routed to the teacher
            log.warning("OCR failed for homework photo %s: %s", p["id"], exc)
            page = vision.PageOCR(page_no=i, text="", warnings=warnings + [f"OCR failed for photo {i}"])
        pages.append(page)
    return pages


def read_submission(hw, sub, photos: list[dict]) -> list[dict]:
    """A suggestion for each question the student did not type, from what
    the photos show under its number (the app numbers them Q1, Q2, ...)."""
    from ..assessment import llm_evaluate, scan
    from ..assessment.schemas import QuestionSchema
    with tempfile.TemporaryDirectory(prefix="hw_read_") as tmp:
        pages = _ocr_photos(photos, Path(tmp))
    failed_pages = [p.page_no for p in pages if any("ocr failed" in w.lower() for w in p.warnings)]
    by_number = {s.question_no: s for s in scan.segment_answers(pages)}
    out = []
    for number, raw in enumerate(hw.questions, start=1):
        if (sub.answers.get(raw["id"]) or "").strip():
            continue                     # typed in the app: already marked from that
        q = QuestionSchema.model_validate(raw)
        seg = by_number.get(number)
        text = seg.text if seg else ""
        warnings = list(seg.warnings) if seg else ["no answer found under this question's number in the photos"]
        if seg is None and failed_pages:
            warnings.append(f"photo(s) {failed_pages} could not be read, so this may not be blank; check the photo")
        ev = llm_evaluate.evaluate_answer_llm(q, q.answer_scheme, text)
        out.append({"questionId": q.id, "answerText": text, "awardedMarks": float(ev.awarded_marks),
                    "maxMarks": int(ev.max_marks), "verdict": ev.verdict, "confidence": float(ev.confidence),
                    "reasoning": ev.reasoning, "warnings": list(dict.fromkeys(ev.ocr_warnings + warnings))})
    return out


def read_and_store(ops, hw, student_id: str, *, by: str, again: bool = False) -> Optional[str]:
    """Claim, read and record one submission. Returns None when read, the
    reason when it was not ("busy" when someone else holds it). Raises
    LLMNotEnabled with no key."""
    from ..config import LLMNotEnabled
    if not enabled():
        raise LLMNotEnabled()
    if not ops.claim_photo_read(hw.id, student_id, by=by, again=again):
        return "busy"
    return read_claimed(ops, hw, student_id, by=by)


def read_claimed(ops, hw, student_id: str, *, by: str) -> Optional[str]:
    """Read a submission the caller has claimed, and record the outcome --
    the readings, or why there are none -- so the claim never stays open.
    Returns None when read, else the reason."""
    from ..assessment.authz import students_without_consent
    from ..assessment.consent import get_consent_store
    from ..curriculum import routes as cr
    try:
        sub = ops.get_submission(hw.id, student_id)
        photos = ops.photos_for(hw.id, student_id)
        if sub is None or not photos:
            ops.finish_photo_read(hw.id, student_id, readings=[], failed="there are no photos to read")
            return "there are no photos to read"
        # Checked here, at the moment of sending, and not only when the read
        # was asked for: consent withdrawn in between stops the send.
        if students_without_consent(get_consent_store(cr._cfg.data_root), hw.school_id, [student_id]):
            ops.finish_photo_read(hw.id, student_id, readings=[],
                                  failed="no parental consent on record, so the photos were not sent to be read")
            return "no parental consent on record"
        readings = read_submission(hw, sub, photos)
    except Exception:
        log.warning("reading homework photos failed for %s/%s", hw.id, student_id, exc_info=True)
        ops.finish_photo_read(hw.id, student_id, readings=[],
                              failed="the photos could not be read just now; try again, or mark them by hand")
        raise
    ops.finish_photo_read(hw.id, student_id, readings=readings)
    from ..assessment.audit_log import get_audit_log
    get_audit_log(cr._cfg.data_root).append(
        "homework_photos_read", actor=by,
        details={"schoolId": hw.school_id, "homeworkId": hw.id, "studentId": student_id,
                 "photos": len(photos), "questions": [r["questionId"] for r in readings], "processor": "sarvam"})
    return None


def homework_photo_reading(ops, cs, users, notify, now: datetime) -> int:
    """The automation: read up to READ_PER_RUN waiting submissions per run,
    across schools. Nothing at all with no key. Returns how many were read."""
    if not enabled():
        return 0
    from .automations import _schools
    n = 0
    for school in _schools(cs):
        for hw, student_id in ops.photo_reads_waiting(school, READ_PER_RUN - n):
            try:
                # `again`: the query chose it as unread since its newest
                # photo; the claim still refuses one being read right now.
                if read_and_store(ops, hw, student_id, by="automation", again=True) is None:
                    n += 1
            except Exception:  # noqa: BLE001 - recorded as failed on the submission; the next one goes on
                log.warning("automatic photo reading failed for %s/%s", hw.id, student_id, exc_info=True)
            if n >= READ_PER_RUN:
                return n
    return n
