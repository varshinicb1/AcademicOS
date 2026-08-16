"""Coverage of QuestionMapStore (src/academicos/storage/question_map.py).

Complements tests/test_qmap.py, which exercises the Q→concept mapper and a
single roundtrip. These tests isolate the JSONL store itself: key stability
(dedupe), ordering, robustness to corrupt lines, counting, health and the
missing-key path.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from academicos.storage.question_map import QuestionMapStore, question_key


@pytest.fixture
def path(tmp_path: Path) -> Path:
    return tmp_path / "qm.jsonl"


@pytest.fixture
def qs(path: Path) -> QuestionMapStore:
    return QuestionMapStore(path)


def test_append_returns_stable_key(qs: QuestionMapStore) -> None:
    k = qs.append({"question": "What is photosynthesis?"})
    assert k == question_key("What is photosynthesis?")
    assert len(k) == 16


def test_dedupe_by_question_key_case_and_whitespace(qs: QuestionMapStore) -> None:
    k1 = qs.append({"question": "What  is  photosynthesis?", "concepts": ["A"]})
    k2 = qs.append({"question": "  WHAT IS PHOTOSYNTHESIS? ", "concepts": ["A"]})
    assert k1 == k2
    found = qs.for_question("what is photosynthesis?")
    assert found is not None
    assert found["key"] == k1
    assert found["question"] == "What  is  photosynthesis?"


def test_different_questions_map_to_different_keys(qs: QuestionMapStore) -> None:
    k1 = qs.append({"question": "What is a cell?"})
    k2 = qs.append({"question": "What is a gene?"})
    assert k1 != k2


def test_all_maps_preserves_append_order(qs: QuestionMapStore) -> None:
    for q in ("first?", "second?", "third?"):
        qs.append({"question": q})
    keys = [m["question"] for m in qs.all_maps()]
    assert keys == ["first?", "second?", "third?"]


def test_all_maps_skips_corrupt_and_blank_lines(path: Path) -> None:
    path.write_text(
        '{"key":"abc123","question":"good line"}\n'
        "not valid json at all\n"
        "\n"
        '{"key":"def456","question":"another good line"}\n',
        encoding="utf-8",
    )
    qs = QuestionMapStore(path)
    maps = qs.all_maps()
    assert len(maps) == 2
    assert [m["question"] for m in maps] == ["good line", "another good line"]
    assert qs.count() == 2


def test_count_matches_lines_after_append(qs: QuestionMapStore) -> None:
    assert qs.count() == 0
    qs.append({"question": "q1?"})
    qs.append({"question": "q2?"})
    assert qs.count() == 2
    # re-asking the same question still appends a line (dedupe is at the
    # key level, not storage level)
    qs.append({"question": "Q1?"})
    assert qs.count() == 3


def test_healthy_shape(qs: QuestionMapStore) -> None:
    qs.append({"question": "q?"})
    h = qs.healthy()
    assert set(h) == {"path", "mapped"}
    assert h["path"] == str(qs.path)
    assert h["mapped"] == 1


def test_append_auto_creates_parent_dir(tmp_path: Path) -> None:
    p = tmp_path / "a" / "b" / "c" / "qm.jsonl"
    qs = QuestionMapStore(p)
    qs.append({"question": "q?"})
    assert p.is_file()


def test_for_question_missing_returns_none(qs: QuestionMapStore) -> None:
    qs.append({"question": "known?"})
    assert qs.for_question("totally different question") is None


def test_for_question_normalizes_lookup(qs: QuestionMapStore) -> None:
    qs.append({"question": "Solve 2 + 2"})
    got = qs.for_question("  solve 2 + 2  ")
    assert got is not None
    assert got["key"] == question_key("Solve 2 + 2")


def test_all_maps_on_missing_file_returns_empty(path: Path) -> None:
    assert path.exists() is False
    qs = QuestionMapStore(path)
    assert qs.all_maps() == []
    assert qs.count() == 0


def test_appended_extra_fields_preserved(qs: QuestionMapStore) -> None:
    qs.append({"question": "q?", "method": "lexical", "confidence": 0.9})
    got = qs.all_maps()[0]
    assert got["method"] == "lexical"
    assert got["confidence"] == 0.9