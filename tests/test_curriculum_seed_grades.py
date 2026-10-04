"""Any class from 6 to 12 can be set up, not only Class 10 -- and a seeded
chapter can reach Topic/Subtopic without an LLM key.

PRD section 0 decision 4 is "all grades 6-12, all subjects". The audit of
2026-09-21 measured the real surface: only Class 10 could be set up through the
API (`seed_cbse_all_grades` existed in seed_cbse10.py wired to no route and no
CLI command; `POST /seed/cbse9` was a 404), and the targeted re-audit of
2026-09-22 measured the level below it: on a fresh school `seed/cbse10` gave 5
subjects / 23 units / 58 chapters and then `GET /chapters/{ch}/topics` returned
`[]` for every one of them, so micro-scheduling, the subtopic filter and
coverage worked for nobody but school_1.

These tests use the REAL syllabus files and the REAL committed decomposition
templates, not fixtures -- the point is that a real principal of a real new
school gets real rows.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from test_assessment_routes_auth import _boot_client, _register  # noqa: E402

BASE = "/api/v1/curriculum"
PRINCIPAL_KEY = "test-bootstrap-key"
YEAR = {"academicYearLabel": "2026-27", "startDate": "2026-06-01", "endDate": "2027-03-31"}


def _bearer(user: dict) -> dict:
    return {"Authorization": f"Bearer {user['token']}"}


@pytest.fixture
def client(tmp_path, monkeypatch):
    with _boot_client(tmp_path, monkeypatch) as c:
        yield c


@pytest.fixture
def principal(client):
    return _register(client, "school_1", "head@school1.test", "Head",
                     principal_key=PRINCIPAL_KEY)


def _seed(client, auth: dict, grade: int):
    return client.post(f"{BASE}/seed/cbse", json={**YEAR, "grade": grade}, headers=auth)


# ---------------- 1-3: any grade, idempotent, honest about what is missing ----------------

def test_seeding_grade_7_creates_the_books_own_chapters(client, principal):
    """What a seeded Class 7 Science looks like (audit D118).

    fb0107a moved each book's own chapters to the TOP of its syllabus file,
    because six of the ten class 6-10 Maths/Science files described a
    different edition than the textbook. The CBSE units that remain carry the
    marks weightage and no chapter list, and nothing in the file says which
    chapter belongs to which unit -- while a chapter row needs a unit.

    Until D118 a seeded class got one chapter per unit: 4 rows for Science 7,
    named after the units, where the book prints 12 chapters. Now the book's
    12 chapters are the rows, in book order (taxonomy/Science_7.json). The
    CBSE course structure does not place these NCF-SE chapters in units, so
    they sit under one unit carrying the subject's marks rather than in a
    unit chosen by a guess."""
    from academicos.curriculum import routes as curriculum_routes
    from academicos.syllabus.cbse_syllabus import load_syllabus, taxonomy_chapters

    r = _seed(client, _bearer(principal), 7)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["grade"] == 7
    assert body["subjectsSeeded"] >= 4

    store = curriculum_routes._require()
    science = next(s for s in store.subjects_for_grade(body["gradeId"]) if s.name == "Science")
    book = store.books_for_subject(science.id)[0]
    seeded = [c.name for c in store.chapters_for_book(book.id)]

    doc = load_syllabus("Science", 7)
    assert doc.chapters, "fixture assumption changed: Science_7.json has no book chapters"
    assert seeded == list(taxonomy_chapters("Science", 7).values())
    assert not set(seeded) & {u.name for u in doc.units}, "no unit stands in for a chapter"
    [unit] = store.units_for_book(book.id)
    assert unit.marks == sum(u.marks for u in doc.units)


def test_seeding_the_same_grade_twice_does_not_duplicate_rows(client, principal):
    from academicos.curriculum import routes as curriculum_routes

    first = _seed(client, _bearer(principal), 7)
    assert first.status_code == 200, first.text
    store = curriculum_routes._require()
    grade_id = first.json()["gradeId"]
    before = {
        s.name: sorted(c.canonical_id
                       for b in store.books_for_subject(s.id)
                       for c in store.chapters_for_book(b.id))
        for s in store.subjects_for_grade(grade_id)
    }

    second = _seed(client, _bearer(principal), 7)
    assert second.status_code == 200, second.text
    assert second.json()["gradeId"] == grade_id
    assert second.json()["chaptersSeeded"] == 0, "a re-seed created chapters again"
    after = {
        s.name: sorted(c.canonical_id
                       for b in store.books_for_subject(s.id)
                       for c in store.chapters_for_book(b.id))
        for s in store.subjects_for_grade(grade_id)
    }
    assert after == before


def test_a_grade_missing_a_subject_file_reports_it_rather_than_seeding_fewer(client, principal):
    """Item 3, against the REAL gap in this repo's data -- no monkeypatching.

    Grade 11 and grade 12 are the same CBSE senior-secondary subject list, and
    academicos-data/syllabus/ has History_12/Geography_12/Political_Science_12
    but no grade-11 equivalents. Seeding grade 11 therefore produces fewer
    subjects than the grade offers, and the whole point of item 3 is that the
    principal is TOLD which ones, not left to notice.

    This is the case the earlier version of this test could not reach: it
    monkeypatched load_syllabus to force the branch, which passed while the
    branch was unreachable in production, because the subject list was built by
    scanning the very files it then checked for.
    """
    from academicos.syllabus.cbse_syllabus import load_syllabus

    r = _seed(client, _bearer(principal), 11)
    assert r.status_code == 200, r.text
    skipped = set(r.json()["subjectsSkipped"])
    assert {"History", "Geography", "Political Science"} <= skipped, (
        "a grade-11 subject with no syllabus file was silently absent")
    for subject in skipped:
        assert load_syllabus(subject, 11) is None, (
            f"{subject} was reported skipped but its syllabus file exists")
    # ...and everything reported as seeded really was.
    assert r.json()["subjectsSeeded"] > 0
    assert not skipped & {"Physics", "Chemistry", "Mathematics", "English"}


def test_a_grade_whose_every_subject_file_exists_reports_nothing_skipped(client, principal):
    """The other half of item 3: "reports the ones that don't" must not turn
    into crying wolf on a grade that is completely covered."""
    r = _seed(client, _bearer(principal), 12)
    assert r.status_code == 200, r.text
    assert r.json()["subjectsSkipped"] == []


def test_teacher_cannot_seed_a_grade(client, principal):
    teacher = _register(client, "school_1", "teach@school1.test", "Teacher")
    r = _seed(client, _bearer(teacher), 7)
    assert r.status_code == 403, r.text


@pytest.mark.parametrize("grade", [13, 0, -1])
def test_a_grade_outside_1_to_12_is_rejected(client, principal, grade):
    r = _seed(client, _bearer(principal), grade)
    assert r.status_code == 422, r.text


def test_a_primary_class_seeds_its_books_chapters(client, principal, monkeypatch):
    """Classes 1-5 have no CBSE marks table: the book's chapters are seeded in
    book order under one unit that claims no marks, and a subject with no book
    chapters yet is reported, not invented."""
    from academicos.syllabus import cbse_syllabus
    chapters = [{"id": "evs-3/family-and-friends", "name": "Family and Friends", "bookTitle": "Our Wondrous World"},
                {"id": "evs-3/going-to-the-mela", "name": "Going to the Mela", "bookTitle": "Our Wondrous World"}]
    monkeypatch.setattr(cbse_syllabus, "_ncert_books", lambda: {"EVS|3": {"chapters": chapters}})
    cbse_syllabus.load_syllabus.cache_clear()
    try:
        r = _seed(client, _bearer(principal), 3)
        assert r.status_code == 200, r.text
        body = r.json()
        assert (body["subjectsSeeded"], body["chaptersSeeded"]) == (1, 2)
        assert sorted(body["subjectsSkipped"]) == ["English", "Hindi", "Mathematics"]
    finally:
        cbse_syllabus.load_syllabus.cache_clear()


def test_the_class_10_route_still_works(client, principal):
    r = client.post(f"{BASE}/seed/cbse10", json=YEAR, headers=_bearer(principal))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["grade"] == 10
    assert body["subjectsSeeded"] == 5


def test_seeding_is_scoped_to_the_callers_own_school(client, principal):
    """school_id is never taken from the body -- the same posture as
    seed/cbse10. A second school's principal gets their own grade row."""
    from academicos.curriculum import routes as curriculum_routes

    other = _register(client, "school_2", "head@school2.test", "Head2",
                      principal_key=PRINCIPAL_KEY)
    mine = _seed(client, _bearer(principal), 8).json()
    theirs = _seed(client, _bearer(other), 8).json()
    assert mine["gradeId"] != theirs["gradeId"]

    store = curriculum_routes._require()
    assert store.get_academic_year(mine["academicYearId"]).school_id == "school_1"
    assert store.get_academic_year(theirs["academicYearId"]).school_id == "school_2"


