"""Apply the inferred chapter tags onto the served corpus records.

`tag_question_bank.py` produces `syllabus/chapter_tags.json`; nothing read it.
A tag file that no corpus carries is the same shape of gap as the SQP parser
that parsed and was wired into nothing -- the work exists and the product does
not have it.

This runs AFTER the builders, so the order is:

    build_cbe_bank.py  /  build_sqp_bank.py
    tag_question_bank.py          # infers, writes chapter_tags.json
    apply_chapter_tags.py         # <- this, writes the tags into the corpora

Re-running a builder discards the applied tags, which is why the order matters
and why it is written down rather than remembered.

What it sets
------------
  * `chapterIds` -- the CBSE chapter id, which is the field a paper blueprint
    filters on.
  * `metadata.chapterTag` -- the confidence and the method, kept SEPARATE from
    `contentCode`. The CBE corpus carries CBSE's own learning-ladder code, which
    is authoritative; an inferred chapter must never be readable as an authored
    one. Where both exist, `contentCode` wins for anything that needs a code
    CBSE issued, and `chapterTag` says how the chapter was decided.

Run:  python scripts/apply_chapter_tags.py [--check]
"""
from __future__ import annotations

import argparse
import collections
import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

TAGS = REPO / "academicos-data" / "syllabus" / "chapter_tags.json"
CORPORA = [
    REPO / "academicos-data" / "corpus" / "cbse-cbe" / "questions.json",
    REPO / "academicos-data" / "corpus" / "cbse-sqp" / "questions.json",
    REPO / "academicos-data" / "syllabus" / "questions.json",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    if not TAGS.exists():
        print(f"no tags at {TAGS}; run scripts/tag_question_bank.py first")
        return 1
    payload = json.loads(TAGS.read_text(encoding="utf-8"))
    tags: dict[str, dict] = payload["tags"]
    print(f"tags available: {len(tags):,}  (method {payload.get('method')})")

    grand_applied = grand_total = 0
    for path in CORPORA:
        if not path.exists():
            print(f"  {path.name}: absent, skipped")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        questions = data["questions"]

        applied = 0
        by_chapter = collections.Counter()
        for rec in questions:
            tag = tags.get(rec["id"])
            if not tag:
                continue
            rec["chapterIds"] = [tag["chapterId"]]
            meta = rec.setdefault("metadata", {})
            meta["chapterTag"] = {
                "chapterId": tag["chapterId"],
                "score": tag["score"],
                # The method is carried on every record so an inferred chapter
                # is distinguishable from an authored one at a glance, not only
                # by whoever happens to read this script.
                "method": tag["method"],
                "inferred": True,
            }
            applied += 1
            by_chapter[tag["chapterId"]] += 1

        print(f"  {path.parent.name}/{path.name}: {applied:,} of {len(questions):,} tagged"
              f"  ({applied / max(1, len(questions)):.0%}), "
              f"{len(by_chapter)} distinct chapters")
        grand_applied += applied
        grand_total += len(questions)

        if not args.check:
            data["chapterTaggedAt"] = datetime.now(timezone.utc).isoformat()
            data["chapterTagMethod"] = payload.get("method")
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    print()
    print(f"applied {grand_applied:,} of {grand_total:,} "
          f"({grand_applied / max(1, grand_total):.0%})")
    if args.check:
        print("--check: nothing written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
