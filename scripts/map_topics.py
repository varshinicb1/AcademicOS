"""Apply the calibrated topic mapper, and only where it earns its place.

Per subject x grade, this:
  1. builds a labeled reference from EVERY parsed CBE item -- including the 849
     that have no answer key. They cannot be served, but they carry a content
     code, so they are perfectly good labeled examples. That doubled the
     reference for Mathematics class 10 (120 -> 200).
  2. maps to COARSE strands, not leaf codes, because 5.9 examples per class is
     why the leaf attempt capped at 43% precision and 28.6 examples per class
     is why the strand attempt reached 95%.
  3. cross-validates, and writes mappings ONLY if the mapped precision clears
     the bar. A subject that fails is reported as failed and left untouched.

The distribution-shift caveat, stated plainly: precision is measured by
cross-validation on CBE items, and the questions being mapped are board-paper
items. Those are not the same distribution -- board papers are older, often
multi-part, and phrased differently. The measured figure is an upper bound on
the real accuracy, not a guarantee. That is why the output is a SEPARATE file
rather than a rewrite of the corpus: a wrong mapping can be discarded without
touching the source, and the mapped subset is marked as inferred.
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

from academicos.assessment.topic_mapper import TopicMapper, coarse_code  # noqa: E402
from academicos.corpus.cbse_cbe import parse_all                          # noqa: E402

MIN_PRECISION = 0.80
MIN_COVERAGE = 0.15

# Per-subject minimum reference examples (English has fewer CBE items)
MIN_EXAMPLES_PER_SUBJECT = {
    "English": 10,
    "Mathematics": 20,
    "Science": 20,
}
DEFAULT_MIN_EXAMPLES = 20


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report only, write nothing")
    args = ap.parse_args()

    items, _errors = parse_all(REPO / "academicos-data/corpus/cbse-cbe")
    labeled = [i for i in items if i.content_code]
    board = json.loads(
        (REPO / "academicos-data/syllabus/questions.json").read_text(encoding="utf-8"))
    board = board["questions"]

    ref = collections.defaultdict(list)
    for it in labeled:
        ref[(it.subject, it.grade)].append((
            " ".join([it.question or "", it.topic or "", it.content_reference or ""]),
            coarse_code(it.content_code),
        ))

    targets = collections.defaultdict(list)
    for rec in board:
        targets[(rec.get("subject"), rec.get("grade"))].append(rec)

    print(f"reference items (all parsed CBE, incl. unanswered): {len(labeled):,}")
    print(f"board questions                                    : {len(board):,}")
    print()
    print(f"{'subject':<14} {'gr':<4} {'ref':>5} {'cls':>4} {'tgt':>5} "
          f"{'prec':>6} {'cov':>6}  verdict")
    print("-" * 72)

    mapping: dict[str, dict] = {}
    refused: list[str] = []

    for key in sorted(ref, key=lambda k: (str(k[0]), str(k[1]))):
        subject, grade = key
        examples = [(t, c) for t, c in ref[key] if c and t.strip()]
        tgt = targets.get(key, [])
        min_examples = MIN_EXAMPLES_PER_SUBJECT.get(subject, DEFAULT_MIN_EXAMPLES)
        if len(examples) < min_examples or len({c for _t, c in examples}) < 2 or not tgt:
            continue

        cv = TopicMapper().cross_validate(examples, folds=5)
        gate = TopicMapper.gate_from_cv(
            cv, min_precision=MIN_PRECISION, min_coverage=MIN_COVERAGE)
        row = next((r for r in cv["rows"] if r["threshold"] == gate), None)

        if gate is None:
            usable = [r for r in cv["rows"] if r["coverage"] >= MIN_COVERAGE]
            best = max(usable, key=lambda r: r["precision"]) if usable else None
            print(f"{str(subject):<14} {str(grade):<4} {len(examples):>5} "
                  f"{len({c for _t, c in examples}):>4} {len(tgt):>5} "
                  f"{(best['precision'] if best else 0):>6.0%} "
                  f"{(best['coverage'] if best else 0):>6.0%}  REFUSED")
            refused.append(f"{subject} {grade}")
            continue

        mapper = TopicMapper(min_score=gate).fit(examples)
        assigned = 0
        by_strand: collections.Counter = collections.Counter()
        for rec in tgt:
            topic, score = mapper.predict(rec.get("stem") or "")
            if not topic:
                continue
            mapping[rec["id"]] = {
                "subject": subject, "grade": grade,
                "strand": topic, "score": round(score, 4),
                "method": "cbe_strand_centroid_v1",
                "precisionAtGate": round(row["precision"], 4),
            }
            assigned += 1
            by_strand[topic] += 1

        print(f"{str(subject):<14} {str(grade):<4} {len(examples):>5} "
              f"{len({c for _t, c in examples}):>4} {len(tgt):>5} "
              f"{row['precision']:>6.0%} {assigned / len(tgt):>6.0%}  ACCEPT "
              f"({assigned}/{len(tgt)} mapped)")

    print()
    print(f"mapped {len(mapping):,} questions across "
          f"{len({v['subject'] + str(v['grade']) for v in mapping.values()})} subject x grade pairs")
    if refused:
        print(f"refused (below {MIN_PRECISION:.0%} precision): {', '.join(refused)}")
        print("  these are left unmapped rather than guessed")

    if args.check:
        print("\n--check: nothing written")
        return 0

    out = REPO / "academicos-data" / "syllabus" / "inferred_topics.json"
    out.write_text(json.dumps({
        "notice": ("Strand-level topics INFERRED from the CBSE CBE learning-ladder "
                   "codes by nearest-centroid. Not authored by CBSE. Precision is "
                   "cross-validated on CBE items and is an upper bound on accuracy "
                   "for board-paper questions."),
        "method": "cbe_strand_centroid_v1",
        "minPrecision": MIN_PRECISION,
        "builtAt": datetime.now(timezone.utc).isoformat(),
        "count": len(mapping),
        "topics": mapping,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nwrote {out.relative_to(REPO)}  ({len(mapping):,} inferred topics)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
