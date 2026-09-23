"""Rules Q1 and Q5, across both surfaces of the bank.

PRD section 5A:

  * **Q1** -- *without an answer key, no question.*
  * **Q5** -- *one corpus, two surfaces: the HTTP API and the MCP server query
    the same engine, so an agent and the backend cannot disagree about what the
    bank contains.*

The re-audit of the live release found both broken, and in the same way: two
definitions of "has an answer key". `qbank_routes._matches` tested the
PROVENANCE LABEL (2,930 records), `QuestionBank.has_answer_key` tested the
SCHEME CONTENT (2,941), and `/v1/questions` applied neither by default -- it
served all 3,286 records, 345 of which carried no answer content at all. The
MCP server meanwhile read three corpora (5,840 records) where HTTP read one
(3,286), so the two surfaces could not even agree on the total.

So these tests are written against the two rules rather than against either
implementation: one function, and one number reported by both surfaces.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.assessment import qbank_routes as routes          # noqa: E402
from academicos.assessment.api_keys import ApiKeyStore            # noqa: E402
from academicos.assessment.qbank_routes import QuestionBank       # noqa: E402
from academicos.mcp import qbank_server                           # noqa: E402


# --------------------------------------------------------------------------- #
# records, in the shapes the real bank actually carries
# --------------------------------------------------------------------------- #

def _record(i: int, scheme: dict, *, subject: str = "Science", grade: int = 10,
            marks: int = 2) -> dict:
    return {
        "id": f"t:q:{i:04d}",
        "questionBankId": "t:doc",
        "subject": subject,
        "grade": grade,
        "marks": marks,
        "type": "short_answer",
        "difficulty": "easy",
        "bloomLevel": "understand",
        "stem": f"Question {i} about {subject}",
        "chapterIds": ["chapter-one"],
        "subtopicIds": ["subtopic-one"],
        "tags": [subject],
        "language": "en",
        "reviewState": "published",
        "version": 1,
        "answerScheme": scheme,
        "rights": {"origin": "CBSE", "redistribution": "unknown", "basis": ""},
        "provenance": {"sourceDocumentId": "t:doc", "pageNumber": 1},
        "calibration": {"measured": False, "basis": "assigned"},
        "supersededBy": None,
    }


def board_scheme(marks: int = 2) -> dict:
    return {"totalMarks": marks, "provenance": "cbse_marking_scheme",
            "markingPoints": [{"id": "mp1", "description": "the answer",
                               "marks": marks}],
            "modelAnswer": ""}


def exemplar_scheme(marks: int = 2) -> dict:
    """NCERT's own answer from an Exemplar book: a model answer, no points."""
    return {"totalMarks": marks, "provenance": "ncert_exemplar_answer",
            "markingPoints": [], "modelAnswer": "Because the gas expands."}


def labelled_but_empty(marks: int = 2) -> dict:
    """The 259-record failure the content check exists for: an official label
    over nothing at all."""
    return {"totalMarks": marks, "provenance": "cbse_marking_scheme",
            "markingPoints": [], "modelAnswer": ""}


def no_scheme(marks: int = 2) -> dict:
    return {"totalMarks": marks, "provenance": "none", "markingPoints": [],
            "modelAnswer": ""}


# 12 answer-keyed records (6 board, 6 Exemplar) and 8 that are not: 4 carrying
# an official label over an empty scheme, 4 with no scheme at all.
def build_records() -> list[dict]:
    out: list[dict] = []
    for i in range(6):
        out.append(_record(i, board_scheme(1 + i % 3), subject="Science",
                           grade=10, marks=1 + i % 3))
    for i in range(6, 12):
        out.append(_record(i, exemplar_scheme(2), subject="Mathematics",
                           grade=9, marks=2))
    for i in range(12, 16):
        out.append(_record(i, labelled_but_empty(), subject="Science", grade=10))
    for i in range(16, 20):
        out.append(_record(i, no_scheme(), subject="Mathematics", grade=9))
    return out


KEYED = 12
UNKEYED = 8
TOTAL = KEYED + UNKEYED


@pytest.fixture
def bank_file(tmp_path: Path) -> Path:
    """The served bank, where `ACOS_DATA_ROOT` says it is."""
    path = tmp_path / "syllabus" / "questions.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    records = build_records()
    path.write_text(json.dumps({"questions": records,
                                "exportedCount": len(records)}),
                    encoding="utf-8")
    return path


@pytest.fixture
def client(tmp_path: Path, bank_file: Path):
    routes.init(tmp_path / "keys.sqlite", bank_file)
    app = FastAPI()
    app.include_router(routes.router)
    return TestClient(app), routes._store


def _headers(store: ApiKeyStore, *, scopes=("questions:read", "facets:read")) -> dict:
    plaintext, _ = store.create(school_id="s", scopes=list(scopes))
    return {"Authorization": f"Bearer {plaintext}"}


# --------------------------------------------------------------------------- #
# 1. one definition of "has an answer key"
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("scheme, expected, why", [
    (board_scheme(), True, "an official CBSE scheme with a value point"),
    (exemplar_scheme(), True, "an NCERT Exemplar answer is a published key too"),
    (labelled_but_empty(), False, "an official label over an empty scheme"),
    (no_scheme(), False, "no scheme at all"),
    ({}, False, "no answerScheme key on the record"),
    ({"provenance": "cbse_marking_scheme",
      "markingPoints": [{"id": "mp1", "description": "   ", "marks": 1}]},
     False, "a value point that is only whitespace"),
    ({"provenance": "cbse_marking_scheme",
      "markingPoints": [{"id": "mp1", "text": "the answer", "marks": 1}]},
     True, "the other field name one builder emitted"),
    ({"provenance": "teacher", "modelAnswer": "my own answer"},
     False, "real content, but not a published key"),
    ({"provenance": "none", "modelAnswer": "an answer with no source"},
     False, "content with no provenance is unattributable"),
])
def test_the_one_has_answer_key_function(scheme, expected, why):
    """Content AND provenance, in one function. Either half alone was wrong:
    the label alone passed 259 empty CBE schemes, and the content alone would
    serve a teacher's or an unattributed answer as if CBSE had published it."""
    rec = _record(1, scheme)
    assert QuestionBank.has_answer_key(rec) is expected, why


def test_both_surfaces_call_the_same_function():
    """Q5 starts here: two copies of this rule is how the surfaces diverged."""
    for scheme in (board_scheme(), exemplar_scheme(), labelled_but_empty(),
                   no_scheme()):
        rec = _record(1, scheme)
        assert (qbank_server.Corpus.has_answer_key(rec)
                is QuestionBank.has_answer_key(rec))


# --------------------------------------------------------------------------- #
# 2. Q1 on the HTTP default path
# --------------------------------------------------------------------------- #

