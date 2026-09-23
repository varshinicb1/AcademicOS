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
from academicos.assessment.question_bank import SCHEME_VERIFIER  # noqa: E402
from test_bank_merge import board, cbe_mcq, exemplar_mcq, exemplar_short  # noqa: E402

# What enrich_question_bank.py writes on a bank its relink verified. The merge
# refuses a served bank without it (see the tests at the end).
STAMP = {"schemeVerifier": SCHEME_VERIFIER}


def _write(path: Path, questions, **extra):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"questions": questions, **extra}), encoding="utf-8")


@pytest.fixture
def layout(tmp_path):
    paths = mqb.Paths(
        served=tmp_path / "served.json", apk=tmp_path / "apk.json",
        cbe=tmp_path / "cbe.json", sqp=tmp_path / "sqp.json",
        excluded=tmp_path / "excluded.json")
    _write(paths.served, [board()], chapterTaggedAt="t", chapterTagMethod="m", **STAMP)
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
    # No Exemplar file in this layout: the source counts none, and is not refused.
    assert payload["composedFrom"] == {"board": 1, "cbe": 1, "sqp": 0, "exemplar": 0}


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
    #
    # The id asked for here is the book's, not a CBSE unit's: Mathematics_10
    # used to list the 7 marks-bearing units with no chapter list, so each unit
    # stood in for a chapter and "algebra" was a chapter id. It now carries the
    # 14 chapters of the book the class actually reads, which is the vocabulary
    # the question bank is tagged in (see
    # scripts/syllabus_chapters_from_taxonomy.py). What this test is about --
    # that a variant subject inherits the base subject's chapter names and does
    # not leak the base subject itself into the keys -- is unchanged.
    names = mqb._chapter_names([board(subject="Mathematics (Standard)", grade=10),
                                board(2, subject="Mathematics (Basic, VIC)", grade=10)])
    chapter = "mathematics-10/real-numbers"
    assert names[("Mathematics (Standard)", 10, chapter)] == "Real Numbers"
    assert names[("Mathematics (Basic, VIC)", 10, chapter)] == "Real Numbers"
    assert not any(subject == "Mathematics" for subject, _g, _c in names)

def test_check_reports_the_codes_it_resolved_and_the_ones_it_dropped(layout, capsys):
    """Task 121: a content code is resolved to the chapter the record names
    ("Operations with Integers" is a real class 7 chapter) or dropped
    ("Geometry" is a strand, and no class 7 chapter is called that). Both ids
    were shown to a teacher before, "7N1A" and "7G2B", and 7N1a/7N1b listed one
    chapter twice.

    The resolving tag is the CURRENT book's name for that chapter. It used to
    be "Integers", which is what the pre-2024 book called it; Mathematics_7's
    syllabus file now lists Ganita Prakash 7, the book the class reads and the
    one the bank is tagged against, where the chapter is "Operations with
    Integers". A tag of "Integers" would now be dropped rather than resolved --
    correctly, since no class 7 chapter carries that name any more."""
    _write(layout.cbe, [
        cbe_mcq(1, chapterIds=["7N1a"], tags=["Operations with Integers"]),
        cbe_mcq(2, chapterIds=["7G2b"], tags=["Geometry"],
                stem="Which of these is the smallest number? Select one option.")],
        chapterTaggedAt="t")
    assert mqb.run(layout, check=True) == 0
    out = capsys.readouterr().out
    assert "chapter ids resolved to a syllabus chapter: 1; dropped, no chapter named: 1" in out
    assert "chapter ids the syllabus cannot name (non-board): 0" in out
    assert "records with no chapter id (non-board): 1" in out


