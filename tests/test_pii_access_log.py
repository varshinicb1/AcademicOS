"""Every read of a named student's data writes an audit entry.

Audit item 8.5 (2026-09-21), box 2 of docs/compliance.md's "before you ship"
list: access to student PII was logged for grading writes and paper exports
only. Reading a student's knowledge model or progress report, every student's
answer to one question, a scan's page photo or PDFs, or a consent record left
no trace, so "who looked at this child's work, and when" had no answer.

The contract held here, through the real routes of a booted app: each read
that serves a named student's data appends one `pii_read` entry to the
append-only audit log (Task 303) with the authenticated caller as `actor`,
the student as `student_id`, and what was read in `details["what"]`. A read
that covers many students at once (the class insight, the question-across-
students view, a consent listing) writes ONE entry listing the ids, not one
per student. A student reading their own knowledge is logged too.

Every store is under pytest's tmp_path; nothing touches a live service.
"""
from __future__ import annotations

import pytest

from academicos.api.main import app
from academicos.assessment import audit_log as audit_mod

from _auth_helpers import grant_consent, register_invited
from test_route_inventory import blueprint_body, question_body

GOOD_ANSWER = ("The solution is x = 2, obtained by subtracting 3 from both sides "
               "then dividing by 2.")


class World:
    def __init__(self, client, data_root, teacher, student, classmate, aid):
        self.client = client
        self.data_root = data_root
        self.teacher = teacher
        self.student = student
        self.classmate = classmate
        self.aid = aid
        self.t_auth = {"Authorization": f"Bearer {teacher['token']}"}
        self.s_auth = {"Authorization": f"Bearer {student['token']}"}

    @property
    def teacher_id(self) -> str:
        return self.teacher["user"]["id"]

    @property
    def student_id(self) -> str:
        return self.student["user"]["id"]

    @property
    def classmate_id(self) -> str:
        return self.classmate["user"]["id"]

    def reads(self) -> list[dict]:
        return audit_mod.get_audit_log(self.data_root).for_action(audit_mod.PII_READ_ACTION)

    def new_reads(self, before: int) -> list[dict]:
        """Entries appended since `before` reads existed (for_action is newest first)."""
        rows = sorted(self.reads(), key=lambda r: int(r["seq"]))
        return rows[before:]


@pytest.fixture
def world(tmp_path, monkeypatch):
    from academicos.assessment import consent as consent_mod
    from academicos.assessment import consent_routes as consent_routes_mod
    from academicos.assessment import users as users_mod
    from academicos.curriculum import store as curriculum_store_mod
    from fastapi.testclient import TestClient

    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr(audit_mod, "_INSTANCE", None)
    monkeypatch.setattr(users_mod, "_INSTANCE", None)
    monkeypatch.setattr(curriculum_store_mod, "_INSTANCE", None)
    monkeypatch.setattr(consent_mod, "_INSTANCE", None)
    monkeypatch.setattr(consent_routes_mod, "_store", None)
    monkeypatch.setattr(consent_routes_mod, "_audit", None)
    with TestClient(app) as client:
        teacher = register_invited(client, "school_1", "pii-t@example.com")
        student = register_invited(client, "school_1", "pii-s@example.com",
                                   name="Asha", role="student")
        classmate = register_invited(client, "school_1", "pii-c@example.com",
                                     name="Bala", role="student")
        t_auth = {"Authorization": f"Bearer {teacher['token']}"}
        created = client.post("/api/v1/assessments", json={
            "teacherId": teacher["user"]["id"], "schoolId": "school_1",
            "title": "PII reads", "subject": "Mathematics", "grade": 10,
            "chapterIds": [], "blueprint": blueprint_body(),
        }, headers=t_auth)
        assert created.status_code == 200, created.text
        w = World(client, tmp_path, teacher, student, classmate, created.json()["id"])
        grant_consent("school_1", w.student_id, w.classmate_id)
        for sid in (w.student_id, w.classmate_id):
            r = client.post("/api/v1/evaluations/sheet", json={
                "assessmentId": w.aid, "studentId": sid, "studentName": "S",
                "questions": [question_body()], "answers": {"q_1": GOOD_ANSWER},
                "correctOptions": {},
            }, headers=t_auth)
            assert r.status_code == 200, r.text
            # Finalizing records the sheet in the knowledge model, which the
            # knowledge and report reads below need something in.
            r = client.post(f"/api/v1/evaluations/sheet/{w.aid}/{sid}/finalize",
                            json={}, headers=t_auth)
            assert r.status_code == 200, r.text
        yield w


