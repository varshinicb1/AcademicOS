"""The baked-bank path must serve the record it loaded, not a reconstruction."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from academicos.assessment import mapping, pool as pool_module  # noqa: E402
from academicos.config import Config  # noqa: E402
from academicos.corpus import bank_merge as bm  # noqa: E402
from test_bank_merge import board, cbe_mcq  # noqa: E402


def _pool(tmp_path, monkeypatch, records, subject, grade):
    path = tmp_path / "q.json"
    path.write_text(json.dumps({"questions": records}), encoding="utf-8")
    monkeypatch.setattr(pool_module, "_baked_bank_paths", lambda cfg: [path])
    cfg = Config(data_root=tmp_path)
    cfg._load_baked_questions = True
    return pool_module.build_pool(cfg, subject=subject, grade=grade)


def test_source_is_the_records_own(tmp_path, monkeypatch):
    rec, _ = bm.normalise(cbe_mcq())
    built = _pool(tmp_path, monkeypatch, [rec], "Mathematics", "VII")
    assert mapping.to_question_schema(built.questions[0]).source == "cbse_question_bank"


def test_the_official_objective_scheme_survives(tmp_path, monkeypatch):
    """Every SQP MCQ lost its key: the key is in markingPoints, modelAnswer is empty."""
    rec, _ = bm.normalise(cbe_mcq())
    schema = mapping.to_question_schema(
        _pool(tmp_path, monkeypatch, [rec], "Mathematics", "VII").questions[0])
    assert schema.answer_scheme.metadata["correctOption"] == "B"
    assert schema.answer_scheme.marking_points


def test_inline_options_reach_the_stem(tmp_path, monkeypatch):
    rec, _ = bm.normalise(cbe_mcq())
    schema = mapping.to_question_schema(
        _pool(tmp_path, monkeypatch, [rec], "Mathematics", "VII").questions[0])
    assert "(A) avoid" in schema.stem


def test_board_questions_come_first(tmp_path, monkeypatch):
    """Existing class 10/12 papers must not be silently re-composed from SQP items."""
    sqp = board(2, id="cbse:sqp:X:Science:2", source="cbse_sample_paper",
                stem="Describe how a rainbow is formed after rain, question 2.")
    built = _pool(tmp_path, monkeypatch, [sqp, board()], "Science", "X")
    assert [q.id for q in built.questions][0] == board()["id"]


def test_the_fallback_applies_the_same_quality_gates(tmp_path, monkeypatch):
    fig = board(3, stem="Study the figure given below and answer the question that follows.")
    built = _pool(tmp_path, monkeypatch, [fig], "Science", "X")
    assert built.questions == []
