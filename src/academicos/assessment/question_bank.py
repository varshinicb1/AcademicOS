"""Question bank: the enriched record, the answer-key relink, and the
curriculum-to-question surface.

Why this module exists
----------------------
The bank holds 3,286 questions and only 1,093 of them (33.3%) carried a marking
scheme, which is the half `docs/question-bank-api.md` calls the moat. That
document concluded the answers were scarce.

They are not scarce. They are **unlinked**. A separate store,
`academicos-data/answer_keys.db`, holds 4,483 official answers with real value
points, and 88.6% of those rows sit under a filename carrying the CBSE paper
code. The questions carry a *content hash* of their source PDF and a question
number, and nothing joined the two.

The link, verified end to end against real files:

    question id      cbse:q:src:af50a3f7….…:4
    parse tree       academicos-data/parse/src_af50a3f7….….json
                     -> page headers carry the paper code 31/1/1
    answer key       answer_keys.db, source "X_086_31-1-1 to 3 Science_MS.pdf"
                     -> KeyedAnswer for question 4

So this module walks that chain, attaches the official scheme where it exists,
and records the provenance that makes the attachment checkable. It never
invents an answer: a question with no matching scheme is left without one and
reported, not filled with a guess.
"""
from __future__ import annotations

import json
import logging
import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional

from .answer_key import normalize_paper_code
from .schemas import (
    AnswerSchemeSchema,
    CalibrationSchema,
    MarkingPointSchema,
    ProvenanceSchema,
    RightsSchema,
)

log = logging.getLogger(__name__)

# Recover the hash and question number back out of a canonical question id.
# `cbse:q:src:<24 hex>:<q_no>` is produced by `pool.py`; this is its inverse.
_QUESTION_ID = re.compile(r"^[a-z]+:q:src:([0-9a-f]{8,}):(\d+)$")

# A CBSE marking scheme's running header prints the code; `normalize_paper_code`
# handles the separators. This pattern is only used to decide whether a page or
# a filename is a *candidate* carrier, so it stays deliberately loose -- but it
# must accept every separator the corpus uses (`.`, `_`, `-`, `/`), because
# gating on a narrower set silently drops whole papers.
_CODE_HINT = re.compile(
    r"(?<!\d)\d{2,3}\s*[/\-._]\s*\d\s*[/\-._]\s*\d(?!\d)")


def parse_question_id(qid: str) -> tuple[str, int] | None:
    """`cbse:q:src:<hash>:<q_no>` -> `(hash, q_no)`, or None if it is not that shape."""
    m = _QUESTION_ID.match((qid or "").strip())
    if not m:
        return None
    return m.group(1), int(m.group(2))


def _collapse(text: str) -> str:
    """Collapse all whitespace runs to single spaces.

    Applied to whole page texts, not just to search probes. Without it a probe
    containing a line break never matched the page text it came from.
    """
    return " ".join(text.split())


# --------------------------------------------------------------------------- #
# source documents
# --------------------------------------------------------------------------- #

@dataclass
class ParsedSource:
    """One parsed source document, with the paper code found in its headers."""

    document_id: str
    doc_type: str = ""
    paper_code: str = ""
    page_count: int = 0
    _pages: list[tuple[int, str]] = field(default_factory=list, repr=False)

    def page_containing(self, needle: str, *, window: int = 60) -> int | None:
        """First page whose text contains the first `window` characters of `needle`.

        Used for provenance only. A miss is not an error -- it means the stem
        was reassembled across a page break, and returning a wrong page would
        be worse than returning none.

        Whitespace is collapsed on BOTH sides. Normalising only the probe, as
        the first version did, matched almost nothing: the page text keeps the
        PDF's line breaks, so a 60-character probe containing a newline never
        appeared in it verbatim and every page came back as None.
        """
        probe = " ".join((needle or "").split())[:window]
        if len(probe) < 24:
            return None
        for page_no, text in self._pages:
            if probe in text:
                return page_no
        return None


