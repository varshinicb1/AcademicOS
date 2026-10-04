"""What counts as a competency-based question: one rule, read only from what a
source printed (Task 125, step 1).

CBSE asks that at least half of a paper be competency-based. The old rule
(`selection.is_competency_question`) answered from values nobody judged:

  * a Bloom level of apply or higher -- but Bloom is the "understand" default
    on 5,429 of 5,429 served records, so the clause could only ever fire on a
    fixture;
  * stem phrases ("read the following", "case study", "assertion" plus
    "reason") -- which matched text our merge prepends, Exemplar's "Read the
    following statements", and an SQP run-on that swallowed Section E's
    heading;
  * metadata flags `is_competency` / `cbq` that nothing writes.

And it missed the one thing the bank does print: 0 of the 435 served class
6-10 items from CBSE's Competency-Based Education item banks counted.

Each case runs on the camelCase record AND the QuestionSchema built from it,
and the two must agree: bank_health reads records, the paper paths read
schemas, and one rule must give one answer to both.
"""
from __future__ import annotations

import ast
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.assessment import competency, selection  # noqa: E402
from academicos.assessment.competency import (  # noqa: E402
    CBE_ITEM_BANK_PREFIX,
    CBSE_COMPETENCY_TARGET,
    COMPETENCY_RULE_TEXT,
    COMPETENCY_TYPES,
    competency_signal,
    is_competency_question,
)
from academicos.assessment.schemas import (  # noqa: E402
    BloomDistribution,
    Blueprint,
    BlueprintRequest,
    ChapterWeights,
    CompetencyWeights,
    DifficultyDistribution,
    QuestionSchema,
)


# ---- fixtures ---------------------------------------------------------------

def _record(**overrides) -> dict:
    """A plain served-shape record: nothing on it says competency-based."""
    now = datetime.now(timezone.utc).isoformat()
    rec = {
        "id": "q1", "questionBankId": "bank", "subject": "Science", "grade": 10,
        "chapterIds": ["ch1"], "competencyIds": [], "bloomLevel": "understand",
        "difficulty": "medium", "type": "short_answer",
        "stem": "Explain why the sky appears blue on a clear day.",
        "answerScheme": {"totalMarks": 3, "modelAnswer": "Scattering of light."},
        "estimatedTimeMinutes": 4, "marks": 3, "source": "cbse_board_paper",
        "createdAt": now, "updatedAt": now, "metadata": {},
    }
    rec.update(overrides)
    return rec


def _signal(rec: dict) -> str | None:
    """The signal for `rec`, asserted identical on its dict and schema forms."""
    as_dict = competency_signal(rec)
    as_schema = competency_signal(QuestionSchema.model_validate(rec))
    assert as_dict == as_schema, (as_dict, as_schema)
    assert is_competency_question(rec) is (as_dict is not None)
    assert is_competency_question(QuestionSchema.model_validate(rec)) is (as_dict is not None)
    # Every caller that imports it from selection gets the same rule.
    assert selection.is_competency_question(QuestionSchema.model_validate(rec)) is (
        as_dict is not None)
    return as_dict


# The real CBSE stems quoted below are from the served bank
# (academicos-data/syllabus/questions.json, composedAt 2026-09-23).
SS10_Q23 = (
    "Two statements are given as Assertion (A) and Reason(R). Study the statements "
    "carefully and identify the correct alternative: ASSERTION (A): Exclusive "
    "attention to caste can produce negative results in democracy. REASON (R): It can "
    "divert attention from other important issues thus leading to tensions, conflicts "
    "and even violence. Choose the correct option: A. Both A and R are true, and R is "
    "the correct explanation of A. B. Both A and R are true, but R is not the correct "
    "explanation of A. C. A is true but R is false. D. A is false but R is true")
# cbse:sqp:ClassX_2024_25:Computer Applications:11 -- the Reason printed first.
REASON_FIRST = ("Reason (R) : HTML is an example of a Protocol. Assertion (A) :Chat and "
                "e-mail are live/real time conversation between 1")
# cbse:sqp:ClassX_2024_25:Mathematics (Standard):35 -- a 5-mark statistics question
# whose extraction ran on into the next section's heading.
SQP_MATHS_Q35_RUN_ON = (
    "Find the value of x and also find the mean expenditure Section E Section E "
    "consists of 3 case study based questions of 4 marks each.")
# bank_merge prepends this to a passage-led item's stem (bank_merge.normalise,
# where metadata carries a `passage`); the words are ours, not the source's.
MERGE_PREPENDED = ("Read the passage below and answer the question that follows.\n\n"
                   "The weights of new born babies in a hospital were recorded.\n\n"
                   "Find the mean weight.")


# ---- the item-bank signal ---------------------------------------------------

