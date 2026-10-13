"""The chapter list a teacher picks from: GET /catalog/{subject}/{grade}/chapters.

Read on the real served bank (academicos-data/syllabus/questions.json), because
this is a defect the bank carries, not one the route can invent: the route
names a chapter the syllabus does not know by the id itself, so a CBE content
code left on a record ("10A2b", "9.1.6", "ENG9.5") is offered to a teacher as
a chapter called "10A2B", and the chapter it belongs to is then listed twice --
Mathematics 10 showed 17 chapters and three "Trigonometry" entries at f90f42c,
against the 7 units its syllabus has. bank_merge.resolve_chapter_ids resolves
each code to the syllabus chapter the record names, or drops it.

Hermetic in the same way as tests/test_cache_headers.py: ACOS_DATA_ROOT is a
pytest tmp_path, so every store is built under tmp; the question bank is the
committed one (assessment/pool.py `_baked_bank_paths` reads it from the repo).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.api.main import app  # noqa: E402
from academicos.assessment import pillar_routes, pool as pool_module  # noqa: E402
from academicos.assessment.chapter_filing import ChapterFiling  # noqa: E402
from academicos.corpus.bank_merge import CONTENT_CODE  # noqa: E402
from academicos.syllabus.cbse_syllabus import load_syllabus, taxonomy_chapters  # noqa: E402
from academicos.syllabus.current_book import studied_chapters  # noqa: E402

SERVED_BANK = ROOT / "academicos-data" / "syllabus" / "questions.json"
# CBSE's learning-ladder content codes as the CBE item banks print them:
# "10A2b" and "6N1e" (Mathematics), "9.1.6" (Science), "ENG9.5" (English).
# The shape is `bank_merge`'s own, imported rather than copied: the merge
# takes a coded id's strand name only for ids of this shape, and a copy here
# would let the assertion and the resolver drift apart.
RELEASE_GRADES = range(6, 11)


# Where the release's questions are, and so where this must not be vacuous:
# every other class 6-10 pair is a handful of records (English 6's seven CBE
# items, all tagged with nothing but their content code) that the web pool's
# own gates can empty.
CORE = [(subject, grade) for grade in RELEASE_GRADES
        for subject in ("Mathematics", "Science")]


def _pairs() -> list[tuple[str, int]]:
    rows = json.loads(SERVED_BANK.read_text(encoding="utf-8"))["questions"]
    return sorted({(q["subject"], q["grade"]) for q in rows
                   if q.get("subject") and q.get("grade") in RELEASE_GRADES})


@pytest.fixture
def served_bank(monkeypatch):
    """The route reading the committed bank.

    `pool.build_pool` skips the baked bank under pytest unless the config asks
    for it (`_load_baked_questions`), so a route test would otherwise measure
    an empty pool and pass whatever the bank holds. The pool cache is emptied
    around the test so no other test inherits these pools.
    """
    pool_module._CACHE.clear()
    try:
        yield monkeypatch
    finally:
        pool_module._CACHE.clear()


@pytest.mark.skipif(not SERVED_BANK.exists(), reason="served bank not built")
def test_every_class_6_to_10_chapter_a_teacher_can_pick_has_a_real_name(
        tmp_path, monkeypatch, served_bank):
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    pairs = _pairs()
    assert pairs, "the served bank has no class 6-10 question"
    with TestClient(app) as client:
        pillar_routes._cfg._load_baked_questions = True
        for subject, grade in pairs:
            response = client.get(f"/api/v1/catalog/{subject}/{grade}/chapters")
            assert response.status_code == 200, (subject, grade)
            entries = response.json()
            if (subject, grade) in CORE:
                assert any(e["questionCount"] for e in entries), \
                    f"{subject} {grade} offers no question under any chapter"
            codes = [e["chapterId"] for e in entries if CONTENT_CODE.match(e["chapterId"])]
            assert codes == [], f"{subject} {grade} offers content codes as chapters: {codes}"

            names = [e["chapterName"] for e in entries]
            twice = sorted({n for n in names if names.count(n) > 1})
            assert twice == [], f"{subject} {grade} lists one chapter under several ids: {twice}"

            if load_syllabus(subject, grade) is not None:
                # The chapters the class studies now: the syllabus file's, or the
                # current book's where its school is seeded with that (#136).
                known = {chapter.id for _unit, chapter in studied_chapters(subject, grade)}
                # "unmapped" is not a claim about the syllabus: it is the
                # named bucket for questions no chapter has claimed yet, and
                # hiding it lost a teacher most of the bank (see
                # test_the_chapter_view_reaches_every_question_the_class_serves).
                unknown = sorted({e["chapterId"] for e in entries} - known - {"unmapped"})
                assert unknown == [], f"{subject} {grade} lists chapters the syllabus has not: {unknown}"


@pytest.mark.skipif(not SERVED_BANK.exists(), reason="served bank not built")
def test_the_chapter_view_reaches_every_question_the_class_serves(
        tmp_path, monkeypatch, served_bank):
    """The unmapped bucket was emitted only where NO syllabus exists, which is
    nowhere for a main subject: every question the tagger could not place
    vanished from the view a teacher picks from. Live on 2026-09-23, Science 6
    offered 12 chapters holding 8 questions while the catalog served 247, and
    Mathematics 6 offered 69 of 446. A question the bank serves and the teacher
    cannot reach is the bank's work thrown away."""
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    with TestClient(app) as client:
        pillar_routes._cfg._load_baked_questions = True
        for subject, grade in CORE:
            entries = client.get(f"/api/v1/catalog/{subject}/{grade}/chapters").json()
            shown = sum(e["questionCount"] for e in entries)
            served = client.get("/api/v1/catalog").json()
            total = next((e["questionCount"] for e in served["entries"]
                          if e["subject"] == subject and e["grade"] == grade), 0)
            assert shown == total, f"{subject} {grade}: {shown} reachable of {total} served"


