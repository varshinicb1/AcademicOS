"""Tests for academic-domain models (academicos.models.academic)."""
from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from academicos.models import (
    AcademicObject,
    AnswerScheme,
    AssessmentBlueprint,
    BloomLevel,
    Chapter,
    Circular,
    Competency,
    Concept,
    Confidence,
    Evidence,
    ExtractionMethod,
    LearningOutcome,
    MarkingPoint,
    Node,
    NodeType,
    Prerequisite,
    Provenance,
    Question,
    QuestionPart,
    QuestionPaper,
    Rubric,
    SourceSpan,
    Subject,
    Subtopic,
    SyllabusItem,
    Topic,
)


def _prov(score=0.9):
    return Provenance(
        source=SourceSpan(document_id="d1", page=1),
        method=ExtractionMethod.ENSEMBLE,
        confidence=Confidence(method=ExtractionMethod.ENSEMBLE, score=score),
    )


def test_academic_object_requires_canonical_id_and_title():
    with pytest.raises(ValidationError):
        AcademicObject(title="Some title")
    with pytest.raises(ValidationError):
        AcademicObject(canonical_id="cbse:1")


def test_academic_object_default_board():
    obj = AcademicObject(canonical_id="cbse:1", title="T")
    assert obj.board == "CBSE"
    assert obj.grade is None
    assert obj.subject is None
    assert obj.academic_year is None
    assert obj.evidence == Evidence()


def test_academic_object_dump_includes_defaults():
    obj = AcademicObject(canonical_id="cbse:1", title="T")
    dumped = obj.model_dump()
    assert dumped["board"] == "CBSE"
    assert dumped["evidence"] == Evidence().model_dump()


def test_academic_object_custom_board():
    obj = AcademicObject(canonical_id="cbse:1", title="T", board="NCERT", grade="XII")
    assert obj.board == "NCERT"
    assert obj.grade == "XII"


def test_subject_optional_fields():
    sub = Subject(canonical_id="s1", title="Physics", code="042", medium="English")
    assert sub.code == "042"
    assert sub.medium == "English"


def test_chapter_optional_fields():
    ch = Chapter(canonical_id="c1", title="Ch 1", chapter_no="1", overview="o", page_range=[1, 10])
    assert ch.chapter_no == "1"
    assert ch.page_range == [1, 10]


def test_topic_requires_chapter_id():
    with pytest.raises(ValidationError):
        Topic(canonical_id="t1", title="Topic 1")


def test_topic_defaults():
    topic = Topic(canonical_id="t1", title="Topic 1", chapter_id="c1")
    assert topic.seq == 0
    assert topic.time_estimate_min is None
    assert topic.bloom_level is None


def test_topic_bloom_level_accepts_enum():
    topic = Topic(canonical_id="t1", title="T", chapter_id="c1", bloom_level=BloomLevel.APPLY)
    assert topic.bloom_level == BloomLevel.APPLY


def test_topic_bloom_level_rejects_bad_string():
    with pytest.raises(ValidationError):
        Topic(canonical_id="t1", title="T", chapter_id="c1", bloom_level="applyy")


def test_subtopic_requires_topic_id_and_default_seq():
    st = Subtopic(canonical_id="st1", title="ST", topic_id="t1")
    assert st.topic_id == "t1"
    assert st.seq == 0


def test_learning_outcome_default_lists():
    lo = LearningOutcome(canonical_id="lo1", title="Can explain")
    assert lo.aligned_concepts == []
    assert lo.competency_ids == []
    assert lo.verb is None
    assert lo.bloom_level is None


def test_competency_default_cross_cutting_false():
    comp = Competency(canonical_id="cmp1", title="C")
    assert comp.cross_cutting is False
    assert comp.code is None


def test_concept_default_lists():
    concept = Concept(canonical_id="con1", title="Photosynthesis")
    assert concept.formulas == []
    assert concept.related_terms == []
    assert concept.misconceptions == []
    assert concept.definition is None


def test_prerequisite_requires_for_and_requires():
    with pytest.raises(ValidationError):
        Prerequisite(canonical_id="p1", title="P", requires_id="r")
    with pytest.raises(ValidationError):
        Prerequisite(canonical_id="p1", title="P", for_id="f")


def test_question_defaults():
    q = Question(canonical_id="q1", title="Q1")
    assert q.q_no == ""
    assert q.marks is None
    assert q.parts == []
    assert q.competency_ids == []
    assert q.question_paper_id is None
    assert q.section is None


def test_question_with_parts_and_marks():
    part = QuestionPart(canonical_id="q1a", title="a", question_id="q1", marks=1.0, text="sub")
    q = Question(canonical_id="q1", title="Q1", q_no="1", marks=2.0, parts=[part])
    assert q.q_no == "1"
    assert q.marks == 2.0
    assert q.parts[0] == part
    assert q.parts[0].part == "a"