def test_check_still_reports_a_label_two_chapters_share(layout, capsys):
    """A subject with no syllabus file has nothing to resolve against, so its
    ids are left alone -- and the phone's picker can still show one label on
    two of them."""
    _write(layout.cbe, [
        cbe_mcq(1, subject="Home Science", grade=10, chapterIds=["hs1"],
                tags=["Meal Planning"]),
        cbe_mcq(2, subject="Home Science", grade=10, chapterIds=["hs2"],
                tags=["Meal Planning"],
                stem="Which of these is the smallest number? Select one option.")],
        chapterTaggedAt="t")
    assert mqb.run(layout, check=True) == 0
    out = capsys.readouterr().out
    assert "chapter ids the syllabus cannot name (non-board): 2" in out
    assert "Home Science 10: 'Meal Planning' covers hs1, hs2" in out


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
    _write(layout.served, [board(1), unverified],
           chapterTaggedAt="t", chapterTagMethod="m", **STAMP)
    for _ in range(2):
        assert mqb.run(layout, check=False) == 0

    served_ids, held = _board_ids(layout)
    assert served_ids == {board(1)["id"]}
    assert held == [unverified]
    excluded = json.loads(layout.excluded.read_text(encoding="utf-8"))["excluded"]
    assert [(e["id"], e["reason"]) for e in excluded] == [(unverified["id"], "no-verified-key")]


def test_a_withheld_record_the_relink_later_verifies_is_served_again(layout):
    unverified = _unverified(2)
    _write(layout.served, [board(1), unverified],
           chapterTaggedAt="t", chapterTagMethod="m", **STAMP)
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
    _write(layout.served, [board(1), _unverified(2)],
           chapterTaggedAt="t", chapterTagMethod="m", **STAMP)
    assert mqb.run(layout, check=True) == 0
    assert not layout.excluded.with_name("board_withheld.json").exists()


# ---- a bank the relink has not stamped ---------------------------------------

def test_a_never_relinked_bank_makes_the_merge_refuse(layout, capsys):
    """No board record carries the relink's stamp before enrich runs, so a
    merge then would withhold every one and ship a bank with no board
    question -- and exit 0. It refuses instead, writing nothing."""
    _write(layout.served, [_unverified(1), _unverified(2)],
           chapterTaggedAt="t", chapterTagMethod="m")
    before = layout.served.read_bytes()
    assert mqb.run(layout, check=False) != 0
    assert "run scripts/enrich_question_bank.py first" in capsys.readouterr().out
    assert layout.served.read_bytes() == before
    assert not layout.apk.exists()
    assert not layout.excluded.exists()
    assert not layout.excluded.with_name("board_withheld.json").exists()


def test_check_on_a_never_relinked_bank_reports_the_refusal(layout, capsys):
    _write(layout.served, [_unverified(1)], chapterTaggedAt="t", chapterTagMethod="m")
    assert mqb.run(layout, check=True) != 0
    assert "run scripts/enrich_question_bank.py first" in capsys.readouterr().out


def test_the_refusal_can_be_overridden_explicitly(layout):
    _write(layout.served, [_unverified(1)], chapterTaggedAt="t", chapterTagMethod="m", **STAMP)
    assert mqb.run(layout, check=False, allow_no_board=True) == 0
    served_ids, held = _board_ids(layout)
    assert served_ids == set() and [q["id"] for q in held] == [_unverified(1)["id"]]


def test_the_merge_refuses_a_bank_the_relink_has_not_stamped(layout, capsys):
    """Pipeline order (Task 151's concern): the merge serves what the relink
    verified, so a merge run before enrich_question_bank.py would serve the
    labels of a bank no verifier has seen. The relink stamps the bank it
    wrote; the merge refuses one without the stamp, writing nothing, even
    when every board record looks verified -- and --allow-no-board, which
    overrides a different refusal, does not override this one."""
    _write(layout.served, [board(1)], chapterTaggedAt="t", chapterTagMethod="m")
    before = layout.served.read_bytes()
    for kwargs in ({"check": False}, {"check": True},
                   {"check": False, "allow_no_board": True}):
        assert mqb.run(layout, **kwargs) != 0
        out = capsys.readouterr().out
        assert "not been through the scheme verifier" in out
        assert "run scripts/enrich_question_bank.py first" in out
    assert layout.served.read_bytes() == before
    assert not layout.apk.exists()
    assert not layout.excluded.exists()
    assert not layout.excluded.with_name("board_withheld.json").exists()