def test_the_default_list_serves_only_answer_keyed_records(client):
    """The audit's 7.1: `/v1/questions` served all 3,286 records, 345 of them
    with no answer content whatsoever."""
    c, store = client
    body = c.get("/v1/questions", params={"limit": 200},
                 headers=_headers(store)).json()
    assert body["totalMatching"] == KEYED
    assert body["count"] == KEYED
    assert all(i["hasAnswerKey"] for i in body["items"])


def test_the_unkeyed_set_is_reachable_only_by_asking_for_it(client):
    """Q1 is a default, not a deletion: the unanswerable set stays auditable,
    which is what `answer_key_state="none"` does on the MCP side."""
    c, store = client
    h = _headers(store)
    everything = c.get("/v1/questions",
                       params={"limit": 200, "include_unkeyed": "true"},
                       headers=h).json()
    assert everything["totalMatching"] == TOTAL

    audit = c.get("/v1/questions", params={"limit": 200, "has_scheme": "false"},
                  headers=h).json()
    assert audit["totalMatching"] == UNKEYED
    assert not any(i["hasAnswerKey"] for i in audit["items"])


def test_the_has_scheme_filter_is_the_same_rule_not_a_second_one(client):
    """It used to test `provenance == "cbse_marking_scheme"` alone, which
    counted the four labelled-but-empty records as having a scheme."""
    c, store = client
    body = c.get("/v1/questions", params={"limit": 200, "has_scheme": "true"},
                 headers=_headers(store)).json()
    assert body["totalMatching"] == KEYED


def test_facets_count_the_same_set_the_list_serves(client):
    """A facet count over a wider set than the list is a lie about the page
    the consumer is about to request."""
    c, store = client
    body = c.get("/v1/questions", params={"facets": "true", "limit": 200},
                 headers=_headers(store)).json()
    subjects = {f["value"]: f["count"] for f in body["facets"]["subject"]}
    assert sum(subjects.values()) == KEYED
    assert subjects == {"Science": 6, "Mathematics": 6}


def test_the_facets_route_counts_what_the_list_route_serves(client):
    """`GET /v1/facets` is the same counts by another door, so it must stand
    under the same default.

    It did not: the inline facets on `/v1/questions` took the Q1 default while
    `/v1/facets` counted the whole bank, so the standalone route reported
    {Science: 10, Mathematics: 10} for a default listing that serves 6 and 6.
    That is the identical "two counts of the same thing" divergence Q1 and Q5
    were written to end -- a consumer sizing a query from `/v1/facets` was
    told about pages the default path will never hand it."""
    c, store = client
    h = _headers(store)
    standalone = c.get("/v1/facets", headers=h).json()
    inline = c.get("/v1/questions", params={"facets": "true", "limit": 200},
                   headers=h).json()["facets"]
    assert standalone == inline
    assert {f["value"]: f["count"] for f in standalone["subject"]} == {
        "Science": 6, "Mathematics": 6}


def test_the_facets_route_opens_the_same_two_ways(client):
    """The opt-ins are the list route's, spelled the same: a caller auditing
    the unanswerable set needs its facet counts too."""
    c, store = client
    h = _headers(store)
    whole = c.get("/v1/facets", params={"include_unkeyed": "true"},
                  headers=h).json()
    assert sum(f["count"] for f in whole["subject"]) == TOTAL

    audit = c.get("/v1/facets", params={"has_scheme": "false"}, headers=h).json()
    assert sum(f["count"] for f in audit["subject"]) == UNKEYED
    assert {f["value"]: f["count"] for f in audit["subject"]} == {
        "Science": 4, "Mathematics": 4}


def test_the_subtopic_listing_keeps_q1_too(client):
    """Same default, or the rule holds on one route and not its neighbour."""
    c, store = client
    h = _headers(store)
    body = c.get("/v1/subtopics/subtopic-one/questions", params={"limit": 200},
                 headers=h).json()
    assert body["totalMatching"] == KEYED
    opened = c.get("/v1/subtopics/subtopic-one/questions",
                   params={"limit": 200, "include_unkeyed": "true"},
                   headers=h).json()
    assert opened["totalMatching"] == TOTAL


def test_the_subtopic_listing_takes_has_scheme_like_its_neighbours(client):
    """`docs/question-bank-api.md` says the two opt-ins are "accepted by all
    three routes". This route declared only `include_unkeyed`, so FastAPI
    dropped the undeclared `has_scheme` and answered **200 with the opposite
    set**: an auditor asking which questions of one subtopic the relink has
    NOT reached was handed the 12 it already covers, with nothing in the
    response to say the filter had been ignored."""
    c, store = client
    h = _headers(store)
    audit = c.get("/v1/subtopics/subtopic-one/questions",
                  params={"limit": 200, "has_scheme": "false"},
                  headers=h).json()
    assert audit["totalMatching"] == UNKEYED
    assert audit["count"] == UNKEYED
    assert not any(i["hasAnswerKey"] for i in audit["items"])

    keyed = c.get("/v1/subtopics/subtopic-one/questions",
                  params={"limit": 200, "has_scheme": "true"},
                  headers=h).json()
    assert keyed["totalMatching"] == KEYED


# --------------------------------------------------------------------------- #
# 2b. which KIND of published key -- the filter has_scheme used to be
# --------------------------------------------------------------------------- #
#
# `has_scheme=true` meant `provenance == "cbse_marking_scheme"` before this
# pass and means the shared answer-key rule after it. On the live bank the
# same request went from 1,235 records to 5,427 with no error and no version
# bump, and nothing else selected official schemes -- while `/v1/coverage`
# kept reporting `withOfficialCbseScheme`, a number naming a set no request
# could be handed.

def test_key_provenance_selects_the_boards_own_schemes(client):
    """The official-CBSE filter, back as its own parameter. Six of the twelve
    keyed fixture records carry a CBSE marking scheme; six carry NCERT's
    Exemplar answer."""
    c, store = client
    h = _headers(store)
    cbse = c.get("/v1/questions",
                 params={"limit": 200, "key_provenance": "cbse_marking_scheme"},
                 headers=h).json()
    assert cbse["totalMatching"] == 6
    assert all(i["keyProvenance"] == "cbse_marking_scheme" for i in cbse["items"])

    ncert = c.get("/v1/questions",
                  params={"limit": 200,
                          "key_provenance": "ncert_exemplar_answer"},
                  headers=h).json()
    assert ncert["totalMatching"] == 6
    assert all(i["keyProvenance"] == "ncert_exemplar_answer" for i in ncert["items"])


def test_key_provenance_narrows_within_q1_it_never_widens_past_it(client):
    """The four labelled-but-empty records carry `cbse_marking_scheme` over
    nothing at all. Selecting by label alone would serve them -- the exact
    259-record failure the content half of the rule exists for."""
    c, store = client
    body = c.get("/v1/questions",
                 params={"limit": 200, "key_provenance": "cbse_marking_scheme",
                         "include_unkeyed": "true"},
                 headers=_headers(store)).json()
    assert body["totalMatching"] == 6
    assert all(i["hasAnswerKey"] for i in body["items"])