def test_a_cbe_item_bank_record_counts_whatever_its_type_and_bloom():
    """A CBE item-bank question is competency-based by its source; the old rule
    counted 0 of the 435 served ones (typed long_answer etc., Bloom 'understand')."""
    rec = _record(questionBankId="cbe:Item-Bank---Maths-Class-6.pdf", type="long_answer",
                  bloomLevel="understand", source="cbse_question_bank")
    assert _signal(rec) == "cbeItemBank"


def test_the_item_bank_prefix_is_the_one_the_importer_writes():
    assert CBE_ITEM_BANK_PREFIX == "cbe:"
    importer = (ROOT / "src" / "academicos" / "corpus" / "cbse_cbe.py").read_text(encoding="utf-8")
    assert '"questionBankId": f"cbe:{item.source_pdf}"' in importer


def test_a_snake_case_mapping_reads_the_same_bank_id():
    rec = {"question_bank_id": "cbe:Item-Bank---Science-Class-9.pdf", "type": "mcq",
           "stem": "Which of these is a mixture?", "metadata": {}}
    assert competency_signal(rec) == "cbeItemBank"


# ---- the type signal --------------------------------------------------------

@pytest.mark.parametrize("qtype", sorted(COMPETENCY_TYPES))
def test_a_printed_competency_type_counts(qtype):
    assert _signal(_record(type=qtype)) == "competencyType"


def test_the_competency_types_are_cbses_section_kinds():
    assert COMPETENCY_TYPES == {"case_study", "assertion_reason", "competency_based"}


@pytest.mark.parametrize("qtype", sorted(COMPETENCY_TYPES))
def test_a_type_the_code_inferred_does_not_count(qtype):
    """mapping.py makes any 5-mark question a case_study and any stem with
    'passage' in it one too; the record says so with typeInferred."""
    assert _signal(_record(type=qtype, metadata={"typeInferred": True})) is None


# ---- the assertion-reason labels --------------------------------------------

def test_the_real_ss10_assertion_reason_stem_counts_even_typed_mcq():
    rec = _record(type="mcq", marks=1, stem=SS10_Q23, subject="Social Science",
                  answerScheme={"totalMarks": 1, "modelAnswer": "A"},
                  source="cbse_sample_paper")
    assert _signal(rec) == "assertionReasonLabels"


def test_the_labels_count_in_either_order():
    rec = _record(type="short_answer", marks=1, stem=REASON_FIRST,
                  answerScheme={"totalMarks": 1, "modelAnswer": "A"})
    assert _signal(rec) == "assertionReasonLabels"


def test_one_label_alone_does_not_count():
    assert _signal(_record(stem="Assertion (A): Iron rusts in moist air.")) is None
    assert _signal(_record(stem="Reason (R): Rusting needs water and oxygen.")) is None


# ---- what the rule never reads ----------------------------------------------

@pytest.mark.parametrize("bloom", ["apply", "analyze", "evaluate", "create"])
def test_a_bloom_level_does_not_count(bloom):
    """Bloom is the neutral default on every served record: nobody judged it."""
    assert _signal(_record(bloomLevel=bloom)) is None


@pytest.mark.parametrize("stem", [
    "Read the following statements about diseases and choose the correct ones.",
    MERGE_PREPENDED,
    SQP_MATHS_Q35_RUN_ON,
    "The assertion that metals expand on heating is true, and for this reason "
    "railway tracks have gaps. Explain.",
], ids=["exemplar-read-the-following", "merge-prepended-passage", "sqp-q35-run-on",
        "assertion-and-reason-as-words"])
def test_stem_phrases_do_not_count(stem):
    assert _signal(_record(stem=stem)) is None


@pytest.mark.parametrize("flag", ["cbq", "is_competency"])
def test_a_metadata_flag_nothing_writes_does_not_count(flag):
    assert _signal(_record(metadata={flag: True})) is None


def test_marks_do_not_count():
    rec = _record(marks=5, type="long_answer",
                  answerScheme={"totalMarks": 5, "modelAnswer": "Five points."})
    assert _signal(rec) is None


def test_an_exemplar_reasoning_heading_does_not_count():
    """Exemplar's 'Short Answer Questions with Reasoning' is a section heading
    about justifying true/false, not CBSE's competency format."""
    rec = _record(
        id="exemplar:q:9:mathematics:5:5.2:1", questionBankId="ncert-exemplar:class9-mathematics/ieep205.pdf",
        subject="Mathematics", grade=9, type="very_short_answer", marks=2,
        stem="Euclidean geometry is valid only for curved surfaces.", source="ncert_exemplar",
        answerScheme={"totalMarks": 2, "modelAnswer": "False."},
        metadata={"sectionKind": "vsa", "sectionLabel": "Short Answer Questions with Reasoning",
                  "difficultyInferred": True, "bloomInferred": True})
    assert _signal(rec) is None


