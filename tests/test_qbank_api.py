"""Scoped API keys, quotas (B8/B9), and the resource API (B6/B7)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.assessment import qbank_routes as routes
from academicos.assessment.api_keys import (
    FORBIDDEN_SCOPES,
    SCOPES,
    ApiKeyStore,
    QuotaExceeded,
    ScopeError,
    hash_key,
    validate_scopes,
)


@pytest.fixture
def store(tmp_path):
    s = ApiKeyStore(tmp_path / "keys.sqlite")
    yield s
    s.close()


# --------------------------------------------------------------------------- #
# B8 -- scoped keys
# --------------------------------------------------------------------------- #

def test_create_returns_the_plaintext_exactly_once(store):
    plaintext, key = store.create(school_id="school_1", scopes=["questions:read"],
                                  label="partner A")
    assert plaintext.startswith("acos_qb_")
    assert key.school_id == "school_1"
    assert key.active


def test_the_plaintext_is_never_stored(store):
    """A database dump must not be a set of usable credentials."""
    plaintext, key = store.create(school_id="s", scopes=["questions:read"])
    blob = "".join(
        str(v) for row in store.conn.execute("SELECT * FROM api_keys")
        for v in tuple(row)
    )
    assert plaintext not in blob
    assert hash_key(plaintext) in blob          # only the hash is present


def test_to_dict_does_not_leak_the_hash(store):
    _, key = store.create(school_id="s", scopes=["questions:read"])
    assert "keyHash" not in key.to_dict()
    assert "key_hash" not in key.to_dict()
    assert key.to_dict()["prefix"].startswith("acos_qb_")


def test_authenticate_resolves_a_live_key(store):
    plaintext, key = store.create(school_id="s", scopes=["questions:read"])
    got = store.authenticate(plaintext)
    assert got is not None and got.id == key.id
    assert got.last_used_at is not None


@pytest.mark.parametrize("presented", ["", "nope", "acos_qb_wrong", None])
def test_authenticate_refuses_everything_else(store, presented):
    store.create(school_id="s", scopes=["questions:read"])
    assert store.authenticate(presented) is None


def test_a_revoked_key_is_refused_but_still_resolvable(store):
    """Revoke, never delete: an incident review needs the record."""
    plaintext, key = store.create(school_id="s", scopes=["questions:read"])
    store.revoke(key.id)
    assert store.authenticate(plaintext) is None
    assert store.get(key.id) is not None            # the row survives
    assert store.get(key.id).revoked_at is not None


def test_scopes_are_validated_against_a_closed_vocabulary(store):
    with pytest.raises(ScopeError, match="unknown scope"):
        store.create(school_id="s", scopes=["questions:write"])


@pytest.mark.parametrize("scope", sorted(FORBIDDEN_SCOPES))
def test_scopes_that_could_reach_student_data_are_refused(store, scope):
    """`question-bank-api.md:119`: student-linked reads are never part of this
    API. Keeping student data out means making the permission unexpressible,
    not documenting that nobody should use it."""
    with pytest.raises(ScopeError, match="refused"):
        store.create(school_id="s", scopes=[scope])


def test_a_key_must_hold_at_least_one_scope(store):
    with pytest.raises(ScopeError, match="at least one"):
        store.create(school_id="s", scopes=[])


def test_the_forbidden_and_allowed_vocabularies_do_not_overlap():
    assert not (SCOPES & FORBIDDEN_SCOPES)


def test_keys_are_listed_per_school(store):
    store.create(school_id="a", scopes=["questions:read"])
    store.create(school_id="a", scopes=["facets:read"])
    store.create(school_id="b", scopes=["questions:read"])
    assert len(store.list_for_school("a")) == 2
    assert len(store.list_for_school("b")) == 1


# --------------------------------------------------------------------------- #
# B9 -- quotas
# --------------------------------------------------------------------------- #

def test_quota_allows_up_to_the_limit_then_refuses(store):
    _, key = store.create(school_id="s", scopes=["questions:read"],
                          quota_per_minute=3)
    for _ in range(3):
        store.check_quota(key)
    with pytest.raises(QuotaExceeded) as exc:
        store.check_quota(key)
    assert exc.value.retry_after >= 1


def test_quota_is_counted_in_the_database_not_in_memory(tmp_path):
    """A per-process counter lets N instances each allow the full quota, and
    resets to zero on redeploy -- exactly when an abuser wants it to."""
    db = tmp_path / "keys.sqlite"
    a = ApiKeyStore(db)
    plaintext, _ = a.create(school_id="s", scopes=["questions:read"],
                            quota_per_minute=2)
    b = ApiKeyStore(db)                          # a second process
    key = b.authenticate(plaintext)
    a.check_quota(key)
    a.check_quota(key)
    with pytest.raises(QuotaExceeded):
        b.check_quota(key)                       # b sees a's usage
    a.close()
    b.close()


def test_quota_is_per_key(store):
    _, k1 = store.create(school_id="s", scopes=["questions:read"], quota_per_minute=1)
    _, k2 = store.create(school_id="s", scopes=["questions:read"], quota_per_minute=1)
    store.check_quota(k1)
    store.check_quota(k2)                        # not affected by k1
    with pytest.raises(QuotaExceeded):
        store.check_quota(k1)


def test_a_zero_quota_is_refused(store):
    with pytest.raises(ValueError):
        store.create(school_id="s", scopes=["questions:read"], quota_per_minute=0)


# --------------------------------------------------------------------------- #
# B6/B7 -- the resource API
# --------------------------------------------------------------------------- #

def _bank(tmp_path: Path, count: int = 60) -> Path:
    records = []
    for i in range(count):
        records.append({
            "id": "cbse:q:src:{:024x}:{}".format(i, i + 1),
            "subject": "Science" if i % 2 == 0 else "Mathematics",
            "grade": 10,
            "marks": 1 + (i % 3),
            "type": "very_short_answer",
            "difficulty": "easy",
            "bloomLevel": "understand",
            "stem": "Question number {} about chemical reactions".format(i),
            "chapterIds": ["chemical-reactions"],
            "tags": ["Chemical Reactions"],
            "language": "en",
            "reviewState": "published",
            "version": 1,
            # The standalone-asset fields, as the enrichment pipeline writes
            # them. The fixture carries them so the API tests exercise the real
            # record shape rather than a reduced one.
            "rights": {"origin": "CBSE", "redistribution": "unknown",
                       "basis": "", "attribution": "CBSE previous year paper"},
            "provenance": {"sourceDocumentId": "src:deadbeef", "pageNumber": 4,
                           "method": "pdf_native", "confidence": 1.0},
            "calibration": {"measured": False, "sampleSize": 0, "basis": "assigned"},
            "answerScheme": (
                {"totalMarks": 1, "provenance": "cbse_marking_scheme",
                 "sourcePaperCode": "31/1/1",
                 "markingPoints": [{"id": "mp1", "description": "the answer",
                                    "marks": 1}]}
                if i % 4 == 0 else
                {"totalMarks": 1, "markingPoints": []}
            ),
        })
    path = tmp_path / "bank.json"
    path.write_text(json.dumps({"questions": records, "exportedCount": len(records)}),
                    encoding="utf-8")
    return path


@pytest.fixture
def client(tmp_path):
    routes.init(tmp_path / "keys.sqlite", _bank(tmp_path))
    app = FastAPI()
    app.include_router(routes.router)
    return TestClient(app), routes._store


def _headers(store, *, scopes=("questions:read",), quota=120):
    plaintext, _ = store.create(school_id="s", scopes=list(scopes),
                                quota_per_minute=quota)
    return {"Authorization": f"Bearer {plaintext}"}


def test_an_unauthenticated_request_is_401(client):
    c, _ = client
    r = c.get("/v1/questions")
    assert r.status_code == 401
    assert "WWW-Authenticate" in r.headers


def test_a_key_without_the_scope_is_403_not_404(client):
    """The key is valid; the permission is not held. That is a 403, and saying
    404 would send a consumer hunting for a route that exists."""
    c, store = client
    r = c.get("/v1/questions", headers=_headers(store, scopes=["facets:read"]))
    assert r.status_code == 403
    assert "questions:read" in r.json()["detail"]


# `include_unkeyed=true` below, wherever a test is about paging or filtering
# over the WHOLE fixture: rule Q1 makes the default path answer-keyed, so
# 45 of these 60 records are off it (tests/test_qbank_q1_q5.py owns that rule).
# These tests are about the cursor and the filters, and they need the full 60.
UNFILTERED = {"include_unkeyed": "true"}


def test_the_list_returns_items_and_total(client):
    c, store = client
    r = c.get("/v1/questions", params=UNFILTERED, headers=_headers(store))
    body = r.json()
    assert r.status_code == 200
    assert body["count"] == 25               # default page size
    assert body["totalMatching"] == 60
    assert body["nextCursor"]


def test_rate_limit_headers_are_always_present(client):
    """"Consumers cannot behave well without them." """
    c, store = client
    r = c.get("/v1/questions", headers=_headers(store, quota=77))
    assert r.headers["RateLimit-Limit"] == "77"
    assert "RateLimit-Policy" in r.headers


def test_cursor_paging_walks_the_whole_set_without_duplicates(client):
    """The property offset paging breaks under concurrent edits."""
    c, store = client
    h = _headers(store)
    seen, cursor, pages = [], None, 0
    while True:
        params = {"limit": 7, **UNFILTERED}
        if cursor:
            params["cursor"] = cursor
        body = c.get("/v1/questions", params=params, headers=h).json()
        seen.extend(i["id"] for i in body["items"])
        pages += 1
        cursor = body["nextCursor"]
        if not cursor:
            break
        assert pages < 20, "paging did not terminate"
    assert len(seen) == 60
    assert len(set(seen)) == 60                # no duplicates
    assert seen == sorted(seen)                # stable order


def test_the_last_page_has_no_cursor(client):
    c, store = client
    body = c.get("/v1/questions", params={"limit": 200, **UNFILTERED},
                 headers=_headers(store)).json()
    assert body["nextCursor"] is None
    assert body["count"] == 60


def test_a_corrupt_cursor_is_a_400_not_a_crash(client):
    c, store = client
    r = c.get("/v1/questions", params={"cursor": "!!!not-base64!!!"},
              headers=_headers(store))
    assert r.status_code == 400
    assert "cursor" in str(r.json()["detail"])


def test_filters_narrow_the_set(client):
    c, store = client
    r = c.get("/v1/questions", params={"subject": "Science", **UNFILTERED},
              headers=_headers(store)).json()
    assert r["totalMatching"] == 30
    assert all(i["subject"] == "Science" for i in r["items"])


def test_has_scheme_filter_uses_the_official_provenance(client):
    """Two thirds of the bank has an empty placeholder scheme. Filtering on
    "has a scheme" must mean "has an official one", or the filter is useless."""
    c, store = client
    r = c.get("/v1/questions", params={"has_scheme": "true"},
              headers=_headers(store)).json()
    assert r["totalMatching"] == 15            # every 4th of 60
    assert all(i["hasOfficialScheme"] for i in r["items"])


def test_the_list_projection_omits_the_scheme_body(client):
    """A page of 25 × four value points is several times the payload for
    information nobody reads in a list."""
    c, store = client
    item = c.get("/v1/questions", headers=_headers(store)).json()["items"][0]
    assert "answerScheme" not in item
    assert item["hasOfficialScheme"] in (True, False)


def test_facets_come_back_in_the_same_round_trip(client):
    c, store = client
    body = c.get("/v1/questions", params={"facets": "true", **UNFILTERED},
                 headers=_headers(store)).json()
    assert "facets" in body
    subjects = {f["value"]: f["count"] for f in body["facets"]["subject"]}
    assert subjects == {"Science": 30, "Mathematics": 30}


def test_the_facets_endpoint_needs_only_its_own_scope(client):
    c, store = client
    r = c.get("/v1/facets", headers=_headers(store, scopes=["facets:read"]))
    assert r.status_code == 200


def test_an_unknown_question_is_404(client):
    c, store = client
    r = c.get("/v1/questions/cbse:q:src:doesnotexist:1", headers=_headers(store))
    assert r.status_code == 404


def test_the_scheme_endpoint_returns_only_the_scheme(client):
    c, store = client
    qid = c.get("/v1/questions", params={"has_scheme": "true"},
                headers=_headers(store)).json()["items"][0]["id"]
    body = c.get(f"/v1/questions/{qid}/scheme", headers=_headers(store)).json()
    assert body["questionId"] == qid
    assert body["provenance"] == "cbse_marking_scheme"
    assert body["sourcePaperCode"] == "31/1/1"
    assert len(body["markingPoints"]) == 1
    assert "stem" not in body


def test_a_question_with_no_scheme_reports_none_rather_than_pretending(client):
    c, store = client
    qid = c.get("/v1/questions", params={"has_scheme": "false"},
                headers=_headers(store)).json()["items"][0]["id"]
    body = c.get(f"/v1/questions/{qid}/scheme", headers=_headers(store)).json()
    assert body["provenance"] == "none"
    assert body["markingPoints"] == []


def test_the_whole_question_includes_provenance_and_rights(client):
    c, store = client
    qid = c.get("/v1/questions", headers=_headers(store)).json()["items"][0]["id"]
    body = c.get(f"/v1/questions/{qid}", headers=_headers(store)).json()
    assert "provenance" in body and "rights" in body and "calibration" in body
    assert body["version"] >= 1


def test_an_over_quota_key_is_429_with_retry_after(client):
    """A burnt-through quota yields 429 with a Retry-After.

    The original test issued three live requests against a fresh key and hoped
    the third landed in the same fixed one-minute window. `check_quota` keys
    usage by a fixed window whose boundary is a minute edge, so on the rare run
    where the third request crossed that edge it saw a fresh window (count 0)
    and the assertion failed. Deterministic now: usage is pre-filled to the
    quota in BOTH the current and the next window, so whichever window the
    request lands in, the limit is already met.
    """
    from datetime import datetime, timedelta, timezone
    c, store = client
    plaintext, key = store.create(
        school_id="s", scopes=["questions:read"], quota_per_minute=2,
    )
    now = datetime.now(timezone.utc)
    windows = [
        now.replace(second=0, microsecond=0),
        (now + timedelta(minutes=1)).replace(second=0, microsecond=0),
    ]
    for w in windows:
        store.conn.execute(
            "INSERT INTO api_key_usage (key_id, window_start, count) "
            "VALUES (?,?,?) ON CONFLICT(key_id, window_start) "
            "DO UPDATE SET count = count + ?",
            (key.id, w.isoformat(), 2, 2),
        )
    store.conn.commit()

    h = {"Authorization": f"Bearer {plaintext}"}
    r = c.get("/v1/questions", headers=h)
    assert r.status_code == 429
    assert int(r.headers["Retry-After"]) >= 1


def test_limit_is_capped(client):
    c, store = client
    assert c.get("/v1/questions", params={"limit": 9999},
                 headers=_headers(store)).status_code == 422
    assert c.get("/v1/questions", params={"limit": 0},
                 headers=_headers(store)).status_code == 422


def test_the_x_api_key_header_also_works(client):
    c, store = client
    plaintext, _ = store.create(school_id="s", scopes=["questions:read"])
    r = c.get("/v1/questions", headers={"X-API-Key": plaintext})
    assert r.status_code == 200