def _one_new_read(world: World, before: int, *, what: str) -> dict:
    new = world.new_reads(before)
    assert len(new) == 1, f"expected one pii_read entry for {what}, got {new}"
    entry = new[0]
    assert entry["details"]["what"] == what
    return entry


# --------------------------------------------------------------------------- #
# one student's data
# --------------------------------------------------------------------------- #

def test_a_teacher_reading_a_students_knowledge_is_logged(world):
    before = len(world.reads())
    r = world.client.get(f"/api/v1/knowledge/{world.student_id}", headers=world.t_auth)
    assert r.status_code == 200, r.text
    entry = _one_new_read(world, before, what="knowledge")
    assert entry["actor"] == world.teacher_id
    assert entry["student_id"] == world.student_id
    assert entry["timestamp"]


def test_a_student_reading_their_own_knowledge_is_logged_too(world):
    before = len(world.reads())
    r = world.client.get(f"/api/v1/knowledge/{world.student_id}", headers=world.s_auth)
    assert r.status_code == 200, r.text
    entry = _one_new_read(world, before, what="knowledge")
    assert entry["actor"] == world.student_id
    assert entry["student_id"] == world.student_id


def test_a_progress_report_download_is_logged(world):
    before = len(world.reads())
    r = world.client.get(f"/api/v1/knowledge/{world.student_id}/report", headers=world.t_auth)
    assert r.status_code == 200, r.text
    entry = _one_new_read(world, before, what="progress_report")
    assert entry["actor"] == world.teacher_id
    assert entry["student_id"] == world.student_id


def test_a_refused_read_is_not_logged_as_a_read(world):
    """A classmate's 403 served nothing, so it is not an access to log as one."""
    before = len(world.reads())
    r = world.client.get(f"/api/v1/knowledge/{world.classmate_id}", headers=world.s_auth)
    assert r.status_code == 403
    assert world.new_reads(before) == []


def test_reading_a_scan_sessions_answers_image_and_pdfs_is_logged(world):
    from academicos.assessment import mobile_scan

    created = world.client.post("/api/v1/scan/sessions", json={
        "assessmentId": world.aid, "studentId": world.student_id, "studentName": "Asha",
    }, headers=world.t_auth)
    assert created.status_code == 200, created.text
    session_id = created.json()["id"]

    # A captured page and both exports, written straight into the session:
    # capturing through the route would run OCR, which calls out to Sarvam.
    session = mobile_scan.get_session(session_id)
    files = world.data_root / "scan_fixture"
    files.mkdir()
    photo = files / "page_001.jpg"
    photo.write_bytes(b"\xff\xd8\xff\xe0 not really a jpeg")
    raw_pdf, corrected_pdf = files / "raw.pdf", files / "corrected.pdf"
    raw_pdf.write_bytes(b"%PDF-1.4 raw")
    corrected_pdf.write_bytes(b"%PDF-1.4 corrected")
    session.pages.append(mobile_scan.CapturedPage(
        page_no=1, raw_path=photo, processed_path=files / "missing.jpg",
        cropped=False, ocr_text=""))
    session.raw_pdf_path, session.corrected_pdf_path = raw_pdf, corrected_pdf
    mobile_scan.save_session(session)

    base = f"/api/v1/scan/sessions/{session_id}"
    for path, what in ((f"{base}/review", "scan_review"),
                       (f"{base}/pages/1/image", "scan_page_image"),
                       (f"{base}/raw-pdf", "scan_raw_pdf"),
                       (f"{base}/corrected-pdf", "scan_corrected_pdf")):
        before = len(world.reads())
        r = world.client.get(path, headers=world.t_auth)
        assert r.status_code == 200, f"{path}: {r.status_code} {r.text[:200]}"
        entry = _one_new_read(world, before, what=what)
        assert entry["actor"] == world.teacher_id
        assert entry["student_id"] == world.student_id
        assert entry["assessment_id"] == world.aid
        assert entry["details"]["scanSessionId"] == session_id


