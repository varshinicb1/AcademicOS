"""What rebuilding the bank would change about its marking points.

Task 124 splits a scheme's answer into the value points its source printed
(`academicos.corpus.marking_split`). The importers run at build time, so until
the bank is rebuilt the change is invisible -- and a number in a commit
message cannot be checked. This runs the splitter over the SERVED bank,
read-only, and prints what a rebuild would produce: per source, how many
multi-mark keys carry more than one value point before and after, the mean
points per multi-mark question, which rule read each split, and -- for every
key that keeps its single point -- why.

It writes nothing. Run it before a rebuild for the prediction and after one
for the outcome; the two should agree, because the same function makes both.

The served bank has NOT been rebuilt for this change yet: another session's
test floors are pinned to the current file (5,427 records / 2,343 chapter
tags), so the rebuild waits for its owner rather than landing under it. Until
it runs, every number this prints is a prediction -- which is why it is a
script and not a sentence in a commit message.

Run:  python scripts/check_marking_split.py [--bank BANK] [--reasons]
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from academicos.corpus import marking_split as ms  # noqa: E402

SERVED = REPO / "academicos-data" / "syllabus" / "questions.json"


def _source_of(record_id: str) -> str:
    if record_id.startswith("exemplar:"):
        return "ncert_exemplar"
    if record_id.startswith("cbse:sqp:"):
        return "cbse_sample_paper"
    if record_id.startswith("cbe:"):
        return "cbse_question_bank"
    return "other"


def _answer_of(record: dict) -> str:
    """The key as the bank stores it: one lump point per record today, so the
    text a rebuilt importer would hand the splitter is its description."""
    scheme = record.get("answerScheme") or {}
    return " ".join((p.get("description") or "")
                    for p in (scheme.get("markingPoints") or []))


def _why_whole(text: str, marks: int, stem: str) -> str:
    """The guard that kept this key whole, named the way the module's own
    docstring names it. Mirrors `split_answer`'s order of refusals."""
    if ms._GROUP_PART.search(text) or len(ms._GROUP_PART.findall(stem)) > 1:
        return "a CBE group item, whose key covers several sub-questions"
    if ms._half_mark_split(text, marks):
        return "half a mark a point, which marks cannot carry"
    if any(int(n) == marks for n in ms._WHOLE_MARK_AWARD.findall(text)):
        return "a level-of-response rubric"
    if ms._INTERNAL_CHOICE.search(text):
        return "two answers in one key -- an internal choice"
    listing = ms._list_items(text)
    items, lead_in = listing.items, listing.lead_in
    if not items:
        return ("named points that do not account for the marks"
                if len(ms._MARKS_FOR.findall(text)) >= 2
                else "prose: no list, no mark annotation, nothing to read")
    if len(lead_in) > ms._MAX_LEAD_IN:
        return "answer content outside the list no point would account for"
    governing = f"{lead_in} {listing.instruction}"
    any_n = ms._any_of_count(governing)
    if any_n is not None and any_n > len(items):
        return "an 'any N' that awards more than the list shows"
    if any_n == 1:
        return "'any one of the following', where one point carries every mark"
    if any_n is not None and 1 < any_n < len(items):
        return "an 'any N' that does not divide the marks"
    if ms._marks_each(text) is not None:
        return "a printed per-point value that does not fit the list"
    if listing.style != ms._PAREN_NUMBER and ms._PARENTHESISED_MARKS.findall(text):
        return "printed marks beside the points that do not fit the list"
    if ms._addends(text, marks) is not None:
        return "an arithmetic split that does not line up with the list"
    if marks % len(items):
        return "a list whose count does not divide the question's marks"
    return "a case study, whose parts the paper weights 1, 1 and 2"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bank", type=Path, default=SERVED)
    ap.add_argument("--reasons", action="store_true",
                    help="also list why each key that stays whole does")
    args = ap.parse_args()

    raw = json.loads(args.bank.read_text(encoding="utf-8"))
    records = raw["questions"] if isinstance(raw, dict) else raw

    before = collections.Counter()
    after = collections.Counter()
    total = collections.Counter()
    points = collections.defaultdict(list)
    rules = collections.Counter()
    reasons = collections.Counter()
    echo_seen = echo_cut = 0
    unaccounted = []

    for record in records:
        stem, key = record.get("stem") or "", _answer_of(record)
        flat = " ".join(key.split())
        if stem and flat:
            head = " ".join(stem.split()).lower()
            shared = 0
            low = flat.lower()
            while shared < min(len(low), len(head)) and low[shared] == head[shared]:
                shared += 1
            if shared >= ms._MIN_ECHO:
                echo_seen += 1
                echo_cut += ms.strip_stem_echo(stem, key) != flat
        marks = int(record.get("marks") or 0)
        if marks <= 1 or not flat:
            continue
        source = _source_of(record.get("id") or "")
        total[source] += 1
        stored = (record.get("answerScheme") or {}).get("markingPoints") or []
        before[source] += len(stored) > 1
        answer = ms.strip_stem_echo(stem, key)
        split = ms.split_answer(answer, marks, stem)
        after[source] += len(split.points) > 1
        points[source].append(len(split.points))
        rules[(split.rule or "(none)", source)] += 1
        if not split.rule:
            reasons[_why_whole(" ".join(answer.split()), marks, stem)] += 1
        if ms.awardable_marks(split) != marks:
            unaccounted.append(record.get("id"))

    print(f"bank: {args.bank}")
    print(f"multi-mark records: {sum(total.values())}\n")
    width = max(len(s) for s in total) if total else 20
    print(f"{'source':<{width}}  {'>1 point before':>15}  {'after':>7}  {'mean points':>11}")
    for source in sorted(total):
        counts = points[source]
        print(f"{source:<{width}}  {before[source]:>15}  {after[source]:>7}  "
              f"{sum(counts) / len(counts):>11.3f}")
    every = [n for counts in points.values() for n in counts]
    print(f"{'ALL':<{width}}  {sum(before.values()):>15}  {sum(after.values()):>7}  "
          f"{sum(every) / len(every):>11.3f}")

    print("\nthe rule that read each key:")
    for (rule, source), count in sorted(rules.items()):
        print(f"  {rule:<15} {source:<20} {count}")

    print(f"\nkeys that keep their single point: {sum(reasons.values())}")
    if args.reasons:
        for why, count in reasons.most_common():
            print(f"  {count:>6}  {why}")

    print(f"\nkeys opening with 20+ characters of their own stem: {echo_seen}, "
          f"of which cut: {echo_cut}")
    print(f"schemes whose points do not account for the question's marks: "
          f"{len(unaccounted)} {unaccounted[:5]}")
    return 1 if unaccounted else 0


if __name__ == "__main__":
    raise SystemExit(main())
