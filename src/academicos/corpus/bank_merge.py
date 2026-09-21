"""Compose the served question bank from its three sources.

The served bank -- academicos-data/syllabus/questions.json and its byte-identical
APK copy, frontend/assets/corpus/questions.json -- is what every surface reads.
It is composed from:

  board  records already in it with source == "cbse_board_paper"
  cbe    academicos-data/corpus/cbse-cbe/questions.json   (classes 6-10)
  sqp    academicos-data/corpus/cbse-sqp/questions.json   (classes 10, 12)

Board records pass through untouched: they already decode on the phone and
render on the web, and this module must not be the thing that breaks them.
CBE and SQP records are normalised to the phone's contract and then gated.

Why the contract is the phone's and not the API's
--------------------------------------------------
`QuestionSchema` accepts all 720 CBE records; the phone's `Question.fromJson`
rejects 259 of them (parts with no `textLatex`) and all 1,834 SQP records (no
`competencyIds`, no `bloomLevel`). One rejected row fails the whole corpus load,
before runApp(), so the app never leaves its splash screen. The two contracts
have drifted, so this enforces the stricter one. `contract_errors` mirrors
frontend/lib/domain/entities/question.g.dart; a Dart test that decodes the real
asset is the final word.

Why a value is checked, not just its presence
---------------------------------------------
The phone's enum converters do not fail on an unknown value -- they default.
An unknown `source` becomes `ncert_textbook`, which would print a CBSE sample
paper question as an NCERT textbook one. So values are checked against the sets
the converters accept.

What is excluded, and why
-------------------------
Nothing is dropped silently; every exclusion is returned with its reason.

  figure-unavailable     no surface can resolve a `cbe-figure:` asset
  passage-unavailable    a comprehension question with no passage to read
  header-as-stem         the "question" is a page header
  stem-too-short         no question text to speak of
  no-answer              rule Q1: no answer key, no question
  answer-is-question-text  the scheme joined the wrong text -- often another
                         question's stem
  answer-bleed           an answer far longer than its marks allow: the
                         scheme ran on into the following questions
  garbled-script         legacy-font extraction produced text nobody can read
  mcq-options-unresolved the options cannot be read as A-D, or a student could
                         not choose between them (empty, or two read alike)
  mcq-answer-unresolved  the correct option cannot be recovered with certainty
  duplicate-id           an id already served
  duplicate-stem         already served, under a board-paper id where possible
"""
from __future__ import annotations

import copy
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..assessment.mapping import _resolve_bloom, _resolve_difficulty, _resolve_type
from ..assessment.question_bank import OfficialAnswer, build_official_scheme

BOARD_SOURCE = "cbse_board_paper"

# The values each phone converter accepts (frontend/lib/domain/entities/enums.dart).
BLOOM_LEVELS = frozenset({"remember", "understand", "apply", "analyze", "evaluate", "create"})
DIFFICULTIES = frozenset({"easy", "medium", "hard"})
QUESTION_TYPES = frozenset({
    "mcq", "very_short_answer", "short_answer", "long_answer", "very_long_answer",
    "case_study", "assertion_reason", "map_based", "diagram_based", "graph_based",
    "table_based", "competency_based"})
SOURCES = frozenset({
    "cbse_board_paper", "cbse_sample_paper", "cbse_question_bank", "ncert_exemplar",
    "ncert_textbook", "school_database", "teacher_created", "ai_generated",
    "competency_framework"})
ANSWER_TYPES = frozenset({
    "singleChoice", "multipleChoice", "textShort", "textLong", "numeric", "diagram",
    "map", "graph", "table"})


class ContractError(Exception):
    """A normalised record still breaks the phone's contract -- a normaliser bug."""

    def __init__(self, record_id: str, errors: list[str]) -> None:
        super().__init__(f"{record_id}: {'; '.join(errors)}")
        self.record_id = record_id
        self.errors = errors


# --------------------------------------------------------------------------- #
# the contract
# --------------------------------------------------------------------------- #

def _is_num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _is_str_list(v: Any) -> bool:
    return isinstance(v, list) and all(isinstance(x, str) for x in v)


