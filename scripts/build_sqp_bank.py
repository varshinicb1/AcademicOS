"""Build a question-bank file from the downloaded CBSE SQP+MS pairs.

The SQP parser has existed and worked (38 of 38 questions on the Class X Social
Science paper) since 2026-09-18 without being wired into anything, so the fourth
coverage gap in the PRD's §0 critical path was "the SQP parser is still not wired
in". This wires it in.

Why this source matters more than its size suggests
---------------------------------------------------
The CBE item banks cover three subjects: Maths, Science, English. Social Science
has no coverage at all, and the SQP+MS pairs are where it comes from. Three pairs
are downloaded today -- SocialScience, HindiCourseA, HindiCourseB -- so this
build is small. The pipeline is the deliverable; adding subjects is then a matter
of downloading more pairs with `scripts/ingest_sqp_ms.py`.

The Hindi pairs parse to nothing, and that is expected
------------------------------------------------------
Both Hindi files extract through a legacy font encoding, so the text is not
Unicode and no parser recovers it -- that was established when they were
downloaded and is recorded in `docs/question-bank-api.md`. They are skipped here
rather than counted as failures, and the skip is printed so the shortfall is
visible rather than implied (PRD rule Q4).

The gates, unchanged from the CBE build
---------------------------------------
  * Q1 -- no answer key, no question. `parse_pair` already refuses to join a
    question with a scheme entry it cannot key, so anything emitted has a real
    CBSE answer.
  * No mark value, no question. A mark-less question corrupts any distribution
    it appears in.
  * An implausible mark value is a block total. Same ceiling as the CBE build.

Run:  python scripts/build_sqp_bank.py [--check]
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

from academicos.corpus import cbse_sqp                      # noqa: E402
from build_cbe_bank import _MAX_SINGLE_QUESTION_MARKS       # noqa: E402

SRC = REPO / "academicos-data" / "corpus" / "cbse-sqp"
OUT = SRC / "questions.json"

# Paper codes look like "ClassX_2025_26"; the grade is readable from the name.
_GRADE = {"ClassX": 10, "ClassXII": 12}

SUBJECT_LABEL = {
    "SocialScience": "Social Science",
    "HindiCourseA": "Hindi",
    "HindiCourseB": "Hindi",
}


def _record(item, *, subject: str, grade: int, year: str) -> dict:
    """The bank shape, matching `cbse_cbe.to_bank_record` so one reader serves both."""
    q = item.question
    qid = f"cbse:sqp:{year}:{subject}:{q.key}"
    marks = q.marks
    return {
        "id": qid,
        "questionBankId": f"cbse-sqp:{year}:{subject}",
        "subject": subject,
        "grade": grade,
        "chapterIds": [],
        "topic": "",                      # SQP items carry no learning-ladder code
        "difficulty": "medium",
        "type": "mcq" if q.options else "short_answer",
        "stem": q.text,
        "stemLatex": "",
        "parts": [
            {"id": f"{qid}:p{i}", "partNumber": i, "text": opt, "marks": 0,
             "answerType": "singleChoice", "alternativeAnswers": []}
            for i, opt in enumerate(q.options, 1)
        ],
        "answerScheme": {
            "totalMarks": marks,
            "markingPoints": ([{"text": item.answer, "marks": marks}]
                              if item.answer else []),
            "rubricLevels": [],
            "commonErrors": [],
            "alternativeAnswers": [],
            "modelAnswer": "" if q.options else item.answer,
            "modelAnswerLatex": "",
            "hasPartialCredit": bool(item.answer and not q.options),
            "metadata": {},
            # Authority-provided: the answer came from the scheme file CBSE
            # publishes alongside the paper, not from an inference.
            "provenance": "cbse_marking_scheme",
            "sourcePaperCode": "",
            "sourceDocumentId": f"cbse-sqp:{year}:{subject}",
        },
        "estimatedTimeMinutes": max(1, marks * 2),
        "marks": marks,
        "language": "en",
        "source": "cbse_sample_paper",
        "qualityScore": 0.95,             # board-published, not extracted
        "tags": ["cbse", "sample-paper", year],
        "createdAt": "2026-09-18T00:00:00Z",
        "updatedAt": "2026-09-18T00:00:00Z",
        "metadata": {
            "questionKey": q.key,
            "alternativeOf": q.alternative_of,
            "options": len(q.options),
            # The SQP/MS split: this question's stem and its scheme answer live
            # in two different documents, joined on the question number.
            "joinedFrom": "sqp+ms-pair",
        },
        "diagramAssetId": None, "mapAssetId": None,
        "graphAssetId": None, "tableAssetId": None,
        "rights": {
            "origin": "CBSE",
            "redistribution": "unknown",
            "basis": "",
            "attribution": ("Central Board of Secondary Education, sample "
                            "question paper and marking scheme"),
        },
        "provenance": {
            "sourceDocumentId": f"cbse-sqp:{year}:{subject}",
            "pageNumber": q.page or None,
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    if not SRC.exists():
        print(f"no SQP pairs in {SRC}; run scripts/ingest_sqp_ms.py first",
              file=sys.stderr)
        return 1

    records: list[dict] = []
    per_pair: list[tuple[str, int, int]] = []
    skipped: list[str] = []

    for year_dir in sorted(p for p in SRC.iterdir() if p.is_dir()):
        year = year_dir.name
        # Exact match on the first segment, NOT `startswith`.
        #
        # `"ClassXII_2025_26".startswith("ClassX")` is True, so a prefix match
        # silently labelled every Class XII paper as Class 10 -- and dict
        # ordering put "ClassX" first, so it always won. Caught by reading the
        # per-subject output: Applied-Maths, EnglishCore and HomeScience were
        # all reported as class 10 when they are XII papers.
        grade = _GRADE.get(year.split("_")[0], 0)
        for sqp in sorted(year_dir.glob("*-SQP.pdf")):
            stem_name = sqp.name[: -len("-SQP.pdf")]
            ms = year_dir / f"{stem_name}-MS.pdf"
            if not ms.exists():
                skipped.append(f"{year}/{stem_name}: no matching MS")
                continue
            joined, stats = cbse_sqp.parse_pair(sqp, ms)
            subject = SUBJECT_LABEL.get(stem_name, stem_name)
            kept = 0
            for item in joined:
                q = item.question
                if not q.marks or q.marks > _MAX_SINGLE_QUESTION_MARKS:
                    continue                       # gate: no mark value / block total
                if not item.answer.strip():
                    continue                       # gate Q1, belt and braces
                records.append(_record(item, subject=subject, grade=grade, year=year))
                kept += 1
            per_pair.append((f"{year}/{stem_name}", stats["joined"], kept))
            if kept == 0:
                skipped.append(f"{year}/{stem_name}: 0 usable (see parse stats)")

    by_sg = collections.Counter((r["subject"], r["grade"]) for r in records)
    spread = collections.Counter(r["marks"] for r in records)

    print(f"pairs parsed   : {len(per_pair)}")
    print(f"{'pair':<38} {'joined':>7} {'served':>7}")
    for name, joined_n, kept in per_pair:
        print(f"  {name:<36} {joined_n:>7} {kept:>7}")
    print()
    print(f"records served : {len(records)}")
    for (s, g), n in sorted(by_sg.items()):
        print(f"    {s:<16} class {g:<4} {n:>4}")
    print(f"marks spread   : {dict(sorted(spread.items()))}")
    print(f"  max mark     : {max(spread) if spread else 0} "
          f"(ceiling {_MAX_SINGLE_QUESTION_MARKS})")
    if skipped:
        print("skipped / empty:")
        for s in skipped:
            print(f"    {s}")

    if args.check:
        print("\n--check: nothing written")
        return 0

    OUT.write_text(json.dumps({
        "questions": records,
        "exportedCount": len(records),
        "source": "cbse-sample-papers-marking-schemes",
        "notice": ("CBSE sample question papers joined to the marking scheme "
                   "published alongside them. Coverage follows what has been "
                   "downloaded, not what CBSE publishes."),
        "rights": {
            "origin": "CBSE",
            "redistribution": "unknown",
            "basis": "",
            "note": "No redistribution position obtained. See "
                    "docs/question-bank-api.md section 2.",
        },
        "builtAt": datetime.now(timezone.utc).isoformat(),
    }, ensure_ascii=False), encoding="utf-8")
    print(f"\nwrote {OUT.relative_to(REPO)}  ({OUT.stat().st_size / 1000:.1f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