def test_an_unservable_key_provenance_is_a_400_not_an_empty_page(client):
    """`?key_provenance=cbse` would otherwise read like "the bank holds none
    of those" rather than "that is not one of the two accepted values"."""
    c, store = client
    r = c.get("/v1/questions", params={"key_provenance": "cbse"},
              headers=_headers(store))
    assert r.status_code == 400
    assert "cbse_marking_scheme" in str(r.json()["detail"])


def test_the_official_count_on_coverage_is_a_set_the_api_can_hand_over(client):
    """`withOfficialCbseScheme` counted the CBSE label alone (10 here, the six
    keyed plus the four empty), so the coverage endpoint advertised four
    records every serving path refuses. It now equals what
    `?key_provenance=cbse_marking_scheme` returns."""
    c, store = client
    h = _headers(store)
    coverage = c.get("/v1/coverage", headers=h).json()
    served = c.get("/v1/questions",
                   params={"limit": 200,
                           "key_provenance": "cbse_marking_scheme"},
                   headers=h).json()
    assert coverage["withOfficialCbseScheme"] == served["totalMatching"] == 6


def test_the_other_two_routes_take_key_provenance_too(client):
    """Same reason the Q1 default holds on all three: a filter that works on
    one listing route and is silently dropped by its neighbour is worse than
    no filter, because the response looks fine."""
    c, store = client
    h = _headers(store)
    facets = c.get("/v1/facets",
                   params={"key_provenance": "cbse_marking_scheme"},
                   headers=h).json()
    assert {f["value"]: f["count"] for f in facets["subject"]} == {"Science": 6}

    sub = c.get("/v1/subtopics/subtopic-one/questions",
                params={"limit": 200,
                        "key_provenance": "ncert_exemplar_answer"},
                headers=h).json()
    assert sub["totalMatching"] == 6
    assert all(i["keyProvenance"] == "ncert_exemplar_answer" for i in sub["items"])


def test_q5_official_means_the_same_thing_on_both_surfaces(client, bank_file):
    """The MCP's `answer_key_state="official"` tested the label alone, which
    is the same asymmetry as the HTTP one in the opposite direction: the agent
    surface would have handed back the four empty-scheme records the HTTP
    surface refuses."""
    c, store = client
    http = {i["id"] for i in c.get(
        "/v1/questions",
        params={"limit": 200, "key_provenance": "cbse_marking_scheme"},
        headers=_headers(store)).json()["items"]}
    mcp = {q["id"] for q in _mcp_tool(
        qbank_server.Corpus.load(bank_file), "search_questions",
        {"limit": 200, "answer_key_state": "official"})["questions"]}
    assert http == mcp
    assert len(http) == 6


def test_a_record_by_name_is_still_reachable(client):
    """Q1 governs the query, not the archive: a caller naming an id gets the
    record and its empty scheme, honestly labelled."""
    c, store = client
    h = _headers(store)
    body = c.get("/v1/questions/t:q:0016/scheme", headers=h).json()
    assert body["provenance"] == "none"
    assert body["markingPoints"] == []


# --------------------------------------------------------------------------- #
# 3. the coverage endpoint, and Q5 against the MCP's own report
# --------------------------------------------------------------------------- #

def _mcp_tool(corpus, tool: str, args: dict | None = None) -> dict:
    """Call a tool through the real MCP client, in memory (as test_qbank_mcp
    does), so the number compared is the one an agent actually receives."""
    from mcp import Client

    mcp = qbank_server.build_server(corpus)

    async def run():
        async with Client(mcp) as client:
            result = await client.call_tool(tool, args or {})
            assert not result.is_error, f"{tool} returned an error"
            if result.structured_content is not None:
                return result.structured_content
            for block in result.content or []:
                text = getattr(block, "text", None)
                if text:
                    return json.loads(text)
            raise AssertionError(f"{tool} returned no readable content")

    return asyncio.run(run())


def test_the_coverage_endpoint_reports_per_subject_and_class(client):
    c, store = client
    body = c.get("/v1/coverage", headers=_headers(store)).json()
    assert body["questions"] == TOTAL
    assert body["withAnswerKey"] == KEYED
    rows = {(r["subject"], r["grade"]): r for r in body["bySubjectClass"]}
    science = rows[("Science", 10)]
    assert science["questions"] == 10 and science["withAnswerKey"] == 6
    assert science["markValues"] == [1, 2, 3]
    maths = rows[("Mathematics", 9)]
    assert maths["questions"] == 10 and maths["withAnswerKey"] == 6
    assert maths["markValues"] == [2]


def test_coverage_separates_the_denominations_from_the_total(client):
    """`marksAvailable` held the distinct mark DENOMINATIONS -- `[8, 9]` for
    Assamese class 12, over two questions -- on an endpoint where "marks
    available" reads as the total a buyer sizes a purchase on. `/v1/coverage`
    has no schema in contract/openapi.json and api-types.ts types its body as
    `unknown`, so nothing would have corrected the reading.

    The six keyed Science records carry 1, 2, 3, 1, 2, 3 marks: three
    denominations, twelve marks. One number is not the other and neither is
    reported under a name that could be mistaken for it."""
    c, store = client
    rows = {(r["subject"], r["grade"]): r
            for r in c.get("/v1/coverage", headers=_headers(store)).json()
            ["bySubjectClass"]}
    science = rows[("Science", 10)]
    assert science["markValues"] == [1, 2, 3]
    assert science["marksTotal"] == 12
    assert "marksAvailable" not in science

    # Six 2-mark Exemplar records, and the unkeyed four contribute nothing:
    # a question that cannot be marked does not make marks available.
    maths = rows[("Mathematics", 9)]
    assert maths["markValues"] == [2] and maths["marksTotal"] == 12


def test_coverage_needs_a_scope_like_every_other_route(client):
    c, store = client
    r = c.get("/v1/coverage", headers=_headers(store, scopes=["questions:read"]))
    assert r.status_code == 403


def test_q5_the_two_surfaces_report_the_same_coverage(client, bank_file):
    """The audit's 7.3: the MCP read 5,840 records where HTTP read 3,286. The
    same bank must now produce the same report on both surfaces."""
    c, store = client
    http = c.get("/v1/coverage", headers=_headers(store)).json()
    mcp = _mcp_tool(qbank_server.Corpus.load(bank_file), "coverage_report")

    for field in ("questions", "withAnswerKey", "withOfficialCbseScheme",
                  "answerKeyCoverage", "subjects", "grades"):
        assert http[field] == mcp[field], field
    assert http["bySubjectClass"] == mcp["bySubjectClass"]