def _is_iso(v: Any) -> bool:
    if not isinstance(v, str):
        return False
    try:
        datetime.fromisoformat(v.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _check(obj: dict, where: str, spec: dict[str, str], errs: list[str]) -> None:
    for key, kind in spec.items():
        present = key in obj and obj[key] is not None
        value = obj.get(key)
        optional = kind.endswith("?")
        kind = kind.rstrip("?")
        if not present:
            if not optional:
                errs.append(f"{where}.{key} missing")
            continue
        ok = {
            "str": isinstance(value, str),
            "num": _is_num(value),
            "bool": isinstance(value, bool),
            "strlist": _is_str_list(value),
            "list": isinstance(value, list),
            "dict": isinstance(value, dict),
            "iso": _is_iso(value),
        }[kind]
        if not ok:
            errs.append(f"{where}.{key} is not {kind}")


_QUESTION = {
    "id": "str", "questionBankId": "str", "subject": "str", "grade": "num",
    "chapterIds": "strlist", "competencyIds": "strlist", "bloomLevel": "str",
    "difficulty": "str", "type": "str", "stem": "str", "stemLatex": "str",
    "parts": "list", "answerScheme": "dict", "estimatedTimeMinutes": "num",
    "marks": "num", "language": "str", "source": "str", "qualityScore": "num",
    "tags": "strlist", "createdAt": "iso", "updatedAt": "iso", "metadata": "dict?",
    "diagramAssetId": "str?", "mapAssetId": "str?", "graphAssetId": "str?",
    "tableAssetId": "str?",
}
_PART = {
    "id": "str", "partNumber": "num", "text": "str", "textLatex": "str", "marks": "num",
    "answerType": "str", "options": "strlist?", "correctOption": "str?",
    "expectedAnswer": "str?", "expectedAnswerLatex": "str?", "keywords": "strlist?",
    "alternativeAnswers": "strlist?",
}
_SCHEME = {
    "totalMarks": "num", "markingPoints": "list", "rubricLevels": "list",
    "commonErrors": "strlist", "alternativeAnswers": "strlist", "modelAnswer": "str",
    "modelAnswerLatex": "str", "hasPartialCredit": "bool?", "metadata": "dict?",
}
_POINT = {"id": "str", "description": "str", "marks": "num", "keyword": "str",
          "isRequired": "bool", "synonyms": "strlist?"}
_RUBRIC = {"level": "num", "label": "str", "minMarks": "num", "maxMarks": "num",
           "description": "str"}
_ENUMS = {"bloomLevel": BLOOM_LEVELS, "difficulty": DIFFICULTIES,
          "type": QUESTION_TYPES, "source": SOURCES}


def contract_errors(rec: dict) -> list[str]:
    """Every way this record would fail, or mis-decode on, the phone."""
    errs: list[str] = []
    _check(rec, "question", _QUESTION, errs)
    for key, allowed in _ENUMS.items():
        if isinstance(rec.get(key), str) and rec[key] not in allowed:
            errs.append(f"question.{key}={rec[key]!r} is not one of the phone's values")
    for i, part in enumerate(rec.get("parts") or []):
        if not isinstance(part, dict):
            errs.append(f"parts[{i}] is not an object")
            continue
        _check(part, f"parts[{i}]", _PART, errs)
        if isinstance(part.get("answerType"), str) and part["answerType"] not in ANSWER_TYPES:
            errs.append(f"parts[{i}].answerType={part['answerType']!r} is not one of the phone's values")
    scheme = rec.get("answerScheme")
    if isinstance(scheme, dict):
        _check(scheme, "answerScheme", _SCHEME, errs)
        for i, mp in enumerate(scheme.get("markingPoints") or []):
            _check(mp if isinstance(mp, dict) else {}, f"markingPoints[{i}]", _POINT, errs)
        for i, rl in enumerate(scheme.get("rubricLevels") or []):
            _check(rl if isinstance(rl, dict) else {}, f"rubricLevels[{i}]", _RUBRIC, errs)
    return errs


# --------------------------------------------------------------------------- #
# gates
# --------------------------------------------------------------------------- #

_HEADER = re.compile(
    r"^(?:PART\s*[-–]|Page\b|Class\s*[-–]|Subject\s*[-–]|Time allowed|"
    r"Maximum marks|General Instructions)", re.I)
# A scheme that joined the wrong text often carries the next question's stem.
_INSTRUCTION = re.compile(
    r"^(?:read the (?:following|given|passage|extract|data|information)|fill in the blank|"
    r"find the odd one|select the (?:correct|appropriate)|choose the (?:correct|appropriate))",
    re.I)
_PASSAGE_REF = re.compile(r"\bread the (?:following )?(?:passage|extract|poem|text)\b", re.I)
_AWARD = re.compile(r"\s*\bAward\b.*$", re.I | re.S)
_MIN_STEM = 15
_GARBLE_RUNS = 3


def _answer_text(rec: dict) -> str:
    scheme = rec.get("answerScheme") or {}
    points = " ".join(str(p.get("description") or "") for p in scheme.get("markingPoints") or [])
    return f"{scheme.get('modelAnswer') or ''} {points}".strip()


def _first_answer(rec: dict) -> str:
    scheme = rec.get("answerScheme") or {}
    if (scheme.get("modelAnswer") or "").strip():
        return scheme["modelAnswer"].strip()
    points = scheme.get("markingPoints") or []
    return str(points[0].get("description") or "").strip() if points else ""


def _vowel_sign_runs(text: str) -> int:
    """Places where two dependent vowel signs sit side by side.

    In any Indic script a vowel sign (matra) attaches to a consonant, so two in a
    row never occur in correctly spelled text. Legacy-font extraction produces
    them constantly: "নিিো".

    Two cases that would otherwise be false positives, both handled:
      * only characters NAMED as vowel signs count. Visarga and anusvara are
        spacing/nonspacing marks too, and "दुःख" (Hindi,
        "sorrow") correctly puts visarga straight after a vowel sign.
      * the text is NFC-composed first. Bengali "ো" decomposes to two
        vowel signs (U+09C7 U+09BE); decomposed-but-correct text must not count.
    """
    runs = 0
    prev = False
    for ch in unicodedata.normalize("NFC", text):
        is_sign = "VOWEL SIGN" in unicodedata.name(ch, "")
        if is_sign and prev:
            runs += 1
        prev = is_sign
    return runs


def exclusion_reason(rec: dict) -> str | None:
    """Why this CBE/SQP record cannot be served, or None if it can."""
    meta = rec.get("metadata") or {}
    stem = str(rec.get("stem") or "").strip()
    passage = str(meta.get("passage") or "").strip()
    if meta.get("needsFigure"):
        return "figure-unavailable"
    if rec.get("source") == "cbse_question_bank" and rec.get("subject") == "English" and not passage:
        # Every CBE English item is read against a text; without it none can be answered.
        return "passage-unavailable"
    if not passage and _PASSAGE_REF.search(stem) and len(stem) < 400:
        return "passage-unavailable"
    if _HEADER.match(stem):
        return "header-as-stem"
    if len(stem) < _MIN_STEM:
        return "stem-too-short"
    if _vowel_sign_runs(stem) >= _GARBLE_RUNS:
        return "garbled-script"
    answer = _answer_text(rec)
    if not answer:
        return "no-answer"
    if _INSTRUCTION.match(_first_answer(rec)):
        return "answer-is-question-text"
    marks = rec.get("marks") if _is_num(rec.get("marks")) else 1
    if len(answer) > max(600, 450 * max(int(marks), 1)):
        return "answer-bleed"
    return None


# --------------------------------------------------------------------------- #
# MCQs
# --------------------------------------------------------------------------- #

_PART_OPTION = re.compile(r"^\s*\(?([A-Da-d])\)?\s*[.)–—:\-]\s*(.*)$", re.S)
_LEADING_LETTER = re.compile(r"^\s*\(?([A-Da-d])\)?\s*(?:[.)–—:\-]|$)")
_LABEL = re.compile(r"(?<![A-Za-z])([A-D])\s*[.)–—:\-]")
_INLINE_OPTION = re.compile(r"\(([A-Da-d])\)\s*")
# "(1)", "(1 mark)" after an answer is the mark column, not part of the answer.
_MARK_NOTE = re.compile(r"(?:\s+\(\s*(?:\d+|½)\s*(?:marks?)?\s*\))+\s*$", re.I)
# "3" alone may be the number of option (3) in a numbered list, not option text.
_BARE_NUMERAL = re.compile(r"^\(?[1-4]\)?\.?$")
_DASHES = str.maketrans(dict.fromkeys("−–—‐‑", "-"))
_TOKEN = re.compile(r"\w+|[^\w\s,.;:'\"‘’“”]")


def _norm(text: str) -> str:
    return " ".join(re.findall(r"\w+", (text or "").lower()))


def _tokens(text: str) -> list[str]:
    """Words and symbols, keeping everything `_norm` throws away.

    `_norm` reads "-48" and "48" alike, "2(x + y)" and "2(x – y)" alike, and
    in Indic text drops every vowel sign (they are not \\w). That is fine for
    finding a candidate and wrong for deciding one: in 15 of the served CBE
    MCQs a wrong option differs from the right one only by a sign, an operator
    or a bracket (measured 2026-09-21). Here signs, brackets and matras are
    tokens; commas, full stops and quotes are not, so "(2x+3), (3x-2)" still
    reads as "(2x+3) (3x-2)".
    """
    t = unicodedata.normalize("NFKC", _MARK_NOTE.sub("", text or ""))
    return _TOKEN.findall(t.casefold().translate(_DASHES).replace("&", " and "))


def _contains(hay: list[str], needle: list[str]) -> bool:
    n = len(needle)
    return 0 < n <= len(hay) and any(hay[i:i + n] == needle for i in range(len(hay) - n + 1))


def _named_option(words: list[str], options: dict[str, str]) -> str | None:
    """The one option these words name, or None when they name none or several.

    An exact reading wins. Failing that the words may quote part of an option,
    or carry one with something trailing ("... II is false SECTION-B") -- but
    only one option may fit.
    """
    toks = {k: _tokens(v) for k, v in options.items()}
    exact = [k for k, t in toks.items() if t == words]
    if exact:
        return exact[0] if len(exact) == 1 else None
    near = [k for k, t in toks.items() if t and (_contains(words, t) or _contains(t, words))]
    return near[0] if len(near) == 1 else None


def _answerable(options: dict[str, str]) -> bool:
    """Every option has text and no two read alike.

    Two options that read alike mean extraction lost what told them apart --
    cbe:q:Maths10AS4 prints 34, 34, 35, 35 with the key on the second 34 -- so
    the printed item is defective even where the key happens to be distinct.
    """
    read = [tuple(_tokens(v)) for v in options.values()]
    return all(read) and len(set(read)) == len(read)


def _options_from_parts(parts: list[dict]) -> dict[str, str] | None:
    """{'A': 'avoid', ...} from CBE/SQP option parts, or None if they are not A-D in order."""
    opts: dict[str, str] = {}
    for part in parts:
        m = _PART_OPTION.match(str(part.get("text") or ""))
        if not m:
            return None
        letter = m.group(1).upper()
        if letter in opts:
            return None
        # Text that opens with the NEXT option's label is two options fused in
        # extraction ("C. D. 7", cbe:q:Maths9IM4). Only the next label counts:
        # assertion-reason options legitimately open "(A) is correct but ...".
        if re.match(rf"\(?{chr(ord(letter) + 1)}[.)]\s", m.group(2)):
            return None
        opts[letter] = m.group(2).strip()
    if len(opts) < 2 or list(opts) != list("ABCD"[: len(opts)]):
        return None
    return opts


def _options_from_stem(stem: str) -> dict[str, str] | None:
    """Options already written inline as (A)..(D) -- the board and most SQP shape."""
    matches = list(_INLINE_OPTION.finditer(stem))
    labels = [m.group(1).upper() for m in matches]
    if len(labels) < 2 or labels != list("ABCD"[: len(labels)]):
        return None
    return {labels[i]: stem[m.end(): matches[i + 1].start() if i + 1 < len(matches) else len(stem)]
            .strip(" .;") for i, m in enumerate(matches)}


def correct_letter(answers: list[str], options: dict[str, str]) -> str | None:
    """The correct option, only when the scheme states it unambiguously.

    Refuses rather than guesses. Two failure shapes are common in the SQP
    schemes and both would yield a confident wrong key if read loosely:
    a matching-question key ("A - III; B - IV; ..."), and question text that
    the scheme parser joined in place of the answer ("modernity A. 1 & 3 B. ...",
    "Read the following data and select ..."). A wrong key is worse than none:
    a teacher trusts it and marks students wrong.

    A letter is not enough on its own either. When the scheme writes words after
    it, those words must name the same option. Taking the letter alone shipped
    keys the scheme itself contradicts -- "A. 243" where 243 is option C,
    "C. Melt" where Melt is option D -- and letters for items that were never
    MCQs ("(a) Na2CO3 (1) (b) ..." is a two-part answer, not option A).
    """
    for raw in answers:
        text = _AWARD.sub("", raw or "").strip()
        if not text:
            continue
        if len(set(_LABEL.findall(text))) >= 2 or _INSTRUCTION.match(text):
            return None
        m = _LEADING_LETTER.match(text)
        if m:
            letter = m.group(1).upper()
            if letter not in options:
                return None
            words = _tokens(text[m.end():])
            if words and _named_option(words, options) != letter:
                return None
            return letter
        if _BARE_NUMERAL.match(text):
            return None
        hits = [k for k, v in options.items() if _norm(v) and _norm(v) == _norm(text)]
        if len(hits) == 1 and _tokens(options[hits[0]]) == _tokens(text):
            return hits[0]
        return None
    return None


def _objective_scheme(rec: dict, options: dict[str, str], letter: str) -> dict:
    """The same objective scheme a board MCQ carries, via the same builder."""
    old = rec.get("answerScheme") or {}
    marks = int(rec["marks"])
    scheme = build_official_scheme(
        OfficialAnswer(q_no=0, correct_option=letter, answer_text=options[letter], marks=marks),
        marks=marks, question_id=rec["id"],
        code=str(old.get("sourcePaperCode") or ""),
        document_id=str(old.get("sourceDocumentId") or ""),
        options=options,
    )
    return scheme.model_dump(mode="json", by_alias=True)


# --------------------------------------------------------------------------- #
# normalisation
# --------------------------------------------------------------------------- #

def _normalise_scheme(scheme: dict, marks: int, record_id: str) -> dict:
    s = dict(scheme)
    s["totalMarks"] = int(s.get("totalMarks") or marks)
    points = []
    for i, mp in enumerate(s.get("markingPoints") or []):
        points.append({
            **mp,
            "id": str(mp.get("id") or f"{record_id}:mp{i + 1}"),
            "description": str(mp.get("description") or ""),
            "marks": int(mp.get("marks") or 0),
            "keyword": str(mp.get("keyword") or ""),
            "isRequired": bool(mp.get("isRequired", False)),
            "synonyms": [str(x) for x in (mp.get("synonyms") or [])],
        })
    s["markingPoints"] = points
    s["rubricLevels"] = [r for r in (s.get("rubricLevels") or []) if isinstance(r, dict)]
    s["commonErrors"] = [str(x) for x in (s.get("commonErrors") or [])]
    s["alternativeAnswers"] = [str(x) for x in (s.get("alternativeAnswers") or [])]
    s["modelAnswer"] = str(s.get("modelAnswer") or "")
    s["modelAnswerLatex"] = str(s.get("modelAnswerLatex") or "")
    s["hasPartialCredit"] = bool(s.get("hasPartialCredit", len(points) > 1))
    s["metadata"] = dict(s.get("metadata") or {})
    return s


def _normalise_part(part: dict, index: int, record_id: str) -> dict:
    p = dict(part)
    p["id"] = str(p.get("id") or f"{record_id}:p{index + 1}")
    p["partNumber"] = int(p.get("partNumber") or index + 1)
    p["text"] = str(p.get("text") or "")
    p["textLatex"] = str(p.get("textLatex") or "")
    p["marks"] = int(p.get("marks") or 0)
    if p.get("answerType") not in ANSWER_TYPES:
        p["answerType"] = "textShort"
    p["alternativeAnswers"] = [str(x) for x in (p.get("alternativeAnswers") or [])]
    return p


def normalise(rec: dict) -> tuple[dict, str | None]:
    """A new record that satisfies the phone's contract, or a reason it cannot.

    Values that had to be supplied are marked `metadata.<field>Inferred`, so an
    inferred Bloom level is never readable as one CBSE authored.
    """
    r = copy.deepcopy(rec)
    meta = dict(r.get("metadata") or {})
    scheme = r.get("answerScheme") or {}
    marks = r.get("marks") if _is_num(r.get("marks")) else scheme.get("totalMarks")
    marks = int(marks) if _is_num(marks) and marks > 0 else 1
    r["marks"] = marks

    if r.get("bloomLevel") not in BLOOM_LEVELS:
        r["bloomLevel"] = _resolve_bloom(None)
        meta["bloomInferred"] = True
    if r.get("type") not in QUESTION_TYPES:
        r["type"] = _resolve_type(r.get("type"), marks)
        meta["typeInferred"] = True
    if r.get("difficulty") not in DIFFICULTIES:
        r["difficulty"] = _resolve_difficulty(marks, r["bloomLevel"])
        meta["difficultyInferred"] = True

    for key in ("chapterIds", "competencyIds", "tags"):
        r[key] = [str(x) for x in (r.get(key) or [])]
    r["stem"] = str(r.get("stem") or "").strip()
    r["stemLatex"] = str(r.get("stemLatex") or "")
    r["language"] = str(r.get("language") or "en")
    r["questionBankId"] = str(r.get("questionBankId") or r.get("source") or "unknown")
    if not _is_num(r.get("estimatedTimeMinutes")):
        r["estimatedTimeMinutes"] = max(1, marks * 2)
    if not _is_num(r.get("qualityScore")):
        r["qualityScore"] = 0.7
    for key in ("createdAt", "updatedAt"):
        if not _is_iso(r.get(key)):
            r[key] = "2026-01-01T00:00:00+00:00"
    r["parts"] = [_normalise_part(p, i, r["id"]) for i, p in enumerate(r.get("parts") or [])]
    r["answerScheme"] = _normalise_scheme(scheme, marks, r["id"])

    passage = str(meta.get("passage") or "").strip()
    if passage:
        r["stem"] = f"Read the passage below and answer the question that follows.\n\n{passage}\n\n{r['stem']}"
        meta["passageInline"] = True

    if r["type"] == "mcq":
        options = _options_from_stem(r["stem"]) or _options_from_parts(r["parts"])
        if options is None or not _answerable(options):
            return r, "mcq-options-unresolved"
        letter = correct_letter(
            [r["answerScheme"]["modelAnswer"]]
            + [mp["description"] for mp in r["answerScheme"]["markingPoints"]],
            options)
        if letter is None:
            return r, "mcq-answer-unresolved"
        if _options_from_stem(r["stem"]) is None:
            r["stem"] = r["stem"] + " " + " ".join(f"({k}) {v}" for k, v in options.items())
        r["parts"] = []            # options live inline, as on every board MCQ
        r["answerScheme"] = _normalise_scheme(_objective_scheme(r, options, letter), marks, r["id"])

    r["metadata"] = meta
    return r, None


# --------------------------------------------------------------------------- #
# composition
# --------------------------------------------------------------------------- #

@dataclass
class ComposeResult:
    questions: list[dict]
    excluded: list[dict] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)