# ---------------- 4: the same capability from the CLI ----------------

def test_cli_seeds_a_grade_into_a_temp_data_root(tmp_path, monkeypatch, capsys):
    from academicos import cli
    from academicos.curriculum import store as curriculum_store_mod

    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr(curriculum_store_mod, "_INSTANCE", None)

    rc = cli.main(["seed-curriculum", "--school-id", "school_cli", "--grade", "9",
                   "--academic-year-label", "2026-27",
                   "--start-date", "2026-06-01", "--end-date", "2027-03-31"])
    assert rc == 0
    assert "grade 9" in capsys.readouterr().out

    store = curriculum_store_mod.get_curriculum_store(tmp_path)
    year = store.get_academic_year_by_label("school_cli", "2026-27")
    grade = store.get_grade_by_number(year.id, 9)
    assert grade is not None
    subjects = store.subjects_for_grade(grade.id)
    assert {s.name for s in subjects} >= {"Science", "Mathematics"}


def test_cli_all_grades_seeds_every_grade_from_6_to_12(tmp_path, monkeypatch, capsys):
    """Item 4 named ONE function: "seed_cbse_all_grades (seed_cbse10.py:128) is
    wired to no route or CLI". `--all-grades` is that wire, and until
    2026-09-23 no test ran it -- the CLI test above only ever passed
    `--grade 9`, so the named function stayed the untested one."""
    from academicos import cli
    from academicos.curriculum import store as curriculum_store_mod

    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr(curriculum_store_mod, "_INSTANCE", None)

    rc = cli.main(["seed-curriculum", "--school-id", "school_every", "--all-grades",
                   "--academic-year-label", "2026-27",
                   "--start-date", "2026-06-01", "--end-date", "2027-03-31"])
    assert rc == 0
    out = capsys.readouterr().out

    store = curriculum_store_mod.get_curriculum_store(tmp_path)
    year = store.get_academic_year_by_label("school_every", "2026-27")
    assert year is not None
    for number in range(6, 13):
        assert f"grade {number}:" in out, f"grade {number} not reported"
        grade = store.get_grade_by_number(year.id, number)
        assert grade is not None, f"grade {number} not seeded"
        subjects = store.subjects_for_grade(grade.id)
        assert subjects, f"grade {number} seeded with no subjects"
        for subject in subjects:
            book = store.books_for_subject(subject.id)[0]
            assert store.chapters_for_book(book.id), (
                f"grade {number} {subject.name} seeded with no chapters")
    # One shared academic year, not seven -- the same year row every grade of
    # the school hangs off, which is what makes re-running it idempotent.
    assert len(store.academic_years_for_school("school_every")) == 1