def load_parsed_source(parse_dir: Path, doc_hash: str) -> ParsedSource | None:
    """Read `parse/src_<hash>.json` and find its paper code.

    The code lives in the running header, so only the first few hundred
    characters of each page are scanned: a code appearing mid-page is far more
    likely to be a question number than the paper identifier.
    """
    path = Path(parse_dir) / f"src_{doc_hash}.json"
    if not path.exists():
        return None
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        log.warning("unreadable parse tree: %s", path)
        return None

    pages: list[tuple[int, str]] = []
    code = ""
    for page in doc.get("pages") or []:
        page_no = int(page.get("page_no") or len(pages) + 1)
        text = " ".join(
            str(page.get(k) or "") for k in ("text", "content", "body")
        ).strip()
        if text:
            pages.append((page_no, _collapse(text)))
            if not code:
                head = text[:300]
                if _CODE_HINT.search(head):
                    code = normalize_paper_code(head)

    return ParsedSource(
        document_id=str(doc.get("document_id") or f"src:{doc_hash}"),
        doc_type=str(doc.get("doc_type") or ""),
        paper_code=code,
        page_count=len(pages),
        _pages=pages,
    )


# --------------------------------------------------------------------------- #
# answer keys
# --------------------------------------------------------------------------- #

@dataclass
class OfficialAnswer:
    q_no: int
    correct_option: str | None
    answer_text: str
    value_points: list[tuple[str, float]] = field(default_factory=list)
    marks: float = 0.0


