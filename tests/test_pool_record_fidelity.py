"""The baked-bank path must serve the record it loaded, not a reconstruction."""
from __future__ import annotations

import json
import logging
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


def test_a_board_record_beats_an_earlier_sqp_copy_of_it(tmp_path, monkeypatch):
    """SQPs reuse board questions. The near-duplicate gate keeps whichever it
    sees first, so it must see the board record first whatever the file order."""
    sqp = board(2, id="cbse:sqp:X:Science:2", source="cbse_sample_paper",
                stem=board()["stem"])
    built = _pool(tmp_path, monkeypatch, [sqp, board()], "Science", "X")
    assert [q.id for q in built.questions] == [board()["id"]]


# One stem per gate the registry path applies; each must drop the record on the
# baked path too, and the drop must be counted where the load log reports it.
_GATED = [
    ("need a figure", "Study the figure given below and answer the question that follows."),
    ("truncated/missing options",
     "Which of the following is the correct statement about photosynthesis in plants?"),
    ("broken option lists",
     "Which gas is released when zinc reacts with acid? (c) oxygen (d) hydrogen"),
]


@pytest.mark.parametrize("label,stem", _GATED, ids=[g[0] for g in _GATED])
def test_each_quality_gate_drops_and_counts(tmp_path, monkeypatch, caplog, label, stem):
    caplog.set_level(logging.INFO, logger=pool_module.log.name)
    built = _pool(tmp_path, monkeypatch, [board(3, stem=stem), board()], "Science", "X")
    assert [q.id for q in built.questions] == [board()["id"]]
    assert f"1 {label}" in caplog.text


def test_a_near_duplicate_is_dropped_and_counted(tmp_path, monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger=pool_module.log.name)
    built = _pool(tmp_path, monkeypatch, [board(), board(2, stem=board()["stem"])],
                  "Science", "X")
    assert [q.id for q in built.questions] == [board()["id"]]
    assert "1 near-duplicates" in caplog.text


def test_a_record_the_api_schema_rejects_is_dropped_at_load(tmp_path, monkeypatch, caplog):
    """A record that passes the phone contract but not QuestionSchema used to
    raise inside every paper request for its subject and grade (a 500)."""
    caplog.set_level(logging.INFO, logger=pool_module.log.name)
    bad = board(2, difficulty="impossible",
                stem="State Ohm's law and name the unit of resistance, question 2.")
    built = _pool(tmp_path, monkeypatch, [bad, board()], "Science", "X")
    assert [q.id for q in built.questions] == [board()["id"]]
    assert [mapping.to_question_schema(q).id for q in built.questions] == [board()["id"]]
    assert "1 invalid records" in caplog.text
    assert bad["id"] in caplog.text
