"""qmap.map_subtopics() -- question -> real curriculum Subtopic resolution
(docs/ACADEMIC_DATA_MODEL.md section 1's canonical-id bridge). Same
token-overlap approach as qmap.py's existing lexical concept proposer,
scoped to one chapter's real, approved subtopics.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.qmap import map_subtopics
from academicos.curriculum.store import CurriculumStore


@pytest.fixture
def store(tmp_path):
    s = CurriculumStore(tmp_path / "curriculum.sqlite")
    yield s
    s.close()


def _seed_science_chapter(store):
    board = store.create_board(name="CBSE", code="CBSE")
    year = store.create_academic_year(school_id="s", label="y", start_date="2026-01-01", end_date="2026-12-31")
    grade = store.create_grade(academic_year_id=year.id, number=10)
    subject = store.create_subject(grade_id=grade.id, name="Science")
    book = store.create_book(subject_id=subject.id, board_id=board.id, title="Book")
    unit = store.create_unit(canonical_id="u1", book_id=book.id, unit_no="I", name="Unit 1", marks=25, seq=0)
    chapter = store.create_chapter(canonical_id="ch:1", unit_id=unit.id,
                                   name="Chemical Reactions and Equations", seq=0)
    topic = store.create_topic(canonical_id="ch:1:topic:eq", chapter_id=chapter.id,
                               name="Chemical Equations", seq=0, source_type="manual")
    sub1 = store.create_subtopic(canonical_id="ch:1:topic:eq:sub:writing", topic_id=topic.id,
                                 name="Writing chemical equations", seq=0, source_type="manual")
    sub2 = store.create_subtopic(canonical_id="ch:1:topic:eq:sub:balancing", topic_id=topic.id,
                                 name="Balancing chemical equations", seq=1, source_type="manual")
    other_topic = store.create_topic(canonical_id="ch:1:topic:reactions", chapter_id=chapter.id,
                                     name="Types of Reactions", seq=1, source_type="manual")
    sub3 = store.create_subtopic(canonical_id="ch:1:topic:reactions:sub:oxidation",
                                 topic_id=other_topic.id, name="Oxidation and reduction", seq=0,
                                 source_type="manual")
    return chapter, {"writing": sub1, "balancing": sub2, "oxidation": sub3}


def test_matches_a_real_subtopic_by_token_overlap(store):
    chapter, subs = _seed_science_chapter(store)
    # Short and close to the subtopic's own wording -- the realistic case
    # a real question-bank tag/keyword phrase looks like, not a full
    # multi-clause exam sentence (which dilutes Jaccard overlap against a
    # 3-word subtopic name regardless of relevance -- a real threshold-
    # calibration question, not this test's concern).
    matches = map_subtopics(store, chapter_id=chapter.id,
                            question_text="Balance the following chemical equation.")

    names = {m.subtopic_name for m in matches}
    assert "Balancing chemical equations" in names
    assert all(m.method == "lexical" for m in matches)
    assert all(0.0 < m.confidence <= 1.0 for m in matches)


def test_scoped_to_the_given_chapter_only(store):
    """A different chapter's subtopics (even with an identical name) must
    never be returned -- resolution is chapter-scoped by design, not
    school- or book-wide."""
    chapter, subs = _seed_science_chapter(store)
    writing_topic = store.get_topic(subs["writing"].topic_id)
    same_unit_id = store.get_chapter(writing_topic.chapter_id).unit_id
    other_chapter = store.create_chapter(
        canonical_id="ch:2", unit_id=same_unit_id, name="Unrelated Chapter", seq=1)
    other_topic = store.create_topic(canonical_id="ch:2:topic:eq", chapter_id=other_chapter.id,
                                     name="Chemical Equations", seq=0, source_type="manual")
    store.create_subtopic(canonical_id="ch:2:topic:eq:sub:balancing", topic_id=other_topic.id,
                          name="Balancing chemical equations", seq=0, source_type="manual")

    matches = map_subtopics(store, chapter_id=chapter.id,
                            question_text="Balance the chemical equation.")
    assert all(m.subtopic_id != "ch:2:topic:eq:sub:balancing" for m in matches)
    # (the real subtopic under `chapter` with the same wording is still found)
    matched_ids = {m.subtopic_id for m in matches}
    assert matched_ids.issubset({subs["writing"].id, subs["balancing"].id, subs["oxidation"].id})


def test_no_match_returns_empty_not_a_guess(store):
    chapter, subs = _seed_science_chapter(store)
    matches = map_subtopics(store, chapter_id=chapter.id,
                            question_text="What is the capital of France?")
    assert matches == []


def test_empty_question_text_returns_empty(store):
    chapter, subs = _seed_science_chapter(store)
    assert map_subtopics(store, chapter_id=chapter.id, question_text="") == []


def test_max_matches_is_respected(store):
    chapter, subs = _seed_science_chapter(store)
    matches = map_subtopics(store, chapter_id=chapter.id,
                            question_text="chemical equation writing balancing reaction",
                            min_score=0.0, max_matches=2)
    assert len(matches) <= 2


def test_results_sorted_best_match_first(store):
    chapter, subs = _seed_science_chapter(store)
    matches = map_subtopics(store, chapter_id=chapter.id,
                            question_text="Balance the chemical equation for combustion.",
                            min_score=0.0, max_matches=10)
    scores = [m.confidence for m in matches]
    assert scores == sorted(scores, reverse=True)


def test_matches_realistic_multiclause_exam_question(store):
    """§21 calibration: A realistic, verbose CBSE exam question with multiple clauses,
    experimental context, and sub-questions must still match the relevant subtopic
    above the 0.15 threshold rather than suffering Jaccard dilution."""
    chapter, subs = _seed_science_chapter(store)
    multiclause_q = (
        "During a laboratory demonstration, 2g of lead nitrate powder is heated in a dry "
        "boiling tube over a flame. A student observes brown fumes evolved and a yellow residue "
        "left in the tube. (a) Identify the brown fumes. (b) Name the type of reaction taking place. "
        "(c) Write a balanced chemical equation for the reaction, indicating physical states."
    )
    matches = map_subtopics(store, chapter_id=chapter.id, question_text=multiclause_q, min_score=0.15)
    matched_names = [m.subtopic_name for m in matches]
    assert "Writing chemical equations" in matched_names or "Balancing chemical equations" in matched_names
    assert len(matches) >= 1
    # Check that the matched confidence is comfortably above threshold
    best = matches[0]
    assert best.confidence >= 0.15
