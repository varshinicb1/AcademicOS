"""Tests for cross-cutting models (academicos.models.common)."""
from __future__ import annotations

import datetime

import pytest
from pydantic import ValidationError

from academicos.models import (
    BoundingBox,
    Confidence,
    Evidence,
    ExtractionMethod,
    Provenance,
    SourceSpan,
)
from academicos.models.common import utcnow


def test_utcnow_returns_iso8601_string():
    now = utcnow()
    assert isinstance(now, str)
    parsed = datetime.datetime.fromisoformat(now)
    assert parsed.tzinfo is not None
    assert parsed.tzinfo.utcoffset(parsed) == datetime.timedelta(0)


def test_bounding_box_defaults():
    bb = BoundingBox()
    assert bb.x0 == 0.0
    assert bb.y0 == 0.0
    assert bb.x1 == 1.0
    assert bb.y1 == 1.0


def test_bounding_box_accepts_custom_values():
    bb = BoundingBox(x0=0.1, y0=0.2, x1=0.8, y1=0.9)
    assert bb.x0 == 0.1
    assert bb.y0 == 0.2
    assert bb.x1 == 0.8
    assert bb.y1 == 0.9


def test_source_span_requires_document_id():
    with pytest.raises(ValidationError):
        SourceSpan(page=1)


def test_source_span_page_must_be_at_least_one():
    with pytest.raises(ValidationError):
        SourceSpan(document_id="d1", page=0)
    with pytest.raises(ValidationError):
        SourceSpan(document_id="d1", page=-3)


def test_source_span_accepts_optional_fields():
    span = SourceSpan(document_id="d1", page=2, block_idx=4, span_text="hello")
    assert span.document_id == "d1"
    assert span.page == 2
    assert span.block_idx == 4
    assert span.span_text == "hello"
    assert span.bbox is None


def test_confidence_requires_method():
    with pytest.raises(ValidationError):
        Confidence(score=0.8)


def test_confidence_defaults():
    conf = Confidence(method=ExtractionMethod.LLM, score=0.8)
    assert conf.score == 0.8
    assert conf.rationale is None
    assert conf.sub_scores == {}


def test_confidence_requires_score():
    with pytest.raises(ValidationError):
        Confidence(method=ExtractionMethod.LLM)


def test_confidence_score_clamped_to_unit_interval():
    with pytest.raises(ValidationError):
        Confidence(method=ExtractionMethod.ENSEMBLE, score=1.5)
    with pytest.raises(ValidationError):
        Confidence(method=ExtractionMethod.ENSEMBLE, score=-0.1)


def test_confidence_boundary_scores_are_valid():
    assert Confidence(method=ExtractionMethod.LLM, score=0.0).score == 0.0
    assert Confidence(method=ExtractionMethod.LLM, score=1.0).score == 1.0


def _prov(score):
    return Provenance(
        source=SourceSpan(document_id="d1", page=1),
        method=ExtractionMethod.ENSEMBLE,
        confidence=Confidence(method=ExtractionMethod.ENSEMBLE, score=score),
    )


def test_provenance_requires_source_method_confidence():
    span = SourceSpan(document_id="d1", page=1)
    conf = Confidence(method=ExtractionMethod.LLM, score=0.9)
    with pytest.raises(ValidationError):
        Provenance(method=ExtractionMethod.LLM, confidence=conf)
    with pytest.raises(ValidationError):
        Provenance(source=span, confidence=conf)
    with pytest.raises(ValidationError):
        Provenance(source=span, method=ExtractionMethod.LLM)


def test_provenance_defaults():
    prov = _prov(0.9)
    assert prov.human_verified is False
    assert prov.extractor_version == "academicos-0.1.0"
    assert isinstance(prov.extracted_at, str)
    assert prov.extracted_at  # non-empty
    datetime.datetime.fromisoformat(prov.extracted_at)
    assert prov.human_correction is None


def test_evidence_starts_empty_and_add_appends():
    ev = Evidence()
    assert ev.items == []
    ev.add(_prov(0.9))
    ev.add(_prov(0.5))
    assert len(ev.items) == 2


def test_evidence_top_sorts_by_confidence_descending_and_caps():
    ev = Evidence()
    ev.add(_prov(0.9))
    ev.add(_prov(0.5))
    ev.add(_prov(0.7))
    top2 = ev.top(2)
    assert [p.confidence.score for p in top2] == [0.9, 0.7]
    top10 = ev.top(10)
    assert len(top10) == 3
    assert [p.confidence.score for p in top10] == [0.9, 0.7, 0.5]


def test_evidence_top_default_k_is_five():
    ev = Evidence()
    for i in range(6):
        ev.add(_prov(i / 10))
    assert len(ev.top()) == 5
    assert ev.top()[0].confidence.score == 0.5