def test_the_merge_refuses_a_bank_stamped_by_an_older_verifier(layout, capsys):
    _write(layout.served, [board(1)], chapterTaggedAt="t", chapterTagMethod="m",
           schemeVerifier="an older verifier")
    assert mqb.run(layout, check=False) != 0
    out = capsys.readouterr().out
    assert "'an older verifier'" in out and SCHEME_VERIFIER in out
    assert not layout.apk.exists()


def test_a_stamped_bank_that_verified_nothing_is_still_refused(layout, capsys):
    """The stamp says the relink ran, not that it verified anything: a bank
    with no verified board record is still the no-board refusal."""
    _write(layout.served, [_unverified(1)], chapterTaggedAt="t", chapterTagMethod="m",
           **STAMP)
    assert mqb.run(layout, check=False) != 0
    assert "carries a verified key" in capsys.readouterr().out
    assert not layout.apk.exists()


def test_the_merge_keeps_the_stamp_it_read(layout):
    assert mqb.run(layout, check=False) == 0
    for path in (layout.served, layout.apk):
        assert json.loads(path.read_text(encoding="utf-8"))["schemeVerifier"] == SCHEME_VERIFIER


# ---- Task 16: what the fidelity gate removes, measured without writing -------

def _furniture_mcq():
    """Biology XII 57/1/1 Q2, verified B, with the paper's "-11" after option D."""
    rec = board(3, subject="Biology", grade=12, marks=1, type="very_short_answer",
                stem="Which one of the following hormones is secreted by the human placenta "
                     "that helps in the maintenance of pregnancy ? (A) Relaxin (B) Human "
                     "Chorionic Gonadotropin (C) Oxytocin (D) Human Placental Lactogen -11")
    rec["answerScheme"]["metadata"].update(objective=True, correctOption="B")
    return rec


def _no_options():
    """Accountancy XII 67/1/2 Q31, verified: its items never came through."""
    return board(4, subject="Accountancy", grade=12, stem=(
        "Classify the following items under major heads and sub-heads (if any) in the "
        "Balance Sheet of a company as per Schedule III, Part I of the Companies Act, 2013 :"))


def test_check_reports_board_reasons_repairs_and_counts_by_subject_and_grade(layout, capsys):
    _write(layout.served, [board(1), _furniture_mcq(), _no_options()],
           chapterTaggedAt="t", chapterTagMethod="m", **STAMP)
    assert mqb.run(layout, check=True) == 0
    out = capsys.readouterr().out
    assert "cbse_board_paper     options-missing" in out
    assert "repairs: page-furniture-stripped 1" in out
    assert "served by subject x grade" in out
    # subject, grade, before (the served file now), after (this merge), board
    rows = {tuple(line.split()[:2]): [int(n) for n in line.split()[2:]]
            for line in out.split("served by subject x grade")[1].splitlines()[2:]
            if line.strip() and line.split()[-1].isdigit()}
    assert rows[("Accountancy", "12")] == [1, 0, 0]
    assert rows[("Biology", "12")] == [1, 1, 1]
    assert rows[("Mathematics", "7")] == [0, 1, 0]


def test_a_board_record_the_fidelity_gate_excludes_is_withheld_whole(layout):
    no_options = _no_options()
    _write(layout.served, [board(1), no_options],
           chapterTaggedAt="t", chapterTagMethod="m", **STAMP)
    assert mqb.run(layout, check=False) == 0
    served_ids, held = _board_ids(layout)
    assert served_ids == {board(1)["id"]}
    assert held == [no_options]
    excluded = json.loads(layout.excluded.read_text(encoding="utf-8"))["excluded"]
    assert [(e["id"], e["reason"]) for e in excluded] == [(no_options["id"], "options-missing")]


