"""Erasing a student's or a parent's data on the school's request (NFR-1,
assessment/erasure.py): one student's data is put into every store, the
principal previews and erases it, and every store is read back. A second
student's data, the teachers' and the parent's own account must stay."""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

from _auth_helpers import grant_consent, register_invited
from test_cover_routes import w  # noqa: F401 - `w` is a fixture
from test_homework import _q

ANSWER = "chlorophyll-traps-light-ASHA-ONLY"   # a string only Asha's answers hold
PNG = b"\x89PNG\r\n\x1a\n" + b"asha-photo-bytes" * 8


def _me(w, headers) -> dict:
    return w.c.get("/api/v1/auth/me", headers=headers).json()


def _ops():
    from academicos.operations.routes import store
    return store()


def _homework(w):
    return _ops().create_homework(school_id="school_1", academic_year_id=w.year, teacher_id=w.uid["ana"],
                                  subject_id=w.sci10, subject_name="Science", grade=10, section_ids=[w.b10],
                                  title="Light worksheet", instructions="", chapter_ids=[],
                                  questions=[_q("q1", "short_answer", "Why are leaves green?", 1,
                                                 points=[("chlorophyll", "chlorophyll")])],
                                  due_date="2026-06-05",
                                  created_by=w.uid["ana"], publish=True)


