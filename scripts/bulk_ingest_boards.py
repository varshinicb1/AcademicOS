"""Bulk-ingest CBSE board question papers for the main subjects of Classes X and XII.

Walks the corpus zips, keeps only the main academic subjects (skipping the long
tail of vocational/regional-language papers), extracts the born-digital PDFs,
and stages them for the AcademicOS pipeline with correct subject/grade/year
metadata already attached.

Scanned papers (no text layer) are reported but not staged: `pdf_native` cannot
read them and the OCR path is per-page and metered. They are listed in the
summary so the gap is visible rather than silent.

Usage
-----
    python scripts/bulk_ingest_boards.py --stage          # copy + tag only
    python scripts/bulk_ingest_boards.py --run            # + ingest/parse/extract
    python scripts/bulk_ingest_boards.py --run --grades X # limit scope
"""
from __future__ import annotations

import argparse
import re
import shutil
import sqlite3
import subprocess
import sys
import zipfile
from collections import Counter
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover
    sys.exit("PyMuPDF is required: pip install pymupdf")

REPO = Path(__file__).resolve().parents[1]
CORPUS = Path(r"C:\Users\varsh\OneDrive\Documents\Sarvam\cbse-dataset"
              r"\question-papers\question-paper")
STAGE = REPO / "pilot-corpus" / "boards"
REGISTRY = REPO / "academicos-data" / "registry" / "registry.sqlite"

# Main academic subjects only. Each entry maps a canonical subject name to the
# patterns seen in CBSE archive names (which are wildly inconsistent).
SUBJECT_PATTERNS: dict[str, str] = {
    # Class X. "Science" is deliberately loose — the more specific
    # Social/Political/Computer Science entries are longer names and are tested
    # first (see SUBJECT_ORDER), so they claim their papers before this runs.
    "Science": r"\bscience\b",
    "Mathematics": r"math(?:ematic)?s?\b|\b0?41\b|\b241\b",
    "Social Science": r"social[_ ]?science",
    # Class XII
    "Physics": r"physics",
    "Chemistry": r"chemistry",
    "Biology": r"biology",
    "Applied Mathematics": r"applied[_ ]?math",
    "Accountancy": r"accountancy",
    "Business Studies": r"business[_ ]?studies",
    "Economics": r"economics",
    "History": r"^history|_history",
    "Geography": r"geography",
    "Political Science": r"political[_ ]?science",
    "Computer Science": r"computer[_ ]?science",
    "Psychology": r"psychology",
    "Sociology": r"sociology",
    # Shared
    "English": r"english(?:[_ ]?(?:core|elective|lang|language|lit|l_l|comm))?",
    "Hindi": r"^hindi(?:[_ ]?[ab])?$|hindi[_ ]?(?:core|elective)",
}
# Checked longest-first so "Applied Mathematics" beats "Mathematics" and
# "Social Science" beats "Science".
SUBJECT_ORDER = sorted(SUBJECT_PATTERNS, key=lambda s: -len(s))

MIN_TEXT_CHARS = 2000          # below this a PDF has no usable text layer
SKIP_IN_NAME = ("visually impaired", "for vi", "_vi", "blind")


def canonical_subject(archive_stem: str, member: str) -> str | None:
    """Map an archive/member name to one of the main subjects, else None."""
    haystack = f"{archive_stem} {member}".lower().replace("-", "_")
    haystack = re.sub(r"\d{2}_\d_\d", " ", haystack)      # drop paper codes
    haystack = re.sub(r"\s+", " ", haystack).strip()
    for subject in SUBJECT_ORDER:
        if re.search(SUBJECT_PATTERNS[subject], haystack, re.I):
            return subject
    return None


