"""Seed the cloud corpus, so the teacher never waits for a batch.

Uploads, into R2, the things the interactive product reads at request time:

  meta/<code>.json     book code, class, subject, title, language
  text/<code>.json     every chapter of the book, one object per book
  blueprint.json       the CBSE section formats, exported from cbse_blueprint so
                       there is one source of truth and the Worker cannot drift
  bank/existing.json   the questions already held, in a compact form, so a
                       generated question can be checked against them

One object per book rather than one per chapter: 55 uploads instead of 572, which
is the difference between a minute and a quarter of subprocess launches, and R2 has
no per-object count to optimise for. The whole corpus is 14MB, comfortably inside
the free tier.

Nothing here generates a question. The point is that the bank is not filled in
advance -- a teacher asks for the paper they want, and only that costs anything.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import gen_cbse_chapter as G                          # noqa: E402
from academicos.corpus import cbse_blueprint as bp     # noqa: E402

BUCKET = "academicos-qgen"
PIPELINE = Path(r"C:\Users\varsh\OneDrive\Documents\Sarvam\bank-pipeline")
CHAPTERS_TEXT = PIPELINE / "chapters_text"
CORPUS = ROOT / "academicos-data" / "corpus"
WRANGLER = r"C:\nvm4w\nodejs\wrangler.cmd"


def put(key: str, local: Path) -> bool:
    result = subprocess.run(
        [WRANGLER, "r2", "object", "put", f"{BUCKET}/{key}",
         f"--file={local}", "--remote"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(ROOT), timeout=300)
    return result.returncode == 0


def put_json(key: str, payload: object, tmp: Path) -> bool:
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return put(key, tmp)


def blueprint_payload() -> dict:
    """Every registered format, as the Worker reads it.

    Exported from the Python module rather than retyped, because the whole point of
    the format living in code is that there is one copy of it -- and a hand-kept
    JavaScript twin would drift the first time somebody corrected a section count.
    """
    out: dict[str, dict] = {}
    for (subject, band), blueprint in bp._BLUEPRINTS.items():
        out[f"{subject}|{band}"] = {
            "subject": blueprint.subject,
            "gradeBand": blueprint.grade_band,
            "theoryMarks": blueprint.theory_marks,
            "durationMinutes": blueprint.duration_minutes,
            "notes": blueprint.notes,
            "sections": [
                {"key": s.key, "name": s.name, "qtype": s.qtype,
                 "count": s.count, "marks": s.marks, "answerWords": s.answer_words,
                 "internalChoice": s.internal_choice, "carriesSource": s.carries_source}
                for s in blueprint.sections
            ],
        }
    return out


def existing_bank_payload(limit_per_corpus: int = 4000) -> dict:
    """Every question already held, reduced to what a duplicate check needs.

    Only the stem. A generated question is compared on its content words, so the
    options, the marking scheme and the provenance are dead weight in a file the
    Worker has to hold in memory on every request.
    """
    out: list[list[str]] = []
    total = 0
    for path in sorted(CORPUS.glob("*/questions.json")):
        if path.parent.name == "ai-cbse":
            continue
        try:
            questions = json.loads(path.read_text(encoding="utf-8")).get("questions") or []
        except (OSError, ValueError):
            continue
        for question in questions[:limit_per_corpus]:
            stem = question.get("stem")
            if not stem:
                content = question.get("content")
                stem = (content or {}).get("question_text") if isinstance(content, dict) else None
            if stem and isinstance(stem, str):
                out.append([question.get("subject") or "",
                            str(question.get("grade") or ""), stem])
                total += 1
    return {"count": total, "rows": out}


def main() -> int:
    global BUCKET

    ap = argparse.ArgumentParser()
    ap.add_argument("--bucket", default=BUCKET)
    ap.add_argument("--tmp", type=Path,
                    default=Path(r"C:\Users\varsh\AppData\Local\Temp\opencode\seed"))
    ap.add_argument("--skip-text", action="store_true")
    args = ap.parse_args()

    BUCKET = args.bucket
    tmp = args.tmp
    uploaded = failed = 0

    print("blueprint ..", end=" ", flush=True)
    formats = blueprint_payload()
    print(f"{len(formats)} formats", end=" ")
    print("ok" if put_json("blueprint.json", formats, tmp / "blueprint.json")
          else "FAILED")
    uploaded += 1

    print("existing bank ...", end=" ", flush=True)
    bank = existing_bank_payload()
    print(f"{bank['count']} questions", end=" ")
    print("ok" if put_json("bank/existing.json", bank, tmp / "bank.json")
          else "FAILED")
    uploaded += 1

    if not args.skip_text:
        registry = G.book_registry()
        print(f"\ntext: {len(registry)} books")
        for index, (code, book) in enumerate(sorted(registry.items()), 1):
            folder = CHAPTERS_TEXT / code
            if not folder.is_dir():
                print(f"   {index:>3}. {code}: no chapter text on disk, skipped")
                continue
            chapters: dict[str, str] = {}
            for text_file in sorted(folder.glob("*.txt")):
                chapters[text_file.stem] = text_file.read_text(
                    encoding="utf-8", errors="replace")
            meta = {"code": code, "book": book,
                    "chapters": sorted(chapters, key=lambda k: (len(k), k))}
            ok_book = put_json(f"meta/{code}.json", meta, tmp / f"{code}.meta.json")
            ok_text = put_json(f"text/{code}.json", chapters, tmp / f"{code}.json")
            if ok_book and ok_text:
                uploaded += 2
                print(f"   {index:>3}. {code}: {len(chapters):>3} chapters"
                      f"  {book.get('subject')} {book.get('class')}"
                      f" [{book.get('language')}]")
            else:
                failed += 1
                print(f"   {index:>3}. {code}: UPLOAD FAILED")

    print(f"\ndone: {uploaded} objects uploaded, {failed} books failed, $0")
    print("The Worker reads these at request time; nothing is pre-generated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
