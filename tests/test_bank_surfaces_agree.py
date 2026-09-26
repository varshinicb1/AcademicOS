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

Every pair, not a chosen few. The first version of this file asserted over
Mathematics and Science alone -- 10 of the 33 class 6-10 subject-and-class
pairs the bank actually holds -- so Home Science 10 (44 records), Social
Science 10 (14), English 9 (39), Mathematics (Standard) 10 (22) and the music
and dance subjects could have drifted apart without turning it red. The pairs
are read from the bank itself, so a subject the bank gains is covered the day
it arrives.

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
# Where the WEB release's questions are. Asserted on their own as well, because
# a hole in these two is a hole in the product, and an average over 33 pairs
# would hide it.
RELEASE = [(subject, grade) for grade in RELEASE_GRADES
           for subject in ("Mathematics", "Science")]

# The records in the COMMITTED bank that the gate refuses, which the next
# rebuild removes. Task 126 widened the merge's figure rule to read a stem that
# points at something "shown below" that never arrived -- three class 12
# Informatics Practices records, each asking for a chart or a table the reader
# is shown and the record does not carry. `merge_question_banks.py --check`
# composes 5,426 against the committed 5,429 and this is the difference;
# rebuilding the served bank needs the bank owner's go-ahead, so until then
# `/v1` sells three records the paper builder refuses and this names them.
# The assertion below is an EQUALITY, not `<=`. It turns red for any other
# record the gate refuses, and also on the day the rebuild lands -- which is
# exactly when this list must be deleted. An allowance that outlives the thing
# it allows for is how the two surfaces drifted apart in the first place.
PENDING_REBUILD = {
    "cbse:sqp:ClassXII_2022_23:Informatics Practices:33",
    "cbse:sqp:ClassXII_2023_24:Informatics Practices:27",
    "cbse:sqp:ClassXII_2023_24:Informatics Practices:35",
}

pytestmark = pytest.mark.skipif(not SERVED_BANK.exists(),
                                reason="served bank not built")


def _records() -> list[dict]:
    return json.loads(SERVED_BANK.read_text(encoding="utf-8"))["questions"]


def _pair(rec: dict) -> tuple[str, int] | None:
    subject = str(rec.get("subject") or "").strip()
    grade = rec.get("grade")
    return (subject, grade) if subject and isinstance(grade, int) else None


def _file_counts() -> dict[tuple[str, int], int]:
    counts: collections.Counter = collections.Counter()
    for rec in _records():
        if (pair := _pair(rec)) is not None:
            counts[pair] += 1
    return counts


def _refused_by_pair() -> dict[tuple[str, int], int]:
    """Served records the one gate refuses, per pair. Zero everywhere once the
    bank is rebuilt; the builder drops exactly these and nothing else."""
    counts: collections.Counter = collections.Counter()
    for rec in _records():
        if bm.unservable_reason(rec) is not None and (pair := _pair(rec)) is not None:
            counts[pair] += 1
    return counts


@pytest.fixture(scope="module")
def pairs() -> list[tuple[str, int]]:
    """Every class 6-10 subject-and-class pair the served bank holds."""
    found = sorted({pair for rec in _records()
                    if (pair := _pair(rec)) is not None and pair[1] in RELEASE_GRADES})
    assert len(found) >= 33, f"the bank lost pairs: {found}"
    return found


@pytest.fixture(scope="module")
def builder_counts(tmp_path_factory, pairs) -> dict[tuple[str, int], int]:
    """What the paper builder composes from the served bank, per pair.

    `/api/v1/catalog`'s `questionCount` is `len(get_pool(...).questions)`, so
    this is that route's number without standing an app up 33 times. Module
    scoped: the bank is 15 MB and every pair re-reads it.
    """
    tmp = tmp_path_factory.mktemp("builder")
    from academicos.assessment import grades
    from academicos.config import Config

    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("ACOS_DATA_ROOT", str(tmp))
        pool_module._CACHE.clear()
        cfg = Config(data_root=tmp)
        cfg._load_baked_questions = True
        try:
            return {(subject, grade): len(pool_module.build_pool(
                        cfg, subject=subject, grade=grades.to_roman(str(grade))).questions)
                    for subject, grade in pairs}
        finally:
            pool_module._CACHE.clear()


@pytest.fixture(scope="module")
def api_counts(tmp_path_factory) -> dict[tuple[str, int], dict]:
    """`GET /v1/coverage`, the number a buyer of the API reads."""
    tmp = tmp_path_factory.mktemp("api")
    qbank_routes.init(tmp / "keys.sqlite", SERVED_BANK)
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
    than the rule, or edited by hand, and both surfaces then disagree about it
    -- the API sells it and the builder refuses it."""
    refused = {rec["id"]: reason for rec in _records()
               if (reason := bm.unservable_reason(rec)) is not None}
    assert set(refused) == PENDING_REBUILD, (
        "the served file and PENDING_REBUILD disagree about which records the "
        "merge's own gate refuses. Extra (the API sells them, no paper can "
        f"print them): { {k: v for k, v in refused.items() if k not in PENDING_REBUILD} }. "
        f"Gone (the rebuild landed -- delete them from PENDING_REBUILD): "
        f"{sorted(PENDING_REBUILD - set(refused))}")


def test_no_release_class_holds_a_record_the_gate_refuses():
    """Requirement 3 is an equality for classes 6-10, so for those classes the
    gate must refuse nothing at all: the file, the builder and `/v1` then give
    the same number with no allowance made."""
    refused = _refused_by_pair()
    in_scope = {pair: n for pair, n in refused.items() if pair[1] in RELEASE_GRADES}
    assert in_scope == {}, (
        "a class 6-10 record the gate refuses is still in the served file; "
        f"until the bank is rebuilt /v1 sells it and no paper can print it: {in_scope}")


def test_the_two_surfaces_count_the_same_questions(pairs, builder_counts, api_counts):
    """D17: `/v1` sold 4,575 for classes 6-10 Maths/Science, the builder
    composed 4,099. One file, two answers, and the difference met the teacher
    at generation time.

    Over every class 6-10 pair the bank holds, not the ten of the release:
    the other 23 could drift apart unwatched otherwise."""
    files = _file_counts()
    disagree = {}
    for pair in pairs:
        # A plain three-way equality, with no allowance made for anything. The
        # pairs are classes 6-10 only and the gate refuses nothing there (the
        # test above pins that at zero), so the builder drops exactly nothing
        # of its own and the three numbers are the same number. An earlier
        # version of this line added `refused[pair]` to the builder's count so
        # it would hold either side of a rebuild -- requirement 3 asks for the
        # equality itself, and slack in the assertion is what a class 6-10
        # regression would hide behind.
        seen = (files.get(pair, 0), builder_counts[pair],
                api_counts.get(pair, {}).get("questions", 0))
        if len(set(seen)) != 1:
            disagree[pair] = seen
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
    assert all(builder_counts[pair] > 0 for pair in RELEASE), builder_counts
    assert sum(builder_counts[pair] for pair in RELEASE) > 4_000, builder_counts