def _excluded(rec: dict, reason: str) -> dict:
    return {"id": rec.get("id"), "source": rec.get("source"), "reason": reason,
            "subject": rec.get("subject"), "grade": rec.get("grade"),
            "stem": str(rec.get("stem") or "")[:200]}


def compose(served: list[dict], cbe: list[dict], sqp: list[dict]) -> ComposeResult:
    """Board records from `served`, then CBE, then SQP.

    Non-board rows already in `served` are ignored and rebuilt from their source
    files, so running the merge twice gives the same bank. A normalised record
    that still breaks the contract raises ContractError and nothing is written.
    """
    out: list[dict] = []
    excluded: list[dict] = []
    seen_ids: set[str] = set()
    seen_stems: set[tuple] = set()
    counts = {"board": 0, "cbe": 0, "sqp": 0}

    for rec in served:
        if rec.get("source") != BOARD_SOURCE:
            continue
        errors = contract_errors(rec)
        if errors:
            raise ContractError(str(rec.get("id")), errors)
        out.append(rec)
        seen_ids.add(rec["id"])
        seen_stems.add((rec.get("subject"), rec.get("grade"), _norm(rec.get("stem", ""))))
        counts["board"] += 1

    for label, rows in (("cbe", cbe), ("sqp", sqp)):
        for raw in rows:
            if raw.get("id") in seen_ids:
                excluded.append(_excluded(raw, "duplicate-id"))
                continue
            reason = exclusion_reason(raw)
            if reason:
                excluded.append(_excluded(raw, reason))
                continue
            rec, reason = normalise(raw)
            if reason:
                excluded.append(_excluded(raw, reason))
                continue
            key = (rec.get("subject"), rec.get("grade"), _norm(raw.get("stem", "")))
            if key in seen_stems:
                excluded.append(_excluded(raw, "duplicate-stem"))
                continue
            errors = contract_errors(rec)
            if errors:
                raise ContractError(str(rec.get("id")), errors)
            out.append(rec)
            seen_ids.add(rec["id"])
            seen_stems.add(key)
            counts[label] += 1

    return ComposeResult(questions=out, excluded=excluded, counts=counts)
