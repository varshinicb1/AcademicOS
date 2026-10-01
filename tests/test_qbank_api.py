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


# --------------------------------------------------------------------------- #
# N-67-12 / D7 -- real filters, and no parameter silently dropped
# --------------------------------------------------------------------------- #

SUB_NUTRITION = "science-10/life-processes/nutrition/nutrition-in-human-beings"
TOPIC_NUTRITION = "science-10/life-processes/nutrition"
EXEMPLAR_X = "NCERT, Exemplar Problems, Class X Science"


def _rec(rid: str, *, subject="Science", grade=10, marks=1, qtype="mcq",
         source="cbse_board_paper", key="cbse_marking_scheme",
         attribution="Central Board of Secondary Education, previous year question paper",
         topics=(), subtopics=(), competencies=(), chapter="life-processes") -> dict:
    """A record in the shape the served bank carries (keys checked against
    academicos-data/syllabus/questions.json): `source`, `rights.attribution`,
    `topicIds`, `subtopicIds`, `competencyIds`, `taxonomyChapterId`."""
    scheme = ({"totalMarks": marks, "provenance": key, "modelAnswer": "",
               "markingPoints": [{"id": "mp1", "description": "the answer", "marks": marks}]}
              if key else {"totalMarks": marks, "provenance": "none", "markingPoints": []})
    return {
        "id": rid, "subject": subject, "grade": grade, "marks": marks, "type": qtype,
        "difficulty": "easy", "bloomLevel": "understand", "stem": f"Question {rid}",
        "chapterIds": [chapter], "taxonomyChapterId": f"{subject.lower()}-{grade}/{chapter}",
        "tags": [], "language": "en", "reviewState": "published", "version": 1,
        "source": source,
        "rights": {"origin": "CBSE", "redistribution": "unknown", "basis": "",
                   "attribution": attribution},
        "provenance": {"sourceDocumentId": f"doc:{rid}", "pageNumber": 1},
        "topicIds": list(topics), "subtopicIds": list(subtopics),
        "competencyIds": list(competencies), "answerScheme": scheme,
    }


def rich_records() -> list[dict]:
    return [
        _rec("r1", topics=[TOPIC_NUTRITION], subtopics=[SUB_NUTRITION], competencies=["C-10.3"]),
        _rec("r2", marks=3, qtype="short_answer", source="ncert_exemplar", key="ncert_exemplar_answer",
             attribution=EXEMPLAR_X, topics=["science-10/life-processes/transportation"]),
        _rec("r3", marks=3, qtype="short_answer", source="ncert_textbook", key="textbook_grounded",
             attribution="NCERT, Science, Class X", topics=[TOPIC_NUTRITION], subtopics=[SUB_NUTRITION]),
        _rec("r4", subject="Mathematics", grade=9, source="cbse_sample_paper",
             attribution="Central Board of Secondary Education, sample question paper and marking scheme"),
        _rec("r5", key=None, topics=[TOPIC_NUTRITION], subtopics=[SUB_NUTRITION]),   # no answer key
    ]


@pytest.fixture
def rich(tmp_path):
    path = tmp_path / "rich.json"
    path.write_text(json.dumps({"questions": rich_records()}), encoding="utf-8")
    routes.init(tmp_path / "rich-keys.sqlite", path)
    app = FastAPI()
    app.include_router(routes.router)
    return TestClient(app), routes._store


def _ids(c, store, params, path="/v1/questions"):
    r = c.get(path, params={**params, "limit": 200}, headers=_headers(store))
    assert r.status_code == 200, r.text
    return {i["id"] for i in r.json()["items"]}


