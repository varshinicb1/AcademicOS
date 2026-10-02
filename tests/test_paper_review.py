"""The paper review workflow (EX-6): author -> reviewer -> principal, with
changes sent back, everyone told at their step, and downloads audited."""
from __future__ import annotations

from test_assessment_routes_auth import _assessment_body
from test_homework import w  # noqa: F401 - `w` is a fixture


def _me(w, h):
    return w.c.get("/api/v1/auth/me", headers=h).json()["id"]


def _paper(w, aid="asmt_review_1"):
    r = w.c.post("/api/v1/assessments", json=_assessment_body(aid), headers=w.ana)
    assert r.status_code == 200, r.text
    aid = r.json()["id"]
    assert w.c.patch(f"/api/v1/assessments/{aid}/status", json={"status": "paperGenerated"},
                     headers=w.ana).status_code == 200
    return aid


def _inbox(w, h, kind):
    return [i for i in w.c.get("/api/v1/notifications", headers=h).json()["items"] if i["kind"] == kind]


def test_review_changes_then_approval(w):
    aid = _paper(w)
    bala = _me(w, w.bala)
    r = w.c.post(f"/api/v1/assessments/{aid}/review-request", json={"reviewerId": bala, "note": "Section C?"},
                 headers=w.ana)
    assert r.status_code == 200, r.text
    assert w.c.get(f"/api/v1/assessments/{aid}", headers=w.ana).json()["status"] == "underReview"
    [asked] = _inbox(w, w.bala, "paper_review_requested")
    assert asked["title"] == "Paper to review: Auth Test Assessment"
    assert [x["assessmentId"] for x in w.c.get("/api/v1/paper-reviews", headers=w.bala).json()] == [aid]

    decide = f"/api/v1/assessments/{aid}/review-decision"
    assert w.c.post(decide, json={"decision": "approve"}, headers=w.ana).status_code == 403   # not the reviewer
    assert w.c.post(decide, json={"decision": "changes"}, headers=w.bala).status_code == 422  # say what
    back = w.c.post(decide, json={"decision": "changes", "comment": "Q7 is out of syllabus"}, headers=w.bala)
    assert back.json()["state"] == "changes_requested"
    assert w.c.get(f"/api/v1/assessments/{aid}", headers=w.ana).json()["status"] == "paperGenerated"
    assert "Q7 is out of syllabus" in _inbox(w, w.ana, "paper_review_decided")[0]["body"]

    w.c.post(f"/api/v1/assessments/{aid}/review-request", json={"reviewerId": bala}, headers=w.ana)
    ok = w.c.post(decide, json={"decision": "approve"}, headers=w.bala).json()
    assert ok["state"] == "approved"
    alerts = [i for i in _inbox(w, w.p, "principal_alert") if i["title"].startswith("Paper ready to approve")]
    assert len(alerts) == 1
    history = w.c.get(f"/api/v1/assessments/{aid}/reviews", headers=w.p).json()
    assert [h["state"] for h in history] == ["changes_requested", "approved"]
    assert w.c.get("/api/v1/paper-reviews", headers=w.bala).json() == []
    assert len(w.c.get("/api/v1/paper-reviews", params={"state": ""}, headers=w.p).json()) == 2

    assert w.c.patch(f"/api/v1/assessments/{aid}/approve", headers=w.p).status_code == 200
    assert w.c.post(f"/api/v1/assessments/{aid}/review-request", json={"reviewerId": bala},
                    headers=w.ana).status_code == 409, "an approved paper is locked"


def test_who_may_review(w):
    aid = _paper(w)
    ana, bala = _me(w, w.ana), _me(w, w.bala)
    url = f"/api/v1/assessments/{aid}/review-request"
    assert w.c.post(url, json={"reviewerId": ana}, headers=w.ana).status_code == 422          # own paper
    assert w.c.post(url, json={"reviewerId": w.ids["s1"]}, headers=w.ana).status_code == 422  # a student
    assert w.c.post(url, json={"reviewerId": bala}, headers=w.bala).status_code == 403        # not the author
    assert w.c.post(url, json={"reviewerId": bala}, headers=w.s1).status_code == 403
    assert w.c.post(url, json={"reviewerId": bala}, headers=w.p2).status_code == 403
    assert w.c.post(url, json={"reviewerId": bala}, headers=w.p).status_code == 200            # the principal may
    assert w.c.post(f"/api/v1/assessments/{aid}/review-decision", json={"decision": "approve"},
                    headers=w.p).status_code == 200


def test_a_paper_a_colleague_approved_waits_in_the_principals_list(w):
    """QA P-12: once Bala approved it for the principal, the principal's
    Waiting tab said "Nothing to review" while the paper waited for them."""
    aid = _paper(w)
    bala = _me(w, w.bala)
    w.c.post(f"/api/v1/assessments/{aid}/review-request", json={"reviewerId": bala}, headers=w.ana)
    [waiting] = w.c.get("/api/v1/paper-reviews", headers=w.p).json()
    assert waiting["state"] == "pending" and waiting["awaitingPrincipal"] is False

    decide = f"/api/v1/assessments/{aid}/review-decision"
    assert w.c.post(decide, json={"decision": "approve"}, headers=w.bala).status_code == 200
    [waiting] = w.c.get("/api/v1/paper-reviews", headers=w.p).json()
    assert waiting["assessmentId"] == aid and waiting["state"] == "approved"
    assert waiting["awaitingPrincipal"] is True
    assert w.c.get("/api/v1/paper-reviews", headers=w.bala).json() == []   # not Bala's any more

    assert w.c.patch(f"/api/v1/assessments/{aid}/approve", headers=w.p).status_code == 200
    assert w.c.get("/api/v1/paper-reviews", headers=w.p).json() == []
    [done] = w.c.get("/api/v1/paper-reviews", params={"state": ""}, headers=w.p).json()
    assert done["awaitingPrincipal"] is False