def _seed(w, sid: str, name: str, hw, *, email: str) -> None:
    """Everything a student leaves behind, one row (or file) in each store."""
    from academicos.algorithms.learner_model import Interaction, LearnerModel
    from academicos.assessment import erasure, mobile_scan, pillar_routes
    from academicos.assessment.mobile_scan import ScanSession
    from academicos.assessment.remediation import PracticeSet

    ops = _ops()
    data_root = Path(erasure._cfg.data_root)
    ops.submit_homework(hw, student_id=sid, section_id=w.b10, answers={"q1": f"{ANSWER} {sid}"}, late=False)
    ops.notify(school_id="school_1", user_ids=[sid], kind="homework_assigned",
               params={"subject": "Science", "title": "Light worksheet", "due": "2026-06-05"},
               dedupe_key=f"hwassigned:{hw.id}:{sid}")
    ops.notify(school_id="school_1", user_ids=[w.uid["ana"]], kind="homework_submitted",
               params={"title": "Light worksheet", "student": name, "count": 1, "total": 2},
               dedupe_key=f"hwsubmitted:{hw.id}:{sid}-day")
    ops.set_settings(sid, language="hi")
    ops.set_digest(sid, "18:00")
    ops.register_device(sid, f"token-{sid}", "android")
    ops.feed_token(sid)
    ops.create_practice(student_id=sid, subject="Science", grade=10, chapter_ids=[], questions=[{"id": "q1"}])
    ops.save_marks("paper_1", [(sid, "q1", 1.0)], absent=[], present=[], entered_by=w.uid["ana"])
    with ops._conn_lock:
        ops.conn.execute("INSERT INTO learning_evidence (student_id, source_kind, source_id, subject, grade, "
                         "chapter_id, topic_id, question_id, outcome, occurred_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                         (sid, "homework", hw.id, "Science", 10, "light", None, "q1", 1.0, "2026-06-01T09:00:00"))
        ops.conn.execute("INSERT INTO sign_in_codes (email, code_hash, expires_at, created_at) VALUES (?,?,?,?)",
                         (email, "hash", "2099-01-01T00:00:00", "2026-06-01T09:00:00"))
        ops._commit()
    pillar_routes._require_graded().save("asmt_1", sid, [])
    pillar_routes._practice.save(PracticeSet(id=f"pset-{sid}", student_id=sid, concept_ids=["light"]),
                                 school_id="school_1")
    _, knowledge, _ = pillar_routes._require()
    knowledge.save(LearnerModel(learner_id=sid))
    erasure._events.append(sid, Interaction(concept_id="light", kind="answer", outcome=1.0))
    session = ScanSession(id=f"scan-{sid}", assessment_id="asmt_1", student_id=sid, student_name=name)
    mobile_scan.save_session(session)
    (mobile_scan._WORKDIR_ROOT / session.id / "raw").mkdir(parents=True, exist_ok=True)
    (mobile_scan._WORKDIR_ROOT / session.id / "raw" / "page_001.jpg").write_bytes(b"page")
    exports = data_root / "exports"
    exports.mkdir(parents=True, exist_ok=True)
    (exports / f"{session.id}_corrected.pdf").write_bytes(b"%PDF corrected")
    (exports / f"progress_{sid}_science.pdf").write_bytes(b"%PDF progress")


@pytest.fixture
def school(w):
    """Asha (w.stu) and Bina in 10-B, Asha's mother Meena, consent for both
    children, one homework both handed in (Asha with a photo), and every
    store holding something of each child."""
    from academicos.assessment.users import get_user_store  # noqa: F401 - the app's store is used below
    asha = _me(w, w.stu)
    bina_auth = register_invited(w.c, "school_1", "bina@example.com", name="Bina", role="student")
    bina = bina_auth["user"]
    w.store.enroll_student(school_id="school_1", student_id=bina["id"], section_id=w.b10)
    meena_auth = register_invited(w.c, "school_1", "meena@example.com", name="Meena", role="parent")
    meena = meena_auth["user"]
    grant_consent("school_1", asha["id"], bina["id"])
    ops = _ops()
    ops.link_guardian(parent_id=meena["id"], student_id=asha["id"], school_id="school_1", relation="mother",
                      created_by=_me(w, w.p)["id"])
    hw = _homework(w)
    r = w.c.post(f"/api/v1/my-homework/{hw.id}/photos", files={"file": ("work.png", PNG, "image/png")},
                 headers=w.stu)
    assert r.status_code == 200, r.text
    _seed(w, asha["id"], "Asha", hw, email="s1@example.com")
    _seed(w, bina["id"], "Bina", hw, email="bina@example.com")
    # A parent's marks notice about Asha, and the teacher's own unrelated notice.
    ops.notify(school_id="school_1", user_ids=[asha["id"], meena["id"]], kind="homework_graded",
               params={"subject": "Science", "title": "Light worksheet", "marks": "1 out of 1"},
               dedupe_key=f"hwgraded:{hw.id}:{asha['id']}:2026-06-01")
    ops.notify(school_id="school_1", user_ids=[w.uid["ana"]], kind="leave_decided",
               params={"decision": "approved", "start": "2026-06-01", "end": "2026-06-01"},
               dedupe_key="leave:l1:approved")
    ops.set_contact(meena["id"], phone="9876543210", sms_ok=True, whatsapp_ok=False)
    return SimpleNamespace(asha=asha["id"], bina=bina["id"], meena=meena["id"], hw=hw,
                           meena_h={"Authorization": f"Bearer {meena_auth['token']}"})


def _body(**over):
    return {"requestedBy": "parent", "requestReceivedOn": "2026-05-30", "confirmName": "Asha", **over}


def _held(sid: str) -> dict[str, int]:
    """What each store still holds of one student."""
    from academicos.assessment import erasure, mobile_scan, pillar_routes
    from academicos.assessment.consent import get_consent_store
    from academicos.operations.forget import ERASED
    ops = _ops()
    data_root = Path(erasure._cfg.data_root)
    out = {}
    with ops._conn_lock:
        for table, col in (("homework_submissions", "student_id"), ("homework_photos", "student_id"),
                           ("learning_evidence", "student_id"), ("practice_sets", "student_id"),
                           ("paper_marks", "student_id"), ("guardianships", "student_id"),
                           ("notifications", "user_id"), ("notification_settings", "user_id"),
                           ("notification_digests", "user_id"), ("device_tokens", "user_id"),
                           ("calendar_feeds", "user_id")):
            assert table in ERASED
            out[table] = ops.conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {col}=?", (sid,)).fetchone()[0]
    out["consent"] = int(get_consent_store(data_root).get_consent("school_1", sid) is not None)
    out["enrollment"] = int(_curriculum().enrollment_for_student(sid) is not None)
    out["graded"] = int(pillar_routes._require_graded().get("asmt_1", sid) is not None)
    out["remediation"] = int(pillar_routes._practice.get(f"pset-{sid}") is not None)
    out["learner_model"] = int(pillar_routes._require()[1]._path(sid).exists())
    out["events"] = len(erasure._events.events(sid))
    out["scan"] = int(mobile_scan._store.get(f"scan-{sid}") is not None)
    out["scan_files"] = int((mobile_scan._WORKDIR_ROOT / f"scan-{sid}").exists())
    out["exports"] = len(list((data_root / "exports").glob(f"*{sid}*")))
    out["photo_files"] = len(list((data_root / "homework-media").glob(f"*/{sid}/*")))
    out["account"] = int(_users().get(sid) is not None)
    return out


def _users():
    from academicos.assessment import auth_routes
    return auth_routes._require()


def _curriculum():
    from academicos.curriculum import routes as cr
    return cr._require()


def test_the_preview_counts_every_part_and_changes_nothing(w, school):
    before = _held(school.asha)
    r = w.c.get(f"/api/v1/auth/users/{school.asha}/erasure", headers=w.p)
    assert r.status_code == 200, r.text
    preview = r.json()
    counts = {p["part"]: p["count"] for p in preview["parts"]}
    assert preview["name"] == "Asha" and preview["role"] == "student" and preview["closed"] is False
    assert {k for k, v in counts.items() if v == 0} == set(), counts
    tables = next(p for p in preview["parts"] if p["part"] == "school_records")["tables"]
    # Her own 2 notices, plus 2 of other people's about her: the teacher's
    # "Asha handed in" and her mother's marks notice.
    assert tables["notifications"] == 4 and tables["homework_photos"] == 1 and tables["guardianships"] == 1
    assert {k["what"] for k in preview["kept"]} >= {"Audit log", "Backups"}
    assert _held(school.asha) == before
    # Reading what is held of her is a read of her data, and is logged.
    from academicos.assessment import erasure
    from academicos.assessment.audit_log import PII_READ_ACTION, get_audit_log
    reads = [e for e in get_audit_log(Path(erasure._cfg.data_root)).for_action(PII_READ_ACTION)
             if e["details"].get("what") == "erasure_preview"]
    assert [(e["student_id"], e["actor"]) for e in reads] == [(school.asha, _me(w, w.p)["id"])]


def test_erasure_deletes_every_part_of_one_student_and_nobody_elses(w, school):
    from academicos.assessment import erasure
    from academicos.assessment.audit_log import get_audit_log
    from academicos.assessment.consent import get_consent_store
    bina_before = _held(school.bina)
    # Each store holds something of her before (photo_files: hers only).
    assert {k for k, v in _held(school.asha).items() if not v} == set()
    r = w.c.post(f"/api/v1/auth/users/{school.asha}/erasure", json=_body(), headers=w.p)
    assert r.status_code == 200, r.text
    assert all(not p.get("error") for p in r.json()["parts"])
    assert {k: v for k, v in _held(school.asha).items() if v} == {}
    assert _held(school.bina) == bina_before
    # The account is gone: no sign-in, not on the roster.
    assert w.c.post("/api/v1/auth/login", json={"email": "s1@example.com", "password": "password123"}
                    ).status_code in (401, 403)
    assert w.c.get("/api/v1/auth/me", headers=w.stu).status_code == 401
    roster = w.c.get("/api/v1/auth/users", headers=w.p).json()
    assert school.asha not in {u["id"] for u in roster}
    # Other people's notices about her are gone; the teacher's own notice stays.
    ana_kinds = [n["kind"] for n in _ops().conn.execute(
        "SELECT kind, data_json FROM notifications WHERE user_id=?", (w.uid["ana"],)).fetchall()
        if "Asha" in n["data_json"] or n["kind"] == "leave_decided"]
    assert ana_kinds == ["leave_decided"]
    meena_kinds = [n["kind"] for n in _ops().conn.execute(
        "SELECT kind FROM notifications WHERE user_id=?", (school.meena,)).fetchall()]
    assert meena_kinds == []
    # Her mother keeps her own account and number; Bina keeps her consent.
    assert _users().get(school.meena) is not None and _ops().contact_for(school.meena) is not None
    assert get_consent_store(Path(erasure._cfg.data_root)).has_consent("school_1", school.bina)
    # One audit entry, by id: neither her name nor her email.
    [entry] = get_audit_log(Path(erasure._cfg.data_root)).for_action("personal_data_erased")
    assert entry["student_id"] == school.asha and entry["actor"] == _me(w, w.p)["id"]
    assert entry["details"]["requestedBy"] == "parent" and entry["details"]["failed"] == []
    assert entry["details"]["erased"]["account"] == 1
    assert "Asha" not in str(entry) and "s1@example.com" not in str(entry)
    # Erased once is gone: the id no longer names anyone.
    again = w.c.post(f"/api/v1/auth/users/{school.asha}/erasure", json=_body(), headers=w.p)
    assert again.status_code == 404


def _file_bytes(db_path) -> bytes:
    """The database and its WAL, as they are on disk (the WAL keeps earlier
    versions of every page until a checkpoint)."""
    return b"".join(f.read_bytes() for f in Path(db_path).parent.glob(Path(db_path).name + "*"))


def test_the_deleted_text_is_not_left_in_the_database_or_its_wal(w, school):
    """The snapshot uploaded to the blob store is this file, and the
    container disk holds the WAL. Some SQLite builds turn secure_delete on by
    default (Debian's) and some do not (the one Python bundles on Windows),
    so it is switched off here first: the erasure must turn it on itself, put
    the connection back, and empty the WAL of the earlier page versions."""
    ops = _ops()
    with ops._conn_lock:
        ops.conn.execute("PRAGMA secure_delete=OFF")
    before = _file_bytes(ops.db_path)
    assert f"{ANSWER} {school.asha}".encode() in before
    assert w.c.post(f"/api/v1/auth/users/{school.asha}/erasure", json=_body(), headers=w.p).status_code == 200
    with ops._conn_lock:
        assert ops.conn.execute("PRAGMA secure_delete").fetchone()[0] == 0
        raw = _file_bytes(ops.db_path)
    assert f"{ANSWER} {school.asha}".encode() not in raw
    assert f"{ANSWER} {school.bina}".encode() in raw


def test_only_the_schools_principal_erases_and_only_a_student_or_parent(w, school):
    from academicos.operations.routes import store
    url = f"/api/v1/auth/users/{school.asha}/erasure"
    # A teacher, even one holding the users capability, cannot.
    store().grant(school_id="school_1", user_id=w.uid["bala"], capability="users", scope=None,
                  granted_by=_me(w, w.p)["id"])
    for who in (w.t["bala"], w.t["ana"], w.stu, school.meena_h):
        assert w.c.get(url, headers=who).status_code == 403
        assert w.c.post(url, json=_body(), headers=who).status_code == 403
    # Another school's principal does not see her.
    assert w.c.get(url, headers=w.p2).status_code == 404
    assert w.c.post(url, json=_body(), headers=w.p2).status_code == 404
    # Staff are closed, not erased.
    teacher = w.c.post(f"/api/v1/auth/users/{w.uid['ana']}/erasure", json=_body(confirmName="Ana"), headers=w.p)
    assert teacher.status_code == 422 and "staff" in teacher.json()["detail"]
    # The name must match; the request cannot come from the future; no stray fields.
    assert w.c.post(url, json=_body(confirmName="Bina"), headers=w.p).status_code == 422
    assert w.c.post(url, json=_body(requestReceivedOn="2099-01-01"), headers=w.p).status_code == 422
    assert w.c.post(url, json=_body(requestedBy="teacher"), headers=w.p).status_code == 422
    assert w.c.post(url, json=_body(reason="x"), headers=w.p).status_code == 422
    assert _held(school.asha)["account"] == 1
    # Spacing and case in the typed name do not matter.
    ok = w.c.post(url, json=_body(confirmName="  asha "), headers=w.p)
    assert ok.status_code == 200, ok.text


def test_erasing_a_parent_keeps_the_consent_they_gave_and_the_childs_data(w, school):
    from academicos.assessment import erasure
    from academicos.assessment.consent import get_consent_store
    asha_before = _held(school.asha)
    url = f"/api/v1/auth/users/{school.meena}/erasure"
    preview = w.c.get(url, headers=w.p).json()
    assert [p["part"] for p in preview["parts"]] == ["school_records", "invites", "account"]
    r = w.c.post(url, json=_body(confirmName="Meena", requestedBy="parent"), headers=w.p)
    assert r.status_code == 200, r.text
    assert _users().get(school.meena) is None
    assert _ops().contact_for(school.meena) is None
    assert _ops().guardians_of(school.asha) == []
    assert get_consent_store(Path(erasure._cfg.data_root)).has_consent("school_1", school.asha)
    after = _held(school.asha)
    # Her own data is untouched; only the link to her mother is gone.
    assert {k: v for k, v in after.items() if v != asha_before[k]} == {"guardianships": 0}


def test_a_part_that_fails_leaves_the_account_closed_and_a_second_run_finishes(w, school, monkeypatch):
    from academicos.assessment import erasure
    from academicos.assessment.audit_log import get_audit_log
    from academicos.assessment.graded_store import GradedStore

    def down(self, student_id, *, dry_run=False):
        raise sqlite3.OperationalError("database is locked")
    url = f"/api/v1/auth/users/{school.asha}/erasure"
    with monkeypatch.context() as m:
        m.setattr(GradedStore, "erase_student", down)
        r = w.c.post(url, json=_body(), headers=w.p)
    assert r.status_code == 503 and "marked answer sheets" in r.json()["detail"]
    held = _held(school.asha)
    # Everything else went; the sheet and the (closed) account stay.
    assert {k: v for k, v in held.items() if v} == {"graded": 1, "account": 1}
    assert _users().get(school.asha).role == "left:student"
    assert w.c.get("/api/v1/auth/me", headers=w.stu).status_code == 401
    [entry] = get_audit_log(Path(erasure._cfg.data_root)).for_action("personal_data_erasure_incomplete")
    assert entry["details"]["failed"] == ["marked_sheets"]
    # The principal runs it again, on the closed account.
    assert w.c.get(url, headers=w.p).json()["closed"] is True
    r = w.c.post(url, json=_body(), headers=w.p)
    assert r.status_code == 200, r.text
    assert {k: v for k, v in _held(school.asha).items() if v} == {}


class _FakeBlobs:
    enabled = True

    def __init__(self, keys=()):
        self.objects = set(keys)
        self.deleted = []

    def upload(self, key, data, content_type):
        self.objects.add(key)

    def delete(self, key):
        self.deleted.append(key)
        self.objects.discard(key)

    def keys(self, prefix):
        return sorted(k for k in self.objects if k.startswith(prefix))


def test_the_blob_store_copies_are_deleted_too(w, school, monkeypatch):
    """Photos and scans are kept in GCS on the live release: erasure deletes
    the objects the rows name, and a scan's whole `<session>/` prefix."""
    from academicos.assessment import mobile_scan
    from academicos.operations import homework_photos
    photos = _FakeBlobs()
    scans = _FakeBlobs({f"scan-{school.asha}/raw/page_001.jpg", f"scan-{school.asha}/corrected.pdf",
                        f"scan-{school.bina}/raw/page_001.jpg"})
    monkeypatch.setattr(homework_photos, "_blobs", lambda: photos)
    monkeypatch.setattr(mobile_scan, "_storage", scans)
    [photo] = _ops().photos_of_student(school.asha)
    key = f"{school.hw.id}/{school.asha}/{photo['id']}.png"
    with _ops()._conn_lock:
        _ops().conn.execute("UPDATE homework_photos SET blob_key=? WHERE id=?", (key, photo["id"]))
    photos.objects.add(key)
    assert w.c.post(f"/api/v1/auth/users/{school.asha}/erasure", json=_body(), headers=w.p).status_code == 200
    assert photos.deleted == [key] and photos.objects == set()
    assert scans.objects == {f"scan-{school.bina}/raw/page_001.jpg"}


# ---------------- nothing that holds a person's data is left undecided ----------------


def test_every_operations_table_is_erased_or_kept_with_a_reason():
    from academicos.operations.forget import ERASED, KEPT
    from academicos.operations.store import OperationsStore
    conn = sqlite3.connect(":memory:")
    conn.executescript(OperationsStore.schema())
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")} - {"sqlite_sequence"}
    assert not set(ERASED) & set(KEPT)
    assert set(ERASED) | set(KEPT) == tables, (
        "a new operations table needs a line in operations/forget.py: what erasure deletes from it (ERASED, "
        "and the delete in forget_student/forget_parent), or why it holds no student's or parent's data (KEPT)")


def test_every_cloud_sql_table_is_erased_or_kept_with_a_reason():
    from academicos.assessment.erasure import DURABLE_ERASED_BY, DURABLE_KEPT, PARTS
    schema = (Path(__file__).resolve().parents[1] / "deploy" / "gcp" / "schema.sql").read_text(encoding="utf-8")
    tables = set(re.findall(r"^CREATE TABLE IF NOT EXISTS (\w+)", schema, re.M))
    assert set(DURABLE_ERASED_BY) | set(DURABLE_KEPT) == tables
    assert set(DURABLE_ERASED_BY.values()) <= {p.key for p in PARTS} | {"account"}


def test_the_curriculum_store_names_a_student_only_in_enrollments(tmp_path):
    from academicos.curriculum.store import CurriculumStore
    store = CurriculumStore(tmp_path / "curriculum.sqlite")
    named = {t for (t,) in store.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
             if any(c[1] in ("student_id", "parent_id", "guardian_id")
                    for c in store.conn.execute(f"PRAGMA table_info({t})"))}
    assert named == {"student_enrollments"}
