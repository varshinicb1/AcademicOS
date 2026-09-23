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


def test_the_baked_path_gates_what_it_loads(tmp_path, monkeypatch):
    """The baked path is a gate, not a passthrough: a record questions.json
    should never have carried does not reach a paper because it is in the
    file."""
    fig = board(3, stem="Study the figure given below and answer the question that follows.")
    built = _pool(tmp_path, monkeypatch, [fig], "Science", "X")
    assert built.questions == []


def test_a_board_record_beats_an_earlier_sqp_copy_of_it(tmp_path, monkeypatch):
    """SQPs reuse board questions, and the board copy is the one served.

    The duplicate is the merge's to reject now (Task 126) -- it is the only
    surface that sees both copies, and `assessment/pool.py` running a second,
    cruder index over the merge's output dropped 307 distinct class 6-10
    Maths/Science questions. So the end-to-end path is asserted: the merge
    excludes the SQP copy, and the pool over its output holds the board one.
    Ordering still matters here, which is what `test_board_questions_come_first`
    covers."""
    sqp = board(2, id="cbse:sqp:X:Science:2", source="cbse_sample_paper",
                stem=board()["stem"])
    result = bm.compose([board()], [], [sqp])
    assert [(e["id"], e["reason"]) for e in result.excluded] == \
        [(sqp["id"], "duplicate-stem")]
    built = _pool(tmp_path, monkeypatch, result.questions, "Science", "X")
    assert [q.id for q in built.questions] == [board()["id"]]


# One stem per shape a student could not answer. Each must be refused by the
# ONE gate -- `bank_merge.unservable_reason` -- and so be absent from the
# served file AND from the pool built over it, with the reason named.
#
# These used to be the registry path's own gates, re-applied here to merged
# records. Measured on the served bank on 2026-09-23 that was wrong in both
# directions: `has_broken_options` refused 195 answerable records (155 because
# every option is one character long -- "(A) 1 (B) 2 (C) 3 (D) 4") and
# `looks_truncated` another 37 (33 print their options as "a." or "A)", which
# its option test does not read). The merge's `mcq_shape` readers answer the
# same question on the same corpus and get it right, so they answer it once.
_GATED = [
    ("figure-unavailable",
     "Study the figure given below and answer the question that follows.", 2),
    # `_options_missing`: an MCQ lead-in with no options is refused at 1 mark,
    # where it is an MCQ. At more marks it is usually a prose list ("Which of
    # the following metals can displace the other two ... zinc, iron, copper",
    # exemplar:q:8:science:4:-:21) -- 4 served records, all answerable.
    ("options-missing",
     "Which of the following is the correct statement about photosynthesis?", 1),
    # `_options_out_of_order`: (c) and (d) with no (a) or (b).
    ("options-out-of-order",
     "Which gas is released when zinc reacts with acid? (c) oxygen (d) hydrogen", 2),
]


@pytest.mark.parametrize("reason,stem,marks", _GATED, ids=[g[0] for g in _GATED])
def test_the_one_gate_refuses_what_a_student_could_not_answer(
        tmp_path, monkeypatch, caplog, reason, stem, marks):
    caplog.set_level(logging.INFO, logger=pool_module.log.name)
    bad = board(3, stem=stem, marks=marks)
    assert bm.unservable_reason(bad) == reason

    # Absent from the served file: the merge never writes it.
    result = bm.compose([bad, board()], [], [])
    assert [q["id"] for q in result.questions] == [board()["id"]]
    assert (bad["id"], reason) in [(e["id"], e["reason"]) for e in result.excluded]

    # And absent from a paper even if a stale questions.json carries it.
    built = _pool(tmp_path, monkeypatch, [bad, board()], "Science", "X")
    assert [q.id for q in built.questions] == [board()["id"]]
    assert f"('{reason}', 1)" in caplog.text


def test_a_near_duplicate_is_dropped_and_counted():
    """Two copies of one question reach one surface -- the merge -- and it is
    the surface that rejects them. `_merge_excluded.json` then says which id
    went and why, which the pool's own counter never did."""
    result = bm.compose([board(), board(2, stem=board()["stem"])], [], [])
    assert [q["id"] for q in result.questions] == [board()["id"]]
    assert [(e["id"], e["reason"]) for e in result.excluded] == \
        [(board(2)["id"], "duplicate-stem")]


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