# --------------------------------------------------------------------------- #
# chapter-tag coverage of the served bank (Task 123)
# --------------------------------------------------------------------------- #
# The Exemplar chapter map (taxonomy/_exemplar_chapter_map.json) files an
# Exemplar question under the chapter its own book printed it in, so these
# numbers are the book's filing plus what the tagger accepted on its own.
# Measured on 2026-09-23 after the pipeline rerun; a change that lowers one has
# lost tags, which is the thing a teacher feels first.

# Both floor sets below are ONE snapshot of ONE bank, re-measured together
# whenever the bank is rebuilt, so that a number here always names a state
# that existed. Currently: the fidelity rebuild of 2026-09-28, 5,319 records /
# 2,289 chapter tags; class 6-10 Mathematics and Science serve 4,505, of which
# the chapter view files 2,250.
#
# They have moved three times, and the reasons are worth keeping because they are
# different kinds of movement:
#   * 223 -> 220 (Mathematics 6 only, at 061176f). The id-prior used to read
#     the corrupt Mathematics_6.json, where the new book's chapter NAMES sat
#     on the old book's ids, and three records were tagged off that wrong
#     name. fb0107a fixed the file and the tagger stopped claiming them. All
#     three LOST a tag, none moved, none gained: a one-directional loss with
#     a single cause, and a tag that came from the wrong book is worth less
#     than no tag.
#   * the current numbers (at 99f3569). Task 124 re-parsed the CBE and SQP
#     banks, which changes STEMS and not just marking schemes, and the tagger
#     scores a question on its stem. Re-calibration also moved the thresholds,
#     so borderline records crossed in BOTH directions -- Mathematics 8 and 9
#     and Science 6 and 7 gained, Mathematics 6, 7 and 10 and Science 8 lost,
#     net -1 tag across the bank while filing rose by 6.
#   * the fidelity rebuild (2026-09-28). The merge now refuses questions that
#     cannot be answered as printed (corpus/fidelity.py); 45 of the removed
#     class 6-10 Mathematics/Science records carried a tag (Mathematics 6: 3,
#     8: 2, 9: 11, 10: 10; Science 6: 1, 9: 6, 10: 12), and two recovered
#     Science 10 CBE records brought 2 back. The per-record diff of the kept
#     records: 0 moved chapter, 6 gained and 5 lost a tag, each a borderline
#     confidence (about 0.01 either side of the gold-set threshold) moved by
#     the tf-idf weights of the batch -- the sources were re-tagged, because
#     the committed served bank carried tags its source banks did not, and a
#     merge rebuilds from the sources. Lowered to the measured counts on the
#     owner's rule: only where the bank holds fewer questions that are all
#     answerable.
#   * the extraction repair (2026-10-01): cbe:q:Maths10AS8 is refused as
#     `value-missing` ("(Using π= )", and its key's Rs 8800 contradicts the
#     stem's Rs 50 a metre). It carried a tag: Mathematics 10, 306 -> 305.
#     cbe:q:SCIENCE8JS41c is refused as `key-covers-one-part` (a three-part
#     question whose key answers part (a)); it carried a tag: Science 8, 75 -> 74.
# The second kind is the one to be careful with: a net that barely moves can
# hide a large two-way churn, so a rebuild that shifts these wants a
# per-record diff (id, old tag, new tag, method), not just a total.