def stage(grades: list[str], years: list[str], limit_per_subject: int) -> dict:
    STAGE.mkdir(parents=True, exist_ok=True)
    staged: Counter = Counter()
    scanned: Counter = Counter()
    unreadable = 0
    failed_downloads: list[str] = []
    copied: list[tuple[Path, str, str, str]] = []

    for year in years:
        for grade in grades:
            gdir = CORPUS / year / grade
            if not gdir.exists():
                continue
            for archive in sorted(gdir.iterdir()):
                if archive.suffix.lower() != ".zip":
                    continue
                subject = canonical_subject(archive.stem, "")
                try:
                    zf = zipfile.ZipFile(archive)
                except zipfile.BadZipFile:
                    # Most of these are ~1 KB HTML error pages saved with a .zip
                    # extension — failed downloads in the corpus, not real archives.
                    head = archive.read_bytes()[:16].lstrip().lower()
                    unreadable += 1
                    if head.startswith(b"<!doctype") or head.startswith(b"<html"):
                        failed_downloads.append(archive.name)
                    continue
                with zf:
                    for member in zf.namelist():
                        if not member.lower().endswith(".pdf"):
                            continue
                        base = Path(member).name
                        if any(s in base.lower() for s in SKIP_IN_NAME):
                            continue
                        subj = subject or canonical_subject(archive.stem, base)
                        if subj is None:
                            continue
                        key = (subj, grade)
                        if staged[key] >= limit_per_subject:
                            continue
                        data = zf.read(member)
                        try:
                            doc = fitz.open(stream=data, filetype="pdf")
                        except Exception:
                            unreadable += 1
                            continue
                        chars = sum(len(doc[i].get_text())
                                    for i in range(min(6, doc.page_count)))
                        doc.close()
                        if chars < MIN_TEXT_CHARS:
                            scanned[key] += 1
                            continue
                        safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", base)
                        target = STAGE / f"{year}__{grade}__{subj.replace(' ', '_')}__{safe}"
                        if not target.exists():
                            target.write_bytes(data)
                        copied.append((target, subj, grade, year))
                        staged[key] += 1

    return {"staged": staged, "scanned": scanned, "unreadable": unreadable,
            "failed_downloads": failed_downloads, "files": copied}


def tag_registry(files: list[tuple[Path, str, str, str]]) -> int:
    """Write subject/grade/year onto the registry rows for staged papers."""
    if not REGISTRY.exists():
        print("registry not found; run ingest first", file=sys.stderr)
        return 0
    by_title = {f.stem: (subj, grade, year) for f, subj, grade, year in files}
    conn = sqlite3.connect(REGISTRY)
    conn.row_factory = sqlite3.Row
    updated = 0
    for row in conn.execute("SELECT source_id, title FROM sources").fetchall():
        meta = by_title.get(row["title"] or "")
        if not meta:
            continue
        subj, grade, year = meta
        conn.execute(
            "UPDATE sources SET doc_type='question_paper', subject=?, grade=?, "
            "academic_year=? WHERE source_id=?",
            (subj, grade, year, row["source_id"]),
        )
        updated += 1
    conn.commit()
    conn.close()
    return updated


def run_stage(name: str, extra: list[str] | None = None) -> None:
    cmd = [sys.executable, "-m", "academicos.cli", name] + (extra or [])
    print(f"\n$ {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, cwd=REPO, check=False)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--grades", nargs="*", default=["X", "XII"])
    ap.add_argument("--years", nargs="*", default=["2023", "2024", "2025"])
    ap.add_argument("--limit-per-subject", type=int, default=12,
                    help="cap papers per (subject, grade) so one subject cannot "
                         "dominate the bank")
    ap.add_argument("--run", action="store_true",
                    help="also run ingest -> parse -> extract")
    ap.add_argument("--fresh", action="store_true", help="clear the staging dir first")
    args = ap.parse_args()

    if args.fresh and STAGE.exists():
        shutil.rmtree(STAGE)

    print(f"staging from {CORPUS}")
    result = stage(args.grades, args.years, args.limit_per_subject)

    print(f"\nstaged {len(result['files'])} papers -> {STAGE}")
    for (subj, grade), n in sorted(result["staged"].items(), key=lambda x: (-x[1], x[0])):
        scanned = result["scanned"].get((subj, grade), 0)
        note = f"  ({scanned} scanned, need OCR)" if scanned else ""
        print(f"  {grade:>3}  {subj:<22} {n:3d}{note}")
    total_scanned = sum(result["scanned"].values())
    print(f"\nskipped: {total_scanned} scanned papers (no text layer), "
          f"{result['unreadable']} unreadable archives")

    if not args.run:
        print("\n--run not given; staging only. "
              f"Next: set ACOS_CORPUS_ROOT={STAGE} and run ingest/parse/extract.")
        return 0

    import os
    os.environ["ACOS_CORPUS_ROOT"] = str(STAGE)
    run_stage("ingest")
    n = tag_registry(result["files"])
    print(f"tagged {n} registry rows with subject/grade/year")
    run_stage("parse")
    run_stage("extract")
    print("\nDone. Restart the API to pick up the new question bank.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