# ---------------- 5a/5b: the committed decomposition templates ----------------

TEMPLATE_DIR = ROOT / "academicos-data" / "syllabus" / "decomposition"


def test_the_exported_template_matches_school_1s_real_approved_class_10_science():
    """Source (a): the template is school_1's approved decomposition re-keyed by
    syllabus chapter slug, not a re-invention of it."""
    from academicos.curriculum.decomposition_templates import load_template

    tpl = load_template("Science", 10)
    assert tpl is not None
    ch = tpl.chapters["chemical-reactions-equations"]
    assert ch.provenance == "template:school_1-approved"
    assert ch.topics, "no topics exported for a chapter school_1 decomposed"
    assert all(t.subtopics for t in ch.topics)


def test_textbook_heading_templates_carry_their_real_ncert_section_numbers():
    """Source (b): the Class 6 templates come from numbered textbook headings
    ("2.2.1 How to group plants?"), so the numbering has to survive -- it is the
    provenance a principal checks the proposal against."""
    from academicos.curriculum.decomposition_templates import load_template

    tpl = load_template("Science", 6)
    assert tpl is not None
    ch = tpl.chapters["diversity-in-the-living-world"]
    assert ch.provenance == "template:ncert-textbook-headings"
    names = {t.name for t in ch.topics}
    assert "How to Group Plants and Animals?" in names
    grouping = next(t for t in ch.topics if t.name == "How to Group Plants and Animals?")
    assert grouping.heading_number == "2.2"
    assert {s.heading_number for s in grouping.subtopics} == {"2.2.1", "2.2.2"}