def test_question_paper_default_lists():
    qp = QuestionPaper(canonical_id="qp1", title="QP 2026")
    assert qp.general_instructions == []
    assert qp.questions == []
    assert qp.exam_year is None
    assert qp.total_marks is None


def test_circular_default_lists():
    circ = Circular(canonical_id="ci1", title="C")
    assert circ.applies_to == []
    assert circ.supersedes_circulars == []
    assert circ.circular_no is None
    assert circ.date is None


def test_marking_point_defaults():
    mp = MarkingPoint(canonical_id="mp1", title="MP", answer_scheme_id="as1")
    assert mp.point_no == 1
    assert mp.marks == 1.0
    assert mp.detail == ""


def test_rubric_is_plain_basemodel_with_defaults():
    rubric = Rubric()
    assert not isinstance(rubric, AcademicObject)
    assert rubric.criteria == []
    assert rubric.total_marks is None
    assert rubric.evidence == Evidence()


def test_rubric_with_criteria():
    rubric = Rubric(criteria=[{"criterion": "accuracy", "marks": 2}], total_marks=5.0)
    assert rubric.criteria == [{"criterion": "accuracy", "marks": 2}]
    assert rubric.total_marks == 5.0


def test_syllabus_item_weightage_optional_float():
    si = SyllabusItem(canonical_id="si1", title="SI")
    assert si.weightage is None
    si2 = SyllabusItem(canonical_id="si2", title="SI", weightage=5.0)
    assert si2.weightage == 5.0


def test_assessment_blueprint_unit_allocations_default_empty():
    ab = AssessmentBlueprint(canonical_id="ab1", title="AB")
    assert ab.unit_allocations == []
    assert ab.question_type_allocations == []
    assert ab.subject_code is None
    assert ab.total_marks is None


def test_question_json_round_trip():
    part = QuestionPart(canonical_id="q1a", title="a", question_id="q1", marks=1.0, text="sub")
    q = Question(
        canonical_id="q1",
        title="Q1",
        q_no="1",
        marks=2.0,
        parts=[part],
        cognitive=BloomLevel.ANALYZE,
    )
    restored = Question.model_validate(json.loads(q.model_dump_json()))
    assert restored == q
    assert restored.cognitive == BloomLevel.ANALYZE


def test_answer_scheme_round_trip_with_marking_points_and_rubric():
    mp = MarkingPoint(canonical_id="mp1", title="MP", answer_scheme_id="as1", point_no=2, marks=1.5, detail="...")
    rubric = Rubric(criteria=[{"c": "x"}], total_marks=5.0)
    scheme = AnswerScheme(
        canonical_id="as1",
        title="AS",
        question_id="q1",
        marking_points=[mp],
        rubric=rubric,
        expected_answer="answer text",
    )
    restored = AnswerScheme.model_validate(json.loads(scheme.model_dump_json()))
    assert restored == scheme
    assert restored.marking_points[0].point_no == 2
    assert restored.rubric.total_marks == 5.0


def test_concept_round_trip():
    concept = Concept(
        canonical_id="con1",
        title="Photosynthesis",
        definition="def",
        formulas=["6CO2 + 6H2O -> C6H12O6 + 6O2"],
        related_terms=["chlorophyll"],
        misconceptions=["plants eat soil"],
        evidence=Evidence(items=[_prov()]),
    )
    restored = Concept.model_validate(json.loads(concept.model_dump_json()))
    assert restored == concept
    assert restored.formulas == concept.formulas
    assert restored.misconceptions == concept.misconceptions


def test_node_with_provenance_round_trip():
    node = Node(id="n1", type=NodeType.CONCEPT, label="Photosynthesis", provenance=_prov())
    restored = Node.model_validate(json.loads(node.model_dump_json()))
    assert restored == node
    assert restored.provenance.confidence.score == 0.9


def test_missing_canonical_id_raises():
    with pytest.raises(ValidationError):
        Question(title="Q1", q_no="1")


def test_missing_title_raises():
    with pytest.raises(ValidationError):
        Question(canonical_id="q1")


def test_model_dump_includes_defaults():
    q = Question(canonical_id="q1", title="Q1")
    dumped = q.model_dump()
    assert dumped["board"] == "CBSE"
    assert dumped["q_no"] == ""
    assert dumped["parts"] == []


def test_evidence_inside_academic_object_round_trip():
    obj = AcademicObject(canonical_id="o1", title="T", evidence=Evidence(items=[_prov(0.7)]))
    restored = AcademicObject.model_validate(json.loads(obj.model_dump_json()))
    assert restored == obj
    assert restored.evidence.items[0].confidence.score == 0.7
