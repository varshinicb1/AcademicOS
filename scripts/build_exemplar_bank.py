"""Build the NCERT Exemplar question bank, classes 6-10, Maths and Science.

Parses the 165 Exemplar files (``ncert-dataset/exemplar/classVI..classX``),
pairs every question with NCERT's own answer from the book's answers file, and
writes the questions that may be served in the question-bank wire shape.

The answer-key rule
-------------------
Without an answer key, no question (PRD rule Q1) -- and a confidently wrong
key or text is worse than none. Every question the parser refuses is counted by
reason in ``_manifest.json`` and listed in ``_excluded.json`` with its text and
whatever answer was found, so the shortfall is auditable and the parser can be
improved against it rather than the loss being invisible.

Outputs, all under ``academicos-data/corpus/ncert-exemplar/``:

  questions.json   the servable records ({"questions": [...], ...})
  _manifest.json   counts by class x subject x section kind x exclusion reason,
                   answers found per book, chapter-title checks, the chapter
                   mapping table, marks distribution
  _excluded.json   every refused question with its reason

Run:  python scripts/build_exemplar_bank.py [--check] [--root DIR] [--cache DIR]

``--cache`` keeps each file's rendered pages as JSON so a rerun does not
re-render 143 MB of PDF (about seven minutes); the cache is keyed by file size,
modification time and `render_key()` -- a hash of the parser module and the
PyMuPDF version -- so pages rendered by an older renderer are never reused. A
cache keyed on the PDF alone once kept loss marks the current renderer no
longer made, and the committed bank could not be rebuilt from committed code.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from academicos.corpus import ncert_exemplar as ex  # noqa: E402

DEFAULT_ROOT = REPO.parent / "ncert-dataset" / "exemplar"
OUT_DIR = REPO / "academicos-data" / "corpus" / "ncert-exemplar"
SYLLABUS = REPO / "academicos-data" / "syllabus"


def render_key() -> str:
    """What the rendered pages depend on besides the PDF: the parser module's
    source (the renderer lives in it) and the PyMuPDF version."""
    h = hashlib.sha256(Path(ex.__file__).read_bytes())
    h.update(str(getattr(ex._pymupdf(), "VersionBind", "")).encode())
    return h.hexdigest()[:16]


def _reader(cache: Path | None):
    if cache is None:
        return ex.read_pdf
    key = render_key()

    def read(path: Path) -> list[str]:
        st = path.stat()
        slot = cache / path.parent.parent.name / path.parent.name / f"{path.stem}.json"
        if slot.exists():
            data = json.loads(slot.read_text(encoding="utf-8"))
            if (data.get("size") == st.st_size and data.get("mtime") == int(st.st_mtime)
                    and data.get("render") == key):
                return data["pages"]
        pages = ex.read_pdf(path)
        slot.parent.mkdir(parents=True, exist_ok=True)
        slot.write_text(json.dumps({"size": st.st_size, "mtime": int(st.st_mtime),
                                    "render": key, "pages": pages}, ensure_ascii=False),
                        encoding="utf-8")
        return pages
    return read


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report only, write nothing")
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--cache", type=Path, default=None)
    args = ap.parse_args()
    if not args.root.exists():
        print(f"no Exemplar files at {args.root}", file=sys.stderr)
        return 1
    try:
        # Before anything is read: under another PyMuPDF the same PDFs give a
        # different bank (see "PDF library" in the parser's docstring).
        ex.require_verified_pymupdf()
    except RuntimeError as e:
        print(f"refusing to build: {e}", file=sys.stderr)
        return 2

    questions, reports = ex.parse_all(args.root, _reader(args.cache))
    book_of = {(b.grade, b.subject): b for b in ex.BOOKS}

    # chapter mapping (rule Q2): exact title match against the syllabus file
    syllabi = {key: ex.load_syllabus(SYLLABUS / f"{key[1]}_{key[0]}.json") for key in book_of}
    chapter_map: dict[tuple[int, str, int], str] = {}
    map_table = []
    for (g, s), titles in ex.CHAPTER_TITLES.items():
        for n, title in sorted(titles.items()):
            cid = ex.map_chapter(title, syllabi[(g, s)]) or ""
            chapter_map[(g, s, n)] = cid
            map_table.append({"grade": g, "subject": s, "exemplarChapter": n,
                              "title": title, "chapterId": cid or None,
                              "syllabusName": next((nm for i, nm in syllabi[(g, s)]
                                                    if i == cid), None)})

    records, excluded = [], []
    counts: dict = collections.defaultdict(lambda: collections.Counter())
    for q in questions:
        reason = ex.exclusion_reason(q)
        cell = f"{q.grade}|{q.subject}"
        counts[cell]["found"] += 1
        counts[cell]["withAnswer"] += q.has_answer
        counts[cell][f"kind:{q.section_kind}"] += 1
        if reason:
            counts[cell][f"excluded:{reason}"] += 1
            excluded.append({"id": q.record_id, "reason": reason, "grade": q.grade,
                             "subject": q.subject, "chapter": q.chapter_number,
                             "exercise": q.scope or None, "number": q.number,
                             "kind": q.section_kind, "file": q.source_file, "page": q.page,
                             "stem": q.stem, "options": q.options,
                             "optionsError": q.options_error or None,
                             "answer": q.answer_text or None,
                             "answerError": q.answer_error or None})
            continue
        counts[cell]["written"] += 1
        counts[cell][f"written:{q.section_kind}"] += 1
        rec = ex.to_bank_record(q, chapter_map.get((q.grade, q.subject, q.chapter_number), ""),
                                book_of[(q.grade, q.subject)].current_textbook)
        counts[cell][f"marks:{rec['marks']}"] += 1
        counts[cell]["chapterMapped"] += bool(rec["chapterIds"])
        records.append(rec)

    ids = collections.Counter(r["id"] for r in records)
    dupes = [i for i, c in ids.items() if c > 1]
    if dupes:
        print(f"duplicate record ids: {dupes[:5]}", file=sys.stderr)
        return 1

    # ---- report ----------------------------------------------------------
    print("NCERT Exemplar, classes 6-10")
    tot = collections.Counter()
    for rep in reports:
        cell = f"{rep['grade']}|{rep['subject']}"
        c = counts[cell]
        files = [f for f in rep["files"] if f.get("chapter")]
        reasons = {k.split(":", 1)[1]: v for k, v in c.items() if k.startswith("excluded:")}
        marks = {k.split(":", 1)[1]: v for k, v in c.items() if k.startswith("marks:")}
        print(f"  class {rep['grade']:<2} {rep['subject']:<11} files {len(files):>2}  "
              f"found {c['found']:>4}  with answer {c['withAnswer']:>4}  "
              f"written {c['written']:>4}  mapped {c['chapterMapped']:>4}")
        print(f"      answers file {rep['answers'].get('file')}: "
              f"{rep['answers'].get('answers', 0)} answers, "
              f"{rep['answers'].get('ambiguous', 0)} ambiguous")
        print(f"      excluded: {dict(sorted(reasons.items(), key=lambda kv: -kv[1]))}")
        print(f"      marks: {dict(sorted(marks.items()))}")
        bad = [f["file"] for f in files if not f["titleVerified"] or not f["chapterVerified"]]
        if bad:
            print(f"      WARNING title/chapter not verified in: {bad}")
        tot.update(c)
    print(f"  TOTAL found {tot['found']}, with answer {tot['withAnswer']}, "
          f"written {tot['written']}, excluded {len(excluded)}")

    if args.check:
        print("\n--check: nothing written")
        return 0

    built_at = datetime.now(timezone.utc).isoformat()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "questions": records,
        "exportedCount": len(records),
        "source": "ncert-exemplar",
        "notice": ("NCERT Exemplar Problems, classes 6-10, Mathematics and Science. "
                   "Every record carries NCERT's own answer from the book's answers "
                   "file; marks are assigned by section kind (metadata.marksBasis)."),
        "rights": {
            "origin": "NCERT",
            "redistribution": "unknown",
            "basis": "",
            "note": "No redistribution position obtained. See docs/question-bank-api.md section 2.",
        },
        "builtAt": built_at,
    }
    manifest = {
        "builtAt": built_at,
        "root": "ncert-dataset/exemplar",
        "counts": {cell: dict(sorted(c.items())) for cell, c in sorted(counts.items())},
        "exclusionReasons": list(ex.EXCLUSION_REASONS),
        "marksBasis": dict(ex.MARKS_BY_KIND),
        "chapterMap": map_table,
        "books": reports,
    }
    (OUT_DIR / "questions.json").write_text(json.dumps(payload, ensure_ascii=False),
                                            encoding="utf-8")
    (OUT_DIR / "_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1),
                                            encoding="utf-8")
    (OUT_DIR / "_excluded.json").write_text(json.dumps(
        {"count": len(excluded), "items": excluded}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(f"\nwrote {OUT_DIR.relative_to(REPO)}/questions.json  ({len(records)} records)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
