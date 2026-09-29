"""Build a source bank from transcribed papers (docs/transcription-format.md).

    python scripts/build_transcribed_bank.py --in <folder of transcription JSONs> \\
        [--out academicos-data/corpus/cbse-board/questions.json] [--check]

Each transcription names the official scheme it was read with
(`paper.schemeFile`); the scheme's text layer is what every value point is
checked against (`corpus/transcribed.py`). A transcription whose scheme file is
missing, or has no text layer, contributes nothing -- its answers cannot be
checked. The output is a source bank in the shape of the CBE and SQP banks;
`scripts/merge_question_banks.py` composes it into the served bank, through
every merge gate. Next: `tag_question_bank.py` and `apply_chapter_tags.py` on the
output, as for the other sources (docs/agent-workflow.md section 5).

--check prints what would be built, per paper and per reason, and writes nothing.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from academicos.corpus import transcribed as tr  # noqa: E402

SOURCES = {"board": "cbse_board_paper", "sqp": "cbse_sample_paper", "cfpq": "cbse_question_bank"}
PREFIX = {"board": "cbse:board", "sqp": "cbse:sqpt", "cfpq": "cbse:cfpq"}


def scheme_text(path: Path) -> str:
    import pymupdf
    with pymupdf.open(str(path)) as d:
        return "".join(p.get_text() for p in d)


def build(folder: Path) -> tuple[list[dict], list[dict], list[dict]]:
    records, refused, report = [], [], []
    for f in sorted(folder.rglob("*.json")):
        try:
            t = json.loads(f.read_text(encoding="utf-8"))
        except ValueError as e:
            report.append({"file": f.name, "skipped": f"not JSON: {e}"})
            continue
        paper = t.get("paper") or {}
        kind = str(paper.get("kind") or "board")
        sf = Path(str(paper.get("schemeFile") or ""))
        if not sf.is_file():
            report.append({"file": f.name, "skipped": "scheme file missing"})
            continue
        text = scheme_text(sf)
        if len(text) < 500:
            report.append({"file": f.name, "skipped": "scheme has no text layer"})
            continue
        b = tr.build(t, source=SOURCES.get(kind, "cbse_board_paper"), scheme=tr.SchemeText.of(text),
                     scheme_file=sf.name, id_prefix=PREFIX.get(kind, "cbse:board"))
        records += b.records
        refused += [{**r, "file": f.name} for r in b.refused]
        report.append({"file": f.name, "year": paper.get("year"), "subject": paper.get("subject"),
                       "code": paper.get("code"), "built": len(b.records),
                       "refused": dict(Counter(r["reason"] for r in b.refused))})
    return records, refused, report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="src", required=True, type=Path, nargs="+",
                    help="transcription folders: board, sqp and cfpq go into one file")
    ap.add_argument("--out", type=Path, default=REPO / "academicos-data" / "corpus" / "cbse-board" / "questions.json")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    records, refused, report = [], [], []
    for src in a.src:
        more = build(src)
        records += more[0]
        refused += more[1]
        report += more[2]
    by_subject = Counter((r["grade"], r["subject"]) for r in records)
    print(f"{len(records)} records from {sum(1 for r in report if 'built' in r)} papers; "
          f"{len(refused)} refused: {dict(Counter(r['reason'] for r in refused))}")
    for (g, s), n in sorted(by_subject.items()):
        print(f"  class {g} {s}: {n}")
    skipped = [r for r in report if "skipped" in r]
    if skipped:
        print(f"{len(skipped)} papers skipped: {dict(Counter(r['skipped'] for r in skipped))}")
    if a.check:
        return 0
    ids = Counter(r["id"] for r in records)
    dupes = [i for i, n in ids.items() if n > 1]
    if dupes:
        print(f"refusing: {len(dupes)} ids appear twice, e.g. {dupes[:3]}")
        return 2
    old = json.loads(a.out.read_text(encoding="utf-8")) if a.out.exists() else {}
    payload = {
        "questions": records,
        "exportedCount": len(records),
        "source": "cbse-papers-transcribed",
        "notice": ("CBSE question papers transcribed with their official marking schemes; every value point "
                   "found in the scheme's own text (docs/transcription-format.md)."),
        "rights": {"origin": "CBSE", "redistribution": "unknown", "basis": "",
                   "note": "No redistribution position obtained. See docs/question-bank-api.md section 2."},
        "builtAt": max((r["updatedAt"] for r in records), default=""),
        "report": report,
        "refused": refused,
    }
    # Chapter tags written into this file by apply_chapter_tags.py survive a rebuild of the same records.
    tags = {r["id"]: r.get("chapterIds") for r in old.get("questions", []) if r.get("chapterIds")}
    for r in payload["questions"]:
        if r["id"] in tags:
            r["chapterIds"] = tags[r["id"]]
    for key in ("chapterTaggedAt", "chapterTagMethod"):
        if old.get(key):
            payload[key] = old[key]
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {a.out.relative_to(REPO) if a.out.is_relative_to(REPO) else a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
