"""The final bank summary: what was generated, what survived, what is missing.

Written alongside the bank rather than only to the console, because "how good is
this question bank" is a question that has to keep being answerable after the
session that built it, and because the answer is mostly about the gaps.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.corpus import cbse_generate as cg      # noqa: E402

BANK = ROOT / "academicos-data" / "corpus" / "ai-cbse" / "questions.json"
TEXTBOOK = ROOT / "academicos-data" / "corpus" / "ncert-textbook" / "questions.json"


def report() -> int:
    if not BANK.is_file():
        print(f"no bank at {BANK}; run collect_ai_cbse.py first")
        return 2
    bank = json.loads(BANK.read_text(encoding="utf-8"))
    questions = bank.get("questions") or []
    refusals = bank.get("refusals") or []

    print("=" * 70)
    print("GENERATED CBSE BANK")
    print("=" * 70)
    print(f"questions kept    : {len(questions)}")
    print(f"refused           : {len(refusals)}")
    keeper = len(questions) / max(1, len(questions) + len(refusals))
    print(f"keeper rate       : {keeper:.0%}")

    if questions:
        print()
        print("by subject :", dict(Counter(
            q["subject"] for q in questions).most_common()))
        print("by grade   :", dict(sorted(
            (g, c) for g, c in Counter(q["grade"] for q in questions).items())))
        print("by section :", dict(Counter(
            q["provenance"]["section"] for q in questions).most_common()))
        print("by type    :", dict(Counter(
            q["type"] for q in questions).most_common()))
        print("bloom      :", dict(Counter(
            q.get("bloomLevel") for q in questions).most_common()))
        print("chapters   :", len({q["taxonomyChapterId"] for q in questions}))

        keys = cg.audit_key_distribution(questions)
        if keys["total"]:
            spread = "  ".join(f"{k} {keys['counts'][k]}"
                               for k in sorted(keys["counts"]))
            print(f"key spread : {spread}"
                  + ("   <- BIASED" if keys["biased"] else "   (within tolerance)"))

        grounded = sum(1 for q in questions
                       if (q.get("answerScheme") or {}).get("metadata", {}).get("objective")
                       or (q.get("answerScheme") or {}).get("modelAnswer"))
        print(f"answerable : {grounded}/{len(questions)}")
        ids = [q["id"] for q in questions]
        print(f"unique ids : {len(set(ids))}/{len(ids)}")

    if refusals:
        print()
        print("refusals by reason:")
        for reason, count in Counter(r["reason"] for r in refusals).most_common():
            print(f"   {count:>4}  {reason}")

    print()
    print("=" * 70)
    print("EXISTING TEXTBOOK BANK (unchanged, for context)")
    print("=" * 70)
    if TEXTBOOK.is_file():
        other = json.loads(TEXTBOOK.read_text(encoding="utf-8")).get("questions") or []
        print(f"questions         : {len(other)}")
        print(f"by source         :", dict(Counter(
            q.get("source") for q in other).most_common()))
        print(f"grades 1-5        :", sum(
            1 for q in other if (q.get("grade") or 0) <= 5))
    else:
        print("not present in this worktree")

    print()
    print("=" * 70)
    print("WHAT IS NOT IN THIS BANK")
    print("=" * 70)
    for line in [
        "No case-based questions (Section E). The free tier returns a question "
        "instead of a passage, 4 attempts out of 4, so it was not asked for.",
        "No social-science map questions, for the same reason.",
        "Coverage is the first chapters of the first books alphabetically -- "
        "40 chapters, not 643.",
        "Bloom level is whatever the model wrote, unverified. A measured run had "
        "every item labelled 'apply', including one-mark recall.",
        "No independent answer verification, so a question with a false premise "
        "would pass. One was caught by hand in an earlier run.",
        "Not merged into the served bank, and not reviewed by a teacher.",
    ]:
        print(f" - {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(report())
