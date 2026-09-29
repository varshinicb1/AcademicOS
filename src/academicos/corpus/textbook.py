"""NCERT textbook exercises, with answers that were checked before they are
served (docs/textbook-exercise-format.md).

Classes 1-10 textbooks print their exercises and, apart from some Mathematics
answer pages, no answers. A transcriber writes each chapter's questions with an
answer that says where it comes from; this module keeps only what it can check:

  book       the book prints the answer                -> ncert_textbook_answer
  grounded   every value point quotes the chapter, and the quote is found in
             the chapter's own text layer               -> textbook_grounded
  solved     worked out (sums, grammar, meanings) and the final answer agrees
             with an independent second solve           -> two_model_solved
  open       no single answer (discuss, find out, draw) -> never keyed

and refuses the rest with the reason. The question itself must be found in the
chapter's text (`stem-not-in-book`): the questions are the book's, never the
transcriber's.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Optional

from .transcribed import SchemeText

# The marks a question of each type usually carries in a CBSE paper; flagged
# `marksInferred`, since a textbook prints none.
MARKS = {"mcq": 1, "true_false": 1, "fill_blank": 1, "very_short_answer": 1, "match": 2,
         "short_answer": 2, "long_answer": 5, "case_based": 4}
BANK_TYPE = {"mcq": "mcq", "true_false": "very_short_answer", "fill_blank": "very_short_answer",
             "very_short_answer": "very_short_answer", "match": "short_answer", "short_answer": "short_answer",
             "long_answer": "long_answer", "case_based": "case_study"}
PROVENANCE = {"book": "ncert_textbook_answer", "grounded": "textbook_grounded", "solved": "two_model_solved"}
LETTERS = ("A", "B", "C", "D")


class BookText(SchemeText):
    """A chapter's text layer, searched like a scheme's. Devanagari is kept:
    Hindi books are checked in their own script."""

    @classmethod
    def of(cls, raw: str) -> "BookText":
        t = _norm(raw)
        book = cls(t, frozenset(t.split()))
        book.compact = t.replace(" ", "")
        return book

    def verbatim(self, needle: str) -> bool:
        """`needle` word for word in the chapter. Spacing is ignored, so a word
        the PDF split across a line ("hemi-" / "spheres") still matches; a
        paraphrase does not."""
        n = _norm(needle)
        return bool(n) and (n in self.text or n.replace(" ", "") in self.compact)


def _norm(s: Any) -> str:
    s = unicodedata.normalize("NFC", str(s or "")).lower()
    return re.sub(r"[^a-z0-9ऀ-ॿ]+", " ", s).strip()


def _has(book: BookText, needle: str) -> bool:
    n = _norm(needle)
    if not n or n in book.text:
        return True
    words = n.split()
    if len(words) <= 3:
        return all(w in book.words for w in words)
    return sum(1 for w in words if w in book.words) / len(words) >= 0.85 and _longest_run(n, book.text) >= min(
        len(n) * 0.5, 40)


def _longest_run(a: str, b: str) -> int:
    from difflib import SequenceMatcher
    return SequenceMatcher(None, a, b, autojunk=False).find_longest_match(0, len(a), 0, len(b)).size


def final_answer_key(s: Any) -> str:
    """A final answer reduced to what two solves must agree on: its numbers
    when it has any ("x = 15 cm", "15km" and "15" agree; units and words are
    how a solver phrased it), else its words, case and spacing ignored."""
    raw = unicodedata.normalize("NFC", str(s or ""))
    nums = re.findall(r"-?\d+(?:\.\d+)?(?:/\d+)?", raw.replace(",", ""))
    if nums:
        return ",".join(nums)
    return _norm(raw).replace(" ", "")


def refusal(q: dict, book: BookText, second: Optional[dict[str, str]]) -> Optional[str]:
    a = q.get("answer") or {}
    src = a.get("source")
    if q.get("needsFigure"):
        return "figure-unavailable"
    if src == "open":
        return "generated-open" if q.get("origin") == "generated" else "open-ended"
    # A book question must be the book's; a generated one is new by design, and
    # stands on its answer alone (grounded or solved, checked below).
    if q.get("origin") != "generated" and not _has(book, str(q.get("stem") or "")):
        return "stem-not-in-book"
    if q.get("type") == "mcq":
        opts = q.get("options") or {}
        if sorted(opts) != list(LETTERS):
            return "options-missing"
        if a.get("correctOption") not in LETTERS:
            return "mcq-answer-unresolved"
    if src == "grounded":
        points = a.get("points") or []
        if not points:
            return "no-answer"
        if not all(book.verbatim(str(p.get("evidence") or "")) for p in points):
            return "evidence-not-found"
        return None
    if src == "solved":
        if not str(a.get("finalAnswer") or "").strip() and a.get("correctOption") is None:
            return "no-answer"
        if second is None or q.get("ref") not in second:
            return "solve-unchecked"
        mine = a.get("correctOption") or a.get("finalAnswer")
        if final_answer_key(mine) != final_answer_key(second[q["ref"]]):
            return "solve-disagrees"
        return None
    if src == "book":
        return None if (a.get("points") or a.get("finalAnswer") or a.get("correctOption")) else "no-answer"
    return "no-answer"


BLOOMS = ("remember", "understand", "apply", "analyze", "evaluate", "create")
DIFFICULTIES = ("easy", "medium", "hard")


def _slug(s: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(s or "").lower()).strip("-")


def record(q: dict, tb: dict, *, rid: str, built_at: str) -> dict:
    book, chapter = tb.get("book") or {}, tb.get("chapter") or {}
    topics = {t.get("id"): t for t in tb.get("topics") or []}
    topic = topics.get(q.get("topic")) or {}
    generated = q.get("origin") == "generated"
    a = q.get("answer") or {}
    qtype = str(q.get("type") or "short_answer")
    marks = MARKS.get(qtype, 2)
    stem = " ".join(str(q.get("stem") or "").split())
    parts = [{"partNumber": i + 1, "text": f"{p.get('label') or ''} {p.get('text') or ''}".strip(), "marks": 0}
             for i, p in enumerate(q.get("parts") or [])]
    if qtype == "mcq":
        opts = q["options"]
        stem += " " + " ".join(f"({k}) {' '.join(str(opts[k]).split())}" for k in LETTERS)
        letter = a["correctOption"]
        points = [{"description": f"Correct option {letter}: {opts[letter]}", "marks": 1, "keyword": str(opts[letter]),
                   "isRequired": True, "synonyms": [letter]}]
        model, parts = f"({letter}) {opts[letter]}", []
    else:
        texts = [str(p.get("text") or "").strip() for p in a.get("points") or [] if str(p.get("text") or "").strip()]
        if not texts and a.get("finalAnswer"):
            texts = [str(a["finalAnswer"]).strip()]
        per = max(1, marks // max(1, len(texts))) if texts else marks
        points = [{"description": t, "marks": per, "keyword": "", "isRequired": True, "synonyms": []}
                  for t in texts[:marks] or texts[:1]]
        if points:
            points[-1]["marks"] = marks - per * (len(points) - 1)
        model = "\n".join(texts)
        if a.get("working"):
            model = f"{model}\n\nWorking: {a['working']}".strip()
    evidence = [{"quote": p.get("evidence"), "page": p.get("page")} for p in a.get("points") or [] if p.get("evidence")]
    return {
        "id": rid,
        "questionBankId": f"ncert-textbook:{book.get('code')}",
        "subject": book.get("subject"),
        "grade": int(book.get("class")),
        "chapterIds": [_slug(chapter.get("title"))] if chapter.get("title") else [],
        "topic": str(topic.get("title") or ""),
        "difficulty": q.get("difficulty") if q.get("difficulty") in DIFFICULTIES else "medium",
        **({"bloomLevel": q["bloom"]} if q.get("bloom") in BLOOMS else {}),
        "type": BANK_TYPE.get(qtype, "short_answer"),
        "stem": stem,
        "stemLatex": "",
        "parts": parts,
        "answerScheme": {
            "totalMarks": marks, "markingPoints": points, "rubricLevels": [], "commonErrors": [],
            "alternativeAnswers": [], "modelAnswer": model, "modelAnswerLatex": "",
            "hasPartialCredit": len(points) > 1,
            "metadata": {"answerSource": a.get("source"), "evidence": evidence,
                         **({"objective": True, "options": q["options"], "correctOption": a["correctOption"]}
                            if qtype == "mcq" else {})},
            "provenance": PROVENANCE[a["source"]],
            "sourcePaperCode": "", "sourceDocumentId": f"ncert-textbook:{book.get('code')}",
        },
        "estimatedTimeMinutes": max(1, marks * 2),
        "marks": marks,
        "language": "hi" if book.get("language") == "hi" else "en",
        # A question written for the topic is the generator's, never passed off as the book's.
        "source": "ai_generated" if generated else "ncert_textbook",
        "qualityScore": 0.8 if generated else 0.85,
        "tags": ["ncert", "generated" if generated else "textbook", str(book.get("title") or "")],
        "createdAt": built_at,
        "updatedAt": built_at,
        "metadata": {"questionKey": q.get("ref"), "bookCode": book.get("code"), "bookTitle": book.get("title"),
                     "chapterNumber": chapter.get("number"), "chapterName": chapter.get("title"),
                     "page": q.get("page"), "marksInferred": True,
                     # The book prints no difficulty; a generated question's is its writer's.
                     "difficultyInferred": not (generated and q.get("difficulty") in DIFFICULTIES),
                     "bloomInferred": q.get("bloom") not in BLOOMS,
                     "topicId": q.get("topic"), "topicTitle": topic.get("title"),
                     "origin": "generated" if generated else "book",
                     "joinedFrom": "textbook-transcription",
                     **({"passage": str(q["passage"]).strip()} if q.get("passage") else {})},
    }


@dataclass
class Built:
    records: list[dict]
    refused: list[dict]


def build(tb: dict, book_text: str, *, second: Optional[dict[str, str]] = None,
          built_at: str = "2026-09-29T00:00:00+00:00") -> Built:
    """Every checked question of one chapter, and every refusal with its reason.
    `second` maps a question's `ref` to an independent second solve's answer."""
    book, chapter = tb.get("book") or {}, tb.get("chapter") or {}
    text = BookText.of(book_text)
    records, refused, seen = [], [], set()
    for i, q in enumerate(tb.get("questions") or []):
        ref = re.sub(r"[^A-Za-z0-9.]+", "-", str(q.get("ref") or i + 1)).strip("-")
        rid = f"ncert:tb:{book.get('code')}:{int(chapter.get('number') or 0):02d}:{ref}"
        while rid in seen:
            rid += "b"
        seen.add(rid)
        reason = refusal(q, text, second)
        if reason:
            refused.append({"id": rid, "reason": reason})
            continue
        records.append(record(q, tb, rid=rid, built_at=built_at))
    return Built(records, refused)
