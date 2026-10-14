"""Build the NCERT textbook source bank from chapter transcriptions
(docs/textbook-exercise-format.md).

    python scripts/build_textbook_bank.py --in <folder of chapter JSONs> --text <folder of chapter texts> \\
        [--out academicos-data/corpus/ncert-textbook/questions.json] [--check]

Each chapter JSON `<code>-<nn>.json` is checked against that chapter's own text
(`<text>/<code>/<nn>.txt`, extracted from the NCERT PDF) and, for worked answers,
an independent second solve (`<code>-<nn>.solve2.json`, bank-pipeline/solve2.py):
corpus/textbook.py keeps only what it can check. The output is a source bank the
merge composes (scripts/merge_question_banks.py) through every gate, and the
book chapters with their topics per class and subject
(academicos-data/syllabus/ncert_books.json): the chapters a class studies now,
which the chapter picker lists and classes 1-5 take as their syllabus.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from academicos.assessment.chapter_filing import name_key  # noqa: E402
from academicos.corpus import textbook as tb  # noqa: E402
from academicos.syllabus import cbse_syllabus  # noqa: E402
from academicos.syllabus.current_book import studied_chapters  # noqa: E402

BOOKS_OUT = REPO / "academicos-data" / "syllabus" / "ncert_books.json"


def planned_chapters(subject: str, grade: int) -> dict[str, str]:
    """The chapters a school plans for this class (current_book.studied_chapters), by name.
    They are the bank's chapters (#146): a question filed under any other id is shown as
    not matched to a chapter."""
    return {name_key(c.name): c.id for _u, c in studied_chapters(subject, grade) if name_key(c.name)}


def chapter_ref(subject: str, grade: int, title: str) -> str:
    """The id of the chapter a school plans under this name; else the id the
    class's syllabus file or taxonomy gives it, matched on the name the book
    prints; the book chapter's own id where none names it. Only real files are
    read -- never the book-chapter fallback this script itself writes.

    The planned chapter first: Social Science 6's syllabus file names "Locating
    Places on the Earth" "locating-places-on-the-earth", the plan
    "social-science-6/locating-places-on-the-earth", and all 81 of its questions
    were filed under the first and shown as not matched (2026-10-14)."""
    planned = planned_chapters(subject, grade)
    if name_key(title) in planned:
        return planned[name_key(title)]
    names: dict[str, str] = {}
    if cbse_syllabus._resolve_syllabus_file(subject, grade) is not None:
        doc = cbse_syllabus.load_syllabus(subject, grade)
        names.update({name_key(c.name): c.id for _u, c in doc.all_chapters()})
    for cid, name in cbse_syllabus.taxonomy_chapters(subject, grade).items():
        names.setdefault(name_key(name), cid)
    names.pop("", None)
    return (names.get(name_key(title)) if name_key(title) else None) or tb.chapter_id(subject, grade, title)


def merge_books(listed: dict, built: dict) -> dict:
    """The committed book chapters with this build's laid over them, by book and
    chapter number. A build only knows the chapters it has a transcription of
    (on 2026-09-29, 1 to 7 of a class 1-5 book's 9 to 26), while the committed
    classes 1-5 come from each book's contents page and are complete: a build
    adds a chapter or its topics and never drops one."""
    out: dict = {}
    for key in sorted(set(listed) | set(built)):
        by = {(str(c["book"]), int(c["number"] or 0)): c for c in listed.get(key, {}).get("chapters", [])}
        for c in built.get(key, []):
            was = by.get((str(c["book"]), int(c["number"] or 0)))
            # The contents page's name and id stay: the chapter may already be seeded under that id.
            by[(str(c["book"]), int(c["number"] or 0))] = (
                {**was, "topics": c["topics"] or was.get("topics", [])} if was else c)
        out[key] = {"chapters": [by[k] for k in sorted(by)]}
    return out


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
        subject, grade = tb.bank_subject(book.get("subject")), int(book.get("class") or 0)
        # The book's own chapter list first, by book and number, as the generator files them: a
        # transcription can title a chapter by its unit or its opening heading ("Fun with
        # Friends" for Santoor 3's "Colours", "Where Are You Hiding?" for Math-Mela 4's "Hide
        # and Seek"), and 39 questions were filed under ids no plan holds (2026-10-14). Of the
        # 65 listed chapters transcribed, 62 carry the listed name and the other 3 are these.
        listed = next((c["id"] for c in cbse_syllabus.book_chapters(subject, grade)
                       if c.get("book") == book.get("code") and c.get("number") == chapter.get("number")), None)
        ref = listed or (chapter_ref(subject, grade, chapter.get("title")) if chapter.get("title") else None)
        # A book printed in units (Poorvi 6-8: one PDF per unit) is planned by its lessons, and
        # the unit's topics are those lessons: each question goes to the lesson it was set on.
        planned = planned_chapters(subject, grade)
        topic_refs = ({} if listed or name_key(chapter.get("title") or "") in planned else
                      {x.get("id"): planned[name_key(x.get("title") or "")] for x in t.get("topics") or []
                       if name_key(x.get("title") or "") in planned})
        b = tb.build(t, txt.read_text(encoding="utf-8"), second=second, chapter_ref=ref, topic_refs=topic_refs)
        records += b.records
        refused += [{**r, "file": f.name} for r in b.refused]
        report.append({"file": f.name, "class": book.get("class"), "subject": book.get("subject"),
                       "chapter": chapter.get("title"), "built": len(b.records),
                       "refused": dict(Counter(r["reason"] for r in b.refused))})
        if ref:
            topics.setdefault(f"{subject}|{grade}", []).append({
                "id": ref, "name": " ".join(str(chapter.get("title")).split()),
                "book": book.get("code"), "bookTitle": book.get("title"), "number": chapter.get("number"),
                "topics": [{"id": x.get("id"), "title": x.get("title")} for x in t.get("topics") or []]})
    for chapters in topics.values():
        chapters.sort(key=lambda c: (str(c["book"]), int(c["number"] or 0)))
    return records, refused, report, topics


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="src", required=True, type=Path)
    ap.add_argument("--text", required=True, type=Path)
    ap.add_argument("--out", type=Path, default=REPO / "academicos-data" / "corpus" / "ncert-textbook" / "questions.json")
    ap.add_argument("--books-out", type=Path, default=BOOKS_OUT,
                    help="the book chapters and topics per class (cbse_syllabus.book_chapters reads it)")
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
    listed = json.loads(a.books_out.read_text(encoding="utf-8")) if a.books_out.exists() else {}
    classes = merge_books(listed.get("classes", {}), topics)
    books = {"source": listed.get("source") or ("NCERT textbooks, 2026-27 catalogue: each chapter's title and "
                                                "topics as the book prints them"),
             "builtAt": payload["builtAt"], "classes": classes}
    a.books_out.parent.mkdir(parents=True, exist_ok=True)
    a.books_out.write_text(json.dumps(books, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {sum(len(c['chapters']) for c in classes.values())} book chapters for {len(classes)} class subjects")
    print(f"wrote {a.out.relative_to(REPO) if a.out.is_relative_to(REPO) else a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
