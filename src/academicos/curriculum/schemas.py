"""Wire schemas for curriculum/routes.py -- camelCase over the wire,
matching assessment/schemas.py's Camel convention.
"""
from __future__ import annotations

from typing import Optional

from pydantic import ConfigDict, BaseModel, Field
from pydantic.alias_generators import to_camel


class Camel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class BoardResponse(Camel):
    id: str
    name: str
    code: str


class AcademicYearResponse(Camel):
    id: str
    school_id: str
    label: str
    start_date: str
    end_date: str
    status: str


class GradeResponse(Camel):
    id: str
    academic_year_id: str
    number: int
    section: Optional[str] = None


class SubjectResponse(Camel):
    id: str
    grade_id: str
    name: str
    code: Optional[str] = None


class BookResponse(Camel):
    id: str
    subject_id: str
    board_id: str
    title: str
    publisher: Optional[str] = None
    status: str


class UnitResponse(Camel):
    id: str
    canonical_id: str
    book_id: str
    unit_no: str
    name: str
    marks: Optional[int] = None
    seq: int


class ChapterResponse(Camel):
    id: str
    canonical_id: str
    unit_id: str
    name: str
    seq: int


class TopicResponse(Camel):
    id: str
    canonical_id: str
    chapter_id: str
    name: str
    seq: int
    description: Optional[str] = None
    source_type: str
    source_reference: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    model_used: Optional[str] = None
    generation_version: Optional[str] = None


class SubtopicResponse(Camel):
    id: str
    canonical_id: str
    topic_id: str
    name: str
    seq: int
    description: Optional[str] = None
    source_type: str
    source_reference: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    model_used: Optional[str] = None
    generation_version: Optional[str] = None


class TopicWithSubtopicsResponse(TopicResponse):
    subtopics: list[SubtopicResponse] = Field(default_factory=list)


class ExtractRequest(Camel):
    grounding_text: Optional[str] = None


class ExtractionRunResponse(Camel):
    id: str
    school_id: str
    book_id: str
    chapter_id: str
    source_hash: Optional[str] = None
    model: Optional[str] = None
    prompt_version: str
    created_at: str
    status: str


class ProposalResponse(Camel):
    id: str
    run_id: str
    entity_type: str
    proposed_name: str
    proposed_description: Optional[str] = None
    proposed_parent: Optional[str] = None
    sequence: int
    confidence: float
    status: str
    edited_name: Optional[str] = None
    materialized_id: Optional[str] = None


class ExtractionRunWithProposalsResponse(Camel):
    run: ExtractionRunResponse
    proposals: list[ProposalResponse]


class ApproveRunRequest(Camel):
    edits: dict[str, str] = Field(default_factory=dict)
    rejected_proposal_ids: list[str] = Field(default_factory=list)


class ApproveRunResponse(Camel):
    run_id: str
    topics_created: int
    subtopics_created: int
    topic_ids: list[str]
    subtopic_ids: list[str]


class AddTopicRequest(Camel):
    name: str = Field(min_length=1)
    description: Optional[str] = None
    seq: int = 0


class AddSubtopicRequest(Camel):
    name: str = Field(min_length=1)
    description: Optional[str] = None
    seq: int = 0


class RenameRequest(Camel):
    name: str = Field(min_length=1)


class TagQuestionRequest(Camel):
    question_id: str
    question_text: str = Field(min_length=1)


class TaggedSubtopic(Camel):
    subtopic_id: str
    subtopic_name: str
    method: str
    confidence: float


class TagQuestionResponse(Camel):
    question_id: str
    tagged: list[TaggedSubtopic]


class QuestionsForSubtopicsRequest(Camel):
    subtopic_ids: list[str] = Field(min_length=1)


class QuestionsForSubtopicsResponse(Camel):
    question_ids: list[str]


class SeedCbse10Request(Camel):
    academic_year_label: str = Field(min_length=1)
    start_date: str
    end_date: str


class SeedCbse10Response(Camel):
    board_id: str
    academic_year_id: str
    grade_id: str
    subjects_seeded: int
    units_seeded: int
    chapters_seeded: int
    subjects_skipped: list[str]


# ---------------- academic calendar (§10, §27-29) ----------------

class CreateCalendarRequest(Camel):
    weekly_off_days: list[str] = Field(default_factory=lambda: ["sunday"])
    alternate_saturday_rule: str = "none"


class CalendarResponse(Camel):
    id: str
    academic_year_id: str
    weekly_off_days: list[str]
    alternate_saturday_rule: str


class AddHolidayRequest(Camel):
    date: str
    label: str = Field(min_length=1)
    kind: str = "holiday"


class HolidayResponse(Camel):
    id: str
    calendar_id: str
    date: str
    label: str
    kind: str


class SetPeriodConfigurationRequest(Camel):
    period_minutes: int = Field(gt=0)


class PeriodConfigurationResponse(Camel):
    id: str
    school_id: str
    academic_year_id: str
    period_minutes: int


class WorkingDaysResponse(Camel):
    academic_year_id: str
    total_days: int
    working_days: int
    weekly_off_count: int
    alternate_saturday_off_count: int
    holiday_count: int
    dates: list[str]


class ComputeTeachingTimeRequest(Camel):
    periods_per_week: int = Field(gt=0)


class TeachingTimeEstimateResponse(Camel):
    id: str
    subtopic_id: str
    academic_year_id: str
    estimated_minutes: int
    estimated_periods: Optional[int] = None
    method: str
    approved_by: Optional[str] = None


class ComputeTeachingTimeResponse(Camel):
    academic_year_id: str
    book_id: str
    periods_per_week: int
    period_minutes: int
    calendar_weeks: int
    total_subject_periods: int
    total_instructional_minutes: int
    units_skipped_no_subtopics: list[str]
    estimates_created: int


# ---------------- micro scheduling (§11-14, §38-41) ----------------

class ScheduleBookRequest(Camel):
    periods_per_week: int = Field(gt=0)
    force: bool = False


class ScheduleBookResponse(Camel):
    academic_year_id: str
    book_id: str
    periods_per_week: int
    teaching_days_available: int
    lessons_created: int
    subtopics_scheduled: int
    subtopics_partially_scheduled: list[str]
    subtopics_unscheduled: list[str]
    subtopics_without_estimate: list[str]
    first_scheduled_date: Optional[str] = None
    last_scheduled_date: Optional[str] = None


class ScheduledLessonResponse(Camel):
    id: str
    school_id: str
    academic_year_id: str
    book_id: str
    subtopic_id: str
    date: str
    status: str
    created_at: str
