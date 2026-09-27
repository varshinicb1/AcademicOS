# Task 125: The competency share is real, and a paper that cannot reach CBSE's 50% says so before it prints

## Why

The re-audit of the live release (2026-09-23) scored item 1.4 at 0.25:

> **CBQ is ~0**: the 10 papers measure 0.0/8.3/0.0/15.8/0.0/2.6/7.9/0.0/0.0/0.0 %
> against a 50% target.

CBSE's 2024-25 scheme requires at least half of a paper to be competency-based:
case studies, source-based and assertion-reason items, and questions that ask a
student to apply or analyse rather than recall. `selection.is_competency_question`
keys off `type in (case_study, assertion_reason, competency_based)` or
`bloom_level in (apply, analyze, evaluate, create)`, and the bank carries
neither: `competencyIds` is empty on all 5,427 records and every Bloom level is
the default "understand" (now honestly flagged `bloomInferred`, Task 122).

But the questions themselves are not all recall. The CBE bank is CBSE's own
COMPETENCY-BASED item bank -- the clue is in its name -- and the Exemplar prints
section kinds. The share is measurable; nobody measured it.

## Required behaviour

1. **Read the competency signal the sources carry**, and only that:
   - a CBE record comes from CBSE's competency-based item bank: say so on the
     record (`competencyIds` or a flag with its provenance), and cite where the
     source states it;
   - a record whose TYPE is case study, source-based or assertion-reason is
     competency-based by CBSE's own definition -- the type is already on the
     record for many, and `corpus/mcq_shape.py` can recognise an A-R stem;
   - Exemplar section kinds that are application/analysis in the book's own
     words (cite the book), if any hold.
   Do NOT infer a Bloom level from marks, from length, or from a model: an
   invented "apply" is exactly the silent wrongness Task 122 removed.
2. **Report the real share per subject and class** -- of served questions, and of
   the questions a blueprint's sections can actually use. Put the numbers in your
   summary and in the bank health report.
3. **A paper says what it can reach BEFORE it prints.** When a blueprint asks
   for 50% competency and the bank for that class and subject holds less, the
   response says so in a warning that names the real share and what the paper
   got, and the guided builder shows it at the step where the teacher can still
   change the scope -- not only after the PDF exists.
4. **Tiers**: with `difficultyInferred` now set on 4,192 records, a tiered
   request returns the same paper and reports `tiersAvailable: false`. Make that
   visible where a teacher chooses the tier (the builder's step), with a sentence
   saying why -- "this subject's questions carry no difficulty we can act on".
   Do not silently keep offering three tiers that do the same thing.

## Required tests (write first, watch them fail)

A CBE record counts as competency-based and says where that comes from; an
assertion-reason record counts; a plain recall record does not; a class whose
bank holds under 50% gets the warning before generation, naming the real share;
the tier control reports unavailable with its reason; no test asserts a Bloom
level the source never printed.

## Files

- Modify: `src/academicos/assessment/selection.py` (the one definition),
  `src/academicos/corpus/` importer that writes the flag, the builder's step
  that shows it (`frontend/lib/presentation/paper_builder/**`),
  `src/academicos/syllabus/bank_health.py`
- Tests: `tests/test_assessment_selection.py`,
  `tests/test_paper_generation_honesty.py`, `tests/test_bank_health.py`,
  `frontend/test/paper_builder/**`