# ---- one rule, one target, one place ----------------------------------------

def test_the_rule_module_imports_nothing_from_the_package():
    """A leaf: paper_templates, selection and bank_health all import it, and
    none of them may pull the others (or pool.py) in through it."""
    tree = ast.parse(Path(competency.__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.level == 0, f"relative import: from {'.' * node.level}{node.module}"
            assert not (node.module or "").startswith("academicos"), node.module
        elif isinstance(node, ast.Import):
            assert not any(a.name.startswith("academicos") for a in node.names)


def test_selection_re_exports_the_one_rule():
    assert selection.is_competency_question is competency.is_competency_question
    assert selection.competency_signal is competency.competency_signal
    # The dead share helper is gone: the paper computes its share from the
    # printed isCompetency flags, and nothing called this one.
    assert not hasattr(selection, "competency_share")


def test_the_cbse_target_is_one_constant():
    assert CBSE_COMPETENCY_TARGET == 0.5
    kw = dict(total_marks=10, duration_minutes=30,
              difficulty=DifficultyDistribution(easy=0.3, medium=0.5, hard=0.2),
              bloom=BloomDistribution(remember=0.2, understand=0.3, apply=0.2, analyze=0.1,
                                      evaluate=0.1, create=0.1),
              chapter_weights=ChapterWeights(), competency_weights=CompetencyWeights())
    assert Blueprint(**kw).competency_percentage == CBSE_COMPETENCY_TARGET == 0.5
    assert BlueprintRequest(**kw).competency_percentage == CBSE_COMPETENCY_TARGET


def test_the_rule_text_names_what_counts_and_what_is_never_read():
    text = COMPETENCY_RULE_TEXT
    assert "item bank" in text and "Assertion (A)" in text and "Reason (R)" in text
    assert "Bloom" in text


# ---- the most a paper's sections can hold (Task 125, step 6) ----------------

def _recs(prefix: str, n: int, *, cbe: bool = False) -> list[dict]:
    return [_record(id=f"{prefix}{i}", **({"questionBankId": "cbe:x.pdf"} if cbe else {}))
            for i in range(n)]


def _both_forms(sections, **kw):
    """`sections` as camelCase records and as QuestionSchemas: one answer."""
    as_schema = [(n, [QuestionSchema.model_validate(r) for r in own],
                  [QuestionSchema.model_validate(r) for r in borrowed])
                 for n, own, borrowed in sections]
    got = competency.competency_ceiling(sections, **kw)
    assert competency.competency_ceiling(as_schema, **kw) == got
    return got


def _worded(prefix: str, n: int, *, cbe: bool = False) -> list[dict]:
    """Like `_recs`, but every stem its own question, so a `repeats` test
    decides which records restate each other."""
    return [_record(id=f"{prefix}{i}", stem=f"State fact {i} about the {prefix} set.",
                    **({"questionBankId": "cbe:x.pdf"} if cbe else {}))
            for i in range(n)]


def _same_stem(a: str, b: str) -> bool:
    """A stand-in for pool.near_duplicate, which this leaf may not import."""
    return a == b


def test_a_section_holds_no_more_competency_questions_than_its_bank_has():
    plain = _recs("plain", 5)
    assert _both_forms([(4, _recs("cbe", 1, cbe=True) + plain, [])]) == 1
    assert _both_forms([(4, _recs("cbe", 3, cbe=True) + plain, [])]) == 3
    assert _both_forms([(2, _recs("cbe", 3, cbe=True) + plain, [])]) == 2
    assert _both_forms([]) == 0


def test_the_fallback_only_fills_a_shortfall():
    """optimize() borrows from outside the chosen chapters only for a section
    its chapters cannot fill (selection.optimize's fallback)."""
    outside = _recs("cbe", 3, cbe=True)
    assert _both_forms([(4, _recs("plain", 4), outside)]) == 0
    assert _both_forms([(4, _recs("plain", 2), outside)]) == 2
    assert _both_forms([(4, [], outside)]) == 3


def test_sections_share_one_bank():
    """A question placed in one section cannot be counted again in the next."""
    shared = _recs("cbe", 3, cbe=True)
    assert _both_forms([(2, shared, []), (2, shared, [])]) == 3
    # And a section whose own fits an earlier section used up is short, so it
    # borrows: 3 plain fits for two 2-question sections leave the second one
    # short by 1, which optimize() fills from the fallback.
    plain = _recs("plain", 3)
    assert _both_forms([(2, plain, _recs("cbe", 2, cbe=True)),
                        (2, plain, _recs("cbe", 2, cbe=True))]) == 1


def test_a_restated_question_does_not_fill_a_section():
    """optimize() skips a question that restates one already on the paper
    (pool.near_duplicate), so an in-scope fit that restates another leaves the
    section short, and the section borrows a competency-based question from
    outside the chapters. Told what repeats, the ceiling counts that borrow;
    blind to it, the ceiling said 0 of a paper that printed 1
    (review_s56/synthetic.py, case 1)."""
    plain = _worded("plain", 4)
    plain[1]["stem"] = plain[0]["stem"]
    outside = _worded("cbe", 2, cbe=True)
    assert _both_forms([(4, plain, outside)]) == 0
    assert _both_forms([(4, plain, outside)], repeats=_same_stem) == 1


def test_restated_competency_questions_count_once():
    """Two copies of one competency-based question can print only once."""
    cbe = _worded("cbe", 3, cbe=True)
    cbe[1]["stem"] = cbe[0]["stem"]
    assert _both_forms([(4, cbe + _worded("plain", 4), [])]) == 3
    assert _both_forms([(4, cbe + _worded("plain", 4), [])], repeats=_same_stem) == 2
    # Across sections too: the second section's copy repeats the first's.
    assert _both_forms([(1, cbe[:1], []), (1, cbe[1:2], [])], repeats=_same_stem) == 1


def test_the_fallback_is_counted_once_and_never_for_its_own_section():
    """A fallback question is one question however often it is listed, and a
    question the section already counted from its own chapters cannot be
    borrowed for it a second time (bank_health passes overlapping lists)."""
    cbe0, plain0 = _worded("cbe", 1, cbe=True)[0], _worded("plain", 1)[0]
    assert _both_forms([(3, [cbe0, plain0], [cbe0])]) == 1
    outside = _worded("out", 1, cbe=True)
    assert _both_forms([(3, [plain0], outside + outside)]) == 1


def test_from_cbe_item_bank_reads_both_record_shapes():
    """One test of the item-bank prefix, for the rule and the tier signals."""
    rec = _record(questionBankId="cbe:Item-Bank---Maths-Class-6.pdf")
    assert competency.from_cbe_item_bank(rec) is True
    assert competency.from_cbe_item_bank(QuestionSchema.model_validate(rec)) is True
    assert competency.from_cbe_item_bank({"question_bank_id": "cbe:x.pdf"}) is True
    assert competency.from_cbe_item_bank(_record()) is False
    assert competency.from_cbe_item_bank({"questionBankId": None}) is False


# ---- the served bank --------------------------------------------------------

_REAL_BANK = ROOT / "academicos-data" / "syllabus" / "questions.json"
needs_real_bank = pytest.mark.skipif(not _REAL_BANK.exists(),
                                     reason="the served question bank is not in this checkout")


@needs_real_bank
def test_the_served_class_6_to_10_signals():
    """Served = what pool.build_pool serves: the merge's gate, a valid
    QuestionSchema, and an answer key. Read, never written."""
    from academicos.assessment import grades
    from academicos.assessment.qbank_engine import QuestionBank
    from academicos.corpus.bank_merge import unservable_reason

    raw = json.loads(_REAL_BANK.read_text(encoding="utf-8"))["questions"]
    by_dict, by_schema, exemplar = Counter(), Counter(), Counter()
    for rec in raw:
        try:
            g = grades.to_int(grades.to_roman(rec.get("grade")))
        except ValueError:
            continue
        if g not in range(6, 11) or unservable_reason(rec) is not None:
            continue
        try:
            q = QuestionSchema.model_validate(rec)
        except ValueError:
            continue
        if not QuestionBank.has_answer_key(rec):
            continue
        s = competency_signal(rec)
        by_dict[s] += 1
        by_schema[competency_signal(q)] += 1
        if rec.get("source") == "ncert_exemplar" and s is not None:
            exemplar[s] += 1
    assert by_dict == by_schema
    del by_dict[None]
    # 435 CBE items until the fidelity rebuild of 2026-09-28, which refused the
    # ones that cannot be answered as printed (corpus/fidelity.py).
    # 366 -> 364 (2026-10-01): cbe:q:Maths10AS8 is refused as value-missing ("(Using π= )",
    # and its key's Rs 8800 contradicts the stem's Rs 50 a metre) after the extraction
    # repair (dde445a, #78), and cbe:q:SCIENCE8JS41c is withheld (its key answers one
    # of three parts).
    # + 274 competencyType (2026-10-04): the model-written class 9-10 questions (corpus/ai-cbse-9-10)
    # whose type a source-grounded generator printed -- case studies, assertion-reason items, and the
    # passage-based reading and extract questions, which CBSE calls competency-based.
    assert dict(by_dict) == {"cbeItemBank": 364, "assertionReasonLabels": 2, "competencyType": 274}
    assert not exemplar
