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
    assert science["marksAvailable"] == [1, 2, 3]
    maths = rows[("Mathematics", 9)]
    assert maths["questions"] == 10 and maths["withAnswerKey"] == 6
    assert maths["marksAvailable"] == [2]


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