@pytest.mark.parametrize("params, expected", [
    ({"topic_id": TOPIC_NUTRITION}, {"r1", "r3"}),            # r5 has it too, but no key (Q1)
    ({"competency": "C-10.3"}, {"r1"}),
    ({"source": "ncert_exemplar"}, {"r2"}),
    ({"source": "NCERT_Exemplar"}, {"r2"}),                     # case is ignored
    ({"trust": "checked"}, {"r3"}),
    ({"trust": "published"}, {"r1", "r2", "r4"}),
    ({"book": EXEMPLAR_X}, {"r2"}),
    ({"book": "  ncert, exemplar problems,   CLASS X science "}, {"r2"}),  # case and spacing
    ({"subject": "Science", "source": "cbse_board_paper"}, {"r1"}),
])
def test_each_new_filter_selects_on_a_field_the_records_carry(rich, params, expected):
    """N-67-12: `?book=`, `?topic_id=`, `?competency=`, `?source=` and
    `?trust=` were dropped, and each answered with the whole class."""
    c, store = rich
    assert _ids(c, store, params) == expected


def test_a_value_that_matches_nothing_is_an_empty_page_not_the_bank(rich):
    """The audit's repro: `?book=zzz` returned all 494 Science 10 records."""
    c, store = rich
    for name in ("book", "topic_id", "competency", "source"):
        body = c.get("/v1/questions", params={name: "zzz"}, headers=_headers(store)).json()
        assert body["totalMatching"] == 0, name


@pytest.mark.parametrize("method, path, params, unknown", [
    ("GET", "/v1/questions", {"subjct": "Science"}, ["subjct"]),          # D7, verbatim
    ("GET", "/v1/questions", {"subject": "Science", "chapter": "x"}, ["chapter"]),
    ("GET", "/v1/questions/r1", {"fields": "stem"}, ["fields"]),
    ("GET", "/v1/questions/r1/scheme", {"x": "1"}, ["x"]),
    ("GET", f"/v1/subtopics/{SUB_NUTRITION}/questions", {"subject": "Science"}, ["subject"]),
    ("GET", "/v1/facets", {"marks": "1", "book": "x"}, ["book", "marks"]),
    ("GET", "/v1/coverage", {"grade": "10"}, ["grade"]),
    ("POST", "/v1/homework-sets", {"dry_run": "1"}, ["dry_run"]),
])
def test_an_unknown_query_parameter_is_a_422_naming_it(rich, method, path, params, unknown):
    """D7: `?subjct=Science` answered with all 5,319 records. A parameter the
    route does not take is now a 422 in FastAPI's own validation shape, with
    `loc` naming it, on every /v1 route."""
    c, store = rich
    h = _headers(store, scopes=("questions:read", "facets:read"))
    body = {"subject": "Science", "grade": 10, "count": 1} if method == "POST" else None
    r = c.request(method, path, params=params, json=body, headers=h)
    assert r.status_code == 422, r.text
    detail = r.json()["detail"]
    assert sorted(d["loc"] for d in detail) == [["query", n] for n in unknown]
    assert all(d["type"] == "extra_forbidden" for d in detail)
    assert all(repr(d["loc"][1]) in d["msg"] for d in detail)


def test_every_declared_parameter_is_still_accepted(rich):
    """The check reads the route's own signature, so nothing it declares,
    including an alias (`type`), is refused."""
    c, store = rich
    params = {"subject": "Science", "grade": 10, "marks": 1, "type": "mcq",
              "difficulty": "easy", "bloom": "understand", "chapter_id": "life-processes",
              "subtopic_id": SUB_NUTRITION, "topic_id": TOPIC_NUTRITION, "competency": "C-10.3",
              "source": "cbse_board_paper", "trust": "published",
              "book": "Central Board of Secondary Education, previous year question paper",
              "has_scheme": "true", "key_provenance": "cbse_marking_scheme",
              "review_state": "published", "keyword": "r1", "limit": 5, "facets": "true",
              "include_unkeyed": "false"}
    r = c.get("/v1/questions", params=params, headers=_headers(store))
    assert r.status_code == 200, r.text
    assert [i["id"] for i in r.json()["items"]] == ["r1"]


