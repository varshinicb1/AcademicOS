"""Build the school-independent Topic/Subtopic templates that let a NEW school
reach Topic/Subtopic level at seed time instead of only school_1.

The gap this closes, measured 2026-09-22 on a fresh school: `POST /seed/cbse10`
gives 5 subjects, 23 units, 58 chapters, and then `GET /chapters/{ch}/topics`
returns `[]` for every one of them -- micro-scheduling, the subtopic filter and
coverage all need Subtopic rows, so none of them work for anybody but school_1,
whose 151 topics / 417 subtopics were approved by hand months ago. The syllabus
JSONs (`academicos-data/syllabus/<Subject>_<grade>.json`) stop at chapters.

Two deterministic sources, no LLM:

  a. `--from-curriculum <curriculum.sqlite>` -- school_1's own APPROVED Class 10
     decomposition. Its chapters' canonical_ids are `{book_id}:chapter:{slug}`
     where `slug` is exactly the syllabus chapter id, so the export is an exact
     key lookup, not a title guess. Provenance `template:school_1-approved`.
  b. `--from-taxonomy <dir>` -- the board-level chapter/topic/subtopic taxonomy
     built from the NCERT textbook PDFs with PyMuPDF (numbered section headings:
     "2.1 Nature - Our Science Laboratory", "2.1.1 Litmus as an indicator"),
     living on branch feat/product-exemplar under
     `academicos-data/syllabus/taxonomy/`. Provenance
     `template:ncert-textbook-headings`.

A template is keyed by (subject, grade, SYLLABUS chapter slug) so it can be
applied to any school's freshly seeded chapters. Source (b)'s trees are keyed by
their own textbook-derived slugs, so they are matched to syllabus chapters by
NORMALISED TITLE and only ever on an exact normalised match (see `_norm`). A
near-match is deliberately NOT accepted: the measured reason is that the two
sides are different textbook editions, not typo variants -- NCERT's 2024-25 NEP
rollout replaced "Nutrition in Plants" (old Class 7 Science) with "Exploring
Substances: Acidic, Basic, and Neutral" (Curiosity), and this repo's Class 7-9
syllabus JSONs still list the old chapter names. Fuzzy-matching those would not
recover a lost chapter, it would attach one chapter's headings to a different
chapter's name. Grades/subjects with no matched source stay chapter-only and are
reported in `_manifest.json`, which is the honest answer, not a gap papered over.

Templates are applied as PENDING proposals (see curriculum/decomposition_
templates.py), never as approved rows -- school_1's principal approved these for
school_1, and the existing propose -> review -> approve states are what keeps
that from silently becoming another school's approval.

Regenerate (both sources, in one pass):

    python scripts/export_decomposition_templates.py \
        --from-curriculum <copy of academicos-data/curriculum/curriculum.sqlite> \
        --from-taxonomy <checkout of academicos-data/syllabus/taxonomy>

    python scripts/export_decomposition_templates.py ... --check   # CI/no writes
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from academicos.syllabus.cbse_syllabus import _slug, load_syllabus  # noqa: E402

OUT_DIR = REPO / "academicos-data" / "syllabus" / "decomposition"
MANIFEST = OUT_DIR / "_manifest.json"

PROVENANCE_APPROVED = "template:school_1-approved"
PROVENANCE_TEXTBOOK = "template:ncert-textbook-headings"

# Which grades a template may exist for at all. 11-12 have syllabus files but
# neither source covers them (no approved decomposition, no textbook tree), so
# they appear in the manifest as uncovered rather than being skipped silently.
GRADES = (6, 7, 8, 9, 10, 11, 12)


def _norm(title: str) -> str:
    """Comparison key for a chapter title across two independently written
    sources. Folds the punctuation that actually differs between them in the
    real data -- en/em dashes vs hyphens ("Light - Reflection and Refraction"),
    curly vs straight apostrophes, a mojibake U+FFFD where a dash was lost in an
    earlier encoding round-trip -- and the English function words that one side
    includes and the other drops ("How do Organisms Reproduce" vs "How
    Organisms Reproduce"). Everything else must match exactly."""
    s = unicodedata.normalize("NFKD", title)
    s = s.replace("–", " ").replace("—", " ").replace("�", " ")
    s = s.lower()
    s = re.sub(r"^(chapter|unit)\s+\d+\s*[:.\-]?\s*", "", s)
    s = re.sub(r"\b(and|the|a|an|of|in|its|do|how)\b", " ", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


def syllabus_chapters(subject: str, grade: int) -> list[tuple[str, str]]:
    """(chapter_slug, chapter_name) exactly as seed_cbse10.seed_cbse_grade will
    create them -- including its fallback of one chapter per unit for subjects
    whose CBSE table has no sub-chapter list (Mathematics 10, English)."""
    doc = load_syllabus(subject, grade)
    if doc is None:
        return []
    out: list[tuple[str, str]] = []
    for u in doc.units:
        if u.chapters:
            out.extend((c.id, c.name) for c in u.chapters)
        else:
            out.append((_slug(u.name), u.name))
    return out


def available_subjects() -> dict[int, list[str]]:
    from academicos.syllabus.cbse_syllabus import get_available_subjects_for_grade
    return {g: get_available_subjects_for_grade(g) for g in GRADES}


# ---------------- source (a): school_1's approved decomposition ----------------

def from_curriculum(db_path: Path, school_id: str) -> dict[tuple[str, int], dict[str, Any]]:
    """Reads APPROVED topics/subtopics out of ONE school's hierarchy and re-keys
    them by syllabus chapter slug. Opened read-only (`mode=ro`): the real store
    is the running product's data, and this script only ever reads it.

    Scoped to one school on purpose. The real store also holds `demo_school`,
    whose Class 10 Science carries a single placeholder topic per chapter; keyed
    by the same syllabus slugs it silently overwrote school_1's 39 topics / 117
    subtopics with 13/13 on the first run of this script."""
    conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT g.number AS grade, s.name AS subject, ch.id AS chapter_id, "
            "       ch.canonical_id AS chapter_canonical_id, ch.name AS chapter_name, ch.seq AS seq "
            "FROM academic_years y JOIN grades g ON g.academic_year_id = y.id "
            "JOIN subjects s ON s.grade_id = g.id "
            "JOIN books b ON b.subject_id = s.id JOIN units u ON u.book_id = b.id "
            "JOIN chapters ch ON ch.unit_id = u.id "
            "WHERE y.school_id = ? "
            "ORDER BY g.number, s.name, u.seq, ch.seq",
            (school_id,),
        ).fetchall()
        out: dict[tuple[str, int], dict[str, Any]] = {}
        for r in rows:
            topics = conn.execute(
                "SELECT id, name FROM topics WHERE chapter_id=? ORDER BY seq", (r["chapter_id"],)
            ).fetchall()
            if not topics:
                continue
            slug = _chapter_slug_from_canonical(r["chapter_canonical_id"])
            if slug is None:
                continue
            entry = {
                "chapter_slug": slug,
                "chapter_name": r["chapter_name"],
                "topics": [
                    {
                        "name": t["name"],
                        "subtopics": [
                            {"name": s["name"]}
                            for s in conn.execute(
                                "SELECT name FROM subtopics WHERE topic_id=? ORDER BY seq", (t["id"],))
                        ],
                    }
                    for t in topics
                ],
            }
            out.setdefault((r["subject"], int(r["grade"])), {})[slug] = entry
        return out
    finally:
        conn.close()


def _chapter_slug_from_canonical(canonical_id: str) -> Optional[str]:
    """`book_xxxx:chapter:<syllabus slug>` -> `<syllabus slug>`. Anything that
    doesn't carry the marker is skipped rather than guessed at (a chapter
    created by the TOC-ingest path, for instance, is slugged from its own title
    and has no syllabus slug to be keyed by)."""
    marker = ":chapter:"
    i = canonical_id.find(marker)
    return canonical_id[i + len(marker):] if i >= 0 else None


# ---------------- source (b): NCERT textbook heading taxonomy ----------------

def from_taxonomy(tax_dir: Path) -> dict[tuple[str, int], dict[str, Any]]:
    out: dict[tuple[str, int], dict[str, Any]] = {}
    for path in sorted(tax_dir.glob("[A-Z]*.json")):
        tree = json.loads(path.read_text(encoding="utf-8"))
        subject, grade = tree.get("subject"), tree.get("grade")
        if not subject or not grade:
            continue
        by_norm = {_norm(name): slug for slug, name in syllabus_chapters(subject, int(grade))}
        matched: dict[str, Any] = {}
        for ch in tree.get("chapters", []):
            slug = by_norm.get(_norm(ch.get("name", "")))
            if slug is None or not ch.get("topics"):
                continue
            matched[slug] = {
                "chapter_slug": slug,
                "chapter_name": ch["name"],
                "source_file": ch.get("source_file"),
                "topics": [
                    {
                        "name": t["name"],
                        "heading_number": t.get("number"),
                        "subtopics": [
                            {"name": s["name"], "heading_number": s.get("number")}
                            for s in t.get("subtopics", [])
                        ],
                    }
                    for t in ch["topics"]
                ],
            }
        if matched:
            out[(subject, int(grade))] = matched
    return out


# ---------------- writing ----------------

def build(curriculum_db: Optional[Path], taxonomy_dir: Optional[Path],
          approved_school_id: str = "school_1") -> tuple[dict, dict]:
    """Returns ({filename: file body}, manifest). An approved decomposition wins
    over a textbook tree for the same chapter: a real principal already reviewed
    it, which is strictly better evidence than a heading number."""
    approved = from_curriculum(curriculum_db, approved_school_id) if curriculum_db else {}
    textbook = from_taxonomy(taxonomy_dir) if taxonomy_dir else {}

    files: dict[str, dict] = {}
    report: list[dict] = []
    for grade, subjects in sorted(available_subjects().items()):
        for subject in subjects:
            chapters = syllabus_chapters(subject, grade)
            a = approved.get((subject, grade), {})
            b = textbook.get((subject, grade), {})
            entries = []
            per_source = {PROVENANCE_APPROVED: 0, PROVENANCE_TEXTBOOK: 0}
            for slug, name in chapters:
                if slug in a:
                    entry = dict(a[slug], provenance=PROVENANCE_APPROVED)
                elif slug in b:
                    entry = dict(b[slug], provenance=PROVENANCE_TEXTBOOK)
                else:
                    continue
                per_source[entry["provenance"]] += 1
                entries.append(entry)

            missing = [{"chapter_slug": s, "chapter_name": n}
                       for s, n in chapters if s not in a and s not in b]
            report.append({
                "subject": subject,
                "grade": grade,
                "syllabus_chapters": len(chapters),
                "chapters_with_topics": len(entries),
                "chapters_without_topics": len(missing),
                "topics": sum(len(e["topics"]) for e in entries),
                "subtopics": sum(len(t["subtopics"]) for e in entries for t in e["topics"]),
                "from_approved_decomposition": per_source[PROVENANCE_APPROVED],
                "from_textbook_headings": per_source[PROVENANCE_TEXTBOOK],
                "why_uncovered": _why(subject, grade, missing, taxonomy_dir),
                "uncovered": missing,
            })
            if entries:
                files[f"{subject.replace(' ', '_')}_{grade}.json"] = {
                    "subject": subject,
                    "grade": grade,
                    "chapters": entries,
                }

    manifest = {
        "built_from": {
            "approved_decomposition": str(curriculum_db) if curriculum_db else None,
            "approved_school_id": approved_school_id if curriculum_db else None,
            "textbook_taxonomy": str(taxonomy_dir) if taxonomy_dir else None,
            "script": "scripts/export_decomposition_templates.py",
        },
        "totals": {
            "chapters_with_topics": sum(r["chapters_with_topics"] for r in report),
            "chapters_without_topics": sum(r["chapters_without_topics"] for r in report),
            "topics": sum(r["topics"] for r in report),
            "subtopics": sum(r["subtopics"] for r in report),
        },
        "by_subject_grade": report,
    }
    return files, manifest


def _why(subject: str, grade: int, missing: list[dict], taxonomy_dir: Optional[Path]) -> Optional[str]:
    """The measured reason a chapter has no template, so the manifest answers
    "why is Class 7 chapter-only" without anyone re-deriving it."""
    if not missing:
        return None
    if taxonomy_dir is None:
        return "no textbook taxonomy directory was given to this run"
    tree = taxonomy_dir / f"{subject.replace(' ', '_')}_{grade}.json"
    if not tree.exists():
        return ("no approved decomposition and no NCERT textbook tree for this "
                "subject/grade -- use the LLM extraction route with a key configured")
    data = json.loads(tree.read_text(encoding="utf-8"))
    n_tax = len(data.get("chapters", []))
    if all(not c.get("topics") for c in data.get("chapters", [])):
        return (f"the textbook tree ({data.get('book') or tree.name}) has {n_tax} chapters but no "
                "numbered section headings inside them -- these are literature/prose chapters, "
                "which carry no sub-structure to extract")
    return (f"the textbook tree is {data.get('book') or tree.name} (NCERT's 2024-25 NEP edition, "
            f"{n_tax} chapters) and this repo's syllabus JSON still lists the previous edition's "
            "chapter names; no title matches exactly, and a near-match would attach one chapter's "
            "headings to a different chapter")


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--from-curriculum", type=Path, default=None,
                   help="a curriculum.sqlite holding an APPROVED decomposition (read-only)")
    p.add_argument("--from-taxonomy", type=Path, default=None,
                   help="directory of <Subject>_<grade>.json textbook heading trees")
    p.add_argument("--approved-school-id", default="school_1",
                   help="whose approved decomposition to export from --from-curriculum")
    p.add_argument("--check", action="store_true",
                   help="compare against the committed output and write nothing")
    args = p.parse_args(argv)
    if not args.from_curriculum and not args.from_taxonomy:
        p.error("give at least one of --from-curriculum / --from-taxonomy")

    files, manifest = build(args.from_curriculum, args.from_taxonomy, args.approved_school_id)
    if args.check:
        stale = []
        for name, body in files.items():
            path = OUT_DIR / name
            if not path.exists() or json.loads(path.read_text(encoding="utf-8")) != body:
                stale.append(name)
        for name in stale:
            print(f"STALE: {name}")
        print(f"check: {len(files)} templates, {len(stale)} stale")
        return 1 if stale else 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, body in files.items():
        (OUT_DIR / name).write_text(
            json.dumps(body, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    MANIFEST.write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    t = manifest["totals"]
    print(f"wrote {len(files)} templates to {OUT_DIR}")
    print(f"  {t['chapters_with_topics']} chapters with topics, "
          f"{t['chapters_without_topics']} without, "
          f"{t['topics']} topics, {t['subtopics']} subtopics")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
