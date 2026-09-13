"""embedding_chapter_tagger.py -- caching, threshold behavior, and the
"no syllabus data" fallback. Uses a small deterministic fake embedding model
(exact string match -> parallel unit vectors, everything else orthogonal) for
fast, hermetic unit tests; test_real_model_tags_plausible_chapters below is
the one test that loads the real sentence-transformers model, to confirm the
wiring actually produces sensible results end-to-end.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.assessment.embedding_chapter_tagger import ChapterTagCache, tag_questions


class _FakeModel:
    """Deterministic stand-in for SentenceTransformer: each distinct input
    string gets its own orthogonal one-hot-ish vector (keyed by first
    occurrence order), so two identical strings are parallel (cosine 1.0)
    and two different strings are orthogonal (cosine 0.0) -- lets tests
    assert exact best-match/threshold behavior without a real model."""

    def __init__(self):
        self._known: dict[str, int] = {}

    def encode(self, texts: list[str], normalize_embeddings: bool = True) -> np.ndarray:
        dim = 32
        out = np.zeros((len(texts), dim))
        for i, t in enumerate(texts):
            if t not in self._known:
                self._known[t] = len(self._known) % dim
            out[i, self._known[t]] = 1.0
        return out


def test_no_syllabus_data_returns_untagged_without_calling_model(tmp_path):
    cache = ChapterTagCache(tmp_path / "tags.sqlite")
    items = [("h1", "some question")]
    # "Underwater Basket Weaving" has no syllabus JSON at all.
    out = tag_questions(cache, subject="Underwater Basket Weaving", grade_label="X",
                        grade_int=10, items=items, model=_FakeModel())
    assert out == {"h1": (None, 0.0)}


def test_exact_match_to_a_chapter_name_tags_with_high_confidence(tmp_path):
    cache = ChapterTagCache(tmp_path / "tags.sqlite")
    model = _FakeModel()
    # Force "Electricity" (a real Science/X chapter name) to be the question
    # text itself, so the fake model gives it a parallel (cosine 1.0) vector.
    items = [("h1", "Electricity")]
    out = tag_questions(cache, subject="Science", grade_label="X", grade_int=10,
                        items=items, model=model)
    assert out["h1"] == ("electricity", pytest.approx(1.0))


def test_orthogonal_text_scores_below_threshold_and_is_declined(tmp_path):
    cache = ChapterTagCache(tmp_path / "tags.sqlite")
    model = _FakeModel()
    # A string that shares no vocabulary with any real chapter name gets an
    # orthogonal (cosine ~0.0) vector against every candidate under the fake
    # model -- below _MIN_SIMILARITY, so it must be declined, not forced.
    items = [("h1", "zzzz_completely_unrelated_nonsense_zzzz")]
    out = tag_questions(cache, subject="Science", grade_label="X", grade_int=10,
                        items=items, model=model)
    assert out["h1"] == (None, 0.0)


def test_real_tag_gets_cached_and_reused_without_recomputing(tmp_path):
    cache = ChapterTagCache(tmp_path / "tags.sqlite")

    class _CountingModel(_FakeModel):
        def __init__(self):
            super().__init__()
            self.encode_calls = 0

        def encode(self, texts, normalize_embeddings=True):
            self.encode_calls += 1
            return super().encode(texts, normalize_embeddings)

    model = _CountingModel()
    items = [("h1", "Electricity")]
    tag_questions(cache, subject="Science", grade_label="X", grade_int=10, items=items, model=model)
    calls_after_first = model.encode_calls
    assert calls_after_first > 0

    # Second call for the same (subject, grade, text_hash): served from
    # cache, model.encode must not be invoked again.
    out2 = tag_questions(cache, subject="Science", grade_label="X", grade_int=10, items=items, model=model)
    assert out2["h1"] == ("electricity", pytest.approx(1.0))
    assert model.encode_calls == calls_after_first


def test_cache_is_scoped_by_subject_and_grade(tmp_path):
    cache = ChapterTagCache(tmp_path / "tags.sqlite")
    # Same text_hash, tagged once under Science and once under Mathematics --
    # a real chapter name in one subject means nothing in the other, and the
    # cache must not leak a Science tag into a Mathematics lookup.
    items = [("h1", "Electricity")]
    out_science = tag_questions(cache, subject="Science", grade_label="X", grade_int=10,
                                items=items, model=_FakeModel())
    out_math = tag_questions(cache, subject="Mathematics", grade_label="X", grade_int=10,
                             items=items, model=_FakeModel())
    assert out_science["h1"][0] == "electricity"
    # "Electricity" shares no vocabulary with any real Mathematics/X unit name,
    # so under a fresh fake model it's orthogonal to all of them.
    assert out_math["h1"][0] is None


def test_every_requested_hash_is_present_in_the_result(tmp_path):
    cache = ChapterTagCache(tmp_path / "tags.sqlite")
    items = [("h1", "Electricity"), ("h2", "something else entirely")]
    out = tag_questions(cache, subject="Science", grade_label="X", grade_int=10,
                        items=items, model=_FakeModel())
    assert set(out.keys()) == {"h1", "h2"}


def test_real_model_tags_plausible_chapters(tmp_path):
    """One real, non-mocked check that the actual sentence-transformers
    model produces a sane result end-to-end -- not just that the plumbing
    calls .encode() correctly."""
    cache = ChapterTagCache(tmp_path / "tags.sqlite")
    items = [
        ("h1", "State Ohm's law and define resistivity of a conductor."),
        ("h2", "Two tangents PQ and PR are drawn to a circle with centre O from an external point P."),
    ]
    out = tag_questions(cache, subject="Science", grade_label="X", grade_int=10, items=items)
    assert out["h1"][0] == "electricity"
