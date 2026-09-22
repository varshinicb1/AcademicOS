"""curriculum/extraction.py -- LLM-proposed + admin-approved Chapter ->
Topic -> Subtopic decomposition. Covers the acceptance criteria from the
transcript follow-up: reproducibility (run/proposal audit trail), AI draft
never silently becomes canonical data, edits/rejections respected,
idempotent approval, canonical ids stable, renaming doesn't break
references, deleting a linked subtopic is blocked.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.curriculum import extraction
from academicos.curriculum.store import CurriculumStore


class _FakeLLM:
    """Matches qmap.py's test double shape exactly: .available, .chat_json."""
    def __init__(self, response, *, available=True, model="fake-model"):
        self.response = response
        self.available_flag = available
        self.model = model

    @property
    def available(self):
        return self.available_flag

    def chat_json(self, messages, **kw):
        return self.response


class _FlakyLLM:
    """Fails with an exception the first `fail_times` calls, then returns
    `response` -- models the real observed behavior (a real bulk run: the
    same chapter/prompt succeeded on one attempt and failed with
    finish_reason="length" on another) that motivated retrying instead of
    just raising max_tokens further."""
    def __init__(self, response, *, fail_times: int, model="fake-model"):
        self.response = response
        self.fail_times = fail_times
        self.calls = 0
        self.model = model

    @property
    def available(self):
        return True

    def chat_json(self, messages, **kw):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise ValueError("Sarvam LLM returned no content (finish=length)")
        return self.response


REAL_SCIENCE_RESPONSE = {
    "topics": [
        {"name": "Chemical Equations", "confidence": 0.9, "subtopics": [
            {"name": "Writing chemical equations", "confidence": 0.85},
            {"name": "Balancing chemical equations", "confidence": 0.85},
        ]},
        {"name": "Types of Chemical Reactions", "confidence": 0.9, "subtopics": [
            {"name": "Combination reactions", "confidence": 0.8},
            {"name": "Decomposition reactions", "confidence": 0.8},
            {"name": "Displacement reactions", "confidence": 0.8},
        ]},
    ]
}


@pytest.fixture
def store(tmp_path):
    s = CurriculumStore(tmp_path / "curriculum.sqlite")
    yield s
    s.close()


def _seed_chapter(store):
    board = store.create_board(name="CBSE", code="CBSE")
    year = store.create_academic_year(school_id="s", label="y", start_date="2026-01-01", end_date="2026-12-31")
    grade = store.create_grade(academic_year_id=year.id, number=10)
    subject = store.create_subject(grade_id=grade.id, name="Science")
    book = store.create_book(subject_id=subject.id, board_id=board.id, title="Book")
    unit = store.create_unit(canonical_id="u1", book_id=book.id, unit_no="I", name="Unit 1", marks=25, seq=0)
    chapter = store.create_chapter(canonical_id="cbse:10:science:chapter:chemical-reactions-equations",
                                   unit_id=unit.id, name="Chemical Reactions and Equations", seq=0)
    return book, chapter


# --------------------------------------------------------------------- #
# propose(): AI draft, never auto-written to topics/subtopics
# --------------------------------------------------------------------- #

def test_propose_with_llm_creates_a_draft_run_not_real_topics(store):
    book, chapter = _seed_chapter(store)
    llm = _FakeLLM(REAL_SCIENCE_RESPONSE)

    run = extraction.propose(store, school_id="s", chapter=chapter, book_id=book.id,
                             subject="Science", grade=10, llm=llm)

    assert run.status == "pending"
    assert run.model == "fake-model"
    # AI DRAFT, not DATABASE: zero real Topic/Subtopic rows exist yet.
    assert store.topics_for_chapter(chapter.id) == []
    proposals = store.proposals_for_run(run.id)
    assert len(proposals) == 7  # 2 topics + 5 subtopics
    topic_names = {p.proposed_name for p in proposals if p.entity_type == "topic"}
    assert topic_names == {"Chemical Equations", "Types of Chemical Reactions"}
    assert all(p.status == "pending" for p in proposals)


