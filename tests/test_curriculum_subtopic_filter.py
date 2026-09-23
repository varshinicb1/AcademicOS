"""The Assessment Designer's subtopic filter can actually find subtopics.

Three id spaces name the same Class 10 Science chapter, and until this test
existed nothing joined them:

1. the SYLLABUS/CATALOG slug -- `chemical-reactions-equations`, from
   academicos-data/syllabus/Science_10.json, which is what
   `GET /api/v1/catalog/{subject}/{grade}/chapters` returns and what
   assessment_create_page.dart stores in `_selectedChapters`;
2. the CURRICULUM-STORE chapter id -- `chap_<uuid>`, a per-school row the
   seed creates, which is what `GET /curriculum/chapters/{id}/topics` takes;
3. the question bank's own BOARD-LEVEL taxonomy -- `taxonomyChapterId`
   `science-10/chemical-reactions-and-equations` with `topicIds`/
   `subtopicIds` under it, which no route accepts as input at all.

The web page sent (1) to the route that wants (2). Before Task 101 that
answered `200 []`; after it, 404 -- either way the page caught it and showed
an empty picker, so a claimed PRD section 21 feature had never once worked.

The join used here is the STORED mapping, not a guess: seed_cbse10.py writes
every chapter's canonical_id as `{book_id}:chapter:{syllabus slug}`, so the
catalog slug is literally recorded on the school's own chapter row when the
curriculum is seeded from the syllabus files. The bank's taxonomy ids are
NOT the join: they are school-independent, and only 109 of the 476 Class 10
Science questions in the live bank carry a `subtopicIds` value at all
(measured 2026-09-23), so filtering on them would drop 77% of the chapter's
questions before a teacher picked anything.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_assessment_routes_auth import _boot_client, _register  # noqa: E402

BASE = "/api/v1/curriculum"
CATALOG = "/api/v1/catalog"
PRINCIPAL_KEY = "test-bootstrap-key"

# The payload frontend/test/widget/assessment_create_page_test.dart renders
# the picker from -- captured from this route, not hand-written, and
# re-captured here on every run so a contract change breaks a test instead
# of silently emptying the picker again.
FIXTURE = (Path(__file__).resolve().parents[1]
           / "frontend" / "test" / "fixtures" / "chapter_subtopics_by_slug.json")

# One real chapter of the real CBSE Class 10 Science syllabus, by the slug
# academicos-data/syllabus/Science_10.json gives it. Asserted against the
# live catalog response below rather than trusted as a constant.
SLUG = "chemical-reactions-equations"


def _bearer(user: dict) -> dict:
    return {"Authorization": f"Bearer {user['token']}"}


def _seed(client, auth: dict, label: str) -> SimpleNamespace:
    """One school's real Class 10 tree plus a real approved Topic/Subtopic
    under the Science chapter the catalog slug names. Ids below the grade are
    read from the store, not through the route under test."""
    from academicos.curriculum import routes as curriculum_routes

    seeded = client.post(f"{BASE}/seed/cbse10", json={
        "academicYearLabel": "2026-27", "startDate": "2026-06-01", "endDate": "2027-03-31",
    }, headers=auth)
    assert seeded.status_code == 200, seeded.text
    body = seeded.json()

    store = curriculum_routes._require()
    science = next(s for s in store.subjects_for_grade(body["gradeId"]) if s.name == "Science")
    book = store.books_for_subject(science.id)[0]
    chapter = store.get_chapter_by_canonical_id(f"{book.id}:chapter:{SLUG}")
    assert chapter is not None, (
        "the CBSE seed must record the syllabus slug on the chapter's canonical_id -- "
        "that stored mapping is what this whole feature joins on")

    topic = client.post(f"{BASE}/chapters/{chapter.id}/topics",
                        json={"name": f"{label} topic"}, headers=auth)
    assert topic.status_code == 200, topic.text
    subtopic = client.post(f"{BASE}/topics/{topic.json()['id']}/subtopics",
                           json={"name": f"{label} subtopic"}, headers=auth)
    assert subtopic.status_code == 200, subtopic.text

    return SimpleNamespace(grade_id=body["gradeId"], subject_id=science.id, book=book.id,
                           chapter=chapter.id, topic=topic.json()["id"],
                           subtopic=subtopic.json()["id"])


@pytest.fixture
def world(tmp_path, monkeypatch):
    with _boot_client(tmp_path, monkeypatch) as client:
        p1 = _register(client, "school_1", "p1@example.com", "Priya Principal",
                       principal_key=PRINCIPAL_KEY)
        p2 = _register(client, "school_2", "p2@example.com", "Ravi Principal",
                       principal_key=PRINCIPAL_KEY)
        teacher = _register(client, "school_1", "t1@example.com", "Ana Teacher")
        s1 = _seed(client, _bearer(p1), "School one")
        s2 = _seed(client, _bearer(p2), "School two")
        yield SimpleNamespace(client=client, s1=s1, s2=s2, p1=_bearer(p1),
                              p2=_bearer(p2), teacher=_bearer(teacher))


def _by_slug(subject: str, grade: int, slug: str) -> str:
    return f"{BASE}/chapters/by-slug/{subject}/{grade}/{slug}/topics"


def test_the_slug_the_catalog_gives_the_page_is_the_slug_the_filter_accepts(world):
    """The regression itself: the chapter id assessment_create_page.dart
    holds comes from /catalog, and that exact string must reach the school's
    own subtopics."""
    catalog = world.client.get(f"{CATALOG}/Science/10/chapters", headers=world.p1)
    assert catalog.status_code == 200, catalog.text
    slugs = [c["chapterId"] for c in catalog.json()]
    assert SLUG in slugs, f"the catalog no longer offers {SLUG}: {slugs[:5]}"

    r = world.client.get(_by_slug("Science", 10, SLUG), headers=world.p1)
    assert r.status_code == 200, r.text
    names = [s["name"] for t in r.json() for s in t["subtopics"]]
    assert "School one subtopic" in names, r.text


def test_a_teacher_of_the_school_reads_it_too(world):
    """Not principal-gated: the picker is a teacher's screen."""
    r = world.client.get(_by_slug("Science", 10, SLUG), headers=world.teacher)
    assert r.status_code == 200, r.text
    assert "School one subtopic" in r.text


