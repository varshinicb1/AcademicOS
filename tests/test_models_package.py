"""Tests for the public API surface of the academicos.models package."""
from __future__ import annotations

import academicos.models as models


def test_all_is_defined():
    assert isinstance(models.__all__, list)
    assert len(models.__all__) >= 30
    assert len(models.__all__) == len(set(models.__all__))


def test_every_name_in_all_is_importable():
    for name in models.__all__:
        assert hasattr(models, name), f"missing {name}"


def test_spot_checked_names_are_correct():
    assert models.Board.CBSE.value == "CBSE"
    assert models.NodeType.CHAPTER.value == "Chapter"
    assert models.EdgeType.EVIDENCED_BY.value == "EVIDENCED_BY"
    assert models.BloomLevel.CREATE.value == "create"
    assert models.ExtractionMethod.ENSEMBLE.value == "ensemble"
    assert models.GraphStatus.SUPERSEDED.value == "superseded"
    assert models.PageKind.IMAGE_ONLY.value == "image_only"
    assert models.BlockKind.MARKING_POINT.value == "marking_point"
    assert models.DocType.UNKNOWN.value == "unknown"


def test_classes_are_basemodel_subclasses():
    for name in [
        "BoundingBox",
        "SourceSpan",
        "Confidence",
        "Provenance",
        "Evidence",
        "Block",
        "Page",
        "ParseResult",
        "ParsedDocument",
        "Node",
        "Edge",
        "GraphSnapshot",
        "AcademicObject",
        "Question",
        "Rubric",
    ]:
        import pydantic

        assert issubclass(getattr(models, name), pydantic.BaseModel), name


def test_class_hierarchy_for_academic_objects():
    assert issubclass(models.Question, models.AcademicObject)
    assert issubclass(models.Topic, models.AcademicObject)
    assert issubclass(models.Circular, models.AcademicObject)
    assert not issubclass(models.Rubric, models.AcademicObject)
