"""Tests for document-layer models (academicos.models.document)."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from academicos.models import (
    Block,
    BlockKind,
    DocType,
    Page,
    PageKind,
    ParseResult,
    ParsedDocument,
)


def test_block_defaults():
    b = Block(kind=BlockKind.PARAGRAPH)
    assert b.kind == BlockKind.PARAGRAPH
    assert b.text == ""
    assert b.order == 0
    assert b.metadata == {}
    assert b.children == []
    assert b.bbox is None


def test_block_requires_kind():
    with pytest.raises(ValidationError):
        Block()


def test_block_nested_children():
    parent = Block(
        kind=BlockKind.PARAGRAPH,
        text="parent",
        children=[
            Block(kind=BlockKind.LIST, text="child1"),
            Block(kind=BlockKind.FIGURE, text="child2", order=2),
        ],
    )
    assert len(parent.children) == 2
    assert parent.children[0].text == "child1"
    assert parent.children[0].kind == BlockKind.LIST
    assert parent.children[1].order == 2


def test_page_requires_page_no():
    with pytest.raises(ValidationError):
        Page()


def test_page_page_no_must_be_at_least_one():
    with pytest.raises(ValidationError):
        Page(page_no=0)
    with pytest.raises(ValidationError):
        Page(page_no=-2)


def test_page_defaults():
    p = Page(page_no=1)
    assert p.page_no == 1
    assert p.kind == PageKind.TEXT
    assert p.text == ""
    assert p.blocks == []
    assert p.image_path is None
    assert p.quality == 1.0
    assert p.metadata == {}


def test_page_quality_within_unit_interval():
    assert Page(page_no=1, quality=0.0).quality == 0.0
    assert Page(page_no=1, quality=1.0).quality == 1.0
    with pytest.raises(ValidationError):
        Page(page_no=1, quality=1.01)
    with pytest.raises(ValidationError):
        Page(page_no=1, quality=-0.01)


def test_parse_result_requires_document_id_and_method():
    with pytest.raises(ValidationError):
        ParseResult(method="pdf_native")
    with pytest.raises(ValidationError):
        ParseResult(document_id="d1")


def test_parse_result_defaults():
    pr = ParseResult(document_id="d1", method="pdf_native")
    assert pr.pages == []
    assert pr.markdown is None
    assert pr.structured is None
    assert pr.language is None
    assert pr.confidence == 0.0
    assert pr.warnings == []
    assert pr.provider_meta == {}


def test_parse_result_confidence_within_unit_interval():
    with pytest.raises(ValidationError):
        ParseResult(document_id="d1", method="x", confidence=1.01)
    with pytest.raises(ValidationError):
        ParseResult(document_id="d1", method="x", confidence=-0.1)


def test_parse_result_with_page():
    page = Page(page_no=1, text="hello")
    pr = ParseResult(document_id="d1", method="pdf_native", pages=[page])
    assert pr.pages[0] == page
    assert pr.pages[0].text == "hello"


def test_parsed_document_requires_document_id_and_doc_type():
    with pytest.raises(ValidationError):
        ParsedDocument(doc_type=DocType.QUESTION_PAPER)
    with pytest.raises(ValidationError):
        ParsedDocument(document_id="d1")


def test_parsed_document_defaults():
    pd = ParsedDocument(document_id="d1", doc_type=DocType.UNKNOWN)
    assert pd.title == ""
    assert pd.pages == []
    assert pd.full_text == ""
    assert pd.page_map == {}
    assert pd.provenance == []
    assert pd.quality_score == 0.0
    assert pd.metadata == {}


def test_parsed_document_quality_score_within_unit_interval():
    with pytest.raises(ValidationError):
        ParsedDocument(document_id="d1", doc_type=DocType.SYLLABUS, quality_score=1.5)
    with pytest.raises(ValidationError):
        ParsedDocument(document_id="d1", doc_type=DocType.SYLLABUS, quality_score=-0.5)


def test_parsed_document_full_payload():
    page = Page(page_no=3, text="page text", kind=PageKind.SCAN)
    pd = ParsedDocument(
        document_id="d1",
        doc_type=DocType.SYLLABUS,
        title="Syllabus 2026",
        pages=[page],
        full_text="page text",
        page_map={3: "page text"},
        quality_score=0.8,
        metadata={"lang": "en"},
    )
    assert pd.title == "Syllabus 2026"
    assert pd.pages[0].kind == PageKind.SCAN
    assert pd.page_map == {3: "page text"}
    assert pd.quality_score == 0.8


def test_block_serialization_round_trip():
    b = Block(
        kind=BlockKind.QUESTION,
        text="Q1",
        order=1,
        metadata={"section": "A"},
        children=[Block(kind=BlockKind.QUESTION_PART, text="a)")],
    )
    assert Block.model_validate_json(b.model_dump_json()) == b
