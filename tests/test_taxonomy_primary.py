"""The primary-class taxonomy trees, and the id the exercise bank points at.

`scripts/build_taxonomy_primary.py` reads the chapter transcriptions and the
chapter text, and writes the classes 1-5 trees `TopicTagger` and
`merge_question_banks.py` read. Two things must hold, and both are about the id:
a tree that names a chapter the bank does not point at is dead weight, and one
that renames a chapter silently drops its questions out of the merge's chapter
offer. So the tests below fix the id, and fix the page a heading resolves to.
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.corpus import textbook as tb  # noqa: E402


def _script():
    spec = importlib.util.spec_from_file_location(
        "build_taxonomy_primary", ROOT / "scripts" / "build_taxonomy_primary.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


BOOK = {"code": "aejm1", "class": 1, "subject": "Mathematics",
        "title": "Joyful-Mathematics", "language": "en"}


def _write(tmp_path, book, number, title, topics, text):
    """One transcription and its chapter text, as the pipeline leaves them."""
    tr = tmp_path / "transcriptions"
    ct = tmp_path / "chapters_text"
    (ct / book["code"]).mkdir(parents=True)
    (ct / book["code"] / f"{number:02d}.txt").write_text(text, encoding="utf-8")
    tr.mkdir(parents=True, exist_ok=True)
    (tr / f"{book['code']}-{number:02d}.json").write_text(json.dumps(
        {"book": book, "chapter": {"number": number, "title": title},
         "topics": topics, "questions": []}), encoding="utf-8")
    return tr, ct


def _topic(n):
    return {"id": f"t{n}", "title": f"Heading {n}", "startsWith": f"start of {n}"}


def test_chapter_id_is_the_id_the_exercise_bank_uses(tmp_path):
    # The builder and the exercise bank must agree, or the tree names chapters
    # no record points at and every class 1-5 question loses its chapter.
    mod = _script()
    tr, ct = _write(tmp_path, BOOK, 1, "Finding the Furry Cat!",
                    [_topic(1)], "[page 3]\nstart of 1\n")
    trees, problems = mod.collect(tr, ct)
    assert not problems
    [(chapter)] = trees[("Mathematics", 1)]["chapters"]
    assert chapter["id"] == tb.chapter_id("Mathematics", 1, "Finding the Furry Cat!")
    assert chapter["id"] == "mathematics-1/finding-the-furry-cat"


def test_printed_book_subject_names_the_tree_file(tmp_path):
    # The book prints "The World Around Us"; the bank files it under EVS, and
    # the tree has to be EVS_3.json or nothing downstream will find it.
    mod = _script()
    book = dict(BOOK, code="ceev1", **{"class": 3, "subject": "The World Around Us"})
    tr, ct = _write(tmp_path, book, 1, "My Body", [_topic(1)], "[page 5]\nstart of 1\n")
    trees, _ = mod.collect(tr, ct)
    assert set(trees) == {("EVS", 3)}
    [(chapter)] = trees[("EVS", 3)]["chapters"]
    assert chapter["id"] == tb.chapter_id("EVS", 3, "My Body")


def test_a_heading_gets_the_page_it_prints_on(tmp_path):
    # A heading is located by the line it starts with, so the page is the one
    # printed at that line -- not the first page of the chapter.
    mod = _script()
    text = "[page 4]\nstart of 1\nbody\n[page 9]\nstart of 2\n"
    tr, ct = _write(tmp_path, BOOK, 1, "Numbers", [_topic(1), _topic(2)], text)
    trees, problems = mod.collect(tr, ct)
    assert not problems
    [(chapter)] = trees[("Mathematics", 1)]["chapters"]
    assert [t["name"] for t in chapter["topics"]] == ["Heading 1", "Heading 2"]
    assert [t["page"] for t in chapter["topics"]] == [4, 9]
    assert chapter["pages"] == [4, 9]


def test_a_heading_the_text_does_not_hold_is_reported(tmp_path):
    # Counted and reported, not silently dropped: a heading with no page is a
    # chapter whose questions the tagger cannot place.
    mod = _script()
    tr, ct = _write(tmp_path, BOOK, 1, "Numbers", [_topic(1)],
                    "[page 2]\nnothing like the anchor\n")
    trees, problems = mod.collect(tr, ct)
    [(chapter)] = trees[("Mathematics", 1)]["chapters"]
    assert chapter["topics"][0]["page"] is None
    assert any("not located" in p["problem"] for p in problems)


def test_curly_quotes_and_dashes_do_not_break_the_anchor(tmp_path):
    # The book prints typographic quotes; the transcription writes ASCII.
    mod = _script()
    topics = [{"id": "t1", "title": "Let us Sing",
               "startsWith": "“Let us sing,” she said—loudly"}]
    text = "[page 6]\n\u201cLet us sing,\u201d she said\u2014loudly\n"
    tr, ct = _write(tmp_path, BOOK, 1, "Poems", topics, text)
    trees, problems = mod.collect(tr, ct)
    assert not problems
    [(chapter)] = trees[("Mathematics", 1)]["chapters"]
    assert chapter["topics"][0]["page"] == 6


def test_solve2_files_are_not_chapters(tmp_path):
    # The second model's answers sit beside each chapter as <book>-<nn>.solve2.
    # Read as a chapter they would double every tree entry.
    mod = _script()
    tr, ct = _write(tmp_path, BOOK, 1, "Numbers", [_topic(1)], "[page 1]\nstart of 1\n")
    (tr / f"{BOOK['code']}-01.solve2.json").write_text(json.dumps(
        {"book": BOOK, "chapter": {"number": 1, "title": "Numbers"},
         "topics": [_topic(1)], "questions": []}), encoding="utf-8")
    trees, _ = mod.collect(tr, ct)
    assert len(trees[("Mathematics", 1)]["chapters"]) == 1


def test_two_books_printing_the_same_chapter_title_keep_both_ids(tmp_path):
    # Ids are unique across every tree, so a shared title must not collide.
    mod = _script()
    a = dict(BOOK)
    b = dict(BOOK, code="bejm1", title="Other Book")
    for book in (a, b):
        _write(tmp_path, book, 1, "Addition", [_topic(1)], "[page 1]\nstart of 1\n")
    trees, _ = mod.collect(tmp_path / "transcriptions", tmp_path / "chapters_text")
    ids = [c["id"] for c in trees[("Mathematics", 1)]["chapters"]]
    assert len(ids) == 2 and len(set(ids)) == 2


def test_a_class_6_chapter_is_left_to_the_pdf_builder(tmp_path):
    # Classes 6-10 come from the books' own typography; this builder is only
    # for the primary classes, so it must not claim their chapters.
    mod = _script()
    tr, ct = _write(tmp_path, dict(BOOK, **{"class": 6}), 1, "Number Play",
                    [_topic(1)], "[page 1]\nstart of 1\n")
    assert mod.collect(tr, ct) == ({}, [])


@pytest.mark.parametrize("grade", [1, 2, 3, 4, 5])
def test_every_primary_grade_is_built(tmp_path, grade):
    mod = _script()
    book = dict(BOOK, **{"class": grade})
    tr, ct = _write(tmp_path, book, 1, "Chapter", [_topic(1)], "[page 1]\nstart of 1\n")
    trees, _ = mod.collect(tr, ct)
    assert set(trees) == {("Mathematics", grade)}


def test_a_built_topic_carries_the_subtopic_key_the_audit_walks():
    # `build_taxonomy.invariant_errors` does `seq.extend(t["subtopics"])` on every
    # topic in every committed tree, so a topic without the key is a KeyError in
    # the audit rather than a shorter tree. The primary books' headings are one
    # level deep, so the list is empty -- but it has to be there.
    mod = _script()
    tr, ct = _write(tmp_path := _fresh(), BOOK, 1, "Numbers", [_topic(1)],
                    "[page 1]\nstart of 1\n")
    trees, _ = mod.collect(tr, ct)
    [(chapter)] = trees[("Mathematics", 1)]["chapters"]
    [(topic)] = chapter["topics"]
    assert topic["subtopics"] == []


def _fresh() -> Path:
    import tempfile

    return Path(tempfile.mkdtemp())


def test_the_primary_trees_satisfy_the_committed_audit():
    # The real trees, through the real invariant check, so a primary tree can
    # never reach the taxonomy directory in a shape the audit rejects.
    trees_dir = ROOT / "academicos-data" / "syllabus" / "taxonomy"
    builder = ROOT / "scripts" / "build_taxonomy.py"
    if not trees_dir.is_dir() or not builder.is_file():
        pytest.skip("the taxonomy trees are not built here")
    spec = importlib.util.spec_from_file_location("build_taxonomy_audit", builder)
    mod = importlib.util.module_from_spec(spec)
    # build_taxonomy's dataclasses look themselves up in sys.modules to resolve
    # their field types, so the module has to be registered before it is run.
    sys.modules["build_taxonomy_audit"] = mod
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.modules.pop("build_taxonomy_audit", None)

    checked = 0
    for tree_path in sorted(trees_dir.glob("*.json")):
        if tree_path.name.startswith("_") or tree_path.name == "review_queue.json":
            continue
        grade = tree_path.stem.rsplit("_", 1)[-1]
        if not grade.isdigit() or not 1 <= int(grade) <= 5:
            continue
        tree = json.loads(tree_path.read_text(encoding="utf-8"))
        assert mod.invariant_errors(tree) == [], tree_path.name
        checked += 1
    if not checked:
        pytest.skip("the primary trees are not built here")


def test_committed_primary_trees_name_chapters_the_bank_points_at():
    # The real trees, against the real exercise bank: every class 1-5 chapter a
    # record carries must be named by a tree, or that record is offered under
    # no chapter at all.
    bank = ROOT / "academicos-data" / "corpus" / "ncert-textbook" / "questions.json"
    taxonomy = ROOT / "academicos-data" / "syllabus" / "taxonomy"
    if not bank.exists():
        pytest.skip("the exercise bank is not built here")
    wanted = {q["taxonomyChapterId"] for q in json.loads(
        bank.read_text(encoding="utf-8"))["questions"]
        if (q.get("grade") or 0) <= 5 and q.get("taxonomyChapterId")}
    named = set()
    for tree in sorted(taxonomy.glob("*.json")):
        if tree.name.startswith("_") or "_" not in tree.stem:
            continue
        grade = tree.stem.rsplit("_", 1)[-1]
        if not grade.isdigit() or not 1 <= int(grade) <= 5:
            continue
        for chapter in json.loads(tree.read_text(encoding="utf-8"))["chapters"]:
            named.add(chapter["id"])
    if not named:
        pytest.skip("the primary trees are not built here")
    assert wanted - named == set()
