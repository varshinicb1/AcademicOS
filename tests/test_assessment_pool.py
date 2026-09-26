"""assessment/pool.py::build_pool's registry-error handling.

Found live 2026-09-18 (an end-to-end verification session, not a report from
reading the code): a registry query failure (locked database, missing table,
any sqlite3.OperationalError) used to be swallowed into `rows = []` --
indistinguishable from "no question papers exist for this subject/grade".
get_pool() caches its result per (subject, grade) forever, so a single
transient failure at the wrong moment permanently zeroed out that subject/
grade's question pool for the rest of the process's life, with nothing in any
log to explain why. This file exists because pool.py had zero dedicated test
coverage before this fix -- its corpus-reading machinery is otherwise only
exercised indirectly through routes tests that always run against a healthy
registry.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.assessment import pool as pool_module
from academicos.assessment.pool import build_pool, get_pool
from academicos.config import Config


def _make_config_with_broken_registry(tmp_path: Path) -> Config:
    """A registry.sqlite that exists but is missing the `sources` table --
    the query itself raises sqlite3.OperationalError, the same exception
    class a locked database raises. Deterministic and fast, unlike actually
    contending a file lock from a second connection."""
    cfg = Config(data_root=tmp_path)
    conn = sqlite3.connect(cfg.registry_db)
    conn.execute("CREATE TABLE not_sources (id TEXT)")
    conn.commit()
    conn.close()
    return cfg


def test_build_pool_raises_on_registry_query_failure_instead_of_returning_empty(tmp_path):
    cfg = _make_config_with_broken_registry(tmp_path)
    with pytest.raises(sqlite3.OperationalError):
        build_pool(cfg, subject="Science", grade="X")


def test_get_pool_does_not_cache_a_failed_build(tmp_path, monkeypatch):
    """The real bug: get_pool's cache assignment must not run when the
    underlying build fails, or a transient error becomes permanent for the
    life of the process."""
    monkeypatch.setattr(pool_module, "_CACHE", {})
    cfg = _make_config_with_broken_registry(tmp_path)

    with pytest.raises(sqlite3.OperationalError):
        get_pool(cfg, subject="Science", grade="X")
    assert ("Science", "X") not in pool_module._CACHE, (
        "a failed build must not be cached -- otherwise every future call "
        "for this subject/grade silently replays the empty pool forever"
    )

    # Fix the registry (simulating the lock clearing / table existing on
    # retry) and confirm a subsequent call succeeds and *does* get cached --
    # proving the failure above didn't leave the pool machinery in a broken
    # state, only refused to memoize the bad result.
    conn = sqlite3.connect(cfg.registry_db)
    conn.execute(
        "CREATE TABLE sources (source_id TEXT, doc_type TEXT, subject TEXT, "
        "grade TEXT, academic_year TEXT)"
    )
    conn.commit()
    conn.close()
    pool = get_pool(cfg, subject="Science", grade="X")
    assert pool.questions == []
    assert ("Science", "X") in pool_module._CACHE


# --------------------------------------------------------------------------- #
# paper code extraction
#
# pool.py carried its own third copy of the CBSE paper-code pattern, separate
# from `answer_key.normalize_paper_code` and `question_bank._CODE_HINT`. All
# three required a two-or-three digit series, so none of them could read an
# English board paper (`1/4/1`, `2/5/1`). Fixing the other two was not enough:
# this is the copy paper generation actually uses, so English papers still
# reached the optimiser with `paper_code == ""` and no marking scheme.
# --------------------------------------------------------------------------- #

class _Page:
    def __init__(self, text: str) -> None:
        self.text = text


class _Doc:
    def __init__(self, text: str) -> None:
        self.pages = [_Page(text)]


@pytest.mark.parametrize("header,expected", [
    # verbatim first-page headers from the parsed corpus
    ("1/4/1 \nH 1 H  \nP.T.O.\nCandidates must write the Q.P. Code ", "1/4/1"),
    ("2/5/1 \n1 \nP.T.O. \nCandidates must write the Q.P. Code on ", "2/5/1"),
    ("2/4/1-14 \n1 \nP.T.O. \nCandidates must write the Q.P. Code ", "2/4/1"),
    # the two-digit series must keep working
    ("Series X_086  31/1/1  Science  Page 1 of 27", "31/1/1"),
])
def test_pool_reads_single_digit_english_series_codes(header, expected):
    assert pool_module._paper_code_of(_Doc(header)) == expected


def test_pool_does_not_read_a_year_as_a_paper_code():
    assert pool_module._paper_code_of(_Doc("Examination 2025-1-1 session")) == ""


def test_pool_returns_empty_for_a_doc_with_no_pages():
    class _Empty:
        pages: list = []

    assert pool_module._paper_code_of(_Empty()) == ""


# --------------------------------------------------------------------------- #
# one bank, one answer (Task 126)
#
# D17, from the re-audit of 2026-09-23: `/v1` sold 4,575 class 6-10
# Mathematics/Science records and this module composed papers from 4,099 of the
# same academicos-data/syllabus/questions.json. Mathematics 6 read 555 on the
# API and 446 here. The difference was a second set of fidelity rules that only
# this module ran -- `has_broken_options`, `needs_missing_figure`,
# `looks_truncated` and a 0.75-Jaccard near-duplicate index -- written for, and
# measured on, the registry path's raw PDF extraction and simply wrong over
# records `bank_merge` had already repaired and normalised.
#
# tests/test_bank_surfaces_agree.py holds the two surfaces together across all
# 33 class 6-10 pairs. These two are the pool's own half of it, in the module
# that was wrong: it composes the file as it stands, and it keeps no copy of
# the rule that decides what the file holds.
# --------------------------------------------------------------------------- #

_SERVED_BANK = ROOT / "academicos-data" / "syllabus" / "questions.json"


@pytest.mark.skipif(not _SERVED_BANK.exists(), reason="served bank not built")
def test_the_pool_composes_every_mathematics_6_record_the_served_file_holds(tmp_path,
                                                                           monkeypatch):
    """Requirement 3 for the pair the audit named. One pair, not all 33: this
    reads the real 15 MB bank, and the other 32 are asserted in
    tests/test_bank_surfaces_agree.py.

    ACOS_DATA_ROOT is tmp_path so every store is built under tmp; the bank is
    the committed one, which `_baked_bank_paths` reads from the repo.
    """
    import json

    from academicos.assessment import grades

    in_file = [rec for rec in
               json.loads(_SERVED_BANK.read_text(encoding="utf-8"))["questions"]
               if str(rec.get("subject") or "").strip() == "Mathematics"
               and rec.get("grade") == 6]
    assert in_file, "the served bank holds no Mathematics 6 records at all"

    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr(pool_module, "_CACHE", {})
    cfg = Config(data_root=tmp_path)
    cfg._load_baked_questions = True
    built = build_pool(cfg, subject="Mathematics", grade=grades.to_roman("6"))

    assert len(built.questions) == len(in_file), (
        f"the paper builder composes {len(built.questions)} Mathematics 6 "
        f"questions from a file that holds {len(in_file)}; every record the "
        "file holds is one the merge's gate passed, so the pool has no "
        "grounds to drop any of them (D17: 446 against 555)")
    assert {q.id for q in built.questions} == {rec["id"] for rec in in_file}


def test_the_pool_asks_the_gate_and_keeps_no_copy_of_it():
    """`pool.py` must not name a servability rule of its own. It imports the
    two gate functions -- one per corpus, `raw_extraction_reason` for the raw
    parse output the registry path reads and `unservable_reason` for the
    merged records the baked path reads -- and nothing else from
    `bank_merge`'s rule set.

    A source scan rather than a behaviour test, as Task 16 did for the merge's
    own filters: the rules were shared by import before this and the module
    was still a second answer, because it ordered and applied them itself.
    """
    source = Path(pool_module.__file__).read_text(encoding="utf-8")
    body = "\n".join(line for line in source.splitlines()
                     if not line.lstrip().startswith("#"))

    for rule in ("has_broken_options", "needs_missing_figure", "looks_truncated",
                 "unanswerable_reason", "exclusion_reason"):
        assert rule not in body, (
            f"pool.py names {rule}, which is half of an answer to \"can this "
            "be served\"; ask bank_merge.raw_extraction_reason (raw "
            "extraction) or bank_merge.unservable_reason (a merged record)")
    assert "raw_extraction_reason(" in body and "unservable_reason(" in body, (
        "pool.py must call both gates: the registry path reads raw PDF "
        "extraction and the baked path reads the merge's own output")