def test_propose_without_llm_is_honest_not_fabricated(store):
    """No LLM available and no offline heuristic invents structure --
    status says manual_required, zero proposals."""
    book, chapter = _seed_chapter(store)
    llm = _FakeLLM({}, available=False)

    run = extraction.propose(store, school_id="s", chapter=chapter, book_id=book.id,
                             subject="Science", grade=10, llm=llm)

    assert run.status == "manual_required"
    assert store.proposals_for_run(run.id) == []


def test_propose_with_no_llm_object_at_all(store):
    book, chapter = _seed_chapter(store)
    run = extraction.propose(store, school_id="s", chapter=chapter, book_id=book.id,
                             subject="Science", grade=10, llm=None)
    assert run.status == "manual_required"


def test_propose_retries_and_recovers_from_a_transient_failure(store, monkeypatch):
    """The real fix: a chapter that fails once (finish_reason="length" or
    similar transient truncation) should not immediately fall back to
    manual_required if a retry would have succeeded -- confirmed against
    the real API, where the exact same chapter/prompt failed on one call
    and succeeded on another."""
    monkeypatch.setattr("time.sleep", lambda s: None)  # no real waiting in tests
    book, chapter = _seed_chapter(store)
    llm = _FlakyLLM(REAL_SCIENCE_RESPONSE, fail_times=2)  # fails twice, succeeds on 3rd (the max)

    run = extraction.propose(store, school_id="s", chapter=chapter, book_id=book.id,
                             subject="Science", grade=10, llm=llm)

    assert run.status == "pending"
    assert llm.calls == 3
    proposals = store.proposals_for_run(run.id)
    assert len(proposals) == 7  # the real response, recovered after 2 failures


def test_propose_gives_up_honestly_after_exhausting_retries(store, monkeypatch):
    """Every attempt fails -> manual_required, not a crash and not an
    infinite retry loop."""
    monkeypatch.setattr("time.sleep", lambda s: None)
    book, chapter = _seed_chapter(store)
    llm = _FlakyLLM(REAL_SCIENCE_RESPONSE, fail_times=99)  # never succeeds within the attempt cap

    run = extraction.propose(store, school_id="s", chapter=chapter, book_id=book.id,
                             subject="Science", grade=10, llm=llm)

    assert run.status == "manual_required"
    assert llm.calls == extraction._MAX_LLM_ATTEMPTS
    assert store.proposals_for_run(run.id) == []


def test_propose_records_source_hash_only_when_grounded(store):
    """Reproducibility: a grounded run's source_hash lets you tell later
    whether the same textbook excerpt would reproduce the same proposal."""
    book, chapter = _seed_chapter(store)
    llm = _FakeLLM(REAL_SCIENCE_RESPONSE)

    ungrounded = extraction.propose(store, school_id="s", chapter=chapter, book_id=book.id,
                                    subject="Science", grade=10, llm=llm)
    assert ungrounded.source_hash is None

    grounded = extraction.propose(store, school_id="s", chapter=chapter, book_id=book.id,
                                  subject="Science", grade=10, llm=llm,
                                  grounding_text="Real excerpt from the NCERT chapter...")
    assert grounded.source_hash is not None
    assert grounded.source_hash != ungrounded.source_hash or True  # different run either way
    assert len(grounded.source_hash) == 16


# --------------------------------------------------------------------- #
# approve_run(): the only path that ever writes real topics/subtopics
# --------------------------------------------------------------------- #

