"""D38: the principal issues a question-bank API key on the running app and
it works against /v1 at once; it is shown once, scoped to the school,
revocable, and refused scopes that would reach student data."""
from __future__ import annotations

from test_blob_factory import clean_env, shared_gcs  # noqa: F401 - fixtures
from test_homework import w  # noqa: F401 - `w` is a fixture
from store_backend import sqlite_only


def test_a_minted_key_opens_v1_until_revoked(w, monkeypatch):
    from academicos.assessment import qbank_routes
    from academicos.assessment.qbank_engine import QuestionBank
    from test_homework import BANK
    monkeypatch.setattr(qbank_routes, "_bank", QuestionBank(BANK))
    r = w.c.post("/api/v1/api-keys", json={"label": "Partner LMS", "scopes": ["questions:read", "facets:read"]},
                 headers=w.p)
    assert r.status_code == 200, r.text
    body = r.json()
    key = body["key"]
    assert key.startswith("acos_qb_") and body["prefix"] == key[:14] and body["active"]
    listed = w.c.get("/api/v1/api-keys", headers=w.p).json()
    assert [k["id"] for k in listed] == [body["id"]] and "key" not in listed[0]

    unauth = w.c.get("/v1/coverage")
    assert unauth.status_code == 401
    ok = w.c.get("/v1/coverage", headers={"X-API-Key": key})
    assert ok.status_code == 200, ok.text
    assert w.c.get(f"/api/v1/api-keys/{body['id']}/usage", headers=w.p).status_code == 200

    assert w.c.delete(f"/api/v1/api-keys/{body['id']}", headers=w.p2).status_code == 404   # another school
    revoked = w.c.delete(f"/api/v1/api-keys/{body['id']}", headers=w.p).json()
    assert revoked["active"] is False
    assert w.c.get("/v1/coverage", headers={"X-API-Key": key}).status_code == 401


def test_scopes_and_who_may(w):
    bad = w.c.post("/api/v1/api-keys", json={"label": "x", "scopes": ["students:read"]}, headers=w.p)
    assert bad.status_code == 422 and "student data" in bad.json()["detail"]
    assert w.c.post("/api/v1/api-keys", json={"label": "x", "scopes": ["nope"]}, headers=w.p).status_code == 422
    assert w.c.post("/api/v1/api-keys", json={"label": "x", "scopes": ["questions:read"]},
                    headers=w.ana).status_code == 403
    assert w.c.get("/api/v1/api-keys", headers=w.p2).json() == []


def test_scopes_no_route_checks_are_refused_like_the_student_ones(w):
    """N-67-10: `papers:create` and `curriculum:read` gated nothing, yet the
    web offered the first and ticked the second by default. Refused at mint
    with a 422, as `students:read` is, saying "not yet" rather than "never"."""
    for scope in ("papers:create", "curriculum:read"):
        r = w.c.post("/api/v1/api-keys", json={"label": "x", "scopes": ["questions:read", scope]},
                     headers=w.p)
        assert r.status_code == 422 and "not available yet" in r.json()["detail"], scope
    ok = w.c.post("/api/v1/api-keys", json={"label": "x", "scopes": ["questions:read", "facets:read"]},
                  headers=w.p).json()
    assert ok["scopesAvailable"] == ["facets:read", "questions:read"]


def test_a_key_limited_to_classes_and_subjects_on_the_running_app(w, monkeypatch):
    """API-3: a key scoped to "which grades/subjects". Minted through the
    web's call, listed with its limits, audited, and held to them on /v1."""
    from academicos.assessment import qbank_routes
    from academicos.assessment.qbank_engine import QuestionBank
    from test_homework import BANK
    keyed = [dict(q, answerScheme={**q["answerScheme"], "provenance": "cbse_marking_scheme"}) for q in BANK]
    maths = dict(keyed[0], id="m1", subject="Mathematics")
    monkeypatch.setattr(qbank_routes, "_bank", QuestionBank(keyed + [maths]))

    typo = w.c.post("/api/v1/api-keys", json={"label": "x", "scopes": ["questions:read"],
                                              "subjects": ["Sceince"]}, headers=w.p)
    assert typo.status_code == 422 and "Sceince" in typo.json()["detail"] and "Science" in typo.json()["detail"]
    assert w.c.post("/api/v1/api-keys", json={"label": "x", "scopes": ["questions:read"], "grades": [13]},
                    headers=w.p).status_code == 422

    made = w.c.post("/api/v1/api-keys", json={"label": "Class 10 Science", "scopes": ["questions:read"],
                                              "grades": [10], "subjects": ["science"]}, headers=w.p)
    assert made.status_code == 200, made.text
    body = made.json()
    assert body["grades"] == [10] and body["subjects"] == ["Science"], "spelled as the bank spells it"
    listed = w.c.get("/api/v1/api-keys", headers=w.p).json()
    assert listed[0]["grades"] == [10] and listed[0]["subjects"] == ["Science"]

    h = {"X-API-Key": body["key"]}
    served = w.c.get("/v1/questions", headers=h).json()
    assert {i["subject"] for i in served["items"]} == {"Science"} and served["totalMatching"] == 4
    assert w.c.get("/v1/questions", params={"subject": "Mathematics"}, headers=h).status_code == 403
    assert w.c.get("/v1/questions/m1", headers=h).status_code == 403
    assert w.c.get("/v1/questions/q1", headers=h).status_code == 200


@sqlite_only
def test_the_store_keeps_keys_through_a_snapshot(shared_gcs, tmp_path):
    """With a blob store behind it, a key minted before a restart
    authenticates after one, on a container whose disk started empty."""
    from academicos.assessment import api_keys
    first = api_keys.ApiKeyStore(tmp_path / "a" / "keys.sqlite", durable=True)
    plaintext, _ = first.create(school_id="school_1", scopes=["questions:read"], label="x")
    first._snapshots.flush()
    first.close()
    second = api_keys.ApiKeyStore(tmp_path / "b" / "keys.sqlite", durable=True)
    assert second.authenticate(plaintext) is not None
    second.close()
