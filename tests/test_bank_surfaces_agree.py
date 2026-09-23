"""One bank, one answer: the API may not sell a question the builder refuses.

Read on the real served bank (academicos-data/syllabus/questions.json),
because this is a defect about that one file being read twice and answered
about differently -- not something a fixture can stand in for.

The re-audit of 2026-09-23 measured `/v1` serving 4,575 records for classes
6-10 Mathematics/Science while `pool.build_pool` composed papers from 4,099 of
them: 476 questions a buyer of the question-bank API could purchase and a
teacher searching the same bank in the web app never saw. Both surfaces read
the same file; only the paper pool ran a second set of fidelity rules over it,
and on the merged bank those rules were wrong -- measured 2026-09-23, every
one of the 238 records they refused was answerable as printed, and the pool's
near-duplicate index dropped a further 307 distinct Exemplar questions whose
stems differ only in the numbers its signature never reads ("10001 x 0 = ___"
against "Successor of 106159 is ___").

So the ONE gate is the merge's (`bank_merge.unservable_reason`): the served
file is, by construction, the set of records that passed it, and both surfaces
now answer from that set. These tests hold the two counts together so they
cannot drift apart again.

Hermetic in the same way as tests/test_catalog_chapters.py: ACOS_DATA_ROOT is a
pytest tmp_path, so every store is built under tmp; the question bank is the
committed one (assessment/pool.py `_baked_bank_paths` reads it from the repo).
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.assessment import pool as pool_module  # noqa: E402
from academicos.assessment import qbank_routes  # noqa: E402
from academicos.corpus import bank_merge as bm  # noqa: E402

SERVED_BANK = ROOT / "academicos-data" / "syllabus" / "questions.json"
RELEASE_GRADES = range(6, 11)
# Where the WEB release's questions are. Every other class 6-10 pair is a
# handful of records, and a test that averaged them in would hide a hole in
# the two subjects the release is sold on.
CORE = [(subject, grade) for grade in RELEASE_GRADES
        for subject in ("Mathematics", "Science")]

pytestmark = pytest.mark.skipif(not SERVED_BANK.exists(),
                                reason="served bank not built")


def _records() -> list[dict]:
    return json.loads(SERVED_BANK.read_text(encoding="utf-8"))["questions"]


def _file_counts() -> dict[tuple[str, int], int]:
    counts: collections.Counter = collections.Counter()
    for rec in _records():
        subject = str(rec.get("subject") or "").strip()
        grade = rec.get("grade")
        if subject and isinstance(grade, int):
            counts[(subject, grade)] += 1
    return counts


@pytest.fixture
def builder_counts(tmp_path, monkeypatch) -> dict[tuple[str, int], int]:
    """What the paper builder composes from the served bank, per pair.

    `/api/v1/catalog`'s `questionCount` is `len(get_pool(...).questions)`, so
    this is that route's number without standing an app up ten times.
    """
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    from academicos.assessment import grades
    from academicos.config import Config

    pool_module._CACHE.clear()
    cfg = Config(data_root=tmp_path)
    cfg._load_baked_questions = True
    try:
        return {(subject, grade): len(pool_module.build_pool(
                    cfg, subject=subject, grade=grades.to_roman(str(grade))).questions)
                for subject, grade in CORE}
    finally:
        pool_module._CACHE.clear()


@pytest.fixture
def api_counts(tmp_path) -> dict[tuple[str, int], dict]:
    """`GET /v1/coverage`, the number a buyer of the API reads."""
    qbank_routes.init(tmp_path / "keys.sqlite", SERVED_BANK)
    app = FastAPI()
    app.include_router(qbank_routes.router)
    client = TestClient(app)
    plaintext, _ = qbank_routes._store.create(school_id="s", scopes=["facets:read"])
    body = client.get("/v1/coverage",
                      headers={"Authorization": f"Bearer {plaintext}"}).json()
    return {(row["subject"], row["grade"]): row for row in body["bySubjectClass"]}


def test_the_served_file_holds_nothing_the_gate_refuses():
    """The merge's gate is the one gate, so running it over its own output
    must remove nothing. A record that fails here was written by a merge older
    than the rule, or edited by hand, and both surfaces would then disagree
    about it -- the API would sell it and the builder would refuse it."""
    refused = [(rec.get("id"), reason) for rec in _records()
               if (reason := bm.unservable_reason(rec)) is not None]
    assert refused == [], (
        f"{len(refused)} served record(s) the merge's own gate refuses; "
        f"first few: {refused[:5]}")


def test_the_two_surfaces_count_the_same_questions(builder_counts, api_counts):
    """D17: `/v1` sold 4,575 for classes 6-10 Maths/Science, the builder
    composed 4,099. One file, two answers, and the difference met the teacher
    at generation time."""
    files = _file_counts()
    disagree = {pair: (files.get(pair, 0), builder_counts[pair],
                       api_counts.get(pair, {}).get("questions", 0))
                for pair in CORE
                if not (files.get(pair, 0) == builder_counts[pair]
                        == api_counts.get(pair, {}).get("questions", 0))}
    assert disagree == {}, (
        "served file / paper builder / /v1 coverage disagree "
        "(pair: file, builder, api): " + str(disagree))


def test_every_question_the_api_sells_can_be_marked(api_counts):
    """Rule Q1 on the same counts: the API's default listing excludes a
    record with no answer key, so a pair whose `withAnswerKey` is below its
    `questions` sells a question the builder cannot print."""
    unkeyed = {pair: row["questions"] - row["withAnswerKey"]
               for pair, row in api_counts.items()
               if row["withAnswerKey"] != row["questions"]}
    assert unkeyed == {}, f"records with no answer key, per pair: {unkeyed}"


def test_the_release_pairs_are_all_present(builder_counts):
    """A guard on the two above: they pass vacuously if the bank serves
    nothing. The live bank at e025bb7f holds 4,575 class 6-10
    Mathematics/Science records."""
    assert all(builder_counts[pair] > 0 for pair in CORE), builder_counts
    assert sum(builder_counts.values()) > 4_000, builder_counts
