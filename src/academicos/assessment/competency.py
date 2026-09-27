"""What counts as a competency-based question: one rule, read only from what a
source printed.

CBSE asks that at least half of a paper be competency-based. Whether a
question is one is a fact about the question's source, so this rule reads
only three things a source put there, and takes the first that holds:

  * ``cbeItemBank`` -- the question comes from one of CBSE's Competency-Based
    Education item banks (https://cbseacademic.nic.in/cbe/assessment.html;
    page 1 of every Maths/Science item-bank PDF reads "Competency-based
    education for CBSE"). The importer writes ``questionBankId`` as
    ``"cbe:" + <source pdf>`` (corpus/cbse_cbe.py).
  * ``competencyType`` -- the record's type is one of CBSE's competency
    section kinds (case study, assertion-reason, competency-based) and our
    code did not supply it. A supplied type carries ``metadata.typeInferred``:
    bank_merge sets it when it retypes an item ``mcq``, and mapping.py on
    every record it builds from extraction, where a 5-mark question becomes a
    ``case_study`` by marks alone and a stem that says "passage" becomes one
    by keyword.
  * ``assertionReasonLabels`` -- the stem carries both of CBSE's printed
    labels, "Assertion (A)" and "Reason (R)", in either order (an SQP item
    typed ``mcq`` is still an assertion-reason item).

What the rule never reads, and why (the served bank, composedAt 2026-09-23):

  * the Bloom level -- "understand" on 5,429 of 5,429 records: the bank's
    default, not a judgement;
  * the metadata flags ``is_competency`` / ``cbq`` -- nothing writes them
    (0 of 5,429 records carry either);
  * stem phrases such as "read the following" or "case study" -- they match
    text our merge prepends ("Read the passage below ..."), Exemplar's "Read
    the following statements", and an SQP question whose extraction ran on
    into the next section's heading ("Section E consists of 3 case study
    based questions");
  * marks.

This module imports nothing from the academicos package. selection,
paper_templates and syllabus.bank_health all need the rule, and a leaf module
lets each import it without the paper_templates/selection import cycle or
pulling pool.py into bank_health.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

# questionBankId prefix of every item read from a CBSE CBE item-bank PDF.
CBE_ITEM_BANK_PREFIX = "cbe:"

# CBSE's competency-based question kinds, as QuestionSchema types.
COMPETENCY_TYPES = frozenset({"case_study", "assertion_reason", "competency_based"})

# CBSE: at least half of a paper competency-based.
CBSE_COMPETENCY_TARGET = 0.50

# The one sentence every surface shows for "what did you count?".
COMPETENCY_RULE_TEXT = (
    "Counted as competency-based: questions from CBSE's competency-based item banks, "
    "questions their source prints as case-based, assertion-reason or competency-based, "
    "and questions printed with CBSE's Assertion (A) and Reason (R) labels. "
    "A Bloom level, the marks or other wording in a question are never counted.")

_ASSERTION_LABEL = re.compile(r"\bAssertion\s*\(A\)")
_REASON_LABEL = re.compile(r"\bReason\s*\(R\)")


def _field(q: Any, camel: str, snake: str) -> Any:
    """`q`'s field, from a camelCase (or snake_case) record or a QuestionSchema."""
    if isinstance(q, Mapping):
        value = q.get(camel)
        return q.get(snake) if value is None else value
    return getattr(q, snake, None)


def competency_signal(q: Any) -> str | None:
    """Why `q` is competency-based -- ``"cbeItemBank"``, ``"competencyType"`` or
    ``"assertionReasonLabels"`` -- or None when nothing its source printed says so.

    `q` is a QuestionSchema or a camelCase record (the served JSON shape); both
    give the same answer.
    """
    bank_id = _field(q, "questionBankId", "question_bank_id")
    if isinstance(bank_id, str) and bank_id.startswith(CBE_ITEM_BANK_PREFIX):
        return "cbeItemBank"
    metadata = _field(q, "metadata", "metadata") or {}
    if _field(q, "type", "type") in COMPETENCY_TYPES and not metadata.get("typeInferred"):
        return "competencyType"
    stem = _field(q, "stem", "stem") or ""
    if _ASSERTION_LABEL.search(stem) and _REASON_LABEL.search(stem):
        return "assertionReasonLabels"
    return None


def is_competency_question(q: Any) -> bool:
    """Is `q` competency-based? See `competency_signal` for the one rule."""
    return competency_signal(q) is not None
