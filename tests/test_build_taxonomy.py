"""scripts/build_taxonomy.py: the tree, its measurement, and the checks that
stop a wrong tree being written.

Real chapters come from ``tests/_textbook_lines.py`` (text-layer lines of the
cited PDF pages); the "PDFs" handed to `build_tree` are empty files, because
`build_tree` reads through the injected reader and never opens them.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _textbook_lines import CHAPTERS  # noqa: E402

from academicos.syllabus import textbook_headings as th  # noqa: E402


@pytest.fixture(scope="module")
def bt():
    spec = importlib.util.spec_from_file_location("build_taxonomy", ROOT / "scripts" / "build_taxonomy.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["build_taxonomy"] = mod      # its dataclasses look themselves up there
    try:
        spec.loader.exec_module(mod)
        yield mod
    finally:
        sys.modules.pop("build_taxonomy", None)


def _lines(key: str) -> list[th.Line]:
    return [th.Line(*t) for t in CHAPTERS[key]]


def _folder_tree(bt, tmp_path, folder, files, source, subject="Mathematics", grade=7):
    """build_tree over a folder of chapter files whose lines are fixtures."""
    d = tmp_path / folder
    d.mkdir(parents=True)
    for name in files:
        (d / f"{name}.pdf").write_bytes(b"")
    problems: list = []
    tree = bt.build_tree(subject, grade, [source], tmp_path,
                         lambda p: _lines(files[p.stem]), problems)
    return tree, problems


# --------------------------------------------------------------------------- #
# build_tree
# --------------------------------------------------------------------------- #

def test_build_tree_from_chapter_files_numbered(bt, tmp_path):
    src = bt.Source("Ganita Prakash Part 2", "chapters/gegp2", (), 2)
    tree, problems = _folder_tree(bt, tmp_path, "chapters/gegp2", {"gegp205": "gegp205"}, src)
    assert problems == []
    (ch,) = tree["chapters"]
    assert (ch["number"], ch["part"], ch["headingKind"]) == (5, 2, "numbered")
    assert ch["source_file"] == "chapters/gegp2/gegp205.pdf"
    assert [t["number"] for t in ch["topics"]] == ["5.1", "5.2", "5.3", "5.4"]
    # ids are chapter-slug/topic-slug/subtopic-slug
    assert all(t["id"].startswith(ch["id"] + "/") for t in ch["topics"])
    assert bt.invariant_errors(tree) == []


def test_build_tree_drops_the_economics_story_titles(bt, tmp_path):
    # jess202.pdf p13: "Kanta" and "Kamal", two boxed stories side by side in
    # the book's 18pt sub-section type, under "Division of Sectors as
    # Organised and Unorganised"
    econ = next(s for s in bt.TREES[("Social Science", 10)] if s.strand == "Economics")
    src = bt.Source(econ.book, "chapters/jess2", styles=econ.styles, strand="Economics",
                    skip_first_page=True, typed_titles=econ.typed_titles,
                    story_titles=econ.story_titles)
    tree, _ = _folder_tree(bt, tmp_path, "chapters/jess2", {"jess202": "jess202"}, src,
                           subject="Social Science", grade=10)
    (ch,) = tree["chapters"]
    names = [t["name"] for t in ch["topics"]] + [s["name"] for t in ch["topics"] for s in t["subtopics"]]
    assert "Division of Sectors as Organised and Unorganised" in names
    assert not {"Kanta", "Kamal"} & set(names)
    assert bt.invariant_errors(tree) == []


# --------------------------------------------------------------------------- #
# invariants and gaps
# --------------------------------------------------------------------------- #

def _tree(topics):
    return {"subject": "Mathematics", "grade": 7, "chapters": [
        {"number": 7, "name": "Finding Common Ground", "source_file": "x.pdf", "topics": topics}]}


def _t(number, name, page, subs=()):
    t = {"name": name, "page": page, "subtopics": [dict(s) for s in subs]}
    if number:
        t["number"] = number
    return t


def test_invariants_catch_a_topic_sorted_out_of_place(bt):
    # the committed Mathematics_7 ch7 before the fix: [7.2, 7.3, 7.1, ...]
    bad = _tree([_t("7.2", "B", 285), _t("7.3", "C", 291),
                 _t("7.1", "Equilateral Triangles", 277,
                    [{"name": "Two Sides and the Included Angle", "page": 291}])])
    errs = bt.invariant_errors(bad)
    assert any("pages go back" in e for e in errs)
    assert any("topic numbers out of order" in e for e in errs)


def test_invariants_catch_box_labels_and_cut_off_lines(bt):
    tree = _tree([_t("4.3", "Finding Directions", 83,
                     [{"name": "More to know!", "page": 84}, {"name": "Do you know?", "page": 85},
                      {"name": "More to", "page": 96}])])
    errs = bt.invariant_errors(tree)
    assert len(errs) == 3 and all("box label or fragment" in e for e in errs)


def test_invariants_pass_a_clean_tree_and_keep_a_numbered_cut_short_name(bt):
    # class9_ganita_manjari.pdf p73 draws the root 2 of "3.5.1 The Proof of
    # Irrationality of [root 2]": kept, and listed rather than refused
    tree = _tree([_t("3.5", "Irrational Numbers", 72,
                     [{"name": "The Proof of Irrationality of", "page": 73, "number": "3.5.1"}])])
    assert bt.invariant_errors(tree) == []
    assert bt.cut_short(tree) == [{"chapter": 7, "number": "3.5.1",
                                   "name": "The Proof of Irrationality of", "page": 73,
                                   "file": "x.pdf"}]


def test_number_gaps_are_reported(bt):
    tree = _tree([_t("5.1", "Introduction", 1), _t("5.2", "Arithmetic Progressions", 3),
                  _t("5.4", "Sum of First n Terms of an AP", 15,
                     [{"name": "a", "page": 15, "number": "5.4.1"},
                      {"name": "c", "page": 16, "number": "5.4.3"}])])
    assert bt.number_gaps(tree) == [{"number": 7, "name": "Finding Common Ground",
                                     "file": "x.pdf", "missing": ["5.3", "5.4.2"]}]
    # a section-numbered chapter (History: "1", "1.1") reports bare numbers
    hist = _tree([_t("1", "A", 2), _t("3", "C", 10)])
    assert bt.number_gaps(hist)[0]["missing"] == ["2"]


# --------------------------------------------------------------------------- #
# measure and compare_syllabus
# --------------------------------------------------------------------------- #

def test_measure_counts_a_subtopic_only_under_its_own_topic(bt):
    trees = {("Mathematics", 7): {"chapters": [{
        "source_file": "x.pdf", "number": 7, "topics": [
            {"name": "Equilateral Triangles", "subtopics": [
                {"name": "Two Sides and the Included Angle"}]},
            {"name": "Construction of Triangles", "subtopics": []},
            {"name": "Box Label", "subtopics": []}]}]}}
    gold = {"chapters": [{"family": "Maths", "file": "x.pdf", "chapter": 7, "headings": [
        {"level": 1, "name": "Equilateral Triangles"},
        {"level": 1, "name": "Construction of Triangles"},
        {"level": 2, "parent": "Construction of Triangles",
         "name": "Two Sides and the Included Angle"}]}]}
    m = bt.measure(trees, gold)
    (row,) = m["chapters"]
    assert (row["extracted"], row["handRead"], row["correct"]) == (4, 3, 2)
    assert row["wrong"] == ["boxlabel", "equilateraltriangles/twosidesandtheincludedangle"]
    assert row["missed"] == ["constructionoftriangles/twosidesandtheincludedangle"]
    assert m["byFamily"]["all"]["precision"] == 0.5
    assert m["byFamily"]["Maths"]["recall"] == 0.667


def test_compare_syllabus_lists_every_disagreement(bt, tmp_path, monkeypatch):
    syl = {"units": [{"chapters": [
        {"id": "knowing-our-numbers", "name": "Patterns in Mathematics"},
        {"id": "whole-numbers", "name": "Whole Numbers"}]}]}
    (tmp_path / "Mathematics_6.json").write_text(json.dumps(syl), encoding="utf-8")
    monkeypatch.setattr(bt, "SYLLABUS", tmp_path)
    monkeypatch.setattr(bt, "REPO", tmp_path)
    tree = {"subject": "Mathematics", "grade": 6, "chapters": [
        {"number": 1, "name": "Patterns in Mathematics", "id": "patterns-in-mathematics"},
        {"number": 2, "name": "Lines and Angles", "id": "lines-and-angles"}]}
    r = bt.compare_syllabus(tree)
    assert (r["syllabusChapters"], r["bookChapters"], r["matched"]) == (2, 2, 1)
    assert r["inSyllabusNotInBook"] == [{"id": "whole-numbers", "name": "Whole Numbers"}]
    assert r["inBookNotInSyllabus"] == ["Lines and Angles"]
    assert r["idDisagreesWithName"] == [{"id": "knowing-our-numbers", "name": "Patterns in Mathematics"}]
    assert [c["id"] for c in r["proposedChapterList"]] == ["patterns-in-mathematics", "lines-and-angles"]
    tree["subject"] = "Economics"
    assert bt.compare_syllabus(tree) is None          # no syllabus file


# --------------------------------------------------------------------------- #
# the committed trees
# --------------------------------------------------------------------------- #

def test_committed_trees_hold_the_invariants(bt):
    out = ROOT / "academicos-data" / "syllabus" / "taxonomy"
    errs = []
    for f in sorted(out.glob("[A-Z]*.json")):
        errs += bt.invariant_errors(json.loads(f.read_text(encoding="utf-8")))
    assert errs == []