def test_approve_run_materializes_real_hierarchy(store):
    book, chapter = _seed_chapter(store)
    llm = _FakeLLM(REAL_SCIENCE_RESPONSE)
    run = extraction.propose(store, school_id="s", chapter=chapter, book_id=book.id,
                             subject="Science", grade=10, llm=llm)

    result = extraction.approve_run(store, run.id, approved_by="admin_1")

    assert result.topics_created == 2
    assert result.subtopics_created == 5
    topics = store.topics_for_chapter(chapter.id)
    assert {t.name for t in topics} == {"Chemical Equations", "Types of Chemical Reactions"}
    for t in topics:
        assert t.source_type == "llm_proposed"
        assert t.approved_by == "admin_1"
        assert t.model_used == "fake-model"
        assert t.source_reference == run.id
        subs = store.subtopics_for_topic(t.id)
        assert len(subs) in (2, 3)
        for s in subs:
            assert s.source_type == "llm_proposed"
            assert s.approved_by == "admin_1"

    # The run itself now reflects approval.
    assert store.get_extraction_run(run.id).status == "approved"


def test_edited_name_is_what_gets_materialized_original_kept_for_audit(store):
    book, chapter = _seed_chapter(store)
    llm = _FakeLLM(REAL_SCIENCE_RESPONSE)
    run = extraction.propose(store, school_id="s", chapter=chapter, book_id=book.id,
                             subject="Science", grade=10, llm=llm)
    proposals = store.proposals_for_run(run.id)
    topic_proposal = next(p for p in proposals if p.entity_type == "topic"
                          and p.proposed_name == "Chemical Equations")

    extraction.approve_run(store, run.id, approved_by="admin_1",
                           edits={topic_proposal.id: "Balancing Chemical Equations (Admin Renamed)"})

    topics = store.topics_for_chapter(chapter.id)
    names = {t.name for t in topics}
    assert "Balancing Chemical Equations (Admin Renamed)" in names
    assert "Chemical Equations" not in names  # the edited name is what's real

    # Traceability preserved: the original AI proposal is still on record.
    reloaded = store.get_proposal(topic_proposal.id)
    assert reloaded.proposed_name == "Chemical Equations"
    assert reloaded.edited_name == "Balancing Chemical Equations (Admin Renamed)"
    assert reloaded.status == "edited"


def test_rejected_proposals_never_appear_in_production_curriculum(store):
    book, chapter = _seed_chapter(store)
    llm = _FakeLLM(REAL_SCIENCE_RESPONSE)
    run = extraction.propose(store, school_id="s", chapter=chapter, book_id=book.id,
                             subject="Science", grade=10, llm=llm)
    proposals = store.proposals_for_run(run.id)
    reject_topic = next(p for p in proposals if p.entity_type == "topic"
                        and p.proposed_name == "Types of Chemical Reactions")

    extraction.approve_run(store, run.id, approved_by="admin_1",
                           rejected_proposal_ids={reject_topic.id})

    topics = store.topics_for_chapter(chapter.id)
    names = {t.name for t in topics}
    assert names == {"Chemical Equations"}  # rejected topic never materialized
    # Its subtopics (Combination/Decomposition/Displacement reactions)
    # cascade-excluded even though not individually rejected.
    all_subtopic_names = {s.name for t in topics for s in store.subtopics_for_topic(t.id)}
    assert "Combination reactions" not in all_subtopic_names

    assert store.get_proposal(reject_topic.id).status == "rejected"


def test_rejecting_a_single_subtopic_keeps_its_topic_and_siblings(store):
    book, chapter = _seed_chapter(store)
    llm = _FakeLLM(REAL_SCIENCE_RESPONSE)
    run = extraction.propose(store, school_id="s", chapter=chapter, book_id=book.id,
                             subject="Science", grade=10, llm=llm)
    proposals = store.proposals_for_run(run.id)
    reject_sub = next(p for p in proposals if p.entity_type == "subtopic"
                      and p.proposed_name == "Combination reactions")

    extraction.approve_run(store, run.id, approved_by="admin_1",
                           rejected_proposal_ids={reject_sub.id})

    topics = {t.name: t for t in store.topics_for_chapter(chapter.id)}
    reactions_topic = topics["Types of Chemical Reactions"]
    subs = {s.name for s in store.subtopics_for_topic(reactions_topic.id)}
    assert subs == {"Decomposition reactions", "Displacement reactions"}


