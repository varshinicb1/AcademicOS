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

def test_seeding_grade_7_creates_its_real_syllabus_chapters(client, principal):
    """Not a count assertion: the real Class 7 Science chapter names from
    academicos-data/syllabus/Science_7.json have to actually be rows."""
    from academicos.curriculum import routes as curriculum_routes
    from academicos.syllabus.cbse_syllabus import load_syllabus

    r = _seed(client, _bearer(principal), 7)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["grade"] == 7
    assert body["subjectsSeeded"] >= 4

    store = curriculum_routes._require()
    science = next(s for s in store.subjects_for_grade(body["gradeId"]) if s.name == "Science")
    book = store.books_for_subject(science.id)[0]
    seeded = {c.name for c in store.chapters_for_book(book.id)}

    doc = load_syllabus("Science", 7)
    expected = {c.name for u in doc.units for c in u.chapters}
    assert expected, "fixture assumption changed: Science_7.json has no chapters"
    assert expected <= seeded


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


def test_a_grade_missing_a_subject_file_reports_it_rather_than_seeding_fewer(client, principal,
                                                                             monkeypatch):
    """Grade 12 has the most subject files of any grade; deliberately hide one
    so the route has something real to report. Never silently fewer (item 3)."""
    from academicos.syllabus import cbse_syllabus

    real_load = cbse_syllabus.load_syllabus.__wrapped__

    def _hide_history(subject: str, grade: int):
        if subject == "History" and grade == 12:
            return None
        return real_load(subject, grade)

    monkeypatch.setattr(cbse_syllabus, "load_syllabus", _hide_history)
    monkeypatch.setattr("academicos.curriculum.seed_cbse10.load_syllabus", _hide_history)

    r = _seed(client, _bearer(principal), 12)
    assert r.status_code == 200, r.text
    assert "History" in r.json()["subjectsSkipped"]


def test_teacher_cannot_seed_a_grade(client, principal):
    teacher = _register(client, "school_1", "teach@school1.test", "Teacher")
    r = _seed(client, _bearer(teacher), 7)
    assert r.status_code == 403, r.text


@pytest.mark.parametrize("grade", [5, 13, 0, -1])
def test_a_grade_outside_6_to_12_is_rejected(client, principal, grade):
    r = _seed(client, _bearer(principal), grade)
    assert r.status_code == 422, r.text


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
    REPORTED. Class 7's syllabus JSON lists the pre-NEP chapter names while the
    only textbook tree is the 2024-25 edition, so nothing matches -- the route
    has to say so rather than look like a successful full setup."""
    body = _seed(client, _bearer(principal), 7).json()
    assert body["chaptersWithTopics"] == 0
    assert body["chaptersWithoutTopics"] > 0
    science = next(t for t in body["topicTemplates"] if t["subject"] == "Science")
    assert science["chaptersWithTopics"] == 0
    assert science["note"], "no reason given for a subject with no topics at all"


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
