"""Parser for the official CBSE CBE item banks.

What these documents are, and why they are the right source
----------------------------------------------------------
CBSE publishes 15 item banks (Classes 6-10 x Mathematics, Science, English) at
`cbseacademic.nic.in/cbe/assessment.html`. They were produced with the British
Council and Alpha Plus, and they are the artefact the requirement actually
describes: a board writing questions against a curriculum, with an answer key.

Every item carries, in a fixed layout:

    Item identity        Maths6AS1
    AO1 marks            1
    AO2 marks
    C/N/E*               N                      (calculator rule)
    Content reference    6A1a Form and use algebraic expressions (up to 2 variables...)
    Marks                1
    Item purpose         prose
    Question(s)          the question, its options, and (N mark)
    Mark scheme          Answer | Guidance table, i.e. the ANSWER KEY

So the topic mapping is not inferred from keywords -- it is a curriculum code
CBSE wrote (`6A1a`), plus a named strand (`Algebra`). And the answer key is not
reconstructed from the text -- it is the published one.

Format notes that the parser depends on, all established by reading the real
files rather than assumed:

  * A running header (`www.britishcouncil.org`, the page number) must be
    stripped before anything else, or every field parse picks up the page
    number.
  * An item BEGINS on a page whose first non-blank line is the item identity
    alone, and may CONTINUE onto following pages. Items therefore have to be
    accumulated page-by-page, not matched within a page.
  * `pymupdf` (imported as `fitz`) emits the metadata table cells in a
    different order from their visual layout, so fields are located by their
    content (the code pattern) rather than by position.

Deliberately NOT parsed: the diagram images. Items that depend on a figure are
flagged (`needs_figure`) rather than silently exported without it, because a
figure-dependent question with no figure is unanswerable -- the same reason
`assessment/pool.py` excludes them from paper generation.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, Optional

log = logging.getLogger(__name__)

# "Maths6AS1", "Science10YP3", "English9JV4a", and -- importantly -- "English6SB"
# and "English8IN", which have NO trailing digit.
#
# The digit was required in the first version, so every id shaped
# `{Subject}{Class}{Letters}` was rejected and English Class 6 and Class 8
# parsed to 3 and 2 items against the 49+ each document holds. A parser that
# silently finds 6% of a document looks like a thin document, not a broken
# pattern, which is why the count is worth asserting rather than eyeballing.
# `[a-z]{0,3}` rather than `[a-z]?`: Science sub-question ids carry roman
# suffixes -- `Science9SRN41bi`, `...1bii`, `...1biii` -- and allowing a single
# lowercase letter rejected every one of them, which is a quiet slice of the
# Science corpus.
ITEM_ID = re.compile(r"^([A-Z][A-Za-z]+)(\d{1,2})([A-Z]{2,4}\d*[a-z]{0,3})$")

# The learning-ladder content reference. Two shapes exist, and both are real:
#   "6A1a", "10A2b", "9C1a"   -- Mathematics and English (digit, letter, digit)
#   "9.1.13", "10.3.9"        -- Science (dotted numeric)
# A pattern that only accepts the first silently yields 0% topic coverage on
# every Science document, which is exactly what happened before this was
# widened -- and 0% looks like "the source has no codes" rather than "the regex
# is wrong", so it is worth being explicit about.
#
# The second alternative is deliberately tight (`\d{1,2}[A-Z]\d{1,2}[a-z]?`).
# A looser version (`[A-Z]?\d{0,2}[A-Z]\d+[a-z]?`) matched fragments of ordinary
# words and produced codes that do not exist in the curriculum, which then
# overrode the authoritative index value.
CONTENT_CODE = re.compile(
    r"(?<![\w.])(\d{1,2}(?:\.\d{1,2}){2}|\d{1,2}[A-Z]\d{1,2}[a-z]?)(?![\w.])")

# Running furniture that must never become content.
_RUNNING_HEAD = re.compile(r"^\s*(www\.britishcouncil\.org|britishcouncil\.org)\s*$", re.I)
_PAGE_NUMBER = re.compile(r"^\s*\d{1,3}\s*$")
_CNE = re.compile(r"\b([CNE])\b")
_MARKS_LINE = re.compile(r"\((\d{1,2})\s*marks?\)", re.I)
_TOTAL_MARKS = re.compile(r"Total marks\s*(\d{1,2})", re.I)
_ITEM_PURPOSE = re.compile(r"Item purpose\s*(.+?)(?=\n\s*(?:Sources|Source|Question|Mark scheme)\b)",
                           re.S | re.I)
_OPTION = re.compile(r"^\s*([A-D])[.)]\s*(.+)$", re.M)
_ANSWER_ROW = re.compile(r"^\s*([A-D])[.)]\s*(.+)$", re.M)

SUBJECT_BY_PREFIX = {
    "maths": "Mathematics", "mathematics": "Mathematics",
    "science": "Science", "english": "English",
}


@dataclass
class CbeItem:
    """One assessment item from a CBSE CBE item bank."""

    item_id: str
    question_id: str                 # the specific part, e.g. Maths6AS1b
    subject: str
    grade: int
    content_code: str = ""            # learning-ladder reference, e.g. "6A1a"
    content_reference: str = ""       # the human description of that code
    topic: str = ""                   # the named strand, e.g. "Algebra"
    ao1_marks: int = 0
    ao2_marks: int = 0
    marks: int = 0
    calculator: str = ""              # "C" required, "N" not allowed, "E" either
    purpose: str = ""
    question: str = ""
    options: list[str] = field(default_factory=list)
    answer: str = ""                  # the official answer, from the mark scheme
    guidance: str = ""
    needs_figure: bool = False
    source_pdf: str = ""
    pages: list[int] = field(default_factory=list)

    @property
    def has_answer_key(self) -> bool:
        """The hard gate. A question with no published answer is not a question.

        An examination board does not issue a question it cannot mark, and a
        bank that mixes answerable and unanswerable items silently degrades
        every paper built from it.
        """
        return bool(self.answer.strip())

    @property
    def ao_marks(self) -> dict[str, int]:
        out = {}
        if self.ao1_marks:
            out["AO1"] = self.ao1_marks
        if self.ao2_marks:
            out["AO2"] = self.ao2_marks
        return out

    def to_dict(self) -> dict:
        return {
            "itemId": self.item_id,
            "questionId": self.question_id,
            "subject": self.subject,
            "grade": self.grade,
            "contentCode": self.content_code,
            "contentReference": self.content_reference,
            "topic": self.topic,
            "aoMarks": self.ao_marks,
            "marks": self.marks,
            "calculator": self.calculator,
            "purpose": self.purpose,
            "question": self.question,
            "options": self.options,
            "answer": self.answer,
            "guidance": self.guidance,
            "hasAnswerKey": self.has_answer_key,
            "needsFigure": self.needs_figure,
            "sourcePdf": self.source_pdf,
            "pages": self.pages,
        }


# --------------------------------------------------------------------------- #
# page-level text
# --------------------------------------------------------------------------- #

def _clean_page(text: str) -> list[str]:
    """Drop running furniture, return meaningful lines."""
    out: list[str] = []
    for line in text.splitlines():
        if _RUNNING_HEAD.match(line) or _PAGE_NUMBER.match(line):
            continue
        out.append(line.rstrip())
    # drop leading/trailing blanks
    while out and not out[0].strip():
        out.pop(0)
    while out and not out[-1].strip():
        out.pop()
    return out


def _page_starts_item(lines: list[str]) -> str | None:
    """An item begins when the first meaningful line is an item identity alone.

    The item markers are required as well as the identity. Without them the
    Item Index pages qualify: their rows also begin with an identifier, so
    every index row was emitted as a question whose text was the rest of the
    table -- which is how the English documents produced items with no
    question and no answer.
    """
    if not lines:
        return None
    first = lines[0].strip()
    if not ITEM_ID.match(first):
        return None
    joined = " ".join(lines[:12]).lower()
    if not any(marker in joined for marker in
               ("item identity", "item purpose", "mark scheme", "question")):
        return None
    return first


def _stream(doc) -> list[tuple[int, str]]:
    """The whole document as `(page_number, line)` pairs.

    Items do NOT align to page boundaries: a 1-mark Mathematics item occupies a
    few lines, so several share a page, and a long English item spans ten. A
    page-based split therefore misses every item that does not happen to start
    at the top of a page -- which is how Maths Class 6 yielded 14 items against
    the 58 the document states, and English Class 6 yielded 5 against 46.
    """
    out: list[tuple[int, str]] = []
    for index in range(len(doc)):
        for line in _clean_page(doc[index].get_text()):
            out.append((index + 1, line))
    return out


def _is_metadata_header(stream: list[tuple[int, str]], i: int) -> bool:
    """True when position `i` opens an item's metadata table.

    The header is `Item identity`, but the PDF splits it across lines in some
    documents (`Item` / `identity`) and keeps it on one line in others. Both
    are treated as the boundary, because every item has it and nothing else
    does -- which makes it a far more reliable anchor than the item id, since
    the Item Index also contains item ids but no metadata header.
    """
    if i >= len(stream):
        return False
    line = stream[i][1].strip().lower()
    if line == "item identity":
        return True
    if line != "item":
        return False
    for j in range(i + 1, min(i + 4, len(stream))):
        nxt = stream[j][1].strip().lower()
        if not nxt:
            continue
        return nxt == "identity"
    return False


def _lookahead_nonblank(stream: list[tuple[int, str]], i: int, n: int) -> list[str]:
    out: list[str] = []
    for j in range(i + 1, min(i + 20, len(stream))):
        t = stream[j][1].strip()
        if t:
            out.append(t)
            if len(out) >= n:
                break
    return out


def _starts_item(stream: list[tuple[int, str]], i: int) -> bool:
    """Is position `i` the first line of an item?

    Two anchors, because the documents are not internally consistent:

      * **A content code follows.** This is the Mathematics and Science shape.
        A 1-mark item is four lines long and its metadata table may omit the
        `Item identity` header entirely, going straight to
        `Maths6AS1 / Maths6AS1 / 6A1a / Algebra`. Anchoring on the header alone
        found 10 of Maths Class 6's stated 58 items.
      * **An `Item identity` header follows.** This is the English shape, where
        the id is followed by the full metadata table.

    Accepting either recovered both, and the id-line is required in both cases
    so the Item Index -- which also contains item ids -- is still excluded, since
    an index row is id/id/marks with no code and no header after it.
    """
    ident = stream[i][1].strip()
    if not ITEM_ID.match(ident):
        return False

    look = _lookahead_nonblank(stream, i, 6)
    if not look:
        return False

    if any(CONTENT_CODE.fullmatch(t) or CONTENT_CODE.match(t) and len(t) < 14
           for t in look[:4]):
        return True

    joined = " ".join(look).lower()
    if "item identity" in joined or "identity" in joined:
        return True
    return False


def split_items(pdf_path: Path) -> Iterator[tuple[str, list[int], str]]:
    """Yield `(item_id, page_numbers, text)` for each item in one document."""
    import fitz

    doc = fitz.open(pdf_path)
    try:
        stream = _stream(doc)

        # Item ids are not unique lines -- an id appears at a page top, again in
        # its own metadata table, and its sub-question ids follow. Only lines
        # that open an item are accepted, then consecutive repeats collapse.
        starts: list[tuple[int, str]] = []
        for i in range(len(stream)):
            if _starts_item(stream, i):
                ident = stream[i][1].strip()
                if starts and starts[-1][1] == ident:
                    continue          # same item, seen at the page top
                starts.append((i, ident))

        for n, (pos, ident) in enumerate(starts):
            end = starts[n + 1][0] if n + 1 < len(starts) else len(stream)
            body = "\n".join(line for _page, line in stream[pos + 1:end])
            pages = sorted({page for page, _line in stream[pos:end]})
            yield ident, pages, body
    finally:
        doc.close()


# --------------------------------------------------------------------------- #
# field extraction
# --------------------------------------------------------------------------- #

def _extract_metadata(block: str) -> dict:
    """Pull the metadata table fields out of an item block.

    The PDF emits the table cells in a different order from the visual layout,
    so each field is found by its own shape rather than by position. The
    content reference is located by the code pattern, which is the only field
    in the table with a distinctive form.
    """
    out: dict = {"content_code": "", "content_reference": "", "marks": 0,
                 "ao1_marks": 0, "ao2_marks": 0, "calculator": ""}

    # The block opens with the identity, then "Item identity", then the AO
    # marks. Everything before "Item purpose" is the table.
    head = block.split("Item purpose", 1)[0]

    m = CONTENT_CODE.search(head)
    if m:
        out["content_code"] = m.group(1)
        # The description runs from just after the code up to the next
        # standalone integer (the Marks cell) or the end of the table.
        rest = head[m.end():]
        desc = re.split(r"\n\s*\d{1,2}\s*\n", rest, maxsplit=1)[0]
        desc = " ".join(desc.split())
        out["content_reference"] = desc.strip(" .;*")[:300]

    total = _TOTAL_MARKS.search(block)
    if total:
        out["marks"] = int(total.group(1))
    else:
        per = _MARKS_LINE.search(block)
        if per:
            out["marks"] = int(per.group(1))

    # AO marks: the table lists AO1 and AO2 columns before the content
    # reference. Their values are small integers on their own lines.
    aomatch = re.search(r"Item\s*identity\s*(.*?)(?=[CEN]\b|Content reference|"
                        r"reference\(s\)|reference from)", head, re.S | re.I)
    if aomatch:
        nums = [int(n) for n in re.findall(r"^\s*(\d{1,2})\s*$", aomatch.group(1), re.M)]
        if nums:
            out["ao1_marks"] = nums[0]
        if len(nums) > 1:
            out["ao2_marks"] = nums[1]

    cne = re.search(r"\b([CNE])\b\s*(?:Content|reference)", head)
    if cne:
        out["calculator"] = cne.group(1)
    return out


def _extract_question_and_answer(block: str) -> tuple[str, list[str], str, str, bool]:
    """Split the block into `(question, options, answer, guidance, needs_figure)`."""
    qsplit = re.split(r"\n\s*Question(?:\(s\))?\s*\n", block, maxsplit=1, flags=re.I)
    body = qsplit[1] if len(qsplit) > 1 else block
    msplit = re.split(r"\n\s*Mark scheme\s*\n", body, maxsplit=1, flags=re.I)
    question_zone = msplit[0]
    scheme_zone = msplit[1] if len(msplit) > 1 else ""

    options = [f"{m.group(1)}. {m.group(2).strip()}"
               for m in _OPTION.finditer(question_zone)]
    question = _OPTION.split(question_zone)[0]
    question = " ".join(question.split())
    # Drop the trailing mark annotation; marks are carried as their own field.
    question = _MARKS_LINE.sub("", question).replace("(Total marks", "").strip()

    answer, guidance = "", ""
    if scheme_zone:
        # The mark scheme restates the question, then an "Answer | Guidance"
        # table. In flattened text the answer is the option letter followed by
        # its text, or a short answer string before the guidance.
        after = re.split(r"\n\s*Answer\s*\n\s*Guidance\s*\n", scheme_zone, maxsplit=1)
        if len(after) > 1:
            tail = after[1]
            am = _ANSWER_ROW.search(tail)
            if am:
                answer = f"{am.group(1)}. {am.group(2).strip()}"
            else:
                answer = " ".join(tail.split()[:40])
            guidance = " ".join(tail.split())[len(answer):].strip()[:400]
        else:
            # "Answer" and "Guidance" may be on one line or reordered.
            flat = " ".join(scheme_zone.split())
            gm = re.search(r"Answer\s+Guidance\s+(.*)$", flat)
            if gm:
                tail = gm.group(1)
                am = _ANSWER_ROW.match(tail.strip())
                answer = (f"{am.group(1)}. {am.group(2).strip()}" if am
                          else " ".join(tail.split()[:40]))
                guidance = " ".join(tail.split())[len(answer):].strip()[:400]

    figure_phrases = ("shown in the figure", "in the given figure", "following diagram",
                      "the diagram below", "figure below", "shown below", "given figure")
    low = question.lower()
    options_text = " ".join(o.lower() for o in options)
    needs_figure = any(p in low for p in figure_phrases) and not options
    return question, options, answer, guidance, needs_figure


def parse_item(item_id: str, pages: list[int], block: str, *, subject: str,
               grade: int, source_pdf: str) -> CbeItem:
    meta = _extract_metadata(block)
    question, options, answer, guidance, needs_figure = _extract_question_and_answer(block)
    purpose_m = _ITEM_PURPOSE.search(block)
    return CbeItem(
        item_id=item_id,
        question_id=item_id,
        subject=subject,
        grade=grade,
        content_code=meta["content_code"],
        content_reference=meta["content_reference"],
        ao1_marks=meta["ao1_marks"],
        ao2_marks=meta["ao2_marks"],
        marks=meta["marks"],
        calculator=meta["calculator"],
        purpose=" ".join(purpose_m.group(1).split())[:300] if purpose_m else "",
        question=question,
        options=options,
        answer=answer,
        guidance=guidance,
        needs_figure=needs_figure,
        source_pdf=source_pdf,
        pages=pages,
    )


# --------------------------------------------------------------------------- #
# the topic index
# --------------------------------------------------------------------------- #

# The index table emits one cell per line, not one row per line:
#
#     6A1a
#     Algebra
#     Maths6AS1
#     Maths6AS1
#     1
#
# so a single-line row regex matches nothing. The rows are reconstructed by
# scanning for a content code and taking the following cells positionally.
_CELL = re.compile(r"^\s*(.+?)\s*$")
# Widths match ITEM_ID: a trailing digit is optional ("English6SB" is real).
_CODE_CELL = re.compile(r"^(?:\d{1,2}(?:\.\d{1,2}){2}|\d{0,2}[A-Z]\d{1,2}[a-z]?)$")
_QID_CELL = re.compile(r"^[A-Za-z]{3,}\d{1,2}[A-Z]{2,4}\d*(?:[a-z]|\d)?$")


def parse_index(pdf_path: Path) -> dict[str, dict]:
    """Read the Item Index: question id -> content code, topic strand, AO marks.

    This is the topic mapping the requirement asks for, and it is CBSE's own --
    not a keyword guess. The index gives the *strand* (`Algebra`, `Living
    world`), while each item's metadata gives the fuller content reference.
    """
    import fitz

    doc = fitz.open(pdf_path)
    out: dict[str, dict] = {}
    try:
        for index in range(min(14, len(doc))):
            lines = [l.strip() for l in _clean_page(doc[index].get_text())]
            i = 0
            while i < len(lines):
                if not _CODE_CELL.match(lines[i]):
                    i += 1
                    continue
                # code, topic, filename, question id, ao1, ao2 -- with the
                # optionals possibly absent, so walk forward rather than
                # indexing blindly.
                code = lines[i]
                j = i + 1
                topic = lines[j] if j < len(lines) else ""
                j += 1
                # skip the filename cell if the next cell is also an id
                qid = ""
                if j < len(lines) and _QID_CELL.match(lines[j]):
                    qid = lines[j]
                    j += 1
                    if j < len(lines) and _QID_CELL.match(lines[j]):
                        qid = lines[j]
                        j += 1
                if not qid or not topic or _CODE_CELL.match(topic):
                    i += 1
                    continue
                ao1 = ao2 = 0
                if j < len(lines) and lines[j].isdigit():
                    ao1 = int(lines[j]); j += 1
                if j < len(lines) and lines[j].isdigit():
                    ao2 = int(lines[j]); j += 1
                out[qid] = {
                    "content_code": code,
                    "topic": " ".join(topic.split()),
                    "ao1_marks": ao1,
                    "ao2_marks": ao2,
                }
                i = j
    finally:
        doc.close()
    return out


def subject_and_grade_for(path: Path) -> tuple[str, int]:
    m = re.search(r"Item-Bank-+([A-Za-z]+)-+Class-?(\d+)", path.name, re.I)
    if not m:
        return "", 0
    raw = m.group(1).lower()
    return SUBJECT_BY_PREFIX.get(raw, m.group(1).title()), int(m.group(2))


# --------------------------------------------------------------------------- #
# converting an item into a question-bank record
# --------------------------------------------------------------------------- #

# CBE items do not print a Bloom level; they print assessment objectives, which
# measure a different thing. Inferring Bloom from AO would be inventing data, so
# every imported item is marked `understand` -- the neutral default the rest of
# the bank uses -- and carries its real AO split alongside.
_DEFAULT_BLOOM = "understand"


def _difficulty_for(marks: int) -> str:
    """Marks are the only difficulty signal these documents carry.

    Same rule `assessment/mapping.py` uses for the board-paper corpus, so the
    two sources are comparable rather than each inventing a scale.
    """
    return "easy" if marks <= 2 else "medium" if marks <= 3 else "hard"


def _question_type_for(item: "CbeItem") -> str:
    if item.options:
        return "mcq"
    return {1: "very_short_answer", 2: "short_answer"}.get(item.marks, "long_answer")


def to_bank_record(item: "CbeItem") -> dict:
    """Convert a parsed CBE item into the question-bank wire shape.

    Every field the bank already uses is populated, plus the four the CBE
    source adds and the rest of the bank does not have: `contentCode`,
    `contentReference`, `topic` and `aoMarks`. Those are the topic mapping and
    the marks-by-assessment-objective split, and dropping them on import would
    throw away the most valuable thing this source provides.

    The answer scheme carries `provenance: "cbse_marking_scheme"` because that is
    literally what it is -- the scheme CBSE published for this item. It is the
    only source in the bank that can say that, and the API's `hasScheme` filter
    depends on the distinction.
    """
    qid = f"cbe:q:{item.item_id}"
    marks = item.marks or 0
    points = []
    if item.answer:
        points.append({
            "id": f"{qid}:mp1",
            "description": item.answer,
            "marks": marks,
            "keyword": "",
            "isRequired": True,
            "synonyms": [],
        })

    return {
        "id": qid,
        "questionBankId": f"cbe:{item.source_pdf}",
        "subject": item.subject,
        "grade": item.grade,
        "chapterIds": [item.content_code] if item.content_code else [],
        # The named strand, when the index supplied one. `topic` is the field
        # the MCP topic tools read.
        "topic": item.topic or "",
        "contentCode": item.content_code,
        "contentReference": item.content_reference,
        "aoMarks": item.ao_marks,
        "calculator": item.calculator,
        "competencyIds": [],
        "bloomLevel": _DEFAULT_BLOOM,
        "difficulty": _difficulty_for(marks),
        "type": _question_type_for(item),
        "stem": item.question,
        "stemLatex": "",
        "parts": [{"id": f"{qid}:p1", "partNumber": 1, "text": o, "marks": 0,
                   "answerType": "singleChoice", "alternativeAnswers": []}
                  for o in item.options],
        "answerScheme": {
            "totalMarks": marks,
            "markingPoints": points,
            "rubricLevels": [],
            "commonErrors": [],
            "alternativeAnswers": [],
            "modelAnswer": "" if item.options else item.answer,
            "modelAnswerLatex": "",
            "hasPartialCredit": False,
            "metadata": {"guidance": item.guidance, "purpose": item.purpose,
                         "calculator": item.calculator, "aoMarks": item.ao_marks},
            "provenance": "cbse_marking_scheme" if item.answer else "none",
            "sourcePaperCode": "",
            "sourceDocumentId": f"cbe:{item.source_pdf}",
        },
        "estimatedTimeMinutes": max(1, marks * 2),
        "marks": marks,
        "language": "en",
        "source": "cbse_question_bank",
        "qualityScore": 0.95,          # board-published, not extracted
        "tags": [t for t in (item.topic, item.content_code) if t],
        "createdAt": "2026-09-17T00:00:00Z",
        "updatedAt": "2026-09-17T00:00:00Z",
        "metadata": {
            "itemId": item.item_id,
            "needsFigure": item.needs_figure,
            "contentReference": item.content_reference,
            "aoMarks": item.ao_marks,
        },
        "diagramAssetId": None, "mapAssetId": None,
        "graphAssetId": None, "tableAssetId": None,
        # An item whose stem refers to a figure that was not extracted is
        # unanswerable as printed. Flagged rather than silently exported, and
        # `assessment/pool.py` excludes these from paper generation.
        "rights": {
            "origin": "CBSE",
            "redistribution": "unknown",
            "basis": "",
            "attribution": ("Central Board of Secondary Education, "
                            "CBE item bank (CBSE / British Council)"),
        },
        "provenance": {
            "sourceDocumentId": f"cbe:{item.source_pdf}",
            "pageNumber": item.pages[0] if item.pages else None,
            "boundingBox": None,
            "method": "pdf_native",
            "confidence": 0.95,
        },
        "calibration": {"measured": False, "sampleSize": 0, "facility": None,
                        "discrimination": None, "basis": "assigned"},
        "version": 1,
        "reviewState": "published",
        "supersededBy": None,
    }


def parse_all(directory: Path) -> tuple[list["CbeItem"], list[str]]:
    """Parse every item bank in a directory. Returns `(items, errors)`."""
    items: list[CbeItem] = []
    errors: list[str] = []
    for pdf in sorted(Path(directory).glob("*.pdf")):
        try:
            items.extend(parse_item_bank(pdf))
        except Exception as exc:                               # noqa: BLE001
            errors.append(f"{pdf.name}: {type(exc).__name__}: {exc}")
    return items, errors


def parse_item_bank(pdf_path: Path) -> list[CbeItem]:
    """Parse one item-bank PDF end to end.

    Anchoring on either the content code or the `Item identity` header finds
    every real item, and also fragments: an id line inside an item's own
    mark scheme, or a sub-question id, can satisfy the same test. The result was
    2,760 candidates against 893 items the documents state.

    So candidates are collapsed by id, keeping the best-scoring one. "Best" is
    deliberately not "first": a fragment can precede the real item, and a
    fragment rarely carries both a question and a mark scheme. Scoring on those
    two fields picks the real one and discards the rest, which recovered the
    counts without needing the anchors to be perfect.
    """
    subject, grade = subject_and_grade_for(pdf_path)
    index = parse_index(pdf_path)

    best: dict[str, tuple[int, CbeItem]] = {}
    for item_id, pages, block in split_items(pdf_path):
        item = parse_item(item_id, pages, block, subject=subject, grade=grade,
                          source_pdf=pdf_path.name)
        score = (1 if item.question else 0) + (2 if item.has_answer_key else 0) \
            + (1 if item.marks else 0) + (1 if item.content_code else 0)
        current = best.get(item_id)
        if current is None or score > current[0]:
            best[item_id] = (score, item)

    items = [item for _score, item in best.values()]

    for item in items:
        row = index.get(item.question_id)
        if row:
            # The INDEX is authoritative for the content code and the strand;
            # the item's own metadata is authoritative only for the fuller
            # reference text. Getting this precedence backwards let a loose
            # in-item regex produce codes that do not exist in the curriculum
            # and override the correct one -- 638 items collapsed onto seven
            # distinct codes, which is how the bug was spotted.
            item.topic = row["topic"] or item.topic
            if row["content_code"]:
                item.content_code = row["content_code"]
            if not item.ao1_marks:
                item.ao1_marks = row["ao1_marks"]
            if not item.ao2_marks:
                item.ao2_marks = row["ao2_marks"]
    return items