def test_reading_a_students_consent_record_is_logged(world):
    before = len(world.reads())
    r = world.client.get(f"/api/v1/consent/students/{world.student_id}", headers=world.t_auth)
    assert r.status_code == 200, r.text
    entry = _one_new_read(world, before, what="consent_record")
    assert entry["actor"] == world.teacher_id
    assert entry["student_id"] == world.student_id


# --------------------------------------------------------------------------- #
# many students in one read: one entry listing the ids
# --------------------------------------------------------------------------- #

def test_the_class_insight_writes_one_entry_listing_every_student(world):
    before = len(world.reads())
    r = world.client.get(f"/api/v1/insights/class/{world.aid}", headers=world.t_auth)
    assert r.status_code == 200, r.text
    entry = _one_new_read(world, before, what="class_insights")
    assert entry["actor"] == world.teacher_id
    assert entry["assessment_id"] == world.aid
    assert entry["student_id"] is None
    assert entry["details"]["studentIds"] == sorted([world.student_id, world.classmate_id])


def test_every_students_answer_to_one_question_writes_one_entry(world):
    before = len(world.reads())
    r = world.client.get(f"/api/v1/evaluations/assessment/{world.aid}/question/q_1",
                         headers=world.t_auth)
    assert r.status_code == 200, r.text
    entry = _one_new_read(world, before, what="answers_to_question")
    assert entry["actor"] == world.teacher_id
    assert entry["assessment_id"] == world.aid
    assert entry["details"]["questionId"] == "q_1"
    assert entry["details"]["studentIds"] == sorted([world.student_id, world.classmate_id])


def test_listing_the_schools_consent_records_writes_one_entry(world):
    before = len(world.reads())
    r = world.client.get("/api/v1/consent", headers=world.t_auth)
    assert r.status_code == 200, r.text
    entry = _one_new_read(world, before, what="consent_records")
    assert entry["actor"] == world.teacher_id
    assert entry["details"]["studentIds"] == sorted([world.student_id, world.classmate_id])


def test_checking_whose_consent_is_missing_writes_one_entry(world):
    before = len(world.reads())
    r = world.client.get("/api/v1/consent/missing",
                         params=[("studentIds", world.student_id), ("studentIds", "s_unknown")],
                         headers=world.t_auth)
    assert r.status_code == 200, r.text
    entry = _one_new_read(world, before, what="consent_status")
    assert entry["details"]["studentIds"] == sorted([world.student_id, "s_unknown"])


# --------------------------------------------------------------------------- #
# fail closed
# --------------------------------------------------------------------------- #

def test_a_read_the_audit_log_refuses_is_not_served(world, monkeypatch):
    """An access that cannot be logged is not served: the entry is written
    before the data leaves, and a refused append answers 503 (the same
    AuditAppendFailed a grading write gets) with no student data in it."""
    log = audit_mod.get_audit_log(world.data_root)

    def refuse(*_a, **_k):
        raise audit_mod.AuditAppendFailed(table="audit_log", op="insert", body="refused")

    monkeypatch.setattr(log, "append", refuse)
    r = world.client.get(f"/api/v1/knowledge/{world.student_id}", headers=world.t_auth)
    assert r.status_code == 503, r.text
    assert "concepts" not in r.text