def test_authentication_is_answered_before_the_parameters(rich):
    """A caller with no key learns nothing about the parameters: 401 first."""
    c, _ = rich
    assert c.get("/v1/questions", params={"subjct": "Science"}).status_code == 401


def test_trust_is_a_closed_vocabulary(rich):
    c, store = rich
    h = _headers(store)
    typo = c.get("/v1/questions", params={"trust": "official"}, headers=h)
    assert typo.status_code == 400
    assert "published" in typo.json()["detail"]["detail"]
    both = c.get("/v1/questions", params={"trust": "checked", "has_scheme": "false"}, headers=h)
    assert both.status_code == 400 and both.json()["detail"]["title"] == "contradictory filters"


def test_the_facets_name_the_new_filters_vocabulary(rich):
    """A book's exact name cannot be guessed, so the facet is where it is read."""
    c, store = rich
    facets = c.get("/v1/questions", params={"facets": "true", "subject": "Science"},
                   headers=_headers(store)).json()["facets"]
    assert {f["value"] for f in facets["book"]} >= {EXEMPLAR_X, "NCERT, Science, Class X"}
    assert {f["value"]: f["count"] for f in facets["keyTier"]} == {"published": 2, "checked": 1}
    assert {f["value"] for f in facets["source"]} == {"cbse_board_paper", "ncert_exemplar", "ncert_textbook"}
    item = c.get("/v1/questions", params={"source": "ncert_exemplar"}, headers=_headers(store)).json()["items"][0]
    assert item["book"] == EXEMPLAR_X and item["source"] == "ncert_exemplar" and item["keyTier"] == "published"


def test_the_next_link_keeps_the_filters(client):
    """`Link` was the bare path plus `?cursor=`, so following it paged the
    whole bank from page two."""
    c, store = client
    h = _headers(store)
    first = c.get("/v1/questions", params={"subject": "Science", "limit": 7, **UNFILTERED}, headers=h)
    link = first.headers["Link"]
    assert "subject=Science" in link and "cursor=" in link
    nxt = c.get(link[1:link.index(">")], headers=h).json()
    assert nxt["items"] and all(i["subject"] == "Science" for i in nxt["items"])
    assert nxt["items"][0]["id"] > first.json()["items"][-1]["id"]


# --------------------------------------------------------------------------- #
# D52 -- a real subtopic id on the path route
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("encoded", [False, True])
def test_a_real_subtopic_id_with_slashes_works_on_the_path_route(rich, encoded):
    """Every real subtopic id carries slashes, and the path route answered 404
    for all 87 while `?subtopic_id=` found them. Raw or percent-encoded, the
    path route now selects exactly what the query filter selects."""
    c, store = rich
    sid = SUB_NUTRITION.replace("/", "%2F") if encoded else SUB_NUTRITION
    r = c.get(f"/v1/subtopics/{sid}/questions", headers=_headers(store))
    assert r.status_code == 200, r.text
    assert r.json()["subtopicId"] == SUB_NUTRITION
    by_path = {i["id"] for i in r.json()["items"]}
    assert by_path == _ids(c, store, {"subtopic_id": SUB_NUTRITION}) == {"r1", "r3"}
    opened = c.get(f"/v1/subtopics/{sid}/questions", params={"include_unkeyed": "true"},
                   headers=_headers(store)).json()
    assert {i["id"] for i in opened["items"]} == {"r1", "r3", "r5"}


# --------------------------------------------------------------------------- #
# N-67-11 -- homework sets: a marks mix, topics, and `count` with types
# --------------------------------------------------------------------------- #