def test_q5_the_two_surfaces_serve_the_same_answerable_set(client, bank_file):
    """Not just the same totals -- the same records."""
    c, store = client
    http_ids = {i["id"] for i in c.get(
        "/v1/questions", params={"limit": 200},
        headers=_headers(store)).json()["items"]}
    mcp_ids = {q["id"] for q in _mcp_tool(
        qbank_server.Corpus.load(bank_file), "search_questions",
        {"limit": 200})["questions"]}
    assert http_ids == mcp_ids


# --------------------------------------------------------------------------- #
# 4. the MCP reads the served bank, where ACOS_DATA_ROOT says it is
# --------------------------------------------------------------------------- #

def test_load_corpus_honours_acos_data_root(tmp_path, bank_file, monkeypatch):
    """It read a cwd-relative path, so the server served an empty bank from
    anywhere but the repo root -- and said nothing about it."""
    monkeypatch.chdir(tmp_path.parent)
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    corpus = qbank_server.load_corpus()
    assert len(corpus) == TOTAL


def test_load_corpus_reads_only_the_served_bank(tmp_path, bank_file, monkeypatch):
    """Q5 again: the merge (Task 11) put the eligible CBE and SQP records INTO
    the served bank, so reading those corpora separately would double-count
    them and serve records the merge deliberately excluded."""
    cbe = tmp_path / "corpus" / "cbse-cbe" / "questions.json"
    cbe.parent.mkdir(parents=True, exist_ok=True)
    stray = _record(9001, board_scheme(), subject="Science", grade=10)
    cbe.write_text(json.dumps({"questions": [stray]}), encoding="utf-8")
    sqp = tmp_path / "corpus" / "cbse-sqp" / "questions.json"
    sqp.parent.mkdir(parents=True, exist_ok=True)
    sqp.write_text(json.dumps({"questions": [_record(9002, board_scheme())]}),
                   encoding="utf-8")

    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    corpus = qbank_server.load_corpus()
    assert len(corpus) == TOTAL
    assert not [r for r in corpus.records if str(r["id"]).startswith("t:q:9")]


def test_an_explicit_bank_argument_still_wins(tmp_path, bank_file, monkeypatch):
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path / "nowhere"))
    assert len(qbank_server.load_corpus(str(bank_file))) == TOTAL


# --------------------------------------------------------------------------- #
# 5. the network transports take the same key as the HTTP surface
# --------------------------------------------------------------------------- #
#
# Driven through the transport's real ASGI app with Starlette's TestClient
# rather than by binding a port: the middleware under test is the one
# `main()` wraps the app in, so nothing about the check is simulated. Only
# uvicorn's socket is absent.

@pytest.fixture
def transport(tmp_path, bank_file):
    store = ApiKeyStore(tmp_path / "mcp-keys.sqlite")
    auth = qbank_server.TransportAuth(store)
    mcp = qbank_server.build_server(qbank_server.Corpus.load(bank_file))
    app = qbank_server.transport_app(mcp, auth, transport="streamable-http")
    yield app, store
    store.close()


def _mcp_post(c: TestClient, headers: dict):
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    return c.post("/mcp", json=body, headers={
        "Accept": "application/json, text/event-stream", **headers})


def test_a_network_request_without_a_key_is_refused(transport):
    """The audit's 7.2: sse and streamable-http had no authentication at all,
    while the HTTP surface of the same product is key-gated."""
    app, _ = transport
    with TestClient(app) as c:
        r = _mcp_post(c, {})
        assert r.status_code == 401
        assert "WWW-Authenticate" in r.headers


def test_a_bogus_key_is_refused(transport):
    app, _ = transport
    with TestClient(app) as c:
        assert _mcp_post(c, {"Authorization": "Bearer acos_qb_nope"}).status_code == 401


def test_a_key_without_the_questions_scope_is_403(transport):
    app, store = transport
    plaintext, _ = store.create(school_id="s", scopes=["facets:read"])
    with TestClient(app) as c:
        r = _mcp_post(c, {"Authorization": f"Bearer {plaintext}"})
        assert r.status_code == 403


def test_a_valid_key_reaches_the_server(transport):
    app, store = transport
    plaintext, _ = store.create(school_id="s", scopes=["questions:read"])
    with TestClient(app) as c:
        r = _mcp_post(c, {"Authorization": f"Bearer {plaintext}"})
        assert r.status_code not in (401, 403), r.text


def test_the_x_api_key_header_works_here_too(transport):
    app, store = transport
    plaintext, _ = store.create(school_id="s", scopes=["questions:read"])
    with TestClient(app) as c:
        assert _mcp_post(c, {"X-API-Key": plaintext}).status_code not in (401, 403)


def test_the_auth_layer_is_the_http_surfaces_own(tmp_path):
    """Called directly, because this is the seam: one key store, one scope
    vocabulary, one quota counter for both surfaces."""
    store = ApiKeyStore(tmp_path / "k.sqlite")
    auth = qbank_server.TransportAuth(store)
    plaintext, key = store.create(school_id="s", scopes=["questions:read"],
                                  quota_per_minute=2)
    assert auth.authenticate({"authorization": f"Bearer {plaintext}"}).id == key.id

    with pytest.raises(routes.AuthFailure) as exc:
        auth.authenticate({})
    assert exc.value.status == 401

    # The same quota counter the HTTP routes spend.
    auth.authenticate({"x-api-key": plaintext})
    with pytest.raises(routes.AuthFailure) as spent:
        auth.authenticate({"x-api-key": plaintext})
    assert spent.value.status == 429
    store.close()


def test_stdio_is_not_wrapped(tmp_path, bank_file):
    """stdio is local by construction -- the client launches the process and
    owns both ends of the pipe, so there is no network peer to authenticate.
    Wrapping it would ask a desktop host for a key it has no way to hold."""
    assert qbank_server.needs_transport_auth("stdio") is False
    assert qbank_server.needs_transport_auth("sse") is True
    assert qbank_server.needs_transport_auth("streamable-http") is True


# `needs_transport_auth` and `transport_app` were each covered above, and the
# line that JOINS them was covered by neither -- yet that line is the whole
# security property. Delete the `transport_app` call in `main` and
# `uvicorn.run(mcp.sse_app(...))` still serves, every test above still passes,
# and the port is open. So: run `main` with uvicorn's socket replaced, and
# look at what it was actually handed.

def test_main_hands_uvicorn_the_gated_app_on_every_network_transport(
        tmp_path, bank_file, monkeypatch):
    uvicorn = pytest.importorskip("uvicorn")
    handed: list = []
    monkeypatch.setattr(uvicorn, "run", lambda app, **kw: handed.append(app))

    for transport in ("streamable-http", "sse"):
        assert qbank_server.main([
            "--transport", transport,
            "--bank", str(bank_file),
            "--keys", str(tmp_path / "k.sqlite"),
        ]) == 0

    # Both branches, not just the one the transport fixture drives: the sse
    # app builder was constructed nowhere in the suite.
    assert len(handed) == 2
    for app in handed:
        assert isinstance(app, qbank_server.ApiKeyMiddleware)
        assert isinstance(app.auth, qbank_server.TransportAuth)
        assert app.auth.scope == qbank_server.TRANSPORT_SCOPE