def _fake_relink(monkeypatch, calls):
    """Stands in for the relink: stamps every board record it is given as
    verified, in place, as relink_answer_schemes does."""
    from academicos.assessment import question_bank

    def relink(records, index, *, parse_dir, **_kw):
        calls.append([r["id"] for r in records])
        for r in records:
            r["answerScheme"] = board(1)["answerScheme"]
        return None

    monkeypatch.setattr(question_bank, "relink_answer_schemes", relink)
    monkeypatch.setattr(question_bank, "AnswerKeyIndex", lambda path: object())


def test_check_can_relink_in_memory_and_writes_nothing(layout, monkeypatch, capsys):
    """Task 11 runs the relink for real; until then the tracked bank carries
    no verifier stamp, and --check --relink-in-memory measures the merge on a
    relinked copy without writing it."""
    _write(layout.served, [_unverified(1), _unverified(2)],
           chapterTaggedAt="t", chapterTagMethod="m")
    before = layout.served.read_bytes()
    calls = []
    _fake_relink(monkeypatch, calls)
    assert mqb.run(layout, check=True, relink_in_memory=True) == 0
    out = capsys.readouterr().out
    assert "relinked in memory" in out
    assert "'board': 2" in out
    assert calls == [[_unverified(1)["id"], _unverified(2)["id"]]]
    assert layout.served.read_bytes() == before
    assert not layout.apk.exists()
    assert not layout.excluded.exists()
    assert not layout.excluded.with_name("board_withheld.json").exists()


def test_relink_in_memory_reads_the_withheld_board_records_too(layout, monkeypatch):
    _write(layout.served, [_unverified(1)], chapterTaggedAt="t", chapterTagMethod="m")
    _write(layout.excluded.with_name("board_withheld.json"), [_unverified(2)])
    calls = []
    _fake_relink(monkeypatch, calls)
    assert mqb.run(layout, check=True, relink_in_memory=True) == 0
    assert calls == [[_unverified(1)["id"], _unverified(2)["id"]]]


def test_relink_in_memory_is_refused_without_check(layout, monkeypatch, capsys):
    _write(layout.served, [_unverified(1)], chapterTaggedAt="t", chapterTagMethod="m")
    before = layout.served.read_bytes()
    _fake_relink(monkeypatch, [])
    assert mqb.run(layout, check=False, relink_in_memory=True) != 0
    assert "--relink-in-memory" in capsys.readouterr().out
    assert layout.served.read_bytes() == before
    assert not layout.apk.exists()


# ---- NCERT Exemplar, a further source (Task 11) ---------------------------------

def test_the_exemplar_bank_is_merged_and_counted(layout, capsys):
    layout.exemplar = layout.cbe.with_name("exemplar.json")
    # The Exemplar builder tags its own chapters (from the book's chapter
    # title) and writes no chapterTaggedAt; the merge does not refuse it.
    _write(layout.exemplar, [exemplar_mcq(), exemplar_short()],
           builtAt="2026-09-22T00:00:00+00:00")
    assert mqb.run(layout, check=False) == 0
    payload = json.loads(layout.served.read_text(encoding="utf-8"))
    assert payload["composedFrom"] == {"board": 1, "cbe": 1, "sqp": 0, "exemplar": 2}
    served = {q["id"]: q for q in payload["questions"]}
    assert served[exemplar_mcq()["id"]]["answerScheme"]["provenance"] == "ncert_exemplar_answer"
    assert layout.served.read_bytes() == layout.apk.read_bytes()
    assert "'exemplar': 2" in capsys.readouterr().out


def test_an_exemplar_exclusion_is_recorded(layout):
    layout.exemplar = layout.cbe.with_name("exemplar.json")
    _write(layout.exemplar, [exemplar_short(
        stem="Study the figure given below and name the process shown in it.")])
    assert mqb.run(layout, check=False) == 0
    excluded = json.loads(layout.excluded.read_text(encoding="utf-8"))["excluded"]
    assert [(e["source"], e["reason"]) for e in excluded] == [("ncert_exemplar", "figure-referenced")]