def homework_records() -> list[dict]:
    """36 keyed Science 10 records over three chapters, four mark values and
    three types, each chapter its own topic and subtopic."""
    out = []
    for i in range(36):
        chapter = ("light", "life-processes", "electricity")[i % 3]
        out.append(_rec(f"h{i:02d}", marks=(1, 2, 3, 5)[i % 4],
                        qtype=("mcq", "short_answer", "long_answer")[(i // 3) % 3],
                        chapter=chapter, topics=[f"science-10/{chapter}/t"],
                        subtopics=[f"science-10/{chapter}/t/s"]))
    return out


@pytest.fixture
def hw(tmp_path):
    path = tmp_path / "hw.json"
    path.write_text(json.dumps({"questions": homework_records()}), encoding="utf-8")
    routes.init(tmp_path / "hw-keys.sqlite", path)
    app = FastAPI()
    app.include_router(routes.router)
    c, store = TestClient(app), routes._store
    h = _headers(store)
    return lambda body: c.post("/v1/homework-sets",
                               json={"subject": "Science", "grade": 10, **body}, headers=h)


def test_a_marks_mix_returns_that_many_of_each_mark(hw):
    from collections import Counter
    r = hw({"marks": {"1": 4, "3": 2}})
    assert r.status_code == 200, r.text
    body = r.json()
    assert Counter(i["marks"] for i in body["items"]) == {1: 4, 3: 2}
    assert body["requested"] == 6 and body["count"] == 6 and body["shortfall"] == {}
    assert len({i["id"] for i in body["items"]}) == 6
    assert hw({"marks": {"1": 4, "3": 2}}).json()["items"] == body["items"], "same request, same set"


def test_a_marks_mix_reports_the_shortfall_per_mark(hw):
    body = hw({"marks": {"2": 3, "4": 2}}).json()
    assert body["shortfall"] == {"4": 2}
    assert [i["marks"] for i in body["items"]] == [2, 2, 2]


def test_types_as_a_list_honour_count(hw):
    """N-67-11: with `types` the `count` was ignored. A list of types now
    means "`count` questions of these types", spread across them."""
    body = hw({"types": ["mcq", "short_answer"], "count": 7}).json()
    assert body["count"] == 7 and body["requested"] == 7 and body["shortfall"] == {}
    types = [i["type"] for i in body["items"]]
    assert set(types) == {"mcq", "short_answer"}
    assert abs(types.count("mcq") - types.count("short_answer")) <= 1


def test_a_types_mix_and_a_count_must_agree(hw):
    disagree = hw({"types": {"mcq": 3, "short_answer": 2}, "count": 10})
    assert disagree.status_code == 422
    assert "adds up to 5" in disagree.text
    agree = hw({"types": {"mcq": 3, "short_answer": 2}, "count": 5}).json()
    assert agree["count"] == 5 and agree["requested"] == 5


def test_a_marks_mix_and_a_types_mix_together_are_refused(hw):
    r = hw({"marks": {"1": 2}, "types": {"mcq": 2}})
    assert r.status_code == 422 and "not both" in r.text


def test_a_marks_mix_chooses_types_from_a_list(hw):
    body = hw({"marks": {"1": 3}, "types": ["mcq"]}).json()
    assert body["count"] == 3
    assert all(i["marks"] == 1 and i["type"] == "mcq" for i in body["items"])


def test_topics_and_subtopics_narrow_the_set(hw):
    by_topic = hw({"topicIds": ["science-10/electricity/t"], "count": 20}).json()
    assert by_topic["available"] == 12 and by_topic["count"] == 12
    assert by_topic["shortfall"] == {"any": 8}
    by_sub = hw({"subtopicIds": ["science-10/light/t/s"], "marks": {"1": 2}}).json()
    assert by_sub["count"] == 2
    assert all(i["chapterIds"] == ["light"] for i in by_sub["items"])
    assert hw({"marks": {"0": 1}}).status_code == 422


# --------------------------------------------------------------------------- #
# N-67-10 -- keys limited to classes and subjects; Retry-After; dead scopes
# --------------------------------------------------------------------------- #

def test_a_key_stores_its_classes_and_subjects(tmp_path):
    db = tmp_path / "keys.sqlite"
    a = ApiKeyStore(db)
    plaintext, key = a.create(school_id="s", scopes=["questions:read"],
                              grades=[10, 9, 10], subjects=[" Science ", "Mathematics"])
    assert key.grades == {9, 10} and key.subjects == {"Science", "Mathematics"}
    assert key.to_dict()["grades"] == [9, 10]
    b = ApiKeyStore(db)
    assert b.authenticate(plaintext).subjects == {"Science", "Mathematics"}
    with pytest.raises(ValueError):
        a.create(school_id="s", scopes=["questions:read"], grades=[13])
    a.close()
    b.close()


def test_a_store_from_before_the_limits_opens_and_reads_unlimited(tmp_path):
    """The live store is restored from a snapshot made before the columns
    existed; `CREATE TABLE IF NOT EXISTS` would leave it without them."""
    import sqlite3
    db = tmp_path / "old.sqlite"
    conn = sqlite3.connect(db)
    conn.executescript("""
        CREATE TABLE api_keys (id TEXT PRIMARY KEY, key_hash TEXT NOT NULL UNIQUE,
          prefix TEXT NOT NULL, label TEXT NOT NULL DEFAULT '', school_id TEXT NOT NULL,
          scopes TEXT NOT NULL, quota_per_min INTEGER NOT NULL, created_at TEXT NOT NULL,
          created_by TEXT NOT NULL DEFAULT '', last_used_at TEXT, revoked_at TEXT);
    """)
    conn.execute("INSERT INTO api_keys VALUES ('key_old', ?, 'acos_qb_old', 'old', 's', "
                 "'questions:read,curriculum:read', 120, '2026-09-01T00:00:00+00:00', '', NULL, NULL)",
                 (hash_key("acos_qb_oldkey"),))
    conn.commit()
    conn.close()
    store = ApiKeyStore(db)
    old = store.authenticate("acos_qb_oldkey")
    assert old is not None and not old.limited and old.may("questions:read")
    _, new = store.create(school_id="s", scopes=["questions:read"], grades=[10])
    assert new.grades == {10}
    store.close()


@pytest.fixture
def limited(client):
    """The 60-record bank (Science and Mathematics, class 10) and a key
    limited to class 10 Science."""
    c, store = client
    plaintext, _ = store.create(school_id="s", scopes=["questions:read", "facets:read"],
                                grades=[10], subjects=["Science"])
    return c, store, {"X-API-Key": plaintext}


def test_a_limited_key_reads_only_its_classes_and_subjects(limited):
    c, _, h = limited
    body = c.get("/v1/questions", params={"limit": 200, **UNFILTERED}, headers=h).json()
    assert body["totalMatching"] == 30 and {i["subject"] for i in body["items"]} == {"Science"}
    facets = c.get("/v1/facets", params=UNFILTERED, headers=h).json()
    assert {f["value"] for f in facets["subject"]} == {"Science"}
    coverage = c.get("/v1/coverage", headers=h).json()
    assert set(coverage["subjects"]) == {"Science"} and coverage["questions"] == 30


@pytest.mark.parametrize("method, path, params, body", [
    ("GET", "/v1/questions", {"subject": "Mathematics"}, None),
    ("GET", "/v1/questions", {"grade": 9}, None),
    ("GET", "/v1/facets", {"subject": "mathematics"}, None),
    ("POST", "/v1/homework-sets", {}, {"subject": "Mathematics", "grade": 10}),
    ("POST", "/v1/homework-sets", {}, {"subject": "Science", "grade": 9}),
])
def test_asking_outside_a_keys_limits_is_a_403(limited, method, path, params, body):
    """403, not an empty page: an empty page reads as "the bank has none",
    when the truth is "this key may not read them"."""
    c, _, h = limited
    r = c.request(method, path, params=params, json=body, headers=h)
    assert r.status_code == 403, r.text
    assert "limited to" in r.json()["detail"]


def test_a_record_outside_a_keys_limits_is_a_403_by_id(limited):
    c, store, h = limited
    maths = c.get("/v1/questions", params={"subject": "Mathematics", **UNFILTERED},
                  headers=_headers(store)).json()["items"][0]["id"]
    science = c.get("/v1/questions", params={"subject": "Science"}, headers=h).json()["items"][0]["id"]
    for suffix in ("", "/scheme"):
        assert c.get(f"/v1/questions/{maths}{suffix}", headers=h).status_code == 403
        assert c.get(f"/v1/questions/{science}{suffix}", headers=h).status_code == 200


def test_a_limited_key_is_inside_on_the_names_its_limit_uses(limited):
    """Subjects compare case-insensitively, like the `subject` filter."""
    c, _, h = limited
    assert c.get("/v1/questions", params={"subject": "science", "grade": 10}, headers=h).status_code == 200


@pytest.mark.parametrize("second, expected", [(42.5, 18), (0.0, 60), (59.9, 1), (30.0, 30)])
def test_retry_after_is_the_seconds_left_in_the_window(store, monkeypatch, second, expected):
    """It was `60 - window.second` with the window's seconds zeroed: always
    60, so a client honouring it waited a minute for a window two seconds off."""
    from datetime import datetime, timedelta, timezone

    from academicos.assessment import api_keys
    at = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc) + timedelta(seconds=second)
    monkeypatch.setattr(api_keys, "_now", lambda: at)
    _, key = store.create(school_id="s", scopes=["questions:read"], quota_per_minute=1)
    store.check_quota(key)
    with pytest.raises(QuotaExceeded) as exc:
        store.check_quota(key)
    assert exc.value.retry_after == expected


@pytest.mark.parametrize("scope", ["papers:create", "curriculum:read"])
def test_scopes_no_route_checks_are_refused_as_not_available_yet(store, scope):
    """N-67-10: both gated nothing, and the web offered `papers:create`."""
    with pytest.raises(ScopeError, match="not available yet"):
        store.create(school_id="s", scopes=["questions:read", scope])
    assert scope not in SCOPES
    assert SCOPES == {"questions:read", "facets:read"}


# --------------------------------------------------------------------------- #
# API-6 -- the OpenAPI document says how to authenticate and what can fail
# --------------------------------------------------------------------------- #

def test_the_openapi_declares_the_key_schemes_and_every_error(client):
    c, _ = client
    spec = c.app.openapi()
    schemes = spec["components"]["securitySchemes"]
    assert {k: v for k, v in schemes["QuestionBankApiKey"].items() if k != "description"} == {
        "type": "apiKey", "in": "header", "name": "X-API-Key"}
    assert schemes["QuestionBankApiKeyBearer"]["scheme"] == "bearer"
    ops = [(p, m, op) for p, item in spec["paths"].items() if p.startswith("/v1/")
           for m, op in item.items()]
    assert len(ops) == 7
    for path, method, op in ops:
        assert op["security"] == [{"QuestionBankApiKeyBearer": []}, {"QuestionBankApiKey": []}], path
        assert {"401", "403", "422", "429", "503"} <= set(op["responses"]), (method, path)
        assert "Retry-After" in op["responses"]["429"]["headers"]
        # The key headers are a security scheme now, not two loose parameters.
        assert not {p["name"].lower() for p in op.get("parameters", [])} & {"authorization", "x-api-key"}
    by_id = spec["paths"]["/v1/questions/{question_id}"]["get"]["responses"]
    assert by_id["404"]["content"]["application/json"]["schema"]["$ref"].endswith("/V1Error")
    listing = spec["paths"]["/v1/questions"]["get"]["responses"]
    assert listing["400"]["content"]["application/json"]["schema"]["$ref"].endswith("/V1BadRequest")
    assert "/v1/subtopics/{subtopic_id}/questions" in spec["paths"]
