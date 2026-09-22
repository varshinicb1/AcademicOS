"""A school's own document uploads (`POST /api/v1/ingest/school-documents`),
end-to-end via starlette's TestClient (in-process, no uvicorn).

Covers docs/compliance.md's ingestion-source checklist for real: a file-type
allowlist, macros stripped from Office documents before storage, and a
mandatory copyright/license confirmation captured at upload time -- each
enforced by the route itself, not left to the caller's discretion. Every
accepted or rejected upload lands in the same append-only `audit_log` the
grading and paper-export paths use.
"""
from __future__ import annotations

import io
import zipfile

from fastapi.testclient import TestClient

from academicos.api.main import app
from academicos.assessment import audit_log

from _auth_helpers import invite_code


SCHOOL_ID = "school_1"


def _boot(tmp_path, monkeypatch):
    from academicos.assessment import users as users_mod

    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr(audit_log, "_INSTANCE", None)
    monkeypatch.setattr(users_mod, "_INSTANCE", None)
    return TestClient(app)


# Keyed by the TestClient object itself (not id()) so a recycled id can never
# hand one test another test's token.
_AUTH: dict[object, tuple[dict[str, str], str]] = {}


def _auth(client) -> tuple[dict[str, str], str]:
    """Register one teacher for SCHOOL_ID and return (headers, user_id).

    The ingest route now takes identity from the session rather than the form
    body, so every upload needs a real token. Cached per client so repeated
    uploads in one test reuse the same user rather than tripping
    EmailAlreadyRegistered."""
    cached = _AUTH.get(client)
    if cached is None:
        r = client.post("/api/v1/auth/register", json={
            "inviteCode": invite_code(SCHOOL_ID), "name": "Ingest Teacher",
            "email": "ingest-teacher@example.com",
            "password": "correct horse battery",
        })
        assert r.status_code == 200, r.text
        body = r.json()
        cached = ({"Authorization": f"Bearer {body['token']}"}, body["user"]["id"])
        _AUTH[client] = cached
    return cached


def _upload(client, *, filename: str, content: bytes, doc_type: str = "question_paper",
            copyright_confirmed: bool = True, school_id: str = SCHOOL_ID,
            uploader_id: str = "teacher_9"):
    """schoolId/uploaderId are still sent, because a real multipart client
    sends them -- but the route ignores them now (they used to BE the
    identity, letting an anonymous caller claim any school)."""
    headers, _ = _auth(client)
    return client.post(
        "/api/v1/ingest/school-documents",
        data={
            "schoolId": school_id, "uploaderId": uploader_id, "docType": doc_type,
            "copyrightConfirmed": str(copyright_confirmed).lower(), "title": "Real Upload",
        },
        files={"file": (filename, io.BytesIO(content), "application/octet-stream")},
        headers=headers,
    )