def test_a_class_the_school_has_not_set_up_says_so(world):
    """Class 9 was never seeded for this school. The page must be able to
    tell the principal what to do, not show an empty picker -- and the
    destination has to be a screen that exists. There is no "Curriculum"
    anywhere in the app (shell.dart's nav is Today / Syllabus / Assessments /
    Planner / Questions / Evaluate / Mastery / Teacher / Principal); book
    editions live on the Principal console's Roster tab."""
    r = world.client.get(_by_slug("Science", 9, SLUG), headers=world.p1)
    assert r.status_code == 404, r.text
    assert r.json()["detail"] == (
        "Set up Class 9 Science under Principal > Roster > Book editions "
        "to filter by subtopic")


def test_the_teacher_is_told_to_ask_her_principal_not_to_do_it_herself(world):
    """The picker is a teacher's screen (see the test above that reads it as
    a teacher), but every remedy is principal-gated: POST /seed/cbse* and
    PUT /subjects/{id}/selected-book both Depend(require_principal). Sending
    the majority reader to a console she cannot act in is not an
    instruction, so the 404 branches on role."""
    r = world.client.get(_by_slug("Science", 9, SLUG), headers=world.teacher)
    assert r.status_code == 404, r.text
    assert r.json()["detail"] == (
        "Ask your principal to set up Class 9 Science, then you can filter by subtopic")
    assert "Principal >" not in r.json()["detail"], (
        "a teacher opening the Principal console gets a 403 from the seed route")


def test_a_subject_the_school_has_not_set_up_says_so(world):
    """Sanskrit has no syllabus file, so the seed never created it."""
    r = world.client.get(_by_slug("Sanskrit", 10, SLUG), headers=world.p1)
    assert r.status_code == 404, r.text
    assert r.json()["detail"] == (
        "Set up Class 10 Sanskrit under Principal > Roster > Book editions "
        "to filter by subtopic")


