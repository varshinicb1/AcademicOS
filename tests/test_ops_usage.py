"""Per-school usage for the operator (NFR-7): behind the operator's key, counts
only, one row per school, the pilot agreement's acceptance shown."""
from __future__ import annotations

from test_homework import _create, w  # noqa: F401 - `w` is a fixture


def _usage(w, key="ops-test-key"):
    return w.c.get("/api/v1/ops/usage", headers={"X-Ops-Key": key} if key else {})


def test_usage_needs_the_operators_key(w, monkeypatch):
    assert _usage(w).status_code == 404, "no key configured: the route does not exist"
    monkeypatch.setenv("ACOS_OPS_KEY", "ops-test-key")
    assert _usage(w, key=None).status_code == 401
    assert _usage(w, key="wrong").status_code == 401
    assert w.c.get("/api/v1/ops/usage", headers=w.p).status_code == 401, "a principal's session is not the key"


def test_usage_counts_each_schools_people_and_work(w, monkeypatch):
    monkeypatch.setenv("ACOS_OPS_KEY", "ops-test-key")
    assert _create(w, "ana").status_code == 200
    shown = w.c.get("/api/v1/pilot-agreement", headers=w.p).json()
    w.c.post("/api/v1/pilot-agreement/accept", headers=w.p, json={
        "version": shown["version"], "sha256": shown["sha256"], "schoolLegalName": "School One",
        "signatoryName": "Priya", "designation": "Principal", "agree": True})
    r = _usage(w)
    assert r.status_code == 200, r.text
    rows = {row["schoolId"]: row for row in r.json()}
    one = rows["school_1"]
    assert (one["principals"], one["teachers"], one["students"]) == (1, 2, 3)
    assert one["homeworkLast30Days"] == 1 and one["pilotAgreementAcceptedAt"]
    assert one["lastActivity"] >= one["pilotAgreementAcceptedAt"][:10]
    assert "@" not in r.text, "counts only: no email addresses"