def test_the_exporter_folds_punctuation_but_never_maps_two_different_chapters():
    """The matching rule for source (b). It has to fold what genuinely differs
    between two independently typed titles, and it must NOT fold two chapters
    that are simply different -- the Class 7-9 syllabus files list the pre-NEP
    chapter names and the only textbook trees are the 2024-25 editions, so a
    loose rule would silently attach one chapter's headings to another's name.
    That is why the exporter matches on this key exactly and reports the rest.
    """
    sys.path.insert(0, str(ROOT / "scripts"))
    from export_decomposition_templates import _norm

    assert _norm("Light \u2013 Reflection and Refraction") == _norm("Light - Reflection and Refraction")
    assert _norm("How do Organisms Reproduce") == _norm("How Organisms Reproduce?")
    assert _norm("Grassroots Democracy \u2013 Part 1: Governance") != \
        _norm("Grassroots Democracy - Part 1: Governance in Villages")
    assert _norm("Nutrition in Plants") != _norm("Nutrition in Animals")


def test_the_exporter_rekeys_an_approved_decomposition_by_syllabus_slug(tmp_path):
    """Source (a) end to end against a REAL store: an approved topic/subtopic
    under a real seeded chapter comes back out keyed by the syllabus chapter
    slug, which is what makes it applicable to a different school."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from export_decomposition_templates import from_curriculum

    from academicos.curriculum.seed_cbse10 import seed_cbse_class_10
    from academicos.curriculum.store import CurriculumStore

    db = tmp_path / "curriculum.sqlite"
    store = CurriculumStore(db)
    try:
        result = seed_cbse_class_10(store, school_id="school_x",
                                    academic_year_label="2026-27",
                                    start_date="2026-06-01", end_date="2027-03-31",
                                    apply_templates=False)
        science = next(s for s in store.subjects_for_grade(result.grade_id)
                       if s.name == "Science")
        book = store.books_for_subject(science.id)[0]
        chapter = next(c for c in store.chapters_for_book(book.id)
                       if c.canonical_id.endswith(":chapter:life-processes"))
        topic = store.create_topic(canonical_id=f"{chapter.canonical_id}:topic:nutrition",
                                   chapter_id=chapter.id, name="Nutrition", seq=0)
        store.create_subtopic(canonical_id=f"{topic.canonical_id}:subtopic:autotrophic",
                              topic_id=topic.id, name="Autotrophic Nutrition", seq=0)
    finally:
        store.close()

    exported = from_curriculum(db, "school_x")
    entry = exported[("Science", 10)]["life-processes"]
    assert entry["chapter_name"] == "Life Processes"
    assert entry["topics"] == [
        {"name": "Nutrition", "subtopics": [{"name": "Autotrophic Nutrition"}]}]
    # Another school's rows are not in this export.
    assert from_curriculum(db, "school_other") == {}


def test_committed_class_6_headings_are_verbatim_in_the_real_ncert_textbook():
    """The precision check for source (b), run against the actual PDF rather
    than trusted: every topic and subtopic the Class 6 Science template carries
    has to appear word for word in NCERT's Curiosity. (21/21 when this was
    written, measured over the first three chapters.) The textbooks are raw
    data outside the repo, so this skips where they aren't present."""
    pdf = (Path("C:/Users/varsh/OneDrive/Documents/Sarvam/ncert-dataset/textbooks")
           / "science" / "class6_curiosity.pdf")
    if not pdf.is_file():
        pytest.skip(f"NCERT textbook not present at {pdf}")
    fitz = pytest.importorskip("fitz")

    from academicos.curriculum.decomposition_templates import load_template

    tpl = load_template("Science", 6)
    doc = fitz.open(pdf)
    try:
        text = " ".join(doc[i].get_text() for i in range(doc.page_count))
    finally:
        doc.close()
    text = " ".join(text.split())

    missing = []
    checked = 0
    for chapter in list(tpl.chapters.values())[:3]:
        for topic in chapter.topics:
            for node in (topic, *topic.subtopics):
                checked += 1
                if " ".join(node.name.split()) not in text:
                    missing.append(node.name)
    assert checked >= 15, "the Class 6 Science template lost its headings"
    assert missing == [], f"headings not found verbatim in the textbook: {missing}"