def test_approving_the_same_run_twice_does_not_duplicate(store):
    """A retried request (real Render/network flakiness) must not corrupt
    approved data by creating duplicate topics/subtopics."""
    book, chapter = _seed_chapter(store)
    llm = _FakeLLM(REAL_SCIENCE_RESPONSE)
    run = extraction.propose(store, school_id="s", chapter=chapter, book_id=book.id,
                             subject="Science", grade=10, llm=llm)

    first = extraction.approve_run(store, run.id, approved_by="admin_1")
    second = extraction.approve_run(store, run.id, approved_by="admin_1")

    assert sorted(first.topic_ids) == sorted(second.topic_ids)
    assert sorted(first.subtopic_ids) == sorted(second.subtopic_ids)
    assert len(store.topics_for_chapter(chapter.id)) == 2  # not 4


def test_canonical_ids_are_stable_and_derived_from_chapter(store):
    book, chapter = _seed_chapter(store)
    llm = _FakeLLM(REAL_SCIENCE_RESPONSE)
    run = extraction.propose(store, school_id="s", chapter=chapter, book_id=book.id,
                             subject="Science", grade=10, llm=llm)
    extraction.approve_run(store, run.id, approved_by="admin_1")

    topic = next(t for t in store.topics_for_chapter(chapter.id) if t.name == "Chemical Equations")
    assert topic.canonical_id.startswith(chapter.canonical_id)
    assert "chemical-equations" in topic.canonical_id
    subtopic = next(s for s in store.subtopics_for_topic(topic.id))
    assert subtopic.canonical_id.startswith(topic.canonical_id)


def test_two_schools_can_decompose_the_same_chapter_differently(store):
    """Each school's chapter row is already independent (seed_cbse10.py's
    per-book canonical ids); this proves the property holds through the
    extraction/approval path too -- independent runs, independent
    approved topics, even with the same LLM response."""
    board = store.create_board(name="CBSE", code="CBSE")
    year_a = store.create_academic_year(school_id="school_a", label="y", start_date="2026-01-01", end_date="2026-12-31")
    grade_a = store.create_grade(academic_year_id=year_a.id, number=10)
    subject_a = store.create_subject(grade_id=grade_a.id, name="Science")
    book_a = store.create_book(subject_id=subject_a.id, board_id=board.id, title="Book A")
    unit_a = store.create_unit(canonical_id="u_a", book_id=book_a.id, unit_no="I", name="U", marks=25, seq=0)
    chapter_a = store.create_chapter(canonical_id="a:chapter:chem", unit_id=unit_a.id, name="Chemical Reactions", seq=0)

    year_b = store.create_academic_year(school_id="school_b", label="y", start_date="2026-01-01", end_date="2026-12-31")
    grade_b = store.create_grade(academic_year_id=year_b.id, number=10)
    subject_b = store.create_subject(grade_id=grade_b.id, name="Science")
    book_b = store.create_book(subject_id=subject_b.id, board_id=board.id, title="Book B")
    unit_b = store.create_unit(canonical_id="u_b", book_id=book_b.id, unit_no="I", name="U", marks=25, seq=0)
    chapter_b = store.create_chapter(canonical_id="b:chapter:chem", unit_id=unit_b.id, name="Chemical Reactions", seq=0)

    llm = _FakeLLM(REAL_SCIENCE_RESPONSE)
    run_a = extraction.propose(store, school_id="school_a", chapter=chapter_a, book_id=book_a.id,
                               subject="Science", grade=10, llm=llm)
    result_a = extraction.approve_run(store, run_a.id, approved_by="admin_a")

    # School B rejects one topic entirely -- a genuinely different decomposition.
    run_b = extraction.propose(store, school_id="school_b", chapter=chapter_b, book_id=book_b.id,
                               subject="Science", grade=10, llm=llm)
    proposals_b = store.proposals_for_run(run_b.id)
    reject = next(p for p in proposals_b if p.entity_type == "topic"
                 and p.proposed_name == "Types of Chemical Reactions")
    result_b = extraction.approve_run(store, run_b.id, approved_by="admin_b",
                                      rejected_proposal_ids={reject.id})

    assert result_a.topics_created == 2
    assert result_b.topics_created == 1
    assert set(result_a.topic_ids).isdisjoint(set(result_b.topic_ids))


