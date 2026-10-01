"""Export every chapter's generation jobs, ready for the cloud worker.

The worker is deliberately dumb. It sends a prompt, gets a completion, stores the
raw result. It does not know what a section is, what the board's marks are, or how
many questions a chapter should carry -- all of that is decided here, in Python,
where the blueprint and its tests live. Two reasons:

* the CBSE format is the part with 31 tests against it, and re-implementing it in
  TypeScript would leave the worker running on a copy nobody re-tests;
* a prompt built here is the same prompt the tests and the local runs use, so what
  the worker sends is what was verified.

So this script writes, per chapter, the exact system text, user text and schema for
each section item, and the worker just makes the calls. Validation stays here too:
the worker stores raw completions and the local side judges them, because the
validator is where the interesting failures live.

Writes, under --out:

    manifest.json        the job list, and the totals
    prompts/<code>-<nn>-<i>.json   one job per section item

Then upload with `wrangler r2 object put`, and let the worker's cron do the rest.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import gen_cbse_chapter as G                       # noqa: E402
from academicos.corpus import cbse_blueprint as bp  # noqa: E402
from academicos.corpus import cbse_generate as cg   # noqa: E402
from academicos.corpus import textbook as tb            # noqa: E402

# A 12-mark slice of the paper. Twelve is the unit that makes a chapter's questions
# add up to a book without any one chapter carrying a whole paper.
DEFAULT_MARKS = 12

# Free tier is 10,000 neurons a day. A chapter at 12 marks measured ~913 neurons on
# the 70B, so ten chapters a day is the whole budget; the worker stops rather than
# overrunning into a paid tier nobody asked for.
CHAPTERS_PER_RUN = 8

"""
`--sections` picks what goes to the free tier. The split is measured, not guessed:

  cloudflare free (llama-3.3-70b, via the Worker AI binding, 10k neurons/day)
      every section except E. On the Real Numbers chapter it produced sections
      A-D cleanly -- 3 of 3 schema-conforming runs, correct marks, correct marking
      point counts, and `case_study` was its only systematic failure.

  deepseek (paid, $0.27/$0.40 per million)
      section E. The free model returns a question where a case-based section
      needs a passage first, and it did so 4 times out of 4. Gemini 2.5 Flash
      returned a correct 121-word passage for the same input; DeepSeek is the
      remaining candidate at 1/6th of Gemini's output price and is the next thing
      to measure on this case.

