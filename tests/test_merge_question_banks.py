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


def test_chapter_names_come_from_the_syllabus():
    from academicos.syllabus.cbse_syllabus import load_syllabus

    names = mqb._chapter_names([board(subject="Mathematics", grade=6),
                                board(2, subject="Nonsense", grade=6),
                                board(3, subject="Mathematics", grade=None)])
    expected = {("Mathematics", 6, c.id): c.name
                for _u, c in load_syllabus("Mathematics", 6).all_chapters()}
    assert expected and names == expected



def test_a_paper_variant_subject_takes_its_base_subjects_chapter_names():
    # SQP files class 10 maths under 'Mathematics (Standard)', 'Mathematics
    # (Basic, VIC)' and so on; only 'Mathematics' has a syllabus file, and the
    # chapter ids are the same ones.
    names = mqb._chapter_names([board(subject="Mathematics (Standard)", grade=10),
                                board(2, subject="Mathematics (Basic, VIC)", grade=10)])
    assert names[("Mathematics (Standard)", 10, "algebra")] == "Algebra"
    assert names[("Mathematics (Basic, VIC)", 10, "algebra")] == "Algebra"
    assert not any(subject == "Mathematics" for subject, _g, _c in names)

def test_check_reports_unresolved_and_shared_chapter_labels(layout, capsys):
    _write(layout.cbe, [
        cbe_mcq(1, chapterIds=["7N1a"], tags=["Integers"]),
        cbe_mcq(2, chapterIds=["7N1b"], tags=["Integers"],
                stem="Which of these is the smallest number? Select one option.")],
        chapterTaggedAt="t")
    assert mqb.run(layout, check=True) == 0
    out = capsys.readouterr().out
    assert "chapter ids the syllabus cannot name (non-board): 2" in out
    assert "records with no chapter id (non-board): 0" in out
    assert "Mathematics 7: 'Integers' covers 7N1a, 7N1b" in out


# ---- board records the no-verified-key gate withholds ------------------------

def _unverified(i):
    """A board record as a relink leaves one it could not verify: its
    scheme quarantined, an empty scheme of its own mark value in its place."""
    rec = board(i, stem=f"Why is the sea salty, question {i}?")
    rec["answerScheme"] = {"totalMarks": 2, "markingPoints": [], "rubricLevels": [],
                           "commonErrors": [], "alternativeAnswers": [], "modelAnswer": "",
                           "modelAnswerLatex": "", "provenance": "none"}
    return rec


def _board_ids(layout) -> tuple[set, list[dict]]:
    served = json.loads(layout.served.read_text(encoding="utf-8"))["questions"]
    held_path = layout.excluded.with_name("board_withheld.json")
    held = json.loads(held_path.read_text(encoding="utf-8"))["questions"]
    return ({q["id"] for q in served if q["source"] == "cbse_board_paper"}, held)


def test_two_merges_after_a_relink_keep_every_board_record_whole(layout):
    """The merge reads its board records from the file it overwrites, and
    _merge_excluded.json keeps 200 characters of a stem and is rewritten
    every run. A withheld board record is kept whole in board_withheld.json,
    which every run adds to and none overwrites, and the next merge reads it
    back: after two merges every board record is somewhere, whole."""
    unverified = _unverified(2)
    _write(layout.served, [board(1), unverified], chapterTaggedAt="t", chapterTagMethod="m")
    for _ in range(2):
        assert mqb.run(layout, check=False) == 0

    served_ids, held = _board_ids(layout)
    assert served_ids == {board(1)["id"]}
    assert held == [unverified]
    excluded = json.loads(layout.excluded.read_text(encoding="utf-8"))["excluded"]
    assert [(e["id"], e["reason"]) for e in excluded] == [(unverified["id"], "no-verified-key")]


def test_a_withheld_record_the_relink_later_verifies_is_served_again(layout):
    unverified = _unverified(2)
    _write(layout.served, [board(1), unverified], chapterTaggedAt="t", chapterTagMethod="m")
    mqb.run(layout, check=False)
    # A later, better relink verifies it where it is kept.
    held_path = layout.excluded.with_name("board_withheld.json")
    verified = board(2, stem=unverified["stem"])
    _write(held_path, [verified])

    mqb.run(layout, check=False)
    served_ids, held = _board_ids(layout)
    assert served_ids == {board(1)["id"], verified["id"]}
    assert [q["id"] for q in held] == [verified["id"]]      # never dropped


def test_check_writes_no_withheld_file(layout):
    _write(layout.served, [board(1), _unverified(2)], chapterTaggedAt="t", chapterTagMethod="m")
    assert mqb.run(layout, check=True) == 0
    assert not layout.excluded.with_name("board_withheld.json").exists()