def test_a_subject_with_two_editions_and_no_choice_says_which_choice_is_missing(world):
    """The Task 107 situation, and the only branch of this 404 nothing
    covered until now.

    `selected_book_for_subject` returns None when a subject has more than
    one book and no recorded selection (store.py), which is exactly what a
    curriculum database written before `create_book` started pinning the
    incumbent edition looks like. That is not hypothetical: the real
    academicos-data/curriculum/curriculum.sqlite has no `book_selections`
    TABLE at all (measured 2026-09-23 on a temp copy -- 8 subjects, 417
    subtopics), so opening it with today's code creates that table empty and
    every subject that already holds two books lands in this branch.

    Reproduced here by adding the second edition through the route a
    principal really uses and then removing the selection row it writes for
    the incumbent -- there is no unselect, by design (PRD 12.7), so the row's
    absence is the only way this state exists. Reading the unchosen edition's
    chapters would offer subtopics nobody in that class is being taught, so
    the route refuses; this asserts the sentence it refuses with, because an
    unasserted user-facing string is the one that rots."""
    from academicos.curriculum import routes as curriculum_routes
    store = curriculum_routes._require()
    seeded_book = store.get_book(world.s1.book)
    added = world.client.post(f"{BASE}/subjects/{world.s1.subject_id}/books", json={
        "title": "Science Textbook for Class X (2027 revision)",
        "publisher": "NCERT", "boardId": seeded_book.board_id,
    }, headers=world.p1)
    assert added.status_code == 200, added.text
    assert len(world.client.get(f"{BASE}/subjects/{world.s1.subject_id}/books",
                                headers=world.p1).json()) == 2

    store._exec("DELETE FROM book_selections WHERE subject_id=?", (world.s1.subject_id,))
    store._commit()
    assert store.selected_book_for_subject(world.s1.subject_id) is None, (
        "the state under test is two editions and no recorded choice")

    r = world.client.get(_by_slug("Science", 10, SLUG), headers=world.p1)
    assert r.status_code == 404, r.text
    assert r.json()["detail"] == (
        "Choose the Class 10 Science book edition under "
        "Principal > Roster > Book editions to filter by subtopic")

    teacher = world.client.get(_by_slug("Science", 10, SLUG), headers=world.teacher)
    assert teacher.status_code == 404, teacher.text
    assert teacher.json()["detail"] == (
        "Ask your principal to choose the Class 10 Science book edition, "
        "then you can filter by subtopic")


def test_a_chapter_the_chosen_edition_does_not_have_is_named(world):
    """A set-up class whose book simply has no such chapter is a different
    answer from "not set up" -- the teacher's action is different."""
    r = world.client.get(_by_slug("Science", 10, "no-such-chapter"), headers=world.p1)
    assert r.status_code == 404, r.text
    detail = r.json()["detail"]
    assert "no-such-chapter" in detail, detail
    assert "Set up Class" not in detail, detail


def test_another_schools_subtopics_are_never_reachable(world):
    """The slug is not school-scoped by itself -- both schools seeded the
    same official chapter -- so the route must resolve it inside the
    caller's OWN school and nowhere else."""
    r = world.client.get(_by_slug("Science", 10, SLUG), headers=world.p2)
    assert r.status_code == 200, r.text
    assert "School one subtopic" not in r.text
    assert "School two subtopic" in r.text

    ids = {s["id"] for t in r.json() for s in t["subtopics"]}
    assert world.s1.subtopic not in ids
    assert world.s2.subtopic in ids

    # The id-keyed route this one is built beside keeps its 403: a school_2
    # caller holding school_1's chap_ id is still refused outright.
    direct = world.client.get(f"{BASE}/chapters/{world.s1.chapter}/topics", headers=world.p2)
    assert direct.status_code == 403, direct.text


def test_the_filter_refuses_an_anonymous_caller(world):
    assert world.client.get(_by_slug("Science", 10, SLUG)).status_code == 401


