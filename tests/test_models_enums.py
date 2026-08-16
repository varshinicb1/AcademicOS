"""Tests for the canonical AcademicOS enums (academicos.models.enums)."""
from __future__ import annotations

import enum

import pytest
from pydantic import BaseModel, ValidationError

from academicos.models import (
    BlockKind,
    BloomLevel,
    Board,
    DocType,
    EdgeType,
    ExtractionMethod,
    GraphStatus,
    NodeType,
    PageKind,
)

ALL_ENUMS = [
    Board,
    DocType,
    PageKind,
    BlockKind,
    NodeType,
    EdgeType,
    BloomLevel,
    ExtractionMethod,
    GraphStatus,
]


@pytest.mark.parametrize("enum_cls", ALL_ENUMS)
def test_enum_is_str_enum(enum_cls):
    assert issubclass(enum_cls, str)
    assert issubclass(enum_cls, enum.Enum)


@pytest.mark.parametrize(
    ("enum_cls", "member", "value"),
    [
        (Board, Board.CBSE, "CBSE"),
        (Board, Board.NCERT, "NCERT"),
        (Board, Board.OTHER, "OTHER"),
        (DocType, DocType.UNKNOWN, "unknown"),
        (DocType, DocType.QUESTION_PAPER, "question_paper"),
        (DocType, DocType.MARKING_SCHEME, "marking_scheme"),
        (PageKind, PageKind.TEXT, "text"),
        (PageKind, PageKind.IMAGE_ONLY, "image_only"),
        (BlockKind, BlockKind.MARKING_POINT, "marking_point"),
        (BlockKind, BlockKind.RUBRIC, "rubric"),
        (NodeType, NodeType.CHAPTER, "Chapter"),
        (NodeType, NodeType.TOPIC, "Topic"),
        (NodeType, NodeType.QUESTION, "Question"),
        (EdgeType, EdgeType.EVIDENCED_BY, "EVIDENCED_BY"),
        (EdgeType, EdgeType.CONTAINS, "CONTAINS"),
        (BloomLevel, BloomLevel.CREATE, "create"),
        (BloomLevel, BloomLevel.REMEMBER, "remember"),
        (ExtractionMethod, ExtractionMethod.ENSEMBLE, "ensemble"),
        (ExtractionMethod, ExtractionMethod.LLM, "llm"),
        (GraphStatus, GraphStatus.DRAFT, "draft"),
        (GraphStatus, GraphStatus.SUPERSEDED, "superseded"),
    ],
)
def test_enum_values(enum_cls, member, value):
    assert member.value == value
    assert member == value


@pytest.mark.parametrize(
    ("enum_cls", "value"),
    [
        (Board, Board.CBSE),
        (DocType, DocType.UNKNOWN),
        (PageKind, PageKind.IMAGE_ONLY),
        (BlockKind, BlockKind.MARKING_POINT),
        (NodeType, NodeType.CHAPTER),
        (EdgeType, EdgeType.EVIDENCED_BY),
        (BloomLevel, BloomLevel.CREATE),
        (ExtractionMethod, ExtractionMethod.ENSEMBLE),
        (GraphStatus, GraphStatus.SUPERSEDED),
    ],
)
def test_enum_is_str_and_coerces_from_string(enum_cls, value):
    assert enum_cls(value.value) is value


class _Holder(BaseModel):
    kind: BlockKind
    status: GraphStatus


def test_enums_serialize_to_their_str_value_in_json():
    h = _Holder(kind=BlockKind.MARKING_POINT, status=GraphStatus.SUPERSEDED)
    dumped = h.model_dump_json()
    assert '"kind":"marking_point"' in dumped
    assert '"status":"superseded"' in dumped
    assert "marking_point" not in dumped.replace('"kind":"marking_point"', "")


def test_enum_round_trip_through_json():
    h = _Holder(kind=BlockKind.MARKING_POINT, status=GraphStatus.SUPERSEDED)
    raw = h.model_dump_json()
    assert _Holder.model_validate_json(raw) == h


class _KindHolder(BaseModel):
    kind: BlockKind


@pytest.mark.parametrize(
    ("enum_cls", "bad_value"),
    [
        (Board, "CBSEX"),
        (DocType, "unknowns"),
        (PageKind, "IMAGE_ONLY"),
        (BlockKind, "MARKING_POINT"),
        (NodeType, "chapter"),
        (EdgeType, "evidenced_by"),
        (BloomLevel, "CREATE"),
        (ExtractionMethod, "ensemble "),
        (GraphStatus, "drafts"),
    ],
)
def test_invalid_enum_value_raises_validation_error(enum_cls, bad_value):
    class Holder(BaseModel):
        value: enum_cls  # type: ignore[valid-type]

    with pytest.raises(ValidationError):
        Holder(value=bad_value)
