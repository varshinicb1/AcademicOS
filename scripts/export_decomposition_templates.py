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
  b. `--from-textbooks <dir>` -- the NCERT textbook PDFs themselves (read-only),
     read with `academicos.syllabus.textbook_headings`: PyMuPDF font size/bold
     plus the printed section numbering ("2.1 Diversity in Plants and Animals
     Around Us", "2.2.1 How to group plants?"). Provenance
     `template:ncert-textbook-headings`. The extractor lives in the package and
     has its own tests against the real PDFs, so every template committed from
     this source can be rebuilt from this branch -- an earlier version of this
     script consumed prebuilt heading trees from a scratch directory, which
     made the committed output unreproducible once that directory was gone.

A template is keyed by (subject, grade, SYLLABUS chapter slug) so it can be
applied to any school's freshly seeded chapters. Source (b)'s trees are keyed by
their own textbook-derived slugs, so they are matched to syllabus chapters by
NORMALISED TITLE and only ever on an exact normalised match (see `_norm`). A
near-match is deliberately NOT accepted, because where the two sides disagree
they are not typo variants of one list, they are two different lists:

  * Science/Mathematics/Social Science 7-9: this repo's syllabus JSONs carry
    the pre-2024 NCERT chapter names, while every textbook here is a 2024-25
    NEP edition that reorganised them. Curiosity 7 prints "Exploring
    Substances: Acidic, Basic, and Neutral" and "The World of Metals and
    Non-metals"; the syllabus JSON lists "Nutrition in Plants" and "Heat".
  * English and Hindi at every grade: the syllabus JSON lists skill areas
    ("Reading Comprehension", "Grammar (Tenses, Active-Passive, ...)") and
    names the whole reader as one chapter, while the book is a set of literary
    units. Nothing was renamed here; there was never a title to match.

Fuzzy-matching either would not recover a lost chapter, it would attach one
chapter's headings to a different chapter's name. Grades/subjects with no
matched source stay chapter-only and are reported in `_manifest.json` with
which of these applies -- the honest answer, not a gap papered over.

Templates are applied as PENDING proposals (see curriculum/decomposition_
templates.py), never as approved rows -- school_1's principal approved these for
school_1, and the existing propose -> review -> approve states are what keeps
that from silently becoming another school's approval.

Regenerate (both sources, in one pass):

    python scripts/export_decomposition_templates.py \
        --from-curriculum <copy of academicos-data/curriculum/curriculum.sqlite> \
        --from-textbooks C:/Users/varsh/OneDrive/Documents/Sarvam/ncert-dataset/textbooks

    python scripts/export_decomposition_templates.py ... --check   # CI/no writes

Reading every textbook takes a few minutes; `--grades`/`--subjects` narrow it
while iterating.
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


# ---------------- source (b): the NCERT textbooks themselves ----------------

# Which book is the textbook for a (subject, grade), relative to the
# ncert-dataset/textbooks root. Declared rather than globbed: `jemh1`/`jesc1`
# look like Class 9 from their filenames and are in fact the Class 10 books,
# and the Social Science titles ship as several part-books per grade. A
# directory means one PDF per chapter, which the extractor reads as one book.
#
# Class 10 is absent on purpose -- source (a), a principal's own approved
# decomposition, covers it and is better evidence than a heading number.
TEXTBOOKS: dict[tuple[str, int], tuple[str, ...]] = {
    ("Science", 6): ("science/class6_curiosity.pdf",),
    ("Science", 7): ("science/class7_curiosity.pdf",),
    ("Science", 8): ("science/class8_curiosity.pdf",),
    ("Science", 9): ("science/class9_exploration.pdf",),
    ("Mathematics", 6): ("maths/class6_ganita_prakash.pdf",),
    ("Mathematics", 7): ("maths/class7_ganita_prakash.pdf", "chapters/gegp2"),
    ("Mathematics", 8): ("maths/class8_ganita_prakash.pdf", "chapters/hegp2"),
    ("Mathematics", 9): ("maths/class9_ganita_manjari.pdf",),
    ("English", 6): ("english/class6_poorvi.pdf",),
    ("English", 7): ("english/class7_poorvi.pdf",),
    ("English", 8): ("english/class8_poorvi.pdf",),
    ("English", 9): ("english/class9_kaveri.pdf",),
    ("Social Science", 6): ("chapters/fees1",),
    ("Social Science", 7): ("chapters/gees1", "chapters/gees2"),
    ("Social Science", 8): ("chapters/hees1", "chapters/hees2"),
    ("Social Science", 9): ("social_science/class9_understanding_society_part1.pdf",),
    ("Hindi", 9): ("hindi/class9_ganga.pdf",),
}


def textbook_sources(books_root: Path, subject: str, grade: int) -> list[str]:
    """The declared books for this subject/grade that are actually on disk.

    Kept separate from reading them because "this repo has no textbook for
    Hindi 7" and "the Hindi 9 book is right here and the extractor got nothing
    out of it" are different answers to item 5c's "why", and until 2026-09-23
    the second was reported as the first."""
    return [rel for rel in TEXTBOOKS.get((subject, grade), ())
            if (books_root / rel).exists()]


def textbook_tree(books_root: Path, subject: str, grade: int) -> list:
    """Every chapter the textbook(s) for this subject/grade print, with their
    own headings. Returns [] both when this repo has no textbook for it
    (Class 11-12, Hindi 6-8) and when it has one the extractor read nothing
    from; `textbook_sources` is what tells those two apart."""
    from academicos.syllabus.textbook_headings import extract_chapters

    out = []
    for rel in textbook_sources(books_root, subject, grade):
        out.extend(extract_chapters(books_root / rel, books_root))
    return out


def from_textbooks(books_root: Path, wanted: Optional[set[tuple[str, int]]] = None
                   ) -> tuple[dict[tuple[str, int], dict[str, Any]],
                              dict[tuple[str, int], dict[str, Any]]]:
    """(matched entries, per-subject extraction facts).

    The second half is what makes item 5c answerable: it records what the
    textbook actually yielded (how many chapters, how many of them print
    headings) even when NONE of it matched a syllabus chapter, so the manifest
    can say "the book has 11 chapters and not one of their titles is in the
    syllabus JSON" instead of a guess.
    """
    matched_all: dict[tuple[str, int], dict[str, Any]] = {}
    facts: dict[tuple[str, int], dict[str, Any]] = {}
    for (subject, grade) in sorted(TEXTBOOKS):
        if wanted is not None and (subject, grade) not in wanted:
            continue
        present = textbook_sources(books_root, subject, grade)
        if not present:
            # Nothing declared for this subject/grade is on disk. This is the
            # only case where "no NCERT textbook for this subject/grade in this
            # repo" is a true thing to tell a principal.
            continue
        chapters = textbook_tree(books_root, subject, grade)
        by_norm = {_norm(name): slug for slug, name in syllabus_chapters(subject, grade)}
        matched: dict[str, Any] = {}
        for ch in chapters:
            slug = by_norm.get(_norm(ch.name))
            if slug is None or not ch.topics:
                continue
            matched[slug] = {
                "chapter_slug": slug,
                "chapter_name": ch.name,
                "source_file": ch.source_file,
                "topics": [
                    {
                        "name": t.name,
                        "heading_number": t.number,
                        "subtopics": [
                            {"name": s.title, "heading_number": s.number}
                            for s in t.subtopics
                        ],
                    }
                    for t in ch.topics
                ],
            }
        facts[(subject, grade)] = {
            "books": present,
            "textbook_chapters": len(chapters),
            "textbook_chapters_with_headings": sum(1 for c in chapters if c.topics),
            "textbook_chapter_titles": [c.name for c in chapters],
            "matched_chapters": len(matched),
            # Not serialised; `_why` uses it to tell "the book has no chapter
            # by that name" apart from "it has one and prints nothing inside".
            "_headings_by_norm": {_norm(c.name): bool(c.topics) for c in chapters},
        }
        if matched:
            matched_all[(subject, grade)] = matched
    return matched_all, facts


# ---------------- writing ----------------

def build(curriculum_db: Optional[Path], books_root: Optional[Path],
          approved_school_id: str = "school_1",
          wanted: Optional[set[tuple[str, int]]] = None) -> tuple[dict, dict]:
    """Returns ({filename: file body}, manifest). An approved decomposition wins
    over a textbook's headings for the same chapter: a real principal already
    reviewed it, which is strictly better evidence than a heading number."""
    approved = from_curriculum(curriculum_db, approved_school_id) if curriculum_db else {}
    textbook, facts = (from_textbooks(books_root, wanted) if books_root else ({}, {}))

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

            fact = facts.get((subject, grade))
            missing = [
                {"chapter_slug": s, "chapter_name": n,
                 "why": _why_chapter(n, fact, bool(books_root))}
                for s, n in chapters if s not in a and s not in b
            ]
            row = {
                "subject": subject,
                "grade": grade,
                "syllabus_chapters": len(chapters),
                "chapters_with_topics": len(entries),
                "chapters_without_topics": len(missing),
                "topics": sum(len(e["topics"]) for e in entries),
                "subtopics": sum(len(t["subtopics"]) for e in entries for t in e["topics"]),
                "from_approved_decomposition": per_source[PROVENANCE_APPROVED],
                "from_textbook_headings": per_source[PROVENANCE_TEXTBOOK],
                "why_uncovered": _why(len(chapters), len(entries), missing, fact),
                "uncovered": missing,
            }
            if fact:
                row["textbook"] = {k: v for k, v in fact.items() if not k.startswith("_")}
            report.append(row)
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
            # The textbook root, not a scratch copy of prebuilt trees: the
            # headings are re-extracted from these PDFs by
            # academicos/syllabus/textbook_headings.py on every run.
            "textbooks": str(books_root) if books_root else None,
            "textbook_extractor": "academicos.syllabus.textbook_headings",
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


# The three measured reasons a syllabus chapter ends up with no template. They
# are per CHAPTER, not per subject: before 2026-09-23 this file reported one
# sentence for the whole subject, so Science 6 -- where 10 of 12 chapters DID
# match -- carried "no title matches exactly", and that sentence is shown
# verbatim to principals as topicTemplates[].note.
_NO_SOURCE = "no NCERT textbook for this subject/grade in this repo, and no approved decomposition to copy from"
_NOTHING_READ = "the textbook for this subject/grade is in this repo, but the extractor read no chapter out of it"
_NOT_IN_BOOK = "the textbook has no chapter with this title"
_NO_HEADINGS = "the textbook's chapter of this name prints no section headings inside it"


def _why_chapter(name: str, fact: Optional[dict], had_books: bool) -> str:
    """Which of them applies to ONE uncovered syllabus chapter. "the textbook
    has no chapter of this name", "it has one and prints nothing inside it" and
    "the book is here but nothing came out of it" are different problems with
    different fixes, and lumping them together is how a subject that mostly
    worked ended up reporting that nothing did.

    `_NO_SOURCE` in particular is a claim about what is on disk, so it is only
    ever reached when `from_textbooks` recorded no book for this subject/grade.
    Until 2026-09-23 `from_textbooks` dropped a book it read zero chapters from,
    which made English 6-8, Hindi 9 and Social Science 9 -- five books that are
    in `TEXTBOOKS` AND on disk -- report to the principal that no textbook
    exists for them."""
    if not had_books:
        return "this run was given no textbook root"
    if not fact:
        return _NO_SOURCE
    if not fact["textbook_chapters"]:
        return _NOTHING_READ
    has_headings = fact["_headings_by_norm"].get(_norm(name))
    if has_headings is None:
        return _NOT_IN_BOOK
    return _NO_HEADINGS if not has_headings else "matched, but its topics were empty"


def _why(n_chapters: int, n_covered: int, missing: list[dict],
         fact: Optional[dict]) -> Optional[str]:
    """One sentence per subject/grade that is true for THAT subject/grade: how
    many chapters got topics, and the measured reason for each group that did
    not. Surfaced to the principal as `topicTemplates[].note`, so a subject
    where most chapters worked must not be told that nothing matched."""
    if not missing:
        return None
    counts: dict[str, int] = {}
    for m in missing:
        counts[m["why"]] = counts.get(m["why"], 0) + 1

    parts = []
    for why, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        many = n != 1
        subject_phrase = f"{n} of them" if many else "the one left"
        if why == _NOT_IN_BOOK and fact:
            books = ", ".join(fact["books"])
            # The titles are quoted, not summarised, because this sentence is
            # the whole of what a principal is given to judge the claim on --
            # and because the earlier version of it asserted a cause (NCERT's
            # 2024-25 NEP editions renaming the chapters) that was true of
            # Science/Maths/Social Science 7-9 but not of English or Hindi,
            # whose syllabus JSONs list skill areas rather than a reader's
            # units, and not of Mathematics 9, where nothing had been read at
            # all. What is measured is that the two chapter lists are different
            # lists; showing both is the honest form of that.
            examples = "; ".join(f'"{t}"' for t in fact["textbook_chapter_titles"][:3])
            parts.append(
                f"{subject_phrase} {'have' if many else 'has'} no chapter of that title in "
                f"{books}, which prints {fact['textbook_chapters']} chapters of its own "
                f"({examples}{', ...' if fact['textbook_chapters'] > 3 else ''}) and not one "
                "of their titles is in this syllabus JSON; a near-match would attach one "
                "chapter's headings to a different chapter")
        elif why == _NOTHING_READ and fact:
            books = ", ".join(fact["books"])
            parts.append(
                f"{subject_phrase} {'have' if many else 'has'} nothing to match against: "
                f"{books} is in this repo, but the extractor read no chapter out of it -- it "
                "keys on a chapter opener printing its number at display size beside a title "
                "set above the body text, and this book does not (the Hindi reader, for one, "
                "prints its chapter titles as artwork rather than as text); the LLM extraction "
                "route is this subject's path until the extractor learns the book's layout")
        elif why == _NO_HEADINGS:
            parts.append(
                f"{subject_phrase} {'are chapters' if many else 'is a chapter'} the textbook "
                f"prints with no section headings inside {'them' if many else 'it'} (prose and "
                "activity-only chapters, which carry no sub-structure to extract)")
        elif why == _NO_SOURCE:
            parts.append(
                f"{subject_phrase} {'have' if many else 'has'} no source at all -- no NCERT "
                "textbook for this subject/grade in this repo and no approved decomposition to "
                "copy; the LLM extraction route is their path when a key is configured")
        else:
            parts.append(f"{subject_phrase}: {why}")

    head = (f"{n_covered} of {n_chapters} chapters got topics"
            if n_covered else f"none of the {n_chapters} chapters got topics")
    return f"{head}; " + "; ".join(parts) + "."


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--from-curriculum", type=Path, default=None,
                   help="a curriculum.sqlite holding an APPROVED decomposition (read-only)")
    p.add_argument("--from-textbooks", type=Path, default=None,
                   help="the read-only ncert-dataset/textbooks root; headings are "
                        "re-extracted from the PDFs on every run")
    p.add_argument("--approved-school-id", default="school_1",
                   help="whose approved decomposition to export from --from-curriculum")
    p.add_argument("--grades", default=None,
                   help="comma-separated grades to read textbooks for (default: all)")
    p.add_argument("--subjects", default=None,
                   help="comma-separated subjects to read textbooks for (default: all)")
    p.add_argument("--check", action="store_true",
                   help="compare against the committed output and write nothing")
    args = p.parse_args(argv)
    if not args.from_curriculum and not args.from_textbooks:
        p.error("give at least one of --from-curriculum / --from-textbooks")

    wanted = None
    if args.grades or args.subjects:
        grades = {int(g) for g in args.grades.split(",")} if args.grades else None
        subjects = {s.strip() for s in args.subjects.split(",")} if args.subjects else None
        wanted = {key for key in TEXTBOOKS
                  if (grades is None or key[1] in grades)
                  and (subjects is None or key[0] in subjects)}

    files, manifest = build(args.from_curriculum, args.from_textbooks,
                            args.approved_school_id, wanted)
    if args.check:
        stale = []
        for name, body in files.items():
            path = OUT_DIR / name
            if not path.exists() or json.loads(path.read_text(encoding="utf-8")) != body:
                stale.append(name)
        if wanted is None:
            # A committed template this run did not produce is stale too --
            # otherwise a source that stopped covering a subject would leave a
            # file nobody can rebuild, which is the failure this script had.
            stale += [p.name for p in sorted(OUT_DIR.glob("[A-Z]*.json"))
                      if p.name not in files]
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