# Every route family that logs a read, with a marker of the student data its
# 200 body would carry. Each has its own path to the log: pillar_routes'
# _log_read, consent_routes' _log_read (through _require_audit), and
# mobile_routes' two call sites per scan read (local file, then Storage).
def _refused_reads(world: World) -> list[tuple[str, str]]:
    return [
        (f"/api/v1/knowledge/{world.student_id}", "concepts"),
        (f"/api/v1/evaluations/assessment/{world.aid}/question/q_1", "reasoning"),
        (f"/api/v1/consent/students/{world.student_id}", "guardian"),
        ("/api/v1/consent", "guardian"),
    ]


def _refuse_every_append(monkeypatch) -> None:
    """On the class, so every route family's handle on the log refuses, not
    only the instance the test happened to fetch."""
    def refuse(*_a, **_k):
        raise audit_mod.AuditAppendFailed(table="audit_log", op="insert", body="refused")
    monkeypatch.setattr(audit_mod.AuditLog, "append", refuse)


@pytest.mark.parametrize("which", range(4))
def test_each_route_family_refuses_a_read_it_cannot_log(world, monkeypatch, which):
    path, marker = _refused_reads(world)[which]
    ok = world.client.get(path, headers=world.t_auth)
    assert ok.status_code == 200 and marker in ok.text, "the marker is really in the data"

    _refuse_every_append(monkeypatch)
    r = world.client.get(path, headers=world.t_auth)
    assert r.status_code == 503, f"{path}: {r.status_code} {r.text[:200]}"
    assert marker not in r.text


def test_a_consent_read_with_no_audit_log_is_a_503(world, monkeypatch):
    """consent_routes has its own way to lose the log: _require_audit()
    returns None when the log cannot be built, and _log_read refuses then."""
    from academicos.assessment import consent_routes as consent_routes_mod

    def unbuildable(*_a, **_k):
        raise RuntimeError("audit store cannot be opened")

    monkeypatch.setattr(consent_routes_mod, "_audit", None)
    monkeypatch.setattr(consent_routes_mod, "get_audit_log", unbuildable)
    for path in (f"/api/v1/consent/students/{world.student_id}", "/api/v1/consent"):
        r = world.client.get(path, headers=world.t_auth)
        assert r.status_code == 503, f"{path}: {r.status_code} {r.text[:200]}"
        assert "guardian" not in r.text


PHOTO = b"\xff\xd8\xff\xe0 handwriting"
RAW_PDF = b"%PDF-1.4 raw"
CORRECTED_PDF = b"%PDF-1.4 corrected"


def _scan_session(world: World, *, on_disk: bool) -> str:
    """A session with one captured page and both exports, written straight
    into the store (capturing through the route would run OCR, which calls
    Sarvam). With on_disk=False nothing is on the local disk and every
    artifact has only a Storage key: a Cloud Run instance that did not
    capture the session, whose disk is ephemeral anyway."""
    from academicos.assessment import mobile_scan

    created = world.client.post("/api/v1/scan/sessions", json={
        "assessmentId": world.aid, "studentId": world.student_id, "studentName": "Asha",
    }, headers=world.t_auth)
    assert created.status_code == 200, created.text
    session_id = created.json()["id"]
    session = mobile_scan.get_session(session_id)
    files = world.data_root / f"scan_fixture_{session_id}"
    files.mkdir()
    photo, raw_pdf, corrected_pdf = (files / "page_001.jpg", files / "raw.pdf",
                                     files / "corrected.pdf")
    if on_disk:
        photo.write_bytes(PHOTO)
        raw_pdf.write_bytes(RAW_PDF)
        corrected_pdf.write_bytes(CORRECTED_PDF)
    session.pages.append(mobile_scan.CapturedPage(
        page_no=1, raw_path=photo, processed_path=files / "missing.jpg",
        cropped=False, ocr_text="", raw_storage_key=f"{session_id}/raw/page_001.jpg",
        processed_storage_key=f"{session_id}/processed/page_001.jpg"))
    session.raw_pdf_path, session.corrected_pdf_path = raw_pdf, corrected_pdf
    session.raw_pdf_storage_key = f"{session_id}/raw.pdf"
    session.corrected_pdf_storage_key = f"{session_id}/corrected.pdf"
    mobile_scan.save_session(session)
    return session_id