def test_main_runs_stdio_unwrapped(tmp_path, bank_file, monkeypatch):
    """The other half of the same line: stdio must reach `mcp.run` directly,
    or a desktop host is asked for a key it has no way to hold."""
    class FakeServer:
        transport = None

        def run(self, transport):
            FakeServer.transport = transport

    monkeypatch.setattr(qbank_server, "build_server", lambda corpus: FakeServer())
    assert qbank_server.main(["--bank", str(bank_file)]) == 0
    assert FakeServer.transport == "stdio"


# --------------------------------------------------------------------------- #
# 5b. `pip install -e ".[mcp]"` can actually run the server
# --------------------------------------------------------------------------- #
#
# The extra declared only the MCP SDK while `Corpus.__init__` and
# `Corpus.has_answer_key` imported `QuestionBank` from `qbank_routes`, which
# imports fastapi at module scope -- so an [mcp] install raised ImportError on
# the first stdio request, and the extra's own comment said the opposite. The
# same coupling reached `pool.build_pool`, so a non-[api] install could not
# build a paper pool from the baked bank either. Deferring the import into the
# method bodies moved the failure; it did not remove it, which is why this
# test runs the import in a SUBPROCESS with fastapi genuinely unimportable
# rather than checking where an import statement sits.

_WITHOUT_FASTAPI = '''
import json, sys

class NoFastAPI:
    """What a [mcp]-only install looks like from the inside."""
    def find_spec(self, name, path=None, target=None):
        if name == "fastapi" or name.startswith("fastapi."):
            raise ImportError("No module named 'fastapi'")
        return None

sys.meta_path.insert(0, NoFastAPI())
sys.path.insert(0, sys.argv[1])

from academicos.assessment import pool                       # paper generation
from academicos.assessment.qbank_engine import QuestionBank  # the shared rule
from academicos.mcp import qbank_server                      # the MCP server

corpus = qbank_server.load_corpus(sys.argv[2])
print(json.dumps({
    "records": len(corpus),
    "keyed": sum(1 for r in corpus.records if corpus.has_answer_key(r)),
    "coverage_keyed": corpus.coverage()["withAnswerKey"],
    "pool_rule": QuestionBank.has_answer_key(corpus.records[0]),
    "list_tools_rc": qbank_server.main(["--bank", sys.argv[2], "--list-tools"]),
    "fastapi_loaded": "fastapi" in sys.modules,
}))
'''


def test_the_mcp_server_and_the_paper_pool_import_without_fastapi(bank_file, tmp_path):
    import subprocess

    script = tmp_path / "no_fastapi.py"
    script.write_text(_WITHOUT_FASTAPI, encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(script), str(ROOT / "src"), str(bank_file)],
        capture_output=True, text=True, encoding="utf-8",
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout.strip().splitlines()[-1])
    assert out["records"] == TOTAL
    assert out["keyed"] == out["coverage_keyed"] == KEYED
    assert out["pool_rule"] is True
    assert out["list_tools_rc"] == 0
    assert out["fastapi_loaded"] is False


# --------------------------------------------------------------------------- #
# 6. the third surface: paper generation
# --------------------------------------------------------------------------- #
#
# Requirement 1 names three callers, not two: "one definition of 'has an answer
# key', used by HTTP, MCP and paper generation". `pool.build_pool` loaded the
# same served bank the HTTP surface serves and applied no answer-key gate at
# all, and `PoolQuestion.has_answer` carried a fourth, weaker rule -- any
# `correct_option` or `answer_text`, whatever its provenance. A no-op on
# today's bank (5,427 of 5,427 keyed), and exactly the state the bank was in
# before the CBE merge, when it was not.

def _served(i: int = 1, scheme: dict | None = None, **overrides) -> dict:
    """A served-bank record in the shape `bank_merge` writes it."""
    sys.path.insert(0, str(ROOT / "tests"))
    from academicos.corpus import bank_merge as bm
    from test_bank_merge import board

    rec = board(i, **overrides)
    if scheme is not None:
        rec["answerScheme"] = {**rec["answerScheme"], **scheme}
    normalised, _ = bm.normalise(rec)
    return normalised


def _pool_over(tmp_path, monkeypatch, records, *, subject: str, grade: str):
    """A pool built from a baked bank holding exactly `records`."""
    from academicos.assessment import pool as pool_module
    from academicos.config import Config

    path = tmp_path / "baked.json"
    path.write_text(json.dumps({"questions": records}), encoding="utf-8")
    monkeypatch.setattr(pool_module, "_baked_bank_paths", lambda cfg: [path])
    cfg = Config(data_root=tmp_path)
    cfg._load_baked_questions = True
    return pool_module.build_pool(cfg, subject=subject, grade=grade)


def test_paper_generation_applies_the_one_rule_too(tmp_path, monkeypatch):
    """A record the HTTP surface refuses to list must not be printable on a
    paper: that is the same unanswerable question served by another door."""
    # Three distinct questions, one per answer-key shape. The stems had to
    # differ while this path ran its own near-duplicate index -- that index
    # dropped the last two before the answer-key gate was ever reached -- and
    # that index is the merge's alone since Task 126. They stay distinct
    # because a test about the answer-key gate should turn on nothing else.
    keyed = _served(1, stem="Explain why the sky appears blue during the day.")
    empty = _served(2, {"markingPoints": [], "modelAnswer": "",
                        "modelAnswerLatex": ""},
                    stem="State the two conditions required for rusting of iron.")
    unattributed = _served(3, {"provenance": "teacher"},
                           stem="Draw the structure of a neuron and name its parts.")
    assert QuestionBank.has_answer_key(keyed)
    assert not QuestionBank.has_answer_key(empty)
    assert not QuestionBank.has_answer_key(unattributed)

    built = _pool_over(tmp_path, monkeypatch, [keyed, empty, unattributed],
                       subject="Science", grade="X")
    assert [q.id for q in built.questions] == [keyed["id"]]


def test_has_answer_is_the_one_rule_for_a_bank_record(tmp_path, monkeypatch):
    """`has_answer` tested `correct_option or answer_text`, so a board record
    keyed by its value points with no model answer -- the shape every SQP MCQ
    and 4,192 Exemplar records arrive in -- read as unanswerable here while
    `/v1/questions` served it. One record, two answers."""
    points_only = _served(4, {"modelAnswer": "", "modelAnswerLatex": ""})
    assert QuestionBank.has_answer_key(points_only)

    built = _pool_over(tmp_path, monkeypatch, [points_only],
                       subject="Science", grade="X")
    assert len(built.questions) == 1
    pq = built.questions[0]
    assert pq.answer_text == ""          # the old rule's only evidence
    assert pq.has_answer is True