So the free tier is not a degraded bank -- it is the bulk of one, and it is the
part that has been proven. Only the case-based section needs a paid model.
"""

SKIP_SECTIONS: frozenset[str] = frozenset()

# What the free tier is asked for, and what is held back for a paid model.
FREE_TIER_SECTIONS = frozenset({bp.MCQ, bp.VSA, bp.SA, bp.LA,
                                bp.ASSERTION_REASON, bp.MAP})
PAID_SECTIONS = frozenset({bp.CASE})


def jobs_for_chapter(book_code: str, number: int, mark_budget: int,
                     skip: frozenset[str] = SKIP_SECTIONS) -> list[dict]:
    """One job per section item, with the prompt already built."""
    book = G.book_registry().get(book_code)
    if not book:
        return []
    subject = tb.bank_subject(book.get("subject"))
    grade = int(book.get("class") or 0)
    if not grade:
        return []
    pdf = G.chapter_pdf(book_code, number)
    if not pdf.is_file():
        return []

    known = G.taxonomy_chapters().get(book_code, {}).get(number) or {}
    topics = G.topics_for(book_code, number)
    chapter_name = known.get("name") or f"Chapter {number}"
    chapter_id = known.get("id") or tb.chapter_id(subject, grade, chapter_name)

    try:
        chapter = cg.read_chapter(
            pdf, book_code=book_code, subject=subject, grade=grade,
            language=book.get("language") or "en", number=number,
            title=chapter_name)
    except Exception as exc:                        # a PDF that will not open
        return [{"error": f"unreadable: {exc}", "code": book_code,
                 "chapter": number}]
    if not chapter.pages:
        return []

    if topics:
        plan = cg.plan_for_chapter(subject, grade, topics, mark_budget)
    else:
        # No tree names this chapter: cover the section mix once, untopiced.
        plan = []
        for section in bp.for_paper(subject, grade).sections:
            for _ in range(max(1, round(section.marks / mark_budget))):
                plan.append((section, ""))

    if skip:
        plan = [(s, t) for s, t in plan if s.qtype not in skip]

    jobs: list[dict] = []
    for index, (section, topic) in enumerate(plan):
        system, schema, user = cg.build_prompt(
            chapter, section, topic, count=1, bank_subject=subject, topics=topics)
        jobs.append({
            "index": index,
            "code": book_code, "chapter": number,
            "subject": subject, "grade": grade,
            "language": book.get("language") or "en",
            "chapterId": chapter_id, "chapterName": chapter_name,
            "topic": topic,
            "sectionKey": section.key, "sectionName": section.name,
            "qtype": section.qtype, "marks": section.marks,
            "model": G.GEMINI_MODEL if os.environ.get("GEN_CBSE_GEMINI") else G.WORKERS_MODEL,
            "system": system, "user": user, "schema": schema,
        })
    return jobs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path,
                    default=Path(r"C:\Users\varsh\AppData\Local\Temp\opencode\cbse-jobs"))
    ap.add_argument("--marks", type=int, default=DEFAULT_MARKS)
    ap.add_argument("--chapters", type=int, default=CHAPTERS_PER_RUN,
                    help="chapters to export this run; the free tier affords ~10")
    ap.add_argument("--book", help="one book only, for a test")
    ap.add_argument("--from-grade", type=int, default=10,
                    help="only chapters at or above this grade (default: 10)")
    ap.add_argument("--to-grade", type=int, default=10,
                    help="only chapters at or below this grade (default: 10)")
    ap.add_argument("--tier", choices=["free", "paid", "all"], default="free",
                    help="free: sections A-D, for the Cloudflare free tier. "
                         "paid: Section E only, for a model that can set it. "
                         "all: everything, on one model")
    args = ap.parse_args()

    skip = {"free": PAID_SECTIONS, "paid": FREE_TIER_SECTIONS,
            "all": frozenset()}[args.tier]
    books = [args.book] if args.book else sorted(G.book_registry())
    exported: list[dict] = []
    skipped: list[dict] = []

    for book_code in books:
        folder = G.BOOKS / book_code
        if not folder.is_dir():
            continue
        numbers = sorted(
            int(p.stem[len(book_code):]) for p in folder.glob(f"{book_code}*.pdf")
            if p.stem[len(book_code):].isdigit())
        # Grade order, not alphabetical book order. Grade 10 is a board paper with
        # a full A-E section structure, so a chapter of it yields long answers and
        # case studies as well as objective items -- which makes it worth a scarce
        # daily neuron budget far more than a Grade 1 chapter, where skipping the
        # case section leaves only MCQ and very-short-answer. The alphabetical
        # order this replaces started at aejm1 and produced 176 questions, all of
        # them Grade 1.
        book_meta = G.book_registry().get(book_code) or {}
        book_grade = int(book_meta.get("class") or 0)
        if book_grade and not (args.from_grade <= book_grade <= args.to_grade):
            continue
        for number in numbers:
            jobs = jobs_for_chapter(book_code, number, args.marks, skip)
            if not jobs or "error" in jobs[0]:
                skipped.append({"code": book_code, "chapter": number,
                                "reason": (jobs[0].get("error") if jobs else "no jobs")})
                continue
            exported.append({"code": book_code, "chapter": number,
                             "jobs": len(jobs),
                             "subject": jobs[0]["subject"], "grade": jobs[0]["grade"],
                             "chapterId": jobs[0]["chapterId"]})
            if len(exported) >= args.chapters:
                break
        if len(exported) >= args.chapters:
            break

    if not exported:
        print("nothing exported")
        return 2

    args.out.mkdir(parents=True, exist_ok=True)
    prompts = args.out / "prompts"
    prompts.mkdir(exist_ok=True)

    entries = []
    for entry in exported:
        jobs = jobs_for_chapter(entry["code"], entry["chapter"], args.marks, skip)
        for job in jobs:
            name = f"{job['code']}-{job['chapter']:02d}-{job['index']}.json"
            (prompts / name).write_text(
                json.dumps(job, ensure_ascii=False), encoding="utf-8")
            entries.append({"key": f"prompts/{name}",
                            "raw": f"raw/{job['code']}-{job['chapter']:02d}-"
                                   f"{job['index']}.json",
                            "code": job["code"], "chapter": job["chapter"],
                            "sectionKey": job["sectionKey"],
                            "qtype": job["qtype"], "marks": job["marks"]})

    (args.out / "manifest.json").write_text(json.dumps({
        "model": G.WORKERS_MODEL,
        "markBudget": args.marks,
        "chapters": exported,
        "entries": entries,
        "skipped": skipped,
        "tier": args.tier,
        "sectionsIncluded": sorted(PAID_SECTIONS - skip if args.tier == "free"
                                   else FREE_TIER_SECTIONS - skip if args.tier == "paid"
                                   else set(bp.QUESTION_TYPES)),
        "sectionsSkipped": sorted(skip),
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    total = len(entries)
    subjects: dict[str, int] = {}
    for e in entries:
        subjects[e["qtype"]] = subjects.get(e["qtype"], 0) + 1
    print(f"{len(exported)} chapters, {total} jobs -> {args.out}")
    print("by section type: " + ", ".join(f"{k} {v}" for k, v in sorted(subjects.items())))
    if skipped:
        print(f"skipped {len(skipped)} chapters that could not be read")
    print()
    print("next:")
    print(f"  wrangler r2 object put <bucket>/manifest.json "
          f"--file={args.out / 'manifest.json'} --remote")
    print(f"  wrangler r2 object put <bucket>/prompts --file={prompts} "
          f"--remote")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