def _storage_holding(session_id: str) -> dict[str, bytes]:
    return {f"{session_id}/processed/page_001.jpg": PHOTO,
            f"{session_id}/raw.pdf": RAW_PDF,
            f"{session_id}/corrected.pdf": CORRECTED_PDF}


_SCAN_READS = (("pages/1/image", "scan_page_image", PHOTO),
               ("raw-pdf", "scan_raw_pdf", RAW_PDF),
               ("corrected-pdf", "scan_corrected_pdf", CORRECTED_PDF))


@pytest.mark.parametrize("suffix,what,body", _SCAN_READS)
def test_a_scan_read_served_from_storage_is_logged_once(world, monkeypatch,
                                                        suffix, what, body):
    """On the GCP release this is the production path: the file is not on
    this instance's disk, so the route fetches it from Storage, and that
    branch logs the read separately from the disk branch."""
    from academicos.assessment import mobile_scan

    session_id = _scan_session(world, on_disk=False)
    stored = _storage_holding(session_id)
    monkeypatch.setattr(mobile_scan, "fetch_storage_bytes", lambda key: stored.get(key))
    before = len(world.reads())
    r = world.client.get(f"/api/v1/scan/sessions/{session_id}/{suffix}", headers=world.t_auth)
    assert r.status_code == 200, r.text
    assert r.content == body, "served from Storage, not the disk"
    entry = _one_new_read(world, before, what=what)
    assert entry["actor"] == world.teacher_id
    assert entry["student_id"] == world.student_id
    assert entry["details"]["scanSessionId"] == session_id


@pytest.mark.parametrize("on_disk", [True, False], ids=["disk", "storage"])
@pytest.mark.parametrize("suffix,what,body", _SCAN_READS)
def test_a_scan_read_the_log_refuses_is_not_served(world, monkeypatch, on_disk,
                                                   suffix, what, body):
    from academicos.assessment import mobile_scan

    session_id = _scan_session(world, on_disk=on_disk)
    stored = _storage_holding(session_id)
    monkeypatch.setattr(mobile_scan, "fetch_storage_bytes", lambda key: stored.get(key))
    _refuse_every_append(monkeypatch)
    r = world.client.get(f"/api/v1/scan/sessions/{session_id}/{suffix}", headers=world.t_auth)
    assert r.status_code == 503, f"{suffix}: {r.status_code} {r.text[:200]}"
    assert body not in r.content


def test_a_read_that_finds_nothing_is_not_logged(world, monkeypatch):
    """A 404 served no student data, so it is not an access to log: a page
    the session does not have, an export in neither place, and a progress
    report for a student with no graded answers."""
    from academicos.assessment import mobile_scan

    session_id = _scan_session(world, on_disk=False)
    monkeypatch.setattr(mobile_scan, "fetch_storage_bytes", lambda key: None)
    ungraded = register_invited(world.client, "school_1", "pii-u@example.com",
                                name="Chitra", role="student")
    base = f"/api/v1/scan/sessions/{session_id}"
    for path in (f"{base}/pages/2/image", f"{base}/pages/1/image",
                 f"{base}/raw-pdf", f"{base}/corrected-pdf",
                 f"/api/v1/knowledge/{ungraded['user']['id']}/report"):
        before = len(world.reads())
        r = world.client.get(path, headers=world.t_auth)
        assert r.status_code == 404, f"{path}: {r.status_code} {r.text[:200]}"
        assert world.new_reads(before) == [], path
