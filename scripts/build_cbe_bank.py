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

from academicos.corpus.cbse_cbe import (          # noqa: E402
    parse_all,
    to_bank_record,
)

SRC = REPO / "academicos-data" / "corpus" / "cbse-cbe"
OUT = SRC / "questions.json"
UNABLE = SRC / "_unanswerable.json"


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
    zero_marks = [i for i in answerable if not i.marks]
    answerable = [i for i in answerable if i.marks]
    unanswerable = unanswerable + zero_marks

    print()
    print(f"  with an answer key    : {len(answerable):,}  "
          f"({100.0 * len(answerable) / max(1, len(items)):.1f}%)")
    print(f"  WITHOUT an answer key : {len(unanswerable) - len(zero_marks):,}")
    print(f"  with 0 marks          : {len(zero_marks):,}  -> also excluded "
          f"(a mark-less question corrupts any marks distribution)")
    print(f"  -> {len(unanswerable):,} excluded in total, listed in {UNABLE.name}")

    records = [to_bank_record(i) for i in answerable]

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
    print(f"  need a figure         : {figures:,} (flagged, excluded from papers)")
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
