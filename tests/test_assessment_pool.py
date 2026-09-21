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
