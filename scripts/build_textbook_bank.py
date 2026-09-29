"""Build the NCERT textbook source bank from chapter transcriptions
(docs/textbook-exercise-format.md).

    python scripts/build_textbook_bank.py --in <folder of chapter JSONs> --text <folder of chapter texts> \\
        [--out academicos-data/corpus/ncert-textbook/questions.json] [--check]

Each chapter JSON `<code>-<nn>.json` is checked against that chapter's own text
(`<text>/<code>/<nn>.txt`, extracted from the NCERT PDF) and, for worked answers,
an independent second solve (`<code>-<nn>.solve2.json`, bank-pipeline/solve2.py):
corpus/textbook.py keeps only what it can check. The output is a source bank the
merge composes (scripts/merge_question_banks.py) through every gate, and a topic
tree per class and subject (`topics`), which the syllabus is built from.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from academicos.corpus import textbook as tb  # noqa: E402


def build(src: Path, text_dir: Path):
    records, refused, report, topics = [], [], [], {}
    for f in sorted(src.glob("*.json")):
        if f.name.endswith(".solve2.json"):
            continue
        try:
            t = json.loads(f.read_text(encoding="utf-8"))
        except ValueError as e:
            report.append({"file": f.name, "skipped": f"not JSON: {e}"})
            continue
        book, chapter = t.get("book") or {}, t.get("chapter") or {}
        txt = text_dir / str(book.get("code")) / f"{int(chapter.get('number') or 0):02d}.txt"
        if not txt.exists():
            report.append({"file": f.name, "skipped": "chapter text missing"})
            continue
        s2 = f.with_suffix(".solve2.json")
        second = json.loads(s2.read_text(encoding="utf-8")) if s2.exists() else None
        b = tb.build(t, txt.read_text(encoding="utf-8"), second=second)
        records += b.records
        refused += [{**r, "file": f.name} for r in b.refused]
        report.append({"file": f.name, "class": book.get("class"), "subject": book.get("subject"),
                       "chapter": chapter.get("title"), "built": len(b.records),
                       "refused": dict(Counter(r["reason"] for r in b.refused))})
        key = f"{book.get('subject')}|{book.get('class')}"
        topics.setdefault(key, []).append({
            "book": book.get("code"), "bookTitle": book.get("title"), "chapter": chapter.get("number"),
            "title": chapter.get("title"), "id": tb._slug(chapter.get("title")),
            "topics": [{"id": x.get("id"), "title": x.get("title")} for x in t.get("topics") or []]})
    return records, refused, report, topics


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="src", required=True, type=Path)
    ap.add_argument("--text", required=True, type=Path)
    ap.add_argument("--out", type=Path, default=REPO / "academicos-data" / "corpus" / "ncert-textbook" / "questions.json")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    records, refused, report, topics = build(a.src, a.text)
    print(f"{len(records)} records from {sum(1 for r in report if 'built' in r)} chapters; "
          f"{len(refused)} refused: {dict(Counter(r['reason'] for r in refused))}")
    by = Counter((r["grade"], r["subject"], r["source"]) for r in records)
    for (g, s, src), n in sorted(by.items()):
        print(f"  class {g} {s} [{src}]: {n}")
    if a.check:
        return 0
    ids = Counter(r["id"] for r in records)
    dupes = [i for i, n in ids.items() if n > 1]
    if dupes:
        print(f"refusing: {len(dupes)} ids appear twice, e.g. {dupes[:3]}")
        return 2
    payload = {
        "questions": records,
        "exportedCount": len(records),
        "source": "ncert-textbook-exercises",
        "notice": ("NCERT textbook exercises and questions written for each topic of each chapter; every answer "
                   "checked against the chapter's own text or by an independent second solve "
                   "(docs/textbook-exercise-format.md). Generated questions carry source ai_generated."),
        "rights": {"origin": "NCERT", "redistribution": "unknown", "basis": "",
                   "note": "No redistribution position obtained. See docs/question-bank-api.md section 2."},
        "builtAt": max((r["updatedAt"] for r in records), default=""),
        "topics": topics,
        "report": report,
        "refused": refused,
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {a.out.relative_to(REPO) if a.out.is_relative_to(REPO) else a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
