"""Generate a fabricated sandbox question bank.

`docs/question-bank-api.md` section 6 sets the requirement and the reason:

> Sandbox | A fixed read-only subset with **fabricated** questions, so the
> sandbox is never the licensing problem and never leaks the corpus

That is the whole design constraint. A sandbox built from real CBSE questions
would either redistribute third-party content without a rights position, or leak
the corpus the licence question is about. So every question here is invented --
invented stems, invented value points, invented paper codes -- and the output is
structurally identical to the real bank so an SDK written against it works
against the real API unchanged.

The one thing that must NOT be fabricated is the `rights` field. Sandbox records
carry `redistribution: "public"` with an explicit basis, because that is true of
them and false of every real record, and a consumer filtering on rights must see
the difference.

Run:  python scripts/export_qbank_sandbox.py [--count 60] [--out PATH]
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

SUBJECTS = ["Science", "Mathematics", "Social Science", "English"]
CHAPTERS = {
    "Science": ["chemical-reactions", "acids-bases-salts", "metals-nonmetals"],
    "Mathematics": ["real-numbers", "polynomials", "trigonometry"],
    "Social Science": ["nationalism-europe", "resources-development"],
    "English": ["reading-comprehension", "grammar"],
}
TYPES = ["mcq", "very_short_answer", "short_answer", "long_answer", "case_study"]
BLOOM = ["remember", "understand", "apply", "analyze"]
DIFFICULTY = ["easy", "medium", "hard"]

STEMS = [
    "In the fictional town of {place}, a student measures {thing}. Which statement follows?",
    "A sample of {thing} is heated in a sealed vessel at {place} Middle School. Explain the outcome.",
    "Read the passage about {thing} and answer the question that follows.",
    "Derive the relation between {thing} and the reading recorded at {place}.",
    "State one property of {thing} that the passage describes.",
]
THINGS = ["a blue solution", "a suspended mass", "the local rainfall record",
          "a simple pendulum", "the school's water usage"]
PLACES = ["Rampur", "Kothagiri", "Nandipur", "Bhavaninagar", "Sitapur"]

POINTS = [
    "identifies the correct quantity and its unit",
    "states the relationship in words before applying it",
    "substitutes the given values without arithmetic error",
    "interprets the result in the context of the question",
    "notes one assumption the calculation depends on",
]


def build(count: int, seed: int = 20260917) -> list[dict]:
    """Deterministic: the same seed produces the same sandbox, so an SDK test
    written against it does not break every regeneration."""
    rng = random.Random(seed)
    out: list[dict] = []

    for i in range(count):
        subject = SUBJECTS[i % len(SUBJECTS)]
        grade = 10
        marks = rng.choice([1, 1, 2, 3, 5])
        qtype = TYPES[i % len(TYPES)]
        stem = rng.choice(STEMS).format(thing=rng.choice(THINGS),
                                        place=rng.choice(PLACES))
        if qtype == "mcq":
            stem += " (a) first option (b) second option (c) third option (d) fourth option"

        # A plausible-looking paper code, in a series CBSE does not use (99),
        # so a fabricated record can never be mistaken for a real one.
        paper_code = "99/{}/{}/sandbox".format(1 + (i % 5), 1 + (i % 3))
        n_points = 1 if marks == 1 else min(3, max(1, marks // 1))
        points = [
            {"id": "sb:q:{}:mp{}".format(i, j + 1),
             "description": POINTS[(i + j) % len(POINTS)],
             "marks": max(1, marks // n_points),
             "keyword": "", "isRequired": False, "synonyms": []}
            for j in range(n_points)
        ]

        out.append({
            "id": "sbx:q:src:{:024x}:{}".format(i, i + 1),
            "questionBankId": "src:{:024x}".format(i),
            "subject": subject,
            "grade": grade,
            "chapterIds": [CHAPTERS[subject][i % len(CHAPTERS[subject])]],
            "competencyIds": [],
            "bloomLevel": BLOOM[i % len(BLOOM)],
            "difficulty": DIFFICULTY[i % len(DIFFICULTY)],
            "type": qtype,
            "stem": stem,
            "stemLatex": "",
            "parts": [],
            "answerScheme": {
                "totalMarks": marks,
                "markingPoints": points,
                "rubricLevels": [],
                "commonErrors": [],
                "alternativeAnswers": [],
                "modelAnswer": "",
                "modelAnswerLatex": "",
                "hasPartialCredit": len(points) > 1,
                "metadata": {},
                # Marked as its own provenance so nobody mistakes a sandbox
                # scheme for an official one in a response body.
                "provenance": "sandbox",
                "sourcePaperCode": paper_code,
                "sourceDocumentId": "sandbox",
            },
            "estimatedTimeMinutes": max(1, marks * 2),
            "marks": marks,
            "language": "en",
            "source": "ai_generated",
            "qualityScore": 0.7,
            "tags": [CHAPTERS[subject][i % len(CHAPTERS[subject])].replace("-", " ").title()],
            "createdAt": "2026-09-17T00:00:00Z",
            "updatedAt": "2026-09-17T00:00:00Z",
            "metadata": {"sandbox": True},
            "diagramAssetId": None, "mapAssetId": None,
            "graphAssetId": None, "tableAssetId": None,
            # The one field that must NOT be fabricated. These really are
            # freely redistributable because a program wrote them; every real
            # record says "unknown" because no rights position exists.
            "rights": {
                "origin": "AcademicOS sandbox generator",
                "redistribution": "public",
                "basis": "machine-generated; contains no third-party content",
                "attribution": "",
            },
            "provenance": {
                "sourceDocumentId": "sandbox",
                "pageNumber": None,
                "boundingBox": None,
                "method": "generated",
                "confidence": None,
            },
            "calibration": {"measured": False, "sampleSize": 0,
                            "facility": None, "discrimination": None,
                            "basis": "assigned"},
            "version": 1,
            "reviewState": "published",
            "supersededBy": None,
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=60)
    ap.add_argument("--out", default=str(REPO / "academicos-data" / "sandbox" / "questions.json"))
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    records = build(args.count)
    payload = {
        "questions": records,
        "exportedCount": len(records),
        "sandbox": True,
        "notice": ("Fabricated data for API evaluation only. Contains no CBSE or "
                   "third-party content. Not for classroom use."),
        "schemeCoverage": 1.0,
    }
    text = json.dumps(payload, ensure_ascii=False, indent=1)

    if args.check:
        print(f"{len(records)} sandbox questions, {len(text):,} chars (not written)")
        return 0

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"wrote {len(records)} fabricated questions to {out.relative_to(REPO)}")
    print(f"  {out.stat().st_size / 1000:.1f} KB")
    real = [r for r in records if r["rights"]["redistribution"] != "public"]
    print(f"  records not marked publicly redistributable: {len(real)} (must be 0)")
    return 1 if real else 0


if __name__ == "__main__":
    raise SystemExit(main())
