"""scripts/merge_question_banks.py, run against temporary files."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

import merge_question_banks as mqb  # noqa: E402
from test_bank_merge import board, cbe_mcq  # noqa: E402


def _write(path: Path, questions, **extra):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"questions": questions, **extra}), encoding="utf-8")


@pytest.fixture
def layout(tmp_path):
    paths = mqb.Paths(
        served=tmp_path / "served.json", apk=tmp_path / "apk.json",
        cbe=tmp_path / "cbe.json", sqp=tmp_path / "sqp.json",
        excluded=tmp_path / "excluded.json")
    _write(paths.served, [board()], chapterTaggedAt="t", chapterTagMethod="m")
    _write(paths.cbe, [cbe_mcq()], chapterTaggedAt="t", builtAt="2026-09-19T00:00:00+00:00")
    _write(paths.sqp, [], chapterTaggedAt="t", builtAt="2026-09-19T00:00:00+00:00")
    return paths


def test_writes_served_and_apk_byte_identical(layout):
    assert mqb.run(layout, check=False) == 0
    assert layout.served.read_bytes() == layout.apk.read_bytes()
    ids = [q["id"] for q in json.loads(layout.served.read_text(encoding="utf-8"))["questions"]]
    assert ids == [board()["id"], cbe_mcq()["id"]]


def test_is_idempotent(layout):
    mqb.run(layout, check=False)
    first = layout.served.read_bytes()
    mqb.run(layout, check=False)
    assert layout.served.read_bytes() == first


def test_check_writes_nothing(layout):
    before = layout.served.read_bytes()
    assert mqb.run(layout, check=True) == 0
    assert layout.served.read_bytes() == before
    assert not layout.apk.exists()


def test_refuses_an_untagged_source(layout):
    """Rebuilding a builder discards chapter tags; merging then ships class 6-9 untagged."""
    _write(layout.cbe, [cbe_mcq()])
    assert mqb.run(layout, check=False) != 0
    assert not layout.apk.exists()


def test_records_every_exclusion(layout):
    _write(layout.cbe, [board(7, id="cbe:q:F", source="cbse_question_bank",
                              metadata={"needsFigure": True})], chapterTaggedAt="t")
    mqb.run(layout, check=False)
    excluded = json.loads(layout.excluded.read_text(encoding="utf-8"))
    assert [e["reason"] for e in excluded["excluded"]] == ["figure-unavailable"]


def test_scheme_coverage_counts_carried_official_schemes(layout):
    mqb.run(layout, check=False)
    payload = json.loads(layout.served.read_text(encoding="utf-8"))
    assert payload["schemeCoverage"] == 1.0
    assert payload["composedFrom"] == {"board": 1, "cbe": 1, "sqp": 0}