@pytest.mark.xfail(reason=(
    "Mathematics_6.json template is keyed to the pre-2024 book's slugs "
    "(decimals-6, algebra-6) and matches neither the new book nor the "
    "marks units. Regenerating it needs "
    "scripts/export_decomposition_templates.py, whose own fix was "
    "still uncommitted when that stream stopped. Un-xfail by rerunning "
    "the exporter over class6_ganita_prakash.pdf."), strict=True)
def test_every_template_key_is_a_real_syllabus_chapter_slug():
    """A template keyed by a slug no seed will ever create is dead weight that
    silently never applies -- exactly the failure mode the manifest exists to
    make visible."""
    from academicos.curriculum.decomposition_templates import load_template
    from academicos.syllabus.cbse_syllabus import _slug, load_syllabus

    checked = 0
    for path in TEMPLATE_DIR.glob("[A-Z]*.json"):
        body = json.loads(path.read_text(encoding="utf-8"))
        doc = load_syllabus(body["subject"], body["grade"])
        assert doc is not None, f"{path.name} has no syllabus file"
        real = {c.id for u in doc.units for c in u.chapters}
        real |= {_slug(u.name) for u in doc.units if not u.chapters}
        tpl = load_template(body["subject"], body["grade"])
        assert set(tpl.chapters) <= real, f"{path.name}: keys not in the syllabus"
        checked += 1
    assert checked >= 5, "the committed templates disappeared"


# ---------------- 5a/5b applied: pending, never silently approved ----------------

def test_seeding_grade_10_proposes_template_topics_pending_approval(client, principal):
    """The whole point of item 5: a NEW school reaches Topic/Subtopic. It reaches
    them as PENDING proposals -- school_1's principal approved these for school_1,
    so nothing may appear as this school's approved curriculum unasked."""
    from academicos.curriculum import routes as curriculum_routes

    body = client.post(f"{BASE}/seed/cbse10", json=YEAR, headers=_bearer(principal)).json()
    assert body["chaptersWithTopics"] > 0
    assert body["topicsProposed"] > 0
    assert body["subtopicsProposed"] > 0

    store = curriculum_routes._require()
    science = next(s for s in store.subjects_for_grade(body["gradeId"]) if s.name == "Science")
    book = store.books_for_subject(science.id)[0]
    chapter = next(c for c in store.chapters_for_book(book.id)
                   if c.canonical_id.endswith(":chapter:chemical-reactions-equations"))

    assert store.topics_for_chapter(chapter.id) == [], "seeding approved topics by itself"
    runs = store.extraction_runs_for_chapter(chapter.id)
    assert len(runs) == 1
    assert runs[0].status == "pending"
    assert runs[0].prompt_version == "template:school_1-approved"
    assert runs[0].model is None, "a template is not an LLM proposal"
    proposals = store.proposals_for_run(runs[0].id)
    assert [p.status for p in proposals] == ["pending"] * len(proposals)


def test_the_seed_reports_which_chapters_got_no_template_and_why(client, principal):
    """Item 5c: grades/subjects with neither source stay chapter-only and are
    REPORTED, rather than look like a successful full setup. Class 11 Physics
    has no source. Class 7 Science (D118) and, since 2026-10-04, class 7
    Social Science are seeded from the current book's own chapters, and their
    topics come from that book's contents: until then Social Science 7 seeded
    Our Pasts, whose chapter names the Exploring Society tree does not print,
    and got no topics at all."""
    body = _seed(client, _bearer(principal), 11).json()
    assert body["chaptersWithoutTopics"] > 0
    physics = next(t for t in body["topicTemplates"] if t["subject"] == "Physics")
    assert physics["chaptersWithTopics"] == 0
    assert physics["note"], "no reason given for a subject with no topics at all"
    body = _seed(client, _bearer(principal), 7).json()
    for subject, chapters in (("Science", 12), ("Social Science", 20)):
        report = next(t for t in body["topicTemplates"] if t["subject"] == subject)
        assert report["chaptersWithTopics"] == report["chapters"] == chapters, report
        assert report["provenance"] == ["template:ncert-textbook-contents"] and report["note"] is None


