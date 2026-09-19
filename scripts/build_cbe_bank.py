"""Build the question-bank file from the CBSE CBE item banks.

Parses the 15 downloaded item banks, converts each item into the question-bank
wire shape, and writes a corpus file the API and the MCP server both read.

The answer-key rule
-------------------
The requirement is: **without an answer key, no question.** So items whose mark
scheme could not be parsed are excluded from the output, and the count of what
was dropped is printed rather than swallowed. An examination board does not
issue a question it cannot mark, and a bank that serves a mix of answerable and
unanswerable items degrades every paper built from it in a way nobody notices
until a teacher is holding it.

Excluded items are not discarded: they are written to a sibling
`_unanswerable.json` so the parser can be improved against them, and so the
shortfall is auditable rather than invisible.

Run:  python scripts/build_cbe_bank.py [--check]
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from academicos.corpus import figures as figmod         # noqa: E402
from academicos.corpus.cbse_cbe import (          # noqa: E402
    parse_all,
    to_bank_record,
)

SRC = REPO / "academicos-data" / "corpus" / "cbse-cbe"
OUT = SRC / "questions.json"
UNABLE = SRC / "_unanswerable.json"
FIGDIR = SRC / "figures"

# The highest mark value a single CBSE class 6-10 question can carry. See the
# marks gate below for why this exists and why it is not lower.
_MAX_SINGLE_QUESTION_MARKS = 10

# Which asset slot a figure belongs in, decided by what the stem calls it. The
# record carries four slots (diagram/map/graph/table) because the schema was
# written for a frontend that renders them differently; routing by the word the
# item actually uses is the only signal available and is better than putting
# every figure in `diagramAssetId`.
_ASSET_SLOT = (
    ("map", "mapAssetId"),
    ("graph", "graphAssetId"),
    ("table", "tableAssetId"),
    ("chart", "graphAssetId"),
    ("diagram", "diagramAssetId"),
    ("figure", "diagramAssetId"),
)


def _asset_slot(text: str) -> str:
    low = (text or "").lower()
    for word, slot in _ASSET_SLOT:
        if word in low:
            return slot
    return "diagramAssetId"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report only")
    args = ap.parse_args()

    if not SRC.exists() or not any(SRC.glob("*.pdf")):
        print(f"no item banks in {SRC}; run scripts/ingest_cbse_item_banks.py first",
              file=sys.stderr)
        return 1

    items, errors = parse_all(SRC)
    print(f"parsed {len(items):,} items from {len(list(SRC.glob('*.pdf')))} documents")
    for e in errors:
        print(f"  ERROR {e}")

    answerable = [i for i in items if i.has_answer_key]
    unanswerable = [i for i in items if not i.has_answer_key]
    # A question with no mark value is not a question either. Three records
    # carried marks=0, which is a parse artefact from a section heading rather
    # than a real item -- and a 0-mark question would corrupt any marks
    # distribution it appeared in.
    #
    # `marks_unresolved` is the same exclusion for a different reason: the item
    # came from a passage group that could not be split, so its marks are the
    # GROUP's stated total and belong to no single question. `to_bank_record`
    # emits marks=0 for those, so the gate has to test the same condition or the
    # bank serves a zero-mark question -- which is exactly what the rule above
    # exists to prevent. Measured, before this: 30 such items were emitted with
    # marks=0 while this gate counted them as marked.
    #
    # `_MAX_SINGLE_QUESTION_MARKS` catches the same defect where the parser has
    # no group signal at all. Measured: `Science10NB3` was served as an 11-mark
    # question whose stem is "Ethanoic acid reacts with sodium to produce sodium
    # ethanoate. 1(a)(i) Complete..." -- a case-based BLOCK with sub-parts,
    # carrying the block's total. Science blocks are not detected by
    # `_group_sub_item_ids`, so the group flag never fires for them.
    #
    # The ceiling is 10 because no CBSE class 6-10 question is worth 11 marks:
    # the scheme tops out at 1, 2, 3, 5 marks, with 4 for a case-based question
    # and occasionally 6. Values above that are block totals.
    #
    # Deliberately NOT extended down to 7-10, which would also drop items. Some
    # of those may be block totals too, but the evidence does not separate them
    # from genuine long-answer questions, and guessing would trade a visible
    # wrong number for an invisible lost question. They stay served and stay
    # visible in the marks distribution, which is where Q3 says a gap belongs.
    zero_marks = [i for i in answerable
                  if not i.marks or i.marks_unresolved
                  or i.marks > _MAX_SINGLE_QUESTION_MARKS]
    answerable = [i for i in answerable
                  if i.marks and not i.marks_unresolved
                  and i.marks <= _MAX_SINGLE_QUESTION_MARKS]
    unanswerable = unanswerable + zero_marks

    print()
    print(f"  with an answer key    : {len(answerable):,}  "
          f"({100.0 * len(answerable) / max(1, len(items)):.1f}%)")
    print(f"  WITHOUT an answer key : {len(unanswerable) - len(zero_marks):,}")
    print(f"  with 0 marks          : {len(zero_marks):,}  -> also excluded "
          f"(a mark-less question corrupts any marks distribution)")
    print(f"  -> {len(unanswerable):,} excluded in total, listed in {UNABLE.name}")

    records = [to_bank_record(i) for i in answerable]

    # Figures. An item whose stem says "in the given figure" is unanswerable as
    # printed without one, so the figure is not a nicety -- it is part of the
    # question. 512 images sit embedded in the source PDFs and were previously
    # discarded, which left 194 items referring to nothing.
    verdicts: dict[str, object] = {}
    figure_errors: list[str] = []
    for pdf_name in sorted({i.source_pdf for i in answerable if i.source_pdf}):
        pdf = SRC / pdf_name
        if not pdf.exists():
            figure_errors.append(f"{pdf_name}: source PDF missing, figures skipped")
            continue
        try:
            # Proximity to the item's own text, not shape alone. Shape-based
            # clustering could not tell a figure from a text box or the item
            # metadata table, and measured WORSE than raster-only. Using the
            # item's position took attributable figures from 59 to 95 of 124.
            verdicts.update(figmod.attribute_by_position(
                pdf, [i for i in answerable if i.source_pdf == pdf_name], FIGDIR))
        except Exception as exc:                  # pragma: no cover - defensive
            figure_errors.append(f"{pdf_name}: figure extraction failed: {exc}")

    fig_states = collections.Counter()
    for item, rec in zip(answerable, records):
        text = item.question or ""
        # The parser suppresses the figure signal whenever an item has options.
        # That is wrong for an MCQ whose stem says "in the given figure" -- an
        # option list does not supply the figure -- so it is recomputed here.
        rec["metadata"]["needsFigure"] = figmod.needs_figure(text)
        verdict = verdicts.get(item.item_id)
        state = getattr(verdict, "state", "none")
        rec["metadata"]["figureState"] = state
        if state == "attached" and item.marks:
            rec[_asset_slot(text)] = f"cbe-figure:{item.item_id}"
        fig_states[state] += 1

    # Coverage the requirement asks for, measured rather than asserted.
    by_sg = collections.Counter((r["subject"], r["grade"]) for r in records)
    topics = {r["contentCode"] for r in records if r["contentCode"]}
    with_topic = sum(1 for r in records if r["contentCode"])
    spread = collections.Counter(r["marks"] for r in records)
    mcq = sum(1 for r in records if r["type"] == "mcq")
    figures = sum(1 for r in records if (r["metadata"] or {}).get("needsFigure"))

    print()
    print(f"  subject x grade pairs : {len(by_sg)}")
    for (s, g), c in sorted(by_sg.items()):
        print(f"      {s:<12} class {g:<3} {c:>4}")
    print(f"  distinct topic codes  : {len(topics):,}")
    print(f"  mapped to a topic     : {with_topic:,} / {len(records):,}  "
          f"({100.0 * with_topic / max(1, len(records)):.1f}%)")
    print(f"  multiple choice       : {mcq:,}")
    print()
    print(f"  items referring to a figure : {figures:,}")
    print(f"      figure attached         : {fig_states['attached']:,}"
          + (f"   ({fig_states['attached'] / figures:.0%})" if figures else ""))
    print(f"      ambiguous (not served)  : {fig_states['ambiguous']:,}")
    print(f"      missing (not served)    : {fig_states['missing']:,}")
    print("      attached items keep their figure; ambiguous and missing items "
          "still\n      serve their text but are flagged, because a wrong figure "
          "is worse than none.")
    for e in figure_errors:
        print(f"      WARNING {e}")
    print("  marks distribution    : " +
          ", ".join(f"{m}x{c}" for m, c in sorted(spread.items())[:10]))

    if args.check:
        print("\n--check: nothing written")
        return 0

    payload = {
        "questions": records,
        "exportedCount": len(records),
        "source": "cbse-cbe-item-banks",
        "notice": ("CBSE CBE item banks, classes 6-10, Mathematics/Science/"
                   "English. Each item carries CBSE's own learning-ladder "
                   "content reference and published mark scheme."),
        "rights": {
            "origin": "CBSE",
            "redistribution": "unknown",
            "basis": "",
            "note": "No redistribution position obtained. See "
                    "docs/question-bank-api.md section 2.",
        },
        "builtAt": datetime.now(timezone.utc).isoformat(),
        # The figures a figure-dependent item needs to be answerable at all.
        # Rendered from the source PDFs, filenames are `<itemId>.png`, and a
        # record points at one through its asset slot as `cbe-figure:<itemId>`.
        "figures": {
            "directory": "figures",
            "naming": "<itemId>.png",
            "attached": fig_states["attached"],
            "ambiguous": fig_states["ambiguous"],
            "missing": fig_states["missing"],
            "note": ("ambiguous and missing items are served without a figure and "
                     "carry metadata.figureState accordingly"),
        },
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    UNABLE.write_text(json.dumps(
        {"items": [i.to_dict() for i in unanswerable],
         "count": len(unanswerable),
         "reason": "mark scheme not parsed; excluded from the served bank"},
        ensure_ascii=False, indent=1), encoding="utf-8")

    print()
    print(f"wrote {OUT.relative_to(REPO)}  ({OUT.stat().st_size / 1_000_000:.1f} MB)")
    print(f"wrote {UNABLE.relative_to(REPO)}  ({len(unanswerable)} items for parser work)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
