"""Filling a teacher's paper template from the bank: availability, then selection.

One engine does both, on purpose. The availability check the builder shows
BEFORE generating and the paper generation itself walk the same candidate
list, in the same section order, with the same claiming rule -- so a section
reported as "4 of 4 available" cannot come back short, and a gap the teacher
was shown is exactly the gap the paper has.

Eligibility, in the order it narrows (each step is reported, so a shortfall
names the constraint that caused it rather than a bare zero):

  bank (class + subject) -> verified answer key (PRD rule Q1: no answer key,
  no question) -> marks match the section -> allowed question types ->
  inside the template's scope (chapters, subtopics, topics)

A section with a shortfall is filled from outside the scope only when the
caller asks (`fill_from_outside_scope`), and every borrowed question is
named in the notes. Unlike `selection.optimize`, nothing is borrowed silently:
the selector's own fallback exists for the one-click path, where there is no
builder to show the gap first.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from .schemas import Camel, DifficultyDistribution, PaperTemplateDraft, QuestionSchema, \
    TemplateScope, TemplateSection

# Where the board-level topic taxonomy will live (being built in another
# stream). Its absence is reported, never treated as "every id is invalid".
TAXONOMY_DIR = Path(__file__).resolve().parents[3] / "academicos-data" / "syllabus" / "taxonomy"


class SectionAvailability(Camel):
    section_id: str
    title: str
    marks_each: int
    needed: int
    available: int
    shortfall: int
    # Eligible (keyed, right marks and type) but outside the chosen scope.
    outside_scope_available: int = 0
    # In scope with the right marks and type, but no verified answer key.
    without_key: int = 0
    reason: str = ""


class AvailabilityReport(Camel):
    template_id: str
    grade: int
    subject: str
    bank_questions: int
    keyed_questions: int
    complete: bool
    sections: list[SectionAvailability]
    scope_notes: list[str] = []


def has_verified_key(q: QuestionSchema) -> bool:
    """Rule Q1, the same content check the question-bank API applies
    (`QuestionBank.has_answer_key`): a scheme with actual text in it, never
    just a provenance label. Reused rather than copied so the two surfaces
    can never disagree about which questions are answerable."""
    from .qbank_routes import QuestionBank
    return QuestionBank.has_answer_key(q.model_dump(by_alias=True, mode="json"))


@dataclass
class ScopeFilter:
    """`in_scope(q)` plus the notes explaining what the filter could not do."""
    in_scope: Callable[[QuestionSchema], bool]
    notes: list[str] = field(default_factory=list)


def build_scope_filter(scope: TemplateScope, candidates: list[QuestionSchema],
                       subtopic_question_ids: Optional[Callable[[list[str]], list[str]]] = None,
                       ) -> ScopeFilter:
    notes: list[str] = []
    chapters = set(scope.chapter_ids)

    topics = set(scope.topic_ids)
    if topics or scope.subtopic_ids:
        if not TAXONOMY_DIR.exists():
            notes.append(
                "Topic and subtopic ids were accepted without checking: the topic "
                "taxonomy (academicos-data/syllabus/taxonomy/) is not on this server yet.")
    if topics and not any(_topic_ids(q) for q in candidates):
        # No question carries topic tags yet. Filtering on them would empty
        # every section and blame the bank for a tagging gap; say so instead.
        notes.append("Topic filter not applied: no question in the bank is tagged "
                      "with topics yet, so the paper uses the chosen chapters.")
        topics = set()

    subtopic_ids: Optional[set[str]] = None
    if scope.subtopic_ids:
        tagged = set(subtopic_question_ids(scope.subtopic_ids)) if subtopic_question_ids else set()
        if tagged:
            subtopic_ids = tagged
        else:
            notes.append("Subtopic filter not applied: no question is tagged to the "
                          "chosen subtopics yet, so the paper uses the chosen chapters.")

    def in_scope(q: QuestionSchema) -> bool:
        if chapters and not chapters.intersection(q.chapter_ids):
            return False
        if subtopic_ids is not None and q.id not in subtopic_ids:
            return False
        if topics and not topics.intersection(_topic_ids(q)):
            return False
        return True

    return ScopeFilter(in_scope=in_scope, notes=notes)


def _topic_ids(q: QuestionSchema) -> list[str]:
    ids = q.metadata.get("topicIds") or q.metadata.get("topic_ids") or []
    single = q.metadata.get("topicId") or q.metadata.get("topic_id")
    return [*ids, single] if single else list(ids)


def _fits(q: QuestionSchema, section: TemplateSection) -> bool:
    if q.marks != section.marks_each:
        return False
    return not section.question_types or q.type in section.question_types


@dataclass
class SectionPlan:
    section: TemplateSection
    picked: list[QuestionSchema]
    borrowed: list[QuestionSchema]
    availability: SectionAvailability
    notes: list[str] = field(default_factory=list)


def plan(template: PaperTemplateDraft, template_id: str, candidates: list[QuestionSchema],
         scope: ScopeFilter, *, fill_from_outside_scope: bool = False,
         ) -> tuple[AvailabilityReport, list[SectionPlan]]:
    """Walks the sections in order, each claiming its questions so a later
    section with the same mark value only counts what is left.

    `candidates` is the whole class+subject bank; this function applies
    every other constraint itself so it can report each one.
    """
    keyed = [q for q in candidates if has_verified_key(q)]
    keyed_ids = {q.id for q in keyed}
    claimed: set[str] = set()
    plans: list[SectionPlan] = []

    for section in template.sections:
        fits_all = [q for q in candidates if _fits(q, section)]
        fits_keyed = [q for q in fits_all if q.id in keyed_ids and q.id not in claimed]
        eligible = [q for q in fits_keyed if scope.in_scope(q)]
        outside = [q for q in fits_keyed if not scope.in_scope(q)]
        without_key = sum(1 for q in fits_all if q.id not in keyed_ids and scope.in_scope(q))
        used_elsewhere = sum(1 for q in fits_all if q.id in claimed and scope.in_scope(q))

        needed = section.question_count
        picked = _pick(eligible, section, needed)
        borrowed: list[QuestionSchema] = []
        notes: list[str] = []
        if len(picked) < needed and fill_from_outside_scope and outside:
            borrowed = _pick(outside, section, needed - len(picked))
            notes.append(
                f"{section.title}: {len(borrowed)} question(s) taken from outside the "
                f"chosen chapters to fill the section ({', '.join(q.id for q in borrowed)}).")
        claimed.update(q.id for q in picked + borrowed)
        notes.extend(_mix_notes(section, picked + borrowed))

        available = len(eligible)
        shortfall = max(0, needed - available)
        availability = SectionAvailability(
            section_id=section.id, title=section.title, marks_each=section.marks_each,
            needed=needed, available=available,
            shortfall=shortfall, outside_scope_available=len(outside),
            without_key=without_key,
            reason=_reason(template, section, shortfall, available, len(candidates),
                           len(keyed), len(fits_all), len(outside), without_key,
                           used_elsewhere) if shortfall else "",
        )
        plans.append(SectionPlan(section, picked, borrowed, availability, notes))

    report = AvailabilityReport(
        template_id=template_id, grade=template.grade, subject=template.subject,
        bank_questions=len(candidates), keyed_questions=len(keyed),
        complete=all(p.availability.shortfall == 0 for p in plans),
        sections=[p.availability for p in plans], scope_notes=scope.notes,
    )
    return report, plans


def _order(pool: list[QuestionSchema]) -> list[QuestionSchema]:
    """Best first, deterministic: the same bank and template give the same paper."""
    return sorted(pool, key=lambda q: (-q.quality_score, q.id))


def _pick(pool: list[QuestionSchema], section: TemplateSection, n: int) -> list[QuestionSchema]:
    """Up to `n` questions honouring the section's difficulty mix and
    competency share as far as the pool allows. When a difficulty runs out,
    the slot goes to the nearest other difficulty rather than staying empty:
    a slightly easier paper is a better outcome than a shorter one, and the
    mismatch is reported by `_mix_notes`."""
    if n <= 0 or not pool:
        return []
    from .selection import is_competency_question

    remaining = _order(pool)
    targets = _difficulty_targets(section.difficulty_mix, n)
    cbq_target = round((section.competency_share or 0.0) * n)
    picked: list[QuestionSchema] = []

    def take(from_list: list[QuestionSchema]) -> Optional[QuestionSchema]:
        if not from_list:
            return None
        want_cbq = sum(1 for q in picked if is_competency_question(q)) < cbq_target
        if want_cbq:
            for q in from_list:
                if is_competency_question(q):
                    return q
        return from_list[0]

    for difficulty, count in targets:
        for _ in range(count):
            q = take([c for c in remaining if difficulty is None or c.difficulty == difficulty])
            if q is None:
                break
            picked.append(q)
            remaining.remove(q)
    while len(picked) < n and remaining:
        q = take(remaining)
        picked.append(q)
        remaining.remove(q)
    return picked


def _difficulty_targets(mix: Optional[DifficultyDistribution],
                        n: int) -> list[tuple[Optional[str], int]]:
    """Largest-remainder split of `n` over the mix, so the counts always sum to n."""
    if mix is None:
        return [(None, n)]
    shares = [("easy", mix.easy), ("medium", mix.medium), ("hard", mix.hard)]
    raw = [(d, share * n) for d, share in shares]
    counts = {d: int(v) for d, v in raw}
    left = n - sum(counts.values())
    for d, v in sorted(raw, key=lambda dv: dv[1] - int(dv[1]), reverse=True)[:left]:
        counts[d] += 1
    return [(d, counts[d]) for d, _ in shares]


def _mix_notes(section: TemplateSection, picked: list[QuestionSchema]) -> list[str]:
    notes: list[str] = []
    if section.difficulty_mix is not None and picked:
        wanted = dict(_difficulty_targets(section.difficulty_mix, len(picked)))
        got = {d: sum(1 for q in picked if q.difficulty == d) for d in wanted}
        if got != wanted:
            notes.append(
                f"{section.title}: difficulty is easy/medium/hard "
                f"{got['easy']}/{got['medium']}/{got['hard']}, the template asked for "
                f"{wanted['easy']}/{wanted['medium']}/{wanted['hard']} -- the bank has "
                "too few at the requested level.")
    if section.competency_share and picked:
        from .selection import is_competency_question
        target = round(section.competency_share * len(picked))
        got_cbq = sum(1 for q in picked if is_competency_question(q))
        if got_cbq < target:
            notes.append(f"{section.title}: {got_cbq} competency-based question(s), "
                         f"the template asked for {target}.")
    return notes


def _reason(template: PaperTemplateDraft, section: TemplateSection, shortfall: int,
            available: int, bank: int, keyed: int, fits: int, outside: int,
            without_key: int, used_elsewhere: int) -> str:
    """The binding constraint, in words a teacher can act on."""
    who = f"Class {template.grade} {template.subject}"
    kind = f"{section.marks_each}-mark"
    if section.question_types:
        kind += " " + "/".join(t.replace("_", " ") for t in section.question_types)
    if bank == 0:
        return f"The bank has no {who} questions yet."
    if keyed == 0:
        return (f"The bank has {bank} {who} questions but none with a verified "
                "answer key yet, so none can be printed.")
    if fits == 0:
        return f"The bank has no {kind} {who} questions."
    parts = [f"Only {available} {kind} question(s) are available; {shortfall} short."]
    if outside:
        parts.append(f"{outside} more are in other chapters -- widen the chapters "
                     "or allow filling from outside them.")
    if without_key:
        parts.append(f"{without_key} more have no verified answer key yet.")
    if used_elsewhere:
        parts.append(f"{used_elsewhere} are already used by earlier sections.")
    return " ".join(parts)
