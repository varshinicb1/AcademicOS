"""A supporting document on a leave request (v3 audit N-3-17; SCH-5 "attach
reason/document").

The leave request forbade any field it did not know, so sending a document
was a 422, and nothing stored one. Now a teacher attaches a small PDF or
image to their own request; the principal (or a delegated leave admin) of the
school reads it; nobody else does -- not another teacher of the school, not
another school's principal.

test_cover_routes' world: 2026-06-01 (MON) is a Monday and "today".
"""
from __future__ import annotations

from test_cover_routes import BASE, _apply, w  # noqa: F401 - `w` is a fixture

PDF = b"%PDF-1.4\n1 0 obj << >> endobj\ntrailer << >>\n%%EOF\n"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def _attach(w, leave_id, who, data=PDF, content_type="application/pdf", name="certificate.pdf"):
    headers = who if isinstance(who, dict) else w.t[who]
    return w.c.post(f"{BASE}/leave-requests/{leave_id}/document", headers=headers,
                    files={"file": (name, data, content_type)})


def test_a_teacher_attaches_a_document_the_principal_reads_it(w):
    leave = _apply(w, "ana", reason="fever", startDate="2026-06-02", endDate="2026-06-04").json()
    assert leave["document"] is None
    r = _attach(w, leave["id"], "ana")
    assert r.status_code == 200, r.text
    doc = r.json()["document"]
    assert (doc["contentType"], doc["size"], doc["name"]) == ("application/pdf", len(PDF), "certificate.pdf")

    # The principal sees it on the request and opens it.
    pending = w.c.get(f"{BASE}/leave-requests", params={"status": "pending"}, headers=w.p).json()
    assert next(l for l in pending if l["id"] == leave["id"])["document"]["name"] == "certificate.pdf"
    got = w.c.get(f"{BASE}/leave-requests/{leave['id']}/document", headers=w.p)
    assert got.status_code == 200 and got.content == PDF
    assert got.headers["content-type"] == "application/pdf"
    assert "no-store" in got.headers["cache-control"]
    # The teacher can read their own back.
    assert w.c.get(f"{BASE}/leave-requests/{leave['id']}/document", headers=w.t["ana"]).content == PDF

    # A second upload replaces the first.
    again = _attach(w, leave["id"], "ana", data=PNG, content_type="image/png", name="scan.png")
    assert again.status_code == 200 and again.json()["document"]["contentType"] == "image/png"
    assert w.c.get(f"{BASE}/leave-requests/{leave['id']}/document", headers=w.p).content == PNG

    # Reading it is on the audit log.
    from academicos.assessment.audit_log import get_audit_log
    from academicos.curriculum import routes as cr
    reads = get_audit_log(cr._cfg.data_root).for_action("leave_document_read")
    assert reads and reads[-1]["details"]["leaveId"] == leave["id"]


def test_another_teacher_and_another_schools_principal_cannot_read_it(w):
    leave = _apply(w, "ana").json()
    assert _attach(w, leave["id"], "ana").status_code == 200
    other_teacher = w.c.get(f"{BASE}/leave-requests/{leave['id']}/document", headers=w.t["bala"])
    assert other_teacher.status_code == 403
    other_school = w.c.get(f"{BASE}/leave-requests/{leave['id']}/document", headers=w.p2)
    assert other_school.status_code == 403
    student = w.c.get(f"{BASE}/leave-requests/{leave['id']}/document", headers=w.stu)
    assert student.status_code == 403
    # Nor may they attach one to her request.
    assert _attach(w, leave["id"], "bala").status_code == 403
    assert _attach(w, leave["id"], w.p2).status_code == 403


def test_the_principal_attaches_one_to_a_request_made_on_a_teachers_behalf(w):
    leave = _apply(w, w.p, teacherId=w.uid["dev"], reason="phoned in sick").json()
    assert _attach(w, leave["id"], w.p).status_code == 200
    assert w.c.get(f"{BASE}/leave-requests/{leave['id']}/document", headers=w.t["dev"]).status_code == 200


def test_only_a_small_pdf_or_image_is_taken(w):
    leave = _apply(w, "ana").json()
    big = _attach(w, leave["id"], "ana", data=b"%PDF-" + b"0" * (2 * 1024 * 1024))
    assert big.status_code == 413
    word = _attach(w, leave["id"], "ana", data=b"PK\x03\x04", content_type="application/msword", name="note.doc")
    assert word.status_code == 415
    renamed = _attach(w, leave["id"], "ana", data=b"not a pdf at all", name="fake.pdf")
    assert renamed.status_code == 415, "the first bytes must be the type it claims"
    assert _attach(w, leave["id"], "ana", data=b"").status_code == 422
    assert w.c.get(f"{BASE}/leave-requests/{leave['id']}/document", headers=w.p).status_code == 404


def test_a_closed_request_takes_no_document(w):
    leave = _apply(w, "ana").json()
    assert w.c.post(f"{BASE}/leave-requests/{leave['id']}/cancel", headers=w.t["ana"]).status_code == 200
    assert _attach(w, leave["id"], "ana").status_code == 409


def test_a_leave_for_named_periods_is_one_request(w):
    """The web now offers named periods; the API already took kind
    'periods' -- what the dialog sends is accepted and opens cover for just
    those periods."""
    r = _apply(w, "ana", kind="periods", periods=[2])
    assert r.status_code == 200 and r.json()["periods"] == [2], r.text
    d = w.c.post(f"{BASE}/leave-requests/{r.json()['id']}/decision", json={"approve": True}, headers=w.p).json()
    assert {(s["sectionId"], s["period"]) for s in d["substitutions"]} == {(w.b10, 2)}
