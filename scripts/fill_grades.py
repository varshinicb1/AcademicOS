"""Fill the bank for chosen grades and subjects, by asking the Worker for chapters.

The batch path needed a `manifest.json` naming one uploaded object per job, which
meant 1,066 `wrangler r2 object put` calls before a single question could be asked
for -- half an hour of subprocess launches, and it was still running when it was
killed. That was a bad shape for the problem.

The interactive Worker already does the whole job for one chapter: it reads the
chapter text out of R2, builds the prompt from the blueprint, generates, validates,
dedupes and records the paper. So the batch is just this file, looping over
chapters and calling it. Nothing to upload, and a run can be stopped and resumed
because the papers accumulate in R2.

    python scripts/fill_grades.py --grades 9 10 --subjects Mathematics Science
    python scripts/fill_grades.py --status
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

BASE = "https://qbank.cbvarshini1.workers.dev"
# A bare urllib request is answered with 403: Cloudflare reads the default agent
# as a bot. Identical URL, identical auth, only the agent differs.
UA = {"Content-Type": "application/json", "User-Agent": "academicos-fill/1"}


def call(path: str, payload: dict | None = None, timeout: int = 300) -> dict:
    url = f"{BASE}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=data, headers=UA,
                                     method="POST" if data else "GET")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grades", type=int, nargs="+", default=[9, 10])
    ap.add_argument("--subjects", nargs="+", default=[
        "Mathematics", "Science", "Social Science", "English", "Hindi"])
    ap.add_argument("--marks", type=int, default=10,
                    help="marks of paper wanted from each chapter")
    ap.add_argument("--chapter", type=int, help="one chapter number, for a test")
    ap.add_argument("--sleep", type=float, default=2.0,
                    help="seconds between chapters; Gemini's free tier is 20 rpm")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--max", type=int, default=0, help="stop after N chapters")
    args = ap.parse_args()

    if args.status:
        health = call("/api/health", timeout=120)
        papers = call("/api/papers", timeout=300)
        print(f"provider      : {health['provider']}")
        print(f"neurons today : {health['neuronsToday']} / {health['freeBudget']}")
        print(f"usd today     : {health.get('usdToday')}")
        print(f"papers held   : {papers.get('count')}")
        held = Counter()
        for paper in papers.get("papers") or []:
            held[(paper.get("grade"), paper.get("subject"))] += 1
        if held:
            print("by grade and subject:")
            for (grade, subject), count in sorted(held.items(), key=lambda kv: str(kv[0])):
                print(f"   {grade:>3}  {subject:<16} {count}")
        return 0

    corpus = call("/api/corpus", timeout=300)
    books = [b for b in corpus.get("books") or []
             if int((b.get("book") or {}).get("class") or 0) in args.grades
             and (b.get("book") or {}).get("subject") in args.subjects]
    books.sort(key=lambda b: (int(b["book"]["class"]), b["book"]["subject"],
                              b["book"]["code"]))
    if not books:
        print(f"no books match grades {args.grades} subjects {args.subjects}")
        return 2

    chapters = [(b["book"]["code"], c)
                for b in books for c in (b.get("chapters") or [])]
    if args.chapter:
        chapters = [(c, n) for c, n in chapters if int(n) == args.chapter]
    print(f"{len(books)} books, {len(chapters)} chapters, "
          f"grades {args.grades}, subjects {args.subjects}")
    print()

    totals = {"generated": 0, "refused": 0, "calls": 0, "usd": 0.0}
    reasons: Counter = Counter()
    done = 0
    for code, chapter in chapters:
        if args.max and done >= args.max:
            break
        health = call("/api/health", timeout=120)
        # The free allowance is the gate that matters; the paid path has no ceiling.
        if health["provider"] != "gemini" and health["neuronsToday"] >= health["freeBudget"]:
            print(f"free allowance spent ({health['neuronsToday']}/"
                  f"{health['freeBudget']}); stopping cleanly")
            break
        done += 1
        try:
            result = call("/api/generate", {
                "code": code, "chapter": str(chapter), "count": args.marks,
            })
        except urllib.error.HTTPError as exc:
            print(f"  {code} ch{chapter}: HTTP {exc.code} {exc.body[:80]!r}")
            continue
        except (urllib.error.URLError, TimeoutError) as exc:
            print(f"  {code} ch{chapter}: {str(exc)[:80]}")
            continue

        totals["generated"] += result.get("generated", 0)
        totals["refused"] += len(result.get("refusals") or [])
        totals["calls"] += 1
        totals["usd"] += result.get("usd", 0.0)
        for refusal in result.get("refusals") or []:
            reasons[str(refusal.get("reason"))] += 1
        flag = " (free fallback)" if result.get("fellBack") else ""
        print(f"  {code} ch{str(chapter):<3} {result.get('generated', 0):>3} kept  "
              f"{len(result.get('refusals') or []):>3} refused  "
              f"${result.get('usd', 0.0):.4f}{flag}")
        time.sleep(args.sleep)

    print()
    print(f"chapters called : {totals['calls']}")
    print(f"questions kept  : {totals['generated']}")
    print(f"refused         : {totals['refused']}")
    print(f"paid spend      : ${totals['usd']:.4f}")
    if reasons:
        print("refusals by reason:")
        for reason, count in reasons.most_common(12):
            print(f"   {count:>5}  {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
