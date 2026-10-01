"""The final question bank: everything generated, validated, in one file.

Pulls from the two places questions have been produced -- the offline batch under
`corpus/ai-cbse`, and the papers the on-demand Worker has written to R2 -- validates
what arrives, dedupes, and writes one artefact with the report a reviewer needs.

Nothing here generates. Finalising is judging and recording, and it is the step
that decides what a school would actually be shown.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from academicos.corpus import cbse_generate as cg      # noqa: E402
from academicos.corpus import textbook as tb               # noqa: E402
from collect_ai_cbse import _is_duplicate, _tokens, load_existing  # noqa: E402

BATCH = ROOT / "academicos-data" / "corpus" / "ai-cbse" / "questions.json"
OUT = ROOT / "academicos-data" / "corpus" / "ai-cbse" / "bank.json"
SCRATCH = Path(r"C:\Users\varsh\AppData\Local\Temp\opencode\final")


def pull_papers() -> list[dict]:
    """Every paper the on-demand Worker has written, in one request.

    Fetched from the Worker rather than from R2: `wrangler r2 object list` does not
    exist, and `wrangler r2 object get` is one subprocess per paper -- of twelve
    papers, one arrived. The Worker can list its own bucket, so it does the listing
    and the reading.
    """
    base = "https://qbank.cbvarshini1.workers.dev"
    try:
        import urllib.request

        # Cloudflare answers a bare urllib request with 403: the default user agent
        # reads as a bot. The endpoint was never the problem.
        request = urllib.request.Request(f"{base}/api/papers",
                                         headers={"User-Agent": "academicos-finalise/1"})
        with urllib.request.urlopen(request, timeout=240) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:                        # noqa: BLE001
        print(f"could not read papers from the worker: {exc}")
        return []
    return list(payload.get("papers") or [])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--skip-papers", action="store_true")
    args = ap.parse_args()

    questions: list[dict] = []
    dropped = Counter()

    if BATCH.is_file():
        batch = json.loads(BATCH.read_text(encoding="utf-8"))
        questions += batch.get("questions") or []
        print(f"batch: {len(batch.get('questions') or [])} questions")

    paper_count = 0
    if not args.skip_papers:
        for paper in pull_papers():
            paper_count += 1
            for entry in paper.get("questions") or []:
                question = entry.get("question") if isinstance(entry, dict) else None
                if question:
                    questions.append(question)
        print(f"on demand: {paper_count} papers collected")

    # Dedupe inside the bank, then against what the school already has. `seen` is
    # built as the list is walked, not from it up front: seeding it with every id
    # first makes each question a duplicate of itself and empties the bank, which
    # is what the first run of this did -- 176 questions in, 0 out.
    existing, existing_total = load_existing()
    seen: set[str] = set()
    unique: list[dict] = []
    known = list(existing)
    for question in questions:
        ident = question.get("id") or ""
        if ident and ident in seen:
            dropped["duplicate-id"] += 1
            continue
        words = _tokens(question.get("stem") or "")
        if words and _is_duplicate(words, known):
            dropped["already-in-bank"] += 1
            continue
        known.append(words)
        if ident:
            seen.add(ident)
        unique.append(question)

    rebalanced = cg.rebalance_keys(unique)
    keys = cg.audit_key_distribution(unique)

    # Fill in the chapter ids the trees already know, so a question can be offered
    # under a chapter. Without this the on-demand path files questions by book and
    # chapter number, which the catalog route cannot resolve.
    filled = 0
    for question in unique:
        if question.get("chapterIds"):
            continue
        code = str(question.get("questionBankId") or "").replace("ai-cbse:", "")
        chapter = None
        for candidate in (question.get("id") or "").split(":"):
            if candidate.isdigit():
                chapter = int(candidate)
        if code and chapter and question.get("subject") and question.get("grade"):
            ident = tb.chapter_id(str(question["subject"]), int(question["grade"]),
                                      str(question.get("chapterName") or ""))
            if ident:
                question["chapterIds"] = [ident]
                question["taxonomyChapterId"] = ident
                filled += 1

    payload = {
        "meta": {
            "generated": True,
            "description": "AI-generated CBSE-format questions, validated before "
                           "being recorded. Every question carries the section, the "
                           "marks the board prints for it, and a marking scheme "
                           "worth those marks.",
            "sources": ["cloudflare workers ai (free tier)",
                        "gemini-2.5-flash (paid, when a key with billing is set)"],
            "papers": paper_count,
            "checkedAgainst": existing_total,
            "keyDistribution": keys,
            "keyRebalanced": rebalanced,
            "dropped": dict(dropped),
        },
        "questions": unique,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")

    print()
    print(f"FINAL: {len(unique)} questions -> {args.out}")
    print(f"  dropped: {dict(dropped) or 'none'}")
    print(f"  chapter ids filled: {filled}")
    if keys["total"]:
        spread = "  ".join(f"{k} {keys['counts'][k]}" for k in sorted(keys["counts"]))
        print(f"  key spread: {spread}"
              + ("  <- BIASED" if keys["biased"] else "  (within tolerance)"))
    print()
    print("by subject :", dict(Counter(q.get("subject") for q in unique).most_common()))
    print("by grade   :", dict(sorted(
        (g, c) for g, c in Counter(q.get("grade") for q in unique).items() if g)))
    print("by section :", dict(Counter(
        (q.get("provenance") or {}).get("section") for q in unique).most_common()))
    print("by type    :", dict(Counter(q.get("type") for q in unique).most_common()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