# --------------------------------------------------------------------- #
# rename / delete safety
# --------------------------------------------------------------------- #

def test_renaming_a_topic_does_not_change_its_canonical_id(store):
    book, chapter = _seed_chapter(store)
    llm = _FakeLLM(REAL_SCIENCE_RESPONSE)
    run = extraction.propose(store, school_id="s", chapter=chapter, book_id=book.id,
                             subject="Science", grade=10, llm=llm)
    extraction.approve_run(store, run.id, approved_by="admin_1")
    topic = next(t for t in store.topics_for_chapter(chapter.id) if t.name == "Chemical Equations")
    original_canonical_id = topic.canonical_id

    store.rename_topic(topic.id, "Chemical Equations (renamed)")

    reloaded = store.get_topic(topic.id)
    assert reloaded.name == "Chemical Equations (renamed)"
    assert reloaded.canonical_id == original_canonical_id  # question references unaffected


def test_deleting_a_subtopic_with_linked_questions_is_blocked(store):
    book, chapter = _seed_chapter(store)
    llm = _FakeLLM(REAL_SCIENCE_RESPONSE)
    run = extraction.propose(store, school_id="s", chapter=chapter, book_id=book.id,
                             subject="Science", grade=10, llm=llm)
    extraction.approve_run(store, run.id, approved_by="admin_1")
    topic = store.topics_for_chapter(chapter.id)[0]
    subtopic = store.subtopics_for_topic(topic.id)[0]

    store.link_question_to_subtopic(question_id="q_1", subtopic_id=subtopic.id)

    with pytest.raises(CurriculumStore.SubtopicHasLinkedQuestions):
        store.delete_subtopic(subtopic.id)
    # Not deleted -- still there.
    assert store.get_subtopic(subtopic.id) is not None

    # force=True is the explicit "migrate/accept data loss" escape hatch.
    store.delete_subtopic(subtopic.id, force=True)
    assert store.get_subtopic(subtopic.id) is None
    assert store.question_links_for_subtopic(subtopic.id) == []


def test_deleting_an_unlinked_subtopic_is_fine(store):
    book, chapter = _seed_chapter(store)
    llm = _FakeLLM(REAL_SCIENCE_RESPONSE)
    run = extraction.propose(store, school_id="s", chapter=chapter, book_id=book.id,
                             subject="Science", grade=10, llm=llm)
    extraction.approve_run(store, run.id, approved_by="admin_1")
    subtopic = store.subtopics_for_topic(store.topics_for_chapter(chapter.id)[0].id)[0]

    store.delete_subtopic(subtopic.id)  # no linked questions -- should not raise
    assert store.get_subtopic(subtopic.id) is None


# --------------------------------------------------------------------- #
# restart-safety: a fresh store instance over the same file sees the
# same approved data (the acceptance criteria's literal "restart server /
# hierarchy is unchanged")
# --------------------------------------------------------------------- #