def test_the_subtopic_ids_it_returns_are_accepted_by_question_search(world):
    """End of the round trip: the ids this route hands the picker are the
    ids POST /questions/search takes as `subtopicIds` (it authorizes them
    through the same school check), so the filter the page sends is a real
    filter and not a 403."""
    listed = world.client.get(_by_slug("Science", 10, SLUG), headers=world.p1)
    ids = [s["id"] for t in listed.json() for s in t["subtopics"]]
    assert ids

    search = world.client.post("/api/v1/questions/search", headers=world.p1, json={
        "subject": "Science", "grade": 10, "subtopicIds": ids})
    assert search.status_code == 200, search.text

    theirs = world.client.post("/api/v1/questions/search", headers=world.p2, json={
        "subject": "Science", "grade": 10, "subtopicIds": ids})
    assert theirs.status_code == 403, theirs.text


def _bank_of(question_ids: list[str], *, chapter_slug: str = SLUG):
    """A served bank holding exactly these question ids, under `chapter_slug`.

    Same seam tests/test_assessment_question_search_subtopics.py uses for the
    search side: the corpus-reading machinery is exercised in
    test_assessment_pool.py, and _boot_client deliberately boots with an
    empty data root, so the only way to say "this question IS in the bank"
    is to hand both routes the same pool.
    """
    from academicos.assessment.pool import PoolQuestion, QuestionPool
    from academicos.models.academic import Question

    return QuestionPool(questions=[
        PoolQuestion(
            question=Question(canonical_id=qid, title=f"Question {qid}",
                              source_text=f"Question {qid}", marks=2.0),
            subject="Science", grade="X", academic_year=None,
            chapter_id=chapter_slug, chapter_name="Chemical Reactions and Equations",
            chapter_confidence=1.0, text_hash=qid)
        for qid in question_ids])


def _serve_bank(monkeypatch, pool) -> None:
    """Both halves of the round trip read the same bank: the picker's count
    (curriculum/routes.py) and the search the count is a promise about
    (assessment/routes.py). Patching only one would let them disagree, which
    is the whole defect."""
    from academicos.assessment import routes as assessment_routes
    from academicos.curriculum import routes as curriculum_routes

    def fake_get_pool(cfg, *, subject, grade):
        return pool

    monkeypatch.setattr(curriculum_routes, "get_pool", fake_get_pool)
    monkeypatch.setattr(assessment_routes, "get_pool", fake_get_pool)


def test_the_count_only_promises_questions_the_search_can_actually_return(world, monkeypatch):
    """A link row can name a question the bank no longer serves, and a count
    that includes it is a lie with a number on it.

    `question_subtopic_links` is (question_id, subtopic_id) and nothing
    deletes a row when the id it names stops existing. Question ids are
    exactly what a bank rebuild churns -- this repo did one on 2026-09-21
    (it re-tagged Science 10 chapters), and `POST /questions/search`
    intersects the links with the pool candidates for the subject/grade/
    chapter, so a stranded link can never contribute a question to a paper.
    Counting it would put "2 questions tagged" next to a subtopic that
    yields an empty paper: the same silent wrongness Task 115 set out to
    remove, in a new place and with more authority.

    The assertion is the invariant, not the number: what the picker promises
    equals what the search delivers."""
    target = world.s1.subtopic
    _serve_bank(monkeypatch, _bank_of(["q-still-in-the-bank"]))

    from academicos.curriculum import routes as curriculum_routes
    store = curriculum_routes._require()
    store.link_question_to_subtopic(question_id="q-still-in-the-bank", subtopic_id=target)
    store.link_question_to_subtopic(question_id="q-dropped-by-the-rebuild", subtopic_id=target)

    listed = world.client.get(_by_slug("Science", 10, SLUG), headers=world.p1)
    assert listed.status_code == 200, listed.text
    counts = {s["id"]: s["taggedQuestionCount"]
              for t in listed.json() for s in t["subtopics"]}
    assert counts[target] == 1, (
        f"2 links, 1 of them stranded -> the picker must promise 1: {counts}")

    search = world.client.post("/api/v1/questions/search", headers=world.p1, json={
        "subject": "Science", "grade": 10, "chapterIds": [SLUG], "subtopicIds": [target]})
    assert search.status_code == 200, search.text
    assert [q["id"] for q in search.json()] == ["q-still-in-the-bank"]
    assert len(search.json()) == counts[target], (
        "the count the teacher reads before generating and the paper she gets "
        "after must be the same number")