def test_a_partly_covered_subject_is_not_told_that_nothing_matched():
    """Item 5c is "chapters with topics, chapters without, and why", and the
    "why" has to be true of the subject it is attached to.

    Until 2026-09-23 the exporter returned one sentence per subject -- "...no
    title matches exactly..." -- as soon as ANY chapter was uncovered, so
    Science 6, where most chapters did match, carried a reason that was false
    for it. That string is not buried in a manifest: it is
    `topicTemplates[].note` in the seed response and a line of CLI output.
    """
    from academicos.curriculum.decomposition_templates import manifest

    rows = {(r["subject"], r["grade"]): r for r in manifest()["by_subject_grade"]}
    partial = [r for r in rows.values()
               if r["chapters_with_topics"] and r["chapters_without_topics"]]
    assert partial, "no partly covered subject left to check this on"
    for row in partial:
        note = row["why_uncovered"]
        assert note, f"{row['subject']} {row['grade']} gives no reason"
        assert (f"{row['chapters_with_topics']} of {row['syllabus_chapters']} "
                "chapters got topics") in note, note
        assert "no title matches exactly" not in note
        for chapter in row["uncovered"]:
            assert chapter["why"], chapter


def test_a_subject_where_nothing_matched_says_so_and_names_the_book():
    """The other half: Class 7-9 really do get nothing, and the reason has to
    name the book it was measured against and show what that book's chapters
    are, not offer a generic apology."""
    from academicos.curriculum.decomposition_templates import manifest

    rows = {(r["subject"], r["grade"]): r for r in manifest()["by_subject_grade"]}
    row = rows[("Science", 7)]
    assert row["chapters_with_topics"] == 0
    assert row["textbook"]["textbook_chapters"] > 0, (
        "nothing was read from the Class 7 textbook at all")
    note = row["why_uncovered"]
    assert f"none of the {row['syllabus_chapters']} chapters got topics" in note
    assert "science/class7_curiosity.pdf" in note
    # The book's own chapter names are quoted, so the claim "not one of their
    # titles is in this syllabus JSON" can be checked instead of believed.
    assert '"Exploring Substances: Acidic, Basic, and Neutral"' in note


# ---------------- 5c: the reported reason has to be the measured one ---------

_BOOKS_ON_DISK = {
    ("English", 6): "english/class6_poorvi.pdf",
    ("English", 7): "english/class7_poorvi.pdf",
    ("English", 8): "english/class8_poorvi.pdf",
    ("Hindi", 9): "hindi/class9_ganga.pdf",
    ("Social Science", 9): "social_science/class9_understanding_society_part1.pdf",
}


def _rows():
    from academicos.curriculum.decomposition_templates import manifest
    return {(r["subject"], r["grade"]): r for r in manifest()["by_subject_grade"]}


def test_a_book_the_extractor_read_nothing_from_is_never_reported_as_absent():
    """The worst thing this manifest did. `from_textbooks` dropped a textbook
    whenever the extractor returned zero chapters from it, so the per-chapter
    reason fell through to "no NCERT textbook for this subject/grade in this
    repo, and no approved decomposition to copy from" -- and that string is
    surfaced verbatim to the principal as `topicTemplates[].note`. All five of
    these books are declared in the exporter's own TEXTBOOKS map AND present on
    disk, so the product was telling a principal a book does not exist while
    holding it."""
    rows = _rows()
    for (subject, grade), book in _BOOKS_ON_DISK.items():
        row = rows[(subject, grade)]
        assert row.get("textbook"), f"{subject} {grade}: the book was dropped again"
        assert row["textbook"]["books"] == [book]
        note = row["why_uncovered"]
        assert "no NCERT textbook for this subject/grade in this repo" not in note, note
        assert book in note, note
        for chapter in row["uncovered"]:
            assert "no source at all" not in chapter["why"], chapter