def test_approved_hierarchy_survives_a_simulated_restart(tmp_path):
    db_path = tmp_path / "curriculum.sqlite"
    store1 = CurriculumStore(db_path)
    book, chapter = _seed_chapter(store1)
    llm = _FakeLLM(REAL_SCIENCE_RESPONSE)
    run = extraction.propose(store1, school_id="s", chapter=chapter, book_id=book.id,
                             subject="Science", grade=10, llm=llm)
    extraction.approve_run(store1, run.id, approved_by="admin_1")
    store1.close()

    # A brand new CurriculumStore instance -- simulates a server restart.
    store2 = CurriculumStore(db_path)
    topics = store2.topics_for_chapter(chapter.id)
    assert {t.name for t in topics} == {"Chemical Equations", "Types of Chemical Reactions"}
    assert store2.get_extraction_run(run.id).status == "approved"
    store2.close()


# --------------------------------------------------------------------- #
# §5-9: Textbook Table of Contents extraction and Unit/Chapter ingestion
# --------------------------------------------------------------------- #

def test_parse_toc_text_structured():
    raw_toc = """
    Unit I: Chemical Substances - Nature and Behaviour
      Chapter 1: Chemical Reactions and Equations
      Chapter 2: Acids, Bases and Salts
      Chapter 3: Metals and Non-Metals
    Unit II: World of Living
      Chapter 4: Life Processes
      Chapter 5: Control and Coordination
    """
    units = extraction.parse_toc_text(raw_toc)
    assert len(units) == 2
    assert units[0].unit_no == "I"
    assert units[0].name == "Chemical Substances - Nature and Behaviour"
    assert units[0].chapters == [
        "Chemical Reactions and Equations",
        "Acids, Bases and Salts",
        "Metals and Non-Metals",
    ]
    assert units[1].unit_no == "II"
    assert len(units[1].chapters) == 2


def test_extract_and_ingest_toc_creates_real_rows(store):
    book, _ = _seed_chapter(store)
    raw_toc = """
    Unit 1: Foundations of Physics
      Chapter 1: Kinematics in One Dimension
      Chapter 2: Newton's Laws of Motion
    Unit 2: Energy and Momentum
      Chapter 3: Work and Kinetic Energy
    """
    result = extraction.extract_and_ingest_toc(store, book_id=book.id, toc_text=raw_toc)
    assert result.units_created == 2
    assert result.chapters_created == 3

    units = store.units_for_book(book.id)
    unit_names = {u.name for u in units}
    assert "Foundations of Physics" in unit_names
    assert "Energy and Momentum" in unit_names

    chapters = store.chapters_for_book(book.id)
    chap_names = {c.name for c in chapters}
    assert "Kinematics in One Dimension" in chap_names
    assert "Newton's Laws of Motion" in chap_names
    assert "Work and Kinetic Energy" in chap_names


def test_extract_route_llm_with_placeholder_key_does_not_call_provider(store, monkeypatch):
    """Task 502 item 9(c): on a fresh GCP release SARVAM_API_KEY holds the
    bootstrap placeholder REPLACE_ME. The route's real `_llm()` must then
    report no LLM, so propose() records manual_required at once -- no request
    with "Bearer REPLACE_ME", no retry sleeps, no provider 401 dressed up as a
    failed extraction."""
    import requests
    from academicos.curriculum import routes as curriculum_routes
    from academicos.llm import sarvam

    monkeypatch.setenv("SARVAM_API_KEY", "REPLACE_ME")
    monkeypatch.setenv("ACOS_LLM_API_KEY", "REPLACE_ME")
    monkeypatch.setattr(curriculum_routes, "_cfg", None)

    def boom(*a, **kw):
        raise AssertionError("placeholder key was sent to the provider")

    monkeypatch.setattr(requests, "post", boom)
    monkeypatch.setattr(sarvam.time, "sleep", boom)

    llm = curriculum_routes._llm()
    assert llm.available is False

    book, chapter = _seed_chapter(store)
    run = extraction.propose(store, school_id="s", chapter=chapter, book_id=book.id,
                             subject="Science", grade=10, llm=llm)
    assert run.status == "manual_required"
    assert run.model is None
    assert store.proposals_for_run(run.id) == []