def test_an_unreadable_bank_sends_no_count_rather_than_a_wrong_one(world, monkeypatch):
    """Listing a chapter's topics never touched the question bank until the
    count did, and build_pool deliberately re-raises a registry
    OperationalError instead of caching a false "no questions exist"
    (pool.py, found live 2026-09-18). A transient lock must not turn the
    picker's own read into a 500 -- that is an empty picker again, the thing
    this feature exists to end -- and must not report 0 either, which reads
    as "nothing is tagged". The field is Optional for exactly this."""
    import sqlite3

    from academicos.curriculum import routes as curriculum_routes

    def locked(cfg, *, subject, grade):
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(curriculum_routes, "get_pool", locked)

    r = world.client.get(_by_slug("Science", 10, SLUG), headers=world.p1)
    assert r.status_code == 200, r.text
    subtopics = [s for t in r.json() for s in t["subtopics"]]
    assert subtopics, "the topics themselves must still be listed"
    assert all(s["taggedQuestionCount"] is None for s in subtopics), (
        "an unknown count is null, not 0")


def test_a_subtopic_says_how_many_questions_are_tagged_to_it(world, monkeypatch):
    """The honest half of the round trip above.

    `POST /questions/search` intersects the chapter's questions with the
    question ids in `question_subtopic_links` -- nothing tagged means zero
    questions, not "fall back to the whole chapter". In real school_1 that
    table has 0 rows (measured 2026-09-23 against
    academicos-data/curriculum/curriculum.sqlite: 417 subtopics, 0 links),
    because its only writer is `POST /chapters/{id}/questions/tag` and no
    client calls it yet. So a teacher who picked a subtopic got a paper of
    102 -> 0 questions with nothing on screen saying why.

    The count travels with the subtopic so the picker can say so BEFORE the
    paper is generated. It is not a fix for the missing tagging -- it is the
    difference between a visible empty state and a silent one."""
    listed = world.client.get(_by_slug("Science", 10, SLUG), headers=world.p1)
    assert listed.status_code == 200, listed.text
    subtopics = [s for t in listed.json() for s in t["subtopics"]]
    assert subtopics
    assert all(s["taggedQuestionCount"] == 0 for s in subtopics), (
        "a freshly approved subtopic has nothing tagged to it; reporting "
        "anything but 0 would tell a teacher the filter will find questions")

    # Tag two questions the bank really serves to one subtopic and the count
    # must follow -- a hardcoded 0 would pass the assertion above.
    from academicos.curriculum import routes as curriculum_routes
    store = curriculum_routes._require()
    target = world.s1.subtopic
    _serve_bank(monkeypatch, _bank_of(["q-real-1", "q-real-2"]))
    store.link_question_to_subtopic(question_id="q-real-1", subtopic_id=target)
    store.link_question_to_subtopic(question_id="q-real-2", subtopic_id=target)

    again = world.client.get(_by_slug("Science", 10, SLUG), headers=world.p1)
    counts = {s["id"]: s["taggedQuestionCount"]
              for t in again.json() for s in t["subtopics"]}
    assert counts[target] == 2, counts
    assert all(v == 0 for k, v in counts.items() if k != target), counts


# ---------------- the web client's fixture, captured from this route ----------------
# Same posture as tests/test_curriculum_coverage_fixture.py, and for the same
# reason: the Flutter side of a curriculum screen tested only against
# hand-written JSON is how the Coverage & Pace screen read five field names
# the backend never sent and showed 0.0% for a school 89 lessons behind.