def test_a_subject_is_not_told_its_chapters_were_renamed_when_none_were_read():
    """A reason has to survive being read next to its own numbers. The Class 9
    Mathematics row said its chapters "do not match ... NCERT's 2024-25 NEP
    editions having renamed and reorganised the chapters" and, in the same
    sentence, "(1 chapters read)" -- the one being the book's front cover. A
    subject nothing was read from cannot be reporting a title mismatch."""
    for row in _rows().values():
        fact = row.get("textbook")
        if not fact or fact["textbook_chapters"]:
            continue
        note = row["why_uncovered"]
        assert "no chapter of that title" not in note, (row["subject"], row["grade"], note)
        assert "read no chapter out of it" in note, (row["subject"], row["grade"], note)


def test_the_committed_chapter_titles_are_the_books_own_words():
    """The manifest's `textbook_chapter_titles` is the evidence every "no
    chapter of that title" claim rests on, and it was carrying page furniture:
    "Cell: The Building Block of Life Chapter", "Geographical Diversity of
    India Questions", "Basic, and Neutral"."""
    for row in _rows().values():
        for title in (row.get("textbook") or {}).get("textbook_chapter_titles", []):
            where = (row["subject"], row["grade"], title)
            assert "Questions" not in title, where
            assert "Chapter" not in title, where
            assert not title.startswith("and "), where


def test_class_9_mathematics_reports_the_books_real_chapters():
    """Ganita Manjari 9 sets its chapter numerals at 2.05x the body size, under
    the extractor's 2.5x floor, so the exporter saw one "chapter" -- the front
    cover, whose lone 43.8pt numeral is the GRADE -- and none of the book's
    eight real ones."""
    fact = _rows()[("Mathematics", 9)]["textbook"]
    titles = fact["textbook_chapter_titles"]
    assert fact["textbook_chapters"] >= 8, titles
    assert "The World of Numbers" in titles
    assert "Orienting Yourself: The Use of Coordinates" in titles
    assert not any("GANITA MANJARI" in t for t in titles), titles


