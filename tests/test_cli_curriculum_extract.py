"""cli.py's curriculum-extract / curriculum-approve commands -- the bulk
operator tools this session's real production run (docs/plan.md-adjacent:
Class 10, 4 subjects, ~46 real chapters) actually used. extraction.py's
own functions are covered thoroughly in test_curriculum_extraction.py;
this covers the CLI layer around them: --force semantics, skipping
chapters that already have real topics, --dry-run, --reject.

Never makes a real network call -- SarvamLLM is monkeypatched at the
class level every test, even though a real SARVAM_API_KEY may be set in
this environment (it was, for the real production run this session did).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos import cli
from academicos.config import Config
from academicos.curriculum import store as curriculum_store_mod


REAL_RESPONSE = {
    "topics": [
        {"name": "Chemical Equations", "confidence": 0.9, "subtopics": [
            {"name": "Writing chemical equations", "confidence": 0.8},
        ]},
    ]
}


class _FakeSarvamLLM:
    """Drop-in for academicos.llm.sarvam.SarvamLLM -- constructed exactly
    the way cmd_curriculum_extract constructs the real one
    (SarvamLLM(api_key=...)), so patching the class is enough."""
    def __init__(self, api_key=None, **kw):
        self.model = "fake-model"

    @property
    def available(self):
        return True

    def chat_json(self, messages, **kw):
        return REAL_RESPONSE


@pytest.fixture(autouse=True)
def _reset_curriculum_singleton(monkeypatch):
    monkeypatch.setattr(curriculum_store_mod, "_INSTANCE", None)


def _config(tmp_path: Path) -> Config:
    return Config(data_root=tmp_path)


def _seed_chapter(store, *, name="Chemical Reactions and Equations"):
    board = store.create_board(name="CBSE", code="CBSE")
    year = store.create_academic_year(school_id="school_1", label="2026-27",
                                      start_date="2026-06-01", end_date="2027-04-30")
    grade = store.create_grade(academic_year_id=year.id, number=10)
    subject = store.create_subject(grade_id=grade.id, name="Science")
    book = store.create_book(subject_id=subject.id, board_id=board.id, title="Book")
    unit = store.create_unit(canonical_id="u1", book_id=book.id, unit_no="I", name="Unit", marks=25, seq=0)
    chapter = store.create_chapter(canonical_id=f"ch:{name}", unit_id=unit.id, name=name, seq=0)
    return book, chapter


def test_extract_reports_no_llm_available_without_a_key(tmp_path, monkeypatch):
    cfg = _config(tmp_path)
    monkeypatch.setattr(cli.Config, "load", staticmethod(lambda: cfg))
    monkeypatch.delenv("SARVAM_API_KEY", raising=False)
    from academicos.curriculum.store import get_curriculum_store
    store = get_curriculum_store(cfg.data_root)
    book, chapter = _seed_chapter(store)

    args = argparse.Namespace(school_id="school_1", book_id=book.id, force=False)
    assert cli.cmd_curriculum_extract(args) == 1


def test_extract_creates_proposals_for_each_chapter_without_real_topics(tmp_path, monkeypatch):
    cfg = _config(tmp_path)
    monkeypatch.setattr(cli.Config, "load", staticmethod(lambda: cfg))
    monkeypatch.setattr("academicos.llm.sarvam.SarvamLLM", _FakeSarvamLLM)
    from academicos.curriculum.store import get_curriculum_store
    store = get_curriculum_store(cfg.data_root)
    book, chapter = _seed_chapter(store)

    args = argparse.Namespace(school_id="school_1", book_id=book.id, force=False)
    assert cli.cmd_curriculum_extract(args) == 0

    runs = store.extraction_runs_for_chapter(chapter.id)
    assert len(runs) == 1
    assert runs[0].status == "pending"
    proposals = store.proposals_for_run(runs[0].id)
    assert len(proposals) == 2  # 1 topic + 1 subtopic


def test_extract_skips_chapters_that_already_have_real_topics(tmp_path, monkeypatch):
    cfg = _config(tmp_path)
    monkeypatch.setattr(cli.Config, "load", staticmethod(lambda: cfg))
    monkeypatch.setattr("academicos.llm.sarvam.SarvamLLM", _FakeSarvamLLM)
    from academicos.curriculum.store import get_curriculum_store
    store = get_curriculum_store(cfg.data_root)
    book, chapter = _seed_chapter(store)
    store.create_topic(canonical_id="already:topic", chapter_id=chapter.id, name="Existing",
                       source_type="manual")

    args = argparse.Namespace(school_id="school_1", book_id=book.id, force=False)
    assert cli.cmd_curriculum_extract(args) == 0
    assert store.extraction_runs_for_chapter(chapter.id) == []  # skipped, no new run


def test_extract_force_reproposes_even_with_existing_topics(tmp_path, monkeypatch):
    cfg = _config(tmp_path)
    monkeypatch.setattr(cli.Config, "load", staticmethod(lambda: cfg))
    monkeypatch.setattr("academicos.llm.sarvam.SarvamLLM", _FakeSarvamLLM)
    from academicos.curriculum.store import get_curriculum_store
    store = get_curriculum_store(cfg.data_root)
    book, chapter = _seed_chapter(store)
    store.create_topic(canonical_id="already:topic", chapter_id=chapter.id, name="Existing",
                       source_type="manual")

    args = argparse.Namespace(school_id="school_1", book_id=book.id, force=True)
    assert cli.cmd_curriculum_extract(args) == 0
    assert len(store.extraction_runs_for_chapter(chapter.id)) == 1


# --------------------------------------------------------------------- #
# curriculum-approve
# --------------------------------------------------------------------- #

def _propose_real_run(cfg, store, chapter, book_id):
    from academicos.curriculum import extraction as extraction_mod

    class _Fake:
        available = True
        model = "fake-model"

        def chat_json(self, messages, **kw):
            return REAL_RESPONSE

    return extraction_mod.propose(store, school_id="school_1", chapter=chapter, book_id=book_id,
                                  subject="Science", grade=10, llm=_Fake())


def test_approve_dry_run_prints_and_approves_nothing(tmp_path, monkeypatch, capsys):
    cfg = _config(tmp_path)
    monkeypatch.setattr(cli.Config, "load", staticmethod(lambda: cfg))
    from academicos.curriculum.store import get_curriculum_store
    store = get_curriculum_store(cfg.data_root)
    book, chapter = _seed_chapter(store)
    run = _propose_real_run(cfg, store, chapter, book.id)

    args = argparse.Namespace(run_id=run.id, approved_by="tester", reject="", dry_run=True)
    assert cli.cmd_curriculum_approve(args) == 0

    out = capsys.readouterr().out
    assert "Chemical Equations" in out
    assert "--dry-run" in out
    assert store.topics_for_chapter(chapter.id) == []


def test_approve_for_real_materializes_topics(tmp_path, monkeypatch):
    cfg = _config(tmp_path)
    monkeypatch.setattr(cli.Config, "load", staticmethod(lambda: cfg))
    from academicos.curriculum.store import get_curriculum_store
    store = get_curriculum_store(cfg.data_root)
    book, chapter = _seed_chapter(store)
    run = _propose_real_run(cfg, store, chapter, book.id)

    args = argparse.Namespace(run_id=run.id, approved_by="tester", reject="", dry_run=False)
    assert cli.cmd_curriculum_approve(args) == 0

    topics = store.topics_for_chapter(chapter.id)
    assert len(topics) == 1
    assert topics[0].approved_by == "tester"
    assert store.get_extraction_run(run.id).status == "approved"


def test_approve_with_reject_excludes_that_proposal(tmp_path, monkeypatch):
    cfg = _config(tmp_path)
    monkeypatch.setattr(cli.Config, "load", staticmethod(lambda: cfg))
    from academicos.curriculum.store import get_curriculum_store
    store = get_curriculum_store(cfg.data_root)
    book, chapter = _seed_chapter(store)
    run = _propose_real_run(cfg, store, chapter, book.id)
    topic_proposal = next(p for p in store.proposals_for_run(run.id) if p.entity_type == "topic")

    args = argparse.Namespace(run_id=run.id, approved_by="tester",
                              reject=topic_proposal.id, dry_run=False)
    assert cli.cmd_curriculum_approve(args) == 0
    assert store.topics_for_chapter(chapter.id) == []


def test_approve_unknown_run_id_fails_cleanly(tmp_path, monkeypatch):
    cfg = _config(tmp_path)
    monkeypatch.setattr(cli.Config, "load", staticmethod(lambda: cfg))
    args = argparse.Namespace(run_id="not_a_real_run", approved_by="tester", reject="", dry_run=False)
    assert cli.cmd_curriculum_approve(args) == 1


def test_approve_run_with_no_proposals_fails_cleanly(tmp_path, monkeypatch):
    cfg = _config(tmp_path)
    monkeypatch.setattr(cli.Config, "load", staticmethod(lambda: cfg))
    from academicos.curriculum.store import get_curriculum_store
    store = get_curriculum_store(cfg.data_root)
    run = store.create_extraction_run(school_id="school_1", book_id="b1", chapter_id="c1",
                                      prompt_version="v2")
    store.update_run_status(run.id, "manual_required")

    args = argparse.Namespace(run_id=run.id, approved_by="tester", reject="", dry_run=False)
    assert cli.cmd_curriculum_approve(args) == 1