TAG_FLOOR = {
    ("Mathematics", 6): 213, ("Mathematics", 7): 189, ("Mathematics", 8): 491,
    ("Mathematics", 9): 73, ("Mathematics", 10): 305,
    ("Science", 6): 105, ("Science", 7): 127, ("Science", 8): 74,
    ("Science", 9): 270, ("Science", 10): 397,
}
# Of those, the ones the map placed rather than the tagger.
MAP_METHOD = "exemplar-chapter-map"
MAP_TAG_FLOOR = 1626


@pytest.mark.skipif(not SERVED_BANK.exists(), reason="served bank not built")
def test_the_served_bank_keeps_the_chapter_tag_coverage_this_release_measured():
    records = json.loads(SERVED_BANK.read_text(encoding="utf-8"))["questions"]
    tagged = {}
    for rec in records:
        key = (rec.get("subject"), rec.get("grade"))
        if key not in TAG_FLOOR:
            continue
        tagged[key] = tagged.get(key, 0) + bool(rec.get("taxonomyChapterId"))
    short = {k: (tagged.get(k, 0), floor) for k, floor in TAG_FLOOR.items()
             if tagged.get(k, 0) < floor}
    assert short == {}, short


@pytest.mark.skipif(not SERVED_BANK.exists(), reason="served bank not built")
def test_the_served_bank_carries_the_exemplar_maps_own_tags():
    """A rerun that dropped the map would still pass the floor above on the
    tagger alone, slowly: this counts the tags that came from the book."""
    records = json.loads(SERVED_BANK.read_text(encoding="utf-8"))["questions"]
    by_map = [r for r in records if r.get("tagMethod") == MAP_METHOD]
    assert len(by_map) >= MAP_TAG_FLOOR, len(by_map)
    for rec in by_map:
        assert rec["taxonomyChapterId"], rec["id"]
        assert rec["tagConfidence"]["chapter"] == 1.0, rec["id"]
        for topic in rec.get("topicIds") or []:
            assert topic.startswith(rec["taxonomyChapterId"] + "/"), rec["id"]


# --------------------------------------------------------------------------- #
# the chapter view reads the tag the bank carries (Task 123 follow-up)
# --------------------------------------------------------------------------- #
# Commit 075c9ab raised `taxonomyChapterId` to 2,289 of the 4,576 class 6-10
# Mathematics/Science records and none of it reached a teacher: the route
# grouped by `chapterIds` alone, so Mathematics 6 filed 69 of its 446 served
# questions and Science 6 filed 8 of 247, unchanged by the tagging run.
#
# These floors are the chapter view measured on the served bank once the route
# read the tag. They are lower than the raw tag counts in TAG_FLOOR above
# because the web pool does not serve every record in the bank (4,099 of the
# 4,575). A change that drops one has taken chapters back off a teacher.
FILED_FLOOR = {
    # Re-measured with TAG_FLOOR above, on the same bank -- see the note there
    # for what moved and why. 2,250 filed of 4,505 served: since Task 126 the
    # web pool serves every record of the bank, so the view files every tag
    # (Science 10 files 4 more through chapterIds the syllabus knows).
    ("Mathematics", 6): 213, ("Mathematics", 7): 189, ("Mathematics", 8): 491,
    ("Mathematics", 9): 73, ("Mathematics", 10): 305,
    ("Science", 6): 105, ("Science", 7): 127, ("Science", 8): 74,
    ("Science", 9): 270, ("Science", 10): 401,
}