def test_the_exporter_keeps_the_facts_of_a_book_it_read_nothing_from(monkeypatch, tmp_path):
    """The same guarantee as a unit, without half a minute of PDF reading: a
    declared book that is on disk is recorded in `facts` whether or not the
    extractor got a chapter out of it, and its chapters' reason says which of
    the two happened."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import export_decomposition_templates as export

    monkeypatch.setattr(export, "textbook_sources",
                        lambda root, subject, grade: list(export.TEXTBOOKS.get((subject, grade), ())))
    monkeypatch.setattr(export, "textbook_tree", lambda root, subject, grade: [])

    matched, facts = export.from_textbooks(tmp_path, wanted={("Hindi", 9)})
    assert matched == {}
    fact = facts[("Hindi", 9)]
    assert fact["textbook_chapters"] == 0
    assert fact["books"] == ["hindi/class9_ganga.pdf"]
    assert export._why_chapter("Kritika Bhag 1", fact, True) == export._NOTHING_READ
    assert export._why_chapter("Kritika Bhag 1", None, True) == export._NO_SOURCE


def test_the_seed_response_note_matches_what_that_subject_actually_got(client, principal):
    """End to end, through the route a principal actually calls."""
    body = _seed(client, _bearer(principal), 6).json()
    for report in body["topicTemplates"]:
        if report["chaptersWithoutTopics"] == 0:
            assert report["note"] is None
            continue
        assert report["note"]
        if report["chaptersWithTopics"]:
            assert f"{report['chaptersWithTopics']} of " in report["note"], report


def test_re_seeding_does_not_propose_the_same_template_twice(client, principal):
    from academicos.curriculum import routes as curriculum_routes

    first = client.post(f"{BASE}/seed/cbse10", json=YEAR, headers=_bearer(principal)).json()
    second = client.post(f"{BASE}/seed/cbse10", json=YEAR, headers=_bearer(principal)).json()
    assert second["topicsProposed"] == 0
    assert second["chaptersWithTopics"] == 0

    store = curriculum_routes._require()
    science = next(s for s in store.subjects_for_grade(first["gradeId"]) if s.name == "Science")
    book = store.books_for_subject(science.id)[0]
    for chapter in store.chapters_for_book(book.id):
        assert len(store.extraction_runs_for_chapter(chapter.id)) <= 1


# ---------------- 5d: seed -> approved topics in minutes ----------------

def _science_chapter(store, grade_id: str, slug: str):
    science = next(s for s in store.subjects_for_grade(grade_id) if s.name == "Science")
    book = store.books_for_subject(science.id)[0]
    return next(c for c in store.chapters_for_book(book.id)
                if c.canonical_id.endswith(f":chapter:{slug}"))


def test_pending_template_topics_are_readable_for_one_chapter(client, principal):
    from academicos.curriculum import routes as curriculum_routes

    body = client.post(f"{BASE}/seed/cbse10", json=YEAR, headers=_bearer(principal)).json()
    store = curriculum_routes._require()
    chapter = _science_chapter(store, body["gradeId"], "chemical-reactions-equations")

    r = client.get(f"{BASE}/chapters/{chapter.id}/proposed-topics", headers=_bearer(principal))
    assert r.status_code == 200, r.text
    runs = r.json()
    assert len(runs) == 1
    assert runs[0]["run"]["status"] == "pending"
    assert any(p["entityType"] == "subtopic" for p in runs[0]["proposals"])


def test_approve_all_turns_a_chapters_pending_template_into_real_topics(client, principal):
    from academicos.curriculum import routes as curriculum_routes

    body = client.post(f"{BASE}/seed/cbse10", json=YEAR, headers=_bearer(principal)).json()
    store = curriculum_routes._require()
    chapter = _science_chapter(store, body["gradeId"], "chemical-reactions-equations")

    r = client.post(f"{BASE}/chapters/{chapter.id}/topics/approve-all", json={},
                    headers=_bearer(principal))
    assert r.status_code == 200, r.text
    result = r.json()
    assert result["topicsCreated"] > 0
    assert result["subtopicsCreated"] > 0

    topics = client.get(f"{BASE}/chapters/{chapter.id}/topics", headers=_bearer(principal)).json()
    assert len(topics) == result["topicsCreated"]
    # Provenance survives approval: this is an imported template a principal
    # accepted, not something an LLM wrote and not this school's own authorship.
    assert {t["sourceType"] for t in topics} == {"imported"}
    assert {t["generationVersion"] for t in topics} == {"template:school_1-approved"}
    assert all(t["approvedBy"] == principal["user"]["id"] for t in topics)
    assert all(t["subtopics"] for t in topics)


def test_approve_all_twice_does_not_duplicate_topics(client, principal):
    from academicos.curriculum import routes as curriculum_routes

    body = client.post(f"{BASE}/seed/cbse10", json=YEAR, headers=_bearer(principal)).json()
    store = curriculum_routes._require()
    chapter = _science_chapter(store, body["gradeId"], "chemical-reactions-equations")
    auth = _bearer(principal)

    first = client.post(f"{BASE}/chapters/{chapter.id}/topics/approve-all", json={}, headers=auth)
    second = client.post(f"{BASE}/chapters/{chapter.id}/topics/approve-all", json={}, headers=auth)
    assert second.status_code == 200, second.text
    assert second.json()["topicsCreated"] == 0
    assert len(store.topics_for_chapter(chapter.id)) == first.json()["topicsCreated"]


def test_a_teacher_cannot_approve_a_chapters_templates(client, principal):
    from academicos.curriculum import routes as curriculum_routes

    body = client.post(f"{BASE}/seed/cbse10", json=YEAR, headers=_bearer(principal)).json()
    store = curriculum_routes._require()
    chapter = _science_chapter(store, body["gradeId"], "chemical-reactions-equations")

    teacher = _register(client, "school_1", "t2@school1.test", "Teacher2")
    r = client.post(f"{BASE}/chapters/{chapter.id}/topics/approve-all", json={},
                    headers=_bearer(teacher))
    assert r.status_code == 403, r.text


def test_another_schools_principal_cannot_read_or_approve_the_chapter(client, principal):
    from academicos.curriculum import routes as curriculum_routes

    body = client.post(f"{BASE}/seed/cbse10", json=YEAR, headers=_bearer(principal)).json()
    store = curriculum_routes._require()
    chapter = _science_chapter(store, body["gradeId"], "chemical-reactions-equations")

    other = _register(client, "school_2", "head2@s2.test", "Head2", principal_key=PRINCIPAL_KEY)
    assert client.get(f"{BASE}/chapters/{chapter.id}/proposed-topics",
                      headers=_bearer(other)).status_code == 403
    assert client.post(f"{BASE}/chapters/{chapter.id}/topics/approve-all", json={},
                       headers=_bearer(other)).status_code == 403