_ID_RE = re.compile(r"\b(topic|subtopic|chap|book|unit|extrun|year|subj|grade|user)_[0-9a-f]{6,}")
_TIMESTAMP_RE = re.compile(r"\d{4}-\d{2}-\d{2}T[\d:.]+\+00:00")
_FIXED_TIMESTAMP = "2026-09-23T00:00:00+00:00"


def _normalise(payload: list[dict]) -> list[dict]:
    """Generated ids and approval timestamps differ every run; both sides are
    reduced to placeholders numbered by first appearance so every real field
    is still compared exactly."""
    seen: dict[str, str] = {}

    def placeholder(m: re.Match) -> str:
        raw, stem = m.group(0), m.group(1)
        if raw not in seen:
            nth = sum(1 for v in seen.values() if v.startswith(f"{stem}_"))
            seen[raw] = f"{stem}_{nth + 1}"
        return seen[raw]

    def walk(node):
        if isinstance(node, dict):
            return {k: walk(v) for k, v in node.items()}
        if isinstance(node, list):
            return [walk(x) for x in node]
        if isinstance(node, str):
            return _TIMESTAMP_RE.sub(_FIXED_TIMESTAMP, _ID_RE.sub(placeholder, node))
        return node

    return walk(payload)


def capture_by_slug_payload(tmp_path, monkeypatch) -> list[dict]:
    """A real school's real answer: seed Class 10, approve the committed
    decomposition template for the Chemical Reactions chapter (a principal's
    own action, never automatic), then read it by the catalog slug -- exactly
    the call assessment_create_page.dart makes."""
    with _boot_client(tmp_path, monkeypatch) as client:
        principal = _register(client, "school_1", "fixture@example.com", "Priya Principal",
                              principal_key=PRINCIPAL_KEY)
        auth = _bearer(principal)
        seeded = client.post(f"{BASE}/seed/cbse10", json={
            "academicYearLabel": "2026-27", "startDate": "2026-06-01", "endDate": "2027-03-31",
        }, headers=auth)
        assert seeded.status_code == 200, seeded.text

        from academicos.curriculum import routes as curriculum_routes
        store = curriculum_routes._require()
        science = next(s for s in store.subjects_for_grade(seeded.json()["gradeId"])
                       if s.name == "Science")
        book = store.books_for_subject(science.id)[0]
        chapter = store.get_chapter_by_canonical_id(f"{book.id}:chapter:{SLUG}")

        approved = client.post(f"{BASE}/chapters/{chapter.id}/topics/approve-all",
                               json={}, headers=auth)
        assert approved.status_code == 200, approved.text
        assert approved.json()["subtopicsCreated"] > 0, approved.text

        r = client.get(_by_slug("Science", 10, SLUG), headers=auth)
        assert r.status_code == 200, r.text
        return _normalise(r.json())


def test_committed_fixture_matches_what_the_route_returns(tmp_path, monkeypatch):
    assert FIXTURE.exists(), (
        f"{FIXTURE} is missing -- regenerate it with "
        "`python tests/test_curriculum_subtopic_filter.py --write`")
    live = capture_by_slug_payload(tmp_path, monkeypatch)
    committed = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert live == committed, (
        "GET /curriculum/chapters/by-slug/... no longer matches the web client's "
        "fixture. If the change is intended, regenerate with --write and update "
        "TopicWithSubtopics.fromJson (frontend/lib/data/datasources/api/curriculum_api.dart).")


def test_the_fixture_really_carries_nested_subtopics(tmp_path, monkeypatch):
    """The picker renders subtopics under topic names, so a fixture that
    happened to capture topics with empty subtopic lists would guard
    nothing."""
    committed = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert committed, "the fixture must not be an empty topic list"
    assert sum(len(t["subtopics"]) for t in committed) >= 2


if __name__ == "__main__":
    if "--write" not in sys.argv:
        sys.exit("usage: python tests/test_curriculum_subtopic_filter.py --write")
    import tempfile

    mp = pytest.MonkeyPatch()
    try:
        # The SQLite stores stay open on Windows until exit, hence the flag.
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            payload = capture_by_slug_payload(Path(tmp), mp)
    finally:
        mp.undo()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {FIXTURE}")