@pytest.mark.skipif(not SERVED_BANK.exists(), reason="served bank not built")
def test_the_chapter_view_files_the_questions_the_tagger_placed(
        tmp_path, monkeypatch, served_bank):
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    with TestClient(app) as client:
        pillar_routes._cfg._load_baked_questions = True
        short = {}
        for (subject, grade), floor in FILED_FLOOR.items():
            entries = client.get(f"/api/v1/catalog/{subject}/{grade}/chapters").json()
            filed = sum(e["questionCount"] for e in entries
                        if e["chapterId"] != "unmapped")
            if filed < floor:
                short[f"{subject} {grade}"] = (filed, floor)
        assert short == {}, short


@pytest.mark.skipif(not SERVED_BANK.exists(), reason="served bank not built")
def test_no_question_the_tagger_placed_falls_into_the_unmapped_bucket():
    """A tag that the chapter list cannot show is a tag that was not written.

    The two vocabularies are bridged in two different ways and both have to
    hold: eight files carry the taxonomy's own ids, so the tag IS the chapter
    id; Science 6 and Science 10 keep ids of their own and the tag reaches
    them by the name the book prints. If a later taxonomy rebuild moves either
    pair onto a new edition, no name will match and its tags land in
    "unmapped" -- which is what this catches.

    Every served class 6-10 pair, not only Mathematics and Science: until
    2026-10-13 the view read the syllabus file while the school's plan read the
    current book (#136), and all 128 Social Science 9 questions and 121 tagged
    English 9 questions were stranded here.
    """
    records = json.loads(SERVED_BANK.read_text(encoding="utf-8"))["questions"]
    stranded = {}
    for subject, grade in _pairs():
        filing = ChapterFiling.for_class(subject, grade)
        lost = [r["id"] for r in records
                if r.get("subject") == subject and r.get("grade") == grade
                and r.get("taxonomyChapterId")
                and filing.chapter_of(r["taxonomyChapterId"], r.get("chapterIds") or []) == "unmapped"]
        if lost:
            stranded[f"{subject} {grade}"] = (len(lost), lost[:3])
    assert stranded == {}, stranded


@pytest.mark.skipif(not SERVED_BANK.exists(), reason="served bank not built")
def test_mathematics_6_offers_the_chapters_of_the_book_its_class_studies(
        tmp_path, monkeypatch, served_bank):
    """Mathematics_6.json paired the NEW book's chapter NAMES with the OLD
    book's chapter IDS, positionally, in 9 of its 11 rows: id
    "knowing-our-numbers" was named "Patterns in Mathematics" and
    "basic-geometrical-ideas" was named "Fractions", so eleven questions about
    basic geometrical ideas were offered to a teacher under a chapter called
    "Fractions". It also listed a "Ratio and Proportion" that Ganita Prakash
    does not have."""
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    with TestClient(app) as client:
        pillar_routes._cfg._load_baked_questions = True
        entries = client.get("/api/v1/catalog/Mathematics/6/chapters").json()
        offered = {e["chapterId"]: e["chapterName"] for e in entries}
        assert "unmapped" in offered
        book = taxonomy_chapters("Mathematics", 6)
        assert book, "the Ganita Prakash tree is what the class 6 chapters come from"
        for cid, name in book.items():
            assert offered.get(cid) == name, (cid, name, offered.get(cid))
        # the pre-2024 book's chapters are not offered as if they were this
        # class's, under any id
        assert "ratio-and-proportion" not in offered
        assert "knowing-our-numbers" not in offered
