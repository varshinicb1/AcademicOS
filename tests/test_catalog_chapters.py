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
from academicos.corpus.bank_merge import CONTENT_CODE  # noqa: E402
from academicos.syllabus.cbse_syllabus import load_syllabus  # noqa: E402

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

            syllabus = load_syllabus(subject, grade)
            if syllabus is not None:
                known = {chapter.id for _unit, chapter in syllabus.all_chapters()}
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