def _macro_docx_bytes() -> bytes:
    """A minimal, real OOXML zip carrying a macro payload the way an actual
    macro-enabled Word document does: a `word/vbaProject.bin` member and a
    Content_Types declaration for the macro-enabled main part."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "[Content_Types].xml",
            b'<?xml version="1.0"?><Types xmlns="ct">'
            b'<Override PartName="/word/document.xml" '
            b'ContentType="application/vnd.ms-word.document.macroEnabled.main+xml"/>'
            b"</Types>",
        )
        zf.writestr("word/document.xml", b"<w:document>hello</w:document>")
        zf.writestr("word/vbaProject.bin", b"\x00FAKE-VBA-MACRO-BYTECODE\x00")
    return buf.getvalue()


def _plain_docx_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "[Content_Types].xml",
            b'<?xml version="1.0"?><Types xmlns="ct">'
            b'<Override PartName="/word/document.xml" '
            b'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            b"</Types>",
        )
        zf.writestr("word/document.xml", b"<w:document>hello</w:document>")
    return buf.getvalue()


def test_valid_pdf_upload_is_registered_and_audited(tmp_path, monkeypatch):
    with _boot(tmp_path, monkeypatch) as client:
        r = _upload(client, filename="own_question_paper.pdf", content=b"%PDF-1.4 real enough bytes")
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["status"] == "registered"
        assert data["docType"] == "question_paper"
        assert data["macrosStripped"] is False
        assert data["duplicate"] is False
        assert data["sourceId"].startswith("src:")

        # Identity is the authenticated uploader, NOT the uploaderId the form
        # claimed ("teacher_9") -- that field is ignored now.
        _, user_id = _auth(client)
        entries = audit_log.get_audit_log(tmp_path).for_action("document_ingested")
        assert len(entries) == 1
        assert entries[0]["actor"] == user_id
        assert entries[0]["details"]["sourceId"] == data["sourceId"]
        assert entries[0]["details"]["schoolId"] == SCHOOL_ID


def test_missing_copyright_confirmation_rejected_400(tmp_path, monkeypatch):
    with _boot(tmp_path, monkeypatch) as client:
        r = _upload(client, filename="paper.pdf", content=b"%PDF-1.4 bytes",
                    copyright_confirmed=False)
        assert r.status_code == 400
        assert "copyright" in r.json()["detail"].lower()

        entries = audit_log.get_audit_log(tmp_path).for_action("document_ingest_rejected")
        assert len(entries) == 1
        assert "copyright" in entries[0]["details"]["reason"].lower()


def test_disallowed_extension_rejected_400(tmp_path, monkeypatch):
    with _boot(tmp_path, monkeypatch) as client:
        r = _upload(client, filename="script.exe", content=b"MZ fake exe bytes")
        assert r.status_code == 400
        assert "not accepted" in r.json()["detail"]

        entries = audit_log.get_audit_log(tmp_path).for_action("document_ingest_rejected")
        assert len(entries) == 1


def test_invalid_doc_type_rejected_400(tmp_path, monkeypatch):
    with _boot(tmp_path, monkeypatch) as client:
        r = _upload(client, filename="paper.pdf", content=b"%PDF-1.4 bytes",
                    doc_type="not_a_real_doc_type")
        assert r.status_code == 400
        assert "docType" in r.json()["detail"]


def test_empty_file_rejected_400(tmp_path, monkeypatch):
    with _boot(tmp_path, monkeypatch) as client:
        r = _upload(client, filename="empty.pdf", content=b"")
        assert r.status_code == 400
        assert "empty" in r.json()["detail"].lower()


def test_macro_bearing_docx_has_macros_stripped_before_storage(tmp_path, monkeypatch):
    with _boot(tmp_path, monkeypatch) as client:
        r = _upload(client, filename="scheme.docx", content=_macro_docx_bytes(),
                    doc_type="marking_scheme")
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["macrosStripped"] is True

        from academicos.assessment import ingest_routes
        cfg, registry, store = ingest_routes._require()
        row = registry.get(data["sourceId"])
        assert row is not None
        stored_bytes = store.get(row["file_key"], tmp_path / "readback.docx").read_bytes()
        with zipfile.ZipFile(io.BytesIO(stored_bytes)) as zf:
            names = zf.namelist()
            assert not any("vbaproject" in n.lower() for n in names)
            content_types = zf.read("[Content_Types].xml")
            assert b"macroEnabled" not in content_types


def test_macro_free_docx_is_untouched(tmp_path, monkeypatch):
    with _boot(tmp_path, monkeypatch) as client:
        original = _plain_docx_bytes()
        r = _upload(client, filename="paper.docx", content=original,
                    doc_type="question_paper")
        assert r.status_code == 200, r.text
        assert r.json()["macrosStripped"] is False

        from academicos.assessment import ingest_routes
        cfg, registry, store = ingest_routes._require()
        row = registry.get(r.json()["sourceId"])
        stored_bytes = store.get(row["file_key"], tmp_path / "readback2.docx").read_bytes()
        assert stored_bytes == original


def test_duplicate_upload_is_not_reregistered(tmp_path, monkeypatch):
    with _boot(tmp_path, monkeypatch) as client:
        content = b"%PDF-1.4 identical bytes twice"
        first = _upload(client, filename="paper.pdf", content=content)
        assert first.status_code == 200
        assert first.json()["duplicate"] is False

        second = _upload(client, filename="paper-again.pdf", content=content)
        assert second.status_code == 200
        assert second.json()["duplicate"] is True
        assert second.json()["sourceId"] == first.json()["sourceId"]

        from academicos.assessment import ingest_routes
        _, registry, _ = ingest_routes._require()
        assert registry.count() == 1

        # Both attempts are still individually audited.
        entries = audit_log.get_audit_log(tmp_path).for_action("document_ingested")
        assert len(entries) == 2