# --------------------------------------------------------------------------- #
# 6b. one gate: "can this record be served" (Task 126)
# --------------------------------------------------------------------------- #
#
# The same failure in the other half of the question. Q1 is "has it an answer
# key"; this is "can a student read it at all", and the two surfaces answered
# it differently for the same file. `pool.build_pool`'s baked-bank path ran
# `has_broken_options` / `needs_missing_figure` / `looks_truncated` and its own
# near-duplicate index over records the merge had already repaired, normalised
# and gated -- 476 class 6-10 Maths/Science records the API sold and the
# builder refused (re-audit, 2026-09-23). Measured on that bank the same day,
# every one of those rules was wrong on merged input: "(A) 1 (B) 2 (C) 3
# (D) 4" reads as a broken option list because each option is one character
# long, and 307 distinct Exemplar questions read as near-duplicates of one
# another because the pool's signature drops every number.
#
# The gate belongs at the merge, which already has it, and `pool` calls that
# one function instead of keeping a second answer.

def test_a_single_character_option_is_an_option_not_a_broken_list(tmp_path, monkeypatch):
    """155 served records read this way, 152 of them Mathematics 6-10:
    `cbe:q:Maths7RKS1`, "What is the value of (30 x 70) + 60? (A) 0 (B) 1
    (C) 2 (D) 27", is answerable and was refused every paper."""
    from academicos.corpus import bank_merge as bm

    rec = _served(31, stem="What is the value of (30 x 70) + 60? "
                           "(A) 0 (B) 1 (C) 2 (D) 27", type="mcq", marks=1)
    assert bm.unservable_reason(rec) is None
    built = _pool_over(tmp_path, monkeypatch, [rec], subject="Science", grade="X")
    assert [q.id for q in built.questions] == [rec["id"]]


def test_two_questions_that_differ_only_in_their_numbers_are_two_questions(
        tmp_path, monkeypatch):
    """`exemplar:q:8:mathematics:3:-:25` and `...:26` ask for the perfect
    squares below 100 and the perfect cubes below 1000. The pool's signature
    keeps only tokens that start with a letter, so both reduced to the same
    bag of words and the second was dropped from every Mathematics 8 paper.
    307 class 6-10 Maths/Science records went this way; twenty were read by
    hand on 2026-09-23 and all twenty were two questions."""
    from academicos.assessment.pool import _NearDuplicateIndex

    stems = ("Fill in the blanks to make the statements true: There are "
             "_________ perfect squares between 1 and 100.",
             "Fill in the blanks to make the statements true: There are "
             "_________ perfect cubes between 1 and 1000.")
    index = _NearDuplicateIndex()
    assert [index.is_duplicate(s) for s in stems] == [False, True], (
        "this test is only worth running while the pool's own index still "
        "calls these one question")

    a, b = (_served(32 + i, stem=s) for i, s in enumerate(stems))
    built = _pool_over(tmp_path, monkeypatch, [a, b], subject="Science", grade="X")
    assert [q.id for q in built.questions] == [a["id"], b["id"]]


def test_an_unreadable_record_is_absent_from_both_surfaces(tmp_path, monkeypatch):
    """The gate's own case, end to end: an MCQ whose options never arrived is
    excluded by the merge, so it is not in the file either surface reads."""
    from academicos.corpus import bank_merge as bm
    from test_bank_merge import board

    broken = board(34, source="cbse_sample_paper", type="mcq", marks=1,
                   stem="Which of the following is the correct option :")
    result = bm.compose([], [], [broken])
    # `normalise`'s more specific name for the same defect; `exclusion_reason`
    # calls it "options-missing" when it is read on the record alone.
    assert [(e["id"], e["reason"]) for e in result.excluded] == \
        [(broken["id"], "mcq-options-unresolved")]
    assert bm.unservable_reason(broken) == "options-missing"
    assert result.questions == []

    assert QuestionBank(result.questions).get(broken["id"]) is None
    built = _pool_over(tmp_path, monkeypatch, result.questions,
                       subject="Science", grade="X")
    assert built.questions == []


def test_the_builder_refuses_what_the_gate_refuses_even_from_a_stale_bank(
        tmp_path, monkeypatch):
    """The gate stays a gate on the builder's side. A questions.json written
    by a merge older than the rule -- or edited by hand -- must not print a
    record neither surface should serve, and the reason must be the merge's
    own, not a second opinion."""
    from academicos.corpus import bank_merge as bm

    good = _served(35, stem="Explain why the sky appears blue during the day.")
    bad = _served(36, stem="Which of the following is the correct option :",
                  type="mcq", marks=1)
    assert bm.unservable_reason(good) is None
    assert bm.unservable_reason(bad) == "options-missing"

    built = _pool_over(tmp_path, monkeypatch, [good, bad],
                       subject="Science", grade="X")
    assert [q.id for q in built.questions] == [good["id"]]


def _build_pool_source() -> tuple[str, str]:
    """`build_pool`'s two branches, comments stripped.

    Code only: the comments name the rules each branch used to apply and why
    they were wrong, which is the point of them."""
    import inspect

    from academicos.assessment import pool as pool_module

    source = inspect.getsource(pool_module.build_pool)
    registry, marker, baked = source.partition("_baked_bank_paths(cfg)")
    assert marker, "build_pool no longer has a baked-bank branch to scan"
    return tuple("\n".join(line.split("#", 1)[0] for line in part.splitlines())
                 for part in (registry, baked))  # type: ignore[return-value]


# The three stem rules, by the name each is imported under. Neither branch of
# `build_pool` may name one: whichever corpus it is reading, it asks the one
# gate that owns that corpus and `bank_merge` composes the rules.
_STEM_RULES = ("has_broken_options", "needs_missing_figure", "looks_truncated")


def test_neither_pool_path_composes_the_stem_rules_itself():
    """A source scan, as Task 16 did for the merge's own filters.

    Scoped to the baked-bank branch when it was written, which left the
    registry branch spelling out `has_broken_options` / `needs_missing_figure`
    / `looks_truncated` in its own order -- a second, differently-composed
    answer to "can this be served", and the one still carrying the
    single-character-option bug. Each branch now asks one named function, and
    the rules are composed once, in `bank_merge`, per corpus."""
    registry, baked = _build_pool_source()
    for branch, text, gate in (("registry", registry, "raw_extraction_reason"),
                               ("baked-bank", baked, "unservable_reason")):
        spelled_out = [name for name in _STEM_RULES if name in text]
        assert spelled_out == [], (
            f"the {branch} path composes its own servability rules "
            f"({', '.join(spelled_out)}); ask bank_merge.{gate}")
        assert gate in text, (
            f"the {branch} path must ask {gate}, the one gate for the corpus "
            "it reads")


