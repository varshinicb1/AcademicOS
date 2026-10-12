"""The Phase 1 pilot agreement: staff read it, only the principal accepts it,
for their own school only, against the exact text shown; the first
acceptance stands and is audited once."""
from __future__ import annotations

from test_homework import w  # noqa: F401 - `w` is a fixture


def _accept(w, who="p", **over):
    shown = w.c.get("/api/v1/pilot-agreement", headers=w.p).json()
    body = {"version": shown["version"], "sha256": shown["sha256"], "schoolLegalName": "Sunrise Public School",
            "signatoryName": "Priya Sharma", "designation": "Principal", "agree": True}
    body.update(over)
    return w.c.post("/api/v1/pilot-agreement/accept", json=body, headers=getattr(w, who))


def test_staff_read_it_and_it_starts_unaccepted(w):
    r = w.c.get("/api/v1/pilot-agreement", headers=w.p)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["version"] == "phase1-v2" and body["accepted"] is None
    assert body["title"] == "AcademicOS Phase 1 Pilot Agreement"
    assert "Part B. Confidentiality (mutual non-disclosure)" in body["text"]
    assert len(body["sha256"]) == 64
    assert w.c.get("/api/v1/pilot-agreement", headers=w.ana).status_code == 200
    assert w.c.get("/api/v1/pilot-agreement", headers=w.s1).status_code == 403


def test_the_principal_accepts_for_their_school_only(w):
    r = _accept(w)
    assert r.status_code == 200, r.text
    acc = r.json()["accepted"]
    assert acc["schoolLegalName"] == "Sunrise Public School" and acc["signatoryName"] == "Priya Sharma"
    assert acc["designation"] == "Principal" and acc["acceptedEmail"] == "p1@example.com"
    assert w.c.get("/api/v1/pilot-agreement", headers=w.ana).json()["accepted"]["signatoryName"] == "Priya Sharma"
    assert w.c.get("/api/v1/pilot-agreement", headers=w.p2).json()["accepted"] is None, "another school's is its own"


def test_only_the_principal_and_only_the_text_shown(w):
    assert _accept(w, "ana").status_code == 403
    assert _accept(w, sha256="0" * 64).status_code == 409
    assert _accept(w, version="phase1-v0").status_code == 409
    assert _accept(w, agree=False).status_code == 422
    assert _accept(w, signatoryName="  ").status_code == 422
    assert w.c.get("/api/v1/pilot-agreement", headers=w.p).json()["accepted"] is None


def test_the_first_acceptance_stands_and_is_audited_once(w):
    from academicos.assessment.audit_log import get_audit_log
    from academicos.operations import routes

    assert _accept(w).status_code == 200
    again = _accept(w, signatoryName="Someone Else", schoolLegalName="Another Name")
    assert again.status_code == 200
    assert again.json()["accepted"]["signatoryName"] == "Priya Sharma"
    entries = get_audit_log(routes._cfg.data_root).for_action("pilot_agreement_accepted")
    assert len(entries) == 1 and entries[0]["details"]["version"] == "phase1-v2"
    row = routes.store().pilot_acceptance("school_1")
    assert row["client_ip"] and row["text_sha256"] == entries[0]["details"]["sha256"]


def test_a_school_that_accepted_an_earlier_text_is_asked_again(w):
    """The text changed (v2, 2026-10-13: the company's name corrected). An
    acceptance of v1 stays on record, but it is not an acceptance of v2."""
    from academicos.assessment import auth_routes
    from academicos.operations import routes
    from academicos.operations.pilot_agreement import VERSION

    store = routes.store()
    principal = auth_routes._require().get_by_email("p1@example.com")
    store.accept_pilot(school_id="school_1", version="phase1-v1", sha256="1" * 64,
                       school_legal_name="Sunrise Public School", signatory_name="Priya Sharma",
                       designation="Principal", user=principal, client_ip=None, user_agent=None)
    shown = w.c.get("/api/v1/pilot-agreement", headers=w.p).json()
    assert VERSION == "phase1-v2" and shown["version"] == "phase1-v2"
    assert shown["accepted"] is None, "a v1 acceptance does not count for v2"
    assert "VidyuthLabs, which operates AcademicOS" in shown["text"] and "Vidyuth Labs" not in shown["text"]
    assert store.pilot_acceptance("school_1", "phase1-v1")["signatory_name"] == "Priya Sharma", "v1 kept"
    assert _accept(w).status_code == 200
    assert store.pilot_acceptance("school_1")["version"] == "phase1-v2"