class AnswerKeyIndex:
    """`answer_keys.db` indexed by normalised paper code.

    Keyed by code rather than by filename because the code is the only
    identifier both a question paper and its marking scheme reliably carry.
    Filenames vary wildly -- "32-3-2 H.pdf", "MS Science (086) 31-8-1 to 3) in
    HINDI.pdf" -- and content hashes identify a file, not a paper.
    """

    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)
        self._by_code: dict[str, dict[int, OfficialAnswer]] = {}
        self.rows_total = 0
        self.rows_keyed = 0
        if self.db_path.exists():
            self._load()

    def _load(self) -> None:
        con = sqlite3.connect(f"file:{self.db_path.as_posix()}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        try:
            rows = list(con.execute(
                "SELECT subject, grade, q_no, correct_option, answer_text, "
                "value_points, marks, source FROM answer_keys"
            ))
        finally:
            con.close()

        for r in rows:
            self.rows_total += 1
            source = str(r["source"] or "")
            if not _CODE_HINT.search(source):
                # No code in the filename. It may still be reachable by content
                # hash, which is a separate pass; do not guess a code here.
                continue
            code = normalize_paper_code(source)
            if not code:
                continue
            try:
                q_no = int(r["q_no"])
            except (TypeError, ValueError):
                continue
            points = _parse_value_points(r["value_points"])
            entry = OfficialAnswer(
                q_no=q_no,
                correct_option=(r["correct_option"] or None),
                answer_text=str(r["answer_text"] or ""),
                value_points=points,
                marks=float(r["marks"] or 0.0),
            )
            self._by_code.setdefault(code, {})[q_no] = entry
            self.rows_keyed += 1

    @property
    def codes(self) -> set[str]:
        return set(self._by_code)

    def lookup(self, code: str, q_no: int) -> OfficialAnswer | None:
        if not code:
            return None
        return self._by_code.get(normalize_paper_code(code) or code, {}).get(q_no)

    def stats(self) -> dict[str, Any]:
        return {
            "rows_total": self.rows_total,
            "rows_keyed": self.rows_keyed,
            "distinct_codes": len(self._by_code),
        }


def _parse_value_points(raw: Any) -> list[tuple[str, float]]:
    """`value_points` is stored as a JSON array of [text, marks] pairs."""
    if not raw:
        return []
    try:
        parsed = json.loads(raw) if isinstance(raw, str) else raw
    except (TypeError, ValueError):
        return []
    out: list[tuple[str, float]] = []
    if isinstance(parsed, list):
        for item in parsed:
            if isinstance(item, (list, tuple)) and item:
                text = str(item[0] or "").strip()
                marks = float(item[1]) if len(item) > 1 and item[1] is not None else 0.0
                if text:
                    out.append((text, marks))
            elif isinstance(item, str) and item.strip():
                out.append((item.strip(), 0.0))
    return out


# --------------------------------------------------------------------------- #
# the relink
# --------------------------------------------------------------------------- #

@dataclass
class RelinkReport:
    """What the relink actually did. Printed by the pipeline, asserted in tests."""

    total: int = 0
    already_had_scheme: int = 0
    newly_attached: int = 0
    no_source_hash: int = 0
    no_parse_tree: int = 0
    no_paper_code: int = 0
    code_not_in_answer_keys: int = 0
    answer_not_found_for_qno: int = 0
    found: int = 0

    @property
    def with_scheme(self) -> int:
        return self.already_had_scheme + self.newly_attached

    def coverage(self) -> float:
        return (100.0 * self.with_scheme / self.total) if self.total else 0.0

    def lines(self) -> list[str]:
        return [
            "questions                      : {:,}".format(self.total),
            "had a scheme before            : {:,}".format(self.already_had_scheme),
            "scheme attached by this pass   : {:,}".format(self.newly_attached),
            "with a scheme after            : {:,}  ({:.1f}%)".format(
                self.with_scheme, self.coverage()),
            "",
            "did not reach an answer key:",
            "  id is not a cbse:q:src:<hash>:<n> : {:,}".format(self.no_source_hash),
            "  no parse tree for the source      : {:,}".format(self.no_parse_tree),
            "  no paper code in the parse tree   : {:,}".format(self.no_paper_code),
            "  code absent from answer_keys.db   : {:,}".format(self.code_not_in_answer_keys),
            "  code present, no answer for q_no  : {:,}".format(self.answer_not_found_for_qno),
            "  (an answer key found for)         : {:,}".format(self.found),
        ]


def build_official_scheme(
    answer: OfficialAnswer, *, marks: int, question_id: str, code: str,
    document_id: str,
) -> AnswerSchemeSchema:
    """Turn a KeyedAnswer into the API's scheme shape.

    Marks per value point are left at 0 when the source did not carry them:
    a marking scheme's mark column is emitted separately from its text in a
    flattened PDF, so attaching a number would be inventing one.
    """
    points = [
        MarkingPointSchema(
            id=f"{question_id}:mp{i + 1}",
            description=text,
            marks=int(round(m)) if m else 0,
        )
        for i, (text, m) in enumerate(answer.value_points)
    ]
    return AnswerSchemeSchema(
        total_marks=marks,
        marking_points=points,
        model_answer=answer.answer_text if not answer.correct_option else "",
        has_partial_credit=len(points) > 1,
        provenance="cbse_marking_scheme",
        source_paper_code=code,
        source_document_id=document_id,
    )


def relink_answer_schemes(
    records: list[dict[str, Any]],
    index: AnswerKeyIndex,
    *,
    parse_dir: Path,
    attach_provenance: bool = True,
) -> RelinkReport:
    """Attach official marking schemes to question records, in place.

    `records` are the camelCase dicts as exported (the wire shape), because that
    is what `questions.json` is made of and rewriting the pipeline's shape here
    would put a second schema in the path. Fields written: `answerScheme`,
    and when `attach_provenance`, `provenance`.
    """
    report = RelinkReport(total=len(records))
    sources: dict[str, ParsedSource | None] = {}

    for rec in records:
        parsed_id = parse_question_id(rec.get("id") or "")
        if not parsed_id:
            report.no_source_hash += 1
            continue
        doc_hash, q_no = parsed_id

        if doc_hash not in sources:
            sources[doc_hash] = load_parsed_source(Path(parse_dir), doc_hash)
        source = sources[doc_hash]
        if source is None:
            report.no_parse_tree += 1
            continue

        if attach_provenance:
            page = source.page_containing(rec.get("stem") or "")
            if page is not None or source.page_count:
                rec["provenance"] = ProvenanceSchema(
                    source_document_id=source.document_id,
                    page_number=page,
                    method="pdf_native",
                    confidence=round(1.0 if page else 0.6, 2),
                ).model_dump(mode="json", by_alias=True)

        scheme = rec.get("answerScheme") or {}
        if scheme.get("markingPoints"):
            report.already_had_scheme += 1
            continue

        if not source.paper_code:
            report.no_paper_code += 1
            continue

        answer = index.lookup(source.paper_code, q_no)
        if answer is None:
            if source.paper_code in index.codes:
                report.answer_not_found_for_qno += 1
            else:
                report.code_not_in_answer_keys += 1
            continue

        report.found += 1
        rec["answerScheme"] = build_official_scheme(
            answer,
            marks=int(rec.get("marks") or 0),
            question_id=str(rec.get("id")),
            code=source.paper_code,
            document_id=source.document_id,
        ).model_dump(mode="json", by_alias=True)
        report.newly_attached += 1

    return report


# --------------------------------------------------------------------------- #
# rights and calibration defaults
# --------------------------------------------------------------------------- #

def rights_for_cbse_board_paper() -> RightsSchema:
    """Every question in the bank today comes from a real CBSE board paper.

    `redistribution` stays `unknown` because no written position exists --
    `docs/question-bank-api.md` section 2 says the legal question gates
    distribution and nothing here is qualified to answer it. Defaulting to
    unknown means an unsettled decision fails closed.
    """
    return RightsSchema(
        origin="CBSE",
        redistribution="unknown",
        basis="",
        attribution="Central Board of Secondary Education, previous year question paper",
    )


def assigned_calibration() -> CalibrationSchema:
    """The difficulty field is derived from mark value and Bloom level.

    That is a heuristic, not a measurement, and the payload says so.
    """
    return CalibrationSchema(measured=False, sample_size=0, basis="assigned")


def enrich_record(rec: dict[str, Any]) -> dict[str, Any]:
    """Fill the standalone-asset fields on one wire-shaped record.

    Idempotent, and never overwrites a value that is already set -- so running
    the pipeline twice does not bump `version` twice or reset a rights decision
    someone has since recorded.

    Fields written: `rights`, `calibration`, `version`, `reviewState`,
    `language`. `provenance` is written by the relink, which is the pass that
    knows where the question sits in its source.
    """
    if not rec.get("rights"):
        rec["rights"] = rights_for_cbse_board_paper().model_dump(
            mode="json", by_alias=True)

    if not rec.get("calibration"):
        rec["calibration"] = assigned_calibration().model_dump(
            mode="json", by_alias=True)

    # Version 1 is the initial extraction. A correction is a new version, never
    # an in-place rewrite, so a consumer can reproduce what they were served.
    rec.setdefault("version", 1)
    rec.setdefault("supersededBy", None)

    # `published` because these are real, reviewed board questions already in
    # use by teachers. `draft` would be a lie that hides them from every
    # consumer filtering on state.
    rec.setdefault("reviewState", "published")

    # Already present on every record, but set explicitly so a record built by
    # some future path cannot silently omit it.
    rec.setdefault("language", "en")

    return rec


def enrich_all(records: Iterable[dict[str, Any]]) -> dict[str, int]:
    """Apply `enrich_record` across a corpus; returns a small census."""
    counts = {"total": 0, "rights_set": 0, "published": 0, "with_provenance": 0,
              "with_page": 0, "with_official_scheme": 0}
    for rec in records:
        counts["total"] += 1
        enrich_record(rec)
        if rec.get("rights"):
            counts["rights_set"] += 1
        if rec.get("reviewState") == "published":
            counts["published"] += 1
        prov = rec.get("provenance") or {}
        if prov.get("sourceDocumentId"):
            counts["with_provenance"] += 1
        if prov.get("pageNumber"):
            counts["with_page"] += 1
        if (rec.get("answerScheme") or {}).get("provenance") == "cbse_marking_scheme":
            counts["with_official_scheme"] += 1
    return counts