def test_the_baked_bank_path_keeps_no_second_copy_of_the_rule():
    """The baked-bank branch, on top of the stem rules, must not re-run the
    encoding check or a near-duplicate index of its own over records the merge
    already repaired and de-duplicated. Those two stay on the registry path:
    it reads raw PDF extraction, where the encoding really is broken and the
    same paper really is parsed twice."""
    _registry, baked = _build_pool_source()
    second_opinions = [name for name in (*_STEM_RULES, "looks_mangled", "near_dupes")
                       if name in baked]
    assert second_opinions == [], (
        "the baked-bank path applies its own servability rules "
        f"({', '.join(second_opinions)}); the merge already answered this "
        "question about this file -- call bank_merge.unservable_reason")
    assert "unservable_reason" in baked, (
        "the baked-bank path must still ask the one gate, so a questions.json "
        "written by an older merge cannot reach a paper")


# The two gates, and the vocabulary that may only be spoken behind them. One
# gate per corpus: `raw_extraction_reason` answers "can this be served" about a
# stem straight out of PDF extraction, `unservable_reason` about a record the
# merge has already repaired and normalised. They read different inputs (a bare
# string against a whole record) and give different answers to the same stem on
# purpose -- applying the raw one to merged records refused 238 answerable
# served questions, which is the defect Task 126 exists to close.
_GATES = ("raw_extraction_reason", "unservable_reason")
# Every other name in bank_merge that decides, or half-decides, servability.
_BEHIND_THE_GATE = (
    "has_broken_options", "needs_missing_figure", "looks_truncated",
    "exclusion_reason", "unanswerable_reason", "source_reason",
    "unallocated_marks_reason", "builder_key_reason",
    "_options_missing", "_options_out_of_order", "_case_without_question",
    "_shown_below_missing",
)


def _bank_merge_names_used_by(path: Path) -> set[str]:
    """Every name a shipping module takes from `bank_merge`, by import or
    through an alias. Parsed, not grepped: `merge_question_banks.py` names
    `bank_merge.exclusion_reason` in its module docstring, and prose about the
    gate is not a second copy of it."""
    import ast

    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    aliases: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if (node.module or "").endswith("bank_merge"):
                names.update(a.name for a in node.names)
            elif (node.module or "").endswith("corpus") or node.module is None:
                aliases.update(a.asname or a.name for a in node.names
                               if a.name == "bank_merge")
        elif isinstance(node, ast.Import):
            aliases.update(a.asname or a.name.rsplit(".", 1)[-1] for a in node.names
                           if a.name.endswith("bank_merge"))
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if node.value.id in aliases:
                names.add(node.attr)
    return names


def test_only_the_two_gates_leave_bank_merge():
    """Requirement 1 asks for exactly ONE implementation of "can this be
    served". There is one per corpus, and this is what holds it at two: no
    module outside `bank_merge` may reach past a gate for a rule or for half
    of the chain behind it, however the rules themselves are shared.

    Repo-wide, not `pool.py` alone. The scan above watches the two branches
    that were wrong; this one is what stops a third answer appearing in
    `qbank_routes.py`, `bank_health.py` or a script the day someone needs
    "just the figure check" somewhere new.
    """
    root = Path(__file__).resolve().parents[1]
    shipping = [p for p in (*(root / "src").rglob("*.py"), *(root / "scripts").glob("*.py"))
                if p.name != "bank_merge.py"]
    assert len(shipping) > 100, "the source scan found almost nothing to scan"

    reaching_past = {}
    for path in shipping:
        behind = _bank_merge_names_used_by(path) & set(_BEHIND_THE_GATE)
        if behind:
            reaching_past[path.relative_to(root).as_posix()] = sorted(behind)
    assert reaching_past == {}, (
        "these modules take a servability rule from bank_merge instead of "
        f"asking one of {_GATES}, which makes each of them a second answer to "
        f"'can this be served': {reaching_past}")


# --------------------------------------------------------------------------- #
# 7. the collection the counts are counted over, and the filter chain
# --------------------------------------------------------------------------- #
#
# Q5 is "one corpus, two surfaces", and it fails in two more ways that the
# first pass left standing:
#
#   * `coverage()` counted `self.records` while `page()` and `facets()`
#     iterated `_by_id`, built by a dict comprehension that silently dropped
#     id-less records and kept only the last of a duplicated id. One bank, two
#     totals -- `/v1/coverage` advertising questions `/v1/questions` cannot
#     serve.
#   * `Corpus.search` reimplemented the filter chain inline, and its keyword
#     haystack included `provenance.sourceDocumentId` where the HTTP
#     `_matches` haystack did not. One keyword, two answers.

def _dup(i: int, dup_of: int, **overrides) -> dict:
    rec = _record(i, board_scheme(), **overrides)
    rec["id"] = f"t:q:{dup_of:04d}"
    return rec


def test_a_duplicated_id_is_counted_once_by_every_surface():
    """`len`, `coverage()` and `page()` must report the same number.

    Three records, one id repeated: the bank used to answer 3, 3 and 2.
    """
    bank = QuestionBank([
        _record(1, board_scheme()),
        _record(2, board_scheme()),
        _dup(3, 1),
    ])
    _, _, total = bank.page(limit=100)
    assert len(bank) == 2
    assert bank.coverage()["questions"] == 2
    assert total == 2


def test_an_id_less_record_is_counted_once_by_every_surface():
    bank = QuestionBank([
        _record(1, board_scheme()),
        {**_record(2, board_scheme()), "id": ""},
    ])
    _, _, total = bank.page(limit=100)
    assert len(bank) == 1
    assert bank.coverage()["questions"] == 1
    assert total == 1


def test_a_dropped_record_is_logged_rather_than_vanishing(caplog):
    """Either reject them or say so -- what the loader must not do is drop
    them without a word. A bank file holding three records whose API serves
    one is a data bug, and load is the only place it can be noticed."""
    import logging as _logging
    with caplog.at_level(_logging.WARNING,
                         logger="academicos.assessment.qbank_engine"):
        QuestionBank([
            _record(1, board_scheme()),
            {**_record(2, board_scheme()), "id": None},
            _dup(3, 1),
        ])
    said = " ".join(caplog.messages).lower()
    assert "id" in said
    assert "duplicate" in said


def test_coverage_grades_come_from_the_collection_the_page_serves():
    """`grades` was derived from `self.records` too, so a class that existed
    only on a dropped record was advertised and then unqueryable."""
    bank = QuestionBank([
        _record(1, board_scheme(), subject="Science", grade=10),
        _dup(2, 1, subject="Science", grade=6),
    ])
    grades = bank.coverage()["grades"]
    served = {r["grade"] for r in bank.page(limit=100)[0]}
    assert set(grades) == served


