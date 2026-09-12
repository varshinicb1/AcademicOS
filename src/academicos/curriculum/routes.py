"""Curriculum API surface -- reads for the operational hierarchy
(docs/ACADEMIC_DATA_MODEL.md) plus the one real write this round of work
built and tested: triggering the CBSE Class 10 seed for a school.

Scoped deliberately narrow: full admin CRUD for academic years / grades /
subjects / books (§29's admin workflow) is a separate, larger UI+API
design that hasn't been reviewed yet -- this exposes exactly what
seed_cbse10.py + store.py actually do today, real and tested, not a
guessed-at superset.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from ..assessment.auth_routes import get_current_user, require_principal
from ..assessment.users import User
from ..config import Config
from . import calendar as calendar_mod
from . import extraction as extraction_mod
from . import scheduling as scheduling_mod
from .schemas import (
    AcademicYearResponse,
    AddHolidayRequest,
    AddSubtopicRequest,
    AddTopicRequest,
    ApproveRunRequest,
    ApproveRunResponse,
    BookResponse,
    BoardResponse,
    CalendarResponse,
    ChapterResponse,
    ComputeTeachingTimeRequest,
    ComputeTeachingTimeResponse,
    CreateCalendarRequest,
    ExtractionRunResponse,
    ExtractionRunWithProposalsResponse,
    ExtractRequest,
    GradeResponse,
    HolidayResponse,
    PeriodConfigurationResponse,
    ProposalResponse,
    QuestionsForSubtopicsRequest,
    QuestionsForSubtopicsResponse,
    RenameRequest,
    ScheduleBookRequest,
    ScheduleBookResponse,
    ScheduledLessonResponse,
    SeedCbse10Request,
    SeedCbse10Response,
    SetPeriodConfigurationRequest,
    SubjectResponse,
    SubtopicResponse,
    TagQuestionRequest,
    TagQuestionResponse,
    TaggedSubtopic,
    TeachingTimeEstimateResponse,
    TopicResponse,
    TopicWithSubtopicsResponse,
    UnitResponse,
    WorkingDaysResponse,
)
from .seed_cbse10 import seed_cbse_class_10
from .store import CurriculumStore, get_curriculum_store

router = APIRouter(prefix="/api/v1/curriculum")

# Read endpoints below are deliberately unauthenticated, matching
# pillar_routes.py's existing /catalog and /syllabus/{subject}/{grade}
# precedent: this is public official-curriculum content (subject names,
# CBSE chapter names/marks), not student data. Only the write below
# (seed/cbse10, which creates/associates real per-school records) is
# principal-gated.

_store: Optional[CurriculumStore] = None
_cfg: Optional[Config] = None


def init(config: Config) -> None:
    global _store, _cfg
    _cfg = config
    _store = get_curriculum_store(config.data_root)


def _require() -> CurriculumStore:
    if _store is None:
        raise HTTPException(503, "curriculum module not initialized")
    return _store


def _llm():
    """Real SarvamLLM when a key is available, else None --
    extraction.propose() already handles a None/unavailable llm honestly
    (status='manual_required'), so this never needs a fallback of its own.

    Fixed a real bug found 2026-09-12: this used to gate on
    `_cfg.llm_api_key` and pass `_cfg.llm_base_url`/`_cfg.llm_model` --
    those Config fields are Groq-oriented (api.groq.com,
    llama-3.3-70b-versatile, matching api/main.py's critic construction),
    a *different* provider from Sarvam despite the shared "an LLM key
    exists" config surface. A real, working SARVAM_API_KEY was set in this
    environment the whole time; this helper never reached it because it
    returned None before SarvamLLM's own constructor (which prioritizes
    SARVAM_API_KEY, falling back to an explicit api_key/ACOS_LLM_API_KEY --
    see llm/sarvam.py's module docstring) ever ran. Fixed by always
    constructing the real client and letting `.available` decide, instead
    of pre-judging availability from the wrong config field."""
    from ..llm.sarvam import SarvamLLM
    api_key = _cfg.llm_api_key if _cfg else None
    return SarvamLLM(api_key=api_key or None)


def _require_school_owns_chapter(chapter_id: str, current: User) -> None:
    owner = _require().school_id_for_chapter(chapter_id)
    if owner is None:
        raise HTTPException(404, "chapter not found")
    if owner != current.school_id:
        raise HTTPException(403, "this chapter belongs to a different school")


def _require_school_owns_topic(topic_id: str, current: User) -> None:
    owner = _require().school_id_for_topic(topic_id)
    if owner is None:
        raise HTTPException(404, "topic not found")
    if owner != current.school_id:
        raise HTTPException(403, "this topic belongs to a different school")


def _require_school_owns_subtopic(subtopic_id: str, current: User) -> None:
    owner = _require().school_id_for_subtopic(subtopic_id)
    if owner is None:
        raise HTTPException(404, "subtopic not found")
    if owner != current.school_id:
        raise HTTPException(403, "this subtopic belongs to a different school")


def _require_school_owns_academic_year(academic_year_id: str, current: User):
    year = _require().get_academic_year(academic_year_id)
    if year is None:
        raise HTTPException(404, "academic year not found")
    if year.school_id != current.school_id:
        raise HTTPException(403, "this academic year belongs to a different school")
    return year


def _require_school_owns_book(book_id: str, current: User) -> None:
    owner = _require().school_id_for_book(book_id)
    if owner is None:
        raise HTTPException(404, "book not found")
    if owner != current.school_id:
        raise HTTPException(403, "this book belongs to a different school")


def _topic_response(t) -> TopicResponse:
    return TopicResponse(id=t.id, canonical_id=t.canonical_id, chapter_id=t.chapter_id,
                         name=t.name, seq=t.seq, description=t.description,
                         source_type=t.source_type, source_reference=t.source_reference,
                         approved_by=t.approved_by, approved_at=t.approved_at,
                         model_used=t.model_used, generation_version=t.generation_version)


def _subtopic_response(s) -> SubtopicResponse:
    return SubtopicResponse(id=s.id, canonical_id=s.canonical_id, topic_id=s.topic_id,
                            name=s.name, seq=s.seq, description=s.description,
                            source_type=s.source_type, source_reference=s.source_reference,
                            approved_by=s.approved_by, approved_at=s.approved_at,
                            model_used=s.model_used, generation_version=s.generation_version)


@router.get("/boards", response_model=list[BoardResponse])
def list_boards() -> list[BoardResponse]:
    return [BoardResponse(id=b.id, name=b.name, code=b.code) for b in _require().list_boards()]


@router.get("/academic-years", response_model=list[AcademicYearResponse])
def list_academic_years(school_id: str) -> list[AcademicYearResponse]:
    return [
        AcademicYearResponse(id=y.id, school_id=y.school_id, label=y.label,
                             start_date=y.start_date, end_date=y.end_date, status=y.status)
        for y in _require().academic_years_for_school(school_id)
    ]


@router.get("/academic-years/{academic_year_id}/grades", response_model=list[GradeResponse])
def list_grades(academic_year_id: str) -> list[GradeResponse]:
    return [
        GradeResponse(id=g.id, academic_year_id=g.academic_year_id, number=g.number, section=g.section)
        for g in _require().grades_for_year(academic_year_id)
    ]


@router.get("/grades/{grade_id}/subjects", response_model=list[SubjectResponse])
def list_subjects(grade_id: str) -> list[SubjectResponse]:
    return [
        SubjectResponse(id=s.id, grade_id=s.grade_id, name=s.name, code=s.code)
        for s in _require().subjects_for_grade(grade_id)
    ]


@router.get("/subjects/{subject_id}/books", response_model=list[BookResponse])
def list_books(subject_id: str) -> list[BookResponse]:
    return [
        BookResponse(id=b.id, subject_id=b.subject_id, board_id=b.board_id, title=b.title,
                     publisher=b.publisher, status=b.status)
        for b in _require().books_for_subject(subject_id)
    ]


@router.get("/books/{book_id}/units", response_model=list[UnitResponse])
def list_units(book_id: str) -> list[UnitResponse]:
    return [
        UnitResponse(id=u.id, canonical_id=u.canonical_id, book_id=u.book_id,
                     unit_no=u.unit_no, name=u.name, marks=u.marks, seq=u.seq)
        for u in _require().units_for_book(book_id)
    ]


@router.get("/books/{book_id}/chapters", response_model=list[ChapterResponse])
def list_chapters(book_id: str) -> list[ChapterResponse]:
    """Unit-then-chapter delivery order across the whole book -- what
    §29's admin curriculum-review step actually wants to show."""
    return [
        ChapterResponse(id=c.id, canonical_id=c.canonical_id, unit_id=c.unit_id,
                        name=c.name, seq=c.seq)
        for c in _require().chapters_for_book(book_id)
    ]


@router.post("/seed/cbse10", response_model=SeedCbse10Response)
def seed_cbse10(req: SeedCbse10Request,
                principal: User = Depends(require_principal)) -> SeedCbse10Response:
    """Seeds the real, official CBSE Class X curriculum
    (syllabus/cbse_syllabus.py) as this school's first academic year ->
    grade 10 -> subjects -> books -> units -> chapters. Idempotent --
    re-running for the same school/year reuses what's already there
    rather than duplicating it (see seed_cbse10.py's module docstring).

    Principal-gated, and school_id is the caller's own -- never taken from
    the request body -- matching the school-scoping pattern already used
    by routes.approve_assessment and this session's pillar_routes.py
    authorization fixes: this is an administrative curriculum-configuration
    action (§29), not something any caller should be able to trigger for
    an arbitrary school_id string.
    """
    result = seed_cbse_class_10(
        _require(), school_id=principal.school_id, academic_year_label=req.academic_year_label,
        start_date=req.start_date, end_date=req.end_date)
    return SeedCbse10Response(
        board_id=result.board_id, academic_year_id=result.academic_year_id,
        grade_id=result.grade_id, subjects_seeded=result.subjects_seeded,
        units_seeded=result.units_seeded, chapters_seeded=result.chapters_seeded,
        subjects_skipped=result.subjects_skipped,
    )


# ---------------- Topic/Subtopic decomposition: extract -> review -> approve ----------------
# See docs/ACADEMIC_DATA_MODEL.md section 6 and extraction.py's module
# docstring: AI DRAFT -> ADMIN REVIEW -> DATABASE. Every write below is
# principal-gated and school-scoped (§ "different schools cannot read/write
# each other's draft curriculum") -- draft proposals are exactly the kind
# of admin-in-progress data this session's pillar_routes.py authorization
# fixes exist to protect the same class of gap for.


@router.get("/chapters/{chapter_id}/topics", response_model=list[TopicWithSubtopicsResponse])
def list_topics(chapter_id: str) -> list[TopicWithSubtopicsResponse]:
    """The real, approved curriculum for a chapter -- what the question-
    paper subtopic picker (§ end-to-end acceptance criteria) reads."""
    store = _require()
    out = []
    for t in store.topics_for_chapter(chapter_id):
        out.append(TopicWithSubtopicsResponse(
            id=t.id, canonical_id=t.canonical_id, chapter_id=t.chapter_id, name=t.name,
            seq=t.seq, description=t.description, source_type=t.source_type,
            source_reference=t.source_reference, approved_by=t.approved_by,
            approved_at=t.approved_at, model_used=t.model_used,
            generation_version=t.generation_version,
            subtopics=[_subtopic_response(s) for s in store.subtopics_for_topic(t.id)],
        ))
    return out


@router.post("/chapters/{chapter_id}/extract", response_model=ExtractionRunResponse)
def extract_chapter(chapter_id: str, req: ExtractRequest,
                    principal: User = Depends(require_principal)) -> ExtractionRunResponse:
    """Proposes a Topic/Subtopic breakdown for a chapter -- a draft only,
    see extraction.py. Uses the real configured Sarvam LLM when a key
    exists; honestly reports status="manual_required" (zero proposals)
    otherwise rather than fabricating a breakdown offline."""
    store = _require()
    _require_school_owns_chapter(chapter_id, principal)
    chapter = store.get_chapter(chapter_id)
    unit = store.get_unit(chapter.unit_id)
    book = store.get_book(unit.book_id)
    subject = store.get_subject(book.subject_id)
    grade = store.get_grade(subject.grade_id)

    run = extraction_mod.propose(
        store, school_id=principal.school_id, chapter=chapter, book_id=book.id,
        subject=subject.name, grade=grade.number, llm=_llm(),
        grounding_text=req.grounding_text)
    return ExtractionRunResponse(
        id=run.id, school_id=run.school_id, book_id=run.book_id, chapter_id=run.chapter_id,
        source_hash=run.source_hash, model=run.model, prompt_version=run.prompt_version,
        created_at=run.created_at, status=run.status)


@router.get("/extraction-runs/{run_id}", response_model=ExtractionRunWithProposalsResponse)
def get_extraction_run(run_id: str,
                       current: User = Depends(get_current_user)) -> ExtractionRunWithProposalsResponse:
    store = _require()
    run = store.get_extraction_run(run_id)
    if run is None:
        raise HTTPException(404, "extraction run not found")
    if store.school_id_for_chapter(run.chapter_id) != current.school_id:
        raise HTTPException(403, "this extraction run belongs to a different school")
    proposals = store.proposals_for_run(run_id)
    return ExtractionRunWithProposalsResponse(
        run=ExtractionRunResponse(id=run.id, school_id=run.school_id, book_id=run.book_id,
                                  chapter_id=run.chapter_id, source_hash=run.source_hash,
                                  model=run.model, prompt_version=run.prompt_version,
                                  created_at=run.created_at, status=run.status),
        proposals=[ProposalResponse(id=p.id, run_id=p.run_id, entity_type=p.entity_type,
                                    proposed_name=p.proposed_name,
                                    proposed_description=p.proposed_description,
                                    proposed_parent=p.proposed_parent, sequence=p.sequence,
                                    confidence=p.confidence, status=p.status,
                                    edited_name=p.edited_name, materialized_id=p.materialized_id)
                  for p in proposals],
    )


@router.post("/extraction-runs/{run_id}/approve", response_model=ApproveRunResponse)
def approve_extraction_run(run_id: str, req: ApproveRunRequest,
                           principal: User = Depends(require_principal)) -> ApproveRunResponse:
    """The one endpoint that turns a draft into real curriculum. Never
    automatic -- always an explicit admin action."""
    store = _require()
    run = store.get_extraction_run(run_id)
    if run is None:
        raise HTTPException(404, "extraction run not found")
    if store.school_id_for_chapter(run.chapter_id) != principal.school_id:
        raise HTTPException(403, "this extraction run belongs to a different school")

    result = extraction_mod.approve_run(
        store, run_id, approved_by=principal.id, edits=req.edits,
        rejected_proposal_ids=set(req.rejected_proposal_ids))
    return ApproveRunResponse(run_id=result.run_id, topics_created=result.topics_created,
                              subtopics_created=result.subtopics_created,
                              topic_ids=result.topic_ids, subtopic_ids=result.subtopic_ids)


@router.post("/chapters/{chapter_id}/topics", response_model=TopicResponse)
def add_manual_topic(chapter_id: str, req: AddTopicRequest,
                     principal: User = Depends(require_principal)) -> TopicResponse:
    """The review UI's "[ + Add Topic ]" -- a topic an admin enters
    directly, no LLM/run involved (source_type="manual")."""
    from ..syllabus.cbse_syllabus import _slug
    store = _require()
    _require_school_owns_chapter(chapter_id, principal)
    chapter = store.get_chapter(chapter_id)
    from datetime import datetime, timezone
    topic = store.create_topic(
        canonical_id=f"{chapter.canonical_id}:topic:{_slug(req.name)}", chapter_id=chapter_id,
        name=req.name, seq=req.seq, description=req.description, source_type="manual",
        approved_by=principal.id, approved_at=datetime.now(timezone.utc).isoformat())
    return _topic_response(topic)


@router.post("/topics/{topic_id}/subtopics", response_model=SubtopicResponse)
def add_manual_subtopic(topic_id: str, req: AddSubtopicRequest,
                        principal: User = Depends(require_principal)) -> SubtopicResponse:
    from ..syllabus.cbse_syllabus import _slug
    store = _require()
    _require_school_owns_topic(topic_id, principal)
    topic = store.get_topic(topic_id)
    from datetime import datetime, timezone
    subtopic = store.create_subtopic(
        canonical_id=f"{topic.canonical_id}:subtopic:{_slug(req.name)}", topic_id=topic_id,
        name=req.name, seq=req.seq, description=req.description, source_type="manual",
        approved_by=principal.id, approved_at=datetime.now(timezone.utc).isoformat())
    return _subtopic_response(subtopic)


@router.patch("/topics/{topic_id}", response_model=TopicResponse)
def rename_topic(topic_id: str, req: RenameRequest,
                 principal: User = Depends(require_principal)) -> TopicResponse:
    """canonical_id (what question tags reference) is untouched by a
    rename -- see store.rename_topic's docstring."""
    store = _require()
    _require_school_owns_topic(topic_id, principal)
    store.rename_topic(topic_id, req.name)
    return _topic_response(store.get_topic(topic_id))


@router.patch("/subtopics/{subtopic_id}", response_model=SubtopicResponse)
def rename_subtopic(subtopic_id: str, req: RenameRequest,
                    principal: User = Depends(require_principal)) -> SubtopicResponse:
    store = _require()
    _require_school_owns_subtopic(subtopic_id, principal)
    store.rename_subtopic(subtopic_id, req.name)
    return _subtopic_response(store.get_subtopic(subtopic_id))


@router.delete("/subtopics/{subtopic_id}")
def delete_subtopic(subtopic_id: str, force: bool = False,
                    principal: User = Depends(require_principal)) -> dict:
    store = _require()
    _require_school_owns_subtopic(subtopic_id, principal)
    try:
        store.delete_subtopic(subtopic_id, force=force)
    except CurriculumStore.SubtopicHasLinkedQuestions as e:
        raise HTTPException(409, str(e))
    return {"ok": True}


# ---------------- question <-> subtopic tagging (qmap.py bridge) ----------------
# §4 of the ordered milestone: only wired here, after real canonical
# Subtopic ids exist above -- see qmap.py's map_subtopics() for the
# resolution logic itself (same propose+verify shape as the existing
# question->concept mapping).


@router.post("/chapters/{chapter_id}/questions/tag", response_model=TagQuestionResponse)
def tag_question(chapter_id: str, req: TagQuestionRequest,
                 current: User = Depends(get_current_user)) -> TagQuestionResponse:
    """Resolves one question's text against this chapter's real, approved
    subtopics and persists the match -- the bridge that makes "generate a
    paper from these subtopics" possible. Scoped to one chapter rather than
    the whole school's subtopics: a question already carries a chapter tag
    from the existing assessment/chapters.py keyword-tagger, and searching
    only that chapter's subtopics is both faster and more correct than a
    school-wide lexical search.

    Requires a real logged-in caller from the chapter's own school (fixed:
    flagged by automated security review as a write endpoint -- persists
    QuestionSubtopicLink rows -- that had no auth at all, unlike every
    other write in this file; an unauthenticated caller could otherwise
    tag arbitrary question ids against any school's curriculum)."""
    from ..qmap import map_subtopics
    store = _require()
    _require_school_owns_chapter(chapter_id, current)
    matches = map_subtopics(store, chapter_id=chapter_id, question_text=req.question_text)
    tagged = []
    for m in matches:
        store.link_question_to_subtopic(question_id=req.question_id, subtopic_id=m.subtopic_id,
                                        method=m.method, confidence=m.confidence)
        tagged.append(TaggedSubtopic(subtopic_id=m.subtopic_id, subtopic_name=m.subtopic_name,
                                     method=m.method, confidence=m.confidence))
    return TagQuestionResponse(question_id=req.question_id, tagged=tagged)


@router.post("/questions/by-subtopics", response_model=QuestionsForSubtopicsResponse)
def questions_by_subtopics(req: QuestionsForSubtopicsRequest) -> QuestionsForSubtopicsResponse:
    """"Generate paper using selected subtopics": every question tagged
    (via tag_question above) to any of the given subtopics."""
    ids = _require().question_ids_for_subtopics(req.subtopic_ids)
    return QuestionsForSubtopicsResponse(question_ids=ids)


# ---------------- academic calendar: Academic Year -> Working Days ->
# Holidays -> Period Duration -> Teaching-Time Estimate (§10, §27-29) ----------------
# Every write here is principal-gated and school-scoped, same posture as
# the Topic/Subtopic draft-curriculum writes above: a school's calendar and
# per-subtopic pacing plan is administrative configuration, not public
# reference content (unlike /boards or /books/{id}/chapters, which mirror
# official, school-independent CBSE data).


@router.post("/academic-years/{academic_year_id}/calendar", response_model=CalendarResponse)
def create_calendar(academic_year_id: str, req: CreateCalendarRequest,
                    principal: User = Depends(require_principal)) -> CalendarResponse:
    store = _require()
    _require_school_owns_academic_year(academic_year_id, principal)
    if store.get_calendar_for_year(academic_year_id) is not None:
        raise HTTPException(409, "this academic year already has a calendar -- add holidays to it instead")
    cal = store.create_calendar(academic_year_id=academic_year_id,
                                weekly_off_days=req.weekly_off_days,
                                alternate_saturday_rule=req.alternate_saturday_rule)
    return CalendarResponse(id=cal.id, academic_year_id=cal.academic_year_id,
                            weekly_off_days=cal.weekly_off_days,
                            alternate_saturday_rule=cal.alternate_saturday_rule)


@router.get("/academic-years/{academic_year_id}/calendar", response_model=CalendarResponse)
def get_calendar(academic_year_id: str,
                 current: User = Depends(get_current_user)) -> CalendarResponse:
    store = _require()
    _require_school_owns_academic_year(academic_year_id, current)
    cal = store.get_calendar_for_year(academic_year_id)
    if cal is None:
        raise HTTPException(404, "no calendar configured for this academic year yet")
    return CalendarResponse(id=cal.id, academic_year_id=cal.academic_year_id,
                            weekly_off_days=cal.weekly_off_days,
                            alternate_saturday_rule=cal.alternate_saturday_rule)


@router.post("/academic-years/{academic_year_id}/holidays", response_model=HolidayResponse)
def add_holiday(academic_year_id: str, req: AddHolidayRequest,
                principal: User = Depends(require_principal)) -> HolidayResponse:
    store = _require()
    _require_school_owns_academic_year(academic_year_id, principal)
    cal = store.get_calendar_for_year(academic_year_id)
    if cal is None:
        raise HTTPException(404, "create a calendar for this academic year first")
    h = store.add_holiday(calendar_id=cal.id, date=req.date, label=req.label, kind=req.kind)
    return HolidayResponse(id=h.id, calendar_id=h.calendar_id, date=h.date, label=h.label, kind=h.kind)


@router.get("/academic-years/{academic_year_id}/holidays", response_model=list[HolidayResponse])
def list_holidays(academic_year_id: str,
                  current: User = Depends(get_current_user)) -> list[HolidayResponse]:
    store = _require()
    _require_school_owns_academic_year(academic_year_id, current)
    cal = store.get_calendar_for_year(academic_year_id)
    if cal is None:
        return []
    return [HolidayResponse(id=h.id, calendar_id=h.calendar_id, date=h.date, label=h.label, kind=h.kind)
            for h in store.holidays_for_calendar(cal.id)]


@router.post("/academic-years/{academic_year_id}/period-configuration",
             response_model=PeriodConfigurationResponse)
def set_period_configuration(academic_year_id: str, req: SetPeriodConfigurationRequest,
                             principal: User = Depends(require_principal)) -> PeriodConfigurationResponse:
    store = _require()
    _require_school_owns_academic_year(academic_year_id, principal)
    if store.period_configuration_for_year(academic_year_id) is not None:
        raise HTTPException(409, "period configuration already set for this academic year")
    cfg = store.create_period_configuration(school_id=principal.school_id,
                                            academic_year_id=academic_year_id,
                                            period_minutes=req.period_minutes)
    return PeriodConfigurationResponse(id=cfg.id, school_id=cfg.school_id,
                                       academic_year_id=cfg.academic_year_id,
                                       period_minutes=cfg.period_minutes)


@router.get("/academic-years/{academic_year_id}/working-days", response_model=WorkingDaysResponse)
def get_working_days(academic_year_id: str,
                     current: User = Depends(get_current_user)) -> WorkingDaysResponse:
    """The actual §10 deliverable: a real, computed count of teaching days
    for this academic year, given its real calendar + holidays."""
    store = _require()
    _require_school_owns_academic_year(academic_year_id, current)
    try:
        result = calendar_mod.working_days_for_year(store, academic_year_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return WorkingDaysResponse(
        academic_year_id=academic_year_id, total_days=result.total_days,
        working_days=result.working_days, weekly_off_count=result.weekly_off_count,
        alternate_saturday_off_count=result.alternate_saturday_off_count,
        holiday_count=result.holiday_count, dates=list(result.dates))


@router.post("/books/{book_id}/teaching-time-estimates", response_model=ComputeTeachingTimeResponse)
def compute_teaching_time_estimates(book_id: str, academic_year_id: str,
                                    req: ComputeTeachingTimeRequest,
                                    principal: User = Depends(require_principal),
                                    ) -> ComputeTeachingTimeResponse:
    """Distributes this subject's real, calendar-grounded instructional
    time across its real, approved Subtopics -- see calendar.py's
    compute_teaching_time_estimates() docstring for the full method.
    Idempotent per subtopic: re-running never duplicates or silently
    overwrites an existing estimate (§29 -- an admin who has since
    hand-adjusted an estimate must not have it clobbered by a re-run)."""
    store = _require()
    _require_school_owns_book(book_id, principal)
    _require_school_owns_academic_year(academic_year_id, principal)
    try:
        result = calendar_mod.compute_teaching_time_estimates(
            store, academic_year_id=academic_year_id, book_id=book_id,
            periods_per_week=req.periods_per_week, approved_by=principal.id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return ComputeTeachingTimeResponse(
        academic_year_id=result.academic_year_id, book_id=result.book_id,
        periods_per_week=result.periods_per_week, period_minutes=result.period_minutes,
        calendar_weeks=result.calendar_weeks, total_subject_periods=result.total_subject_periods,
        total_instructional_minutes=result.total_instructional_minutes,
        units_skipped_no_subtopics=list(result.units_skipped_no_subtopics),
        estimates_created=len(result.estimates))


@router.get("/subtopics/{subtopic_id}/teaching-time-estimate",
           response_model=Optional[TeachingTimeEstimateResponse])
def get_teaching_time_estimate(subtopic_id: str, academic_year_id: str,
                               current: User = Depends(get_current_user),
                               ) -> Optional[TeachingTimeEstimateResponse]:
    store = _require()
    _require_school_owns_subtopic(subtopic_id, current)
    est = store.teaching_time_estimate_for_subtopic(subtopic_id, academic_year_id)
    if est is None:
        return None
    return TeachingTimeEstimateResponse(
        id=est.id, subtopic_id=est.subtopic_id, academic_year_id=est.academic_year_id,
        estimated_minutes=est.estimated_minutes, estimated_periods=est.estimated_periods,
        method=est.method, approved_by=est.approved_by)


# ---------------- micro scheduling: curriculum x teaching-time-estimate x
# calendar -> a real, dated ScheduledLesson[] (§11-14, §38-41) ----------------


def _lesson_response(lesson) -> ScheduledLessonResponse:
    return ScheduledLessonResponse(id=lesson.id, school_id=lesson.school_id,
                                   academic_year_id=lesson.academic_year_id, book_id=lesson.book_id,
                                   subtopic_id=lesson.subtopic_id, date=lesson.date,
                                   status=lesson.status, created_at=lesson.created_at)


@router.post("/books/{book_id}/schedule", response_model=ScheduleBookResponse)
def schedule_book(book_id: str, academic_year_id: str, req: ScheduleBookRequest,
                  principal: User = Depends(require_principal)) -> ScheduleBookResponse:
    """Generates the real, dated schedule for this book -- see
    scheduling.py's module docstring for the full method and its honestly-
    documented weekday-assignment simplification. Requires
    compute_teaching_time_estimates() to have already run for this
    (book, academic_year); a Subtopic without a real estimate is skipped
    and reported, never given a guessed period count."""
    store = _require()
    _require_school_owns_book(book_id, principal)
    _require_school_owns_academic_year(academic_year_id, principal)
    try:
        result = scheduling_mod.schedule_book(
            store, school_id=principal.school_id, academic_year_id=academic_year_id,
            book_id=book_id, periods_per_week=req.periods_per_week, force=req.force)
    except ValueError as e:
        raise HTTPException(409, str(e))
    return ScheduleBookResponse(
        academic_year_id=result.academic_year_id, book_id=result.book_id,
        periods_per_week=result.periods_per_week,
        teaching_days_available=result.teaching_days_available, lessons_created=result.lessons_created,
        subtopics_scheduled=result.subtopics_scheduled,
        subtopics_partially_scheduled=list(result.subtopics_partially_scheduled),
        subtopics_unscheduled=list(result.subtopics_unscheduled),
        subtopics_without_estimate=list(result.subtopics_without_estimate),
        first_scheduled_date=result.first_scheduled_date, last_scheduled_date=result.last_scheduled_date)


@router.get("/books/{book_id}/schedule", response_model=list[ScheduledLessonResponse])
def get_book_schedule(book_id: str, academic_year_id: str,
                      current: User = Depends(get_current_user)) -> list[ScheduledLessonResponse]:
    store = _require()
    _require_school_owns_book(book_id, current)
    return [_lesson_response(l) for l in store.scheduled_lessons_for_book(academic_year_id, book_id)]


@router.get("/schedule", response_model=list[ScheduledLessonResponse])
def get_schedule_for_range(start_date: str, end_date: str,
                           current: User = Depends(get_current_user)) -> list[ScheduledLessonResponse]:
    """The real access pattern a yearly/monthly/weekly/daily view or a
    teacher's "what do I teach today" screen (both later milestones) will
    call -- every lesson across every subject for the caller's own school
    in a date range. School-scoped by the caller's own token, not a
    request parameter -- same posture as every other write/read in this
    module that touches per-school administrative data."""
    store = _require()
    return [_lesson_response(l)
            for l in store.scheduled_lessons_for_date_range(current.school_id, start_date, end_date)]