def test_the_mcp_corpus_de_duplicates_like_the_old_loader_did():
    """`Corpus.load` used to do this itself (`seen[rid] = rec`, blank ids
    skipped) and the rewrite dropped it. The engine now owns it, so both
    surfaces inherit it -- but the MCP surface must still have it."""
    corpus = qbank_server.Corpus([
        _record(1, board_scheme()),
        _dup(2, 1),
        {**_record(3, board_scheme()), "id": ""},
    ])
    assert len(corpus) == 1
    assert corpus.coverage()["questions"] == 1
    assert len(corpus.search(limit=100)) == 1


# --- the filter chain ------------------------------------------------------ #

def _sourced(i: int, source: str, **overrides) -> dict:
    """A record whose source document id is NOT in its stem or its tags."""
    rec = _record(i, board_scheme(), **overrides)
    rec["provenance"] = {"sourceDocumentId": source, "pageNumber": 1}
    return rec


def sourced_records() -> list[dict]:
    return [_sourced(9001, "CBSE2023"), _sourced(9002, "NCERT-EX")]


def _bank_client(tmp_path: Path, records: list[dict], name: str = "alt"):
    """An HTTP client over an arbitrary bank, so the two surfaces can be
    compared record for record rather than only in totals."""
    path = tmp_path / name / "questions.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"questions": records}), encoding="utf-8")
    routes.init(tmp_path / f"{name}-keys.sqlite", path)
    app = FastAPI()
    app.include_router(routes.router)
    return TestClient(app), routes._store, path


def test_one_keyword_cannot_mean_two_things(tmp_path):
    """The MCP haystack was stem + tags + `provenance.sourceDocumentId`; the
    HTTP one was stem + tags. `keyword=CBSE2023` therefore selected one record
    over MCP and none over HTTP, from the same bank."""
    c, store, path = _bank_client(tmp_path, sourced_records())
    http = {i["id"] for i in c.get(
        "/v1/questions", params={"keyword": "CBSE2023", "limit": 200},
        headers=_headers(store)).json()["items"]}
    mcp = {q["id"] for q in _mcp_tool(
        qbank_server.Corpus.load(path), "search_questions",
        {"keyword": "CBSE2023", "limit": 200})["questions"]}
    assert http == mcp


def test_the_source_document_is_a_filter_of_its_own_not_a_keyword_term():
    """Selecting by source paper is a real need -- it is how an agent asks for
    "the 2023 board paper". It keeps working, as a named parameter, rather
    than as a term smuggled into one surface's keyword search."""
    corpus = qbank_server.Corpus(sourced_records())
    hits = corpus.search(source_document_id="CBSE2023", limit=100)
    assert [r["id"] for r in hits] == ["t:q:9001"]
    assert corpus.search(source_document_id="nothing", limit=100) == []


def test_every_shared_filter_answers_the_same_on_both_surfaces(tmp_path):
    """The docstring claims `Corpus` wraps the engine "so the MCP surface and
    the HTTP surface answer identically". This is that claim, tested."""
    records = build_records() + sourced_records()
    c, store, path = _bank_client(tmp_path, records, name="shared")
    corpus = qbank_server.Corpus.load(path)

    cases = [
        ({}, {}),
        ({"subject": "Science"}, {"subject": "Science"}),
        ({"grade": 9}, {"grade": 9}),
        ({"marks": 2}, {"marks": 2}),
        ({"type": "short_answer"}, {"question_type": "short_answer"}),
        ({"difficulty": "easy"}, {"difficulty": "easy"}),
        ({"keyword": "Science"}, {"keyword": "Science"}),
        ({"keyword": "CBSE2023"}, {"keyword": "CBSE2023"}),
        ({"has_scheme": "false"}, {"answer_key_state": "none"}),
        ({"key_provenance": "cbse_marking_scheme"},
         {"answer_key_state": "official"}),
    ]
    for http_params, mcp_args in cases:
        http = {i["id"] for i in c.get(
            "/v1/questions", params={**http_params, "limit": 200},
            headers=_headers(store)).json()["items"]}
        mcp = {q["id"] for q in _mcp_tool(
            corpus, "search_questions", {**mcp_args, "limit": 200})["questions"]}
        assert http == mcp, http_params


def test_an_unknown_answer_key_state_is_refused_not_ignored():
    """It fell through every branch, so a typo widened the query past Q1 and
    handed back the unanswerable set."""
    corpus = qbank_server.Corpus(build_records())
    with pytest.raises(ValueError):
        corpus.search(answer_key_state="offical", limit=200)


# --- the contradictory pair ------------------------------------------------ #

@pytest.mark.parametrize("route", [
    "/v1/questions",
    "/v1/subtopics/subtopic-one/questions",
    "/v1/facets",
])
def test_unkeyed_and_a_kind_of_key_together_are_a_400(client, route):
    """`?has_scheme=false&key_provenance=cbse_marking_scheme` asks for the
    records with no answer key that have a CBSE answer key. It answered 200
    with an empty page, which reads as "the bank holds no CBSE records in the
    unanswerable set" -- true, and meaningless. That is the failure
    `_checked_key_provenance` was written to prevent, in its own words: not
    "a silent empty page that reads like 'the bank has none of those'"."""
    c, store = client
    r = c.get(route, params={"has_scheme": "false",
                             "key_provenance": "cbse_marking_scheme"},
              headers=_headers(store))
    assert r.status_code == 400
    body = json.dumps(r.json()).lower()
    assert "has_scheme" in body and "key_provenance" in body


def test_the_opt_in_is_not_the_contradiction(client):
    """`include_unkeyed=true` widens and `key_provenance` narrows back, and
    the result is the keyed CBSE set -- a set the API can hand over. Only an
    explicitly false `has_scheme` is a contradiction."""
    c, store = client
    r = c.get("/v1/questions",
              params={"include_unkeyed": "true",
                      "key_provenance": "cbse_marking_scheme", "limit": 200},
              headers=_headers(store))
    assert r.status_code == 200
    assert r.json()["totalMatching"] == 6


def test_an_empty_scheme_under_an_official_label_says_so_on_every_surface(client):
    """Q5, the last two places the label alone still spoke for the key: the
    list's `hasOfficialScheme` and the scheme route itself. Record 12 carries
    provenance cbse_marking_scheme over no value point and no model answer --
    unmarkable, and both used to present it as CBSE's own."""
    c, store = client
    h = _headers(store)
    listed = c.get("/v1/questions", params={"include_unkeyed": "true"}, headers=h).json()
    empty = next(q for q in listed["items"] if q["id"] == "t:q:0012")
    assert empty["hasAnswerKey"] is False
    assert empty["hasOfficialScheme"] is False, "an empty scheme is not an official scheme"

    scheme = c.get("/v1/questions/t:q:0012/scheme", headers=h).json()
    assert scheme["provenance"] == "cbse_marking_scheme"   # the label is reported as it is
    assert scheme["hasAnswerKey"] is False, "the route must say the key cannot be marked"

    keyed = c.get("/v1/questions/t:q:0000/scheme", headers=h).json()
    assert keyed["hasAnswerKey"] is True
